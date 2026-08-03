#!/usr/bin/env python3
"""
test_generate_rashi_batch_progress.py - regression tests for
generate_rashi_batch_progress.py: totals reconcile against the live
inventory, JSON mode matches text-mode facts, and stale/partial-batch
detection fires when a batch's entries are found REVIEWED without the
batch being fully complete - except for a DECLARED multi-PR child rollout
(a batch whose own report documents a child-PR split and whose reviewed
entries partition cleanly by daf), which is real, expected progress, not
staleness.

Offline, no network. Run from modules/yoma/:
  python3 scripts/test_generate_rashi_batch_progress.py
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).parent
ROOT = SCRIPTS.parent
REPO_ROOT = ROOT.parent.parent
INVENTORY_PATH = REPO_ROOT / "docs" / "reports" / "data" / "rashi-translation-quality-inventory.json"

sys.path.insert(0, str(SCRIPTS))
import generate_rashi_batch_progress as gbp  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    print(f"  {'ok ' if cond else 'FAIL'} {name}" + (f" ({detail})" if detail and not cond else ""))
    if not cond:
        FAILED.append(name)


r = subprocess.run([sys.executable, str(SCRIPTS / "generate_rashi_batch_progress.py"), "--json"],
                    cwd=str(ROOT), capture_output=True, text=True)
check("1. script exits 0", r.returncode == 0, r.stderr[-500:])

report = json.loads(r.stdout)
inv = json.loads(INVENTORY_PATH.read_text())

check("2. totalEntries matches live inventory count", report["totalEntries"] == len(inv["entries"]))
check("3. reviewedCount + unreviewedCount == totalEntries",
      report["reviewedCount"] + report["unreviewedCount"] == report["totalEntries"])
check("4. reviewedCount matches a fresh count of REVIEWED entries",
      report["reviewedCount"] == sum(1 for e in inv["entries"] if e["reviewStatus"] == "REVIEWED"))
check("5. dispositionCounts sums to reviewedCount",
      sum(report["dispositionCounts"].values()) == report["reviewedCount"])
check("6. no UNDECLARED batch is currently stale (fresh plan, or only declared child-PR rollouts in progress)",
      report["staleBatchWarnings"] == [])
check("7. rashi-yoma-009b-001 is no longer a source-repair blocker (resolved in Step 6 PR A)",
      "rashi-yoma-009b-001" not in report["sourceRepairBlockers"] and report["sourceRepairBlockers"] == [])
check("8. text-mode output runs without error",
      subprocess.run([sys.executable, str(SCRIPTS / "generate_rashi_batch_progress.py")],
                      cwd=str(ROOT), capture_output=True, text=True).returncode == 0)


def _fixture_entries():
    return {
        "e1": {"id": "e1", "daf": "10a"}, "e2": {"id": "e2", "daf": "10a"},
        "e3": {"id": "e3", "daf": "10b"}, "e4": {"id": "e4", "daf": "10b"},
    }


check("9. daf-clean partition: a whole daf reviewed, a whole daf not, is clean",
      gbp._daf_partition_clean(["e1", "e2", "e3", "e4"], _fixture_entries(), {"e1", "e2"}))
check("10. daf-clean partition: one daf half-reviewed is NOT clean (genuine partial edit shape)",
      not gbp._daf_partition_clean(["e1", "e2", "e3", "e4"], _fixture_entries(), {"e1", "e3"}))
check("11. daf-clean partition: nothing reviewed is trivially clean",
      gbp._daf_partition_clean(["e1", "e2", "e3", "e4"], _fixture_entries(), set()))

with tempfile.TemporaryDirectory() as tmp:
    tmp_root = Path(tmp)
    old_repo_root = gbp.REPO_ROOT
    try:
        gbp.REPO_ROOT = tmp_root
        reports_dir = tmp_root / "docs" / "reports"
        reports_dir.mkdir(parents=True)
        (reports_dir / "rashi-step6-batch-999-report.md").write_text(
            "# Report\n\n## Child-PR split (change-count cap)\n\ntext\n", encoding="utf-8")
        (reports_dir / "rashi-step6-batch-998-report.md").write_text(
            "# Report\n\nNo split section here.\n", encoding="utf-8")
        check("12. declared child-PR split heading detected when present",
              gbp._has_declared_child_pr_split("step6-batch-999"))
        check("13. no declared split when the heading is absent from an existing report",
              not gbp._has_declared_child_pr_split("step6-batch-998"))
        check("14. no declared split when the report file does not exist at all",
              not gbp._has_declared_child_pr_split("step6-batch-997"))
    finally:
        gbp.REPO_ROOT = old_repo_root

check("15. every batch flagged as a declared in-progress rollout actually has the heading in its own report",
      all(gbp._has_declared_child_pr_split(w["batchId"]) for w in report["declaredInProgressBatches"]))
check("16. every batch still flagged stale has NO declared child-PR split in its own report "
      "(genuinely undeclared/out-of-band, not a recognized rollout)",
      all(not gbp._has_declared_child_pr_split(w["batchId"]) for w in report["staleBatchWarnings"]))

if FAILED:
    print(f"\n{len(FAILED)} check(s) failed: {FAILED}")
    sys.exit(1)
print("\nAll checks passed.")
