#!/usr/bin/env python3
"""
validate_daftext.py — verify that assets/daftexts/<daf>.txt was generated
from assets/talmuddev/<daf>.json (the authoritative talmud.dev source) and
not from a stale PDF or other secondary source.

For each daf that has both a talmuddev JSON and a daftext txt:
  1. Reads talmuddev/<daf>.json lines[] array
  2. Generates the expected daftext content: "{N} {line}\\n" per line
  3. Compares against the actual daftext file
  4. Reports any mismatch as an ERROR

A mismatch means daftext_align.py will embed wrong Vilna breaks into learning_data.js
even though all other gates (validate, audit, order, validate:en) pass.

Usage:
  python3 scripts/validate_daftext.py           # all daf with talmuddev JSON
  python3 scripts/validate_daftext.py 2a 2b     # specific daf
"""
import json
import os
import sys

TXTDIR = "assets/daftexts"
JSONDIR = "assets/talmuddev"


def expected_lines(daf):
    path = os.path.join(JSONDIR, f"{daf}.json")
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    return [f"{i} {line}" for i, line in enumerate(d.get("lines", []), 1)]


def actual_lines(daf):
    path = os.path.join(TXTDIR, f"{daf}.txt")
    with open(path, encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f if line.strip()]


def check_daf(daf):
    json_path = os.path.join(JSONDIR, f"{daf}.json")
    txt_path = os.path.join(TXTDIR, f"{daf}.txt")

    if not os.path.exists(json_path):
        return None, f"no talmuddev JSON (fetch with: python3 scripts/fetch_talmuddev.py {daf})"
    if not os.path.exists(txt_path):
        return None, f"no daftext file (regenerate with: python3 scripts/validate_daftext.py --fix {daf})"

    expected = expected_lines(daf)
    actual = actual_lines(daf)

    if expected == actual:
        return True, f"{len(expected)} lines match"

    errs = []
    if len(expected) != len(actual):
        errs.append(f"length mismatch: talmuddev has {len(expected)} lines, daftext has {len(actual)}")
    else:
        for i, (exp, act) in enumerate(zip(expected, actual), 1):
            if exp != act:
                errs.append(f"  line {i}: expected '{exp[:60]}' got '{act[:60]}'")
                if len(errs) >= 5:
                    errs.append("  ... (more differences)")
                    break
    return False, "; ".join(errs)


def fix_daf(daf):
    json_path = os.path.join(JSONDIR, f"{daf}.json")
    if not os.path.exists(json_path):
        print(f"  {daf}: SKIP - no talmuddev JSON")
        return
    lines = expected_lines(daf)
    txt_path = os.path.join(TXTDIR, f"{daf}.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")
    print(f"  {daf}: wrote {len(lines)} lines -> {txt_path}")


def main():
    fix_mode = "--fix" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if args:
        daf_list = args
    else:
        # All daf that have a talmuddev JSON
        daf_list = sorted(
            (f[:-5] for f in os.listdir(JSONDIR) if f.endswith(".json")),
            key=lambda x: (int(x[:-1]), x[-1])
        )

    if fix_mode:
        print(f"Regenerating {len(daf_list)} daftext file(s) from talmuddev JSON...")
        for daf in daf_list:
            fix_daf(daf)
        return

    errors = []
    skipped = []
    ok = 0

    print(f"Checking {len(daf_list)} daftext file(s) against talmuddev source...\n")
    for daf in daf_list:
        result, msg = check_daf(daf)
        if result is None:
            skipped.append((daf, msg))
            print(f"  {daf:4s}  SKIP  {msg}")
        elif result:
            ok += 1
            print(f"  {daf:4s}  OK    {msg}")
        else:
            errors.append((daf, msg))
            print(f"  {daf:4s}  ERROR {msg}")

    print()
    if errors:
        print(f"ERROR: {len(errors)} daftext file(s) are out of sync with talmuddev:\n")
        for daf, msg in errors:
            print(f"  [{daf}] {msg}")
        print()
        print("Fix: python3 scripts/validate_daftext.py --fix")
        print("Then: python3 scripts/daftext_align.py <daf> --apply --force")
        print("Then: npm run validate && npm run audit:order")
        sys.exit(1)

    print(f"OK: {ok} daftext file(s) match talmuddev source.")
    if skipped:
        print(f"    {len(skipped)} skipped (no JSON or no txt).")


if __name__ == "__main__":
    main()
