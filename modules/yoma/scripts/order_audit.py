#!/usr/bin/env python3
"""
order_audit.py — verify that every daf's content appears in Vilna order.

The reading order of learning_data.js (sugya by sugya, line by line) must follow the
physical Vilna column: each field's vilna_line must be >= the previous
field's vilna_line (ties allowed — several fields can start on one line).

Checks per daf:
  ERROR  INVERSION  — a field starts on an earlier Vilna line than the field
                      before it (text is out of sequence)
  ERROR  DUPLICATE  — two fields cover the same Vilna span with the same
                      opening words (passage pasted twice)
  WARN   GAP        — consecutive fields skip more than GAP_TOLERANCE Vilna
                      lines (possible missing passage)
  WARN   NO-STAMP   — a substantive he: field lacks vilna_line (cannot be
                      order-checked)

Exit codes: 0 = clean (warnings allowed with --strict off), 1 = errors found.

Usage:
  python3 scripts/order_audit.py             # all daf
  python3 scripts/order_audit.py 5a 12b      # specific daf
  python3 scripts/order_audit.py --strict    # warnings are fatal too
"""

import re
import sys

DATA_JS = "learning_data.js"
GAP_TOLERANCE = 3   # Vilna lines that may be skipped between fields (Mishnah headers etc.)
HEB = re.compile(r"[א-ת]")


def letters_of(text):
    return "".join(ch for ch in text if HEB.match(ch))


def parse(content):
    """Yield (daf, sugya_id, jsline, vilna_line|None, n_rows, he_prefix)."""
    raw_lines = content.split("\n")
    daf_re = re.compile(r'^\s*"(\d+[ab])":\s*\{')
    sug_re = re.compile(r'\bid\s*:\s*"([^"]+)"')
    he_re = re.compile(r'\bhe\s*:\s*"((?:[^"\\]|\\.)*)"')
    vl_re = re.compile(r'\bvilna_line\s*:\s*(\d+)')

    daf = sugya = None
    in_lines = False
    depth = 0
    pend = None  # (jsline, he_raw)

    for lineno, line in enumerate(raw_lines, 1):
        m = daf_re.match(line)
        if m:
            daf = m.group(1)
            in_lines = False
            pend = None
            continue
        if daf is None:
            continue
        m = sug_re.search(line)
        if m and not in_lines:
            sugya = m.group(1)
        if not in_lines and re.search(r'\blines\s*:\s*\[', line):
            in_lines = True
            depth = line.count("[") - line.count("]")
            continue
        if in_lines:
            depth += line.count("[") - line.count("]")
            if depth <= 0:
                if pend:
                    yield (daf, sugya, pend[0], None, pend[1], pend[2])
                    pend = None
                in_lines = False
                continue
            hm = he_re.search(line)
            if hm:
                if pend:  # previous he had no vilna_line stamp
                    yield (daf, sugya, pend[0], None, pend[1], pend[2])
                raw = hm.group(1)
                txt = raw.replace('\\"', '"').replace("\\\\", "\\")
                n_rows = txt.count("\\n") + 1
                flat = txt.replace("\\n", " ")
                pend = (lineno, n_rows, flat[:45])
                continue
            vm = vl_re.search(line)
            if vm and pend:
                yield (daf, sugya, pend[0], int(vm.group(1)), pend[1], pend[2])
                pend = None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    strict = "--strict" in sys.argv
    target = set(args) if args else None

    with open(DATA_JS, encoding="utf-8") as f:
        content = f.read()

    by_daf = {}
    for daf, sugya, jsline, vl, n_rows, prefix in parse(content):
        if target and daf not in target:
            continue
        by_daf.setdefault(daf, []).append((sugya, jsline, vl, n_rows, prefix))

    errors = []
    warns = []

    for daf in sorted(by_daf, key=lambda x: (int(x[:-1]), x[-1])):
        fields = by_daf[daf]
        prev_vl = None
        prev_info = None
        seen_spans = {}
        for sugya, jsline, vl, n_rows, prefix in fields:
            has_letters = bool(letters_of(prefix))
            if vl is None:
                if has_letters and len(prefix) > 20:
                    warns.append((daf, jsline, "NO-STAMP",
                                  f"[{sugya}] no vilna_line: “{prefix}…”"))
                continue
            if prev_vl is not None and vl < prev_vl:
                errors.append((daf, jsline, "INVERSION",
                               f"[{sugya}] starts at Vilna L{vl} but previous field "
                               f"({prev_info}) starts at L{prev_vl}"))
            if prev_vl is not None and vl > prev_vl:
                prev_end = prev_vl + (prev_rows - 1)
                if vl - prev_end > GAP_TOLERANCE:
                    warns.append((daf, jsline, "GAP",
                                  f"[{sugya}] jumps to L{vl}; previous field ended ~L{prev_end} "
                                  f"({vl - prev_end} lines skipped)"))
            key = (vl, letters_of(prefix)[:25])
            if key in seen_spans and key[1]:
                errors.append((daf, jsline, "DUPLICATE",
                               f"[{sugya}] same passage as learning_data.js line {seen_spans[key]} "
                               f"(L{vl}: “{prefix}…”)"))
            else:
                seen_spans[key] = jsline
            prev_vl = vl
            prev_rows = n_rows
            prev_info = f"[{sugya}] js:{jsline}"

    for daf, jsline, kind, msg in errors:
        print(f"ERROR {kind:9s} [{daf}] learning_data.js:{jsline}  {msg}")
    for daf, jsline, kind, msg in warns:
        print(f"warn  {kind:9s} [{daf}] learning_data.js:{jsline}  {msg}")

    n_daf = len(by_daf)
    n_fields = sum(len(v) for v in by_daf.values())
    print(f"\n{n_fields} fields across {n_daf} daf — "
          f"{len(errors)} error(s), {len(warns)} warning(s).")

    if errors or (strict and warns):
        sys.exit(1)
    print("Order audit passed.")


if __name__ == "__main__":
    main()
