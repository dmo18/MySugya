#!/usr/bin/env python3
"""
worker_pipeline.py - project-wide bounded-worker task pipeline.

One driver, six subcommands, all fed by scripts/worker_task_types.json:

  manifest   emit a machine-readable task manifest (stdout or --out FILE)
  preflight  environment + target safety checks for a manifest
  packet     task-type-specific work packet (context source of truth)
  prompt     compact worker prompt for the task
  verify     post-edit verification (--fast / --full)
  scope      general PR scope validation for the manifest's task type
  ci-check   CI enforcement: content PRs must carry a valid manifest

Usage examples:
  python3 scripts/worker_pipeline.py manifest --type rashi-repair --module yoma --range 61a
  python3 scripts/worker_pipeline.py manifest --type docs-tooling --out .worker-manifest.json
  python3 scripts/worker_pipeline.py preflight --manifest .worker-manifest.json [--dry-run]
  python3 scripts/worker_pipeline.py packet --manifest .worker-manifest.json
  python3 scripts/worker_pipeline.py prompt --manifest .worker-manifest.json
  python3 scripts/worker_pipeline.py verify --manifest .worker-manifest.json --fast|--full
  python3 scripts/worker_pipeline.py scope --manifest .worker-manifest.json [--base REF]
  python3 scripts/worker_pipeline.py ci-check --base origin/main

Rashi task types delegate to the existing, proven Rashi tooling
(rashi_preflight/make_rashi_work_packet/rashi_verify/check_rashi_pr_scope)
so nothing is duplicated or weakened. Offline except local git.
"""
import argparse
import fnmatch
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
REGISTRY = Path(__file__).parent / "worker_task_types.json"
MANIFEST_DEFAULT = REPO / ".worker-manifest.json"

sys.path.insert(0, str(Path(__file__).parent))
import module_resolver  # noqa: E402
import validate_enrichment_contracts as enrichment_contracts  # noqa: E402

# YROOT/YSCRIPTS/ACTIVE_MODULE/SCAFFOLD_BASELINE/REPETITION_BASELINE are
# rebound per invocation by set_active_module(), called once the requested
# module's key is known (from --module for `manifest`/`queue create`, or
# from the manifest's own "module" field for every command that reads an
# existing manifest - see load_manifest()). The Yoma values below are only
# a belt-and-suspenders default for the (never-exercised in normal
# operation) case where something reads these before set_active_module
# runs; every real command path calls it explicitly first, and an unknown
# or malformed module raises before any of these are touched - it is never
# silently substituted with Yoma.
YROOT = REPO / "modules" / "yoma"
YSCRIPTS = YROOT / "scripts"
SCAFFOLD_BASELINE = YSCRIPTS / "baselines" / "rashi_scaffold_debt.json"
REPETITION_BASELINE = YSCRIPTS / "allowlists" / "rashi_repetition_baseline.json"
ACTIVE_MODULE = None


MODULE_SEARCH_ROOT_ENV = "MYSUGYA_MODULE_SEARCH_ROOT"


def resolve_active_module(key):
    """Resolve and validate `key`'s module descriptor, or exit clearly.
    The single point every command uses to turn a requested module id
    into real paths - never falls back to another module on failure.

    Reads MYSUGYA_MODULE_SEARCH_ROOT to override the search root, exactly
    like module_resolver.resolve_module's own search_root parameter -
    unset in every normal invocation (interactive, npm script, CI), so
    production command paths always resolve against modules/ only. This
    exists for test/fixture callers (this file's own test suite, and the
    Phase 3 Step 5/6 empty-module onboarding end-to-end test) that need
    worker_pipeline.py itself - not just module_resolver directly - to
    resolve a synthetic descriptor outside modules/ without ever making
    that possible through an implicit default or a production code path."""
    search_root = os.environ.get(MODULE_SEARCH_ROOT_ENV)
    try:
        return module_resolver.resolve_module(key, search_root=search_root)
    except module_resolver.ModuleResolutionError as e:
        sys.exit(f"ERROR: cannot resolve module {key!r}: {e}")


def _physical_root(descriptor):
    """The module's real directory on disk. Honors MYSUGYA_MODULE_SEARCH_ROOT
    the same way resolve_active_module does - descriptor["paths"]["root"]
    is always the logical "modules/<key>" string (Step 2's validator
    requires it unconditionally, even for a fixture physically living
    elsewhere), so it is never safe to assume REPO / paths["root"] is the
    real location. When no override is set this returns exactly
    REPO / "modules" / key, byte-identical to the pre-Step-6 behavior."""
    search_root = os.environ.get(MODULE_SEARCH_ROOT_ENV)
    if search_root:
        return Path(search_root) / descriptor["key"]
    return REPO / "modules" / descriptor["key"]


def _physical_path(descriptor, field):
    """Resolve descriptor["paths"][field] (a logical, repo-relative
    "modules/<key>/..." value) to its real physical location."""
    logical_root = descriptor["paths"]["root"]
    logical_value = descriptor["paths"][field]
    suffix = logical_value[len(logical_root):].lstrip("/")
    root = _physical_root(descriptor)
    return root / suffix if suffix else root


def set_active_module(descriptor):
    """Rebind the module-scoped globals to the given resolved descriptor.
    Must be called before any code path touches YROOT/YSCRIPTS/
    ACTIVE_MODULE/SCAFFOLD_BASELINE/REPETITION_BASELINE for this
    invocation."""
    global YROOT, YSCRIPTS, ACTIVE_MODULE, SCAFFOLD_BASELINE, REPETITION_BASELINE
    ACTIVE_MODULE = descriptor
    YROOT = _physical_path(descriptor, "root")
    YSCRIPTS = _physical_path(descriptor, "scriptsRoot")
    SCAFFOLD_BASELINE = YSCRIPTS / "baselines" / "rashi_scaffold_debt.json"
    REPETITION_BASELINE = YSCRIPTS / "allowlists" / "rashi_repetition_baseline.json"


def all_content_prefixes():
    """Union of every registered module's asset-content prefixes, used
    only by cmd_ci_check (which runs before any single module is known -
    it is deciding whether ANY module's content changed at all). Not the
    same question as "does this changed file belong to the active
    module"; see json_scope_check and cmd_scope for that, which use the
    single resolved ACTIVE_MODULE instead."""
    prefixes = set()
    for key in module_resolver.list_modules():
        d = module_resolver.resolve_module(key)
        prefixes.add(d["paths"]["sourceAssetsRoot"] + "/")
        prefixes.add(d["paths"]["generatedAssetsRoot"] + "/")
    return tuple(sorted(prefixes))

RASHI_TYPES = {"rashi-repair", "rashi-reconstruction", "rashi-realignment",
               "placeholder-backfill", "rashi-structural-repair"}
STRUCTURAL_TYPE = "rashi-structural-repair"
REPAIR_TASK_TYPE = "rashi-boundary-translation-repair"
# Task types eligible for the source-relative citation-evidence policy (see
# drift_ok_for_type below). Deliberately excludes rashi-structural-repair,
# which already has its own, broader, unconditional line-level-safe allowance.
EVIDENCE_TIER_TYPES = ("rashi-reconstruction", "rashi-realignment")
ONE_ANCHOR_ATTESTATION_KEYS = (
    "onlyOneGenuineCitation",
    "citationTranslatedOnOwnLine",
    "noCitationInventedMovedOrDuplicated",
    "noSemanticUncertaintyRemains",
)
ZERO_ANCHOR_ATTESTATION_KEYS = (
    "everyRawLineRereadForCitations",
    "noTractateDafChapterVerseOrOtherCitationAnywhere",
    "noCitationInventedMovedOrDuplicated",
    "noSemanticUncertaintyRemains",
)


# ---------------- audited-sugya-enrichment-repair support ----------------
# The merged tail-enrichment audit, its derived repair queue, and the
# repair-progress tracking file are Yoma-specific artifacts today (like the
# Rashi tooling above); this section is deliberately hardcoded to their
# paths rather than generalized per-module, matching the existing pattern
# in this file (see all_content_prefixes/RASHI_TYPES comments).
AUDIT_RECORD_TASK_TYPE = "audited-sugya-enrichment-repair"
AUDIT_PATH = REPO / "docs" / "reports" / "data" / "yoma-tail-enrichment-audit.json"
REPAIR_QUEUE_PATH = REPO / "docs" / "reports" / "data" / "yoma-tail-enrichment-repair-queue.json"
REPAIR_PROGRESS_PATH = REPO / "docs" / "reports" / "data" / "yoma-tail-enrichment-repair-progress.json"


def _load_json_or(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_audit_records():
    data = _load_json_or(AUDIT_PATH, None)
    return {r["sugyaId"]: r for r in data["records"]} if data else {}


def load_queue_records():
    data = _load_json_or(REPAIR_QUEUE_PATH, None)
    return {r["sugyaId"]: r for r in data["records"]} if data else {}


def load_repair_progress():
    return _load_json_or(REPAIR_PROGRESS_PATH, {"progress": {}}).get("progress", {})


def validate_audit_record_ids(ids, targets):
    """Validate --audit-record-id values for audited-sugya-enrichment-repair.
    auditRecordIds is real manifest data naming which audit findings this
    PR repairs -- never a boolean authorization flag. Every id must: exist
    in the merged audit, belong to a manifest target daf, be present in the
    derived repair queue, not already be COMPLETE in the progress file, and
    carry an actual repair disposition (not VERIFIED). Returns (ok, errors)."""
    errors = []
    if not ids:
        return False, ["audited-sugya-enrichment-repair requires at least one --audit-record-id"]
    dup = sorted({x for x in ids if ids.count(x) > 1})
    if dup:
        errors.append(f"duplicate auditRecordIds in manifest: {dup} (each named audit record "
                      f"may appear at most once)")
    audit = load_audit_records()
    queue = load_queue_records()
    progress = load_repair_progress()
    for aid in ids:
        rec = audit.get(aid)
        if rec is None:
            errors.append(f"{aid}: not found in the merged audit "
                          f"({AUDIT_PATH.relative_to(REPO)})")
            continue
        if targets and rec["daf"] not in targets:
            errors.append(f"{aid}: belongs to daf {rec['daf']!r}, not manifest targets {targets}")
        if aid not in queue:
            errors.append(f"{aid}: not present in the repair queue "
                          f"({REPAIR_QUEUE_PATH.relative_to(REPO)})")
        if progress.get(aid, {}).get("status") == "COMPLETE":
            errors.append(f"{aid}: already marked COMPLETE in the repair-progress file; "
                          f"cannot be repaired again")
        if rec.get("overallDisposition") == "VERIFIED":
            errors.append(f"{aid}: overallDisposition is VERIFIED (no repair disposition; "
                          f"nothing to repair)")
    return (not errors), errors


def normalize_audit_pointer(ptr, daf):
    """Map a changed JSON pointer (as produced by json_leaf_diff against a
    daf's learning.json, e.g. '/sugyot/3/display/hint') onto the
    affectedFields vocabulary used by the frozen merged audit (e.g.
    'display.hint'). This IS the documented field-path normalization:

      1. A bare top-level '/summary' pointer maps to '<daf>.summary'.
      2. A leading '/sugyot/<n>/' prefix is stripped -- audit records are
         already scoped to one sugya by sugyaId.
      3. A numeric path segment is dropped; if it is not the LAST segment
         (a container of objects, e.g. visualizableElements[i].item), the
         preceding field gets an '[]' suffix; if it IS the last segment (a
         scalar array, e.g. topicTags[i]), no suffix is added, matching how
         the audit records bare 'topicTags' / 'requiresUnderstanding'.
      4. visualizableElements[*].{item,label,type,role,priority} all
         normalize onto 'visualizableElements[].name': the audit predates
         the item/name canonical-key migration and recorded the legacy key.
      5. Remaining segments are dot-joined.
    """
    if ptr == "/summary":
        # The frozen audit vocabulary uses the LITERAL template string
        # "<daf>.summary" in every record's affectedFields (see the audit
        # JSON itself) -- it is not per-daf-substituted. Returning the
        # literal template, not "%s.summary" % daf, is what lets this
        # normalized value actually be found in affectedFields.
        return "<daf>.summary"
    p = ptr
    if p.startswith("/sugyot/"):
        parts = p.split("/", 3)
        p = "/" + parts[3] if len(parts) > 3 else ""
    segs = [s for s in p.split("/") if s != ""]
    out = []
    for i, seg in enumerate(segs):
        if seg.isdigit():
            if out and i != len(segs) - 1:
                out[-1] = out[-1] + "[]"
            continue
        out.append(seg)
    normalized = ".".join(out)
    if normalized == "visualizableElements[]" or normalized.startswith("visualizableElements[]."):
        return "visualizableElements[].name"
    return normalized


# Maps an audit record's affectedFields vocabulary onto the enrichment-
# contract rule ids that mechanically cover that field, for audited-sugya-
# enrichment-repair's rule-scoped target-clean check. Fields with no
# mechanical rule (display.title, display.whats, learning.*, <daf>.summary,
# concepts.*) simply contribute no rules -- they are semantic-only or (for
# concepts) owned by a different task type entirely.
FIELD_TO_RULES = {
    "display.hint": ["hint_not_string", "hint_trailing_ellipsis", "hint_not_a_question"],
    "finalRuling": ["finalRuling_not_string", "finalRuling_trailing_ellipsis",
                    "finalRuling_unterminated", "finalRuling_equals_hint",
                    "finalRuling_prefix_of_hint"],
    "requiresUnderstanding": ["requiresUnderstanding_not_list", "requiresUnderstanding_prose",
                              "requiresUnderstanding_unresolved_id",
                              "requiresUnderstanding_self_reference"],
    "topicTags": ["topicTags_not_list", "topicTags_invalid_slug", "topicTags_duplicate"],
    "visualizableElements[].name": [
        "visualizableElements_not_list", "visualizableElements_bare_value",
        "visualizableElements_missing_item", "visualizableElements_legacy_key",
        "visualizableElements_unknown_key", "visualizableElements_field_not_string",
        "visualizableElements_priority_not_numeric",
    ],
}


def audit_affected_fields(ids):
    audit = load_audit_records()
    fields = set()
    for aid in ids:
        rec = audit.get(aid)
        if rec:
            fields.update(rec.get("affectedFields", []))
    return fields


# ---------------- enrichment-schema-migration support ----------------
# migrationKinds is real, repeatable manifest data (never a boolean
# authorization) naming which deterministic migration(s) a PR performs.
# Each kind owns an explicit, disjoint subset of enrichment-schema-
# migration's full jsonScope.mutable path set; a manifest may only touch
# the paths its declared kinds own.
MIGRATION_KINDS = ("requires-understanding", "visualizable-elements", "difficulty")
MIGRATION_KIND_PATHS = {
    "requires-understanding": ["sugyot[*].requiresUnderstanding[*]",
                               "sugyot[*].prerequisiteKnowledge[*]"],
    "visualizable-elements": ["sugyot[*].visualizableElements[*]"],
    "difficulty": ["sugyot[*].difficulty"],
}
# The enrichment-contract rule ids each migration kind is responsible for
# clearing (see cmd_verify's task-specific rule-scoped target-clean call).
MIGRATION_KIND_RULES = {
    "requires-understanding": [
        "requiresUnderstanding_not_list", "requiresUnderstanding_prose",
        "requiresUnderstanding_unresolved_id", "requiresUnderstanding_self_reference",
        "prerequisiteKnowledge_not_list", "prerequisiteKnowledge_blank",
        "prerequisiteKnowledge_contains_sugya_id", "prerequisiteKnowledge_duplicate",
    ],
    "visualizable-elements": [
        "visualizableElements_not_list", "visualizableElements_bare_value",
        "visualizableElements_missing_item", "visualizableElements_legacy_key",
        "visualizableElements_unknown_key", "visualizableElements_field_not_string",
        "visualizableElements_priority_not_numeric",
    ],
    "difficulty": ["difficulty_invalid_enum"],
}


def migration_kind_paths(kinds):
    paths = []
    for k in kinds:
        paths += MIGRATION_KIND_PATHS.get(k, [])
    return paths


# Maps a repair-queue record's migrationPrerequisites vocabulary (see
# generate_enrichment_repair_queue.py's MIGRATION_FIELDS) onto the
# enrichment-contract rule ids that must be clean, PER SUGYA, before that
# record's audited repair may proceed. Deliberately the SAME rule lists as
# MIGRATION_KIND_RULES (one migration, one set of rules, one vocabulary),
# just keyed by the queue's own prerequisite names instead of --migration-
# kind values, since the two vocabularies differ.
QUEUE_MIGRATION_PREREQ_RULES = {
    "requiresUnderstanding-prose-to-prerequisiteKnowledge":
        MIGRATION_KIND_RULES["requires-understanding"],
    "visualizableElements-shape-normalization": MIGRATION_KIND_RULES["visualizable-elements"],
    "difficulty-introductory-to-intro": MIGRATION_KIND_RULES["difficulty"],
}


def audit_repair_prerequisite_errors(audit_record_ids):
    """A SEPARATE prerequisite gate for audited-sugya-enrichment-repair,
    independent of semantic-field validation (task_specific_rule_scoped_
    targets' rule-scoped target-clean, which asks "is the repaired content
    itself correct?"). This gate instead asks "have the mechanical
    migrations this repair depends on already landed?" Before an
    audited-sugya-enrichment-repair manifest or preflight may succeed:

      - the corpus-wide legacy-concepts purge must be complete
        (legacy_concepts_present must be exactly zero across the WHOLE
        corpus, not merely baselined-and-ratcheted);
      - every named queue record's migrationPrerequisites (requires-
        understanding / visualizable-elements / difficulty, whichever the
        queue declares for THAT sugya) must already be clean for that
        exact sugya id.

    Unrelated ordinary debt elsewhere in the corpus, or on an unnamed
    sugya, or a migration prerequisite the queue does NOT declare for this
    record, must never block an otherwise-valid repair -- this function
    only checks exactly what the queue declares as a prerequisite for the
    named records, plus the one corpus-wide purge precondition. Returns a
    list of error strings (empty = prerequisites satisfied)."""
    if not audit_record_ids:
        return []
    data_path = REPO / ACTIVE_MODULE["paths"]["learningDataFile"]
    daf_content = enrichment_contracts.load_daf_content(data_path)
    violations, _detail, _occ = enrichment_contracts.collect_violations(daf_content)

    errors = []
    legacy_debt = violations.get("legacy_concepts_present", [])
    if legacy_debt:
        errors.append(f"corpus-wide legacy concepts purge is not complete: "
                      f"{len(legacy_debt)} sugya(s) still carry a concepts key "
                      f"(legacy_concepts_present must be exactly zero globally before any "
                      f"audited-sugya-enrichment-repair manifest/preflight may succeed)")

    queue = load_queue_records()
    for aid in audit_record_ids:
        rec = queue.get(aid)
        if not rec:
            continue  # validate_audit_record_ids already reports this separately
        for prereq in rec.get("migrationPrerequisites", []):
            rules = QUEUE_MIGRATION_PREREQ_RULES.get(prereq, [])
            dirty_rules = sorted(r for r in rules if aid in violations.get(r, []))
            if dirty_rules:
                errors.append(f"{aid}: migration prerequisite {prereq!r} is not yet satisfied "
                              f"for this sugya (still flagged by rule(s) {dirty_rules}); the "
                              f"required migration must land before this record's audited "
                              f"repair may proceed")
    return errors


def migration_kind_rules(kinds):
    rules = []
    for k in kinds:
        rules += MIGRATION_KIND_RULES.get(k, [])
    return rules


def _sugya_ids_for_daf_targets(daf_targets):
    ids = []
    for daf in daf_targets:
        fp = REPO / ACTIVE_MODULE["paths"]["learningDataDir"] / f"{daf}.learning.json"
        if fp.exists():
            ids += [s["id"] for s in json.loads(fp.read_text()).get("sugyot", [])]
    return ids


def task_specific_rule_scoped_targets(m):
    """(rule_ids, target_sugya_ids) for cmd_verify's task-specific
    rule-scoped target-clean check (via validate_enrichment_contracts.py
    --rules/--targets). Returns (None, None) when this task type has no
    such scoped check -- the corpus-wide ratchet still always runs
    separately (validate:offline:yoma), regardless.

      legacy-concepts-purge: only legacy_concepts_present, across every
        sugya on the manifest's target daf -- never blocked by unrelated
        hint/topicTag/etc debt on those same sugyot.
      enrichment-schema-migration: only the rules owned by the manifest's
        declared migrationKinds, across every sugya on the target daf.
      audited-sugya-enrichment-repair: only the rules mechanically covering
        the named audit records' affectedFields, and ONLY those exact
        sugya ids (auditRecordIds) -- unrelated legacy debt on other
        sugyot sharing the same daf is deliberately out of scope.
    """
    t = m["type"]
    if t == "legacy-concepts-purge":
        return ["legacy_concepts_present"], _sugya_ids_for_daf_targets(m.get("targets", []))
    if t == "enrichment-schema-migration":
        rules = migration_kind_rules(m.get("migrationKinds", []))
        return (rules or None), _sugya_ids_for_daf_targets(m.get("targets", []))
    if t == AUDIT_RECORD_TASK_TYPE:
        ids = m.get("auditRecordIds", [])
        fields = audit_affected_fields(ids)
        rules = sorted({r for f in fields for r in FIELD_TO_RULES.get(f, [])})
        return (rules or None), ids
    return None, None


def structure_authorized(m, spec):
    """True only for a structural-repair manifest carrying the explicit
    allowStructure authorization. No other task type can ever pass the
    --allow-structure flag to the Rashi scope validator."""
    return (m.get("type") == STRUCTURAL_TYPE
            and "allowStructure" in m.get("authorizations", []))
DRIFT_OVERRIDE_ENV = "WORKER_DRIFT_OVERRIDE"
# Lifecycle values a task type may declare. 'pr' passes produce a tracked
# change and therefore take a VERSION bump plus exactly one PR; 'read-only'
# passes must leave the tracked tree byte-identical and never bump VERSION,
# commit, or open a PR. Enforced by cmd_verify (see verify_read_only).
LIFECYCLES = ("pr", "read-only")
# Formerly a Yoma-only constant; cmd_ci_check now calls
# all_content_prefixes() instead, which unions every registered module's
# asset prefixes - it runs before any single module is known.


def sh(args, cwd=REPO, env=None):
    e = dict(os.environ, **(env or {}))
    return subprocess.run(args, capture_output=True, text=True, cwd=cwd, env=e)


def load_registry():
    return json.loads(REGISTRY.read_text())["taskTypes"]


def legal_authorizations(spec):
    """The full set of authorization flags a manifest may legally carry for
    this task type: every requiredAuthorizations entry, every
    optionalAuthorizations entry, every jsonScope.flagMutable key, and the
    declared jsonScope.structureFlag. A required authorization that is not
    also a legal --authorize value would be impossible to ever supply, so
    this single function is the source of truth for both --authorize
    validation (cmd_manifest) and the required-authorization check
    (cmd_preflight) -- they can never drift apart."""
    legal = set(spec.get("requiredAuthorizations", [])) | set(spec.get("optionalAuthorizations", []))
    scope = spec.get("jsonScope") or {}
    legal |= set(scope.get("flagMutable", {}).keys())
    if scope.get("structureFlag"):
        legal.add(scope["structureFlag"])
    return legal


def review_policy_of(spec):
    """A task type's review policy: 'conditional' (worker self-review plus
    the machine-checked auto-merge gate; escalation to escalationModel),
    'independent' (a second, independent Sonnet review must approve the PR
    before merge; no auto-merge gate exists), or 'none'."""
    if spec.get("reviewPolicy"):
        return spec["reviewPolicy"]
    return "independent" if spec.get("independentReviewRequired") else "none"


def lifecycle_of(spec):
    """A task type's lifecycle: 'pr' (default) or 'read-only'. Read-only
    types must end a pass with a byte-identical tracked tree: no VERSION
    bump, no commit, no PR. This is what makes audit-only/deployment-verify
    style contracts internally consistent instead of demanding a VERSION
    bump for a pass that is forbidden to change tracked files."""
    lc = spec.get("lifecycle", "pr")
    if lc not in LIFECYCLES:
        sys.exit(f"ERROR: task type declares unknown lifecycle {lc!r}")
    return lc


def load_manifest(path):
    m = json.loads(Path(path).read_text())
    types = load_registry()
    if m.get("type") not in types:
        sys.exit(f"ERROR: manifest type {m.get('type')!r} not in registry")
    # Single choke point: every command that reads an existing manifest
    # (preflight/packet/prompt/scope/verify/review/report, and ci-check
    # when a manifest is present) goes through load_manifest() as its
    # first step, so resolving the manifest's own module here covers all
    # of them without a separate call at each site. An unknown or
    # malformed module.module value fails here, clearly, before any
    # YROOT/YSCRIPTS-derived path is touched.
    set_active_module(resolve_active_module(m["module"]))
    return m, types[m["type"]]


ALLOWLIST_DRAIN_TYPES = ("rashi-reconstruction", "rashi-realignment")


def content_allowlist_entries(daf=None):
    ca_path = YSCRIPTS / "allowlists" / "rashi_content_allowlist.json"
    entries = json.loads(ca_path.read_text()).get("entries", [])
    return [e for e in entries if daf is None or e["daf"] == daf]


def scaffold_debt_entries(daf=None, path=None):
    """Entries of the locked scaffold-fabrication debt baseline (see
    modules/yoma/scripts/audit_rashi_scaffold.py), optionally filtered to one
    daf. Missing file means zero debt."""
    p = path or SCAFFOLD_BASELINE
    if not p.exists():
        return []
    entries = json.loads(p.read_text()).get("entries", [])
    return [e for e in entries if daf is None or e["daf"] == daf]


def repetition_baseline_entries(daf=None, path=None):
    """Entries of the locked within-daf skeleton-repetition baseline (see
    modules/yoma/scripts/validate_rashi_repetition.py), optionally filtered
    to one daf. Missing file means zero debt. Distinct from
    scaffold_debt_entries/content_allowlist_entries: entries here are keyed
    by (daf, skeleton) -> maxCount, not by vilnaLine, since repetition is a
    whole-daf pattern rather than a single-line defect."""
    p = path or REPETITION_BASELINE
    if not p.exists():
        return []
    entries = json.loads(p.read_text()).get("entries", [])
    return [e for e in entries if daf is None or e["daf"] == daf]


def scaffold_drain_status(m, daf, old_baseline, new_baseline, target_hits):
    """Pure post-edit enforcement for target-scoped scaffold-debt draining
    on rashi-reconstruction/rashi-realignment manifests. The scaffold debt
    baseline is a shrink-only ratchet: after the repair, the target daf must
    carry ZERO current scaffold hits and ZERO remaining baseline entries;
    the baseline diff may contain only removals, and only for the target;
    growth or hash changes anywhere are forbidden. Returns (ok, msgs)."""
    if m.get("type") not in ALLOWLIST_DRAIN_TYPES:
        return True, []
    ok, msgs = True, []
    old_map = {(e["daf"], e["vilnaLine"]): e.get("enHash") for e in old_baseline}
    new_map = {(e["daf"], e["vilnaLine"]): e.get("enHash") for e in new_baseline}
    if target_hits:
        ok = False
        lines = sorted(h["vilnaLine"] for h in target_hits)
        msgs.append(f"{len(target_hits)} scaffold hit(s) remain on {daf} "
                    f"(vilnaLine {lines}); rewrite them as direct translation")
    added = sorted(set(new_map) - set(old_map))
    if added:
        ok = False
        msgs.append(f"scaffold-debt baseline GREW: {added} (growth requires "
                    "explicit operator authorization, never a worker PR)")
    rehashed = sorted(k for k in set(new_map) & set(old_map)
                      if new_map[k] != old_map[k])
    if rehashed:
        ok = False
        msgs.append(f"scaffold-debt baseline entry rehashed: {rehashed} "
                    "(a baseline entry covers only its original text)")
    foreign_removed = sorted(k for k in set(old_map) - set(new_map) if k[0] != daf)
    if foreign_removed:
        ok = False
        msgs.append(f"scaffold-debt entries removed outside target daf: {foreign_removed}")
    remaining_target = sorted(k[1] for k in new_map if k[0] == daf)
    if remaining_target:
        ok = False
        msgs.append(f"scaffold-debt baseline still lists {daf} vilnaLine "
                    f"{remaining_target}; retire drained entries with "
                    "audit_rashi_scaffold.py --update-baseline")
    if ok:
        drained = sum(1 for k in set(old_map) - set(new_map) if k[0] == daf)
        msgs.append(f"scaffold debt drained for {daf} ({drained} entr(ies) "
                    "retired); no growth; unrelated entries unchanged")
    return ok, msgs


def repetition_drain_status(m, daf, old_baseline, new_baseline, target_violations):
    """Pure post-edit enforcement for target-scoped repetition-baseline
    draining on rashi-reconstruction/rashi-realignment manifests, mirroring
    scaffold_drain_status exactly. After the reconstruction, the target daf
    must carry ZERO current repetition violations (per
    validate_rashi_repetition.py) and ZERO remaining baseline entries; the
    baseline diff may contain only removals, and only for the target;
    growth or maxCount/skeleton changes anywhere are forbidden. This never
    touches count-mismatch debt -- that is a wholly separate, always-hard-
    blocked check in rashi_preflight.py with no drain path at all. Returns
    (ok, msgs)."""
    if m.get("type") not in ALLOWLIST_DRAIN_TYPES:
        return True, []
    ok, msgs = True, []
    old_map = {(e["daf"], e["skeleton"]): e.get("maxCount") for e in old_baseline}
    new_map = {(e["daf"], e["skeleton"]): e.get("maxCount") for e in new_baseline}
    if target_violations:
        ok = False
        msgs.append(f"{len(target_violations)} repetition violation(s) remain on {daf}; "
                    "rewrite the repeated skeleton lines as direct translation")
    added = sorted(set(new_map) - set(old_map))
    if added:
        ok = False
        msgs.append(f"repetition baseline GREW: {added} (growth requires "
                    "explicit operator authorization, never a worker PR)")
    changed = sorted(k for k in set(new_map) & set(old_map)
                      if new_map[k] != old_map[k])
    if changed:
        ok = False
        msgs.append(f"repetition-baseline entry modified: {changed} "
                    "(a baseline entry covers only its original maxCount)")
    foreign_removed = sorted(k for k in set(old_map) - set(new_map) if k[0] != daf)
    if foreign_removed:
        ok = False
        msgs.append(f"repetition-baseline entries removed outside target daf: {foreign_removed}")
    remaining_target = sorted(k for k in new_map if k[0] == daf)
    if remaining_target:
        ok = False
        msgs.append(f"repetition baseline still lists {daf}: {remaining_target}; "
                    "retire drained entries by removing them from "
                    "rashi_repetition_baseline.json")
    if ok:
        drained = sum(1 for k in set(old_map) - set(new_map) if k[0] == daf)
        msgs.append(f"repetition debt drained for {daf} ({drained} entr(ies) "
                    "retired); no growth; unrelated entries unchanged")
    return ok, msgs


def validate_allowlist_drain(m, daf):
    """Check whether m's allowlistDrain snapshot legitimately authorizes
    starting rashi-reconstruction/rashi-realignment on daf despite
    pre-existing content-allowlist debt for that exact daf. Returns
    (ok, note). This is target-scoped repair debt, not new tolerance: the
    snapshot must equal (not merely cover) daf's CURRENT allowlist
    entries, so it can neither hide unrelated debt nor claim entries that
    were added after the snapshot was taken. Ordinary task types (those
    outside ALLOWLIST_DRAIN_TYPES) can never use this authorization, and
    a manifest naming more than one target (or a target other than daf)
    is rejected outright, since the drain is single-daf by design."""
    if m["type"] not in ALLOWLIST_DRAIN_TYPES:
        return False, (f"allowlist-drain authorization only applies to "
                        f"{'/'.join(ALLOWLIST_DRAIN_TYPES)}, not {m['type']!r}")
    if len(m.get("targets", [])) != 1 or m["targets"][0] != daf:
        return False, "allowlist-drain authorization requires a single-target manifest matching the daf"
    drain = m.get("allowlistDrain")
    if not drain or not drain.get("authorized"):
        return False, "no allowlistDrain authorization on manifest"
    snapshot = drain.get("snapshot", [])
    foreign = [e for e in snapshot if e.get("daf") != daf]
    if foreign:
        return False, f"allowlistDrain snapshot contains entries outside target daf {daf!r}: {foreign}"
    snap_set = {(e["vilnaLine"], e["reason"]) for e in snapshot}
    current_set = {(e["vilnaLine"], e["reason"]) for e in content_allowlist_entries(daf)}
    if current_set != snap_set:
        return False, (f"allowlistDrain snapshot does not match {daf}'s current allowlist entries "
                        f"(snapshot {sorted(snap_set)} vs current {sorted(current_set)}); "
                        "regenerate the manifest so the snapshot matches exactly")
    return True, (f"allowlist-drain authorized: {len(snap_set)} pre-existing "
                  f"entr{'y' if len(snap_set) == 1 else 'ies'} for {daf} accepted as repair debt, "
                  "not new tolerance")


def validate_repetition_drain(m, daf):
    """Check whether m's repetitionDrain snapshot legitimately authorizes
    starting rashi-reconstruction/rashi-realignment on daf despite
    pre-existing repetition-baseline debt for that exact daf. Mirrors
    validate_allowlist_drain, with one deliberate tightening beyond it: the
    daf's drift profile must still recommend rashi-reconstruction. This
    authorization is scoped to a specific, already-drift-approved remedy
    (a FABRICATION-SUSPECT or SHIFTED daf whose recommended fix is already
    full reconstruction), not a generic override -- no new drift-override
    mechanism is introduced, and WORKER_DRIFT_OVERRIDE/authorizeDriftOverride
    are untouched by this function entirely. This is target-scoped repair
    debt a full reconstruction is expected to eliminate by construction
    (the whole daf is rewritten), not new tolerance: the snapshot must
    equal (not merely cover) daf's CURRENT repetition-baseline entries.
    Ordinary task types (those outside ALLOWLIST_DRAIN_TYPES) can never use
    this authorization, and a manifest naming more than one target is
    rejected outright. This authorization never applies to count-mismatch
    debt, which has no drain path anywhere in the pipeline and stays a hard
    block in rashi_preflight.py regardless of task type or manifest
    content."""
    if m["type"] not in ALLOWLIST_DRAIN_TYPES:
        return False, (f"repetition-drain authorization only applies to "
                        f"{'/'.join(ALLOWLIST_DRAIN_TYPES)}, not {m['type']!r}")
    if len(m.get("targets", [])) != 1 or m["targets"][0] != daf:
        return False, "repetition-drain authorization requires a single-target manifest matching the daf"
    drain = m.get("repetitionDrain")
    if not drain:
        return False, ("no repetitionDrain snapshot on manifest; regenerate the manifest "
                        "(worker_pipeline.py manifest auto-snapshots current repetition-"
                        "baseline debt for single-target reconstruction/realignment manifests)")
    snapshot = drain.get("snapshot", [])
    foreign = [e for e in snapshot if e.get("daf") != daf]
    if foreign:
        return False, f"repetitionDrain snapshot contains entries outside target daf {daf!r}: {foreign}"
    snap_set = {(e["daf"], e["skeleton"], e["maxCount"]) for e in snapshot}
    current_set = {(e["daf"], e["skeleton"], e["maxCount"]) for e in repetition_baseline_entries(daf)}
    if current_set != snap_set:
        return False, (f"repetitionDrain snapshot does not match {daf}'s current repetition-baseline "
                        f"entries (snapshot {sorted(snap_set)} vs current {sorted(current_set)}); "
                        "regenerate the manifest so the snapshot matches exactly")
    sys.path.insert(0, str(YSCRIPTS))
    import audit_rashi_semantic as ars
    profile = ars.profile_daf(daf)
    recommended = profile.get("recommendedTaskType") if profile else None
    if recommended != "rashi-reconstruction":
        return False, (f"{daf}'s drift profile does not recommend rashi-reconstruction "
                        f"(recommendedTaskType={recommended!r}); repetition-drain is only "
                        "authorized when reconstruction is already the drift-approved "
                        "remedy, never as a generic override")
    return True, (f"repetition-drain authorized: {len(snap_set)} pre-existing skeleton "
                  f"entr{'y' if len(snap_set) == 1 else 'ies'} for {daf} accepted as repair "
                  "debt the reconstruction must eliminate, not new tolerance "
                  f"(drift profile {profile['classification']} recommends "
                  f"{profile['recommendedTaskType']})")


def allowlist_drain_status(m, old_entries, new_entries, stale_pairs):
    """Pure post-edit check of whether a manifest's allowlistDrain snapshot
    was actually eliminated by this PR's content fix. old_entries/new_entries
    are the full content-allowlist entry lists before/after this PR's diff;
    stale_pairs is the set of (daf, vilnaLine) the content validator
    currently reports as no longer violating (validate_rashi_content.py
    --json's "stale" list). Returns (ok, messages); ok is True with no
    messages when the manifest carries no drain authorization (nothing to
    enforce), so callers can skip printing when there is nothing to say.

    The snapshot is repair debt, not an exemption: this never silently
    passes just because the snapshot was accepted at preflight. Every
    snapshotted entry must end up either genuinely removed, or (if still
    present) explicitly reported stale by the validator so the caller can
    at least distinguish "cleanup omission" from "content still violates,
    escalate" in the failure message. A stale-but-not-yet-removed entry
    still fails, same as a genuinely-still-needed one -- both require a
    human decision, not an auto-merge."""
    drain = m.get("allowlistDrain")
    if not (drain and drain.get("authorized") and m.get("type") in ALLOWLIST_DRAIN_TYPES
            and len(m.get("targets", [])) == 1):
        return True, []
    daf = m["targets"][0]
    snap_set = {(e["vilnaLine"], e["reason"]) for e in drain.get("snapshot", []) if e["daf"] == daf}
    current_set = {(e["vilnaLine"], e["reason"]) for e in new_entries if e["daf"] == daf}
    growth = current_set - snap_set
    remaining = current_set & snap_set
    old_other = [e for e in old_entries if e["daf"] != daf]
    new_other = [e for e in new_entries if e["daf"] != daf]
    ok = True
    msgs = []
    if growth:
        ok = False
        msgs.append(f"new/unauthorized allowlist entries for {daf}: {sorted(growth)}")
    if old_other != new_other:
        ok = False
        msgs.append("unrelated allowlist entries (other daf) changed")
    if remaining:
        still_needed = sorted(vl for vl, _ in remaining if (daf, vl) not in stale_pairs)
        stale_not_removed = sorted(vl for vl, _ in remaining if (daf, vl) in stale_pairs)
        if still_needed:
            ok = False
            msgs.append(f"snapshotted entries still needed (content genuinely still violates) "
                        f"for {daf} L{still_needed}: repair gap, escalate")
        if stale_not_removed:
            ok = False
            msgs.append(f"validator reports these snapshotted entries stale but they were not "
                        f"removed for {daf} L{stale_not_removed}")
    if ok:
        msgs.append(f"all {len(snap_set)} snapshotted entr{'y' if len(snap_set) == 1 else 'ies'} "
                    f"for {daf} drained; no growth; unrelated entries unchanged")
    return ok, msgs


def _daf_sort_key(d):
    mm = re.match(r"(\d+)([ab])", d)
    return (int(mm.group(1)), mm.group(2))


def all_daf_ids():
    """The EXACT full daf set for the currently active module, derived from
    its talmuddev source directory -- the descriptor's ground truth for
    which daf exist. Never hardcoded, never guessed, always module-scoped
    (YROOT is rebound per invocation by set_active_module). Used both by
    expand_range's open-ended ranges and by the corpus-wide
    legacy-concepts-purge manifest's target derivation."""
    td = YROOT / "assets" / "talmuddev"
    return sorted((p.name.replace(".json", "") for p in td.glob("*.json")), key=_daf_sort_key)


def expand_range(spec):
    if not spec:
        return []
    m = re.match(r"^(\d+[ab])(?:-(\d+[ab]))?$", spec)
    if not m:
        sys.exit(f"ERROR: malformed range {spec!r}")
    if not m.group(2):
        return [m.group(1)]
    all_daf = all_daf_ids()
    lo, hi = _daf_sort_key(m.group(1)), _daf_sort_key(m.group(2))
    out = [d for d in all_daf if lo <= _daf_sort_key(d) <= hi]
    if not out:
        sys.exit(f"ERROR: range {spec!r} matches no daf")
    return out


def file_allowed(path, spec, targets, module):
    """A changed file is in scope only if it matches the allowed set.
    The forbiddenFiles list is documentation for prompts; enforcement is
    allowlist-style (anything not explicitly allowed is a violation).

    Each allowedFiles pattern may carry a <module> placeholder (templated
    the same way <daf> already is): substituted with the manifest's own
    module before matching, so a fixture-targeted manifest's allowedFiles
    resolve to fixture paths only, and a Yoma-targeted manifest's resolve
    to Yoma paths only - never the other way around, and never both."""
    for pat in spec.get("allowedFiles", []):
        pat = pat.replace("<module>", module)
        if "<daf>" in pat:
            if any(fnmatch.fnmatch(path, pat.replace("<daf>", d)) for d in targets):
                return True
            continue
        if fnmatch.fnmatch(path, pat) or (pat.endswith("/*") and path.startswith(pat[:-1])):
            return True
    return False


def pattern_to_regex(pat, allow_children=True):
    """'sugyot[*].learning.takeaway.text' -> compiled regex matching the
    JSON pointer '/sugyot/<n>/learning/takeaway/text'. With allow_children
    (the default, used for mutable/flagMutable patterns) it also matches
    anything below that pointer. With allow_children=False (used for
    deleteOnly patterns) it matches the exact pointer only -- a deleteOnly
    authorization never extends to a child of the deleted path, since the
    only legal operation on it is whole-key removal."""
    body = "/".join(seg.replace("[*]", "/\\d+") for seg in pat.split("."))
    suffix = "(/.*)?" if allow_children else ""
    return re.compile("^/" + body + suffix + "$")


def json_leaf_diff(old, new, ptr, leaves, structure):
    """Collect changed-leaf JSON pointers (with change kind: added/removed/
    changed) and array structure changes."""
    if isinstance(old, dict) and isinstance(new, dict):
        for k in sorted(set(old) | set(new)):
            if k not in new:
                leaves.append({"ptr": f"{ptr}/{k}", "kind": "removed"})
            elif k not in old:
                leaves.append({"ptr": f"{ptr}/{k}", "kind": "added"})
            else:
                json_leaf_diff(old[k], new[k], f"{ptr}/{k}", leaves, structure)
    elif isinstance(old, list) and isinstance(new, list):
        if len(old) != len(new):
            structure.append(f"{ptr} array length {len(old)} -> {len(new)}")
            return
        for i, (a, b) in enumerate(zip(old, new)):
            json_leaf_diff(a, b, f"{ptr}/{i}", leaves, structure)
    else:
        if old != new:
            leaves.append({"ptr": ptr, "kind": "changed"})


def json_scope_check(mb, changed, m, spec, errors):
    """Generic per-task JSON scope engine, driven by the registry's
    jsonScope: {mutable: [path patterns], flagMutable: {flag: [patterns]},
    structureFlag}. Reports exact JSON-pointer violations. Array entry
    add/remove/reorder surfaces as a structure error unless the manifest
    carries the structure flag."""
    scope = spec.get("jsonScope")
    if not scope:
        return
    flags = set(m.get("authorizations", []))
    mutable_patterns = scope.get("mutable", [])
    if m["type"] == "enrichment-schema-migration":
        # migrationKinds narrows the generic jsonScope.mutable set (which
        # names every path the task type could EVER touch) down to only the
        # paths this specific manifest's declared kinds own. A manifest
        # with migrationKinds=["difficulty"] may not touch
        # visualizableElements, even though the registry's jsonScope says
        # the task TYPE can.
        mutable_patterns = migration_kind_paths(m.get("migrationKinds", []))
    allowed_rx = [pattern_to_regex(p) for p in mutable_patterns]
    for flag, pats in scope.get("flagMutable", {}).items():
        if flag in flags:
            allowed_rx += [pattern_to_regex(p) for p in pats]
    # deleteOnly patterns are matched EXACTLY (allow_children=False): the
    # only legal operation is deleting the whole key, never touching a
    # child, so a deleteOnly path is deliberately never treated as a prefix
    # the way mutable/flagMutable paths are.
    delete_only_rx = [pattern_to_regex(p, allow_children=False) for p in scope.get("deleteOnly", [])]
    structure_ok = scope.get("structureFlag") and scope["structureFlag"] in flags
    targets = set(m.get("targets", []))
    # audited-sugya-enrichment-repair: every changed '/sugyot/<n>/...'
    # pointer must resolve to the EXACT SAME sugya id at that array index in
    # both base and proposed JSON, that exact sugya id must be named in
    # manifest.auditRecordIds, and the normalized field path must appear in
    # THAT record's own affectedFields -- never merely "some named record's
    # affectedFields contains this field" (a per-sugya union would let one
    # named record authorize a field on an unnamed sugya, or on a different
    # named record, purely because they happen to share a field name). A
    # daf-scoped pointer with no sugya index (only '/summary' today) is
    # authorized when ANY named record for that same daf lists the
    # normalized field.
    is_audit_repair = m["type"] == AUDIT_RECORD_TASK_TYPE
    audit_by_id = load_audit_records() if is_audit_repair else {}
    named_ids = list(m.get("auditRecordIds", [])) if is_audit_repair else []
    named_id_set = set(named_ids)
    daf_scoped_fields = {}
    if is_audit_repair:
        for aid in named_ids:
            rec = audit_by_id.get(aid)
            if rec:
                daf_scoped_fields.setdefault(rec["daf"], set()).update(
                    f for f in rec.get("affectedFields", []) if f == "<daf>.summary")

    for p in changed:
        if not (p.startswith(ACTIVE_MODULE["paths"]["learningDataDir"] + "/")
                and p.endswith(".learning.json")):
            continue
        daf = p.split("/")[-1].replace(".learning.json", "")
        if daf not in targets:
            errors.append(f"{p}: daf {daf} is not in the manifest targets {sorted(targets)} (no cross-daf edits)")
            continue
        r = sh(["git", "show", f"{mb}:{p}"])
        if r.returncode != 0:
            errors.append(f"{p}: does not exist at base; new files require structure authorization")
            continue
        old, new = json.loads(r.stdout), json.loads((REPO / p).read_text())
        leaves, structure = [], []
        json_leaf_diff(old, new, "", leaves, structure)
        for s in structure:
            ptr = s.split(" array length")[0]
            # A structure change entirely under an authorized mutable path
            # (e.g. growing a flag-authorized container array) is permitted;
            # anything else needs the explicit structure flag.
            if any(rx.match(ptr) for rx in allowed_rx):
                continue
            if not structure_ok:
                errors.append(f"{p}: {s} (requires --authorize {scope.get('structureFlag', 'allowStructure')})")
        for leaf in leaves:
            ptr, kind = leaf["ptr"], leaf["kind"]
            if any(rx.match(ptr) for rx in delete_only_rx):
                if kind == "removed":
                    continue  # exactly the authorized deletion: key existed, now gone
                if kind == "added":
                    errors.append(f"{p}: {ptr} added (this path is deleteOnly; it may never "
                                  f"be created)")
                else:
                    errors.append(f"{p}: {ptr} changed instead of deleted (this path is "
                                  f"deleteOnly; it may only be removed entirely, never "
                                  f"replaced with null/an empty container/any other value, "
                                  f"and its children may never be edited)")
                continue
            if not any(rx.match(ptr) for rx in allowed_rx):
                errors.append(f"{p}: {ptr} changed (outside the {m['type']} mutable path set)")
                continue
            if is_audit_repair:
                sidx = sugya_index_from_ptr(ptr)
                if sidx is not None:
                    old_sid = sugya_id_at_index(old, sidx)
                    new_sid = sugya_id_at_index(new, sidx)
                    if old_sid != new_sid:
                        errors.append(f"{p}: {ptr}: sugya id at index {sidx} changed "
                                      f"({old_sid!r} -> {new_sid!r}); editing enrichment must "
                                      f"never change a sugya id")
                        continue
                    sid = new_sid
                    if sid is None:
                        errors.append(f"{p}: {ptr}: sugya index {sidx} does not resolve to a "
                                      f"sugya id in either base or proposed JSON")
                        continue
                    if sid not in named_id_set:
                        errors.append(f"{p}: {ptr}: touches sugya {sid!r}, which is not named "
                                      f"in manifest.auditRecordIds {sorted(named_id_set)} "
                                      f"(another named record on the same daf may never "
                                      f"authorize a change on an unnamed sugya)")
                        continue
                    rec = audit_by_id.get(sid)
                    if rec is None:
                        errors.append(f"{p}: {ptr}: sugya {sid!r} is named in "
                                      f"auditRecordIds but has no audit record")
                        continue
                    normalized = normalize_audit_pointer(ptr, daf)
                    if normalized not in rec.get("affectedFields", []):
                        errors.append(f"{p}: {ptr} (normalized {normalized!r}) is not an "
                                      f"affectedFields entry of the exact named audit record "
                                      f"for {sid!r} (it may not be authorized merely because a "
                                      f"DIFFERENT named record lists it)")
                else:
                    normalized = normalize_audit_pointer(ptr, daf)
                    if normalized not in daf_scoped_fields.get(daf, set()):
                        errors.append(f"{p}: {ptr} (normalized {normalized!r}) is not an "
                                      f"affectedFields entry of any named audit record for "
                                      f"daf {daf!r}")


def sugya_index_from_ptr(ptr):
    """The integer array index for a '/sugyot/<n>/...' JSON pointer, or
    None when ptr is not scoped to exactly one sugya (e.g. the top-level
    '/summary' pointer, which is daf-scoped, not sugya-scoped)."""
    if not ptr.startswith("/sugyot/"):
        return None
    parts = ptr.split("/")
    if len(parts) < 3 or not parts[2].isdigit():
        return None
    return int(parts[2])


def sugya_id_at_index(doc, index):
    """The sugyaId at the given array index of doc['sugyot'], or None if
    the index is out of range or the document carries no such array. Used
    to prove a changed '/sugyot/<n>/...' pointer's sugya identity did not
    shift between base and proposed JSON before any field on it can be
    authorized."""
    sugyot = doc.get("sugyot") or []
    if 0 <= index < len(sugyot):
        return sugyot[index].get("id")
    return None


def is_source_protected_pointer(ptr):
    """True for a JSON pointer inside a source-of-truth or Rashi/
    argumentFlow/sourceRefs field, used by sourcesMustBeUnchanged
    enforcement (verify_sources_unchanged). Deliberately INDEPENDENT of any
    task type's jsonScope contract: this is a second, defense-in-depth
    proof, not a re-derivation of the same allowlist logic."""
    segs = [s for s in ptr.split("/") if s and not s.isdigit()]
    joined = "/" + "/".join(segs)
    return (joined.startswith("/rashiTranslations")
            or joined.startswith("/sugyot/lines")
            or joined.startswith("/sugyot/argumentFlow")
            or "/sourceRefs" in joined)


def verify_sources_unchanged(spec, changed, mb):
    """Independent, defense-in-depth proof that a sourcesMustBeUnchanged
    task type touched no source-of-truth file (source_store, talmuddev,
    daftexts) and no Rashi/argumentFlow/sourceRefs/Gemara-source-line field
    inside any changed learning JSON, regardless of whether jsonScope's
    mutable-path allowlist would separately have caught it. Returns
    (ok, messages). A no-op (True, []) when the task type does not declare
    sourcesMustBeUnchanged."""
    if not spec.get("sourcesMustBeUnchanged"):
        return True, []
    problems = []
    paths = ACTIVE_MODULE["paths"]
    protected_file_prefixes = (paths["sourceAssetsRoot"] + "/talmuddev/",
                               paths["sourceAssetsRoot"] + "/daftexts/")
    source_store = paths.get("sourceStore")
    for p in changed:
        if p.startswith(protected_file_prefixes):
            problems.append(f"{p}: source asset changed")
        elif source_store and p == source_store:
            problems.append(f"{p}: source_store file changed")

    learning_dir = paths["learningDataDir"]
    for p in changed:
        if not (p.startswith(learning_dir + "/") and p.endswith(".learning.json")):
            continue
        r = sh(["git", "show", f"{mb}:{p}"])
        if r.returncode != 0:
            continue  # new/missing-at-base file: file-level scope already flags this
        old, new = json.loads(r.stdout), json.loads((REPO / p).read_text())
        leaves, structure = [], []
        json_leaf_diff(old, new, "", leaves, structure)
        for leaf in leaves:
            if is_source_protected_pointer(leaf["ptr"]):
                problems.append(f"{p}: {leaf['ptr']} changed (source/Rashi/argumentFlow/"
                                f"sourceRefs fields may never change)")
        for s in structure:
            ptr = s.split(" array length")[0]
            if is_source_protected_pointer(ptr):
                problems.append(f"{p}: {s} (structural change to a protected source field)")
    return (not problems), problems


def verify_concepts_purge(m, mb, learning_dir):
    """legacy-concepts-purge-specific post-edit proof: the number of sugyot
    that carried a `concepts` key at the manifest's base commit must equal
    the number of deletions in this PR's diff, exactly; zero `concepts`
    keys may remain across the manifest's targets. This is independent,
    exact-count defense-in-depth on top of json_scope_check's deleteOnly
    enforcement (which already proves no OTHER field changed). Returns
    (ok, messages)."""
    if m["type"] != "legacy-concepts-purge":
        return True, []
    problems, msgs = [], []
    before_count = deleted_count = remaining_count = 0
    for daf in m["targets"]:
        rel = f"{learning_dir}/{daf}.learning.json"
        r = sh(["git", "show", f"{mb}:{rel}"])
        if r.returncode != 0:
            continue
        old = json.loads(r.stdout)
        new_path = REPO / rel
        if not new_path.exists():
            problems.append(f"{rel}: missing after purge")
            continue
        new = json.loads(new_path.read_text())
        old_sugyot = {s["id"]: s for s in old.get("sugyot", [])}
        new_sugyot = {s["id"]: s for s in new.get("sugyot", [])}
        for sid, old_s in old_sugyot.items():
            had = "concepts" in old_s
            before_count += 1 if had else 0
            still_has = "concepts" in new_sugyot.get(sid, {})
            if had and not still_has:
                deleted_count += 1
            if still_has:
                remaining_count += 1
                problems.append(f"{rel}: {sid} still carries a concepts key")
    msgs.append(f"concepts before: {before_count}, deleted: {deleted_count}, "
               f"remaining: {remaining_count}")
    if before_count != deleted_count:
        problems.append(f"deleted count {deleted_count} does not exactly match the base-commit "
                        f"concepts inventory {before_count} across manifest targets")
    return (not problems), (msgs + problems)


_BOUNDARY_RATCHET_CACHE = {}


def _load_boundary_ratchet():
    """Dynamically load modules/<module>/scripts/boundary_fingerprint_ratchet.py
    for the currently active module. Not a static top-of-file import: YSCRIPTS
    is rebound per invocation by set_active_module(), so the file to load is
    only known once a module is active. None if the active module has no such
    file (only Yoma does today)."""
    path = YSCRIPTS / "boundary_fingerprint_ratchet.py"
    if not path.exists():
        return None
    key = str(path)
    if key not in _BOUNDARY_RATCHET_CACHE:
        # The module's own internal `from validate_rashi_review_records import
        # ...` needs YSCRIPTS on sys.path to resolve, exactly as it does when
        # check_rashi_pr_scope.py imports it as a same-directory sibling.
        if str(YSCRIPTS) not in sys.path:
            sys.path.insert(0, str(YSCRIPTS))
        spec = importlib.util.spec_from_file_location(
            f"boundary_fingerprint_ratchet_{ACTIVE_MODULE['key']}", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _BOUNDARY_RATCHET_CACHE[key] = mod
    return _BOUNDARY_RATCHET_CACHE[key]


def _check_boundary_registry_ratchet(rel, old_entries, new_entries, mb, errors, policy):
    bfr = _load_boundary_ratchet()
    old_by_id, new_by_id, added, _removed, rehashed = bfr.diff_registry_entries(old_entries, new_entries)
    for daf, vl in added:
        errors.append(f"{rel}: entries entry ADDED (policy {policy}): {daf} L{vl}")
    if len(rehashed) > 1:
        errors.append(f"{rel}: {len(rehashed)} registry entries rehashed in one PR "
                       f"(only one fingerprint refresh is permitted per PR): {rehashed}")
        return
    if not rehashed:
        return
    identity = rehashed[0]
    learn_dir_rel = ACTIVE_MODULE["paths"]["learningDataDir"]
    ok, reason = bfr.authorize_rehash(
        REPO, mb, learn_dir_rel, identity, old_by_id[identity], new_by_id[identity],
        MANIFEST_DEFAULT, expected_module=ACTIVE_MODULE["key"],
    )
    print(f"NOTE: {reason}")
    if not ok:
        errors.append(f"{rel}: {reason}")


def allowlist_ratchet_inline(mb, policy, errors):
    """Remove-only allowlist enforcement for non-Rashi task types. The
    boundary-authorizations registry gets one narrow exception: see
    _check_boundary_registry_ratchet / boundary_fingerprint_ratchet.py."""
    if policy == "restructure-with-env" and os.environ.get("RASHI_ALLOWLIST_RESTRUCTURE") == "1":
        return
    bfr = _load_boundary_ratchet()
    for p in sorted((YSCRIPTS / "allowlists").glob("*.json")):
        rel = p.relative_to(REPO).as_posix()
        r = sh(["git", "show", f"{mb}:{rel}"])
        old = json.loads(r.stdout) if r.returncode == 0 else {}
        new = json.loads(p.read_text())
        if bfr is not None and p.name == bfr.BOUNDARY_FILENAME:
            _check_boundary_registry_ratchet(rel, old.get("entries", []), new.get("entries", []), mb, errors, policy)
            continue
        for section in ("entries", "count_mismatches"):
            oe = {json.dumps(e, sort_keys=True) for e in old.get(section, [])}
            ne = {json.dumps(e, sort_keys=True) for e in new.get(section, [])}
            for a in sorted(ne - oe):
                errors.append(f"{rel}: {section} entry ADDED (policy {policy}): {a}")


# ---------------- manifest ----------------

def cmd_manifest(opts):
    types = load_registry()
    if opts.type not in types:
        sys.exit(f"ERROR: unknown task type {opts.type!r}. Known: {', '.join(sorted(types))}")
    spec = types[opts.type]
    # Resolve and validate the requested module before generating anything.
    # An unknown/malformed module fails clearly here; the manifest is
    # never written with a module value that couldn't actually resolve.
    set_active_module(resolve_active_module(opts.module))
    targets = expand_range(opts.range) if opts.range else []
    if spec["requiresTarget"] and not targets:
        sys.exit(f"ERROR: task type {opts.type!r} requires --range")

    # The corpus-wide legacy-concepts-purge: no --range means "every daf",
    # but that is never an implicit/empty-target mode. targets are set to
    # the EXACT descriptor-derived full daf set for the active module (see
    # all_daf_ids), so the manifest always carries an explicit, inspectable
    # target list -- never an empty list standing in for "unbounded". A
    # partial run is always an intentional, explicit --range instead.
    corpus_wide_purge = opts.type == "legacy-concepts-purge" and not opts.range
    if corpus_wide_purge:
        targets = all_daf_ids()

    auths = opts.authorize or []
    legal = legal_authorizations(spec)
    for a in auths:
        if a not in legal:
            sys.exit(f"ERROR: authorization {a!r} is not defined for type {opts.type!r} "
                     f"(legal: {sorted(legal) or 'none'})")
    if corpus_wide_purge and "allowCorpusWideMechanicalMigration" not in auths:
        sys.exit("ERROR: a corpus-wide legacy-concepts-purge (no --range) additionally "
                 "requires --authorize allowCorpusWideMechanicalMigration, naming the full "
                 f"{len(targets)}-daf descriptor-derived target set explicitly; pass --range "
                 "for an intentional partial/per-daf purge instead")

    max_batch = spec.get("maxBatch")
    # maxBatch is None ONLY for task types that substitute their own
    # explicit, independently-verified corpus-wide policy (today: only
    # legacy-concepts-purge's corpus_wide_purge path, gated above by
    # allowCorpusWideMechanicalMigration and pinned to the exact
    # descriptor-derived daf set) -- never a silent "0 means unlimited"
    # truthiness accident. Every other max_batch value, including 0, is
    # enforced as a real numeric cap.
    if max_batch is not None and len(targets) > max_batch:
        sys.exit(f"ERROR: {len(targets)} targets exceed maxBatch {max_batch} for {opts.type!r}; "
                 f"split the range into smaller PRs")
    allowlist_drain = None
    if opts.drain_allowlist:
        if opts.type not in ALLOWLIST_DRAIN_TYPES:
            sys.exit(f"ERROR: --drain-allowlist is only valid for "
                     f"{'/'.join(ALLOWLIST_DRAIN_TYPES)}, not {opts.type!r}")
        if len(targets) != 1:
            sys.exit("ERROR: --drain-allowlist requires exactly one target daf")
        daf = targets[0]
        snapshot = content_allowlist_entries(daf)
        allowlist_drain = {"authorized": True, "snapshot": snapshot}
    # Scaffold-fabrication debt is snapshotted automatically for single-target
    # reconstruction/realignment manifests: the baseline itself is the
    # tolerance, so no separate authorization is needed, but the snapshot
    # binds the worker to drain every entry (see scaffold_drain_status).
    scaffold_debt = None
    if opts.type in ALLOWLIST_DRAIN_TYPES and len(targets) == 1:
        snap = scaffold_debt_entries(targets[0])
        if snap:
            scaffold_debt = {"snapshot": snap}
    # Repetition-baseline debt is snapshotted automatically for single-target
    # reconstruction/realignment manifests, exactly like scaffold debt: the
    # baseline itself is the tolerance, so no --authorize flag is needed.
    # validate_repetition_drain (used by preflight) still checks the
    # snapshot against live state and the drift profile before it lets this
    # bypass a rashi_preflight.py block; the snapshot alone authorizes
    # nothing on its own. Count-mismatch debt has no equivalent anywhere.
    repetition_drain = None
    if opts.type in ALLOWLIST_DRAIN_TYPES and len(targets) == 1:
        rsnap = repetition_baseline_entries(targets[0])
        if rsnap:
            repetition_drain = {"snapshot": rsnap}

    # rashi-boundary-translation-repair's extra manifest fields are all
    # derived here from the current registry/review-record state, then
    # independently RECOMPUTED and cross-checked by
    # boundary_fingerprint_ratchet.authorize_rehash at scope-check time -
    # the manifest's declared values are a self-check, never the ground
    # truth the gate trusts. See docs/reports/rashi-boundary-fingerprint-
    # ratchet.md for the full contract.
    boundary_repair_fields = {}
    if opts.type == REPAIR_TASK_TYPE:
        if len(targets) != 1:
            sys.exit(f"ERROR: {REPAIR_TASK_TYPE!r} requires --range with exactly one daf")
        if opts.vilna_line is None:
            sys.exit(f"ERROR: {REPAIR_TASK_TYPE!r} requires --vilna-line")
        if not opts.entry_id:
            sys.exit(f"ERROR: {REPAIR_TASK_TYPE!r} requires --entry-id")
        if not opts.review_record:
            sys.exit(f"ERROR: {REPAIR_TASK_TYPE!r} requires --review-record")
        daf = targets[0]
        registry_path = YSCRIPTS / "allowlists" / "rashi_boundary_authorizations.json"
        registry = json.loads(registry_path.read_text())
        reg_entry = next((e for e in registry.get("entries", [])
                           if e.get("daf") == daf and e.get("vilnaLine") == opts.vilna_line), None)
        if reg_entry is None:
            sys.exit(f"ERROR: no existing boundary authorization for {daf} L{opts.vilna_line}")
        review_record_path = Path(opts.review_record)
        review_doc = json.loads(review_record_path.read_text())
        record = next((r for r in review_doc.get("records", []) if r.get("entryId") == opts.entry_id), None)
        if record is None:
            sys.exit(f"ERROR: no record for entryId {opts.entry_id!r} in {opts.review_record!r}")
        final_en = (record.get("secondPass") or {}).get("finalEnglish") or record.get("proposedEnglish")
        if not final_en:
            sys.exit(f"ERROR: review record for {opts.entry_id!r} has no finalEnglish/proposedEnglish yet")
        review_record_rel = review_record_path.as_posix()
        if review_record_path.is_absolute():
            review_record_rel = review_record_path.resolve().relative_to(REPO.resolve()).as_posix()
        boundary_repair_fields = {
            "entryId": opts.entry_id,
            "registryIdentity": {"daf": daf, "vilnaLine": opts.vilna_line},
            "baseEnFingerprint": reg_entry["enFingerprint"],
            "expectedNewEnFingerprint": hashlib.sha256(final_en.encode("utf-8")).hexdigest()[:16],
            "reviewRecordPath": review_record_rel,
        }

    # auditRecordIds is real manifest data, never an authorization flag: it
    # names the specific audit findings this PR repairs, validated against
    # the merged audit, the derived repair queue, the manifest targets and
    # the progress file (see validate_audit_record_ids).
    audit_record_ids = []
    if opts.type == AUDIT_RECORD_TASK_TYPE:
        audit_record_ids = list(opts.audit_record_id or [])
        ok, errs = validate_audit_record_ids(audit_record_ids, targets)
        if not ok:
            sys.exit("ERROR: invalid --audit-record-id value(s):\n  " + "\n  ".join(errs))
        # Separate migration-prerequisite gate (requirement: the corpus-wide
        # concepts purge and any per-sugya migration prerequisite the queue
        # declares must already be clean before this manifest may even be
        # generated, independent of semantic-field validation).
        prereq_errs = audit_repair_prerequisite_errors(audit_record_ids)
        if prereq_errs:
            sys.exit("ERROR: audited-sugya-enrichment-repair prerequisite(s) not satisfied:\n  "
                     + "\n  ".join(prereq_errs))
    elif opts.audit_record_id:
        sys.exit(f"ERROR: --audit-record-id is only valid for {AUDIT_RECORD_TASK_TYPE!r}, "
                 f"not {opts.type!r}")

    # migrationKinds is likewise real manifest data, never a boolean
    # authorization: it names which deterministic migration(s) this PR
    # performs, and restricts the scope engine to only the paths those
    # kinds own (see MIGRATION_KIND_PATHS / json_scope_check).
    migration_kinds = []
    if opts.type == "enrichment-schema-migration":
        migration_kinds = list(opts.migration_kind or [])
        if not migration_kinds:
            sys.exit("ERROR: enrichment-schema-migration requires at least one --migration-kind "
                     f"(legal: {sorted(MIGRATION_KINDS)})")
        unknown = [k for k in migration_kinds if k not in MIGRATION_KINDS]
        if unknown:
            sys.exit(f"ERROR: unknown --migration-kind value(s) {unknown}; "
                     f"legal: {sorted(MIGRATION_KINDS)}")
    elif opts.migration_kind:
        sys.exit("ERROR: --migration-kind is only valid for 'enrichment-schema-migration', "
                 f"not {opts.type!r}")

    manifest = {
        "type": opts.type,
        "module": opts.module,
        "targets": targets,
        "model": spec["model"],
        "paused": spec.get("paused", False),
        "lifecycle": lifecycle_of(spec),
        "mechanicalTier": spec.get("mechanicalTier", False),
        "independentReviewRequired": spec.get("independentReviewRequired", False),
        "reviewPolicy": review_policy_of(spec),
        "escalationModel": spec.get("escalationModel", "sonnet"),
        "authorizations": auths,
        "maxBatch": max_batch,
        "allowedFiles": spec["allowedFiles"],
        "allowedJsonPaths": spec["allowedJsonPaths"],
        "forbiddenFiles": spec["forbiddenFiles"],
        "allowlistPolicy": spec["allowlistPolicy"],
        "structurePolicy": spec["structurePolicy"],
        "requiredValidators": spec["requiredValidators"],
        "generationCommands": spec["generationCommands"],
        "buildTestCommands": spec["buildTestCommands"],
        "escalationTriggers": spec["escalationTriggers"],
        "allowlistDrain": allowlist_drain,
        "scaffoldDebt": scaffold_debt,
        "repetitionDrain": repetition_drain,
        "auditRecordIds": audit_record_ids,
        "migrationKinds": migration_kinds,
    }
    manifest.update(boundary_repair_fields)
    out = json.dumps(manifest, indent=1)
    if opts.out:
        Path(opts.out).write_text(out + "\n")
        print(f"manifest written to {opts.out}")
    else:
        print(out)


# ---------------- preflight ----------------

def cmd_preflight(opts):
    m, spec = load_manifest(opts.manifest)
    errors, notes = [], []
    if m.get("paused"):
        errors.append(f"task type {m['type']!r} is PAUSED; requires explicit unpausing (registry change)")
    for req in spec.get("requiredAuthorizations", []):
        if req not in m.get("authorizations", []):
            errors.append(f"task type {m['type']!r} requires the explicit --authorize {req} "
                          f"authorization on the manifest (operator-issued only)")

    if m["type"] == AUDIT_RECORD_TASK_TYPE:
        ok, audit_errs = validate_audit_record_ids(m.get("auditRecordIds", []), m.get("targets", []))
        if not ok:
            errors.extend("auditRecordIds: %s" % e for e in audit_errs)
        # Separate migration-prerequisite gate, independent of semantic-field
        # validation: the corpus-wide concepts purge and any per-sugya
        # migration prerequisite the queue declares must already be clean.
        errors.extend(audit_repair_prerequisite_errors(m.get("auditRecordIds", [])))
    if m["type"] == "enrichment-schema-migration" and not m.get("migrationKinds"):
        errors.append("enrichment-schema-migration manifest carries no migrationKinds; "
                      "regenerate with at least one --migration-kind")
    if m["type"] == "legacy-concepts-purge":
        learning_dir = ACTIVE_MODULE["paths"]["learningDataDir"]
        cnt = 0
        for daf in m["targets"]:
            fp = REPO / learning_dir / f"{daf}.learning.json"
            if fp.exists():
                doc = json.loads(fp.read_text())
                cnt += sum(1 for s in doc.get("sugyot", []) if "concepts" in s)
        print(f"preflight concepts inventory: {cnt} sugya(s) across {len(m['targets'])} target "
              f"daf currently carry a concepts key; worker:verify requires exactly this many "
              f"deletions, zero remaining, and no other field changed")

    dirty = sh(["git", "status", "--porcelain"]).stdout.strip()
    branch = sh(["git", "rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
    hooks = sh(["git", "config", "core.hooksPath"]).stdout.strip()
    version = (REPO / "VERSION").read_text().strip()
    pkg = json.loads((REPO / "package.json").read_text())["version"]
    lock = json.loads((REPO / "package-lock.json").read_text())["version"]

    print(f"branch: {branch} ({'DIRTY' if dirty else 'clean'}), VERSION {version}, "
          f"package {pkg}, lock {lock}, hooksPath {hooks or '(unset)'}")
    if dirty:
        (notes if opts.dry_run else errors).append("git tree is dirty" + (" (tolerated: --dry-run)" if opts.dry_run else "; commit or stash first"))
    if hooks != "githooks":
        errors.append("core.hooksPath inactive; run: git config core.hooksPath githooks")
    if not (version == pkg == lock):
        errors.append(f"VERSION/package/lock out of sync: {version}/{pkg}/{lock}")

    wf = (REPO / ".github" / "workflows" / "deploy-pages.yml").read_text()
    for needle in ("validate:offline:yoma", "check:rashi-pr-scope:yoma"):
        if needle not in wf:
            errors.append(f"CI workflow is missing required gate {needle!r}")

    if m["type"] in RASHI_TYPES or m.get("generationCommands"):
        fresh = sh([sys.executable, "scripts/check_generated_freshness.py"], cwd=YROOT)
        print(f"generated freshness: {'OK' if fresh.returncode == 0 else 'STALE'}")
        if fresh.returncode != 0:
            errors.append("generated data stale; regenerate before starting")

    if m["type"] in RASHI_TYPES:
        task = spec.get("rashiPreflightTask", "reconstruct")
        # Drift-block enforcement is manifest-aware here: the underlying
        # rashi_preflight env override is honored ONLY when the manifest
        # also carries the operator-issued authorizeDriftOverride flag. A
        # worker cannot unblock a SHIFTED/FABRICATION-SUSPECT daf by
        # setting the env var alone, and a manifest flag alone (however it
        # was generated) does nothing without the operator-issued env var.
        child_env = dict(os.environ)
        if spec.get("driftBlocked") and "authorizeDriftOverride" not in m.get("authorizations", []):
            child_env.pop(DRIFT_OVERRIDE_ENV, None)
        for daf in m["targets"]:
            r = subprocess.run([sys.executable, "scripts/rashi_preflight.py", daf, "--task", task],
                               capture_output=True, text=True, cwd=YROOT, env=child_env)
            per_daf_errors = [l for l in r.stdout.splitlines() if l.strip().startswith("ERROR") and daf in l]
            kept_errors = []
            for l in per_daf_errors:
                msg = l.strip().removeprefix("ERROR").strip()
                if "has unresolved CONTENT ALLOWLIST hits" in msg:
                    drain_ok, drain_note = validate_allowlist_drain(m, daf)
                    if drain_ok:
                        notes.append(drain_note)
                        continue
                    msg = f"{msg} [allowlist-drain not authorized: {drain_note}]"
                elif "has unresolved REPETITION-BASELINE hits" in msg:
                    drain_ok, drain_note = validate_repetition_drain(m, daf)
                    if drain_ok:
                        notes.append(drain_note)
                        continue
                    msg = f"{msg} [repetition-drain not authorized: {drain_note}]"
                # COUNT MISMATCH hits are deliberately never filtered here:
                # there is no drain path for structural count mismatches,
                # regardless of task type or manifest content.
                kept_errors.append(msg)
            ok = not kept_errors
            print(f"rashi preflight {daf} ({task}): {'OK' if ok else 'FAIL'}")
            errors.extend(kept_errors)
    elif m["targets"]:
        for daf in m["targets"]:
            if not (YROOT / "assets" / "talmuddev" / f"{daf}.json").exists():
                errors.append(f"{daf}: no talmuddev source")

    for l in notes:
        print(f"NOTE: {l}")
    if errors:
        print("\nWORKER PREFLIGHT FAILED:")
        for e in errors:
            print(f"  ERROR  {e}")
        sys.exit(1)
    print(f"\nOK: worker preflight passed for type {m['type']}"
          + (f", targets {', '.join(m['targets'])}" if m["targets"] else "")
          + (" [dry-run]" if opts.dry_run else "") + ".")


# ---------------- packet ----------------

def cmd_packet(opts):
    m, spec = load_manifest(opts.manifest)
    t = m["type"]
    if t in RASHI_TYPES:
        for daf in m["targets"]:
            r = sh([sys.executable, "scripts/make_rashi_work_packet.py", daf], cwd=YROOT)
            print(r.stdout)
        return
    if spec.get("jsonScope") and m["targets"]:
        for daf in m["targets"]:
            lj = json.loads((REPO / ACTIVE_MODULE["paths"]["learningDataDir"] / f"{daf}.learning.json").read_text())
            print(f"# Gemara-learning packet: {daf}")
            print(f"sugyot: {len(lj['sugyot'])}")
            for s in lj["sugyot"]:
                d = s.get("display", {})
                print(f"\n## {s['id']} (vilna {s['lineRange']['startVilnaLine']}-{s['lineRange']['endVilnaLine']})")
                print(f"title: {d.get('title','')}")
                print(f"argumentFlow ids: {[af['id'].split('-')[-1] for af in s.get('argumentFlow', [])]}")
                print(f"learning keys: {sorted((s.get('learning') or {}).keys())}")
            print("\nschema contract: shared/schema_map.js; gate: validate:schema:yoma")
        return
    if t == "literal-layer":
        r = sh(["npm", "run", "status:literal:yoma"], cwd=REPO)
        print(r.stdout[-2000:])
        print("commands: fetch_literal_en.py --range <a> <b> --skip-existing; then build_literal_layer.py --apply; gate: validate:literal:yoma")
        return
    if t == "docs-tooling":
        print("# Docs/tooling packet")
        print("affected commands: see package.json scripts block")
        print("required green: validate:offline:yoma, build, check:deploy-html, npm test, test:browser")
        print("docs likely needing updates: docs/worker-pipeline.md, docs/rashi-workflow.md, docs/rashi-audit-backlog.md")
        return
    if t == "generated-refresh":
        print("# Generated-refresh packet")
        for c in spec["generationCommands"]:
            print(f"run: {c}")
        print("then: npm run check:generated:yoma must pass; only learning_data.js/coverage.json may differ")
        return
    if t == "deployment-verify":
        print("# Deployment-verify packet")
        print("check Deploy Cloudways Branch and Deploy GitHub Pages for the target commit; then live site VERSION")
        print("no file changes permitted")
        return
    if t == "audit-only":
        print("# Audit-only packet")
        print("read-only: corpus scans, audit:rashi:semantic:yoma, validator dry runs, backlog reconciliation")
        print("output only under docs/reports/ (plus backlog process notes); no content or generated edits")
        return
    if t == "nekudot":
        print("# Nekudot packet: task type is PAUSED. No packet is issued.")
        return


# ---------------- prompt ----------------

def cmd_prompt(opts):
    m, spec = load_manifest(opts.manifest)
    t = m["type"]
    tgt = ", ".join(m["targets"]) if m["targets"] else "(no daf target)"
    lines = [
        f"Run a bounded MySugya worker pass: type {t}, module {m['module']}, target {tgt}.",
        "",
        spec["description"],
        "",
        f"Model: {m['model']}. Sonnet is the only execution and escalation model in this"
        " pipeline; no other model may take, review, or escalate any task type."
        + (" This type additionally requires a second, independent Sonnet review of the PR"
           " before merge." if review_policy_of(spec) == "independent" else ""),
        "",
        f"Lifecycle: {m['lifecycle']}."
        + (" This is a READ-ONLY pass: it must end with the tracked tree byte-identical."
           " Do NOT bump VERSION, do NOT commit, do NOT open a PR. Report findings only."
           if m["lifecycle"] == "read-only" else
           " This pass produces a tracked change, so it takes exactly one VERSION patch"
           " bump and exactly one PR."),
        "",
        "Procedure:",
        f"1. Reconcile to origin/main; confirm clean tree.",
        f"2. npm run worker:preflight -- --manifest .worker-manifest.json   (STOP on failure)",
        f"3. npm run worker:packet -- --manifest .worker-manifest.json     (sole context source)",
        "4. Perform ONLY the edits the manifest allows:",
        f"   allowed files: {json.dumps(m['allowedFiles'])}",
        f"   allowed JSON paths: {json.dumps(m['allowedJsonPaths'])}",
        f"   forbidden: {json.dumps(m['forbiddenFiles'])}",
    ]
    if t in RASHI_TYPES:
        lines += [
            "",
            "Rashi linking contract: linkedGemaraLineIds are SEMANTIC text anchors.",
            "Match each Rashi comment to the local segment(s) whose text it explains,",
            "using the packet's full segment text (Gemara and Mishnah ids alike).",
            "Never assign links by vilna line number or positional offset. A comment",
            "may link to multiple segments when it genuinely spans them; boundary",
            "policy never covers unrelated commentary. If the correct target segment",
            "cannot be identified from the packet, stop and escalate; never guess.",
        ]
    if m["generationCommands"]:
        lines.append("5. Regenerate: " + " && ".join(m["generationCommands"]))
    if m["lifecycle"] == "read-only":
        lines += [
            "6. Do NOT bump VERSION and do NOT run sync_version.py: this lifecycle"
            " forbids every tracked change.",
            "7. npm run worker:verify -- --manifest .worker-manifest.json --fast",
            "   then npm run worker:verify -- --manifest .worker-manifest.json --full",
            "   (verify asserts the tracked tree is byte-identical for a read-only pass)",
            "8. Do NOT commit, push, or open a PR. Report findings in your final report"
            " block only. If the pass produced something that must be persisted, STOP:"
            " that is a task-type mismatch, not a reason to write.",
        ]
        lines += [
            "",
            f"Allowlist policy: {m['allowlistPolicy']}. You may NEVER add allowlist or baseline entries.",
            f"Structure policy: {m['structurePolicy']}.",
            "You may not override, weaken, or reinterpret any validator. A red gate means your content or scope is wrong.",
            "",
            "Escalate (stop immediately and report) on:",
        ]
        lines += [f"- {e}" for e in m["escalationTriggers"]]
        lines += [
            "- any need to write a tracked file at all",
            "",
            "Final report format (one compact block): task type, targets, VERSION observed,",
            "gates status, findings, anything escalated.",
        ]
        print("\n".join(lines))
        return
    lines += [
        "6. Bump VERSION one patch; python3 scripts/sync_version.py",
        "7. npm run worker:verify -- --manifest .worker-manifest.json --fast",
        "   then npm run worker:verify -- --manifest .worker-manifest.json --full",
    ]
    if review_policy_of(spec) == "conditional":
        lines += [
            "8. Fresh post-edit self-review (MANDATORY before the PR): reread the raw",
            "   Hebrew and the packet's FULL segment text from scratch, without relying",
            "   on your earlier working assumptions, and recheck: the beginning, middle,",
            "   and tail of the daf; every citation anchor; every multi-id link; every",
            "   truncated boundary entry; every formerly allowlisted entry; that every",
            "   link is semantic (never positional); that no line uses the final id as",
            "   an unrelated-content fallback; and that no line narrates the comment's",
            "   own structure instead of translating it. This means: never write",
            "   'Rashi: opens/continues/closes/begins/resumes ...', and never write the",
            "   same narration with the word 'Rashi' dropped ('Opens \"X\":',",
            "   'continuing:', 'closing:', 'begins:', 'resumes:', or 'Then opens \"Y\":'",
            "   mid-sentence). Both forms are the same fabrication defect: describing",
            "   the shape of the comment instead of translating its content. When a raw",
            "   line contains more than one dibbur hamathil (more than one lemma the",
            "   comment addresses), translate all of them as one flowing direct",
            "   sentence, never as separately narrated structural beats. Record the",
            "   result in",
            "   .worker-self-review.json:",
            '   {"daf": "<daf>", "model": "' + m["model"] + '", "rechecked": {'
            + ", ".join(f'"{c}": true' for c in SELF_REVIEW_CHECKS) + "},",
            '    "blockersFound": [], "notes": "<one line>"}',
            "   Any blocker found = escalate; do not open the PR as mergeable.",
            "9. Commit .worker-manifest.json and .worker-self-review.json together with",
            "   the work, push, ONE PR for this daf only, wait for CI.",
            "10. npm run worker:review -- --manifest .worker-manifest.json",
            "    Merge ONLY when CI is green on the exact final head AND this prints",
            "    AUTO-MERGE-ELIGIBLE. No operator authorization is needed when both hold.",
            "    Then verify BOTH deploy workflows for the merge commit.",
            "11. If a queue is active: rerun npm run worker:queue. Progress derives",
            "    automatically from the merged manifest at origin/main; there is no state",
            "    to commit and NEVER a direct push to main. Continue to the",
            "    next queued target with a fresh manifest. Stop ONLY on an escalation",
            "    condition, unexpected repository state, or an empty queue.",
            f"    On escalation: stop, do not merge, and hand off to {spec.get('escalationModel', 'sonnet')} with a report.",
        ]
    elif review_policy_of(spec) == "independent":
        lines += [
            "8. Commit .worker-manifest.json together with the work, push, ONE PR, wait for CI.",
            "9. This task type requires an independent Sonnet review of the PR before merge:"
            " you may open the PR and poll CI, but you may NOT merge your own work."
            " Request the independent review and stop.",
        ]
    else:
        lines += [
            "8. Commit .worker-manifest.json together with the work, push, one PR, wait for CI, merge when green, verify both deploy workflows.",
        ]
    lines += [
        "",
        f"Allowlist policy: {m['allowlistPolicy']}. You may NEVER add allowlist or baseline entries.",
        f"Structure policy: {m['structurePolicy']}.",
        "You may not override, weaken, or reinterpret any validator. A red gate means your content or scope is wrong.",
        "",
        "Escalate (stop immediately and report) on:",
    ]
    lines += [f"- {e}" for e in m["escalationTriggers"]]
    lines += [
        "- any need to touch a file outside the allowed set",
        "",
        "Final report format (one compact block): task type, targets, PR number and merge commit,",
        "VERSION, gates status, deploy status, allowlist delta, anything escalated.",
    ]
    print("\n".join(lines))


# ---------------- scope ----------------

def resolve_base(base):
    if base:
        return base
    env_base = os.environ.get("GITHUB_BASE_REF", "").strip()
    return f"origin/{env_base}" if env_base else "origin/main"


def cmd_scope(opts):
    m, spec = load_manifest(opts.manifest)
    base = resolve_base(opts.base)
    mb = sh(["git", "merge-base", base, "HEAD"]).stdout.strip()
    if not mb:
        print(f"WARNING: cannot resolve merge-base of {base!r}; skipping scope check.")
        return
    changed = [l for l in sh(["git", "diff", "--name-only", mb]).stdout.splitlines() if l.strip()]
    errors = []

    for p in changed:
        if not file_allowed(p, spec, m["targets"], m["module"]):
            errors.append(f"{p}: outside the {m['type']} allowed file set")
    if not spec["allowedFiles"] and changed:
        errors.append(f"task type {m['type']} permits no file changes; {len(changed)} file(s) changed")

    if m["type"] in RASHI_TYPES:
        # Field-level enforcement reuses the proven Rashi validator. Only a
        # structural-repair manifest with the explicit allowStructure
        # authorization may relax the structure rules; every other type
        # (every ordinary manifest included) gets the strict contract.
        scope_cmd = [sys.executable, "scripts/check_rashi_pr_scope.py", "--base", base]
        if structure_authorized(m, spec):
            scope_cmd.append("--allow-structure")
            print("NOTE: allowStructure authorization active (rashi-structural-repair manifest).")
        r = sh(scope_cmd, cwd=YSCRIPTS.parent)
        if r.returncode != 0:
            errors.append("check_rashi_pr_scope failed:\n" + r.stdout[-1200:])
        max_batch = m.get("maxBatch")
        if max_batch is not None and len(m.get("targets", [])) > max_batch:
            errors.append(f"manifest targets {len(m['targets'])} exceed maxBatch {max_batch} "
                          f"for {m['type']} (split into smaller PRs)")
    else:
        # Non-Rashi types: inline allowlist ratchet (the Rashi validator's
        # field rules do not apply to these diffs).
        allowlist_ratchet_inline(mb, m["allowlistPolicy"], errors)
        json_scope_check(mb, changed, m, spec, errors)
        paths = ACTIVE_MODULE["paths"]
        if m["type"] == "generated-refresh":
            src_changed = [p for p in changed if p.startswith(paths["sourceAssetsRoot"] + "/")]
            if src_changed:
                errors.append(f"generated-refresh PR changed source files: {src_changed} "
                              f"(generated outputs only)")
        if m["type"] == "literal-layer":
            lit = ACTIVE_MODULE["capabilities"]["literalTranslation"]
            gen_only = [p for p in changed
                        if p in (paths["learningDataFile"], paths["coverageFile"])]
            lit_dir = lit.get("assetsDir") if lit["enabled"] else None
            src = [p for p in changed if lit_dir and p.startswith(lit_dir + "/")]
            if gen_only and not src:
                errors.append("literal-layer PR changed generated output without any "
                              "literal-translation source change (use generated-refresh instead)")

    # Manifest lifecycle: every changed learning JSON must be a manifest target
    if m["type"] not in ("docs-tooling",):
        learning_dir = ACTIVE_MODULE["paths"]["learningDataDir"]
        for p in changed:
            if p.startswith(learning_dir + "/") and p.endswith(".learning.json"):
                daf = p.split("/")[-1].replace(".learning.json", "")
                if daf not in m.get("targets", []):
                    errors.append(f"{p}: changed but daf {daf!r} is not in manifest targets "
                                  f"{m.get('targets', [])} (regenerate the manifest to cover it)")

    if errors:
        print(f"WORKER SCOPE CHECK FAILED (type {m['type']}, base {base}):\n")
        for e in errors:
            print(f"  ERROR  {e}")
        sys.exit(1)
    print(f"OK: {len(changed)} changed file(s) within {m['type']} scope vs {base}.")


# ---------------- verify ----------------

def verify_read_only(m, spec, base):
    """Read-only lifecycle enforcement: a read-only pass must end with the
    tracked tree byte-identical to base. Any tracked diff at all -- including
    a VERSION bump the universal loop would otherwise demand -- is a failure,
    which is precisely what makes the read-only contract self-consistent
    instead of unsatisfiable. Returns (ok, changed_paths)."""
    changed = [l.strip() for l in sh(["git", "diff", "--name-only", base]).stdout.splitlines()
               if l.strip()]
    changed += [l.strip() for l in sh(["git", "diff", "--name-only", "--cached"]).stdout.splitlines()
                if l.strip()]
    untracked = [l.strip() for l in
                 sh(["git", "ls-files", "--others", "--exclude-standard"]).stdout.splitlines()
                 if l.strip()]
    changed = sorted(set(changed) | set(untracked))
    return (not changed), changed


def cmd_verify(opts):
    m, spec = load_manifest(opts.manifest)
    results = []

    if lifecycle_of(spec) == "read-only":
        ok, changed = verify_read_only(m, spec, resolve_base(getattr(opts, "base", None)))
        results.append(("read-only-no-tracked-change", ok))
        if not ok:
            print("READ-ONLY LIFECYCLE VIOLATION: this task type must not change any tracked "
                  "file, and must never bump VERSION or open a PR. Offending paths:")
            for c in changed:
                print(f"  {c}")

    if m["type"] in RASHI_TYPES and m["targets"]:
        cmd = [sys.executable, "scripts/rashi_verify.py", *m["targets"]]
        if opts.full:
            cmd.append("--full")
        r = sh(cmd, cwd=YROOT)
        print(r.stdout[-3000:])
        results.append(("rashi-verify", r.returncode == 0))
        # Post-edit drift profile: hard gate for rashi-realignment (the
        # task's whole purpose is restoring alignment), advisory for the
        # other Rashi types.
        pr = sh([sys.executable, "scripts/audit_rashi_semantic.py", "--profile", "--json",
                 *m["targets"]], cwd=YROOT)
        try:
            profs = json.loads(pr.stdout)
            profs = profs if isinstance(profs, list) else [profs]
        except json.JSONDecodeError:
            profs = []
        bad = [f"{p['daf']}={p['classification']}" for p in profs if not p.get("lineLevelSafe")]
        print(f"post-edit drift profile: {', '.join(bad) if bad else 'all targets aligned'}")
        if m["type"] in ("rashi-realignment", "rashi-reconstruction", STRUCTURAL_TYPE):
            results.append(("drift-profile", not bad and bool(profs)))
    else:
        # Intentionally still Yoma-hardcoded: scripts/worker_task_types.json's
        # requiredValidators (and the npm scripts they name) are validator/
        # generator-layer parameterization, deferred to Phase 3 Step 3C per
        # docs/reports/phase3-inventory.md - a validate:offline:<module>
        # script does not exist for any non-Yoma module yet, so genericizing
        # this call today would silently fail rather than validate anything.
        r = sh(["npm", "run", "validate:offline:yoma"])
        results.append(("offline-gates", r.returncode == 0))
        if r.returncode != 0:
            print(r.stdout[-1500:])
        if opts.full:
            for name, cmd in [("build", ["npm", "run", "build"]),
                              ("deploy-html", ["npm", "run", "check:deploy-html"]),
                              ("unit+render", ["npm", "test"]),
                              ("browser", ["npm", "run", "test:browser"])]:
                if not spec["buildTestCommands"]:
                    break
                rr = sh(cmd)
                results.append((name, rr.returncode == 0))
                if rr.returncode != 0:
                    print(rr.stdout[-1200:])

    # scope + hygiene for every type
    scope_ns = argparse.Namespace(manifest=opts.manifest, base=opts.base)
    try:
        cmd_scope(scope_ns)
        results.append(("worker-scope", True))
    except SystemExit as ex:
        results.append(("worker-scope", ex.code in (0, None)))

    version = (REPO / "VERSION").read_text().strip()
    pkg = json.loads((REPO / "package.json").read_text())["version"]
    results.append(("version-sync", version == pkg))

    mb = sh(["git", "merge-base", resolve_base(opts.base), "HEAD"]).stdout.strip()
    changed = sh(["git", "diff", "--name-only", mb]).stdout.split() if mb else []
    dash_bad = []
    source_assets = ACTIVE_MODULE["paths"]["sourceAssetsRoot"]
    talmuddev_prefix = source_assets + "/talmuddev/"
    if mb:
        for p in changed:
            fp = REPO / p
            if fp.suffix in (".py", ".md", ".json", ".yml", ".js", ".jsx") and fp.exists():
                if p.startswith(talmuddev_prefix) or p == ACTIVE_MODULE["paths"]["learningDataFile"]:
                    continue
                txt = fp.read_text(errors="ignore")
                if "\u2014" in txt or "\u2013" in txt:
                    if not p.startswith(source_assets + "/"):
                        dash_bad.append(p)
    results.append(("no-dashes", not dash_bad))
    for p in dash_bad:
        print(f"  dash found in {p}")

    if spec.get("sourcesMustBeUnchanged"):
        src_ok, src_msgs = verify_sources_unchanged(spec, changed, mb)
        results.append(("sources-unchanged", src_ok))
        if src_msgs:
            print("\nsourcesMustBeUnchanged enforcement:")
            for msg in src_msgs:
                print(f"  {'PASS' if src_ok else 'FAIL'}  {msg}")
        if src_ok:
            print("sourcesMustBeUnchanged: OK, no source/Rashi/argumentFlow/sourceRefs field "
                  "or source asset changed.")

    if m["type"] == "legacy-concepts-purge" and mb:
        cp_ok, cp_msgs = verify_concepts_purge(m, mb, ACTIVE_MODULE["paths"]["learningDataDir"])
        results.append(("concepts-purge-exact-deletion", cp_ok))
        print("\nlegacy-concepts-purge deletion accounting:")
        for msg in cp_msgs:
            print(f"  {'PASS' if cp_ok else ('FAIL' if 'concepts key' in msg or 'does not exactly' in msg else 'NOTE')}  {msg}")

    # Task-specific rule-scoped target-clean: legacy-concepts-purge,
    # enrichment-schema-migration and audited-sugya-enrichment-repair each
    # get a NARROW enrichment-contract check covering only their own
    # rules/targets, so unrelated legacy debt never blocks an otherwise
    # valid scoped change. The corpus-wide ratchet (every rule, whole
    # corpus) already ran above via validate:offline:yoma and stays the
    # final word on new debt anywhere.
    scoped_rules, scoped_targets = task_specific_rule_scoped_targets(m)
    if scoped_rules and scoped_targets:
        rc = sh([sys.executable, "scripts/validate_enrichment_contracts.py",
                "--module", m["module"], "--rules", *scoped_rules, "--targets", *scoped_targets])
        results.append(("task-scoped-enrichment-clean", rc.returncode == 0))
        print(f"\ntask-specific rule-scoped target-clean ({', '.join(scoped_rules)}):")
        print(rc.stdout[-1800:])
        if rc.returncode != 0:
            print(rc.stderr[-600:])

    # Merge-base monotonic ratchet: applies to EVERY task type whose PR
    # changes the active module's learning data, not gated on task type at
    # all (unlike task-scoped-enrichment-clean above, which only runs for
    # the three enrichment-authoring task types and only checks the rules
    # those task types own). This answers a different question: "did this
    # PR regress any enrichment rule anywhere compared with current main?"
    # It closes the gap the frozen historical baseline cannot close on its
    # own -- the frozen baseline never stops a later PR from silently
    # reintroducing a violation a previous PR already fixed on main, because
    # that exact value is still inside the frozen envelope. Both checks are
    # required; neither replaces the other.
    learning_dir = ACTIVE_MODULE["paths"]["learningDataDir"]
    learning_file = ACTIVE_MODULE["paths"]["learningDataFile"]
    learning_data_changed = bool(mb) and any(
        p == learning_file or p.startswith(learning_dir + "/") for p in changed)
    if learning_data_changed:
        rc = sh([sys.executable, "scripts/validate_enrichment_contracts.py",
                "--module", m["module"], "--compare-ref", mb])
        results.append(("enrichment-regression-vs-merge-base", rc.returncode == 0))
        print(f"\nenrichment-regression-vs-merge-base (compare-ref {mb[:12]}):")
        print(rc.stdout[-2500:])
        if rc.returncode != 0:
            print(rc.stderr[-800:])

    if m["type"] == AUDIT_RECORD_TASK_TYPE and mb:
        # --allowed-ids restricts progress-record changes to exactly this
        # manifest's named auditRecordIds (requirement: progress scope is
        # record-specific, not "any record may advance as long as the
        # transition is legal"). --base mb plus the default --head HEAD
        # makes the check walk the FULL commit history of this branch, not
        # just compare the two endpoints, so a legal NOT_STARTED ->
        # IN_PROGRESS -> FIXED_PENDING_REVIEW walk across several commits on
        # this branch is never rejected as a false "skip".
        rc = sh([sys.executable, "scripts/generate_enrichment_repair_queue.py",
                "--check", "--base", mb, "--allowed-ids", *m.get("auditRecordIds", [])])
        results.append(("repair-queue-progress-check", rc.returncode == 0))
        print("\nrepair-queue/progress-file check:")
        print(rc.stdout[-1500:])
        if rc.returncode != 0:
            print(rc.stderr[-600:])
        # A semantic repair PR must advance the progress record for every
        # audit record it names -- NOT_STARTED surviving the PR means the
        # queue was never actually updated to reflect the work done.
        progress = load_repair_progress()
        stale = [aid for aid in m.get("auditRecordIds", [])
                if progress.get(aid, {}).get("status", "NOT_STARTED") == "NOT_STARTED"]
        results.append(("progress-record-updated", not stale))
        if stale:
            print(f"\nFAIL progress-record-updated: {stale} still NOT_STARTED; a semantic "
                 f"repair PR must update its corresponding progress record(s) in "
                 f"{REPAIR_PROGRESS_PATH.relative_to(REPO)}")

    # Per-daf allowlist completion summary (placeholder/rashi repair tasks)
    if m["targets"] and mb:
        ca_path = YSCRIPTS / "allowlists" / "rashi_content_allowlist.json"
        r = sh(["git", "show", f"{mb}:{ca_path.relative_to(REPO).as_posix()}"])
        old_entries = json.loads(r.stdout).get("entries", []) if r.returncode == 0 else []
        new_entries = json.loads(ca_path.read_text()).get("entries", [])
        print("\nper-daf allowlist completion:")
        shrank_or_equal = True
        for daf in m["targets"]:
            before = sum(1 for e in old_entries if e["daf"] == daf)
            after = sum(1 for e in new_entries if e["daf"] == daf)
            print(f"  {daf}: allowlisted lines {before} -> {after}")
            if after > before:
                shrank_or_equal = False
        if m.get("type") == "placeholder-backfill" and not shrank_or_equal:
            results.append(("allowlist-shrink", False))

        # Allowlist-drain enforcement: a rashi-reconstruction/rashi-realignment
        # manifest that snapshotted pre-existing target-scoped debt at preflight
        # must actually eliminate it here. See allowlist_drain_status for the
        # pure check (unit-tested independently of this subprocess plumbing).
        if m.get("allowlistDrain"):
            cr = sh([sys.executable, "scripts/validate_rashi_content.py", "--json"], cwd=YROOT)
            try:
                report = json.loads(cr.stdout)
            except json.JSONDecodeError:
                report = None
            stale_pairs = ({(e["daf"], e["vilnaLine"]) for e in report["stale"]} if report else set())
            drain_ok, drain_msgs = allowlist_drain_status(m, old_entries, new_entries, stale_pairs)
            if drain_msgs:
                print("\nallowlist-drain enforcement:")
                for msg in drain_msgs:
                    print(f"  {'PASS' if drain_ok else 'FAIL'}  {msg}")
                results.append(("allowlist-drain", drain_ok))

        # Scaffold-debt drain enforcement: reconstruction/realignment must
        # leave its single target with zero scaffold hits and zero remaining
        # baseline entries, and the baseline may only shrink, target-scoped.
        if m.get("type") in ALLOWLIST_DRAIN_TYPES and len(m["targets"]) == 1:
            daf = m["targets"][0]
            sb_rel = SCAFFOLD_BASELINE.relative_to(REPO).as_posix()
            rr = sh(["git", "show", f"{mb}:{sb_rel}"])
            old_sb = json.loads(rr.stdout).get("entries", []) if rr.returncode == 0 else []
            new_sb = scaffold_debt_entries()
            hr = sh([sys.executable, "scripts/audit_rashi_scaffold.py", daf,
                     "--json", "--no-baseline"], cwd=YROOT)
            try:
                target_hits = json.loads(hr.stdout).get("hits", [])
            except json.JSONDecodeError:
                target_hits = [{"daf": daf, "vilnaLine": -1}]
            sc_ok, sc_msgs = scaffold_drain_status(m, daf, old_sb, new_sb, target_hits)
            if sc_msgs:
                print("\nscaffold-debt drain enforcement:")
                for msg in sc_msgs:
                    print(f"  {'PASS' if sc_ok else 'FAIL'}  {msg}")
            results.append(("scaffold-drain", sc_ok))

            # Repetition-baseline drain enforcement: reconstruction/realignment
            # must leave its single target with zero repetition violations and
            # zero remaining baseline entries; the baseline may only shrink,
            # target-scoped. Count-mismatch debt is untouched by this and has
            # no drain path anywhere; it stays a hard block in
            # rashi_preflight.py regardless of task type or manifest content.
            rb_rel = REPETITION_BASELINE.relative_to(REPO).as_posix()
            rbr = sh(["git", "show", f"{mb}:{rb_rel}"])
            old_rb = json.loads(rbr.stdout).get("entries", []) if rbr.returncode == 0 else []
            new_rb = repetition_baseline_entries()
            rep_r = sh([sys.executable, "scripts/validate_rashi_repetition.py"], cwd=YROOT)
            target_violations = [l for l in rep_r.stdout.splitlines()
                                  if l.strip().startswith("ERROR") and f"{daf}:" in l]
            rp_ok, rp_msgs = repetition_drain_status(m, daf, old_rb, new_rb, target_violations)
            if rp_msgs:
                print("\nrepetition-baseline drain enforcement:")
                for msg in rp_msgs:
                    print(f"  {'PASS' if rp_ok else 'FAIL'}  {msg}")
            results.append(("repetition-drain", rp_ok))

    # Literal-layer coverage delta
    if m["type"] == "literal-layer":
        cov = sh([sys.executable, "scripts/validate_literal.py"], cwd=YROOT)
        for line in cov.stdout.splitlines():
            if line.startswith(("Coverage:", "Has en_lit:", "Non-empty:")):
                print(f"  {line.strip()}")
        lit_dir = ACTIVE_MODULE["capabilities"]["literalTranslation"].get("assetsDir")
        impacted = [p for p in changed if lit_dir and p.startswith(lit_dir + "/")]
        print(f"  literal-translation files impacted: {len(impacted)}")

    print("\n============ worker:verify summary ============")
    fail = False
    for name, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        fail |= not ok
    if fail:
        print("\nWORKER VERIFY FAILED. Fix your content/scope or STOP AND ESCALATE.")
        sys.exit(1)
    policy = review_policy_of(spec)
    if policy == "independent":
        print("\nREVIEW GATE: this task type requires an independent Sonnet review of the PR "
              "before merge. Workers may open the PR and poll CI, but may NOT merge their own "
              "work; request the independent review and stop.")
    elif policy == "conditional":
        print("\nCONDITIONAL REVIEW GATE: after the fresh post-edit self-review is recorded "
              "in .worker-self-review.json and CI is green on the final head, run "
              "`npm run worker:review -- --manifest .worker-manifest.json`. Merge ONLY if it "
              f"prints AUTO-MERGE-ELIGIBLE; on any failed condition, escalate to "
              f"{spec.get('escalationModel', 'sonnet')} instead of merging.")
    if lifecycle_of(spec) == "read-only":
        nxt = ("report findings; this lifecycle ends with NO commit, NO VERSION bump, and NO PR"
               if opts.full else "npm run worker:verify -- --manifest .worker-manifest.json --full")
    else:
        nxt = "commit (include .worker-manifest.json), push, open the PR" if opts.full else \
              "npm run worker:verify -- --manifest .worker-manifest.json --full"
    print(f"\nWORKER VERIFY PASSED ({'full' if opts.full else 'fast'}). Next: {nxt}")


# ---------------- review (conditional auto-merge gate) ----------------

SELF_REVIEW_PATH = REPO / ".worker-self-review.json"
SELF_REVIEW_CHECKS = (
    "beginningMiddleTail", "citationAnchors", "multiIdLinks",
    "truncatedBoundaryEntries", "formerlyAllowlistedEntries",
    "semanticNotPositional", "noUnrelatedFinalIdFallback",
    "noPlainMetaNarration",
)

# Canonical machine-checked auto-merge conditions, in report order. CI
# greenness and the verify --fast/--full runs are procedural conditions the
# worker satisfies in the loop itself (worker:review reminds about them but
# cannot observe CI from here).
REVIEW_CONDITIONS = (
    "single-target-manifest",
    "exactly-one-authorized-daf-changed",
    "scope-clean-no-structure-no-hebrew-no-forbidden-fields",
    "no-allowlist-additions",
    "allowlist-removals-limited-to-target-daf",
    "scaffold-clean-on-target",
    "scaffold-baseline-shrink-only",
    "repetition-clean-on-target",
    "repetition-baseline-shrink-only",
    "packet-contains-every-linked-local-id",
    "all-links-legal-and-empty-links-authorized",
    "drift-profile-ALIGNED",
    "semantic-audit-zero-shift-candidates",
    "no-stub-or-duplicate-helpers",
    "generated-files-fresh",
    "version-metadata-synced",
    "fresh-self-review-committed-and-clean",
)


def evaluate_review_policy(conditions):
    """Pure auto-merge policy: eligible only when EVERY condition is true.
    Returns (eligible, failed_condition_names)."""
    failed = [k for k in conditions if not conditions[k]]
    return (not failed, failed)


def _citation_shaped(inner):
    """Independent citation-shape test for one parenthetical's inner text,
    deliberately not reusing anchors_of()'s tractate-name list: flags it
    as citation-like only if it names a page ("daf") or ends in the
    short daf/amud marker every Talmudic page citation uses (1-4 Hebrew
    letters immediately followed by a period or colon). An ordinary
    editorial gloss like "(Torah)" carries neither signal."""
    if "דף" in inner:
        return True
    return bool(re.search(r'[א-ת"׳]{1,4}[.:]$', inner.strip()))


def independent_zero_citation_scan(daf):
    """A SECOND, independent check that a daf's raw Hebrew contains no
    citation-like text at all, deliberately not reusing anchors_of()'s
    per-line/lookahead/tractate-name-matching logic: scans the ENTIRE
    concatenated raw text for any parenthetical group shaped like a
    citation (see _citation_shaped), whether or not its contents match a
    known tractate name or a daf number. Catches citation-like tokens (an
    unrecognized abbreviation, a same-parens "tractate daf N" citation, a
    verse citation format anchors_of does not model) that a zero-anchor
    profile from the primary scanner could otherwise miss, while not
    flagging ordinary non-citation parenthetical glosses. Returns
    (ok: bool, detail: str)."""
    tpath = YROOT / "assets" / "talmuddev" / f"{daf}.json"
    if not tpath.exists():
        return False, f"no talmuddev source for {daf}"
    raw = [l for l in json.loads(tpath.read_text()).get("rashi", []) if l and l.strip()]
    whole = " ".join(raw)
    all_groups = re.findall(r"\(([^()]{1,60})\)", whole)
    hits = [g for g in all_groups if _citation_shaped(g)]
    if hits:
        return False, f"parenthetical citation-like text found: {hits[:5]}"
    return True, "no parenthetical citation-like text anywhere in the raw Hebrew"


def multi_anchor_safe(prof):
    """Case A: 2+ genuine anchors. Stricter than the bare ALIGNED label
    (which the classifier also grants to a daf with anchors still
    missing, e.g. 2 found + 2 missing): requires the classification
    itself be ALIGNED, every expected anchor found, zero missing, and
    every found offset exactly 0 -- except a dafnum anchor flagged
    splitContinuation (its digits are sourced from the following raw
    line, e.g. he ends "(Berakhot" and the next line opens "39a)"), for
    which offset 0 or +1 are both the citation's own, honestly-translated
    position, not drift. Returns (ok: bool, reason: str)."""
    if not prof:
        return False, "no drift profile available"
    cls = prof.get("classification")
    if cls != "ALIGNED":
        return False, f"classification is {cls}, not ALIGNED"
    if len(prof.get("anchors", [])) < 2:
        return False, "fewer than 2 genuine anchors (not a multi-anchor daf)"
    if prof.get("anchorsMissing", 1) != 0:
        return False, f"{prof.get('anchorsMissing')} expected anchor(s) missing"
    bad_offsets = []
    for a in prof.get("anchors", []):
        o = a.get("offset")
        if o is None:
            continue
        allowed_offsets = (0, 1) if a.get("splitContinuation") else (0,)
        if o not in allowed_offsets:
            bad_offsets.append(o)
    if bad_offsets:
        return False, f"offset(s) not exactly 0: {bad_offsets}"
    return True, ("classification ALIGNED, every expected anchor found, zero missing, "
                  "all offsets 0 (or +1 for a legitimately split citation's daf number)")


def one_anchor_safe(prof, sr):
    """Case B (Yoma 48b class of daf): a rashi-reconstruction/realignment
    daf whose raw Hebrew genuinely contains exactly one detectable
    citation may substitute for ALIGNED when ALL of the following hold,
    computed only from the drift profile and the fresh self-review (no
    file I/O, no git):

      1. prof['anchors'] has exactly one entry.
      2. that entry's offset is not None (it is found in the English).
      3. that entry's offset is exactly 0 (no displacement) -- or +1 when
         the anchor is flagged splitContinuation, since a dafnum token
         whose digits are sourced from the following raw line legitimately
         lands one English line later in a faithful translation.
      4. prof['anchorsMissing'] is 0 (no expected anchor is missing).
      5. the self-review carries an 'oneAnchorAttestation' (or the
         legacy 'anchorPoorAttestation') block with all of
         ONE_ANCHOR_ATTESTATION_KEYS explicitly true.

    SHIFTED requires >= SHIFT_MIN_ANCHORS (2) same-sign displaced
    anchors and FABRICATION-SUSPECT requires >= FAB_MIN_CONSECUTIVE_MISSES
    (2) consecutive missing name anchors, so condition 1 alone already
    excludes both classifications from ever qualifying; this function
    never reclassifies or relabels the daf. Returns (ok: bool, reason: str)."""
    if not prof:
        return False, "no drift profile available"
    anchors = prof.get("anchors", [])
    if len(anchors) != 1:
        return False, (f"{len(anchors)} genuine detectable citation(s) in the raw Hebrew "
                        "(this tier requires exactly 1)")
    offset = anchors[0].get("offset")
    if offset is None:
        return False, "the single citation is not found anywhere in the English"
    allowed_offsets = (0, 1) if anchors[0].get("splitContinuation") else (0,)
    if offset not in allowed_offsets:
        return False, f"the single citation is found at offset {offset}, not 0"
    if prof.get("anchorsMissing", 1) != 0:
        return False, f"{prof.get('anchorsMissing')} expected citation(s) missing"
    att = (sr or {}).get("oneAnchorAttestation") or (sr or {}).get("anchorPoorAttestation") or {}
    missing_att = [k for k in ONE_ANCHOR_ATTESTATION_KEYS if att.get(k) is not True]
    if missing_att:
        return False, f"self-review oneAnchorAttestation missing or false: {missing_att}"
    return True, ("exactly one genuine citation, found at offset 0, no missing anchors, "
                  "self-review attests no invented/moved/duplicated citation")


def zero_anchor_safe(daf, prof, sr, entries=None):
    """Case C: a rashi-reconstruction/realignment daf whose raw Hebrew
    genuinely contains ZERO detectable citations of any kind. Citation
    anchors are corroborating evidence, not a mandatory content feature,
    so their absence must not automatically imply correctness; this tier
    therefore requires a stronger full-daf attestation than the one- or
    multi-anchor tiers, computed from the drift profile, an independent
    second source scan, the fresh self-review, and (when provided) the
    daf's own entries. Returns (ok: bool, reason: str)."""
    if not prof:
        return False, "no drift profile available"
    if prof.get("classification") != "INSUFFICIENT-ANCHORS":
        return False, f"classification is {prof.get('classification')}, not INSUFFICIENT-ANCHORS"
    anchors = prof.get("anchors", [])
    if anchors:
        return False, f"{len(anchors)} genuine detectable citation(s) exist (this tier requires 0)"
    scan_ok, scan_detail = independent_zero_citation_scan(daf)
    if not scan_ok:
        return False, f"independent second scan disagrees: {scan_detail}"
    att = (sr or {}).get("zeroAnchorAttestation") or {}
    missing_att = [k for k in ZERO_ANCHOR_ATTESTATION_KEYS if att.get(k) is not True]
    if missing_att:
        return False, f"self-review zeroAnchorAttestation missing or false: {missing_att}"
    if entries is not None:
        empty_vl = {e["vilnaLine"] for e in entries if not e.get("linkedGemaraLineIds")}
        authorized = {a.get("vilnaLine") for a in (sr or {}).get("authorizedEmptyLinks", [])
                      if a.get("rule")}
        unauthorized = sorted(empty_vl - authorized)
        if unauthorized:
            return False, (f"empty linkedGemaraLineIds on vilnaLine {unauthorized} without an "
                            "authorizedEmptyLinks entry citing a documented boundary rule")
    return True, ("two independent scans confirm zero citations anywhere in the raw Hebrew, "
                  "self-review attests every line was reread with no uncertainty")


def drift_ok_for_type(m_type, daf, prof, sr, entries=None):
    """Pure dispatch (file I/O limited to the one independent-scan read
    inside zero_anchor_safe; no git): does the post-edit drift profile
    satisfy this task type's merge bar? Returns (ok, extra_condition_key_
    or_None, note) where extra_condition_key_or_None is a SECOND
    condition name to add to the conditions dict (its own PASS/FAIL
    line) only when an evidence tier is what actually decided the
    outcome; note is an empty string when there is nothing to add."""
    cls = prof["classification"] if prof else "NO-PROFILE"
    if m_type == STRUCTURAL_TYPE:
        ok = bool(prof) and prof.get("lineLevelSafe", False)
        note = "" if ok else f"post-edit drift profile is {cls}, not line-level-safe"
        return ok, None, note
    if m_type in EVIDENCE_TIER_TYPES:
        n_anchors = len(prof.get("anchors", [])) if prof else -1
        if n_anchors >= 2:
            ok, reason = multi_anchor_safe(prof)
            note = "" if ok else (f"post-edit drift profile is {cls}, not ALIGNED, and does not "
                                   f"satisfy the multi-anchor evidence tier: {reason}")
            return ok, None, note
        if n_anchors == 1:
            ok, reason = one_anchor_safe(prof, sr)
            if ok:
                return True, "one-anchor-safe", (
                    f"ONE-ANCHOR-SAFE: {reason} (classification remains {cls}, not relabeled ALIGNED)")
            return False, "one-anchor-safe", (
                f"post-edit drift profile is {cls}, not ALIGNED, and does not qualify for the "
                f"one-anchor-safe evidence tier: {reason}")
        if n_anchors == 0:
            ok, reason = zero_anchor_safe(daf, prof, sr, entries)
            if ok:
                return True, "zero-anchor-safe", (
                    f"ZERO-ANCHOR-SAFE: {reason} (classification remains {cls}, not relabeled ALIGNED)")
            return False, "zero-anchor-safe", (
                f"post-edit drift profile is {cls}, not ALIGNED, and does not qualify for the "
                f"zero-anchor-safe evidence tier: {reason}")
        return False, None, "no drift profile available"
    ok = cls == "ALIGNED"
    note = "" if ok else f"post-edit drift profile is {cls}, not ALIGNED"
    return ok, None, note


def gather_review_conditions(m, spec, base):
    """Collect the machine-checkable auto-merge conditions for a conditional
    review task. Every check is read-only. Returns (conditions, notes)."""
    conditions = {k: False for k in REVIEW_CONDITIONS}
    notes = []
    targets = m.get("targets", [])
    conditions["single-target-manifest"] = len(targets) == 1
    if len(targets) != 1:
        notes.append(f"manifest carries {len(targets)} targets; conditional review is one daf per PR")
        return conditions, notes
    target = targets[0]

    # Structural repair exists to restore 1:1 raw correspondence: entry
    # count and vilnaLine sequence must match the authoritative source
    # exactly after the pass. Computed before any git dependency so the
    # condition is always present and valued for structural manifests.
    if m["type"] == STRUCTURAL_TYPE:
        tpath = YROOT / "assets" / "talmuddev" / f"{target}.json"
        raw_n = len([l for l in json.loads(tpath.read_text()).get("rashi", []) if l and l.strip()])
        lp = REPO / ACTIVE_MODULE["paths"]["learningDataDir"] / f"{target}.learning.json"
        ent = json.loads(lp.read_text()).get("rashiTranslations", []) if lp.exists() else []
        seq_ok = [e.get("vilnaLine") for e in ent] == list(range(1, raw_n + 1))
        conditions["entry-count-and-order-match-raw"] = len(ent) == raw_n and seq_ok
        if not (len(ent) == raw_n and seq_ok):
            notes.append(f"rashiTranslations {len(ent)} entries vs {raw_n} raw lines "
                         f"(sequence {'ok' if seq_ok else 'broken'})")

    mb = sh(["git", "merge-base", base, "HEAD"]).stdout.strip()
    if not mb:
        notes.append(f"cannot resolve merge-base of {base!r}")
        return conditions, notes
    changed = [l for l in sh(["git", "diff", "--name-only", mb]).stdout.splitlines() if l.strip()]

    learning_dir = ACTIVE_MODULE["paths"]["learningDataDir"]
    learn_changed = [p for p in changed
                     if p.startswith(learning_dir + "/") and p.endswith(".learning.json")]
    expected = f"{learning_dir}/{target}.learning.json"
    conditions["exactly-one-authorized-daf-changed"] = learn_changed == [expected]
    if learn_changed != [expected]:
        notes.append(f"learning JSONs changed: {learn_changed or 'none'} (expected exactly [{expected}])")

    # Scope: structure, Hebrew, forbidden fields, file set (reuses the
    # hard Rashi validator via cmd_scope semantics). Structure relaxation
    # exists ONLY for an explicitly authorized structural-repair manifest.
    scope_cmd = [sys.executable, "scripts/check_rashi_pr_scope.py", "--base", base]
    if structure_authorized(m, spec):
        scope_cmd.append("--allow-structure")
    r = sh(scope_cmd, cwd=YROOT)
    conditions["scope-clean-no-structure-no-hebrew-no-forbidden-fields"] = r.returncode == 0
    if r.returncode != 0:
        notes.append("check_rashi_pr_scope failed:\n" + r.stdout[-800:])

    # Allowlist delta: additions are forbidden anywhere; removals only on
    # the target daf (a removal that survives the content gate green was by
    # definition validator-stale, since the gate re-derives violations).
    added, foreign_removed = [], []
    for p in sorted((YSCRIPTS / "allowlists").glob("*.json")):
        rel = p.relative_to(REPO).as_posix()
        rr = sh(["git", "show", f"{mb}:{rel}"])
        old = json.loads(rr.stdout) if rr.returncode == 0 else {}
        new = json.loads(p.read_text())
        for section in ("entries", "count_mismatches"):
            oe = {json.dumps(e, sort_keys=True) for e in old.get(section, [])}
            ne = {json.dumps(e, sort_keys=True) for e in new.get(section, [])}
            added += [f"{rel}:{a}" for a in sorted(ne - oe)]
            for gone in sorted(oe - ne):
                if json.loads(gone).get("daf") != target:
                    foreign_removed.append(f"{rel}:{gone}")
    conditions["no-allowlist-additions"] = not added
    conditions["allowlist-removals-limited-to-target-daf"] = not foreign_removed
    for a in added:
        notes.append(f"allowlist entry ADDED: {a}")
    for g in foreign_removed:
        notes.append(f"allowlist entry removed outside target daf: {g}")

    # Scaffold-fabrication gate: after any conditional-review Rashi task, the
    # target daf must carry zero current scaffold hits AND zero remaining
    # scaffold-debt baseline entries (a repair never leaves scaffold text or
    # unretired debt behind); and the debt baseline may only shrink, with
    # removals limited to the target daf and no entry rehashed.
    sr = sh([sys.executable, "scripts/audit_rashi_scaffold.py", target, "--json"], cwd=YROOT)
    try:
        srep = json.loads(sr.stdout)
    except json.JSONDecodeError:
        srep = None
    sc_clean = bool(srep) and not srep["new"] and not srep["changed"] \
        and srep["remainingDebt"] == 0 and not srep["stale"]
    conditions["scaffold-clean-on-target"] = sc_clean
    if not sc_clean:
        if srep:
            notes.append(f"scaffold gate on {target}: {len(srep['new'])} new, "
                         f"{len(srep['changed'])} changed, {srep['remainingDebt']} "
                         f"baselined debt, {len(srep['stale'])} stale baseline entr(ies)")
        else:
            notes.append("scaffold audit produced no parseable report")
    sb_rel = SCAFFOLD_BASELINE.relative_to(REPO).as_posix()
    rr = sh(["git", "show", f"{mb}:{sb_rel}"])
    old_sb = json.loads(rr.stdout).get("entries", []) if rr.returncode == 0 else []
    new_sb = scaffold_debt_entries()
    old_map = {(e["daf"], e["vilnaLine"]): e.get("enHash") for e in old_sb}
    new_map = {(e["daf"], e["vilnaLine"]): e.get("enHash") for e in new_sb}
    sb_added = sorted(set(new_map) - set(old_map))
    sb_rehashed = sorted(k for k in set(new_map) & set(old_map) if new_map[k] != old_map[k])
    sb_foreign = sorted(k for k in set(old_map) - set(new_map) if k[0] != target)
    conditions["scaffold-baseline-shrink-only"] = not sb_added and not sb_rehashed and not sb_foreign
    for k in sb_added:
        notes.append(f"scaffold-debt baseline entry ADDED: {k}")
    for k in sb_rehashed:
        notes.append(f"scaffold-debt baseline entry rehashed: {k}")
    for k in sb_foreign:
        notes.append(f"scaffold-debt entry removed outside target daf: {k}")

    # Repetition-baseline gate: mirrors the scaffold-fabrication gate above
    # exactly. After any conditional-review Rashi task, the target daf must
    # produce zero repetition violations AND zero remaining repetition-
    # baseline entries; the baseline may only shrink, target-scoped, with no
    # entry's maxCount/skeleton modified. This never touches count-mismatch
    # debt, which has no drain path anywhere in the pipeline.
    rep_out = sh([sys.executable, "scripts/validate_rashi_repetition.py"], cwd=YROOT)
    target_rep_violations = [l for l in rep_out.stdout.splitlines()
                              if l.strip().startswith("ERROR") and f"{target}:" in l]
    rb_rel = REPETITION_BASELINE.relative_to(REPO).as_posix()
    rbr = sh(["git", "show", f"{mb}:{rb_rel}"])
    old_rb = json.loads(rbr.stdout).get("entries", []) if rbr.returncode == 0 else []
    new_rb = repetition_baseline_entries()
    old_rmap = {(e["daf"], e["skeleton"]): e.get("maxCount") for e in old_rb}
    new_rmap = {(e["daf"], e["skeleton"]): e.get("maxCount") for e in new_rb}
    rb_added = sorted(set(new_rmap) - set(old_rmap))
    rb_changed = sorted(k for k in set(new_rmap) & set(old_rmap) if new_rmap[k] != old_rmap[k])
    rb_foreign = sorted(k for k in set(old_rmap) - set(new_rmap) if k[0] != target)
    rb_remaining_target = sorted(k for k in new_rmap if k[0] == target)
    conditions["repetition-clean-on-target"] = not target_rep_violations and not rb_remaining_target
    if target_rep_violations:
        notes.append(f"repetition gate on {target}: {len(target_rep_violations)} violation(s) remain")
    if rb_remaining_target:
        notes.append(f"repetition-baseline still lists {target}: {rb_remaining_target}")
    conditions["repetition-baseline-shrink-only"] = not rb_added and not rb_changed and not rb_foreign
    for k in rb_added:
        notes.append(f"repetition-baseline entry ADDED: {k}")
    for k in rb_changed:
        notes.append(f"repetition-baseline entry modified: {k}")
    for k in rb_foreign:
        notes.append(f"repetition-baseline entry removed outside target daf: {k}")

    # Packet completeness and link legality against the live segment table.
    sys.path.insert(0, str(YSCRIPTS))
    import make_rashi_work_packet as mrwp
    import audit_rashi_semantic as ars
    table = {s["id"] for s in mrwp.local_segments_for(target)}
    lpath = REPO / ACTIVE_MODULE["paths"]["learningDataDir"] / f"{target}.learning.json"
    entries = json.loads(lpath.read_text()).get("rashiTranslations", []) if lpath.exists() else []
    used = {i for e in entries for i in e.get("linkedGemaraLineIds", [])}
    empty = [e["vilnaLine"] for e in entries if not e.get("linkedGemaraLineIds")]
    illegal = sorted(used - table)
    conditions["packet-contains-every-linked-local-id"] = bool(table) and not illegal
    if illegal:
        notes.append(f"linked ids not in the packet segment table: {illegal}")

    # Empty linkedGemaraLineIds are legal ONLY for entries the boundary
    # registry authorizes (a Rashi comment whose Gemara content is truncated
    # at the daf's last line and completes on the next daf has no valid
    # same-daf target, and cross-daf links are prohibited). The authoritative
    # answer comes from the canonical validator via
    # authorized_empty_vilna_lines, never from a second reading of the
    # registry here: any stale, duplicate, nonexistent-entry, now-nonempty,
    # or over-ratchet authorization anywhere in the registry collapses that
    # helper to an empty set, so every empty entry then reads unauthorized.
    #
    # The worker must ALSO declare each one in the fresh self-review's
    # authorizedEmptyLinks, and may not claim any that is not both actually
    # empty and registry-authorized. Registry and declaration must agree
    # exactly, in both directions.
    self_review = None
    if SELF_REVIEW_PATH.exists():
        try:
            self_review = json.loads(SELF_REVIEW_PATH.read_text())
        except json.JSONDecodeError:
            self_review = None

    import validate_rashi_boundary_authorizations as vrba
    authorized_vl, registry_errors = vrba.authorized_empty_vilna_lines(target)
    declared_vl = {a.get("vilnaLine") for a in (self_review or {}).get("authorizedEmptyLinks", [])
                   if isinstance(a, dict)}
    empty_set = set(empty)
    unauthorized = sorted(empty_set - authorized_vl)
    undeclared = sorted(empty_set - declared_vl)
    overclaimed = sorted(declared_vl - (empty_set & authorized_vl))
    conditions["all-links-legal-and-empty-links-authorized"] = (
        bool(entries) and not illegal and not registry_errors
        and not unauthorized and not undeclared and not overclaimed
    )
    for e in registry_errors:
        notes.append(f"boundary registry invalid: {e}")
    if unauthorized:
        notes.append(f"empty linkedGemaraLineIds with no boundary authorization: {unauthorized}")
    if undeclared:
        notes.append(f"authorized empty entries missing from self-review authorizedEmptyLinks: {undeclared}")
    if overclaimed:
        notes.append(f"self-review authorizedEmptyLinks claims not backed by an empty, registry-authorized entry: {overclaimed}")
    if empty and not (unauthorized or undeclared or overclaimed or registry_errors):
        notes.append(f"empty linkedGemaraLineIds authorized by the boundary registry and declared: {sorted(empty_set)}")

    # Post-edit drift: realignment/reconstruction must restore full
    # alignment (ALIGNED, tightened to zero missing anchors and all
    # offsets exactly 0), or qualify for the one-anchor-safe or
    # zero-anchor-safe evidence tier (see drift_ok_for_type); structural
    # repair on an anchor-poor daf keeps its own, broader, unconditional
    # line-level-safe allowance. drift_ok_for_type never mutates the
    # classification itself and never accepts SHIFTED or
    # FABRICATION-SUSPECT.
    prof = ars.profile_daf(target, ars.load_allowlisted())
    ok, extra_key, note = drift_ok_for_type(m["type"], target, prof, self_review, entries)
    conditions["drift-profile-ALIGNED"] = ok
    if extra_key:
        conditions[extra_key] = ok
    if note:
        notes.append(note)

    ra = sh([sys.executable, "scripts/audit_rashi_semantic.py", target], cwd=YROOT)
    conditions["semantic-audit-zero-shift-candidates"] = "0 shift candidate(s)" in ra.stdout
    if "0 shift candidate(s)" not in ra.stdout:
        notes.append("scoped semantic audit reports shift candidates on the target daf")

    stub = [e["vilnaLine"] for e in entries
            if re.search(r"Rashi line \d+|: continuation\.?$", e.get("en", ""))]
    seen, dupes = {}, []
    for e in entries:
        seen.setdefault(e.get("en", ""), []).append(e["vilnaLine"])
    dupes = {k[:40]: v for k, v in seen.items() if len(v) > 1 and k}
    conditions["no-stub-or-duplicate-helpers"] = not stub and not dupes
    if stub:
        notes.append(f"stub-pattern helpers remain on lines {stub}")
    if dupes:
        notes.append(f"duplicate helper English: {dupes}")

    fr = sh([sys.executable, "scripts/check_generated_freshness.py"], cwd=YROOT)
    conditions["generated-files-fresh"] = fr.returncode == 0

    version = (REPO / "VERSION").read_text().strip()
    pkg = json.loads((REPO / "package.json").read_text())["version"]
    lock = json.loads((REPO / "package-lock.json").read_text())["version"]
    conditions["version-metadata-synced"] = version == pkg == lock

    # Fresh post-edit self-review: the attestation must be part of THIS
    # PR's diff (that is what makes it fresh), name the target daf, tick
    # every required recheck, and report no blockers.
    sr_ok, why = False, ""
    if ".worker-self-review.json" not in changed:
        why = ".worker-self-review.json is not part of this PR's diff (a fresh post-edit self-review is required)"
    elif not SELF_REVIEW_PATH.exists():
        why = ".worker-self-review.json missing from the working tree"
    else:
        try:
            sr = json.loads(SELF_REVIEW_PATH.read_text())
            missing = [c for c in SELF_REVIEW_CHECKS if sr.get("rechecked", {}).get(c) is not True]
            if sr.get("daf") != target:
                why = f"self-review daf {sr.get('daf')!r} does not match target {target!r}"
            elif missing:
                why = f"self-review rechecks missing or false: {missing}"
            elif sr.get("blockersFound"):
                why = f"self-review reports blockers: {sr['blockersFound']}"
            else:
                sr_ok = True
        except json.JSONDecodeError as ex:
            why = f"self-review file unparseable: {ex}"
    conditions["fresh-self-review-committed-and-clean"] = sr_ok
    if not sr_ok:
        notes.append(why)

    return conditions, notes


def cmd_review(opts):
    """Conditional-review auto-merge gate. Exit 0 with AUTO-MERGE-ELIGIBLE
    only when every machine-checked condition passes; otherwise exit 1 with
    the exact failed conditions and the escalation target."""
    m, spec = load_manifest(opts.manifest)
    policy = review_policy_of(spec)
    if policy == "independent":
        print(f"REVIEW: task type {m['type']} requires an independent Sonnet review; "
              "there is no auto-merge gate. Request the independent review and stop.")
        sys.exit(1)
    if policy != "conditional":
        print(f"REVIEW: task type {m['type']} has no review gate (policy: {policy}).")
        return
    base = resolve_base(opts.base)
    conditions, notes = gather_review_conditions(m, spec, base)
    eligible, failed = evaluate_review_policy(conditions)
    print(f"Conditional review gate (type {m['type']}, targets {m.get('targets')}, base {base}):\n")
    for k in conditions:
        print(f"  {'PASS' if conditions[k] else 'FAIL'}  {k}")
    for n in notes:
        print(f"  note: {n}")
    print("\nProcedural conditions (not observable here, still mandatory):")
    print("  - worker:verify --fast and --full both passed on this head")
    print("  - CI is green on the exact final head at merge time")
    if eligible:
        print("\nAUTO-MERGE-ELIGIBLE: all machine-checked conditions pass. Merge only "
              "when CI is green on this exact head; then verify both deploy workflows "
              "and advance the queue.")
    else:
        print(f"\nESCALATE to {spec.get('escalationModel', 'sonnet')}: failed condition(s) "
              f"{failed}. Do NOT merge.")
        sys.exit(1)


# ---------------- queue (sequential autopilot) ----------------

QUEUE_PATH = REPO / ".worker-queue.json"


def merged_manifest_evidence(override=None):
    """The last worker manifest MERGED to origin/main: the durable evidence
    queue progress derives from. Never reads the working tree (an unmerged
    manifest is not evidence). --evidence FILE overrides for tests."""
    if override:
        try:
            return json.loads(Path(override).read_text())
        except (OSError, json.JSONDecodeError):
            return {}
    sh(["git", "fetch", "origin", "main"])  # best-effort freshness
    r = sh(["git", "show", "origin/main:.worker-manifest.json"])
    if r.returncode != 0:
        return {}
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {}


def derive_queue_progress(q, evidence):
    """Pure derivation of (done, remaining) from the immutable queue
    definition and the merged-manifest evidence. Sequential-by-design: the
    evidence names the LAST merged target for this queue's type/module;
    under the enforced one-PR-per-target sequential process, everything at
    or before that index is complete. A manifest of another type/module, a
    target outside the queue, or a merely-local (unmerged) manifest never
    advances anything, so failed or escalated targets can never become
    done."""
    targets = q["targets"]
    if (evidence.get("type") == q["type"]
            and evidence.get("module") == q["module"]
            and len(evidence.get("targets", [])) == 1
            and evidence["targets"][0] in targets):
        i = targets.index(evidence["targets"][0])
        return targets[:i + 1], targets[i + 1:]
    return [], list(targets)


def cmd_queue(opts):
    """Sequential autopilot queue: ordered targets, one PR per target,
    merge+deploy verification between targets, stop-on-escalation.

    The tracked queue file is an IMMUTABLE definition (type, module,
    ordered targets, policy) committed once alongside the first target's
    manifest. Progress is DERIVED from merged-PR evidence (the manifest at
    origin/main), never stored: there is no runtime state to mutate, so
    completing the final target leaves a clean tree and nothing ever needs
    a direct push to main. Resuming after a container or session recycle
    needs only a fresh clone: derivation is a pure function of the
    definition and origin/main."""
    qpath = Path(opts.file) if opts.file else QUEUE_PATH
    if opts.advance:
        sys.exit("ERROR: --advance is retired. Queue progress is derived from merged PR "
                 "evidence (origin/main:.worker-manifest.json); there is no runtime state "
                 "to mutate, no completion commit, and never a direct push to main.")
    if opts.targets:
        if not opts.type:
            sys.exit("ERROR: queue creation requires --type")
        types = load_registry()
        if opts.type not in types:
            sys.exit(f"ERROR: unknown task type {opts.type!r}")
        set_active_module(resolve_active_module(opts.module))
        targets = [t.strip() for t in opts.targets.split(",") if t.strip()]
        for t in targets:
            if not (YROOT / "assets" / "talmuddev" / f"{t}.json").exists():
                sys.exit(f"ERROR: {t}: no talmuddev source")
        q = {"type": opts.type, "module": opts.module, "targets": targets,
             "policy": "stop-on-escalation"}
        qpath.write_text(json.dumps(q, indent=1) + "\n")
        print(f"queue definition written to {qpath}: {len(targets)} target(s), one PR per "
              "target, sequential merge+deploy, stop-on-escalation. Commit it with the "
              "FIRST target's manifest commit; it is immutable afterward (progress is "
              "derived from merged PRs, never written back).")
        return
    if not qpath.exists():
        sys.exit(f"ERROR: no queue at {qpath}; create one with --type/--targets")
    q = json.loads(qpath.read_text())
    set_active_module(resolve_active_module(q["module"]))
    done, remaining = derive_queue_progress(q, merged_manifest_evidence(opts.evidence))
    print(f"queue: type {q['type']}, module {q['module']}, policy {q['policy']}")
    print(f"done (derived from merged PRs): {done or 'none'} | remaining: {remaining or 'none'}")
    if remaining:
        nxt = remaining[0]
        print(f"\nNext target: {nxt}. One PR for this daf only. Before starting, verify the")
        print("previous merge's deploy workflows are green, then run the read-only capability")
        print("scan across the remaining queue once per campaign (not per daf) to catch any")
        print("unsupported anchor-cardinality or packet-completeness state before content work:")
        print(f"  npm run worker:capability-scan -- --targets {','.join(remaining)}")
        print("If it reports UNSUPPORTED for any target, stop and escalate; do not edit content")
        print("for that daf until the tooling gap is resolved. Otherwise, command sequence:")
        print(f"  npm run worker:manifest -- --type {q['type']} --module {q['module']} "
              f"--range {nxt} --out .worker-manifest.json")
        print("  npm run worker:preflight -- --manifest .worker-manifest.json")
        print("  npm run worker:packet -- --manifest .worker-manifest.json")
        print("  npm run worker:prompt -- --manifest .worker-manifest.json")
        print("  (edit, regenerate, VERSION bump, self-review, verify --fast/--full, PR, CI)")
        print("  npm run worker:review -- --manifest .worker-manifest.json")
        print("  (merge when eligible AND CI green; verify all deploy workflows; then rerun")
        print("   npm run worker:queue, and progress advances automatically from the merge)")
        print("Stop the queue on ANY escalation condition; do not continue past it.")
    else:
        print("\nQueue complete. No queue-state commit is needed and the tree stays clean:")
        print("completion is derived from merged PR evidence, never pushed to main.")


# ---------------- capability-scan ----------------

def capability_report_for(daf):
    """Read-only per-daf capability assessment: never edits content.
    Classifies the daf's raw Hebrew by anchor cardinality (ZERO, ONE,
    MULTI), confirms packet/local-segment completeness, and states
    whether the current review-gate tiers can represent a legitimate
    AUTO-MERGE-ELIGIBLE final state for it. Returns a plain dict (JSON-
    serializable) so a whole queue's results can be reported together."""
    sys.path.insert(0, str(YSCRIPTS))
    import make_rashi_work_packet as mrwp
    import audit_rashi_semantic as ars

    tpath = YROOT / "assets" / "talmuddev" / f"{daf}.json"
    lpath = REPO / ACTIVE_MODULE["paths"]["learningDataDir"] / f"{daf}.learning.json"
    entry = {"daf": daf, "supported": False, "issues": []}
    if not tpath.exists():
        entry["issues"].append("no talmuddev source")
        return entry
    if not lpath.exists():
        entry["issues"].append("no learning JSON")
        return entry

    try:
        raw = [l for l in json.loads(tpath.read_text()).get("rashi", []) if l and l.strip()]
    except json.JSONDecodeError as ex:
        entry["issues"].append(f"talmuddev source unparseable: {ex}")
        return entry
    try:
        trans = json.loads(lpath.read_text()).get("rashiTranslations", [])
    except json.JSONDecodeError as ex:
        entry["issues"].append(f"learning JSON unparseable: {ex}")
        return entry

    entry["rawCount"] = len(raw)
    entry["translationCount"] = len(trans)
    if len(raw) != len(trans):
        entry["issues"].append(f"raw count {len(raw)} != translation count {len(trans)}")
    seq_ok = [e.get("vilnaLine") for e in trans] == list(range(1, len(raw) + 1))
    entry["sequenceOk"] = seq_ok
    if not seq_ok:
        entry["issues"].append("vilnaLine sequence does not match 1..raw count")

    try:
        segs = mrwp.local_segments_for(daf)
        entry["localSegmentIds"] = len(segs)
        empty_he = [s["id"] for s in segs if not (s.get("he") or "").strip()]
        if empty_he:
            entry["issues"].append(f"local segment(s) with empty Hebrew text: {empty_he}")
        if not segs:
            entry["issues"].append("zero local segment ids (packet cannot anchor any link)")
    except Exception as ex:  # noqa: BLE001 - report, never crash the scan
        entry["issues"].append(f"packet/local-segment extraction failed: {ex}")

    prof = ars.profile_daf(daf, ars.load_allowlisted())
    if not prof:
        entry["issues"].append("no drift profile available")
        return entry
    n_anchors = len(prof.get("anchors", []))
    entry["classification"] = prof["classification"]
    entry["anchorCount"] = n_anchors
    entry["anchorsFound"] = prof.get("anchorsFound")
    entry["anchorsMissing"] = prof.get("anchorsMissing")
    entry["cardinality"] = "ZERO" if n_anchors == 0 else ("ONE" if n_anchors == 1 else "MULTI")

    if prof["classification"] == "SHIFTED":
        entry["issues"].append("current profile is SHIFTED (needs rashi-realignment content work first)")
    elif prof["classification"] == "FABRICATION-SUSPECT":
        entry["issues"].append("current profile is FABRICATION-SUSPECT (needs rashi-reconstruction "
                                "content work first)")

    if entry["cardinality"] == "ZERO":
        scan_ok, scan_detail = independent_zero_citation_scan(daf)
        entry["independentZeroScan"] = scan_detail
        if not scan_ok:
            entry["issues"].append(f"independent second scan disagrees with ZERO cardinality: "
                                    f"{scan_detail}")

    entry["supportedFinalStates"] = {
        "ZERO": "zero-anchor-safe (requires full-daf self-review attestation)",
        "ONE": "one-anchor-safe (requires one-anchor self-review attestation)",
        "MULTI": "multi-anchor-safe (requires ALIGNED, zero missing, all offsets 0)",
    }[entry["cardinality"]]
    entry["supported"] = not any(
        "unparseable" in i or "no talmuddev" in i or "no learning JSON" in i
        or "no drift profile" in i or "empty Hebrew text" in i
        or "zero local segment ids" in i or "independent second scan disagrees" in i
        for i in entry["issues"])
    return entry


def cmd_capability_scan(opts):
    """Read-only preflight over an entire target list (or the tracked
    queue): classifies every daf by anchor cardinality, confirms packet
    and local-segment completeness, and states whether the review-gate
    evidence tiers can represent a legitimate final state for it. Never
    edits content. Exits 1 if any target is unsupported, so a campaign
    can be blocked before the first content PR rather than discovering a
    tooling gap mid-queue."""
    if opts.targets:
        targets = [t.strip() for t in opts.targets.split(",") if t.strip()]
        set_active_module(resolve_active_module(opts.module))
    else:
        qpath = Path(opts.file) if opts.file else QUEUE_PATH
        if not qpath.exists():
            sys.exit(f"ERROR: no --targets given and no queue at {qpath}")
        q = json.loads(qpath.read_text())
        targets = q["targets"]
        # The queue file's own module, not --module, when reading from a
        # queue - consistent with cmd_queue's own read path.
        set_active_module(resolve_active_module(q["module"]))

    report = [capability_report_for(d) for d in targets]
    unsupported = [r for r in report if not r["supported"]]

    print(f"Campaign capability scan ({len(targets)} target(s)):\n")
    for r in report:
        status = "OK" if r["supported"] else "UNSUPPORTED"
        card = r.get("cardinality", "?")
        print(f"  {status:11s} {r['daf']:6s} cardinality={card:5s} "
              f"raw={r.get('rawCount', '?')} trans={r.get('translationCount', '?')} "
              f"segIds={r.get('localSegmentIds', '?')} class={r.get('classification', '?')}")
        for issue in r["issues"]:
            print(f"               note: {issue}")

    if opts.json:
        print("\n" + json.dumps(report, indent=1))

    if unsupported:
        print(f"\n{len(unsupported)} unsupported target(s): {[r['daf'] for r in unsupported]}")
        print("FAILED: campaign cannot represent a legitimate final state for every target above.")
        sys.exit(1)
    print(f"\nOK: all {len(targets)} target(s) can reach a supported final review-gate state "
          "(ZERO/ONE/MULTI anchor cardinality all covered).")


# ---------------- schema-matrix ----------------

SCHEMA_SCOPE = Path(__file__).parent / "worker_schema_scope.json"


def cmd_schema_matrix(opts):
    """Cross-check the schema inventory against the task-type registry.

    For every classified path, compute which task types can edit it (via
    their jsonScope mutable/flagMutable patterns, or the Rashi contract for
    rashiTranslations en/links). FAIL if: a path classified as editable has
    no owning task type; a path classified immutable/generated-only IS
    reachable by some type's mutable patterns; or an inventory entry is
    missing a known classification. Print the full matrix with --print."""
    inv = json.loads(SCHEMA_SCOPE.read_text())["paths"]
    types = load_registry()
    legal_class = {"immutable", "manifest-editable", "judgment-required", "flag-only",
                   "generated-only", "deprecated", "delete-only"}
    RASHI_MUTABLE = {"rashiTranslations[*].en", "rashiTranslations[*].linkedGemaraLineIds[*]"}
    errors = []
    matrix = {}

    for path, cls in inv.items():
        if cls not in legal_class:
            errors.append(f"{path}: unknown classification {cls!r}")
            continue
        owners, flag_owners, delete_owners = [], [], []
        if path in RASHI_MUTABLE:
            owners += ["rashi-repair", "rashi-reconstruction", "rashi-realignment", "placeholder-backfill"]
        ptr = "/" + "/".join(seg.replace("[*]", "/0") for seg in path.split("."))
        for tname, tspec in types.items():
            scope = tspec.get("jsonScope")
            if not scope:
                continue
            if any(pattern_to_regex(p).match(ptr) for p in scope.get("mutable", [])):
                owners.append(tname)
            for flag, pats in scope.get("flagMutable", {}).items():
                if any(pattern_to_regex(p).match(ptr) for p in pats):
                    flag_owners.append(f"{tname}({flag})")
            if any(pattern_to_regex(p, allow_children=False).match(ptr)
                   for p in scope.get("deleteOnly", [])):
                delete_owners.append(tname)
        matrix[path] = {"class": cls, "taskTypes": sorted(set(owners)),
                        "flagTaskTypes": sorted(set(flag_owners)),
                        "deleteTaskTypes": sorted(set(delete_owners))}

        if cls in ("manifest-editable", "judgment-required") and not owners:
            errors.append(f"{path}: classified {cls} but NO task type can edit it")
        if cls == "flag-only" and not flag_owners:
            errors.append(f"{path}: classified flag-only but no flagMutable pattern reaches it")
        if cls == "delete-only" and not delete_owners:
            errors.append(f"{path}: classified delete-only but no deleteOnly pattern reaches it")
        if cls == "delete-only" and owners:
            errors.append(f"{path}: classified delete-only but also reachable as plain-mutable "
                          f"by {owners} (a delete-only path may never be editable in place)")
        if cls in ("immutable", "generated-only", "deprecated") and owners:
            errors.append(f"{path}: classified {cls} but reachable by {owners}")
        if cls == "manifest-editable":
            ok = any(types[o].get("mechanicalTier") for o in owners)
            if not ok:
                errors.append(f"{path}: classified manifest-editable but no owning type "
                              f"declares mechanicalTier")

    if opts.print_matrix:
        print(json.dumps(matrix, indent=1))
    if errors:
        print("SCHEMA MATRIX CHECK FAILED:\n")
        for e in errors:
            print(f"  ERROR  {e}")
        sys.exit(1)
    n_by = {}
    for v in matrix.values():
        n_by[v["class"]] = n_by.get(v["class"], 0) + 1
    print(f"OK: schema matrix consistent: {len(matrix)} paths "
          f"({', '.join(f'{k}={v}' for k, v in sorted(n_by.items()))}); "
          f"every editable path has an owning task type and no immutable path is reachable.")


# ---------------- docs ----------------

def cmd_docs(opts):
    """Regenerate the machine-generated reference docs from the registry and
    schema inventory: docs/reports/task-type-reference.md and
    docs/reports/schema-coverage-matrix.md. Run after any registry or
    inventory change and commit the result."""
    types = load_registry()
    L = ["# Worker task-type reference (generated)",
         "",
         "Generated by `npm run worker:docs` from scripts/worker_task_types.json.",
         "Do not hand-edit; regenerate after registry changes.", ""]
    for name in sorted(types):
        s = types[name]
        L.append(f"## {name}")
        L.append("")
        L.append(s["description"])
        L.append("")
        pol = review_policy_of(s)
        pol_txt = {"independent": "; independent Sonnet review required before merge",
                   "conditional": f"; review: conditional auto-merge gate (worker self-review "
                                  f"+ worker:review; escalation to {s.get('escalationModel', 'sonnet')})",
                   "none": ""}[pol]
        L.append(f"- model: {s['model']}"
                 + ("; PAUSED" if s.get("paused") else "")
                 + pol_txt)
        L.append(f"- escalation model: {s.get('escalationModel', 'sonnet')}")
        L.append(f"- lifecycle: {lifecycle_of(s)}"
                 + ("  (no VERSION bump, no commit, no PR)" if lifecycle_of(s) == "read-only"
                    else "  (one VERSION patch bump, one PR)"))
        L.append(f"- mechanical tier: {'yes' if s.get('mechanicalTier') else 'no'}")
        L.append(f"- max batch: {s.get('maxBatch', 1 if s.get('requiresTarget') else 'n/a')}")
        if s.get("requiredAuthorizations"):
            L.append(f"- REQUIRED authorization: {', '.join(s['requiredAuthorizations'])} "
                     f"(operator-issued; preflight fails without it)")
        L.append(f"- allowed files: {', '.join(s['allowedFiles']) or 'none (read-only task)'}")
        if s.get("jsonScope"):
            L.append(f"- mutable JSON paths: {', '.join(s['jsonScope']['mutable'])}")
            for flag, pats in sorted(s["jsonScope"].get("flagMutable", {}).items()):
                L.append(f"- with --authorize {flag}: {', '.join(pats)}")
        elif s.get("allowedJsonPaths"):
            L.append(f"- mutable JSON paths: {', '.join(s['allowedJsonPaths'])}")
        L.append(f"- allowlist policy: {s['allowlistPolicy']}; structure policy: {s['structurePolicy']}")
        L.append(f"- required validators: {', '.join(s['requiredValidators']) or 'none'}")
        L.append("- stop conditions:")
        for e in s["escalationTriggers"]:
            L.append(f"  - {e}")
        L.append("")
    (REPO / "docs" / "reports" / "task-type-reference.md").write_text("\n".join(L))

    inv = json.loads(SCHEMA_SCOPE.read_text())["paths"]
    M = ["# Schema coverage matrix (generated)",
         "",
         "Generated by `npm run worker:docs` from scripts/worker_schema_scope.json.",
         "Consistency with the registry is enforced by `npm run worker:schema-matrix`",
         "(run in CI on every manifest-bearing PR). High-risk paths (structure, ids,",
         "sourceRefs, Hebrew, argumentFlow, quiz/misconception content) are",
         "judgment-required because their correctness needs semantic or structural",
         "judgment that pattern gates cannot verify. Sonnet executes every tier.", "",
         "| path | classification |", "|---|---|"]
    for path in sorted(inv):
        M.append(f"| `{path}` | {inv[path]} |")
    M.append("")
    M.append("Known drift: argumentFlow sourceRefs carry 550 referential defects")
    M.append("across 102 daf (412 mechanically repairable, 138 needing content")
    M.append("judgment), plus 331 sound refs still in the older string form.")
    M.append("Nothing renders them today, so this is latent data debt. The full")
    M.append("inventory, canonical schema and four-PR migration plan are in")
    M.append("docs/reports/source-refs-normalization-plan.md; check current state")
    M.append("with `npm run validate:sourcerefs:yoma`.")
    (REPO / "docs" / "reports" / "schema-coverage-matrix.md").write_text("\n".join(M) + "\n")
    print("wrote docs/reports/task-type-reference.md and docs/reports/schema-coverage-matrix.md")


# ---------------- report ----------------

def cmd_report(opts):
    """Emit the machine-readable final report template, prefilled with what
    is derivable locally. The worker fills prNumber/mergeCommit/deploys
    after merge and posts the JSON block verbatim."""
    m, spec = load_manifest(opts.manifest)
    base = resolve_base(None)
    mb = sh(["git", "merge-base", base, "HEAD"]).stdout.strip()
    changed = [l for l in sh(["git", "diff", "--name-only", mb]).stdout.splitlines() if l.strip()] if mb else []
    ca = YSCRIPTS / "allowlists" / "rashi_content_allowlist.json"
    r = sh(["git", "show", f"{mb}:{ca.relative_to(REPO).as_posix()}"]) if mb else None
    old_n = len(json.loads(r.stdout).get("entries", [])) if r and r.returncode == 0 else None
    new_n = len(json.loads(ca.read_text()).get("entries", []))
    report = {
        "taskType": m["type"],
        "targets": m["targets"],
        "version": (REPO / "VERSION").read_text().strip(),
        "branch": sh(["git", "rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip(),
        "filesChanged": changed,
        "allowlistDelta": {"before": old_n, "after": new_n},
        "independentReviewRequired": m.get("independentReviewRequired", False),
        "lifecycle": m.get("lifecycle", "pr"),
        "reviewPolicy": review_policy_of(spec),
        "selfReviewRecorded": SELF_REVIEW_PATH.exists(),
        "prNumber": "<fill after PR creation>",
        "mergeCommit": "<fill after merge>",
        "gates": "<fill: verify --full result>",
        "deploys": {"cloudways": "<fill>", "githubPages": "<fill>"},
        "escalations": [],
    }
    print(json.dumps(report, indent=1))


# ---------------- ci-check ----------------

def cmd_ci_check(opts):
    base = resolve_base(opts.base)
    mb = sh(["git", "merge-base", base, "HEAD"]).stdout.strip()
    if not mb:
        print(f"WARNING: cannot resolve merge-base of {base!r}; skipping ci-check.")
        return
    changed = [l for l in sh(["git", "diff", "--name-only", mb]).stdout.splitlines() if l.strip()]
    content_changed = [p for p in changed if p.startswith(all_content_prefixes())]
    workflow_changed = [p for p in changed if p.startswith(".github/workflows/")]
    # The manifest counts as part of the PR if it exists and is new or
    # different relative to the base (a stale leftover identical to the base
    # does not count; every PR must bring its own manifest).
    manifest_present = False
    if MANIFEST_DEFAULT.exists():
        r = sh(["git", "show", f"{mb}:.worker-manifest.json"])
        manifest_present = r.returncode != 0 or r.stdout != MANIFEST_DEFAULT.read_text()

    if not content_changed and not workflow_changed:
        print("OK: no module content or workflow changes; manifest not required.")
        return

    if not manifest_present:
        if content_changed:
            print("CI MANIFEST CHECK FAILED:\n")
            print("  ERROR  module content changed but no .worker-manifest.json is part of this PR.")
            print("  Generate one, e.g.:")
            print("    npm run worker:manifest -- --type rashi-repair --module yoma --range <daf> --out .worker-manifest.json")
            print("  and commit it with the content change.")
            sys.exit(1)
        # workflow-only change without manifest: require docs-tooling manifest
        print("CI MANIFEST CHECK FAILED:\n")
        print("  ERROR  workflow files changed but no .worker-manifest.json (docs-tooling) is part of this PR.")
        print("  Workflow edits require an explicit docs-tooling manifest and pipeline-level review.")
        sys.exit(1)

    m, spec = load_manifest(MANIFEST_DEFAULT)
    if workflow_changed and m["type"] != "docs-tooling":
        print(f"CI MANIFEST CHECK FAILED: workflow files changed but manifest type is {m['type']!r}, not docs-tooling.")
        sys.exit(1)
    # Registry/inventory consistency is part of every manifest-bearing PR.
    matrix_ns = argparse.Namespace(print_matrix=False)
    cmd_schema_matrix(matrix_ns)
    scope_ns = argparse.Namespace(manifest=str(MANIFEST_DEFAULT), base=opts.base)
    cmd_scope(scope_ns)

    # Merge-base monotonic ratchet, enforced in CI for every PR that changes
    # the active module's learning data, independent of task type. This is
    # the enforcement point the GitHub Actions workflow actually calls
    # (`worker_pipeline.py ci-check --base origin/<base-ref>`); see
    # cmd_verify's identically-named local gate for the worker-facing half
    # of the same check. Neither replaces the frozen-baseline comparison
    # that validate_enrichment_contracts.py always runs; this is additive.
    learning_dir = ACTIVE_MODULE["paths"]["learningDataDir"]
    learning_file = ACTIVE_MODULE["paths"]["learningDataFile"]
    learning_data_changed = any(
        p == learning_file or p.startswith(learning_dir + "/") for p in changed)
    if learning_data_changed:
        rc = sh([sys.executable, "scripts/validate_enrichment_contracts.py",
                "--module", m["module"], "--compare-ref", mb])
        print(f"\nenrichment-regression-vs-merge-base (compare-ref {mb[:12]}):")
        print(rc.stdout[-2500:])
        if rc.returncode != 0:
            print(rc.stderr[-800:])
            sys.exit(1)

    print(f"OK: PR carries a valid {m['type']} manifest and passes its scope contract.")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("manifest")
    p.add_argument("--type", required=True)
    p.add_argument("--module", default="yoma")
    p.add_argument("--range", default=None)
    p.add_argument("--out", default=None)
    p.add_argument("--authorize", action="append", default=None,
                   help="grant an optional authorization defined by the task type "
                        "(e.g. authorizeQuizSeeds); repeatable; operator-issued only")
    p.add_argument("--drain-allowlist", action="store_true",
                   help="snapshot the target daf's CURRENT pre-existing content-allowlist "
                        "entries into the manifest, authorizing preflight to start "
                        "rashi-reconstruction/rashi-realignment despite that debt (single "
                        "target only); the snapshot is repair debt to eliminate, not an "
                        "exemption, and worker:verify fails if any snapshotted entry is not "
                        "cleanly removed as validator-confirmed stale")
    p.add_argument("--vilna-line", type=int, default=None,
                   help=f"required for --type {REPAIR_TASK_TYPE}: the boundary-authorized "
                        f"entry's vilnaLine, together with --range's single daf forming its "
                        f"registryIdentity")
    p.add_argument("--entry-id", default=None,
                   help=f"required for --type {REPAIR_TASK_TYPE}: the entryId this repair "
                        f"authorizes (must match a record in --review-record)")
    p.add_argument("--review-record", default=None,
                   help=f"required for --type {REPAIR_TASK_TYPE}: path to the Step 6 batch "
                        f"review-record JSON documenting a CONFIRMED second pass for --entry-id")
    p.add_argument("--audit-record-id", action="append", default=None,
                   help=f"required for --type {AUDIT_RECORD_TASK_TYPE}, repeatable: a "
                        f"sugyaId from the merged tail-enrichment audit this PR repairs. "
                        f"Real manifest data (stored as auditRecordIds), never an "
                        f"authorization flag.")
    p.add_argument("--migration-kind", action="append", default=None,
                   help="required for --type enrichment-schema-migration, repeatable: "
                        "one of requires-understanding, visualizable-elements, difficulty. "
                        "Real manifest data (stored as migrationKinds), never an "
                        "authorization flag.")

    for name in ("preflight", "packet", "prompt"):
        p = sub.add_parser(name)
        p.add_argument("--manifest", default=str(MANIFEST_DEFAULT))
        if name == "preflight":
            p.add_argument("--dry-run", action="store_true")

    p = sub.add_parser("verify")
    p.add_argument("--manifest", default=str(MANIFEST_DEFAULT))
    p.add_argument("--fast", action="store_true")
    p.add_argument("--full", action="store_true")
    p.add_argument("--base", default=None)

    p = sub.add_parser("scope")
    p.add_argument("--manifest", default=str(MANIFEST_DEFAULT))
    p.add_argument("--base", default=None)

    p = sub.add_parser("ci-check")
    p.add_argument("--base", default=None)

    p = sub.add_parser("review")
    p.add_argument("--manifest", default=str(MANIFEST_DEFAULT))
    p.add_argument("--base", default=None)

    p = sub.add_parser("queue")
    p.add_argument("--type", default=None)
    p.add_argument("--module", default="yoma")
    p.add_argument("--targets", default=None,
                   help="comma-separated ordered daf list; creates/overwrites the queue")
    p.add_argument("--advance", default=None,
                   help="RETIRED: progress derives from merged PR evidence; this flag only errors")
    p.add_argument("--file", default=None, help="queue file path (default .worker-queue.json)")
    p.add_argument("--evidence", default=None,
                   help="test override: read merged-manifest evidence from FILE instead of origin/main")

    p = sub.add_parser("capability-scan")
    p.add_argument("--targets", default=None,
                   help="comma-separated daf list; defaults to the tracked queue's targets")
    p.add_argument("--module", default="yoma",
                   help="module to scan; only used with --targets (reading from a queue file "
                        "uses that queue's own declared module instead). Explicit documented "
                        "default of 'yoma' for backwards compatibility with existing campaign "
                        "instructions that invoke this without --module.")
    p.add_argument("--file", default=None, help="queue file path (default .worker-queue.json)")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("report")
    p.add_argument("--manifest", default=str(MANIFEST_DEFAULT))

    p = sub.add_parser("schema-matrix")
    p.add_argument("--print", dest="print_matrix", action="store_true")

    sub.add_parser("docs")

    opts = ap.parse_args()
    {"manifest": cmd_manifest, "preflight": cmd_preflight, "packet": cmd_packet,
     "prompt": cmd_prompt, "verify": cmd_verify, "scope": cmd_scope,
     "ci-check": cmd_ci_check, "report": cmd_report, "review": cmd_review,
     "queue": cmd_queue, "capability-scan": cmd_capability_scan,
     "schema-matrix": cmd_schema_matrix, "docs": cmd_docs}[opts.cmd](opts)


if __name__ == "__main__":
    main()
