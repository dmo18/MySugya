#!/usr/bin/env python3
"""Regression tests for the schema-2.0 mandatory final whole-record audit.

These reproduce, as generalized invariants (never hardcoded to a specific
daf), the exact failure class an independent audit demonstrated on Yoma
7a/7b: a schema-1.0 certificate could exist even though a daf ended
mid-thought and other fields still asserted the next daf's conclusion, or a
repair fixed one field while a stale duplicate of the original error
survived elsewhere in the same record. See docs/semantic-self-heal.md.
"""
from __future__ import annotations

import copy
import json

from semantic_certification import (
    CERT_SCHEMA_VERSION,
    STALE_SWEEP_CATEGORIES,
    certificate_status,
    enumerate_semantic_paths,
    fingerprints,
    load_corpus,
    make_certified_record,
    raw_dir,
)
from migrate_certification_schema_v2 import migrate
from validate_semantic_certification import allowed_schema_migration_downgrade

MODULE = "yoma"
SID = "yoma-042a-s01"


def load_target():
    corpus = load_corpus(MODULE)
    daf, doc, sugya = corpus[SID]
    return daf, doc, sugya


def base_review(review_id: str, ctx: str, verdict: str, source_fp: str, semantic_fp: str) -> dict:
    return {
        "reviewId": review_id,
        "reviewerContextId": ctx,
        "sourceFirst": True,
        "verdict": verdict,
        "reviewedSourceFingerprint": source_fp,
        "reviewedSemanticFingerprint": semantic_fp,
        "evidence": "test evidence",
    }


def clean_audit(module: str, daf: str, doc: dict, sugya: dict, review_id: str = "audit-C", ctx: str = "agent-C") -> dict:
    source_fp, semantic_fp = fingerprints(module, daf, doc, sugya)
    raw_lines = json.loads((raw_dir(module) / f"{daf}.json").read_text(encoding="utf-8")).get("lines") or []
    return {
        "reviewId": review_id,
        "auditorContextId": ctx,
        "auditedSourceFingerprint": source_fp,
        "auditedSemanticFingerprint": semantic_fp,
        "dafBoundary": {
            "rawLineCount": len(raw_lines),
            "finalRawLine": raw_lines[-1] if raw_lines else "",
            "dafEndState": "COMPLETE",
        },
        "fieldInventory": [
            {"path": p, "verdict": "NONFACTUAL", "boundarySafe": True, "crossReference": False}
            for p in enumerate_semantic_paths(sugya)
        ],
        "staleContentSweep": {
            "entries": [{"category": c, "found": False} for c in STALE_SWEEP_CATEGORIES]
        },
    }


def build_certified(module, daf, doc, sugya, audit=None) -> dict:
    source_fp, semantic_fp = fingerprints(module, daf, doc, sugya)
    audit = audit if audit is not None else clean_audit(module, daf, doc, sugya)
    return make_certified_record(
        module, daf, doc, sugya,
        base_review("pass-A", "agent-A", "VERIFIED", source_fp, semantic_fp),
        base_review("pass-B", "agent-B", "CONFIRMED", source_fp, semantic_fp),
        audit,
        "deadbeef",
    )


def test_1_open_ending_cannot_certify_with_false_closure_elsewhere():
    """A daf ending mid-thought cannot certify merely because one field is
    hedged while other fields (fieldInventory or openEndingFieldSweep) still
    assert the completed result."""
    daf, doc, sugya = load_target()
    audit = clean_audit(MODULE, daf, doc, sugya)
    audit["dafBoundary"]["dafEndState"] = "MID_ARGUMENT"
    # No openEndingFieldSweep at all: must fail outright.
    rec = build_certified(MODULE, daf, doc, sugya, audit)
    state, problems = certificate_status(MODULE, daf, doc, sugya, rec)
    assert state != "CERTIFIED"
    assert any("openEndingFieldSweep" in p for p in problems), problems

    # Now supply a sweep, but one entry dishonestly (for test purposes)
    # admits it imports the next daf's conclusion -- must still fail.
    audit2 = clean_audit(MODULE, daf, doc, sugya)
    audit2["dafBoundary"]["dafEndState"] = "MID_ARGUMENT"
    paths = enumerate_semantic_paths(sugya)
    audit2["openEndingFieldSweep"] = [
        {"path": p, "importsNextDafConclusion": (p == paths[0])}
        for p in paths
    ]
    rec2 = build_certified(MODULE, daf, doc, sugya, audit2)
    state2, problems2 = certificate_status(MODULE, daf, doc, sugya, rec2)
    assert state2 != "CERTIFIED"
    assert any("importing the next daf's conclusion" in p for p in problems2), problems2

    # A fully clean sweep (nothing imports next-daf conclusions) certifies.
    audit3 = clean_audit(MODULE, daf, doc, sugya)
    audit3["dafBoundary"]["dafEndState"] = "MID_ARGUMENT"
    audit3["openEndingFieldSweep"] = [
        {"path": p, "importsNextDafConclusion": False} for p in paths
    ]
    rec3 = build_certified(MODULE, daf, doc, sugya, audit3)
    state3, problems3 = certificate_status(MODULE, daf, doc, sugya, rec3)
    assert state3 == "CERTIFIED", problems3


def test_2_stale_content_sweep_finding_blocks_certification():
    """A repair that fixes the primary field but leaves a stale old error
    elsewhere cannot pass the final whole-record audit."""
    daf, doc, sugya = load_target()
    audit = clean_audit(MODULE, daf, doc, sugya)
    audit["staleContentSweep"]["entries"] = [
        {"category": c, "found": (c == "old_conclusion_in_secondary_field")}
        for c in STALE_SWEEP_CATEGORIES
    ]
    rec = build_certified(MODULE, daf, doc, sugya, audit)
    state, problems = certificate_status(MODULE, daf, doc, sugya, rec)
    assert state != "CERTIFIED"
    assert any("old_conclusion_in_secondary_field" in p and "unresolved" in p for p in problems), problems


def test_3_missing_field_from_inventory_fails():
    """Missing even one semantic field from the machine-generated field
    inventory makes certification fail."""
    daf, doc, sugya = load_target()
    audit = clean_audit(MODULE, daf, doc, sugya)
    assert len(audit["fieldInventory"]) > 1
    audit["fieldInventory"] = audit["fieldInventory"][1:]
    rec = build_certified(MODULE, daf, doc, sugya, audit)
    state, problems = certificate_status(MODULE, daf, doc, sugya, rec)
    assert state != "CERTIFIED"
    assert any("omits" in p and "expected path" in p for p in problems), problems


def test_4_stale_final_audit_fingerprint_fails():
    """A final audit whose semantic fingerprint does not equal the current
    candidate fails."""
    daf, doc, sugya = load_target()
    audit = clean_audit(MODULE, daf, doc, sugya)
    audit["auditedSemanticFingerprint"] = "0" * 64
    rec = build_certified(MODULE, daf, doc, sugya, audit)
    state, problems = certificate_status(MODULE, daf, doc, sugya, rec)
    assert state != "CERTIFIED"
    assert any("auditedSemanticFingerprint" in p for p in problems), problems


def test_5_semantic_edit_after_final_audit_makes_certificate_stale():
    """A semantic edit after the final audit makes the certificate stale."""
    daf, doc, sugya = load_target()
    rec = build_certified(MODULE, daf, doc, sugya)
    state, _ = certificate_status(MODULE, daf, doc, sugya, rec)
    assert state == "CERTIFIED"

    edited_doc = copy.deepcopy(doc)
    edited_sugya = next(s for s in edited_doc["sugyot"] if s["id"] == SID)
    edited_sugya.setdefault("display", {})["title"] = edited_sugya.get("display", {}).get("title", "") + " EDITED"
    state2, problems2 = certificate_status(MODULE, daf, edited_doc, edited_sugya, rec)
    assert state2 != "CERTIFIED"
    assert any("stale" in p.lower() for p in problems2), problems2


def test_6_source_support_outside_authorized_range_fails():
    """Source-support lines outside the authorized daf/sugya range fail,
    even when boundarySafe is falsely declared true. dafSummary is exempt
    from per-sugya containment (a shared page claim may cite any line on the
    current daf), so this targets an ordinary sugya-scoped field instead."""
    daf, doc, sugya = load_target()
    audit = clean_audit(MODULE, daf, doc, sugya)
    lr = sugya["lineRange"]
    target_index = next(i for i, e in enumerate(audit["fieldInventory"]) if e["path"] != "dafSummary")
    target_path = audit["fieldInventory"][target_index]["path"]
    out_of_range_entry = {
        "path": target_path,
        "verdict": "SUPPORTED",
        "boundarySafe": True,  # falsely declared safe
        "crossReference": False,
        "supportingLines": [{"daf": daf, "startVilnaLine": lr["endVilnaLine"] + 5, "endVilnaLine": lr["endVilnaLine"] + 6}],
    }
    audit["fieldInventory"][target_index] = out_of_range_entry
    rec = build_certified(MODULE, daf, doc, sugya, audit)
    state, problems = certificate_status(MODULE, daf, doc, sugya, rec)
    assert state != "CERTIFIED"
    assert any("outside the authorized" in p or "does not match the mechanically" in p for p in problems), problems

    # The classic failure mode named in the audit: citing a DIFFERENT daf
    # as support for a claim on the current daf, without crossReference.
    next_daf_entry = dict(out_of_range_entry)
    next_daf_entry["supportingLines"] = [{"daf": "differentdaf", "startVilnaLine": 1, "endVilnaLine": 1}]
    audit2 = clean_audit(MODULE, daf, doc, sugya)
    audit2["fieldInventory"][target_index] = next_daf_entry
    rec2 = build_certified(MODULE, daf, doc, sugya, audit2)
    state2, problems2 = certificate_status(MODULE, daf, doc, sugya, rec2)
    assert state2 != "CERTIFIED"


def test_7_reused_reviewer_context_fails():
    """Reusing the same actual reviewer context for the supposedly
    independent pass fails, even with different reviewId strings."""
    daf, doc, sugya = load_target()
    source_fp, semantic_fp = fingerprints(MODULE, daf, doc, sugya)
    audit = clean_audit(MODULE, daf, doc, sugya)
    rec = make_certified_record(
        MODULE, daf, doc, sugya,
        base_review("pass-A", "same-context", "VERIFIED", source_fp, semantic_fp),
        base_review("pass-B", "same-context", "CONFIRMED", source_fp, semantic_fp),
        audit,
        "deadbeef",
    )
    state, problems = certificate_status(MODULE, daf, doc, sugya, rec)
    assert state != "CERTIFIED"
    assert any("reviewer contexts" in p for p in problems), problems


def test_migration_is_one_time_and_preserves_evidence():
    data = {
        "schemaVersion": "1.0",
        "module": MODULE,
        "strictMode": False,
        "records": {
            "x": {
                "sugyaId": "x", "daf": "2a", "state": "CERTIFIED",
                "sourceFingerprint": "src-a", "semanticFingerprint": "sem-a",
                "firstPass": {"reviewId": "r1", "verdict": "VERIFIED"},
                "secondPass": {"reviewId": "r2", "verdict": "CONFIRMED"},
                "certifiedAtCommit": "deadbeef",
            },
            "y": {"sugyaId": "y", "daf": "2a", "state": "REPAIR_REQUIRED", "firstPass": {}},
        },
    }
    migrated, count = migrate(data, "commit123")
    assert count == 1
    assert migrated["schemaVersion"] == CERT_SCHEMA_VERSION
    assert migrated["records"]["x"]["state"] == "REVALIDATION_REQUIRED"
    assert migrated["records"]["x"]["sourceFingerprint"] == "src-a"
    assert migrated["records"]["x"]["semanticFingerprint"] == "sem-a"
    assert migrated["records"]["x"]["certifiedAtCommit"] == "deadbeef"
    assert migrated["records"]["x"]["migration"]["fromSchemaVersion"] == "1.0"
    # Non-CERTIFIED records pass through untouched.
    assert migrated["records"]["y"] == data["records"]["y"]

    try:
        migrate(migrated, "commit456")
        raise AssertionError("migrating an already-2.0 registry must be refused")
    except ValueError:
        pass


def test_ratchet_carveout_is_narrow_and_self_disabling():
    old_record = {"state": "CERTIFIED", "sourceFingerprint": "s1", "semanticFingerprint": "m1"}
    good_new_record = {
        "state": "REVALIDATION_REQUIRED",
        "sourceFingerprint": "s1", "semanticFingerprint": "m1",
        "migration": {"fromSchemaVersion": "1.0"},
    }
    # Exactly the sanctioned transition: allowed.
    assert allowed_schema_migration_downgrade("1.0", CERT_SCHEMA_VERSION, old_record, good_new_record) is True

    # Base already on schema 2.0 (post-migration): never allowed again.
    assert allowed_schema_migration_downgrade(CERT_SCHEMA_VERSION, CERT_SCHEMA_VERSION, old_record, good_new_record) is False

    # No migration provenance marker: not the sanctioned path.
    unmarked = dict(good_new_record)
    del unmarked["migration"]
    assert allowed_schema_migration_downgrade("1.0", CERT_SCHEMA_VERSION, old_record, unmarked) is False

    # Fingerprints changed under the relabel: a real content regression
    # cannot hide behind the migration exception.
    smuggled = dict(good_new_record)
    smuggled["semanticFingerprint"] = "TAMPERED"
    assert allowed_schema_migration_downgrade("1.0", CERT_SCHEMA_VERSION, old_record, smuggled) is False

    # Not actually REVALIDATION_REQUIRED (e.g. plain UNCERTIFIED/absent): no.
    assert allowed_schema_migration_downgrade("1.0", CERT_SCHEMA_VERSION, old_record, None) is False


def main() -> None:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
        print(f"OK: {t.__name__}")
    print(f"OK: {len(tests)} schema-2.0 final-audit regression tests passed")


if __name__ == "__main__":
    main()
