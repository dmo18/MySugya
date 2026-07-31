#!/usr/bin/env python3
"""
build_learning_data.py - the demo tractate fixture's own minimal generator.

Phase 3 Step 5 (docs/reports/phase3-inventory.md, docs/platform-closure-plan.md):
this fixture proves a second module can be scaffolded, populated, and
generated without hidden Yoma assumptions. It deliberately does NOT reuse or
clone modules/yoma/scripts/build_learning_data.py (445 lines, with Yoma
naming conventions baked into several f-strings/regexes per that script's
own Step 3B clone-cost finding) - this is a small, self-contained generator
for a 3-daf, 4-sugya synthetic corpus, run directly with cwd-relative paths
exactly like Yoma's own per-module scripts, not through shared/module_resolver.js
or scripts/module_resolver.py (this module is not discoverable under modules/,
so those resolvers are never the right tool for the fixture's own generation
step - see the module.json "physical location vs paths.root" note below).

Reads:
  ../assets/fixture_source/<daf>.source.json      (verbatim source lines)
  ../assets/learning/demotractate/<daf>.learning.json  (enrichment layer)
Writes:
  ../source_store.js   (verbatim source layer, mirrors Yoma's transitional store)
  ../learning_data.js  (full runtime data: TRACTATE_META, PERAKIM, DAF_INDEX, DAF_CONTENT)
  ../coverage.json      (small coverage summary)

Usage:
  python3 build_learning_data.py
"""
import json
from pathlib import Path

SCRIPTS = Path(__file__).parent
ROOT = SCRIPTS.parent
SOURCE_DIR = ROOT / "assets" / "fixture_source"
LEARNING_DIR = ROOT / "assets" / "learning" / "demotractate"

DAF_ORDER = ["1a", "1b", "2a"]

DATA_VERSION = "1.0"
DATA_SCHEMA_VERSION = "1.0"

PERAKIM = [
    {
        "n": 1,
        "name_he": "פֶּרֶק א (דֻּגְמָה)",
        "name_en": "Chapter One (Demo)",
        "topic": "[FIXTURE] The Widget Certification Board's opening rulings",
        "start": "1a",
        "end": "2a",
    }
]

DAF_TOPICS = {
    "1a": "[FIXTURE] Opening certification rule and the prototype question",
    "1b": "[FIXTURE] Resolution of the prototype question and the durable takeaway",
    "2a": "[FIXTURE] Independent recall-window scenario for defective widgets",
}


def load_source(daf):
    data = json.loads((SOURCE_DIR / f"{daf}.source.json").read_text())
    return {line["id"]: line for line in data["lines"]}, data["lines"]


def load_learning(daf):
    return json.loads((LEARNING_DIR / f"{daf}.learning.json").read_text())


def build_source_store_daf(daf, source_lines):
    return {
        "canonicalRef": f"[FIXTURE] Demo Tractate {daf}",
        "daf": daf,
        "lines": [
            {
                "id": line["id"],
                "kind": line["kind"],
                "he": line["he"],
                "vilna_line": line["vilna_line"],
                "en": line["en"],
                "sefaria_ref": None,
                "commentaries": {"rashi": [], "tosafot": []},
            }
            for line in source_lines
        ],
    }


def build_daf_content(daf, source_by_id, source_lines, learning):
    sugyot = []
    for sg in learning["sugyot"]:
        lo, hi = sg["lineRange"]["startVilnaLine"], sg["lineRange"]["endVilnaLine"]
        sg_source_lines = [ln for ln in source_lines if lo <= ln["vilna_line"] <= hi]
        lines_out = []
        for src in sg_source_lines:
            lines_out.append({
                "id": src["id"],
                "kind": src["kind"],
                "he": src["he"],
                "vilna_line": src["vilna_line"],
                "en": src["en"],
                "sefaria_ref": None,
                "commentaries": {"rashi": [], "tosafot": []},
            })
        entry = {
            "id": sg["id"],
            "canonicalRef": f"[FIXTURE] Demo Tractate {daf}",
            "daf": daf,
            "sugyaNumber": sg["sugyaNumber"],
            "lineRange": {
                "startLineId": sg_source_lines[0]["id"],
                "endLineId": sg_source_lines[-1]["id"],
                "startVilnaLine": lo,
                "endVilnaLine": hi,
            },
            "display": sg.get("display", {}),
            "learning": sg.get("learning", {}),
            "lines": lines_out,
            "argumentFlow": sg.get("argumentFlow", []),
            "topicTags": sg.get("topicTags", []),
        }
        for optional_field in (
            "misconceptions", "relatedSugyot", "visualizableElements",
            "quizSeeds", "finalRuling", "difficulty", "review",
        ):
            if optional_field in sg:
                entry[optional_field] = sg[optional_field]
        sugyot.append(entry)

    rashi_lines = []
    for rt in learning.get("rashiTranslations", []):
        rashi_lines.append({
            "id": f"rashi-demo-{daf}-{rt['vilnaLine']:03d}",
            "sourceType": "rashi",
            "daf": daf,
            "vilnaLine": rt["vilnaLine"],
            "he": rt["he"],
            "en": rt.get("en", ""),
            "enSource": "ai_helper_translation",
            "source": "fixture-local",
            "confidence": "helper",
            "linkedGemaraLineIds": rt.get("linkedGemaraLineIds", []),
        })

    result = {
        "canonicalRef": f"[FIXTURE] Demo Tractate {daf}",
        "daf": daf,
        "summary": learning.get("summary", ""),
        "sugyot": sugyot,
    }
    if learning.get("glossary"):
        result["glossary"] = learning["glossary"]
    if rashi_lines:
        result["rashiLines"] = rashi_lines
    if learning.get("review"):
        result["review"] = learning["review"]
    return result


def js_string(s):
    return json.dumps(s, ensure_ascii=False)


def render_source_store(per_daf):
    lines = [
        "/* ============================================",
        "   Demo Tractate (SYNTHETIC FIXTURE) -- verbatim source layer (GENERATED)",
        "   Do NOT edit by hand. Regenerate with:",
        "     python3 scripts/build_learning_data.py",
        "   This is a Phase 3 tractate-agnostic-replication fixture. It contains no",
        "   real Talmud content - every he:/en: value is an explicit placeholder.",
        "   See tests/fixtures/modules/demotractate/MODULE.md.",
        "   ============================================ */",
        f'const DATA_VERSION = {js_string(DATA_VERSION)};',
        f'const DATA_SCHEMA_VERSION = {js_string(DATA_SCHEMA_VERSION)};',
        "const TRACTATE_META = " + json.dumps({
            "id": "demotractate",
            "title_en": "Demo Tractate (Synthetic Fixture)",
            "title_he": "דֻּגְמָה",
            "seder": "Fixture",
            "dafRange": {"first": "1a", "last": "2a"},
            "totalDaf": len(DAF_ORDER),
            "schemaVersion": DATA_SCHEMA_VERSION,
            "fullyStructured": DAF_ORDER,
        }, ensure_ascii=False, indent=2) + ";",
        "const PERAKIM = " + json.dumps(PERAKIM, ensure_ascii=False, indent=2) + ";",
        "const DAF_INDEX = " + json.dumps([
            {"id": d, "perek": 1, "status": "rich", "topic": DAF_TOPICS[d]}
            for d in DAF_ORDER
        ], ensure_ascii=False, indent=2) + ";",
        "const DAF_CONTENT = " + json.dumps(per_daf, ensure_ascii=False, indent=2) + ";",
    ]
    return "\n".join(lines) + "\n"


def render_learning_data(per_daf):
    lines = [
        "/* ============================================",
        "   Demo Tractate (SYNTHETIC FIXTURE) -- canonical learning data (GENERATED)",
        "   Do NOT edit by hand. Regenerate with:",
        "     python3 scripts/build_learning_data.py",
        "   Source line layer: assets/fixture_source/<daf>.source.json",
        "   Learning layer:    assets/learning/demotractate/<daf>.learning.json",
        "",
        "   THIS IS A SYNTHETIC PHASE 3 REPLICATION-PROOF FIXTURE, NOT REAL CONTENT.",
        "   Every he:/en: field below is an explicit bracketed placeholder. Never",
        "   wired into manifest.js, never built by scripts/build.mjs's default",
        "   invocation, never deployed to GitHub Pages. See MODULE.md.",
        "   ============================================ */",
        f'const DATA_VERSION = {js_string(DATA_VERSION)};',
        f'const DATA_SCHEMA_VERSION = {js_string(DATA_SCHEMA_VERSION)};',
        "const LEARNING_DATA_VERSION = DATA_VERSION;",
        "const TRACTATE_META = " + json.dumps({
            "id": "demotractate",
            "title": "Demo Tractate (Synthetic Fixture)",
            "title_he": "דֻּגְמָה",
            "seder": "Fixture",
            "schemaVersion": DATA_SCHEMA_VERSION,
            "dataVersion": DATA_VERSION,
            "sourceEdition": "Phase 3 synthetic fixture - no real source edition",
            "dafRange": {"first": "1a", "last": "2a"},
            "totalDaf": len(DAF_ORDER),
            "fullyStructured": DAF_ORDER,
        }, ensure_ascii=False, indent=2) + ";",
        "const PERAKIM = " + json.dumps(PERAKIM, ensure_ascii=False, indent=2) + ";",
        "const DAF_INDEX = " + json.dumps([
            {"id": d, "perek": 1, "status": "rich", "topic": DAF_TOPICS[d]}
            for d in DAF_ORDER
        ], ensure_ascii=False, indent=2) + ";",
        "const DAF_CONTENT = " + json.dumps(per_daf, ensure_ascii=False, indent=2) + ";",
        "",
        "if (typeof module !== \"undefined\" && module.exports) {",
        "  module.exports = { DATA_VERSION, DATA_SCHEMA_VERSION, LEARNING_DATA_VERSION,",
        "    TRACTATE_META, PERAKIM, DAF_INDEX, DAF_CONTENT };",
        "}",
    ]
    return "\n".join(lines) + "\n"


def main():
    source_store_daf = {}
    learning_daf_content = {}
    sugya_count = 0
    rashi_line_count = 0

    for daf in DAF_ORDER:
        source_by_id, source_lines = load_source(daf)
        learning = load_learning(daf)
        source_store_daf[daf] = build_source_store_daf(daf, source_lines)
        content = build_daf_content(daf, source_by_id, source_lines, learning)
        learning_daf_content[daf] = content
        sugya_count += len(content["sugyot"])
        rashi_line_count += len(content.get("rashiLines", []))

    (ROOT / "source_store.js").write_text(render_source_store(source_store_daf))
    (ROOT / "learning_data.js").write_text(render_learning_data(learning_daf_content))

    coverage = {
        "tractate": "Demo Tractate (Synthetic Fixture)",
        "version": DATA_VERSION,
        "dafCompleted": len(DAF_ORDER),
        "dafTotal": len(DAF_ORDER),
        "sugyaCount": sugya_count,
        "rashiLineCount": rashi_line_count,
        "enrichedDaf": DAF_ORDER,
    }
    (ROOT / "coverage.json").write_text(json.dumps(coverage, indent=1) + "\n")

    print(
        f"wrote source_store.js, learning_data.js, coverage.json: "
        f"{len(DAF_ORDER)} daf, {sugya_count} sugyot, {rashi_line_count} rashi lines"
    )


if __name__ == "__main__":
    main()
