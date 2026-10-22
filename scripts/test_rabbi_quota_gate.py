#!/usr/bin/env python3
"""No-provider-call regression tests for Rabbi's quota admission guard."""
from __future__ import annotations

import copy
import json
import unittest

import rabbi_quota_gate as gate

NOW = 1_800_000_000_000


def snapshot(*, week_used=60, short_used=20, age=1_000):
    return {
        "usage": {
            "updatedAt": NOW - age,
            "providers": [{
                "provider": "openai",
                "displayName": "OpenAI",
                "windows": [
                    {"label": "5h", "usedPercent": short_used, "resetAt": NOW + 3600000},
                    {"label": "Week", "usedPercent": week_used, "resetAt": NOW + 259200000},
                ],
            }],
        },
    }


class TestQuotaGuard(unittest.TestCase):
    def check(self, obj):
        return gate.evaluate(obj, now_ms=NOW)

    def deny(self, obj):
        with self.assertRaises(gate.GateDenied):
            self.check(obj)

    def test_healthy_week(self):
        result = self.check(snapshot(week_used=60))
        self.assertTrue(result["admitted"])
        self.assertEqual(result["weeklyRemainingPercent"], 40)

    def test_evidence_22_percent_remaining_refused(self):
        self.deny(snapshot(week_used=78))

    def test_35_percent_floor_inclusive(self):
        self.assertEqual(self.check(snapshot(week_used=65))["weeklyRemainingPercent"], 35)
        self.deny(snapshot(week_used=65.001))

    def test_no_telemetry_fails_closed(self):
        self.deny({})
        self.deny({"usage": {"updatedAt": NOW, "providers": []}})
        self.deny({"usage": {"updatedAt": NOW, "providers": [{"provider": "openai"}]}})

    def test_bogus_provider_and_duplicate_refused(self):
        p = snapshot()
        with self.assertRaises(gate.GateDenied):
            gate.evaluate(p, provider="anthropic", now_ms=NOW)
        p["usage"]["providers"].append(copy.deepcopy(p["usage"]["providers"][0]))
        self.deny(p)

    def test_duplicates_and_unknown_windows_refused(self):
        p = snapshot()
        p["usage"]["providers"][0]["windows"].append({"label": "weekly", "usedPercent": 0})
        self.deny(p)
        p = snapshot()
        p["usage"]["providers"][0]["windows"][1]["label"] = "month"
        self.deny(p)

    def test_malformed_percent_refused(self):
        for bad in (-1, 101, "20", True, None, float("nan")):
            p = snapshot()
            p["usage"]["providers"][0]["windows"][1]["usedPercent"] = bad
            self.deny(p)

    def test_stale_future_and_expired_reset_refused(self):
        self.deny(snapshot(age=gate.MAX_SNAPSHOT_AGE_MS + 1))
        self.deny(snapshot(age=-gate.CLOCK_SKEW_MS - 1))
        p = snapshot()
        p["usage"]["providers"][0]["windows"][1]["resetAt"] = NOW - 1
        self.deny(p)

    def test_short_term_capability_refused(self):
        self.deny(snapshot(short_used=86))
        self.check(snapshot(short_used=85))

    def test_source_provider_errors_and_unknown(self):
        for val in ({"error": "Timeout"}, {"status": "unknown"}):
            p = snapshot()
            p["usage"]["providers"][0].update(val)
            self.deny(p)

    def test_gate_never_exposes_provider_private_fields(self):
        p = snapshot()
        p["usage"]["providers"][0]["authToken"] = "DO_NOT_ECHO"
        assert "DO_NOT_ECHO" not in json.dumps(self.check(p))

    def test_no_model_calls_on_import(self):
        # This test suite only calls the pure evaluate() helper.
        # current_status() is a separate read-only CLI invocation.
        self.assertFalse(hasattr(gate, "launch_agent"))
        self.assertFalse(hasattr(gate, "enable_cron"))


    def test_usage_cli_receives_sufficient_deadline(self):
        import subprocess
        from unittest.mock import patch
        from types import SimpleNamespace
        from rabbi_quota_gate import current_status
        response = SimpleNamespace(returncode=0, stdout='{"usage": {"updatedAt": 123, "providers": []}}')
        with patch("rabbi_quota_gate.subprocess.run", return_value=response) as mocked:
            result = current_status()
        self.assertIn("usage", result)
        args, kwargs = mocked.call_args
        self.assertEqual(args[0][-2:], ["--timeout", "90000"])
        self.assertGreater(kwargs["timeout"], 90)

    def test_usage_timeout_is_fail_closed_and_sanitized(self):
        import subprocess
        from unittest.mock import patch
        from rabbi_quota_gate import current_status
        error = subprocess.TimeoutExpired(cmd=["openclaw", "status"], timeout=100)
        with patch("rabbi_quota_gate.subprocess.run", side_effect=error):
            with self.assertRaises(gate.GateDenied) as caught:
                current_status()
        self.assertIn("timed out", str(caught.exception))
        self.assertNotIn("token", str(caught.exception).lower())

if __name__ == "__main__":
    unittest.main(verbosity=2)
