#!/usr/bin/env python3
"""No-network tests for a host-only, non-reentrant Rabbi dispatcher."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import rabbi_host_dispatch as host
from rabbi_quota_gate import GateDenied

JOB_ID = "not-a-secret-job-id"
MODEL = "openai/gpt-test"
BINARY = "fake-openclaw"


def job():
    return {
        "id": JOB_ID,
        "name": "Rabbi Yoma Autonomous Campaign",
        "agentId": "rabbi",
        "enabled": False,
        "sessionTarget": "isolated",
        "payload": {
            "kind": "agentTurn", "model": MODEL,
            "timeoutSeconds": 900, "fallbacks": [],
        },
        "trigger": {"script": "return {fire:false}"},
    }


class TestOwnerDispatcher(unittest.TestCase):
    def test_exact_job_contract_accepts_disabled_pinned_job(self):
        host.check_job(job(), JOB_ID, MODEL)

    def test_wrong_job_state_and_model_fail_closed(self):
        mutations = [
            ("enabled", True),
            ("agentId", "main"),
            ("sessionTarget", "main"),
            ("name", "Another job"),
            ("trigger", {}),
            ("payload", {"kind": "agentTurn", "model": MODEL,
                         "timeoutSeconds": 900, "fallbacks": ["anthropic/model"]}),
            ("payload", {"kind": "agentTurn", "model": MODEL,
                         "timeoutSeconds": 1800, "fallbacks": []}),
            ("payload", {"kind": "agentTurn", "model": None,
                         "timeoutSeconds": 900, "fallbacks": []}),
        ]
        for key, value in mutations:
            bad = copy.deepcopy(job())
            bad[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(GateDenied):
                host.check_job(bad, JOB_ID, MODEL)
        with self.assertRaises(GateDenied):
            host.check_job(job(), JOB_ID, "anthropic/model")

    def test_cron_inspection_sanitizes_errors(self):
        with patch.object(host.subprocess, "run", return_value=SimpleNamespace(
            returncode=0, stdout=json.dumps({"job": job()}),
        )) as cmd:
            self.assertEqual(host.get_job(BINARY, JOB_ID)["agentId"], "rabbi")
        self.assertEqual(cmd.call_args.args[0],
                         [BINARY, "cron", "get", JOB_ID, "--json"])
        with patch.object(host.subprocess, "run", return_value=SimpleNamespace(
            returncode=2, stdout="sensitive info", stderr="sensitive key",
        )):
            with self.assertRaises(GateDenied) as got:
                host.get_job(BINARY, JOB_ID)
        self.assertNotIn("sensitive", str(got.exception))

    def test_lock_enforces_non_reentrancy_and_permissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "state" / "dispatch.lock"
            fd = host.private_lock(target)
            try:
                self.assertEqual(target.stat().st_mode & 0o777, 0o600)
                self.assertEqual(target.parent.stat().st_mode & 0o777, 0o700)
                with self.assertRaises(GateDenied):
                    host.private_lock(target)
            finally:
                import os
                os.close(fd)

    def test_read_only_check_does_not_reserve_or_launch(self):
        with patch.object(host, "get_job", return_value=job()), \
             patch.object(host, "read_private_approval", return_value=2), \
             patch.object(host, "read_cached_quota", return_value={}), \
             patch.object(host, "evaluate", return_value={"admitted": True}), \
             patch.object(host, "decide", side_effect=AssertionError("no ledger reservations")), \
             patch.object(host, "_dispatch", side_effect=AssertionError("no runs")):
            self.assertEqual(host.main(["--job-id", JOB_ID,
                                        "--expected-model", MODEL]), 0)

    def test_run_requires_current_gate_and_never_retries(self):
        ok = {"admitted": True, "provider": "openai"}
        with patch.object(host, "decide", return_value=ok) as gate, \
             patch.object(host.subprocess, "run", return_value=SimpleNamespace(returncode=0)) as cmd:
            host._dispatch(BINARY, JOB_ID)
        self.assertEqual(gate.call_count, 1)
        self.assertEqual(cmd.call_count, 1)
        argv = cmd.call_args.args[0]
        self.assertEqual(argv[:4], [BINARY, "cron", "run", JOB_ID])
        self.assertIn("--wait", argv)

        with patch.object(host, "decide", side_effect=GateDenied("quota")) as gate, \
             patch.object(host.subprocess, "run", side_effect=AssertionError("no provider run")):
            with self.assertRaises(GateDenied):
                host._dispatch(BINARY, JOB_ID)
        self.assertEqual(gate.call_count, 1)

        with patch.object(host, "decide", return_value=ok), \
             patch.object(host.subprocess, "run", return_value=SimpleNamespace(returncode=1)) as cmd:
            with self.assertRaises(GateDenied):
                host._dispatch(BINARY, JOB_ID)
        self.assertEqual(cmd.call_count, 1)

    def test_disabled_and_unpinned_gate_denies_before_reserving(self):
        broken = job()
        broken["enabled"] = True
        with patch.object(host, "get_job", return_value=broken), \
             patch.object(host, "decide", side_effect=AssertionError("no quota reservation")), \
             patch.object(host, "state_dir", return_value=Path(tempfile.gettempdir())):
            self.assertEqual(host.main(["--job-id", JOB_ID,
                                        "--expected-model", MODEL]), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
