# Rashi translation-quality campaign, Step 6 batch 005 report

Batch `step6-batch-005` of the full-corpus review defined in
`docs/reports/rashi-full-corpus-review-strategy.md` (Step 5). Selected as
the next batch per the strategy document's recommended order (position 3,
systemic-candidate-dense priority group; prioritization only, not evidence
of defect). Full per-entry evidence lives in
`docs/reports/data/rashi-step6-batch-005-review-records.json` (validated
against the Step 5 contract).

## Batch scope (frozen from the committed batch plan, unmodified)

- **Batch id**: `step6-batch-005`
- **Perek**: 1
- **Daf**: 11b, 12a, 12b, 13a, 13b, 14a (6 daf)
- **Tier**: `normal`
- **Entries**: 270
- **Risk-tier counts** (Step 2 automated triage, advisory only): high 0, medium 31, zero-risk 239
- **Historical-provenance counts** (Step 1): `content-reviewed` 270
- **Estimated changed count** (Step 5 projection): 29.7

Re-generated and re-validated (`generate_rashi_batch_progress.py`,
`generate_rashi_translation_inventory.py --check`) at the start of this
batch against current main to confirm the batch manifest entry is
unmodified and still selects exactly these 270 entries, that all 270 were
still UNREVIEWED, and that they were assigned only to `step6-batch-005`
(0 overlap with any other batch). A fresh review packet
(`generate_rashi_review_packets.py --batch-id step6-batch-005`) was
generated and used as the basis for review. No entry outside the batch
was edited.

## Child-PR split (change-count cap)

The confirmed changed count (78) exceeds the 40-changes-per-PR limit, so
this batch is applied as six deterministic child PRs, split by daf (each
daf's own changed count is already under 40), merged sequentially. The
parent batch identity (`step6-batch-005`) and its one review-records file
cover the complete, one-time review of all 270 entries; each child PR
applies only its own daf's confirmed English changes plus that daf's
inventory review-metadata.

| Child | Daf | Entries | Changed | PR | Merge SHA | Status |
|---|---|---|---|---|---|---|
| 1 | 11b | 37 | 12 | (pending) | (pending) | applying |
| 2 | 12a | 64 | 19 | (pending) | (pending) | not started |
| 3 | 12b | 60 | 18 | (pending) | (pending) | not started |
| 4 | 13a | 27 | 8 | (pending) | (pending) | not started |
| 5 | 13b | 26 | 4 | (pending) | (pending) | not started |
| 6 | 14a | 56 | 17 | (pending) | (pending) | not started |

This table is updated in place as each child PR merges. Batch 005 is not
COMPLETE until all six rows show a merge SHA.

## Method

Every entry was reviewed against its own Hebrew, its linked Gemara/Mishnah
context, neighboring Rashi entries (required wherever a Vilna line ends
mid-clause or mid-comment), the style guide, and the terminology registry -
never from the existing English alone. Risk scores and systemic-candidate
membership were treated as advisory only.

**First pass**: all 270 entries reviewed individually. Result: 192
VERIFIED, 78 MINOR_EDIT, 0 SUBSTANTIVE_REPAIR, 0 RETRANSLATE, 0
DUPLICATION_OR_CONTAMINATION, 0 BLOCKED.

**Second pass**: 100% of the 78 MINOR_EDIT entries independently
re-reviewed (re-derived from Hebrew and context again). Result: **78/78
CONFIRMED**, 0 MODIFIED, 0 REJECTED, 0 REMAINED_BLOCKED.

**Blind QA**: a deterministic 14.6% sample (28 of the 192 provisionally
VERIFIED entries, selected two ways fixed before any evidence text was
read: every 9th entry in canonical batch order, plus the first
risk-signaled VERIFIED entry per daf not already captured by that rule -
covering all 6 daf and both risk-signaled and zero-risk entries). Result:
**28/28 CONFIRMED_VERIFIED, 0 escalations.** No expansion of the sample
was required.

## Systemic-candidate review

### Family 1: fabricated "New comment:" scaffold text

78 of this batch's 270 entries (28.9%) carry this defect, the same
dominant pattern already confirmed in batches 040, 041, and 039.

**Root cause, confirmed against the raw source**: this daf range again
has Vilna print lines carrying more than one short Rashi comment on the
same physical line. The original AI-helper translation pass inserted an
English label at each such boundary instead of following the corpus's own
established convention (plain, unlabeled `'<next fragment>' - <comment>`,
e.g. `rashi-yoma-002a-001`).

**Refined wording-variant handling (correcting a mistake in batch 039)**:
one entry in this batch, `rashi-yoma-014a-014`, carries the `"New comment
on the mishna:"` wording variant. While reviewing this batch, a
corpus-wide check of the Hebrew abbreviation `מתני'` (Mishnah) found it is
consistently and correctly rendered elsewhere in this corpus as the
standalone marker `"Mishnah:"` (e.g. `67b` L35, `68b` L18, `70a` L26,
`71b` L10, `82a` L1, `83a` L21, `83a` L43, `85b` L39) - a real, meaningful
structural cue corresponding to a genuine Hebrew marker, not fabricated
text. This is the same phenomenon as `גמ'`/`"Gemara:"`, whose incorrect
full-strip in batch 039 (`rashi-yoma-083a-051`) was found during this
batch's review and corrected in a separate follow-up PR (see batch 039's
report for the correction note). For `rashi-yoma-014a-014`, only the
fabricated `"New comment on the"` portion was removed; `"Mishnah:"` was
preserved (`"(Chullin 132b). Mishnah: 'he sprinkles the'"`).

**Disposition for all 78: CONFIRMED_DEFECT.** Fix: remove the fabricated
label (preserving any genuine `"Gemara:"`/`"Mishnah:"` structural marker
where present) and let the next quoted fragment begin directly, per the
corpus's own established convention - verified individually for every
occurrence that the remaining text, once joined, is grammatically
coherent and semantically unchanged. MINOR_EDIT, defect tag
`INVENTED_TEXT`.

No new systemic family was created for this PR.

### Family 2: cross-entry word anticipation

6 candidates in this batch, all daf-boundary single-word stubs
(`rashi-yoma-011b-039`, `rashi-yoma-012a-066`, `rashi-yoma-012b-062`,
`rashi-yoma-013a-029`, `rashi-yoma-013b-028`, `rashi-yoma-014a-058`).
**Disposition: FALSE_POSITIVE for all 6.** Same low-precision
OVEREXPLAINED length-ratio trigger already confirmed in batches 040, 041,
and 039. This batch's stubs use the phrase `"is the catchword anticipating
<daf>'s opening comment"` rather than the terser `"This (...) continues on
<daf>."` template used elsewhere; verified this is a faithful, arguably
more precise description of the genuine Vilna-page catchword (kustos)
convention, and confirmed the full comment content lives at the linked
daf's opening entry - e.g. `rashi-yoma-011b-039`'s catchword `"דכרכים"`
corresponds to `rashi-yoma-012a-001`, whose full Hebrew (`"דכרכים. שהוא
מקום שווקים ומתקבצים שם ממקומות הרבה והיא"`) and English are already
independently REVIEWED/VERIFIED and correctly excluded from all 41 Step 6
batches (the same pattern as the `rashi-yoma-009b-001` source-repair
precedent). No anticipation defect present in any of the six. Left
unchanged, VERIFIED.

## Other risk-signaled entries (outside both systemic families)

20 additional medium-risk entries (5 of which overlap with the scaffold
family above and are resolved by that fix) were flagged by Step 2's
automated triage (`TRUNCATED`, `PUNCTUATION`, `WRONG_REFERENT`) but fall
outside both authorized systemic-candidate families. All confirmed
**FALSE_POSITIVE** for their respective signals: this corpus splits Rashi
comments across Vilna-line entries, so a line ending mid-clause is the
normal, correct shape of a continuing entry - confirmed in every case by
reading the immediately following vilnaLine entry, which completes the
clause. All are VERIFIED.

## Aggregate results (270 entries)

| Disposition | Count | Rate |
|---|---|---|
| VERIFIED | 192 | 71.1% |
| MINOR_EDIT | 78 | 28.9% |
| SUBSTANTIVE_REPAIR | 0 | 0.0% |
| RETRANSLATE | 0 | 0.0% |
| DUPLICATION_OR_CONTAMINATION | 0 | 0.0% |
| BLOCKED | 0 | 0.0% |
| **Total** | **270** | **100%** |

**Changed-translation count: 78** (English to be applied across the six
child PRs). Second-pass results: 78/78 CONFIRMED. Defect-tag totals:
`INVENTED_TEXT` 78 (all from the "New comment:" scaffold family and its
"New comment on the mishna:" wording variant; no other defect tag
occurred in this batch).

No BLOCKED entries and no structural/source-cache blockers were found
anywhere in this batch.

## Regression and platform evidence

Recorded per child PR below as each merges; batch-level totals (corpus
entry/association/boundary-registry counts, full validation suite) are
recorded once after child 6 (14a) merges, since only that state is the
true post-batch snapshot.

## Status

**Batch 005: IN PROGRESS.** Child 1/6 (11b) applying. Final disposition
totals for the full batch (both VERIFIED and MINOR_EDIT breakdowns) are
fixed above and will not change as children merge; only per-child
application status changes. This section and the child-PR table above are
updated as each child PR merges; batch 005 is COMPLETE only when all six
rows in the child-PR table show a merge SHA.
