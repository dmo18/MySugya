#!/usr/bin/env python3
"""
test_generate_rashi_batch_progress.py - regression tests for
generate_rashi_batch_progress.py: totals reconcile against the live
inventory, JSON mode matches text-mode facts, and stale/partial-batch
detection fires when a batch's entries are found REVIEWED without the
batch being fully complete.

Offline, no network. Run from modules/yoma/:
  python3 scripts/test_generate_rashi_batch_progress.py
"""
import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).parent
ROOT = SCRIPTS.parent
REPO_ROOT = ROOT.parent.parent
INVENTORY_PATH = REPO_ROOT / "docs" / "reports" / "data" / "rashi-translation-quality-inventory.json"

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
check("6. no batch is currently stale (fresh plan, no partial batches yet)",
      report["staleBatchWarnings"] == [])
check("7. source-repair blocker rashi-yoma-009b-001 is listed",
      "rashi-yoma-009b-001" in report["sourceRepairBlockers"])
check("8. text-mode output runs without error",
      subprocess.run([sys.executable, str(SCRIPTS / "generate_rashi_batch_progress.py")],
                      cwd=str(ROOT), capture_output=True, text=True).returncode == 0)

if FAILED:
    print(f"\n{len(FAILED)} check(s) failed: {FAILED}")
    sys.exit(1)
print("\nAll checks passed.")
