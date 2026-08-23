#!/usr/bin/env python3
"""Regression tests for the semantic certification safety properties."""
from __future__ import annotations

import copy

from semantic_certification import (
    certificate_status,
    fingerprints,
    load_corpus,
    load_registry,
    make_certified_record,
)

MODULE = "yoma"


def review(review_id: str, verdict: str, source_fp: str, semantic_fp: str) -> dict:
    return {
        "reviewId": review_id,
        "sourceFirst": True,
        "verdict": verdict,
        "reviewedSourceFingerprint": source_fp,
        "reviewedSemanticFingerprint": semantic_fp,
        "evidence": "test evidence",
    }


def main() -> None:
    corpus = load_corpus(MODULE)
    assert len(corpus) == 492, f"expected 492 Yoma sugyot, got {len(corpus)}"

    sid = "yoma-042a-s01"
    daf, doc, sugya = corpus[sid]
    source_fp, semantic_fp = fingerprints(MODULE, daf, doc, sugya)

    # 1. Legacy review metadata is never certification.
    fake = copy.deepcopy(sugya)
    fake["review"] = "reviewed"
    state, _ = certificate_status(MODULE, daf, doc, fake, None)
    assert state == "UNCERTIFIED"

    # 2. A clean two-pass certificate is fresh only when both reviewers saw
    # exactly the candidate being certified.
    rec = make_certified_record(
        MODULE,
        daf,
        doc,
        sugya,
        review("pass-A", "VERIFIED", source_fp, semantic_fp),
        review("pass-B", "CONFIRMED", source_fp, semantic_fp),
        "deadbeef",
    )
    state, problems = certificate_status(MODULE, daf, doc, sugya, rec)
    assert state == "CERTIFIED", problems

    # 3. Same reviewer cannot certify both passes.
    bad = copy.deepcopy(rec)
    bad["secondPass"]["reviewId"] = bad["firstPass"]["reviewId"]
    state, problems = certificate_status(MODULE, daf, doc, sugya, bad)
    assert state == "STALE" and any("different reviewId" in p for p in problems)

    # 4. Semantic edit automatically invalidates the old certificate.
    changed_doc = copy.deepcopy(doc)
    changed_sugya = next(s for s in changed_doc["sugyot"] if s["id"] == sid)
    changed_sugya.setdefault("display", {})["title"] = changed_sugya.get("display", {}).get("title", "") + " changed"
    state, problems = certificate_status(MODULE, daf, changed_doc, changed_sugya, rec)
    assert state == "STALE" and "semanticFingerprint is stale" in problems

    # 5. Page summary is part of semantic fingerprint, so shared page claims
    # cannot change under still-green per-sugya certificates.
    changed_summary = copy.deepcopy(doc)
    changed_summary["summary"] = changed_summary.get("summary", "") + " changed"
    changed_sugya2 = next(s for s in changed_summary["sugyot"] if s["id"] == sid)
    state, problems = certificate_status(MODULE, daf, changed_summary, changed_sugya2, rec)
    assert state == "STALE" and "semanticFingerprint is stale" in problems

    # 6. Source mapping/range is bound by the source fingerprint.
    changed_source_map = copy.deepcopy(sugya)
    changed_source_map["sefariaRefs"] = list(changed_source_map.get("sefariaRefs") or []) + ["Yoma.TEST"]
    state, problems = certificate_status(MODULE, daf, doc, changed_source_map, rec)
    assert state == "STALE" and "sourceFingerprint is stale" in problems

    # 7. A first pass that explicitly found REPAIR_REQUIRED cannot be converted
    # to CERTIFIED by metadata alone. It needs both repairRef and a real candidate delta.
    known_bad = make_certified_record(
        MODULE,
        daf,
        doc,
        sugya,
        review("repair-finder", "REPAIR_REQUIRED", source_fp, semantic_fp),
        review("repair-checker", "CONFIRMED", source_fp, semantic_fp),
        "deadbeef",
    )
    state, problems = certificate_status(MODULE, daf, doc, sugya, known_bad)
    assert state == "STALE"
    assert any("repairRef" in p for p in problems)
    assert any("no source/semantic repair delta" in p for p in problems)

    # 8. Even with repairRef, an unchanged candidate cannot certify.
    unchanged_with_ref = copy.deepcopy(known_bad)
    unchanged_with_ref["repairRef"] = "feedface"
    state, problems = certificate_status(MODULE, daf, doc, sugya, unchanged_with_ref)
    assert state == "STALE" and any("no source/semantic repair delta" in p for p in problems)

    # 9. A genuine repaired candidate can certify when the first pass is bound
    # to the old candidate and the second pass is bound to the repaired candidate.
    repaired_doc = copy.deepcopy(doc)
    repaired_sugya = next(s for s in repaired_doc["sugyot"] if s["id"] == sid)
    repaired_sugya.setdefault("display", {})["title"] = repaired_sugya.get("display", {}).get("title", "") + " repaired"
    repaired_source_fp, repaired_semantic_fp = fingerprints(MODULE, daf, repaired_doc, repaired_sugya)
    repaired_rec = make_certified_record(
        MODULE,
        daf,
        repaired_doc,
        repaired_sugya,
        review("repair-finder", "REPAIR_REQUIRED", source_fp, semantic_fp),
        review("repair-checker", "CONFIRMED", repaired_source_fp, repaired_semantic_fp),
        "deadbeef",
        repair_ref="feedface",
    )
    state, problems = certificate_status(MODULE, daf, repaired_doc, repaired_sugya, repaired_rec)
    assert state == "CERTIFIED", problems

    # 10. Second-pass fingerprints are also mandatory and must match live candidate.
    stale_second = copy.deepcopy(rec)
    stale_second["secondPass"]["reviewedSemanticFingerprint"] = "0" * 64
    state, problems = certificate_status(MODULE, daf, doc, sugya, stale_second)
    assert state == "STALE" and any("secondPass semantic fingerprint" in p for p in problems)

    # 11. Registry starts in bootstrap mode and never silently calls unlisted
    # corpus records certified.
    registry = load_registry(MODULE)
    assert registry.get("strictMode") is False
    assert registry.get("records", {}).get(sid, {}).get("state") != "CERTIFIED"

    print("OK: semantic certification safety properties hold")


if __name__ == "__main__":
    main()
