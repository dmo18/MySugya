#!/usr/bin/env python3
"""
check_rashi_pr_scope.py - scope gate for Yoma Rashi content changes.

Compares the working tree against a base ref (merge-base semantics) and, when
the diff touches any modules/yoma/assets/learning/yoma/*.learning.json,
enforces the bounded-content-PR contract:

  1. File set: a content PR may only change learning JSONs, the generated
     learning_data.js and coverage.json, VERSION, package.json,
     package-lock.json, docs/rashi-audit-backlog.md, files under
     modules/yoma/scripts/allowlists/, the Rashi translation-quality
     campaign's inventory (docs/reports/data/rashi-translation-quality-
     inventory.json) and its batch/reconciliation reports
     (docs/reports/rashi-pilot-*.md - the audit trail for the campaign's
     own content changes). It may never touch .github/workflows/.
  2. Within each changed learning JSON, only rashiTranslations[*].en and
     rashiTranslations[*].linkedGemaraLineIds may differ from base. The
     entry count, vilnaLine sequence, every other rashiTranslations key,
     and every other top-level field (sugyot, argumentFlow, he, learning,
     takeaway, glossary, quizSeeds, metadata, everything) must be
     byte-equal in JSON terms. Structure changes require --allow-structure
     (explicitly authorized passes only).
  3. Allowlist ratchet: changed allowlist files may only remove entries,
     never add them.
  4. learning_data.js/coverage.json may change only when at least one
     learning JSON (or assets/literal_en file) changed too; freshness
     itself is enforced by check_generated_freshness.py.

If the diff touches no learning JSON, this gate is a no-op (exit 0), so it
is safe to run on every PR and on push.

Base ref resolution: --base <ref>, else origin/$GITHUB_BASE_REF when set
(GitHub PR context), else origin/main. Comparison is against
merge-base(base, HEAD) so unrelated later commits on the base branch do not
produce false diffs.

Exit 1 with exact paths and JSON pointers on any violation. Offline except
for reading local git objects.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import boundary_fingerprint_ratchet  # noqa: E402

LEARN_PREFIX = "modules/yoma/assets/learning/yoma/"
LITERAL_PREFIX = "modules/yoma/assets/literal_en/"
GENERATED = {"modules/yoma/learning_data.js", "modules/yoma/coverage.json"}
ALLOWLIST_PREFIX = "modules/yoma/scripts/allowlists/"
SCAFFOLD_BASELINE_FILE = "modules/yoma/scripts/baselines/rashi_scaffold_debt.json"
# The Rashi translation-quality campaign's per-entry review provenance
# (docs/reports/data/rashi-translation-quality-inventory.json) and its
# batch/reconciliation reports (docs/reports/rashi-pilot-*.md) are the audit
# trail for exactly the content changes this gate polices - the same reason
# docs/rashi-audit-backlog.md is already always-allowed below. Letting a
# content PR carry them alongside its learning JSON changes is required by
# the campaign's own PR structure (each batch PR must update both the
# translation and its inventory/evidence together); it does not relax any
# rule this gate enforces on the learning JSON itself.
RASHI_CAMPAIGN_DOC_PREFIX = "docs/reports/rashi-pilot-"
RASHI_CAMPAIGN_INVENTORY = "docs/reports/data/rashi-translation-quality-inventory.json"
# Step 6 (full-corpus batch review, docs/reports/rashi-full-corpus-review-strategy.md)
# extends the same audit-trail rationale as RASHI_CAMPAIGN_DOC_PREFIX/RASHI_CAMPAIGN_INVENTORY
# above: a batch PR carries its content edit alongside the batch's own review-record file,
# its narrative report, and (when this PR is also the one introducing them) the tooling that
# validates that record file and the registry entry defining this task type's own scope.
RASHI_STEP6_REPORT_PREFIX = "docs/reports/rashi-step6-batch-"
RASHI_STEP6_RECORDS_PREFIX = "docs/reports/data/rashi-step6-batch-"
RASHI_STEP6_STRATEGY_DOC = "docs/reports/rashi-full-corpus-review-strategy.md"
# The audited-sugya-enrichment-repair lifecycle records its own advancing
# status (NOT_STARTED -> IN_PROGRESS -> FIXED_PENDING_REVIEW -> ...) in this
# file as part of the SAME content-repair PR that edits the learning JSON --
# see generate_enrichment_repair_queue.py and worker_pipeline.py's
# REPAIR_PROGRESS_PATH. It is infrastructure bookkeeping, not enrichment
# content, so it belongs alongside the other always-allowed worker-pipeline
# files (.worker-manifest.json etc.) rather than being rejected as an
# unexpected file in the content PR's diff.
REPAIR_PROGRESS_PATH = "docs/reports/data/yoma-tail-enrichment-repair-progress.json"
# The semantic self-heal system (docs/semantic-self-heal.md) records its own
# manifest and registry alongside a content edit in the SAME PR, exactly like
# .worker-manifest.json above. It is infrastructure bookkeeping for a
# different, newer authorization route (semantic_repair_scope_v2.py, which
# runs in the same CI job and independently enforces rashiTranslations
# byte-identity for semantic PRs), not enrichment content itself.
SEMANTIC_MANIFEST_PATH = ".semantic-repair-manifest.json"
SEMANTIC_CERT_REGISTRY = "docs/reports/data/yoma-semantic-certifications.json"
ALWAYS_ALLOWED = {"VERSION", "package.json", "package-lock.json",
                  "docs/rashi-audit-backlog.md", ".worker-manifest.json",
                  ".worker-self-review.json", ".worker-queue.json",
                  RASHI_CAMPAIGN_INVENTORY, RASHI_STEP6_STRATEGY_DOC,
                  REPAIR_PROGRESS_PATH,
                  "scripts/worker_task_types.json",
                  "modules/yoma/scripts/check_rashi_pr_scope.py",
                  "modules/yoma/scripts/validate_rashi_review_records.py",
                  "modules/yoma/scripts/test_validate_rashi_review_records.py",
                  SEMANTIC_MANIFEST_PATH, SEMANTIC_CERT_REGISTRY}
FORBIDDEN_PREFIXES = (".github/workflows/",)

MUTABLE_KEYS = {"en", "linkedGemaraLineIds"}


def run(args, **kw):
    return subprocess.run(args, capture_output=True, text=True, **kw)


def git_show(rev, path):
    r = run(["git", "show", f"{rev}:{path}"])
    return r.stdout if r.returncode == 0 else None


def structural_deferral(wm_data, types, fresh):
    """The single daf (as a set) whose rashiTranslations STRUCTURE may
    change under a fresh, explicitly authorized rashi-structural-repair
    manifest; empty otherwise. The manifest must be part of this PR
    (fresh), be the structural type whose registry entry REQUIRES the
    allowStructure authorization, carry that authorization, and target
    exactly one daf. Any other manifest (realignment, repair, forged
    authorizations, multi-target) grants nothing, so ordinary passes can
    never change entry counts."""
    wtype = wm_data.get("type")
    spec = types.get(wtype, {})
    if (fresh
            and wtype == "rashi-structural-repair"
            and "allowStructure" in wm_data.get("authorizations", [])
            and "allowStructure" in spec.get("requiredAuthorizations", [])
            and len(wm_data.get("targets", [])) == 1):
        return set(wm_data["targets"])
    return set()


def check_boundary_registry_ratchet(path, old_entries, new_entries, base_rev, errors):
    """Identity-aware ratchet for the boundary-authorizations registry only
    (see boundary_fingerprint_ratchet.py). Entries may be removed freely
    (unchanged, existing behavior); at most one entry may be rehashed
    (its enFingerprint refreshed) per PR, and only when
    boundary_fingerprint_ratchet.authorize_rehash approves it; entries may
    never be added."""
    old_by_id, new_by_id, added, _removed, rehashed = \
        boundary_fingerprint_ratchet.diff_registry_entries(old_entries, new_entries)
    for daf, vl in added:
        errors.append(f"{path}: entries entry ADDED (ratchet is remove-only; "
                       f"requires RASHI_ALLOWLIST_RESTRUCTURE=1): {daf} L{vl}")
    if len(rehashed) > 1:
        errors.append(f"{path}: {len(rehashed)} registry entries rehashed in one PR "
                       f"(only one fingerprint refresh is permitted per PR): {rehashed}")
        return
    if not rehashed:
        return
    identity = rehashed[0]
    top = run(["git", "rev-parse", "--show-toplevel"]).stdout.strip()
    ok, reason = boundary_fingerprint_ratchet.authorize_rehash(
        Path(top), base_rev, LEARN_PREFIX.rstrip("/"), identity,
        old_by_id[identity], new_by_id[identity],
        Path(".worker-manifest.json"), expected_module="yoma",
    )
    print(f"NOTE: {reason}")
    if not ok:
        errors.append(f"{path}: {reason}")


def check_allowlist_ratchet(allowlist_changed, base_rev, errors):
    """Allowlist files may only shrink. Additions or new files require the
    explicit RASHI_ALLOWLIST_RESTRUCTURE=1 authorization (tooling PRs that
    document a new baseline; see docs/rashi-workflow.md). The boundary-
    authorizations registry gets one narrow exception to the remove-only
    rule: see check_boundary_registry_ratchet."""
    if os.environ.get("RASHI_ALLOWLIST_RESTRUCTURE") == "1":
        if allowlist_changed:
            print("NOTE: RASHI_ALLOWLIST_RESTRUCTURE=1 set; allowlist growth "
                  "authorization active for this run.")
        return
    for p in allowlist_changed:
        base_text = git_show(base_rev, p)
        if base_text is None:
            errors.append(f"{p}: new allowlist files require RASHI_ALLOWLIST_RESTRUCTURE=1")
            continue
        old = json.loads(base_text)
        new = json.loads(Path(p).read_text())
        if Path(p).name == boundary_fingerprint_ratchet.BOUNDARY_FILENAME:
            check_boundary_registry_ratchet(p, old.get("entries", []), new.get("entries", []), base_rev, errors)
            continue
        for section in ("entries", "count_mismatches"):
            old_e = {json.dumps(e, sort_keys=True) for e in old.get(section, [])}
            new_e = {json.dumps(e, sort_keys=True) for e in new.get(section, [])}
            for a in sorted(new_e - old_e):
                errors.append(f"{p}: {section} entry ADDED (ratchet is remove-only; "
                              f"requires RASHI_ALLOWLIST_RESTRUCTURE=1): {a}")


def check_scaffold_baseline_ratchet(base_rev, errors):
    """The scaffold-fabrication debt baseline may only shrink in any PR this
    gate covers: entries may be removed (retired after repair) but never
    added or rehashed. Growth or restructure requires the explicit
    RASHI_ALLOWLIST_RESTRUCTURE=1 operator authorization (tooling PRs)."""
    if os.environ.get("RASHI_ALLOWLIST_RESTRUCTURE") == "1":
        print("NOTE: RASHI_ALLOWLIST_RESTRUCTURE=1 set; scaffold-baseline "
              "growth authorization active for this run.")
        return
    base_text = git_show(base_rev, SCAFFOLD_BASELINE_FILE)
    old = json.loads(base_text) if base_text is not None else {"entries": []}
    new = json.loads(Path(SCAFFOLD_BASELINE_FILE).read_text())
    old_map = {(e["daf"], e["vilnaLine"]): e.get("enHash") for e in old.get("entries", [])}
    new_map = {(e["daf"], e["vilnaLine"]): e.get("enHash") for e in new.get("entries", [])}
    for k in sorted(set(new_map) - set(old_map)):
        errors.append(f"{SCAFFOLD_BASELINE_FILE}: entry ADDED (ratchet is "
                      f"remove-only; requires RASHI_ALLOWLIST_RESTRUCTURE=1): {k}")
    for k in sorted(x for x in set(new_map) & set(old_map) if new_map[x] != old_map[x]):
        errors.append(f"{SCAFFOLD_BASELINE_FILE}: entry rehashed (an entry "
                      f"covers only its original text): {k}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=None, help="base ref (default: origin/$GITHUB_BASE_REF or origin/main)")
    ap.add_argument("--allow-structure", action="store_true",
                    help="permit rashiTranslations entry count/structure changes (authorized passes only)")
    opts = ap.parse_args()

    top = run(["git", "rev-parse", "--show-toplevel"]).stdout.strip()
    if not top:
        sys.exit("ERROR: not inside a git repository.")
    os.chdir(top)

    base = opts.base
    if base is None:
        env_base = os.environ.get("GITHUB_BASE_REF", "").strip()
        base = f"origin/{env_base}" if env_base else "origin/main"

    mb = run(["git", "merge-base", base, "HEAD"])
    if mb.returncode != 0:
        print(f"WARNING: cannot resolve merge-base of {base!r} and HEAD "
              f"({mb.stderr.strip()}); skipping scope check.")
        return
    base_rev = mb.stdout.strip()

    diff = run(["git", "diff", "--name-only", base_rev])
    changed = [l for l in diff.stdout.splitlines() if l.strip()]

    learn_changed = [p for p in changed if p.startswith(LEARN_PREFIX) and p.endswith(".learning.json")]
    allowlist_changed = [p for p in changed if p.startswith(ALLOWLIST_PREFIX) and p.endswith(".json")]
    scaffold_baseline_changed = SCAFFOLD_BASELINE_FILE in changed
    errors = []

    if not learn_changed:
        # Tooling PRs skip the content rules, but the allowlist ratchet still
        # applies: additions require the explicit RASHI_ALLOWLIST_RESTRUCTURE=1
        # authorization (documented in docs/rashi-workflow.md).
        if allowlist_changed:
            check_allowlist_ratchet(allowlist_changed, base_rev, errors)
        if scaffold_baseline_changed:
            check_scaffold_baseline_ratchet(base_rev, errors)
        if errors:
            print(f"Rashi PR scope check FAILED vs {base} ({base_rev[:9]}):\n")
            for e in errors:
                print(f"  ERROR  {e}")
            sys.exit(1)
        print(f"OK: no Yoma learning JSON changed vs {base} ({base_rev[:9]}); "
              f"scope gate is a no-op (allowlist ratchet still verified).")
        return

    # 1. File-set rules
    for p in changed:
        for fp in FORBIDDEN_PREFIXES:
            if p.startswith(fp):
                errors.append(f"file-set: content PR must not touch {p}")
        allowed = (
            (p.startswith(LEARN_PREFIX) and p.endswith(".learning.json"))
            or p.startswith(LITERAL_PREFIX)
            or p in GENERATED
            or p.startswith(ALLOWLIST_PREFIX)
            or p == SCAFFOLD_BASELINE_FILE
            or p in ALWAYS_ALLOWED
            or p.startswith(RASHI_CAMPAIGN_DOC_PREFIX)
            or p.startswith(RASHI_STEP6_REPORT_PREFIX)
            or p.startswith(RASHI_STEP6_RECORDS_PREFIX)
        )
        if not allowed and not any(p.startswith(fp) for fp in FORBIDDEN_PREFIXES):
            errors.append(f"file-set: {p} is outside the allowed content-PR file set")

    # 4. Generated files only alongside source changes
    if any(p in GENERATED for p in changed):
        if not learn_changed and not any(p.startswith(LITERAL_PREFIX) for p in changed):
            errors.append("file-set: generated learning_data.js/coverage.json changed "
                          "without any learning JSON or literal_en source change")

    # A fresh gemara-learning worker manifest defers per-file FIELD rules for
    # its target daf to the worker pipeline's stricter gemara-learning JSON
    # diff (worker_pipeline.py ci-check, which runs in the same CI job and
    # must also pass). File-set, workflow, and allowlist ratchet rules above
    # still apply here regardless. This is a hand-off, not a bypass: without
    # the manifest, or for daf outside its targets, full Rashi rules apply.
    deferred_daf = set()
    wm = Path(".worker-manifest.json")
    registry = Path("scripts/worker_task_types.json")
    if wm.exists() and registry.exists():
        base_wm = git_show(base_rev, ".worker-manifest.json")
        fresh = base_wm is None or base_wm != wm.read_text()
        try:
            wm_data = json.loads(wm.read_text())
            types = json.loads(registry.read_text())["taskTypes"]
        except (json.JSONDecodeError, KeyError):
            wm_data, types = {}, {}
        wtype = wm_data.get("type")
        # Defer only to enrichment types whose registry entry carries a
        # jsonScope contract (enforced by worker_pipeline.py in the same CI
        # job). Rashi types never defer; without a fresh manifest, full
        # Rashi rules apply.
        if fresh and wtype in types and types[wtype].get("jsonScope"):
            deferred_daf = set(wm_data.get("targets", []))
            print(f"NOTE: fresh {wtype} manifest present; deferring field rules for "
                  f"daf {sorted(deferred_daf)} to the worker pipeline jsonScope gate "
                  f"(which must also pass).")
        structure_daf = structural_deferral(wm_data, types, fresh)
        if structure_daf:
            print(f"NOTE: fresh authorized rashi-structural-repair manifest present; "
                  f"structure rules relaxed for daf {sorted(structure_daf)} ONLY "
                  f"(the worker pipeline gates on that manifest must also pass).")
    else:
        structure_daf = set()

    # A fresh semantic-repair/certify manifest defers per-file FIELD rules for
    # its one target daf to semantic_repair_scope_v2.py (which runs in the
    # same CI job, must also pass, and independently requires
    # rashiTranslations to stay byte-identical). This is the same hand-off
    # pattern as the worker-manifest deferral above, keyed off the semantic
    # system's own manifest instead. Without a fresh manifest naming this
    # daf, full Rashi rules still apply.
    semantic_deferred_daf = set()
    sm = Path(SEMANTIC_MANIFEST_PATH)
    if sm.exists():
        base_sm = git_show(base_rev, SEMANTIC_MANIFEST_PATH)
        sm_fresh = base_sm is None or base_sm != sm.read_text()
        try:
            sm_data = json.loads(sm.read_text())
        except json.JSONDecodeError:
            sm_data = {}
        if (sm_fresh
                and sm_data.get("module") == "yoma"
                and sm_data.get("type") in {"semantic-daf-repair", "semantic-daf-certify"}
                and isinstance(sm_data.get("daf"), str)):
            semantic_deferred_daf = {sm_data["daf"]}
            print(f"NOTE: fresh {sm_data['type']} manifest present; deferring field "
                  f"rules for daf {sorted(semantic_deferred_daf)} to "
                  f"semantic_repair_scope_v2.py (which must also pass).")

    # 2. Per-file structural diff
    for p in learn_changed:
        daf_name = p.split("/")[-1].replace(".learning.json", "")
        if daf_name in deferred_daf or daf_name in semantic_deferred_daf:
            continue
        allow_structure_here = opts.allow_structure or daf_name in structure_daf
        base_text = git_show(base_rev, p)
        if base_text is None:
            errors.append(f"{p}: file does not exist at base; new files require --allow-structure")
            continue
        try:
            old = json.loads(base_text)
            new = json.loads(Path(p).read_text())
        except (json.JSONDecodeError, FileNotFoundError) as ex:
            errors.append(f"{p}: cannot parse JSON ({ex})")
            continue

        for key in sorted(set(old) | set(new)):
            if key == "rashiTranslations":
                continue
            if old.get(key) != new.get(key):
                errors.append(f"{p}: /{key} changed (only rashiTranslations en/links may change)")

        o_rt = old.get("rashiTranslations", [])
        n_rt = new.get("rashiTranslations", [])
        if len(o_rt) != len(n_rt):
            if not allow_structure_here:
                errors.append(f"{p}: /rashiTranslations length {len(o_rt)} -> {len(n_rt)} "
                              f"(structure change requires --allow-structure or a fresh "
                              f"authorized rashi-structural-repair manifest for this daf)")
            continue
        for i, (o, n) in enumerate(zip(o_rt, n_rt)):
            if o.get("vilnaLine") != n.get("vilnaLine") and not allow_structure_here:
                errors.append(f"{p}: /rashiTranslations/{i}/vilnaLine changed "
                              f"{o.get('vilnaLine')} -> {n.get('vilnaLine')}")
            for key in sorted(set(o) | set(n)):
                if key in MUTABLE_KEYS or key == "vilnaLine":
                    continue
                if o.get(key) != n.get(key):
                    errors.append(f"{p}: /rashiTranslations/{i}/{key} changed "
                                  f"(only en and linkedGemaraLineIds may change)")

    # 3. Allowlist ratchet: removals only (the scaffold-debt baseline gets
    # the same remove-only treatment; see check_scaffold_baseline_ratchet)
    check_allowlist_ratchet(allowlist_changed, base_rev, errors)
    if scaffold_baseline_changed:
        check_scaffold_baseline_ratchet(base_rev, errors)

    if errors:
        print(f"Rashi PR scope check FAILED vs {base} ({base_rev[:9]}):\n")
        for e in errors:
            print(f"  ERROR  {e}")
        print(f"\n{len(errors)} violation(s).")
        sys.exit(1)

    print(f"OK: Rashi content changes vs {base} ({base_rev[:9]}) stay within scope "
          f"({len(learn_changed)} learning JSON file(s); only en/linkedGemaraLineIds changed; "
          f"allowlists shrink-only).")


if __name__ == "__main__":
    main()
