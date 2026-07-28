#!/usr/bin/env python3
"""
make_rashi_work_packet.py - emit a compact, deterministic per-daf work
packet for bounded Rashi helper work, so a worker model does not have to
re-derive context from the whole repository.

Contents per daf:
  - raw Rashi print lines (verbatim Hebrew, numbered; the translation
    ground truth)
  - the daf's real local segment id space, Gemara AND Mishnah kinds, in
    source order, each with its kind, vilna_line, and FULL untruncated
    Hebrew text (the only legal linkedGemaraLineIds targets). Sparse and
    suffixed ids such as l13a/l13b are preserved verbatim; ids are never
    renumbered or manufactured. Full text is included because links are
    SEMANTIC: the worker must match each Rashi comment to the segment
    whose text it explains, never map positionally by vilna line number
    (the PR #80 failure mode: the table then omitted the kind "mishna"
    segment l13b, and 50 of 60 links had to be corrected in review).
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
SCRIPTS = Path(__file__).parent
ALLOW_DIR = SCRIPTS / "allowlists"

POST_EDIT_COMMANDS = [
    "cd modules/yoma && python3 scripts/build_learning_data.py",
    "cd modules/yoma && python3 scripts/build_literal_layer.py --apply",
    "edit VERSION (one patch bump), then python3 scripts/sync_version.py",
    "npm run validate:offline:yoma",
    "npm run check:rashi-pr-scope:yoma",
    "npm test && npm run test:browser",
]

RULES = [
    "If this packet's drift profile says SHIFTED or FABRICATION-SUSPECT, STOP: this daf is not eligible for stub repair or link edits; it needs the recommended Sonnet task type.",
    "Translate every raw Rashi line from its own Hebrew; no placeholders, no generic filler.",
    "Never write or preserve scaffold narration ('Rashi: opens/continues/concludes ...') or guessed bracket completions such as '[the Gemara]'; even when part of the old meaning is correct, rewrite the line as a direct translation of its own Hebrew (audit_rashi_scaffold.py enforces this).",
    "linkedGemaraLineIds are SEMANTIC text anchors: link each Rashi comment to the local segment(s) whose text it explains, by matching the Rashi dibbur hamatchil, quoted phrase, subject, or discussion against the full segment text in this packet's id table.",
    "NEVER assign links by vilna line number or positional offset. A Rashi line's number and a segment's vilna_line are unrelated coordinates; positional mapping is exactly the failure mode this packet exists to prevent.",
    "linkedGemaraLineIds may only use ids listed in this packet's local segment id table (Gemara and Mishnah kinds alike).",
    "A single Rashi entry may link to multiple local segments when its comment genuinely spans them.",
    "A line whose commentary continues the FINAL segment's own discussion past the last id stays on that final id (boundary policy). Boundary policy never justifies linking unrelated commentary to the last available id, and never exempts a line from translation.",
    "If a comment's correct target segment cannot be identified from the segment text, STOP and escalate; never guess.",
    "Only rashiTranslations en and linkedGemaraLineIds may change; never touch he, sugyot, argumentFlow, or learning fields.",
    "Never add allowlist entries. If a validator fails, fix the content or stop and escalate.",
    "No em dashes or en dashes in helper English.",
    "Stop and escalate on any uncertain Hebrew meaning or placement.",
]


def local_segments_for(daf):
    """Every real local segment in this daf's generated data block that may
    anchor Rashi: Gemara AND Mishnah kinds, in source order, with the FULL
    untruncated Hebrew text. Only ids that exist in the data are emitted
    (sparse and suffixed ids such as l13a/l13b come through verbatim);
    nothing is renumbered or manufactured. Restricting this table to kind
    "gemara" is the PR #80 root cause: the end-of-perek Mishnah l13b
    vanished from 68b's table and the worker fell back to positional
    linking."""
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
    seen = set()
    pat = re.compile(r'id:\s*"(yoma-[0-9]+[ab]-l[0-9]+[ab]?)",\s*kind:\s*"(gemara|mishna)",\s*he:\s*"((?:[^"\\]|\\.)*)",\s*\n?\s*vilna_line:\s*(\d+)')
    for m in pat.finditer(block):
        if m.group(1) in seen:
            continue
        seen.add(m.group(1))
        he = json.loads('"' + m.group(3) + '"').replace("\n", " ")
        out.append({"id": m.group(1), "kind": m.group(2),
                    "vilnaLine": int(m.group(4)), "he": he})
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


def scaffold_debt_for(daf, total_lines):
    """This daf's entries in the locked scaffold-fabrication debt baseline,
    plus the task-type recommendation the contamination profile implies:
    definite fabrication (bracket guessing, passthrough, line-number
    placeholders) or widespread scaffold means rashi-reconstruction; a
    localized shifted-but-genuine English block means rashi-realignment; an
    isolated straggler may use rashi-repair only after the whole daf is
    freshly semantically verified."""
    sb = SCRIPTS / "baselines" / "rashi_scaffold_debt.json"
    if not sb.exists():
        return None
    entries = [e for e in json.loads(sb.read_text()).get("entries", [])
               if e["daf"] == daf]
    if not entries:
        return None
    rules = {}
    for e in entries:
        rules[e["rule"]] = rules.get(e["rule"], 0) + 1
    definite = any(r in rules for r in
                   ("scaffold-bracket-guess", "hebrew-passthrough", "line-number-scaffold"))
    widespread = total_lines and len(entries) / total_lines >= 0.30
    if definite or widespread or len(entries) > 5:
        rec = ("rashi-reconstruction (definite fabrication or widespread scaffold; "
               "a localized shifted-but-genuine block would instead be rashi-realignment)")
    else:
        rec = ("rashi-repair ONLY after fresh semantic verification of the whole daf; "
               "otherwise rashi-reconstruction")
    return {"lines": sorted(e["vilnaLine"] for e in entries),
            "rules": rules, "recommendation": rec}


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
            "lineLevelSafe": profile["lineLevelSafe"],
            "recommendedTaskType": profile["recommendedTaskType"],
        }
    return {
        "daf": daf,
        "rawRashiCount": len(raw),
        "rawRashi": [{"line": i + 1, "he": l} for i, l in enumerate(raw)],
        "localSegments": local_segments_for(daf),
        "sugyot": sugyot,
        "currentTranslations": [{
            "vilnaLine": e["vilnaLine"],
            "linkedGemaraLineIds": e.get("linkedGemaraLineIds", []),
            "en": e.get("en", ""),
        } for e in enrich.get("rashiTranslations", [])],
        "validatorBaseline": baseline_for(daf),
        "scaffoldDebt": scaffold_debt_for(daf, len(raw)),
        "driftProfile": drift,
        "rules": RULES,
        "postEditCommands": POST_EDIT_COMMANDS,
    }


def to_markdown(p):
    L = []
    L.append(f"# Rashi work packet: Yoma {p['daf']}")
    L.append(f"\nRaw Rashi lines: {p['rawRashiCount']} | current entries: {len(p['currentTranslations'])} "
             f"| local segment ids: {len(p['localSegments'])}")
    d = p.get("driftProfile")
    if d:
        L.append("\n## Semantic drift profile")
        L.append(f"- classification: {d['classification']}")
        L.append(f"- anchors: {d['anchorsFound']} found, {d['anchorsMissing']} missing; "
                 f"offsets: {' '.join(f'{o:+d}' for o in d['offsets']) or 'none'}"
                 f" (max |offset| {d['maxAbsOffset']})")
        L.append(f"- line-level-safe for line-level work: {'yes' if d['lineLevelSafe'] else 'NO'}")
        if not d["lineLevelSafe"]:
            L.append(f"- WARNING: stub repair and link edits are FORBIDDEN on this daf; "
                     f"required task type: {d['recommendedTaskType']} (Sonnet, independent review)")
    L.append("\n## Rules")
    for r in p["rules"]:
        L.append(f"- {r}")
    L.append("\n## Sugyot")
    for s in p["sugyot"]:
        L.append(f"- {s['id']} (vilna {s['startVilnaLine']}-{s['endVilnaLine']}): {s['title']}")
    L.append("\n## Legal local segment ids (Gemara AND Mishnah; the ONLY valid linkedGemaraLineIds targets)")
    L.append("Full segment text follows each id. Link every Rashi comment to the")
    L.append("segment(s) whose text it explains; never by vilna line number or")
    L.append("positional offset.")
    for g in p["localSegments"]:
        L.append(f"- {g['id']} [{g['kind']}] (vilna {g['vilnaLine']}): {g['he']}")
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
    sd = p.get("scaffoldDebt")
    if sd:
        L.append("\n## Scaffold-fabrication debt for this daf (MUST drain to zero)")
        L.append(f"- {len(sd['lines'])} baselined scaffold line(s): vilnaLine {sd['lines']}")
        L.append(f"- rules: {', '.join(f'{r} x{c}' for r, c in sorted(sd['rules'].items()))}")
        L.append(f"- recommended task type: {sd['recommendation']}")
        L.append("- after repair: zero scaffold hits may remain on this daf; retire the "
                 "baseline entries with `python3 scripts/audit_rashi_scaffold.py --update-baseline`; "
                 "never preserve scaffold wording even where its meaning was partly correct")
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
