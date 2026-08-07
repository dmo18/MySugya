# Rashi translation-quality campaign, Step 6 batch 036 report

Batch `step6-batch-036` of the full-corpus review defined in
`docs/reports/rashi-full-corpus-review-strategy.md` (Step 5). Selected as
the next batch per the strategy document's recommended order (position
41, "remaining contiguous order" priority group; prioritization only,
not evidence of defect). Full per-entry evidence lives in
`docs/reports/data/rashi-step6-batch-036-review-records.json` (validated
against the Step 5 contract).

**This is the final batch of the Step 6 full-corpus Rashi translation
review.** Its completion brings the entire 8,854-entry corpus to 0
UNREVIEWED.

## Batch scope (frozen from the committed batch plan, unmodified)

- **Batch id**: `step6-batch-036`
- **Perek**: 8
- **Daf**: 74a, 74b, 75a, 75b, 76a, 76b (6 daf)
- **Tier**: `normal`
- **Entries**: 283 (74a=55, 74b=42, 75a=49, 75b=46, 76a=47, 76b=44)
- **Historical-provenance counts** (Step 1): `content-reviewed` 283
  (100%)

This batch carries no `known-needs-reconstruction` or
`known-needs-realignment` flag on any of its six daf.

Re-generated and re-validated (`generate_rashi_batch_progress.py`,
`generate_rashi_translation_inventory.py --check`) at the start of this
batch against current main to confirm the batch manifest entry is
unmodified and still selects exactly these 283 entries, that all 283
were still UNREVIEWED, and that they were assigned only to
`step6-batch-036` (0 overlap with any other batch). A fresh review
packet (`generate_rashi_review_packets.py --batch-id step6-batch-036`)
was generated and used as the basis for review. No entry outside the
batch was edited. All 283 entries have a non-empty `he` field.

## Method

All 283 entries were read individually and independently re-derived
from their own Hebrew (never from the existing English alone),
cross-checked against neighboring entries' Hebrew, linked Gemara/Mishnah
context, the style guide, and the terminology registry.

**Provenance discrepancy found and corrected in this batch's evidence:**
unlike every prior batch this session, the inventory's
`dafProvenance[<daf>]` field for all six daf in this batch claimed
`postSquashCommitCount: 0`, `contentReviewCommits: []`, and
`provenanceSource: "...pre-squash batch review, not independently
git-verifiable (repo history squashed at commit 655b973)"`. This claim
was checked and found to be inaccurate: `git log --oneline --all | grep
-i "yoma <daf>"` recovered a genuine, dated post-squash fix commit for
every one of the six daf, all well after the `655b973` squash point and
all predating this review session's start (`13ce837`, 2026-08-02,
batch-001):

```
74a: 121db53 Reconstruct Yoma 74a Rashi translations (#220)
74b: de12c24 Reconstruct Yoma 74b Rashi translations (#221)
75a: 55b1f47 Reconstruct Yoma 75a Rashi translations (#222)
75b: 25aa42d Reconstruct Yoma 75b Rashi translations (#223)
76a: 0a73f05 Reconstruct Yoma 76a Rashi translations (#224)
76b: e19a860 Yoma 76b: full Rashi reconstruction (44 entries)
```

Each commit's discovery and date are recorded per-entry in this batch's
review records. The `dafProvenance` field itself is generator-owned
(derived from `docs/rashi-audit-backlog.md`'s coverage map) and was not
hand-edited; this report and the review records document the correction
for the historical audit trail.

**First pass**: all 283 entries reviewed individually. Result: **283
VERIFIED, 0 MINOR_EDIT, 0 SUBSTANTIVE_REPAIR, 0 RETRANSLATE, 0
DUPLICATION_OR_CONTAMINATION, 0 BLOCKED.**

**Second pass**: not applicable (0 changed entries).

**Blind QA**: a full-coverage sample was used for all 283 entries (not a
subsample), each independently re-derived from the raw Hebrew a second
time in a separate pass, deliberately independent of the first-pass
reasoning and the git-log commit lookups. Result: **283/283
CONFIRMED_VERIFIED, 0 escalations.**

## Systemic-candidate review

### Family 1: fabricated "New comment:" scaffold text

**0 candidates in this batch.** A corpus-wide check confirms 0
occurrences, consistent with `step6-batch-006` (this session) fully
draining this family from the entire unreviewed corpus.

### Family 2: cross-entry word anticipation

6 candidates in this batch, all daf-boundary fragment stubs, every one
carrying this corpus's standard explanatory continuation framing (a
return to the pattern seen throughout the session prior to the
`step6-batch-018` bare-fragment anomaly):

- `rashi-yoma-074a-055` (Hebrew "אתא" / "'The verse comes'") - confirmed
  `rashi-yoma-074b-001` begins "אתא קרא לרבויי ספיקא..." - genuine
  continuation, verified within this batch's own dump.
- `rashi-yoma-074b-042` (Hebrew "עינו" / "'His eye'") - confirmed
  `rashi-yoma-075a-001` begins "עינו בכוסו..." - genuine continuation,
  verified within this batch's own dump.
- `rashi-yoma-075a-049` (Hebrew "לחם" / "'Bread'") - confirmed
  `rashi-yoma-075b-001` begins "לחם ששאלו כהוגן..." - genuine
  continuation, verified within this batch's own dump.
- `rashi-yoma-075b-046` (Hebrew "זה" / "'This'") - confirmed
  `rashi-yoma-076a-001` begins "זה יהושע..." - genuine continuation,
  verified within this batch's own dump.
- `rashi-yoma-076a-047` (Hebrew "חייב" / "'Liable'") - confirmed
  `rashi-yoma-076b-001` begins "חייב. משום שכר אל תשת..." - genuine
  continuation, verified within this batch's own dump.
- `rashi-yoma-076b-044` (Hebrew "לבוש" / "'Clothed'") - this one
  continues outside the batch scope, into 77a. Located
  `rashi-yoma-077a-001` directly in `modules/yoma/learning_data.js`
  (line 178374) and confirmed it reads `he: "לבוש הבדים. הוא גבריאל
  בספר דניאל..."`, `en: "'clothed in linen' - this is Gabriel, in the
  book of Daniel..."` - genuine, non-fabricated continuation confirmed.

**Disposition: FALSE_POSITIVE for all 6.** Each is a genuine partial
translation of a comment that resumes in full on the following daf, not
a fabrication or corruption. Left unchanged, VERIFIED.

## Other risk-signaled entries (outside both systemic families)

No additional TRUNCATED or WRONG_REFERENT candidates were flagged in
this batch's risk signals beyond those already covered above.

## Aggregate results (283 entries)

| Disposition | Count | Rate |
|---|---|---|
| VERIFIED | 283 | 100.0% |
| MINOR_EDIT | 0 | 0.0% |
| SUBSTANTIVE_REPAIR | 0 | 0.0% |
| RETRANSLATE | 0 | 0.0% |
| DUPLICATION_OR_CONTAMINATION | 0 | 0.0% |
| BLOCKED | 0 | 0.0% |
| **Total** | **283** | **100%** |

**Changed-translation count: 0.** No PR content-diff applies to any
`modules/yoma/assets/learning/yoma/*.learning.json` file for this batch
- only review-records, inventory review-metadata, and documentation
change. No BLOCKED entries and no structural/source-cache blockers were
found anywhere in this batch.

## Regression and platform evidence

- Rashi entry count: 8,854 (unchanged) - Associations: 10,061 declared, 0
  broken, 0 cross-daf (unchanged) - Boundary registry: 20/20 (unchanged)
- Hebrew and English text: byte-unchanged across all 283 entries in this
  batch (0 changes to apply)
- `npm run validate:offline:yoma`, `npm test`, `npm run test:browser`,
  `npm run build`, `npm run check:deploy-html`, `python3
  scripts/worker_pipeline.py verify --full`: all green
- Exhaustive 8-shard browser checkpoint dispatched after the 40th parent
  batch (`step6-batch-032`) merged, per the established cadence (last
  triggered at the 35th parent batch, `step6-batch-015`). Confirmed at
  commit `26a4c73` (the step6-batch-032 merge commit): **173/173 daf,
  8,854 entries, 215 passed, 0 failed, 8 shards.**

## Status

**Batch 036: COMPLETE.** All 283 entries reviewed with an assigned final
disposition; 0 entries left in an ambiguous state; 0 BLOCKED. This is the
thirtieth consecutive batch this session (`002`, `003`, `023`, `024`,
`025`, `026`, `027`, `028`, `029`, `030`, `031`, `033`, `034`, `035`,
`009`, `017`, `007`, `008`, `010`, `011`, `012`, `013`, `014`, `015`,
`016`, `018`, `019`, `020`, `032`, `036`) with a fully positive finding
(VERIFIED throughout). Blind QA (100%, full coverage): 283/283
CONFIRMED_VERIFIED, 0 escalations.

**This is the 41st and final parent batch of the Step 6 full-corpus
Rashi translation review.** Once this batch merges, 0 entries remain
UNREVIEWED across the entire 8,854-entry corpus, and the campaign
proceeds to final reconciliation and the terminal report per the
governing campaign directive.
