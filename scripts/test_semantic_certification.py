#!/usr/bin/env python3
"""Regression tests for the semantic certification safety properties."""
from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path

from semantic_certification import (
    certificate_status,
    fingerprints,
    load_corpus,
    load_registry,
    make_certified_record,
)

MODULE = "yoma"


def review(review_id: str, verdict: str) -> dict:
    return {
        "reviewId": review_id,
        "sourceFirst": True,
        "verdict": verdict,
        "evidence": "test evidence",
    }


def main() -> None:
    corpus = load_corpus(MODULE)
    assert len(corpus) == 492, f"expected 492 Yoma sugyot, got {len(corpus)}"

    sid = "yoma-042a-s01"
    daf, doc, sugya = corpus[sid]

    # 1. Legacy review metadata is never certification.
    fake = copy.deepcopy(sugya)
    fake["review"] = "reviewed"
    state, _ = certificate_status(MODULE, daf, doc, fake, None)
    assert state == "UNCERTIFIED"

    # 2. A valid two-pass certificate is fresh for exactly the data it binds.
    rec = make_certified_record(
        MODULE,
        daf,
        doc,
        sugya,
        review("pass-A", "VERIFIED"),
        review("pass-B", "CONFIRMED"),
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

    # 7. Registry starts in bootstrap mode and never silently calls unlisted
    # corpus records certified.
    registry = load_registry(MODULE)
    assert registry.get("strictMode") is False
    assert registry.get("records", {}).get(sid, {}).get("state") != "CERTIFIED"

    print("OK: semantic certification safety properties hold")


if __name__ == "__main__":
    main()
