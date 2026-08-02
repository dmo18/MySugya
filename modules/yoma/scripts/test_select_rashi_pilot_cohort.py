#!/usr/bin/env python3
"""
test_select_rashi_pilot_cohort.py - regression tests for
select_rashi_pilot_cohort.py: cohort size/daf minimums, every stratum
minimum actually met, determinism, and that every selected id is a real
entry in the live inventory with unmodified he/en text.

Offline, no network. Run from modules/yoma/:
  python3 scripts/test_select_rashi_pilot_cohort.py
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
import select_rashi_pilot_cohort as sc  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    print(f"  {'ok ' if cond else 'FAIL'} {name}" + (f" ({detail})" if detail and not cond else ""))
    if not cond:
        FAILED.append(name)


def run_and_load(out_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "select_rashi_pilot_cohort.py"), "--out", str(out_path)],
        cwd=str(ROOT), capture_output=True, text=True,
    )
    return result, json.loads(out_path.read_text())


with tempfile.TemporaryDirectory() as tmp:
    out1 = Path(tmp) / "cohort1.json"
    out2 = Path(tmp) / "cohort2.json"

    result1, cohort1 = run_and_load(out1)
    check("1. script exits 0", result1.returncode == 0, result1.stderr[-500:])

    result2, cohort2 = run_and_load(out2)
    check("2. determinism: two runs produce byte-identical output",
          out1.read_text() == out2.read_text())

    entries = cohort1["entries"]
    ids = [e["id"] for e in entries]
    check("3. total entries >= 200", len(entries) >= 200, len(entries))
    check("4. all entry ids unique", len(set(ids)) == len(ids))
    daf_set = {e["daf"] for e in entries}
    check("5. daf coverage >= 10", len(daf_set) >= 10, len(daf_set))
    perek_set = {e["perek"] for e in entries}
    check("6. perek coverage >= 3", len(perek_set) >= 3, perek_set)

    for name, minimum in sc.REQUIREMENT_MINIMUMS:
        actual = cohort1["stratumCounts"][name]
        check(f"7. stratum '{name}' >= {minimum}", actual >= minimum, actual)

    for e in entries:
        for field in ("id", "daf", "perek", "vilnaLine", "he", "en", "linkedGemaraLineIds",
                      "riskScore", "riskSignals", "priorReviewDepth", "selectionStratum",
                      "selectionRationale"):
            if field not in e:
                check(f"8. entry {e.get('id')} has field '{field}'", False)
                break
    else:
        check("8. every entry has all required fields", True)

    inventory = json.loads(INVENTORY_PATH.read_text())
    inv_by_id = {e["id"]: e for e in inventory["entries"]}
    mismatches = [
        e["id"] for e in entries
        if e["id"] not in inv_by_id
        or inv_by_id[e["id"]]["he"] != e["he"]
        or inv_by_id[e["id"]]["en"] != e["en"]
    ]
    check("9. every cohort entry's he/en exactly matches the live inventory (no drift, no truncation)",
          not mismatches, mismatches[:5])

    check("10. every entry has at least one selectionStratum tag",
          all(e["selectionStratum"] for e in entries),
          [e["id"] for e in entries if not e["selectionStratum"]][:5])

if FAILED:
    print(f"\n{len(FAILED)} check(s) failed: {FAILED}")
    sys.exit(1)
print("\nAll checks passed.")
