#!/usr/bin/env python3
"""Core primitives for source-first semantic certification.

This module deliberately does not decide whether Talmudic analysis is correct.
It makes semantic review durable and self-invalidating:

- sourceFingerprint binds a review to the exact Hebrew source range and source map
- semanticFingerprint binds it to every learner-facing semantic field
- each review pass records the exact source/semantic fingerprints it reviewed
- CERTIFIED requires two source-first review passes with different review ids
  AND a fingerprint-bound final whole-record audit performed after the
  candidate is finalized (schema 2.0, see below)
- a first pass that found REPAIR_REQUIRED cannot certify until a real payload
  change is proven and a repairRef is recorded
- incomplete historical findings are INVALID until re-read through the current
  fingerprint-bound review process
- any later source or semantic edit makes the certificate STALE automatically
- legacy review:"reviewed" metadata is never treated as certification
- legacy schema-1.0 CERTIFIED records never silently read as schema-2.0
  CERTIFIED; they read as REVALIDATION_REQUIRED until they receive a real
  schema-2.0 final whole-record audit (see migrate_certification_schema_v2.py)

Schema 2.0 final whole-record audit
------------------------------------
A schema-1.0 certificate required two source-first passes and trusted a
free-text declaration that "every field was checked". That was demonstrated
insufficient: a daf ending mid-thought could be repaired in one field
(argumentFlow) while other fields (quiz, finalRuling, summaries) still
asserted a conclusion that is only reached on the following daf.

Schema 2.0 adds a mandatory `finalAudit` block to every CERTIFIED record,
produced AFTER the first and second source-first passes, bound by hash to the
exact final sourceFingerprint/semanticFingerprint being certified:

- `fieldInventory`: one entry per machine-enumerated semantically authored
  field/leaf actually present in the record (see enumerate_semantic_paths),
  each carrying a verdict and, for factual claims, source-support lines that
  must fall inside the sugya's own authorized range (or the current daf for
  the shared daf summary) unless explicitly marked as a cross-reference.
- `dafBoundary`: a mechanically-checked physical-boundary assessment
  (rawLineCount/finalRawLine verified against the live raw source, plus a
  reviewer-declared dafEndState). An open dafEndState requires an explicit
  per-field `openEndingFieldSweep` proving no field imports the next daf's
  conclusion.
- `staleContentSweep`: a fixed, mechanically-enumerated checklist of stale-
  content failure modes (see STALE_SWEEP_CATEGORIES), each with an explicit
  found:true/false attestation. Any found:true blocks certification.

The final audit does not, by itself, prove Talmudic correctness -- a
dishonest or careless reviewer can still declare false verdicts. It closes
the specific gap that was demonstrated: an "everything was checked" free-text
claim can no longer stand in for a mechanically-enumerated, fingerprint-bound,
range-checked record. Genuine independent review (a real second reviewer
context, not just a second reviewId string) remains mandatory; see
`reviewerContextId`/`auditorContextId` below.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

REPO = Path(__file__).resolve().parent.parent
CERT_SCHEMA_VERSION = "2.0"
CERT_STATES = {
    "REPAIR_REQUIRED",
    "REPAIRED_PENDING_REVIEW",
    "PENDING_FINAL_AUDIT",
    "CERTIFIED",
    "BLOCKED",
    "REVALIDATION_REQUIRED",
}

SOURCE_KEYS = {"id", "sugyaNumber", "lineRange", "lines", "sefariaRefs", "canonicalRef", "daf"}
NON_SEMANTIC_KEYS = SOURCE_KEYS | {"review"}

# Legal verdicts for a single finalAudit.fieldInventory entry. SUPPORTED and
# NONFACTUAL are the only verdicts that can appear in a certifiable audit; an
# audit that honestly records REPAIR_REQUIRED or BLOCKED for any field proves
# the record is not ready to certify (repair and re-audit instead).
FIELD_VERDICTS = {"SUPPORTED", "REPAIR_REQUIRED", "BLOCKED", "NONFACTUAL"}

# Recognized physical daf-ending classifications for finalAudit.dafBoundary.
# Anything other than COMPLETE requires an explicit openEndingFieldSweep.
DAF_END_STATES = {
    "COMPLETE",
    "MID_WORD",
    "MID_SENTENCE",
    "MID_QUESTION",
    "MID_PROOF",
    "MID_ARGUMENT",
    "OTHER_OPEN_CONTINUATION",
}

# Fixed, mechanically-enumerated stale-content failure modes every finalAudit
# must explicitly attest to (found: true/false) before a record can certify.
# This is deliberately a closed checklist, not free text: the validator can
# then require every category to be present rather than trusting a reviewer
# to remember to check for all of them.
STALE_SWEEP_CATEGORIES = (
    "stale_original_error",
    "stale_speaker_or_attribution",
    "contradictory_speaker_attribution",
    "old_conclusion_in_secondary_field",
    "false_closure",
    "next_daf_content_leaked_backward",
    "claim_unsupported_by_physical_daf",
    "stale_quiz_question_or_answer",
    "stale_final_ruling",
    "stale_summary",
    "stale_learning_field",
    "stale_misconception",
    "stale_related_sugya_description",
    "stale_visualizable_element_prose",
    "source_refs_no_longer_supporting_claim",
    "reference_outside_declared_line_range",
)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def daf_sort_key(daf: str) -> Tuple[int, int]:
    m = re.fullmatch(r"(\d+)([ab])", daf)
    if not m:
        return (10**9, 9)
    return (int(m.group(1)), 0 if m.group(2) == "a" else 1)


def learning_dir(module: str) -> Path:
    return REPO / "modules" / module / "assets" / "learning" / module


def raw_dir(module: str) -> Path:
    return REPO / "modules" / module / "assets" / "talmuddev"


def cert_path(module: str) -> Path:
    return REPO / "docs" / "reports" / "data" / f"{module}-semantic-certifications.json"


def load_registry(module: str) -> Dict[str, Any]:
    path = cert_path(module)
    if not path.exists():
        return {
            "schemaVersion": CERT_SCHEMA_VERSION,
            "module": module,
            "strictMode": False,
            "records": {},
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("module") != module:
        raise ValueError(f"certification registry module mismatch: {data.get('module')!r} != {module!r}")
    if data.get("schemaVersion") != CERT_SCHEMA_VERSION:
        raise ValueError(
            f"unsupported semantic certification schemaVersion {data.get('schemaVersion')!r}; "
            f"expected {CERT_SCHEMA_VERSION!r}"
        )
    if not isinstance(data.get("records"), dict):
        raise ValueError("semantic certification registry records must be an object keyed by sugya id")
    return data


def load_corpus(module: str) -> Dict[str, Tuple[str, Dict[str, Any], Dict[str, Any]]]:
    out: Dict[str, Tuple[str, Dict[str, Any], Dict[str, Any]]] = {}
    for path in sorted(learning_dir(module).glob("*.learning.json"), key=lambda p: daf_sort_key(p.name.split(".")[0])):
        daf = path.name.replace(".learning.json", "")
        doc = json.loads(path.read_text(encoding="utf-8"))
        for sugya in doc.get("sugyot", []):
            sid = sugya.get("id")
            if not sid:
                raise ValueError(f"{path}: sugya without id")
            if sid in out:
                raise ValueError(f"duplicate sugya id {sid}")
            out[sid] = (daf, doc, sugya)
    return out


def source_payload(module: str, daf: str, sugya: Dict[str, Any]) -> Dict[str, Any]:
    raw_path = raw_dir(module) / f"{daf}.json"
    if not raw_path.exists():
        raise ValueError(f"missing authoritative talmuddev source for {daf}: {raw_path}")
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    lines = raw.get("lines") or []
    lr = sugya.get("lineRange") or {}
    start = lr.get("startVilnaLine")
    end = lr.get("endVilnaLine")
    if not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < start:
        raise ValueError(f"{sugya.get('id')}: invalid lineRange {lr!r}")
    if end > len(lines):
        raise ValueError(
            f"{sugya.get('id')}: lineRange {start}-{end} exceeds raw {daf} line count {len(lines)}"
        )
    return {
        "module": module,
        "daf": daf,
        "sugyaId": sugya.get("id"),
        "lineRange": lr,
        "lineMap": sugya.get("lines") or [],
        "sefariaRefs": sugya.get("sefariaRefs") or [],
        "rawHebrew": lines[start - 1 : end],
    }


def semantic_payload(daf_doc: Dict[str, Any], sugya: Dict[str, Any]) -> Dict[str, Any]:
    authored = {k: v for k, v in sugya.items() if k not in NON_SEMANTIC_KEYS}
    return {"dafSummary": daf_doc.get("summary", ""), "sugya": authored}


def fingerprints(module: str, daf: str, daf_doc: Dict[str, Any], sugya: Dict[str, Any]) -> Tuple[str, str]:
    return digest(source_payload(module, daf, sugya)), digest(semantic_payload(daf_doc, sugya))


def validate_review_block(block: Any, name: str) -> Iterable[str]:
    if not isinstance(block, dict):
        yield f"{name} must be an object"
        return
    if not isinstance(block.get("reviewId"), str) or not block["reviewId"].strip():
        yield f"{name}.reviewId must be a nonblank string"
    if block.get("sourceFirst") is not True:
        yield f"{name}.sourceFirst must be true"
    if not isinstance(block.get("verdict"), str) or not block["verdict"].strip():
        yield f"{name}.verdict must be a nonblank string"
    if not isinstance(block.get("reviewedSourceFingerprint"), str) or not block["reviewedSourceFingerprint"].strip():
        yield f"{name}.reviewedSourceFingerprint must be a nonblank string"
    if not isinstance(block.get("reviewedSemanticFingerprint"), str) or not block["reviewedSemanticFingerprint"].strip():
        yield f"{name}.reviewedSemanticFingerprint must be a nonblank string"
    # Schema 2.0: a different reviewId string inside the same reasoning
    # context is not real independence. reviewerContextId must name a
    # genuinely distinct reviewer/session/subagent context (never fabricated;
    # see docs/semantic-self-heal.md). Required on every review block going
    # forward, including firstPass, so REPAIR_REQUIRED/BLOCKED records also
    # carry real provenance.
    if not isinstance(block.get("reviewerContextId"), str) or not block["reviewerContextId"].strip():
        yield f"{name}.reviewerContextId must be a nonblank string naming a genuinely distinct reviewer/session/context"


def enumerate_semantic_paths(sugya: Dict[str, Any]) -> List[str]:
    """Machine-enumerate every semantically authored field/leaf actually
    present in a finished sugya record, for finalAudit.fieldInventory.

    This is deliberately produced by code from the actual final payload, not
    written by a reviewer, so "every field was checked" can be verified
    rather than merely declared. Only fields with real content are included:
    an optional field left empty carries no claim and needs no audit entry.
    Paths use argumentFlow step ids (stable across edits) and 0-based indices
    for other arrays (their own array identity is part of the semantic
    fingerprint, so a reordering already invalidates any prior audit).
    """
    paths: List[str] = []

    def add(p: str) -> None:
        paths.append(p)

    # Shared page-level claim: every sugya certificate on the daf includes
    # the daf summary in its semantic fingerprint, so it must be audited by
    # every sugya's finalAudit too.
    add("dafSummary")
    # Boundary/source-ownership fields: excluded from the semantic
    # fingerprint (they belong to sourceFingerprint) but explicitly required
    # in the final audit inventory so boundary correctness is never silently
    # assumed just because the fingerprint machinery didn't flag it.
    add("lineRange")
    add("lines")

    display = sugya.get("display") or {}
    if isinstance(display, dict):
        for k in ("title", "oneLine", "shortSummary", "whats", "hint"):
            if display.get(k):
                add(f"display.{k}")

    learning = sugya.get("learning") or {}
    if isinstance(learning, dict):
        for k in (
            "learnerQuestion", "coreTension", "coreMove", "resolution",
            "ahaMoment", "learningBlocker", "memoryAnchor",
        ):
            if learning.get(k):
                add(f"learning.{k}")
        takeaway = learning.get("takeaway")
        if isinstance(takeaway, dict) and takeaway.get("text"):
            add("learning.takeaway.text")
        reasoning = learning.get("reasoningPattern")
        if isinstance(reasoning, dict) and reasoning.get("notes"):
            add("learning.reasoningPattern.notes")

    for i, step in enumerate(sugya.get("argumentFlow") or []):
        if not isinstance(step, dict):
            continue
        key = step.get("id") or str(i)
        if step.get("label"):
            add(f"argumentFlow[{key}].label")
        if step.get("speaker"):
            add(f"argumentFlow[{key}].speaker")
        if step.get("text"):
            add(f"argumentFlow[{key}].text")
        if step.get("sourceRefs"):
            add(f"argumentFlow[{key}].sourceRefs")

    for i, q in enumerate(sugya.get("quizSeeds") or []):
        if not isinstance(q, dict):
            continue
        if q.get("question"):
            add(f"quizSeeds[{i}].question")
        if q.get("answer"):
            add(f"quizSeeds[{i}].answer")

    for i, m in enumerate(sugya.get("misconceptions") or []):
        if not isinstance(m, dict):
            continue
        if m.get("misconception"):
            add(f"misconceptions[{i}].misconception")
        if m.get("correction"):
            add(f"misconceptions[{i}].correction")

    if sugya.get("finalRuling"):
        add("finalRuling")

    for i, a in enumerate(sugya.get("alternateAngles") or []):
        if isinstance(a, dict):
            for k, v in sorted(a.items()):
                if isinstance(v, str) and v:
                    add(f"alternateAngles[{i}].{k}")
        elif isinstance(a, str) and a:
            add(f"alternateAngles[{i}]")

    for i, p in enumerate(sugya.get("prerequisiteKnowledge") or []):
        if p:
            add(f"prerequisiteKnowledge[{i}]")

    for i, r in enumerate(sugya.get("requiresUnderstanding") or []):
        if r:
            add(f"requiresUnderstanding[{i}]")

    for i, r in enumerate(sugya.get("relatedSugyot") or []):
        if r:
            add(f"relatedSugyot[{i}]")

    for i, v in enumerate(sugya.get("visualizableElements") or []):
        if isinstance(v, dict):
            if v.get("item"):
                add(f"visualizableElements[{i}].item")
            if v.get("label"):
                add(f"visualizableElements[{i}].label")

    if sugya.get("topicTags"):
        add("topicTags")

    if sugya.get("conceptRefs"):
        add("conceptRefs")

    return paths


def validate_final_audit(
    module: str,
    daf: str,
    sugya: Dict[str, Any],
    current_source: str,
    current_semantic: str,
    final_audit: Any,
    first: Any,
    second: Any,
) -> list[str]:
    """Mechanically validate a finalAudit block against the live candidate.

    Returns a list of problems; empty means the final audit is acceptable.
    This never judges Talmudic correctness -- it enforces that the audit is
    complete (every expected path present, no ambiguous duplicates),
    fingerprint-fresh, boundary-checked against the live raw source, and
    that every source-support claim actually falls inside its authorized
    range unless explicitly marked a cross-reference.
    """
    problems: list[str] = []
    if not isinstance(final_audit, dict):
        return ["finalAudit must be an object"]

    if not isinstance(final_audit.get("reviewId"), str) or not final_audit["reviewId"].strip():
        problems.append("finalAudit.reviewId must be a nonblank string")

    auditor_context = final_audit.get("auditorContextId")
    if not isinstance(auditor_context, str) or not auditor_context.strip():
        problems.append("finalAudit.auditorContextId must be a nonblank string naming a genuinely distinct reviewer/session/context")
    elif isinstance(first, dict) and auditor_context == first.get("reviewerContextId"):
        problems.append("finalAudit.auditorContextId must differ from firstPass.reviewerContextId")

    if final_audit.get("auditedSourceFingerprint") != current_source:
        problems.append("finalAudit.auditedSourceFingerprint differs from the current candidate (stale final audit)")
    if final_audit.get("auditedSemanticFingerprint") != current_semantic:
        problems.append("finalAudit.auditedSemanticFingerprint differs from the current candidate (stale final audit)")

    expected_paths = set(enumerate_semantic_paths(sugya))
    inventory = final_audit.get("fieldInventory")
    if not isinstance(inventory, list) or not inventory:
        problems.append("finalAudit.fieldInventory must be a nonempty array")
        inventory = []

    lr = sugya.get("lineRange") or {}
    lr_start = lr.get("startVilnaLine")
    lr_end = lr.get("endVilnaLine")
    seen_paths: list[str] = []
    for entry in inventory:
        if not isinstance(entry, dict):
            problems.append("finalAudit.fieldInventory entry must be an object")
            continue
        path = entry.get("path")
        if not isinstance(path, str) or not path.strip():
            problems.append("finalAudit.fieldInventory entry missing nonblank path")
            continue
        seen_paths.append(path)

        verdict = entry.get("verdict")
        if verdict not in FIELD_VERDICTS:
            problems.append(f"{path}: illegal fieldInventory verdict {verdict!r}")
            continue
        if verdict in ("REPAIR_REQUIRED", "BLOCKED"):
            problems.append(f"{path}: fieldInventory verdict {verdict} means this record is not ready to certify; repair and produce a fresh final audit")
            continue

        boundary_safe_declared = entry.get("boundarySafe")
        if not isinstance(boundary_safe_declared, bool):
            problems.append(f"{path}: fieldInventory.boundarySafe must be true or false")
            continue
        cross_ref = entry.get("crossReference")
        if not isinstance(cross_ref, bool):
            problems.append(f"{path}: fieldInventory.crossReference must be true or false")
            cross_ref = False

        if verdict == "NONFACTUAL":
            if boundary_safe_declared is not True:
                problems.append(f"{path}: NONFACTUAL entries must declare boundarySafe true (no factual claim to be unsafe)")
            continue

        # SUPPORTED: a factual/interpretive claim. Its supporting lines must
        # be real and, unless explicitly a cross-reference, must fall inside
        # this sugya's own authorized range (or anywhere on the current daf
        # for the shared dafSummary claim). This is the mechanical form of
        # "a claim may not use the following daf as source support."
        lines = entry.get("supportingLines")
        if not isinstance(lines, list) or not lines:
            problems.append(f"{path}: SUPPORTED verdict requires a nonempty supportingLines array")
            continue
        computed_safe = True
        for item in lines:
            if not isinstance(item, dict):
                computed_safe = False
                continue
            item_daf = item.get("daf")
            start = item.get("startVilnaLine")
            end = item.get("endVilnaLine")
            if (
                not isinstance(item_daf, str) or not item_daf.strip()
                or not isinstance(start, int) or not isinstance(end, int)
                or start < 1 or end < start
            ):
                computed_safe = False
                continue
            if cross_ref:
                continue
            if item_daf != daf:
                computed_safe = False
                continue
            if path == "dafSummary":
                continue
            if lr_start is None or lr_end is None or not (lr_start <= start and end <= lr_end):
                computed_safe = False
        if boundary_safe_declared != computed_safe:
            problems.append(
                f"{path}: declared boundarySafe={boundary_safe_declared} does not match the mechanically "
                f"verified source-support range check (expected {computed_safe})"
            )
        if not computed_safe:
            problems.append(f"{path}: source-support line(s) fall outside the authorized daf/sugya range and are not marked crossReference")

    if len(seen_paths) != len(set(seen_paths)):
        problems.append("finalAudit.fieldInventory has duplicate/ambiguous path entries")
    missing = expected_paths - set(seen_paths)
    if missing:
        problems.append(f"finalAudit.fieldInventory omits {len(missing)} expected path(s): {sorted(missing)}")

    # Physical daf-boundary contract.
    raw_lines: list[str] = []
    raw_path = raw_dir(module) / f"{daf}.json"
    if raw_path.exists():
        raw_lines = json.loads(raw_path.read_text(encoding="utf-8")).get("lines") or []
    else:
        problems.append(f"missing authoritative talmuddev source for {daf}: {raw_path}")

    db = final_audit.get("dafBoundary")
    end_state = None
    if not isinstance(db, dict):
        problems.append("finalAudit.dafBoundary must be an object")
    else:
        if db.get("rawLineCount") != len(raw_lines):
            problems.append("finalAudit.dafBoundary.rawLineCount does not match the live raw source line count")
        if not raw_lines or db.get("finalRawLine") != raw_lines[-1]:
            problems.append("finalAudit.dafBoundary.finalRawLine does not match the live raw source's actual final line")
        end_state = db.get("dafEndState")
        if end_state not in DAF_END_STATES:
            problems.append(f"finalAudit.dafBoundary.dafEndState is not a recognized value: {end_state!r}")

    if end_state and end_state != "COMPLETE":
        sweep = final_audit.get("openEndingFieldSweep")
        if not isinstance(sweep, list) or not sweep:
            problems.append(f"dafEndState {end_state} requires a nonempty openEndingFieldSweep covering every field path")
        else:
            sweep_paths: set[str] = set()
            for entry in sweep:
                if not isinstance(entry, dict):
                    problems.append("openEndingFieldSweep entry must be an object")
                    continue
                p = entry.get("path")
                if isinstance(p, str):
                    sweep_paths.add(p)
                imports_next = entry.get("importsNextDafConclusion")
                if not isinstance(imports_next, bool):
                    problems.append(f"openEndingFieldSweep[{p!r}] missing boolean importsNextDafConclusion")
                elif imports_next is True:
                    problems.append(f"openEndingFieldSweep flags {p!r} as importing the next daf's conclusion; repair before certifying")
            missing_sweep = expected_paths - sweep_paths
            if missing_sweep:
                problems.append(f"openEndingFieldSweep omits {len(missing_sweep)} expected path(s): {sorted(missing_sweep)}")

    # Post-repair stale-content sweep, required unconditionally.
    sweep2 = final_audit.get("staleContentSweep")
    if not isinstance(sweep2, dict) or not isinstance(sweep2.get("entries"), list):
        problems.append("finalAudit.staleContentSweep.entries must be an array")
    else:
        by_cat: Dict[str, Any] = {}
        for entry in sweep2["entries"]:
            if isinstance(entry, dict) and isinstance(entry.get("category"), str):
                by_cat[entry["category"]] = entry
        missing_cats = set(STALE_SWEEP_CATEGORIES) - set(by_cat)
        if missing_cats:
            problems.append(f"finalAudit.staleContentSweep missing categories: {sorted(missing_cats)}")
        for cat, entry in by_cat.items():
            found = entry.get("found")
            if not isinstance(found, bool):
                problems.append(f"staleContentSweep[{cat}] missing boolean found")
            elif found is True:
                problems.append(f"staleContentSweep[{cat}] reports an unresolved stale finding; repair before certifying")

    return problems


def certificate_status(module: str, daf: str, daf_doc: Dict[str, Any], sugya: Dict[str, Any], record: Any) -> Tuple[str, list[str]]:
    sid = sugya.get("id", "<no-id>")
    if record is None:
        return "UNCERTIFIED", ["no semantic certification record"]
    if not isinstance(record, dict):
        return "INVALID", ["record is not an object"]

    problems: list[str] = []
    state = record.get("state")
    if state not in CERT_STATES:
        return "INVALID", [f"illegal state {state!r}"]
    if record.get("daf") != daf:
        problems.append(f"record daf {record.get('daf')!r} does not match corpus daf {daf!r}")
    if record.get("sugyaId", sid) != sid:
        problems.append(f"record sugyaId {record.get('sugyaId')!r} does not match {sid!r}")

    current_source, current_semantic = fingerprints(module, daf, daf_doc, sugya)
    first = record.get("firstPass")
    second = record.get("secondPass")

    # Non-certified states still need enough valid state to route the autonomous
    # queue safely. Historical findings with no reviewed fingerprints are kept as
    # evidence but become INVALID, which routes them back through a fresh AUDIT.
    if state == "REPAIR_REQUIRED":
        problems.extend(validate_review_block(first, "firstPass"))
        if isinstance(first, dict) and first.get("verdict") != "REPAIR_REQUIRED":
            problems.append("REPAIR_REQUIRED state requires firstPass.verdict REPAIR_REQUIRED")
        if isinstance(first, dict):
            if first.get("reviewedSourceFingerprint") != current_source:
                problems.append("REPAIR_REQUIRED firstPass source fingerprint is stale")
            if first.get("reviewedSemanticFingerprint") != current_semantic:
                problems.append("REPAIR_REQUIRED firstPass semantic fingerprint is stale")
        return ("REPAIR_REQUIRED" if not problems else "INVALID"), problems

    if state == "REPAIRED_PENDING_REVIEW":
        problems.extend(validate_review_block(first, "firstPass"))
        if isinstance(first, dict) and first.get("verdict") not in {"VERIFIED", "REPAIR_REQUIRED"}:
            problems.append("pending review requires firstPass verdict VERIFIED or REPAIR_REQUIRED")
        if isinstance(first, dict) and first.get("verdict") == "VERIFIED":
            if first.get("reviewedSourceFingerprint") != current_source:
                problems.append("VERIFIED firstPass source fingerprint is stale before second pass")
            if first.get("reviewedSemanticFingerprint") != current_semantic:
                problems.append("VERIFIED firstPass semantic fingerprint is stale before second pass")
        if isinstance(first, dict) and first.get("verdict") == "REPAIR_REQUIRED":
            if not isinstance(record.get("repairRef"), str) or not record["repairRef"].strip():
                problems.append("repaired pending review requires nonblank repairRef")
            if first.get("reviewedSourceFingerprint") == current_source and first.get("reviewedSemanticFingerprint") == current_semantic:
                problems.append("repaired pending review has no source/semantic delta from known-bad first pass")
        return ("REPAIRED_PENDING_REVIEW" if not problems else "INVALID"), problems

    if state == "BLOCKED":
        # BLOCKED intentionally remains a hard stop. It may originate in either
        # pass, but at least one fingerprint-bound review block must explain it.
        blocks = []
        if isinstance(first, dict):
            blocks.append((first, "firstPass"))
        if isinstance(second, dict):
            blocks.append((second, "secondPass"))
        if not blocks:
            problems.append("BLOCKED state requires a review block")
        for block, name in blocks:
            problems.extend(validate_review_block(block, name))
        return ("BLOCKED" if not problems else "INVALID"), problems

    if state == "PENDING_FINAL_AUDIT":
        # Schema 2.0: both source-first passes are done and the second pass
        # CONFIRMED the exact candidate now on record, but the mandatory
        # fingerprint-bound final whole-record audit has not been performed
        # yet. This state exists so the final audit is provably performed
        # AFTER the candidate is finalized, never folded into the same pass
        # that produced it.
        problems.extend(validate_review_block(first, "firstPass"))
        problems.extend(validate_review_block(second, "secondPass"))
        if isinstance(second, dict) and second.get("verdict") != "CONFIRMED":
            problems.append("PENDING_FINAL_AUDIT requires secondPass.verdict CONFIRMED")
        if isinstance(first, dict) and isinstance(second, dict):
            if first.get("reviewId") and first.get("reviewId") == second.get("reviewId"):
                problems.append("firstPass and secondPass must have different reviewId values")
            if first.get("reviewerContextId") and first.get("reviewerContextId") == second.get("reviewerContextId"):
                problems.append("firstPass and secondPass must run in genuinely different reviewer contexts (reviewerContextId)")
        if record.get("sourceFingerprint") != current_source or record.get("semanticFingerprint") != current_semantic:
            problems.append("PENDING_FINAL_AUDIT candidate fingerprints are stale; re-run the second pass against current content before the final audit")
        return ("PENDING_FINAL_AUDIT" if not problems else "INVALID"), problems

    if state == "REVALIDATION_REQUIRED":
        # Produced only by the one-time schema-1.0 -> schema-2.0 migration
        # (scripts/migrate_certification_schema_v2.py). A record in this
        # state NEVER reads as CERTIFIED, regardless of fingerprint
        # freshness: it explicitly means "was certified under the old
        # insufficient contract; needs a real schema-2.0 final audit and
        # genuinely independent review before it can certify again." Prior
        # firstPass/secondPass evidence is preserved as historical record
        # but is not re-validated here -- it is inert until a fresh review
        # cycle (via semantic_review_state.py `first`) supersedes it.
        migration = record.get("migration")
        if not isinstance(migration, dict) or migration.get("fromSchemaVersion") != "1.0":
            problems.append("REVALIDATION_REQUIRED record is missing a valid migration provenance block")
        return "REVALIDATION_REQUIRED", problems

    # CERTIFIED
    final_audit = record.get("finalAudit")
    if not isinstance(final_audit, dict):
        # Defense in depth: the normal tooling path (semantic_review_state.py
        # `final-audit`) never writes state=CERTIFIED without a finalAudit
        # block, but a record could reach this shape through hand-editing or
        # stale schema-1.0 data that was never migrated. Either way it must
        # never silently read as fresh schema-2.0 CERTIFIED.
        return "REVALIDATION_REQUIRED", [
            "CERTIFIED record has no schema-2.0 finalAudit; this is either "
            "unmigrated schema-1.0 data or a malformed record, and either way "
            "requires a fresh schema-2.0 final whole-record audit"
        ]

    if record.get("sourceFingerprint") != current_source:
        problems.append("sourceFingerprint is stale")
    if record.get("semanticFingerprint") != current_semantic:
        problems.append("semanticFingerprint is stale")

    problems.extend(validate_review_block(first, "firstPass"))
    problems.extend(validate_review_block(second, "secondPass"))

    if isinstance(first, dict):
        first_verdict = first.get("verdict")
        if first_verdict not in {"VERIFIED", "REPAIR_REQUIRED"}:
            problems.append("firstPass.verdict must be VERIFIED or REPAIR_REQUIRED")
        first_source = first.get("reviewedSourceFingerprint")
        first_semantic = first.get("reviewedSemanticFingerprint")
        if first_verdict == "VERIFIED":
            if first_source != current_source:
                problems.append("firstPass VERIFIED source fingerprint differs from certified candidate")
            if first_semantic != current_semantic:
                problems.append("firstPass VERIFIED semantic fingerprint differs from certified candidate")
        elif first_verdict == "REPAIR_REQUIRED":
            if not isinstance(record.get("repairRef"), str) or not record["repairRef"].strip():
                problems.append("firstPass REPAIR_REQUIRED requires nonblank repairRef before certification")
            if first_source == current_source and first_semantic == current_semantic:
                problems.append("firstPass REPAIR_REQUIRED but certified candidate has no source/semantic repair delta")

    if isinstance(second, dict):
        if second.get("verdict") != "CONFIRMED":
            problems.append("secondPass.verdict must be CONFIRMED")
        if second.get("reviewedSourceFingerprint") != current_source:
            problems.append("secondPass source fingerprint differs from certified candidate")
        if second.get("reviewedSemanticFingerprint") != current_semantic:
            problems.append("secondPass semantic fingerprint differs from certified candidate")

    if isinstance(first, dict) and isinstance(second, dict):
        if first.get("reviewId") and first.get("reviewId") == second.get("reviewId"):
            problems.append("firstPass and secondPass must have different reviewId values")
        if first.get("reviewerContextId") and first.get("reviewerContextId") == second.get("reviewerContextId"):
            problems.append("firstPass and secondPass must run in genuinely different reviewer contexts (reviewerContextId)")

    if not isinstance(record.get("certifiedAtCommit"), str) or not record["certifiedAtCommit"].strip():
        problems.append("certifiedAtCommit must be a nonblank commit sha/ref")

    problems.extend(validate_final_audit(module, daf, sugya, current_source, current_semantic, final_audit, first, second))

    return ("CERTIFIED" if not problems else "STALE"), problems


def corpus_status(module: str) -> Tuple[Dict[str, int], Dict[str, Dict[str, Any]]]:
    registry = load_registry(module)
    corpus = load_corpus(module)
    counts: Dict[str, int] = {}
    details: Dict[str, Dict[str, Any]] = {}
    for sid, (daf, doc, sugya) in corpus.items():
        effective, problems = certificate_status(module, daf, doc, sugya, registry["records"].get(sid))
        counts[effective] = counts.get(effective, 0) + 1
        details[sid] = {"daf": daf, "state": effective, "problems": problems}
    orphaned = sorted(set(registry["records"]) - set(corpus))
    if orphaned:
        counts["ORPHANED_RECORD"] = len(orphaned)
        for sid in orphaned:
            details[sid] = {"daf": registry["records"][sid].get("daf"), "state": "ORPHANED_RECORD", "problems": ["record has no corpus sugya"]}
    return counts, details


def make_pending_final_audit_record(module: str, daf: str, daf_doc: Dict[str, Any], sugya: Dict[str, Any], first_pass: Dict[str, Any], second_pass: Dict[str, Any], repair_ref: str | None = None) -> Dict[str, Any]:
    """Build a PENDING_FINAL_AUDIT record: both source-first passes are done
    and locked to the current candidate, awaiting the mandatory schema-2.0
    final whole-record audit (see validate_final_audit / make_certified_record)."""
    source_fp, semantic_fp = fingerprints(module, daf, daf_doc, sugya)
    out = {
        "sugyaId": sugya["id"],
        "daf": daf,
        "state": "PENDING_FINAL_AUDIT",
        "sourceFingerprint": source_fp,
        "semanticFingerprint": semantic_fp,
        "firstPass": first_pass,
        "secondPass": second_pass,
    }
    if repair_ref is not None:
        out["repairRef"] = repair_ref
    return out


def make_certified_record(module: str, daf: str, daf_doc: Dict[str, Any], sugya: Dict[str, Any], first_pass: Dict[str, Any], second_pass: Dict[str, Any], final_audit: Dict[str, Any], certified_at_commit: str, repair_ref: str | None = None) -> Dict[str, Any]:
    """Build a full CERTIFIED record in one call (schema 2.0 requires all
    three: firstPass, secondPass, and the fingerprint-bound finalAudit).

    The real campaign workflow goes through the two-step
    make_pending_final_audit_record -> semantic_review_state.py `final-audit`
    path so the final audit is provably performed after the candidate is
    finalized; this single-call form exists for tests and tooling that need
    a complete valid record directly.
    """
    source_fp, semantic_fp = fingerprints(module, daf, daf_doc, sugya)
    out = {
        "sugyaId": sugya["id"],
        "daf": daf,
        "state": "CERTIFIED",
        "sourceFingerprint": source_fp,
        "semanticFingerprint": semantic_fp,
        "firstPass": first_pass,
        "secondPass": second_pass,
        "finalAudit": final_audit,
        "certifiedAtCommit": certified_at_commit,
    }
    if repair_ref is not None:
        out["repairRef"] = repair_ref
    return out
