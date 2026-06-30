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
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _js_parser import parse_line_items_from_lines_array

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

    # Find line objects with sefaria_ref (Gemara text lines), using the
    # bracket-and-quote-aware parser instead of a one-level DOTALL regex.
    items = parse_line_items_from_lines_array(source)

    total     = len(items)
    has_lit   = sum(1 for item in items if item["en_lit"] is not None)
    empty_lit = sum(1 for item in items if item["en_lit"] == "")
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
