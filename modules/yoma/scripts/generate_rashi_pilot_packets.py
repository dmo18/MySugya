#!/usr/bin/env python3
"""
generate_rashi_pilot_packets.py - Rashi translation-quality campaign, Step 4:
review-packet generation for the frozen pilot cohort.

Reads the frozen cohort (docs/reports/data/rashi-pilot-cohort.json, written
by select_rashi_pilot_cohort.py) and live learning_data.js, and produces one
review packet per cohort entry: the Hebrew Rashi, its current English, every
linked Gemara line's Hebrew/English/literal text, a window of surrounding
Gemara context, neighboring Rashi entries on the same daf, the entry's risk
signals, the style-guide sections and terminology-registry entries that
apply to it, and its historical provenance - plus a blank review record for
a human reviewer to fill in.

This tool assembles CONTEXT only. It does not read Hebrew, compare it to
English, or draw any semantic conclusion - the campaign's governing
directive is explicit that semantic conclusions may not be automated. The
`review` block in every packet starts null/empty and stays that way until a
human (or an AI acting as a human reviewer, reading and reasoning the way a
human would, never a regex or heuristic) fills it in during the actual
review pass.
"""
import argparse
import json
import re
import sys
from pathlib import Path

SCRIPTS = Path(__file__).parent
ROOT = SCRIPTS.parent
REPO_ROOT = ROOT.parent.parent
DATA_DIR = REPO_ROOT / "docs" / "reports" / "data"
COHORT_PATH = DATA_DIR / "rashi-pilot-cohort.json"
REGISTRY_PATH = DATA_DIR / "rashi-terminology-registry.json"
OUT_PATH = DATA_DIR / "rashi-pilot-review-packets.json"

sys.path.insert(0, str(SCRIPTS))
from audit_rashi_translation_risk import load_corpus  # noqa: E402

CONTEXT_WINDOW = 2  # gemara lines before/after the linked line(s)
NEIGHBOR_WINDOW = 2  # rashi entries before/after the pilot entry

STRATUM_TO_STYLE_SECTIONS = {
    "sacrificial_terminology": ["Sacrificial terminology"],
    "priesthood_or_temple_terminology": ["Priesthood terminology", "Temple terminology"],
    "purity_terminology": ["Purity terminology"],
    "short_gloss": ["When not to expand the text"],
    "long_explanation": ["Narrative or contextual explanation", "When not to expand the text"],
    "narrative_or_contextual_explanation": ["Logical connectors", "Elliptical Hebrew and dibbur hamatchil fragments"],
    "multiple_linked_gemara_lines": ["Quotations from Gemara vs. quotations from Scripture"],
    "terminology_variance_signal": ["Terminology registry"],
    "historical_reconstruction_or_realignment": ["Recurring Rashi formulas"],
}
ALWAYS_APPLICABLE_SECTIONS = [
    "Names and titles",
    "Rabbi / Rav conventions",
    "Elliptical Hebrew and dibbur hamatchil fragments",
    "Punctuation",
    "Capitalization",
]


def style_sections_for(strata):
    sections = list(ALWAYS_APPLICABLE_SECTIONS)
    for s in strata:
        for sec in STRATUM_TO_STYLE_SECTIONS.get(s, []):
            if sec not in sections:
                sections.append(sec)
    return sections


def load_registry():
    reg = json.loads(REGISTRY_PATH.read_text())
    terms = []
    for tier_name in ("near_invariant", "contextual", "do_not_enforce"):
        for t in reg["tiers"][tier_name]["terms"]:
            terms.append({
                "hebrew": t["hebrew"],
                "tier": tier_name,
                "rendering": t.get("canonicalRendering") or t.get("dominantRendering"),
                "acceptableVariants": t.get("acceptableVariants") or t.get("commonRenderings") or [],
            })
    return terms


def registry_matches(he, registry_terms):
    return [t for t in registry_terms if t["hebrew"] in (he or "")]


def ordered_lines(daf_line_items):
    return sorted(daf_line_items.values(), key=lambda item: item.get("vilna_line", 0))


def gemara_context(daf_lines_ordered, linked_ids):
    ids_in_order = [item["id"] for item in daf_lines_ordered]
    positions = [ids_in_order.index(i) for i in linked_ids if i in ids_in_order]
    if not positions:
        return {"linked": [], "before": [], "after": []}
    lo, hi = min(positions), max(positions)
    before = daf_lines_ordered[max(0, lo - CONTEXT_WINDOW):lo]
    after = daf_lines_ordered[hi + 1:hi + 1 + CONTEXT_WINDOW]
    linked = daf_lines_ordered[lo:hi + 1]

    def slim(item):
        return {
            "id": item["id"],
            "kind": item.get("kind"),
            "he": item.get("he"),
            "en": item.get("en"),
            "en_lit": item.get("en_lit"),
            "sefaria_ref": item.get("sefaria_ref"),
        }

    return {
        "linked": [slim(i) for i in linked],
        "before": [slim(i) for i in before],
        "after": [slim(i) for i in after],
    }


def rashi_neighbors(daf_rashi_sorted, entry_id):
    ids = [r["id"] for r in daf_rashi_sorted]
    idx = ids.index(entry_id)
    lo = max(0, idx - NEIGHBOR_WINDOW)
    hi = min(len(daf_rashi_sorted), idx + NEIGHBOR_WINDOW + 1)
    return [
        {"id": r["id"], "vilnaLine": r["vilnaLine"], "he": r["he"], "en": r["en"]}
        for r in daf_rashi_sorted[lo:hi] if r["id"] != entry_id
    ]


def blank_review_record():
    return {
        "reviewMethod": "human-equivalent semantic review: Hebrew read independently, "
                        "linked Gemara and surrounding context read, English compared "
                        "against Hebrew and context, style guide applied without forcing "
                        "advisory terminology",
        "disposition": None,
        "defectTags": [],
        "evidence": None,
        "finalEnglish": None,
        "secondPass": {"result": None, "notes": None},
        "structuralStop": None,
        "repairPR": None,
        "finalVerificationSHA": None,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cohort", default=str(COHORT_PATH))
    ap.add_argument("--out", default=str(OUT_PATH))
    args = ap.parse_args()

    cohort = json.loads(Path(args.cohort).read_text())
    daf_order, rashi_by_daf, lines_by_daf = load_corpus()
    registry_terms = load_registry()

    rashi_sorted_by_daf = {
        daf: sorted(rashi_by_daf[daf], key=lambda r: r["vilnaLine"]) for daf in daf_order
    }
    lines_ordered_by_daf = {daf: ordered_lines(lines_by_daf[daf]) for daf in daf_order}

    packets = []
    for c in cohort["entries"]:
        daf = c["daf"]
        packets.append({
            "id": c["id"],
            "daf": daf,
            "perek": c["perek"],
            "vilnaLine": c["vilnaLine"],
            "he": c["he"],
            "en": c["en"],
            "linkedGemaraLineIds": c["linkedGemaraLineIds"],
            "gemaraContext": gemara_context(lines_ordered_by_daf[daf], c["linkedGemaraLineIds"]),
            "neighboringRashi": rashi_neighbors(rashi_sorted_by_daf[daf], c["id"]),
            "riskScore": c["riskScore"],
            "riskSignals": c["riskSignals"],
            "priorReviewDepth": c["priorReviewDepth"],
            "selectionStratum": c["selectionStratum"],
            "applicableStyleGuideSections": style_sections_for(c["selectionStratum"]),
            "applicableTerminologyRegistryEntries": registry_matches(c["he"], registry_terms),
            "review": blank_review_record(),
        })

    out = {
        "schemaVersion": 1,
        "generatedFromCohort": args.cohort,
        "totalPackets": len(packets),
        "packets": packets,
    }
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {args.out} ({len(packets)} packets)")


if __name__ == "__main__":
    main()
