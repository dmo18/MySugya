#!/usr/bin/env python3
"""
audit_rashi_semantic.py - semantic plausibility report and drift profile
for the Rashi helper layer.

Two modes:

  report (default)  ADVISORY ranked report; never blocks CI; exits 0
                    unless --strict.
  --profile         machine-readable per-daf drift profile (JSON when daf
                    are named, compact classification table for a corpus
                    run). This is what the repair preflight block, the
                    work packet warning, and worker:verify consume.

This cannot prove a translation correct. It uses anchor tokens that
survive translation (citations and source names) to flag two failure
modes that pattern gates cannot see, both confirmed on the corpus by the
VERSION 15.84 look-alike audit (docs/reports/rashi-lookalike-shift-audit.md):

  SHIFTED             the English is a genuine translation but its line
                      alignment drifts ahead of the Hebrew (67b/68a/68b/
                      70a/71b: offsets -7 to -15, stub-padded tails).
  FABRICATION-SUSPECT the Hebrew's anchors appear NOWHERE in the English
                      (61a lines 1-45: a fluent essay unrelated to its
                      Hebrew).

Anchor extraction handles what the first-generation detector missed:
  - amud-b citations carry a colon, e.g. (daf nz:), which the old
    character class excluded;
  - tractate names usually sit OUTSIDE the parentheses, e.g.
    d'Zevachim (daf tv:), so names are also matched in a lookbehind
    window before a daf citation;
  - citations split across vilna lines (open paren on one line, close
    on the next) are scanned with the next line's head appended.

Classification (profile mode):
  SHIFTED              2+ anchors at |offset| > 2 with a consistent sign
  FABRICATION-SUSPECT  2+ consecutive anchors (by Hebrew line, skipping
                       allowlisted lines) whose tokens appear nowhere in
                       any non-stub English line within the window
  INSUFFICIENT-ANCHORS fewer than 2 anchors total (no evidence; never
                       blocks)
  ALIGNED              everything else

haikuSafe is true only for ALIGNED and INSUFFICIENT-ANCHORS. The
recommended remedy is rashi-realignment for SHIFTED and
rashi-reconstruction for FABRICATION-SUSPECT (both Fable/Sonnet).

Lines tolerated by allowlists/rashi_content_allowlist.json are excluded
from fabrication counting (they are documented defects) and their stub
English is never used as a token match target, but anchors ON
allowlisted Hebrew lines still participate in offset search: finding a
stub line's content translated 13 lines earlier is the strongest
shift signal there is.

Usage:
  python3 scripts/audit_rashi_semantic.py                  # corpus report
  python3 scripts/audit_rashi_semantic.py 41a 12b          # specific daf
  python3 scripts/audit_rashi_semantic.py --profile 67b    # JSON profile
  python3 scripts/audit_rashi_semantic.py --profile        # corpus table
  --top N    how many daf/lines to print in report mode (default 15)
  --strict   exit 1 if any examined daf is not haikuSafe
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
LEARN_DIR = ROOT / "assets" / "learning" / "yoma"
TALMUDDEV_DIR = ROOT / "assets" / "talmuddev"
CONTENT_ALLOWLIST = Path(__file__).parent / "allowlists" / "rashi_content_allowlist.json"

WINDOW = 25          # offset search radius (real corpus drifts reach 17)
BIG_OFFSET = 2       # |offset| beyond this counts toward SHIFTED
SHIFT_MIN_ANCHORS = 2
FAB_MIN_CONSECUTIVE_MISSES = 2

# Hebrew source name -> compiled English pattern. Word-ish boundaries and
# dotted abbreviation forms so 'gen.' does not match 'generation'.
def _rx(*alts):
    return re.compile("|".join(alts), re.I)

NAME_MAP = {
    "בראשית": _rx(r"genesis", r"bereshit", r"bereishit", r"\bgen\."),
    "שמות": _rx(r"exodus", r"shemot", r"shemos", r"\bex\.", r"\bexod\."),
    "ויקרא": _rx(r"leviticus", r"vayikra", r"\blev\."),
    "במדבר": _rx(r"numbers", r"bamidbar", r"\bnum\."),
    "דברים": _rx(r"deuteronomy", r"devarim", r"\bdeut\."),
    "ישעיה": _rx(r"isaiah", r"yeshaya", r"\bisa\."),
    "יחזקאל": _rx(r"ezekiel", r"yechezkel", r"\bezek\."),
    "משלי": _rx(r"proverbs", r"mishlei", r"\bprov\."),
    "תהלים": _rx(r"psalms", r"tehillim", r"\bps\.", r"\bpss\."),
    "דניאל": _rx(r"daniel", r"\bdan\."),
    "שמואל": _rx(r"samuel", r"\bsam\."),
    "מלכים": _rx(r"kings"),
    "סנהדרין": _rx(r"sanhedrin"),
    "זבחים": _rx(r"zevachim", r"zevahim", r"zevaḥim"),
    "מנחות": _rx(r"menachot", r"menahot", r"menachos"),
    "שבועות": _rx(r"shevuot", r"shevuos", r"shavuot", r"shevu'ot"),
    "כלים": _rx(r"kelim"),
    "סוכה": _rx(r"sukka", r"succa", r"suka"),
    "פסחים": _rx(r"pesachim", r"pesahim"),
    "חולין": _rx(r"chullin", r"hullin"),
    "עירובין": _rx(r"eruvin", r"eiruvin", r"eruvim"),
    "מגילה": _rx(r"megilla", r"megila"),
    "תענית": _rx(r"taanit", r"taanis", r"ta'anit"),
    "ברכות": _rx(r"beracho", r"berakho", r"bracho", r"berachos"),
    "שבת": _rx(r"shabbat", r"shabbos", r"shabbas"),
    "סוטה": _rx(r"sota"),
    "גיטין": _rx(r"gittin", r"gitin"),
    "כריתות": _rx(r"keritot", r"kereitot", r"kerisus"),
    "בבא מציעא": _rx(r"bava metzia", r"\bb\.m\."),
    'ב"מ': _rx(r"bava metzia", r"\bb\.m\."),
    'ב"ב': _rx(r"bava batra", r"\bb\.b\."),
    'ב"ק': _rx(r"bava kamma", r"bava kama", r"\bb\.k\.", r"\bb\.q\."),
    "קידושין": _rx(r"kiddushin", r"kidushin"),
    "כתובות": _rx(r"ketubo", r"kesubo"),
    "נדרים": _rx(r"nedarim"),
    "נזיר": _rx(r"nazir"),
    "חגיגה": _rx(r"chagiga", r"hagiga"),
    "ראש השנה": _rx(r"rosh hashana"),
}
# Tractate-name subset legal for adjacency matching (name OUTSIDE parens,
# immediately before a daf citation).
TRACTATES = {k for k in NAME_MAP
             if k not in ("בראשית", "שמות", "ויקרא", "במדבר", "דברים", "ישעיה",
                          "יחזקאל", "משלי", "תהלים", "דניאל", "שמואל", "מלכים")}

CITATION_RE = re.compile(r"\(([^()]{2,40})\)")
# Same-parens citations may lead with a tractate name/abbreviation or a
# relative reference word (le'eil, lekaman) before "daf", e.g. (b"b daf
# tz:) or (le'eil daf lat.); the leading text is unrestricted as long as
# the literal "daf" token precedes the trailing letters+punct.
DAF_CIT_RE = re.compile(r"\((?:[^()]*?דף\s*)?([א-ת\"׳]{1,4})\s*([.:])\s*\)")
STUB_EN_RE = re.compile(r"rashi line \d+:\s*continuation", re.I)
ADJACENCY_CHARS = 25

GEMATRIA = {"א": 1, "ב": 2, "ג": 3, "ד": 4, "ה": 5, "ו": 6, "ז": 7, "ח": 8,
            "ט": 9, "י": 10, "כ": 20, "ל": 30, "מ": 40, "נ": 50, "ס": 60,
            "ע": 70, "פ": 80, "צ": 90, "ק": 100, "ר": 200}


def gematria_daf(letters, punct):
    """(nz:) -> '57b'. Returns None for non-numeric groups like (shem)."""
    n = 0
    for ch in letters:
        if ch in ('"', "׳"):
            continue
        if ch not in GEMATRIA:
            return None
        n += GEMATRIA[ch]
    if not 2 <= n <= 180:
        return None
    return f"{n}{'a' if punct == '.' else 'b'}"


def anchors_of(he, next_he=""):
    """Yield (kind, hebrew_token, english_regex) anchors found in a Hebrew
    line. kind is 'name' (book/tractate name; a miss counts toward
    fabrication) or 'dafnum' (numeric daf citation via gematria; offset
    evidence only, since English legitimately drops daf numbers). next_he
    (the head of the following line) closes citations split across vilna
    lines."""
    text = he
    if he.count("(") > he.count(")") and next_he:
        text = he + " " + next_he[:40]
    seen = set()
    for m in CITATION_RE.finditer(text):
        inner = m.group(1)
        for heb in NAME_MAP:
            if heb in inner and heb not in seen:
                seen.add(heb)
                yield "name", heb, NAME_MAP[heb]
    for m in DAF_CIT_RE.finditer(text):
        pre = text[max(0, m.start() - ADJACENCY_CHARS):m.start()]
        for heb in TRACTATES:
            if heb in pre and heb not in seen:
                seen.add(heb)
                yield "name", heb, NAME_MAP[heb]
        token = gematria_daf(m.group(1), m.group(2))
        if token and token not in seen:
            seen.add(token)
            yield "dafnum", token, re.compile(rf"\b{token}\b")


def load_allowlisted():
    if not CONTENT_ALLOWLIST.exists():
        return set()
    data = json.loads(CONTENT_ALLOWLIST.read_text())
    return {(e["daf"], e["vilnaLine"]) for e in data.get("entries", [])}


def profile_daf(daf, allowed=None):
    """Compute the drift profile for one daf. Returns None if sources are
    missing. Deterministic; reads only repository files."""
    lpath = LEARN_DIR / f"{daf}.learning.json"
    tpath = TALMUDDEV_DIR / f"{daf}.json"
    if not lpath.exists() or not tpath.exists():
        return None
    if allowed is None:
        allowed = load_allowlisted()
    trans = json.loads(lpath.read_text()).get("rashiTranslations", [])
    raw = [l for l in json.loads(tpath.read_text()).get("rashi", []) if l and l.strip()]
    ens = {e["vilnaLine"]: e.get("en", "") for e in trans}

    def searchable(nb):
        if nb not in ens or (daf, nb) in allowed:
            return None
        en = ens[nb]
        if STUB_EN_RE.search(en):
            return None
        return en

    anchors = []
    for v in range(1, len(raw) + 1):
        he = raw[v - 1]
        nxt = raw[v] if v < len(raw) else ""
        for kind, token, rx in anchors_of(he, nxt):
            offset = None
            for d in sorted(range(-WINDOW, WINDOW + 1), key=lambda x: (abs(x), x)):
                en = searchable(v + d)
                if en is not None and rx.search(en):
                    offset = d
                    break
            anchors.append({"line": v, "kind": kind, "token": token,
                            "offset": offset,
                            "allowlisted": (daf, v) in allowed})

    offsets = [a["offset"] for a in anchors if a["offset"] is not None]
    # Distinct Hebrew lines showing displacement, split by sign; a single
    # citation yielding both a name and a dafnum anchor counts once.
    nz_pos = {a["line"] for a in anchors if a["offset"] is not None and a["offset"] > 0}
    nz_neg = {a["line"] for a in anchors if a["offset"] is not None and a["offset"] < 0}
    big_pos = {a["line"] for a in anchors if a["offset"] is not None and a["offset"] > BIG_OFFSET}
    big_neg = {a["line"] for a in anchors if a["offset"] is not None and a["offset"] < -BIG_OFFSET}
    shifted = ((len(big_neg) >= 1 and len(nz_neg) >= SHIFT_MIN_ANCHORS and not big_pos)
               or (len(big_pos) >= 1 and len(nz_pos) >= SHIFT_MIN_ANCHORS and not big_neg))

    # Fabrication: consecutive missing NAME anchors on non-allowlisted
    # lines (documented-defect lines do not count against the daf; numeric
    # daf anchors are offset evidence only, since English legitimately
    # drops daf numbers).
    max_consec_miss = consec = 0
    for a in anchors:
        if a["allowlisted"] or a["kind"] != "name":
            continue
        if a["offset"] is None:
            consec += 1
            max_consec_miss = max(max_consec_miss, consec)
        else:
            consec = 0
    fabrication = max_consec_miss >= FAB_MIN_CONSECUTIVE_MISSES

    if shifted:
        classification = "SHIFTED"
    elif fabrication:
        classification = "FABRICATION-SUSPECT"
    elif len(anchors) < 2 or not offsets:
        classification = "INSUFFICIENT-ANCHORS"
    else:
        classification = "ALIGNED"
    haiku_safe = classification in ("ALIGNED", "INSUFFICIENT-ANCHORS")
    recommended = {"SHIFTED": "rashi-realignment",
                   "FABRICATION-SUSPECT": "rashi-reconstruction"}.get(classification)
    return {
        "daf": daf,
        "rawLines": len(raw),
        "anchors": anchors,
        "anchorsFound": len(offsets),
        "anchorsMissing": len(anchors) - len(offsets),
        "offsets": offsets,
        "maxAbsOffset": max((abs(o) for o in offsets), default=0),
        "classification": classification,
        "haikuSafe": haiku_safe,
        "recommendedTaskType": recommended,
    }


def all_daf():
    return sorted(p.name.replace(".learning.json", "")
                  for p in LEARN_DIR.glob("*.learning.json"))


def run_profile(targets, as_json_always=False):
    allowed = load_allowlisted()
    named = bool(targets)
    targets = targets or all_daf()
    profiles = [p for p in (profile_daf(d, allowed) for d in targets) if p]
    if named or as_json_always:
        print(json.dumps(profiles if len(profiles) > 1 else profiles[0], indent=1))
    else:
        print("drift profile (corpus): daf not ALIGNED/INSUFFICIENT listed first")
        print(f"{'daf':5s} {'class':22s} {'found':>5s} {'miss':>4s} {'max|off|':>8s}  offsets")
        flagged = [p for p in profiles if not p["haikuSafe"]]
        for p in flagged:
            offs = " ".join(f"{o:+d}" for o in p["offsets"])
            print(f"{p['daf']:5s} {p['classification']:22s} {p['anchorsFound']:5d} "
                  f"{p['anchorsMissing']:4d} {p['maxAbsOffset']:8d}  {offs}")
        print(f"\n{len(flagged)} daf flagged of {len(profiles)} profiled "
              f"(remainder ALIGNED or INSUFFICIENT-ANCHORS).")
    return profiles


def run_report(targets, top):
    """ADVISORY ranked report, backward compatible in shape with the
    first-generation detector (rashi_verify greps the detail lines)."""
    allowed = load_allowlisted()
    targets = targets or all_daf()
    daf_scores, shift_details = [], []
    profiles = []
    for daf in targets:
        p = profile_daf(daf, allowed)
        if not p:
            continue
        profiles.append(p)
        shifts = [a for a in p["anchors"] if a["offset"] not in (None, 0)]
        missing = p["anchorsMissing"]
        # generic flag: long specific Hebrew rendered as very short English
        generic = 0
        trans = json.loads((LEARN_DIR / f"{daf}.learning.json").read_text()).get("rashiTranslations", [])
        raw = [l for l in json.loads((TALMUDDEV_DIR / f"{daf}.json").read_text()).get("rashi", []) if l and l.strip()]
        ens = {e["vilnaLine"]: e.get("en", "") for e in trans}
        for v in range(1, len(raw) + 1):
            if (daf, v) in allowed or v not in ens:
                continue
            if len(raw[v - 1]) > 80 and len(ens[v].strip()) < 45:
                generic += 1
        score = 3 * len(shifts) + missing + 0.5 * generic
        if score or not p["haikuSafe"]:
            daf_scores.append((score, daf, len(shifts), missing, generic,
                               p["rawLines"], p["classification"]))
        for a in shifts:
            shift_details.append((daf, a["line"], a["offset"], a["token"]))

    daf_scores.sort(reverse=True)
    print("ADVISORY semantic plausibility report (flags likelihood, not proof)")
    print(f"\n=== Ranked daf (top {top}) ===")
    print(f"{'daf':5s} {'score':>6s} {'shift':>5s} {'miss':>5s} {'genrc':>5s} {'lines':>5s}  classification")
    for score, daf, s, m, g, n, cls in daf_scores[:top]:
        print(f"{daf:5s} {score:6.1f} {s:5d} {m:5d} {g:5d} {n:5d}  {cls}")

    print(f"\n=== Top shift candidates (citation found at a displaced line) ===")
    for daf, v, d, heb in shift_details[:top]:
        print(f"  {daf} L{v}: Hebrew cites ({heb}) but its English appears at L{v + d} (offset {d:+d})")

    print(f"\nTotals: {len(shift_details)} shift candidate(s), "
          f"{sum(m for _, _, _, m, _, _, _ in daf_scores)} missing-anchor flag(s), "
          f"{sum(g for _, _, _, _, g, _, _ in daf_scores)} generic flag(s) "
          f"across {len(daf_scores)} flagged daf.")
    return profiles


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("daf", nargs="*", help="specific daf (default: all)")
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--profile", action="store_true",
                    help="emit the machine-readable drift profile")
    ap.add_argument("--json", action="store_true",
                    help="with --profile and no daf: JSON instead of the table")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if any examined daf is not haikuSafe")
    opts = ap.parse_args()

    if opts.profile:
        profiles = run_profile(opts.daf, as_json_always=opts.json)
    else:
        profiles = run_report(opts.daf, opts.top)
    if opts.strict and any(not p["haikuSafe"] for p in profiles):
        sys.exit(1)


if __name__ == "__main__":
    main()
