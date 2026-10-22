#!/usr/bin/env python3
"""Headless admission gate for the Rabbi OpenClaw scheduler condition script.

NOT an agent turn. Checks an explicit PRIVATE operator approval file, the
cached, freshly refreshed OpenClaw provider quota and a private UTC-day admission counter, then
reserves ONE launch. Exit nonzero / print admitted:false on any ambiguity.

The scheduler must install scripts/rabbi_cron_trigger.js and use ordinary
due scheduling. Forced manual cron runs bypass native trigger scripts and
must be restricted to operators. This gate cannot cap an already-running
provider call or independently control Codex-native child workers.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
import stat
import sys
import time
from datetime import datetime, timezone
from typing import Callable

from rabbi_quota_gate import GateDenied, evaluate

EXPECTED_AGENT = "rabbi"
EXPECTED_CAMPAIGN = "mysugya-yoma-remediation"
DEFAULT_MAX_STARTS_PER_UTC_DAY = 2
UPPER_MAX_STARTS_PER_UTC_DAY = 2


def state_dir() -> Path:
    return Path.home() / ".local" / "state" / "mysugya"


def approval_path() -> Path:
    return state_dir() / "rabbi-autonomy-approval.json"


def ledger_path() -> Path:
    return state_dir() / "rabbi-admissions.json"


def read_private_approval(path: Path) -> int:
    try:
        s = path.lstat()
    except FileNotFoundError as exc:
        raise GateDenied("private operator approval absent") from exc
    if not stat.S_ISREG(s.st_mode) or s.st_uid != os.getuid() or (s.st_mode & 0o077):
        raise GateDenied("private operator approval has unsafe ownership or mode")
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise GateDenied("private operator approval is unreadable") from exc
    if not isinstance(record, dict) or set(record) != {
        "schemaVersion", "agentId", "campaignId", "authorized", "maxStartsPerUtcDay"
    }:
        raise GateDenied("private operator approval schema mismatch")
    if record["schemaVersion"] != 1 or record["agentId"] != EXPECTED_AGENT:
        raise GateDenied("private operator approval identity mismatch")
    if record["campaignId"] != EXPECTED_CAMPAIGN or record["authorized"] is not True:
        raise GateDenied("private operator approval does not authorize this campaign")
    limit = record["maxStartsPerUtcDay"]
    if isinstance(limit, bool) or not isinstance(limit, int) or not (1 <= limit <= UPPER_MAX_STARTS_PER_UTC_DAY):
        raise GateDenied("private operator approval daily limit invalid")
    return limit


def snapshot_path() -> Path:
    return state_dir() / "rabbi-quota-snapshot.json"


def read_cached_quota(path: Path | None = None, *, now_ms: int | None = None) -> dict:
    """Fast, fail-closed quota read; NEVER calls OpenClaw or a provider.

    The refresh worker owns acquisition of Rabbi-scoped provider evidence
    well before cron is due. This function must fit inside the scheduler's
    30-second native trigger evaluation budget.
    """
    from rabbi_quota_gate import CLOCK_SKEW_MS, MAX_SNAPSHOT_AGE_MS
    from rabbi_quota_refresh import SNAPSHOT_SOURCE

    path = snapshot_path() if path is None else path
    now_ms = int(time.time() * 1000) if now_ms is None else now_ms
    try:
        parent = path.parent.stat()
        item = path.lstat()
    except (OSError, ValueError) as exc:
        raise GateDenied("cached Rabbi quota snapshot absent") from exc
    if parent.st_uid != os.getuid() or parent.st_mode & 0o077:
        raise GateDenied("cached quota directory permissions unsafe")
    if not stat.S_ISREG(item.st_mode) or item.st_uid != os.getuid() or item.st_mode & 0o077:
        raise GateDenied("cached quota snapshot permissions unsafe")
    if item.st_size < 10 or item.st_size > 4096:
        raise GateDenied("cached quota snapshot size invalid")
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as exc:
        raise GateDenied("cached quota snapshot invalid JSON") from exc
    if not isinstance(data, dict) or set(data) != {
        "schemaVersion", "source", "collectedAtMs", "payload"
    }:
        raise GateDenied("cached quota snapshot schema mismatch")
    if data["schemaVersion"] != 1 or data["source"] != SNAPSHOT_SOURCE:
        raise GateDenied("cached quota snapshot source mismatch")
    timestamp = data["collectedAtMs"]
    if isinstance(timestamp, bool) or not isinstance(timestamp, int):
        raise GateDenied("cached quota snapshot collection time invalid")
    if timestamp > now_ms + CLOCK_SKEW_MS or now_ms - timestamp > MAX_SNAPSHOT_AGE_MS:
        raise GateDenied("cached quota snapshot expired")
    if not isinstance(data["payload"], dict):
        raise GateDenied("cached quota snapshot payload invalid")
    # The normal evidence evaluator separately checks provider identity,
    # 35% floor, weekly reserve, source updatedAt and 5h capacity.
    return data["payload"]


def reserve_admission(path: Path, *, max_per_day: int, now_ms: int) -> int:
    """Atomically reserve a daily slot; fail closed if the ledger is corrupt."""
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    parent_stat = path.parent.stat()
    if parent_stat.st_uid != os.getuid() or (parent_stat.st_mode & 0o077):
        raise GateDenied("admission state directory permissions unsafe")
    if path.is_symlink():
        raise GateDenied("admission ledger must not be a symlink")
    fd = os.open(str(path), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        s = os.fstat(fd)
        if not stat.S_ISREG(s.st_mode) or s.st_uid != os.getuid() or (s.st_mode & 0o077):
            raise GateDenied("admission ledger permissions unsafe")
        fcntl.flock(fd, fcntl.LOCK_EX)
        with os.fdopen(os.dup(fd), "r+", encoding="utf-8") as fh:
            data = fh.read()
            if data.strip():
                try:
                    state = json.loads(data)
                except ValueError as exc:
                    raise GateDenied("admission ledger corrupt") from exc
                if not isinstance(state, dict) or set(state) != {"dayUtc", "starts", "lastAtMs"}:
                    raise GateDenied("admission ledger schema mismatch")
                if isinstance(state["starts"], bool) or not isinstance(state["starts"], int) or state["starts"] < 0:
                    raise GateDenied("admission ledger count invalid")
                if not isinstance(state["lastAtMs"], int) or state["lastAtMs"] > now_ms + 60000:
                    raise GateDenied("admission ledger clock invalid")
            else:
                state = {"dayUtc": "", "starts": 0, "lastAtMs": 0}
            day = datetime.fromtimestamp(now_ms / 1000, timezone.utc).strftime("%Y-%m-%d")
            if state["dayUtc"] != day:
                # A future ledger date indicates tampering/clock rollback,
                # not grounds for resetting the counter.
                if state["dayUtc"] and state["dayUtc"] > day:
                    raise GateDenied("admission ledger date is in the future")
                state = {"dayUtc": day, "starts": 0, "lastAtMs": 0}
            if state["starts"] >= max_per_day:
                raise GateDenied("daily model-work admission cap reached")
            state["starts"] += 1
            state["lastAtMs"] = now_ms
            fh.seek(0)
            fh.truncate()
            json.dump(state, fh, sort_keys=True)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
            return state["starts"]
    finally:
        os.close(fd)


def decide(
    approval_file: Path,
    ledger_file: Path,
    usage_supplier: Callable[[], dict],
    *,
    now_ms: int | None = None,
) -> dict:
    now_ms = now_ms if now_ms is not None else int(time.time() * 1000)
    cap = read_private_approval(approval_file)
    quota = evaluate(usage_supplier(), provider="openai", now_ms=now_ms)
    slot = reserve_admission(ledger_file, max_per_day=cap, now_ms=now_ms)
    return {
        "admitted": True,
        "provider": "openai",
        "dayAdmission": slot,
        "dayAdmissionLimit": cap,
        "weeklyRemainingPercent": quota["weeklyRemainingPercent"],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--approval", type=Path, default=approval_path())
    ap.add_argument("--ledger", type=Path, default=ledger_path())
    ap.add_argument("--quota-snapshot", type=Path, default=snapshot_path())
    args = ap.parse_args()
    try:
        result = decide(args.approval, args.ledger, lambda: read_cached_quota(args.quota_snapshot))
    except (GateDenied, OSError, ValueError) as exc:
        print(json.dumps({"admitted": False, "reason": str(exc)}, sort_keys=True))
        return 3
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
