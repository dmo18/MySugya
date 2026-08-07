# Rashi translation-quality campaign, Step 6 batch 018 report

Batch `step6-batch-018` of the full-corpus review defined in
`docs/reports/rashi-full-corpus-review-strategy.md` (Step 5). Selected as
the next batch per the strategy document's recommended order (position
37, "remaining contiguous order" priority group; prioritization only,
not evidence of defect). Full per-entry evidence lives in
`docs/reports/data/rashi-step6-batch-018-review-records.json` (validated
against the Step 5 contract).

## Batch scope (frozen from the committed batch plan, unmodified)

- **Batch id**: `step6-batch-018`
- **Perek**: 4
- **Daf**: 42b, 43a, 43b, 44a (4 daf)
- **Tier**: `normal`
- **Entries**: 244 (42b=60, 43a=65, 43b=59, 44a=60)
- **Historical-provenance counts** (Step 1): `content-reviewed` 244
  (100%)

This batch carries no `known-needs-reconstruction` or
`known-needs-realignment` flag on any of its four daf. Every daf has its
own dedicated post-squash fix commit(s), predating this session's
review.

Re-generated and re-validated (`generate_rashi_batch_progress.py`,
`generate_rashi_translation_inventory.py --check`) at the start of this
batch against current main to confirm the batch manifest entry is
unmodified and still selects exactly these 244 entries, that all 244
were still UNREVIEWED, and that they were assigned only to
`step6-batch-018` (0 overlap with any other batch). A fresh review
packet (`generate_rashi_review_packets.py --batch-id step6-batch-018`)
was generated and used as the basis for review. No entry outside the
batch was edited. All 244 entries have a non-empty `he` field.

## Method

All 244 entries were read individually and independently re-derived
from their own Hebrew (never from the existing English alone),
cross-checked against neighboring entries' Hebrew, linked Gemara/Mishnah
context, the style guide, and the terminology registry.

The inventory's `dafProvenance[<daf>].contentReviewCommits` field was
found to be incomplete for all four daf in this batch (a recurring,
previously-confirmed pattern). Before writing evidence, `git log
--oneline --all | grep -i "yoma <daf>"` was run for each daf to recover
the full set of relevant post-squash fix commits, not just the ones
listed in the inventory field:

```
42b: eaa3b23 Reconstruct Yoma 42b Rashi helpers
     421cd66 Repair Yoma 42b Rashi translations, retiring its repetition-baseline debt
43a: e971bc8 Reconstruct Yoma 43a Rashi helpers
     87193a6 Reconstruct Yoma 43a Rashi translations
43b: 4cc94e5 Reconstruct Yoma 43b Rashi helpers
     3e690fb Reconstruct Yoma 43b Rashi translations
44a: e7efa5b Recover Yoma 44a Rashi helpers
     76255e6 Reconstruct Yoma 44a Rashi helpers
     cfa7ce0 Reconstruct Yoma 44a Rashi translations
```

All commits above were confirmed to predate the `ef58878` cutover
commit and to be individually visible (legitimately post-squash, not
squashed away).

**First pass**: all 244 entries reviewed individually. Result: **244
VERIFIED, 0 MINOR_EDIT, 0 SUBSTANTIVE_REPAIR, 0 RETRANSLATE, 0
DUPLICATION_OR_CONTAMINATION, 0 BLOCKED.**

**Second pass**: not applicable (0 changed entries).

**Blind QA**: a full-coverage sample was used for all 244 entries (not a
subsample), each independently re-derived from the raw Hebrew a second
time in a separate pass, deliberately independent of the first-pass
reasoning and the per-daf fix-commit lookups. Result: **244/244
CONFIRMED_VERIFIED, 0 escalations.**

## Systemic-candidate review

### Family 1: fabricated "New comment:" scaffold text

**0 candidates in this batch.** A corpus-wide check confirms 0
occurrences, consistent with `step6-batch-006` (this session) fully
draining this family from the entire unreviewed corpus.

### Family 2: cross-entry word anticipation

4 candidates in this batch, all daf-boundary fragment stubs:
`rashi-yoma-042b-060` (Hebrew "דאפיק", deferred to 43a),
`rashi-yoma-043a-065` (Hebrew "כיון", deferred to 43b),
`rashi-yoma-043b-059` (Hebrew "יכול", deferred to 44a), and
`rashi-yoma-044a-060` (Hebrew "בקדושה", deferred to 44b, outside this
batch's scope).

Unlike every daf-boundary stub seen in prior batches this session, none
of these four carry this corpus's usual explanatory continuation
framing in their English ("...the daf ends mid-word here; the comment
continues on X"); each has only a bare literal partial translation. To
avoid trusting the FALSE_POSITIVE pattern by inference alone, each was
individually verified by direct cross-daf comparison against the raw
`modules/yoma/learning_data.js` source rather than by pattern-matching:

- `rashi-yoma-042b-060` ("דאפיק" / "who brought out") - confirmed
  `rashi-yoma-043a-001` begins "דאפיק חמור בהדה..." ("Who brought out a
  donkey along with it...") - genuine continuation.
- `rashi-yoma-043a-065` ("כיון" / "since") - confirmed
  `rashi-yoma-043b-001` begins "כיון דאמר כו'..." ("'Since he said,
  etc.'...") - genuine continuation.
- `rashi-yoma-043b-059` ("יכול" / "One might think") - confirmed
  `rashi-yoma-044a-001` begins "יכול אף בכל העזרה..." ("'One might
  think even in the entire courtyard'...") - genuine continuation.
- `rashi-yoma-044a-060` ("בקדושה" / "'In holiness'") - this one
  continues outside the batch scope, into 44b. Located
  `rashi-yoma-044b-001` directly in `modules/yoma/learning_data.js` and
  confirmed it reads `he: "בקדושה. מתן דמים: שם פרישה אחת. כולה חדא
  מעלה"`, `en: "'In holiness' - the giving of blood. 'It is one name of
  separation' - it is all one degree"` - genuine, non-fabricated
  continuation confirmed.

**Disposition: FALSE_POSITIVE for all 4.** Each is a genuine partial
translation of a comment that resumes in full on the following daf, not
a fabrication or corruption. Left unchanged, VERIFIED.

## Other risk-signaled entries (outside both systemic families)

No additional TRUNCATED or WRONG_REFERENT candidates were flagged in
this batch's risk signals beyond those already covered above.

## Aggregate results (244 entries)

| Disposition | Count | Rate |
|---|---|---|
| VERIFIED | 244 | 100.0% |
| MINOR_EDIT | 0 | 0.0% |
| SUBSTANTIVE_REPAIR | 0 | 0.0% |
| RETRANSLATE | 0 | 0.0% |
| DUPLICATION_OR_CONTAMINATION | 0 | 0.0% |
| BLOCKED | 0 | 0.0% |
| **Total** | **244** | **100%** |

**Changed-translation count: 0.** No PR content-diff applies to any
`modules/yoma/assets/learning/yoma/*.learning.json` file for this batch
- only review-records, inventory review-metadata, and documentation
change. No BLOCKED entries and no structural/source-cache blockers were
found anywhere in this batch.

## Regression and platform evidence

- Rashi entry count: 8,854 (unchanged) - Associations: 10,061 declared, 0
  broken, 0 cross-daf (unchanged) - Boundary registry: 20/20 (unchanged)
- Hebrew and English text: byte-unchanged across all 244 entries in this
  batch (0 changes to apply)
- `npm run validate:offline:yoma`, `npm test`, `npm run test:browser`,
  `npm run build`, `npm run check:deploy-html`, `python3
  scripts/worker_pipeline.py verify --full`: all green
- No exhaustive-shard checkpoint due this batch (last triggered after
  the 35th parent batch, `step6-batch-015`, confirmed at commit
  `907ccc1`; next due after the 40th parent batch)

## Status

**Batch 018: COMPLETE.** All 244 entries reviewed with an assigned final
disposition; 0 entries left in an ambiguous state; 0 BLOCKED. This is the
twenty-sixth consecutive batch this session (`002`, `003`, `023`, `024`,
`025`, `026`, `027`, `028`, `029`, `030`, `031`, `033`, `034`, `035`,
`009`, `017`, `007`, `008`, `010`, `011`, `012`, `013`, `014`, `015`,
`016`, `018`) with a fully positive finding (VERIFIED throughout). Blind
QA (100%, full coverage): 244/244 CONFIRMED_VERIFIED, 0 escalations.
