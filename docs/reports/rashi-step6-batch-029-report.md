# Rashi translation-quality campaign, Step 6 batch 029 report

Batch `step6-batch-029` of the full-corpus review defined in
`docs/reports/rashi-full-corpus-review-strategy.md` (Step 5). Selected as
the next batch per the strategy document's recommended order (position
19, high-risk (dense) priority group; prioritization only, not evidence
of defect). Full per-entry evidence lives in
`docs/reports/data/rashi-step6-batch-029-review-records.json` (validated
against the Step 5 contract).

## Batch scope (frozen from the committed batch plan, unmodified)

- **Batch id**: `step6-batch-029`
- **Perek**: 6
- **Daf**: 63a, 63b, 64a (3 daf)
- **Tier**: `dense`
- **Entries**: 147 (63a=57, 63b=54, 64a=36)
- **Historical-provenance counts** (Step 1): `known-needs-reconstruction`
  93 (63a, 64a), `known-needs-realignment` 54 (63b)

This batch is the first this session to contain a `known-needs-
realignment` daf (63b) rather than exclusively `known-needs-
reconstruction` daf. The two flags describe different historical-defect
shapes: reconstruction-flagged daf were claimed to have wholesale
fabricated/generic `en` text; realignment-flagged daf were claimed to
have a narrower, more insidious defect where `en` is present and fluent
but systematically translates an *adjacent* line's Hebrew instead of
its own.

Re-generated and re-validated (`generate_rashi_batch_progress.py`,
`generate_rashi_translation_inventory.py --check`) at the start of this
batch against current main to confirm the batch manifest entry is
unmodified and still selects exactly these 147 entries, that all 147
were still UNREVIEWED, and that they were assigned only to
`step6-batch-029` (0 overlap with any other batch). A fresh review
packet (`generate_rashi_review_packets.py --batch-id step6-batch-029`)
was generated and used as the basis for review. No entry outside the
batch was edited.

## Method: two different verification paths for two different flag types

### 63a and 64a (known-needs-reconstruction): the now-established stale-flag check

Following the `step6-batch-003`/`023`/`024`/`025`/`026`/`027`/`028`
precedent, `git log --oneline --all -- modules/yoma/assets/learning/yoma/<daf>.learning.json`
was checked for both daf **before** reading the flagged entries at face
value:

```
63a: 5341db2 Yoma 63a: full Rashi reconstruction (59 entries) (#309)
64a: c5b5d2c Yoma 64a: full Rashi reconstruction (38 entries) (#311)
```

Both daf were already fully reconstructed, well before the VERSION
15.293 Wave 1 audit whose finding the `known-needs-reconstruction`
provenance bucket still cites. Same stale-classification pattern as the
eight prior batches this session.

### 63b (known-needs-realignment): a genuinely different check, not a rubber stamp

63b has **no post-reconstruction fix commit** in its git history (`git
log` shows only the daf's original "full Rashi reconstruction (56
entries)" commit) - unlike the reconstruction-flagged daf, staleness
here cannot be inferred from a later repair PR. Two independent prior
signals bear on this specific daf, both discovered before reading any
entry:

- `docs/rashi-audit-backlog.md` lists 63b as `Needs realignment
  (partial)` - meaning only *some* of 63b's entries were already
  checked, not the whole daf.
- `docs/reports/rashi-pilot-batch-4-report.md` (an earlier phase of
  this campaign, before this session's Step 6 batches) already reviewed
  a different subset of 63b's entries and reported: "This batch
  reviewed several entries on daf 63b (`needs realignment`) and found
  both entries faithful (another two false positives for that
  daf-level flag, adding to batch 1's finding)."

Because this batch's 54 63b entries are ones the pilot never touched
(pilot-reviewed entries are already `REVIEWED` and excluded from batch
selection), the pilot's finding does not itself clear these specific
entries. Each of the 54 entries was therefore read with the specific
defect shape in mind - checking whether its English corresponds to a
*neighboring* entry's Hebrew rather than its own - not just checked for
general fluency. Every entry's English was traced against its own
Hebrew and confirmed to match, including the corpus's normal same-entry
mid-clause continuation into the following vilnaLine (the same
line-splitting convention seen throughout Yoma); no case was found
where an entry's English content actually belonged to an adjacent
entry's Hebrew.

**First pass**: all 147 entries reviewed individually. Result: **147
VERIFIED, 0 MINOR_EDIT, 0 SUBSTANTIVE_REPAIR, 0 RETRANSLATE, 0
DUPLICATION_OR_CONTAMINATION, 0 BLOCKED.**

**Second pass**: not applicable (0 changed entries).

**Blind QA**: given this batch's mixed and partly novel provenance -
the first CONTEXT_MISMATCH/realignment flag encountered this session -
a full-coverage sample was used for all 147 entries (not a subsample),
each independently re-derived from the raw Hebrew a second time in a
separate pass, deliberately independent of the first-pass reasoning.
For the 54 63b entries specifically, the second pass re-applied the
same adjacent-line check independently. Result: **147/147
CONFIRMED_VERIFIED, 0 escalations.**

## Systemic-candidate review

### Family 1: fabricated "New comment:" scaffold text

**0 candidates in this batch.** A corpus-wide check confirms 0
occurrences, consistent with `step6-batch-006` (this session) fully
draining this family from the entire unreviewed corpus.

### Family 2: cross-entry word anticipation

3 candidates in this batch, all daf-boundary single-word/fragment
stubs: `rashi-yoma-063a-059` (Hebrew "אי", deferred to 63b),
`rashi-yoma-063b-056` (Hebrew "רבא", deferred to 64a), and
`rashi-yoma-064a-038` (Hebrew "יתקיים", deferred to 64b). **Disposition:
FALSE_POSITIVE for all 3.** Same low-precision OVEREXPLAINED
length-ratio trigger already confirmed throughout this session. Left
unchanged, VERIFIED.

## Other risk-signaled entries (outside both systemic families)

**TRUNCATED** (5 entries: `063a-011`, `063a-028`, `063a-051`,
`063b-008`, `063b-012`, `063b-020`, `063b-048`, `064a-003`, `064a-004`,
`064a-020`): all confirmed **FALSE_POSITIVE** - each ends mid-clause on
a function word because this corpus splits Rashi comments across
Vilna-line entries, and the immediately following vilnaLine entry
completes the clause in every case (verified individually). All are
VERIFIED.

## Aggregate results (147 entries)

| Disposition | Count | Rate |
|---|---|---|
| VERIFIED | 147 | 100.0% |
| MINOR_EDIT | 0 | 0.0% |
| SUBSTANTIVE_REPAIR | 0 | 0.0% |
| RETRANSLATE | 0 | 0.0% |
| DUPLICATION_OR_CONTAMINATION | 0 | 0.0% |
| BLOCKED | 0 | 0.0% |
| **Total** | **147** | **100%** |

**Changed-translation count: 0.** No PR content-diff applies to any
`modules/yoma/assets/learning/yoma/*.learning.json` file for this batch
- only review-records, inventory review-metadata, and documentation
change. No BLOCKED entries and no structural/source-cache blockers were
found anywhere in this batch.

## Regression and platform evidence

- Rashi entry count: 8,854 (unchanged) - Associations: 10,061 declared, 0
  broken, 0 cross-daf (unchanged) - Boundary registry: 20/20 (unchanged)
- Hebrew and English text: byte-unchanged across all 147 entries in this
  batch (0 changes to apply)
- `npm run validate:offline:yoma`, `npm test`, `npm run test:browser`,
  `npm run build`, `npm run check:deploy-html`, `python3
  scripts/worker_pipeline.py verify --full`: all green

## Status

**Batch 029: COMPLETE.** All 147 entries reviewed with an assigned final
disposition; 0 entries left in an ambiguous state; 0 BLOCKED. This
batch confirms two distinct historical-defect flags are both stale for
their respective daf: `known-needs-reconstruction` for 63a/64a (the
ninth confirmation of this pattern this session, following batches 002,
003, 023, 024, 025, 026, 027, 028) and, independently, `known-needs-
realignment` for 63b - the first time this session that flag type was
checked against fresh (never-before-reviewed) entries, and it likewise
came back clean, consistent with the earlier pilot's finding on a
different subset of the same daf. Blind QA (100%, full coverage):
147/147 CONFIRMED_VERIFIED, 0 escalations.
