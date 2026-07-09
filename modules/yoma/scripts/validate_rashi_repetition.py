#!/usr/bin/env python3
"""
validate_rashi_repetition.py - template/scaffold repetition gate for the
Rashi helper layer.

Scaffold text tends to repeat: the same sentence or the same sentence
skeleton stamped across many lines of a daf. Genuine translations almost
never collide because the underlying Hebrew differs line to line. This gate
measures within-daf repetition of rashiTranslations.en, excluding lines
already tolerated by allowlists/rashi_content_allowlist.json (the documented
deferred blocks), and fails on NEW repetition only.

Checks per daf (non-allowlisted lines only):
  1. Exact-duplicate en strings appearing >= EXACT_LIMIT times: FAIL.
  2. Skeleton duplicates appearing >= SKELETON_LIMIT times: FAIL unless the
     (daf, skeleton, count) is covered by the baseline file. A skeleton is
     the en with quoted spans, bracketed spans, and digits normalized, so
     formulaic openings with real content do not collide but fully
     templated lines do.
  3. REPORT (non-fatal): daf where one opening prefix (first 4 words)
     covers > 90% of lines, as a style signal.

Baseline: allowlists/rashi_repetition_baseline.json holds documented
pre-existing skeleton repetition (currently the bracket-heavy 41b/42b batch
pending its own repair pass). Ratchet semantics: a baseline entry tolerates
up to its recorded count; counts may only shrink, and new entries are never
added for new work. Stale entries are reported.

Offline, no network. Source of truth is the learning JSON layer.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent.parent
LEARN_DIR = ROOT / "assets" / "learning" / "yoma"
CONTENT_ALLOWLIST = Path(__file__).parent / "allowlists" / "rashi_content_allowlist.json"
BASELINE = Path(__file__).parent / "allowlists" / "rashi_repetition_baseline.json"

EXACT_LIMIT = 3
SKELETON_LIMIT = 4
PREFIX_WORDS = 4
PREFIX_DOMINANCE = 0.90


def skeleton(en):
    s = re.sub(r"'[^']*'", "'X'", en)
    s = re.sub(r"\[[^\]]*\]", "[X]", s)
    s = re.sub(r"[0-9]+", "N", s)
    return s.strip()


def main():
    allowed_lines = set()
    if CONTENT_ALLOWLIST.exists():
        data = json.loads(CONTENT_ALLOWLIST.read_text())
        allowed_lines = {(e["daf"], e["vilnaLine"]) for e in data.get("entries", [])}

    baseline = {}
    if BASELINE.exists():
        data = json.loads(BASELINE.read_text())
        baseline = {(e["daf"], e["skeleton"]): e["maxCount"] for e in data.get("entries", [])}

    errors = []
    reports = []
    used_baseline = set()
    checked_daf = 0

    for path in sorted(LEARN_DIR.glob("*.learning.json")):
        daf = path.name.replace(".learning.json", "")
        trans = json.loads(path.read_text()).get("rashiTranslations", [])
        if not trans:
            continue
        checked_daf += 1

        lines = [(e["vilnaLine"], e.get("en", "").strip()) for e in trans
                 if (daf, e["vilnaLine"]) not in allowed_lines]
        if not lines:
            continue

        exact = Counter(en for _, en in lines if en)
        for en, n in exact.items():
            if n >= EXACT_LIMIT:
                errors.append(f"{daf}: exact en string repeated {n}x: {en[:70]!r}")

        skels = Counter(skeleton(en) for _, en in lines if en)
        for sk, n in skels.items():
            if n >= SKELETON_LIMIT:
                key = (daf, sk)
                if key in baseline and n <= baseline[key]:
                    used_baseline.add(key)
                    continue
                errors.append(f"{daf}: en skeleton repeated {n}x"
                              f"{' (exceeds baseline ' + str(baseline[key]) + 'x)' if key in baseline else ''}"
                              f": {sk[:70]!r}")
                if key in baseline:
                    used_baseline.add(key)

        prefixes = Counter(" ".join(en.split()[:PREFIX_WORDS]) for _, en in lines if en)
        if prefixes:
            top_prefix, top_n = prefixes.most_common(1)[0]
            if len(lines) >= 10 and top_n / len(lines) > PREFIX_DOMINANCE:
                reports.append(f"{daf}: opening prefix {top_prefix!r} covers "
                               f"{top_n}/{len(lines)} non-allowlisted lines")

    stale = sorted(set(baseline) - used_baseline)
    if stale:
        print(f"NOTE: {len(stale)} repetition baseline entries no longer needed; remove them from "
              f"{BASELINE.name} to ratchet down:")
        for daf, sk in stale:
            print(f"  stale: {daf}: {sk[:60]!r}")

    if reports:
        print(f"\nREPORT (non-fatal): dominant opening prefixes ({len(reports)} daf):")
        for r in reports[:10]:
            print(f"  {r}")
        if len(reports) > 10:
            print(f"  ... and {len(reports) - 10} more")

    if errors:
        print("\nRashi repetition validation FAILED:\n")
        for e in errors:
            print(f"  ERROR  {e}")
        print(f"\n{len(errors)} error(s) across {checked_daf} daf.")
        sys.exit(1)

    print(f"\nOK: Rashi repetition gate passed across {checked_daf} daf "
          f"(exact limit {EXACT_LIMIT}, skeleton limit {SKELETON_LIMIT}; "
          f"{len(used_baseline)} documented baseline skeleton(s) tolerated).")


if __name__ == "__main__":
    main()
