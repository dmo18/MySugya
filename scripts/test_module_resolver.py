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
        "sourceAcquisition": {
            "strategy": "local-fixture",
            "fixtureInputDir": "modules/fixturemasechet/assets/fixture_source",
        },
    },
    "browserTest": {"defaultTargetDaf": "2a"},
    "docsOutput": {},
    "buildRuntime": {"dataScript": "modules/fixturemasechet/learning_data.js"},
}


def write_descriptor(root, key, data):
    d = root / key
    d.mkdir(parents=True, exist_ok=True)
    (d / "module.json").write_text(json.dumps(data), encoding="utf-8")


def fixture_for(key):
    """A structurally valid descriptor for a fresh key, with every path
    field (not just paths.root) correctly rewritten - unlike a bare
    copy.deepcopy(VALID_FIXTURE) with only key/paths.root changed, which
    leaves scriptsRoot/sourceAssetsRoot/etc. pointed at the ORIGINAL
    fixturemasechet paths and trips the unrelated "not under the module's
    own root" check before ever reaching whatever this test actually
    means to exercise. Callers mutate the specific field(s) under test
    on the returned dict."""
    old_root = VALID_FIXTURE["paths"]["root"]
    new_root = f"modules/{key}"
    d = copy.deepcopy(VALID_FIXTURE)
    d["key"] = key

    def rewrite(p):
        return new_root + p[len(old_root):] if p.startswith(old_root) else p

    d["paths"] = {k: (rewrite(v) if isinstance(v, str) else v)
                   for k, v in d["paths"].items()}
    d["buildRuntime"]["dataScript"] = rewrite(d["buildRuntime"]["dataScript"])
    sa = d["capabilities"].get("sourceAcquisition")
    if sa and sa.get("fixtureInputDir"):
        sa["fixtureInputDir"] = rewrite(sa["fixtureInputDir"])
    return d


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
        bad2 = fixture_for("inconmod")
        bad2["capabilities"]["rashi"] = {"enabled": True}  # missing allowlistsRoot
        write_descriptor(incon_root, "inconmod", bad2)
        ok, code = expect_error(
            "FEATURE_INCONSISTENCY",
            lambda: mr.resolve_module("inconmod", search_root=incon_root))
        check("enabled capability missing required config is FEATURE_INCONSISTENCY",
              ok, code)

        disabled_with_config_root = root / "disabled_config_root"
        bad3 = fixture_for("disabledmod")
        bad3["capabilities"]["rashi"] = {"enabled": False, "allowlistsRoot": "modules/disabledmod/x"}
        write_descriptor(disabled_with_config_root, "disabledmod", bad3)
        ok, code = expect_error(
            "FEATURE_INCONSISTENCY",
            lambda: mr.resolve_module("disabledmod", search_root=disabled_with_config_root))
        check("disabled capability declaring config anyway is FEATURE_INCONSISTENCY",
              ok, code)

        publishable_synthetic_root = root / "pub_synth_root"
        bad4 = fixture_for("pubsynthmod")
        bad4["publishable"] = True  # synthetic + publishable
        write_descriptor(publishable_synthetic_root, "pubsynthmod", bad4)
        ok, code = expect_error(
            "FEATURE_INCONSISTENCY",
            lambda: mr.resolve_module("pubsynthmod", search_root=publishable_synthetic_root))
        check("a non-publishable-fixture rule: synthetic+publishable=true is rejected",
              ok, code)

        drift_root = root / "drift_root"
        bad5 = fixture_for("driftmod")
        bad5["buildRuntime"]["dataScript"] = "modules/driftmod/OTHER_FILE.js"
        write_descriptor(drift_root, "driftmod", bad5)
        ok, code = expect_error(
            "FEATURE_INCONSISTENCY",
            lambda: mr.resolve_module("driftmod", search_root=drift_root))
        check("buildRuntime.dataScript disagreeing with paths.learningDataFile "
              "is FEATURE_INCONSISTENCY", ok, code)

        root_mismatch_root = root / "root_mismatch_root"
        bad6 = fixture_for("rootmismatchmod")
        bad6["paths"]["root"] = "modules/somethingelse"  # disagrees with the directory key
        write_descriptor(root_mismatch_root, "rootmismatchmod", bad6)
        ok, code = expect_error(
            "MALFORMED_DESCRIPTOR",
            lambda: mr.resolve_module("rootmismatchmod", search_root=root_mismatch_root))
        check("paths.root disagreeing with the module's own directory key "
              "is MALFORMED_DESCRIPTOR", ok, code)

        print("\nsource acquisition strategy (Phase 3 Step 3B)")
        no_sa_root = root / "no_sa_root"
        bad7 = fixture_for("nosamod")
        del bad7["capabilities"]["sourceAcquisition"]
        write_descriptor(no_sa_root, "nosamod", bad7)
        ok, code = expect_error(
            "MISSING_FIELD", lambda: mr.resolve_module("nosamod", search_root=no_sa_root))
        check("missing capabilities.sourceAcquisition entirely is MISSING_FIELD "
              "(unlike rashi/literalTranslation, there is no legal disabled state)",
              ok, code)

        bad_strategy_root = root / "bad_strategy_root"
        bad8 = fixture_for("badstratmod")
        bad8["capabilities"]["sourceAcquisition"] = {"strategy": "telepathy"}
        write_descriptor(bad_strategy_root, "badstratmod", bad8)
        ok, code = expect_error(
            "MALFORMED_DESCRIPTOR",
            lambda: mr.resolve_module("badstratmod", search_root=bad_strategy_root))
        check("an unrecognised strategy value is MALFORMED_DESCRIPTOR", ok, code)

        remote_missing_root = root / "remote_missing_root"
        bad9 = fixture_for("remotemissingmod")
        bad9["capabilities"]["sourceAcquisition"] = {"strategy": "remote-fetch"}
        write_descriptor(remote_missing_root, "remotemissingmod", bad9)
        ok, code = expect_error(
            "MISSING_FIELD",
            lambda: mr.resolve_module("remotemissingmod", search_root=remote_missing_root))
        check("remote-fetch without sourceSystem/fetchScript is MISSING_FIELD", ok, code)

        local_missing_root = root / "local_missing_root"
        bad10 = fixture_for("localmissingmod")
        bad10["capabilities"]["sourceAcquisition"] = {"strategy": "local-fixture"}
        write_descriptor(local_missing_root, "localmissingmod", bad10)
        ok, code = expect_error(
            "MISSING_FIELD",
            lambda: mr.resolve_module("localmissingmod", search_root=local_missing_root))
        check("local-fixture without fixtureInputDir is MISSING_FIELD", ok, code)

        remote_with_fixture_root = root / "remote_with_fixture_root"
        bad11 = fixture_for("remotewithfixturemod")
        bad11["capabilities"]["sourceAcquisition"] = {
            "strategy": "remote-fetch", "sourceSystem": "x", "fetchScript": "y",
            "fixtureInputDir": "modules/remotewithfixturemod/assets/fixture_source",
        }
        write_descriptor(remote_with_fixture_root, "remotewithfixturemod", bad11)
        ok, code = expect_error(
            "FEATURE_INCONSISTENCY",
            lambda: mr.resolve_module("remotewithfixturemod", search_root=remote_with_fixture_root))
        check("remote-fetch declaring fixtureInputDir anyway is FEATURE_INCONSISTENCY",
              ok, code)

        local_with_remote_root = root / "local_with_remote_root"
        bad12 = fixture_for("localwithremotemod")
        bad12["capabilities"]["sourceAcquisition"] = {
            "strategy": "local-fixture",
            "fixtureInputDir": "modules/localwithremotemod/assets/fixture_source",
            "sourceSystem": "should not be here",
        }
        write_descriptor(local_with_remote_root, "localwithremotemod", bad12)
        ok, code = expect_error(
            "FEATURE_INCONSISTENCY",
            lambda: mr.resolve_module("localwithremotemod", search_root=local_with_remote_root))
        check("local-fixture declaring sourceSystem anyway is FEATURE_INCONSISTENCY "
              "(a synthetic module must not claim a live source system)", ok, code)

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
