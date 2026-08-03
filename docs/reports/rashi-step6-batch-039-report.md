# Rashi translation-quality campaign, Step 6 batch 039 report

Batch `step6-batch-039` of the full-corpus review defined in
`docs/reports/rashi-full-corpus-review-strategy.md` (Step 5). Selected as
the next batch per the strategy document's recommended order (position 2,
systemic-candidate-dense priority group; prioritization only, not evidence
of defect). Full per-entry evidence lives in
`docs/reports/data/rashi-step6-batch-039-review-records.json` (validated
against the Step 5 contract).

## Batch scope (frozen from the committed batch plan, unmodified)

- **Batch id**: `step6-batch-039`
- **Perek**: 8
- **Daf**: 83a, 83b, 84a, 84b, 85a (5 daf)
- **Tier**: `normal`
- **Entries**: 294
- **Risk-tier counts** (Step 2 automated triage, advisory only): high 0, medium 24, zero-risk 270
- **Historical-provenance counts** (Step 1): `content-reviewed` 294
- **Estimated changed count** (Step 5 projection): 32.3

Re-generated and re-validated (`generate_rashi_batch_progress.py`,
`generate_rashi_translation_inventory.py --check`) at the start of this
batch against current main to confirm the batch manifest entry is
unmodified and still selects exactly these 294 entries, that all 294 were
still UNREVIEWED, and that they were assigned only to `step6-batch-039`
(0 overlap with any other batch). A fresh review packet
(`generate_rashi_review_packets.py --batch-id step6-batch-039`) was
generated and used as the basis for review. No entry outside the batch was
edited.

## Child-PR split (change-count cap)

The confirmed changed count (108) exceeds the 40-changes-per-PR limit, so
this batch is applied as five deterministic child PRs, split by daf (each
daf's own changed count is already under 40), merged sequentially. The
parent batch identity (`step6-batch-039`) and its one review-records file
cover the complete, one-time review of all 294 entries; each child PR
applies only its own daf's confirmed English changes plus that daf's
inventory review-metadata.

| Child | Daf | Entries | Changed | PR | Merge SHA | Status |
|---|---|---|---|---|---|---|
| 1 | 83a | 58 | 16 | (pending) | (pending) | applying |
| 2 | 83b | 57 | 22 | (pending) | (pending) | not started |
| 3 | 84a | 55 | 25 | (pending) | (pending) | not started |
| 4 | 84b | 64 | 24 | (pending) | (pending) | not started |
| 5 | 85a | 60 | 21 | (pending) | (pending) | not started |

This table is updated in place as each child PR merges. Batch 039 is not
COMPLETE until all five rows show a merge SHA.

## Method

Every entry was reviewed against its own Hebrew, its linked Gemara/Mishnah
context, neighboring Rashi entries (required wherever a Vilna line ends
mid-clause or mid-comment), the style guide, and the terminology registry -
never from the existing English alone. Risk scores and systemic-candidate
membership were treated as advisory only.

**First pass**: all 294 entries reviewed individually. Result: 186
VERIFIED, 108 MINOR_EDIT, 0 SUBSTANTIVE_REPAIR, 0 RETRANSLATE, 0
DUPLICATION_OR_CONTAMINATION, 0 BLOCKED.

**Second pass**: 100% of the 108 MINOR_EDIT entries independently
re-reviewed (re-derived from Hebrew and context again). Result: **108/108
CONFIRMED**, 0 MODIFIED, 0 REJECTED, 0 REMAINED_BLOCKED.

**Blind QA**: a deterministic 14.0% sample (26 of the 186 provisionally
VERIFIED entries, selected two ways fixed before any evidence text was
read: every 9th entry in canonical batch order, plus the first
risk-signaled VERIFIED entry per daf not already captured by that rule -
covering all 5 daf and both risk-signaled and zero-risk entries). Result:
**26/26 CONFIRMED_VERIFIED, 0 escalations.** No expansion of the sample
was required.

## Systemic-candidate review

### Family 1: fabricated "New comment:" scaffold text

107 of this batch's 294 entries (36.4%) carry this defect, the same
dominant pattern already confirmed in batches 040 and 041.

**Root cause, confirmed against the raw source**: this daf range again has
Vilna print lines carrying more than one short Rashi comment on the same
physical line. The original AI-helper translation pass inserted an English
label at each such boundary instead of following the corpus's own
established convention (plain, unlabeled `'<next fragment>' - <comment>`,
e.g. `rashi-yoma-002a-001`).

**New finding this batch, recorded for future batches' benefit**: the
label is not always the exact literal string `"New comment: "`. A
corpus-wide search (`grep` across all 173 daf's `learning_data.js`) found
five additional wording variants of the same fabricated label:
`"New comment on the Gemara:"` (3 occurrences corpus-wide: `81a` L22,
`82a` L55, and this batch's `rashi-yoma-083a-051`), `"New comment on the
Mishnah:"` (2 occurrences: `81a` L18, `82a` L54), `"New comment on the
mishna:"` (1 occurrence: `14a` L14), and `"New comment, textual note:"`
(1 occurrence: `51b` L5). All are the identical defect - a leaked internal
processing label with no Hebrew basis - just with different appended
wording; the fix is the same (remove the entire label). None of the other
four daf carrying these variants (`14a`, `51b`, `81a`, `82a`) belong to any
already-completed batch (001, 040, 041), so nothing in prior completed
work needs revisiting; the variant is simply noted here as an advisory
observation so future batches searching only for the literal string
`"New comment: "` do not miss it. `rashi-yoma-083a-051` in this batch
carries both the `"New comment on the Gemara:"` variant and a plain
`"New comment: "` later in the same field; both were removed together.

**Disposition for all 107: CONFIRMED_DEFECT.** Fix: remove the label and
let the next quoted fragment begin directly, per the corpus's own
established convention - verified individually for every occurrence that
the remaining text, once joined, is grammatically coherent and
semantically unchanged. MINOR_EDIT, defect tag `INVENTED_TEXT`.

No new systemic family was created for this PR (this is a documented
wording variant of the existing authorized family, not a new pattern).

### Family 2: cross-entry word anticipation

5 candidates in this batch, all daf-boundary single-word stubs
(`rashi-yoma-083a-058`, `rashi-yoma-083b-057`, `rashi-yoma-084a-055`,
`rashi-yoma-084b-064`, `rashi-yoma-085a-060`), each the final vilnaLine of
its own daf and already correctly formatted as `"This ('<gloss>')
continues on <daf>."`. **Disposition: FALSE_POSITIVE for all 5.** Same
low-precision OVEREXPLAINED length-ratio trigger already confirmed in
batches 040 and 041; no anticipation defect present in any of the five.
Left unchanged, VERIFIED.

## Other findings (outside both authorized families)

**Isolated defect found during individual review**: `rashi-yoma-084b-023`
(Hebrew `"אע"ג דקאמר הכא משנה יתירה דייק"`) rendered the impersonal
construction `דייק` ("precisely infers/indicates") as `"Rashi deduces"`,
naming the commentator by name. A corpus-wide search confirms this
construction is rendered impersonally everywhere else in the 8,854-entry
corpus (e.g. `rashi-yoma-083b-033`: `"he scrutinized the name"`); this is
the only entry anywhere in the corpus that names "Rashi" as an explicit
actor, which is inconsistent with both the corpus's own established voice
and with how a commentary would refer to its own author. **Disposition:
CONFIRMED_DEFECT** (an isolated finding, not part of either authorized
systemic family - reported here as an advisory observation per the
governing directive, not enforced as a new family). Fix: replace `"Rashi
deduces"` with the impersonal `"this precisely indicates"`. MINOR_EDIT,
defect tag `INVENTED_TEXT`.

**Other risk-signaled entries**: 19 additional medium-risk entries (7 of
which overlap with the scaffold family above and are resolved by that
fix) were flagged by Step 2's automated triage (`TRUNCATED`,
`WRONG_REFERENT`) but fall outside both authorized systemic-candidate
families. All confirmed **FALSE_POSITIVE** for their respective signals:
this corpus splits Rashi comments across Vilna-line entries, so a line
ending mid-clause is the normal, correct shape of a continuing entry -
confirmed in every case by reading the immediately following vilnaLine
entry, which completes the clause. All are VERIFIED.

## Aggregate results (294 entries)

| Disposition | Count | Rate |
|---|---|---|
| VERIFIED | 186 | 63.3% |
| MINOR_EDIT | 108 | 36.7% |
| SUBSTANTIVE_REPAIR | 0 | 0.0% |
| RETRANSLATE | 0 | 0.0% |
| DUPLICATION_OR_CONTAMINATION | 0 | 0.0% |
| BLOCKED | 0 | 0.0% |
| **Total** | **294** | **100%** |

**Changed-translation count: 108** (English to be applied across the five
child PRs). Second-pass results: 108/108 CONFIRMED. Defect-tag totals:
`INVENTED_TEXT` 108 (107 from the "New comment:" scaffold family plus its
wording variant, 1 isolated finding at `rashi-yoma-084b-023`).

No BLOCKED entries and no structural/source-cache blockers were found
anywhere in this batch.

## Regression and platform evidence

Recorded per child PR below as each merges; batch-level totals (corpus
entry/association/boundary-registry counts, full validation suite) are
recorded once after child 5 (85a) merges, since only that state is the
true post-batch snapshot.

### Child 1 (83a) - 16 changed, 58 reviewed

- Rashi entry count: 8,854 (unchanged) - Associations: 10,061 declared, 0
  broken, 0 cross-daf (unchanged) - Boundary registry: 20/20 (unchanged)
- Hebrew text: byte-unchanged across all 58 entries on this daf
- `npm run validate:offline:yoma`, `npm test`, `npm run test:browser`,
  `npm run build`, `npm run check:deploy-html`, `python3
  scripts/worker_pipeline.py verify --full`: all green

## Status

**Batch 039: IN PROGRESS.** Child 1/5 (83a) applying. Final disposition
totals for the full batch (both VERIFIED and MINOR_EDIT breakdowns) are
fixed above and will not change as children merge; only per-child
application status changes. This section and the child-PR table above are
updated as each child PR merges; batch 039 is COMPLETE only when all five
rows in the child-PR table show a merge SHA.
