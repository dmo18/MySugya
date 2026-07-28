#!/usr/bin/env python3
"""
audit_rashi_association.py - referential-integrity and coverage audit for
linkedGemaraLineIds, built on the authoritative structural parser
(_js_parser.py) rather than ad hoc regex scanning of whole daf blocks.

This checks the SAME underlying fact as validate_rashi_links.py (every
non-empty linkedGemaraLineIds value must resolve to a real local line
object), but at finer granularity: it classifies every declared association
(multi-link / mishnah / suffixed / sparse / boundary / plain) and can emit an
exact JSON plan - including the real he/en/kind of both the Rashi entry and
its target line - for tests/browser/rashi-association.spec.js to assert
against without ever hardcoding expected text.

Validity is exact-id-equality only. A bare "yoma-043a-l01" is NOT considered
valid merely because "yoma-043a-l01a" and "yoma-043a-l01b" exist; no prefix
or startswith tolerance is applied anywhere in this file. A target is valid
only if it is the literal id of an object inside that daf's own lines: [...]
array (Gemara or Mishnah - both live in the same array, distinguished only by
kind, and neither gets special-cased for validity).

Daf scope is derived by parsing the real "<daf>": { ... } blocks (via
_js_parser.parse_daf_blocks) - never a hardcoded numeric range - so this
script can never manufacture a daf (such as 88b) that does not exist in the
generated file.

Modes:
  --target DAF                 exactly one daf (default: 11a)
  --range-from A --range-to B  exact inclusive canonical range
  --corpus                     honest sample: first/middle/last Rashi entry
                                per daf, plus every multi-link, Mishnah,
                                suffixed, sparse, and boundary entry in the
                                whole corpus
  --exhaustive-corpus          every Rashi entry and every declared
                                association in the whole corpus

Output: human-readable text (default) or --json (exact plan, including he/en,
consumed by the browser spec and the readiness gate).

Exit nonzero (in both text and JSON modes) when any association resolves to
a target that does not exist, or that exists in a different daf than the one
declaring it. Boundary (empty-link) entries are reported but do not fail the
gate, consistent with validate_rashi_links.py's existing non-fatal treatment
of not-yet-linked entries.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _js_parser import parse_daf_blocks, parse_line_items_from_lines_array, parse_rashi_lines_array

ROOT = Path(__file__).parent.parent
DATA_JS = ROOT / "learning_data.js"

SUFFIXED_RE = re.compile(r"\d+[a-z]$")


def daf_pad(daf):
    m = re.match(r"^(\d+)([ab])$", daf)
    if not m:
        raise ValueError(f"not a canonical daf id: {daf!r}")
    return f"{int(m.group(1)):03d}{m.group(2)}"


def load_corpus(text):
    """Return dict daf_id -> {"lines_by_id": {...}, "rashi": [...]} for every
    real daf block in the generated file, in file order.
    """
    corpus = {}
    for daf, block in parse_daf_blocks(text):
        line_items = parse_line_items_from_lines_array(block)
        lines_by_id = {item["id"]: item for item in line_items}
        rashi_items = parse_rashi_lines_array(block)
        corpus[daf] = {"lines_by_id": lines_by_id, "rashi": rashi_items}
    return corpus


def analyze_daf(daf, daf_data):
    """Return (entries, errors) for one daf.

    entries: list of dicts, one per rashi item, each carrying its own
    "associations" list (one dict per declared target, exact target he/en/
    kind resolved when the target exists).
    errors: list of human-readable error strings for broken/cross-daf ids.
    """
    lines_by_id = daf_data["lines_by_id"]
    rashi_items = daf_data["rashi"]
    prefix = f"yoma-{daf_pad(daf)}-"

    entries = []
    errors = []
    prev_vilna_line = None

    for r in rashi_items:
        targets = r["linkedGemaraLineIds"]
        if len(targets) == 0:
            entry_category = "boundary"
        elif len(targets) > 1:
            entry_category = "multiLink"
        else:
            entry_category = "single"

        is_sparse = (
            prev_vilna_line is not None
            and r["vilnaLine"] is not None
            and r["vilnaLine"] != prev_vilna_line + 1
        )
        if r["vilnaLine"] is not None:
            prev_vilna_line = r["vilnaLine"]

        associations = []
        for target in targets:
            exists = target in lines_by_id
            is_cross_daf = not target.startswith(prefix)
            is_broken = (not exists) or is_cross_daf
            target_line = lines_by_id.get(target)
            is_mishnah = exists and not is_cross_daf and target_line["kind"] == "mishna"
            is_suffixed = bool(SUFFIXED_RE.search(target))

            if is_cross_daf:
                errors.append(
                    f"{daf} rashi {r['id']} (vilnaLine {r['vilnaLine']}): "
                    f"linkedGemaraLineIds target {target!r} has a different daf's prefix "
                    f"(expected prefix {prefix!r})"
                )
            elif is_broken:
                errors.append(
                    f"{daf} rashi {r['id']} (vilnaLine {r['vilnaLine']}): "
                    f"linkedGemaraLineIds target {target!r} does not exist as a line object on {daf}"
                )

            associations.append({
                "target": target,
                "exists": exists,
                "is_broken": is_broken,
                "is_cross_daf": is_cross_daf,
                "is_mishnah": is_mishnah,
                "is_suffixed": is_suffixed,
                "target_kind": target_line["kind"] if target_line else None,
                "target_he": target_line["he"] if target_line else None,
                "target_en": target_line["en"] if target_line else None,
            })

        entries.append({
            "daf": daf,
            "rashi_id": r["id"],
            "rashi_he": r["he"],
            "rashi_en": r["en"],
            "rashi_vilna_line": r["vilnaLine"],
            "entry_category": entry_category,
            "is_sparse": is_sparse,
            "associations": associations,
        })

    return entries, errors


def select_target_daf(corpus, args):
    all_daf = list(corpus.keys())
    if args.range_from and args.range_to:
        if args.range_from not in corpus:
            sys.exit(f"ERROR: --range-from {args.range_from!r} is not a real daf in {DATA_JS.name}")
        if args.range_to not in corpus:
            sys.exit(f"ERROR: --range-to {args.range_to!r} is not a real daf in {DATA_JS.name}")
        start = all_daf.index(args.range_from)
        end = all_daf.index(args.range_to)
        if end < start:
            sys.exit(f"ERROR: --range-to {args.range_to!r} precedes --range-from {args.range_from!r}")
        return all_daf[start:end + 1]
    if args.exhaustive_corpus:
        return all_daf
    if args.corpus:
        return all_daf  # corpus mode still scans every daf; sampling narrows *entries*, not daf scope
    if args.target not in corpus:
        sys.exit(f"ERROR: --target {args.target!r} is not a real daf in {DATA_JS.name}")
    return [args.target]


def sample_entries_for_daf(entries):
    """Honest corpus (non-exhaustive) sample: first, middle, last entry, plus
    every multi-link / mishnah / suffixed / sparse / boundary entry.
    """
    if not entries:
        return []
    selected_idx = {0, len(entries) - 1, len(entries) // 2}
    for i, e in enumerate(entries):
        if e["entry_category"] in ("multiLink", "boundary"):
            selected_idx.add(i)
        elif e["is_sparse"]:
            selected_idx.add(i)
        elif any(a["is_mishnah"] or a["is_suffixed"] for a in e["associations"]):
            selected_idx.add(i)
    return [entries[i] for i in sorted(selected_idx)]


def summarize(entries):
    counts = {
        "daf": len({e["daf"] for e in entries}),
        "rashi_entries": len(entries),
        "declared_associations": sum(len(e["associations"]) for e in entries),
        "single_link": sum(1 for e in entries if e["entry_category"] == "single"),
        "multi_link": sum(1 for e in entries if e["entry_category"] == "multiLink"),
        "boundary": sum(1 for e in entries if e["entry_category"] == "boundary"),
        "mishnah": sum(1 for e in entries for a in e["associations"] if a["is_mishnah"]),
        "suffixed": sum(1 for e in entries for a in e["associations"] if a["is_suffixed"]),
        "sparse": sum(1 for e in entries if e["is_sparse"]),
        "broken": sum(1 for e in entries for a in e["associations"] if a["is_broken"]),
    }
    return counts


def main():
    parser = argparse.ArgumentParser(description="Audit linkedGemaraLineIds referential integrity and coverage")
    parser.add_argument("--target", default="11a", help="Single daf to audit (default: 11a)")
    parser.add_argument("--range-from", help="Daf range start (e.g., 2a)")
    parser.add_argument("--range-to", help="Daf range end (e.g., 14b)")
    parser.add_argument("--corpus", action="store_true", help="Audit an honest full-corpus sample")
    parser.add_argument("--exhaustive-corpus", action="store_true", help="Audit every daf and every association")
    parser.add_argument("--json", action="store_true", help="Emit exact JSON plan (he/en/kind included)")
    parser.add_argument("--list-daf", action="store_true",
                         help="Print the ordered JSON list of every real daf in the corpus and exit "
                              "(no analysis; for sharding tools that need the authoritative daf order "
                              "without paying for a full exhaustive-corpus plan)")
    args = parser.parse_args()

    if not DATA_JS.exists():
        sys.exit(f"ERROR: {DATA_JS} not found; run build_learning_data.py first.")

    text = DATA_JS.read_text()
    corpus = load_corpus(text)
    if not corpus:
        sys.exit(f"ERROR: no daf blocks found in {DATA_JS.name}")

    if args.list_daf:
        print(json.dumps(list(corpus.keys())))
        sys.exit(0)

    target_daf = select_target_daf(corpus, args)

    all_errors = []
    all_entries = []
    for daf in target_daf:
        entries, errors = analyze_daf(daf, corpus[daf])
        all_errors.extend(errors)
        all_entries.extend(entries)

    if args.corpus and not args.exhaustive_corpus and not (args.range_from and args.range_to):
        by_daf = {}
        for e in all_entries:
            by_daf.setdefault(e["daf"], []).append(e)
        sampled = []
        for daf in target_daf:
            sampled.extend(sample_entries_for_daf(by_daf.get(daf, [])))
        report_entries = sampled
    else:
        report_entries = all_entries

    counts = summarize(report_entries)

    if args.json:
        plan = {
            "daf_list": sorted({e["daf"] for e in report_entries}, key=lambda d: target_daf.index(d)),
            "findings": report_entries,
            "counts": counts,
            "error_count": len(all_errors),
            "errors": all_errors,
            "success": len(all_errors) == 0,
        }
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        sys.exit(0 if not all_errors else 1)

    print(f"Scope: {len(target_daf)} daf ({target_daf[0]}..{target_daf[-1]})" if target_daf else "Scope: (empty)")
    print(f"Counts: daf={counts['daf']} rashi_entries={counts['rashi_entries']} "
          f"declared_associations={counts['declared_associations']} "
          f"single_link={counts['single_link']} multi_link={counts['multi_link']} "
          f"mishnah={counts['mishnah']} suffixed={counts['suffixed']} "
          f"sparse={counts['sparse']} boundary={counts['boundary']} broken={counts['broken']}")

    if all_errors:
        print("\nRashi association audit FAILED:\n")
        for e in all_errors[:40]:
            print(f"  ERROR  {e}")
        if len(all_errors) > 40:
            print(f"  ... and {len(all_errors) - 40} more")
        print(f"\n{len(all_errors)} error(s) found.")
        sys.exit(1)

    print(f"\nOK: no broken or cross-daf linkedGemaraLineIds targets in scope.")
    if counts["boundary"]:
        print(f"NOTE (non-fatal): {counts['boundary']} boundary (empty-link) entries in scope "
              f"are not yet linked; see docs/rashi-audit-backlog.md.")


if __name__ == "__main__":
    main()
