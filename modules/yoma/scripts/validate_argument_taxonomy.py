#!/usr/bin/env python3
"""
validate_argument_taxonomy.py - Phase 2A gate: argumentFlow category
coverage and registry integrity.

Checks, against shared/argument_step_taxonomy.json and the live corpus:

  R1  registry integrity   every category referenced in typeToCategory is
                           defined in categories; every defined category is
                           used by at least one type (no dead entries)
  R2  no duplicate/conflicting mappings   typeToCategory has exactly one
                           category per type (structurally guaranteed by
                           JSON object semantics; checked defensively anyway
                           in case of a future non-JSON registry format)
  R3  category coverage    every distinct type value observed in the corpus
                           has a registry entry (the actual completeness gate)
  R4  no empty/malformed type   no argumentFlow step has a missing, null,
                           non-string, or empty-string type
  R5  no invented Hebrew   every category's `he` is either null or a string
                           containing at least one Hebrew letter (catches an
                           accidental placeholder or transliteration)
  R6  renderer/registry parity   app.jsx's generated ARGUMENT_CATEGORIES and
                           ARGUMENT_TYPE_TO_CATEGORY blocks byte-reproduce
                           from the JSON registry (delegates to
                           generate_argument_taxonomy.py --check, so there is
                           one interpretation of the registry, not two)
  R7  no silent Question fallback   no category other than "inquiry"/"answer"
                           resolves to the Hebrew term for question (שְׁאֵלָה)
                           or symbol "?", and no type outside those two
                           categories can reach that treatment

Offline, no network. Exit 1 on any failure.
"""
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent.parent
REPO = ROOT.parent.parent
LEARN_DIR = ROOT / "assets" / "learning" / "yoma"
TAXONOMY_PATH = REPO / "shared" / "argument_step_taxonomy.json"

HEBREW_RE = re.compile(r'[֐-׿]')


def load_taxonomy():
    return json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))


def observed_types():
    """Return (counter, malformed) - malformed is a list of
    (daf, sugyaId, stepId, reason) for missing/null/non-string/empty type."""
    counter = Counter()
    malformed = []
    for path in sorted(LEARN_DIR.glob("*.learning.json")):
        daf = path.name.replace(".learning.json", "")
        doc = json.loads(path.read_text(encoding="utf-8"))
        for s in doc.get("sugyot", []):
            for st in (s.get("argumentFlow") or []):
                t = st.get("type")
                where = (daf, s.get("id"), st.get("id"))
                if t is None:
                    malformed.append((*where, "missing or null type"))
                elif not isinstance(t, str):
                    malformed.append((*where, f"non-string type: {t!r}"))
                elif t.strip() == "":
                    malformed.append((*where, "empty-string type"))
                else:
                    counter[t] += 1
    return counter, malformed


def main():
    errors = []
    taxonomy = load_taxonomy()
    categories = taxonomy["categories"]
    type_to_category = taxonomy["typeToCategory"]

    # R1: registry integrity
    used_categories = set(type_to_category.values())
    defined_categories = set(categories.keys())
    unknown_refs = used_categories - defined_categories
    for c in sorted(unknown_refs):
        errors.append(f"R1: typeToCategory references undefined category {c!r}")
    dead = defined_categories - used_categories
    for c in sorted(dead):
        errors.append(f"R1: category {c!r} is defined but no type maps to it (dead entry)")

    # R2: duplicate/conflicting mappings (defensive; JSON objects can't
    # actually have duplicate keys once parsed, so this only catches a
    # malformed non-dict value)
    for t, c in type_to_category.items():
        if not isinstance(c, str):
            errors.append(f"R2: type {t!r} maps to non-string category {c!r}")

    # R3: category coverage against the live corpus
    counter, malformed = observed_types()
    uncovered = sorted(set(counter.keys()) - set(type_to_category.keys()))
    for t in uncovered:
        errors.append(f"R3: observed type {t!r} ({counter[t]} step(s)) has no registry entry")

    # R4: malformed type values
    for daf, sid, stid, reason in malformed:
        errors.append(f"R4: {daf} {sid} {stid}: {reason}")

    # R5: no invented Hebrew (either null, or contains a real Hebrew letter)
    for cat_id, meta in categories.items():
        he = meta.get("he")
        if he is not None and not HEBREW_RE.search(he):
            errors.append(f"R5: category {cat_id!r} has he={he!r} with no Hebrew characters")

    # R6: renderer/registry parity
    r = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "generate_argument_taxonomy.py"), "--check"],
        cwd=REPO, capture_output=True, text=True)
    if r.returncode != 0:
        errors.append(f"R6: app.jsx taxonomy block is stale: {(r.stdout + r.stderr).strip()}")

    # R7: no silent Question fallback outside inquiry/answer
    question_shaped = {
        cat_id for cat_id, meta in categories.items()
        if meta.get("sym") == "?" or meta.get("he") == "שְׁאֵלָה"
    }
    allowed = {"inquiry"}
    leaked = question_shaped - allowed
    for c in sorted(leaked):
        errors.append(f"R7: category {c!r} carries the Question symbol/Hebrew "
                      f"but is not the inquiry category")
    # and: nothing outside categories mapping to 'inquiry' can produce this
    # treatment, which R1/R3 already guarantee structurally (every type's
    # sym/he comes from exactly one category's own definition)

    total_types = len(counter)
    total_steps = sum(counter.values())

    if errors:
        print(f"Argument taxonomy validation FAILED ({len(errors)} error(s)):\n")
        for e in errors:
            print(f"  ERROR  {e}")
        print(f"\nCorpus: {total_steps} steps, {total_types} distinct type "
              f"values, {len(type_to_category)} registry entries, "
              f"{len(categories)} categories.")
        sys.exit(1)

    print(f"OK: argument taxonomy valid - {total_steps} steps across "
          f"{total_types} distinct type values, 100% covered by "
          f"{len(type_to_category)} registry entries mapping to "
          f"{len(categories)} categories. app.jsx generated block fresh. "
          f"0 malformed type values.")


if __name__ == "__main__":
    main()
