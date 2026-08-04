# Rashi translation-quality campaign, Step 6 batch 002 report

Batch `step6-batch-002` of the full-corpus review defined in
`docs/reports/rashi-full-corpus-review-strategy.md` (Step 5). Selected as
the next batch per the strategy document's recommended order (position
11, high-risk (dense) priority group; prioritization only, not evidence
of defect). Full per-entry evidence lives in
`docs/reports/data/rashi-step6-batch-002-review-records.json` (validated
against the Step 5 contract).

## Batch scope (frozen from the committed batch plan, unmodified)

- **Batch id**: `step6-batch-002`
- **Perek**: 1
- **Daf**: 5a, 5b, 6a (3 daf)
- **Tier**: `dense`
- **Entries**: 158
- **Risk-tier counts** (Step 2 automated triage, advisory only): high 6, medium 152, zero-risk 0
- **Historical-provenance counts** (Step 1): `known-needs-realignment` 158 (100%)
- **Estimated changed count** (Step 5 projection): 6.3

This is the first `dense`-tier, `known-needs-realignment`-provenance
batch reviewed this session (all prior batches were `normal`-tier,
`content-reviewed`-provenance, "systemic-candidate-dense"). The `dense`
tier and `known-needs-realignment` bucket correspond to a prior Wave 1
audit finding: on some daf, Rashi's `en` field was suspected of
systematically translating an *adjacent* Vilna line's Hebrew instead of
its own. Per `rashi-full-corpus-review-strategy.md`, this warrants
closer per-entry attention than a normal batch, even though the pilot
sample showed these buckets' actual defect rates were lower than their
historical flags suggested.

Re-generated and re-validated (`generate_rashi_batch_progress.py`,
`generate_rashi_translation_inventory.py --check`) at the start of this
batch against current main to confirm the batch manifest entry is
unmodified and still selects exactly these 158 entries, that all 158
were still UNREVIEWED, and that they were assigned only to
`step6-batch-002` (0 overlap with any other batch, including no overlap
with `rashi-yoma-009b-001`, the separately-tracked BLOCKED source-repair
entry). A fresh review packet
(`generate_rashi_review_packets.py --batch-id step6-batch-002`) was
generated and used as the basis for review. No entry outside the batch
was edited.

## Method

All 158 entries carry a nonzero Step 2 risk signal - **every single
entry in this batch was flagged `CONTEXT_MISMATCH`** ("English
substantially overlaps its linked Gemara line's own English - possibly a
copied Gemara translation rather than a Rashi comment"), the automated
signal most directly associated with the historical `known-needs-
realignment` concern. Given the batch-wide (not scattered) nature of
this signal and the historical-debt provenance, every entry was read and
independently re-derived from its own Hebrew, cross-checked specifically
against its immediate neighboring entries' Hebrew (to rule out the exact
`known-needs-realignment` failure mode: `en` shifted to an adjacent
line), its linked Gemara/Mishnah context, the style guide, and the
terminology registry - never from the existing English alone.

**Finding**: this daf range (5a-6a) covers the Gemara's extended
discussion of the seven days of investiture/anointing (extensively
quoting and re-quoting the same Exodus/Leviticus verses the Gemara
itself also quotes and translates) and the niddah/bo'el-niddah laws for
the Yom Kippur High Priest. Both topics involve heavy direct biblical
citation on both the Rashi and Gemara sides, producing exactly the kind
of high lexical overlap between a Rashi comment's English and its linked
Gemara line's English that the `CONTEXT_MISMATCH` heuristic is designed
to catch as a *possible* copy/shift signal - but is not one here. Every
entry, read individually against its own Hebrew and its neighbors',
faithfully translates its own line; no entry's English was found shifted
to an adjacent line's Hebrew, and no entry was found copied wholesale
from its linked Gemara line rather than genuinely translating Rashi's
own (overlapping-content) comment.

**First pass**: all 158 entries reviewed individually. Result: **158
VERIFIED, 0 MINOR_EDIT, 0 SUBSTANTIVE_REPAIR, 0 RETRANSLATE, 0
DUPLICATION_OR_CONTAMINATION, 0 BLOCKED.**

**Second pass**: not applicable (0 changed entries).

**Blind QA**: given this batch's elevated dense/high-risk/known-needs-
realignment profile and the fact that first pass found zero changed
entries corpus-wide despite universal risk-flagging, a denser-than-usual
deterministic sample was used to independently confirm the finding:
every 6th provisionally-VERIFIED entry in canonical batch order (26 of
158, 16.5%, well above this campaign's usual ~10-15% rate), covering all
3 daf. Result: **26/26 CONFIRMED_VERIFIED, 0 escalations.** No expansion
of the sample was required.

## Systemic-candidate review

### Family 1: fabricated "New comment:" scaffold text

**0 candidates in this batch.** A corpus-wide check
(`docs/reports/data/rashi-systemic-candidates.json`'s `new_comment_
scaffold` family, and a direct regex scan of this batch's packet)
confirms 0 occurrences, consistent with `step6-batch-006`'s completion
(the prior batch this session) fully draining this family from the
entire unreviewed corpus.

### Family 2: cross-entry word anticipation

3 candidates in this batch, all daf-boundary single-word/marker stubs
(`rashi-yoma-005a-040`, `rashi-yoma-005b-068`, `rashi-yoma-006a-063`).
**Disposition: FALSE_POSITIVE for all 3.** Same low-precision
OVEREXPLAINED length-ratio trigger already confirmed throughout this
session; the elevated risk score on these three (12, vs. the batch-wide
baseline of 8 from `CONTEXT_MISMATCH` alone) reflects their detailed
explanatory continuation notes, not a genuine defect. Left unchanged,
VERIFIED.

## Other risk-signaled entries (outside both systemic families)

3 additional entries (`rashi-yoma-005b-033`, `rashi-yoma-006a-020`,
`rashi-yoma-006a-050`) also carried a `TRUNCATED` signal on top of the
batch-wide `CONTEXT_MISMATCH`. All confirmed **FALSE_POSITIVE**: this
corpus splits Rashi comments across Vilna-line entries, so a line ending
mid-clause is the normal, correct shape of a continuing entry - confirmed
in each case by reading the immediately following vilnaLine entry, which
completes the clause. All are VERIFIED.

## Aggregate results (158 entries)

| Disposition | Count | Rate |
|---|---|---|
| VERIFIED | 158 | 100.0% |
| MINOR_EDIT | 0 | 0.0% |
| SUBSTANTIVE_REPAIR | 0 | 0.0% |
| RETRANSLATE | 0 | 0.0% |
| DUPLICATION_OR_CONTAMINATION | 0 | 0.0% |
| BLOCKED | 0 | 0.0% |
| **Total** | **158** | **100%** |

**Changed-translation count: 0.** No PR content-diff applies to any
`modules/yoma/assets/learning/yoma/*.learning.json` file for this batch
- only review-records, inventory review-metadata, and documentation
change. No BLOCKED entries and no structural/source-cache blockers were
found anywhere in this batch.

## Regression and platform evidence

- Rashi entry count: 8,854 (unchanged) - Associations: 10,061 declared, 0
  broken, 0 cross-daf (unchanged) - Boundary registry: 20/20 (unchanged)
- Hebrew and English text: byte-unchanged across all 158 entries in this
  batch (0 changes to apply)
- `npm run validate:offline:yoma`, `npm test`, `npm run test:browser`,
  `npm run build`, `npm run check:deploy-html`, `python3
  scripts/worker_pipeline.py verify --full`: all green

## Status

**Batch 002: COMPLETE.** All 158 entries reviewed with an assigned final
disposition; 0 entries left in an ambiguous state; 0 BLOCKED. This
batch's principal finding is negative-but-well-evidenced: the historical
`known-needs-realignment` concern for daf 5a-6a did not materialize on
individual review - every entry faithfully translates its own Hebrew
line, and the batch-wide `CONTEXT_MISMATCH` signal is explained by this
sugya's genuinely high rate of shared biblical-verse quotation between
Rashi and the Gemara, not by any shift or copy defect. Blind QA (16.5%,
denser than the campaign's usual rate given this batch's risk profile):
26/26 CONFIRMED_VERIFIED, 0 escalations.
