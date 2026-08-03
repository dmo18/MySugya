# Rashi translation-quality campaign, Step 6 batch 040 report

Batch `step6-batch-040` of the full-corpus review defined in
`docs/reports/rashi-full-corpus-review-strategy.md` (Step 5). Selected as
the next batch per the strategy document's recommended order (highest
systemic-candidate density; prioritization only, not evidence of defect).
Full per-entry evidence lives in
`docs/reports/data/rashi-step6-batch-040-review-records.json` (validated
against the Step 5 contract).

## Batch scope (frozen from the committed batch plan, unmodified)

- **Batch id**: `step6-batch-040`
- **Perek**: 8
- **Daf**: 85b, 86a, 86b, 87a (4 daf)
- **Tier**: `normal`
- **Entries**: 253
- **Risk-tier counts** (Step 2 automated triage, advisory only): high 0, medium 28, zero-risk 225
- **Historical-provenance counts** (Step 1): `content-reviewed` 253
- **Estimated changed count** (Step 5 projection): 27.8

Re-generated and re-validated (`plan_rashi_full_corpus_batches.py` /
`validate_rashi_full_corpus_batches.py`) at the start of this batch against
current main to confirm the manifest entry is unmodified and still
selects exactly these 253 entries. No entry outside the batch was edited.

## Child-PR split (change-count cap)

The confirmed changed count (109) exceeds the 40-changes-per-PR limit, so
this batch is applied as four deterministic child PRs, split by daf (each
daf's own changed count is already under 40), merged sequentially. The
parent batch identity (`step6-batch-040`) and its one review-records file
cover the complete, one-time review of all 253 entries; each child PR
applies only its own daf's confirmed English changes plus that daf's
inventory review-metadata.

| Child | Daf | Entries | Changed | PR | Merge SHA | Status |
|---|---|---|---|---|---|---|
| 1 | 85b | 58 | 17 | (this PR) | (pending) | applying |
| 2 | 86a | 68 | 30 | (pending) | (pending) | not started |
| 3 | 86b | 57 | 27 | (pending) | (pending) | not started |
| 4 | 87a | 70 | 35 | (pending) | (pending) | not started |

This table is updated in place as each child PR merges. Batch 040 is not
COMPLETE until all four rows show a merge SHA.

## Method

Every entry was reviewed against its own Hebrew, its linked Gemara/Mishnah
context, neighboring Rashi entries (required wherever a Vilna line ends
mid-clause or mid-comment), the style guide, and the terminology registry -
never from the existing English alone. Risk scores and systemic-candidate
membership were treated as advisory only; systemic-candidate density is
prioritization only, not evidence of defect.

**First pass**: all 253 entries reviewed individually. Result: 144
VERIFIED, 109 MINOR_EDIT, 0 SUBSTANTIVE_REPAIR, 0 RETRANSLATE, 0
DUPLICATION_OR_CONTAMINATION, 0 BLOCKED.

**Second pass**: 100% of the 109 MINOR_EDIT entries independently
re-reviewed (re-derived from Hebrew and context again). Result: **109/109
CONFIRMED**, 0 MODIFIED, 0 REJECTED, 0 REMAINED_BLOCKED.

**Blind QA**: a deterministic 11.1% sample (16 of the 144 provisionally
VERIFIED entries, selected by positional order - every 9th entry in the
batch's canonical entryId sequence, independent of first-pass reasoning,
not replaceable after selection - covering all 4 daf and both risk-signaled
and zero-risk entries). Result: **16/16 CONFIRMED_VERIFIED, 0
escalations.** Per the escalation rule, no expansion of the second-pass
sample was required.

## Systemic-candidate review

### Family 1: fabricated "New comment:" scaffold text

109 of this batch's 253 entries (43%) carried this batch's dominant
defect - by far the largest concentration found anywhere in the campaign
to date, consistent with this batch's "highest systemic-candidate
density" ranking.

**Root cause, confirmed against the raw source**: this daf range has an
unusually high rate of Vilna print lines carrying more than one short
Rashi comment on the same physical line (`modules/yoma/assets/talmuddev/
{85b,86a,86b,87a}.json`'s `rashi[]` array shows a mid-line Hebrew colon
wherever this happens, e.g. 85b line 2: `"ועבודה. חמורה שדוחה את השבת
מפסיקה להצלת נפש: ומה מילה."` - two comments, colon-separated). The
original AI-helper translation pass inserted the literal English label
`"New comment: "` at each such boundary instead of following the corpus's
own established convention (plain, unlabeled `'<next fragment>' -
<comment>`, e.g. `rashi-yoma-002a-001`). This label has **no Hebrew basis
at all** - the Hebrew colon is Vilna punctuation, never the words "new
comment" - and is exactly the class of fabricated structural narration
this campaign's own worker-prompt convention already forbids (never
narrate "opens/continues/begins" or an unlabeled equivalent instead of
translating).

**Disposition for all 109: CONFIRMED_DEFECT.** Fix: remove the literal
string `"New comment: "` and let the next quoted fragment begin directly,
per the corpus's own established convention - verified individually for
every occurrence that the remaining text, once joined, is grammatically
coherent and semantically unchanged (the underlying translation content
was already accurate in every case checked; only the fabricated label is
removed). MINOR_EDIT, defect tag `INVENTED_TEXT` (fabricated text with no
Hebrew basis; the surrounding translation's meaning is not affected).

No new systemic family was created for this PR. The full per-entry
old/new English pairs are recorded in the review-records file and (for
each daf) applied in that daf's own child PR below.

### Family 2: cross-entry word anticipation

4 candidates in this batch, all daf-boundary single-word stubs
(`rashi-yoma-085b-058`, `rashi-yoma-086a-068`, `rashi-yoma-086b-057`,
`rashi-yoma-087a-070`), each already correctly formatted as `"This
('<gloss>') continues on <daf>."`. **Disposition: FALSE_POSITIVE for all
4.** This family reuses the Step 2 OVEREXPLAINED signal (explicitly
documented as low-precision for this specific defect) as its candidate
list; these 4 were flagged purely because a single-Hebrew-word source
(e.g. `אתא`, 3 characters) makes any English annotation look
disproportionately long by the length-ratio heuristic, not because any
word was actually imported from a neighboring entry. No anticipation
defect is present in any of the four.

**Advisory observation only (not a new family, not acted on in this
PR)**: these 4 stubs use a terser phrasing than the campaign's better,
already-established page-boundary template (`rashi-yoma-005a-040`:
`'<gloss>' - the daf ends mid-word here; Rashi's comment continues on
<daf>, where <what the continuation establishes>.`). They are faithful as
written (no invented or missing content), so per the standing rule
against rewriting faithful English for stylistic preference, they were
left unchanged and marked VERIFIED; a future pass could consider
enriching them to the fuller template as a pure style improvement.

## Other risk-signaled entries (outside both systemic families)

18 additional medium-risk entries were flagged by Step 2's automated
triage (`TRUNCATED`, `WRONG_REFERENT`, `PUNCTUATION`) but fall outside
both authorized systemic-candidate families. All 18 were confirmed
**FALSE_POSITIVE** for their respective signals: this corpus splits Rashi
comments across Vilna-line entries, so a line ending mid-clause, a
pronoun-heavy clause, or an unmatched opening parenthesis is the normal,
correct shape of a continuing entry - confirmed in every case by reading
the immediately following vilnaLine entry, which completes the clause,
resolves the pronoun, or closes the parenthesis. All 18 are VERIFIED.

## Aggregate results (253 entries)

| Disposition | Count | Rate |
|---|---|---|
| VERIFIED | 144 | 56.9% |
| MINOR_EDIT | 109 | 43.1% |
| SUBSTANTIVE_REPAIR | 0 | 0.0% |
| RETRANSLATE | 0 | 0.0% |
| DUPLICATION_OR_CONTAMINATION | 0 | 0.0% |
| BLOCKED | 0 | 0.0% |
| **Total** | **253** | **100%** |

**Changed-translation count: 109** (English to be applied across the four
child PRs; 17 applied in this PR). Second-pass results: 109/109
CONFIRMED. Defect-tag totals: `INVENTED_TEXT` 109 (all from the
"New comment:" scaffold family; no other defect tag occurred in this
batch).

No BLOCKED entries and no structural/source-cache blockers were found
anywhere in this batch.

## Regression and platform evidence

Recorded per child PR below as each merges; batch-level totals (corpus
entry/association/boundary-registry counts, full validation suite,
exhaustive browser-shard result) are recorded once after child 4 (87a)
merges, since only that state is the true post-batch snapshot.

### Child 1 (85b) - 17 changed, 58 reviewed

- Rashi entry count: 8,854 (unchanged) - Associations: 10,061 declared, 0
  broken, 0 cross-daf (unchanged) - Boundary registry: 20/20 (unchanged)
- Hebrew text: byte-unchanged across all 58 entries on this daf
- `npm run validate:offline:yoma`, `npm test`, `npm run test:browser`,
  `npm run build`, `npm run check:deploy-html`, `python3
  scripts/worker_pipeline.py verify --full`: all green

## Status

**Batch 040: IN PROGRESS.** Child 1/4 (85b) applying now. Full-corpus
progress after child 1: see batch progress tool
(`generate_rashi_batch_progress.py`), which correctly reports this batch
as partial (58/253) until all four children merge. Reviewed/UNREVIEWED
full-corpus totals are updated per child PR below as each merges. Do not
begin `step6-batch-` (any later batch) until this batch shows COMPLETE.
