#!/usr/bin/env python3
"""
test_rashi_association_audit.py - Unit tests for audit_rashi_association.py.

Exercises the real exported functions (analyze_daf, select_target_daf,
sample_entries_for_daf, summarize, daf_pad) against synthetic in-memory
fixtures shaped exactly like _js_parser.parse_line_items_from_lines_array /
parse_rashi_lines_array output. No text parsing, no network, no dependency
on the generated learning_data.js - these are deterministic unit tests, not
an integration check (see run-rashi-association.mjs / npm scripts for the
integration audit against the real generated file).

Covers every failure mode the referential-integrity auditor is responsible
for: nonexistent target, l01 accepted only via exact suffix match (never
collapsed into l01a/l01b or vice versa), cross-daf target, arbitrary
nonexistent Mishnah target, empty link (boundary, non-fatal), multi-link
completeness. Semantic correctness (a target that exists but is the "wrong"
one for a given Rashi) and rendering-level failure modes (omitted multi-link
target in the DOM, Hebrew/English cross-pairing, vilnaLine-coincidence
fallback) are out of scope for this auditor and are covered instead by
tests/unit/rashi-association.test.mjs (groupRashiByLinkedId) and
tests/browser/rashi-association.spec.js (rendered DOM) respectively; see
docs/reports/rashi-association-audit.md for the coverage/limitations map.

Run directly: python3 scripts/test_rashi_association_audit.py
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_rashi_association import (
    analyze_daf,
    daf_pad,
    sample_entries_for_daf,
    select_target_daf,
    summarize,
)


def line(id_, kind="gemara", he="he", en="en"):
    return {"id": id_, "kind": kind, "he": he, "en": en, "vilna_line": None,
            "en_lit": None, "sefaria_ref": ""}


def rashi(id_, vilna_line, targets, he="rashi he", en="rashi en"):
    return {"id": id_, "sourceType": "rashi", "daf": None, "vilnaLine": vilna_line,
            "he": he, "en": en, "enSource": "ai_helper_translation", "source": "talmud.dev",
            "confidence": "helper", "linkedGemaraLineIds": list(targets)}


class TestDafPad(unittest.TestCase):
    def test_pads_single_digit(self):
        self.assertEqual(daf_pad("2a"), "002a")

    def test_pads_double_digit(self):
        self.assertEqual(daf_pad("11b"), "011b")

    def test_leaves_triple_digit(self):
        self.assertEqual(daf_pad("176a"), "176a")

    def test_rejects_malformed(self):
        with self.assertRaises(ValueError):
            daf_pad("not-a-daf")


class TestAnalyzeDafReferentialIntegrity(unittest.TestCase):
    """Each test proves one concrete failure mode is actually caught."""

    def test_nonexistent_target_is_broken(self):
        daf_data = {
            "lines_by_id": {"yoma-002a-l01": line("yoma-002a-l01")},
            "rashi": [rashi("rashi-002a-001", 1, ["yoma-002a-l99"])],
        }
        entries, errors = analyze_daf("2a", daf_data)
        self.assertTrue(entries[0]["associations"][0]["is_broken"])
        self.assertEqual(len(errors), 1)
        self.assertIn("does not exist", errors[0])

    def test_bare_id_not_accepted_when_only_suffixed_variants_exist(self):
        """Reproduces the real 43a/43b/44b bug: a Rashi links to bare
        'l01' but only 'l01a'/'l01b' exist as real line objects. No
        startswith/prefix tolerance may treat the bare id as valid.
        """
        daf_data = {
            "lines_by_id": {
                "yoma-043a-l01a": line("yoma-043a-l01a"),
                "yoma-043a-l01b": line("yoma-043a-l01b"),
            },
            "rashi": [rashi("rashi-043a-001", 1, ["yoma-043a-l01"])],
        }
        entries, errors = analyze_daf("43a", daf_data)
        self.assertTrue(entries[0]["associations"][0]["is_broken"])
        self.assertEqual(len(errors), 1)

    def test_suffixed_id_not_collapsed_into_bare_or_sibling_suffix(self):
        """The inverse: a target of 'l01a' must resolve only to the literal
        'l01a' object, never to a bare 'l01' or to sibling 'l01b'.
        """
        daf_data = {
            "lines_by_id": {
                "yoma-043a-l01a": line("yoma-043a-l01a", he="line a"),
                "yoma-043a-l01b": line("yoma-043a-l01b", he="line b"),
            },
            "rashi": [rashi("rashi-043a-001", 1, ["yoma-043a-l01a"])],
        }
        entries, errors = analyze_daf("43a", daf_data)
        assoc = entries[0]["associations"][0]
        self.assertFalse(assoc["is_broken"])
        self.assertEqual(assoc["target_he"], "line a")
        self.assertEqual(errors, [])

    def test_cross_daf_target_is_broken(self):
        daf_data = {
            "lines_by_id": {"yoma-002a-l01": line("yoma-002a-l01")},
            "rashi": [rashi("rashi-002a-001", 1, ["yoma-003a-l01"])],
        }
        entries, errors = analyze_daf("2a", daf_data)
        assoc = entries[0]["associations"][0]
        self.assertTrue(assoc["is_broken"])
        self.assertTrue(assoc["is_cross_daf"])
        self.assertEqual(len(errors), 1)
        self.assertIn("different daf", errors[0])

    def test_arbitrary_nonexistent_mishnah_target_is_broken(self):
        """A target is never presumed valid merely because it looks like it
        could be a Mishnah reference. Only exact-id existence counts, and
        kind (gemara vs mishna) is read from the real resolved line, never
        guessed from the id string.
        """
        daf_data = {
            "lines_by_id": {"yoma-011b-l01": line("yoma-011b-l01", kind="mishna")},
            "rashi": [rashi("rashi-011b-001", 1, ["mishnah-011b-l99"])],
        }
        entries, errors = analyze_daf("11b", daf_data)
        assoc = entries[0]["associations"][0]
        self.assertTrue(assoc["is_broken"])
        self.assertFalse(assoc["is_mishnah"])
        self.assertEqual(len(errors), 1)

    def test_real_mishnah_target_is_detected_by_resolved_kind(self):
        daf_data = {
            "lines_by_id": {"yoma-011b-l01": line("yoma-011b-l01", kind="mishna")},
            "rashi": [rashi("rashi-011b-001", 1, ["yoma-011b-l01"])],
        }
        entries, errors = analyze_daf("11b", daf_data)
        assoc = entries[0]["associations"][0]
        self.assertFalse(assoc["is_broken"])
        self.assertTrue(assoc["is_mishnah"])
        self.assertEqual(errors, [])

    def test_empty_link_is_boundary_and_non_fatal(self):
        daf_data = {
            "lines_by_id": {"yoma-002a-l01": line("yoma-002a-l01")},
            "rashi": [rashi("rashi-002a-001", 1, [])],
        }
        entries, errors = analyze_daf("2a", daf_data)
        self.assertEqual(entries[0]["entry_category"], "boundary")
        self.assertEqual(entries[0]["associations"], [])
        self.assertEqual(errors, [])  # boundary entries never fail the gate

    def test_multi_link_entry_carries_every_declared_target(self):
        daf_data = {
            "lines_by_id": {
                "yoma-002a-l01": line("yoma-002a-l01"),
                "yoma-002a-l02": line("yoma-002a-l02"),
            },
            "rashi": [rashi("rashi-002a-001", 1, ["yoma-002a-l01", "yoma-002a-l02"])],
        }
        entries, errors = analyze_daf("2a", daf_data)
        self.assertEqual(entries[0]["entry_category"], "multiLink")
        self.assertEqual(len(entries[0]["associations"]), 2)
        self.assertEqual(errors, [])

    def test_multi_link_with_one_broken_target_reports_only_that_target(self):
        daf_data = {
            "lines_by_id": {"yoma-002a-l01": line("yoma-002a-l01")},
            "rashi": [rashi("rashi-002a-001", 1, ["yoma-002a-l01", "yoma-002a-l99"])],
        }
        entries, errors = analyze_daf("2a", daf_data)
        assocs = entries[0]["associations"]
        self.assertFalse(assocs[0]["is_broken"])
        self.assertTrue(assocs[1]["is_broken"])
        self.assertEqual(len(errors), 1)

    def test_sparse_detects_gap_in_rashi_vilna_line_sequence(self):
        daf_data = {
            "lines_by_id": {"yoma-002a-l01": line("yoma-002a-l01")},
            "rashi": [
                rashi("rashi-002a-001", 1, ["yoma-002a-l01"]),
                rashi("rashi-002a-003", 3, ["yoma-002a-l01"]),  # vilnaLine 2 skipped
            ],
        }
        entries, _ = analyze_daf("2a", daf_data)
        self.assertFalse(entries[0]["is_sparse"])
        self.assertTrue(entries[1]["is_sparse"])

    def test_no_gap_is_not_sparse(self):
        daf_data = {
            "lines_by_id": {"yoma-002a-l01": line("yoma-002a-l01")},
            "rashi": [
                rashi("rashi-002a-001", 1, ["yoma-002a-l01"]),
                rashi("rashi-002a-002", 2, ["yoma-002a-l01"]),
            ],
        }
        entries, _ = analyze_daf("2a", daf_data)
        self.assertFalse(entries[1]["is_sparse"])


class TestSelectTargetDaf(unittest.TestCase):
    def _corpus(self):
        return {d: {"lines_by_id": {}, "rashi": []} for d in ["2a", "2b", "3a", "3b"]}

    def test_target_mode_returns_exactly_one(self):
        class Args:
            target = "2b"; range_from = None; range_to = None
            corpus = False; exhaustive_corpus = False
        self.assertEqual(select_target_daf(self._corpus(), Args()), ["2b"])

    def test_target_mode_rejects_nonexistent_daf(self):
        class Args:
            target = "99z"; range_from = None; range_to = None
            corpus = False; exhaustive_corpus = False
        with self.assertRaises(SystemExit):
            select_target_daf(self._corpus(), Args())

    def test_range_mode_is_exact_inclusive(self):
        class Args:
            target = "2a"; range_from = "2b"; range_to = "3a"
            corpus = False; exhaustive_corpus = False
        self.assertEqual(select_target_daf(self._corpus(), Args()), ["2b", "3a"])

    def test_exhaustive_corpus_returns_every_daf(self):
        class Args:
            target = "2a"; range_from = None; range_to = None
            corpus = False; exhaustive_corpus = True
        corpus = self._corpus()
        self.assertEqual(select_target_daf(corpus, Args()), list(corpus.keys()))

    def test_never_manufactures_a_daf_outside_the_real_corpus(self):
        """The real corpus ends at 88a; range mode must reject a request for
        a daf (e.g. 88b) that was never parsed out of the generated file,
        rather than silently manufacturing it.
        """
        class Args:
            target = "2a"; range_from = "3a"; range_to = "88b"
            corpus = False; exhaustive_corpus = False
        with self.assertRaises(SystemExit):
            select_target_daf(self._corpus(), Args())


class TestSampleEntriesForDaf(unittest.TestCase):
    def test_includes_first_middle_last(self):
        entries = [
            {"entry_category": "single", "is_sparse": False, "associations": []}
            for _ in range(5)
        ]
        sampled = sample_entries_for_daf(entries)
        self.assertIn(entries[0], sampled)
        self.assertIn(entries[2], sampled)
        self.assertIn(entries[4], sampled)

    def test_includes_every_special_category_entry(self):
        entries = [
            {"entry_category": "single", "is_sparse": False, "associations": []},
            {"entry_category": "multiLink", "is_sparse": False, "associations": []},
            {"entry_category": "single", "is_sparse": False, "associations": []},
            {"entry_category": "boundary", "is_sparse": False, "associations": []},
            {"entry_category": "single", "is_sparse": True, "associations": []},
            {"entry_category": "single", "is_sparse": False,
             "associations": [{"is_mishnah": True, "is_suffixed": False}]},
            {"entry_category": "single", "is_sparse": False,
             "associations": [{"is_mishnah": False, "is_suffixed": True}]},
        ]
        sampled = sample_entries_for_daf(entries)
        for special in (entries[1], entries[3], entries[4], entries[5], entries[6]):
            self.assertIn(special, sampled)

    def test_empty_daf_yields_empty_sample(self):
        self.assertEqual(sample_entries_for_daf([]), [])


class TestSummarize(unittest.TestCase):
    def test_counts_match_entry_shape(self):
        entries = [
            {"daf": "2a", "entry_category": "single", "is_sparse": False,
             "associations": [{"is_mishnah": False, "is_suffixed": False, "is_broken": False}]},
            {"daf": "2a", "entry_category": "multiLink", "is_sparse": False,
             "associations": [
                 {"is_mishnah": True, "is_suffixed": False, "is_broken": False},
                 {"is_mishnah": False, "is_suffixed": True, "is_broken": True},
             ]},
            {"daf": "2b", "entry_category": "boundary", "is_sparse": False, "associations": []},
        ]
        counts = summarize(entries)
        self.assertEqual(counts["daf"], 2)
        self.assertEqual(counts["rashi_entries"], 3)
        self.assertEqual(counts["declared_associations"], 3)
        self.assertEqual(counts["single_link"], 1)
        self.assertEqual(counts["multi_link"], 1)
        self.assertEqual(counts["boundary"], 1)
        self.assertEqual(counts["mishnah"], 1)
        self.assertEqual(counts["suffixed"], 1)
        self.assertEqual(counts["broken"], 1)


if __name__ == "__main__":
    unittest.main()
