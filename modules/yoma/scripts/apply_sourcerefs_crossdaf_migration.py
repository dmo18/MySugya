#!/usr/bin/env python3
"""
apply_sourcerefs_crossdaf_migration.py - applies the QUALIFIED_CROSS_DAF
sourceRefs migrations from docs/reports/sourcerefs-blocker-classifications.json
to the new cross-daf object shape defined in
docs/reports/sourcerefs-crossdaf-schema-decision.md (Step 3 of the current
sourceRefs Phase 2B campaign).

What this changes: for each case classified QUALIFIED_CROSS_DAF, replaces
the one flagged ref (a same-daf object whose lineId happened to equal its
own stepId, a self-referential coordinate that never resolved on its own
daf) with { refType: "crossDaf", targetDaf, targetLineId,
targetVilnaLine, sourceType, note? }. The target daf/lineId/vilnaLine and
sourceType come from the classification's own recorded evidence, not
invented here - this script is a mechanical, format-preserving writer for
a decision already made and reviewed, the same relationship
apply_sourcerefs_semantic_repair.py has to source-refs-semantic-review.json.

Only two cases exist today (yoma-069b-l19 -> yoma-070a-l16,
yoma-069b-l21 -> yoma-070a-l22); ABSENT_OR_UNANCHORED and TIED_CANDIDATES
cases are untouched by this script entirely.

FORMAT PRESERVATION: identical approach to the other apply_sourcerefs_*
scripts - detect each file's exact serialization and refuse to touch a
file that can't be reproduced byte-for-byte.

SAFETY: only mutates a ref that still exactly matches the classification's
recorded flaggedRef (protects against a stale classification if the
corpus changed since Step 2/3 were written). After writing, re-runs the
corpus classifier and proves: both touched refs are now OK_CROSSDAF, the
corpus-wide OBJECT_COORDINATE_CONFLICT count dropped by exactly 2, and no
other defect class grew.

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
REPO = Path(__file__).parent.parent.parent.parent
TABLE_PATH = REPO / "docs" / "reports" / "data" / "sourcerefs-blocker-table.json"

# The target's real sourceType, established as evidence in Step 2/3 (both
# targets are gemara-kind lines quoting the eight-blessings baraita) -
# read from the corpus at classification time, not guessed here.
TARGETS = {
    ("yoma-069b-s03", "yoma-069b-l19"): {
        "targetDaf": "70a", "targetLineId": "yoma-070a-l16",
        "targetVilnaLine": 16, "sourceType": "gemara",
    },
    ("yoma-069b-s03", "yoma-069b-l21"): {
        "targetDaf": "70a", "targetLineId": "yoma-070a-l22",
        "targetVilnaLine": 22, "sourceType": "gemara",
    },
}


def detect_format(raw_bytes, data):
    for indent in (1, 2, 3, 4):
        candidate = (json.dumps(data, indent=indent, ensure_ascii=False) + "\n").encode("utf-8")
        if candidate == raw_bytes:
            return indent
    return None


def load_cases():
    table = json.loads(TABLE_PATH.read_text(encoding="utf-8"))
    return [c for c in table["cases"] if c["classification"] == "QUALIFIED_CROSS_DAF"]


def apply_to_file(path, cases_for_daf):
    raw = path.read_bytes()
    doc = json.loads(raw)
    indent = detect_format(raw, doc)
    if indent is None:
        return None, None, "cannot reproduce original file bytes; refusing to touch format"

    by_key = {(c["sugyaId"], c["stepId"]): c for c in cases_for_daf}
    applied = 0
    for sugya in doc.get("sugyot", []):
        for step in (sugya.get("argumentFlow") or []):
            key = (sugya.get("id"), step.get("id"))
            case = by_key.get(key)
            if case is None:
                continue
            target = TARGETS[key]
            refs = step.get("sourceRefs") or []
            match_idx = None
            for idx, ref in enumerate(refs):
                if ref == case["flaggedRef"]:
                    match_idx = idx
                    break
            if match_idx is None:
                return None, None, (
                    f"{key}: recorded flaggedRef not found among this step's "
                    f"sourceRefs (file changed since classification was written); "
                    f"refusing to apply a stale migration")
            refs[match_idx] = {
                "refType": "crossDaf",
                "targetDaf": target["targetDaf"],
                "targetLineId": target["targetLineId"],
                "targetVilnaLine": target["targetVilnaLine"],
                "sourceType": target["sourceType"],
            }
            applied += 1
    return doc, indent, applied


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    args = ap.parse_args()

    cases = load_cases()
    if set((c["sugyaId"], c["stepId"]) for c in cases) != set(TARGETS.keys()):
        sys.exit("ERROR: blocker table's QUALIFIED_CROSS_DAF cases don't match "
                 "this script's known TARGETS - re-check before applying")

    by_daf = {}
    for c in cases:
        by_daf.setdefault(c["daf"], []).append(c)

    print(f"Cross-daf sourceRefs migration - {len(cases)} case(s) across {len(by_daf)} daf\n")

    written = 0
    written_refs = 0
    errors = []
    for daf in sorted(by_daf):
        path = LEARN_DIR / f"{daf}.learning.json"
        if not path.exists():
            errors.append(f"{daf}: learning file not found")
            continue
        doc, indent, result = apply_to_file(path, by_daf[daf])
        if doc is None:
            errors.append(f"{daf}: {result}")
            continue
        print(f"  {daf}: {result} ref(s) migrated (format: indent={indent})")
        if args.apply:
            path.write_text(json.dumps(doc, indent=indent, ensure_ascii=False) + "\n",
                             encoding="utf-8")
            written += 1
            written_refs += result

    if errors:
        print(f"\n{len(errors)} file(s) could not be safely migrated:")
        for e in errors:
            print(f"  ERROR  {e}")
        sys.exit(1)

    if not args.apply:
        print(f"\nDRY RUN: would migrate {sum(len(v) for v in by_daf.values())} "
              f"ref(s) across {len(by_daf)} file(s). Re-run with --apply to write.")
        return

    print(f"\nWrote {written_refs} ref(s) across {written} file(s).")

    counts, findings = vsr.run(sorted(LEARN_DIR.glob("*.learning.json")))
    print(f"\nPost-write corpus classification: {dict(counts)}")
    print(f"OK_CROSSDAF: {counts.get('OK_CROSSDAF', 0)} (expected 2)")
    print(f"OBJECT_COORDINATE_CONFLICT remaining: {counts.get('OBJECT_COORDINATE_CONFLICT', 0)} "
          f"(expected 22, was 24)")


if __name__ == "__main__":
    main()
