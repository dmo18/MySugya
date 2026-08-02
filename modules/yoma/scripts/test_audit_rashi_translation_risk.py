#!/usr/bin/env python3
"""
test_audit_rashi_translation_risk.py - synthetic unit tests for every
Step 2 risk detector in audit_rashi_translation_risk.py.

Each test constructs a minimal synthetic Hebrew/English pair (never
real corpus data) that should or should not trip a specific detector,
and checks the exact tag/absence. This proves each detector in
isolation, independent of the live corpus.
"""
import sys
from pathlib import Path

SCRIPTS = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS))
import audit_rashi_translation_risk as art  # noqa: E402

FAILURES = []


def check(label, cond, detail=""):
    if cond:
        print(f"  ok  {label}")
    else:
        print(f"  FAIL  {label}  {detail}")
        FAILURES.append(label)


def tags_of(signals):
    return {t for t, _w, _r in signals}


def test_detect_empty():
    print("detect_empty:")
    check("empty string flags OMITTED_TEXT", "OMITTED_TEXT" in tags_of(list(art.detect_empty(""))))
    check("whitespace-only flags OMITTED_TEXT", "OMITTED_TEXT" in tags_of(list(art.detect_empty("   "))))
    check("real text does not flag", tags_of(list(art.detect_empty("A real translation."))) == set())


def test_detect_identical_to_hebrew():
    print("detect_identical_to_hebrew:")
    he = "שבעת ימים קודם"
    check("identical text flags HEBREW_LEFT_UNTRANSLATED",
          "HEBREW_LEFT_UNTRANSLATED" in tags_of(list(art.detect_identical_to_hebrew(he, he))))
    check("distinct English does not flag",
          tags_of(list(art.detect_identical_to_hebrew(he, "Seven days before"))) == set())


def test_detect_hebrew_leakage():
    print("detect_hebrew_leakage:")
    check("Hebrew characters in English flag HEBREW_LEFT_UNTRANSLATED",
          "HEBREW_LEFT_UNTRANSLATED" in tags_of(list(art.detect_hebrew_leakage("This says כהן גדול here."))))
    check("pure English does not flag",
          tags_of(list(art.detect_hebrew_leakage("This is fully English text."))) == set())


def test_detect_length_ratio():
    print("detect_length_ratio:")
    he = "מילה קצרה " * 20  # long Hebrew
    check("very short English vs long Hebrew flags OMITTED_TEXT",
          "OMITTED_TEXT" in tags_of(list(art.detect_length_ratio(he, "short"))))
    he_short = "קצר"
    en_long = "A very long explanatory passage that goes on and on and on and on far beyond the terse Hebrew original, adding invented detail after invented detail well past any reasonable literal rendering of three short Hebrew words."
    check("very long English vs short Hebrew flags OVEREXPLAINED",
          "OVEREXPLAINED" in tags_of(list(art.detect_length_ratio(he_short, en_long))))
    check("proportionate lengths do not flag",
          tags_of(list(art.detect_length_ratio("מילים בעברית כאן", "Words in English here"))) == set())


def test_detect_truncation():
    print("detect_truncation:")
    check("trailing comma does NOT flag (legitimate Rashi lemma-boundary convention)",
          tags_of(list(art.detect_truncation("This sentence trails off,"))) == set())
    check("trailing dash does NOT flag (legitimate lemma-quote boundary convention)",
          tags_of(list(art.detect_truncation("The verse states 'and he shall bring' -"))) == set())
    check("bare ending on 'and' with no closing punctuation flags TRUNCATED",
          "TRUNCATED" in tags_of(list(art.detect_truncation("The Kohen Gadol performed the service and"))))
    check("complete sentence does not flag",
          tags_of(list(art.detect_truncation("This is a complete sentence."))) == set())


def test_detect_fragment():
    print("detect_fragment:")
    check("very short fragment flags FRAGMENT",
          "FRAGMENT" in tags_of(list(art.detect_fragment("the offering"))))
    check("full sentence does not flag",
          tags_of(list(art.detect_fragment("The Kohen Gadol brought the offering to the altar."))) == set())


def test_detect_unmatched_punctuation():
    print("detect_unmatched_punctuation:")
    check("unmatched paren flags PUNCTUATION",
          "PUNCTUATION" in tags_of(list(art.detect_unmatched_punctuation("This has an (unclosed parenthesis."))))
    check("balanced parens do not flag",
          tags_of(list(art.detect_unmatched_punctuation("This (is balanced)."))) == set())
    check("odd quote count flags PUNCTUATION",
          "PUNCTUATION" in tags_of(list(art.detect_unmatched_punctuation('He said "hello and left.'))))


def test_detect_mechanical_template():
    print("detect_mechanical_template:")
    check("scaffold phrasing flags FRAGMENT",
          "FRAGMENT" in tags_of(list(art.detect_mechanical_template("Rashi: opens with an explanation of the verse."))))
    check("placeholder bracket flags FRAGMENT",
          "FRAGMENT" in tags_of(list(art.detect_mechanical_template("[TBD] needs translation"))))
    check("trailing ellipsis flags FRAGMENT",
          "FRAGMENT" in tags_of(list(art.detect_mechanical_template("This trails off..."))))
    check("ordinary sentence does not flag",
          tags_of(list(art.detect_mechanical_template("The Kohen Gadol wore the special garments."))) == set())


def test_detect_pronoun_heavy():
    print("detect_pronoun_heavy:")
    pronoun_heavy = "He said that it was his and that they took it from them and it was theirs and his."
    check("pronoun-dense text flags WRONG_REFERENT",
          "WRONG_REFERENT" in tags_of(list(art.detect_pronoun_heavy(pronoun_heavy))))
    check("named-entity text does not flag",
          tags_of(list(art.detect_pronoun_heavy("The Kohen Gadol entered the Holy of Holies on Yom Kippur."))) == set())
    check("too-short text is not evaluated",
          tags_of(list(art.detect_pronoun_heavy("He did it."))) == set())


def test_detect_possible_copied_gemara():
    print("detect_possible_copied_gemara:")
    gemara_en = "The Sages taught in a baraita: Seven days before Yom Kippur they remove the Kohen Gadol from his house."
    rashi_en_copy = "The Sages taught in a baraita: Seven days before Yom Kippur they remove the Kohen Gadol from his house."
    check("substantial overlap with linked Gemara line flags CONTEXT_MISMATCH",
          "CONTEXT_MISMATCH" in tags_of(list(art.detect_possible_copied_gemara(rashi_en_copy, [gemara_en]))))
    check("genuinely distinct Rashi commentary does not flag",
          tags_of(list(art.detect_possible_copied_gemara(
              "This explains why the seven-day period specifically corresponds to the Yom Kippur service.",
              [gemara_en]))) == set())
    check("no linked lines does not flag",
          tags_of(list(art.detect_possible_copied_gemara("Any text at all.", []))) == set())


def test_build_duplicate_clusters():
    print("build_duplicate_clusters:")
    entries = [
        {"id": "a1", "daf": "2a", "vilnaLine": 1, "he": "טקסט עברי אחד", "en": "This is a shared duplicated English translation string."},
        {"id": "a2", "daf": "5b", "vilnaLine": 3, "he": "טקסט עברי שונה לגמרי", "en": "This is a shared duplicated English translation string."},
        {"id": "a3", "daf": "9a", "vilnaLine": 2, "he": "עוד טקסט", "en": "A completely unrelated unique translation."},
    ]
    clusters = art.build_duplicate_clusters(entries)
    check("cross-daf identical English with different Hebrew forms a cluster",
          len(clusters) == 1 and clusters[0]["memberCount"] == 2)
    same_he_entries = [
        {"id": "b1", "daf": "3a", "vilnaLine": 1, "he": "אותו טקסט עברי בדיוק", "en": "Repeated phrase across identical Hebrew."},
        {"id": "b2", "daf": "3a", "vilnaLine": 1, "he": "אותו טקסט עברי בדיוק", "en": "Repeated phrase across identical Hebrew."},
    ]
    check("identical Hebrew + identical English is not flagged as a contamination cluster (expected legitimate case)",
          art.build_duplicate_clusters(same_he_entries) == [])


def test_apply_neighboring_duplicate_signals():
    print("apply_neighboring_duplicate_signals:")
    from collections import defaultdict
    rashi_by_daf = {
        "2a": [
            {"id": "n1", "daf": "2a", "vilnaLine": 1, "he": "א", "en": "Duplicate neighboring text here for testing."},
            {"id": "n2", "daf": "2a", "vilnaLine": 2, "he": "ב", "en": "Duplicate neighboring text here for testing."},
            {"id": "n3", "daf": "2a", "vilnaLine": 3, "he": "ג", "en": "A distinct third entry entirely."},
        ]
    }
    risk_by_id = defaultdict(list)
    art.apply_neighboring_duplicate_signals(["2a"], rashi_by_daf, risk_by_id)
    check("second of two identical neighbors is flagged DUPLICATED",
          "DUPLICATED" in {t for t, _w, _r in risk_by_id["n2"]})
    check("first of the pair is not flagged (only the follower is)",
          "DUPLICATED" not in {t for t, _w, _r in risk_by_id["n1"]})
    check("distinct third entry is not flagged",
          risk_by_id["n3"] == [])


def test_apply_daf_level_signals():
    print("apply_daf_level_signals:")
    from collections import defaultdict
    rashi_by_daf = {
        "53a": [{"id": "r1", "daf": "53a", "vilnaLine": 1, "he": "x", "en": "y"}],
        "5a": [{"id": "r2", "daf": "5a", "vilnaLine": 1, "he": "x", "en": "y"}],
        "2a": [{"id": "r3", "daf": "2a", "vilnaLine": 1, "he": "x", "en": "y"}],
    }
    semantic_profile = {"53a": "FABRICATION-SUSPECT", "5a": "ALIGNED", "2a": "SHIFTED"}
    step1_provenance = {
        "53a": {"depth": "known-needs-reconstruction"},
        "5a": {"depth": "known-needs-realignment"},
        "2a": {"depth": "narrow-fix-only"},
    }
    risk_by_id = defaultdict(list)
    art.apply_daf_level_signals(["53a", "5a", "2a"], rashi_by_daf, semantic_profile, step1_provenance, risk_by_id)
    check("known-needs-reconstruction daf flags INVENTED_TEXT",
          "INVENTED_TEXT" in {t for t, _w, _r in risk_by_id["r1"]})
    check("known-needs-realignment daf flags CONTEXT_MISMATCH",
          "CONTEXT_MISMATCH" in {t for t, _w, _r in risk_by_id["r2"]})
    check("SHIFTED semantic classification flags SHIFTED",
          "SHIFTED" in {t for t, _w, _r in risk_by_id["r3"]})


def test_build_terminology_variance():
    print("build_terminology_variance:")
    entries = [
        {"id": "t1", "daf": "2a", "vilnaLine": 1, "he": "דברי כהן גדול כאן", "en": "The Kohen Gadol said this."},
        {"id": "t2", "daf": "3a", "vilnaLine": 1, "he": "עוד דברי כהן גדול", "en": "The high priest said that."},
        {"id": "t3", "daf": "4a", "vilnaLine": 1, "he": "ללא מונח כלל", "en": "Nothing relevant here."},
    ]
    variance = art.build_terminology_variance(entries)
    entry = variance.get("כהן גדול")
    check("watchlist term with entries is reported", entry is not None)
    if entry:
        check("total entries containing the term is 2", entry["totalEntriesContainingTerm"] == 2)
        check("expected rendering 'kohen gadol' is counted", entry["renderingCounts"].get("kohen gadol") == 1)
        check("non-matching rendering counted as noneOfExpectedRenderings", entry["noneOfExpectedRenderings"] == 1)


def main():
    test_detect_empty()
    test_detect_identical_to_hebrew()
    test_detect_hebrew_leakage()
    test_detect_length_ratio()
    test_detect_truncation()
    test_detect_fragment()
    test_detect_unmatched_punctuation()
    test_detect_mechanical_template()
    test_detect_pronoun_heavy()
    test_detect_possible_copied_gemara()
    test_build_duplicate_clusters()
    test_apply_neighboring_duplicate_signals()
    test_apply_daf_level_signals()
    test_build_terminology_variance()
    if FAILURES:
        print(f"\nFAILED: {len(FAILURES)} check(s): {FAILURES}")
        sys.exit(1)
    print("\nOK: all Rashi translation-risk detector tests passed.")


if __name__ == "__main__":
    main()
