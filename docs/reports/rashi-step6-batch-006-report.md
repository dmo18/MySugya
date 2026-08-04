# Rashi translation-quality campaign, Step 6 batch 006 report

Batch `step6-batch-006` of the full-corpus review defined in
`docs/reports/rashi-full-corpus-review-strategy.md` (Step 5). Selected as
the next batch per the strategy document's recommended order (position
10, systemic-candidate-dense priority group; prioritization only, not
evidence of defect). Full per-entry evidence lives in
`docs/reports/data/rashi-step6-batch-006-review-records.json` (validated
against the Step 5 contract).

## Batch scope (frozen from the committed batch plan, unmodified)

- **Batch id**: `step6-batch-006`
- **Perek**: 1
- **Daf**: 14b, 15a, 15b, 16a (4 daf)
- **Tier**: `normal`
- **Entries**: 244
- **Risk-tier counts** (Step 2 automated triage, advisory only): high 0, medium 20, zero-risk 224
- **Historical-provenance counts** (Step 1): `content-reviewed` 244
- **Estimated changed count** (Step 5 projection): 26.8

Re-generated and re-validated (`generate_rashi_batch_progress.py`,
`generate_rashi_translation_inventory.py --check`) at the start of this
batch against current main to confirm the batch manifest entry is
unmodified and still selects exactly these 244 entries, that all 244 were
still UNREVIEWED, and that they were assigned only to `step6-batch-006`
(0 overlap with any other batch). A fresh review packet
(`generate_rashi_review_packets.py --batch-id step6-batch-006`) was
generated and used as the basis for review. No entry outside the batch
was edited.

## Single PR (under the change-count cap)

The confirmed changed count (12) is well under the 40-changes-per-PR
limit, so this batch is applied as a single PR covering only the one daf
that actually carries changes (14b) - the fourth consecutive Step 6
batch this session (after `step6-batch-022`, `step6-batch-004`, and
`step6-batch-021`) not to require a multi-child split.

## Method

Every entry was reviewed against its own Hebrew, its linked Gemara/Mishnah
context, neighboring Rashi entries (required wherever a Vilna line ends
mid-clause or mid-comment), the style guide, and the terminology registry -
never from the existing English alone. Risk scores and systemic-candidate
membership were treated as advisory only.

**First pass**: all 244 entries reviewed individually. Result: 232
VERIFIED, 12 MINOR_EDIT, 0 SUBSTANTIVE_REPAIR, 0 RETRANSLATE, 0
DUPLICATION_OR_CONTAMINATION, 0 BLOCKED.

**Second pass**: 100% of the 12 MINOR_EDIT entries independently
re-reviewed (re-derived from Hebrew and context again). Result: **12/12
CONFIRMED**, 0 MODIFIED, 0 REJECTED, 0 REMAINED_BLOCKED.

**Blind QA**: a deterministic 12.5% sample (29 of the 232 provisionally
VERIFIED entries, selected two ways fixed before any evidence text was
read: every 9th entry in canonical batch order, plus the first
risk-signaled VERIFIED entry per daf not already captured by that rule -
covering all 4 daf and both risk-signaled and zero-risk entries). Result:
**29/29 CONFIRMED_VERIFIED, 0 escalations.** No expansion of the sample
was required.

## Systemic-candidate review

### Family 1: fabricated "New comment:" scaffold text

12 of this batch's 244 entries (4.9%) carry the base "New comment:"
defect, the same dominant pattern already confirmed in batches 040, 041,
039, 005, 038, 037, 022, 004, and 021. All 12 occur on 14b; none occur on
15a, 15b, or 16a. This batch's rate is notably lower than most prior
batches (4.9% vs. the 10-28% range seen elsewhere this session).

**Wording-variant handling**: a full corpus-wide scan for all previously
discovered fabricated-label synonyms ("New comment on the Gemara/Mishnah:",
"Continuing:", "Textual note:", the combined "New comment, textual
note:", the capitalization-variant case, "New difficulty:", "Rashi's
textual note:", "Proof-text:") found none in this batch. A broader scan
for other capitalized-word-colon patterns also found nothing beyond the
base family.

**Disposition for all 12: CONFIRMED_DEFECT.** Fix: remove the fabricated
label and let the next quoted lemma begin directly, per the corpus's own
established convention - verified individually for every occurrence that
the remaining text, once joined, is grammatically coherent and
semantically unchanged. MINOR_EDIT, defect tag `INVENTED_TEXT`.

No new systemic family was created for this PR.

### Family 2: cross-entry word anticipation

4 candidates in this batch, all daf-boundary single-word/marker stubs
(`rashi-yoma-014b-059`, `rashi-yoma-015a-066`, `rashi-yoma-015b-066`,
`rashi-yoma-016a-061`). **Disposition: FALSE_POSITIVE for all 4.** Same
low-precision OVEREXPLAINED length-ratio trigger already confirmed in
batches 040, 041, 039, 005, 038, 037, 022, 004, and 021. Left unchanged,
VERIFIED.

## Other risk-signaled entries (outside both systemic families)

15 additional medium-risk entries (1 of which overlaps with the scaffold
family above and is resolved by that fix) were flagged by Step 2's
automated triage (`TRUNCATED`, `WRONG_REFERENT`) but fall outside both
authorized systemic-candidate families. All confirmed **FALSE_POSITIVE**
for their respective signals: this corpus splits Rashi comments across
Vilna-line entries, so a line ending mid-clause is the normal, correct
shape of a continuing entry - confirmed in every case by reading the
immediately following vilnaLine entry, which completes the clause. All
are VERIFIED.

## Aggregate results (244 entries)

| Disposition | Count | Rate |
|---|---|---|
| VERIFIED | 232 | 95.1% |
| MINOR_EDIT | 12 | 4.9% |
| SUBSTANTIVE_REPAIR | 0 | 0.0% |
| RETRANSLATE | 0 | 0.0% |
| DUPLICATION_OR_CONTAMINATION | 0 | 0.0% |
| BLOCKED | 0 | 0.0% |
| **Total** | **244** | **100%** |

**Changed-translation count: 12** (English to be applied in this single
PR). Second-pass results: 12/12 CONFIRMED. Defect-tag totals:
`INVENTED_TEXT` 12 (all from the base "New comment:" scaffold family;
no synonym variants occurred in this batch).

No BLOCKED entries and no structural/source-cache blockers were found
anywhere in this batch.

## Regression and platform evidence

- Rashi entry count: 8,854 (unchanged) - Associations: 10,061 declared, 0
  broken, 0 cross-daf (unchanged) - Boundary registry: 20/20 (unchanged)
- Hebrew text: byte-unchanged across all 244 entries in this batch
- `npm run validate:offline:yoma`, `npm test`, `npm run test:browser`,
  `npm run build`, `npm run check:deploy-html`, `python3
  scripts/worker_pipeline.py verify --full`: all green

## Status

**Batch 006: COMPLETE.** All 244 entries reviewed with an assigned final
disposition, applied in a single PR; 0 entries left in an ambiguous
state; 0 BLOCKED. Final disposition totals: 232 VERIFIED, 12 MINOR_EDIT,
0 SUBSTANTIVE_REPAIR, 0 RETRANSLATE, 0 DUPLICATION_OR_CONTAMINATION, 0
BLOCKED. Changed-translation count: 12 (all `INVENTED_TEXT`). Second
pass: 12/12 CONFIRMED. Blind QA: 29/29 CONFIRMED_VERIFIED, 0
escalations. Both authorized systemic-candidate families resolved
(scaffold: 12 CONFIRMED_DEFECT, applied; anticipation: 4 FALSE_POSITIVE,
unchanged).

This is the 11th parent batch completed this session (001, 040, 041,
039, 005, 038, 037, 022, 004, 021, 006).
