#!/usr/bin/env python3
"""
scaffold_module.py - generic module scaffolder (Phase 3 six-row closure
campaign, row 23: fixture can be scaffolded from empty state).

Creates a minimal, valid module skeleton (module.json + learning_data.js
+ coverage.json) from nothing, given only a key and an output root. The
scaffolded module is always status="synthetic", publishable=false, and
sourceAcquisition.strategy="local-fixture" - this tool can only ever
produce a throwaway/fixture module, never a production one, so accidental
misuse cannot create a shadow-production module descriptor.

This is the "from empty state" complement to Step 5's demotractate
fixture (which Step 6 proved resolves/builds/renders correctly as an
*existing* committed module): running this tool against an empty
directory and then feeding its output through the same generic tooling
chain (module_resolver -> validate_module_schema.mjs -> build.mjs
--search-root -> a real browser render) proves the fixture's own shape
is reproducible from nothing, not just hand-maintained.

Usage:
  python3 scripts/scaffold_module.py --key democase --search-root /tmp/scratch
  python3 scripts/scaffold_module.py --key democase --search-root /tmp/scratch --rashi enabled --literal enabled
"""
import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent

sys.path.insert(0, str(Path(__file__).parent))
import module_resolver  # noqa: E402


def build_module_json(key, display_name, daf, rashi_enabled, literal_enabled):
    root = f"modules/{key}"
    capabilities = {
        "rashi": {"enabled": rashi_enabled},
        "literalTranslation": {"enabled": literal_enabled},
        "sourceAcquisition": {
            "strategy": "local-fixture",
            "fixtureInputDir": f"{root}/assets/fixture_source",
        },
    }
    if rashi_enabled:
        capabilities["rashi"]["allowlistsRoot"] = f"{root}/scripts/allowlists"
    if literal_enabled:
        capabilities["literalTranslation"]["assetsDir"] = f"{root}/assets/literal_en"

    return {
        "key": key,
        "displayNameEn": display_name,
        "displayNameHe": display_name,
        "status": "synthetic",
        "publishable": False,
        "seder": "Fixture",
        "dafRange": {"first": daf, "last": daf},
        "totalDaf": 1,
        "paths": {
            "root": root,
            "scriptsRoot": f"{root}/scripts",
            "sourceAssetsRoot": f"{root}/assets",
            "generatedAssetsRoot": f"{root}/assets",
            "sourceStore": f"{root}/source_store.js",
            "learningDataDir": f"{root}/assets/learning/{key}",
            "learningDataFile": f"{root}/learning_data.js",
            "coverageFile": f"{root}/coverage.json",
            "chapterMetadataLocation": "embedded in learningDataFile (PERAKIM constant)",
        },
        "schemaMapRef": "shared/schema_map.js",
        "capabilities": capabilities,
        "browserTest": {"defaultTargetDaf": daf},
        "buildRuntime": {"dataScript": f"{root}/learning_data.js"},
    }


def build_learning_data(key, display_name, daf, rashi_enabled, literal_enabled):
    line = {
        "id": f"{key}-{daf}-l01",
        "kind": "gemara",
        "he": f"[SCAFFOLD] Placeholder Hebrew text for {key} {daf}, line 1.",
        "vilna_line": 1,
        "en": f"[SCAFFOLD] Placeholder English text for {key} {daf}, line 1.",
    }
    if literal_enabled:
        line["en_lit"] = f"[SCAFFOLD] Placeholder literal text for {key} {daf}, line 1."

    sugya = {
        "id": f"{key}-{daf}-s01",
        "canonicalRef": f"[SCAFFOLD] {display_name} {daf}",
        "daf": daf,
        "sugyaNumber": 1,
        "lineRange": {
            "startLineId": line["id"],
            "endLineId": line["id"],
            "startVilnaLine": 1,
            "endVilnaLine": 1,
        },
        "display": {"title": f"[SCAFFOLD] Placeholder sugya title for {daf}"},
        "learning": {
            "learnerQuestion": "[SCAFFOLD] Placeholder learner question.",
            "coreTension": "[SCAFFOLD] Placeholder core tension.",
            "coreMove": "[SCAFFOLD] Placeholder core move.",
            "ahaMoment": "[SCAFFOLD] Placeholder aha moment.",
            "learningBlocker": "[SCAFFOLD] Placeholder learning blocker.",
            "memoryAnchor": "[SCAFFOLD] Placeholder memory anchor.",
            "takeaway": {"type": "conceptual", "text": "[SCAFFOLD] Placeholder takeaway."},
        },
        "lines": [line],
    }

    daf_entry = {
        "canonicalRef": f"[SCAFFOLD] {display_name} {daf}",
        "daf": daf,
        "summary": f"[SCAFFOLD] Placeholder summary for {daf}.",
        "sugyot": [sugya],
    }
    if rashi_enabled:
        daf_entry["rashiLines"] = [{
            "id": f"rashi-{key}-{daf}-001",
            "sourceType": "rashi",
            "daf": daf,
            "vilnaLine": 1,
            "he": f"[SCAFFOLD] Placeholder Rashi Hebrew for {daf}.",
            "en": f"[SCAFFOLD] Placeholder Rashi English for {daf}.",
            "enSource": "ai_helper_translation",
            "source": "talmud.dev",
            "confidence": "helper",
        }]

    tractate_meta = {
        "id": key,
        "title": display_name,
        "title_he": display_name,
        "seder": "Fixture",
        "schemaVersion": "1.0",
        "dataVersion": "1.0",
        "sourceEdition": "Scaffolded - no real source edition",
        "dafRange": {"first": daf, "last": daf},
        "totalDaf": 1,
        "fullyStructured": [daf],
    }
    perakim = [{
        "n": 1, "name_he": "Perek 1", "name_en": "Chapter One",
        "topic": f"[SCAFFOLD] {daf}", "start": daf, "end": daf,
    }]
    daf_index = [{"id": daf, "perek": 1, "status": "rich", "topic": f"[SCAFFOLD] {daf}"}]
    daf_content = {daf: daf_entry}

    header = (
        "/* ============================================\n"
        f"   {display_name} -- canonical learning data (SCAFFOLDED, not real content)\n"
        "   Generated by scripts/scaffold_module.py. Never wired into manifest.js,\n"
        "   never built by scripts/build.mjs's default invocation, never deployed.\n"
        "   ============================================ */\n"
    )
    body = (
        'const DATA_VERSION = "1.0";\n'
        'const DATA_SCHEMA_VERSION = "1.0";\n'
        'const LEARNING_DATA_VERSION = DATA_VERSION;\n'
        f"const TRACTATE_META = {json.dumps(tractate_meta, indent=2, ensure_ascii=False)};\n"
        f"const PERAKIM = {json.dumps(perakim, indent=2, ensure_ascii=False)};\n"
        f"const DAF_INDEX = {json.dumps(daf_index, indent=2, ensure_ascii=False)};\n"
        f"const DAF_CONTENT = {json.dumps(daf_content, indent=2, ensure_ascii=False)};\n"
    )
    return header + body


def build_coverage(key, display_name, daf, rashi_enabled):
    return {
        "tractate": display_name,
        "version": "1.0",
        "dafCompleted": 1,
        "dafTotal": 1,
        "sugyaCount": 1,
        "rashiLineCount": 1 if rashi_enabled else 0,
        "enrichedDaf": [daf],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", required=True, help="module key, e.g. democase")
    ap.add_argument("--search-root", required=True,
                     help="directory to scaffold <key>/ under (never modules/ - "
                          "this tool never writes into the real repo tree)")
    ap.add_argument("--daf", default="1a")
    ap.add_argument("--display-name", default=None)
    ap.add_argument("--rashi", choices=["enabled", "disabled"], default="disabled")
    ap.add_argument("--literal", choices=["enabled", "disabled"], default="disabled")
    opts = ap.parse_args()

    if not module_resolver.KEY_RE.match(opts.key):
        sys.exit(f"ERROR: {opts.key!r} is not a valid module key "
                  f"(must match {module_resolver.KEY_RE.pattern})")

    search_root = Path(opts.search_root).resolve()
    modules_root = (REPO / "modules").resolve()
    if search_root == modules_root or modules_root in search_root.parents or search_root in modules_root.parents:
        sys.exit("ERROR: --search-root must not resolve inside (or contain) the real modules/ tree")

    module_dir = search_root / opts.key
    if module_dir.exists():
        sys.exit(f"ERROR: {module_dir} already exists; scaffold only writes to a fresh directory")

    display_name = opts.display_name or f"Scaffolded Module ({opts.key})"
    rashi_enabled = opts.rashi == "enabled"
    literal_enabled = opts.literal == "enabled"

    module_json = build_module_json(opts.key, display_name, opts.daf, rashi_enabled, literal_enabled)
    learning_data_js = build_learning_data(opts.key, display_name, opts.daf, rashi_enabled, literal_enabled)
    coverage_json = build_coverage(opts.key, display_name, opts.daf, rashi_enabled)

    module_dir.mkdir(parents=True)
    (module_dir / "module.json").write_text(json.dumps(module_json, indent=2, ensure_ascii=False) + "\n")
    (module_dir / "learning_data.js").write_text(learning_data_js)
    (module_dir / "coverage.json").write_text(json.dumps(coverage_json, indent=2, ensure_ascii=False) + "\n")

    # Resolve what was just written through the real, canonical resolver
    # immediately - a scaffold that doesn't pass its own resolver is not a
    # valid scaffold.
    descriptor = module_resolver.resolve_module(opts.key, search_root=str(search_root))
    assert descriptor.key == opts.key

    print(f"scaffolded {module_dir} (key={opts.key}, daf={opts.daf}, "
          f"rashi={opts.rashi}, literal={opts.literal}) - resolves cleanly via module_resolver")


if __name__ == "__main__":
    main()
