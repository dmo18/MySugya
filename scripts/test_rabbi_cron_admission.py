#!/usr/bin/env python3
"""Offline tests of the private, headless Rabbi cron admission safety gate."""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest

from rabbi_cron_admission import decide
from rabbi_quota_gate import GateDenied

NOW = 1_800_000_000_000


def snapshot(weekly_used=60):
    return {
        "usage": {
            "updatedAt": NOW - 1000,
            "providers": [{
                "provider": "openai",
                "windows": [
                    {"label": "5h", "usedPercent": 10, "resetAt": NOW + 3_600_000},
                    {"label": "Week", "usedPercent": weekly_used, "resetAt": NOW + 3600_000},
                ],
            }],
        },
    }


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.approval = self.dir / "operator-approval.json"
        self.ledger = self.dir / "private-state" / "ledger.json"
        self.authorize()

    def authorize(self, *, approved=True, limit=2):
        self.approval.write_text(json.dumps({
            "schemaVersion": 1,
            "agentId": "rabbi",
            "campaignId": "mysugya-yoma-remediation",
            "authorized": approved,
            "maxStartsPerUtcDay": limit,
        }), encoding="utf-8")
        self.approval.chmod(0o600)

    def check(self, used=60, at=NOW):
        return decide(self.approval, self.ledger, lambda: snapshot(used), now_ms=at)

    def deny(self, used=60, at=NOW):
        with self.assertRaises(GateDenied):
            self.check(used, at)

    def test_absent_operator_authorization_denies_without_launch(self):
        self.approval.unlink()
        self.deny()
        self.assertFalse(self.ledger.exists())

    def test_operator_false_never_queries_provider(self):
        self.authorize(approved=False)
        called = []
        with self.assertRaises(GateDenied):
            decide(self.approval, self.ledger, lambda: called.append(True), now_ms=NOW)
        self.assertFalse(called)

    def test_wrong_campaign_and_invalid_limit_denied(self):
        self.authorize(limit=0)
        self.deny()
        self.authorize(limit=7)
        self.deny()
        self.authorize(limit=3)
        self.deny()
        self.authorize()
        d = json.loads(self.approval.read_text())
        d["campaignId"] = "other-campaign"
        self.approval.write_text(json.dumps(d))
        self.deny()

    def test_insecure_marker_or_symlink_rejected(self):
        self.approval.chmod(0o644)
        self.deny()
        self.approval.unlink()
        self.approval.symlink_to(self.dir / "nonexistent")
        self.deny()

    def test_weekly_21_percent_is_blocked(self):
        self.deny(used=79)
        self.assertFalse(self.ledger.exists())

    def test_two_per_day_are_allowed_not_three(self):
        a = self.check()
        b = self.check()
        self.assertTrue(a["admitted"])
        self.assertEqual(a["dayAdmission"], 1)
        self.assertEqual(b["dayAdmission"], 2)
        self.deny()
        state = json.loads(self.ledger.read_text())
        self.assertEqual(state["starts"], 2)

    def test_private_ledger_is_0600_and_persists(self):
        self.check()
        self.assertEqual(self.ledger.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.ledger.parent.stat().st_mode & 0o777, 0o700)

    def test_ledger_corruption_fails_closed(self):
        self.check()
        self.ledger.write_text("not json")
        self.deny()

    def test_ledger_symlink_fails_closed(self):
        other = self.dir / "elsewhere"
        other.write_text('{"dayUtc": "", "starts": 0, "lastAtMs": 0}')
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        self.ledger.symlink_to(other)
        self.deny()

    def test_ledger_future_clock_fails_closed(self):
        self.check()
        state = json.loads(self.ledger.read_text())
        state["dayUtc"] = "2999-01-01"
        self.ledger.write_text(json.dumps(state))
        self.deny()

    def test_quota_probe_errors_do_not_count_as_admission(self):
        def exploded():
            raise GateDenied("provider unavailable")
        with self.assertRaises(GateDenied):
            decide(self.approval, self.ledger, exploded, now_ms=NOW)
        self.assertFalse(self.ledger.exists())

    def test_next_utc_day_restarts_counter_with_fresh_snapshot(self):
        self.check()
        new_now = NOW + 86_400_000
        def fresh():
            x = snapshot()
            x["usage"]["updatedAt"] = new_now - 1000
            x["usage"]["providers"][0]["windows"][0]["resetAt"] = new_now + 100000
            x["usage"]["providers"][0]["windows"][1]["resetAt"] = new_now + 100000
            return x
        nxt = decide(self.approval, self.ledger, fresh, now_ms=new_now)
        self.assertEqual(nxt["dayAdmission"], 1)

    def test_private_file_rejects_unapproved_unknown_fields(self):
        d = json.loads(self.approval.read_text())
        d["bypassQuota"] = True
        self.approval.write_text(json.dumps(d))
        self.deny()


    def write_snapshot(self, used=60):
        from rabbi_quota_refresh import sanitize
        folder = self.dir / "private-cache"
        folder.mkdir(mode=0o700, exist_ok=True)
        target = folder / "quota.json"
        target.write_text(json.dumps(sanitize(snapshot(used), now_ms=NOW)), encoding="utf-8")
        target.chmod(0o600)
        return target

    def test_cached_quota_is_fast_and_makes_no_provider_call(self):
        from rabbi_cron_admission import read_cached_quota
        from unittest.mock import patch
        path = self.write_snapshot()
        with patch("subprocess.run", side_effect=AssertionError("model/provider query forbidden")):
            quota = read_cached_quota(path, now_ms=NOW)
        self.assertEqual(quota["usage"]["providers"][0]["provider"], "openai")

    def test_cached_quota_missing_and_expired_denied(self):
        from rabbi_cron_admission import read_cached_quota
        from rabbi_quota_gate import MAX_SNAPSHOT_AGE_MS
        with self.assertRaises(GateDenied):
            read_cached_quota(self.dir / "absent", now_ms=NOW)
        target = self.write_snapshot()
        with self.assertRaises(GateDenied):
            read_cached_quota(target, now_ms=NOW + MAX_SNAPSHOT_AGE_MS + 1)

    def test_cached_quota_symlink_bad_permissions_or_invalid_source_denied(self):
        from rabbi_cron_admission import read_cached_quota
        target = self.write_snapshot()
        target.chmod(0o644)
        with self.assertRaises(GateDenied):
            read_cached_quota(target, now_ms=NOW)
        target.chmod(0o600)
        d = json.loads(target.read_text())
        d["source"] = "operator-provided-numbers"
        target.write_text(json.dumps(d))
        with self.assertRaises(GateDenied):
            read_cached_quota(target, now_ms=NOW)
        target.unlink()
        target.symlink_to(self.dir / "nothing")
        with self.assertRaises(GateDenied):
            read_cached_quota(target, now_ms=NOW)

    def test_cached_quota_respects_weekly_threshold_and_preserves_ledger(self):
        from rabbi_cron_admission import read_cached_quota
        target = self.write_snapshot(used=79)
        with self.assertRaises(GateDenied):
            decide(self.approval, self.ledger, lambda: read_cached_quota(target, now_ms=NOW), now_ms=NOW)
        self.assertFalse(self.ledger.exists())
        self.write_snapshot(used=60)
        result = decide(self.approval, self.ledger, lambda: read_cached_quota(target, now_ms=NOW), now_ms=NOW)
        self.assertEqual(result["dayAdmission"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
