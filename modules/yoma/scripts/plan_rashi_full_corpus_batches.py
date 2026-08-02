#!/usr/bin/env python3
"""
plan_rashi_full_corpus_batches.py - Rashi translation-quality campaign,
Step 5: deterministic full-corpus review batch planner.

Assigns every one of the 8,654 UNREVIEWED Rashi entries (all entries minus
the 200-entry Step 4 pilot cohort, which is frozen and never reassigned)
to exactly one contiguous-daf review batch, for the future Step 6 batch
review PRs. This script only PLANS batches - it never assigns a
disposition, never edits a translation, and never marks anything VERIFIED.

Algorithm (fully deterministic, no randomness):

  1. Load the live corpus (daf order, Rashi entries) and the Step 1/2/4
     inventory (riskScore, priorReviewDepth, reviewStatus).
  2. Classify every daf into one of three density tiers using its
     nonzero-riskScore fraction, which the corpus shows is naturally
     bimodal with a clean gap at 0.3-0.5 (see docs/reports/
     rashi-full-corpus-review-strategy.md for the histogram):
       dense       nonzero fraction >= 0.5  (34 daf - exactly the Step 1
                   known-needs-reconstruction/-realignment buckets)
       low_defect  nonzero fraction <  0.1  (55 daf)
       normal      everything else          (84 daf)
     Each tier has its own preferred entry/daf caps (tighter for dense
     material, looser for low-defect material), per the campaign
     directive's adaptive-size guidance.
  3. Split the 173 daf into their 8 perek segments (from PERAKIM in
     learning_data.js). A batch never crosses a perek boundary - this is
     enforced structurally, not just checked afterward: the daf walk
     resets at every perek start.
  4. Walk each perek's daf in canonical order. Accumulate a batch's daf
     list and unreviewed entries; before adding a daf, check whether doing
     so would exceed the batch's current tier's caps (the batch's tier is
     the most restrictive tier of any daf already in it - adding one dense
     daf to an otherwise-normal batch makes the whole batch dense-capped)
     or the absolute hard limits (350 entries, 8 daf, from the campaign
     directive). If it would, close the current batch and start a new one
     with that daf. A perek's last batch closes at the perek boundary
     regardless of size - there is no minimum batch size.
  5. Any closed batch whose estimated changed-translation count (a rough
     projection from pilot-observed per-provenance rates, never a
     disposition) exceeds 40 is recursively halved by daf until it is at
     or under the guidance or down to a single daf.
  6. Every batch gets a stable id (`step6-batch-NNN`, sequential in daf
     order across the whole corpus) and a stable, deterministically
     ordered entry list (daf order, then vilnaLine).

Reads only: live learning_data.js (via audit_rashi_translation_risk's
load_corpus, already used by Step 2/4 tooling) and the Step 1 inventory.
Writes only docs/reports/data/rashi-full-corpus-review-batches.json.
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
OUT_PATH = DATA_DIR / "rashi-full-corpus-review-batches.json"

sys.path.insert(0, str(SCRIPTS))
from audit_rashi_translation_risk import load_corpus  # noqa: E402
from select_rashi_pilot_cohort import load_perek_ranges, perek_for_daf  # noqa: E402

# Tier caps: (preferred_min, preferred_max, max_daf). The hard ceilings
# (350 entries, 8 daf) always win if a tier's own cap would exceed them.
HARD_MAX_ENTRIES = 350
HARD_MAX_DAF = 8
TIER_CAPS = {
    "dense": {"max_entries": 180, "max_daf": 4},
    "normal": {"max_entries": 300, "max_daf": 6},
    "low_defect": {"max_entries": 350, "max_daf": 8},
}
TIER_RESTRICTIVENESS = {"dense": 0, "normal": 1, "low_defect": 2}  # lower = more restrictive

# Pilot-observed changed rate per historical-provenance bucket (Step 4
# reconciliation, docs/reports/rashi-pilot-step4-final-report.md), used
# only as a rough per-batch estimate for the >40-change split check, never
# as a disposition or a promise. Only buckets with a well-sampled pilot n
# (>=20) get their own rate; narrow-fix-only (pilot n=2) and checked-no-
# fix-needed (pilot n=9) are too small to extrapolate reliably and fall
# back to the overall pilot average (11%, 22/200) instead of their own
# noisy small-sample rate (e.g. narrow-fix-only's raw 1/2=50% would wildly
# overstate a 54-entry batch's expected changes).
OVERALL_PILOT_RATE = 0.11
PILOT_CHANGED_RATE = {
    "content-reviewed": 0.11,
    "known-needs-realignment": 0.04,
    "known-needs-reconstruction": 0.14,
}


def classify_daf_tier(nonzero_frac):
    if nonzero_frac >= 0.5:
        return "dense"
    if nonzero_frac < 0.1:
        return "low_defect"
    return "normal"


def combined_tier(tiers):
    """Most restrictive tier among a set (dense wins over normal wins over low_defect)."""
    return min(tiers, key=lambda t: TIER_RESTRICTIVENESS[t])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT_PATH))
    opts = ap.parse_args()

    daf_order, rashi_by_daf, _lines_by_daf = load_corpus()
    inv = json.loads(INVENTORY_PATH.read_text())
    inv_by_id = {e["id"]: e for e in inv["entries"]}
    perek_ranges = load_perek_ranges()

    # Per-daf stats: tier, unreviewed entry ids (ordered), risk/provenance counts.
    daf_stats = {}
    for daf in daf_order:
        entries = sorted(rashi_by_daf[daf], key=lambda r: r["vilnaLine"])
        scores = [inv_by_id[r["id"]]["riskScore"] for r in entries]
        nonzero_frac = sum(1 for s in scores if s > 0) / len(scores) if scores else 0.0
        unreviewed = [r["id"] for r in entries if inv_by_id[r["id"]]["reviewStatus"] == "UNREVIEWED"]
        daf_stats[daf] = {
            "tier": classify_daf_tier(nonzero_frac),
            "nonzeroFraction": round(nonzero_frac, 4),
            "unreviewedIds": unreviewed,
            "totalEntries": len(entries),
            "reviewedCount": len(entries) - len(unreviewed),
        }

    # Perek segments: list of (perek_n, [daf...]) in daf order.
    perek_of = {d: perek_for_daf(d, daf_order, perek_ranges) for d in daf_order}
    segments = []
    cur_perek, cur_daf_list = None, []
    for d in daf_order:
        p = perek_of[d]
        if p != cur_perek:
            if cur_daf_list:
                segments.append((cur_perek, cur_daf_list))
            cur_perek, cur_daf_list = p, [d]
        else:
            cur_daf_list.append(d)
    if cur_daf_list:
        segments.append((cur_perek, cur_daf_list))

    raw_batches = []  # (perek, daf_list, entry_ids) before final id assignment/splitting

    def estimate_changed(entry_ids):
        return sum(PILOT_CHANGED_RATE.get(inv_by_id[eid]["priorReviewDepth"], OVERALL_PILOT_RATE)
                   for eid in entry_ids)

    def split_if_needed(perek, daf_list, entry_ids):
        """Recursively halve a batch by daf (not mid-daf) until its
        estimated changed count is at or under the 40 guidance, or it is
        down to a single daf (which cannot be split further without
        breaking the daf/entry pairing)."""
        if estimate_changed(entry_ids) <= 40 or len(daf_list) <= 1:
            return [(perek, daf_list, entry_ids)]
        mid = len(daf_list) // 2
        left_daf, right_daf = daf_list[:mid], daf_list[mid:]
        left_ids = [eid for d in left_daf for eid in daf_stats[d]["unreviewedIds"]]
        right_ids = [eid for d in right_daf for eid in daf_stats[d]["unreviewedIds"]]
        return split_if_needed(perek, left_daf, left_ids) + split_if_needed(perek, right_daf, right_ids)

    def close_batch(perek, daf_list, entry_ids):
        if not entry_ids:
            return
        raw_batches.extend(split_if_needed(perek, daf_list, entry_ids))

    batches = []

    def finalize_batches():
        for perek, daf_list, entry_ids in raw_batches:
            tier = combined_tier({daf_stats[d]["tier"] for d in daf_list})
            risk_counts = {"high_risk": 0, "medium_risk": 0, "zero_risk": 0}
            prov_counts = {}
            for eid in entry_ids:
                score = inv_by_id[eid]["riskScore"]
                if score >= 9:
                    risk_counts["high_risk"] += 1
                elif score >= 2:
                    risk_counts["medium_risk"] += 1
                else:
                    risk_counts["zero_risk"] += 1
                prov = inv_by_id[eid]["priorReviewDepth"]
                prov_counts[prov] = prov_counts.get(prov, 0) + 1
            est_changed = round(estimate_changed(entry_ids), 1)
            batches.append({
                "batchId": f"step6-batch-{len(batches) + 1:03d}",
                "perek": perek,
                "daf": list(daf_list),
                "tier": tier,
                "entryIds": list(entry_ids),
                "entryCount": len(entry_ids),
                "riskTierCounts": risk_counts,
                "provenanceCounts": prov_counts,
                "estimatedChangedCount": est_changed,
                "needsSplitReview": est_changed > 40,
            })

    for perek, daf_list_for_perek in segments:
        batch_daf, batch_entries = [], []
        for d in daf_list_for_perek:
            unreviewed = daf_stats[d]["unreviewedIds"]
            if not unreviewed and not batch_daf:
                # An all-reviewed daf (fully covered by the pilot) with no
                # batch open yet: nothing to add, move on.
                continue
            candidate_daf = batch_daf + [d]
            candidate_tiers = {daf_stats[x]["tier"] for x in candidate_daf}
            tier = combined_tier(candidate_tiers) if candidate_tiers else "normal"
            caps = TIER_CAPS[tier]
            max_entries = min(caps["max_entries"], HARD_MAX_ENTRIES)
            max_daf = min(caps["max_daf"], HARD_MAX_DAF)
            projected_entries = len(batch_entries) + len(unreviewed)
            projected_daf = len(batch_daf) + (1 if d not in batch_daf else 0)
            if batch_daf and (projected_entries > max_entries or projected_daf > max_daf):
                close_batch(perek, batch_daf, batch_entries)
                batch_daf, batch_entries = [], []
            batch_daf.append(d)
            batch_entries.extend(unreviewed)
        close_batch(perek, batch_daf, batch_entries)

    finalize_batches()

    all_assigned = [eid for b in batches for eid in b["entryIds"]]
    remaining_unreviewed = [e["id"] for e in inv["entries"] if e["reviewStatus"] == "UNREVIEWED"]

    sizes = [b["entryCount"] for b in batches]
    out = {
        "schemaVersion": 1,
        "generatedFrom": "live learning_data.js + docs/reports/data/rashi-translation-quality-inventory.json",
        "totalRemainingUnreviewed": len(remaining_unreviewed),
        "totalAssigned": len(all_assigned),
        "totalBatches": len(batches),
        "batchSizeStats": {
            "min": min(sizes) if sizes else 0,
            "max": max(sizes) if sizes else 0,
            "median": sorted(sizes)[len(sizes) // 2] if sizes else 0,
            "average": round(sum(sizes) / len(sizes), 1) if sizes else 0,
        },
        "tierCaps": TIER_CAPS,
        "hardLimits": {"maxEntries": HARD_MAX_ENTRIES, "maxDaf": HARD_MAX_DAF},
        "batches": batches,
    }
    Path(opts.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {opts.out}: {len(batches)} batches, "
          f"{len(all_assigned)}/{len(remaining_unreviewed)} entries assigned, "
          f"sizes min={out['batchSizeStats']['min']} max={out['batchSizeStats']['max']} "
          f"median={out['batchSizeStats']['median']} avg={out['batchSizeStats']['average']}")
    splits_needed = [b["batchId"] for b in batches if b["needsSplitReview"]]
    if splits_needed:
        print(f"NOTE: {len(splits_needed)} batch(es) exceed the ~40-estimated-change guidance and are flagged needsSplitReview: {splits_needed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
