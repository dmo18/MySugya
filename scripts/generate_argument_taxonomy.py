#!/usr/bin/env python3
"""
generate_argument_taxonomy.py - regenerate the argumentFlow category block
in app.jsx from the single canonical source, shared/argument_step_taxonomy.json.

category is DERIVED from this registry, never stored per argumentFlow step:
no modules/yoma/assets/learning/*.json content is touched by this script or
by anything downstream of it. This is why Phase 2A (argumentFlow) needs zero
corpus content edits: the registry alone determines category for every
observed type, and a new tractate just adds entries here.

The generated block sits between marker comments in app.jsx:

  // BEGIN GENERATED ARGUMENT TAXONOMY ...
  ...
  // END GENERATED ARGUMENT TAXONOMY

Two exported structures:
  ARGUMENT_CATEGORIES        category id -> { he, sym, en }
  ARGUMENT_TYPE_TO_CATEGORY  observed type -> category id

stepMetaFor (app.jsx) looks up a step's category via
ARGUMENT_TYPE_TO_CATEGORY, then its sym/he via ARGUMENT_CATEGORIES, while
the displayed en label is always the step's OWN type name, humanized - never
the category's name. This is what keeps a step's authored distinction
visible even though many types share one category's visual treatment.

--check regenerates into memory and byte-compares against the committed
app.jsx without writing; --apply writes only if different. Default (no
flag) behaves as --apply. Offline, no network.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
TAXONOMY_PATH = ROOT / "shared" / "argument_step_taxonomy.json"
APP_JSX = ROOT / "app.jsx"

BEGIN_MARKER = "// BEGIN GENERATED ARGUMENT TAXONOMY"
END_MARKER = "// END GENERATED ARGUMENT TAXONOMY"


def js_string(s):
    if s is None:
        return "null"
    escaped = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def generate_block(taxonomy):
    lines = [
        BEGIN_MARKER + " (source: shared/argument_step_taxonomy.json;",
        "// regenerate with: python3 scripts/generate_argument_taxonomy.py)",
        "// Do NOT hand-edit between these markers - see the source JSON.",
        "const ARGUMENT_CATEGORIES = {",
    ]
    for cat_id, meta in taxonomy["categories"].items():
        he = js_string(meta.get("he"))
        sym = js_string(meta["symbol"])
        en = js_string(meta["en"])
        lines.append(f'  {cat_id}: {{ he: {he}, sym: {sym}, en: {en} }},')
    lines.append("};")
    lines.append("const ARGUMENT_TYPE_TO_CATEGORY = {")
    for type_val, cat_id in taxonomy["typeToCategory"].items():
        key = type_val if re.match(r'^[A-Za-z_$][A-Za-z0-9_$]*$', type_val) else js_string(type_val)
        lines.append(f'  {key}: "{cat_id}",')
    lines.append("};")
    lines.append(END_MARKER)
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if app.jsx's generated block is stale, write nothing")
    args = ap.parse_args()

    taxonomy = json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))
    new_block = generate_block(taxonomy)

    text = APP_JSX.read_text(encoding="utf-8")
    pattern = re.compile(
        re.escape(BEGIN_MARKER) + r".*?" + re.escape(END_MARKER),
        re.DOTALL)
    if not pattern.search(text):
        sys.exit(f"ERROR: marker block not found in {APP_JSX}. "
                  f"Expected '{BEGIN_MARKER}' ... '{END_MARKER}'.")

    new_text = pattern.sub(new_block.rstrip("\n"), text, count=1)

    if args.check:
        if new_text == text:
            print("OK: app.jsx argument taxonomy block is fresh "
                  "(regeneration reproduces the committed bytes exactly).")
            sys.exit(0)
        sys.exit("STALE: app.jsx argument taxonomy block does not match "
                 "shared/argument_step_taxonomy.json. Run: "
                 "python3 scripts/generate_argument_taxonomy.py")

    if new_text != text:
        APP_JSX.write_text(new_text, encoding="utf-8")
        print(f"wrote {APP_JSX}")
    else:
        print("already fresh, nothing written")


if __name__ == "__main__":
    main()
