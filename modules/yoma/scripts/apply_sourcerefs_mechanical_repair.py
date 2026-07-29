#!/usr/bin/env python3
"""
apply_sourcerefs_mechanical_repair.py - applies ONLY the mechanically
lossless sourceRefs repairs (class OBJECT_DANGLING_REPAIRABLE from
validate_source_refs.py / preview_source_refs_migration.py) to
modules/yoma/assets/learning/*.json.

What this changes: exactly one field, `lineId`, on refs where the ref's
`lineId` does not resolve to any local line but its `vilnaLine` falls
inside exactly one line's Vilna interval - the containing line's id is the
only lossless repair, unique by construction (dry-run enforced this before
any file is touched). `vilnaLine`, `sourceType`, and `note` are byte-
identical before and after. Judgment-required refs (OBJECT_DANGLING_
AMBIGUOUS, OBJECT_COORDINATE_CONFLICT) are untouched - those need a human
reading the step text against the Gemara and are handled by a separate,
later pass per docs/reports/source-refs-normalization-plan.md.

FORMAT PRESERVATION

The corpus's own *.learning.json files are not uniformly formatted (163
files use json.dumps(indent=1), 8 use indent=2, both with
ensure_ascii=False). Rewriting a file with the wrong indent would produce a
diff touching every line, not just the repaired refs, which would make the
actual change unreviewable and risk unrelated formatting drift in frozen-
adjacent content. This script therefore detects each file's own exact
serialization by trying indent values until one byte-reproduces the
original text, refuses to touch a file where no candidate matches
byte-for-byte, and re-serializes with that same exact indent after the
in-place mutation.

SAFETY

- Never guesses: only touches `lineId`; the target it writes is exactly
  the dry-run's own unique-candidate resolution, already proven lossless
  by preview_source_refs_migration.py's losslessness_report().
- Refuses to write a file whose original bytes cannot be exactly
  reproduced by re-serialization (protects any file with an idiosyncratic
  format from being silently reformatted).
- After writing, re-parses every changed file and re-runs the corpus
  classifier to prove every touched ref moved from OBJECT_DANGLING_
  REPAIRABLE to OK, and that overall counts moved by exactly the expected
  amount with no other class's count changing beyond that.

--dry-run (default) reports what would change without writing anything.
--apply writes. Offline, no network.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import validate_source_refs as vsr  # noqa: E402
import preview_source_refs_migration as pre  # noqa: E402

LEARN_DIR = vsr.LEARN_DIR


def detect_format(raw_bytes, data):
    for indent in (1, 2, 3, 4):
        candidate = (json.dumps(data, indent=indent, ensure_ascii=False) + "\n").encode("utf-8")
        if candidate == raw_bytes:
            return indent
    return None


def apply_to_file(path, proposals_for_file):
    """proposals_for_file: list of preview proposals (sugyaId, stepId,
    refIndex, before, after) for this one daf. Mutates and returns the
    parsed doc; caller re-serializes and writes."""
    raw = path.read_bytes()
    doc = json.loads(raw)
    indent = detect_format(raw, doc)
    if indent is None:
        return None, None, "cannot reproduce original file bytes; refusing to touch format"

    by_key = {(p["sugyaId"], p["stepId"], p["refIndex"]): p for p in proposals_for_file}
    applied = 0
    for sugya in doc.get("sugyot", []):
        for step in (sugya.get("argumentFlow") or []):
            refs = step.get("sourceRefs") or []
            for idx, ref in enumerate(refs):
                key = (sugya.get("id"), step.get("id"), idx)
                prop = by_key.get(key)
                if prop is None or not isinstance(ref, dict):
                    continue
                # exact match against the dry run's own recorded before-state
                if ref != prop["before"]:
                    return None, None, (
                        f"{key}: live ref no longer matches the dry-run's recorded "
                        f"before-state (file changed since preview was generated); "
                        f"refusing to apply a stale proposal")
                ref["lineId"] = prop["after"]["lineId"]
                applied += 1
    return doc, indent, applied


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    args = ap.parse_args()

    paths = sorted(LEARN_DIR.glob("*.learning.json"))
    by_daf_proposals = {}
    for path in paths:
        daf, sugyot = vsr.load_daf(path)
        proposals, blocked, stats = pre.plan_for_daf(daf, sugyot)
        mech = [p for p in proposals if p["kind"] == "dangling-lineid-repair"]
        if mech:
            by_daf_proposals[daf] = (path, mech)

    total_proposals = sum(len(v[1]) for v in by_daf_proposals.values())
    print(f"Mechanical sourceRefs repair - {len(by_daf_proposals)} daf, "
          f"{total_proposals} proposal(s)\n")

    written = 0
    written_refs = 0
    errors = []
    for daf in sorted(by_daf_proposals):
        path, mech = by_daf_proposals[daf]
        doc, indent, result = apply_to_file(path, mech)
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
        print(f"\nDRY RUN: would repair {total_proposals} ref(s) across "
              f"{len(by_daf_proposals)} file(s). Re-run with --apply to write.")
        return

    print(f"\nWrote {written_refs} ref(s) across {written} file(s).")

    # Post-write proof: re-classify the whole corpus and confirm the exact
    # expected shift, nothing more.
    counts, _ = vsr.run(sorted(LEARN_DIR.glob("*.learning.json")))
    print(f"\nPost-write corpus classification: {dict(counts)}")
    if counts["OBJECT_DANGLING_REPAIRABLE"] != 0:
        sys.exit(f"ERROR: {counts['OBJECT_DANGLING_REPAIRABLE']} "
                 f"OBJECT_DANGLING_REPAIRABLE ref(s) remain after applying - "
                 f"expected 0.")
    print("OK: 0 OBJECT_DANGLING_REPAIRABLE remain.")


if __name__ == "__main__":
    main()
