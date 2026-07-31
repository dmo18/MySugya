#!/usr/bin/env python3
"""
apply_sourcerefs_final_two.py - applies the two proven repairs to the last
two sourceRefs blockers of the Phase 2B campaign (docs/reports/
sourcerefs-blocker-classifications.json's TIED_CANDIDATES cases), after a
fresh re-adjudication found evidence the prior campaign did not fully
exploit. See docs/reports/sourcerefs-final-two-resolution.md for the full
evidence record.

yoma-044b-l01 (44b): the step is a compound claim (two clauses). Multiple
sourceRefs per step is an already-legal, already-used shape (21 existing
steps carry 2+ refs); each clause maps 1:1 onto one of two real same-vilna
segments, so this is a two-ref repair, not a step split. Replaces the
single self-referential ref with two ordered refs: yoma-044b-l01a (clause
1), yoma-044b-l01b (clause 2).

yoma-063a-l03a (63a): the step's own speaker field ("Rav Dimi from Eretz
Yisrael") verbatim-matches yoma-063a-l10's transmission formula, and
l10's conclusion (exempt) matches/supports the ruling this step cites
(yoma-063a-l01, also exempt) - resolving what the prior campaign
classified as a tie between yoma-063a-l10 and yoma-063a-l17 (a different
transmitter, Ravin, with the opposite conclusion). Replaces the single
self-referential ref with one ref to yoma-063a-l10.

FORMAT PRESERVATION: same approach as the other apply_sourcerefs_* tools.
SAFETY: only mutates a ref that still exactly matches its recorded
before-state.

--dry-run (default) reports what would change without writing anything.
--apply writes. Offline, no network.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import validate_source_refs as vsr  # noqa: E402

LEARN_DIR = vsr.LEARN_DIR

REPAIRS = {
    "44b": {
        "sugyaId": "yoma-044b-s01",
        "stepId": "yoma-044b-l01",
        "before": {"sourceType": "gemara", "lineId": "yoma-044b-l01", "vilnaLine": 1},
        "after": [
            {"sourceType": "gemara", "lineId": "yoma-044b-l01a", "vilnaLine": 1},
            {"sourceType": "gemara", "lineId": "yoma-044b-l01b", "vilnaLine": 1},
        ],
    },
    "63a": {
        "sugyaId": "yoma-063a-s01",
        "stepId": "yoma-063a-l03a",
        "before": {"sourceType": "gemara", "lineId": "yoma-063a-l03a", "vilnaLine": 2},
        "after": [
            {"sourceType": "gemara", "lineId": "yoma-063a-l10", "vilnaLine": 10},
        ],
    },
}


def detect_format(raw_bytes, data):
    for indent in (1, 2, 3, 4):
        base = json.dumps(data, indent=indent, ensure_ascii=False)
        if (base + "\n").encode("utf-8") == raw_bytes:
            return indent, True
        if base.encode("utf-8") == raw_bytes:
            return indent, False
    return None


def apply_to_file(path, repair):
    raw = path.read_bytes()
    doc = json.loads(raw)
    fmt = detect_format(raw, doc)
    if fmt is None:
        return None, None, "cannot reproduce original file bytes; refusing to touch format"
    indent, trailing_newline = fmt

    found = False
    for sugya in doc.get("sugyot", []):
        if sugya.get("id") != repair["sugyaId"]:
            continue
        for step in (sugya.get("argumentFlow") or []):
            if step.get("id") != repair["stepId"]:
                continue
            refs = step.get("sourceRefs") or []
            if refs != [repair["before"]]:
                return None, None, (
                    f"{repair['sugyaId']}/{repair['stepId']}: sourceRefs is not exactly "
                    f"[before] as recorded; refusing to apply a stale repair")
            step["sourceRefs"] = repair["after"]
            found = True
    if not found:
        return None, None, f"{repair['sugyaId']}/{repair['stepId']}: not found in {path.name}"
    return doc, fmt, len(repair["after"])


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    args = ap.parse_args()

    print(f"Final two sourceRefs repairs - 2 case(s) across 2 daf\n")

    written = 0
    errors = []
    for daf, repair in REPAIRS.items():
        path = LEARN_DIR / f"{daf}.learning.json"
        if not path.exists():
            errors.append(f"{daf}: learning file not found")
            continue
        doc, fmt, result = apply_to_file(path, repair)
        if doc is None:
            errors.append(f"{daf}: {result}")
            continue
        indent, trailing_newline = fmt
        print(f"  {daf}: {repair['stepId']} -> {result} ref(s) "
              f"(format: indent={indent}, trailing_newline={trailing_newline})")
        if args.apply:
            text = json.dumps(doc, indent=indent, ensure_ascii=False)
            if trailing_newline:
                text += "\n"
            path.write_text(text, encoding="utf-8")
            written += 1

    if errors:
        print(f"\n{len(errors)} file(s) could not be safely repaired:")
        for e in errors:
            print(f"  ERROR  {e}")
        sys.exit(1)

    if not args.apply:
        print(f"\nDRY RUN: would repair 2 case(s) across 2 file(s). Re-run with --apply to write.")
        return

    print(f"\nWrote repairs across {written} file(s).")

    counts, findings = vsr.run(sorted(LEARN_DIR.glob("*.learning.json")))
    print(f"\nPost-write corpus classification: {dict(counts)}")
    defects = sum(counts[c] for c in vsr.DEFECT_CLASSES)
    print(f"Total defects remaining: {defects}")


if __name__ == "__main__":
    main()
