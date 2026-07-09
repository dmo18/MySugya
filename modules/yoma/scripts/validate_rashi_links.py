#!/usr/bin/env python3
"""
validate_rashi_links.py - referential-integrity gate for linkedGemaraLineIds
in the Rashi helper layer.

Checks every rashiTranslations entry in assets/learning/yoma/*.learning.json:
  1. Every non-empty linkedGemaraLineIds value must exist in that daf's real
     Gemara line id set (extracted from the generated learning_data.js, whose
     freshness is enforced separately by check_generated_freshness.py).
  2. No cross-daf ids: every id must carry this daf's own zero-padded prefix.

Pre-existing bogus ids (117 on 7b-9b, documented in
docs/rashi-audit-backlog.md) are tolerated via
allowlists/rashi_links_allowlist.json (exact daf+vilnaLine+id triples).
Ratchet semantics: never add new entries; remove entries as daf are repaired.
Stale allowlist entries are reported as warnings.

Also REPORTS (non-fatal) the per-daf percentage of entries with empty
linkedGemaraLineIds, so the unlinked back half of the tractate stays visible.

Exit 1 on any non-allowlisted bogus or cross-daf id. Offline, no network.
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
LEARN_DIR = ROOT / "assets" / "learning" / "yoma"
DATA_JS = ROOT / "learning_data.js"
ALLOWLIST = Path(__file__).parent / "allowlists" / "rashi_links_allowlist.json"

GEMARA_ID_RE = re.compile(r'id:\s*"(yoma-[0-9]+[ab]-l[0-9]+[ab]?)"')
DAF_BLOCK_RE = re.compile(r'// YOMA (\S+)')


def daf_pad(daf):
    m = re.match(r"(\d+)([ab])", daf)
    return f"{int(m.group(1)):03d}{m.group(2)}"


def gemara_ids_per_daf():
    """Extract each daf's Gemara line id set from generated learning_data.js.

    Matches only bare yoma-NNN[ab]-lNN ids; rashi-* ids do not match because
    the pattern is anchored to the opening quote.
    """
    text = DATA_JS.read_text()
    starts = [(m.group(1), m.start()) for m in DAF_BLOCK_RE.finditer(text)]
    out = defaultdict(set)
    for i, (daf, s) in enumerate(starts):
        e = starts[i + 1][1] if i + 1 < len(starts) else len(text)
        for m in GEMARA_ID_RE.finditer(text[s:e]):
            out[daf].add(m.group(1))
    return out


def main():
    if not DATA_JS.exists():
        sys.exit("ERROR: learning_data.js not found; run build_learning_data.py first.")

    allow = set()
    if ALLOWLIST.exists():
        data = json.loads(ALLOWLIST.read_text())
        allow = {(e["daf"], e["vilnaLine"], e["id"]) for e in data.get("entries", [])}

    valid = gemara_ids_per_daf()
    errors = []
    seen_bogus = set()
    empty_by_daf = {}
    checked_daf = 0
    checked_links = 0

    for path in sorted(LEARN_DIR.glob("*.learning.json")):
        daf = path.name.replace(".learning.json", "")
        trans = json.loads(path.read_text()).get("rashiTranslations", [])
        if not trans:
            continue
        checked_daf += 1
        prefix = f"yoma-{daf_pad(daf)}-"
        empty = 0
        for e in trans:
            links = e.get("linkedGemaraLineIds", [])
            vl = e.get("vilnaLine")
            if not links:
                empty += 1
                continue
            for lid in links:
                checked_links += 1
                if not lid.startswith(prefix):
                    key = (daf, vl, lid)
                    seen_bogus.add(key)
                    if key not in allow:
                        errors.append(f"{daf} L{vl}: cross-daf or mis-prefixed id {lid!r} (expected prefix {prefix!r})")
                elif lid not in valid.get(daf, set()):
                    key = (daf, vl, lid)
                    seen_bogus.add(key)
                    if key not in allow:
                        errors.append(f"{daf} L{vl}: id {lid!r} does not exist in learning_data.js Gemara id set")
        empty_by_daf[daf] = (empty, len(trans))

    stale = sorted(allow - seen_bogus)
    if stale:
        print(f"NOTE: {len(stale)} allowlist entries no longer violate; remove them from "
              f"{ALLOWLIST.name} to ratchet down:")
        for daf, vl, lid in stale[:10]:
            print(f"  stale: {daf} L{vl} {lid}")
        if len(stale) > 10:
            print(f"  ... and {len(stale) - 10} more")

    worst = sorted(((e / t, daf, e, t) for daf, (e, t) in empty_by_daf.items() if t), reverse=True)
    fully_or_mostly_empty = [(daf, e, t) for frac, daf, e, t in worst if frac >= 0.5]
    total_empty = sum(e for e, t in empty_by_daf.values())
    total_entries = sum(t for e, t in empty_by_daf.values())
    print(f"\nREPORT (non-fatal): empty linkedGemaraLineIds: {total_empty}/{total_entries} entries "
          f"({100 * total_empty / total_entries:.0f}%) across {checked_daf} daf; "
          f"{len(fully_or_mostly_empty)} daf are >= 50% unlinked.")
    for daf, e, t in fully_or_mostly_empty[:10]:
        print(f"  {daf}: {e}/{t} unlinked")
    if len(fully_or_mostly_empty) > 10:
        print(f"  ... and {len(fully_or_mostly_empty) - 10} more")

    allowed_count = len(seen_bogus & allow)
    if errors:
        print("\nRashi link validation FAILED:\n")
        for e in errors[:40]:
            print(f"  ERROR  {e}")
        if len(errors) > 40:
            print(f"  ... and {len(errors) - 40} more")
        print(f"\n{len(errors)} error(s); {allowed_count} documented pre-existing bogus ids tolerated via allowlist.")
        sys.exit(1)

    print(f"\nOK: linkedGemaraLineIds valid across {checked_daf} daf "
          f"({checked_links} non-empty links checked; {allowed_count} documented pre-existing "
          f"bogus ids on 7b-9b tolerated via allowlist; see docs/rashi-audit-backlog.md).")


if __name__ == "__main__":
    main()
