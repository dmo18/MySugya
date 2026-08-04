# Rashi translation-quality campaign, Step 6 batch 022 report

Batch `step6-batch-022` of the full-corpus review defined in
`docs/reports/rashi-full-corpus-review-strategy.md` (Step 5). Selected as
the next batch per the strategy document's recommended order (position 6,
systemic-candidate-dense priority group; prioritization only, not evidence
of defect). Full per-entry evidence lives in
`docs/reports/data/rashi-step6-batch-022-review-records.json` (validated
against the Step 5 contract).

## Batch scope (frozen from the committed batch plan, unmodified)

- **Batch id**: `step6-batch-022`
- **Perek**: 5
- **Daf**: 51a, 51b, 52a, 52b (4 daf)
- **Tier**: `normal`
- **Entries**: 186
- **Risk-tier counts** (Step 2 automated triage, advisory only): high 0, medium 20, zero-risk 166
- **Historical-provenance counts** (Step 1): `content-reviewed` 186
- **Estimated changed count** (Step 5 projection): 20.5

Re-generated and re-validated (`generate_rashi_batch_progress.py`,
`generate_rashi_translation_inventory.py --check`) at the start of this
batch against current main to confirm the batch manifest entry is
unmodified and still selects exactly these 186 entries, that all 186 were
still UNREVIEWED, and that they were assigned only to `step6-batch-022`
(0 overlap with any other batch). A fresh review packet
(`generate_rashi_review_packets.py --batch-id step6-batch-022`) was
generated and used as the basis for review. No entry outside the batch
was edited.

## Single PR (under the change-count cap)

The confirmed changed count (37) is under the 40-changes-per-PR limit, so
this batch is applied as a single PR covering all four daf, unlike the
prior five Step 6 batches this session (each of which required a
multi-child split).

## Method

Every entry was reviewed against its own Hebrew, its linked Gemara/Mishnah
context, neighboring Rashi entries (required wherever a Vilna line ends
mid-clause or mid-comment), the style guide, and the terminology registry -
never from the existing English alone. Risk scores and systemic-candidate
membership were treated as advisory only.

**First pass**: all 186 entries reviewed individually. Result: 149
VERIFIED, 37 MINOR_EDIT, 0 SUBSTANTIVE_REPAIR, 0 RETRANSLATE, 0
DUPLICATION_OR_CONTAMINATION, 0 BLOCKED.

**Second pass**: 100% of the 37 MINOR_EDIT entries independently
re-reviewed (re-derived from Hebrew and context again). Result: **37/37
CONFIRMED**, 0 MODIFIED, 0 REJECTED, 0 REMAINED_BLOCKED.

**Blind QA**: a deterministic 13.4% sample (20 of the 149 provisionally
VERIFIED entries, selected two ways fixed before any evidence text was
read: every 9th entry in canonical batch order, plus the first
risk-signaled VERIFIED entry per daf not already captured by that rule -
covering all 4 daf and both risk-signaled and zero-risk entries). Result:
**20/20 CONFIRMED_VERIFIED, 0 escalations.** No expansion of the sample
was required.

## Systemic-candidate review

### Family 1: fabricated "New comment:" scaffold text, plus one newly observed combined synonym variant

36 of this batch's 186 entries (19.4%) carry the base "New comment:"
defect, the same dominant pattern already confirmed in batches 040, 041,
039, 005, 038, and 037.

**Wording-variant handling (per the corrected rule established while
reviewing batch 005, itself correcting a mistake made in batch 039)**:
this batch contains no `"New comment on the Mishnah/Gemara:"` instances,
but does contain one previously-unseen variant found by a corpus-wide
check before deciding on a fix:

- **`"New comment, textual note:"`** - one occurrence,
  `rashi-yoma-051b-005`, stacking both already-established fabricated
  labels together in a single combined prefix, immediately before a
  quoted fragment. The Hebrew ends with the word `גרסינן` ('this is our
  reading') positioned at the end of the line, which the English already
  correctly renders via its existing trailing `"- this is the correct
  reading:"` clause (left unchanged, since it matches `גרסינן`'s position
  in the Hebrew and the established convention seen elsewhere, e.g. 37a
  L66, 42a L3, 57b L35, 74b L34, 80a L60/62, and the `"Textual note:"`
  synonym fixed in step6-batch-037 at 77b-002 and 78a-003). Neither
  "New comment" nor "textual note" has any Hebrew basis; the fabricated
  prefix was removed entirely, letting the quoted fragment begin
  directly. This entry is additional to the 36 above (37 total
  MINOR_EDIT in this family).

Neither this combined variant nor any other new wording is common enough
corpus-wide to warrant a new named systemic family (per the directive's
instruction not to create new families); it is recorded here as an
advisory note and folded into the existing scaffold-removal disposition.

**Disposition for all 37: CONFIRMED_DEFECT.** Fix: remove the fabricated
label(s) (preserving any genuine `"Gemara:"`/`"Mishnah:"` structural
marker where present - none occurred in this batch) and let the next
quoted fragment or clause begin directly, per the corpus's own
established convention - verified individually for every occurrence that
the remaining text, once joined, is grammatically coherent and
semantically unchanged. MINOR_EDIT, defect tag `INVENTED_TEXT`.

No new systemic family was created for this PR.

### Family 2: cross-entry word anticipation

4 candidates in this batch, all daf-boundary single-word/marker stubs
(`rashi-yoma-051a-026`, `rashi-yoma-051b-060`, `rashi-yoma-052a-037`,
`rashi-yoma-052b-063`). **Disposition: FALSE_POSITIVE for all 4.** Same
low-precision OVEREXPLAINED length-ratio trigger already confirmed in
batches 040, 041, 039, 005, 038, and 037. Left unchanged, VERIFIED.

## Other risk-signaled entries (outside both systemic families)

13 additional medium-risk entries were flagged by Step 2's automated
triage (`TRUNCATED`, `PUNCTUATION`, `WRONG_REFERENT`) but fall outside
both authorized systemic-candidate families. All confirmed
**FALSE_POSITIVE** for their respective signals: this corpus splits Rashi
comments across Vilna-line entries, so a line ending mid-clause (or with
an unmatched bracket that closes on the next line) is the normal, correct
shape of a continuing entry - confirmed in every case by reading the
immediately following vilnaLine entry, which completes the clause. All
are VERIFIED.

## Aggregate results (186 entries)

| Disposition | Count | Rate |
|---|---|---|
| VERIFIED | 149 | 80.1% |
| MINOR_EDIT | 37 | 19.9% |
| SUBSTANTIVE_REPAIR | 0 | 0.0% |
| RETRANSLATE | 0 | 0.0% |
| DUPLICATION_OR_CONTAMINATION | 0 | 0.0% |
| BLOCKED | 0 | 0.0% |
| **Total** | **186** | **100%** |

**Changed-translation count: 37** (English to be applied in this single
PR). Second-pass results: 37/37 CONFIRMED. Defect-tag totals:
`INVENTED_TEXT` 37 (36 from the base "New comment:" scaffold family, plus
the one newly observed "New comment, textual note:" combined synonym
instance).

No BLOCKED entries and no structural/source-cache blockers were found
anywhere in this batch.

## Regression and platform evidence

- Rashi entry count: 8,854 (unchanged) - Associations: 10,061 declared, 0
  broken, 0 cross-daf (unchanged) - Boundary registry: 20/20 (unchanged)
- Hebrew text: byte-unchanged across all 186 entries in this batch
- `npm run validate:offline:yoma`, `npm test`, `npm run test:browser`,
  `npm run build`, `npm run check:deploy-html`, `python3
  scripts/worker_pipeline.py verify --full`: all green

## Status

**Batch 022: COMPLETE.** All 186 entries reviewed with an assigned final
disposition, applied in a single PR; 0 entries left in an ambiguous
state; 0 BLOCKED. Final disposition totals: 149 VERIFIED, 37 MINOR_EDIT,
0 SUBSTANTIVE_REPAIR, 0 RETRANSLATE, 0 DUPLICATION_OR_CONTAMINATION, 0
BLOCKED. Changed-translation count: 37 (all `INVENTED_TEXT`). Second
pass: 37/37 CONFIRMED. Blind QA: 20/20 CONFIRMED_VERIFIED, 0
escalations. Both authorized systemic-candidate families resolved
(scaffold: 37 CONFIRMED_DEFECT, applied; anticipation: 4 FALSE_POSITIVE,
unchanged).
