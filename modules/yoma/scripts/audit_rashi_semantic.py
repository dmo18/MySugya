#!/usr/bin/env python3
"""
audit_rashi_semantic.py - ADVISORY semantic plausibility report for the
Rashi helper layer. Never blocks CI; always exits 0 unless --strict.

This cannot prove a translation correct. It flags lines whose English is
UNLIKELY to be a rendering of its own Hebrew, using anchor tokens that
survive translation:

  - Parenthesized citations in the Hebrew: biblical books (e.g. (viykra h)),
    tractate/daf references (e.g. (daf pv.)). If the citation's English
    name appears not in this line's en but in a NEIGHBOR's en (window +-4),
    that is a SHIFT candidate, the strongest signal (this is the manual
    method that confirmed the documented 12b and 41a drift blocks).
  - Anchors that appear nowhere nearby: MISSING-anchor flag (weaker; the
    translation may legitimately paraphrase).
  - Long, specific Hebrew rendered as very short generic English:
    GENERIC flag (weakest).

Lines tolerated by allowlists/rashi_content_allowlist.json (documented
scaffold blocks) are skipped; they are already known to be non-faithful.

Output: per-daf ranked summary (shift candidates weighted 3x, missing 1x,
generic 0.5x) and the top individual shift candidates with evidence.

Usage:
  python3 scripts/audit_rashi_semantic.py             # whole corpus
  python3 scripts/audit_rashi_semantic.py 41a 12b     # specific daf
  --top N   how many daf/lines to print (default 15)
  --strict  exit 1 if any shift candidate is found (not used in CI)
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

WINDOW = 4

# Hebrew source-name -> acceptable English tokens (lowercase substring match)
NAME_MAP = {
    "בראשית": ["genesis", "bereshit", "bereishit"],
    "שמות": ["exodus", "shemot", "shemos"],
    "ויקרא": ["leviticus", "vayikra"],
    "במדבר": ["numbers", "bamidbar"],
    "דברים": ["deuteronomy", "devarim"],
    "ישעיה": ["isaiah", "yeshaya"],
    "יחזקאל": ["ezekiel", "yechezkel"],
    "משלי": ["proverbs", "mishlei"],
    "תהלים": ["psalms", "tehillim"],
    "דניאל": ["daniel"],
    "סנהדרין": ["sanhedrin"],
    "זבחים": ["zevachim", "zevahim"],
    "מנחות": ["menachot", "menahot"],
    "שבועות": ["shevuot", "shevuos", "shavuot"],
    "כלים": ["kelim"],
    "סוכה": ["sukkah", "succah"],
    "פסחים": ["pesachim"],
    "חולין": ["chullin", "hullin"],
    "עירובין": ["eruvin", "eiruvin"],
    "מגילה": ["megillah", "megilla"],
    "תענית": ["taanit", "taanis"],
    "ברכות": ["berachot", "berakhot", "brachot"],
    "שבת": ["shabbat", "shabbos"],
}
CITATION_RE = re.compile(r"\(([֐-׿\"'׳״ .]{2,20})\)")


def anchors_of(he):
    """Yield (hebrew_token, [english_tokens]) anchors found in a Hebrew line."""
    for m in CITATION_RE.finditer(he):
        inner = m.group(1)
        for heb, engs in NAME_MAP.items():
            if heb in inner:
                yield heb, engs
    # bare tractate names outside parentheses are too noisy; citations only


def en_has(en_low, engs):
    return any(t in en_low for t in engs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("daf", nargs="*", help="specific daf (default: all)")
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--strict", action="store_true")
    opts = ap.parse_args()

    allowed = set()
    if CONTENT_ALLOWLIST.exists():
        data = json.loads(CONTENT_ALLOWLIST.read_text())
        allowed = {(e["daf"], e["vilnaLine"]) for e in data.get("entries", [])}

    targets = opts.daf or sorted(p.name.replace(".learning.json", "")
                                 for p in LEARN_DIR.glob("*.learning.json"))
    daf_scores = []
    shift_details = []

    for daf in targets:
        lpath = LEARN_DIR / f"{daf}.learning.json"
        tpath = TALMUDDEV_DIR / f"{daf}.json"
        if not lpath.exists() or not tpath.exists():
            continue
        trans = json.loads(lpath.read_text()).get("rashiTranslations", [])
        raw = [l for l in json.loads(tpath.read_text()).get("rashi", []) if l and l.strip()]
        if not trans:
            continue
        ens = {e["vilnaLine"]: e.get("en", "") for e in trans}
        n = len(raw)
        shifts = missing = generic = 0

        for v in range(1, n + 1):
            if (daf, v) in allowed or v not in ens:
                continue
            he = raw[v - 1]
            en_low = ens[v].lower()
            for heb, engs in anchors_of(he):
                if en_has(en_low, engs):
                    continue
                hit = None
                for d in list(range(-WINDOW, 0)) + list(range(1, WINDOW + 1)):
                    nb = v + d
                    if nb in ens and (daf, nb) not in allowed and en_has(ens[nb].lower(), engs):
                        hit = d
                        break
                if hit is not None:
                    shifts += 1
                    shift_details.append((daf, v, hit, heb, engs[0]))
                else:
                    missing += 1
            if len(he) > 80 and len(ens[v].strip()) < 45:
                generic += 1

        score = 3 * shifts + missing + 0.5 * generic
        if score:
            daf_scores.append((score, daf, shifts, missing, generic, n))

    daf_scores.sort(reverse=True)
    print("ADVISORY semantic plausibility report (flags likelihood, not proof)")
    print(f"\n=== Ranked daf (top {opts.top}) ===")
    print(f"{'daf':5s} {'score':>6s} {'shift':>5s} {'miss':>5s} {'genrc':>5s} {'lines':>5s}")
    for score, daf, s, m, g, n in daf_scores[:opts.top]:
        print(f"{daf:5s} {score:6.1f} {s:5d} {m:5d} {g:5d} {n:5d}")

    print(f"\n=== Top shift candidates (citation found in neighbor, not own line) ===")
    for daf, v, d, heb, eng in shift_details[:opts.top]:
        print(f"  {daf} L{v}: Hebrew cites ({heb}) but {eng!r} appears at L{v + d} (offset {d:+d})")

    total_shifts = len(shift_details)
    print(f"\nTotals: {total_shifts} shift candidate(s), "
          f"{sum(m for _, _, _, m, _, _ in daf_scores)} missing-anchor flag(s), "
          f"{sum(g for _, _, _, _, g, _ in daf_scores)} generic flag(s) "
          f"across {len(daf_scores)} flagged daf.")
    if opts.strict and total_shifts:
        sys.exit(1)


if __name__ == "__main__":
    main()
