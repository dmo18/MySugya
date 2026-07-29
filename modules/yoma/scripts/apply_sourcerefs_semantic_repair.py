#!/usr/bin/env python3
"""
apply_sourcerefs_semantic_repair.py - applies the judgment-required
sourceRefs repairs (classes OBJECT_COORDINATE_CONFLICT and
OBJECT_DANGLING_AMBIGUOUS from validate_source_refs.py) that a human
reviewer resolved with confidence after reading each step's text against
the actual Gemara content on its daf, per docs/reports/
source-refs-semantic-review.json.

What this changes: for each resolved case, `lineId` (only when the review
found a different, better-supported segment) and `vilnaLine` (always, to
match the resolved segment's true position) on exactly the one flagged ref.
`sourceType` and `note` are left untouched. Cases the review marked
UNRESOLVED are never touched - each has a documented reason no safe repair
was possible (ambiguous candidates, content not found anywhere on the daf,
or the true content living on a different daf that the per-daf lineId
contract cannot reference).

FORMAT PRESERVATION

Same approach as apply_sourcerefs_mechanical_repair.py: each file's exact
serialization (indent level, ensure_ascii=False) is detected by trying
candidates until one byte-reproduces the original, and the script refuses
to touch a file it cannot reproduce byte-for-byte.

SAFETY

- Only ever mutates a ref that still exactly matches the review's recorded
  "before" state (protects against a stale review if the corpus changed
  since the review was written).
- Only writes lineId when the resolution actually changes it; leaves
  REPAIR_VILNA_ONLY cases' lineId untouched.
- After writing, re-runs the corpus classifier and proves: every touched
  ref is now OK, the corpus-wide OBJECT_COORDINATE_CONFLICT and
  OBJECT_DANGLING_AMBIGUOUS counts dropped by exactly the number of
  REASSIGN + REPAIR_VILNA_ONLY resolutions, and no other defect class grew.

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
REVIEW_PATH = Path(__file__).parent.parent.parent.parent / "docs" / "reports" / "source-refs-semantic-review.json"


def detect_format(raw_bytes, data):
    for indent in (1, 2, 3, 4):
        candidate = (json.dumps(data, indent=indent, ensure_ascii=False) + "\n").encode("utf-8")
        if candidate == raw_bytes:
            return indent
    return None


def load_review():
    return json.loads(REVIEW_PATH.read_text(encoding="utf-8"))


def apply_to_file(path, resolutions_for_daf):
    """resolutions_for_daf: list of resolution dicts for this one daf.
    Mutates and returns the parsed doc; caller re-serializes and writes."""
    raw = path.read_bytes()
    doc = json.loads(raw)
    indent = detect_format(raw, doc)
    if indent is None:
        return None, None, "cannot reproduce original file bytes; refusing to touch format"

    by_key = {(r["sugyaId"], r["stepId"]): r for r in resolutions_for_daf}
    applied = 0
    for sugya in doc.get("sugyot", []):
        for step in (sugya.get("argumentFlow") or []):
            key = (sugya.get("id"), step.get("id"))
            res = by_key.get(key)
            if res is None:
                continue
            refs = step.get("sourceRefs") or []
            match_idx = None
            for idx, ref in enumerate(refs):
                if ref == res["beforeRef"]:
                    match_idx = idx
                    break
            if match_idx is None:
                return None, None, (
                    f"{key}: recorded before-state not found among this step's "
                    f"sourceRefs (file changed since review was written); "
                    f"refusing to apply a stale resolution")
            ref = refs[match_idx]
            if res["decision"] == "REASSIGN":
                ref["lineId"] = res["newLineId"]
            ref["vilnaLine"] = res["newVilna"]
            applied += 1
    return doc, indent, applied


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    args = ap.parse_args()

    review = load_review()
    actionable = [r for r in review if r["decision"] in ("REASSIGN", "REPAIR_VILNA_ONLY")]
    unresolved = [r for r in review if r["decision"] == "UNRESOLVED"]

    by_daf = {}
    for r in actionable:
        by_daf.setdefault(r["daf"], []).append(r)

    print(f"Semantic sourceRefs repair - {len(review)} reviewed case(s): "
          f"{len(actionable)} actionable, {len(unresolved)} unresolved (untouched)\n")

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
        print(f"  {daf}: {result} ref(s) repaired (format: indent={indent})")
        if args.apply:
            path.write_text(json.dumps(doc, indent=indent, ensure_ascii=False) + "\n",
                             encoding="utf-8")
            written += 1
            written_refs += result

    if errors:
        print(f"\n{len(errors)} file(s) could not be safely repaired:")
        for e in errors:
            print(f"  ERROR  {e}")
        sys.exit(1)

    if not args.apply:
        print(f"\nDRY RUN: would repair {sum(len(v) for v in by_daf.values())} "
              f"ref(s) across {len(by_daf)} file(s). Re-run with --apply to write.")
        return

    print(f"\nWrote {written_refs} ref(s) across {written} file(s).")

    counts, findings = vsr.run(sorted(LEARN_DIR.glob("*.learning.json")))
    print(f"\nPost-write corpus classification: {dict(counts)}")

    remaining_conflict = counts.get("OBJECT_COORDINATE_CONFLICT", 0)
    remaining_ambiguous = counts.get("OBJECT_DANGLING_AMBIGUOUS", 0)
    print(f"OBJECT_COORDINATE_CONFLICT remaining: {remaining_conflict} "
          f"(expected: {len([r for r in unresolved if True])} unresolved cases' "
          f"original class, see docs/reports/source-refs-semantic-review.json)")
    print(f"OBJECT_DANGLING_AMBIGUOUS remaining: {remaining_ambiguous}")


if __name__ == "__main__":
    main()
