# Rashi translation-quality campaign, Step 6 batch 004 report

Batch `step6-batch-004` of the full-corpus review defined in
`docs/reports/rashi-full-corpus-review-strategy.md` (Step 5). Selected as
the next batch per the strategy document's recommended order (position 8,
systemic-candidate-dense priority group; prioritization only, not evidence
of defect). Full per-entry evidence lives in
`docs/reports/data/rashi-step6-batch-004-review-records.json` (validated
against the Step 5 contract).

## Batch scope (frozen from the committed batch plan, unmodified)

- **Batch id**: `step6-batch-004`
- **Perek**: 1
- **Daf**: 8b, 9a, 9b, 10a, 10b, 11a (6 daf)
- **Tier**: `normal`
- **Entries**: 196
- **Risk-tier counts** (Step 2 automated triage, advisory only): high 0, medium 20, zero-risk 176
- **Historical-provenance counts** (Step 1): `checked-no-fix-needed` 87, `content-reviewed` 109
- **Estimated changed count** (Step 5 projection): 21.6

Re-generated and re-validated (`generate_rashi_batch_progress.py`,
`generate_rashi_translation_inventory.py --check`) at the start of this
batch against current main to confirm the batch manifest entry is
unmodified and still selects exactly these 196 entries, that all 196 were
still UNREVIEWED, and that they were assigned only to `step6-batch-004`
(0 overlap with any other batch). A fresh review packet
(`generate_rashi_review_packets.py --batch-id step6-batch-004`) was
generated and used as the basis for review. No entry outside the batch
was edited.

## Single PR (under the change-count cap)

The confirmed changed count (32) is under the 40-changes-per-PR limit, so
this batch is applied as a single PR covering all six daf, the second
consecutive Step 6 batch this session (after `step6-batch-022`) not to
require a multi-child split.

## Method

Every entry was reviewed against its own Hebrew, its linked Gemara/Mishnah
context, neighboring Rashi entries (required wherever a Vilna line ends
mid-clause or mid-comment), the style guide, and the terminology registry -
never from the existing English alone. Risk scores and systemic-candidate
membership were treated as advisory only.

**First pass**: all 196 entries reviewed individually. Result: 164
VERIFIED, 32 MINOR_EDIT, 0 SUBSTANTIVE_REPAIR, 0 RETRANSLATE, 0
DUPLICATION_OR_CONTAMINATION, 0 BLOCKED.

**Second pass**: 100% of the 32 MINOR_EDIT entries independently
re-reviewed (re-derived from Hebrew and context again). Result: **32/32
CONFIRMED**, 0 MODIFIED, 0 REJECTED, 0 REMAINED_BLOCKED.

**Blind QA**: a deterministic 14.0% sample (23 of the 164 provisionally
VERIFIED entries, selected two ways fixed before any evidence text was
read: every 9th entry in canonical batch order, plus the first
risk-signaled VERIFIED entry per daf not already captured by that rule -
covering all 6 daf and both risk-signaled and zero-risk entries). Result:
**23/23 CONFIRMED_VERIFIED, 0 escalations.** No expansion of the sample
was required.

## Systemic-candidate review

### Family 1: fabricated "New comment:" scaffold text, plus one newly observed capitalization case

32 of this batch's 196 entries (16.3%) carry the base "New comment:"
defect, the same dominant pattern already confirmed in batches 040, 041,
039, 005, 038, 037, and 022. None occur on daf 8b, 9a, or 9b in this
batch; all 32 are on 10a, 10b, and 11a.

**Wording-variant handling**: this batch contains no
`"New comment on the Mishnah/Gemara:"`, `"Continuing:"`, `"Textual
note:"`, or combined-label instances. It does contain one entry needing
a variant of the standard fix, found by checking every occurrence's
immediate continuation before deciding on a mechanical strip:

- **`rashi-yoma-010a-014`** - Hebrew `"דבר אחר לא גרסינן:"` ('the words
  "another interpretation" are not the correct reading'). Unlike every
  other occurrence in this batch, where `"New comment:"` is immediately
  followed by a quoted Hebrew lemma in single quotes (kept lowercase per
  the corpus's established quote-dash convention, e.g. `rashi-yoma-
  010a-008`'s `'and there were Achiman, etc.'`), here the label is
  followed directly by an unquoted descriptive sentence: `"the words
  'another interpretation' are not in the correct text."` Removing the
  label without capitalizing would leave a sentence starting mid-lowercase
  directly after a period. Per the established convention for
  descriptive/editorial notes (the same treatment given to the `"Textual
  note:"` synonym in step6-batch-037 and the combined `"New comment,
  textual note:"` variant in step6-batch-022), the first letter is
  capitalized after removal: `"The words 'another interpretation' are not
  in the correct text."`

This is not common enough corpus-wide to warrant a new named systemic
family; it is recorded here as an advisory note and folded into the
existing scaffold-removal disposition.

**Disposition for all 32: CONFIRMED_DEFECT.** Fix: remove the fabricated
label (capitalizing the following word only where it introduces an
unquoted descriptive sentence, per the note above) and let the next
quoted lemma or sentence begin directly, per the corpus's own established
convention - verified individually for every occurrence that the
remaining text, once joined, is grammatically coherent and semantically
unchanged. MINOR_EDIT, defect tag `INVENTED_TEXT`.

No new systemic family was created for this PR.

### Family 2: cross-entry word anticipation

5 candidates in this batch, all daf-boundary single-word/marker stubs
(`rashi-yoma-008b-050`, `rashi-yoma-009b-041`, `rashi-yoma-010a-035`,
`rashi-yoma-010b-021`, `rashi-yoma-011a-043`). **Disposition:
FALSE_POSITIVE for all 5.** Same low-precision OVEREXPLAINED length-ratio
trigger already confirmed in batches 040, 041, 039, 005, 038, 037, and
022. Left unchanged, VERIFIED.

## Other risk-signaled entries (outside both systemic families)

12 additional medium-risk entries were flagged by Step 2's automated
triage (`TRUNCATED`, `WRONG_REFERENT`) but fall outside both authorized
systemic-candidate families. All confirmed **FALSE_POSITIVE** for their
respective signals: this corpus splits Rashi comments across Vilna-line
entries, so a line ending mid-clause is the normal, correct shape of a
continuing entry - confirmed in every case by reading the immediately
following vilnaLine entry, which completes the clause. All are VERIFIED.

## Aggregate results (196 entries)

| Disposition | Count | Rate |
|---|---|---|
| VERIFIED | 164 | 83.7% |
| MINOR_EDIT | 32 | 16.3% |
| SUBSTANTIVE_REPAIR | 0 | 0.0% |
| RETRANSLATE | 0 | 0.0% |
| DUPLICATION_OR_CONTAMINATION | 0 | 0.0% |
| BLOCKED | 0 | 0.0% |
| **Total** | **196** | **100%** |

**Changed-translation count: 32** (English to be applied in this single
PR). Second-pass results: 32/32 CONFIRMED. Defect-tag totals:
`INVENTED_TEXT` 32 (31 from the base "New comment:" scaffold family, plus
the one entry needing the capitalization variant of the same fix).

No BLOCKED entries and no structural/source-cache blockers were found
anywhere in this batch.

## Regression and platform evidence

- Rashi entry count: 8,854 (unchanged) - Associations: 10,061 declared, 0
  broken, 0 cross-daf (unchanged) - Boundary registry: 20/20 (unchanged)
- Hebrew text: byte-unchanged across all 196 entries in this batch
- `npm run validate:offline:yoma`, `npm test`, `npm run test:browser`,
  `npm run build`, `npm run check:deploy-html`, `python3
  scripts/worker_pipeline.py verify --full`: all green

## Status

**Batch 004: COMPLETE.** All 196 entries reviewed with an assigned final
disposition, applied in a single PR; 0 entries left in an ambiguous
state; 0 BLOCKED. Final disposition totals: 164 VERIFIED, 32 MINOR_EDIT,
0 SUBSTANTIVE_REPAIR, 0 RETRANSLATE, 0 DUPLICATION_OR_CONTAMINATION, 0
BLOCKED. Changed-translation count: 32 (all `INVENTED_TEXT`). Second
pass: 32/32 CONFIRMED. Blind QA: 23/23 CONFIRMED_VERIFIED, 0
escalations. Both authorized systemic-candidate families resolved
(scaffold: 32 CONFIRMED_DEFECT, applied; anticipation: 5 FALSE_POSITIVE,
unchanged).
