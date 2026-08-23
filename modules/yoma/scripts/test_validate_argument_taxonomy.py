#!/usr/bin/env python3
"""
test_validate_argument_taxonomy.py - unit tests for the argumentFlow
category registry validator and the app.jsx generator, against synthetic
fixtures so each rule is exercised deliberately, plus corpus-level checks
against the real registry and corpus.

Run: cd modules/yoma && python3 scripts/test_validate_argument_taxonomy.py
"""
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parent.parent.parent

spec = importlib.util.spec_from_file_location(
    "validate_argument_taxonomy", HERE / "validate_argument_taxonomy.py")
vat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vat)

FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}{(' - ' + detail) if detail else ''}")
        FAILURES.append(name)


def run_rules(taxonomy, counter, malformed):
    """Re-run the R1/R3/R4/R5/R7 body of main() against synthetic inputs,
    without touching the real corpus or filesystem (R2/R6 are structural/
    subprocess checks exercised separately below)."""
    errors = []
    categories = taxonomy["categories"]
    type_to_category = taxonomy["typeToCategory"]

    used = set(type_to_category.values())
    defined = set(categories.keys())
    for c in sorted(used - defined):
        errors.append(f"R1: typeToCategory references undefined category {c!r}")
    for c in sorted(defined - used):
        errors.append(f"R1: category {c!r} is defined but no type maps to it (dead entry)")

    uncovered = sorted(set(counter.keys()) - set(type_to_category.keys()))
    for t in uncovered:
        errors.append(f"R3: observed type {t!r} has no registry entry")

    for daf, sid, stid, reason in malformed:
        errors.append(f"R4: {daf} {sid} {stid}: {reason}")

    for cat_id, meta in categories.items():
        he = meta.get("he")
        if he is not None and not vat.HEBREW_RE.search(he):
            errors.append(f"R5: category {cat_id!r} has he={he!r} with no Hebrew characters")

    question_shaped = {cid for cid, m in categories.items()
                      if m.get("sym") == "?" or m.get("he") == "שְׁאֵלָה"}
    for c in sorted(question_shaped - {"inquiry"}):
        errors.append(f"R7: category {c!r} carries Question symbol/Hebrew")

    return errors


# ---------------------------------------------------------------- R1
print("R1: registry integrity")

tax = {"categories": {"a": {"he": None}}, "typeToCategory": {"x": "a"}}
errs = run_rules(tax, {"x": 1}, [])
check("clean registry produces no R1 errors", not any("R1" in e for e in errs))

tax_bad_ref = {"categories": {"a": {"he": None}}, "typeToCategory": {"x": "b"}}
errs = run_rules(tax_bad_ref, {"x": 1}, [])
check("undefined category reference is caught",
      any("undefined category" in e for e in errs), str(errs))

tax_dead = {"categories": {"a": {"he": None}, "b": {"he": None}}, "typeToCategory": {"x": "a"}}
errs = run_rules(tax_dead, {"x": 1}, [])
check("dead (unused) category is caught",
      any("dead entry" in e for e in errs), str(errs))

# ---------------------------------------------------------------- R3
print("\nR3: category coverage against observed corpus")

tax = {"categories": {"a": {"he": None}}, "typeToCategory": {"x": "a"}}
errs = run_rules(tax, {"x": 5, "y": 2}, [])
check("uncovered observed type is caught",
      any("'y'" in e and "no registry entry" in e for e in errs), str(errs))

errs = run_rules(tax, {"x": 5}, [])
check("fully covered corpus produces no R3 errors", not any("R3" in e for e in errs))

# ---------------------------------------------------------------- R4
print("\nR4: malformed type values")

errs = run_rules({"categories": {}, "typeToCategory": {}}, {},
                 [("2a", "s01", "step-01", "missing or null type")])
check("malformed type entries are reported verbatim",
      any("missing or null type" in e for e in errs), str(errs))

# ---------------------------------------------------------------- R5
print("\nR5: no invented Hebrew")

tax = {"categories": {"a": {"he": "not hebrew text"}}, "typeToCategory": {"x": "a"}}
errs = run_rules(tax, {"x": 1}, [])
check("non-Hebrew he value is caught", any("R5" in e for e in errs), str(errs))

tax = {"categories": {"a": {"he": "שְׁאֵלָה"}}, "typeToCategory": {"x": "a"}}
errs = run_rules(tax, {"x": 1}, [])
check("real Hebrew text passes R5", not any("R5" in e for e in errs))

tax = {"categories": {"a": {"he": None}}, "typeToCategory": {"x": "a"}}
errs = run_rules(tax, {"x": 1}, [])
check("null he passes R5 (no Hebrew claimed)", not any("R5" in e for e in errs))

# ---------------------------------------------------------------- R7
print("\nR7: no silent Question fallback outside inquiry")

tax = {"categories": {"inquiry": {"sym": "?", "he": "שְׁאֵלָה"},
                      "ruling": {"sym": "?", "he": None}},
       "typeToCategory": {"question": "inquiry", "ruling": "ruling"}}
errs = run_rules(tax, {"question": 1, "ruling": 1}, [])
check("a non-inquiry category carrying the Question symbol is caught",
      any("R7" in e and "'ruling'" in e for e in errs), str(errs))

tax = {"categories": {"inquiry": {"sym": "?", "he": "שְׁאֵלָה"}},
       "typeToCategory": {"question": "inquiry"}}
errs = run_rules(tax, {"question": 1}, [])
check("inquiry itself carrying the Question symbol is fine",
      not any("R7" in e for e in errs))

# ---------------------------------------------------------------- generator
print("\napp.jsx generator")

taxonomy_real = json.loads((REPO / "shared" / "argument_step_taxonomy.json").read_text(encoding="utf-8"))

with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    fake_app = tmp / "app.jsx"
    fake_app.write_text(
        "const x = 1;\n"
        "// BEGIN GENERATED ARGUMENT TAXONOMY\n"
        "stale content\n"
        "// END GENERATED ARGUMENT TAXONOMY\n"
        "const y = 2;\n",
        encoding="utf-8")
    fake_taxonomy = tmp / "argument_step_taxonomy.json"
    fake_taxonomy.write_text(json.dumps({
        "categories": {"a": {"en": "A", "he": None, "symbol": "○"}},
        "typeToCategory": {"x": "a"},
    }), encoding="utf-8")

    import importlib.util as ilu
    gspec = ilu.spec_from_file_location("gen_mod", REPO / "scripts" / "generate_argument_taxonomy.py")
    gen = ilu.module_from_spec(gspec)
    gspec.loader.exec_module(gen)

    old_app, old_tax = gen.APP_JSX, gen.TAXONOMY_PATH
    gen.APP_JSX, gen.TAXONOMY_PATH = fake_app, fake_taxonomy
    try:
        block = gen.generate_block(json.loads(fake_taxonomy.read_text()))
        check("generated block contains the category key",
              '"en": "A"' in block or "en: \"A\"" in block, block)
        check("generated block contains the type mapping",
              'x: "a"' in block, block)

        gen.main.__wrapped__ = None  # no-op, keep lints quiet
    finally:
        gen.APP_JSX, gen.TAXONOMY_PATH = old_app, old_tax

# ---------------------------------------------------------------- corpus-level (real data)
print("\ncorpus-level (real registry, real corpus)")

counter, malformed = vat.observed_types()
real_errors_uncovered = sorted(set(counter.keys()) - set(taxonomy_real["typeToCategory"].keys()))
check("every observed type in the real corpus has a registry entry",
      not real_errors_uncovered, str(real_errors_uncovered))
check("no malformed type values in the real corpus", not malformed, str(malformed[:5]))

used = set(taxonomy_real["typeToCategory"].values())
defined = set(taxonomy_real["categories"].keys())
check("no dead categories in the real registry", used == defined,
      f"defined-only={defined-used} used-only={used-defined}")

for cat_id, meta in taxonomy_real["categories"].items():
    he = meta.get("he")
    if he is not None:
        check(f"real category {cat_id!r} he is genuine Hebrew text",
              bool(vat.HEBREW_RE.search(he)), he)

qshaped = {c for c, m in taxonomy_real["categories"].items()
          if m.get("symbol") == "?" or m.get("he") == "שְׁאֵלָה"}
check("only 'inquiry' carries the Question symbol/Hebrew in the real registry",
      qshaped == {"inquiry"}, str(qshaped))

total_steps = sum(counter.values())
print(f"  (informational) total observed argumentFlow steps in corpus: {total_steps}")

print()
if FAILURES:
    print(f"FAILED: {len(FAILURES)} check(s): {', '.join(FAILURES)}")
    sys.exit(1)
print("All argument taxonomy validator checks passed.")
