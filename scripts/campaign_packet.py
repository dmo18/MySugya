#!/usr/bin/env python3
"""Compact per-daf packet builder for the schema-2.0 semantic campaign's
isolated subagents (Source Auditor / Independent Reviewer / Final
Whole-Record Auditor).

Deliberately minimal: raw Hebrew, current authored candidate, relevant
Rashi, and (for the final audit) the machine-generated field inventory and
physical-boundary facts. No prior review evidence, no certification state,
no campaign history, no CLAUDE.md, no full repo. Token efficiency comes
from cutting irrelevant context, never from cutting source coverage.
"""
from __future__ import annotations

import argparse
import json
import re
from typing import Any, Dict, List

from semantic_certification import (
    NON_SEMANTIC_KEYS,
    daf_sort_key,
    enumerate_semantic_paths,
    load_corpus,
    raw_dir,
)


def _rashi_for_daf(doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = []
    for entry in doc.get("rashiTranslations") or []:
        if entry.get("en"):
            out.append({"linkedGemaraLineIds": entry.get("linkedGemaraLineIds") or [], "en": entry["en"]})
    return out


def _authored(sugya: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in sugya.items() if k not in NON_SEMANTIC_KEYS}


def _minted_line_ids(module: str, daf: str, sugya: Dict[str, Any]) -> List[str]:
    """The real, minted sourceRefs.lineId values for this sugya, derived from
    its own `lines` map (one per Sefaria segment start, NOT one per raw Vilna
    line -- a segment can span several raw lines).

    A reviewer given only vilnaLine numbers naturally but wrongly infers
    lineId should equal "l" + vilnaLine for every line; the actual contract
    (docs/reports/sourcerefs-contract-decision.md) is that lineId identifies
    the segment, validated against vilnaLine by containment, never equality.
    Handing over the exact minted set closes that recurring false-positive
    class instead of relying on prose alone to prevent it."""
    num, letter = daf[:-1], daf[-1]
    out = []
    for entry in sugya.get("lines") or []:
        vilna = entry.get("vilnaLine")
        if isinstance(vilna, int):
            out.append(f"{module}-{int(num):03d}{letter}-l{vilna:02d}")
    return out


def _preceding_context(module: str, daf: str, corpus: Dict[str, Any]) -> Dict[str, Any] | None:
    """Compact anchor from the last sugya of the immediately preceding daf.

    Many sugyot open mid-discussion (a position just stated, a dispute
    already framed) and a fresh isolated reviewer given only the current
    daf's raw text can misattribute a first-person claim like "from where
    do I say this" without knowing what was just established. This is
    deliberately small -- id, title, and one-line summary only, never the
    preceding daf's full argumentFlow, raw Hebrew, or Rashi."""
    dafs = sorted({d for d, _doc, _sugya in corpus.values()}, key=daf_sort_key)
    if daf not in dafs or dafs.index(daf) == 0:
        return None
    prev_daf = dafs[dafs.index(daf) - 1]
    rows = sorted(
        ((sid, doc, sugya) for sid, (d, doc, sugya) in corpus.items() if d == prev_daf),
        key=lambda x: x[2].get("sugyaNumber", 0),
    )
    if not rows:
        return None
    sid, _doc, sugya = rows[-1]
    display = sugya.get("display") or {}
    return {
        "daf": prev_daf,
        "sugyaId": sid,
        "title": display.get("title", ""),
        "oneLine": display.get("oneLine", ""),
    }


def build_candidate_packet(module: str, daf: str) -> Dict[str, Any]:
    """Source Auditor / Independent Reviewer packet: raw source + current
    candidate only. No fingerprints, no certification state, no prior
    findings."""
    corpus = load_corpus(module)
    rows = sorted(
        ((sid, doc, sugya) for sid, (d, doc, sugya) in corpus.items() if d == daf),
        key=lambda x: x[2].get("sugyaNumber", 0),
    )
    if not rows:
        raise SystemExit(f"no sugyot found for {module}/{daf}")
    doc = rows[0][1]
    raw_lines = json.loads((raw_dir(module) / f"{daf}.json").read_text(encoding="utf-8")).get("lines") or []
    packet: Dict[str, Any] = {
        "daf": daf,
        "rawHebrewLines": [{"l": i + 1, "he": t} for i, t in enumerate(raw_lines)],
        "dafSummary": doc.get("summary", ""),
        "dafGlossary": doc.get("glossary") or [],
        "sugyot": [
            {
                "id": sid,
                "sugyaNumber": sugya.get("sugyaNumber"),
                "lineRange": sugya.get("lineRange"),
                "authored": _authored(sugya),
                "mintedLineIds": _minted_line_ids(module, daf, sugya),
            }
            for sid, _, sugya in rows
        ],
        "relevantRashi": _rashi_for_daf(doc),
        "mintedLineIdsNote": (
            "mintedLineIds lists the only real sourceRefs.lineId values for each sugya: one per "
            "Sefaria segment start, not one per raw Vilna line -- a segment can span multiple Vilna "
            "lines (e.g. lineId l06 can legitimately be the source for content at vilnaLine 7 if the "
            "segment starting at line 6 extends through line 7). A sourceRefs entry's lineId must be "
            "one of mintedLineIds; its vilnaLine is separate metadata checked by containment, never "
            "required to equal the lineId's own number."
        ),
    }
    preceding = _preceding_context(module, daf, corpus)
    if preceding is not None:
        packet["precedingDafContext"] = preceding
    return packet


def build_final_audit_packet(module: str, daf: str, sugya_id: str) -> Dict[str, Any]:
    """Final Whole-Record Auditor packet: raw source + exact final candidate
    + machine-generated field inventory (paths + classification) the agent
    must produce a verdict for, plus the fixed sweep category lists."""
    from semantic_certification import STALE_SWEEP_CATEGORIES, DAF_END_STATES

    corpus = load_corpus(module)
    if sugya_id not in corpus:
        raise SystemExit(f"unknown sugya {sugya_id!r}")
    d, doc, sugya = corpus[sugya_id]
    if d != daf:
        raise SystemExit(f"{sugya_id} is on {d}, not {daf}")
    raw_lines = json.loads((raw_dir(module) / f"{daf}.json").read_text(encoding="utf-8")).get("lines") or []
    paths = enumerate_semantic_paths(module, doc, sugya)
    return {
        "daf": daf,
        "sugyaId": sugya_id,
        "lineRange": sugya.get("lineRange"),
        "rawHebrewLines": [{"l": i + 1, "he": t} for i, t in enumerate(raw_lines)],
        "dafSummary": doc.get("summary", ""),
        "dafGlossary": doc.get("glossary") or [],
        "authored": _authored(sugya),
        "mintedLineIds": _minted_line_ids(module, daf, sugya),
        "mintedLineIdsNote": (
            "mintedLineIds lists the only real sourceRefs.lineId values for this sugya: one per "
            "Sefaria segment start, not one per raw Vilna line -- a segment can span multiple Vilna "
            "lines (e.g. lineId l06 can legitimately be the source for content at vilnaLine 7 if the "
            "segment starting at line 6 extends through line 7). A sourceRefs entry's lineId must be "
            "one of mintedLineIds; its vilnaLine is separate metadata checked by containment, never "
            "required to equal the lineId's own number."
        ),
        "fieldInventoryRequired": [{"path": p, "class": c} for p, c in paths],
        "dafEndStates": sorted(DAF_END_STATES),
        "staleSweepCategories": list(STALE_SWEEP_CATEGORIES),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--module", default="yoma")
    ap.add_argument("--daf", required=True)
    ap.add_argument("--mode", choices=["candidate", "final-audit"], default="candidate")
    ap.add_argument("--sugya", help="required for --mode final-audit")
    args = ap.parse_args()
    if args.mode == "candidate":
        print(json.dumps(build_candidate_packet(args.module, args.daf), ensure_ascii=False, separators=(",", ":")))
    else:
        if not args.sugya:
            raise SystemExit("--sugya required for --mode final-audit")
        print(json.dumps(build_final_audit_packet(args.module, args.daf, args.sugya), ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
