#!/usr/bin/env python3
"""
test_module_resolver.py - tests for scripts/module_resolver.py.

Uses a temp-directory search root for synthetic descriptors so nothing
here depends on or mutates the real modules/ tree; Yoma resolution is
proven separately against the real modules/yoma/module.json.

Run: python3 scripts/test_module_resolver.py
"""
import copy
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import module_resolver as mr  # noqa: E402

FAILURES = []


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print(f"  {status}  {name}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        FAILURES.append(name)


VALID_FIXTURE = {
    "key": "fixturemasechet",
    "displayNameEn": "Fixture Masechet",
    "displayNameHe": None,
    "sefariaTractate": None,
    "status": "synthetic",
    "publishable": False,
    "seder": None,
    "dafRange": {"first": "2a", "last": "3a"},
    "totalDaf": 3,
    "paths": {
        "root": "modules/fixturemasechet",
        "scriptsRoot": "modules/fixturemasechet/scripts",
        "sourceAssetsRoot": "modules/fixturemasechet/assets",
        "generatedAssetsRoot": "modules/fixturemasechet/assets",
        "sourceStore": "modules/fixturemasechet/source_store.js",
        "learningDataDir": "modules/fixturemasechet/assets/learning/fixturemasechet",
        "learningDataFile": "modules/fixturemasechet/learning_data.js",
        "coverageFile": "modules/fixturemasechet/coverage.json",
        "chapterMetadataLocation": None,
    },
    "schemaMapRef": "shared/schema_map.js",
    "capabilities": {
        "rashi": {"enabled": False},
        "literalTranslation": {"enabled": False},
    },
    "browserTest": {"defaultTargetDaf": "2a"},
    "docsOutput": {},
    "buildRuntime": {"dataScript": "modules/fixturemasechet/learning_data.js"},
}


def write_descriptor(root, key, data):
    d = root / key
    d.mkdir(parents=True, exist_ok=True)
    (d / "module.json").write_text(json.dumps(data), encoding="utf-8")


def expect_error(code, fn):
    try:
        fn()
    except mr.ModuleResolutionError as e:
        return e.code == code, e.code
    return False, "no exception raised"


def main():
    print("valid Yoma resolution (real modules/yoma/module.json)")
    y = mr.resolve_module("yoma")
    check("resolves the real Yoma descriptor", y.key == "yoma")
    check("Yoma is production", y.status == "production" and y.publishable is True)
    check("Yoma is not synthetic", y.is_synthetic is False)
    check("Yoma paths.root matches modules/yoma", y.paths["root"] == "modules/yoma")
    check("Yoma rashi capability enabled with config",
          y.capabilities["rashi"]["enabled"] is True and
          y.capabilities["rashi"]["allowlistsRoot"])
    check("list_modules() finds yoma under the real modules/ tree",
          "yoma" in mr.list_modules())

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_descriptor(root, "fixturemasechet", VALID_FIXTURE)

        print("\nvalid fixture resolution (synthetic descriptor, temp search root)")
        f = mr.resolve_module("fixturemasechet", search_root=root)
        check("resolves the synthetic fixture descriptor", f.key == "fixturemasechet")
        check("fixture is synthetic and non-publishable",
              f.is_synthetic and f.publishable is False)
        check("fixture rashi capability correctly disabled with no config",
              f.capabilities["rashi"]["enabled"] is False and
              "allowlistsRoot" not in f.capabilities["rashi"])
        check("list_modules() finds the fixture under the temp root",
              mr.list_modules(search_root=root) == ["fixturemasechet"])

        print("\nunknown module")
        ok, code = expect_error("UNKNOWN_MODULE",
                                 lambda: mr.resolve_module("doesnotexist", search_root=root))
        check("unknown module raises UNKNOWN_MODULE, never falls back to yoma",
              ok, code)
        ok = mr.resolve_module("doesnotexist" if False else "yoma").key == "yoma"  # sanity
        check("(sanity) yoma itself still resolves normally", ok)

        print("\nmissing descriptor")
        empty_dir_root = root / "empty_root"
        (empty_dir_root / "fixturemasechet").mkdir(parents=True)
        ok, code = expect_error(
            "UNKNOWN_MODULE",
            lambda: mr.resolve_module("fixturemasechet", search_root=empty_dir_root))
        check("directory exists but module.json missing raises UNKNOWN_MODULE", ok, code)

        print("\nmalformed descriptor")
        bad_root = root / "bad_json_root"
        d = bad_root / "brokenmod"
        d.mkdir(parents=True)
        (d / "module.json").write_text("{not valid json", encoding="utf-8")
        ok, code = expect_error(
            "MALFORMED_DESCRIPTOR",
            lambda: mr.resolve_module("brokenmod", search_root=bad_root))
        check("invalid JSON raises MALFORMED_DESCRIPTOR", ok, code)

        not_obj_root = root / "not_obj_root"
        write_descriptor(not_obj_root, "arraymod", [])  # type: ignore[arg-type]
        # write_descriptor json.dumps of a list produces "[]", still valid JSON
        # but not an object - exercise that path directly instead:
        d2 = not_obj_root / "arraymod"
        (d2 / "module.json").write_text("[]", encoding="utf-8")
        ok, code = expect_error(
            "MALFORMED_DESCRIPTOR",
            lambda: mr.resolve_module("arraymod", search_root=not_obj_root))
        check("JSON array root raises MALFORMED_DESCRIPTOR (not an object)", ok, code)

        print("\nmissing required field")
        missing_root = root / "missing_root"
        bad = copy.deepcopy(VALID_FIXTURE)
        bad["key"] = "missingfieldmod"
        bad["paths"]["root"] = "modules/missingfieldmod"
        del bad["totalDaf"]
        write_descriptor(missing_root, "missingfieldmod", bad)
        ok, code = expect_error(
            "MISSING_FIELD",
            lambda: mr.resolve_module("missingfieldmod", search_root=missing_root))
        check("missing top-level required field raises MISSING_FIELD", ok, code)

        print("\npath traversal")
        ok, code = expect_error(
            "INVALID_KEY", lambda: mr.resolve_module("../etc", search_root=root))
        check("'../etc' as a key is rejected before any filesystem access", ok, code)
        ok, code = expect_error(
            "INVALID_KEY", lambda: mr.resolve_module("modules/yoma", search_root=root))
        check("a key containing a slash is rejected", ok, code)
        ok, code = expect_error(
            "INVALID_KEY", lambda: mr.resolve_module("Yoma", search_root=root))
        check("an uppercase key is rejected (not a valid slug)", ok, code)

        print("\nfeature inconsistency")
        incon_root = root / "incon_root"
        bad2 = copy.deepcopy(VALID_FIXTURE)
        bad2["key"] = "inconmod"
        bad2["paths"]["root"] = "modules/inconmod"
        bad2["capabilities"]["rashi"] = {"enabled": True}  # missing allowlistsRoot
        write_descriptor(incon_root, "inconmod", bad2)
        ok, code = expect_error(
            "FEATURE_INCONSISTENCY",
            lambda: mr.resolve_module("inconmod", search_root=incon_root))
        check("enabled capability missing required config is FEATURE_INCONSISTENCY",
              ok, code)

        disabled_with_config_root = root / "disabled_config_root"
        bad3 = copy.deepcopy(VALID_FIXTURE)
        bad3["key"] = "disabledmod"
        bad3["paths"]["root"] = "modules/disabledmod"
        bad3["capabilities"]["rashi"] = {"enabled": False, "allowlistsRoot": "modules/disabledmod/x"}
        write_descriptor(disabled_with_config_root, "disabledmod", bad3)
        ok, code = expect_error(
            "FEATURE_INCONSISTENCY",
            lambda: mr.resolve_module("disabledmod", search_root=disabled_with_config_root))
        check("disabled capability declaring config anyway is FEATURE_INCONSISTENCY",
              ok, code)

        publishable_synthetic_root = root / "pub_synth_root"
        bad4 = copy.deepcopy(VALID_FIXTURE)
        bad4["key"] = "pubsynthmod"
        bad4["paths"]["root"] = "modules/pubsynthmod"
        bad4["publishable"] = True  # synthetic + publishable
        write_descriptor(publishable_synthetic_root, "pubsynthmod", bad4)
        ok, code = expect_error(
            "FEATURE_INCONSISTENCY",
            lambda: mr.resolve_module("pubsynthmod", search_root=publishable_synthetic_root))
        check("a non-publishable-fixture rule: synthetic+publishable=true is rejected",
              ok, code)

        drift_root = root / "drift_root"
        bad5 = copy.deepcopy(VALID_FIXTURE)
        bad5["key"] = "driftmod"
        bad5["paths"]["root"] = "modules/driftmod"
        bad5["buildRuntime"]["dataScript"] = "modules/driftmod/OTHER_FILE.js"
        write_descriptor(drift_root, "driftmod", bad5)
        ok, code = expect_error(
            "FEATURE_INCONSISTENCY",
            lambda: mr.resolve_module("driftmod", search_root=drift_root))
        check("buildRuntime.dataScript disagreeing with paths.learningDataFile "
              "is FEATURE_INCONSISTENCY", ok, code)

        root_mismatch_root = root / "root_mismatch_root"
        bad6 = copy.deepcopy(VALID_FIXTURE)
        bad6["key"] = "rootmismatchmod"
        # paths.root deliberately left as the fixture's original value,
        # disagreeing with the directory key
        write_descriptor(root_mismatch_root, "rootmismatchmod", bad6)
        ok, code = expect_error(
            "MALFORMED_DESCRIPTOR",
            lambda: mr.resolve_module("rootmismatchmod", search_root=root_mismatch_root))
        check("paths.root disagreeing with the module's own directory key "
              "is MALFORMED_DESCRIPTOR", ok, code)

    print("\nno implicit Yoma fallback")
    with tempfile.TemporaryDirectory() as td2:
        empty_root = Path(td2)
        ok, code = expect_error(
            "UNKNOWN_MODULE",
            lambda: mr.resolve_module("yoma", search_root=empty_root))
        check("requesting 'yoma' against a root that has no yoma descriptor "
              "fails cleanly instead of resolving the real modules/yoma "
              "(proves search_root, not a hardcoded yoma path, drives "
              "resolution)", ok, code)

    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s): {', '.join(FAILURES)}")
        sys.exit(1)
    print("All module_resolver checks passed.")


if __name__ == "__main__":
    main()
