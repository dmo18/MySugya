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
  field/leaf actually present in the record. enumerate_semantic_paths()
  RECURSES the entire payload (daf summary, daf glossary, every authored
  sugya field) rather than naming fields by hand, so a new or legacy field
  is caught automatically. Each path is classified SEMANTIC (authored prose/
  claims; must be SUPPORTED, REPAIR_REQUIRED, or BLOCKED -- NONFACTUAL is
  illegal) or STRUCTURAL (identifiers/coordinates/enums/slugs; may be
  NONFACTUAL) by a fixed, reviewer-independent allowlist
  (STRUCTURAL_LEAF_KEYS/STRUCTURAL_SCALAR_ARRAY_KEYS); a SUPPORTED claim's
  source-support lines must fall inside the sugya's own authorized range (or
  the current daf for the shared daf summary/glossary) unless the path is
  both SEMANTIC-cross-reference-eligible (CROSS_REFERENCE_ALLOWED_SEMANTIC_TOP_KEYS)
  or STRUCTURAL, AND the cited daf/range actually exists.
- `dafBoundary`: a mechanically-checked physical-boundary assessment
  (rawLineCount/finalRawLine verified against the live raw source, plus a
  reviewer-declared dafEndState).
- `boundaryLeakageSweep`: mandatory for EVERY daf regardless of dafEndState
  -- a reviewer's own (possibly mistaken or dishonest) `COMPLETE`
  classification never gates whether this runs. Covers every SEMANTIC path
  with an explicit importsNextDafConclusion:true/false; an open dafEndState
  additionally requires a nonblank justifying `note` per entry.
- `staleContentSweep`: a fixed, mechanically-enumerated checklist of stale-
  content failure modes (see STALE_SWEEP_CATEGORIES), each with an explicit
  found:true/false attestation. Any found:true blocks certification.

The final audit does not, by itself, prove Talmudic correctness -- a
dishonest or careless reviewer can still declare false verdicts for a
SUPPORTED claim, or falsely mark a sweep entry found:false. It closes the
specific gaps that were demonstrated: an "everything was checked" free-text
claim can no longer stand in for a mechanically-enumerated, fingerprint-bound,
range-checked record, and a reviewer can no longer choose NONFACTUAL for
authored prose to dodge that check. Genuine independent review (a real
second reviewer context, not just a second reviewId string) remains
mandatory; see `reviewerContextId`/`auditorContextId` below -- and see there
for the honest limit of what this module can verify about that.
"""
from __future__ import annotations

import functools
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

# Legal verdicts for a single finalAudit.fieldInventory entry. An audit that
# honestly records REPAIR_REQUIRED or BLOCKED for any field proves the
# record is not ready to certify (repair and re-audit instead). Which of the
# remaining verdicts (SUPPORTED / NONFACTUAL / REVIEWED) is legal for a given
# entry depends on its path classification -- see LEGAL_VERDICTS_BY_CLASS.
FIELD_VERDICTS = {"SUPPORTED", "REPAIR_REQUIRED", "BLOCKED", "NONFACTUAL", "REVIEWED"}

# Recognized physical daf-ending classifications for finalAudit.dafBoundary.
# boundaryLeakageSweep is mandatory regardless of which state is declared
# here; anything other than COMPLETE additionally raises its evidentiary
# burden (a required nonblank `note` per swept path).
DAF_END_STATES = {
    "COMPLETE",
    "MID_WORD",
    "MID_SENTENCE",
    "MID_QUESTION",
    "MID_PROOF",
    "MID_ARGUMENT",
    "OTHER_OPEN_CONTINUATION",
}

# Field-path classification for finalAudit.fieldInventory. This is a
# machine-fixed classification, never a reviewer choice (see
# enumerate_semantic_paths): a path's class is entirely determined by its
# position in the schema and, where the schema contract makes the field's
# *value* the actual authority (see below), by that value -- never by
# anything the reviewer supplies in the audit itself.
#
# - STRUCTURAL: identifiers, coordinates -- never authored prose, and
#   verified structural by the schema's own contract, not merely assumed
#   because the corpus is supposed to already conform to it. May legally be
#   NONFACTUAL.
# - SEMANTIC: authored prose/claims about what the source says. Must be
#   SUPPORTED, REPAIR_REQUIRED, or BLOCKED -- NONFACTUAL and REVIEWED are
#   both illegal for a SEMANTIC path.
# - METADATA: authored editorial/pedagogical classification (an
#   argumentFlow step's discourse-move type, a takeaway's kind, a
#   reasoning-pattern category, an overall difficulty rating) that is
#   neither raw prose requiring line support nor a bare identifier. Must be
#   REVIEWED (with a mandatory justifying note), SUPPORTED, REPAIR_REQUIRED,
#   or BLOCKED -- NONFACTUAL is illegal (it IS meaningful content, unlike a
#   STRUCTURAL id/coordinate) and it still participates in the
#   boundaryLeakageSweep (an argumentFlow step's "type" can misrepresent a
#   daf's resolution status just as easily as its "text" can).
#
# This is deliberately exhaustive-by-default: enumerate_semantic_paths
# recurses the ENTIRE semantic payload (daf-level and sugya-level alike),
# and a leaf is only ever classified STRUCTURAL or METADATA if it matches
# one of the narrow, explicit rules below. A new field added anywhere in the
# schema, including one that happens to share a key name with an existing
# rule (e.g. a hypothetical future "type" field the rules below don't name),
# defaults to SEMANTIC -- the strictest, fully-audited bucket. Classification
# can only ever narrow the audited set for fields it explicitly names; it
# never silently exempts something new by key-name coincidence.
#
# No "pedagogical prompt" exemption is defined for prose. display.hint and
# learning.learnerQuestion look like prompts/questions rather than
# assertions, but shared/schema_map.js is explicit that both must still be
# "independently supported by the declared source range" -- a fabricated or
# out-of-scope question is still a defect. Every prose field is SEMANTIC.
STRUCTURAL_LEAF_KEYS = {
    "id",                 # stable identifiers (argumentFlow step id, etc.)
    "sourceType",          # controlled vocabulary (gemara/mishnah/unknown)
    "refType",             # controlled vocabulary (sourceRefs discriminator)
    "lineId",              # structural line-id pointer
    "targetLineId",        # structural cross-daf line-id pointer
    "targetDaf",           # structural cross-daf daf pointer
    "vilnaLine",           # structural line-number coordinate
    "startVilnaLine",      # structural line-number coordinate
    "endVilnaLine",        # structural line-number coordinate
    "targetVilnaLine",     # structural line-number coordinate
    "priority",            # numeric ranking, not prose
    "correctedByStepId",   # structural pointer
    "image",               # derived .webp filename, not authored prose
}

# Exact/pattern paths classified METADATA (see above). Deliberately PATH-
# based, not key-name-based: "type"/"category"/"difficulty" are NOT globally
# structural key names (a future unrelated field happening to be named
# "type" defaults to SEMANTIC, the strict bucket, until someone reviews and
# explicitly classifies it here or elsewhere).
METADATA_EXACT_PATHS = {"difficulty"}
METADATA_PATH_PATTERNS = (
    re.compile(r"^argumentFlow\[[^\]]+\]\.type$"),
    re.compile(r"^learning\.takeaway\.type$"),
    re.compile(r"^learning\.reasoningPattern\.category$"),
    re.compile(r"^visualizableElements\[\d+\]\.type$"),
    re.compile(r"^quizSeeds\[\d+\]\.type$"),
)

# Legal verdicts per path classification. NONFACTUAL is legal ONLY for
# STRUCTURAL; REVIEWED is legal ONLY for METADATA; SEMANTIC gets neither
# shortcut. SUPPORTED/REPAIR_REQUIRED/BLOCKED remain legal everywhere (a
# reviewer may always choose to support even a structural/metadata field
# with real lines instead).
LEGAL_VERDICTS_BY_CLASS = {
    "SEMANTIC": {"SUPPORTED", "REPAIR_REQUIRED", "BLOCKED"},
    "STRUCTURAL": {"SUPPORTED", "REPAIR_REQUIRED", "BLOCKED", "NONFACTUAL"},
    "METADATA": {"SUPPORTED", "REPAIR_REQUIRED", "BLOCKED", "REVIEWED"},
}

# Keys whose SCALAR array elements are claimed to be sugya-id references.
# STRUCTURAL only when the value actually resolves to a real sugya id in the
# live corpus (see _known_sugya_ids) -- never merely because it sits under
# one of these container keys. Legacy prose left over from before the
# requiresUnderstanding/prerequisiteKnowledge split (a real, current example:
# Yoma 7a's requiresUnderstanding still holds full sentences, not ids) must
# not escape SEMANTIC review just because of its container.
SUGYA_ID_REFERENCE_ARRAY_KEYS = {"requiresUnderstanding", "relatedSugyot"}

# Keys whose SCALAR array elements are claimed to be normalized ASCII slugs.
# STRUCTURAL only when the value actually matches the slug shape the schema
# contract requires (validate_enrichment_contracts.py enforces the same
# shape for topicTags) -- never merely because of the container key.
SLUG_REFERENCE_ARRAY_KEYS = {"topicTags", "conceptRefs"}
_SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def _looks_like_slug(value: Any) -> bool:
    return isinstance(value, str) and bool(_SLUG_RE.fullmatch(value))


@functools.lru_cache(maxsize=None)
def _known_sugya_ids(module: str) -> frozenset:
    """The full set of real sugya ids in the live corpus, cached per process
    (the corpus does not change mid-run). Used only to test whether a
    requiresUnderstanding/relatedSugyot scalar value actually resolves to a
    real sugya -- the one mechanical way to tell a genuine id reference
    apart from legacy prose sitting in the same field."""
    return frozenset(load_corpus(module).keys())


# Paths whose top-level key may legally set fieldInventory.crossReference on
# a SEMANTIC-class SUPPORTED entry, i.e. cite a DIFFERENT daf as support. Any
# other SEMANTIC path describes what THIS sugya/daf says and must be
# supported by lines on its own daf -- "it is true on 8a" never justifies
# stating it as established on 7b. STRUCTURAL-class paths (e.g. a
# sourceRefs crossDaf pointer, already individually validated by
# validate_source_refs.py) are not restricted by this set at all.
CROSS_REFERENCE_ALLOWED_SEMANTIC_TOP_KEYS = {"relatedSugyot"}

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


# Daf-level keys that are never authored semantic content: identity/
# structural fields (daf, canonicalRef), the sugyot container (walked
# separately, per sugya), review metadata, and the Rashi/source layers
# (governed by their own dedicated system, never by semantic certification).
# Every OTHER daf-level key is authored semantic content by default -- this
# mirrors NON_SEMANTIC_KEYS's role for the sugya level: a narrow exclusion
# list, not an inclusion allowlist, so a new daf-level field (anything other
# than summary/glossary) is automatically part of the semantic fingerprint
# and the audited inventory without code changes.
DAF_LEVEL_NON_SEMANTIC_KEYS = {"daf", "canonicalRef", "sugyot", "review", "rashiLines", "rashiTranslations"}


def semantic_payload(daf_doc: Dict[str, Any], sugya: Dict[str, Any]) -> Dict[str, Any]:
    authored = {k: v for k, v in sugya.items() if k not in NON_SEMANTIC_KEYS}
    daf_level_authored = {k: v for k, v in daf_doc.items() if k not in DAF_LEVEL_NON_SEMANTIC_KEYS}
    return {
        # Daf-level authored semantic content: at minimum the summary and
        # glossary, but exhaustively whatever else DAF_LEVEL_NON_SEMANTIC_KEYS
        # does not exclude. A stale glossary entry left behind by a one-daf
        # semantic repair is a real defect (found during the campaign on 9a),
        # not a theoretical gap, and this is not limited to the two fields
        # known today. Any change here invalidates every sugya certificate on
        # the daf, exactly like the summary always did.
        "dafLevel": daf_level_authored,
        "sugya": authored,
    }


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


def _classify_leaf(path: str, container_key: str) -> str:
    """Classify a single leaf value at `path` (whose immediate dict key or
    array container is `container_key`). Path-based rules (METADATA) are
    checked first since they are more specific than the generic key-name
    rule (STRUCTURAL_LEAF_KEYS); a path not matched by anything defaults to
    SEMANTIC, the strict/audited bucket."""
    if path in METADATA_EXACT_PATHS or any(p.match(path) for p in METADATA_PATH_PATTERNS):
        return "METADATA"
    if container_key in STRUCTURAL_LEAF_KEYS:
        return "STRUCTURAL"
    return "SEMANTIC"


def _classify_scalar_array_element(container_key: str, value: Any, known_sugya_ids: frozenset) -> str:
    """Classify a bare scalar list element. Never structural merely because
    of its container key: a requiresUnderstanding/relatedSugyot value is
    STRUCTURAL only if it actually resolves to a real sugya id in the live
    corpus, and a topicTags/conceptRefs value only if it actually matches
    the required slug shape. Anything else -- including legacy prose left
    in requiresUnderstanding from before the prerequisiteKnowledge split --
    defaults to SEMANTIC and must be reviewed and source-supported."""
    if container_key in SUGYA_ID_REFERENCE_ARRAY_KEYS:
        return "STRUCTURAL" if isinstance(value, str) and value in known_sugya_ids else "SEMANTIC"
    if container_key in SLUG_REFERENCE_ARRAY_KEYS:
        return "STRUCTURAL" if _looks_like_slug(value) else "SEMANTIC"
    return "SEMANTIC"


def _walk_semantic_value(value: Any, prefix: str, container_key: str, out: List[Tuple[str, str]], known_sugya_ids: frozenset) -> None:
    """Recursively enumerate leaf paths under `value`, classifying each as
    SEMANTIC, STRUCTURAL, or METADATA. See the classification constants
    above and _classify_leaf/_classify_scalar_array_element.

    `container_key` is the key of the dict/list `value` itself lives under
    (used only when `value` turns out to be a leaf or a list of scalars);
    recursing into a dict always re-derives classification from ITS OWN keys,
    so container_key passed into a dict call is inert -- nothing here lets a
    field "inherit" a structural classification from an enclosing container.
    """
    if isinstance(value, dict):
        for k in sorted(value.keys()):
            v = value[k]
            child_prefix = f"{prefix}.{k}" if prefix else k
            _walk_semantic_value(v, child_prefix, k, out, known_sugya_ids)
        return
    if isinstance(value, list):
        for i, item in enumerate(value):
            if isinstance(item, (dict, list)):
                if isinstance(item, dict) and isinstance(item.get("id"), str) and item.get("id"):
                    key = item["id"]
                else:
                    key = str(i)
                _walk_semantic_value(item, f"{prefix}[{key}]", container_key, out, known_sugya_ids)
            else:
                if item is None or item == "":
                    continue
                cls = _classify_scalar_array_element(container_key, item, known_sugya_ids)
                out.append((f"{prefix}[{i}]", cls))
        return
    if value is None or value == "":
        return
    out.append((prefix, _classify_leaf(prefix, container_key)))


def enumerate_semantic_paths(module: str, daf_doc: Dict[str, Any], sugya: Dict[str, Any]) -> List[Tuple[str, str]]:
    """Machine-enumerate every semantically authored field/leaf actually
    present in a finished daf/sugya record, for finalAudit.fieldInventory,
    each tagged (path, classification).

    This recurses the ENTIRE semantic payload (semantic_payload's dafLevel
    -- summary, glossary, and any other daf-level field -- and every
    authored sugya field) rather than naming fields by hand, so a new or
    legacy semantic field automatically appears in the audit inventory
    without any change to this function. Classification is narrow and, for
    the fields where the schema contract makes the VALUE the actual
    authority (requiresUnderstanding/relatedSugyot ids, topicTags/conceptRefs
    slugs), value-aware: a field is never STRUCTURAL merely because the
    corpus is assumed to already conform to its ideal shape. Only fields
    with real content are included: an optional field left empty carries no
    claim and needs no audit entry. Paths use stable ids (argumentFlow step
    ids, etc.) where present and 0-based indices otherwise; array
    identity/order is already part of the semantic fingerprint, so a
    reordering invalidates any prior audit regardless of path naming.
    """
    known_sugya_ids = _known_sugya_ids(module)
    out: List[Tuple[str, str]] = []
    # Boundary/source-ownership fields: excluded from the semantic
    # fingerprint (they belong to sourceFingerprint) but explicitly required
    # in the final audit inventory so boundary correctness is never silently
    # assumed just because the fingerprint machinery didn't flag it.
    out.append(("lineRange", "STRUCTURAL"))
    out.append(("lines", "STRUCTURAL"))

    payload = semantic_payload(daf_doc, sugya)
    daf_level = payload.get("dafLevel") or {}
    for k in sorted(daf_level.keys()):
        _walk_semantic_value(daf_level[k], f"dafLevel.{k}", k, out, known_sugya_ids)
    authored = payload.get("sugya") or {}
    for k in sorted(authored.keys()):
        _walk_semantic_value(authored[k], k, k, out, known_sugya_ids)

    return out


def validate_final_audit(
    module: str,
    daf: str,
    daf_doc: Dict[str, Any],
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
    complete (every expected path present, no ambiguous duplicates, correctly
    classified), fingerprint-fresh, boundary-checked against the live raw
    source, that every SEMANTIC claim actually falls inside its authorized
    range unless explicitly and legitimately marked a cross-reference, and
    that the boundary-leakage sweep ran unconditionally.

    Independence limitation (see docs/semantic-self-heal.md): this function
    can only check that reviewId/reviewerContextId/auditorContextId values
    are mechanically DISTINCT from each other. It cannot cryptographically
    verify that they correspond to genuinely separate execution contexts --
    that provenance guarantee comes from how the values were produced (a
    real separate subagent/session invocation), not from anything this
    validator can inspect. Distinctness here is a necessary, not sufficient,
    condition for real independence.
    """
    problems: list[str] = []
    if not isinstance(final_audit, dict):
        return ["finalAudit must be an object"]

    if not isinstance(final_audit.get("reviewId"), str) or not final_audit["reviewId"].strip():
        problems.append("finalAudit.reviewId must be a nonblank string")
    else:
        if isinstance(first, dict) and final_audit["reviewId"] == first.get("reviewId"):
            problems.append("finalAudit.reviewId must differ from firstPass.reviewId")
        if isinstance(second, dict) and final_audit["reviewId"] == second.get("reviewId"):
            problems.append("finalAudit.reviewId must differ from secondPass.reviewId")

    auditor_context = final_audit.get("auditorContextId")
    if not isinstance(auditor_context, str) or not auditor_context.strip():
        problems.append("finalAudit.auditorContextId must be a nonblank string naming a genuinely distinct reviewer/session/context")
    else:
        if isinstance(first, dict) and auditor_context == first.get("reviewerContextId"):
            problems.append("finalAudit.auditorContextId must differ from firstPass.reviewerContextId")
        if isinstance(second, dict) and auditor_context == second.get("reviewerContextId"):
            problems.append("finalAudit.auditorContextId must differ from secondPass.reviewerContextId")

    if final_audit.get("auditedSourceFingerprint") != current_source:
        problems.append("finalAudit.auditedSourceFingerprint differs from the current candidate (stale final audit)")
    if final_audit.get("auditedSemanticFingerprint") != current_semantic:
        problems.append("finalAudit.auditedSemanticFingerprint differs from the current candidate (stale final audit)")

    expected = dict(enumerate_semantic_paths(module, daf_doc, sugya))
    expected_paths = set(expected)
    # Fields whose meaning can misrepresent the daf's resolution status --
    # SEMANTIC prose, but also METADATA classifications like an argumentFlow
    # step's discourse-move type, which can just as easily assert a false
    # closure as free prose can.
    swept_paths = {p for p, cls in expected.items() if cls in ("SEMANTIC", "METADATA")}
    inventory = final_audit.get("fieldInventory")
    if not isinstance(inventory, list) or not inventory:
        problems.append("finalAudit.fieldInventory must be a nonempty array")
        inventory = []

    lr = sugya.get("lineRange") or {}
    lr_start = lr.get("startVilnaLine")
    lr_end = lr.get("endVilnaLine")
    raw_line_cache: Dict[str, list[str]] = {}

    def raw_lines_for(target_daf: str) -> list[str]:
        if target_daf not in raw_line_cache:
            p = raw_dir(module) / f"{target_daf}.json"
            raw_line_cache[target_daf] = json.loads(p.read_text(encoding="utf-8")).get("lines") or [] if p.exists() else []
        return raw_line_cache[target_daf]

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
        path_class = expected.get(path)
        path_top_key = re.split(r"[.\[]", path, maxsplit=1)[0]

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

        # A reviewer never chooses which verdicts are legal for a path: that
        # is entirely a function of the path's machine classification (see
        # LEGAL_VERDICTS_BY_CLASS). NONFACTUAL is only legal for STRUCTURAL
        # paths and REVIEWED only for METADATA ones -- summaries, display/
        # learning prose, argumentFlow labels/text/speakers, quiz
        # questions/answers, misconceptions, finalRuling, alternateAngles,
        # glossary definitions, visualization descriptions, and relatedSugya
        # reasons are all SEMANTIC and can never take either shortcut. An
        # unrecognized path (not present in the machine-enumerated
        # inventory) gets the strictest legal set, not a permissive default.
        legal_for_class = LEGAL_VERDICTS_BY_CLASS.get(path_class, {"SUPPORTED", "REPAIR_REQUIRED", "BLOCKED"})
        if verdict not in legal_for_class:
            problems.append(
                f"{path}: {verdict} is not a legal verdict for a {path_class or 'unrecognized'} path; "
                f"must be one of {sorted(legal_for_class)}"
            )
            continue

        if verdict == "NONFACTUAL":
            if boundary_safe_declared is not True:
                problems.append(f"{path}: NONFACTUAL entries must declare boundarySafe true (no factual claim to be unsafe)")
            continue

        if verdict == "REVIEWED":
            # METADATA: an editorial/pedagogical classification (argumentFlow
            # step type, takeaway kind, reasoning-pattern category, overall
            # difficulty) rather than free prose or a bare identifier. No
            # source-line pointer is required, but the reviewer must record
            # an explicit justification that the classification is actually
            # consistent with the source -- a bare boolean would be exactly
            # the kind of unfalsifiable "everything checked" claim schema 2.0
            # was built to reject.
            note = entry.get("note")
            if not isinstance(note, str) or not note.strip():
                problems.append(f"{path}: REVIEWED entries require a nonblank note justifying consistency with the source")
            if boundary_safe_declared is not True:
                problems.append(f"{path}: REVIEWED entries must declare boundarySafe true (no source-line-range claim to be unsafe)")
            continue

        # SUPPORTED: a factual/interpretive claim. Its supporting lines must
        # be real and, unless explicitly and legitimately a cross-reference,
        # must fall inside this sugya's own authorized range (or anywhere on
        # the current daf for the shared daf-level claims under `dafLevel.`).
        # This is the mechanical form of "a claim may not use the following
        # daf as source support."
        # Permitted only for a path whose classification is actually known
        # (present in the machine-enumerated `expected` map): STRUCTURAL
        # paths always qualify, SEMANTIC paths only under the fixed
        # top-key allowlist. An unrecognized/fabricated path (not part of
        # the enumerated inventory at all) is never granted crossReference
        # eligibility by default -- it cannot substitute for a real expected
        # path's completeness requirement either way, but this keeps the
        # permission check itself from ever defaulting open.
        cross_ref_permitted = (
            path_class == "STRUCTURAL"
            or (path_class == "SEMANTIC" and path_top_key in CROSS_REFERENCE_ALLOWED_SEMANTIC_TOP_KEYS)
        )
        if cross_ref and not cross_ref_permitted:
            problems.append(
                f"{path}: crossReference is not permitted for this field; local semantic claims about the "
                f"current daf/sugya must be supported by lines on that same daf"
            )

        lines = entry.get("supportingLines")
        if not isinstance(lines, list) or not lines:
            problems.append(f"{path}: SUPPORTED verdict requires a nonempty supportingLines array")
            continue
        effective_cross_ref = cross_ref and cross_ref_permitted
        computed_safe = True
        for item in lines:
            if not isinstance(item, dict):
                computed_safe = False
                continue
            item_daf = item.get("daf")
            start = item.get("startVilnaLine")
            end = item.get("endVilnaLine")
            if (
                not isinstance(item_daf, str) or not re.fullmatch(r"\d+[ab]", item_daf)
                or not isinstance(start, int) or not isinstance(end, int)
                or start < 1 or end < start
            ):
                computed_safe = False
                continue
            if effective_cross_ref:
                # Even a legitimate cross-reference must point at a real daf
                # and a real line range on it -- never trusted blindly. The
                # daf shape is already constrained to \d+[ab] above, so this
                # never resolves a path outside raw_dir(module).
                target_lines = raw_lines_for(item_daf)
                if not target_lines or end > len(target_lines):
                    computed_safe = False
                continue
            if item_daf != daf:
                computed_safe = False
                continue
            if path.startswith("dafLevel."):
                if end > len(raw_lines_for(daf)):
                    computed_safe = False
                continue
            if lr_start is None or lr_end is None or not (lr_start <= start and end <= lr_end):
                computed_safe = False
        if boundary_safe_declared != computed_safe:
            problems.append(
                f"{path}: declared boundarySafe={boundary_safe_declared} does not match the mechanically "
                f"verified source-support range check (expected {computed_safe})"
            )
        if not computed_safe:
            problems.append(f"{path}: source-support line(s) fall outside the authorized daf/sugya range, point at a nonexistent daf/range, or are not legitimately marked crossReference")

    if len(seen_paths) != len(set(seen_paths)):
        problems.append("finalAudit.fieldInventory has duplicate/ambiguous path entries")
    missing = expected_paths - set(seen_paths)
    if missing:
        problems.append(f"finalAudit.fieldInventory omits {len(missing)} expected path(s): {sorted(missing)}")

    # Physical daf-boundary contract.
    raw_lines = raw_lines_for(daf)
    if not raw_lines:
        problems.append(f"missing authoritative talmuddev source for {daf}: {raw_dir(module) / f'{daf}.json'}")

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

    # Boundary-leakage sweep: required for EVERY daf regardless of the
    # reviewer's own dafEndState classification. A mistaken (or dishonest)
    # `COMPLETE` declaration must never be able to skip the exact sweep
    # designed to catch false closure/next-daf leakage; dafEndState is
    # additional evidence, not a gate on whether this check runs. Scoped to
    # SEMANTIC- and METADATA-class paths (a slug or line-number coordinate
    # cannot "assert a resolved conclusion", but an argumentFlow step's type
    # classification can).
    sweep = final_audit.get("boundaryLeakageSweep")
    if not isinstance(sweep, list) or not sweep:
        problems.append("finalAudit.boundaryLeakageSweep must be a nonempty array covering every SEMANTIC/METADATA-class field path, required for every daf regardless of dafEndState")
    else:
        sweep_paths: set[str] = set()
        strict = bool(end_state) and end_state != "COMPLETE"
        for entry in sweep:
            if not isinstance(entry, dict):
                problems.append("boundaryLeakageSweep entry must be an object")
                continue
            p = entry.get("path")
            if isinstance(p, str):
                sweep_paths.add(p)
            imports_next = entry.get("importsNextDafConclusion")
            if not isinstance(imports_next, bool):
                problems.append(f"boundaryLeakageSweep[{p!r}] missing boolean importsNextDafConclusion")
            elif imports_next is True:
                problems.append(f"boundaryLeakageSweep flags {p!r} as importing the next daf's conclusion; repair before certifying")
            if strict:
                note = entry.get("note")
                if not isinstance(note, str) or not note.strip():
                    problems.append(f"boundaryLeakageSweep[{p!r}] requires a nonblank note justifying non-leakage on an open ({end_state}) daf")
        missing_sweep = swept_paths - sweep_paths
        if missing_sweep:
            problems.append(f"boundaryLeakageSweep omits {len(missing_sweep)} SEMANTIC/METADATA-class path(s): {sorted(missing_sweep)}")

    # Post-repair stale-content sweep, required unconditionally. Each
    # required category must appear EXACTLY once: a duplicate (even one
    # where both copies happen to agree) is rejected outright rather than
    # silently collapsed to "whichever entry came last", since silently
    # picking a winner is exactly the kind of ambiguity that could let a
    # dishonest found:true be shadowed by a later found:false for the same
    # category.
    sweep2 = final_audit.get("staleContentSweep")
    if not isinstance(sweep2, dict) or not isinstance(sweep2.get("entries"), list):
        problems.append("finalAudit.staleContentSweep.entries must be an array")
    else:
        cat_counts: Dict[str, int] = {}
        first_entry_by_cat: Dict[str, Any] = {}
        for entry in sweep2["entries"]:
            if not isinstance(entry, dict) or not isinstance(entry.get("category"), str):
                problems.append("staleContentSweep entry must be an object with a string category")
                continue
            cat = entry["category"]
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
            first_entry_by_cat.setdefault(cat, entry)
        duplicate_cats = sorted(c for c, n in cat_counts.items() if n > 1)
        if duplicate_cats:
            problems.append(f"finalAudit.staleContentSweep has duplicate category entries (each required category must appear exactly once): {duplicate_cats}")
        unknown_cats = sorted(set(cat_counts) - set(STALE_SWEEP_CATEGORIES))
        if unknown_cats:
            problems.append(f"finalAudit.staleContentSweep has unrecognized categories: {unknown_cats}")
        missing_cats = set(STALE_SWEEP_CATEGORIES) - set(cat_counts)
        if missing_cats:
            problems.append(f"finalAudit.staleContentSweep missing categories: {sorted(missing_cats)}")
        for cat, entry in first_entry_by_cat.items():
            if cat not in STALE_SWEEP_CATEGORIES:
                continue
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

    problems.extend(validate_final_audit(module, daf, daf_doc, sugya, current_source, current_semantic, final_audit, first, second))

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
