#!/usr/bin/env python3
"""Shadow-mode integration adapter for the autonomy controller (scripts/autonomy_controller.py).

Purpose: give an OpenClaw agent/automation one narrow, read-only entry point
to ask "what would the controller decide for this candidate work unit right
now" without ever executing a command, launching an agent, mutating Git/
GitHub, mutating an automation, or touching the live remediation ledger.

This adapter never calls the real controller's live state file by default.
It:

  1. Reads a single structured JSON request (candidate work unit +
     quota/evidence snapshot + repoSha binding). productContractId and
     campaignId are NOT caller-trusted: the request must assert exactly
     REQUIRED_PRODUCT_CONTRACT_ID / REQUIRED_CAMPAIGN_ID, checked before any
     state is loaded or simulated, before anything else in the request is
     interpreted.
  2. Verifies the caller's asserted repoSha matches this repo's actual
     current `git rev-parse HEAD` -- a stale or wrong-repo request is
     rejected, not silently simulated against the wrong commit.
  3. Builds a brand-new, in-memory controller state (or an in-memory copy of
     an explicitly supplied --read-state snapshot; the original file, if
     any, is never opened for writing). Campaign mode is force-set to
     "shadow" regardless of what the request claims. A readStatePath whose
     own binding does not match the fixed contract/campaign fails closed
     (it is never silently discarded/replaced).
  4. Runs bind_contract -> submit_unit -> (optional) admission transition ->
     (optional) one additional requested transition entirely through the
     real controller module, so every existing fail-closed rule (schema,
     evidence, scope, anti-loop, contract fingerprint, etc.) applies
     unmodified.
  5. Refuses, before calling the controller, any requested transition that
     the controller's own shadow-mode rule would treat as a mutating
     lifecycle step (verified / merged / post_merge_verified), and any
     per-unit "mode" field -- these are checked here too so the rejection
     reason is explicit and in the first-class error shape.
  6. Emits exactly one JSON decision report to stdout. It writes a state
     artifact to disk ONLY if the caller passes --output-state, and only
     beneath the fixed, repo-independent sandbox root SHADOW_ARTIFACT_ROOT.
     Any resolved path outside that root, any symlink escape, any forbidden
     basename (the controller's live ledger name or known MySugya
     remediation-state filenames), or any output path that is itself an
     existing symlink is rejected before the simulation runs. The same
     sandbox and forbidden-basename rules apply to readStatePath.

Standard library only. No subprocess execution of arbitrary commands: the
only shell-adjacent action is `git rev-parse HEAD`, which is read-only.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import sys
import tempfile
import time
import uuid
from typing import Any, Dict, Optional

import autonomy_controller as ac

# The controller's own default live state file. A path (output-state or
# readStatePath) that resolves to this basename is refused: this adapter
# must never be a read or write path into the real remediation ledger.
LIVE_LEDGER_BASENAME = ".autonomy_controller_state.json"

# Other known MySugya remediation-state filenames that must never be reached
# through this adapter's filesystem surface, even inside the sandbox root.
FORBIDDEN_BASENAMES = frozenset(
    {
        LIVE_LEDGER_BASENAME,
        "remediation-progress.json",
        "remediation-hold.json",
    }
)

# The only filesystem root this adapter will ever read or write a state
# artifact beneath, regardless of the repo it is pointed at. Fixed and
# repo-independent so a caller can never widen the write/read surface by
# supplying a path argument.
SHADOW_ARTIFACT_ROOT = "/tmp/mysugya-autonomy-shadow"

# This adapter only ever simulates exactly one product contract / campaign.
# Caller-supplied values are validated against these constants, not trusted;
# see validate_request().
REQUIRED_PRODUCT_CONTRACT_ID = "yoma-product-acceptance-v2"
REQUIRED_CAMPAIGN_ID = "mysugya-yoma-remediation"

# Lifecycle transitions that are mutating in the sense the controller itself
# forbids under shadow mode. Re-checked here so adapter callers get an
# explicit, adapter-level rejection reason before the controller is ever
# invoked.
SHADOW_FORBIDDEN_TRANSITIONS = ("verified", "merged", "post_merge_verified")


class AdapterError(Exception):
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


def _git_head_sha(repo_root: str) -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise AdapterError("REPO_SHA_UNRESOLVABLE", f"could not resolve repo HEAD sha: {exc}") from exc
    sha = out.stdout.strip()
    if not sha:
        raise AdapterError("REPO_SHA_UNRESOLVABLE", "git rev-parse HEAD returned no output")
    return sha


def _resolve_sandboxed_path(path: str, *, field_name: str) -> str:
    """Resolve `path` and verify it is confined to SHADOW_ARTIFACT_ROOT with
    an allowed basename. Rejects traversal (`..`), symlink escape (resolved
    via os.path.realpath, which follows every symlink component), and any
    forbidden basename. Returns the resolved absolute path; never performs
    any filesystem write."""
    if not path or not isinstance(path, str):
        raise AdapterError(
            "INVALID_PATH", f"{field_name} must be a non-empty string", {"field": field_name}
        )

    # Check the literal requested path for an existing symlink before any
    # realpath resolution: os.path.realpath() below silently dereferences
    # symlinks, which would otherwise make an existing symlink at the exact
    # requested path invisible to every check that follows (including the
    # dedicated os.path.islink() guard in _atomic_write_json, which only ever
    # sees the already-resolved target).
    if os.path.islink(path):
        raise AdapterError(
            "OUTPUT_IS_SYMLINK",
            f"refusing to follow an existing symlink at the requested {field_name}",
            {"field": field_name, "requestedPath": path},
        )

    root_real = os.path.realpath(SHADOW_ARTIFACT_ROOT)
    candidate_real = os.path.realpath(path)

    if candidate_real != root_real and not candidate_real.startswith(root_real + os.sep):
        raise AdapterError(
            "PATH_OUTSIDE_SANDBOX_ROOT",
            f"{field_name} must resolve beneath {SHADOW_ARTIFACT_ROOT}",
            {"field": field_name, "requestedPath": path, "resolvedPath": candidate_real},
        )

    basename = os.path.basename(candidate_real)
    if basename in FORBIDDEN_BASENAMES:
        raise AdapterError(
            "FORBIDDEN_PATH_BASENAME",
            f"{field_name} may not target a reserved remediation-state filename",
            {"field": field_name, "basename": basename},
        )

    return candidate_real


def _atomic_write_json(path: str, obj: dict) -> None:
    # Never write through an existing symlink, even one that resolves inside
    # the sandbox root: the caller's literal path is the write target, and a
    # symlink there means some other process controls where bytes actually
    # land.
    if os.path.islink(path):
        raise AdapterError(
            "OUTPUT_IS_SYMLINK",
            "refusing to write through an existing symlink output target",
            {"outputState": path},
        )

    directory = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(directory, exist_ok=True)
    tmp_path = os.path.join(directory, f".{os.path.basename(path)}.tmp-{uuid.uuid4().hex}")
    try:
        with open(tmp_path, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2, sort_keys=True)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise

    try:
        dir_fd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except OSError:
        # Best-effort durability only; the rename above already succeeded.
        pass


def validate_request(request: dict) -> None:
    if not isinstance(request, dict):
        raise AdapterError("MALFORMED_REQUEST", "request must be a JSON object")

    required = ("productContractId", "campaignId", "repoSha", "workUnit")
    missing = [f for f in required if f not in request or request[f] in (None, "")]
    if missing:
        raise AdapterError(
            "MISSING_REQUEST_FIELDS", "request missing required fields", {"missing": missing}
        )

    # productContractId/campaignId are never caller-trusted: this adapter
    # simulates exactly one fixed contract/campaign binding. Checked before
    # anything else about the request (git sha, workUnit shape, state) is
    # interpreted.
    if request["productContractId"] != REQUIRED_PRODUCT_CONTRACT_ID:
        raise AdapterError(
            "CONTRACT_BINDING_MISMATCH",
            "request productContractId does not match the adapter's fixed binding",
            {
                "requiredProductContractId": REQUIRED_PRODUCT_CONTRACT_ID,
                "requestProductContractId": request["productContractId"],
            },
        )
    if request["campaignId"] != REQUIRED_CAMPAIGN_ID:
        raise AdapterError(
            "CONTRACT_BINDING_MISMATCH",
            "request campaignId does not match the adapter's fixed binding",
            {
                "requiredCampaignId": REQUIRED_CAMPAIGN_ID,
                "requestCampaignId": request["campaignId"],
            },
        )

    if not isinstance(request["workUnit"], dict):
        raise AdapterError("MALFORMED_REQUEST", "workUnit must be a JSON object")

    if "mode" in request["workUnit"]:
        raise AdapterError(
            "FORBIDDEN_UNIT_FIELD", "per-unit campaign mode is not permitted; mode is adapter/controller-authoritative"
        )

    requested_transition = request.get("requestedTransition")
    if requested_transition is not None:
        if requested_transition not in ac.STATES:
            raise AdapterError(
                "UNKNOWN_STATE", f"requestedTransition {requested_transition!r} is not a recognized state"
            )
        if requested_transition in SHADOW_FORBIDDEN_TRANSITIONS:
            raise AdapterError(
                "SHADOW_FORBIDS_MUTATING_TRANSITION",
                "shadow mode permits decision simulation only; this adapter never requests a mutating "
                "lifecycle transition",
                {"requestedTransition": requested_transition},
            )

    admission_evidence = request.get("admissionEvidence")
    if admission_evidence is not None and not isinstance(admission_evidence, dict):
        raise AdapterError("MALFORMED_REQUEST", "admissionEvidence must be a JSON object")

    transition_evidence = request.get("transitionEvidence")
    if transition_evidence is not None and not isinstance(transition_evidence, dict):
        raise AdapterError("MALFORMED_REQUEST", "transitionEvidence must be a JSON object")

    read_state_path = request.get("readStatePath")
    if read_state_path is not None:
        _resolve_sandboxed_path(read_state_path, field_name="readStatePath")


def run_shadow_simulation(request: dict, repo_root: str, now: Optional[float] = None) -> dict:
    """Pure function: validates the request (including the fixed contract/
    campaign binding and sandboxed readStatePath), checks the exact repo SHA
    binding, and simulates the candidate work unit against a brand-new,
    in-memory controller state forced into shadow mode. Never writes
    anything; the caller decides whether/where to persist the returned
    state artifact."""
    now = now if now is not None else time.time()
    validate_request(request)

    actual_sha = _git_head_sha(repo_root)
    if request["repoSha"] != actual_sha:
        raise AdapterError(
            "REPO_SHA_MISMATCH",
            "request repoSha does not match this repo's actual current HEAD",
            {"requestRepoSha": request["repoSha"], "actualRepoSha": actual_sha},
        )

    read_state_path = request.get("readStatePath")
    if read_state_path:
        resolved_read_path = _resolve_sandboxed_path(read_state_path, field_name="readStatePath")
        state = ac.load_state(resolved_read_path)
        state = copy.deepcopy(state)
        # A readStatePath snapshot bound to a different product
        # contract/campaign than this adapter's fixed binding is never
        # silently discarded and replaced with a fresh state -- that would
        # let a caller launder an unrelated or stale snapshot into a
        # simulation that looks authoritative. Fail closed instead.
        existing_fp = state.get("contractFingerprint")
        if existing_fp is not None:
            requested_fp = ac.contract_fingerprint(REQUIRED_PRODUCT_CONTRACT_ID, REQUIRED_CAMPAIGN_ID)
            if existing_fp != requested_fp:
                raise AdapterError(
                    "CROSS_CONTRACT_READ_STATE_REJECTED",
                    "readStatePath snapshot is bound to a different product contract/campaign; "
                    "refusing to simulate against it",
                    {"readStatePath": read_state_path},
                )
    else:
        state = ac._empty_state()

    # Shadow mode is authoritative regardless of any prior state or request
    # content; this adapter can never be used to simulate a non-shadow mode.
    state = ac.set_campaign_mode(state, "shadow", now=now)

    state = ac.bind_contract(state, REQUIRED_PRODUCT_CONTRACT_ID, REQUIRED_CAMPAIGN_ID, now=now)

    simulated: Dict[str, Any] = {
        "steps": [],
    }

    unit = copy.deepcopy(request["workUnit"])
    state = ac.submit_unit(state, unit, now=now)
    simulated["steps"].append({"step": "submit_unit", "unitId": unit["unitId"], "status": "queued"})

    commit_fingerprint = request.get("commitFingerprint")
    if commit_fingerprint:
        state = ac.record_commit(state, commit_fingerprint, now=now)
        simulated["steps"].append({"step": "record_commit", "commitFingerprint": commit_fingerprint})

    admission_evidence = request.get("admissionEvidence")
    if admission_evidence is not None:
        state = ac.transition(state, "admitted", admission_evidence, now=now)
        simulated["steps"].append({"step": "transition", "toState": "admitted"})

    requested_transition = request.get("requestedTransition")
    if requested_transition is not None:
        transition_evidence = request.get("transitionEvidence")
        state = ac.transition(state, requested_transition, transition_evidence, now=now)
        simulated["steps"].append({"step": "transition", "toState": requested_transition})

    final_unit = state.get("activeUnit") or state.get("lastClosedUnit")
    report = {
        "ok": True,
        "mode": "shadow",
        "boundProductContractId": state.get("productContractId"),
        "boundCampaignId": state.get("campaignId"),
        "repoSha": actual_sha,
        "unitId": unit["unitId"],
        "finalStatus": final_unit.get("status") if final_unit else None,
        "simulation": simulated,
        "at": now,
    }
    return {"report": report, "state": state}


def cmd_simulate(args: argparse.Namespace) -> int:
    with open(args.request_file, "r", encoding="utf-8") as fh:
        request = json.load(fh)

    repo_root = args.repo_root or os.getcwd()

    # Check the output-state target before running the simulation: this is a
    # cheap, unconditional guard against writing outside the sandbox root or
    # backdooring a reserved remediation-state filename, and must not depend
    # on whether the rest of the request (e.g. evidence freshness) happens to
    # be valid.
    resolved_output_path = None
    if args.output_state:
        try:
            resolved_output_path = _resolve_sandboxed_path(args.output_state, field_name="outputState")
        except AdapterError as err:
            print(json.dumps(err.to_dict(), indent=2, sort_keys=True))
            return 1

    try:
        result = run_shadow_simulation(request, repo_root)
    except (AdapterError, ac.ControllerError) as exc:
        print(json.dumps(exc.to_dict(), indent=2, sort_keys=True))
        return 1

    if resolved_output_path:
        _atomic_write_json(resolved_output_path, result["state"])
        result["report"]["outputState"] = resolved_output_path

    print(json.dumps(result["report"], indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Shadow-mode OpenClaw integration adapter for the MySugya autonomy controller"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_sim = sub.add_parser(
        "simulate",
        help="read a candidate work-unit request and emit a read-only shadow-mode decision report",
    )
    p_sim.add_argument("request_file", help="path to a JSON request (see module docstring for shape)")
    p_sim.add_argument(
        "--repo-root",
        default=None,
        help="repo root to resolve the exact HEAD sha against (default: current working directory)",
    )
    p_sim.add_argument(
        "--output-state",
        default=None,
        help=f"optional explicit path, confined beneath {SHADOW_ARTIFACT_ROOT}, to atomically write the "
        "resulting in-memory state artifact; never the controller's live state filename or another "
        "reserved remediation-state filename",
    )
    p_sim.set_defaults(func=cmd_simulate)

    return parser


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
