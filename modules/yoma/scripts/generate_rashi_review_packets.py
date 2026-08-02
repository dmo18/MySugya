#!/usr/bin/env python3
"""
generate_rashi_review_packets.py - Rashi translation-quality campaign,
Step 6: review-packet generation for any full-corpus batch.

Generalizes generate_rashi_pilot_packets.py (Step 4's frozen-cohort packet
generator) to work from any of the batches in
docs/reports/data/rashi-full-corpus-review-batches.json instead of the
frozen 200-entry pilot cohort. Same context-assembly logic (Gemara context
window, neighboring Rashi, applicable style-guide sections, terminology-
registry matches) - but entries and their riskScore/riskSignals/
priorReviewDepth/linkedGemaraLineIds come from the live translation-quality
inventory, since a batch-plan entry carries only an id, not risk detail.

The applicable-style-guide-sections computation reuses the exact per-entry
conditions select_rashi_pilot_cohort.build_pools uses to fill its stratum
pools (sacrificial/priesthood/purity vocabulary regexes, short-gloss/long-
explanation word-count thresholds, terminology-variance-signal check,
narrative-connector check, multiple-linked-lines check, historical-
provenance check) - applied directly to one entry instead of accumulated
into a corpus-wide sampling pool, since the full corpus has no quota to
fill and every entry still needs to know which style-guide sections apply.

Each packet's "review" block is pre-filled with every field the Step 5
review-record contract (docs/reports/data/rashi-review-record-contract.json)
marks immutable and already known at generation time (batchId, entryId,
daf, hebrew, originalEnglish) and left null/blank for every field only a
human reviewer can supply (proposedEnglish, firstPassDisposition,
defectTags, firstPassEvidence, secondPass, blindQA, finalDisposition,
structuralStop, repairPR, finalVerificationSHA) - so a filled-in "review"
block is directly a valid record for validate_rashi_review_records.py,
with no reshaping step in between.

This tool assembles CONTEXT only, exactly like the pilot generator: it
never reads Hebrew, compares it to English, or draws a semantic
conclusion. It does not write to the live inventory, the batch plan, or
any generated corpus file - it only writes the packet file itself,
wherever --out points (nowhere by default; --out is required so this tool
can never silently leave a stray artifact in docs/reports/data/).

Usage:
  python3 scripts/generate_rashi_review_packets.py --batch-id step6-batch-001 --out /tmp/packet.json
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
BATCHES_PATH = DATA_DIR / "rashi-full-corpus-review-batches.json"

sys.path.insert(0, str(SCRIPTS))
from audit_rashi_translation_risk import load_corpus  # noqa: E402
from generate_rashi_pilot_packets import (  # noqa: E402
    style_sections_for, load_registry, registry_matches, ordered_lines,
    gemara_context, rashi_neighbors,
)
from select_rashi_pilot_cohort import (  # noqa: E402
    word_count, SACRIFICIAL_RE, PRIESTHOOD_TEMPLE_RE, PURITY_RE,
    CONNECTOR_RE, has_terminology_variance_signal, load_registry_terms,
)


def classify_strata(e, variance_registry_terms):
    he, en = e["he"], e["en"]
    wc = word_count(en)
    strata = []
    if e["priorReviewDepth"] in ("known-needs-reconstruction", "known-needs-realignment"):
        strata.append("historical_reconstruction_or_realignment")
    if wc <= 6:
        strata.append("short_gloss")
    if wc >= 30:
        strata.append("long_explanation")
    if SACRIFICIAL_RE.search(he):
        strata.append("sacrificial_terminology")
    if PRIESTHOOD_TEMPLE_RE.search(he):
        strata.append("priesthood_or_temple_terminology")
    if PURITY_RE.search(he):
        strata.append("purity_terminology")
    if wc >= 20 and CONNECTOR_RE.search(en or ""):
        strata.append("narrative_or_contextual_explanation")
    if len(e["linkedGemaraLineIds"]) > 1:
        strata.append("multiple_linked_gemara_lines")
    if has_terminology_variance_signal(he, en, variance_registry_terms):
        strata.append("terminology_variance_signal")
    return strata


def blank_review_record(batch_id, entry_id, daf, hebrew, original_english):
    return {
        "batchId": batch_id,
        "entryId": entry_id,
        "daf": daf,
        "hebrew": hebrew,
        "originalEnglish": original_english,
        "proposedEnglish": None,
        "firstPassDisposition": None,
        "defectTags": [],
        "firstPassEvidence": None,
        "secondPass": {"required": None, "status": None, "evidence": None, "finalEnglish": None},
        "blindQA": {"selected": False, "result": None, "evidence": None},
        "finalDisposition": None,
        "structuralStop": None,
        "repairPR": None,
        "finalVerificationSHA": None,
    }


def build_packets(batch, entries_by_id, rashi_sorted_by_daf, lines_ordered_by_daf,
                   registry_terms, variance_registry_terms):
    packets = []
    for eid in batch["entryIds"]:
        e = entries_by_id.get(eid)
        if e is None:
            raise KeyError(f"batch {batch['batchId']} references unknown entry id {eid!r}")
        daf = e["daf"]
        strata = classify_strata(e, variance_registry_terms)
        packets.append({
            "id": e["id"],
            "batchId": batch["batchId"],
            "daf": daf,
            "perek": batch["perek"],
            "vilnaLine": e["vilnaLine"],
            "he": e["he"],
            "en": e["en"],
            "linkedGemaraLineIds": e["linkedGemaraLineIds"],
            "gemaraContext": gemara_context(lines_ordered_by_daf[daf], e["linkedGemaraLineIds"]),
            "neighboringRashi": rashi_neighbors(rashi_sorted_by_daf[daf], e["id"]),
            "riskScore": e["riskScore"],
            "riskSignals": e["riskSignals"],
            "priorReviewDepth": e["priorReviewDepth"],
            "applicableStyleGuideSections": style_sections_for(strata),
            "applicableTerminologyRegistryEntries": registry_matches(e["he"], registry_terms),
            "review": blank_review_record(batch["batchId"], e["id"], daf, e["he"], e["en"]),
        })
    return packets


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch-id", required=True)
    ap.add_argument("--batches", default=str(BATCHES_PATH))
    ap.add_argument("--out", required=True,
                     help="no default - this tool never silently writes into docs/reports/data/")
    args = ap.parse_args()

    inv = json.loads(INVENTORY_PATH.read_text())
    entries_by_id = {e["id"]: e for e in inv["entries"]}
    batches_doc = json.loads(Path(args.batches).read_text())
    batch = next((b for b in batches_doc["batches"] if b["batchId"] == args.batch_id), None)
    if batch is None:
        print(f"error: no batch {args.batch_id!r} in {args.batches}", file=sys.stderr)
        return 1

    daf_order, rashi_by_daf, lines_by_daf = load_corpus()
    registry_terms = load_registry()
    variance_registry_terms = load_registry_terms()
    rashi_sorted_by_daf = {
        daf: sorted(rashi_by_daf[daf], key=lambda r: r["vilnaLine"]) for daf in daf_order
    }
    lines_ordered_by_daf = {daf: ordered_lines(lines_by_daf[daf]) for daf in daf_order}

    try:
        packets = build_packets(batch, entries_by_id, rashi_sorted_by_daf, lines_ordered_by_daf,
                                 registry_terms, variance_registry_terms)
    except KeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    out = {
        "schemaVersion": 1,
        "batchId": args.batch_id,
        "generatedFromBatch": args.batches,
        "daf": batch["daf"],
        "perek": batch["perek"],
        "totalPackets": len(packets),
        "packets": packets,
    }
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {args.out} ({len(packets)} packets, batch {args.batch_id})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
