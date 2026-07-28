#!/usr/bin/env python3
"""
test_validate_rashi_boundary_authorizations.py - unit tests for
validate_rashi_boundary_authorizations.py's validate() function.

Exercises validate() against synthetic in-memory fixtures (a corpus dict and
a registry entries list), never the real repository files, so each of the
six required failure modes is proven independently and deterministically:
  1. authorization for a non-empty (already-linked) entry
  2. missing authorization for a currently boundary (empty-linked) entry
  3. stale authorization (en text changed since enFingerprint was recorded)
  4. duplicate authorization (same daf+vilnaLine twice)
  5. authorization referencing a nonexistent daf/vilnaLine
  6. registry growth beyond the authorized ceiling

Also proves the clean/no-op path: a registry that exactly matches the
corpus's boundary entries, with correct fingerprints, passes with zero
errors.

Run directly: python3 scripts/test_validate_rashi_boundary_authorizations.py
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate_rashi_boundary_authorizations import fingerprint, validate


def corpus_entry(en, linked=None):
    return {"linkedGemaraLineIds": list(linked or []), "en": en}


def authorization(daf, vl, en_for_fingerprint):
    return {
        "daf": daf,
        "vilnaLine": vl,
        "reason": "test reason",
        "evidenceClassification": "daf-boundary-truncation",
        "boundaryRule": "test rule",
        "enFingerprint": fingerprint(en_for_fingerprint),
    }


class TestValidateBoundaryAuthorizations(unittest.TestCase):
    def test_clean_registry_matching_corpus_passes(self):
        corpus = {
            ("4b", 61): corpus_entry("stub text", linked=[]),
            ("4b", 62): corpus_entry("linked text", linked=["yoma-004b-l10"]),
        }
        entries = [authorization("4b", 61, "stub text")]
        self.assertEqual(validate(entries, corpus), [])

    def test_authorization_for_non_empty_entry_fails(self):
        corpus = {("4b", 61): corpus_entry("now linked", linked=["yoma-004b-l10"])}
        entries = [authorization("4b", 61, "now linked")]
        errors = validate(entries, corpus)
        self.assertEqual(len(errors), 1)
        self.assertIn("no longer empty-linked", errors[0])

    def test_missing_authorization_for_boundary_entry_fails(self):
        corpus = {("4b", 61): corpus_entry("stub text", linked=[])}
        entries = []
        errors = validate(entries, corpus)
        self.assertEqual(len(errors), 1)
        self.assertIn("no authorization", errors[0])
        self.assertIn("4b L61", errors[0])

    def test_stale_authorization_fails(self):
        corpus = {("4b", 61): corpus_entry("edited text", linked=[])}
        entries = [authorization("4b", 61, "original text")]
        errors = validate(entries, corpus)
        self.assertEqual(len(errors), 1)
        self.assertIn("stale authorization", errors[0])

    def test_duplicate_authorization_fails(self):
        corpus = {("4b", 61): corpus_entry("stub text", linked=[])}
        entries = [authorization("4b", 61, "stub text"), authorization("4b", 61, "stub text")]
        errors = validate(entries, corpus)
        self.assertEqual(len(errors), 1)
        self.assertIn("duplicate authorization", errors[0])

    def test_authorization_for_nonexistent_daf_vilna_line_fails(self):
        corpus = {("4b", 61): corpus_entry("stub text", linked=[])}
        entries = [authorization("4b", 61, "stub text"), authorization("4b", 999, "anything")]
        errors = validate(entries, corpus)
        self.assertEqual(len(errors), 1)
        self.assertIn("does not exist in the corpus", errors[0])

    def test_registry_growth_beyond_ceiling_fails(self):
        corpus = {
            ("4b", 61): corpus_entry("a", linked=[]),
            ("4b", 62): corpus_entry("b", linked=[]),
            ("4b", 63): corpus_entry("c", linked=[]),
        }
        entries = [
            authorization("4b", 61, "a"),
            authorization("4b", 62, "b"),
            authorization("4b", 63, "c"),
        ]
        errors = validate(entries, corpus, max_authorized_entries=2)
        self.assertTrue(any("beyond the MAX_AUTHORIZED_ENTRIES ratchet" in e for e in errors))

    def test_multiple_failure_modes_all_reported_together(self):
        corpus = {
            ("4b", 61): corpus_entry("stub text", linked=[]),
            ("61a", 46): corpus_entry("linked now", linked=["yoma-061a-l10"]),
            ("61a", 47): corpus_entry("boundary, unauthorized", linked=[]),
        }
        entries = [
            authorization("4b", 61, "stub text"),          # fine
            authorization("61a", 46, "linked now"),         # now-linked -> fails
            authorization("61a", 999, "ghost"),             # nonexistent -> fails
            # 61a L47 boundary entry has no authorization -> fails
        ]
        errors = validate(entries, corpus)
        self.assertEqual(len(errors), 3)
        joined = " | ".join(errors)
        self.assertIn("no longer empty-linked", joined)
        self.assertIn("does not exist in the corpus", joined)
        self.assertIn("61a L47", joined)


if __name__ == "__main__":
    unittest.main()
