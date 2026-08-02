#!/usr/bin/env python3
"""
test_generate_rashi_pilot_packets.py - regression tests for
generate_rashi_pilot_packets.py: one packet per cohort entry, no text
truncation/drift against the frozen cohort, every packet carries a linked
Gemara line, blank review fields start empty, and output is deterministic.

Offline, no network. Run from modules/yoma/:
  python3 scripts/test_generate_rashi_pilot_packets.py
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).parent
ROOT = SCRIPTS.parent
REPO_ROOT = ROOT.parent.parent
COHORT_PATH = REPO_ROOT / "docs" / "reports" / "data" / "rashi-pilot-cohort.json"

FAILED = []


def check(name, cond, detail=""):
    print(f"  {'ok ' if cond else 'FAIL'} {name}" + (f" ({detail})" if detail and not cond else ""))
    if not cond:
        FAILED.append(name)


if not COHORT_PATH.exists():
    print("SKIP: frozen cohort not present yet (run select_rashi_pilot_cohort.py first)")
    sys.exit(0)

cohort = json.loads(COHORT_PATH.read_text())

with tempfile.TemporaryDirectory() as tmp:
    out1 = Path(tmp) / "packets1.json"
    out2 = Path(tmp) / "packets2.json"

    r1 = subprocess.run(
        [sys.executable, str(SCRIPTS / "generate_rashi_pilot_packets.py"),
         "--cohort", str(COHORT_PATH), "--out", str(out1)],
        cwd=str(ROOT), capture_output=True, text=True,
    )
    check("1. script exits 0", r1.returncode == 0, r1.stderr[-500:])

    r2 = subprocess.run(
        [sys.executable, str(SCRIPTS / "generate_rashi_pilot_packets.py"),
         "--cohort", str(COHORT_PATH), "--out", str(out2)],
        cwd=str(ROOT), capture_output=True, text=True,
    )
    check("2. determinism: two runs produce byte-identical output",
          out1.read_text() == out2.read_text())

    packets = json.loads(out1.read_text())["packets"]
    check("3. one packet per cohort entry", len(packets) == len(cohort["entries"]),
          (len(packets), len(cohort["entries"])))

    by_id = {p["id"]: p for p in packets}
    check("4. every cohort entry has a packet",
          all(e["id"] in by_id for e in cohort["entries"]))

    mismatches = [
        e["id"] for e in cohort["entries"]
        if by_id.get(e["id"], {}).get("he") != e["he"]
        or by_id.get(e["id"], {}).get("en") != e["en"]
    ]
    check("5. packet he/en exactly matches frozen cohort text (no truncation)",
          not mismatches, mismatches[:5])

    no_linked = [p["id"] for p in packets if not p["gemaraContext"]["linked"]]
    check("6. every packet resolves at least one linked Gemara line",
          not no_linked, no_linked[:5])

    bad_review = [
        p["id"] for p in packets
        if p["review"]["disposition"] is not None
        or p["review"]["defectTags"]
        or p["review"]["finalEnglish"] is not None
        or p["review"]["secondPass"]["result"] is not None
    ]
    check("7. every packet's review block starts blank",
          not bad_review, bad_review[:5])

    check("8. every packet carries its selectionStratum",
          all(p["selectionStratum"] for p in packets))

if FAILED:
    print(f"\n{len(FAILED)} check(s) failed: {FAILED}")
    sys.exit(1)
print("\nAll checks passed.")
