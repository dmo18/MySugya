#!/usr/bin/env python3
"""
validate_rashi_content.py - content-quality gate for the Rashi helper layer.

validate_rashi.py checks structure (he order/count vs talmud.dev, en non-empty,
enSource stamped). It deliberately does not judge what the en text says, which
is how placeholder and scaffold text reached main three separate times (the
44a-46b batch, the 61a/67b-71b stubs, the 77a-88a filler). This gate closes
that hole with pattern checks against the enrichment source of truth
(assets/learning/yoma/*.learning.json).

FAILS (exit 1) when any rashiTranslations.en matches a known placeholder or
scaffold pattern, or contains an em dash or en dash, or when a daf's
rashiTranslations count does not match its raw talmud.dev rashi line count.

Pre-existing violations documented in docs/rashi-audit-backlog.md are
tolerated via allowlists/rashi_content_allowlist.json (exact daf+vilnaLine
pairs). The allowlist is a ratchet: new violations are never allowlisted, and
entries are removed as daf are repaired. An allowlist entry whose line no
longer violates is reported as stale (warning only) so the ratchet shrinks.

REPORTS but does not fail (yet): suspiciously short en fields (< 20 chars).

Runs offline. No network. Source of truth is the learning JSON layer, not the
generated learning_data.js.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
LEARN_DIR = ROOT / "assets" / "learning" / "yoma"
TALMUDDEV_DIR = ROOT / "assets" / "talmuddev"
ALLOWLIST = Path(__file__).parent / "allowlists" / "rashi_content_allowlist.json"

EM_DASH = "\u2014"
EN_DASH = "\u2013"

FORBIDDEN_SUBSTRINGS = [
    "Rashi: opens - [line",
    "Rashi: continues - [line",
    "Rashi: concludes - [line",
    "[line ",
    "beyond sugya coverage",
]
FORBIDDEN_CI_SUBSTRINGS = [
    "orphaned",
]
FILLER_EXACT = {
    "Rashi clarifies the ruling and its application.",
    "Rashi elaborates on the halachic details of this sugya.",
}
FORBIDDEN_REGEXES = [
    ("filler_opening", re.compile(r"^Rashi explains the opening discussion of this topic on [0-9]+[ab]\.$")),
    ("stub_commentary", re.compile(r"^Rashi commentary line [0-9]+\.$")),
    ("stub_continuation", re.compile(r"^Rashi line [0-9]+: continuation")),
]

SHORT_EN_THRESHOLD = 20


def violation_for(en):
    """Return a short reason string if en violates the content rules, else None."""
    stripped = en.strip()
    for s in FORBIDDEN_SUBSTRINGS:
        if s in en:
            return f"forbidden substring {s!r}"
    low = en.lower()
    for s in FORBIDDEN_CI_SUBSTRINGS:
        if s in low:
            return f"forbidden substring {s!r} (case-insensitive)"
    if stripped in FILLER_EXACT:
        return "known filler string"
    for name, rx in FORBIDDEN_REGEXES:
        if rx.match(stripped):
            return f"scaffold pattern {name}"
    if EM_DASH in en or EN_DASH in en:
        return "em dash or en dash in helper English"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true",
                    help="emit a machine-readable report (errors, stale allowlist "
                         "entries) on stdout instead of the human-readable report; "
                         "still exits 1 on error, matching the default mode")
    opts = ap.parse_args()

    allow = set()
    count_allow = {}
    if ALLOWLIST.exists():
        data = json.loads(ALLOWLIST.read_text())
        allow = {(e["daf"], e["vilnaLine"]) for e in data.get("entries", [])}
        count_allow = {e["daf"]: (e["transCount"], e["rawCount"])
                       for e in data.get("count_mismatches", [])}

    errors = []
    short_reports = []
    seen_violations = set()
    checked_daf = 0
    checked_lines = 0

    for path in sorted(LEARN_DIR.glob("*.learning.json")):
        daf = path.name.replace(".learning.json", "")
        enrich = json.loads(path.read_text())
        trans = enrich.get("rashiTranslations", [])
        if not trans:
            continue
        checked_daf += 1

        td_path = TALMUDDEV_DIR / f"{daf}.json"
        if td_path.exists():
            raw = [l for l in json.loads(td_path.read_text()).get("rashi", []) if l and l.strip()]
            if len(trans) != len(raw):
                if count_allow.get(daf) == (len(trans), len(raw)):
                    print(f"NOTE: {daf}: tolerating documented count mismatch "
                          f"(rashiTranslations {len(trans)} vs raw {len(raw)}; see backlog).")
                else:
                    errors.append(f"{daf}: rashiTranslations count {len(trans)} != raw talmud.dev rashi count {len(raw)}")

        for e in trans:
            checked_lines += 1
            vl = e.get("vilnaLine")
            en = e.get("en", "")
            reason = violation_for(en)
            if reason:
                seen_violations.add((daf, vl))
                if (daf, vl) not in allow:
                    errors.append(f"{daf} L{vl}: {reason}: {en[:80]!r}")
            if len(en.strip()) < SHORT_EN_THRESHOLD:
                short_reports.append(f"{daf} L{vl}: en only {len(en.strip())} chars: {en.strip()!r}")

    stale = sorted(allow - seen_violations)
    allowed_count = len(seen_violations & allow)

    if opts.json:
        report = {
            "checkedDaf": checked_daf,
            "checkedLines": checked_lines,
            "errors": errors,
            "stale": [{"daf": d, "vilnaLine": vl} for d, vl in stale],
            "allowedCount": allowed_count,
        }
        print(json.dumps(report, indent=1))
        sys.exit(1 if errors else 0)

    if stale:
        print(f"NOTE: {len(stale)} allowlist entries no longer violate; remove them from "
              f"{ALLOWLIST.name} to ratchet down:")
        for daf, vl in stale[:10]:
            print(f"  stale: {daf} L{vl}")
        if len(stale) > 10:
            print(f"  ... and {len(stale) - 10} more")

    if short_reports:
        print(f"\nREPORT (non-fatal): {len(short_reports)} suspiciously short en fields (< {SHORT_EN_THRESHOLD} chars):")
        for r in short_reports[:15]:
            print(f"  {r}")
        if len(short_reports) > 15:
            print(f"  ... and {len(short_reports) - 15} more")

    if errors:
        print("\nRashi content validation FAILED:\n")
        for e in errors:
            print(f"  ERROR  {e}")
        print(f"\n{len(errors)} error(s) across {checked_daf} daf / {checked_lines} lines "
              f"({allowed_count} pre-existing violations tolerated via allowlist).")
        sys.exit(1)

    print(f"\nOK: Rashi helper content gate passed across {checked_daf} daf / {checked_lines} lines "
          f"({allowed_count} documented pre-existing violations tolerated via allowlist; "
          f"see docs/rashi-audit-backlog.md).")


if __name__ == "__main__":
    main()
