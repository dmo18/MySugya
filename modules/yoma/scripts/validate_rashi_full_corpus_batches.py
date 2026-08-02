#!/usr/bin/env python3
"""
validate_rashi_full_corpus_batches.py - Rashi translation-quality
campaign, Step 5: proves the full-corpus batch plan
(docs/reports/data/rashi-full-corpus-review-batches.json) is safe against
the campaign directive's invariants, and detects a stale plan (one that no
longer matches the live corpus or inventory).

Checks, each fatal on failure:
  1. exact remaining-corpus coverage: every UNREVIEWED entry in the live
     inventory appears in exactly one batch, and no batch contains an
     entry the inventory does not currently list as UNREVIEWED
  2. no duplicate assignment: every entry id appears in at most one batch
  3. no pilot-entry reassignment: no REVIEWED (pilot) entry appears in any
     batch
  4. contiguous daf: every batch's daf list, mapped to corpus daf-order
     positions, is a contiguous run (no gaps)
  5. perek boundary: every daf in a batch maps to the same perek
  6. configured limits: entryCount <= 350, len(daf) <= 8, and each
     tier-specific soft cap is only exceeded when the hard limit is
     already binding (i.e. no batch is looser than its own declared tier)
  7. stable ids: batch ids are unique and sequential (step6-batch-001..N)
  8. stale-data detection: recomputing each daf's tier and each batch's
     entryIds/entryCount from the CURRENT live corpus reproduces the
     committed plan exactly - if the corpus or inventory has changed since
     the plan was generated, this fails loudly rather than silently
     validating a stale plan.

Offline, no network. Exit 1 on any violation with exact batch/entry ids.
"""
import argparse
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).parent
ROOT = SCRIPTS.parent
REPO_ROOT = ROOT.parent.parent
DATA_DIR = REPO_ROOT / "docs" / "reports" / "data"
INVENTORY_PATH = DATA_DIR / "rashi-translation-quality-inventory.json"
BATCHES_PATH = DATA_DIR / "rashi-full-corpus-review-batches.json"

sys.path.insert(0, str(SCRIPTS))
from audit_rashi_translation_risk import load_corpus  # noqa: E402
from select_rashi_pilot_cohort import load_perek_ranges, perek_for_daf  # noqa: E402
import plan_rashi_full_corpus_batches as planner  # noqa: E402

HARD_MAX_ENTRIES = planner.HARD_MAX_ENTRIES
HARD_MAX_DAF = planner.HARD_MAX_DAF
TIER_CAPS = planner.TIER_CAPS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batches", default=str(BATCHES_PATH))
    opts = ap.parse_args()

    errors = []
    batches_doc = json.loads(Path(opts.batches).read_text())
    batches = batches_doc["batches"]

    inv = json.loads(INVENTORY_PATH.read_text())
    inv_by_id = {e["id"]: e for e in inv["entries"]}
    unreviewed_ids = {e["id"] for e in inv["entries"] if e["reviewStatus"] == "UNREVIEWED"}
    reviewed_ids = {e["id"] for e in inv["entries"] if e["reviewStatus"] == "REVIEWED"}

    daf_order, rashi_by_daf, _ = load_corpus()
    daf_index = {d: i for i, d in enumerate(daf_order)}
    perek_ranges = load_perek_ranges()
    perek_of = {d: perek_for_daf(d, daf_order, perek_ranges) for d in daf_order}

    # 1+2+3: coverage, duplicates, pilot reassignment
    seen = {}
    all_assigned = []
    for b in batches:
        for eid in b["entryIds"]:
            all_assigned.append(eid)
            if eid in seen:
                errors.append(f"duplicate assignment: {eid} in both {seen[eid]} and {b['batchId']}")
            seen[eid] = b["batchId"]
            if eid in reviewed_ids:
                errors.append(f"pilot-entry reassignment: {eid} (REVIEWED) assigned to {b['batchId']}")
            if eid not in inv_by_id:
                errors.append(f"unknown entry id in {b['batchId']}: {eid}")

    assigned_set = set(all_assigned)
    missing = unreviewed_ids - assigned_set
    extra = assigned_set - unreviewed_ids
    if missing:
        errors.append(f"{len(missing)} UNREVIEWED entries missing from every batch: {sorted(missing)[:10]}{' ...' if len(missing) > 10 else ''}")
    if extra:
        errors.append(f"{len(extra)} batch entries are not currently UNREVIEWED (stale plan or pilot leak): {sorted(extra)[:10]}{' ...' if len(extra) > 10 else ''}")

    # 4+5: contiguous daf, single perek
    for b in batches:
        daf_list = b["daf"]
        if not daf_list:
            errors.append(f"{b['batchId']}: empty daf list")
            continue
        positions = sorted(daf_index[d] for d in daf_list if d in daf_index)
        if len(positions) != len(daf_list):
            errors.append(f"{b['batchId']}: contains daf not in the live corpus: {daf_list}")
        elif positions != list(range(positions[0], positions[0] + len(positions))):
            errors.append(f"{b['batchId']}: daf list is not contiguous in corpus order: {daf_list}")
        perekim = {perek_of.get(d) for d in daf_list}
        if len(perekim) > 1:
            errors.append(f"{b['batchId']}: spans multiple perakim {perekim}: {daf_list}")
        elif perekim and list(perekim)[0] != b.get("perek"):
            errors.append(f"{b['batchId']}: declared perek {b.get('perek')} does not match actual {perekim}")

    # 6: hard + tier limits
    for b in batches:
        if b["entryCount"] > HARD_MAX_ENTRIES:
            errors.append(f"{b['batchId']}: entryCount {b['entryCount']} exceeds hard max {HARD_MAX_ENTRIES}")
        if len(b["daf"]) > HARD_MAX_DAF:
            errors.append(f"{b['batchId']}: daf count {len(b['daf'])} exceeds hard max {HARD_MAX_DAF}")
        tier = b.get("tier")
        caps = TIER_CAPS.get(tier)
        if caps is None:
            errors.append(f"{b['batchId']}: unknown tier {tier!r}")
        else:
            soft_max_entries = min(caps["max_entries"], HARD_MAX_ENTRIES)
            soft_max_daf = min(caps["max_daf"], HARD_MAX_DAF)
            if b["entryCount"] > soft_max_entries:
                errors.append(f"{b['batchId']}: entryCount {b['entryCount']} exceeds its own tier {tier!r} cap {soft_max_entries}")
            if len(b["daf"]) > soft_max_daf:
                errors.append(f"{b['batchId']}: daf count {len(b['daf'])} exceeds its own tier {tier!r} cap {soft_max_daf}")

    # 7: stable sequential ids
    expected_ids = [f"step6-batch-{i + 1:03d}" for i in range(len(batches))]
    actual_ids = [b["batchId"] for b in batches]
    if actual_ids != expected_ids:
        errors.append(f"batch ids are not sequential step6-batch-001..{len(batches):03d}: {actual_ids[:5]}...")

    # 8: stale-data detection - regenerate to a temp path and diff byte-for-byte
    import io
    import contextlib
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        sys.argv = ["plan_rashi_full_corpus_batches.py", "--out", tmp_path]
        planner.main()
    regenerated = Path(tmp_path).read_text()
    committed = Path(opts.batches).read_text()
    Path(tmp_path).unlink()
    if regenerated != committed:
        errors.append("STALE PLAN: regenerating the batch plan from the current live corpus/inventory "
                      "does not reproduce the committed file byte-for-byte - the corpus or inventory "
                      "changed since this plan was generated; re-run plan_rashi_full_corpus_batches.py.")

    if errors:
        print(f"Batch plan validation FAILED ({len(errors)} violation(s)):\n")
        for e in errors:
            print(f"  ERROR  {e}")
        return 1

    print(f"OK: {len(batches)} batches valid - {len(assigned_set)}/{len(unreviewed_ids)} UNREVIEWED entries "
          f"assigned exactly once, 0 duplicates, 0 pilot entries, all daf contiguous and single-perek, "
          f"all within hard and tier limits, ids sequential, plan matches live corpus (not stale).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
