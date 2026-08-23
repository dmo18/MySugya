#!/usr/bin/env python3
"""Regression tests for the schema-2.0 mandatory final whole-record audit.

These reproduce, as generalized invariants (never hardcoded to a specific
daf), the exact failure classes an independent audit demonstrated: (1) Yoma
7a/7b certified while a daf ending mid-thought left stale completed-
conclusion prose in fields other than the one a repair touched, and (2) a
follow-up review of the schema-2.0 implementation itself found remaining
certification bypasses (a NONFACTUAL escape hatch for authored prose, a
hand-curated rather than exhaustive field enumerator, missing daf-level
glossary coverage, an unrestricted crossReference bypass, a conditional
boundary-leakage sweep, and incomplete reviewer-context distinctness). See
docs/semantic-self-heal.md.
"""
from __future__ import annotations

import copy
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from semantic_certification import (
    CERT_SCHEMA_VERSION,
    REPO,
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


def clean_audit(module, daf, doc, sugya, review_id="audit-C", ctx="agent-C", daf_end_state="COMPLETE") -> dict:
    """A mechanically-valid finalAudit: every SEMANTIC path is SUPPORTED with
    real, in-range supporting lines; STRUCTURAL paths use NONFACTUAL;
    METADATA paths (argumentFlow step type, takeaway type, difficulty, etc.)
    use REVIEWED with a justifying note. boundaryLeakageSweep is always
    populated (mandatory regardless of dafEndState) and covers SEMANTIC and
    METADATA paths alike; entries carry a `note` when dafEndState is not
    COMPLETE (the stricter open-ending evidentiary burden).
    """
    source_fp, semantic_fp = fingerprints(module, daf, doc, sugya)
    raw_lines = json.loads((raw_dir(module) / f"{daf}.json").read_text(encoding="utf-8")).get("lines") or []
    lr = sugya["lineRange"]

    entries = []
    swept_paths = []
    for path, cls in enumerate_semantic_paths(module, doc, sugya):
        if cls == "STRUCTURAL":
            entries.append({"path": path, "verdict": "NONFACTUAL", "boundarySafe": True, "crossReference": False})
            continue
        if cls == "METADATA":
            entries.append({
                "path": path, "verdict": "REVIEWED", "boundarySafe": True, "crossReference": False,
                "note": "test: classification independently re-derived from source and confirmed consistent",
            })
            swept_paths.append(path)
            continue
        swept_paths.append(path)
        if path.startswith("dafLevel."):
            lines = [{"daf": daf, "startVilnaLine": 1, "endVilnaLine": len(raw_lines)}]
        else:
            lines = [{"daf": daf, "startVilnaLine": lr["startVilnaLine"], "endVilnaLine": lr["endVilnaLine"]}]
        entries.append({
            "path": path, "verdict": "SUPPORTED", "boundarySafe": True,
            "crossReference": False, "supportingLines": lines,
        })

    sweep = []
    for p in swept_paths:
        e = {"path": p, "importsNextDafConclusion": False}
        if daf_end_state != "COMPLETE":
            e["note"] = "test: reviewed and does not import the next daf's conclusion"
        sweep.append(e)

    return {
        "reviewId": review_id,
        "auditorContextId": ctx,
        "auditedSourceFingerprint": source_fp,
        "auditedSemanticFingerprint": semantic_fp,
        "dafBoundary": {
            "rawLineCount": len(raw_lines),
            "finalRawLine": raw_lines[-1] if raw_lines else "",
            "dafEndState": daf_end_state,
        },
        "fieldInventory": entries,
        "boundaryLeakageSweep": sweep,
        "staleContentSweep": {"entries": [{"category": c, "found": False} for c in STALE_SWEEP_CATEGORIES]},
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


def test_1_semantic_prose_cannot_be_marked_nonfactual_to_bypass_support():
    """Item 1: a factual/interpretive semantic field cannot be classified
    NONFACTUAL to skip source-support validation, even though the same
    verdict is legal for a STRUCTURAL path."""
    daf, doc, sugya = load_target()
    audit = clean_audit(MODULE, daf, doc, sugya)
    idx = next(i for i, e in enumerate(audit["fieldInventory"]) if e["verdict"] == "SUPPORTED")
    path = audit["fieldInventory"][idx]["path"]
    audit["fieldInventory"][idx] = {"path": path, "verdict": "NONFACTUAL", "boundarySafe": True, "crossReference": False}
    rec = build_certified(MODULE, daf, doc, sugya, audit)
    state, problems = certificate_status(MODULE, daf, doc, sugya, rec)
    assert state != "CERTIFIED"
    assert any("NONFACTUAL is not a legal verdict" in p for p in problems), problems


def test_2_unknown_new_semantic_field_automatically_inventoried():
    """Item 2: enumerate_semantic_paths recurses the whole payload, so a
    brand-new field the enumerator has never seen by name is still caught
    -- without any change to the enumerator itself."""
    daf, doc, sugya = load_target()
    doc2 = copy.deepcopy(doc)
    sugya2 = next(s for s in doc2["sugyot"] if s["id"] == SID)
    sugya2["totallyNewFieldNeverSeenByTheEnumerator"] = "a brand new authored claim about this sugya"

    paths = dict(enumerate_semantic_paths(MODULE, doc2, sugya2))
    assert "totallyNewFieldNeverSeenByTheEnumerator" in paths
    assert paths["totallyNewFieldNeverSeenByTheEnumerator"] == "SEMANTIC"

    # An audit that omits the new field from its inventory fails.
    audit = clean_audit(MODULE, daf, doc2, sugya2)
    audit["fieldInventory"] = [e for e in audit["fieldInventory"] if e["path"] != "totallyNewFieldNeverSeenByTheEnumerator"]
    audit["boundaryLeakageSweep"] = [e for e in audit["boundaryLeakageSweep"] if e["path"] != "totallyNewFieldNeverSeenByTheEnumerator"]
    rec = build_certified(MODULE, daf, doc2, sugya2, audit)
    state, problems = certificate_status(MODULE, daf, doc2, sugya2, rec)
    assert state != "CERTIFIED"
    assert any("omits" in p and "totallyNewFieldNeverSeenByTheEnumerator" in p for p in problems), problems

    # Including it (the normal clean_audit output) certifies.
    audit2 = clean_audit(MODULE, daf, doc2, sugya2)
    rec2 = build_certified(MODULE, daf, doc2, sugya2, audit2)
    state2, problems2 = certificate_status(MODULE, daf, doc2, sugya2, rec2)
    assert state2 == "CERTIFIED", problems2


def test_3_legacy_visualizable_description_key_inventoried():
    """Item 2 coverage check: a legacy visualizableElements shape using a
    'description' key (rather than the current 'item') is still caught by
    generic recursion, not only the specific keys the schema names today."""
    daf, doc, sugya = load_target()
    doc2 = copy.deepcopy(doc)
    sugya2 = next(s for s in doc2["sugyot"] if s["id"] == SID)
    sugya2.setdefault("visualizableElements", []).append({"description": "a legacy-shaped visualization description"})
    paths = dict(enumerate_semantic_paths(MODULE, doc2, sugya2))
    matches = [p for p in paths if p.startswith("visualizableElements") and p.endswith(".description")]
    assert matches, sorted(paths)
    assert paths[matches[0]] == "SEMANTIC"


def test_4_quiz_distractors_inventoried():
    """Item 2 coverage check: quiz distractors, not named in any hardcoded
    list, are still caught by generic recursion."""
    daf, doc, sugya = load_target()
    doc2 = copy.deepcopy(doc)
    sugya2 = next(s for s in doc2["sugyot"] if s["id"] == SID)
    sugya2.setdefault("quizSeeds", []).append({"question": "q", "answer": "a", "distractors": ["wrong1", "wrong2"]})
    paths = dict(enumerate_semantic_paths(MODULE, doc2, sugya2))
    matches = [p for p in paths if "distractors" in p]
    assert matches, sorted(paths)
    assert all(paths[p] == "SEMANTIC" for p in matches)


def test_5_daf_glossary_missing_from_inventory_fails():
    """Item 3: daf-level glossary is part of the audited inventory; omitting
    it fails certification."""
    daf, doc, sugya = load_target()
    doc2 = copy.deepcopy(doc)
    doc2["glossary"] = list(doc2.get("glossary") or []) + [{"he": "test", "translit": "test", "en": "a glossary definition"}]
    sugya2 = next(s for s in doc2["sugyot"] if s["id"] == SID)

    audit = clean_audit(MODULE, daf, doc2, sugya2)
    audit["fieldInventory"] = [e for e in audit["fieldInventory"] if not e["path"].startswith("dafLevel.glossary")]
    audit["boundaryLeakageSweep"] = [e for e in audit["boundaryLeakageSweep"] if not e["path"].startswith("dafLevel.glossary")]
    rec = build_certified(MODULE, daf, doc2, sugya2, audit)
    state, problems = certificate_status(MODULE, daf, doc2, sugya2, rec)
    assert state != "CERTIFIED"
    assert any("dafLevel.glossary" in p for p in problems), problems


def test_6_glossary_edit_after_certification_makes_certificate_stale():
    """Item 3: a change to the daf-level glossary invalidates every sugya
    certificate on the daf, exactly like the daf summary."""
    daf, doc, sugya = load_target()
    rec = build_certified(MODULE, daf, doc, sugya)
    state, _ = certificate_status(MODULE, daf, doc, sugya, rec)
    assert state == "CERTIFIED"

    edited_doc = copy.deepcopy(doc)
    edited_doc["glossary"] = list(edited_doc.get("glossary") or []) + [
        {"he": "x", "translit": "x", "en": "a definition that was never certified"}
    ]
    edited_sugya = next(s for s in edited_doc["sugyot"] if s["id"] == SID)
    state2, problems2 = certificate_status(MODULE, daf, edited_doc, edited_sugya, rec)
    assert state2 != "CERTIFIED"
    assert any("semanticFingerprint is stale" in p for p in problems2), problems2


def test_7_illegal_crossreference_on_local_field_fails():
    """Item 4: a local semantic claim (display/learning/argumentFlow/etc.)
    can never escape same-daf source support merely by setting
    crossReference true."""
    daf, doc, sugya = load_target()
    audit = clean_audit(MODULE, daf, doc, sugya)
    idx = next(i for i, e in enumerate(audit["fieldInventory"]) if e["path"].startswith("learning."))
    entry = audit["fieldInventory"][idx]
    entry["crossReference"] = True
    entry["supportingLines"] = [{"daf": "88a", "startVilnaLine": 1, "endVilnaLine": 1}]
    rec = build_certified(MODULE, daf, doc, sugya, audit)
    state, problems = certificate_status(MODULE, daf, doc, sugya, rec)
    assert state != "CERTIFIED"
    assert any("crossReference is not permitted" in p for p in problems), problems


def test_8_legitimate_crossreference_validated_against_real_target():
    """Item 4: relatedSugyot prose IS allowed to cite another daf, but the
    cited daf/range must actually exist -- a legitimate crossReference is
    not trusted blindly."""
    daf, doc, sugya = load_target()
    doc2 = copy.deepcopy(doc)
    sugya2 = next(s for s in doc2["sugyot"] if s["id"] == SID)
    sugya2["relatedSugyot"] = [{"id": "yoma-002a-s01", "reason": "parallel discussion elsewhere in the tractate"}]
    paths = dict(enumerate_semantic_paths(MODULE, doc2, sugya2))
    reason_path = next(p for p in paths if p.startswith("relatedSugyot") and p.endswith(".reason"))
    assert paths[reason_path] == "SEMANTIC"

    real_2a_lines = json.loads((raw_dir(MODULE) / "2a.json").read_text(encoding="utf-8")).get("lines") or []

    # Valid: real daf, real in-range lines -> certifies.
    audit = clean_audit(MODULE, daf, doc2, sugya2)
    idx = next(i for i, e in enumerate(audit["fieldInventory"]) if e["path"] == reason_path)
    audit["fieldInventory"][idx] = {
        "path": reason_path, "verdict": "SUPPORTED", "boundarySafe": True, "crossReference": True,
        "supportingLines": [{"daf": "2a", "startVilnaLine": 1, "endVilnaLine": min(2, len(real_2a_lines))}],
    }
    audit["boundaryLeakageSweep"] = [e for e in audit["boundaryLeakageSweep"] if e["path"] != reason_path] + [
        {"path": reason_path, "importsNextDafConclusion": False}
    ]
    rec = build_certified(MODULE, daf, doc2, sugya2, audit)
    state, problems = certificate_status(MODULE, daf, doc2, sugya2, rec)
    assert state == "CERTIFIED", problems

    # Invalid: line range past the real target daf's actual line count.
    audit2 = clean_audit(MODULE, daf, doc2, sugya2)
    idx2 = next(i for i, e in enumerate(audit2["fieldInventory"]) if e["path"] == reason_path)
    audit2["fieldInventory"][idx2] = {
        "path": reason_path, "verdict": "SUPPORTED", "boundarySafe": True, "crossReference": True,
        "supportingLines": [{"daf": "2a", "startVilnaLine": 1, "endVilnaLine": len(real_2a_lines) + 500}],
    }
    rec2 = build_certified(MODULE, daf, doc2, sugya2, audit2)
    state2, problems2 = certificate_status(MODULE, daf, doc2, sugya2, rec2)
    assert state2 != "CERTIFIED"


def test_9_complete_cannot_skip_boundary_leakage_sweep():
    """Item 5: the boundary-leakage sweep is mandatory for EVERY daf,
    including one honestly (or dishonestly) declared COMPLETE."""
    daf, doc, sugya = load_target()
    audit = clean_audit(MODULE, daf, doc, sugya, daf_end_state="COMPLETE")
    del audit["boundaryLeakageSweep"]
    rec = build_certified(MODULE, daf, doc, sugya, audit)
    state, problems = certificate_status(MODULE, daf, doc, sugya, rec)
    assert state != "CERTIFIED"
    assert any("boundaryLeakageSweep" in p for p in problems), problems


def test_10_sweep_flag_true_blocks_regardless_of_declared_end_state():
    """Item 5: importsNextDafConclusion=True blocks certification whether
    the reviewer declared COMPLETE or an open state -- dafEndState is
    evidence, never a gate on whether the sweep is honored."""
    daf, doc, sugya = load_target()
    for end_state in ("COMPLETE", "MID_ARGUMENT"):
        audit = clean_audit(MODULE, daf, doc, sugya, daf_end_state=end_state)
        audit["boundaryLeakageSweep"][0]["importsNextDafConclusion"] = True
        rec = build_certified(MODULE, daf, doc, sugya, audit)
        state, problems = certificate_status(MODULE, daf, doc, sugya, rec)
        assert state != "CERTIFIED", end_state
        assert any("importing the next daf's conclusion" in p for p in problems), (end_state, problems)


def test_11_open_ending_sweep_requires_nonblank_note():
    """Item 5 (stricter mode): an open dafEndState raises the evidentiary
    burden -- every sweep entry needs an explicit justification, not just
    the same boolean required for a COMPLETE daf."""
    daf, doc, sugya = load_target()
    audit = clean_audit(MODULE, daf, doc, sugya, daf_end_state="MID_ARGUMENT")
    for e in audit["boundaryLeakageSweep"]:
        e.pop("note", None)
    rec = build_certified(MODULE, daf, doc, sugya, audit)
    state, problems = certificate_status(MODULE, daf, doc, sugya, rec)
    assert state != "CERTIFIED"
    assert any("requires a nonblank note" in p for p in problems), problems


def test_12_stale_content_sweep_finding_blocks_certification():
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


def test_13_missing_field_from_inventory_fails():
    daf, doc, sugya = load_target()
    audit = clean_audit(MODULE, daf, doc, sugya)
    assert len(audit["fieldInventory"]) > 1
    dropped = audit["fieldInventory"][0]["path"]
    audit["fieldInventory"] = audit["fieldInventory"][1:]
    audit["boundaryLeakageSweep"] = [e for e in audit["boundaryLeakageSweep"] if e["path"] != dropped]
    rec = build_certified(MODULE, daf, doc, sugya, audit)
    state, problems = certificate_status(MODULE, daf, doc, sugya, rec)
    assert state != "CERTIFIED"
    assert any("omits" in p and "expected path" in p for p in problems), problems


def test_14_stale_final_audit_fingerprint_fails():
    daf, doc, sugya = load_target()
    audit = clean_audit(MODULE, daf, doc, sugya)
    audit["auditedSemanticFingerprint"] = "0" * 64
    rec = build_certified(MODULE, daf, doc, sugya, audit)
    state, problems = certificate_status(MODULE, daf, doc, sugya, rec)
    assert state != "CERTIFIED"
    assert any("auditedSemanticFingerprint" in p for p in problems), problems


def test_15_semantic_edit_after_final_audit_makes_certificate_stale():
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


def test_16_source_support_outside_authorized_range_fails():
    """Source-support lines outside the authorized daf/sugya range fail,
    even when boundarySafe is falsely declared true. dafLevel.* paths are
    exempt from per-sugya containment (a shared page claim may cite any
    line on the current daf), so this targets an ordinary sugya-scoped
    SEMANTIC field instead."""
    daf, doc, sugya = load_target()
    audit = clean_audit(MODULE, daf, doc, sugya)
    lr = sugya["lineRange"]
    target_index = next(
        i for i, e in enumerate(audit["fieldInventory"])
        if e["verdict"] == "SUPPORTED" and not e["path"].startswith("dafLevel.")
    )
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

    # Citing a DIFFERENT daf without crossReference is the same failure mode.
    next_daf_entry = dict(out_of_range_entry)
    next_daf_entry["supportingLines"] = [{"daf": "differentdaf", "startVilnaLine": 1, "endVilnaLine": 1}]
    audit2 = clean_audit(MODULE, daf, doc, sugya)
    audit2["fieldInventory"][target_index] = next_daf_entry
    rec2 = build_certified(MODULE, daf, doc, sugya, audit2)
    state2, _ = certificate_status(MODULE, daf, doc, sugya, rec2)
    assert state2 != "CERTIFIED"


def test_17_reused_reviewer_context_fails():
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


def test_18_final_auditor_context_same_as_second_reviewer_fails():
    """Item 6: the final auditor context must differ from BOTH the first
    and second pass reviewer contexts, not only the first."""
    daf, doc, sugya = load_target()
    rec = build_certified(MODULE, daf, doc, sugya)
    tampered = copy.deepcopy(rec)
    tampered["finalAudit"]["auditorContextId"] = tampered["secondPass"]["reviewerContextId"]
    state, problems = certificate_status(MODULE, daf, doc, sugya, tampered)
    assert state != "CERTIFIED"
    assert any("auditorContextId must differ from secondPass" in p for p in problems), problems


def test_19_final_audit_reviewid_must_differ_from_first_and_second():
    daf, doc, sugya = load_target()
    rec = build_certified(MODULE, daf, doc, sugya)
    tampered = copy.deepcopy(rec)
    tampered["finalAudit"]["reviewId"] = tampered["firstPass"]["reviewId"]
    state, problems = certificate_status(MODULE, daf, doc, sugya, tampered)
    assert state != "CERTIFIED"
    assert any("finalAudit.reviewId must differ from firstPass" in p for p in problems), problems

    tampered2 = copy.deepcopy(rec)
    tampered2["finalAudit"]["reviewId"] = tampered2["secondPass"]["reviewId"]
    state2, problems2 = certificate_status(MODULE, daf, doc, sugya, tampered2)
    assert state2 != "CERTIFIED"
    assert any("finalAudit.reviewId must differ from secondPass" in p for p in problems2), problems2


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
    assert allowed_schema_migration_downgrade("1.0", CERT_SCHEMA_VERSION, old_record, good_new_record) is True
    assert allowed_schema_migration_downgrade(CERT_SCHEMA_VERSION, CERT_SCHEMA_VERSION, old_record, good_new_record) is False
    unmarked = dict(good_new_record)
    del unmarked["migration"]
    assert allowed_schema_migration_downgrade("1.0", CERT_SCHEMA_VERSION, old_record, unmarked) is False
    smuggled = dict(good_new_record)
    smuggled["semanticFingerprint"] = "TAMPERED"
    assert allowed_schema_migration_downgrade("1.0", CERT_SCHEMA_VERSION, old_record, smuggled) is False
    assert allowed_schema_migration_downgrade("1.0", CERT_SCHEMA_VERSION, old_record, None) is False


def _git(args, cwd):
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)


def _make_repo_copy_fixture():
    """A disposable tar+git-init copy of the real repo, exactly the pattern
    used by test_worker_pipeline_integration.py, so semantic_repair_scope_v2.py
    (which resolves its own repo root from __file__) operates on a throwaway
    copy instead of the real working tree."""
    tmp = Path(tempfile.mkdtemp(prefix="mysugya-glossary-scope-fixture-"))
    dest = tmp / "repo"
    dest.mkdir()
    r = subprocess.run(
        "tar --exclude=.git --exclude=node_modules --exclude=dist --exclude=__pycache__ "
        "-cf - . | tar -xf - -C %s" % dest,
        shell=True, cwd=str(REPO), capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
    _git(["init", "-q"], dest)
    _git(["config", "core.hooksPath", "githooks"], dest)
    hook = dest / "githooks" / "pre-commit"
    hook.write_text("#!/bin/sh\nexit 0\n")
    hook.chmod(0o755)
    _git(["add", "-A", "-f"], dest)
    _git(["-c", "user.email=t@t.local", "-c", "user.name=t", "commit", "-q", "-m", "base"], dest)
    base_sha = _git(["rev-parse", "HEAD"], dest).stdout.strip()
    return dest, base_sha


def test_20_glossary_repair_scope_requires_full_daf_target():
    """Item 3: a same-daf glossary correction is permitted only when every
    sugya on that daf is named in the manifest, exactly like a summary edit;
    a partial-scope glossary edit still fails."""
    dest, base_sha = _make_repo_copy_fixture()
    try:
        learn_path = dest / "modules/yoma/assets/learning/yoma/2a.learning.json"
        doc = json.loads(learn_path.read_text(encoding="utf-8"))
        sugya_ids = [s["id"] for s in doc["sugyot"]]
        assert len(sugya_ids) >= 2, "2a fixture must have multiple sugyot for this test"
        doc["glossary"] = list(doc.get("glossary") or []) + [{"he": "test", "translit": "test", "en": "new definition"}]
        learn_path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

        registry_path = dest / "docs/reports/data/yoma-semantic-certifications.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        registry["_testTouch"] = True
        registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

        manifest_path = dest / ".semantic-repair-manifest.json"

        # Partial scope: only one sugya named -> FAIL.
        manifest_path.write_text(json.dumps({
            "schemaVersion": "1.0", "type": "semantic-daf-repair", "module": "yoma",
            "daf": "2a", "sugyaIds": [sugya_ids[0]], "firstReviewId": "test-review",
        }), encoding="utf-8")
        _git(["add", "-A"], dest)
        _git(["-c", "user.email=t@t.local", "-c", "user.name=t", "commit", "-q", "-m", "partial glossary edit"], dest)
        r = subprocess.run(
            ["python3", "scripts/semantic_repair_scope_v2.py", "--base", base_sha],
            cwd=str(dest), capture_output=True, text=True,
        )
        assert r.returncode != 0 and "glossary" in (r.stdout + r.stderr), (r.stdout, r.stderr)

        # Full scope: every sugya on the daf named -> PASS.
        manifest_path.write_text(json.dumps({
            "schemaVersion": "1.0", "type": "semantic-daf-repair", "module": "yoma",
            "daf": "2a", "sugyaIds": sugya_ids, "firstReviewId": "test-review",
        }), encoding="utf-8")
        _git(["add", "-A"], dest)
        _git(["-c", "user.email=t@t.local", "-c", "user.name=t", "commit", "-q", "-m", "full-daf glossary edit"], dest)
        r2 = subprocess.run(
            ["python3", "scripts/semantic_repair_scope_v2.py", "--base", base_sha],
            cwd=str(dest), capture_output=True, text=True,
        )
        assert r2.returncode == 0, (r2.stdout, r2.stderr)
    finally:
        shutil.rmtree(dest.parent, ignore_errors=True)


def test_21_requires_understanding_legacy_prose_is_semantic():
    """Round-3 item 1: requiresUnderstanding scalar values are STRUCTURAL
    only when they actually resolve to a real sugya id. Legacy prose --
    the real shape currently in Yoma 7a's requiresUnderstanding, e.g. "The
    hutrah/dchuya framework from 6b" -- is SEMANTIC and must be source-
    supported, never NONFACTUAL, regardless of its container key."""
    daf, doc, sugya = load_target()
    doc2 = copy.deepcopy(doc)
    sugya2 = next(s for s in doc2["sugyot"] if s["id"] == SID)
    sugya2["requiresUnderstanding"] = [
        "The hutrah/dchuya framework from 6b",
        "What makes an offering 'communal' and what makes it 'fixed time'",
    ]
    paths = dict(enumerate_semantic_paths(MODULE, doc2, sugya2))
    ru_paths = [p for p in paths if p.startswith("requiresUnderstanding[")]
    assert ru_paths, sorted(paths)
    assert all(paths[p] == "SEMANTIC" for p in ru_paths), paths

    # The old escape (NONFACTUAL under cover of the container key) still fails.
    audit = clean_audit(MODULE, daf, doc2, sugya2)
    idx = next(i for i, e in enumerate(audit["fieldInventory"]) if e["path"] == ru_paths[0])
    audit["fieldInventory"][idx] = {"path": ru_paths[0], "verdict": "NONFACTUAL", "boundarySafe": True, "crossReference": False}
    rec = build_certified(MODULE, daf, doc2, sugya2, audit)
    state, problems = certificate_status(MODULE, daf, doc2, sugya2, rec)
    assert state != "CERTIFIED"
    assert any("NONFACTUAL is not a legal verdict" in p for p in problems), problems


def test_22_requires_understanding_valid_sugya_id_is_structural():
    """Round-3 item 1: a requiresUnderstanding value that actually resolves
    to a real sugya id in the live corpus is legitimately STRUCTURAL."""
    daf, doc, sugya = load_target()
    doc2 = copy.deepcopy(doc)
    sugya2 = next(s for s in doc2["sugyot"] if s["id"] == SID)
    real_other_id = "yoma-002a-s01"
    sugya2["requiresUnderstanding"] = [real_other_id]
    paths = dict(enumerate_semantic_paths(MODULE, doc2, sugya2))
    ru_path = next(p for p in paths if p.startswith("requiresUnderstanding["))
    assert paths[ru_path] == "STRUCTURAL", paths

    audit = clean_audit(MODULE, daf, doc2, sugya2)
    rec = build_certified(MODULE, daf, doc2, sugya2, audit)
    state, problems = certificate_status(MODULE, daf, doc2, sugya2, rec)
    assert state == "CERTIFIED", problems


def test_23_unknown_field_named_type_does_not_become_structural():
    """Round-3 item 2: classification is PATH-based, not key-name-based, for
    controlled metadata. A brand-new, unrelated field literally named "type"
    that does not match any known METADATA path defaults to SEMANTIC -- it
    never silently inherits STRUCTURAL from the generic key name."""
    daf, doc, sugya = load_target()
    doc2 = copy.deepcopy(doc)
    sugya2 = next(s for s in doc2["sugyot"] if s["id"] == SID)
    sugya2["totallyHypotheticalFutureField"] = {"type": "a made-up classification asserting something about this sugya"}
    paths = dict(enumerate_semantic_paths(MODULE, doc2, sugya2))
    type_path = "totallyHypotheticalFutureField.type"
    assert type_path in paths
    assert paths[type_path] == "SEMANTIC", paths


def test_24_known_metadata_paths_require_explicit_verdict():
    """Round-3 item 2: known METADATA paths (argumentFlow step type,
    learning.takeaway.type, difficulty, etc.) must appear in the inventory
    with an explicit verdict. NONFACTUAL is illegal for them (they are
    meaningful editorial content, unlike a bare STRUCTURAL id/coordinate),
    and REVIEWED requires a nonblank justifying note -- a bare boolean would
    be exactly the kind of unfalsifiable claim schema 2.0 rejects."""
    daf, doc, sugya = load_target()
    paths = dict(enumerate_semantic_paths(MODULE, doc, sugya))
    metadata_paths = [p for p, cls in paths.items() if cls == "METADATA"]
    assert metadata_paths, "expected at least one METADATA path (e.g. argumentFlow[*].type/learning.takeaway.type)"

    audit = clean_audit(MODULE, daf, doc, sugya)
    idx = next(i for i, e in enumerate(audit["fieldInventory"]) if e["path"] == metadata_paths[0])
    audit["fieldInventory"][idx] = {"path": metadata_paths[0], "verdict": "NONFACTUAL", "boundarySafe": True, "crossReference": False}
    rec = build_certified(MODULE, daf, doc, sugya, audit)
    state, problems = certificate_status(MODULE, daf, doc, sugya, rec)
    assert state != "CERTIFIED"
    assert any("not a legal verdict" in p for p in problems), problems

    audit2 = clean_audit(MODULE, daf, doc, sugya)
    idx2 = next(i for i, e in enumerate(audit2["fieldInventory"]) if e["path"] == metadata_paths[0])
    audit2["fieldInventory"][idx2] = {"path": metadata_paths[0], "verdict": "REVIEWED", "boundarySafe": True, "crossReference": False}
    rec2 = build_certified(MODULE, daf, doc, sugya, audit2)
    state2, problems2 = certificate_status(MODULE, daf, doc, sugya, rec2)
    assert state2 != "CERTIFIED"
    assert any("REVIEWED entries require a nonblank note" in p for p in problems2), problems2


def test_25_new_daf_level_field_automatically_fingerprinted_and_inventoried():
    """Round-3 item 3: daf-level enumeration is exhaustive, not limited to
    summary and glossary. A brand-new top-level daf field is automatically
    part of both semanticFingerprint and the audited fieldInventory, and
    editing it after certification makes the certificate stale."""
    daf, doc, sugya = load_target()
    doc2 = copy.deepcopy(doc)
    doc2["totallyNewDafLevelField"] = "a brand new authored claim about the whole daf"
    sugya2 = next(s for s in doc2["sugyot"] if s["id"] == SID)

    paths = dict(enumerate_semantic_paths(MODULE, doc2, sugya2))
    assert "dafLevel.totallyNewDafLevelField" in paths
    assert paths["dafLevel.totallyNewDafLevelField"] == "SEMANTIC"

    rec = build_certified(MODULE, daf, doc2, sugya2)
    state, problems = certificate_status(MODULE, daf, doc2, sugya2, rec)
    assert state == "CERTIFIED", problems

    edited_doc = copy.deepcopy(doc2)
    edited_doc["totallyNewDafLevelField"] = "an edit that was never certified"
    edited_sugya = next(s for s in edited_doc["sugyot"] if s["id"] == SID)
    state2, problems2 = certificate_status(MODULE, daf, edited_doc, edited_sugya, rec)
    assert state2 != "CERTIFIED"
    assert any("semanticFingerprint is stale" in p for p in problems2), problems2


def test_26_duplicate_stale_sweep_category_fails():
    """Round-3 item 4: each staleContentSweep category must appear exactly
    once; a duplicate (even with conflicting found values) fails
    certification rather than silently picking a winner."""
    daf, doc, sugya = load_target()
    audit = clean_audit(MODULE, daf, doc, sugya)
    entries = [{"category": c, "found": False} for c in STALE_SWEEP_CATEGORIES]
    entries.append({"category": STALE_SWEEP_CATEGORIES[0], "found": True})  # conflicting duplicate
    audit["staleContentSweep"]["entries"] = entries
    rec = build_certified(MODULE, daf, doc, sugya, audit)
    state, problems = certificate_status(MODULE, daf, doc, sugya, rec)
    assert state != "CERTIFIED"
    assert any("duplicate category" in p for p in problems), problems


def main() -> None:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
        print(f"OK: {t.__name__}")
    print(f"OK: {len(tests)} schema-2.0 final-audit regression tests passed")


if __name__ == "__main__":
    main()
