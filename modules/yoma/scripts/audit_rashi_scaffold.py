#!/usr/bin/env python3
"""
audit_rashi_scaffold.py - scaffold-fabrication gate for the Rashi helper layer.

validate_rashi_content.py catches a fixed list of literal placeholder strings.
A second fabrication family evaded it: meta-narration scaffolds ("Rashi:
opens/continues/concludes - ...") that describe what Rashi is doing instead of
translating the line, frequently padded with bracket-guessed editorial
completions ("[the Gemara]", "[that the statute applies]") not present in the
Hebrew, plus line-number placeholders that pass raw Hebrew through as English.
This gate hard-detects that family and ratchets the pre-existing debt.

Rules (anchored; ordinary mid-sentence use of "opens"/"continues"/"concludes"
never matches):

  scaffold-prefix        en begins "Rashi: opens|continues|concludes|closes|
                         completes|begins|resumes ..." (case, colon/comma, and
                         spacing variants included)
  scaffold-bracket-guess a scaffold-prefix line that also carries 2+ bracketed
                         editorial insertions (guessed completions)
  line-number-scaffold   en begins "Rashi on line N" or "[Rashi commentary on
                         line N]" (placeholder framing, not translation)
  hebrew-passthrough     40%+ of the en field's letters are Hebrew script (the
                         raw line was passed through instead of translated)

Debt ratchet: pre-existing hits are inventoried, with content hashes, in
baselines/rashi_scaffold_debt.json (generated from the audited main state;
see docs/reports/yoma-rashi-scaffold-audit.md). Gate semantics:

  - a hit not present in the baseline FAILS (new scaffold text);
  - a hit whose en changed but still matches a rule FAILS (a baseline entry
    covers only the exact contaminated text it was generated from);
  - a baseline entry whose line no longer hits is STALE (warning): remove it
    with --update-baseline, which can only shrink the baseline;
  - baseline growth is never performed by this tool and is forbidden in
    ordinary worker PRs (worker review enforces shrink-only).

Exit 1 on any new or changed hit. Offline, no network.

Usage:
  python3 scripts/audit_rashi_scaffold.py                 # full corpus gate
  python3 scripts/audit_rashi_scaffold.py 12a             # one daf
  python3 scripts/audit_rashi_scaffold.py --range 10a 12b # inclusive range
  python3 scripts/audit_rashi_scaffold.py --json          # machine output
  python3 scripts/audit_rashi_scaffold.py --no-baseline   # raw scan report
  python3 scripts/audit_rashi_scaffold.py --fail-on-debt  # closure mode
  python3 scripts/audit_rashi_scaffold.py --update-baseline  # retire stale
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SCRIPTS = Path(__file__).parent
ROOT = SCRIPTS.parent
LEARN_DIR = ROOT / "assets" / "learning" / "yoma"
BASELINE = SCRIPTS / "baselines" / "rashi_scaffold_debt.json"

SCAFFOLD_VERBS = "opens|continues|concludes|closes|completes|begins|resumes"
SCAFFOLD_PREFIX_RE = re.compile(
    rf"^\s*Rashi\s*[:,]?\s+({SCAFFOLD_VERBS})\b", re.IGNORECASE)
LINE_NUMBER_RE = re.compile(
    r"^\s*\[?\s*Rashi\s+(?:commentary\s+)?on\s+line\s+\d+", re.IGNORECASE)
BRACKET_RE = re.compile(r"\[[^\[\]]+\]")
HEBREW_RE = re.compile(r"[֐-׿]")
BRACKET_GUESS_MIN = 2
HEBREW_RATIO_MIN = 0.40

REMEDIATION = ("rewrite as a direct English translation of this line's own "
               "raw Hebrew; never keep scaffold narration or guessed bracket "
               "completions, even when part of the meaning is correct")


def hebrew_ratio(text):
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if HEBREW_RE.match(c)) / len(letters)


def rules_for(en):
    """Return the ordered list of rule names the en text violates (possibly
    empty). Pure; the single source of truth for detection."""
    rules = []
    m = SCAFFOLD_PREFIX_RE.match(en)
    if m:
        rules.append("scaffold-prefix")
        if len(BRACKET_RE.findall(en)) >= BRACKET_GUESS_MIN:
            rules.append("scaffold-bracket-guess")
    if LINE_NUMBER_RE.match(en):
        rules.append("line-number-scaffold")
    if hebrew_ratio(en) >= HEBREW_RATIO_MIN:
        rules.append("hebrew-passthrough")
    return rules


def signature_of(en, rules):
    m = SCAFFOLD_PREFIX_RE.match(en)
    if m:
        return re.sub(r"\s+", " ", m.group(0).strip().lower())
    return rules[0] if rules else ""


def en_hash(en):
    return hashlib.sha256(en.encode("utf-8")).hexdigest()[:16]


def daf_sort_key(daf):
    m = re.match(r"^(\d+)([ab])$", daf)
    return (int(m.group(1)), m.group(2))


def all_daf():
    return sorted((p.name.replace(".learning.json", "")
                   for p in LEARN_DIR.glob("*.learning.json")), key=daf_sort_key)


def scan_daf(daf):
    """Scan one daf's rashiTranslations. Returns a list of hit dicts."""
    path = LEARN_DIR / f"{daf}.learning.json"
    if not path.exists():
        sys.exit(f"ERROR: no learning JSON for daf {daf!r}")
    hits = []
    for e in json.loads(path.read_text()).get("rashiTranslations", []):
        en = e.get("en", "")
        rules = rules_for(en)
        if rules:
            hits.append({
                "daf": daf, "vilnaLine": e.get("vilnaLine"),
                "rule": rules[0], "rules": rules,
                "signature": signature_of(en, rules),
                "enHash": en_hash(en),
                "message": REMEDIATION,
            })
    return hits


def load_baseline():
    if not BASELINE.exists():
        return {}
    data = json.loads(BASELINE.read_text())
    return {(e["daf"], e["vilnaLine"]): e for e in data.get("entries", [])}


def compare(hits, baseline):
    """Pure gate: split current hits into (new, changed, covered) against the
    baseline index, and find stale baseline entries within the scanned daf
    set. Returns (new, changed, covered, hit_keys, scanned)."""
    new, changed, covered = [], [], []
    hit_keys = set()
    scanned = set()
    for h in hits:
        key = (h["daf"], h["vilnaLine"])
        hit_keys.add(key)
        scanned.add(h["daf"])
        b = baseline.get(key)
        if b is None:
            new.append(h)
        elif b.get("enHash") != h["enHash"]:
            changed.append(h)
        else:
            covered.append(h)
    return new, changed, covered, hit_keys, scanned


def stale_entries(baseline, hit_keys, daf_set):
    return sorted((k for k in baseline
                   if k[0] in daf_set and k not in hit_keys),
                  key=lambda k: (daf_sort_key(k[0]), k[1]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("daf", nargs="*", help="daf to scan (default: full corpus)")
    ap.add_argument("--range", nargs=2, metavar=("FROM", "TO"),
                    help="inclusive daf range, e.g. --range 10a 12b")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--no-baseline", action="store_true",
                    help="raw scan report; no gate, exit 0")
    ap.add_argument("--fail-on-debt", action="store_true",
                    help="also fail while ANY scaffold debt remains in scope")
    ap.add_argument("--update-baseline", action="store_true",
                    help="retire stale baseline entries (shrink-only)")
    opts = ap.parse_args()

    corpus = all_daf()
    if opts.range:
        lo, hi = (daf_sort_key(d) for d in opts.range)
        dafs = [d for d in corpus if lo <= daf_sort_key(d) <= hi]
    elif opts.daf:
        dafs = opts.daf
    else:
        dafs = corpus

    hits = []
    for d in dafs:
        hits.extend(scan_daf(d))

    if opts.no_baseline:
        if opts.json:
            print(json.dumps({"hits": hits, "count": len(hits)}, indent=1))
        else:
            for h in hits:
                print(f"{h['daf']} L{h['vilnaLine']}: {h['rule']} ({h['signature']})")
            print(f"\n{len(hits)} scaffold hit(s) across "
                  f"{len({h['daf'] for h in hits})} daf (raw scan, no baseline).")
        return

    baseline = load_baseline()
    new, changed, covered, hit_keys, _ = compare(hits, baseline)
    stale = stale_entries(baseline, hit_keys, set(dafs))

    if opts.update_baseline:
        if new or changed:
            for h in new:
                print(f"  NEW      {h['daf']} L{h['vilnaLine']}: {h['rule']}")
            for h in changed:
                print(f"  CHANGED  {h['daf']} L{h['vilnaLine']}: {h['rule']}")
            sys.exit("ERROR: --update-baseline is shrink-only; new or changed "
                     "scaffold hits must be fixed in content, never baselined.")
        if not stale:
            print("Baseline already minimal; nothing to retire.")
            return
        data = json.loads(BASELINE.read_text())
        stale_set = set(stale)
        before = len(data["entries"])
        data["entries"] = [e for e in data["entries"]
                           if (e["daf"], e["vilnaLine"]) not in stale_set]
        BASELINE.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
        print(f"Retired {before - len(data['entries'])} stale entr(ies); "
              f"baseline {before} -> {len(data['entries'])}.")
        return

    if opts.json:
        print(json.dumps({
            "scope": dafs, "new": new, "changed": changed,
            "coveredCount": len(covered),
            "stale": [{"daf": k[0], "vilnaLine": k[1]} for k in stale],
            "remainingDebt": len(covered),
        }, indent=1))
    else:
        for h in new:
            print(f"  NEW      {h['daf']} L{h['vilnaLine']}: {h['rule']} "
                  f"({h['signature']}) - {h['message']}")
        for h in changed:
            print(f"  CHANGED  {h['daf']} L{h['vilnaLine']}: {h['rule']} "
                  f"(line edited but still scaffold) - {h['message']}")
        for k in stale:
            print(f"  STALE    {k[0]} L{k[1]}: baseline entry no longer hits; "
                  f"retire it with --update-baseline")

    ok = not new and not changed
    if ok and not (opts.fail_on_debt and covered):
        if not opts.json:
            debt_daf = len({h['daf'] for h in covered})
            print(f"OK: no new scaffold text ({len(covered)} baselined debt "
                  f"line(s) across {debt_daf} daf remain to drain"
                  f"{'; ' + str(len(stale)) + ' stale' if stale else ''}).")
        return
    if not opts.json:
        if not ok:
            print(f"\nFAIL: {len(new)} new / {len(changed)} changed scaffold "
                  f"hit(s). {REMEDIATION}.")
        else:
            print(f"\nFAIL (--fail-on-debt): {len(covered)} baselined scaffold "
                  f"debt line(s) still present in scope.")
    sys.exit(1)


if __name__ == "__main__":
    main()
