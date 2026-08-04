# Rashi translation-quality campaign, Step 6 batch 015 report

Batch `step6-batch-015` of the full-corpus review defined in
`docs/reports/rashi-full-corpus-review-strategy.md` (Step 5). Selected as
the next batch per the strategy document's recommended order (position
35, "remaining contiguous order" priority group; prioritization only,
not evidence of defect). Full per-entry evidence lives in
`docs/reports/data/rashi-step6-batch-015-review-records.json` (validated
against the Step 5 contract).

## Batch scope (frozen from the committed batch plan, unmodified)

- **Batch id**: `step6-batch-015`
- **Perek**: 3 (closes at 39a) and the opening of Perek 4
- **Daf**: 36b, 37a, 37b, 38a, 38b, 39a (6 daf)
- **Tier**: `normal`
- **Entries**: 297 (36b=61, 37a=70, 37b=24, 38a=36, 38b=48, 39a=58)
- **Historical-provenance counts** (Step 1): `content-reviewed` 297
  (100%)

This batch carries no `known-needs-reconstruction` or
`known-needs-realignment` flag on any of its six daf. Every daf has its
own dedicated post-squash fix commit, predating this session's review.
Daf 36b has two applicable post-squash commits (the inventory's
`contentReviewCommits` array listed only the first; the second, a
targeted `linkedGemaraLineIds` correction shared with 36a, was found via
`git log` and is cited alongside it below).

Re-generated and re-validated (`generate_rashi_batch_progress.py`,
`generate_rashi_translation_inventory.py --check`) at the start of this
batch against current main to confirm the batch manifest entry is
unmodified and still selects exactly these 297 entries, that all 297
were still UNREVIEWED, and that they were assigned only to
`step6-batch-015` (0 overlap with any other batch). A fresh review
packet (`generate_rashi_review_packets.py --batch-id step6-batch-015`)
was generated and used as the basis for review. No entry outside the
batch was edited. All 297 entries have a non-empty `he` field.

## Method

All 297 entries were read individually and independently re-derived
from their own Hebrew (never from the existing English alone),
cross-checked against neighboring entries' Hebrew, linked Gemara/Mishnah
context, the style guide, and the terminology registry:

```
36b: 50bad7c Fix Yoma 36b Rashi helper alignment, second of the 36a-52b batch
     6345222 Fix Yoma 36a/36b linkedGemaraLineIds, correcting a self-caught methodology error
37a: 4561b93 Fix Yoma 37a Rashi helper alignment, third of the 36a-52b batch
37b: 1ef0d06 Fix Yoma 37b Rashi helper alignment, fourth of the 36a-52b batch
38a: 857320e Fix Yoma 38a Rashi helper alignment, fifth of the 36a-52b batch
38b: 280b236 Fix Yoma 38b Rashi helper alignment, sixth of the 36a-52b batch
39a: 84be26a Fix Yoma 39a Rashi helper alignment, seventh of the 36a-52b batch
```

**First pass**: all 297 entries reviewed individually. Result: **297
VERIFIED, 0 MINOR_EDIT, 0 SUBSTANTIVE_REPAIR, 0 RETRANSLATE, 0
DUPLICATION_OR_CONTAMINATION, 0 BLOCKED.**

**Second pass**: not applicable (0 changed entries).

**Blind QA**: a full-coverage sample was used for all 297 entries (not a
subsample), each independently re-derived from the raw Hebrew a second
time in a separate pass, deliberately independent of the first-pass
reasoning and the per-daf fix-commit lookups. Result: **297/297
CONFIRMED_VERIFIED, 0 escalations.**

## Systemic-candidate review

### Family 1: fabricated "New comment:" scaffold text

**0 candidates in this batch.** A corpus-wide check confirms 0
occurrences, consistent with `step6-batch-006` (this session) fully
draining this family from the entire unreviewed corpus.

### Family 2: cross-entry word anticipation

6 candidates in this batch, all daf-boundary single-word/fragment
stubs: `rashi-yoma-036b-062` (Hebrew "ומנין", deferred to 37a),
`rashi-yoma-037a-071` (Hebrew "בידות", deferred to 37b),
`rashi-yoma-037b-025` (Hebrew "בסירוגין", deferred to 38a),
`rashi-yoma-038a-037` (Hebrew "ומשלך", deferred to 38b),
`rashi-yoma-038b-049` (Hebrew "בא", deferred to 39a), and
`rashi-yoma-039a-059` (Hebrew "חמצן", deferred to 39b, outside this
batch's scope). **Disposition: FALSE_POSITIVE for all 6.** Same
low-precision OVEREXPLAINED length-ratio trigger already confirmed
throughout this session. Left unchanged, VERIFIED.

### Special entry: Perek 3/4 transition marker

`rashi-yoma-039a-005` (Hebrew "הדרן עלך אמר להם הממונה") flagged
OVEREXPLAINED (English 5.30x Hebrew length) and individually checked in
full. This is the standard Hadran formula closing Perek 3 ("Amar Lahem
HaMemune," named after that perek's own opening Mishnah words).
`linkedGemaraLineIds` confirms it maps only to gemara line
`yoma-039a-l13` (the Hadran line itself), distinct from the actual Perek
4 opening Mishnah at `yoma-039a-l14`/`rashi-yoma-039a-006` ("Mishnah: He
shook the urn"). The English is a faithful, literal translation of both
halves of the Hebrew - "We shall return to you" for the Hadran formula,
and "The appointed one said to them" as a correct literal rendering of
the perek-name citation - with bracketed editorial glosses that orient
the reader to the structural transition without altering or inventing
content. Confirmed **VERIFIED**, not a defect.

## Other risk-signaled entries (outside both systemic families)

No additional TRUNCATED or WRONG_REFERENT candidates were flagged in
this batch's risk signals beyond those already covered above.

## Aggregate results (297 entries)

| Disposition | Count | Rate |
|---|---|---|
| VERIFIED | 297 | 100.0% |
| MINOR_EDIT | 0 | 0.0% |
| SUBSTANTIVE_REPAIR | 0 | 0.0% |
| RETRANSLATE | 0 | 0.0% |
| DUPLICATION_OR_CONTAMINATION | 0 | 0.0% |
| BLOCKED | 0 | 0.0% |
| **Total** | **297** | **100%** |

**Changed-translation count: 0.** No PR content-diff applies to any
`modules/yoma/assets/learning/yoma/*.learning.json` file for this batch
- only review-records, inventory review-metadata, and documentation
change. No BLOCKED entries and no structural/source-cache blockers were
found anywhere in this batch.

## Regression and platform evidence

- Rashi entry count: 8,854 (unchanged) - Associations: 10,061 declared, 0
  broken, 0 cross-daf (unchanged) - Boundary registry: 20/20 (unchanged)
- Hebrew and English text: byte-unchanged across all 297 entries in this
  batch (0 changes to apply)
- `npm run validate:offline:yoma`, `npm test`, `npm run test:browser`,
  `npm run build`, `npm run check:deploy-html`, `python3
  scripts/worker_pipeline.py verify --full`: all green
- This batch completes the 35th parent-batch position for this session.
  The exhaustive 8-shard browser checkpoint (last triggered after the
  29th parent batch, `step6-batch-008`) is due once this batch merges.

## Status

**Batch 015: COMPLETE.** All 297 entries reviewed with an assigned final
disposition; 0 entries left in an ambiguous state; 0 BLOCKED. This is the
twenty-fourth consecutive batch this session (`002`, `003`, `023`,
`024`, `025`, `026`, `027`, `028`, `029`, `030`, `031`, `033`, `034`,
`035`, `009`, `017`, `007`, `008`, `010`, `011`, `012`, `013`, `014`,
`015`) with a fully positive finding (VERIFIED throughout). Blind QA
(100%, full coverage): 297/297 CONFIRMED_VERIFIED, 0 escalations.
