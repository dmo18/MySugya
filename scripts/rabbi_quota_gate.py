#!/usr/bin/env python3
"""Fail-closed, no-LLM provider-quota preflight for OpenClaw Rabbi.

Reads OpenClaw's own current provider usage via:
    openclaw status --usage --agent rabbi --json

Never invokes Rabbi, any other agent, a cron job, or any model. It does
not remove a manual operator stop or authorize a scheduled campaign.
Future launch code must call this preflight immediately before EACH
model-powered work unit, and bind the checked provider to the actual
worker route. A preflight alone is not a hard mid-run spending cutoff.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import time
from typing import Any

ADMISSION_FLOOR_PERCENT = 35
WEEKLY_RESERVE_PERCENT = 30
MAX_UNIT_HEADROOM_PERCENT = 2
SHORT_WINDOW_FLOOR_PERCENT = 15
MAX_SNAPSHOT_AGE_MS = 5 * 60 * 1000
CLOCK_SKEW_MS = 60 * 1000

# The provider window labels are deliberately narrow. A new schema or an
# unknown usage interpretation must be investigated, not guessed.
WEEK_LABELS = frozenset({"week", "weekly", "7d"})
SHORT_LABELS = frozenset({"5h", "5-hour", "5hour"})


class GateDenied(Exception):
    """Expected refusal, including missing or untrusted quota telemetry."""


def _number(value: Any, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise GateDenied(f"{path} must be a number")
    num = float(value)
    if not math.isfinite(num):
        raise GateDenied(f"{path} must be finite")
    return num


def _window(windows: list, labels: frozenset[str], required: bool) -> dict | None:
    matches = [
        w for w in windows
        if isinstance(w, dict) and str(w.get("label", "")).strip().lower() in labels
    ]
    if len(matches) > 1:
        raise GateDenied("duplicate provider window labels")
    if required and not matches:
        raise GateDenied("provider weekly quota window missing")
    return matches[0] if matches else None


def evaluate(status: dict, *, provider: str = "openai", now_ms: int | None = None) -> dict:
    """Return only sanitized, noncredential quota facts if admission is safe.

    Missing/stale/contradictory snapshots or insufficient provider capacity
    raise GateDenied. No input from a model or work-unit manifest counts as
    a trusted provider usage observation.
    """
    if not isinstance(status, dict):
        raise GateDenied("usage response must be a JSON object")
    usage = status.get("usage")
    if not isinstance(usage, dict):
        raise GateDenied("usage section missing")
    observed_at = _number(usage.get("updatedAt"), "usage.updatedAt")
    now_ms = now_ms if now_ms is not None else int(time.time() * 1000)
    if observed_at > now_ms + CLOCK_SKEW_MS or now_ms - observed_at > MAX_SNAPSHOT_AGE_MS:
        raise GateDenied("quota telemetry stale or from future")
    providers = usage.get("providers")
    if not isinstance(providers, list):
        raise GateDenied("provider usage list missing")
    selected = [
        item for item in providers
        if isinstance(item, dict) and item.get("provider") == provider
    ]
    if len(selected) != 1:
        raise GateDenied("requested provider missing or duplicated")
    item = selected[0]
    if item.get("error") or item.get("status") in ("error", "unknown", "unavailable"):
        raise GateDenied("provider usage unavailable")
    windows = item.get("windows")
    if not isinstance(windows, list) or not windows:
        raise GateDenied("provider windows missing")
    weekly = _window(windows, WEEK_LABELS, True)
    weekly_used = _number(weekly.get("usedPercent"), "weekly usedPercent")
    if not 0 <= weekly_used <= 100:
        raise GateDenied("weekly percentage outside [0,100]")
    weekly_remaining = 100 - weekly_used
    reset_at = weekly.get("resetAt")
    if reset_at is not None:
        reset_at = _number(reset_at, "weekly resetAt")
        if reset_at <= now_ms:
            raise GateDenied("weekly reset time is not in the future")
    if weekly_remaining < ADMISSION_FLOOR_PERCENT:
        raise GateDenied(
            f"weekly remaining {weekly_remaining:g}% below {ADMISSION_FLOOR_PERCENT}% admission floor"
        )
    if weekly_remaining - MAX_UNIT_HEADROOM_PERCENT < WEEKLY_RESERVE_PERCENT:
        raise GateDenied("weekly reserve would be endangered by bounded unit headroom")
    short = _window(windows, SHORT_LABELS, False)
    # OpenAI Codex admission requires BOTH independent quota windows. If
    # the short window disappears, its capacity is unknown, not unlimited.
    if provider == "openai" and short is None:
        raise GateDenied("OpenAI 5h quota window missing")
    short_remaining = None
    if short is not None:
        short_used = _number(short.get("usedPercent"), "5h usedPercent")
        if not 0 <= short_used <= 100:
            raise GateDenied("5h percentage outside [0,100]")
        short_remaining = 100 - short_used
        if short_remaining < SHORT_WINDOW_FLOOR_PERCENT:
            raise GateDenied("5h capacity below short-window floor")
    return {
        "admitted": True,
        "provider": provider,
        "weeklyRemainingPercent": weekly_remaining,
        "shortWindowRemainingPercent": short_remaining,
        "minimumWeeklyRemainingPercent": ADMISSION_FLOOR_PERCENT,
        "weeklyReservePercent": WEEKLY_RESERVE_PERCENT,
        "nominalMaximumUnitHeadroomPercent": MAX_UNIT_HEADROOM_PERCENT,
        "observationAgeMs": max(0, now_ms - observed_at),
    }


def current_status(*, timeout_seconds: int = 100) -> dict:
    """Obtain fresh quota telemetry without starting any model turn."""
    try:
        proc = subprocess.run(
            ["openclaw", "status", "--usage", "--agent", "rabbi", "--json", "--timeout", "90000"],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise GateDenied("OpenClaw usage probe timed out; admission denied") from exc
    if proc.returncode != 0:
        raise GateDenied("OpenClaw provider usage query failed")
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise GateDenied("OpenClaw did not return a valid JSON usage snapshot") from exc
    if not isinstance(payload, dict):
        raise GateDenied("OpenClaw usage output has unexpected type")
    return payload


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--provider", choices=("openai", "anthropic"), default="openai",
        help="the actual provider about to be used by a separate, authorized runner",
    )
    args = ap.parse_args()
    try:
        result = evaluate(current_status(), provider=args.provider)
    except (GateDenied, OSError, subprocess.TimeoutExpired) as exc:
        # Only the reason, not auth profiles or raw OpenClaw output.
        print(json.dumps({"admitted": False, "reason": str(exc)}, sort_keys=True))
        return 3
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
