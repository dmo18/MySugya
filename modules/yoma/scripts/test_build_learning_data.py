#!/usr/bin/env python3
"""test_build_learning_data.py - proves build_learning_data.py's optional
prerequisiteKnowledge passthrough and its DATA_SCHEMA_VERSION/
TRACTATE_META.schemaVersion preserve-or-override behavior.

Every scenario runs against a disposable temp copy of modules/yoma; the real
corpus and the real learning_data.js/coverage.json are never written to.

Run from repo root:
  python3 modules/yoma/scripts/test_build_learning_data.py
"""
import difflib
import importlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import pathlib

YOMA_ROOT = pathlib.Path(__file__).resolve().parents[1]
FAILED = []


def check(name, cond, detail=""):
    print("  %s %s%s" % ("ok  " if cond else "FAIL", name,
                          "" if cond else " (%s)" % str(detail)[-700:]))
    if not cond:
        FAILED.append(name)


def make_temp_copy():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="yoma-build-test-"))
    dest = tmp / "yoma"
    shutil.copytree(YOMA_ROOT, dest)
    return dest


def test_prerequisite_knowledge_passthrough():
    print("\n1-4. prerequisiteKnowledge lossless optional passthrough")
    dest = make_temp_copy()
    sys.path.insert(0, str(dest / "scripts"))
    if "build_learning_data" in sys.modules:
        del sys.modules["build_learning_data"]
    B = importlib.import_module("build_learning_data")
    B.SOURCE_JS = dest / "source_store.js"
    B.OUT_JS = dest / "learning_data.js"
    B.LEARN_DIR = dest / "assets" / "learning" / "yoma"
    B.TALMUDDEV_DIR = dest / "assets" / "talmuddev"

    # Establish a known-absent precondition on the disposable copy rather than
    # assuming the real corpus's current daf 2a sugyot happen to lack this
    # optional field -- that assumption is fragile against ordinary content
    # edits (e.g. a semantic repair legitimately adding prerequisiteKnowledge
    # to daf 2a sugyot) and is not itself part of what this test proves. The
    # whole-daf entry concatenates every sugya, so every sugya's field must be
    # cleared, not just the targeted sugya[0].
    learn_path = B.LEARN_DIR / "2a.learning.json"
    doc = json.loads(learn_path.read_text())
    for s in doc["sugyot"]:
        s.pop("prerequisiteKnowledge", None)
    learn_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2))

    entry_before = B.build_daf_entry("2a")
    check("absent prerequisiteKnowledge stays absent (not fabricated)",
          "prerequisiteKnowledge" not in entry_before)

    doc = json.loads(learn_path.read_text())
    synthetic = ["Familiarity with the seven-day Parhedrin separation rule.",
                 "Basic structure of the Yom Kippur Kohen Gadol service."]
    doc["sugyot"][0]["prerequisiteKnowledge"] = synthetic
    learn_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2))

    entry_present = B.build_daf_entry("2a")
    check("present prerequisiteKnowledge is emitted",
          "prerequisiteKnowledge:" in entry_present)
    expected_js = B.js(synthetic, indent=4)
    check("emitted value is byte/value-identical to the source list",
          ("prerequisiteKnowledge: " + expected_js) in entry_present,
          entry_present)
    check("exactly one occurrence (only the targeted sugya carries it)",
          entry_present.count("prerequisiteKnowledge:") == 1)

    # The inserted lines form ONE contiguous block (the multi-line
    # prerequisiteKnowledge: [...] array); only its first line contains the
    # field name, so check the whole inserted block as a unit rather than
    # requiring every individual line to mention it.
    sm = difflib.SequenceMatcher(a=entry_before.splitlines(), b=entry_present.splitlines())
    opcodes = [op for op in sm.get_opcodes() if op[0] != "equal"]
    check("exactly one contiguous change (a single pure insertion, no deletion/replacement)",
          len(opcodes) == 1 and opcodes[0][0] == "insert", opcodes)
    if opcodes and opcodes[0][0] == "insert":
        inserted = entry_present.splitlines()[opcodes[0][3]:opcodes[0][4]]
        check("the entire inserted block is the prerequisiteKnowledge field",
              bool(inserted) and "prerequisiteKnowledge:" in inserted[0], inserted)

    doc["sugyot"][0]["prerequisiteKnowledge"] = []
    learn_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2))
    entry_empty = B.build_daf_entry("2a")
    check("an explicit empty list, if present, remains an empty list",
          "prerequisiteKnowledge: []" in entry_empty)

    del doc["sugyot"][0]["prerequisiteKnowledge"]
    learn_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2))
    entry_removed = B.build_daf_entry("2a")
    check("removing the key again produces the original absent-field output",
          entry_removed == entry_before)

    del sys.modules["build_learning_data"]
    sys.path.remove(str(dest / "scripts"))
    shutil.rmtree(dest.parent, ignore_errors=True)


def test_schema_version_preserve_and_override():
    print("\n5-6. DATA_SCHEMA_VERSION / TRACTATE_META.schemaVersion preserve + override")
    dest = make_temp_copy()
    script = dest / "scripts" / "build_learning_data.py"

    # Read whatever DATA_SCHEMA_VERSION the corpus this copy was made from
    # currently carries, rather than assuming a hardcoded "1.0" -- that
    # literal drifts forward the moment a real --schema-version bump lands
    # (e.g. an enrichment-schema-migration PR), so this test must track the
    # CURRENT committed value, not a frozen one.
    existing_out = (dest / "learning_data.js").read_text()
    existing_schema_version = re.search(r'const DATA_SCHEMA_VERSION\s*=\s*"([^"]+)"',
                                        existing_out).group(1)

    r = subprocess.run([sys.executable, str(script)], cwd=str(dest),
                       capture_output=True, text=True)
    check("(setup) default regeneration on the disposable copy succeeds",
          r.returncode == 0, r.stdout + r.stderr)
    default_out = (dest / "learning_data.js").read_text()
    m_top = re.search(r'const DATA_SCHEMA_VERSION\s*=\s*"([^"]+)"', default_out)
    m_meta = re.search(r'schemaVersion:\s*"([^"]+)"', default_out)
    check("running normally preserves DATA_SCHEMA_VERSION as the existing %s"
         % existing_schema_version,
          bool(m_top) and m_top.group(1) == existing_schema_version, m_top)
    check("running normally preserves TRACTATE_META.schemaVersion as the existing %s"
         % existing_schema_version,
          bool(m_meta) and m_meta.group(1) == existing_schema_version, m_meta)

    r2 = subprocess.run([sys.executable, str(script), "--schema-version", "1.1-test"],
                        cwd=str(dest), capture_output=True, text=True)
    check("(setup) --schema-version override run succeeds",
          r2.returncode == 0, r2.stdout + r2.stderr)
    override_out = (dest / "learning_data.js").read_text()
    m_top2 = re.search(r'const DATA_SCHEMA_VERSION\s*=\s*"([^"]+)"', override_out)
    m_meta2 = re.search(r'schemaVersion:\s*"([^"]+)"', override_out)
    check("--schema-version overrides DATA_SCHEMA_VERSION",
          bool(m_top2) and m_top2.group(1) == "1.1-test", m_top2)
    check("--schema-version overrides TRACTATE_META.schemaVersion",
          bool(m_meta2) and m_meta2.group(1) == "1.1-test", m_meta2)

    diff_lines = list(difflib.unified_diff(default_out.splitlines(),
                                            override_out.splitlines(), lineterm=""))
    unrelated = [l for l in diff_lines if l.startswith(("+", "-"))
                 and not l.startswith(("+++", "---"))
                 and existing_schema_version not in l and "1.1-test" not in l]
    check("only the schema-version lines differ between the default and override runs",
          not unrelated, unrelated[:10])

    dv_default = re.search(r'const DATA_VERSION\s*=\s*"([^"]+)"', default_out).group(1)
    dv_override = re.search(r'const DATA_VERSION\s*=\s*"([^"]+)"', override_out).group(1)
    check("DATA_VERSION is unaffected by --schema-version", dv_default == dv_override,
          (dv_default, dv_override))

    # a THIRD run with no --schema-version, on top of the override, must now
    # preserve 1.1-test (not silently revert to 1.0) -- proves preservation
    # reads the CURRENT committed value, not a hardcoded default.
    r3 = subprocess.run([sys.executable, str(script)], cwd=str(dest),
                        capture_output=True, text=True)
    check("(setup) a further default run after an override succeeds",
          r3.returncode == 0, r3.stdout + r3.stderr)
    reran_out = (dest / "learning_data.js").read_text()
    m_top3 = re.search(r'const DATA_SCHEMA_VERSION\s*=\s*"([^"]+)"', reran_out)
    check("a subsequent default run preserves the just-set override, not the original default",
          bool(m_top3) and m_top3.group(1) == "1.1-test", m_top3)

    shutil.rmtree(dest.parent, ignore_errors=True)


def main():
    test_prerequisite_knowledge_passthrough()
    test_schema_version_preserve_and_override()
    print()
    if FAILED:
        for name in FAILED:
            print("  FAIL %s" % name)
        sys.exit("test_build_learning_data.py: %d check(s) failed" % len(FAILED))
    print("All build_learning_data.py generator-readiness checks passed.")


if __name__ == "__main__":
    main()
