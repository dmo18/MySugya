#!/usr/bin/env python3
"""Owner-side, model-free dispatcher for the disabled Rabbi campaign.

This script is NOT for use by Rabbi's SSH sandbox user. The owner user
verifies a pinned job, quota and operator approval before reserving one
launch. A forced OpenClaw run bypasses trigger.script by design; only
this external, protected and non-reentrant entry point should use it.

No invocation is allowed without --dispatch. --check never reserves a
launch or calls a model. This is not a mid-turn token-spending firewall.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

from rabbi_cron_admission import (
    approval_path, decide, ledger_path, read_cached_quota,
    read_private_approval, state_dir,
)
from rabbi_quota_gate import GateDenied, evaluate

EXPECTED_NAME = "Rabbi Yoma Autonomous Campaign"
EXPECTED_AGENT = "rabbi"
MAX_PARENT_TIMEOUT_SECONDS = 900
GET_TIMEOUT_SECONDS = 45
WAIT_TIMEOUT_SECONDS = 1140


def check_job(job: dict, job_id: str, model: str) -> None:
    """Refuse surprise changes to the owner-approved job or model route."""
    if not model.startswith("openai/") or model.count("/") != 1:
        raise GateDenied("expected model must be an exact OpenAI model reference")
    if not isinstance(job, dict):
        raise GateDenied("OpenClaw returned no cron job")
    if job.get("id") != job_id or job.get("name") != EXPECTED_NAME:
        raise GateDenied("Rabbi campaign identity mismatch")
    if job.get("agentId") != EXPECTED_AGENT or job.get("enabled") is not False:
        raise GateDenied("Rabbi job is not disabled and correctly scoped")
    if job.get("sessionTarget") != "isolated":
        raise GateDenied("Rabbi campaign must remain isolated")
    payload = job.get("payload")
    if not isinstance(payload, dict) or payload.get("kind") != "agentTurn":
        raise GateDenied("Rabbi campaign payload is not an agent turn")
    if payload.get("model") != model:
        raise GateDenied("Rabbi campaign has no approved explicit model pin")
    timeout = payload.get("timeoutSeconds")
    if isinstance(timeout, bool) or not isinstance(timeout, int) or not (
        1 <= timeout <= MAX_PARENT_TIMEOUT_SECONDS
    ):
        raise GateDenied("Rabbi campaign parent timeout invalid")
    if payload.get("fallbacks") != []:
        raise GateDenied("Rabbi campaign fallback list must be explicitly empty")
    trigger = job.get("trigger")
    if not isinstance(trigger, dict) or not isinstance(trigger.get("script"), str) or not trigger["script"].strip():
        raise GateDenied("Rabbi campaign is missing its native fail-closed trigger")


def get_job(binary: str, job_id: str) -> dict:
    """Inspect the real OpenClaw job without creating any model call."""
    try:
        proc = subprocess.run(
            [binary, "cron", "get", job_id, "--json"],
            text=True, capture_output=True, timeout=GET_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GateDenied("OpenClaw cron inspection unavailable") from exc
    if proc.returncode:
        raise GateDenied("OpenClaw cron inspection failed")
    try:
        decoded = json.loads(proc.stdout)
    except ValueError as exc:
        raise GateDenied("OpenClaw cron inspection is not JSON") from exc
    if not isinstance(decoded, dict):
        raise GateDenied("OpenClaw cron inspection schema invalid")
    job = decoded.get("job", decoded)
    if not isinstance(job, dict):
        raise GateDenied("OpenClaw cron job missing")
    return job


def private_lock(path: Path) -> int:
    """A running dispatch holds this lock until its parent cron turn ends."""
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    parent = path.parent.lstat()
    if not stat.S_ISDIR(parent.st_mode) or parent.st_uid != os.getuid() or parent.st_mode & 0o077:
        raise GateDenied("dispatcher state directory ownership unsafe")
    try:
        fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    except OSError as exc:
        raise GateDenied("dispatcher lock unavailable") from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise GateDenied("dispatcher lock permissions unsafe")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise GateDenied("an earlier Rabbi dispatch is still active") from exc
        return fd
    except BaseException:
        os.close(fd)
        raise


def _dispatch(binary: str, job_id: str) -> None:
    """The only provider-spending path. Never retry unknown run outcomes."""
    approved = decide(approval_path(), ledger_path(), read_cached_quota)
    if approved["provider"] != "openai":
        raise GateDenied("unexpected provider")
    try:
        proc = subprocess.run(
            [binary, "cron", "run", job_id, "--wait",
             "--wait-timeout", "18m", "--poll-interval", "2s", "--json"],
            text=True, capture_output=True, timeout=WAIT_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GateDenied("campaign run completion unknown; do not retry") from exc
    if proc.returncode:
        raise GateDenied("campaign run failed or completion unknown; do not retry")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dispatch", action="store_true",
                    help="permit exactly one protected launch, never by default")
    ap.add_argument("--job-id", default=os.getenv("RABBI_JOB_ID", ""))
    ap.add_argument("--expected-model", default=os.getenv("RABBI_EXPECTED_MODEL", ""))
    ap.add_argument("--openclaw", default=os.getenv("RABBI_OPENCLAW_BIN", "openclaw"))
    args = ap.parse_args(argv)
    try:
        if not args.job_id:
            raise GateDenied("private RABBI_JOB_ID is not configured")
        if not args.expected_model:
            raise GateDenied("private RABBI_EXPECTED_MODEL is not configured")
        fd = private_lock(state_dir() / "rabbi-dispatch.lock") if args.dispatch else None
        try:
            check_job(get_job(args.openclaw, args.job_id), args.job_id, args.expected_model)
            if args.dispatch:
                _dispatch(args.openclaw, args.job_id)
            else:
                read_private_approval(approval_path())
                evaluate(read_cached_quota(), provider="openai")
        finally:
            if fd is not None:
                os.close(fd)
    except (GateDenied, OSError, ValueError) as exc:
        print(json.dumps({"admitted": False, "reason": str(exc)}, sort_keys=True))
        return 3
    print(json.dumps({"admitted": True, "dispatched": args.dispatch}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
