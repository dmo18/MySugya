#!/usr/bin/env python3
"""
test_boundary_fingerprint_ratchet.py - unit tests for the identity-aware
boundary-authorizations ratchet in boundary_fingerprint_ratchet.py.

diff_registry_entries()/authorize_rehash() do real `git show`/`git ls-tree`
reads, so each scenario below builds a small, disposable, temporary git
repository from scratch (never the live repository) with a committed BASE
state and a live-working-tree HEAD state, exactly mirroring how
check_rashi_pr_scope.py and worker_pipeline.py invoke this module against a
real PR diff.

Run directly: python3 scripts/test_boundary_fingerprint_ratchet.py
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

LEARN_DIR_REL = "learn"
REVIEW_DIR_REL = "docs/reports/data"
MANIFEST_REL = ".worker-manifest.json"

ORIGINAL_EN = "R61: 'Davar' - a word (stub continuation, continues on 5a)."
FIXED_EN = ("'Davar' - a matter; the comment is truncated here at the end of the daf, "
            "and continues on 5a, where the lemma is completed as 'a matter that does "
            "not invalidate for future generations.'")


def _git(repo, *args):
    r = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr}")
    return r.stdout


def _write(repo, rel, obj):
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(obj if isinstance(obj, str) else json.dumps(obj, indent=1), encoding="utf-8")


def _learning_doc(entries):
    return {"sugyot": [], "rashiTranslations": entries}


def _registry_doc(entries):
    return {"entries": entries}


def _review_records_doc(records):
    return {"batchId": "step6-batch-001", "records": records, "totals": {}}


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
              base_fp=None, new_fp=None, review_record_path=None,
              type_=bfr.REPAIR_TASK_TYPE, module="yoma"):
    return {
        "type": type_, "module": module, "targets": [daf],
        "entryId": entry_id,
        "registryIdentity": {"daf": daf, "vilnaLine": vl},
        "baseEnFingerprint": base_fp if base_fp is not None else bfr.fingerprint(ORIGINAL_EN),
        "expectedNewEnFingerprint": new_fp if new_fp is not None else bfr.fingerprint(FIXED_EN),
        "reviewRecordPath": review_record_path or f"{REVIEW_DIR_REL}/rashi-step6-batch-001-review-records.json",
    }


class TestDiffRegistryEntries(unittest.TestCase):
    """Pure, in-memory tests of the identity-aware diff - no git involved."""

    def test_added_entry_detected(self):
        old = [_registry_entry()]
        new = [_registry_entry(), _registry_entry(daf="4b", vl=62, en="new")]
        _, _, added, removed, rehashed = bfr.diff_registry_entries(old, new)
        self.assertEqual(added, [("4b", 62)])
        self.assertEqual(removed, [])
        self.assertEqual(rehashed, [])

    def test_removed_entry_always_allowed_by_the_diff_itself(self):
        old = [_registry_entry()]
        _, _, added, removed, rehashed = bfr.diff_registry_entries(old, [])
        self.assertEqual(removed, [("4b", 61)])
        self.assertEqual(added, [])
        self.assertEqual(rehashed, [])

    def test_changing_daf_looks_like_add_plus_remove_not_rehash(self):
        old = [_registry_entry(daf="4b", vl=61)]
        new = [_registry_entry(daf="5a", vl=61)]
        _, _, added, removed, rehashed = bfr.diff_registry_entries(old, new)
        self.assertEqual(added, [("5a", 61)])
        self.assertEqual(removed, [("4b", 61)])
        self.assertEqual(rehashed, [])

    def test_changing_vilna_line_looks_like_add_plus_remove_not_rehash(self):
        old = [_registry_entry(daf="4b", vl=61)]
        new = [_registry_entry(daf="4b", vl=62)]
        _, _, added, removed, rehashed = bfr.diff_registry_entries(old, new)
        self.assertEqual(added, [("4b", 62)])
        self.assertEqual(removed, [("4b", 61)])

    def test_fingerprint_only_change_is_rehashed(self):
        old = [_registry_entry(en=ORIGINAL_EN)]
        new = [_registry_entry(en=FIXED_EN)]
        _, _, added, removed, rehashed = bfr.diff_registry_entries(old, new)
        self.assertEqual(added, [])
        self.assertEqual(removed, [])
        self.assertEqual(rehashed, [("4b", 61)])

    def test_multiple_rehashed_entries_detected_together(self):
        old = [_registry_entry(daf="4b", vl=61, en="a"), _registry_entry(daf="61a", vl=46, en="b")]
        new = [_registry_entry(daf="4b", vl=61, en="a2"), _registry_entry(daf="61a", vl=46, en="b2")]
        _, _, added, removed, rehashed = bfr.diff_registry_entries(old, new)
        self.assertEqual(len(rehashed), 2)


class BoundaryRatchetRepoTestCase(unittest.TestCase):
    """Builds a fresh temp git repo with a committed BASE state (original
    English, original registry fingerprint) before every test. Each test
    edits the live working tree to represent the PR's HEAD state without
    committing again, since authorize_rehash reads head straight from disk."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="bfr-test-")
        self.addCleanup(shutil.rmtree, self.tmpdir, ignore_errors=True)
        self.repo = Path(self.tmpdir)
        _git(self.repo, "init", "-q")
        _git(self.repo, "config", "user.email", "test@example.com")
        _git(self.repo, "config", "user.name", "Test")

        _write(self.repo, f"{LEARN_DIR_REL}/4b.learning.json", _learning_doc([_corpus_entry()]))
        _write(self.repo, f"{REVIEW_DIR_REL}/rashi-step6-batch-001-review-records.json",
               _review_records_doc([_review_record()]))
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-q", "-m", "base")
        self.base_rev = _git(self.repo, "rev-parse", "HEAD").strip()

        self.old_entry = _registry_entry()

    def _apply_head(self, *, new_en=FIXED_EN, manifest=None, corrupt_second_entry=False, linked=None):
        """Write the working-tree HEAD state for a scenario; returns the new
        registry entries list (always exactly one entry, the refreshed one)."""
        if corrupt_second_entry:
            _write(self.repo, f"{LEARN_DIR_REL}/61a.learning.json",
                   _learning_doc([_corpus_entry(daf="61a", vl=46, en="tampered")]))
        _write(self.repo, f"{LEARN_DIR_REL}/4b.learning.json",
               _learning_doc([_corpus_entry(en=new_en, linked=linked)]))
        reg_entries = [_registry_entry(en=new_en)]
        if manifest is not None:
            _write(self.repo, MANIFEST_REL, manifest)
        return reg_entries

    def _authorize(self, new_entry, old_entry=None):
        manifest_path = self.repo / MANIFEST_REL
        return bfr.authorize_rehash(
            self.repo, self.base_rev, LEARN_DIR_REL, ("4b", 61),
            old_entry if old_entry is not None else self.old_entry, new_entry,
            manifest_path, expected_module="yoma", review_record_dir=REVIEW_DIR_REL,
        )

    # ---- positive ----

    def test_legitimate_fingerprint_refresh_authorized(self):
        entries = self._apply_head(manifest=_manifest())
        ok, reason = self._authorize(entries[0])
        self.assertTrue(ok, reason)

    def test_identity_and_rationale_fields_survive_the_refresh(self):
        entries = self._apply_head(manifest=_manifest())
        new_entry = entries[0]
        for f in ("daf", "vilnaLine", "reason", "evidenceClassification", "boundaryRule"):
            self.assertEqual(self.old_entry[f], new_entry[f])
        self.assertNotEqual(self.old_entry["enFingerprint"], new_entry["enFingerprint"])
        ok, _ = self._authorize(new_entry)
        self.assertTrue(ok)

    def test_authorization_not_required_via_restructure_env_var(self):
        os.environ.pop("RASHI_ALLOWLIST_RESTRUCTURE", None)
        entries = self._apply_head(manifest=_manifest())
        ok, reason = self._authorize(entries[0])
        self.assertTrue(ok, reason)

    # ---- negative ----

    def test_changing_rationale_is_rejected(self):
        entries = self._apply_head(manifest=_manifest())
        new_entry = dict(entries[0])
        new_entry["reason"] = "a different reason"
        ok, reason = self._authorize(new_entry)
        self.assertFalse(ok)
        self.assertIn("more than enFingerprint differs", reason)

    def test_changing_evidence_classification_is_rejected(self):
        entries = self._apply_head(manifest=_manifest())
        new_entry = dict(entries[0])
        new_entry["evidenceClassification"] = "something-else"
        ok, reason = self._authorize(new_entry)
        self.assertFalse(ok)
        self.assertIn("more than enFingerprint differs", reason)

    def test_changing_boundary_rule_is_rejected(self):
        entries = self._apply_head(manifest=_manifest())
        new_entry = dict(entries[0])
        new_entry["boundaryRule"] = "a different rule"
        ok, reason = self._authorize(new_entry)
        self.assertFalse(ok)
        self.assertIn("more than enFingerprint differs", reason)

    def test_changing_linked_gemara_line_ids_is_rejected(self):
        entries = self._apply_head(manifest=_manifest(), linked=["yoma-004b-l10"])
        ok, reason = self._authorize(entries[0])
        self.assertFalse(ok)
        self.assertIn("linkedGemaraLineIds", reason)

    def test_changing_a_second_rashi_entry_anywhere_in_corpus_is_rejected(self):
        entries = self._apply_head(manifest=_manifest(), corrupt_second_entry=True)
        ok, reason = self._authorize(entries[0])
        self.assertFalse(ok)
        self.assertIn("undeclared Rashi entry", reason)

    def test_refreshing_fingerprint_without_an_english_change_is_rejected(self):
        entries = self._apply_head(new_en=ORIGINAL_EN, manifest=_manifest())
        new_entry = dict(entries[0])
        new_entry["enFingerprint"] = "deadbeefdeadbeef"  # claims a change that never happened
        ok, reason = self._authorize(new_entry)
        self.assertFalse(ok)
        self.assertIn("unchanged between base and head", reason)

    def test_supplied_fingerprint_not_matching_new_english_is_rejected(self):
        entries = self._apply_head(manifest=_manifest())
        new_entry = dict(entries[0])
        new_entry["enFingerprint"] = "0000000000000000"
        ok, reason = self._authorize(new_entry)
        self.assertFalse(ok)
        self.assertIn("recomputed fingerprint of the head revision", reason)

    def test_false_base_fingerprint_is_rejected(self):
        stale_old_entry = dict(self.old_entry)
        stale_old_entry["enFingerprint"] = "1111111111111111"
        entries = self._apply_head(manifest=_manifest())
        ok, reason = self._authorize(entries[0], old_entry=stale_old_entry)
        self.assertFalse(ok)
        self.assertIn("base registry enFingerprint", reason)

    def test_manifest_base_fingerprint_mismatch_is_rejected(self):
        entries = self._apply_head(manifest=_manifest(base_fp="2222222222222222"))
        ok, reason = self._authorize(entries[0])
        self.assertFalse(ok)
        self.assertIn("manifest baseEnFingerprint", reason)

    def test_manifest_expected_new_fingerprint_mismatch_is_rejected(self):
        entries = self._apply_head(manifest=_manifest(new_fp="3333333333333333"))
        ok, reason = self._authorize(entries[0])
        self.assertFalse(ok)
        self.assertIn("manifest expectedNewEnFingerprint", reason)

    def test_review_record_for_another_entry_is_rejected(self):
        _write(self.repo, f"{REVIEW_DIR_REL}/rashi-step6-batch-001-review-records.json",
               _review_records_doc([_review_record(entry_id="rashi-yoma-999a-001", daf="999a")]))
        entries = self._apply_head(manifest=_manifest())
        ok, reason = self._authorize(entries[0])
        self.assertFalse(ok)
        self.assertIn("no record for entryId", reason)

    def test_missing_second_pass_confirmation_is_rejected(self):
        _write(self.repo, f"{REVIEW_DIR_REL}/rashi-step6-batch-001-review-records.json",
               _review_records_doc([_review_record(status="REMAINED_BLOCKED",
                                                    final_disposition="BLOCKED",
                                                    final_english=None)]))
        entries = self._apply_head(manifest=_manifest())
        ok, reason = self._authorize(entries[0])
        self.assertFalse(ok)
        self.assertIn("not CONFIRMED", reason)

    def test_ordinary_translation_review_manifest_cannot_authorize_registry_change(self):
        entries = self._apply_head(manifest=_manifest(type_="rashi-translation-review"))
        ok, reason = self._authorize(entries[0])
        self.assertFalse(ok)
        self.assertIn("manifest type is", reason)

    def test_path_traversal_in_review_record_path_is_rejected(self):
        entries = self._apply_head(manifest=_manifest(review_record_path="../../../etc/passwd"))
        ok, reason = self._authorize(entries[0])
        self.assertFalse(ok)
        self.assertIn("safe repo-relative path", reason)

    def test_review_record_path_outside_the_review_record_family_is_rejected(self):
        entries = self._apply_head(manifest=_manifest(review_record_path="docs/reports/data/something-else.json"))
        ok, reason = self._authorize(entries[0])
        self.assertFalse(ok)
        self.assertIn("outside the review-record file family", reason)

    def test_module_mismatch_is_rejected(self):
        entries = self._apply_head(manifest=_manifest(module="other-module"))
        ok, reason = self._authorize(entries[0])
        self.assertFalse(ok)
        self.assertIn("does not match", reason)

    def test_missing_manifest_cannot_authorize(self):
        entries = self._apply_head(manifest=None)
        ok, reason = self._authorize(entries[0])
        self.assertFalse(ok)
        self.assertIn("no .worker-manifest.json present", reason)

    def test_stale_manifest_identical_to_base_cannot_authorize(self):
        _write(self.repo, MANIFEST_REL, _manifest())
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-q", "-m", "manifest already at base")
        self.base_rev = _git(self.repo, "rev-parse", "HEAD").strip()
        entries = self._apply_head(manifest=_manifest())  # byte-identical to the base commit
        ok, reason = self._authorize(entries[0])
        self.assertFalse(ok)
        self.assertIn("stale manifest", reason)

    def test_registry_identity_mismatch_in_manifest_is_rejected(self):
        manifest = _manifest()
        manifest["registryIdentity"] = {"daf": "4b", "vilnaLine": 999}
        entries = self._apply_head(manifest=manifest)
        ok, reason = self._authorize(entries[0])
        self.assertFalse(ok)
        self.assertIn("registryIdentity", reason)


def _corpus_wide_diff_repo():
    tmpdir = tempfile.mkdtemp(prefix="bfr-corpus-test-")
    repo = Path(tmpdir)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    _write(repo, f"{LEARN_DIR_REL}/4b.learning.json", _learning_doc([_corpus_entry()]))
    _write(repo, f"{LEARN_DIR_REL}/61a.learning.json",
           _learning_doc([_corpus_entry(daf="61a", vl=46, en="stable text")]))
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    base_rev = _git(repo, "rev-parse", "HEAD").strip()
    return tmpdir, repo, base_rev


class TestCorpusWideEnDiff(unittest.TestCase):
    def setUp(self):
        self.tmpdir, self.repo, self.base_rev = _corpus_wide_diff_repo()
        self.addCleanup(shutil.rmtree, self.tmpdir, ignore_errors=True)

    def test_only_the_declared_entry_changing_is_the_only_diff(self):
        _write(self.repo, f"{LEARN_DIR_REL}/4b.learning.json", _learning_doc([_corpus_entry(en=FIXED_EN)]))
        changed = bfr.corpus_wide_en_diff(self.repo, self.base_rev, LEARN_DIR_REL)
        self.assertEqual(changed, [("4b", 61)])

    def test_an_undeclared_second_entry_change_is_detected(self):
        _write(self.repo, f"{LEARN_DIR_REL}/4b.learning.json", _learning_doc([_corpus_entry(en=FIXED_EN)]))
        _write(self.repo, f"{LEARN_DIR_REL}/61a.learning.json",
               _learning_doc([_corpus_entry(daf="61a", vl=46, en="tampered")]))
        changed = bfr.corpus_wide_en_diff(self.repo, self.base_rev, LEARN_DIR_REL)
        self.assertIn(("61a", 46), changed)
        self.assertIn(("4b", 61), changed)
        self.assertEqual(len(changed), 2)

    def test_no_change_is_no_diff(self):
        changed = bfr.corpus_wide_en_diff(self.repo, self.base_rev, LEARN_DIR_REL)
        self.assertEqual(changed, [])


if __name__ == "__main__":
    unittest.main()
