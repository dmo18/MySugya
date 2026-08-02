#!/usr/bin/env python3
"""
generate_rashi_systemic_candidates.py - Rashi translation-quality
campaign, Step 5: deterministic candidate generation for the two
cluster-assisted defect families the campaign directive authorizes
(and only these two - "other cluster families require evidence from
later direct review before they may be added").

This script assigns NO disposition and repairs NOTHING. It only proposes,
for human confirmation, entries worth a closer look, exactly as Step 2's
risk-triage tooling already does for its own signals. Every candidate
still requires the full entry-level semantic review method (Hebrew,
linked Gemara, context, style guide, terminology registry) before any
change is made - a candidate list is not a verdict.

Family 1: fabricated "New comment:" scaffold phrase.
  A deterministic, exact literal-string search across every UNREVIEWED
  entry's English for the substring "New comment:". Found 4 times in the
  Step 4 pilot (rashi-yoma-011a-001, -011b-015, -012b-002, -013b-001), all
  4 confirmed genuine fabrications with no Hebrew basis. This is a simple,
  complete, and high-confidence search - not a heuristic - but every hit
  still needs a human to confirm the Hebrew has no real structural marker
  before the phrase is removed (the campaign's Step 4 batch 2 report notes
  a legitimate 'Mishna:' label exists elsewhere and must not be confused
  with this pattern).

Family 2: cross-entry word anticipation.
  Found 7 times in the pilot (rashi-yoma-002a-011, -015a-003, -020b-023,
  -023a-005, -059b-001/002, -065a-001/002), always as a pair: one entry's
  own Hebrew word gets translated early or late by a NEIGHBORING entry.
  The pilot's own defect-tag data shows this pattern correlates strongly
  with Step 2's existing OVEREXPLAINED signal (2 of 3 SHIFTED-tagged pilot
  entries were also OVEREXPLAINED-flagged; OVEREXPLAINED had 100%
  precision, n=3, in the pilot - the strongest signal found). Rather than
  reimplement a new, unproven detector, this generator reuses the existing
  OVEREXPLAINED signal (already computed by audit_rashi_translation_risk.py
  and stored in the inventory) as the primary candidate list, and attaches
  each candidate's immediate daf-neighbors (previous/next vilnaLine) for
  reviewer context, since the pilot's confirmed instances were always
  neighbor pairs. This is explicitly a low-precision aid for prioritizing
  WHERE to look, not a claim that every OVEREXPLAINED entry has this
  specific defect - most do not (batch 1-4 also found OVEREXPLAINED
  entries whose defect was invented interpretive gloss, unrelated to any
  neighbor).

Reads only the live inventory. Writes only
docs/reports/data/rashi-systemic-candidates.json.
"""
import argparse
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).parent
ROOT = SCRIPTS.parent
REPO_ROOT = ROOT.parent.parent
DATA_DIR = REPO_ROOT / "docs" / "reports" / "data"
INVENTORY_PATH = DATA_DIR / "rashi-translation-quality-inventory.json"
OUT_PATH = DATA_DIR / "rashi-systemic-candidates.json"

SCAFFOLD_MARKER = "New comment:"


def find_scaffold_candidates(entries_by_id, unreviewed_ids):
    out = []
    for eid in sorted(unreviewed_ids):
        e = entries_by_id[eid]
        if SCAFFOLD_MARKER in (e["en"] or ""):
            idx = e["en"].index(SCAFFOLD_MARKER)
            out.append({
                "entryId": eid,
                "daf": e["daf"],
                "vilnaLine": e["vilnaLine"],
                "en": e["en"],
                "matchContext": e["en"][max(0, idx - 40):idx + len(SCAFFOLD_MARKER) + 40],
            })
    out.sort(key=lambda c: (c["daf"], c["vilnaLine"]))
    return out


def find_anticipation_candidates(entries_by_id, unreviewed_ids, by_daf_vilnaline):
    out = []
    for eid in sorted(unreviewed_ids):
        e = entries_by_id[eid]
        if not any(s["tag"] == "OVEREXPLAINED" for s in e["riskSignals"]):
            continue
        daf = e["daf"]
        vl = e["vilnaLine"]
        neighbors = []
        for delta in (-1, 1):
            n = by_daf_vilnaline.get((daf, vl + delta))
            if n is not None:
                neighbors.append({
                    "entryId": n["id"],
                    "vilnaLine": n["vilnaLine"],
                    "en": n["en"],
                    "reviewStatus": n["reviewStatus"],
                })
        out.append({
            "entryId": eid,
            "daf": daf,
            "vilnaLine": vl,
            "en": e["en"],
            "overexplainedReason": next(s["reason"] for s in e["riskSignals"] if s["tag"] == "OVEREXPLAINED"),
            "neighbors": neighbors,
        })
    out.sort(key=lambda c: (c["daf"], c["vilnaLine"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT_PATH))
    opts = ap.parse_args()

    inv = json.loads(INVENTORY_PATH.read_text())
    entries_by_id = {e["id"]: e for e in inv["entries"]}
    unreviewed_ids = {e["id"] for e in inv["entries"] if e["reviewStatus"] == "UNREVIEWED"}
    by_daf_vilnaline = {(e["daf"], e["vilnaLine"]): e for e in inv["entries"]}

    scaffold = find_scaffold_candidates(entries_by_id, unreviewed_ids)
    anticipation = find_anticipation_candidates(entries_by_id, unreviewed_ids, by_daf_vilnaline)

    out = {
        "schemaVersion": 1,
        "purpose": "Read-only candidate generation for the two Step 5-authorized cluster-assisted "
                   "families. No disposition or repair is assigned here; every candidate requires "
                   "full entry-level semantic review before any change.",
        "authorizedFamilies": ["new_comment_scaffold", "cross_entry_word_anticipation"],
        "families": {
            "new_comment_scaffold": {
                "method": "exact literal-string search for 'New comment:' across all UNREVIEWED entries' English",
                "candidateCount": len(scaffold),
                "candidates": scaffold,
            },
            "cross_entry_word_anticipation": {
                "method": "reuses the existing Step 2 OVEREXPLAINED signal (100% precision, n=3, in the "
                          "Step 4 pilot) as the primary candidate list, with immediate daf-neighbors "
                          "attached for reviewer context - not a new detector, and explicitly "
                          "low-precision as a claim about THIS specific defect (most OVEREXPLAINED "
                          "entries have unrelated causes; see this file's module docstring)",
                "candidateCount": len(anticipation),
                "candidates": anticipation,
            },
        },
    }
    Path(opts.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {opts.out}: {len(scaffold)} new_comment_scaffold candidate(s), "
          f"{len(anticipation)} cross_entry_word_anticipation candidate(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
