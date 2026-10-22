#!/usr/bin/env python3
"""Offline tests of Claude CLI quota evidence and dual-provider refresh."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

import rabbi_claude_quota as claude
import rabbi_quota_refresh as refresh
from rabbi_quota_gate import GateDenied

NOW = 1_800_000_000_000
MODEL = "anthropic/claude-future-model"


class ClaudeQuotaTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.path = self.root / "cache" / "claude.json"
        self.config = self.root / "openclaw.json"
        self.write_config("claude-cli")

    def write_config(self, runtime, model=MODEL):
        self.config.write_text(json.dumps({
            "agents": {
                "defaults": {},
                "entries": {"rabbi": {
                    "subagents": {"model": model},
                    "models": {model: {"agentRuntime": {"id": runtime}}}
                }}
            }
        }))

    def make_private(self, weekly=59, session=100):
        data = claude.sanitized_snapshot(
            {"weeklyRemaining": weekly, "currentSessionRemaining": session},
            worker_model=MODEL, now_ms=NOW,
        )
        refresh.write_private(data, self.path)
        return data

    def test_model_independent_cli_route(self):
        self.assertEqual(claude.configured_worker_model(self.config), MODEL)
        self.write_config("openclaw")
        with self.assertRaises(GateDenied):
            claude.configured_worker_model(self.config)

    def test_only_quota_fields_are_retained(self):
        data = claude.sanitized_snapshot(
            {"weeklyRemaining": 59, "currentSessionRemaining": 100,
             "authToken": "PRIVATE-AUTH", "accountEmail": "PRIVATE-ACCOUNT"},
            worker_model=MODEL, now_ms=NOW,
        )
        raw = json.dumps(data)
        self.assertNotIn("PRIVATE-AUTH", raw)
        self.assertNotIn("PRIVATE-ACCOUNT", raw)
        self.assertEqual(data["workerModel"], MODEL)

    def test_missing_invalid_or_outside_range_refused(self):
        for data in (
            {}, {"weeklyRemaining": True, "currentSessionRemaining": 100},
            {"weeklyRemaining": "59", "currentSessionRemaining": 100},
            {"weeklyRemaining": 59, "currentSessionRemaining": 101},
            {"weeklyRemaining": 59, "currentSessionRemaining": float("nan")},
        ):
            with self.subTest(data=data), self.assertRaises(GateDenied):
                claude.sanitized_snapshot(data, worker_model=MODEL, now_ms=NOW)

    def test_healthy_snapshot_is_local_only(self):
        self.make_private()
        with patch("subprocess.run", side_effect=AssertionError("provider/model call forbidden")):
            found = claude.read_cached(path=self.path, config_path=self.config, now_ms=NOW)
        self.assertEqual(found, {"weeklyRemainingPercent": 59.0, "sessionRemainingPercent": 100.0})

    def test_low_week_stale_and_low_session_denied(self):
        self.make_private(weekly=34)
        with self.assertRaises(GateDenied):
            claude.read_cached(path=self.path, config_path=self.config, now_ms=NOW)
        self.make_private(session=29)
        with self.assertRaises(GateDenied):
            claude.read_cached(path=self.path, config_path=self.config, now_ms=NOW)
        self.make_private()
        with self.assertRaises(GateDenied):
            claude.read_cached(path=self.path, config_path=self.config, now_ms=NOW + 300001)

    def test_worker_route_switch_invalidates_old_snapshot(self):
        self.make_private()
        self.write_config("claude-cli", "anthropic/claude-something-new")
        with self.assertRaises(GateDenied):
            claude.read_cached(path=self.path, config_path=self.config, now_ms=NOW)

    def test_insecure_file_symlink_and_false_source_denied(self):
        obj = self.make_private()
        self.path.chmod(0o644)
        with self.assertRaises(GateDenied):
            claude.read_cached(path=self.path, config_path=self.config, now_ms=NOW)
        self.path.chmod(0o600)
        obj["source"] = "untrusted-numbers"
        self.path.write_text(json.dumps(obj))
        with self.assertRaises(GateDenied):
            claude.read_cached(path=self.path, config_path=self.config, now_ms=NOW)
        self.path.unlink()
        self.path.symlink_to(self.root / "no-file")
        with self.assertRaises(GateDenied):
            claude.read_cached(path=self.path, config_path=self.config, now_ms=NOW)

    def test_probe_timeout_or_missing_script_denied(self):
        path = self.root / "probe.py"
        path.write_text("print('not invoked')")
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("claude", 25)):
            with self.assertRaises(GateDenied):
                claude.fetch_usage(probe_path=path)
        with self.assertRaises(GateDenied):
            claude.fetch_usage(probe_path=self.root / "missing.py")

    def test_dual_refresh_success_and_failure_clears_both_caches(self):
        now = int(time.time() * 1000)
        status = {"usage": {"updatedAt": now - 1000, "providers": [
            {"provider": "openai", "windows": [
                {"label": "Week", "usedPercent": 40, "resetAt": now + 3600000},
                {"label": "5h", "usedPercent": 20, "resetAt": now + 3600000},
            ]}
        ]}}
        openai_file = self.root / "cache" / "openai.json"
        with (
            patch.object(refresh, "current_status", return_value=status),
            patch.object(refresh, "configured_worker_model", return_value=MODEL),
            patch.object(refresh, "fetch_claude_usage", return_value={
                "weeklyRemaining": 59, "currentSessionRemaining": 100,
            }) as claude_probe,
            patch.object(refresh, "snapshot_path", return_value=openai_file),
            patch.object(refresh, "claude_snapshot_path", return_value=self.path),
        ):
            self.assertEqual(refresh.main(), 0)
            claude_probe.assert_called_once()
            self.assertTrue(openai_file.is_file())
            self.assertTrue(self.path.is_file())
        with (
            patch.object(refresh, "current_status", return_value=status),
            patch.object(refresh, "configured_worker_model", return_value=MODEL),
            patch.object(refresh, "fetch_claude_usage", side_effect=GateDenied("offline")),
            patch.object(refresh, "snapshot_path", return_value=openai_file),
            patch.object(refresh, "claude_snapshot_path", return_value=self.path),
        ):
            self.assertEqual(refresh.main(), 3)
        self.assertFalse(openai_file.exists())
        self.assertFalse(self.path.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
