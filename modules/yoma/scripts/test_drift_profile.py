#!/usr/bin/env python3
"""
test_drift_profile.py - tests for the Rashi drift-profile detector and
the repair preflight block (audit_rashi_semantic.py, rashi_preflight.py).

Two layers:

1. Synthetic-fixture tests of the classifier itself (permanent; corpus
   state cannot change them): anchor extraction (colon citations,
   tractate adjacency, split citations, gematria), SHIFTED,
   FABRICATION-SUSPECT, ALIGNED, INSUFFICIENT-ANCHORS, and the
   Fable-only override behavior of the preflight drift block.

2. Live-corpus assertions for the documented VERSION 15.84 audit
   findings (docs/reports/rashi-lookalike-shift-audit.md). These are
   SELF-RETIRING: each is asserted only while the underlying defect is
   still present (stub_continuation allowlist entries for the shifted
   daf; the missing Shevuot citations for 61a), so the future
   realignment/reconstruction PRs do not need to edit this file.

Run: python3 scripts/test_drift_profile.py   (cwd modules/yoma)
Exit 0 on success, 1 on first failure.
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import audit_rashi_semantic as ars
from rashi_preflight import drift_block_error

FAILURES = []


def check(name, cond, detail=""):
    status = "ok" if cond else "FAIL"
    print(f"  {status}  {name}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        FAILURES.append(name)


# ---------- layer 1: synthetic fixtures ----------

def test_anchor_extraction():
    print("anchor extraction:")
    a = list(ars.anchors_of("כדאמרינן במסכת גיטין (דף נז:) התם"))
    check("colon amud citation + adjacency",
          ("name", "גיטין", ars.NAME_MAP["גיטין"], False) in a)
    check("gematria daf token", any(k == "dafnum" and t == "57b" for k, t, _, _ in a))
    a = list(ars.anchors_of("דכתיב (ויקרא"))
    check("split citation unclosed alone", not any(t == "ויקרא" for _, t, _, _ in a))
    a = list(ars.anchors_of("דכתיב (ויקרא", "טז) ואת חלב"))
    check("split citation closed by next line", any(t == "ויקרא" for _, t, _, _ in a))
    check("gematria 57b", ars.gematria_daf("נז", ":") == "57b")
    check("gematria 15a", ars.gematria_daf("טו", ".") == "15a")
    check("gematria shem is None", ars.gematria_daf("שם", ":") is None)


def test_same_parens_daf_citation():
    """Yoma 83a/86b/88a class: the tractate name or a relative reference
    word (le'eil/lekaman) sits INSIDE the same parens as "daf", not
    outside-adjacent to it (e.g. Sanhedrin's own (daf ה.) convention).
    Regression for the campaign-83a/88a capability-scan gap."""
    print("same-parens daf citation (tractate/reference word + daf inside parens):")
    a = list(ars.anchors_of('ותניא (ב"ב דף צ:) אין אוצרין פירות בארץ'))
    check("bava batra name recognized", ("name", 'ב"ב', ars.NAME_MAP['ב"ב'], False) in a)
    check("bava batra dafnum token", any(k == "dafnum" and t == "90b" for k, t, _, _ in a))

    a = list(ars.anchors_of('כדאיתא בבבא קמא (ב"ק דף פב.) התם'))
    check("bava kamma name recognized", ("name", 'ב"ק', ars.NAME_MAP['ב"ק'], False) in a)
    check("bava kamma dafnum token", any(k == "dafnum" and t == "82a" for k, t, _, _ in a))

    # Self-reference to an earlier/later daf of THIS tractate: no tractate
    # name to recognize, but the dafnum token must still be extracted.
    a = list(ars.anchors_of("טעם דבר זה (לעיל דף לט.) הוא"))
    check("le'eil self-reference dafnum token still extracted",
          any(k == "dafnum" and t == "39a" for k, t, _, _ in a))
    check("le'eil self-reference yields no spurious name anchor",
          not any(k == "name" for k, _, _, _ in a))

    # Unchanged: the outside-adjacency convention (name before the parens)
    # must keep working after the same-parens extension.
    a = list(ars.anchors_of("בסנהדרין (דף ה.) שאין חכם מתיר"))
    check("outside-adjacency convention still recognized",
          ("name", "סנהדרין", ars.NAME_MAP["סנהדרין"], False) in a)


def test_split_continuation_dafnum():
    """Yoma 80a class: a citation whose tractate name and daf number are
    split across two print lines (he ends "(Berakhot", next_he opens
    "39a)"). A faithful translation legitimately places the daf number on
    the FOLLOWING English line, one past the anchor's own line; this must
    be flagged splitContinuation so the review gate's offset-0 requirement
    can tolerate +1 for that token without tolerating it everywhere."""
    print("split-continuation dafnum (citation's daf number crosses the print-line break):")
    a = list(ars.anchors_of("קים לן (ברכות", "דף לט.) דלא חייבה"))
    dafnum = [x for x in a if x[0] == "dafnum" and x[1] == "39a"]
    check("dafnum token found", len(dafnum) == 1, a)
    if dafnum:
        check("dafnum flagged splitContinuation (digits sourced from next_he)",
              dafnum[0][3] is True)
    name = [x for x in a if x[0] == "name" and x[1] == "ברכות"]
    check("name token found and NOT flagged splitContinuation (fully on its own line)",
          len(name) == 1 and name[0][3] is False, name)

    # A same-line citation (no print-line split) must never be flagged.
    a2 = list(ars.anchors_of("בבכורות (דף נז:) שטבעה ביצתו"))
    dafnum2 = [x for x in a2 if x[0] == "dafnum"]
    check("same-line dafnum NOT flagged splitContinuation",
          len(dafnum2) == 1 and dafnum2[0][3] is False, a2)


def synth_corpus(tmp):
    """Three synthetic daf: 901a shifted, 902a fabricated, 903a aligned,
    904a anchor-poor."""
    learn = tmp / "learning"
    talmud = tmp / "talmuddev"
    learn.mkdir()
    talmud.mkdir()
    pad_he = "ומיהו ודאי צריך להקטיר קטורת אחרת"
    pad_en = "and certainly he must burn other incense afterwards"

    def write(daf, raw, ens):
        (talmud / f"{daf}.json").write_text(json.dumps({"rashi": raw}, ensure_ascii=False))
        (learn / f"{daf}.learning.json").write_text(json.dumps({
            "rashiTranslations": [{"vilnaLine": i + 1, "en": e, "linkedGemaraLineIds": []}
                                  for i, e in enumerate(ens)]}, ensure_ascii=False))

    # 901a SHIFTED: two citations whose English sits 5 lines earlier
    raw = [pad_he] * 12
    raw[6] = "כדאמרינן במסכת גיטין (דף נז:)"
    raw[10] = "כדכתיב (ויקרא טז) ואת החלב"
    ens = [pad_en] * 12
    ens[1] = "as we say in tractate Gittin (57b)"
    ens[5] = "as it is written (Lev. 16), and the fat"
    write("901a", raw, ens)

    # 902a FABRICATION-SUSPECT: two citations that appear nowhere
    raw = [pad_he] * 8
    raw[2] = "וילפינן מקראי בפ\"ק דשבועות (דף ז:)"
    raw[5] = "ובמסכת זבחים (דף טו:) אמרינן"
    write("902a", raw, ["generic essay text about the temple service"] * 8)

    # 903a ALIGNED: citations on their own lines
    raw = [pad_he] * 6
    raw[1] = "כדאמרינן במסכת גיטין (דף נז:)"
    raw[4] = "כדכתיב (ויקרא טז)"
    ens = [pad_en] * 6
    ens[1] = "as stated in Gittin (57b)"
    ens[4] = "as written (Lev. 16)"
    write("903a", raw, ens)

    # 904a INSUFFICIENT: no anchors at all
    write("904a", [pad_he] * 4, [pad_en] * 4)

    # 905a ALIGNED with a genuine split-continuation citation: the daf
    # number is honestly translated one line after the tractate name,
    # mirroring the same print-line split in the raw Hebrew.
    raw = [pad_he] * 6
    raw[2] = "קים לן (ברכות"
    raw[3] = "דף לט.) דלא חייבה"
    ens = [pad_en] * 6
    ens[2] = "we hold (Berakhot"
    ens[3] = "39a) that it does not obligate"
    write("905a", raw, ens)


def test_classifier_synthetic():
    print("classifier (synthetic corpus):")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        synth_corpus(tmp)
        saved = ars.LEARN_DIR, ars.TALMUDDEV_DIR
        ars.LEARN_DIR, ars.TALMUDDEV_DIR = tmp / "learning", tmp / "talmuddev"
        try:
            p = ars.profile_daf("901a", allowed=set())
            check("synthetic shifted -> SHIFTED", p["classification"] == "SHIFTED",
                  p["classification"])
            check("shifted not haikuSafe", not p["haikuSafe"])
            check("shifted -> rashi-realignment",
                  p["recommendedTaskType"] == "rashi-realignment")

            p = ars.profile_daf("902a", allowed=set())
            check("synthetic fabricated -> FABRICATION-SUSPECT",
                  p["classification"] == "FABRICATION-SUSPECT", p["classification"])
            check("fabricated -> rashi-reconstruction",
                  p["recommendedTaskType"] == "rashi-reconstruction")

            p = ars.profile_daf("903a", allowed=set())
            check("synthetic aligned -> ALIGNED", p["classification"] == "ALIGNED",
                  p["classification"])
            check("aligned is haikuSafe", p["haikuSafe"])

            p = ars.profile_daf("904a", allowed=set())
            check("anchor-poor -> INSUFFICIENT-ANCHORS",
                  p["classification"] == "INSUFFICIENT-ANCHORS", p["classification"])
            check("insufficient is haikuSafe (never blocks)", p["haikuSafe"])

            # allowlisted defect lines do not count toward fabrication
            p = ars.profile_daf("902a", allowed={("902a", 3), ("902a", 6)})
            check("allowlisted misses excluded from fabrication",
                  p["classification"] != "FABRICATION-SUSPECT", p["classification"])

            # 905a: the report's "shift candidates" count must not flag a
            # genuine split-continuation citation (offset +1, flagged),
            # while 901a's real SHIFTED daf must still be flagged.
            import contextlib
            import io
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                ars.run_report(["905a"], top=15)
            check("split-continuation citation is not a shift candidate in the report",
                  "0 shift candidate(s)" in buf.getvalue(), buf.getvalue())

            buf2 = io.StringIO()
            with contextlib.redirect_stdout(buf2):
                ars.run_report(["901a"], top=15)
            check("genuine SHIFTED daf still reported as shift candidate(s)",
                  "0 shift candidate(s)" not in buf2.getvalue(), buf2.getvalue())
        finally:
            ars.LEARN_DIR, ars.TALMUDDEV_DIR = saved


def test_drift_block():
    print("preflight drift block:")
    bad = {"daf": "901a", "classification": "SHIFTED", "haikuSafe": False,
           "anchorsFound": 2, "anchorsMissing": 0, "maxAbsOffset": 5,
           "recommendedTaskType": "rashi-realignment"}
    good = dict(bad, classification="ALIGNED", haikuSafe=True, recommendedTaskType=None)

    err = drift_block_error(bad, "repair", env={})
    check("repair blocked on SHIFTED", err is not None and "rashi-realignment" in err)
    check("block names the daf", err is not None and "901a" in err)
    check("links blocked too", drift_block_error(bad, "links", env={}) is not None)
    check("shifted-block task not blocked (realignment remedy)",
          drift_block_error(bad, "shifted-block", env={}) is None)
    check("reconstruct task not blocked", drift_block_error(bad, "reconstruct", env={}) is None)
    check("aligned daf not blocked", drift_block_error(good, "repair", env={}) is None)
    check("worker env alone cannot unblock (only FABLE_DRIFT_OVERRIDE=1)",
          drift_block_error(bad, "repair", env={"FABLE_DRIFT_OVERRIDE": "0"}) is not None)
    check("Fable override env unblocks",
          drift_block_error(bad, "repair", env={"FABLE_DRIFT_OVERRIDE": "1"}) is None)


# ---------- layer 2: live corpus (self-retiring) ----------

def stub_daf_still_documented(daf):
    al = json.loads((Path(__file__).parent / "allowlists" /
                     "rashi_content_allowlist.json").read_text())
    return any(e["daf"] == daf and e["reason"] == "stub_continuation"
               for e in al.get("entries", []))


def test_live_corpus():
    print("live corpus (self-retiring while the documented defects remain):")
    allowed = ars.load_allowlisted()
    for daf in ("67b", "68a", "68b", "70a", "71b"):
        if not stub_daf_still_documented(daf):
            print(f"  skip  {daf} (stub entries drained; defect presumably realigned)")
            continue
        p = ars.profile_daf(daf, allowed)
        check(f"{daf} classifies SHIFTED", p["classification"] == "SHIFTED",
              p["classification"])
        check(f"{daf} blocked from repair",
              drift_block_error(p, "repair", env={}) is not None)

    # 61a lines 1-45: fabricated while its Shevuot citations (Hebrew L10,
    # L33) appear nowhere in the English.
    trans = json.loads((Path(__file__).parent.parent / "assets" / "learning" /
                        "yoma" / "61a.learning.json").read_text())["rashiTranslations"]
    if any("shevu" in e.get("en", "").lower() for e in trans):
        print("  skip  61a (Shevuot citations now translated; presumably reconstructed)")
    else:
        p = ars.profile_daf("61a", allowed)
        check("61a classifies FABRICATION-SUSPECT",
              p["classification"] == "FABRICATION-SUSPECT", p["classification"])
        check("61a blocked from repair",
              drift_block_error(p, "repair", env={}) is not None)

    # A clean daf must stay repair-eligible (no false hard-block).
    for daf in ("2a", "12b"):
        p = ars.profile_daf(daf, allowed)
        check(f"{daf} haikuSafe (clean daf not blocked)", p["haikuSafe"],
              p["classification"])
        check(f"{daf} repair not blocked", drift_block_error(p, "repair", env={}) is None)


def main():
    test_anchor_extraction()
    test_same_parens_daf_citation()
    test_split_continuation_dafnum()
    test_classifier_synthetic()
    test_drift_block()
    test_live_corpus()
    if FAILURES:
        print(f"\nFAILED: {len(FAILURES)} check(s): {FAILURES}")
        sys.exit(1)
    print("\nOK: all drift-profile tests passed.")


if __name__ == "__main__":
    main()
