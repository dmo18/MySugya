#!/usr/bin/env python3
"""
validate_schema_completeness.py - check the authored learning enrichment layer
(assets/learning/yoma/<daf>.learning.json) against the required display/learning
fields declared in shared/schema_map.js.

This is a different concern from the other Yoma gates. validate_sefaria.py,
validate_en.py, validate_daftext.py, validate_rashi.py, validate_literal.py, and
order_audit.py all check the Gemara SOURCE text layer (he/en/Vilna alignment).
This script checks the learning PRODUCT layer: whether each sugya carries the
display.title and learning.* fields that app.jsx renders as the sugya heading
and the LearningPanel. A sugya can pass every source-text gate and still fail
this one if its enrichment predates the canonical display/learning schema.

Required per sugya (shared/schema_map.js, required: true):
  display.title
  learning.learnerQuestion
  learning.coreTension
  learning.coreMove
  learning.takeaway.text
  learning.ahaMoment
  learning.learningBlocker
  learning.memoryAnchor

Also flagged (not in shared/schema_map.js; legacy-only, pre-dates the
canonical learning shape; should be retired once a sugya is backfilled):
  learning.summary
  learning.openQuestion

Also checked, regardless of canonical/legacy shape:
  quizSeeds[] entries must have non-empty question AND answer if present at
    all (app.jsx filters out incomplete entries silently; an incomplete entry
    is dead weight, not a soft-optional field).
  misconceptions[] entries must be {misconception, correction} objects with
    both non-empty, not plain strings.

Usage:
  python3 scripts/validate_schema_completeness.py            # all daf
  python3 scripts/validate_schema_completeness.py 19b 24a     # specific daf
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
LEARN_DIR = ROOT / "assets" / "learning" / "yoma"

REQUIRED_DISPLAY_FIELDS = ["title"]
REQUIRED_LEARNING_FIELDS = [
    "learnerQuestion", "coreTension", "coreMove",
    "ahaMoment", "learningBlocker", "memoryAnchor",
]
LEGACY_ONLY_LEARNING_FIELDS = ["summary", "openQuestion"]


def is_blank(value):
    return value is None or (isinstance(value, str) and not value.strip())


def daf_sort_key(daf_id):
    m = re.match(r"(\d+)([ab])", daf_id)
    return (int(m.group(1)), m.group(2))


def check_sugya(sug):
    """Return a list of human-readable problem strings for one sugya, or [] if clean."""
    problems = []
    display = sug.get("display") or {}
    learning = sug.get("learning") or {}

    for field in REQUIRED_DISPLAY_FIELDS:
        if is_blank(display.get(field)):
            problems.append(f"missing display.{field}")

    for field in REQUIRED_LEARNING_FIELDS:
        if is_blank(learning.get(field)):
            problems.append(f"missing learning.{field}")

    takeaway = learning.get("takeaway")
    if not isinstance(takeaway, dict) or is_blank(takeaway.get("text")):
        problems.append("missing learning.takeaway.text")

    legacy_present = [f for f in LEGACY_ONLY_LEARNING_FIELDS if not is_blank(learning.get(f))]
    if legacy_present:
        problems.append("legacy-only field(s) present: " + ", ".join(f"learning.{f}" for f in legacy_present))

    for i, q in enumerate(sug.get("quizSeeds") or []):
        if not isinstance(q, dict):
            problems.append(f"quizSeeds[{i}] is not an object")
            continue
        if is_blank(q.get("question")) or is_blank(q.get("answer")):
            problems.append(f"quizSeeds[{i}] missing question or answer")

    for i, m in enumerate(sug.get("misconceptions") or []):
        if not isinstance(m, dict):
            problems.append(f"misconceptions[{i}] is a {type(m).__name__}, expected object")
            continue
        if is_blank(m.get("misconception")) or is_blank(m.get("correction")):
            problems.append(f"misconceptions[{i}] missing misconception or correction")

    return problems


def main():
    target = set(sys.argv[1:]) if len(sys.argv) > 1 else None

    files = sorted(LEARN_DIR.glob("*.learning.json"),
                    key=lambda p: daf_sort_key(p.stem.replace(".learning", "")))
    if target:
        files = [p for p in files if p.stem.replace(".learning", "") in target]

    if not files:
        print(f"No enrichment files found under {LEARN_DIR}")
        sys.exit(1)

    print(f"Checking schema completeness for {len(files)} daf...\n")

    total_sugyot = 0
    total_failing = 0
    daf_with_failures = 0
    quiz_total = 0
    quiz_bad = 0
    misc_total = 0
    misc_bad = 0
    failure_lines = []

    for path in files:
        daf = path.stem.replace(".learning", "")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"  {daf:4s}  PARSE ERROR ({e})")
            daf_with_failures += 1
            continue

        sugyot = data.get("sugyot", [])
        n_fail = 0
        for sug in sugyot:
            total_sugyot += 1
            for q in sug.get("quizSeeds") or []:
                quiz_total += 1
                if not isinstance(q, dict) or is_blank(q.get("question")) or is_blank(q.get("answer")):
                    quiz_bad += 1
            for m in sug.get("misconceptions") or []:
                misc_total += 1
                if not isinstance(m, dict) or is_blank(m.get("misconception")) or is_blank(m.get("correction")):
                    misc_bad += 1

            problems = check_sugya(sug)
            if problems:
                n_fail += 1
                total_failing += 1
                sug_id = sug.get("id", "<no id>")
                failure_lines.append(f"  [{daf}] {sug_id}: " + "; ".join(problems))

        status = "OK" if n_fail == 0 else f"FAIL ({n_fail}/{len(sugyot)} sugyot)"
        if n_fail:
            daf_with_failures += 1
        print(f"  {daf:4s}  {status}")

    print()
    print(f"Daf checked            : {len(files)}")
    print(f"Daf with failures      : {daf_with_failures}")
    print(f"Sugyot checked         : {total_sugyot}")
    print(f"Sugyot failing         : {total_failing}")
    print(f"quizSeeds checked      : {quiz_total}  incomplete: {quiz_bad}")
    print(f"misconceptions checked : {misc_total}  wrong shape or incomplete: {misc_bad}")

    if failure_lines:
        print("\n--- per-sugya failures ---\n")
        for line in failure_lines:
            print(line)

    if total_failing:
        print(f"\nFAIL: {total_failing} of {total_sugyot} sugyot are missing required schema fields.")
        sys.exit(1)

    print("\nOK: all sugyot are schema complete.")


if __name__ == "__main__":
    main()
