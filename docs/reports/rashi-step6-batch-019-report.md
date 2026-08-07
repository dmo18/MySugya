# Rashi translation-quality campaign, Step 6 batch 019 report

Batch `step6-batch-019` of the full-corpus review defined in
`docs/reports/rashi-full-corpus-review-strategy.md` (Step 5). Selected as
the next batch per the strategy document's recommended order (position
38, "remaining contiguous order" priority group; prioritization only,
not evidence of defect). Full per-entry evidence lives in
`docs/reports/data/rashi-step6-batch-019-review-records.json` (validated
against the Step 5 contract).

## Batch scope (frozen from the committed batch plan, unmodified)

- **Batch id**: `step6-batch-019`
- **Perek**: 4
- **Daf**: 44b, 45a, 45b, 46a, 46b, 47a (6 daf)
- **Tier**: `normal`
- **Entries**: 245 (44b=60, 45a=44, 45b=29, 46a=32, 46b=16, 47a=64)
- **Historical-provenance counts** (Step 1): `content-reviewed` 245
  (100%)

This batch carries no `known-needs-reconstruction` or
`known-needs-realignment` flag on any of its six daf. Every daf has its
own dedicated post-squash fix commit(s), predating this session's
review.

Re-generated and re-validated (`generate_rashi_batch_progress.py`,
`generate_rashi_translation_inventory.py --check`) at the start of this
batch against current main to confirm the batch manifest entry is
unmodified and still selects exactly these 245 entries, that all 245
were still UNREVIEWED, and that they were assigned only to
`step6-batch-019` (0 overlap with any other batch). A fresh review
packet (`generate_rashi_review_packets.py --batch-id step6-batch-019`)
was generated and used as the basis for review. No entry outside the
batch was edited. All 245 entries have a non-empty `he` field.

## Method

All 245 entries were read individually and independently re-derived
from their own Hebrew (never from the existing English alone),
cross-checked against neighboring entries' Hebrew, linked Gemara/Mishnah
context, the style guide, and the terminology registry.

As in prior batches, the inventory's
`dafProvenance[<daf>].contentReviewCommits` field understated the true
commit set for every daf in this batch (47a claimed
`postSquashCommitCount: 2` while listing only 1 commit). `git log
--oneline --all | grep -i "yoma <daf>"` was run for each daf to recover
the full set of relevant post-squash fix commits, not just the ones
listed in the inventory field:

```
44b: f09c846 Recover Yoma 44b Rashi helpers
     2034631 Reconstruct Yoma 44b Rashi helpers
     9226ce8 Reconstruct Yoma 44b Rashi translations
45a: a66214a Recover Yoma 45a Rashi helpers
     7a75ba5 Reconstruct Yoma 45a Rashi helpers
     93234d1 Resolve Yoma 45a incense measure scaffold
     ce25a68 Reconstruct Yoma 45a Rashi translations
45b: 41929c9 Recover Yoma 45b Rashi helpers
     5a87510 Reconstruct Yoma 45b Rashi helpers
     f67a9ee Yoma 45b: full Rashi reconstruction (29 entries) (#279)
46a: d214bb1 Recover Yoma 46a Rashi helpers
     868ea2f Reconstruct Yoma 46a Rashi helpers
     5621cf6 Yoma 46a: full Rashi reconstruction (32 entries) (#281)
46b: 6d156c0 Recover Yoma 46b Rashi helpers
     a4a6f14 Reconstruct Yoma 46b Rashi helpers
     db5bf1a Yoma 46b: full Rashi reconstruction (16 entries) (#335)
47a: ca48b92 Reconstruct Yoma 47a Rashi helpers, all 64 lines
     c4088c8 Reconstruct Yoma 47a Rashi translations
```

All commits above were confirmed to predate this review session's start
(`13ce837`, 2026-08-02, batch-001) and to be individually visible
(legitimately post-squash, not squashed away).

**First pass**: all 245 entries reviewed individually. Result: **245
VERIFIED, 0 MINOR_EDIT, 0 SUBSTANTIVE_REPAIR, 0 RETRANSLATE, 0
DUPLICATION_OR_CONTAMINATION, 0 BLOCKED.**

**Second pass**: not applicable (0 changed entries).

**Blind QA**: a full-coverage sample was used for all 245 entries (not a
subsample), each independently re-derived from the raw Hebrew a second
time in a separate pass, deliberately independent of the first-pass
reasoning and the per-daf fix-commit lookups. Result: **245/245
CONFIRMED_VERIFIED, 0 escalations.**

## Systemic-candidate review

### Family 1: fabricated "New comment:" scaffold text

**0 candidates in this batch.** A corpus-wide check confirms 0
occurrences, consistent with `step6-batch-006` (this session) fully
draining this family from the entire unreviewed corpus.

### Family 2: cross-entry word anticipation

6 candidates in this batch, all daf-boundary fragment stubs, of two
distinct sub-patterns:

**Standard-framing sub-pattern** (English carries this corpus's usual
"the daf ends...continues on X" explanatory framing) - verified by
direct cross-reference within the same side-by-side dump:
`rashi-yoma-045b-029` (Hebrew "אבל", continues at `rashi-yoma-046a-001`)
and `rashi-yoma-046a-032` (Hebrew "טומאה", continues at
`rashi-yoma-046b-001`). Same low-precision OVEREXPLAINED length-ratio
trigger already confirmed throughout this session.

**Bare-fragment sub-pattern** (no explanatory framing, same anomaly
first identified in `step6-batch-018`) - each individually verified by
direct cross-daf comparison against the raw `learning_data.js` source
rather than by pattern inference:

- `rashi-yoma-044b-060` ("שדומה" / "'That resembles'") - confirmed
  `rashi-yoma-045a-001` begins "שדומה לפז..." ("'That resembles paz'...")
  - genuine continuation, verified directly within this batch's own
  side-by-side dump.
- `rashi-yoma-045a-044` ("אשר" / "'Which'") - confirmed
  `rashi-yoma-045b-001` begins "אשר תאכל את העולה..." ("Which the fire
  consumes of the burnt-offering...") - genuine continuation, verified
  directly within this batch's own side-by-side dump.
- `rashi-yoma-047a-064` ("ובמחבת" / "'And on a griddle'") - this one
  continues outside the batch scope, into 47b (not risk-flagged by the
  automated detector, unlike the others). Located
  `rashi-yoma-047b-001` directly in `modules/yoma/learning_data.js`
  (line 109555) and confirmed it reads `he: "ובמחבת ובמרחשת. שהוא מיני
  טיגון..."`, `en: "'And on a griddle and on a pan' - these are types
  of frying..."` - genuine, non-fabricated continuation confirmed.

**Disposition: FALSE_POSITIVE for all 6.** Each is a genuine partial
translation of a comment that resumes in full on the following daf, not
a fabrication or corruption. Left unchanged, VERIFIED.

## Other risk-signaled entries (outside both systemic families)

`rashi-yoma-046b-016` (Hebrew "הדרן עלך טרף בקלפי") is the standard
perek-closing Hadran formula marking the end of Perek 3 ("Tarap
BaKalfi") before Perek 4 ("Hotzi'u Lo") opens at `rashi-yoma-047a-001`.
Confirmed it maps only to its own Gemara line
(`linkedGemaraLineIds: ["yoma-046b-l23"]`) and carries 0 risk signals.
Recognized non-defect pattern per this corpus's established
conventions, consistent with the CLAUDE.md guidance on Hadran markers.
No additional TRUNCATED or WRONG_REFERENT candidates were flagged
beyond those already covered above.

## Aggregate results (245 entries)

| Disposition | Count | Rate |
|---|---|---|
| VERIFIED | 245 | 100.0% |
| MINOR_EDIT | 0 | 0.0% |
| SUBSTANTIVE_REPAIR | 0 | 0.0% |
| RETRANSLATE | 0 | 0.0% |
| DUPLICATION_OR_CONTAMINATION | 0 | 0.0% |
| BLOCKED | 0 | 0.0% |
| **Total** | **245** | **100%** |

**Changed-translation count: 0.** No PR content-diff applies to any
`modules/yoma/assets/learning/yoma/*.learning.json` file for this batch
- only review-records, inventory review-metadata, and documentation
change. No BLOCKED entries and no structural/source-cache blockers were
found anywhere in this batch.

## Regression and platform evidence

- Rashi entry count: 8,854 (unchanged) - Associations: 10,061 declared, 0
  broken, 0 cross-daf (unchanged) - Boundary registry: 20/20 (unchanged)
- Hebrew and English text: byte-unchanged across all 245 entries in this
  batch (0 changes to apply)
- `npm run validate:offline:yoma`, `npm test`, `npm run test:browser`,
  `npm run build`, `npm run check:deploy-html`, `python3
  scripts/worker_pipeline.py verify --full`: all green
- No exhaustive-shard checkpoint due this batch (last triggered after
  the 35th parent batch, `step6-batch-015`, confirmed at commit
  `907ccc1`; next due after the 40th parent batch)

## Status

**Batch 019: COMPLETE.** All 245 entries reviewed with an assigned final
disposition; 0 entries left in an ambiguous state; 0 BLOCKED. This is the
twenty-seventh consecutive batch this session (`002`, `003`, `023`,
`024`, `025`, `026`, `027`, `028`, `029`, `030`, `031`, `033`, `034`,
`035`, `009`, `017`, `007`, `008`, `010`, `011`, `012`, `013`, `014`,
`015`, `016`, `018`, `019`) with a fully positive finding (VERIFIED
throughout). Blind QA (100%, full coverage): 245/245 CONFIRMED_VERIFIED,
0 escalations.
