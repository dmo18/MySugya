#!/usr/bin/env python3
"""Deterministic autonomy controller (v2) for MySugya.

Pure state-transition / evidence engine. This module NEVER calls a model
provider, never schedules work, never launches a process, never pushes,
merges, or sends anything, and never self-certifies a work unit. It only
reads and writes its own JSON state file and emits JSON decisions.

Every mutation is fail-closed: malformed, unknown, missing, changed,
stale, absent, colliding, over-budget, out-of-scope, or denied evidence is
rejected with a structured reason instead of silently proceeding. Evidence
is revalidated at the exact transition that consumes it, not merely counted
by type: outcome, freshness, and commit/content binding are rechecked every
time.

Standard library only.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

SCHEMA_VERSION = "2.0.0"

# ---------------------------------------------------------------------------
# Fixed vocabularies
# ---------------------------------------------------------------------------

MODES = (
    "frozen",
    "shadow",
    "canary",
    "limited",
    "full",
    "quarantined",
    "complete",
)

STATES = (
    "queued",
    "admitted",
    "running",
    "awaiting_verification",
    "verified",
    "merged",
    "post_merge_verified",
    "rejected",
    "blocked_operator",
    "blocked_quota",
    "expired",
    "quarantined",
)

# Terminal for the active unit: no transition leaves these within the same
# unit. An operator must author a new work unit to continue.
TERMINAL_STATES = (
    "post_merge_verified",
    "rejected",
    "blocked_operator",
    "blocked_quota",
    "expired",
    "quarantined",
)

# Legal transition graph: from_state -> set(to_state). "running" is
# reachable a second time from awaiting_verification/verified ONLY as the
# one allowed reject-before-correction return (see transition()).
TRANSITIONS: Dict[str, Tuple[str, ...]] = {
    "queued": ("admitted", "rejected", "blocked_operator", "blocked_quota", "expired"),
    "admitted": ("running", "rejected", "blocked_operator", "blocked_quota", "expired"),
    "running": (
        "awaiting_verification",
        "rejected",
        "blocked_operator",
        "blocked_quota",
        "expired",
        "quarantined",
    ),
    "awaiting_verification": (
        "verified",
        "running",
        "rejected",
        "blocked_operator",
        "blocked_quota",
        "expired",
        "quarantined",
    ),
    "verified": ("merged", "running", "rejected", "blocked_operator", "expired", "quarantined"),
    "merged": ("post_merge_verified", "quarantined", "blocked_operator"),
    "post_merge_verified": (),
    "rejected": (),
    "blocked_operator": (),
    "blocked_quota": (),
    "expired": (),
    "quarantined": (),
}

# Evidence component types the controller recognizes.
EVIDENCE_TYPES = (
    "deterministic",
    "semantic",
    "reviewer",
    "quota",
    "merge",
    "post_merge",
    "notification_receipt",
)

# notification_receipt is recorded for audit only; it can never satisfy an
# engineering acceptance requirement.
FORBIDDEN_ACCEPTANCE_TYPES = ("notification_receipt",)

# Transitions that require at least one fresh, currently-valid evidence
# component of the listed types (in addition to whatever the work unit's own
# acceptanceComponents list declares as mandatory for awaiting_verification).
TRANSITION_EVIDENCE_REQUIREMENTS: Dict[str, Tuple[str, ...]] = {
    "admitted": ("quota",),
    "awaiting_verification": (),
    "verified": ("reviewer",),
    "merged": ("merge",),
    "post_merge_verified": ("post_merge",),
}

# Per-type outcome vocabularies and the single outcome value that counts as
# success for consuming a transition requirement. FAIL/DENY/UNKNOWN are
# legal to log, but can never satisfy a transition.
OUTCOME_ENUMS: Dict[str, Tuple[str, ...]] = {
    "deterministic": ("PASS", "FAIL", "UNKNOWN"),
    "semantic": ("PASS", "FAIL", "UNKNOWN"),
    "reviewer": ("APPROVE", "REJECT", "UNKNOWN"),
    "quota": ("ALLOW", "DENY", "UNKNOWN"),
    "merge": ("MERGED", "FAILED", "UNKNOWN"),
    "post_merge": ("PASS", "FAIL", "UNKNOWN"),
    "notification_receipt": ("DELIVERED", "FAILED", "UNKNOWN"),
}

SUCCESS_OUTCOME: Dict[str, str] = {
    "deterministic": "PASS",
    "semantic": "PASS",
    "reviewer": "APPROVE",
    "quota": "ALLOW",
    "merge": "MERGED",
    "post_merge": "PASS",
}

# Evidence types that must be bound to the unit's exact current commit /
# content fingerprint at the moment they are consumed.
FINGERPRINT_BOUND_TYPES = ("deterministic", "semantic", "reviewer", "merge", "post_merge")

# Evidence types that must declare how they were produced.
PROVENANCE_REQUIRED_TYPES = ("deterministic", "semantic", "post_merge")

# Evidence types that must report the exact scope (paths changed, commands
# used) they certify, so it can be checked against the unit's contract.
SCOPE_REQUIRED_TYPES = ("deterministic", "semantic")

# Command registry: the fixed, closed set of command *names* the controller
# is aware of for evidence-provenance purposes. The controller never
# executes these; it only validates that evidence claims to have used a
# known, allowed command rather than an arbitrary shell string.
COMMAND_REGISTRY = {
    "git_status": "report working tree status",
    "git_diff": "report a diff",
    "git_log": "report commit history",
    "run_tests": "run the project test/validator suite",
    "run_validator": "run a named validator script",
    "git_push_branch": "push a short-lived working branch",
    "gh_pr_create": "open a pull request",
    "gh_pr_merge": "merge an eligible pull request",
    "ci_rerun": "rerun/dispatch GitHub Actions for the unit's PR",
}

DEFAULT_STALE_AFTER_SECONDS = 24 * 60 * 60  # 24h
MAX_CORRECTIONS = 1
ANTI_LOOP_CONSECUTIVE_LIMIT = 3

# operator_override is intentionally NOT an approved reopen trigger: an
# operator cannot silently bypass the repair/reconstruct decision or the
# anti-loop rule merely by asserting authority. Reopening must bind to new
# structured evidence.
APPROVED_REOPEN_TRIGGERS = (
    "new_failure_evidence",
    "new_input_evidence",
)

HISTORY_EVENTS = (
    "unit_submitted",
    "transition",
    "unit_closed",
    "repair_decision",
    "commit_recorded",
    "campaign_mode_set",
)


class ControllerError(Exception):
    """Fail-closed error. Always carries a stable machine-readable code."""

    def __init__(self, code: str, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict:
        return {
            "ok": False,
            "errorCode": self.code,
            "message": self.message,
            "details": self.details,
        }


# ---------------------------------------------------------------------------
# Fingerprinting (anti-loop). Deterministic, excludes all free text.
# ---------------------------------------------------------------------------

def structured_fingerprint(payload: dict, include_keys: Tuple[str, ...]) -> str:
    """Hash only the named structured keys, in sorted-key canonical form.

    Any key not in include_keys (e.g. narrative/free-text fields like
    "notes", "summary", "reason") is excluded on purpose so that rewording
    an explanation can never change the fingerprint and no transition can
    be justified by narrative alone.
    """
    narrowed = {k: payload.get(k) for k in sorted(include_keys)}
    canonical = json.dumps(narrowed, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


FAILURE_FINGERPRINT_KEYS = (
    "unitClass",
    "toState",
    "failureCategory",
    "failingComponentType",
    "failingComponentFingerprint",
    "authoritativeInputFingerprint",
)


def failure_fingerprint(unit_class: str, to_state: str, evidence: dict) -> str:
    payload = {
        "unitClass": unit_class,
        "toState": to_state,
        "failureCategory": evidence.get("failureCategory"),
        "failingComponentType": evidence.get("failingComponentType"),
        "failingComponentFingerprint": evidence.get("failingComponentFingerprint"),
        "authoritativeInputFingerprint": evidence.get("authoritativeInputFingerprint"),
    }
    return structured_fingerprint(payload, FAILURE_FINGERPRINT_KEYS)


def contract_fingerprint(product_contract_id: str, campaign_id: str) -> str:
    return hashlib.sha256(
        f"{product_contract_id}:{campaign_id}:{SCHEMA_VERSION}".encode("utf-8")
    ).hexdigest()


# ---------------------------------------------------------------------------
# State file I/O (atomic, optimistic concurrency)
# ---------------------------------------------------------------------------

def _empty_state() -> dict:
    return {
        "schemaVersion": SCHEMA_VERSION,
        "stateVersion": 0,
        "activeUnit": None,
        "history": [],
        "productContractId": None,
        "campaignId": None,
        "contractFingerprint": None,
        "canaryUnitId": None,
        "canaryClass": None,
        "campaignMode": "shadow",
    }


def _validate_state_schema(data: dict) -> None:
    """Fail closed on any malformed, manually-edited, or inconsistent
    historical state: unknown enums, broken append-only history, a
    violated active-unit invariant, or a contract fingerprint that does
    not match its own bound productContractId/campaignId."""
    history = data.get("history")
    if not isinstance(history, list):
        raise ControllerError("MALFORMED_STATE", "history must be a list")
    for entry in history:
        if not isinstance(entry, dict) or "event" not in entry:
            raise ControllerError("MALFORMED_STATE", "history entries must be objects with an event")
        if entry["event"] not in HISTORY_EVENTS:
            raise ControllerError("MALFORMED_STATE", f"unknown history event {entry['event']!r}")
        if entry["event"] == "transition":
            if entry.get("toState") not in STATES or entry.get("fromState") not in STATES:
                raise ControllerError("MALFORMED_STATE", "transition history entry has an unrecognized state")
        if entry["event"] == "unit_closed" and entry.get("finalState") not in TERMINAL_STATES:
            raise ControllerError("MALFORMED_STATE", "unit_closed history entry has a non-terminal finalState")

    campaign_mode = data.get("campaignMode", "shadow")
    if campaign_mode not in MODES:
        raise ControllerError("MALFORMED_STATE", "campaignMode is not recognized")

    active = data.get("activeUnit")
    if active is not None:
        if not isinstance(active, dict) or "status" not in active:
            raise ControllerError("MALFORMED_STATE", "activeUnit missing status")
        if active["status"] not in STATES or active["status"] in TERMINAL_STATES:
            raise ControllerError(
                "MALFORMED_STATE",
                "activeUnit status invariant violated: must be a recognized, non-terminal state",
            )

    contract_fp = data.get("contractFingerprint")
    pc = data.get("productContractId")
    cid = data.get("campaignId")
    if contract_fp is not None:
        if not pc or not cid:
            raise ControllerError("MALFORMED_STATE", "contractFingerprint present without productContractId/campaignId")
        if contract_fingerprint(pc, cid) != contract_fp:
            raise ControllerError("MALFORMED_STATE", "contractFingerprint does not match productContractId/campaignId")
    if active is not None and not contract_fp:
        raise ControllerError("MALFORMED_STATE", "activeUnit present but no product contract/campaign is bound")


def load_state(path: str) -> dict:
    if not os.path.exists(path):
        return _empty_state()
    with open(path, "r", encoding="utf-8") as fh:
        raw = fh.read()
    if not raw.strip():
        return _empty_state()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ControllerError(
            "MALFORMED_STATE", f"state file is not valid JSON: {exc}"
        ) from exc
    if not isinstance(data, dict) or "schemaVersion" not in data or "stateVersion" not in data:
        raise ControllerError("MALFORMED_STATE", "state file missing required top-level keys")
    if data["schemaVersion"] != SCHEMA_VERSION:
        raise ControllerError(
            "SCHEMA_MISMATCH",
            f"state file schemaVersion {data['schemaVersion']!r} != controller {SCHEMA_VERSION!r}",
        )
    _validate_state_schema(data)
    data.setdefault("productContractId", None)
    data.setdefault("campaignId", None)
    data.setdefault("contractFingerprint", None)
    data.setdefault("canaryUnitId", None)
    data.setdefault("canaryClass", None)
    data.setdefault("campaignMode", "shadow")
    return data


def save_state(path: str, state: dict, expected_version: int) -> None:
    """Atomic optimistic-concurrency write.

    Re-reads the file immediately before writing; if stateVersion on disk
    no longer matches expected_version, another process raced us and we
    fail closed rather than silently overwriting.
    """
    current = load_state(path) if os.path.exists(path) else _empty_state()
    if current.get("stateVersion", 0) != expected_version:
        raise ControllerError(
            "CONCURRENT_MODIFICATION",
            "state file changed since it was read; refusing to overwrite",
            {"expected": expected_version, "found": current.get("stateVersion")},
        )
    _validate_state_schema(state)
    state = copy.deepcopy(state)
    state["stateVersion"] = expected_version + 1
    tmp_path = f"{path}.tmp-{uuid.uuid4().hex}"
    with open(tmp_path, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(tmp_path, path)


def bind_contract(state: dict, product_contract_id: str, campaign_id: str, now: Optional[float] = None) -> dict:
    """Bind (or confirm) the product-contract/campaign identity for this
    state file. Immutable once set: rebinding to a different contract or
    campaign fails closed."""
    now = now if now is not None else time.time()
    if not isinstance(product_contract_id, str) or not product_contract_id.strip():
        raise ControllerError("MALFORMED_CONTRACT", "productContractId must be a non-empty string")
    if not isinstance(campaign_id, str) or not campaign_id.strip():
        raise ControllerError("MALFORMED_CONTRACT", "campaignId must be a non-empty string")
    fp = contract_fingerprint(product_contract_id, campaign_id)
    existing_fp = state.get("contractFingerprint")
    if existing_fp is not None and existing_fp != fp:
        raise ControllerError(
            "CONTRACT_MISMATCH",
            "state is already bound to a different product contract/campaign",
            {"existingProductContractId": state.get("productContractId"), "existingCampaignId": state.get("campaignId")},
        )
    state["productContractId"] = product_contract_id
    state["campaignId"] = campaign_id
    state["contractFingerprint"] = fp
    return state


def set_campaign_mode(state: dict, mode: str, now: Optional[float] = None) -> dict:
    """Set the authoritative campaign mode; work units cannot choose it."""
    now = now if now is not None else time.time()
    if mode not in MODES:
        raise ControllerError("UNKNOWN_MODE", f"mode {mode!r} is not recognized")
    state["campaignMode"] = mode
    state["history"].append({"event": "campaign_mode_set", "mode": mode, "at": now})
    return state


def configure_canary(state: dict, unit_id: Optional[str] = None, unit_class: Optional[str] = None) -> dict:
    state["canaryUnitId"] = unit_id
    state["canaryClass"] = unit_class
    return state


# ---------------------------------------------------------------------------
# Work-unit contract validation
# ---------------------------------------------------------------------------

REQUIRED_UNIT_FIELDS = (
    "unitId",
    "unitClass",
    "worktree",
    "baseSha",
    "allowedPaths",
    "allowedCommands",
    "acceptanceComponents",
    "reviewerIdentities",
    "quotaBudget",
)

IMMUTABLE_UNIT_FIELDS = (
    "unitId",
    "unitClass",
    "worktree",
    "baseSha",
    "allowedPaths",
    "allowedCommands",
    "acceptanceComponents",
    "reviewerIdentities",
    "quotaBudget",
    "implementerIdentity",
    "createdAt",
)


def unit_contract_fingerprint(unit: dict) -> str:
    payload = {field: unit.get(field) for field in IMMUTABLE_UNIT_FIELDS}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def validate_new_unit(unit: dict) -> None:
    if not isinstance(unit, dict):
        raise ControllerError("MALFORMED_UNIT", "work unit must be a JSON object")
    if "mode" in unit:
        raise ControllerError("FORBIDDEN_UNIT_FIELD", "work units cannot choose campaign mode")
    missing = [f for f in REQUIRED_UNIT_FIELDS if f not in unit]
    if missing:
        raise ControllerError(
            "MISSING_FIELDS", "work unit missing required fields", {"missing": missing}
        )
    if not isinstance(unit["allowedPaths"], list) or not unit["allowedPaths"]:
        raise ControllerError("MALFORMED_UNIT", "allowedPaths must be a non-empty list")
    if not isinstance(unit["allowedCommands"], list) or not unit["allowedCommands"]:
        raise ControllerError("MALFORMED_UNIT", "allowedCommands must be a non-empty list")
    unknown_commands = [c for c in unit["allowedCommands"] if c not in COMMAND_REGISTRY]
    if unknown_commands:
        raise ControllerError(
            "UNKNOWN_COMMAND",
            "allowedCommands references commands outside the command registry",
            {"unknown": unknown_commands},
        )
    if not isinstance(unit["acceptanceComponents"], list) or not unit["acceptanceComponents"]:
        raise ControllerError("MALFORMED_UNIT", "acceptanceComponents must be a non-empty list")
    unknown_types = [t for t in unit["acceptanceComponents"] if t not in EVIDENCE_TYPES]
    if unknown_types:
        raise ControllerError(
            "UNKNOWN_EVIDENCE_TYPE",
            "acceptanceComponents references unknown evidence types",
            {"unknown": unknown_types},
        )
    forbidden_types = [t for t in unit["acceptanceComponents"] if t in FORBIDDEN_ACCEPTANCE_TYPES]
    if forbidden_types:
        raise ControllerError(
            "FORBIDDEN_ACCEPTANCE_TYPE",
            "acceptanceComponents cannot require types that are not engineering evidence",
            {"forbidden": forbidden_types},
        )
    if not isinstance(unit["reviewerIdentities"], list) or not unit["reviewerIdentities"]:
        raise ControllerError("MALFORMED_UNIT", "reviewerIdentities must be a non-empty list")
    qb = unit["quotaBudget"]
    if (
        not isinstance(qb, dict)
        or "provider" not in qb
        or "accountPoolId" not in qb
        or "remainingPercent" not in qb
        or not isinstance(qb["remainingPercent"], (int, float))
    ):
        raise ControllerError(
            "MALFORMED_UNIT",
            "quotaBudget must declare provider, accountPoolId and numeric remainingPercent",
        )


def validate_evidence(component: dict) -> None:
    if not isinstance(component, dict):
        raise ControllerError("MALFORMED_EVIDENCE", "evidence component must be a JSON object")
    required = ("type", "fingerprint", "submittedAt")
    missing = [f for f in required if f not in component or component[f] in (None, "")]
    if missing:
        raise ControllerError(
            "MISSING_EVIDENCE_FIELDS", "evidence component missing required fields",
            {"missing": missing},
        )
    if component["type"] not in EVIDENCE_TYPES:
        raise ControllerError(
            "UNKNOWN_EVIDENCE_TYPE", f"evidence type {component['type']!r} is not recognized"
        )
    if not isinstance(component["fingerprint"], str) or len(component["fingerprint"]) < 8:
        raise ControllerError("MALFORMED_EVIDENCE", "evidence fingerprint must be a non-trivial string")
    try:
        submitted_at = float(component["submittedAt"])
    except (TypeError, ValueError) as exc:
        raise ControllerError("MALFORMED_EVIDENCE", "submittedAt must be a numeric timestamp") from exc
    stale_after = component.get("staleAfterSeconds", DEFAULT_STALE_AFTER_SECONDS)
    now = component.get("_now", time.time())
    if now - submitted_at > stale_after:
        raise ControllerError(
            "STALE_EVIDENCE",
            "evidence component is older than its staleness window",
            {"submittedAt": submitted_at, "now": now, "staleAfterSeconds": stale_after},
        )

    allowed_outcomes = OUTCOME_ENUMS.get(component["type"])
    outcome = component.get("outcome")
    if allowed_outcomes is not None and outcome not in allowed_outcomes:
        raise ControllerError(
            "UNKNOWN_OUTCOME",
            f"outcome {outcome!r} is not valid for evidence type {component['type']!r}",
            {"allowed": list(allowed_outcomes)},
        )

    if component["type"] in FINGERPRINT_BOUND_TYPES and not component.get("commitFingerprint"):
        raise ControllerError(
            "MISSING_EVIDENCE_FIELDS", f"{component['type']} evidence missing commitFingerprint"
        )

    if component["type"] in PROVENANCE_REQUIRED_TYPES:
        prov = component.get("provenance")
        if prov not in COMMAND_REGISTRY and prov != "ci_pipeline":
            raise ControllerError(
                "UNKNOWN_PROVENANCE",
                f"provenance {prov!r} is not a recognized command or ci_pipeline",
            )

    if component["type"] in SCOPE_REQUIRED_TYPES:
        changed = component.get("changedPaths")
        cmds = component.get("commandsUsed")
        if not isinstance(changed, list) or not changed:
            raise ControllerError(
                "MISSING_SCOPE_REPORT", f"{component['type']} evidence must report changedPaths"
            )
        if not isinstance(cmds, list) or not cmds:
            raise ControllerError(
                "MISSING_SCOPE_REPORT", f"{component['type']} evidence must report commandsUsed"
            )

    if component["type"] == "reviewer":
        if not component.get("reviewerIdentity"):
            raise ControllerError("MISSING_EVIDENCE_FIELDS", "reviewer evidence missing reviewerIdentity")
    if component["type"] == "merge":
        cmd = component.get("commandUsed")
        if cmd not in COMMAND_REGISTRY:
            raise ControllerError(
                "UNKNOWN_COMMAND", "merge evidence references a command outside the registry",
                {"commandUsed": cmd},
            )
    if component["type"] == "notification_receipt":
        if not component.get("receiptId"):
            raise ControllerError(
                "MISSING_EVIDENCE_FIELDS", "notification_receipt evidence missing receiptId"
            )
    if component["type"] == "quota":
        required_quota_fields = ("provider", "accountPoolId", "remainingPercent", "thresholdPercent", "measuredAt")
        missing_q = [f for f in required_quota_fields if component.get(f) in (None, "")]
        if missing_q:
            raise ControllerError(
                "MISSING_EVIDENCE_FIELDS",
                "quota evidence missing required telemetry fields",
                {"missing": missing_q},
            )


def _unit_history(unit: dict) -> List[dict]:
    return unit.setdefault("evidenceLog", [])


def _check_collision(unit: dict, component: dict) -> None:
    for prior in _unit_history(unit):
        if prior["fingerprint"] == component["fingerprint"] and prior["type"] == component["type"]:
            raise ControllerError(
                "DUPLICATE_EVIDENCE",
                "this exact evidence fingerprint was already submitted for this unit/type",
                {"fingerprint": component["fingerprint"], "type": component["type"]},
            )


def _check_contradiction(unit: dict, component: dict) -> None:
    """Fail closed if two components of the same type disagree on outcome
    without superseding each other explicitly."""
    for prior in _unit_history(unit):
        if prior["type"] != component["type"]:
            continue
        if "outcome" in prior and "outcome" in component and prior["outcome"] != component["outcome"]:
            if not component.get("supersedes"):
                raise ControllerError(
                    "CONTRADICTORY_EVIDENCE",
                    "new evidence contradicts prior evidence of the same type without an explicit supersedes link",
                    {"priorOutcome": prior["outcome"], "newOutcome": component["outcome"]},
                )


def _check_quota(unit: dict, component: dict) -> None:
    if component["type"] != "quota":
        return
    remaining = component.get("remainingPercent")
    threshold = component.get("thresholdPercent")
    if not isinstance(remaining, (int, float)) or not isinstance(threshold, (int, float)):
        raise ControllerError("MALFORMED_EVIDENCE", "quota evidence missing numeric remainingPercent/thresholdPercent")
    if remaining < threshold:
        raise ControllerError(
            "QUOTA_INSUFFICIENT",
            "quota evidence reports remaining percent below the configured threshold",
            {"remainingPercent": remaining, "thresholdPercent": threshold},
        )
    budget = unit.get("quotaBudget", {})
    if component.get("provider") != budget.get("provider"):
        raise ControllerError(
            "QUOTA_PROVIDER_MISMATCH",
            "quota evidence provider does not match the unit's declared quotaBudget provider",
            {"evidenceProvider": component.get("provider"), "unitProvider": budget.get("provider")},
        )
    if component.get("accountPoolId") != budget.get("accountPoolId"):
        raise ControllerError(
            "QUOTA_ACCOUNT_POOL_MISMATCH",
            "quota evidence accountPoolId does not match the unit's declared quotaBudget accountPoolId",
            {"evidenceAccountPoolId": component.get("accountPoolId"), "unitAccountPoolId": budget.get("accountPoolId")},
        )


def _check_budget(unit: dict, component: dict) -> None:
    budget = unit.get("quotaBudget", {})
    if component["type"] == "quota" and "costPercent" in component:
        spent = sum(
            e.get("costPercent", 0) for e in _unit_history(unit) if e["type"] == "quota"
        ) + component["costPercent"]
        cap = budget.get("maxSpendPercent")
        if cap is not None and spent > cap:
            raise ControllerError(
                "OVER_BUDGET",
                "cumulative quota spend for this unit exceeds its declared budget cap",
                {"spent": spent, "cap": cap},
            )


def _check_reviewer_allowed(unit: dict, component: dict) -> None:
    if component["type"] != "reviewer":
        return
    identity = component.get("reviewerIdentity")
    if identity not in unit.get("reviewerIdentities", []):
        raise ControllerError(
            "REVIEWER_DENIED",
            "reviewerIdentity is not in the work unit's allowed reviewerIdentities",
            {"reviewerIdentity": identity},
        )
    if identity == unit.get("implementerIdentity"):
        raise ControllerError(
            "REVIEWER_DENIED",
            "reviewer identity must not equal the implementer identity (no self-certification)",
            {"reviewerIdentity": identity},
        )


def _normalize_path(p: str) -> str:
    return p[2:] if p.startswith("./") else p


def _check_scope(unit: dict, component: dict) -> None:
    if component["type"] not in SCOPE_REQUIRED_TYPES:
        return
    changed = component.get("changedPaths", [])
    cmds = component.get("commandsUsed", [])
    allowed_paths = unit.get("allowedPaths", [])
    allowed_commands = unit.get("allowedCommands", [])

    out_of_scope = []
    for p in changed:
        if not isinstance(p, str) or not p or p.startswith("/") or ".." in p.split("/"):
            out_of_scope.append(p)
            continue
        norm = _normalize_path(p)
        if not any(norm.startswith(_normalize_path(a)) for a in allowed_paths):
            out_of_scope.append(p)
    if out_of_scope:
        raise ControllerError(
            "OUT_OF_SCOPE_PATH",
            "evidence reports changed paths outside this unit's allowedPaths",
            {"outOfScope": out_of_scope},
        )

    unknown_cmds = [c for c in cmds if c not in COMMAND_REGISTRY]
    if unknown_cmds:
        raise ControllerError(
            "UNKNOWN_COMMAND",
            "evidence reports commands outside the command registry",
            {"unknown": unknown_cmds},
        )
    unallowed_cmds = [c for c in cmds if c not in allowed_commands]
    if unallowed_cmds:
        raise ControllerError(
            "UNALLOWED_COMMAND",
            "evidence reports commands outside this unit's allowedCommands",
            {"unallowed": unallowed_cmds},
        )


def submit_evidence(unit: dict, component: dict) -> dict:
    """Validate and append one evidence component. Returns the stored record."""
    validate_evidence(component)
    _check_collision(unit, component)
    _check_contradiction(unit, component)
    _check_quota(unit, component)
    _check_budget(unit, component)
    _check_reviewer_allowed(unit, component)
    _check_scope(unit, component)
    record = copy.deepcopy(component)
    record.pop("_now", None)
    _unit_history(unit).append(record)
    return record


def _evidence_satisfies(unit: dict, etype: str, component: dict, now: float) -> bool:
    """Revalidate ONE stored/just-submitted evidence component against the
    *current* requirement for etype, at the moment of consumption. This is
    deliberately re-derived from the component every time: a type match in
    the evidence log is never, by itself, enough."""
    if component.get("type") != etype:
        return False
    try:
        submitted_at = float(component["submittedAt"])
    except (TypeError, ValueError, KeyError):
        return False
    stale_after = component.get("staleAfterSeconds", DEFAULT_STALE_AFTER_SECONDS)
    if now - submitted_at > stale_after:
        return False

    success = SUCCESS_OUTCOME.get(etype)
    if success is not None and component.get("outcome") != success:
        return False

    if etype in FINGERPRINT_BOUND_TYPES:
        current_fp = unit.get("currentCommitFingerprint")
        if not current_fp or component.get("commitFingerprint") != current_fp:
            return False

    if etype == "reviewer":
        identity = component.get("reviewerIdentity")
        if identity not in unit.get("reviewerIdentities", []):
            return False
        if identity == unit.get("implementerIdentity"):
            return False

    if etype == "quota":
        remaining = component.get("remainingPercent")
        threshold = component.get("thresholdPercent")
        if not isinstance(remaining, (int, float)) or not isinstance(threshold, (int, float)):
            return False
        if remaining < threshold:
            return False
        budget = unit.get("quotaBudget", {})
        if component.get("provider") != budget.get("provider"):
            return False
        if component.get("accountPoolId") != budget.get("accountPoolId"):
            return False

    return True


# ---------------------------------------------------------------------------
# Transition engine
# ---------------------------------------------------------------------------

def _consecutive_same_class_failures(history: List[dict], unit_class: str) -> int:
    """Count consecutive prior *closed* units of this class that ended in a
    failure state, most recent first, stopping at the first non-matching
    class or non-failure close."""
    count = 0
    for entry in reversed(history):
        if entry.get("event") != "unit_closed":
            continue
        if entry.get("unitClass") != unit_class:
            break
        if entry.get("finalState") not in ("rejected", "blocked_operator", "blocked_quota", "quarantined"):
            break
        count += 1
    return count


def transition(
    state: dict,
    to_state: str,
    evidence: Optional[dict] = None,
    now: Optional[float] = None,
) -> dict:
    """Apply one transition to the active unit. Mutates and returns state."""
    now = now if now is not None else time.time()
    unit = state.get("activeUnit")
    if unit is None:
        raise ControllerError("NO_ACTIVE_UNIT", "there is no active work unit to transition")

    stored_contract_fp = unit.get("unitContractFingerprint")
    if not stored_contract_fp or unit_contract_fingerprint(unit) != stored_contract_fp:
        raise ControllerError("CONTRACT_FINGERPRINT_MISMATCH", "active work-unit contract changed after submission")

    from_state = unit["status"]
    if to_state not in STATES:
        raise ControllerError("UNKNOWN_STATE", f"{to_state!r} is not a recognized state")
    legal = TRANSITIONS.get(from_state, ())
    if to_state not in legal:
        raise ControllerError(
            "ILLEGAL_TRANSITION",
            f"cannot move from {from_state!r} to {to_state!r}",
            {"from": from_state, "to": to_state, "legal": list(legal)},
        )

    mode = state.get("campaignMode", "shadow")

    # ---- mode enforcement ----
    if to_state == "admitted":
        if mode == "frozen":
            raise ControllerError("MODE_FORBIDS_ADMISSION", "frozen mode cannot admit work units")
        if mode in ("quarantined", "complete"):
            raise ControllerError("MODE_FORBIDS_ADMISSION", f"{mode!r} mode cannot admit work units")
        if mode == "canary":
            canary_unit = state.get("canaryUnitId")
            canary_class = state.get("canaryClass")
            if unit["unitId"] != canary_unit and unit["unitClass"] != canary_class:
                raise ControllerError(
                    "CANARY_NOT_ELIGIBLE",
                    "canary mode permits only the configured canary unit/class",
                    {"canaryUnitId": canary_unit, "canaryClass": canary_class},
                )
    if mode == "shadow" and to_state in ("verified", "merged", "post_merge_verified"):
        raise ControllerError(
            "MODE_FORBIDS_TRANSITION",
            "shadow mode permits decision simulation only, not mutating lifecycle transitions",
            {"mode": mode, "toState": to_state},
        )

    # ---- correction-return plumbing ----
    # "running" is only reachable a second time from awaiting_verification
    # or verified as the one allowed reject-before-correction return.
    if to_state == "running" and from_state == "admitted" and evidence and evidence.get("isCorrection"):
        raise ControllerError(
            "ILLEGAL_TRANSITION",
            "a unit cannot start as a correction; corrections apply to units already run once",
        )
    if to_state == "running" and from_state in ("awaiting_verification", "verified"):
        if not evidence or not evidence.get("isCorrection"):
            raise ControllerError(
                "ILLEGAL_TRANSITION",
                "returning to running from verification requires isCorrection evidence "
                "(a recorded reject-before-correction)",
            )
        required_reject_fields = ("failureCategory", "failingComponentType", "failingComponentFingerprint")
        missing_reject = [f for f in required_reject_fields if not evidence.get(f)]
        if missing_reject:
            raise ControllerError(
                "MISSING_FAILURE_EVIDENCE",
                "correction-return requires recorded reject-before-correction evidence",
                {"missing": missing_reject},
            )

    if evidence and evidence.get("isCorrection"):
        if unit.get("correctionCount", 0) >= MAX_CORRECTIONS:
            raise ControllerError(
                "CORRECTION_LIMIT_EXCEEDED",
                "work unit already used its one allowed correction",
                {"correctionCount": unit.get("correctionCount", 0), "max": MAX_CORRECTIONS},
            )

    # ---- evidence collection ----
    submitted_components: List[dict] = []
    if evidence:
        components = evidence.get("components", [])
        if not isinstance(components, list):
            raise ControllerError("MALFORMED_EVIDENCE", "evidence.components must be a list")
        for component in components:
            component = dict(component)
            component["_now"] = now
            submitted_components.append(submit_evidence(unit, component))

    # ---- required-evidence revalidation at the point of consumption ----
    required_types = set(TRANSITION_EVIDENCE_REQUIREMENTS.get(to_state, ()))
    if to_state == "awaiting_verification":
        required_types |= set(unit.get("acceptanceComponents", []))

    missing_types = set()
    for etype in required_types:
        # Admission quota evidence must be freshly submitted THIS call; it
        # can never be satisfied by reusing an older logged component.
        if to_state == "admitted" and etype == "quota":
            candidates = submitted_components
        else:
            candidates = unit.get("evidenceLog", [])
        if not any(_evidence_satisfies(unit, etype, c, now) for c in candidates):
            missing_types.add(etype)
    if missing_types:
        raise ControllerError(
            "MISSING_REQUIRED_EVIDENCE",
            f"transition to {to_state!r} requires valid evidence types not present",
            {"missing": sorted(missing_types)},
        )

    # ---- anti-loop: repeated failure-class transitions require a new,
    # distinct structured failure/authoritative-input fingerprint by the
    # 3rd consecutive hit for this unit class. This standing rule cannot be
    # silently bypassed by operator assertion. ----
    if to_state in ("rejected", "blocked_operator", "blocked_quota", "quarantined"):
        if not evidence or not evidence.get("failureCategory"):
            raise ControllerError(
                "MISSING_FAILURE_EVIDENCE",
                f"transition to {to_state!r} requires structured failureCategory evidence",
            )
        fp = failure_fingerprint(unit["unitClass"], to_state, evidence)
        consecutive = _consecutive_same_class_failures(state["history"], unit["unitClass"])
        if consecutive >= ANTI_LOOP_CONSECUTIVE_LIMIT - 1:
            prior_fps = [
                e.get("failureFingerprint")
                for e in reversed(state["history"])
                if e.get("event") == "transition"
                and e.get("unitClass") == unit["unitClass"]
                and e.get("failureFingerprint")
            ][: ANTI_LOOP_CONSECUTIVE_LIMIT - 1]
            if fp in prior_fps:
                raise ControllerError(
                    "ANTI_LOOP_BLOCKED",
                    "repeated failure in the same unit class requires new failure/input evidence, not a repeat",
                    {"consecutive": consecutive, "failureFingerprint": fp},
                )
        unit["_last_failure_fingerprint"] = fp
    else:
        fp = None

    unit["status"] = to_state
    if evidence and evidence.get("isCorrection"):
        unit["correctionCount"] = unit.get("correctionCount", 0) + 1

    history_entry = {
        "event": "transition",
        "unitId": unit["unitId"],
        "unitClass": unit["unitClass"],
        "fromState": from_state,
        "toState": to_state,
        "at": now,
        "evidenceTypesSubmitted": [c["type"] for c in submitted_components],
    }
    if fp:
        history_entry["failureFingerprint"] = fp
    if to_state == "running" and from_state in ("awaiting_verification", "verified"):
        history_entry["correctionReturn"] = True
        history_entry["rejectBeforeCorrection"] = {
            "failureCategory": evidence.get("failureCategory"),
            "failingComponentType": evidence.get("failingComponentType"),
            "failingComponentFingerprint": evidence.get("failingComponentFingerprint"),
        }
    state["history"].append(history_entry)

    if to_state in TERMINAL_STATES:
        # Terminal for this unit: clear activeUnit slot so a new unit can
        # be admitted, but the unit's full record stays in history.
        state["history"].append(
            {
                "event": "unit_closed",
                "unitId": unit["unitId"],
                "unitClass": unit["unitClass"],
                "finalState": to_state,
                "at": now,
            }
        )
        state["lastClosedUnit"] = unit
        state["activeUnit"] = None
    else:
        # Explicitly NOT cleared before the correction transition, or at
        # any other non-terminal point: the active unit stays active.
        state["activeUnit"] = unit

    return state


def submit_unit(state: dict, unit: dict, now: Optional[float] = None) -> dict:
    now = now if now is not None else time.time()
    if not state.get("contractFingerprint"):
        raise ControllerError(
            "CONTRACT_NOT_BOUND",
            "state must be bound to a product contract/campaign (bind_contract) before accepting work units",
        )
    if state.get("activeUnit") is not None:
        raise ControllerError(
            "UNIT_ALREADY_ACTIVE",
            "only one active work unit is allowed at a time",
            {"activeUnitId": state["activeUnit"]["unitId"]},
        )
    validate_new_unit(unit)
    unit = copy.deepcopy(unit)
    unit["createdAt"] = unit.get("createdAt", now)
    unit["status"] = "queued"
    unit["correctionCount"] = 0
    unit["repairVsReconstruction"] = unit.get("repairVsReconstruction", "undecided")
    unit["repairDecision"] = None
    unit["evidenceLog"] = []
    unit["currentCommitFingerprint"] = unit.get("currentCommitFingerprint")
    unit["unitContractFingerprint"] = unit_contract_fingerprint(unit)
    state["activeUnit"] = unit
    state["history"].append(
        {"event": "unit_submitted", "unitId": unit["unitId"], "unitClass": unit["unitClass"], "at": now}
    )
    return state


def record_commit(state: dict, commit_fingerprint: str, now: Optional[float] = None) -> dict:
    """Bind the active unit to its exact current commit/content fingerprint.
    Evidence that claims a different fingerprint can never satisfy a
    transition after this call."""
    now = now if now is not None else time.time()
    unit = state.get("activeUnit")
    if unit is None:
        raise ControllerError("NO_ACTIVE_UNIT", "there is no active work unit")
    if unit.get("status") in TERMINAL_STATES or unit.get("status") in ("merged", "post_merge_verified"):
        raise ControllerError("COMMIT_RECORDING_FORBIDDEN", "cannot record or repoint a commit after merge")
    stored_contract_fp = unit.get("unitContractFingerprint")
    if not stored_contract_fp or unit_contract_fingerprint(unit) != stored_contract_fp:
        raise ControllerError("CONTRACT_FINGERPRINT_MISMATCH", "active work-unit contract changed after submission")
    if not isinstance(commit_fingerprint, str) or not commit_fingerprint.strip():
        raise ControllerError("MALFORMED_COMMIT_FINGERPRINT", "commit fingerprint must be a non-empty string")
    unit["currentCommitFingerprint"] = commit_fingerprint
    state["history"].append(
        {
            "event": "commit_recorded",
            "unitId": unit["unitId"],
            "commitFingerprint": commit_fingerprint,
            "at": now,
        }
    )
    return state


def set_repair_decision(state: dict, decision: str, decision_evidence: dict, now: Optional[float] = None) -> dict:
    now = now if now is not None else time.time()
    unit = state.get("activeUnit")
    if unit is None:
        raise ControllerError("NO_ACTIVE_UNIT", "there is no active work unit")
    if decision not in ("repair", "reconstruct"):
        raise ControllerError("MALFORMED_DECISION", "decision must be 'repair' or 'reconstruct'")
    existing = unit.get("repairDecision")
    if existing is not None:
        trigger = decision_evidence.get("reopenTrigger")
        if trigger not in APPROVED_REOPEN_TRIGGERS:
            raise ControllerError(
                "REPAIR_DECISION_IMMUTABLE",
                "a repair/reconstruct decision is already set; reopening requires an approved trigger",
                {"approvedTriggers": list(APPROVED_REOPEN_TRIGGERS)},
            )
        if not decision_evidence.get("bindingFingerprint"):
            raise ControllerError(
                "MISSING_FIELDS",
                "reopening a repair/reconstruct decision requires a bindingFingerprint tying it to the "
                "newly failing test, new authoritative evidence, changed source, or defect fingerprint",
                {"missing": ["bindingFingerprint"]},
            )
        existing.setdefault("reopenHistory", []).append(
            {"at": now, "trigger": trigger, "evidence": decision_evidence}
        )
    required = ("decidedAt", "decisionEvidence", "contentScopeFingerprint")
    payload = {
        "decidedAt": now,
        "decisionEvidence": decision_evidence,
        "contentScopeFingerprint": structured_fingerprint(
            decision_evidence, tuple(k for k in decision_evidence.keys() if k != "notes")
        ),
        "reopenHistory": existing.get("reopenHistory", []) if existing else [],
    }
    missing = [f for f in required if payload.get(f) in (None, "")]
    if missing:
        raise ControllerError("MISSING_FIELDS", "repair decision missing required fields", {"missing": missing})
    unit["repairVsReconstruction"] = decision
    unit["repairDecision"] = payload
    state["history"].append(
        {"event": "repair_decision", "unitId": unit["unitId"], "decision": decision, "at": now}
    )
    return state


# ---------------------------------------------------------------------------
# Read-only migration / shadow fixture check
# ---------------------------------------------------------------------------

def check_shadow_fixture(fixture_path: str) -> dict:
    """Validate a read-only shadow/migration fixture without mutating any
    live state. Returns a report; never writes."""
    if not os.path.exists(fixture_path):
        raise ControllerError("FIXTURE_ABSENT", f"fixture not found: {fixture_path}")
    with open(fixture_path, "r", encoding="utf-8") as fh:
        try:
            fixture = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ControllerError("MALFORMED_STATE", f"fixture is not valid JSON: {exc}") from exc
    if fixture.get("schemaVersion") != SCHEMA_VERSION:
        return {
            "ok": False,
            "reason": "SCHEMA_MISMATCH",
            "fixtureSchemaVersion": fixture.get("schemaVersion"),
            "controllerSchemaVersion": SCHEMA_VERSION,
        }
    active = fixture.get("activeUnit")
    if active is not None:
        try:
            validate_new_unit(active)
        except ControllerError as exc:
            return {"ok": False, "reason": exc.code, "message": exc.message}
    return {"ok": True, "schemaVersion": SCHEMA_VERSION, "activeUnitPresent": active is not None}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print(obj: dict) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True))


def cmd_show(args: argparse.Namespace) -> int:
    state = load_state(args.state_file)
    _print(state)
    return 0


def cmd_bind_contract(args: argparse.Namespace) -> int:
    state = load_state(args.state_file)
    version = state["stateVersion"]
    try:
        state = bind_contract(state, args.product_contract_id, args.campaign_id)
    except ControllerError as exc:
        _print(exc.to_dict())
        return 1
    save_state(args.state_file, state, version)
    _print({"ok": True, "productContractId": args.product_contract_id, "campaignId": args.campaign_id})
    return 0


def cmd_set_canary(args: argparse.Namespace) -> int:
    state = load_state(args.state_file)
    version = state["stateVersion"]
    state = configure_canary(state, unit_id=args.unit_id, unit_class=args.unit_class)
    save_state(args.state_file, state, version)
    _print({"ok": True, "canaryUnitId": args.unit_id, "canaryClass": args.unit_class})
    return 0


def cmd_record_commit(args: argparse.Namespace) -> int:
    state = load_state(args.state_file)
    version = state["stateVersion"]
    try:
        state = record_commit(state, args.commit_fingerprint)
    except ControllerError as exc:
        _print(exc.to_dict())
        return 1
    save_state(args.state_file, state, version)
    _print({"ok": True, "commitFingerprint": args.commit_fingerprint})
    return 0


def cmd_submit(args: argparse.Namespace) -> int:
    with open(args.unit_file, "r", encoding="utf-8") as fh:
        unit = json.load(fh)
    state = load_state(args.state_file)
    version = state["stateVersion"]
    try:
        state = submit_unit(state, unit)
    except ControllerError as exc:
        _print(exc.to_dict())
        return 1
    save_state(args.state_file, state, version)
    _print({"ok": True, "unitId": unit["unitId"], "status": "queued"})
    return 0


def cmd_transition(args: argparse.Namespace) -> int:
    evidence = None
    if args.evidence_file:
        with open(args.evidence_file, "r", encoding="utf-8") as fh:
            evidence = json.load(fh)
    state = load_state(args.state_file)
    version = state["stateVersion"]
    try:
        state = transition(state, args.to_state, evidence)
    except ControllerError as exc:
        _print(exc.to_dict())
        return 1
    save_state(args.state_file, state, version)
    _print({"ok": True, "toState": args.to_state})
    return 0


def cmd_check_fixture(args: argparse.Namespace) -> int:
    try:
        report = check_shadow_fixture(args.fixture_file)
    except ControllerError as exc:
        _print(exc.to_dict())
        return 1
    _print(report)
    return 0 if report.get("ok") else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MySugya deterministic autonomy controller (v2)")
    parser.add_argument("--state-file", default="scripts/.autonomy_controller_state.json")
    sub = parser.add_subparsers(dest="command", required=True)

    p_show = sub.add_parser("show", help="print current state")
    p_show.set_defaults(func=cmd_show)

    p_bind = sub.add_parser("bind-contract", help="bind the state file to a product contract/campaign")
    p_bind.add_argument("product_contract_id")
    p_bind.add_argument("campaign_id")
    p_bind.set_defaults(func=cmd_bind_contract)

    p_canary = sub.add_parser("set-canary", help="configure the canary-eligible unit/class")
    p_canary.add_argument("--unit-id")
    p_canary.add_argument("--unit-class")
    p_canary.set_defaults(func=cmd_set_canary)

    p_commit = sub.add_parser("record-commit", help="bind the active unit to its current commit fingerprint")
    p_commit.add_argument("commit_fingerprint")
    p_commit.set_defaults(func=cmd_record_commit)

    p_submit = sub.add_parser("submit", help="submit a new work unit (queued)")
    p_submit.add_argument("unit_file")
    p_submit.set_defaults(func=cmd_submit)

    p_trans = sub.add_parser("transition", help="apply a state transition to the active unit")
    p_trans.add_argument("to_state", choices=STATES)
    p_trans.add_argument("--evidence-file")
    p_trans.set_defaults(func=cmd_transition)

    p_fixture = sub.add_parser("check-fixture", help="read-only validation of a shadow/migration fixture")
    p_fixture.add_argument("fixture_file")
    p_fixture.set_defaults(func=cmd_check_fixture)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
