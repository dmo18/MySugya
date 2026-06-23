#!/usr/bin/env python3
"""
validate_literal.py — gate script: verify en_lit coverage in learning_data.js.

Exits 0 if coverage meets threshold, 1 otherwise.

Usage (from modules/yoma/):
  python3 scripts/validate_literal.py            # require 95% coverage
  python3 scripts/validate_literal.py --min 100  # require 100%
  python3 scripts/validate_literal.py --status   # print coverage and exit 0
"""

import argparse
import re
import sys
from pathlib import Path

LEARNING_DATA = Path("learning_data.js")
DEFAULT_MIN   = 95   # percent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--min", type=int, default=DEFAULT_MIN,
                        help=f"Minimum required coverage %% (default {DEFAULT_MIN})")
    parser.add_argument("--status", action="store_true",
                        help="Print coverage stats only, always exit 0")
    args = parser.parse_args()

    source = LEARNING_DATA.read_text()

    # Find line objects with sefaria_ref (Gemara text lines)
    line_blocks = re.findall(
        r'\{(?:[^{}]|\{[^{}]*\})*?sefaria_ref:\s*"[^"]*"(?:[^{}]|\{[^{}]*\})*?\}',
        source, re.DOTALL
    )

    total     = len(line_blocks)
    has_lit   = sum(1 for b in line_blocks if "en_lit:" in b)
    empty_lit = sum(1 for b in line_blocks
                    if re.search(r'en_lit:\s*""', b))
    filled    = has_lit - empty_lit
    pct       = round(filled / total * 100, 1) if total else 0

    print(f"Gemara lines:  {total}")
    print(f"Has en_lit:    {has_lit}")
    print(f"Non-empty:     {filled}")
    print(f"Coverage:      {pct}%")

    if args.status:
        sys.exit(0)

    if pct < args.min:
        print(f"FAIL: coverage {pct}% < required {args.min}%", file=sys.stderr)
        sys.exit(1)

    print(f"OK: coverage {pct}% >= {args.min}%")
    sys.exit(0)


if __name__ == "__main__":
    main()
