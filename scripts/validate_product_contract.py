#!/usr/bin/env python3
"""validate_product_contract.py - deterministic gate over the Yoma product
acceptance contract (docs/reports/data/yoma-product-acceptance-contract.json).

This validates the CONTRACT FILE's own internal consistency. It does not
inspect Yoma's corpus data and it never upgrades a requirement's status; it
only fails closed when the recorded JSON is malformed, duplicated, uses an
unknown enum value, references an unknown requirement id, claims a
PASS/FAIL status without the evidence a status requires, or declares a
typed evidence component whose own shape is incomplete or contradictory.

Usage:
  python3 scripts/validate_product_contract.py
  python3 scripts/validate_product_contract.py --contract path/to/file.json
  python3 scripts/validate_product_contract.py --quiet
"""
import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "docs" / "reports" / "data" / "yoma-product-acceptance-contract.json"

# Registry of every requirement id this validator currently recognizes. A
# requirement id present in the contract file but absent here, or vice
# versa, is a hard failure -- the registry and the file must change
# together, in the same diff, never silently.
KNOWN_REQUIREMENT_IDS = frozenset(
    [
        "YOMA-CORPUS-COVERAGE",
        "YOMA-SOURCE-TEXT-INTEGRITY",
        "YOMA-LITERAL-TRANSLATION-COVERAGE",
        "YOMA-GEMARA-TRANSLATION-ACCURACY",
        "YOMA-RASHI-TRANSLATION-ACCURACY",
        "YOMA-RASHI-TEXT-INTEGRITY",
        "YOMA-RASHI-CONTENT-QUALITY",
        "YOMA-RASHI-ASSOCIATION-INTEGRITY",
        "YOMA-RASHI-BOUNDARY-AUTHORIZATION",
        "YOMA-RASHI-NO-DUPLICATION",
        "YOMA-RASHI-RENDERER-READINESS",
        "YOMA-ENRICHMENT-CONTRACT-COMPLIANCE",
        "YOMA-ARGUMENT-TAXONOMY-COVERAGE",
        "YOMA-SOURCE-REFS-NORMALIZATION",
        "YOMA-ENRICHMENT-COMPLETENESS",
        "YOMA-NAVIGATION-RENDERING",
        "YOMA-SEARCH-AVAILABILITY",
        "YOMA-BUILD-REPRODUCIBILITY",
        "YOMA-TEST-SUITE-GREEN",
        "YOMA-PRODUCTION-RELEASE-VERIFICATION",
        "YOMA-NO-ENRICHMENT-DATA-DELETION",
    ]
)

REQUIRED_FIELDS = (
    "id",
    "category",
    "mandatory",
    "verificationMode",
    "scopeStatement",
    "independentReviewRequired",
    "evidenceComponents",
    "status",
    "repairVsReconstruction",
    "repairDecision",
    "evidenceRefs",
)

VALID_CATEGORIES = frozenset(
    [
        "corpus",
        "source-layer",
        "translation",
        "rashi",
        "enrichment",
        "navigation",
        "build",
        "release",
        "policy",
    ]
)

# "undecided" is the honest default: a requirement has not yet had an
# evidence-based repair-vs-reconstruction triage performed. "repair" and
# "reconstruct" are real decisions and require a repairDecision object.
VALID_REPAIR_DECISIONS = frozenset(["undecided", "repair", "reconstruct"])
DECISIONS_REQUIRING_REPAIR_DECISION = frozenset(["repair", "reconstruct"])

TERMINAL_STATUSES_REQUIRING_EVIDENCE = frozenset(["PASS", "FAIL"])

# Component types a requirement's evidenceComponents array may contain.
VALID_COMPONENT_TYPES = frozenset(["deterministic", "semantic", "external"])

# Which component types a verificationMode mechanically requires. "both"
# requires both a deterministic and a semantic component -- a single flat
# sourceClass/acceptanceCommand pair cannot satisfy this.
REQUIRED_COMPONENTS_BY_MODE = {
    "deterministic": frozenset(["deterministic"]),
    "semantic": frozenset(["semantic"]),
    "both": frozenset(["deterministic", "semantic"]),
    "external": frozenset(["external"]),
}

VALID_SOURCE_CLASSES = frozenset(
    ["repo-script", "repo-test", "ci-workflow", "review-record", "external-source"]
)

# Fields a semantic or external component's review record must declare it
# will carry, so the schema cannot imply that shape alone validates
# judgment: scope coverage, source-first review, and enrichment-field
# preservation are named explicitly rather than left implicit.
BASE_REVIEW_RECORD_FIELDS = (
    "reviewer",
    "reviewedAt",
    "disposition",
    "evidenceRefs",
    "scopeCoverage",
    "sourceFirstReview",
    "enrichmentFieldsPreserved",
)
EXTERNAL_REVIEW_RECORD_FIELDS = ("edition", "license", "sourceProvenance")
INDEPENDENT_REVIEWER_FIELD = "independentReviewer"

# Categories whose semantic/external requirements must state exhaustive
# corpus scope (defect: semantic requirements must express exhaustive scope,
# not an implicit sample). Checked via scopeStatement wording.
EXHAUSTIVE_SCOPE_CATEGORIES = frozenset(["translation", "rashi", "enrichment"])

# A sourceClass=ci-workflow component must describe how to read the result
# of a workflow run that already happened -- never a command that itself
# triggers/dispatches that workflow. Case-insensitive substring match.
FORBIDDEN_CI_DISPATCH_SUBSTRINGS = ("gh workflow run",)

REPAIR_DECISION_FIELDS = (
    "decidedAt",
    "decisionEvidence",
    "contentScopeFingerprint",
    "reopenHistory",
)


class ContractError(Exception):
    """Raised for any fail-closed condition. Carries a list of defects."""

    def __init__(self, defects):
        super().__init__("; ".join(defects))
        self.defects = defects


def load_contract(path):
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ContractError([f"cannot read contract file {path}: {exc}"])
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ContractError([f"malformed JSON in {path}: {exc}"])
    return data


def _is_nonblank_str(value):
    return isinstance(value, str) and value.strip() != ""


def _validate_review_record_fields(req_id, where, component, required_extra=()):
    defects = []
    fields = component.get("reviewRecordRequiredFields")
    if not isinstance(fields, list) or not fields:
        defects.append(
            f"{req_id}: {where}.reviewRecordRequiredFields must be a non-empty array"
        )
        return defects
    fields_set = set(fields)
    needed = set(BASE_REVIEW_RECORD_FIELDS) | set(required_extra)
    missing = sorted(needed - fields_set)
    if missing:
        defects.append(
            f"{req_id}: {where}.reviewRecordRequiredFields is missing required "
            f"field(s): {', '.join(missing)}"
        )
    return defects


def _validate_component(req, where, component, component_type):
    req_id = req["id"]
    defects = []

    if not isinstance(component, dict):
        return [f"{req_id}: {where} must be an object"]

    if component.get("component") != component_type:
        defects.append(
            f"{req_id}: {where}.component must equal '{component_type}', got "
            f"'{component.get('component')}'"
        )

    status = component.get("status")
    statuses_allowed = req.get("_status_enum") or []
    if statuses_allowed and status not in statuses_allowed:
        defects.append(f"{req_id}: {where}.status '{status}' not in declared statusEnum")

    evidence_refs = component.get("evidenceRefs")
    if not isinstance(evidence_refs, list):
        defects.append(f"{req_id}: {where}.evidenceRefs must be an array")
        evidence_refs = []
    else:
        for ref_index, ref in enumerate(evidence_refs):
            if not _is_nonblank_str(ref):
                defects.append(
                    f"{req_id}: {where}.evidenceRefs[{ref_index}] must be a nonblank string"
                )

    exact_commit = component.get("exactCommitBinding")
    if exact_commit is not None and not _is_nonblank_str(exact_commit):
        defects.append(f"{req_id}: {where}.exactCommitBinding must be null or a nonblank string")

    if status in TERMINAL_STATUSES_REQUIRING_EVIDENCE:
        if not evidence_refs:
            defects.append(
                f"{req_id}: {where}.status '{status}' claimed with no evidenceRefs "
                "(evidence-free status claim)"
            )
        if exact_commit is None:
            defects.append(
                f"{req_id}: {where}.status '{status}' claimed with no exactCommitBinding "
                "(evidence-free status claim)"
            )

    if component_type == "deterministic":
        source_class = component.get("sourceClass")
        if source_class not in VALID_SOURCE_CLASSES:
            defects.append(f"{req_id}: {where}.sourceClass '{source_class}' is not a valid sourceClass")
        if not _is_nonblank_str(component.get("acceptanceCommand")):
            defects.append(f"{req_id}: {where}.acceptanceCommand must be a nonblank string")
        if source_class == "ci-workflow":
            command = component.get("acceptanceCommand") or ""
            lowered = command.lower()
            for forbidden in FORBIDDEN_CI_DISPATCH_SUBSTRINGS:
                if forbidden in lowered:
                    defects.append(
                        f"{req_id}: {where}.acceptanceCommand must not contain a mutating "
                        f"workflow-dispatch command ('{forbidden}'); a ci-workflow component "
                        "must describe reading an already-produced run's result, never "
                        "triggering one"
                    )

    elif component_type in ("semantic", "external"):
        source_class = component.get("sourceClass")
        expected_source_class = "review-record" if component_type == "semantic" else "external-source"
        if source_class != expected_source_class:
            defects.append(
                f"{req_id}: {where}.sourceClass must be '{expected_source_class}' for a "
                f"{component_type} component, got '{source_class}'"
            )
        if not _is_nonblank_str(component.get("acceptanceCommand")):
            defects.append(f"{req_id}: {where}.acceptanceCommand must be a nonblank string")

        required_extra = EXTERNAL_REVIEW_RECORD_FIELDS if component_type == "external" else ()
        if req.get("independentReviewRequired"):
            required_extra = tuple(required_extra) + (INDEPENDENT_REVIEWER_FIELD,)
        defects.extend(_validate_review_record_fields(req_id, where, component, required_extra))

    return defects


def validate_contract(data, known_ids=KNOWN_REQUIREMENT_IDS):
    defects = []

    if not isinstance(data, dict):
        raise ContractError(["top-level contract value must be an object"])

    status_enum = data.get("statusEnum")
    verification_modes = data.get("verificationModes")
    if not isinstance(status_enum, list) or not status_enum:
        defects.append("missing or empty top-level statusEnum")
        status_enum = []
    if not isinstance(verification_modes, list) or not verification_modes:
        defects.append("missing or empty top-level verificationModes")
        verification_modes = []

    requirements = data.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        raise ContractError(defects + ["requirements must be a non-empty array"])

    seen_ids = set()
    file_ids = set()

    for index, req in enumerate(requirements):
        where = f"requirements[{index}]"
        if not isinstance(req, dict):
            defects.append(f"{where}: requirement must be an object")
            continue

        missing = [field for field in REQUIRED_FIELDS if field not in req]
        if missing:
            defects.append(f"{where}: missing required field(s): {', '.join(missing)}")
            continue

        req_id = req["id"]
        if not _is_nonblank_str(req_id):
            defects.append(f"{where}: id must be a nonblank string")
            continue

        # Duplicate requirement id: multiset identity check.
        if req_id in seen_ids:
            defects.append(f"duplicate requirement id: {req_id}")
        seen_ids.add(req_id)
        file_ids.add(req_id)

        if req_id not in known_ids:
            defects.append(
                f"{req_id}: unknown requirement id -- not present in the validator's "
                "KNOWN_REQUIREMENT_IDS registry"
            )

        category = req.get("category")
        if category not in VALID_CATEGORIES:
            defects.append(f"{req_id}: invalid category '{category}'")

        if not isinstance(req.get("mandatory"), bool):
            defects.append(f"{req_id}: mandatory must be a boolean")

        if not isinstance(req.get("independentReviewRequired"), bool):
            defects.append(f"{req_id}: independentReviewRequired must be a boolean")

        if not _is_nonblank_str(req.get("scopeStatement")):
            defects.append(f"{req_id}: scopeStatement must be a nonblank string")
        elif category in EXHAUSTIVE_SCOPE_CATEGORIES:
            scope_lower = req["scopeStatement"].lower()
            if "all" not in scope_lower or "sugyot" not in scope_lower:
                defects.append(
                    f"{req_id}: scopeStatement for category '{category}' must express "
                    "exhaustive corpus scope (mention 'all' ... 'sugyot'), not an implicit "
                    "or sampled scope"
                )

        verification_mode = req.get("verificationMode")
        if verification_modes and verification_mode not in verification_modes:
            defects.append(
                f"{req_id}: verificationMode '{verification_mode}' not in declared "
                "verificationModes enum"
            )

        status = req.get("status")
        if status_enum and status not in status_enum:
            defects.append(f"{req_id}: status '{status}' not in declared statusEnum")
        req["_status_enum"] = status_enum

        repair_decision_kind = req.get("repairVsReconstruction")
        if repair_decision_kind not in VALID_REPAIR_DECISIONS:
            defects.append(
                f"{req_id}: repairVsReconstruction must be one of "
                f"{sorted(VALID_REPAIR_DECISIONS)}, got '{repair_decision_kind}'"
            )

        repair_decision = req.get("repairDecision")
        if repair_decision_kind in DECISIONS_REQUIRING_REPAIR_DECISION:
            if not isinstance(repair_decision, dict):
                defects.append(
                    f"{req_id}: repairVsReconstruction='{repair_decision_kind}' requires a "
                    "repairDecision object recording decision evidence, scope fingerprint, "
                    "and reopen history"
                )
            else:
                rd_missing = [f for f in REPAIR_DECISION_FIELDS if f not in repair_decision]
                if rd_missing:
                    defects.append(
                        f"{req_id}: repairDecision missing required field(s): "
                        f"{', '.join(rd_missing)}"
                    )
                else:
                    if not _is_nonblank_str(repair_decision.get("decidedAt")):
                        defects.append(f"{req_id}: repairDecision.decidedAt must be a nonblank string")
                    if not _is_nonblank_str(repair_decision.get("decisionEvidence")):
                        defects.append(
                            f"{req_id}: repairDecision.decisionEvidence must be a nonblank string"
                        )
                    if not _is_nonblank_str(repair_decision.get("contentScopeFingerprint")):
                        defects.append(
                            f"{req_id}: repairDecision.contentScopeFingerprint must be a "
                            "nonblank string"
                        )
                    if not isinstance(repair_decision.get("reopenHistory"), list):
                        defects.append(f"{req_id}: repairDecision.reopenHistory must be an array")
        else:
            if repair_decision is not None:
                defects.append(
                    f"{req_id}: repairVsReconstruction='undecided' must carry "
                    "repairDecision=null (no decision evidence exists yet)"
                )

        evidence_refs = req.get("evidenceRefs")
        if not isinstance(evidence_refs, list):
            defects.append(f"{req_id}: evidenceRefs must be an array")
            evidence_refs = []
        else:
            for ref_index, ref in enumerate(evidence_refs):
                if not _is_nonblank_str(ref):
                    defects.append(
                        f"{req_id}: evidenceRefs[{ref_index}] must be a nonblank string"
                    )

        # Typed evidence components: verificationMode mechanically dictates
        # which component types must be present, so "both" cannot be
        # satisfied by a single flat sourceClass/acceptanceCommand pair.
        components = req.get("evidenceComponents")
        if not isinstance(components, list) or not components:
            defects.append(f"{req_id}: evidenceComponents must be a non-empty array")
            components = []

        present_types = []
        for comp_index, component in enumerate(components):
            comp_where = f"evidenceComponents[{comp_index}]"
            if not isinstance(component, dict):
                defects.append(f"{req_id}: {comp_where} must be an object")
                continue
            comp_type = component.get("component")
            if comp_type not in VALID_COMPONENT_TYPES:
                defects.append(
                    f"{req_id}: {comp_where}.component '{comp_type}' is not a known "
                    f"component type ({sorted(VALID_COMPONENT_TYPES)})"
                )
                continue
            if comp_type in present_types:
                defects.append(f"{req_id}: duplicate evidenceComponents entry of type '{comp_type}'")
            present_types.append(comp_type)
            defects.extend(_validate_component(req, comp_where, component, comp_type))

        required_component_types = REQUIRED_COMPONENTS_BY_MODE.get(verification_mode, frozenset())
        missing_components = required_component_types - set(present_types)
        for missing_type in sorted(missing_components):
            defects.append(
                f"{req_id}: verificationMode '{verification_mode}' requires an "
                f"evidenceComponents entry of type '{missing_type}', found none"
            )
        extra_components = set(present_types) - required_component_types
        for extra_type in sorted(extra_components):
            defects.append(
                f"{req_id}: evidenceComponents has an unexpected '{extra_type}' component "
                f"not required by verificationMode '{verification_mode}'"
            )

        # Top-level status PASS requires every required component to also
        # be PASS -- a requirement cannot claim overall PASS while one of
        # its mandatory evidence components is unknown, missing, or FAIL
        # (contradictory evidence fails closed).
        if status == "PASS":
            component_statuses = {
                c.get("component"): c.get("status")
                for c in components
                if isinstance(c, dict)
            }
            for required_type in sorted(required_component_types):
                if component_statuses.get(required_type) != "PASS":
                    defects.append(
                        f"{req_id}: top-level status PASS requires evidenceComponents "
                        f"'{required_type}' to also be PASS, found "
                        f"'{component_statuses.get(required_type)}' (contradictory evidence)"
                    )

        req.pop("_status_enum", None)

    # Registry ids present in the file must equal the registry exactly on
    # the known-id side (a file id outside the registry is already flagged
    # above as "unknown requirement id"). A registry id entirely missing
    # from the file is also a defect: the registry and file must move
    # together.
    missing_from_file = known_ids - file_ids
    for missing_id in sorted(missing_from_file):
        defects.append(
            f"{missing_id}: present in validator registry but missing from contract file"
        )

    if defects:
        raise ContractError(defects)

    return requirements


def format_report(requirements):
    lines = []
    lines.append(f"{'id':<40} {'status':<14} {'mode':<13} {'mandatory':<9} repair")
    for req in sorted(requirements, key=lambda r: r.get("id", "")):
        lines.append(
            "{id:<40} {status:<14} {mode:<13} {mandatory:<9} {repair}".format(
                id=req.get("id", "?"),
                status=req.get("status", "?"),
                mode=req.get("verificationMode", "?"),
                mandatory=str(req.get("mandatory", "?")),
                repair=req.get("repairVsReconstruction", "?"),
            )
        )
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=pathlib.Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    try:
        data = load_contract(args.contract)
        requirements = validate_contract(data)
    except ContractError as exc:
        print(f"FAIL: {len(exc.defects)} defect(s) in {args.contract}", file=sys.stderr)
        for defect in exc.defects:
            print(f"  - {defect}", file=sys.stderr)
        return 1

    if not args.quiet:
        print(format_report(requirements))
        unverified = sum(1 for r in requirements if r.get("status") == "UNVERIFIED")
        print(
            f"\n{len(requirements)} requirement(s), {unverified} UNVERIFIED. "
            "Contract file is internally consistent. This does NOT certify "
            "Yoma as complete; it only validates the contract's own shape."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
