#!/usr/bin/env python3
"""Adversarial tests for the shadow-mode OpenClaw integration adapter.

Proves: read-only behavior (no live state ever mutated), exact fixed
productContractId/campaignId binding (never caller-trusted), exact repoSha
binding, fail-closed rejection of cross-contract readStatePath snapshots
(never silently discarded/replaced), a fixed filesystem sandbox root for
both --output-state and readStatePath (rejecting traversal, symlink escape,
and reserved remediation-state filenames), hardened atomic writes, and
rejection of malformed/stale evidence, wrong-repo-sha requests, out-of-scope
paths/commands, per-unit mode, and any attempt to request a mutating
lifecycle transition under shadow mode.
"""

import copy
import json
import os
import shutil
import subprocess
import tempfile
import unittest
import uuid

import autonomy_controller as ac
import autonomy_shadow_adapter as asa


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def real_head_sha() -> str:
    out = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


def base_unit(**overrides):
    unit = {
        "unitId": "shadow-canary-unit",
        "unitClass": "controller-shadow-integration",
        "worktree": "/tmp/shadow-canary",
        "baseSha": "irrelevant-base-sha",
        "allowedPaths": ["scripts/"],
        "allowedCommands": ["git_status", "run_tests"],
        "acceptanceComponents": ["deterministic"],
        "reviewerIdentities": ["reviewer-canary"],
        "implementerIdentity": "implementer-canary",
        "quotaBudget": {
            "provider": "claude",
            "accountPoolId": "pool-canary",
            "maxSpendPercent": 20,
            "remainingPercent": 50,
        },
    }
    unit.update(overrides)
    return unit


def base_request(head_sha, **overrides):
    req = {
        "productContractId": asa.REQUIRED_PRODUCT_CONTRACT_ID,
        "campaignId": asa.REQUIRED_CAMPAIGN_ID,
        "repoSha": head_sha,
        "workUnit": base_unit(),
        "admissionEvidence": {
            "components": [
                {
                    "type": "quota",
                    "fingerprint": "canary-quota-evidence-0001",
                    "submittedAt": 0,
                    "_now": 0,
                    "provider": "claude",
                    "accountPoolId": "pool-canary",
                    "remainingPercent": 50,
                    "thresholdPercent": 30,
                    "measuredAt": 0,
                    "outcome": "ALLOW",
                }
            ]
        },
    }
    req.update(overrides)
    return req


class AdapterTestCase(unittest.TestCase):
    def setUp(self):
        self.head_sha = real_head_sha()


class SandboxTestCase(AdapterTestCase):
    """Base for tests that need a fresh subdirectory beneath the fixed
    shadow sandbox root, cleaned up afterward."""

    def setUp(self):
        super().setUp()
        os.makedirs(asa.SHADOW_ARTIFACT_ROOT, exist_ok=True)
        self.sandbox_dir = os.path.join(asa.SHADOW_ARTIFACT_ROOT, f"test-{uuid.uuid4().hex}")
        os.makedirs(self.sandbox_dir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.sandbox_dir, ignore_errors=True)


class TestExactBinding(AdapterTestCase):
    def test_matching_repo_sha_is_accepted(self):
        request = base_request(self.head_sha)
        result = asa.run_shadow_simulation(request, REPO_ROOT, now=1000.0)
        self.assertEqual(result["report"]["repoSha"], self.head_sha)
        self.assertEqual(result["report"]["boundProductContractId"], asa.REQUIRED_PRODUCT_CONTRACT_ID)
        self.assertEqual(result["report"]["boundCampaignId"], asa.REQUIRED_CAMPAIGN_ID)

    def test_wrong_repo_sha_is_rejected(self):
        request = base_request("0" * 40)
        with self.assertRaises(asa.AdapterError) as cm:
            asa.run_shadow_simulation(request, REPO_ROOT, now=1000.0)
        self.assertEqual(cm.exception.code, "REPO_SHA_MISMATCH")

    def test_mismatched_product_contract_id_is_rejected_before_anything_else(self):
        request = base_request(self.head_sha, productContractId="other-contract")
        with self.assertRaises(asa.AdapterError) as cm:
            asa.run_shadow_simulation(request, REPO_ROOT, now=1000.0)
        self.assertEqual(cm.exception.code, "CONTRACT_BINDING_MISMATCH")

    def test_mismatched_campaign_id_is_rejected(self):
        request = base_request(self.head_sha, campaignId="other-campaign")
        with self.assertRaises(asa.AdapterError) as cm:
            asa.run_shadow_simulation(request, REPO_ROOT, now=1000.0)
        self.assertEqual(cm.exception.code, "CONTRACT_BINDING_MISMATCH")

    def test_caller_cannot_widen_binding_even_with_a_valid_looking_other_id(self):
        # A caller-supplied ID that happens to look plausible (not just an
        # obviously wrong string) must still be rejected -- the adapter
        # trusts only the fixed constants, never anything from the request.
        request = base_request(self.head_sha, productContractId="yoma-product-acceptance-v1")
        with self.assertRaises(asa.AdapterError) as cm:
            asa.run_shadow_simulation(request, REPO_ROOT, now=1000.0)
        self.assertEqual(cm.exception.code, "CONTRACT_BINDING_MISMATCH")


class TestReadOnlyBehavior(SandboxTestCase):
    def test_simulation_never_touches_an_existing_live_state_file_outside_sandbox(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        tmp.close()
        live_path = tmp.name
        try:
            state = ac.load_state(live_path)
            state = ac.bind_contract(state, "live-contract", "live-campaign", now=1.0)
            state = ac.set_campaign_mode(state, "full", now=1.0)
            ac.save_state(live_path, state, 0)

            request = base_request(self.head_sha, readStatePath=live_path)
            with self.assertRaises(asa.AdapterError) as cm:
                asa.run_shadow_simulation(request, REPO_ROOT, now=1000.0)
            self.assertEqual(cm.exception.code, "PATH_OUTSIDE_SANDBOX_ROOT")
        finally:
            os.remove(live_path)

    def test_cross_contract_read_state_inside_sandbox_fails_closed_not_silently_replaced(self):
        live_path = os.path.join(self.sandbox_dir, "cross-contract-state.json")
        state = ac.load_state(live_path)
        state = ac.bind_contract(state, "live-contract", "live-campaign", now=1.0)
        state = ac.set_campaign_mode(state, "full", now=1.0)
        ac.save_state(live_path, state, 0)
        with open(live_path, "r", encoding="utf-8") as fh:
            before = fh.read()

        request = base_request(self.head_sha, readStatePath=live_path)
        with self.assertRaises(asa.AdapterError) as cm:
            asa.run_shadow_simulation(request, REPO_ROOT, now=1000.0)
        self.assertEqual(cm.exception.code, "CROSS_CONTRACT_READ_STATE_REJECTED")

        with open(live_path, "r", encoding="utf-8") as fh:
            after = fh.read()
        self.assertEqual(before, after)

    def test_matching_contract_read_state_inside_sandbox_is_copied_in_memory(self):
        state_path = os.path.join(self.sandbox_dir, "matching-state.json")
        state = ac.load_state(state_path)
        state = ac.bind_contract(state, asa.REQUIRED_PRODUCT_CONTRACT_ID, asa.REQUIRED_CAMPAIGN_ID, now=1.0)
        state = ac.set_campaign_mode(state, "shadow", now=1.0)
        ac.save_state(state_path, state, 0)
        with open(state_path, "r", encoding="utf-8") as fh:
            before = fh.read()

        request = base_request(self.head_sha, readStatePath=state_path)
        result = asa.run_shadow_simulation(request, REPO_ROOT, now=1000.0)
        self.assertEqual(result["state"]["productContractId"], asa.REQUIRED_PRODUCT_CONTRACT_ID)

        with open(state_path, "r", encoding="utf-8") as fh:
            after = fh.read()
        self.assertEqual(before, after)

    def test_output_state_refuses_the_controllers_live_ledger_filename(self):
        live_ledger_path = os.path.join(self.sandbox_dir, asa.LIVE_LEDGER_BASENAME)
        request_path = os.path.join(self.sandbox_dir, "request.json")
        with open(request_path, "w", encoding="utf-8") as fh:
            json.dump(base_request(self.head_sha), fh)

        rc, output = self._run_cli(request_path, live_ledger_path)
        self.assertEqual(rc, 1)
        self.assertFalse(os.path.exists(live_ledger_path))
        payload = json.loads(output)
        self.assertEqual(payload["errorCode"], "FORBIDDEN_PATH_BASENAME")

    def test_output_state_refuses_remediation_progress_filename(self):
        target = os.path.join(self.sandbox_dir, "remediation-progress.json")
        request_path = os.path.join(self.sandbox_dir, "request.json")
        with open(request_path, "w", encoding="utf-8") as fh:
            json.dump(base_request(self.head_sha), fh)

        rc, output = self._run_cli(request_path, target)
        self.assertEqual(rc, 1)
        self.assertFalse(os.path.exists(target))
        payload = json.loads(output)
        self.assertEqual(payload["errorCode"], "FORBIDDEN_PATH_BASENAME")

    def test_output_state_refuses_remediation_hold_filename(self):
        target = os.path.join(self.sandbox_dir, "remediation-hold.json")
        request_path = os.path.join(self.sandbox_dir, "request.json")
        with open(request_path, "w", encoding="utf-8") as fh:
            json.dump(base_request(self.head_sha), fh)

        rc, output = self._run_cli(request_path, target)
        self.assertEqual(rc, 1)
        self.assertFalse(os.path.exists(target))
        payload = json.loads(output)
        self.assertEqual(payload["errorCode"], "FORBIDDEN_PATH_BASENAME")

    def test_output_state_outside_sandbox_root_is_rejected(self):
        outside_dir = tempfile.mkdtemp()
        try:
            target = os.path.join(outside_dir, "shadow-artifact.json")
            request_path = os.path.join(self.sandbox_dir, "request.json")
            with open(request_path, "w", encoding="utf-8") as fh:
                json.dump(base_request(self.head_sha), fh)

            rc, output = self._run_cli(request_path, target)
            self.assertEqual(rc, 1)
            self.assertFalse(os.path.exists(target))
            payload = json.loads(output)
            self.assertEqual(payload["errorCode"], "PATH_OUTSIDE_SANDBOX_ROOT")
        finally:
            shutil.rmtree(outside_dir, ignore_errors=True)

    def test_output_state_traversal_outside_sandbox_root_is_rejected(self):
        target = os.path.join(self.sandbox_dir, "..", "..", "escaped.json")
        request_path = os.path.join(self.sandbox_dir, "request.json")
        with open(request_path, "w", encoding="utf-8") as fh:
            json.dump(base_request(self.head_sha), fh)

        rc, output = self._run_cli(request_path, target)
        self.assertEqual(rc, 1)
        payload = json.loads(output)
        self.assertEqual(payload["errorCode"], "PATH_OUTSIDE_SANDBOX_ROOT")

    def test_output_state_symlink_escape_is_rejected(self):
        outside_dir = tempfile.mkdtemp()
        try:
            real_outside_target = os.path.join(outside_dir, "escaped.json")
            symlink_path = os.path.join(self.sandbox_dir, "escape-link.json")
            os.symlink(real_outside_target, symlink_path)

            request_path = os.path.join(self.sandbox_dir, "request.json")
            with open(request_path, "w", encoding="utf-8") as fh:
                json.dump(base_request(self.head_sha), fh)

            rc, output = self._run_cli(request_path, symlink_path)
            self.assertEqual(rc, 1)
            self.assertFalse(os.path.exists(real_outside_target))
            payload = json.loads(output)
            # The literal requested path is itself a symlink, so the
            # islink() check (which runs before realpath resolution) fires
            # first with the more specific OUTPUT_IS_SYMLINK code -- the
            # escape is still blocked either way.
            self.assertEqual(payload["errorCode"], "OUTPUT_IS_SYMLINK")
        finally:
            shutil.rmtree(outside_dir, ignore_errors=True)

    def test_output_state_existing_symlink_inside_sandbox_is_refused(self):
        real_target = os.path.join(self.sandbox_dir, "real-target.json")
        with open(real_target, "w", encoding="utf-8") as fh:
            fh.write("{}")
        symlink_path = os.path.join(self.sandbox_dir, "via-link.json")
        os.symlink(real_target, symlink_path)

        # Uses real wall-clock time for admissionEvidence.submittedAt: the
        # CLI runs the simulation with real `now`, and this test needs the
        # simulation itself to succeed so execution reaches the write step.
        import time as _time

        request = base_request(self.head_sha)
        request["admissionEvidence"]["components"][0]["submittedAt"] = _time.time()
        del request["admissionEvidence"]["components"][0]["_now"]
        request_path = os.path.join(self.sandbox_dir, "request.json")
        with open(request_path, "w", encoding="utf-8") as fh:
            json.dump(request, fh)

        rc, output = self._run_cli(request_path, symlink_path)
        self.assertEqual(rc, 1)
        payload = json.loads(output)
        self.assertEqual(payload["errorCode"], "OUTPUT_IS_SYMLINK")

    def test_read_state_path_outside_sandbox_root_is_rejected(self):
        outside = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        outside.close()
        try:
            state = ac.load_state(outside.name)
            state = ac.bind_contract(state, asa.REQUIRED_PRODUCT_CONTRACT_ID, asa.REQUIRED_CAMPAIGN_ID, now=1.0)
            ac.save_state(outside.name, state, 0)

            request = base_request(self.head_sha, readStatePath=outside.name)
            with self.assertRaises(asa.AdapterError) as cm:
                asa.run_shadow_simulation(request, REPO_ROOT, now=1000.0)
            self.assertEqual(cm.exception.code, "PATH_OUTSIDE_SANDBOX_ROOT")
        finally:
            os.remove(outside.name)

    def test_read_state_path_symlink_escape_is_rejected(self):
        outside = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        outside.close()
        try:
            state = ac.load_state(outside.name)
            state = ac.bind_contract(state, asa.REQUIRED_PRODUCT_CONTRACT_ID, asa.REQUIRED_CAMPAIGN_ID, now=1.0)
            ac.save_state(outside.name, state, 0)

            symlink_path = os.path.join(self.sandbox_dir, "escape-read-link.json")
            os.symlink(outside.name, symlink_path)

            request = base_request(self.head_sha, readStatePath=symlink_path)
            with self.assertRaises(asa.AdapterError) as cm:
                asa.run_shadow_simulation(request, REPO_ROOT, now=1000.0)
            # The literal readStatePath is itself a symlink, so the
            # islink() check (which runs before realpath resolution) fires
            # first with the more specific OUTPUT_IS_SYMLINK code -- the
            # escape is still blocked either way.
            self.assertEqual(cm.exception.code, "OUTPUT_IS_SYMLINK")
        finally:
            os.remove(outside.name)

    def test_explicit_output_state_is_written_atomically_and_is_not_the_live_path(self):
        out_path = os.path.join(self.sandbox_dir, "shadow-artifact.json")
        request = base_request(self.head_sha)
        result = asa.run_shadow_simulation(request, REPO_ROOT, now=1000.0)
        asa._atomic_write_json(out_path, result["state"])
        self.assertTrue(os.path.exists(out_path))
        with open(out_path, "r", encoding="utf-8") as fh:
            written = json.load(fh)
        self.assertEqual(written["campaignMode"], "shadow")
        # no stray temp files left behind
        leftovers = [f for f in os.listdir(self.sandbox_dir) if f != "shadow-artifact.json"]
        self.assertEqual(leftovers, [])

    def test_atomic_write_cleans_up_temp_file_on_error(self):
        out_path = os.path.join(self.sandbox_dir, "will-fail.json")

        class Unserializable:
            pass

        with self.assertRaises(TypeError):
            asa._atomic_write_json(out_path, {"bad": Unserializable()})
        leftovers = os.listdir(self.sandbox_dir)
        self.assertEqual(leftovers, [])

    def _run_cli(self, request_path, output_state_path):
        import sys
        from io import StringIO

        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            rc = asa.main(
                ["simulate", request_path, "--repo-root", REPO_ROOT, "--output-state", output_state_path]
            )
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        return rc, output


class TestDeterministicRepeatability(AdapterTestCase):
    def test_same_request_produces_the_same_decision_report_fields(self):
        request = base_request(self.head_sha)
        r1 = asa.run_shadow_simulation(copy.deepcopy(request), REPO_ROOT, now=1000.0)
        r2 = asa.run_shadow_simulation(copy.deepcopy(request), REPO_ROOT, now=1000.0)
        self.assertEqual(r1["report"]["finalStatus"], r2["report"]["finalStatus"])
        self.assertEqual(r1["report"]["unitId"], r2["report"]["unitId"])
        self.assertEqual(r1["report"]["simulation"], r2["report"]["simulation"])
        self.assertEqual(r1["report"]["finalStatus"], "admitted")


class TestShadowModeNeverMutates(SandboxTestCase):
    def test_requesting_verified_is_rejected_before_the_controller_runs(self):
        request = base_request(self.head_sha, requestedTransition="verified")
        with self.assertRaises(asa.AdapterError) as cm:
            asa.run_shadow_simulation(request, REPO_ROOT, now=1000.0)
        self.assertEqual(cm.exception.code, "SHADOW_FORBIDS_MUTATING_TRANSITION")

    def test_requesting_merged_is_rejected(self):
        request = base_request(self.head_sha, requestedTransition="merged")
        with self.assertRaises(asa.AdapterError) as cm:
            asa.run_shadow_simulation(request, REPO_ROOT, now=1000.0)
        self.assertEqual(cm.exception.code, "SHADOW_FORBIDS_MUTATING_TRANSITION")

    def test_requesting_post_merge_verified_is_rejected(self):
        request = base_request(self.head_sha, requestedTransition="post_merge_verified")
        with self.assertRaises(asa.AdapterError) as cm:
            asa.run_shadow_simulation(request, REPO_ROOT, now=1000.0)
        self.assertEqual(cm.exception.code, "SHADOW_FORBIDS_MUTATING_TRANSITION")

    def test_campaign_mode_is_forced_to_shadow_even_if_live_state_says_full(self):
        state_path = os.path.join(self.sandbox_dir, "full-mode-state.json")
        state = ac.load_state(state_path)
        state = ac.bind_contract(state, asa.REQUIRED_PRODUCT_CONTRACT_ID, asa.REQUIRED_CAMPAIGN_ID, now=1.0)
        state = ac.set_campaign_mode(state, "full", now=1.0)
        ac.save_state(state_path, state, 0)

        request = base_request(self.head_sha, readStatePath=state_path)
        result = asa.run_shadow_simulation(request, REPO_ROOT, now=1000.0)
        self.assertEqual(result["state"]["campaignMode"], "shadow")


class TestPerUnitModeRejected(AdapterTestCase):
    def test_per_unit_mode_field_is_rejected(self):
        request = base_request(self.head_sha, workUnit=base_unit(mode="full"))
        with self.assertRaises(asa.AdapterError) as cm:
            asa.run_shadow_simulation(request, REPO_ROOT, now=1000.0)
        self.assertEqual(cm.exception.code, "FORBIDDEN_UNIT_FIELD")


class TestMalformedRequestsRejected(AdapterTestCase):
    def test_missing_required_fields_is_rejected(self):
        request = base_request(self.head_sha)
        del request["campaignId"]
        with self.assertRaises(asa.AdapterError) as cm:
            asa.run_shadow_simulation(request, REPO_ROOT, now=1000.0)
        self.assertEqual(cm.exception.code, "MISSING_REQUEST_FIELDS")

    def test_unknown_requested_transition_is_rejected(self):
        request = base_request(self.head_sha, requestedTransition="not_a_real_state")
        with self.assertRaises(asa.AdapterError) as cm:
            asa.run_shadow_simulation(request, REPO_ROOT, now=1000.0)
        self.assertEqual(cm.exception.code, "UNKNOWN_STATE")

    def test_stale_evidence_is_rejected_by_the_underlying_controller(self):
        request = base_request(self.head_sha)
        request["admissionEvidence"]["components"][0]["submittedAt"] = 0
        request["admissionEvidence"]["components"][0]["_now"] = 10_000_000.0
        with self.assertRaises(ac.ControllerError) as cm:
            asa.run_shadow_simulation(request, REPO_ROOT, now=10_000_000.0)
        self.assertEqual(cm.exception.code, "STALE_EVIDENCE")

    def test_unknown_evidence_type_is_rejected(self):
        request = base_request(self.head_sha)
        request["admissionEvidence"]["components"][0]["type"] = "not_a_real_type"
        with self.assertRaises(ac.ControllerError) as cm:
            asa.run_shadow_simulation(request, REPO_ROOT, now=1000.0)
        self.assertEqual(cm.exception.code, "UNKNOWN_EVIDENCE_TYPE")


class TestOutOfScopeRejected(AdapterTestCase):
    def test_unregistered_command_in_work_unit_is_rejected(self):
        request = base_request(
            self.head_sha,
            workUnit=base_unit(allowedCommands=["rm_rf_everything"]),
        )
        with self.assertRaises(ac.ControllerError) as cm:
            asa.run_shadow_simulation(request, REPO_ROOT, now=1000.0)
        self.assertEqual(cm.exception.code, "UNKNOWN_COMMAND")

    def test_out_of_scope_changed_paths_in_deterministic_evidence_is_rejected(self):
        request = base_request(self.head_sha)
        request["requestedTransition"] = "running"
        request["transitionEvidence"] = {
            "components": [
                {
                    "type": "deterministic",
                    "fingerprint": "det-evidence-0001",
                    "submittedAt": 0,
                    "_now": 0,
                    "commitFingerprint": "canary-commit",
                    "provenance": "run_tests",
                    "changedPaths": ["modules/yoma/outside-scope.md"],
                    "commandsUsed": ["run_tests"],
                    "outcome": "PASS",
                }
            ]
        }
        request["commitFingerprint"] = "canary-commit"
        with self.assertRaises(ac.ControllerError) as cm:
            asa.run_shadow_simulation(request, REPO_ROOT, now=1000.0)
        self.assertEqual(cm.exception.code, "OUT_OF_SCOPE_PATH")


class TestFixtureShapeIsValid(AdapterTestCase):
    def test_bundled_canary_fixture_is_shape_valid_once_sha_placeholders_are_filled(self):
        fixture_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "controller_shadow_integration_fixture.json")
        with open(fixture_path, "r", encoding="utf-8") as fh:
            fixture = json.load(fh)
        fixture.pop("_note", None)
        fixture["repoSha"] = self.head_sha
        fixture["commitFingerprint"] = self.head_sha
        fixture["workUnit"]["baseSha"] = self.head_sha
        fixture["admissionEvidence"]["components"][0]["_now"] = 0

        self.assertEqual(fixture["productContractId"], asa.REQUIRED_PRODUCT_CONTRACT_ID)
        self.assertEqual(fixture["campaignId"], asa.REQUIRED_CAMPAIGN_ID)

        result = asa.run_shadow_simulation(fixture, REPO_ROOT, now=1000.0)
        self.assertEqual(result["report"]["finalStatus"], "admitted")
        self.assertEqual(result["report"]["mode"], "shadow")


if __name__ == "__main__":
    unittest.main()
