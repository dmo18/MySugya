#!/usr/bin/env python3
"""
generate_scaffold_baseline.py - one-time (operator-authorized) generation of
the scaffold-fabrication debt baseline from the current corpus scan. Ordinary
worker PRs never run this: the baseline is a shrink-only ratchet and grows
only under explicit operator authorization (see audit_rashi_scaffold.py and
docs/reports/yoma-rashi-scaffold-audit.md).

Usage (from modules/yoma/):
  python3 scripts/baselines/generate_scaffold_baseline.py <generatedFrom-ref>
"""
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPTS))
import audit_rashi_scaffold as asc  # noqa: E402


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: generate_scaffold_baseline.py <generatedFrom-ref>")
    hits = []
    for d in asc.all_daf():
        hits.extend(asc.scan_daf(d))
    entries = [{"daf": h["daf"], "vilnaLine": h["vilnaLine"],
                "rule": h["rule"], "enHash": h["enHash"]} for h in hits]
    data = {
        "_comment": ("Locked inventory of pre-existing Rashi scaffold-"
                     "fabrication debt (see docs/reports/yoma-rashi-scaffold-"
                     "audit.md). audit_rashi_scaffold.py enforces it as a "
                     "shrink-only ratchet: an entry covers ONLY the exact "
                     "contaminated en text hashed here. Never add entries in "
                     "worker PRs; growth requires explicit operator "
                     "authorization. Retire stale entries with "
                     "--update-baseline as daf are repaired."),
        "generatedFrom": sys.argv[1],
        "entries": entries,
    }
    asc.BASELINE.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
    print(f"wrote {asc.BASELINE} with {len(entries)} entries")


if __name__ == "__main__":
    main()
