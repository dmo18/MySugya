#!/usr/bin/env python3
"""
make_rashi_work_packet.py - emit a compact, deterministic per-daf work
packet for bounded Rashi helper work, so a worker model does not have to
re-derive context from the whole repository.

Contents per daf:
  - raw Rashi print lines (verbatim Hebrew, numbered; the translation
    ground truth)
  - the daf's real local Gemara id space with each id's vilna_line and the
    opening of its Hebrew text (the only legal linkedGemaraLineIds targets)
  - sugya ranges and titles
  - current rashiTranslations (vilnaLine, current links, current en)
  - validator baseline for this daf: allowlisted content violations,
    repetition baseline entries, count-mismatch tolerances
  - the required post-edit command checklist

Usage:
  python3 scripts/make_rashi_work_packet.py 47a [more daf...] [--json]

Default output is markdown (deterministic ordering). --json emits the same
data as JSON. Offline; reads only repository files.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import audit_rashi_semantic

ROOT = Path(__file__).parent.parent
LEARN_DIR = ROOT / "assets" / "learning" / "yoma"
TALMUDDEV_DIR = ROOT / "assets" / "talmuddev"
DATA_JS = ROOT / "learning_data.js"
ALLOW_DIR = Path(__file__).parent / "allowlists"

POST_EDIT_COMMANDS = [
    "cd modules/yoma && python3 scripts/build_learning_data.py",
    "cd modules/yoma && python3 scripts/build_literal_layer.py --apply",
    "edit VERSION (one patch bump), then python3 scripts/sync_version.py",
    "npm run validate:offline:yoma",
    "npm run check:rashi-pr-scope:yoma",
    "npm test && npm run test:browser",
]

RULES = [
    "If this packet's drift profile says SHIFTED or FABRICATION-SUSPECT, STOP: this daf is not eligible for stub repair or link edits; it needs the recommended Fable/Sonnet task type.",
    "Translate every raw Rashi line from its own Hebrew; no placeholders, no generic filler.",
    "linkedGemaraLineIds may only use ids listed in this packet's Gemara id table.",
    "Lines past the last Gemara segment link to the final id (boundary policy); linking policy never exempts a line from translation.",
    "Only rashiTranslations en and linkedGemaraLineIds may change; never touch he, sugyot, argumentFlow, or learning fields.",
    "Never add allowlist entries. If a validator fails, fix the content or stop and escalate.",
    "No em dashes or en dashes in helper English.",
    "Stop and escalate on any uncertain Hebrew meaning or placement.",
]


def gemara_ids_for(daf):
    text = DATA_JS.read_text()
    starts = [(m.group(1), m.start()) for m in re.finditer(r"// YOMA (\S+)", text)]
    block = None
    for i, (d, s) in enumerate(starts):
        if d == daf:
            e = starts[i + 1][1] if i + 1 < len(starts) else len(text)
            block = text[s:e]
            break
    if block is None:
        return []
    out = []
    pat = re.compile(r'id:\s*"(yoma-[0-9]+[ab]-l[0-9]+[ab]?)",\s*kind:\s*"gemara",\s*he:\s*"((?:[^"\\]|\\.)*)",\s*\n?\s*vilna_line:\s*(\d+)')
    for m in pat.finditer(block):
        he = json.loads('"' + m.group(2) + '"').replace("\n", " ")
        out.append({"id": m.group(1), "vilnaLine": int(m.group(3)), "heOpening": he[:60]})
    return out


def baseline_for(daf):
    base = {"contentAllowlisted": [], "countMismatch": None, "repetitionBaseline": []}
    ca = ALLOW_DIR / "rashi_content_allowlist.json"
    if ca.exists():
        d = json.loads(ca.read_text())
        base["contentAllowlisted"] = sorted(e["vilnaLine"] for e in d.get("entries", []) if e["daf"] == daf)
        for c in d.get("count_mismatches", []):
            if c["daf"] == daf:
                base["countMismatch"] = c
    rb = ALLOW_DIR / "rashi_repetition_baseline.json"
    if rb.exists():
        d = json.loads(rb.read_text())
        base["repetitionBaseline"] = [e for e in d.get("entries", []) if e["daf"] == daf]
    return base


def packet_for(daf):
    tpath = TALMUDDEV_DIR / f"{daf}.json"
    lpath = LEARN_DIR / f"{daf}.learning.json"
    if not tpath.exists():
        sys.exit(f"ERROR: {tpath} not found")
    raw = [l for l in json.loads(tpath.read_text()).get("rashi", []) if l and l.strip()]
    enrich = json.loads(lpath.read_text()) if lpath.exists() else {}
    sugyot = [{
        "id": s.get("id"),
        "title": (s.get("display") or {}).get("title", ""),
        "startVilnaLine": s["lineRange"]["startVilnaLine"],
        "endVilnaLine": s["lineRange"]["endVilnaLine"],
    } for s in enrich.get("sugyot", [])]
    profile = audit_rashi_semantic.profile_daf(daf)
    drift = None
    if profile:
        drift = {
            "classification": profile["classification"],
            "anchorsFound": profile["anchorsFound"],
            "anchorsMissing": profile["anchorsMissing"],
            "offsets": profile["offsets"],
            "maxAbsOffset": profile["maxAbsOffset"],
            "haikuSafe": profile["haikuSafe"],
            "recommendedTaskType": profile["recommendedTaskType"],
        }
    return {
        "daf": daf,
        "rawRashiCount": len(raw),
        "rawRashi": [{"line": i + 1, "he": l} for i, l in enumerate(raw)],
        "gemaraIds": gemara_ids_for(daf),
        "sugyot": sugyot,
        "currentTranslations": [{
            "vilnaLine": e["vilnaLine"],
            "linkedGemaraLineIds": e.get("linkedGemaraLineIds", []),
            "en": e.get("en", ""),
        } for e in enrich.get("rashiTranslations", [])],
        "validatorBaseline": baseline_for(daf),
        "driftProfile": drift,
        "rules": RULES,
        "postEditCommands": POST_EDIT_COMMANDS,
    }


def to_markdown(p):
    L = []
    L.append(f"# Rashi work packet: Yoma {p['daf']}")
    L.append(f"\nRaw Rashi lines: {p['rawRashiCount']} | current entries: {len(p['currentTranslations'])} "
             f"| Gemara ids: {len(p['gemaraIds'])}")
    d = p.get("driftProfile")
    if d:
        L.append("\n## Semantic drift profile")
        L.append(f"- classification: {d['classification']}")
        L.append(f"- anchors: {d['anchorsFound']} found, {d['anchorsMissing']} missing; "
                 f"offsets: {' '.join(f'{o:+d}' for o in d['offsets']) or 'none'}"
                 f" (max |offset| {d['maxAbsOffset']})")
        L.append(f"- haiku-safe for line-level work: {'yes' if d['haikuSafe'] else 'NO'}")
        if not d["haikuSafe"]:
            L.append(f"- WARNING: stub repair and link edits are FORBIDDEN on this daf; "
                     f"required task type: {d['recommendedTaskType']} (Fable/Sonnet, Fable review)")
    L.append("\n## Rules")
    for r in p["rules"]:
        L.append(f"- {r}")
    L.append("\n## Sugyot")
    for s in p["sugyot"]:
        L.append(f"- {s['id']} (vilna {s['startVilnaLine']}-{s['endVilnaLine']}): {s['title']}")
    L.append("\n## Legal Gemara ids (the ONLY valid linkedGemaraLineIds targets)")
    for g in p["gemaraIds"]:
        L.append(f"- {g['id']} (vilna {g['vilnaLine']}): {g['heOpening']}")
    L.append("\n## Raw Rashi Hebrew (translation ground truth)")
    for r in p["rawRashi"]:
        L.append(f"{r['line']:3d}: {r['he']}")
    L.append("\n## Current rashiTranslations")
    for t in p["currentTranslations"]:
        links = ",".join(t["linkedGemaraLineIds"]) or "(none)"
        L.append(f"{t['vilnaLine']:3d} [{links}]: {t['en']}")
    b = p["validatorBaseline"]
    L.append("\n## Validator baseline for this daf")
    L.append(f"- content-allowlisted lines: {b['contentAllowlisted'] or 'none'}")
    L.append(f"- count mismatch tolerance: {b['countMismatch'] or 'none'}")
    L.append(f"- repetition baseline: {b['repetitionBaseline'] or 'none'}")
    L.append("\n## Required post-edit commands (all must pass)")
    for c in p["postEditCommands"]:
        L.append(f"- {c}")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("daf", nargs="+")
    ap.add_argument("--json", action="store_true")
    opts = ap.parse_args()
    packets = [packet_for(d) for d in opts.daf]
    if opts.json:
        print(json.dumps(packets if len(packets) > 1 else packets[0],
                         ensure_ascii=False, indent=1))
    else:
        print("\n\n".join(to_markdown(p) for p in packets))


if __name__ == "__main__":
    main()
