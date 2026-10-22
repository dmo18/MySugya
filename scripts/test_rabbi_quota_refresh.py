#!/usr/bin/env python3
"""Tests for model-free, Rabbi-scoped provider usage refresh and sanitation."""
from __future__ import annotations

import copy
import json
import stat
import tempfile
from pathlib import Path
import unittest

import rabbi_quota_refresh as refresh
from rabbi_quota_gate import GateDenied

NOW = 1_800_000_000_000


def response(used=79, five_hour=25):
    return {
        "runtimeVersion": "2026.10.5",
        "host": "PRIVATE-HOST",
        "auth": {"token": "PRIVATE-AUTH"},
        "usage": {
            "updatedAt": NOW - 1_000,
            "providers": [{
                "provider": "openai",
                "accountEmail": "PRIVATE-ACCOUNT",
                "authToken": "PRIVATE-AUTH",
                "windows": [
                    {"label": "Week", "usedPercent": used, "resetAt": NOW + 3_600_000},
                    {"label": "5h", "usedPercent": five_hour, "resetAt": NOW + 2_000_000},
                ],
            }],
        },
    }


class TestQuotaRefresh(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / "cache" / "snapshot.json"

    def test_sanitizes_private_data_even_below_floor(self):
        data = refresh.sanitize(response(), now_ms=NOW)
        self.assertEqual(data["source"], refresh.SNAPSHOT_SOURCE)
        self.assertEqual(data["payload"]["usage"]["providers"][0]["windows"][0]["usedPercent"], 79)
        serialized = json.dumps(data)
        for secret in ("PRIVATE-HOST", "PRIVATE-AUTH", "PRIVATE-ACCOUNT", "runtimeVersion"):
            self.assertNotIn(secret, serialized)
        refresh.write_private(data, self.path)
        self.assertTrue(self.path.is_file())
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.path.parent.stat().st_mode & 0o777, 0o700)

    def test_missing_or_untrusted_provider_refused(self):
        for bad in ({}, {"usage": {"updatedAt": NOW, "providers": []}}):
            with self.assertRaises(GateDenied):
                refresh.sanitize(bad, now_ms=NOW)

    def test_source_error_and_refreshing_deny(self):
        for change in ({"error": "Timeout"}, {"status": "unknown"}):
            p = response()
            p["usage"]["providers"][0].update(change)
            with self.assertRaises(GateDenied):
                refresh.sanitize(p, now_ms=NOW)
        p = response()
        p["usage"]["refreshing"] = True
        with self.assertRaises(GateDenied):
            refresh.sanitize(p, now_ms=NOW)

    def test_invalid_percent_and_duplicate_windows_refused(self):
        for bad in (-1, 101, "60", True, None, float("nan")):
            p = response()
            p["usage"]["providers"][0]["windows"][0]["usedPercent"] = bad
            with self.assertRaises(GateDenied):
                refresh.sanitize(p, now_ms=NOW)
        p = response()
        p["usage"]["providers"][0]["windows"].append({"label": "weekly", "usedPercent": 20})
        with self.assertRaises(GateDenied):
            refresh.sanitize(p, now_ms=NOW)

    def test_future_expired_and_stale_quota_refused(self):
        p = response()
        p["usage"]["updatedAt"] = NOW - 500_000
        with self.assertRaises(GateDenied):
            refresh.sanitize(p, now_ms=NOW)
        p = response()
        p["usage"]["providers"][0]["windows"][0]["resetAt"] = NOW - 2
        with self.assertRaises(GateDenied):
            refresh.sanitize(p, now_ms=NOW)

    def test_symlink_destination_refused(self):
        self.path.parent.mkdir(mode=0o700)
        target = self.root / "target"
        target.write_text("DO_NOT_TOUCH")
        self.path.symlink_to(target)
        with self.assertRaises(GateDenied):
            refresh.write_private(refresh.sanitize(response(), now_ms=NOW), self.path)
        self.assertEqual(target.read_text(), "DO_NOT_TOUCH")

    def test_fail_if_cache_parent_is_world_readable(self):
        self.path.parent.mkdir(mode=0o755)
        with self.assertRaises(GateDenied):
            refresh.write_private(refresh.sanitize(response(), now_ms=NOW), self.path)

    def test_do_not_fetch_models_or_start_agent(self):
        self.assertFalse(hasattr(refresh, "run_agent"))
        self.assertFalse(hasattr(refresh, "enable_campaign"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
