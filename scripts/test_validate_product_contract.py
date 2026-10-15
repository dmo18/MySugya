#!/usr/bin/env python3
"""test_validate_product_contract.py - tests for validate_product_contract.py.

Covers: the real contract file validates clean; the validator fails closed
on malformed JSON, a duplicate requirement id, an unknown requirement id,
an unknown enum value, a PASS/FAIL status with no evidence, a registry/file
id mismatch in either direction, and the typed evidenceComponents schema
added to correct the first-pass rejection: missing required component types
for a mode, mutating ci-workflow dispatch commands, repairVsReconstruction/
repairDecision consistency, incomplete review-record fields, missing
independentReviewer, non-exhaustive scopeStatement wording, unknown
component types, and contradictory PASS/component-status evidence.

Run: python3 scripts/test_validate_product_contract.py   (cwd repo root)
Exit 0 on success, 1 on failure.
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))
import validate_product_contract as vpc

FAILURES = []


def check(label, condition):
    if not condition:
        FAILURES.append(label)
        print(f"FAIL: {label}")
    else:
        print(f"ok: {label}")


def load_real_contract():
    with open(vpc.DEFAULT_CONTRACT, encoding="utf-8") as fh:
        return json.load(fh)


def minimal_component(component_type, **overrides):
    if component_type == "deterministic":
        base = {
            "component": "deterministic",
            "sourceClass": "repo-script",
            "acceptanceCommand": "npm test",
            "exactCommitBinding": None,
            "status": "UNVERIFIED",
            "evidenceRefs": [],
        }
    else:
        source_class = "review-record" if component_type == "semantic" else "external-source"
        fields = list(vpc.BASE_REVIEW_RECORD_FIELDS)
        if component_type == "external":
            fields += list(vpc.EXTERNAL_REVIEW_RECORD_FIELDS)
        base = {
            "component": component_type,
            "sourceClass": source_class,
            "acceptanceCommand": "manual review record",
            "exactCommitBinding": None,
            "status": "UNVERIFIED",
            "evidenceRefs": [],
            "reviewRecordRequiredFields": fields,
        }
    base.update(overrides)
    return base


def minimal_requirement(req_id, verification_mode="deterministic", components=None, **overrides):
    if components is None:
        if verification_mode == "both":
            components = [
                minimal_component("deterministic"),
                minimal_component("semantic"),
            ]
        elif verification_mode == "external":
            components = [minimal_component("external")]
        else:
            components = [minimal_component(verification_mode)]
    base = {
        "id": req_id,
        "category": "build",
        "mandatory": True,
        "verificationMode": verification_mode,
        "scopeStatement": "All build artifacts across all sugyot in the current corpus must build cleanly.",
        "independentReviewRequired": False,
        "evidenceComponents": components,
        "status": "UNVERIFIED",
        "repairVsReconstruction": "undecided",
        "repairDecision": None,
        "evidenceRefs": [],
    }
    base.update(overrides)
    return base


def minimal_contract(requirements):
    return {
        "statusEnum": ["UNVERIFIED", "PASS", "FAIL", "BLOCKED", "NOT_APPLICABLE"],
        "verificationModes": ["deterministic", "semantic", "both", "external"],
        "sourceClasses": [
            "repo-script",
            "repo-test",
            "ci-workflow",
            "review-record",
            "external-source",
        ],
        "requirements": requirements,
    }


def test_real_contract_validates_clean():
    data = load_real_contract()
    requirements = vpc.validate_contract(data)
    check(
        "real contract file validates with no defects",
        len(requirements) == len(data["requirements"]),
    )
    check(
        "real contract file ids exactly match validator registry",
        {r["id"] for r in requirements} == set(vpc.KNOWN_REQUIREMENT_IDS),
    )


def test_malformed_json_fails_closed(tmp_path):
    bad_path = tmp_path / "bad.json"
    bad_path.write_text("{not valid json", encoding="utf-8")
    threw = False
    try:
        vpc.load_contract(bad_path)
    except vpc.ContractError:
        threw = True
    check("malformed JSON raises ContractError", threw)


def test_duplicate_requirement_id_fails_closed():
    one = "YOMA-KNOWN-ONE"
    reqs = [minimal_requirement(one), minimal_requirement(one)]
    data = minimal_contract(reqs)
    threw = False
    try:
        vpc.validate_contract(data, known_ids=frozenset([one]))
    except vpc.ContractError as exc:
        threw = True
        check(
            "duplicate id defect message mentions the id",
            any(one in d and "duplicate" in d for d in exc.defects),
        )
    check("duplicate requirement id raises ContractError", threw)


def test_unknown_requirement_id_fails_closed():
    known = "YOMA-KNOWN-ONE"
    unknown = "YOMA-UNKNOWN-TWO"
    reqs = [minimal_requirement(known), minimal_requirement(unknown)]
    data = minimal_contract(reqs)
    threw = False
    try:
        vpc.validate_contract(data, known_ids=frozenset([known]))
    except vpc.ContractError as exc:
        threw = True
        check(
            "unknown id defect message mentions the unknown id",
            any(unknown in d for d in exc.defects),
        )
    check("unknown requirement id raises ContractError", threw)


def test_unknown_enum_value_fails_closed():
    known = "YOMA-KNOWN-ONE"
    reqs = [minimal_requirement(known, verificationMode="telepathic")]
    data = minimal_contract(reqs)
    threw = False
    try:
        vpc.validate_contract(data, known_ids=frozenset([known]))
    except vpc.ContractError as exc:
        threw = True
        check(
            "unknown verificationMode defect mentions the bad value",
            any("telepathic" in d for d in exc.defects),
        )
    check("unknown verificationMode value raises ContractError", threw)


def test_pass_status_without_evidence_fails_closed():
    known = "YOMA-KNOWN-ONE"
    component = minimal_component(
        "deterministic", status="PASS", evidenceRefs=[], exactCommitBinding=None
    )
    reqs = [minimal_requirement(known, components=[component])]
    data = minimal_contract(reqs)
    threw = False
    try:
        vpc.validate_contract(data, known_ids=frozenset([known]))
    except vpc.ContractError as exc:
        threw = True
        check(
            "evidence-free PASS defect is reported",
            any("evidence-free" in d for d in exc.defects),
        )
    check("PASS with no evidenceRefs/exactCommitBinding raises ContractError", threw)


def test_pass_status_with_evidence_passes():
    known = "YOMA-KNOWN-ONE"
    component = minimal_component(
        "deterministic",
        status="PASS",
        evidenceRefs=["docs/reports/data/some-evidence.json"],
        exactCommitBinding="deadbeef",
    )
    reqs = [
        minimal_requirement(
            known,
            components=[component],
            status="PASS",
        )
    ]
    data = minimal_contract(reqs)
    requirements = vpc.validate_contract(data, known_ids=frozenset([known]))
    check("PASS with evidence and commit binding validates clean", len(requirements) == 1)


def test_registry_file_mismatch_missing_from_file_fails_closed():
    known = "YOMA-KNOWN-ONE"
    other = "YOMA-KNOWN-TWO"
    reqs = [minimal_requirement(known)]
    data = minimal_contract(reqs)
    threw = False
    try:
        vpc.validate_contract(data, known_ids=frozenset([known, other]))
    except vpc.ContractError as exc:
        threw = True
        check(
            "missing-from-file defect mentions the missing id",
            any(other in d and "missing from contract file" in d for d in exc.defects),
        )
    check("registry id missing from file raises ContractError", threw)


def test_missing_required_field_fails_closed():
    known = "YOMA-KNOWN-ONE"
    req = minimal_requirement(known)
    del req["evidenceRefs"]
    data = minimal_contract([req])
    threw = False
    try:
        vpc.validate_contract(data, known_ids=frozenset([known]))
    except vpc.ContractError:
        threw = True
    check("requirement missing a required field raises ContractError", threw)


def test_cli_exit_codes(tmp_path):
    good_path = tmp_path / "good.json"
    known = "YOMA-KNOWN-ONE"
    good_path.write_text(
        json.dumps(minimal_contract([minimal_requirement(known)])), encoding="utf-8"
    )
    data = json.loads(good_path.read_text(encoding="utf-8"))
    requirements = vpc.validate_contract(data, known_ids=frozenset([known]))
    check("CLI-equivalent validation of a minimal valid contract succeeds", len(requirements) == 1)

    bad_path = tmp_path / "bad.json"
    bad_path.write_text("not json at all", encoding="utf-8")
    rc = vpc.main(["--contract", str(bad_path), "--quiet"])
    check("main() returns exit code 1 for malformed contract file", rc == 1)

    rc_real = vpc.main(["--contract", str(vpc.DEFAULT_CONTRACT), "--quiet"])
    check("main() returns exit code 0 for the real contract file", rc_real == 0)


# --- Defect #8 adversarial coverage: typed evidenceComponents schema ---


def test_both_mode_missing_semantic_component_fails_closed():
    known = "YOMA-KNOWN-ONE"
    reqs = [
        minimal_requirement(
            known,
            verification_mode="both",
            components=[minimal_component("deterministic")],
        )
    ]
    data = minimal_contract(reqs)
    threw = False
    try:
        vpc.validate_contract(data, known_ids=frozenset([known]))
    except vpc.ContractError as exc:
        threw = True
        check(
            "missing-semantic-component defect names the missing type",
            any(
                known in d and "'semantic'" in d and "requires an evidenceComponents" in d
                for d in exc.defects
            ),
        )
    check("both-mode requirement missing a semantic component raises ContractError", threw)


def test_both_mode_missing_deterministic_component_fails_closed():
    known = "YOMA-KNOWN-ONE"
    reqs = [
        minimal_requirement(
            known,
            verification_mode="both",
            components=[minimal_component("semantic")],
        )
    ]
    data = minimal_contract(reqs)
    threw = False
    try:
        vpc.validate_contract(data, known_ids=frozenset([known]))
    except vpc.ContractError as exc:
        threw = True
        check(
            "missing-deterministic-component defect names the missing type",
            any(
                known in d and "'deterministic'" in d and "requires an evidenceComponents" in d
                for d in exc.defects
            ),
        )
    check("both-mode requirement missing a deterministic component raises ContractError", threw)


def test_extra_unrequired_component_fails_closed():
    known = "YOMA-KNOWN-ONE"
    reqs = [
        minimal_requirement(
            known,
            verification_mode="deterministic",
            components=[minimal_component("deterministic"), minimal_component("semantic")],
        )
    ]
    data = minimal_contract(reqs)
    threw = False
    try:
        vpc.validate_contract(data, known_ids=frozenset([known]))
    except vpc.ContractError as exc:
        threw = True
        check(
            "unexpected-component defect names the extra type",
            any("unexpected 'semantic' component" in d for d in exc.defects),
        )
    check("deterministic-mode requirement with an extra semantic component raises ContractError", threw)


def test_duplicate_component_type_fails_closed():
    known = "YOMA-KNOWN-ONE"
    reqs = [
        minimal_requirement(
            known,
            verification_mode="deterministic",
            components=[minimal_component("deterministic"), minimal_component("deterministic")],
        )
    ]
    data = minimal_contract(reqs)
    threw = False
    try:
        vpc.validate_contract(data, known_ids=frozenset([known]))
    except vpc.ContractError as exc:
        threw = True
        check(
            "duplicate component type defect is reported",
            any("duplicate evidenceComponents entry" in d for d in exc.defects),
        )
    check("duplicate component type raises ContractError", threw)


def test_unknown_component_type_fails_closed():
    known = "YOMA-KNOWN-ONE"
    bad_component = minimal_component("deterministic")
    bad_component["component"] = "telepathic-sense"
    reqs = [minimal_requirement(known, components=[bad_component])]
    data = minimal_contract(reqs)
    threw = False
    try:
        vpc.validate_contract(data, known_ids=frozenset([known]))
    except vpc.ContractError as exc:
        threw = True
        check(
            "unknown component type defect names the bad value",
            any("telepathic-sense" in d and "not a known" in d for d in exc.defects),
        )
    check("unknown evidenceComponents component type raises ContractError", threw)


def test_ci_workflow_dispatch_command_fails_closed():
    known = "YOMA-KNOWN-ONE"
    component = minimal_component(
        "deterministic",
        sourceClass="ci-workflow",
        acceptanceCommand="gh workflow run rashi-browser-shards.yml",
    )
    reqs = [minimal_requirement(known, components=[component])]
    data = minimal_contract(reqs)
    threw = False
    try:
        vpc.validate_contract(data, known_ids=frozenset([known]))
    except vpc.ContractError as exc:
        threw = True
        check(
            "ci-workflow dispatch defect names the forbidden substring",
            any("mutating workflow-dispatch command" in d for d in exc.defects),
        )
    check("ci-workflow component with a dispatch command raises ContractError", threw)


def test_ci_workflow_read_only_command_passes():
    known = "YOMA-KNOWN-ONE"
    component = minimal_component(
        "deterministic",
        sourceClass="ci-workflow",
        acceptanceCommand="gh run view --workflow rashi-browser-shards.yml --json conclusion,jobs",
    )
    reqs = [minimal_requirement(known, components=[component])]
    data = minimal_contract(reqs)
    requirements = vpc.validate_contract(data, known_ids=frozenset([known]))
    check("ci-workflow component with a read-only command validates clean", len(requirements) == 1)


def test_repair_decision_required_but_missing_fails_closed():
    known = "YOMA-KNOWN-ONE"
    reqs = [
        minimal_requirement(known, repairVsReconstruction="repair", repairDecision=None)
    ]
    data = minimal_contract(reqs)
    threw = False
    try:
        vpc.validate_contract(data, known_ids=frozenset([known]))
    except vpc.ContractError as exc:
        threw = True
        check(
            "missing repairDecision defect is reported",
            any("requires a repairDecision object" in d for d in exc.defects),
        )
    check("repairVsReconstruction='repair' with no repairDecision raises ContractError", threw)


def test_repair_decision_incomplete_fails_closed():
    known = "YOMA-KNOWN-ONE"
    reqs = [
        minimal_requirement(
            known,
            repairVsReconstruction="reconstruct",
            repairDecision={"decidedAt": "2026-10-15"},
        )
    ]
    data = minimal_contract(reqs)
    threw = False
    try:
        vpc.validate_contract(data, known_ids=frozenset([known]))
    except vpc.ContractError as exc:
        threw = True
        check(
            "incomplete repairDecision defect lists missing fields",
            any("repairDecision missing required field(s)" in d for d in exc.defects),
        )
    check("incomplete repairDecision object raises ContractError", threw)


def test_undecided_with_nonnull_repair_decision_fails_closed():
    known = "YOMA-KNOWN-ONE"
    reqs = [
        minimal_requirement(
            known,
            repairVsReconstruction="undecided",
            repairDecision={
                "decidedAt": "2026-10-15",
                "decisionEvidence": "x",
                "contentScopeFingerprint": "y",
                "reopenHistory": [],
            },
        )
    ]
    data = minimal_contract(reqs)
    threw = False
    try:
        vpc.validate_contract(data, known_ids=frozenset([known]))
    except vpc.ContractError as exc:
        threw = True
        check(
            "undecided-with-repairDecision defect is reported",
            any("must carry repairDecision=null" in d for d in exc.defects),
        )
    check("undecided repairVsReconstruction with non-null repairDecision raises ContractError", threw)


def test_repair_decision_complete_passes():
    known = "YOMA-KNOWN-ONE"
    reqs = [
        minimal_requirement(
            known,
            repairVsReconstruction="repair",
            repairDecision={
                "decidedAt": "2026-10-15",
                "decisionEvidence": "failing integrity check on daf 19b",
                "contentScopeFingerprint": "yoma:19b:rashi",
                "reopenHistory": [],
            },
        )
    ]
    data = minimal_contract(reqs)
    requirements = vpc.validate_contract(data, known_ids=frozenset([known]))
    check("complete repairDecision object validates clean", len(requirements) == 1)


def test_incomplete_review_record_fields_fails_closed():
    known = "YOMA-KNOWN-ONE"
    component = minimal_component(
        "semantic", reviewRecordRequiredFields=["reviewer", "reviewedAt"]
    )
    reqs = [
        minimal_requirement(known, verification_mode="semantic", components=[component])
    ]
    data = minimal_contract(reqs)
    threw = False
    try:
        vpc.validate_contract(data, known_ids=frozenset([known]))
    except vpc.ContractError as exc:
        threw = True
        check(
            "incomplete reviewRecordRequiredFields defect lists missing fields",
            any("reviewRecordRequiredFields is missing required field(s)" in d for d in exc.defects),
        )
    check("semantic component with incomplete reviewRecordRequiredFields raises ContractError", threw)


def test_independent_review_required_but_missing_fails_closed():
    known = "YOMA-KNOWN-ONE"
    component = minimal_component("semantic")  # no independentReviewer
    reqs = [
        minimal_requirement(
            known,
            verification_mode="semantic",
            components=[component],
            independentReviewRequired=True,
        )
    ]
    data = minimal_contract(reqs)
    threw = False
    try:
        vpc.validate_contract(data, known_ids=frozenset([known]))
    except vpc.ContractError as exc:
        threw = True
        check(
            "missing independentReviewer defect is reported",
            any("independentReviewer" in d for d in exc.defects),
        )
    check(
        "independentReviewRequired=true with no independentReviewer field raises ContractError",
        threw,
    )


def test_independent_review_required_and_present_passes():
    known = "YOMA-KNOWN-ONE"
    fields = list(vpc.BASE_REVIEW_RECORD_FIELDS) + ["independentReviewer"]
    component = minimal_component("semantic", reviewRecordRequiredFields=fields)
    reqs = [
        minimal_requirement(
            known,
            verification_mode="semantic",
            components=[component],
            independentReviewRequired=True,
        )
    ]
    data = minimal_contract(reqs)
    requirements = vpc.validate_contract(data, known_ids=frozenset([known]))
    check("independentReviewRequired=true with independentReviewer present validates clean", len(requirements) == 1)


def test_non_exhaustive_scope_statement_fails_closed():
    known = "YOMA-KNOWN-ONE"
    reqs = [
        minimal_requirement(
            known,
            category="rashi",
            scopeStatement="Rashi entries in a sample of daf must pass integrity validation.",
        )
    ]
    data = minimal_contract(reqs)
    threw = False
    try:
        vpc.validate_contract(data, known_ids=frozenset([known]))
    except vpc.ContractError as exc:
        threw = True
        check(
            "non-exhaustive scopeStatement defect is reported",
            any("express exhaustive corpus scope" in d for d in exc.defects),
        )
    check("rashi-category requirement with a sampled scopeStatement raises ContractError", threw)


def test_exhaustive_scope_statement_passes():
    known = "YOMA-KNOWN-ONE"
    reqs = [
        minimal_requirement(
            known,
            category="translation",
            scopeStatement="All translation records across all sugyot in the current corpus must align with the source.",
        )
    ]
    data = minimal_contract(reqs)
    requirements = vpc.validate_contract(data, known_ids=frozenset([known]))
    check("exhaustive scopeStatement wording validates clean", len(requirements) == 1)


def test_external_component_missing_provenance_fields_fails_closed():
    known = "YOMA-KNOWN-ONE"
    component = minimal_component(
        "external", reviewRecordRequiredFields=list(vpc.BASE_REVIEW_RECORD_FIELDS)
    )
    reqs = [
        minimal_requirement(known, verification_mode="external", components=[component])
    ]
    data = minimal_contract(reqs)
    threw = False
    try:
        vpc.validate_contract(data, known_ids=frozenset([known]))
    except vpc.ContractError as exc:
        threw = True
        check(
            "external component missing provenance fields defect lists them",
            any(
                "edition" in d and "license" in d and "sourceProvenance" in d
                for d in exc.defects
            ),
        )
    check("external component with no edition/license/sourceProvenance raises ContractError", threw)


def test_contradictory_pass_with_non_pass_component_fails_closed():
    known = "YOMA-KNOWN-ONE"
    deterministic = minimal_component(
        "deterministic",
        status="PASS",
        evidenceRefs=["ref"],
        exactCommitBinding="deadbeef",
    )
    semantic = minimal_component("semantic", status="UNVERIFIED")
    reqs = [
        minimal_requirement(
            known,
            verification_mode="both",
            components=[deterministic, semantic],
            status="PASS",
        )
    ]
    data = minimal_contract(reqs)
    threw = False
    try:
        vpc.validate_contract(data, known_ids=frozenset([known]))
    except vpc.ContractError as exc:
        threw = True
        check(
            "contradictory PASS defect names the non-PASS component",
            any("contradictory evidence" in d for d in exc.defects),
        )
    check(
        "top-level PASS with a required component not itself PASS raises ContractError",
        threw,
    )


def test_both_components_pass_allows_top_level_pass():
    known = "YOMA-KNOWN-ONE"
    deterministic = minimal_component(
        "deterministic",
        status="PASS",
        evidenceRefs=["ref1"],
        exactCommitBinding="deadbeef",
    )
    semantic = minimal_component(
        "semantic",
        status="PASS",
        evidenceRefs=["ref2"],
        exactCommitBinding="deadbeef",
    )
    reqs = [
        minimal_requirement(
            known,
            verification_mode="both",
            components=[deterministic, semantic],
            status="PASS",
        )
    ]
    data = minimal_contract(reqs)
    requirements = vpc.validate_contract(data, known_ids=frozenset([known]))
    check(
        "top-level PASS with every required component also PASS validates clean",
        len(requirements) == 1,
    )


def main():
    import tempfile

    test_real_contract_validates_clean()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        test_malformed_json_fails_closed(tmp_path)
        test_cli_exit_codes(tmp_path)
    test_duplicate_requirement_id_fails_closed()
    test_unknown_requirement_id_fails_closed()
    test_unknown_enum_value_fails_closed()
    test_pass_status_without_evidence_fails_closed()
    test_pass_status_with_evidence_passes()
    test_registry_file_mismatch_missing_from_file_fails_closed()
    test_missing_required_field_fails_closed()

    test_both_mode_missing_semantic_component_fails_closed()
    test_both_mode_missing_deterministic_component_fails_closed()
    test_extra_unrequired_component_fails_closed()
    test_duplicate_component_type_fails_closed()
    test_unknown_component_type_fails_closed()
    test_ci_workflow_dispatch_command_fails_closed()
    test_ci_workflow_read_only_command_passes()
    test_repair_decision_required_but_missing_fails_closed()
    test_repair_decision_incomplete_fails_closed()
    test_undecided_with_nonnull_repair_decision_fails_closed()
    test_repair_decision_complete_passes()
    test_incomplete_review_record_fields_fails_closed()
    test_independent_review_required_but_missing_fails_closed()
    test_independent_review_required_and_present_passes()
    test_non_exhaustive_scope_statement_fails_closed()
    test_exhaustive_scope_statement_passes()
    test_external_component_missing_provenance_fields_fails_closed()
    test_contradictory_pass_with_non_pass_component_fails_closed()
    test_both_components_pass_allows_top_level_pass()

    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("\nAll tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
