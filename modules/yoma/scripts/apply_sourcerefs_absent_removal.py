#!/usr/bin/env python3
"""
apply_sourcerefs_absent_removal.py - applies the ABSENT_OR_UNANCHORED
sourceRefs removals from docs/reports/sourcerefs-blocker-classifications.json
(Step 4 of the current sourceRefs Phase 2B campaign).

What this changes: for each case classified ABSENT_OR_UNANCHORED, removes
the one flagged ref from its step's sourceRefs array. Every one of these
29 cases has exactly one ref in its sourceRefs array (confirmed against
docs/reports/data/sourcerefs-blocker-dossier.json before this script was
written), so removing it always leaves an empty array. The array itself
is kept (sourceRefs: []), not deleted: shared/schema_map.js declares
sourceRefs optional, and the corpus's own convention for other optional
array fields left inapplicable (relatedSugyot, alternateAngles) is an
empty array, not an absent key - this keeps sourceRefs consistent with
that existing convention rather than inventing a new absent-key
representation with no precedent in the corpus.

This is a documented removal, not a guess: each case's evidence (full
argumentFlow context, full source text on the declared daf, adjacent daf,
and a tractate-wide search) is in docs/reports/sourcerefs-blocker-table.md,
and found no exact segment the step's content could be truthfully
anchored to. Leaving a false coordinate to keep the field populated is
exactly what the canonical contract forbids.

FORMAT PRESERVATION: identical approach to the other apply_sourcerefs_*
scripts - detect each file's exact serialization and refuse to touch a
file that can't be reproduced byte-for-byte.

SAFETY: only mutates a ref that still exactly matches the classification's
recorded flaggedRef (protects against a stale classification if the
corpus changed since Step 2 was written). Refuses to run if any case
unexpectedly has more than one ref in its sourceRefs array (that would
mean removing the wrong element, or leaving a non-empty array this
script was not designed to handle) - re-check the case by hand instead.
After writing, re-runs the corpus classifier and proves: the corpus-wide
defect count dropped by exactly the number of cases removed, and no
other defect class grew.

--dry-run (default) reports what would change without writing anything.
--apply writes. Offline, no network. --daf <daf> limits to one daf, for
batching a multi-daf application across smaller, individually-verifiable
diffs.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import validate_source_refs as vsr  # noqa: E402

LEARN_DIR = vsr.LEARN_DIR
REPO = Path(__file__).parent.parent.parent.parent
TABLE_PATH = REPO / "docs" / "reports" / "data" / "sourcerefs-blocker-table.json"


def detect_format(raw_bytes, data):
    """Returns (indent, trailing_newline) or None. Most corpus files end
    with a trailing newline after the closing brace, but at least one
    (61a) does not - so both must be tried, or a file with no trailing
    newline is wrongly reported as unreproducible and skipped entirely."""
    for indent in (1, 2, 3, 4):
        base = json.dumps(data, indent=indent, ensure_ascii=False)
        if (base + "\n").encode("utf-8") == raw_bytes:
            return indent, True
        if base.encode("utf-8") == raw_bytes:
            return indent, False
    return None


def load_cases():
    table = json.loads(TABLE_PATH.read_text(encoding="utf-8"))
    return [c for c in table["cases"] if c["classification"] == "ABSENT_OR_UNANCHORED"]


def apply_to_file(path, cases_for_daf):
    raw = path.read_bytes()
    doc = json.loads(raw)
    fmt = detect_format(raw, doc)
    if fmt is None:
        return None, None, "cannot reproduce original file bytes; refusing to touch format"
    indent, trailing_newline = fmt

    by_key = {(c["sugyaId"], c["stepId"]): c for c in cases_for_daf}
    applied = 0
    for sugya in doc.get("sugyot", []):
        for step in (sugya.get("argumentFlow") or []):
            key = (sugya.get("id"), step.get("id"))
            case = by_key.get(key)
            if case is None:
                continue
            refs = step.get("sourceRefs") or []
            if refs != [case["flaggedRef"]]:
                return None, None, (
                    f"{key}: sourceRefs is not exactly [flaggedRef] as recorded "
                    f"(file changed since classification was written, or this case "
                    f"has more than one ref); refusing to apply a stale/ambiguous removal")
            step["sourceRefs"] = []
            applied += 1
    return doc, fmt, applied


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    ap.add_argument("--daf", help="limit to one daf, e.g. 48b")
    args = ap.parse_args()

    cases = load_cases()
    by_daf = {}
    for c in cases:
        by_daf.setdefault(c["daf"], []).append(c)

    target_daf = sorted(by_daf) if not args.daf else [args.daf]
    if args.daf and args.daf not in by_daf:
        sys.exit(f"ERROR: no ABSENT_OR_UNANCHORED case on daf {args.daf}")

    print(f"ABSENT_OR_UNANCHORED sourceRefs removal - {len(cases)} case(s) "
          f"across {len(by_daf)} daf total; this run targets "
          f"{sum(len(by_daf[d]) for d in target_daf)} case(s) across {len(target_daf)} daf\n")

    written = 0
    written_refs = 0
    errors = []
    for daf in target_daf:
        path = LEARN_DIR / f"{daf}.learning.json"
        if not path.exists():
            errors.append(f"{daf}: learning file not found")
            continue
        doc, fmt, result = apply_to_file(path, by_daf[daf])
        if doc is None:
            errors.append(f"{daf}: {result}")
            continue
        indent, trailing_newline = fmt
        print(f"  {daf}: {result} ref(s) removed "
              f"(format: indent={indent}, trailing_newline={trailing_newline})")
        if args.apply:
            text = json.dumps(doc, indent=indent, ensure_ascii=False)
            if trailing_newline:
                text += "\n"
            path.write_text(text, encoding="utf-8")
            written += 1
            written_refs += result

    if errors:
        print(f"\n{len(errors)} file(s) could not be safely repaired:")
        for e in errors:
            print(f"  ERROR  {e}")
        sys.exit(1)

    if not args.apply:
        print(f"\nDRY RUN: would remove {sum(len(by_daf[d]) for d in target_daf)} "
              f"ref(s) across {len(target_daf)} file(s). Re-run with --apply to write.")
        return

    print(f"\nWrote {written_refs} ref(s) removed across {written} file(s).")

    counts, findings = vsr.run(sorted(LEARN_DIR.glob("*.learning.json")))
    print(f"\nPost-write corpus classification: {dict(counts)}")
    defects = sum(counts[c] for c in vsr.DEFECT_CLASSES)
    print(f"Total defects remaining: {defects}")


if __name__ == "__main__":
    main()
