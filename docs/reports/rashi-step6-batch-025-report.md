# Rashi translation-quality campaign, Step 6 batch 025 report

Batch `step6-batch-025` of the full-corpus review defined in
`docs/reports/rashi-full-corpus-review-strategy.md` (Step 5). Selected as
the next batch per the strategy document's recommended order (position
15, high-risk (dense) priority group; prioritization only, not evidence
of defect). Full per-entry evidence lives in
`docs/reports/data/rashi-step6-batch-025-review-records.json` (validated
against the Step 5 contract).

## Batch scope (frozen from the committed batch plan, unmodified)

- **Batch id**: `step6-batch-025`
- **Perek**: 5
- **Daf**: 57a, 57b (2 daf)
- **Tier**: `dense`
- **Entries**: 112 (57a=55, 57b=57)
- **Historical-provenance counts** (Step 1): `known-needs-reconstruction`
  112 (100%)

This batch carries the highest concentration of `known-needs-
reconstruction`-flagged entries reviewed this session: 112 of 112
entries (100%, both daf), each carrying an `INVENTED_TEXT` Step 2 risk
signal citing the same "VERSION 15.293 Wave 1 audit" finding already
encountered in `step6-batch-003` (daf 6b), `step6-batch-023` (daf
53a/53b/54b), and `step6-batch-024` (daf 55a/55b/56b).

Re-generated and re-validated (`generate_rashi_batch_progress.py`,
`generate_rashi_translation_inventory.py --check`) at the start of this
batch against current main to confirm the batch manifest entry is
unmodified and still selects exactly these 112 entries, that all 112
were still UNREVIEWED, and that they were assigned only to
`step6-batch-025` (0 overlap with any other batch). A fresh review
packet (`generate_rashi_review_packets.py --batch-id step6-batch-025`)
was generated and used as the basis for review. No entry outside the
batch was edited.

## Method and key finding: the "needs-reconstruction" flags are stale for both affected daf

Following the `step6-batch-003`/`023`/`024` precedent, `git log
--oneline --all -- modules/yoma/assets/learning/yoma/<daf>.learning.json`
was checked for every daf in this batch **before** reading the flagged
entries at face value:

```
57a: 0d71fd0 Yoma 57a: full Rashi reconstruction (57 entries) (#298)
57b: 6a78036 Yoma 57b: full Rashi reconstruction (59 entries) (#299)
```

**Both daf in this batch were already fully reconstructed** in PRs #298
and #299 respectively, well before the VERSION 15.293 Wave 1 audit whose
finding the current Step 2 risk-signal generator and batch-planning
`known-needs-reconstruction` provenance bucket still cite. As with the
three prior stale-flag batches this session, the classification metadata
was never refreshed to reflect that the underlying content problem had
already been fixed.

All 112 entries were nonetheless read individually and independently
re-derived from their own Hebrew (never from the existing English
alone), cross-checked against neighboring entries' Hebrew, linked
Gemara/Mishnah context, the style guide, and the terminology registry.
Every one of the 112 flagged entries was individually confirmed to be a
faithful, specific, non-generic translation of its own Hebrew line - not
filler, not fabricated, and not shifted from a neighbor.

**First pass**: all 112 entries reviewed individually. Result: **112
VERIFIED, 0 MINOR_EDIT, 0 SUBSTANTIVE_REPAIR, 0 RETRANSLATE, 0
DUPLICATION_OR_CONTAMINATION, 0 BLOCKED.**

**Second pass**: not applicable (0 changed entries).

**Blind QA**: given this batch's 100% known-needs-reconstruction
concentration - the highest of any batch reviewed this session - a
full-coverage sample was used for all 112 entries (not a subsample),
each independently re-derived from the raw Hebrew a second time in a
separate pass, deliberately independent of the first-pass reasoning and
the PR #298/#299 history lookups. Result: **112/112
CONFIRMED_VERIFIED, 0 escalations.** No expansion of the sample was
required (already full coverage).

## Systemic-candidate review

### Family 1: fabricated "New comment:" scaffold text

**0 candidates in this batch.** A corpus-wide check confirms 0
occurrences, consistent with `step6-batch-006` (this session) fully
draining this family from the entire unreviewed corpus.

### Family 2: cross-entry word anticipation

2 candidates in this batch, both daf-boundary single-word stubs:
`rashi-yoma-057a-057` (Hebrew "כוסות", deferred to 57b) and
`rashi-yoma-057b-059` (Hebrew "וקבל", deferred to 58a). **Disposition:
FALSE_POSITIVE for both.** Same low-precision OVEREXPLAINED
length-ratio trigger already confirmed throughout this session. Left
unchanged, VERIFIED.

## Other risk-signaled entries (outside both systemic families)

- **TRUNCATED** (7 entries: `057a-016`, `057a-021`, `057a-040`,
  `057b-005`, `057b-017`, `057b-021`, `057b-031`): all confirmed
  **FALSE_POSITIVE** - each ends mid-clause on a function word because
  this corpus splits Rashi comments across Vilna-line entries, and the
  immediately following vilnaLine entry completes the clause in every
  case (verified individually).
- **PUNCTUATION** (2 entries: `057b-016`, `057b-017`, one overlapping
  with the TRUNCATED set): an open parenthetical citation ("(Zevachim"
  / "47a)") spans across the entry boundary exactly as the Hebrew's own
  parenthetical citation does. **FALSE_POSITIVE.**
- **WRONG_REFERENT** (2 entries: `057a-041`, `057b-036`): pronoun
  referents checked against established context from the immediately
  preceding entries (the inner-service subject at `057a-032/033`; the
  sin-offering subject at `057b-035`). Both resolve correctly.
  **FALSE_POSITIVE.**

All are VERIFIED.

## Aggregate results (112 entries)

| Disposition | Count | Rate |
|---|---|---|
| VERIFIED | 112 | 100.0% |
| MINOR_EDIT | 0 | 0.0% |
| SUBSTANTIVE_REPAIR | 0 | 0.0% |
| RETRANSLATE | 0 | 0.0% |
| DUPLICATION_OR_CONTAMINATION | 0 | 0.0% |
| BLOCKED | 0 | 0.0% |
| **Total** | **112** | **100%** |

**Changed-translation count: 0.** No PR content-diff applies to any
`modules/yoma/assets/learning/yoma/*.learning.json` file for this batch
- only review-records, inventory review-metadata, and documentation
change. No BLOCKED entries and no structural/source-cache blockers were
found anywhere in this batch.

## Regression and platform evidence

- Rashi entry count: 8,854 (unchanged) - Associations: 10,061 declared, 0
  broken, 0 cross-daf (unchanged) - Boundary registry: 20/20 (unchanged)
- Hebrew and English text: byte-unchanged across all 112 entries in this
  batch (0 changes to apply)
- `npm run validate:offline:yoma`, `npm test`, `npm run test:browser`,
  `npm run build`, `npm run check:deploy-html`, `python3
  scripts/worker_pipeline.py verify --full`: all green

## Status

**Batch 025: COMPLETE.** All 112 entries reviewed with an assigned final
disposition; 0 entries left in an ambiguous state; 0 BLOCKED. This is
the fifth consecutive batch this session (`002`, `003`, `023`, `024`,
`025`) whose principal finding is negative-but-well-evidenced and traced
to a concrete root cause: historical-defect flags (`CONTEXT_MISMATCH`
for batch 002, `INVENTED_TEXT`/`known-needs-reconstruction` for batches
003, 023, 024, and 025) all predate completed repair PRs and are stale,
not live defects. Blind QA (100%, full coverage): 112/112
CONFIRMED_VERIFIED, 0 escalations.
