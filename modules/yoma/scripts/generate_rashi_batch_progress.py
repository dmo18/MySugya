#!/usr/bin/env python3
"""
generate_rashi_batch_progress.py - Rashi translation-quality campaign,
Step 5/6: full-corpus review progress report.

Reads the live translation-quality inventory and the full-corpus batch
plan, and reports where the campaign stands: how many entries are
reviewed vs. remaining, disposition totals, daf/perek coverage, which
batches remain, and any blockers. This is a read-only report generator -
it never edits the inventory or the batch plan.

Also performs stale-record detection: for every batch, checks whether any
of its planned entryIds have since become REVIEWED without a matching
completed-batch marker. A batch whose changed-entry count exceeds the
per-PR cap is legitimately applied via several deterministic child PRs
(one per daf) merged sequentially, per docs/reports/rashi-full-corpus-
review-strategy.md - that in-progress state is expected, not stale, and
is recognized as DECLARED (see _daf_partition_clean/_has_declared_child_pr_split)
only when the batch's own report explicitly documents a child-PR split
AND the currently-reviewed entries partition cleanly along daf boundaries
(every daf in the batch is either fully reviewed or not reviewed at all -
the shape a per-daf child-PR rollout always produces, and not one an
accidental or out-of-band partial edit is likely to produce by
coincidence). Anything else partially reviewed is still flagged as a
genuine stale/out-of-band partial edit outside the normal Step 6 flow.

Usage:
  python3 scripts/generate_rashi_batch_progress.py [--json]
"""
import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

SCRIPTS = Path(__file__).parent
ROOT = SCRIPTS.parent
REPO_ROOT = ROOT.parent.parent
DATA_DIR = REPO_ROOT / "docs" / "reports" / "data"
INVENTORY_PATH = DATA_DIR / "rashi-translation-quality-inventory.json"
BATCHES_PATH = DATA_DIR / "rashi-full-corpus-review-batches.json"
SOURCE_BLOCKERS_PATH = DATA_DIR / "rashi-source-blockers.json"
CHILD_PR_SPLIT_HEADING = "## Child-PR split"

sys.path.insert(0, str(SCRIPTS))
from audit_rashi_translation_risk import load_corpus  # noqa: E402
from select_rashi_pilot_cohort import load_perek_ranges, perek_for_daf  # noqa: E402


def _has_declared_child_pr_split(batch_id):
    """True only when this batch's own report.md explicitly documents a
    child-PR split (docs/reports/rashi-<batchId>-report.md contains the
    literal CHILD_PR_SPLIT_HEADING). A batch that has simply never had a
    report written yet, or whose report says nothing about a split, is
    never treated as a declared rollout."""
    report_path = REPO_ROOT / "docs" / "reports" / f"rashi-{batch_id}-report.md"
    if not report_path.exists():
        return False
    return CHILD_PR_SPLIT_HEADING in report_path.read_text(encoding="utf-8")


def _daf_partition_clean(ids, entries_by_id, reviewed_ids):
    """True if, for every distinct daf among this batch's entryIds, either
    ALL of that daf's ids are reviewed or NONE are. This is the exact
    shape a deterministic per-daf child-PR rollout produces at every
    intermediate merge; a genuinely accidental or out-of-band partial
    edit is very unlikely to happen to align to whole-daf boundaries."""
    by_daf = defaultdict(list)
    for eid in ids:
        by_daf[entries_by_id[eid]["daf"]].append(eid)
    for daf_ids in by_daf.values():
        reviewed_count = sum(1 for eid in daf_ids if eid in reviewed_ids)
        if reviewed_count not in (0, len(daf_ids)):
            return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON instead of a text report")
    opts = ap.parse_args()

    inv = json.loads(INVENTORY_PATH.read_text())
    batches_doc = json.loads(BATCHES_PATH.read_text())
    blockers_doc = json.loads(SOURCE_BLOCKERS_PATH.read_text()) if SOURCE_BLOCKERS_PATH.exists() else {"blockers": []}

    entries = inv["entries"]
    total = len(entries)
    reviewed = [e for e in entries if e["reviewStatus"] == "REVIEWED"]
    unreviewed = [e for e in entries if e["reviewStatus"] == "UNREVIEWED"]
    disposition_counts = Counter(e["primaryDisposition"] for e in reviewed)

    daf_order, _rashi_by_daf, _ = load_corpus()
    perek_ranges = load_perek_ranges()
    perek_of = {d: perek_for_daf(d, daf_order, perek_ranges) for d in daf_order}

    daf_reviewed = {e["daf"] for e in reviewed}
    daf_unreviewed = {e["daf"] for e in unreviewed}
    perek_reviewed = {perek_of.get(e["daf"]) for e in reviewed}

    entries_by_id = {e["id"]: e for e in entries}
    reviewed_ids = {e["id"] for e in reviewed}

    batches = batches_doc["batches"]
    batch_status = []
    stale_batches = []
    declared_in_progress = []
    for b in batches:
        ids = b["entryIds"]
        reviewed_in_batch = [eid for eid in ids if next((e for e in entries if e["id"] == eid), {}).get("reviewStatus") == "REVIEWED"]
        status = "not-started" if not reviewed_in_batch else ("in-progress" if len(reviewed_in_batch) < len(ids) else "complete")
        if reviewed_in_batch and status != "complete":
            warning = {"batchId": b["batchId"], "reviewedCount": len(reviewed_in_batch), "totalCount": len(ids)}
            if _has_declared_child_pr_split(b["batchId"]) and _daf_partition_clean(ids, entries_by_id, reviewed_ids):
                declared_in_progress.append(warning)
            else:
                stale_batches.append(warning)
        batch_status.append({"batchId": b["batchId"], "daf": b["daf"], "perek": b["perek"],
                             "entryCount": len(ids), "reviewedCount": len(reviewed_in_batch), "status": status})

    remaining_batches = [b for b in batch_status if b["status"] != "complete"]

    blockers = [b for b in blockers_doc.get("blockers", []) if b.get("planningStatus") == "SOURCE_REPAIR_REQUIRED"]

    report = {
        "generatedFrom": "live inventory + full-corpus batch plan",
        "totalEntries": total,
        "reviewedCount": len(reviewed),
        "unreviewedCount": len(unreviewed),
        "dispositionCounts": dict(disposition_counts),
        "dafCoverage": {"reviewed": len(daf_reviewed), "unreviewed": len(daf_unreviewed), "total": len(daf_reviewed | daf_unreviewed)},
        "perekCoverage": {"reviewed": sorted(p for p in perek_reviewed if p is not None)},
        "totalBatches": len(batches),
        "batchesComplete": sum(1 for b in batch_status if b["status"] == "complete"),
        "batchesInProgress": sum(1 for b in batch_status if b["status"] == "in-progress"),
        "batchesNotStarted": sum(1 for b in batch_status if b["status"] == "not-started"),
        "remainingBatches": [b["batchId"] for b in remaining_batches],
        "staleBatchWarnings": stale_batches,
        "declaredInProgressBatches": declared_in_progress,
        "sourceRepairBlockers": [b["entryId"] for b in blockers],
    }

    if opts.json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
        return 0

    print("Rashi translation-quality campaign - full-corpus progress")
    print("=" * 60)
    print(f"Total entries:      {report['totalEntries']}")
    print(f"Reviewed:           {report['reviewedCount']}")
    print(f"Unreviewed:         {report['unreviewedCount']}")
    print(f"Disposition totals: {report['dispositionCounts']}")
    print(f"Daf coverage:       {report['dafCoverage']['reviewed']}/{report['dafCoverage']['total']} daf have >=1 reviewed entry")
    print(f"Perek coverage:     {report['perekCoverage']['reviewed']}")
    print(f"Batches:            {report['batchesComplete']} complete, {report['batchesInProgress']} in progress, {report['batchesNotStarted']} not started (of {report['totalBatches']})")
    if report["declaredInProgressBatches"]:
        print(f"\nDeclared multi-PR rollout in progress ({len(report['declaredInProgressBatches'])}):")
        for w in report["declaredInProgressBatches"]:
            print(f"  {w['batchId']}: {w['reviewedCount']}/{w['totalCount']} reviewed, child-PR split declared and daf-clean")
    if report["staleBatchWarnings"]:
        print(f"\nSTALE/PARTIAL BATCH WARNINGS ({len(report['staleBatchWarnings'])}):")
        for w in report["staleBatchWarnings"]:
            print(f"  {w['batchId']}: {w['reviewedCount']}/{w['totalCount']} reviewed but not marked complete")
    if report["sourceRepairBlockers"]:
        print(f"\nSource-repair blockers (SOURCE_REPAIR_REQUIRED, campaign disposition BLOCKED): {report['sourceRepairBlockers']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
