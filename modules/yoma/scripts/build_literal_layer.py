#!/usr/bin/env python3
"""
build_literal_layer.py — inject en_lit: fields from assets/literal_en/
into learning_data.js by matching sefaria_ref on each line object.

Run from modules/yoma/ after fetch_literal_en.py has populated
assets/literal_en/<daf>.json for all (or a subset of) daf.

Usage:
  python3 scripts/build_literal_layer.py               # dry-run: print stats
  python3 scripts/build_literal_layer.py --apply       # write to learning_data.js
  python3 scripts/build_literal_layer.py --apply --daf 2a 3b   # specific daf only
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _js_parser import extract_string_field, find_string_field_span, iter_line_object_spans

LEARNING_DATA = Path("learning_data.js")
LITERAL_DIR   = Path("assets/literal_en")


def load_literal_cache(daf_filter: list[str] | None = None) -> dict[str, str]:
    """Return {sefaria_ref: en_lit} for all fetched daf."""
    cache: dict[str, str] = {}
    for f in sorted(LITERAL_DIR.glob("*.json")):
        if f.name == "progress.json":
            continue
        daf_id = f.stem
        if daf_filter and daf_id not in daf_filter:
            continue
        data = json.loads(f.read_text())
        for line in data.get("lines", []):
            ref = line.get("sefaria_ref", "")
            lit = line.get("en_lit", "")
            if ref:
                cache[ref] = lit
    return cache


def inject(source: str, cache: dict[str, str]) -> tuple[str, int, int]:
    """
    Find every line object that has sefaria_ref: "..." and either:
      - insert en_lit: after the en: field if not already present
      - update en_lit: if already present
    Returns (new_source, injected_count, skipped_count).

    Line object boundaries come from iter_line_object_spans, which tracks
    brace depth and skips quoted strings, so nested commentaries blocks and
    literal { } [ ] characters inside he:/en: text cannot misalign a span.
    """
    injected = skipped = 0
    parts: list[str] = []
    cursor = 0

    for start, end in iter_line_object_spans(source):
        block = source[start:end]

        try:
            ref = extract_string_field(block, "sefaria_ref")
        except ValueError:
            continue

        lit = cache.get(ref)
        if lit is None:
            skipped += 1
            continue

        lit_escaped = lit.replace("\\", "\\\\").replace('"', '\\"')

        en_lit_span = find_string_field_span(block, "en_lit")
        if en_lit_span is not None:
            # Already has en_lit: - update it
            field_start, field_end = en_lit_span
            new_block = (
                block[:field_start] + f'en_lit: "{lit_escaped}"' + block[field_end:]
            )
            injected += 1
        else:
            en_span = find_string_field_span(block, "en")
            if en_span is None:
                skipped += 1
                continue
            insert_at = en_span[1]
            new_block = block[:insert_at] + f', en_lit: "{lit_escaped}"' + block[insert_at:]
            injected += 1

        parts.append(source[cursor:start])
        parts.append(new_block)
        cursor = end

    parts.append(source[cursor:])
    new_source = "".join(parts)
    return new_source, injected, skipped


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Write changes to learning_data.js")
    parser.add_argument("--daf", nargs="*", help="Limit to specific daf IDs")
    args = parser.parse_args()

    if not LEARNING_DATA.exists():
        print("ERROR: learning_data.js not found. Run from modules/yoma/.", file=sys.stderr)
        sys.exit(1)

    cache = load_literal_cache(args.daf)
    print(f"Loaded {len(cache)} en_lit entries from {LITERAL_DIR}/")

    source = LEARNING_DATA.read_text()
    new_source, injected, skipped = inject(source, cache)

    print(f"Lines injected/updated : {injected}")
    print(f"Lines skipped (no ref) : {skipped}")

    if injected == 0:
        print("Nothing to write.")
        return

    if args.apply:
        LEARNING_DATA.write_text(new_source)
        print(f"Written to {LEARNING_DATA}")
    else:
        print("Dry run — pass --apply to write.")


if __name__ == "__main__":
    main()
