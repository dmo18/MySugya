#!/usr/bin/env python3
"""Fetch fresh Rabbi-scoped OpenClaw quota OUTSIDE the 30-second cron trigger.

Run via OpenClaw's model-free command job shortly before a
fixed UTC scheduled campaign tick. Never schedule a model turn here.
Store only sanitized OpenAI windows and Claude CLI /usage percentages;
no credentials or account identities.

The fast cron admission gate reads this local snapshot; absent, stale,
incomplete, errored, or improperly scoped evidence is always denied.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import stat
import sys
import tempfile
import time

from rabbi_claude_quota import (
    configured_worker_model,
    fetch_usage as fetch_claude_usage,
    sanitized_snapshot as sanitize_claude,
    snapshot_path as claude_snapshot_path,
)
from rabbi_quota_gate import (
    CLOCK_SKEW_MS,
    GateDenied,
    MAX_SNAPSHOT_AGE_MS,
    SHORT_LABELS,
    WEEK_LABELS,
    current_status,
    _number,
    _window,
)

SNAPSHOT_SOURCE = "openclaw-status-rabbi-v1"
RECOGNIZED_LABELS = WEEK_LABELS | SHORT_LABELS


def snapshot_path() -> Path:
    return Path.home() / ".local" / "state" / "mysugya" / "rabbi-quota-snapshot.json"


def sanitize(status: dict, *, now_ms: int | None = None) -> dict:
    """Keep only quota fields from Rabbi's explicitly selected auth scope.

    Valid percent values are recorded even when below admission floor,
    allowing operators to see the real reason for an expected denial.
    """
    now_ms = int(time.time() * 1000) if now_ms is None else now_ms
    if not isinstance(status, dict) or not isinstance(status.get("usage"), dict):
        raise GateDenied("OpenClaw usage object absent")
    data = status["usage"]
    ts = _number(data.get("updatedAt"), "usage.updatedAt")
    if now_ms - ts > MAX_SNAPSHOT_AGE_MS or ts > now_ms + CLOCK_SKEW_MS:
        raise GateDenied("provider observation stale or future dated")
    if data.get("refreshing"):
        raise GateDenied("provider usage is not yet complete")
    providers = data.get("providers")
    if not isinstance(providers, list):
        raise GateDenied("provider list unavailable")
    found = [p for p in providers if isinstance(p, dict) and p.get("provider") == "openai"]
    if len(found) != 1:
        raise GateDenied("Rabbi OpenAI quota window missing or duplicated")
    p = found[0]
    if p.get("error") or p.get("status") in ("error", "unavailable", "unknown"):
        raise GateDenied("OpenAI quota source returned an error")
    windows = p.get("windows")
    if not isinstance(windows, list):
        raise GateDenied("OpenAI quota windows missing")
    if _window(windows, WEEK_LABELS, True) is None:
        raise GateDenied("weekly quota missing")
    sanitized = []
    seen_labels = set()
    for row in windows:
        if not isinstance(row, dict):
            continue
        label = str(row.get("label", "")).strip().lower()
        if label not in RECOGNIZED_LABELS:
            continue
        canonical = "Week" if label in WEEK_LABELS else "5h"
        if canonical in seen_labels:
            raise GateDenied("duplicate quota window")
        seen_labels.add(canonical)
        used = _number(row.get("usedPercent"), canonical + " usedPercent")
        if not 0 <= used <= 100:
            raise GateDenied("quota percent invalid")
        win = {"label": canonical, "usedPercent": used}
        if "resetAt" in row and row["resetAt"] is not None:
            reset = _number(row["resetAt"], canonical + " resetAt")
            if reset <= now_ms or not math.isfinite(reset):
                raise GateDenied("provider reset time invalid")
            win["resetAt"] = int(reset)
        sanitized.append(win)
    if "Week" not in seen_labels:
        raise GateDenied("no valid weekly window")
    if "5h" not in seen_labels:
        raise GateDenied("no valid OpenAI 5h window")
    return {
        "schemaVersion": 1,
        "source": SNAPSHOT_SOURCE,
        "collectedAtMs": now_ms,
        "payload": {
            "usage": {"updatedAt": int(ts), "providers": [
                {"provider": "openai", "windows": sanitized}
            ]}
        },
    }


def private_parent(path: Path) -> None:
    # The regular sandbox path is separate from this host-only state.
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    s = path.parent.stat()
    if not stat.S_ISDIR(s.st_mode) or s.st_uid != os.getuid() or s.st_mode & 0o077:
        raise GateDenied("quota snapshot directory permissions unsafe")


def write_private(snapshot: dict, path: Path) -> None:
    private_parent(path)
    if path.is_symlink():
        raise GateDenied("quota snapshot target must not be a symlink")
    if path.exists():
        s = path.lstat()
        if not stat.S_ISREG(s.st_mode) or s.st_uid != os.getuid() or s.st_mode & 0o077:
            raise GateDenied("quota snapshot destination permissions unsafe")
    fd, temp = tempfile.mkstemp(prefix=".rabbi-quota-", dir=str(path.parent))
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, separators=(",", ":"), allow_nan=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def main() -> int:
    try:
        # Both quota sources must be fresh before publishing either cache.
        # Probe budgets fit inside the existing 110-second model-free job.
        snapshot = sanitize(current_status(timeout_seconds=75))
        worker_model = configured_worker_model()
        claude = sanitize_claude(fetch_claude_usage(), worker_model=worker_model)
        write_private(snapshot, snapshot_path())
        write_private(claude, claude_snapshot_path())
        week = next(w for w in snapshot["payload"]["usage"]["providers"][0]["windows"]
                    if w["label"] == "Week")
        print(json.dumps({
            "ok": True,
            "provider": "openai",
            "weeklyRemainingPercent": 100 - week["usedPercent"],
            "claudeWeeklyRemainingPercent": claude["weeklyRemainingPercent"],
            "claudeSessionRemainingPercent": claude["sessionRemainingPercent"],
            "snapshotAgeSeconds": 0,
        }, sort_keys=True))
        return 0
    except (GateDenied, OSError, ValueError) as exc:
        # Remove stale earlier snapshot so refresh failures always deny a launch.
        for path in (snapshot_path(), claude_snapshot_path()):
            if path.is_file() and not path.is_symlink():
                try:
                    path.unlink()
                except OSError:
                    pass
        print(json.dumps({"ok": False, "reason": str(exc)}, sort_keys=True))
        return 3


if __name__ == "__main__":
    sys.exit(main())
