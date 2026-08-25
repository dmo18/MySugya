#!/usr/bin/env python3
"""Regression tests for campaign_packet.py's safety properties: the packets
handed to isolated schema-2.0 campaign subagents must carry real source
segment ids (not an approximate reimplementation), no certification state
or prior review evidence, no untrusted semantic content from another daf,
and exhaustive daf-level field coverage.
"""
from __future__ import annotations

import json

from campaign_packet import (
    _daf_segment_map,
    _source_refs_module,
    build_candidate_packet,
    build_final_audit_packet,
)
from semantic_certification import load_corpus, load_registry

MODULE = "yoma"


def test_1_duplicate_start_vilna_line_mints_suffixed_ids():
    # Yoma 24a: yoma-024a-s01 carries two lines both at vilnaLine 1 (a real
    # duplicate-start case, not a synthetic one).
    packet = build_candidate_packet(MODULE, "24a")
    s01 = next(s for s in packet["sugyot"] if s["id"] == "yoma-024a-s01")
    minted = [e["mintedLineId"] for e in s01["sourceSegmentMap"]]
    assert "yoma-024a-l01a" in minted, minted
    assert "yoma-024a-l01b" in minted, minted
    assert "yoma-024a-l01" not in minted, "unsuffixed id must not appear when the Vilna line is shared"
    # No duplicate values anywhere in the packet's segment map for this daf.
    all_ids = [e["mintedLineId"] for s in packet["sugyot"] for e in s["sourceSegmentMap"]]
    assert len(all_ids) == len(set(all_ids)), f"duplicate minted ids: {all_ids}"


def test_2_segment_map_matches_canonical_validator_derivation():
    # The packet's ids must be byte-identical to validate_source_refs.py's
    # own derive_line_ids() output for the same daf -- not a second,
    # possibly-drifting implementation.
    vsr = _source_refs_module(MODULE)
    corpus = load_corpus(MODULE)
    for daf in ("7a", "24a", "10a"):
        sugyot = []
        for sid, (d, _doc, sugya) in sorted(corpus.items()):
            if d != daf:
                continue
            tagged = dict(sugya)
            tagged["_daf"] = daf
            tagged["id"] = sid
            sugyot.append(tagged)
        sugyot.sort(key=lambda s: s.get("sugyaNumber", 0))
        expected = vsr.derive_line_ids(sugyot)
        actual = _daf_segment_map(MODULE, daf, corpus)
        assert actual == expected, (daf, actual, expected)


def test_3_frequency_computed_across_whole_daf_not_one_sugya():
    # A duplicate Vilna-line start shared across two DIFFERENT sugyot on the
    # same daf must still receive suffixes -- suffixing must never be
    # computed per-sugya in isolation. Construct this directly against
    # derive_line_ids with two synthetic single-line sugyot sharing
    # vilnaLine 1, mirroring how _daf_segment_map assembles its input.
    vsr = _source_refs_module(MODULE)
    sugyot = [
        {"_daf": "7a", "id": "fake-s01", "lines": [{"vilnaLine": 1, "sefariaRef": "Yoma.7a.1"}]},
        {"_daf": "7a", "id": "fake-s02", "lines": [{"vilnaLine": 1, "sefariaRef": "Yoma.7a.2"}]},
    ]
    ids = vsr.derive_line_ids(sugyot)
    minted = [e["id"] for e in ids]
    assert minted == ["yoma-007a-l01a", "yoma-007a-l01b"], minted
    # And confirm each of those two ids' sugyaId is correctly its own sugya
    # (frequency crossed the sugya boundary, but assignment didn't).
    assert ids[0]["sugyaId"] == "fake-s01"
    assert ids[1]["sugyaId"] == "fake-s02"


def test_4_candidate_packet_contains_no_certification_state():
    packet = build_candidate_packet(MODULE, "7a")
    blob = json.dumps(packet)
    for forbidden in ("CERTIFIED", "REVALIDATION_REQUIRED", "PENDING_FINAL_AUDIT",
                       "sourceFingerprint", "semanticFingerprint", "certifiedAtCommit"):
        assert forbidden not in blob, f"candidate packet leaked certification state: {forbidden!r}"


def test_5_candidate_packet_contains_no_review_evidence():
    packet = build_candidate_packet(MODULE, "7a")
    blob = json.dumps(packet)
    for forbidden in ("firstPass", "secondPass", "finalAudit", "reviewerContextId",
                       "auditorContextId", "reviewId"):
        assert forbidden not in blob, f"candidate packet leaked review evidence: {forbidden!r}"
    # Also confirm none of the registry's actual recorded review ids for
    # this exact sugya leaked in, not just the field names above.
    registry = load_registry(MODULE)
    record = registry.get("records", {}).get("yoma-007a-s01")
    if record:
        for pass_key in ("firstPass", "secondPass", "finalAudit"):
            block = record.get(pass_key)
            if isinstance(block, dict):
                rid = block.get("reviewId") or block.get("auditorContextId")
                if rid:
                    assert rid not in blob, f"leaked real review id {rid!r} into candidate packet"


def test_6_preceding_daf_context_is_raw_hebrew_only():
    packet = build_candidate_packet(MODULE, "7a")
    preceding = packet.get("precedingDafContext")
    assert preceding is not None, "7a has a preceding daf (6b); context must be present"
    assert set(preceding.keys()) == {"daf", "precedingDafRawTail"}, preceding.keys()
    assert preceding["daf"] == "6b"
    tail = preceding["precedingDafRawTail"]
    assert 1 <= len(tail) <= 5, tail
    for entry in tail:
        assert set(entry.keys()) == {"l", "he"}, entry
        assert isinstance(entry["he"], str) and entry["he"], entry
    # No semantic-enrichment field names anywhere in the whole packet's
    # preceding-context blob.
    blob = json.dumps(preceding)
    for forbidden in ("title", "oneLine", "summary", "argumentFlow", "display", "learning"):
        assert forbidden not in blob, f"precedingDafContext leaked authored enrichment: {forbidden!r}"


def test_7_unknown_daf_level_field_automatically_appears():
    # Simulate a new daf-level authored field the way semantic_payload()
    # would see it (exclusion-list based, not an inclusion allowlist):
    # build_candidate_packet must reflect a real corpus doc, so verify the
    # exclusion logic itself rather than mutating a live file. Any doc key
    # not in DAF_LEVEL_NON_SEMANTIC_KEYS must appear in packet["dafLevel"].
    from semantic_certification import DAF_LEVEL_NON_SEMANTIC_KEYS
    from campaign_packet import _daf_level_authored

    fake_doc = {
        "daf": "7a",
        "canonicalRef": "Yoma 7a",
        "summary": "s",
        "glossary": [],
        "sugyot": [],
        "review": {},
        "rashiLines": [],
        "rashiTranslations": [],
        "aBrandNewDafLevelField": "should appear automatically",
    }
    out = _daf_level_authored(fake_doc)
    assert out == {"summary": "s", "glossary": [], "aBrandNewDafLevelField": "should appear automatically"}, out
    for excluded in DAF_LEVEL_NON_SEMANTIC_KEYS:
        assert excluded not in out, excluded


def test_8_final_audit_packet_contains_no_review_evidence():
    packet = build_final_audit_packet(MODULE, "7a", "yoma-007a-s01")
    blob = json.dumps(packet)
    for forbidden in ("firstPass", "secondPass", "finalAudit", "reviewerContextId",
                       "auditorContextId", "CERTIFIED", "sourceFingerprint"):
        assert forbidden not in blob, f"final-audit packet leaked review/certification state: {forbidden!r}"


def test_9_final_audit_packet_has_same_source_context_as_candidate():
    # The Final Whole-Record Auditor must not receive strictly less source
    # context than a candidate-packet reviewer: it must be able to
    # independently verify a candidate's opening contextual claims
    # (precedingDafContext) and inspect the auxiliary Rashi evidence the
    # finished candidate rests on (relevantRashi), not just trust that an
    # earlier review pass already checked them.
    packet = build_final_audit_packet(MODULE, "7a", "yoma-007a-s01")

    preceding = packet.get("precedingDafContext")
    assert preceding is not None, "7a has a preceding daf (6b); final-audit packet must carry it"
    assert set(preceding.keys()) == {"daf", "precedingDafRawTail"}, preceding.keys()
    assert preceding["daf"] == "6b", preceding["daf"]
    tail = preceding["precedingDafRawTail"]
    assert 1 <= len(tail) <= 5, tail
    for entry in tail:
        assert set(entry.keys()) == {"l", "he"}, entry
        assert isinstance(entry["he"], str) and entry["he"], entry
    preceding_blob = json.dumps(preceding)
    for forbidden in ("title", "oneLine", "summary", "argumentFlow", "display", "learning"):
        assert forbidden not in preceding_blob, f"final-audit precedingDafContext leaked authored enrichment: {forbidden!r}"

    rashi = packet.get("relevantRashi")
    assert rashi, "final-audit packet must carry relevantRashi (candidate packets do)"
    assert isinstance(rashi, list) and len(rashi) > 0
    for entry in rashi:
        assert set(entry.keys()) == {"linkedGemaraLineIds", "en"}, entry.keys()

    # Still no prior review evidence or certification state of any kind,
    # despite the added source context.
    blob = json.dumps(packet)
    for forbidden in ("firstPass", "secondPass", "finalAudit", "reviewId",
                       "reviewerContextId", "auditorContextId",
                       "CERTIFIED", "REVALIDATION_REQUIRED", "PENDING_FINAL_AUDIT",
                       "sourceFingerprint", "semanticFingerprint", "certifiedAtCommit"):
        assert forbidden not in blob, f"final-audit packet leaked review/certification state: {forbidden!r}"


def main() -> None:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
        print(f"OK: {t.__name__}")
    print(f"OK: {len(tests)} campaign_packet regression tests passed")


if __name__ == "__main__":
    main()
