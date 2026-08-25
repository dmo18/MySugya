#!/usr/bin/env python3
"""Compact per-daf packet builder for the schema-2.0 semantic campaign's
isolated subagents (Source Auditor / Independent Reviewer / Final
Whole-Record Auditor).

Deliberately minimal: raw Hebrew, current authored candidate, relevant
Rashi, and (for the final audit) the machine-generated field inventory and
physical-boundary facts. No prior review evidence, no certification state,
no campaign history, no CLAUDE.md, no full repo. Token efficiency comes
from cutting irrelevant context, never from cutting source coverage.

sourceRefs.lineId minting is delegated to the module's own
validate_source_refs.derive_line_ids() (imported dynamically from
modules/<module>/scripts/) rather than reimplemented here -- the id space
is coarser than raw Vilna line numbers (one id per Sefaria segment start,
with a/b/c suffixes when more than one segment starts on the same Vilna
line within a daf) and a second, approximate implementation would drift
from the canonical one build_learning_data.py and validate_source_refs.py
already share.

The precedingDafContext carries only raw Hebrew, deliberately: the
preceding daf's own authored enrichment is itself unreviewed campaign
content (frequently REVALIDATION_REQUIRED) and must never anchor a fresh
reviewer toward a prior mistake -- only the physical source text a
reviewer would need to resolve a sentence/dispute continuing across the
daf boundary belongs in the packet.
"""
from __future__ import annotations

import argparse
import functools
import json
import sys
from typing import Any, Dict, List

from semantic_certification import (
    DAF_LEVEL_NON_SEMANTIC_KEYS,
    NON_SEMANTIC_KEYS,
    REPO,
    daf_sort_key,
    enumerate_semantic_paths,
    load_corpus,
    raw_dir,
)

PRECEDING_TAIL_LINES = 5


@functools.lru_cache(maxsize=None)
def _source_refs_module(module: str):
    """Dynamically import modules/<module>/scripts/validate_source_refs.py,
    the canonical owner of the sourceRefs.lineId minting algorithm. Cached
    per module so repeated calls (e.g. across a test suite) don't keep
    mutating sys.path."""
    scripts_dir = REPO / "modules" / module / "scripts"
    path_str = str(scripts_dir)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)
    import validate_source_refs  # noqa: E402

    return validate_source_refs


def _daf_segment_map(module: str, daf: str, corpus: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The canonical, whole-daf-derived {id, vilnaLine, sefariaRef,
    sugyaId} list for every segment on `daf`, via the same
    derive_line_ids() build_learning_data.py and validate_source_refs.py
    use. Frequency for the a/b/c suffix assignment is computed across
    every sugya on the daf, never a single sugya in isolation -- two
    sugyot on the same daf can each start a segment on the same Vilna
    line, and the suffixing must see both to agree with the corpus."""
    vsr = _source_refs_module(module)
    rows = sorted(
        ((sid, sugya) for sid, (d, _doc, sugya) in corpus.items() if d == daf),
        key=lambda x: x[1].get("sugyaNumber", 0),
    )
    sugyot_for_derivation = []
    for sid, sugya in rows:
        tagged = dict(sugya)
        tagged["_daf"] = daf
        tagged["id"] = sid
        sugyot_for_derivation.append(tagged)
    return vsr.derive_line_ids(sugyot_for_derivation)


def _source_segment_map_for_sugya(daf_segment_map: List[Dict[str, Any]], sugya_id: str) -> List[Dict[str, Any]]:
    return [
        {"mintedLineId": e["id"], "vilnaLine": e["vilnaLine"], "sefariaRef": e["sefariaRef"]}
        for e in daf_segment_map
        if e["sugyaId"] == sugya_id
    ]


SOURCE_SEGMENT_MAP_NOTE = (
    "sourceSegmentMap lists the only real sourceRefs.lineId values for this sugya (mintedLineId), "
    "each paired with the Vilna line it starts at and its Sefaria segment ref. A lineId identifies a "
    "Sefaria segment, not a single Vilna line -- a segment can span multiple Vilna lines (e.g. a "
    "segment starting at vilnaLine 6 can legitimately be the source for content at vilnaLine 7 if no "
    "new segment starts before line 8). A sourceRefs entry's lineId must be one of this list's "
    "mintedLineId values; its own vilnaLine field is separate metadata checked by containment within "
    "the segment's Vilna range, never required to equal the lineId's own number. When more than one "
    "segment starts on the same Vilna line, ids receive letter suffixes (l01a, l01b, ...) in source "
    "order -- never assume an unsuffixed numeric match is the only valid id for that line."
)


def _rashi_for_daf(doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = []
    for entry in doc.get("rashiTranslations") or []:
        if entry.get("en"):
            out.append({"linkedGemaraLineIds": entry.get("linkedGemaraLineIds") or [], "en": entry["en"]})
    return out


def _authored(sugya: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in sugya.items() if k not in NON_SEMANTIC_KEYS}


def _daf_level_authored(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Every authored daf-level semantic field, exhaustively -- the same
    exclusion-list logic semantic_payload() uses, so a new daf-level field
    automatically appears here without this file changing. Never a
    hand-picked subset (summary/glossary only)."""
    return {k: v for k, v in doc.items() if k not in DAF_LEVEL_NON_SEMANTIC_KEYS}


def _preceding_daf_raw_tail(module: str, daf: str, corpus: Dict[str, Any]) -> Dict[str, Any] | None:
    """The final few RAW HEBREW lines of the immediately preceding daf --
    source text only, never any authored enrichment (title/oneLine/summary/
    argumentFlow/etc). Many sugyot open mid-discussion (a position or
    dispute stated moments earlier) and a fresh isolated reviewer needs
    that physical continuation to correctly read a first-person claim like
    "from where do I say this" at the top of a new daf. But the preceding
    daf's own enrichment is itself unreviewed campaign content -- often
    REVALIDATION_REQUIRED -- and must never be handed to a fresh reviewer
    as if it were established truth; only the primary source text is
    trustworthy enough to anchor another reviewer's independent reading."""
    dafs = sorted({d for d, _doc, _sugya in corpus.values()}, key=daf_sort_key)
    if daf not in dafs or dafs.index(daf) == 0:
        return None
    prev_daf = dafs[dafs.index(daf) - 1]
    raw_path = raw_dir(module) / f"{prev_daf}.json"
    if not raw_path.exists():
        return None
    raw_lines = json.loads(raw_path.read_text(encoding="utf-8")).get("lines") or []
    if not raw_lines:
        return None
    tail_start = max(0, len(raw_lines) - PRECEDING_TAIL_LINES)
    return {
        "daf": prev_daf,
        "precedingDafRawTail": [
            {"l": i + 1, "he": t} for i, t in enumerate(raw_lines) if i >= tail_start
        ],
    }


def build_candidate_packet(module: str, daf: str) -> Dict[str, Any]:
    """Source Auditor / Independent Reviewer packet: raw source + current
    candidate only. No fingerprints, no certification state, no prior
    findings, no authored enrichment from any other daf."""
    corpus = load_corpus(module)
    rows = sorted(
        ((sid, doc, sugya) for sid, (d, doc, sugya) in corpus.items() if d == daf),
        key=lambda x: x[2].get("sugyaNumber", 0),
    )
    if not rows:
        raise SystemExit(f"no sugyot found for {module}/{daf}")
    doc = rows[0][1]
    raw_lines = json.loads((raw_dir(module) / f"{daf}.json").read_text(encoding="utf-8")).get("lines") or []
    daf_segment_map = _daf_segment_map(module, daf, corpus)
    packet: Dict[str, Any] = {
        "daf": daf,
        "rawHebrewLines": [{"l": i + 1, "he": t} for i, t in enumerate(raw_lines)],
        "dafLevel": _daf_level_authored(doc),
        "sugyot": [
            {
                "id": sid,
                "sugyaNumber": sugya.get("sugyaNumber"),
                "lineRange": sugya.get("lineRange"),
                "authored": _authored(sugya),
                "sourceSegmentMap": _source_segment_map_for_sugya(daf_segment_map, sid),
            }
            for sid, _, sugya in rows
        ],
        "relevantRashi": _rashi_for_daf(doc),
        "sourceSegmentMapNote": SOURCE_SEGMENT_MAP_NOTE,
    }
    preceding = _preceding_daf_raw_tail(module, daf, corpus)
    if preceding is not None:
        packet["precedingDafContext"] = preceding
    return packet


def build_final_audit_packet(module: str, daf: str, sugya_id: str) -> Dict[str, Any]:
    """Final Whole-Record Auditor packet: raw source + exact final candidate
    + machine-generated field inventory (paths + classification) the agent
    must produce a verdict for, plus the fixed sweep category lists.

    Carries the same source context a candidate-packet reviewer sees
    (precedingDafContext, relevantRashi) -- the final auditor must be able
    to independently verify a candidate's opening contextual claims and
    inspect the auxiliary Rashi evidence the finished candidate rests on,
    not trust that an earlier review pass already checked them. Never
    prior semantic-review reasoning, evidence, or certification state."""
    from semantic_certification import STALE_SWEEP_CATEGORIES, DAF_END_STATES

    corpus = load_corpus(module)
    if sugya_id not in corpus:
        raise SystemExit(f"unknown sugya {sugya_id!r}")
    d, doc, sugya = corpus[sugya_id]
    if d != daf:
        raise SystemExit(f"{sugya_id} is on {d}, not {daf}")
    raw_lines = json.loads((raw_dir(module) / f"{daf}.json").read_text(encoding="utf-8")).get("lines") or []
    paths = enumerate_semantic_paths(module, doc, sugya)
    daf_segment_map = _daf_segment_map(module, daf, corpus)
    packet: Dict[str, Any] = {
        "daf": daf,
        "sugyaId": sugya_id,
        "lineRange": sugya.get("lineRange"),
        "rawHebrewLines": [{"l": i + 1, "he": t} for i, t in enumerate(raw_lines)],
        "dafLevel": _daf_level_authored(doc),
        "authored": _authored(sugya),
        "sourceSegmentMap": _source_segment_map_for_sugya(daf_segment_map, sugya_id),
        "sourceSegmentMapNote": SOURCE_SEGMENT_MAP_NOTE,
        "relevantRashi": _rashi_for_daf(doc),
        "fieldInventoryRequired": [{"path": p, "class": c} for p, c in paths],
        "dafEndStates": sorted(DAF_END_STATES),
        "staleSweepCategories": list(STALE_SWEEP_CATEGORIES),
    }
    preceding = _preceding_daf_raw_tail(module, daf, corpus)
    if preceding is not None:
        packet["precedingDafContext"] = preceding
    return packet


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
