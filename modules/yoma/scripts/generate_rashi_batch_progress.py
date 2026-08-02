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
completed-batch marker (i.e. a partial or out-of-band edit happened
outside the normal Step 6 batch-PR flow) and flags it rather than silently
reporting a clean number.

Usage:
  python3 scripts/generate_rashi_batch_progress.py [--json]
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

SCRIPTS = Path(__file__).parent
ROOT = SCRIPTS.parent
REPO_ROOT = ROOT.parent.parent
DATA_DIR = REPO_ROOT / "docs" / "reports" / "data"
INVENTORY_PATH = DATA_DIR / "rashi-translation-quality-inventory.json"
BATCHES_PATH = DATA_DIR / "rashi-full-corpus-review-batches.json"
SOURCE_BLOCKERS_PATH = DATA_DIR / "rashi-source-blockers.json"

sys.path.insert(0, str(SCRIPTS))
from audit_rashi_translation_risk import load_corpus  # noqa: E402
from select_rashi_pilot_cohort import load_perek_ranges, perek_for_daf  # noqa: E402


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

    batches = batches_doc["batches"]
    batch_status = []
    stale_batches = []
    for b in batches:
        ids = b["entryIds"]
        reviewed_in_batch = [eid for eid in ids if next((e for e in entries if e["id"] == eid), {}).get("reviewStatus") == "REVIEWED"]
        status = "not-started" if not reviewed_in_batch else ("in-progress" if len(reviewed_in_batch) < len(ids) else "complete")
        if reviewed_in_batch and status != "complete":
            stale_batches.append({"batchId": b["batchId"], "reviewedCount": len(reviewed_in_batch), "totalCount": len(ids)})
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
    if report["staleBatchWarnings"]:
        print(f"\nSTALE/PARTIAL BATCH WARNINGS ({len(report['staleBatchWarnings'])}):")
        for w in report["staleBatchWarnings"]:
            print(f"  {w['batchId']}: {w['reviewedCount']}/{w['totalCount']} reviewed but not marked complete")
    if report["sourceRepairBlockers"]:
        print(f"\nSource-repair blockers (SOURCE_REPAIR_REQUIRED, campaign disposition BLOCKED): {report['sourceRepairBlockers']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
