# Rashi translation-quality campaign, Step 6 batch 037 report

Batch `step6-batch-037` of the full-corpus review defined in
`docs/reports/rashi-full-corpus-review-strategy.md` (Step 5). Selected as
the next batch per the strategy document's recommended order (position 5,
systemic-candidate-dense priority group; prioritization only, not evidence
of defect). Full per-entry evidence lives in
`docs/reports/data/rashi-step6-batch-037-review-records.json` (validated
against the Step 5 contract).

## Batch scope (frozen from the committed batch plan, unmodified)

- **Batch id**: `step6-batch-037`
- **Perek**: 8
- **Daf**: 77a, 77b, 78a, 78b, 79a, 79b (6 daf)
- **Tier**: `normal`
- **Entries**: 250
- **Risk-tier counts** (Step 2 automated triage, advisory only): high 0, medium 27, zero-risk 223
- **Historical-provenance counts** (Step 1): `content-reviewed` 250
- **Estimated changed count** (Step 5 projection): 27.5

Re-generated and re-validated (`generate_rashi_batch_progress.py`,
`generate_rashi_translation_inventory.py --check`) at the start of this
batch against current main to confirm the batch manifest entry is
unmodified and still selects exactly these 250 entries, that all 250 were
still UNREVIEWED, and that they were assigned only to `step6-batch-037`
(0 overlap with any other batch). A fresh review packet
(`generate_rashi_review_packets.py --batch-id step6-batch-037`) was
generated and used as the basis for review. No entry outside the batch
was edited.

## Child-PR split (change-count cap)

The confirmed changed count (69) exceeds the 40-changes-per-PR limit, so
this batch is applied as six deterministic child PRs, split by daf (each
daf's own changed count is already under 40), merged sequentially. The
parent batch identity (`step6-batch-037`) and its one review-records file
cover the complete, one-time review of all 250 entries; each child PR
applies only its own daf's confirmed English changes plus that daf's
inventory review-metadata.

| Child | Daf | Entries | Changed | PR | Merge SHA | Status |
|---|---|---|---|---|---|---|
| 1 | 77a | 43 | 16 | #430 | `e075287c20f5bdd1f67a3f257737e50de108dc94` | merged |
| 2 | 77b | 59 | 14 | #431 | `2de645f2c066fae6ef9877271c68b58a9424694f` | merged |
| 3 | 78a | 52 | 18 | (pending) | (pending) | applying |
| 4 | 78b | 45 | 16 | (pending) | (pending) | pending |
| 5 | 79a | 16 | 2 | (pending) | (pending) | pending |
| 6 | 79b | 35 | 3 | (pending) | (pending) | pending |

This table is updated in place as each child PR merges. Batch 037 is not
COMPLETE until all six rows show a merge SHA.

## Method

Every entry was reviewed against its own Hebrew, its linked Gemara/Mishnah
context, neighboring Rashi entries (required wherever a Vilna line ends
mid-clause or mid-comment), the style guide, and the terminology registry -
never from the existing English alone. Risk scores and systemic-candidate
membership were treated as advisory only.

**First pass**: all 250 entries reviewed individually. Result: 181
VERIFIED, 69 MINOR_EDIT, 0 SUBSTANTIVE_REPAIR, 0 RETRANSLATE, 0
DUPLICATION_OR_CONTAMINATION, 0 BLOCKED.

**Second pass**: 100% of the 69 MINOR_EDIT entries independently
re-reviewed (re-derived from Hebrew and context again). Result: **69/69
CONFIRMED**, 0 MODIFIED, 0 REJECTED, 0 REMAINED_BLOCKED.

**Blind QA**: a deterministic 14.9% sample (27 of the 181 provisionally
VERIFIED entries, selected two ways fixed before any evidence text was
read: every 9th entry in canonical batch order, plus the first
risk-signaled VERIFIED entry per daf not already captured by that rule -
covering all 6 daf and both risk-signaled and zero-risk entries). Result:
**27/27 CONFIRMED_VERIFIED, 0 escalations.** No expansion of the sample
was required.

## Systemic-candidate review

### Family 1: fabricated "New comment:" scaffold text, plus two newly observed synonym variants

67 of this batch's 250 entries (26.8%) carry the base "New comment:"
defect, the same dominant pattern already confirmed in batches 040, 041,
039, 005, and 038.

**Wording-variant handling (per the corrected rule established while
reviewing batch 005, itself correcting a mistake made in batch 039)**:
this batch contains no `"New comment on the Mishnah/Gemara:"` instances,
but does contain two previously-unseen fabricated-label synonyms, found
by a corpus-wide check before deciding on a fix in each case:

- **`"Continuing:"`** - one occurrence, `rashi-yoma-077a-002`, a second
  fabricated scaffold label at a second colon boundary within an entry
  that also carries a plain `"New comment:"` earlier in the same field.
  No Hebrew basis for either label (the Hebrew shows only mid-line
  colons). Fix: removed both labels entirely, same as the base "New
  comment:" family. This entry is counted once in the 67 above (it is
  not double-counted as a separate family member).
- **`"Textual note:"`** - two occurrences, `rashi-yoma-077b-002` and
  `rashi-yoma-078a-003`, both a fabricated redundant prefix placed before
  an already-complete "this is the correct reading" note (Hebrew `ה"ג`
  / `הכי גרסינן`). Checked against the corpus's own established
  convention for this construction elsewhere (37a L66, 42a L3, 57b L35,
  74b L34, 80a L60, 80a L62): in every other occurrence the note begins
  directly with a capitalized `"This is the correct reading:"` /
  `"This is our reading:"`, with no separate label. Fix: removed
  `"Textual note: "` and capitalized the first letter of what follows,
  bringing both entries into line with the corpus's established
  rendering. These two entries are additional to the 67 above (69 total
  MINOR_EDIT in this family).

Neither synonym is common enough corpus-wide to warrant a new named
systemic family (per the directive's instruction not to create new
families); both are recorded here as advisory notes and folded into the
existing scaffold-removal disposition.

**Disposition for all 69: CONFIRMED_DEFECT.** Fix: remove the fabricated
label(s) (preserving any genuine `"Gemara:"`/`"Mishnah:"` structural
marker where present - none occurred in this batch) and let the next
quoted fragment or clause begin directly, per the corpus's own
established convention - verified individually for every occurrence that
the remaining text, once joined, is grammatically coherent and
semantically unchanged. MINOR_EDIT, defect tag `INVENTED_TEXT`.

No new systemic family was created for this PR.

### Family 2: cross-entry word anticipation

5 candidates in this batch, all daf-boundary single-word/marker stubs
(`rashi-yoma-077a-043`, `rashi-yoma-077b-059`, `rashi-yoma-078a-052`,
`rashi-yoma-079a-016`, `rashi-yoma-079b-035`). **Disposition:
FALSE_POSITIVE for all 5.** Same low-precision OVEREXPLAINED length-ratio
trigger already confirmed in batches 040, 041, 039, 005, and 038. Left
unchanged, VERIFIED.

## Other risk-signaled entries (outside both systemic families)

21 additional medium-risk entries were flagged by Step 2's automated
triage (`TRUNCATED`, `PUNCTUATION`, `WRONG_REFERENT`, `OVEREXPLAINED`) but
fall outside both authorized systemic-candidate families. All confirmed
**FALSE_POSITIVE** for their respective signals: this corpus splits Rashi
comments across Vilna-line entries, so a line ending mid-clause is the
normal, correct shape of a continuing entry - confirmed in every case by
reading the immediately following vilnaLine entry, which completes the
clause. All are VERIFIED.

## Aggregate results (250 entries)

| Disposition | Count | Rate |
|---|---|---|
| VERIFIED | 181 | 72.4% |
| MINOR_EDIT | 69 | 27.6% |
| SUBSTANTIVE_REPAIR | 0 | 0.0% |
| RETRANSLATE | 0 | 0.0% |
| DUPLICATION_OR_CONTAMINATION | 0 | 0.0% |
| BLOCKED | 0 | 0.0% |
| **Total** | **250** | **100%** |

**Changed-translation count: 69** (English to be applied across the six
child PRs). Second-pass results: 69/69 CONFIRMED. Defect-tag totals:
`INVENTED_TEXT` 69 (67 from the base "New comment:" scaffold family, plus
the two newly observed "Textual note:" synonym instances; the single
"Continuing:" synonym instance is counted within the 67 since it co-occurs
with a base "New comment:" removal in the same entry).

No BLOCKED entries and no structural/source-cache blockers were found
anywhere in this batch.

## Regression and platform evidence

Recorded per child PR below as each merges; batch-level totals (corpus
entry/association/boundary-registry counts, full validation suite) are
recorded once after child 6 (79b) merges, since only that state is the
true post-batch snapshot.

### Child 1 (77a) - 16 changed, 43 reviewed (merged as #430)

- Rashi entry count: 8,854 (unchanged) - Associations: 10,061 declared, 0
  broken, 0 cross-daf (unchanged) - Boundary registry: 20/20 (unchanged)
- Hebrew text: byte-unchanged across all 43 entries on this daf
- `npm run validate:offline:yoma`, `npm test`, `npm run test:browser`,
  `npm run build`, `npm run check:deploy-html`, `python3
  scripts/worker_pipeline.py verify --full`: all green

### Child 2 (77b) - 14 changed, 59 reviewed (merged as #431)

- Rashi entry count: 8,854 (unchanged) - Associations: 10,061 declared, 0
  broken, 0 cross-daf (unchanged) - Boundary registry: 20/20 (unchanged)
- Hebrew text: byte-unchanged across all 59 entries on this daf
- `npm run validate:offline:yoma`, `npm test`, `npm run test:browser`,
  `npm run build`, `npm run check:deploy-html`, `python3
  scripts/worker_pipeline.py verify --full`: all green

### Child 3 (78a) - 18 changed, 52 reviewed (applying)

- Rashi entry count: 8,854 (unchanged) - Associations: 10,061 declared, 0
  broken, 0 cross-daf (unchanged) - Boundary registry: 20/20 (unchanged)
- Hebrew text: byte-unchanged across all 52 entries on this daf
- `npm run validate:offline:yoma`, `npm test`, `npm run test:browser`,
  `npm run build`, `npm run check:deploy-html`, `python3
  scripts/worker_pipeline.py verify --full`: all green

## Status

**Batch 037: IN PROGRESS.** All 250 entries reviewed with an assigned
final disposition (this parent review pass is complete); child PRs are
being applied and merged sequentially to bring the English text in line
with the confirmed dispositions. Final review-pass disposition totals:
181 VERIFIED, 69 MINOR_EDIT, 0 SUBSTANTIVE_REPAIR, 0 RETRANSLATE, 0
DUPLICATION_OR_CONTAMINATION, 0 BLOCKED. Changed-translation count: 69
(all `INVENTED_TEXT`). Second pass: 69/69 CONFIRMED. Blind QA: 27/27
CONFIRMED_VERIFIED, 0 escalations. Both authorized systemic-candidate
families resolved (scaffold: 69 CONFIRMED_DEFECT, applying; anticipation:
5 FALSE_POSITIVE, unchanged).
