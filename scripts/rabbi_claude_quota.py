#!/usr/bin/env python3
"""Fail-closed Claude CLI subscription quota evidence for Rabbi; never call a model.

The model-free refresh job invokes the existing local Claude /usage probe.
Scheduled admission reads a private, five-minute cache. The current model and
CLI runtime are resolved from OpenClaw, never pinned to a model version here.

NOTE: A Claude CLI runtime is necessary but not sufficient to prove that the
worker and /usage probe select the same billing account. Verify that separately
before enabling Rabbi.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import stat
import subprocess
import time

from rabbi_quota_gate import CLOCK_SKEW_MS, GateDenied, MAX_SNAPSHOT_AGE_MS

SOURCE = "claude-cli-usage-rabbi-v1"
WEEKLY_FLOOR = 35
SESSION_FLOOR = 30
PROBE_TIMEOUT_SECONDS = 25


def snapshot_path() -> Path:
    return Path.home() / ".local/state/mysugya/rabbi-claude-quota-snapshot.json"


def configured_worker_model(config_path: Path | None = None) -> str:
    """Resolve the current worker ref and exact CLI runtime from OpenClaw."""
    config_path = config_path or Path.home() / ".openclaw/openclaw.json"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        agents = config["agents"]
        rabbi = agents["entries"]["rabbi"]
        defaults = agents.get("defaults", {})
        model = rabbi["subagents"]["model"]
        if isinstance(model, dict):
            model = model.get("primary")
        if not isinstance(model, str) or not model.startswith("anthropic/"):
            raise GateDenied("Rabbi worker is not an Anthropic model")
        policies = rabbi.get("models") or {}
        shared = defaults.get("models") or {}
        route = (policies.get(model) or {}).get("agentRuntime")
        if route is None:
            route = (shared.get(model) or {}).get("agentRuntime")
        if route is None:
            route = rabbi.get("agentRuntime") or defaults.get("agentRuntime")
        if not isinstance(route, dict) or route.get("id") != "claude-cli":
            raise GateDenied("Rabbi worker is not explicitly on Claude CLI")
        return model
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        raise GateDenied("cannot verify Rabbi Claude worker route") from exc


def fetch_usage(*, timeout_seconds: int = PROBE_TIMEOUT_SECONDS,
                probe_path: Path | None = None) -> dict:
    """Run the existing local /usage probe (not an LLM prompt)."""
    probe = probe_path or Path.home() / ".openclaw/tools/quota-watch/claude-quota-probe.py"
    if probe.is_symlink() or not probe.is_file():
        raise GateDenied("Claude quota probe missing or a symlink")
    try:
        proc = subprocess.run(
            ["/usr/bin/python3", str(probe)],
            capture_output=True, text=True, timeout=timeout_seconds, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GateDenied("Claude subscription quota probe unavailable") from exc
    if proc.returncode:
        raise GateDenied("Claude subscription quota probe failed")
    try:
        value = json.loads(proc.stdout)
    except ValueError as exc:
        raise GateDenied("Claude subscription quota response invalid") from exc
    if not isinstance(value, dict):
        raise GateDenied("Claude subscription quota object missing")
    return value


def sanitized_snapshot(probe: dict, *, worker_model: str,
                       now_ms: int | None = None) -> dict:
    now_ms = int(time.time() * 1000) if now_ms is None else now_ms
    if not isinstance(probe, dict):
        raise GateDenied("Claude quota response missing")
    if not isinstance(worker_model, str) or not worker_model.startswith("anthropic/"):
        raise GateDenied("invalid Claude worker model scope")
    week = probe.get("weeklyRemaining")
    session = probe.get("currentSessionRemaining")
    for label, value in (("weekly", week), ("session", session)):
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or not 0 <= value <= 100):
            raise GateDenied("Claude " + label + " quota percentage invalid")
    return {
        "schemaVersion": 1,
        "source": SOURCE,
        "collectedAtMs": now_ms,
        "workerModel": worker_model,
        "workerRuntime": "claude-cli",
        "weeklyRemainingPercent": float(week),
        "sessionRemainingPercent": float(session),
    }


def read_cached(*, path: Path | None = None, config_path: Path | None = None,
                now_ms: int | None = None) -> dict:
    """Validate freshness, private file, selected worker and both quota floors."""
    path = path or snapshot_path()
    now_ms = int(time.time() * 1000) if now_ms is None else now_ms
    try:
        parent = path.parent.stat()
        item = path.lstat()
    except OSError as exc:
        raise GateDenied("cached Claude quota evidence absent") from exc
    if parent.st_uid != os.getuid() or parent.st_mode & 0o077:
        raise GateDenied("cached Claude quota directory permissions unsafe")
    if (not stat.S_ISREG(item.st_mode) or item.st_uid != os.getuid()
            or item.st_mode & 0o077 or item.st_size < 10 or item.st_size > 4096):
        raise GateDenied("cached Claude quota file unsafe")
    try:
        evidence = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise GateDenied("cached Claude quota evidence unreadable") from exc
    if (not isinstance(evidence, dict) or set(evidence) != {
        "schemaVersion", "source", "collectedAtMs", "workerModel",
        "workerRuntime", "weeklyRemainingPercent", "sessionRemainingPercent"
    } or evidence["schemaVersion"] != 1 or evidence["source"] != SOURCE
            or evidence["workerRuntime"] != "claude-cli"):
        raise GateDenied("cached Claude quota source or schema invalid")
    observed = evidence["collectedAtMs"]
    if (isinstance(observed, bool) or not isinstance(observed, int)
            or observed > now_ms + CLOCK_SKEW_MS
            or now_ms - observed > MAX_SNAPSHOT_AGE_MS):
        raise GateDenied("cached Claude quota evidence expired")
    if evidence["workerModel"] != configured_worker_model(config_path):
        raise GateDenied("Claude worker selection changed since quota refresh")
    for field, floor in (
        ("weeklyRemainingPercent", WEEKLY_FLOOR),
        ("sessionRemainingPercent", SESSION_FLOOR),
    ):
        value = evidence[field]
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or not 0 <= value <= 100):
            raise GateDenied("cached Claude quota percentage invalid")
        if value < floor:
            raise GateDenied("Claude " + field + " below admission floor")
    return {
        "weeklyRemainingPercent": evidence["weeklyRemainingPercent"],
        "sessionRemainingPercent": evidence["sessionRemainingPercent"],
    }
