#!/usr/bin/env python3
"""
test_generate_rashi_systemic_candidates.py - regression tests for
generate_rashi_systemic_candidates.py: determinism, no pilot (REVIEWED)
entries in either candidate family, every candidate is genuinely
UNREVIEWED and actually contains its trigger condition, and no
disposition/repair field appears anywhere in the output.

Offline, no network. Run from modules/yoma/:
  python3 scripts/test_generate_rashi_systemic_candidates.py
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

FAILED = []


def check(name, cond, detail=""):
    print(f"  {'ok ' if cond else 'FAIL'} {name}" + (f" ({detail})" if detail and not cond else ""))
    if not cond:
        FAILED.append(name)


inv = json.loads(INVENTORY_PATH.read_text())
inv_by_id = {e["id"]: e for e in inv["entries"]}
reviewed_ids = {e["id"] for e in inv["entries"] if e["reviewStatus"] == "REVIEWED"}

with tempfile.TemporaryDirectory() as tmp:
    out1 = Path(tmp) / "cand1.json"
    out2 = Path(tmp) / "cand2.json"

    r1 = subprocess.run([sys.executable, str(SCRIPTS / "generate_rashi_systemic_candidates.py"),
                         "--out", str(out1)], cwd=str(ROOT), capture_output=True, text=True)
    check("1. script exits 0", r1.returncode == 0, r1.stderr[-500:])

    r2 = subprocess.run([sys.executable, str(SCRIPTS / "generate_rashi_systemic_candidates.py"),
                         "--out", str(out2)], cwd=str(ROOT), capture_output=True, text=True)
    check("2. determinism: two runs produce byte-identical output", out1.read_text() == out2.read_text())

    doc = json.loads(out1.read_text())
    scaffold = doc["families"]["new_comment_scaffold"]["candidates"]
    anticipation = doc["families"]["cross_entry_word_anticipation"]["candidates"]

    # The Step 6 review campaign is actively draining the "New comment:"
    # scaffold family from the unreviewed corpus batch by batch, so a
    # hardcoded non-empty expectation goes stale (and eventually false) as
    # batches complete. Cross-check the generator's count against an
    # independent, obviously-correct count instead of assuming a fixed
    # corpus condition: this still catches a genuinely broken generator
    # (wrong count) while remaining correct once the family is fully
    # drained to 0.
    expected_scaffold_count = sum(
        1 for e in inv["entries"]
        if e["reviewStatus"] == "UNREVIEWED" and "New comment:" in e["en"]
    )
    check("3. scaffold candidate count matches an independent corpus count",
          len(scaffold) == expected_scaffold_count,
          f"generator={len(scaffold)} independent={expected_scaffold_count}")
    check("4. every scaffold candidate's English actually contains the marker",
          all("New comment:" in c["en"] for c in scaffold))
    check("5. no scaffold candidate is a pilot (REVIEWED) entry",
          not any(c["entryId"] in reviewed_ids for c in scaffold))

    check("6. anticipation candidates non-empty", len(anticipation) > 0, len(anticipation))
    check("7. every anticipation candidate is OVEREXPLAINED-flagged in the live inventory",
          all(any(s["tag"] == "OVEREXPLAINED" for s in inv_by_id[c["entryId"]]["riskSignals"]) for c in anticipation))
    check("8. no anticipation candidate is a pilot (REVIEWED) entry",
          not any(c["entryId"] in reviewed_ids for c in anticipation))

    forbidden_keys = {"disposition", "finalDisposition", "firstPassDisposition", "repairPR", "finalVerificationSHA"}
    check("9. no candidate carries a disposition or repair field (candidates only, never a verdict)",
          not any(forbidden_keys & set(c.keys()) for c in scaffold + anticipation))

if FAILED:
    print(f"\n{len(FAILED)} check(s) failed: {FAILED}")
    sys.exit(1)
print("\nAll checks passed.")
