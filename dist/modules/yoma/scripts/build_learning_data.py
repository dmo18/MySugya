#!/usr/bin/env python3
"""
build_learning_data.py - generate the canonical learning_data.js from the
existing source pipeline plus the structured learning enrichment layer.

Pipeline:
  source assets / validated source store  ->  source line layer (he/en/kind/vilna_line)
  assets/learning/<tractate>/<daf>.learning.json  ->  sugya learning enrichment
  merge  ->  learning_data.js  ->  app

For this proof of concept the SOURCE adapter (load_source_daf) reads the
verbatim, Sefaria-validated, Vilna-aligned line layer from source_store.js -
the pipeline's current materialized output. he/en are copied byte-for-byte from
the raw string literals; they are never re-parsed, re-fetched, or rewritten,
so every existing validator passes against learning_data.js unchanged. As the
pipeline matures this adapter can be repointed at a dedicated per-daf source
store (Sefaria fetch + daftext_align output) without touching the merge/emit
core below.

Enriched daf are listed in ENRICHED. All other daf are carried over verbatim
(raw text slice) from source_store.js so navigation and validation cover the whole
tractate while only the enriched daf gain the learning layer.

Usage:
  python3 scripts/build_learning_data.py [--version X.YY]
"""
import re, json, sys, argparse
from pathlib import Path

ROOT = Path(__file__).parent.parent
SOURCE_JS    = ROOT / "source_store.js"    # transitional source store (see module docstring)
OUT_JS       = ROOT / "learning_data.js"
LEARN_DIR    = ROOT / "assets" / "learning" / "yoma"
TALMUDDEV_DIR = ROOT / "assets" / "talmuddev"

ENRICHED = ["2a", "2b", "3a", "3b", "4a", "4b", "5a", "5b", "6a", "6b", "7a", "7b", "8a", "8b", "9a", "9b", "10a", "10b", "11a", "11b", "12a", "12b", "13a", "13b", "14a", "14b", "15a", "15b", "16a", "16b", "17a", "17b", "18a", "18b", "19a", "19b", "20a", "20b", "21a", "21b", "22a", "22b", "23a", "23b", "24a", "24b", "25a", "25b", "26a", "26b", "27a", "27b", "28a", "28b", "29a", "29b", "30a", "30b", "31a", "31b", "32a", "32b", "33a", "33b", "34a", "34b", "35a", "35b", "36a", "36b", "37a", "37b", "38a", "38b", "39a", "39b", "40a", "40b", "41a", "41b", "42a", "42b", "43a", "43b", "44a", "44b", "45a", "45b", "46a", "46b", "47a", "47b", "48a", "48b", "49a", "49b", "50a", "50b", "51a", "51b", "52a", "52b", "53a", "53b", "54a", "54b", "55a", "55b", "56a", "56b", "57a", "57b", "58a", "58b", "59a", "59b", "60a", "60b", "61a", "61b", "62a", "62b", "63a", "63b", "64a", "64b", "65a", "65b", "66a", "66b", "67a", "67b", "68a", "68b", "69a", "69b", "70a", "70b", "71a", "71b", "72a", "72b", "73a", "73b", "74a", "74b", "75a", "75b", "76a", "76b", "77a", "77b", "78a", "78b", "79a", "79b", "80a", "80b", "81a", "81b", "82a", "82b", "83a", "83b", "84a", "84b", "85a", "85b", "86a", "86b", "87a", "87b", "88a"]  # daf rebuilt from the learning enrichment layer

HE_RE  = re.compile(r'\bhe\s*:\s*"((?:[^"\\]|\\.)*)"')
EN_RE  = re.compile(r'\ben\s*:\s*"((?:[^"\\]|\\.)*)"')
KIND_RE= re.compile(r'\bkind\s*:\s*"(\w+)"')
VL_RE  = re.compile(r'\bvilna_line\s*:\s*(\d+)')
# Matches both new-format IDs (yoma-002b-s01) and old-format IDs (2b-1, 3a-2)
SUG_RE = re.compile(r'\bid\s*:\s*"(?:yoma-[0-9]{3}[ab]-s\d+|\d+[ab]-\d+)"')


def daf_pad(daf):
    """'2a' -> '002a', '88a' -> '088a'."""
    m = re.match(r'(\d+)([ab])', daf)
    return f"{int(m.group(1)):03d}{m.group(2)}"


# ---------------------------------------------------------------------------
# SOURCE adapter: extract verbatim source line layer for one daf from source_store.js.
# Confined to lines:[] blocks (brace/bracket tracked) so enrichment prose can
# never be mistaken for a source field.
# ---------------------------------------------------------------------------
def load_source_daf(daf):
    text = SOURCE_JS.read_text()
    start = text.find(f"// YOMA {daf}\n")
    if start == -1:
        sys.exit(f"ERROR: '// YOMA {daf}' marker not found in {SOURCE_JS.name}")
    # bound at the next daf marker
    nxt = text.find("// YOMA ", start + 5)
    block = text[start:nxt] if nxt != -1 else text[start:]

    sugyot = []          # list of list-of-line-dicts, one per sugya in order
    cur = None
    in_lines = False
    sq_depth = 0         # square-bracket depth of the lines:[] array
    br_depth = 0         # brace depth of the current line object
    obj = None

    for raw in block.split("\n"):
        if not in_lines and SUG_RE.search(raw):
            cur = []
            sugyot.append(cur)
        if not in_lines and re.search(r'\blines\s*:\s*\[', raw):
            in_lines = True
            sq_depth = raw.count("[") - raw.count("]")
            br_depth = 0
            obj = None
            continue
        if in_lines:
            # a new line object opens when brace depth rises from 0
            if br_depth == 0 and "{" in raw:
                obj = {"kind": None, "vilna_line": None, "he": None, "en": None}
            if obj is not None:
                m = KIND_RE.search(raw)
                if m and obj["kind"] is None: obj["kind"] = m.group(1)
                m = HE_RE.search(raw)
                if m and obj["he"] is None: obj["he"] = m.group(1)
                m = VL_RE.search(raw)
                if m and obj["vilna_line"] is None: obj["vilna_line"] = int(m.group(1))
                m = EN_RE.search(raw)
                if m and obj["en"] is None: obj["en"] = m.group(1)
            br_depth += raw.count("{") - raw.count("}")
            if obj is not None and br_depth <= 0:
                if obj["he"] is not None:
                    cur.append(obj)
                obj = None
                br_depth = 0
            sq_depth += raw.count("[") - raw.count("]")
            if sq_depth <= 0:
                in_lines = False
    return sugyot


# ---------------------------------------------------------------------------
# JS emitter: unquoted identifier keys, JSON-escaped string values (matches the
# source_store.js hand-authored style so every regex validator behaves identically).
# ---------------------------------------------------------------------------
def js(value, indent=0):
    pad = "  " * indent
    pad1 = "  " * (indent + 1)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if value is None:
        return '""'
    if isinstance(value, list):
        if not value:
            return "[]"
        items = [pad1 + js(v, indent + 1) for v in value]
        return "[\n" + ",\n".join(items) + "\n" + pad + "]"
    if isinstance(value, dict):
        if not value:
            return "{}"
        items = []
        for k, v in value.items():
            items.append(f"{pad1}{k}: {js(v, indent + 1)}")
        return "{\n" + ",\n".join(items) + "\n" + pad + "}"
    raise TypeError(type(value))


def emit_line(line_src, line_id, sefaria_ref, cont="            "):
    """Emit one source line object verbatim he/en, with stable id + hooks.

    vilna_line MUST sit on a separate physical line from he: order_audit pairs
    them across lines and warns NO-STAMP if both share one line. `cont` is the
    continuation indent for the 2nd and 3rd physical lines.
    """
    he = line_src["he"]
    en = line_src["en"] if line_src["en"] is not None else ""
    ref = json.dumps(sefaria_ref, ensure_ascii=False)
    return (
        f'{{ id: "{line_id}", kind: "{line_src["kind"]}", he: "{he}",\n'
        f'{cont}vilna_line: {line_src["vilna_line"]}, en: "{en}",\n'
        f'{cont}sefaria_ref: {ref}, commentaries: {{ rashi: [], tosafot: [] }} }}'
    )


def load_rashi_lines(daf, enrich):
    """Build the daf-level rashiLines array.

    he comes ONLY from the talmud.dev source (Vilna print order, verbatim).
    en / linkedGemaraLineIds come from the enrichment layer's rashiTranslations
    (editorial helper translation - NOT Sefaria-validated). Every emitted line is
    stamped enSource: "ai_helper_translation", confidence: "helper" so downstream
    tutor/image/learning tools know the English is a helper, not a source layer.
    """
    td_path = TALMUDDEV_DIR / f"{daf}.json"
    if not td_path.exists():
        return []
    td = json.loads(td_path.read_text())
    rashi_he = [line for line in td.get("rashi", []) if line and line.strip()]
    trans = {t["vilnaLine"]: t for t in enrich.get("rashiTranslations", [])}
    pad = daf_pad(daf)
    out = []
    for i, he in enumerate(rashi_he):
        vl = i + 1
        t = trans.get(vl, {})
        out.append({
            "id": f"rashi-yoma-{pad}-{vl:03d}",
            "sourceType": "rashi",
            "daf": daf,
            "vilnaLine": vl,
            "he": he,
            "en": t.get("en", ""),
            "enSource": "ai_helper_translation",
            "source": "talmud.dev",
            "confidence": "helper",
            "linkedGemaraLineIds": t.get("linkedGemaraLineIds", []),
        })
    return out


def build_daf_entry(daf):
    from collections import Counter
    enrich = json.loads((LEARN_DIR / f"{daf}.learning.json").read_text())
    src_sugyot = load_source_daf(daf)
    if len(src_sugyot) != len(enrich["sugyot"]):
        sys.exit(f"ERROR {daf}: source has {len(src_sugyot)} sugyot, "
                 f"enrichment has {len(enrich['sugyot'])}")

    pad = daf_pad(daf)

    # Pre-compute IDs for all lines on this daf, adding letter suffixes for
    # duplicate vilna_line values (e.g. two lines at vilna_line 1 -> l01a, l01b).
    all_vl = [sl["vilna_line"] for sls in src_sugyot for sl in sls]
    vl_freq = Counter(all_vl)
    vl_seen: dict = {}
    sugya_line_ids = []
    for src_lines in src_sugyot:
        ids = []
        for sl in src_lines:
            vl = sl["vilna_line"]
            if vl_freq[vl] > 1:
                vl_seen[vl] = vl_seen.get(vl, 0) + 1
                suffix = chr(ord("a") + vl_seen[vl] - 1)
                lid = f"yoma-{pad}-l{vl:02d}{suffix}"
            else:
                lid = f"yoma-{pad}-l{vl:02d}"
            ids.append(lid)
        sugya_line_ids.append(ids)

    sugyot_js = []
    for si, (src_lines, e) in enumerate(zip(src_sugyot, enrich["sugyot"])):
        if len(src_lines) != len(e["lines"]):
            sys.exit(f"ERROR {daf} {e['id']}: source has {len(src_lines)} lines, "
                     f"enrichment has {len(e['lines'])}")
        # source lines block: 10-space item indent, 12-space continuation,
        # closing bracket at 8 spaces (sugya emitted at js indent=3 -> keys at 8)
        line_objs = []
        for sl, el, lid in zip(src_lines, e["lines"], sugya_line_ids[si]):
            if sl["vilna_line"] != el["vilnaLine"]:
                sys.exit(f"ERROR {daf} {e['id']}: vilna_line mismatch "
                         f"source={sl['vilna_line']} enrichment={el['vilnaLine']}")
            line_objs.append(emit_line(sl, lid, el.get("sefariaRef", "")))
        lines_block = ("[\n" + ",\n".join("          " + lo for lo in line_objs)
                       + "\n        ]")

        ids_for_sugya = sugya_line_ids[si]
        SENTINEL = "@@LINES@@"
        sug = {
            "id": e["id"],
            "canonicalRef": enrich["canonicalRef"],
            "daf": daf,
            "sugyaNumber": e["sugyaNumber"],
            "lineRange": {
                "startLineId": ids_for_sugya[0],
                "endLineId": ids_for_sugya[-1],
                "startVilnaLine": e["lineRange"]["startVilnaLine"],
                "endVilnaLine": e["lineRange"]["endVilnaLine"],
            },
            "display": e["display"],
            "learning": e["learning"],
            "lines": SENTINEL,
            "argumentFlow": e["argumentFlow"],
            "concepts": e["concepts"],
            "conceptRefs": e["conceptRefs"],
            "requiresUnderstanding": e["requiresUnderstanding"],
            "misconceptions": e["misconceptions"],
            "relatedSugyot": e["relatedSugyot"],
            "visualizableElements": e["visualizableElements"],
            "quizSeeds": e["quizSeeds"],
            "finalRuling": e["finalRuling"],
            "difficulty": e["difficulty"],
            "alternateAngles": e["alternateAngles"],
            "topicTags": e.get("topicTags", []),
            "review": e["review"],
        }
        body = js(sug, indent=3)
        body = body.replace(f'lines: "{SENTINEL}"', "lines: " + lines_block)
        sugyot_js.append(body)

    rashi_lines = load_rashi_lines(daf, enrich)

    entry = []
    entry.append(f"  // YOMA {daf}")
    entry.append(f'  "{daf}": {{')
    entry.append(f'    canonicalRef: {json.dumps(enrich["canonicalRef"], ensure_ascii=False)},')
    entry.append(f'    daf: "{daf}",')
    entry.append(f'    summary: {json.dumps(enrich["summary"], ensure_ascii=False)},')
    entry.append(f'    sugyot: [')
    entry.append(",\n".join("      " + s for s in sugyot_js))
    entry.append(f'    ],')
    entry.append(f'    glossary: {js(enrich["glossary"], indent=2)},')
    if rashi_lines:
        entry.append(f'    rashiLines: {js(rashi_lines, indent=2)},')
    entry.append(f'    review: {js(enrich["review"], indent=2)}')
    entry.append(f'  }},')
    return "\n".join(entry)


def slice_between(text, start_token, end_token):
    s = text.find(start_token)
    if s == -1:
        sys.exit(f"ERROR: '{start_token}' not found")
    e = text.find(end_token, s)
    if e == -1:
        sys.exit(f"ERROR: '{end_token}' after '{start_token}' not found")
    return text[s:e + len(end_token)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", help="set DATA_VERSION (else preserve current)")
    args = ap.parse_args()

    src = SOURCE_JS.read_text()

    # version: explicit arg, else keep existing learning_data.js value, else source_store.js
    version = args.version
    if not version and OUT_JS.exists():
        m = re.search(r'const DATA_VERSION\s*=\s*"([^"]+)"', OUT_JS.read_text())
        if m: version = m.group(1)
    if not version:
        m = re.search(r'const DATA_VERSION\s*=\s*"([^"]+)"', src)
        version = m.group(1) if m else "0.0"

    # header: PERAKIM + DAF_INDEX carried over verbatim
    perek_index_block = slice_between(src, "const PERAKIM = [", "];")
    # DAF_INDEX closing ]; is the next one after const DAF_INDEX
    di_start = src.find("const DAF_INDEX = [")
    daf_index_block = slice_between(src[di_start:], "const DAF_INDEX = [", "];")
    # include the comment line preceding DAF_INDEX if present
    comment_start = src.rfind("\n", 0, di_start) + 1
    di_comment = src[comment_start:di_start]

    # DAF_CONTENT body chunked by // YOMA markers
    body = slice_between(src, "const DAF_CONTENT = {", "\n};")
    body = body[len("const DAF_CONTENT = {"):-len("\n};")]
    chunks = re.split(r'(?=^[ \t]*// YOMA )', body, flags=re.M)
    chunks = [c for c in chunks if c.strip()]

    rebuilt = []
    for chunk in chunks:
        m = re.match(r'\s*// YOMA (\S+)', chunk)
        daf = m.group(1) if m else None
        if daf in ENRICHED:
            rebuilt.append(build_daf_entry(daf) + "\n")
        else:
            rebuilt.append(chunk if chunk.endswith("\n") else chunk + "\n")

    meta = {
        "id": "yoma",
        "title": "Yoma",
        "title_he": "יוֹמָא",
        "seder": "Moed",
        "schemaVersion": "1.0",
        "sourceEdition": "Vilna / Sefaria / talmud.dev",
        "dafRange": {"first": "2a", "last": "88a"},
        "totalDaf": 173,
        "fullyStructured": ENRICHED,
    }

    out = []
    out.append("/* ============================================")
    out.append("   Yoma -- canonical learning data (GENERATED)")
    out.append("   Do NOT edit by hand. Regenerate with:")
    out.append("     python3 scripts/build_learning_data.py")
    out.append("   Source line layer: source_store.js (verbatim he/en, Vilna-aligned).")
    out.append("   Learning layer:    assets/learning/yoma/<daf>.learning.json")
    out.append("   ============================================ */")
    out.append('// Tractate Yoma: 8 chapters (scope: 2a-88a). Perek boundaries: 1(2a-21b), 2(22a-28a), 3(28b-39b), 4(39b-47b), 5(47b-57b), 6(57b-68b), 7(68b-73b), 8(73b-88a)')
    out.append(f'const DATA_VERSION = "{version}";        // single version source; synced to VERSION/package.json/index.html by pre-commit')
    out.append('const DATA_SCHEMA_VERSION = "1.0";   // sugya/line object shape version')
    out.append('const LEARNING_DATA_VERSION = DATA_VERSION;')
    out.append("const TRACTATE_META = " + js(meta, indent=0) + ";")
    out.append("TRACTATE_META.dataVersion = DATA_VERSION;  // always mirrors DATA_VERSION - never a stale literal")
    out.append(perek_index_block)
    out.append("")
    out.append(di_comment + daf_index_block)
    out.append("")
    out.append("const DAF_CONTENT = {")
    out.append("".join(rebuilt).rstrip("\n"))
    out.append("};")
    out.append("")

    OUT_JS.write_text("\n".join(out))
    print(f"wrote {OUT_JS.name} (v{version}, enriched: {', '.join(ENRICHED)})")

    # Generate coverage.json
    generate_coverage(version)


def generate_coverage(version: str) -> None:
    """Emit coverage.json summarizing enrichment progress."""
    TOTAL_DAF = 173  # Yoma 2a-88a
    sugya_count = 0
    rashi_count = 0

    for daf in ENRICHED:
        path = LEARN_DIR / f"{daf}.learning.json"
        if path.exists():
            try:
                d = json.loads(path.read_text())
                sugya_count += len(d.get("sugyot", []))
                rashi_count += len(d.get("rashiTranslations", []))
            except Exception:
                pass

    last_daf = ENRICHED[-1] if ENRICHED else ""
    completion_pct = round(len(ENRICHED) / TOTAL_DAF * 100, 1)

    coverage = {
        "tractate": "Yoma",
        "version": version,
        "dafCompleted": len(ENRICHED),
        "dafTotal": TOTAL_DAF,
        "sugyaCount": sugya_count,
        "rashiLineCount": rashi_count,
        "enrichedDaf": ENRICHED,
        "completionPercent": completion_pct,
        "lastCompletedDaf": last_daf,
    }

    out_path = ROOT / "coverage.json"
    out_path.write_text(json.dumps(coverage, indent=2, ensure_ascii=False))
    print(f"coverage.json: {len(ENRICHED)}/{TOTAL_DAF} daf ({completion_pct}%), {sugya_count} sugyot, {rashi_count} Rashi lines")


if __name__ == "__main__":
    main()
