#!/usr/bin/env python3
"""Core primitives for source-first semantic certification.

This module deliberately does not decide whether Talmudic analysis is correct.
It makes semantic review durable and self-invalidating:

- sourceFingerprint binds a review to the exact Hebrew source range and source map
- semanticFingerprint binds it to every learner-facing semantic field
- each review pass records the exact source/semantic fingerprints it reviewed
- CERTIFIED requires two source-first review passes with different review ids
- a first pass that found REPAIR_REQUIRED cannot certify until a real payload
  change is proven and a repairRef is recorded
- incomplete historical findings are INVALID until re-read through the current
  fingerprint-bound review process
- any later source or semantic edit makes the certificate STALE automatically
- legacy review:"reviewed" metadata is never treated as certification

The semantic reviewer, not this program, decides meaning. The program makes it
impossible for that human-style judgment to be silently reused after the data
it certified has changed.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

REPO = Path(__file__).resolve().parent.parent
CERT_SCHEMA_VERSION = "1.0"
CERT_STATES = {
    "REPAIR_REQUIRED",
    "REPAIRED_PENDING_REVIEW",
    "CERTIFIED",
    "BLOCKED",
}

SOURCE_KEYS = {"id", "sugyaNumber", "lineRange", "lines", "sefariaRefs", "canonicalRef", "daf"}
NON_SEMANTIC_KEYS = SOURCE_KEYS | {"review"}


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

    # CERTIFIED
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

    if isinstance(first, dict) and isinstance(second, dict) and first.get("reviewId") and first.get("reviewId") == second.get("reviewId"):
        problems.append("firstPass and secondPass must have different reviewId values")
    if not isinstance(record.get("certifiedAtCommit"), str) or not record["certifiedAtCommit"].strip():
        problems.append("certifiedAtCommit must be a nonblank commit sha/ref")

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


def make_certified_record(module: str, daf: str, daf_doc: Dict[str, Any], sugya: Dict[str, Any], first_pass: Dict[str, Any], second_pass: Dict[str, Any], certified_at_commit: str, repair_ref: str | None = None) -> Dict[str, Any]:
    source_fp, semantic_fp = fingerprints(module, daf, daf_doc, sugya)
    out = {
        "sugyaId": sugya["id"],
        "daf": daf,
        "state": "CERTIFIED",
        "sourceFingerprint": source_fp,
        "semanticFingerprint": semantic_fp,
        "firstPass": first_pass,
        "secondPass": second_pass,
        "certifiedAtCommit": certified_at_commit,
    }
    if repair_ref is not None:
        out["repairRef"] = repair_ref
    return out
