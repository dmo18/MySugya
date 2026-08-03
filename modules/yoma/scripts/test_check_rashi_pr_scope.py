#!/usr/bin/env python3
"""
test_check_rashi_pr_scope.py - regression + new-behavior tests for
check_rashi_pr_scope.py's check_allowlist_ratchet, exercised end to end
against a disposable temporary git repository (never the live repository).

Covers two things:
  1. Regression: ordinary allowlist files (anything other than
     rashi_boundary_authorizations.json) keep the exact remove-only,
     identity-blind serialized-dict-set behavior this gate always had.
  2. New behavior: the boundary-authorizations registry gets the one narrow
     fingerprint-refresh exception from boundary_fingerprint_ratchet.py,
     wired in identically to how worker_pipeline.py's allowlist_ratchet_inline
     wires it in.

Run directly: python3 scripts/test_check_rashi_pr_scope.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import boundary_fingerprint_ratchet as bfr
import check_rashi_pr_scope as scope

ORIGINAL_EN = "R61: 'Davar' - a word (stub continuation, continues on 5a)."
FIXED_EN = ("'Davar' - a matter; the comment is truncated here at the end of the daf, "
            "and continues on 5a, where the lemma is completed as 'a matter that does "
            "not invalidate for future generations.'")

LEARN_REL = "modules/yoma/assets/learning/yoma"
ALLOWLIST_REL = "modules/yoma/scripts/allowlists"
REVIEW_REL = "docs/reports/data"


def _git(repo, *args):
    r = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr}")
    return r.stdout


def _write(repo, rel, obj):
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(obj if isinstance(obj, str) else json.dumps(obj, indent=1), encoding="utf-8")


def _registry_entry(daf="4b", vl=61, en=ORIGINAL_EN, **overrides):
    e = {
        "daf": daf, "vilnaLine": vl,
        "reason": "Single-word stub comment whose own text marks it as a continuation.",
        "evidenceClassification": "daf-boundary-truncation",
        "boundaryRule": "Cross-daf linkedGemaraLineIds are prohibited.",
        "enFingerprint": bfr.fingerprint(en),
    }
    e.update(overrides)
    return e


def _corpus_entry(daf="4b", vl=61, en=ORIGINAL_EN, linked=None):
    return {"vilnaLine": vl, "en": en, "enSource": "ai_helper_translation",
            "confidence": "helper", "linkedGemaraLineIds": list(linked or [])}


def _review_record(entry_id="rashi-yoma-004b-061", daf="4b", status="CONFIRMED",
                    final_disposition="SUBSTANTIVE_REPAIR", final_english=FIXED_EN):
    return {
        "entryId": entry_id, "daf": daf, "hebrew": "דבר",
        "originalEnglish": ORIGINAL_EN, "proposedEnglish": final_english,
        "firstPassDisposition": "SUBSTANTIVE_REPAIR",
        "defectTags": ["INVENTED_TEXT", "WRONG_MEANING"],
        "firstPassEvidence": "test evidence",
        "secondPass": {"required": True, "status": status,
                       "evidence": "test second-pass evidence", "finalEnglish": final_english},
        "blindQA": {"selected": False, "result": None, "evidence": None},
        "finalDisposition": final_disposition,
        "structuralStop": None, "repairPR": None, "finalVerificationSHA": None,
    }


def _manifest(entry_id="rashi-yoma-004b-061", daf="4b", vl=61,
              review_record_path=None, type_=bfr.REPAIR_TASK_TYPE, module="yoma"):
    return {
        "type": type_, "module": module, "targets": [daf],
        "entryId": entry_id,
        "registryIdentity": {"daf": daf, "vilnaLine": vl},
        "baseEnFingerprint": bfr.fingerprint(ORIGINAL_EN),
        "expectedNewEnFingerprint": bfr.fingerprint(FIXED_EN),
        "reviewRecordPath": review_record_path or f"{REVIEW_REL}/rashi-step6-batch-001-review-records.json",
    }


class CheckAllowlistRatchetTestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="scope-test-")
        self.addCleanup(shutil.rmtree, self.tmpdir, ignore_errors=True)
        self.repo = Path(self.tmpdir)
        self._old_cwd = os.getcwd()
        self._old_restructure = os.environ.pop("RASHI_ALLOWLIST_RESTRUCTURE", None)
        self.addCleanup(os.chdir, self._old_cwd)
        self.addCleanup(self._restore_env)

        _git(self.repo, "init", "-q")
        _git(self.repo, "config", "user.email", "test@example.com")
        _git(self.repo, "config", "user.name", "Test")
        _write(self.repo, f"{LEARN_REL}/4b.learning.json",
               {"sugyot": [], "rashiTranslations": [_corpus_entry()]})
        _write(self.repo, f"{ALLOWLIST_REL}/rashi_boundary_authorizations.json",
               {"entries": [_registry_entry()]})
        _write(self.repo, f"{ALLOWLIST_REL}/rashi_content_allowlist.json",
               {"entries": [{"daf": "2a", "vilnaLine": 5, "note": "pre-existing debt"}]})
        _write(self.repo, f"{REVIEW_REL}/rashi-step6-batch-001-review-records.json",
               {"batchId": "step6-batch-001", "records": [_review_record()], "totals": {}})
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-q", "-m", "base")
        self.base_rev = _git(self.repo, "rev-parse", "HEAD").strip()
        os.chdir(self.repo)

    def _restore_env(self):
        if self._old_restructure is None:
            os.environ.pop("RASHI_ALLOWLIST_RESTRUCTURE", None)
        else:
            os.environ["RASHI_ALLOWLIST_RESTRUCTURE"] = self._old_restructure

    # ---- regression: ordinary allowlist files unchanged ----

    def test_ordinary_allowlist_addition_still_rejected(self):
        doc = json.loads((self.repo / f"{ALLOWLIST_REL}/rashi_content_allowlist.json").read_text())
        doc["entries"].append({"daf": "2a", "vilnaLine": 6, "note": "new"})
        _write(self.repo, f"{ALLOWLIST_REL}/rashi_content_allowlist.json", doc)
        errors = []
        scope.check_allowlist_ratchet([f"{ALLOWLIST_REL}/rashi_content_allowlist.json"], self.base_rev, errors)
        self.assertEqual(len(errors), 1)
        self.assertIn("entry ADDED", errors[0])

    def test_ordinary_allowlist_removal_still_allowed(self):
        _write(self.repo, f"{ALLOWLIST_REL}/rashi_content_allowlist.json", {"entries": []})
        errors = []
        scope.check_allowlist_ratchet([f"{ALLOWLIST_REL}/rashi_content_allowlist.json"], self.base_rev, errors)
        self.assertEqual(errors, [])

    # ---- boundary registry: add/remove unchanged ----

    def test_boundary_registry_addition_still_rejected(self):
        doc = json.loads((self.repo / f"{ALLOWLIST_REL}/rashi_boundary_authorizations.json").read_text())
        doc["entries"].append(_registry_entry(daf="61a", vl=46, en="new stub"))
        _write(self.repo, f"{ALLOWLIST_REL}/rashi_boundary_authorizations.json", doc)
        errors = []
        scope.check_allowlist_ratchet([f"{ALLOWLIST_REL}/rashi_boundary_authorizations.json"], self.base_rev, errors)
        self.assertEqual(len(errors), 1)
        self.assertIn("entry ADDED", errors[0])

    def test_boundary_registry_removal_still_allowed(self):
        _write(self.repo, f"{ALLOWLIST_REL}/rashi_boundary_authorizations.json", {"entries": []})
        errors = []
        scope.check_allowlist_ratchet([f"{ALLOWLIST_REL}/rashi_boundary_authorizations.json"], self.base_rev, errors)
        self.assertEqual(errors, [])

    # ---- boundary registry: new fingerprint-refresh exception ----

    def test_boundary_registry_legitimate_rehash_authorized_end_to_end(self):
        _write(self.repo, f"{LEARN_REL}/4b.learning.json",
               {"sugyot": [], "rashiTranslations": [_corpus_entry(en=FIXED_EN)]})
        _write(self.repo, f"{ALLOWLIST_REL}/rashi_boundary_authorizations.json",
               {"entries": [_registry_entry(en=FIXED_EN)]})
        _write(self.repo, ".worker-manifest.json", _manifest())
        errors = []
        scope.check_allowlist_ratchet([f"{ALLOWLIST_REL}/rashi_boundary_authorizations.json"], self.base_rev, errors)
        self.assertEqual(errors, [])

    def test_boundary_registry_rehash_without_manifest_rejected(self):
        _write(self.repo, f"{LEARN_REL}/4b.learning.json",
               {"sugyot": [], "rashiTranslations": [_corpus_entry(en=FIXED_EN)]})
        _write(self.repo, f"{ALLOWLIST_REL}/rashi_boundary_authorizations.json",
               {"entries": [_registry_entry(en=FIXED_EN)]})
        errors = []
        scope.check_allowlist_ratchet([f"{ALLOWLIST_REL}/rashi_boundary_authorizations.json"], self.base_rev, errors)
        self.assertEqual(len(errors), 1)
        self.assertIn("no .worker-manifest.json present", errors[0])

    def test_restructure_env_var_bypasses_both_files(self):
        os.environ["RASHI_ALLOWLIST_RESTRUCTURE"] = "1"
        doc = json.loads((self.repo / f"{ALLOWLIST_REL}/rashi_content_allowlist.json").read_text())
        doc["entries"].append({"daf": "2a", "vilnaLine": 6, "note": "new"})
        _write(self.repo, f"{ALLOWLIST_REL}/rashi_content_allowlist.json", doc)
        reg = json.loads((self.repo / f"{ALLOWLIST_REL}/rashi_boundary_authorizations.json").read_text())
        reg["entries"].append(_registry_entry(daf="61a", vl=46, en="new stub"))
        _write(self.repo, f"{ALLOWLIST_REL}/rashi_boundary_authorizations.json", reg)
        errors = []
        scope.check_allowlist_ratchet(
            [f"{ALLOWLIST_REL}/rashi_content_allowlist.json", f"{ALLOWLIST_REL}/rashi_boundary_authorizations.json"],
            self.base_rev, errors)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
