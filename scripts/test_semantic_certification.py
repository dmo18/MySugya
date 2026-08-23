#!/usr/bin/env python3
"""Regression tests for the semantic certification safety properties."""
from __future__ import annotations

import copy
import json

from semantic_certification import (
    STALE_SWEEP_CATEGORIES,
    certificate_status,
    enumerate_semantic_paths,
    fingerprints,
    load_corpus,
    load_registry,
    make_certified_record,
    raw_dir,
)

MODULE = "yoma"


def review(review_id: str, reviewer_context_id: str, verdict: str, source_fp: str, semantic_fp: str) -> dict:
    return {
        "reviewId": review_id,
        "reviewerContextId": reviewer_context_id,
        "sourceFirst": True,
        "verdict": verdict,
        "reviewedSourceFingerprint": source_fp,
        "reviewedSemanticFingerprint": semantic_fp,
        "evidence": "test evidence",
    }


def realistic_final_audit(module: str, daf: str, doc: dict, sugya: dict, review_id: str, auditor_context_id: str) -> dict:
    """A mechanically-valid finalAudit for plumbing tests. Every SEMANTIC-class
    path is SUPPORTED with real, in-range supporting lines (schema 2.0 no
    longer permits NONFACTUAL for authored prose); STRUCTURAL-class paths
    (identifiers/coordinates/slugs/resolvable ids) use NONFACTUAL; METADATA-
    class paths (argumentFlow step type, takeaway type, difficulty, etc.)
    use REVIEWED with a justifying note. Content-QUALITY tests (is the claim
    actually true) live in the semantic campaign itself, not here -- this
    only proves the plumbing accepts a mechanically sound, fully-covered,
    correctly-classified audit.
    """
    source_fp, semantic_fp = fingerprints(module, daf, doc, sugya)
    raw = json.loads((raw_dir(module) / f"{daf}.json").read_text(encoding="utf-8"))
    raw_lines = raw.get("lines") or []
    lr = sugya["lineRange"]

    entries = []
    for path, cls in enumerate_semantic_paths(module, doc, sugya):
        if cls == "STRUCTURAL":
            entries.append({"path": path, "verdict": "NONFACTUAL", "boundarySafe": True, "crossReference": False})
            continue
        if cls == "METADATA":
            entries.append({
                "path": path, "verdict": "REVIEWED", "boundarySafe": True, "crossReference": False,
                "note": "test: classification independently re-derived from source and confirmed consistent",
            })
            continue
        if path.startswith("dafLevel."):
            lines = [{"daf": daf, "startVilnaLine": 1, "endVilnaLine": len(raw_lines)}]
        else:
            lines = [{"daf": daf, "startVilnaLine": lr["startVilnaLine"], "endVilnaLine": lr["endVilnaLine"]}]
        entries.append({
            "path": path, "verdict": "SUPPORTED", "boundarySafe": True,
            "crossReference": False, "supportingLines": lines,
        })

    return {
        "reviewId": review_id,
        "auditorContextId": auditor_context_id,
        "auditedSourceFingerprint": source_fp,
        "auditedSemanticFingerprint": semantic_fp,
        "dafBoundary": {
            "rawLineCount": len(raw_lines),
            "finalRawLine": raw_lines[-1] if raw_lines else "",
            "dafEndState": "COMPLETE",
        },
        "fieldInventory": entries,
        "boundaryLeakageSweep": [
            {"path": path, "importsNextDafConclusion": False}
            for path, cls in enumerate_semantic_paths(module, doc, sugya) if cls in ("SEMANTIC", "METADATA")
        ],
        "staleContentSweep": {
            "entries": [{"category": c, "found": False} for c in STALE_SWEEP_CATEGORIES]
        },
    }


def main() -> None:
    corpus = load_corpus(MODULE)
    assert len(corpus) == 492, f"expected 492 Yoma sugyot, got {len(corpus)}"

    sid = "yoma-042a-s01"
    daf, doc, sugya = corpus[sid]
    source_fp, semantic_fp = fingerprints(MODULE, daf, doc, sugya)
    audit = realistic_final_audit(MODULE, daf, doc, sugya, "audit-C", "agent-C")

    # 1. Legacy review metadata is never certification.
    fake = copy.deepcopy(sugya)
    fake["review"] = "reviewed"
    state, _ = certificate_status(MODULE, daf, doc, fake, None)
    assert state == "UNCERTIFIED"

    # 2. A clean three-block certificate is fresh only when all three saw
    # exactly the candidate being certified.
    rec = make_certified_record(
        MODULE,
        daf,
        doc,
        sugya,
        review("pass-A", "agent-A", "VERIFIED", source_fp, semantic_fp),
        review("pass-B", "agent-B", "CONFIRMED", source_fp, semantic_fp),
        audit,
        "deadbeef",
    )
    state, problems = certificate_status(MODULE, daf, doc, sugya, rec)
    assert state == "CERTIFIED", problems

    # 3. Same reviewer cannot certify both passes.
    bad = copy.deepcopy(rec)
    bad["secondPass"]["reviewId"] = bad["firstPass"]["reviewId"]
    state, problems = certificate_status(MODULE, daf, doc, sugya, bad)
    assert state == "STALE" and any("different reviewId" in p for p in problems)

    # 3b. Same reviewer CONTEXT cannot certify both passes, even with
    # different reviewId strings -- a different label inside the same
    # reasoning context is not real independence.
    bad_context = copy.deepcopy(rec)
    bad_context["secondPass"]["reviewerContextId"] = bad_context["firstPass"]["reviewerContextId"]
    state, problems = certificate_status(MODULE, daf, doc, sugya, bad_context)
    assert state == "STALE" and any("reviewer contexts" in p for p in problems)

    # 3c. The final auditor context cannot equal the first-pass reviewer context.
    bad_audit_context = copy.deepcopy(rec)
    bad_audit_context["finalAudit"]["auditorContextId"] = bad_audit_context["firstPass"]["reviewerContextId"]
    state, problems = certificate_status(MODULE, daf, doc, sugya, bad_audit_context)
    assert state == "STALE" and any("auditorContextId must differ" in p for p in problems)

    # 3d. The final auditor context also cannot equal the second-pass
    # reviewer context.
    bad_audit_context2 = copy.deepcopy(rec)
    bad_audit_context2["finalAudit"]["auditorContextId"] = bad_audit_context2["secondPass"]["reviewerContextId"]
    state, problems = certificate_status(MODULE, daf, doc, sugya, bad_audit_context2)
    assert state == "STALE" and any("auditorContextId must differ from secondPass" in p for p in problems)

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

    # 5b. Daf-level glossary is also part of the semantic fingerprint (item
    # 3): a stale/changed glossary entry invalidates every sugya certificate
    # on the daf, exactly like the summary.
    changed_glossary = copy.deepcopy(doc)
    changed_glossary["glossary"] = list(changed_glossary.get("glossary") or []) + [
        {"he": "test", "translit": "test", "en": "a glossary definition that was never certified"}
    ]
    changed_sugya3 = next(s for s in changed_glossary["sugyot"] if s["id"] == sid)
    state, problems = certificate_status(MODULE, daf, changed_glossary, changed_sugya3, rec)
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
        review("repair-finder", "agent-A", "REPAIR_REQUIRED", source_fp, semantic_fp),
        review("repair-checker", "agent-B", "CONFIRMED", source_fp, semantic_fp),
        audit,
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
    # to the old candidate and the second pass/final audit are bound to the
    # repaired candidate.
    repaired_doc = copy.deepcopy(doc)
    repaired_sugya = next(s for s in repaired_doc["sugyot"] if s["id"] == sid)
    repaired_sugya.setdefault("display", {})["title"] = repaired_sugya.get("display", {}).get("title", "") + " repaired"
    repaired_source_fp, repaired_semantic_fp = fingerprints(MODULE, daf, repaired_doc, repaired_sugya)
    repaired_audit = realistic_final_audit(MODULE, daf, repaired_doc, repaired_sugya, "audit-C2", "agent-C2")
    repaired_rec = make_certified_record(
        MODULE,
        daf,
        repaired_doc,
        repaired_sugya,
        review("repair-finder", "agent-A", "REPAIR_REQUIRED", source_fp, semantic_fp),
        review("repair-checker", "agent-B", "CONFIRMED", repaired_source_fp, repaired_semantic_fp),
        repaired_audit,
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
    # corpus records certified. Checked over whichever sugyot are currently
    # absent from the registry (not a fixed sid), since the campaign
    # legitimately adds real CERTIFIED entries daf by daf and a hardcoded sid
    # would eventually fail on correct progress rather than a regression.
    registry = load_registry(MODULE)
    assert registry.get("strictMode") is False
    for other_sid, (other_daf, other_doc, other_sugya) in corpus.items():
        if other_sid in registry.get("records", {}):
            continue
        state, _ = certificate_status(MODULE, other_daf, other_doc, other_sugya, None)
        assert state == "UNCERTIFIED"

    # 12. A CERTIFIED record with no finalAudit at all (e.g. unmigrated
    # schema-1.0 data, or hand-tampering) never silently reads as CERTIFIED
    # under schema 2.0 -- it reads as REVALIDATION_REQUIRED specifically,
    # distinct from an ordinary STALE content change.
    no_audit = copy.deepcopy(rec)
    del no_audit["finalAudit"]
    state, problems = certificate_status(MODULE, daf, doc, sugya, no_audit)
    assert state == "REVALIDATION_REQUIRED", (state, problems)

    print("OK: semantic certification safety properties hold")


if __name__ == "__main__":
    main()
