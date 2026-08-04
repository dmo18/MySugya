# Rashi translation-quality campaign, Step 6 batch 003 report

Batch `step6-batch-003` of the full-corpus review defined in
`docs/reports/rashi-full-corpus-review-strategy.md` (Step 5). Selected as
the next batch per the strategy document's recommended order (position
12, high-risk (dense) priority group; prioritization only, not evidence
of defect). Full per-entry evidence lives in
`docs/reports/data/rashi-step6-batch-003-review-records.json` (validated
against the Step 5 contract).

## Batch scope (frozen from the committed batch plan, unmodified)

- **Batch id**: `step6-batch-003`
- **Perek**: 1
- **Daf**: 6b, 7a, 7b, 8a (4 daf)
- **Tier**: `dense`
- **Entries**: 126
- **Risk-tier counts** (Step 2 automated triage, advisory only): high 26, medium 12, zero-risk 88
- **Historical-provenance counts** (Step 1): `known-needs-reconstruction` 26, `checked-no-fix-needed` 51, `content-reviewed` 49
- **Estimated changed count** (Step 5 projection): 14.6

The 26 `known-needs-reconstruction` entries (all on daf 6b) carry a more
serious historical flag than `step6-batch-002`'s `known-needs-
realignment` bucket: an `INVENTED_TEXT` Step 2 risk signal citing a
"VERSION 15.293 Wave 1 audit" finding that this daf's `en` text was
"generic filler or fabricated, unrelated to its own Hebrew line."

Re-generated and re-validated (`generate_rashi_batch_progress.py`,
`generate_rashi_translation_inventory.py --check`) at the start of this
batch against current main to confirm the batch manifest entry is
unmodified and still selects exactly these 126 entries, that all 126
were still UNREVIEWED, and that they were assigned only to
`step6-batch-003` (0 overlap with any other batch). A fresh review
packet (`generate_rashi_review_packets.py --batch-id step6-batch-003`)
was generated and used as the basis for review. No entry outside the
batch was edited.

## Method and key finding: the "needs-reconstruction" flag on daf 6b is stale

Before reading the 26 flagged entries at face value, `git log --oneline
--all -- modules/yoma/assets/learning/yoma/6b.learning.json` was checked
to establish the daf's actual repair history. It shows:

```
b191909 Yoma 6b: full Rashi reconstruction (29 entries) (#291)
```

Daf 6b was **already fully reconstructed in PR #291**, well before the
VERSION 15.293 Wave 1 audit whose finding is still cited by the current
Step 2 risk-signal generator and the batch-planning `known-needs-
reconstruction` provenance bucket. The classification metadata was never
refreshed to reflect that the underlying content problem had already
been fixed - this is the same class of stale-historical-signal issue
already encountered with `step6-batch-002`'s universal `CONTEXT_MISMATCH`
flag, but for a stronger ("confirmed fabricated") historical claim, so it
warranted correspondingly stronger verification before accepting it as
resolved.

All 126 entries were read and independently re-derived from their own
Hebrew (never from the existing English alone), cross-checked against
neighboring entries' Hebrew, linked Gemara/Mishnah context, the style
guide, and the terminology registry. Every one of the 26 flagged daf-6b
entries was individually confirmed to be a faithful, specific,
non-generic translation of its own Hebrew line - not filler, not
fabricated, and not shifted from a neighbor.

**First pass**: all 126 entries reviewed individually. Result: **126
VERIFIED, 0 MINOR_EDIT, 0 SUBSTANTIVE_REPAIR, 0 RETRANSLATE, 0
DUPLICATION_OR_CONTAMINATION, 0 BLOCKED.**

**Second pass**: not applicable (0 changed entries).

**Blind QA**: given the significance of confirming a stale "confirmed
fabricated" historical flag, a full-coverage sample was used for daf 6b
(all 26 of its entries, not a subsample) plus a denser-than-usual every-
6th-entry sample across the other 3 daf (16 of 100), for a combined
sample of 42 of 126 provisionally VERIFIED entries (33.3%) covering all
4 daf. Each was independently re-derived from the raw Hebrew a second
time, deliberately independent of the first-pass reasoning and the PR
#291 history lookup. Result: **42/42 CONFIRMED_VERIFIED, 0
escalations.** No expansion of the sample was required.

## Systemic-candidate review

### Family 1: fabricated "New comment:" scaffold text

**0 candidates in this batch.** A corpus-wide check confirms 0
occurrences, consistent with `step6-batch-006` (2 batches prior this
session) fully draining this family from the entire unreviewed corpus.

### Family 2: cross-entry word anticipation

4 candidates in this batch, all daf-boundary single-word/marker stubs:
`rashi-yoma-006b-029`, `rashi-yoma-007a-053`, `rashi-yoma-007b-018`
(all three flagged by the automated systemic-candidates generator), plus
`rashi-yoma-008a-035` (the batch's final entry, `"That this one"` for
Hebrew `"שזה"` - not flagged by the automated detector, but confirmed a
genuine catchword by direct comparison: 8b's actual opening entry begins
`"'That this one's separation is for holiness' ..."`, an exact match).
**Disposition: FALSE_POSITIVE for all 4.** Same low-precision
OVEREXPLAINED/FRAGMENT length-ratio trigger already confirmed throughout
this session. Left unchanged, VERIFIED.

## Other risk-signaled entries (outside both systemic families)

12 additional medium-risk entries were flagged by Step 2's automated
triage (`TRUNCATED`) but fall outside both authorized systemic-candidate
families. All confirmed **FALSE_POSITIVE**: this corpus splits Rashi
comments across Vilna-line entries, so a line ending mid-clause is the
normal, correct shape of a continuing entry - confirmed in every case by
reading the immediately following vilnaLine entry, which completes the
clause. All are VERIFIED.

## Aggregate results (126 entries)

| Disposition | Count | Rate |
|---|---|---|
| VERIFIED | 126 | 100.0% |
| MINOR_EDIT | 0 | 0.0% |
| SUBSTANTIVE_REPAIR | 0 | 0.0% |
| RETRANSLATE | 0 | 0.0% |
| DUPLICATION_OR_CONTAMINATION | 0 | 0.0% |
| BLOCKED | 0 | 0.0% |
| **Total** | **126** | **100%** |

**Changed-translation count: 0.** No PR content-diff applies to any
`modules/yoma/assets/learning/yoma/*.learning.json` file for this batch
- only review-records, inventory review-metadata, and documentation
change. No BLOCKED entries and no structural/source-cache blockers were
found anywhere in this batch.

## Regression and platform evidence

- Rashi entry count: 8,854 (unchanged) - Associations: 10,061 declared, 0
  broken, 0 cross-daf (unchanged) - Boundary registry: 20/20 (unchanged)
- Hebrew and English text: byte-unchanged across all 126 entries in this
  batch (0 changes to apply)
- `npm run validate:offline:yoma`, `npm test`, `npm run test:browser`,
  `npm run build`, `npm run check:deploy-html`, `python3
  scripts/worker_pipeline.py verify --full`: all green

## Status

**Batch 003: COMPLETE.** All 126 entries reviewed with an assigned final
disposition; 0 entries left in an ambiguous state; 0 BLOCKED. This
batch's principal finding, like `step6-batch-002`'s, is negative-but-
well-evidenced and traced to a concrete root cause: the daf-6b
`known-needs-reconstruction`/`INVENTED_TEXT` historical flag predates a
completed reconstruction (PR #291) and is stale, not a live defect.
Blind QA (33.3%, full coverage of the flagged daf plus a denser-than-
usual sample elsewhere): 42/42 CONFIRMED_VERIFIED, 0 escalations.
