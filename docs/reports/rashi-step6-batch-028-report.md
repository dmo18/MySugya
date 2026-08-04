# Rashi translation-quality campaign, Step 6 batch 028 report

Batch `step6-batch-028` of the full-corpus review defined in
`docs/reports/rashi-full-corpus-review-strategy.md` (Step 5). Selected as
the next batch per the strategy document's recommended order (position
18, high-risk (dense) priority group; prioritization only, not evidence
of defect). Full per-entry evidence lives in
`docs/reports/data/rashi-step6-batch-028-review-records.json` (validated
against the Step 5 contract).

## Batch scope (frozen from the committed batch plan, unmodified)

- **Batch id**: `step6-batch-028`
- **Perek**: 6
- **Daf**: 61b, 62a, 62b (3 daf)
- **Tier**: `dense`
- **Entries**: 171 (61b=65, 62a=42, 62b=64)
- **Historical-provenance counts** (Step 1): `known-needs-reconstruction`
  171 (100%)

This batch carries a 100% `known-needs-reconstruction` concentration:
all 171 entries carry an `INVENTED_TEXT` Step 2 risk signal citing the
same "VERSION 15.293 Wave 1 audit" finding already encountered in the
seven immediately preceding stale-flag batches this session.

61b's opening entries were read against the fresh context of daf 61a's
boundary-authorized comment (Rabbi Yaakov's metzora log-of-oil
distinction, ending at 61a's own final line per
`rashi_boundary_authorizations.json`) and 61a's own daf-boundary
anticipation stub ("אשם", from `step6-batch-027`). 61b opens with its
own valid Gemara lines (`yoma-061b-l01` onward) and a new sub-topic
(whether an incomplete inner service voids the metzora's obligation);
this is normal cross-daf narrative continuity, not a boundary/
authorization matter itself.

Re-generated and re-validated (`generate_rashi_batch_progress.py`,
`generate_rashi_translation_inventory.py --check`) at the start of this
batch against current main to confirm the batch manifest entry is
unmodified and still selects exactly these 171 entries, that all 171
were still UNREVIEWED, and that they were assigned only to
`step6-batch-028` (0 overlap with any other batch). A fresh review
packet (`generate_rashi_review_packets.py --batch-id step6-batch-028`)
was generated and used as the basis for review. No entry outside the
batch was edited.

## Method and key finding: the "needs-reconstruction" flags are stale for all three affected daf

Following the `step6-batch-003`/`023`/`024`/`025`/`026`/`027`
precedent, `git log --oneline --all -- modules/yoma/assets/learning/yoma/<daf>.learning.json`
was checked for every daf in this batch **before** reading the flagged
entries at face value:

```
61b: b6e16f1 Yoma 61b: full Rashi reconstruction (67 entries) (#306)
62a: 60e8fd7 Yoma 62a: full Rashi reconstruction (44 entries) (#307)
62b: c86e778 Yoma 62b: full Rashi reconstruction (66 entries) (#308)
```

**All three daf in this batch were already fully reconstructed** in
PRs #306, #307, and #308 respectively, well before the VERSION 15.293
Wave 1 audit whose finding the current Step 2 risk-signal generator and
batch-planning `known-needs-reconstruction` provenance bucket still
cite. As with the seven prior stale-flag batches this session, the
classification metadata was never refreshed to reflect that the
underlying content problem had already been fixed.

All 171 entries were nonetheless read individually and independently
re-derived from their own Hebrew (never from the existing English
alone), cross-checked against neighboring entries' Hebrew, linked
Gemara/Mishnah context, the style guide, and the terminology registry.
Every one of the 171 flagged entries was individually confirmed to be a
faithful, specific, non-generic translation of its own Hebrew line - not
filler, not fabricated, and not shifted from a neighbor.

**First pass**: all 171 entries reviewed individually. Result: **171
VERIFIED, 0 MINOR_EDIT, 0 SUBSTANTIVE_REPAIR, 0 RETRANSLATE, 0
DUPLICATION_OR_CONTAMINATION, 0 BLOCKED.**

**Second pass**: not applicable (0 changed entries).

**Blind QA**: given this batch's 100% known-needs-reconstruction
concentration, a full-coverage sample was used for all 171 entries (not
a subsample), each independently re-derived from the raw Hebrew a
second time in a separate pass, deliberately independent of the
first-pass reasoning and the PR #306/#307/#308 history lookups. Result:
**171/171 CONFIRMED_VERIFIED, 0 escalations.**

## Systemic-candidate review

### Family 1: fabricated "New comment:" scaffold text

**0 candidates in this batch.** A corpus-wide check confirms 0
occurrences, consistent with `step6-batch-006` (this session) fully
draining this family from the entire unreviewed corpus.

### Family 2: cross-entry word anticipation

3 candidates in this batch, all daf-boundary single-word/fragment
stubs: `rashi-yoma-061b-067` (Hebrew "וכי", deferred to 62a),
`rashi-yoma-062a-044` (Hebrew "גמ'", deferred to 62b), and
`rashi-yoma-062b-066` (Hebrew "ומי", deferred to 63a). **Disposition:
FALSE_POSITIVE for all 3.** Same low-precision OVEREXPLAINED
length-ratio trigger already confirmed throughout this session. Left
unchanged, VERIFIED.

## Other risk-signaled entries (outside both systemic families)

**TRUNCATED** (7 entries: `061b-003`, `062a-021`, `062a-036`,
`062b-031`, `062b-048`, `062b-051`, `062b-057`): all confirmed
**FALSE_POSITIVE** - each ends mid-clause on a function word because
this corpus splits Rashi comments across Vilna-line entries, and the
immediately following vilnaLine entry completes the clause in every
case (verified individually). All are VERIFIED.

## Aggregate results (171 entries)

| Disposition | Count | Rate |
|---|---|---|
| VERIFIED | 171 | 100.0% |
| MINOR_EDIT | 0 | 0.0% |
| SUBSTANTIVE_REPAIR | 0 | 0.0% |
| RETRANSLATE | 0 | 0.0% |
| DUPLICATION_OR_CONTAMINATION | 0 | 0.0% |
| BLOCKED | 0 | 0.0% |
| **Total** | **171** | **100%** |

**Changed-translation count: 0.** No PR content-diff applies to any
`modules/yoma/assets/learning/yoma/*.learning.json` file for this batch
- only review-records, inventory review-metadata, and documentation
change. No BLOCKED entries and no structural/source-cache blockers were
found anywhere in this batch.

## Regression and platform evidence

- Rashi entry count: 8,854 (unchanged) - Associations: 10,061 declared, 0
  broken, 0 cross-daf (unchanged) - Boundary registry: 20/20 (unchanged)
- Hebrew and English text: byte-unchanged across all 171 entries in this
  batch (0 changes to apply)
- `npm run validate:offline:yoma`, `npm test`, `npm run test:browser`,
  `npm run build`, `npm run check:deploy-html`, `python3
  scripts/worker_pipeline.py verify --full`: all green

## Status

**Batch 028: COMPLETE.** All 171 entries reviewed with an assigned final
disposition; 0 entries left in an ambiguous state; 0 BLOCKED. This is
the eighth consecutive batch this session (`002`, `003`, `023`, `024`,
`025`, `026`, `027`, `028`) whose principal finding is
negative-but-well-evidenced and traced to a concrete root cause:
historical-defect flags (`CONTEXT_MISMATCH` for batch 002,
`INVENTED_TEXT`/`known-needs-reconstruction` for batches 003, 023, 024,
025, 026, 027, and 028) all predate completed repair PRs and are stale,
not live defects. Blind QA (100%, full coverage): 171/171
CONFIRMED_VERIFIED, 0 escalations.
