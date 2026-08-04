# Rashi translation-quality campaign, Step 6 batch 023 report

Batch `step6-batch-023` of the full-corpus review defined in
`docs/reports/rashi-full-corpus-review-strategy.md` (Step 5). Selected as
the next batch per the strategy document's recommended order (position
13, high-risk (dense) priority group; prioritization only, not evidence
of defect). Full per-entry evidence lives in
`docs/reports/data/rashi-step6-batch-023-review-records.json` (validated
against the Step 5 contract).

## Batch scope (frozen from the committed batch plan, unmodified)

- **Batch id**: `step6-batch-023`
- **Perek**: 5
- **Daf**: 53a, 53b, 54a, 54b (4 daf)
- **Tier**: `dense`
- **Entries**: 180
- **Risk-tier counts** (Step 2 automated triage, advisory only): high 118, medium 7, zero-risk 55
- **Historical-provenance counts** (Step 1): `known-needs-reconstruction` 118 (65.6%), `narrow-fix-only` 62
- **Estimated changed count** (Step 5 projection): 23.3

This batch carries the highest concentration of `known-needs-
reconstruction`-flagged entries reviewed this session so far: 118 of 180
entries (across daf 53a, 53b, and 54b), each carrying an `INVENTED_TEXT`
Step 2 risk signal citing the same "VERSION 15.293 Wave 1 audit" finding
already encountered in `step6-batch-003` for daf 6b.

Re-generated and re-validated (`generate_rashi_batch_progress.py`,
`generate_rashi_translation_inventory.py --check`) at the start of this
batch against current main to confirm the batch manifest entry is
unmodified and still selects exactly these 180 entries, that all 180
were still UNREVIEWED, and that they were assigned only to
`step6-batch-023` (0 overlap with any other batch). A fresh review
packet (`generate_rashi_review_packets.py --batch-id step6-batch-023`)
was generated and used as the basis for review. No entry outside the
batch was edited.

## Method and key finding: the "needs-reconstruction" flags are stale for all three affected daf

Following the `step6-batch-003` precedent, `git log --oneline --all --
modules/yoma/assets/learning/yoma/<daf>.learning.json` was checked for
every daf in this batch **before** reading the flagged entries at face
value:

```
53a: abc4bda Yoma 53a: full Rashi reconstruction (60 entries) (#292)
53b: b8a9b94 Yoma 53b: full Rashi reconstruction (50 entries) (#293)
54a: 2cf3f1a Yoma 54a: full Rashi reconstruction (62 entries) (#324)
54b: cc2943e Yoma 54b: full Rashi reconstruction (14 entries) (#294)
```

**All four daf in this batch were already fully reconstructed** in PRs
#292, #293, #324, and #294 respectively, well before the VERSION 15.293
Wave 1 audit whose finding the current Step 2 risk-signal generator and
batch-planning `known-needs-reconstruction` provenance bucket still
cite. As with daf 6b in `step6-batch-003`, the classification metadata
was never refreshed to reflect that the underlying content problem had
already been fixed.

All 180 entries were nonetheless read individually and independently
re-derived from their own Hebrew (never from the existing English
alone), cross-checked against neighboring entries' Hebrew, linked
Gemara/Mishnah context, the style guide, and the terminology registry.
Every one of the 118 flagged entries was individually confirmed to be a
faithful, specific, non-generic translation of its own Hebrew line - not
filler, not fabricated, and not shifted from a neighbor.

**First pass**: all 180 entries reviewed individually. Result: **180
VERIFIED, 0 MINOR_EDIT, 0 SUBSTANTIVE_REPAIR, 0 RETRANSLATE, 0
DUPLICATION_OR_CONTAMINATION, 0 BLOCKED.**

**Second pass**: not applicable (0 changed entries).

**Blind QA**: given the scale of this batch's stale "confirmed
fabricated" flag (118 entries, the largest such bucket reviewed this
session), a full-coverage sample was used for all 118 flagged entries
(not a subsample) plus a denser-than-usual every-6th-entry sample across
the remaining 62 (10 of 62), for a combined sample of 128 of 180
provisionally VERIFIED entries (71.1%) covering all 4 daf. Each was
independently re-derived from the raw Hebrew a second time, deliberately
independent of the first-pass reasoning and the PR #292/#293/#324/#294
history lookups. Result: **128/128 CONFIRMED_VERIFIED, 0 escalations.**
No expansion of the sample was required.

## Systemic-candidate review

### Family 1: fabricated "New comment:" scaffold text

**0 candidates in this batch.** A corpus-wide check confirms 0
occurrences, consistent with `step6-batch-006` (this session) fully
draining this family from the entire unreviewed corpus.

### Family 2: cross-entry word anticipation

4 candidates in this batch, all daf-boundary single-word/marker stubs:
`rashi-yoma-053a-060`, `rashi-yoma-053b-050`, `rashi-yoma-054a-062`,
`rashi-yoma-054b-014`. **Disposition: FALSE_POSITIVE for all 4.** Same
low-precision OVEREXPLAINED length-ratio trigger already confirmed
throughout this session. Left unchanged, VERIFIED.

## Other risk-signaled entries (outside both systemic families)

6 additional entries (all on daf 54a: `rashi-yoma-054a-001`,
`-040`, `-045`, `-049`, `-056`, `-059`) carried a `TRUNCATED` signal.
All confirmed **FALSE_POSITIVE**: this corpus splits Rashi comments
across Vilna-line entries, so a line ending mid-clause is the normal,
correct shape of a continuing entry - confirmed in each case by reading
the immediately following vilnaLine entry, which completes the clause.
All are VERIFIED.

## Aggregate results (180 entries)

| Disposition | Count | Rate |
|---|---|---|
| VERIFIED | 180 | 100.0% |
| MINOR_EDIT | 0 | 0.0% |
| SUBSTANTIVE_REPAIR | 0 | 0.0% |
| RETRANSLATE | 0 | 0.0% |
| DUPLICATION_OR_CONTAMINATION | 0 | 0.0% |
| BLOCKED | 0 | 0.0% |
| **Total** | **180** | **100%** |

**Changed-translation count: 0.** No PR content-diff applies to any
`modules/yoma/assets/learning/yoma/*.learning.json` file for this batch
- only review-records, inventory review-metadata, and documentation
change. No BLOCKED entries and no structural/source-cache blockers were
found anywhere in this batch.

## Regression and platform evidence

- Rashi entry count: 8,854 (unchanged) - Associations: 10,061 declared, 0
  broken, 0 cross-daf (unchanged) - Boundary registry: 20/20 (unchanged)
- Hebrew and English text: byte-unchanged across all 180 entries in this
  batch (0 changes to apply)
- `npm run validate:offline:yoma`, `npm test`, `npm run test:browser`,
  `npm run build`, `npm run check:deploy-html`, `python3
  scripts/worker_pipeline.py verify --full`: all green

## Status

**Batch 023: COMPLETE.** All 180 entries reviewed with an assigned final
disposition; 0 entries left in an ambiguous state; 0 BLOCKED. This is
the third consecutive batch this session (`002`, `003`, `023`) whose
principal finding is negative-but-well-evidenced and traced to a
concrete root cause: three separate historical-defect flags
(`CONTEXT_MISMATCH` for batch 002, `INVENTED_TEXT`/`known-needs-
reconstruction` for batches 003 and 023) all predate completed repair
PRs and are stale, not live defects. Blind QA (71.1%, full coverage of
every flagged entry): 128/128 CONFIRMED_VERIFIED, 0 escalations.
