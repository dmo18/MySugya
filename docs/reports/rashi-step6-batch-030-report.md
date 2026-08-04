# Rashi translation-quality campaign, Step 6 batch 030 report

Batch `step6-batch-030` of the full-corpus review defined in
`docs/reports/rashi-full-corpus-review-strategy.md` (Step 5). Selected as
the next batch per the strategy document's recommended order (position
20, high-risk (dense) priority group; prioritization only, not evidence
of defect). Full per-entry evidence lives in
`docs/reports/data/rashi-step6-batch-030-review-records.json` (validated
against the Step 5 contract).

## Batch scope (frozen from the committed batch plan, unmodified)

- **Batch id**: `step6-batch-030`
- **Perek**: 6
- **Daf**: 64b, 65a, 65b (3 daf)
- **Tier**: `dense`
- **Entries**: 150 (64b=42, 65a=71, 65b=37)
- **Historical-provenance counts** (Step 1): `known-needs-reconstruction`
  150 (100%)

An older `docs/rashi-audit-backlog.md` note additionally claimed 65a and
65b "have no `he` field at all (unbuilt)." This was checked directly
against the live inventory before starting review, since an unbuilt `he`
field would be a genuine structural blocker requiring the TRUE STOP
CONDITIONS protocol rather than a routine translation check: all 150
entries in this batch (and all entries on 64b/65a/65b generally) have a
non-empty `he` field. The note is simply stale documentation that
predates a later build, the same pattern as the stale reconstruction
flags addressed elsewhere in this report - not a live blocker.

Re-generated and re-validated (`generate_rashi_batch_progress.py`,
`generate_rashi_translation_inventory.py --check`) at the start of this
batch against current main to confirm the batch manifest entry is
unmodified and still selects exactly these 150 entries, that all 150
were still UNREVIEWED, and that they were assigned only to
`step6-batch-030` (0 overlap with any other batch). A fresh review
packet (`generate_rashi_review_packets.py --batch-id step6-batch-030`)
was generated and used as the basis for review. No entry outside the
batch was edited.

## Method and key finding: the "needs-reconstruction" flags are stale for all three affected daf

Following the `step6-batch-003`/`023`/`024`/`025`/`026`/`027`/`028`/`029`
precedent, `git log --oneline --all -- modules/yoma/assets/learning/yoma/<daf>.learning.json`
was checked for every daf in this batch **before** reading the flagged
entries at face value:

```
64b: fbe5a22 Yoma 64b: full Rashi reconstruction (44 entries) (#312)
65a: ce25b6a Yoma 65a: full Rashi reconstruction (73 entries) (#313)
65b: b6a3253 Yoma 65b: full Rashi reconstruction (39 entries) (#314)
```

65a additionally received a later semantic-review pass
(`docs/reports/rashi-pilot-batch-4-report.md`, PR #399) that corrected a
two-entry content-swap pair (065a-001/065a-002); those two entries are
already `REVIEWED` and excluded from this batch's 71 65a entries.

All three daf in this batch were already fully reconstructed, well
before the VERSION 15.293 Wave 1 audit whose finding the current Step 2
risk-signal generator and batch-planning `known-needs-reconstruction`
provenance bucket still cite. As with the eight prior stale-flag batches
this session, the classification metadata was never refreshed to reflect
that the underlying content problem had already been fixed.

All 150 entries were nonetheless read individually and independently
re-derived from their own Hebrew (never from the existing English
alone), cross-checked against neighboring entries' Hebrew, linked
Gemara/Mishnah context, the style guide, and the terminology registry.
Every one of the 150 flagged entries was individually confirmed to be a
faithful, specific, non-generic translation of its own Hebrew line - not
filler, not fabricated, and not shifted from a neighbor.

**First pass**: all 150 entries reviewed individually. Result: **150
VERIFIED, 0 MINOR_EDIT, 0 SUBSTANTIVE_REPAIR, 0 RETRANSLATE, 0
DUPLICATION_OR_CONTAMINATION, 0 BLOCKED.**

**Second pass**: not applicable (0 changed entries).

**Blind QA**: given this batch's 100% known-needs-reconstruction
concentration, a full-coverage sample was used for all 150 entries (not
a subsample), each independently re-derived from the raw Hebrew a
second time in a separate pass, deliberately independent of the
first-pass reasoning and the PR #312/#313/#314 history lookups. Result:
**150/150 CONFIRMED_VERIFIED, 0 escalations.**

## Systemic-candidate review

### Family 1: fabricated "New comment:" scaffold text

**0 candidates in this batch.** A corpus-wide check confirms 0
occurrences, consistent with `step6-batch-006` (this session) fully
draining this family from the entire unreviewed corpus.

### Family 2: cross-entry word anticipation

3 candidates in this batch, all daf-boundary single-word/fragment
stubs: `rashi-yoma-064b-044` (Hebrew "אלא", deferred to 65a),
`rashi-yoma-065a-073` (Hebrew "קרבנות", deferred to 65b), and
`rashi-yoma-065b-039` (Hebrew "ואם", deferred to 66a). **Disposition:
FALSE_POSITIVE for all 3.** Same low-precision OVEREXPLAINED
length-ratio trigger already confirmed throughout this session. Left
unchanged, VERIFIED.

## Other risk-signaled entries (outside both systemic families)

- **TRUNCATED** (2 entries: `064b-014`, `065a-023`, `065a-024`,
  `065b-033`): all confirmed **FALSE_POSITIVE** - each ends mid-clause
  on a function word because this corpus splits Rashi comments across
  Vilna-line entries, and the immediately following vilnaLine entry
  completes the clause in every case (verified individually).
- **WRONG_REFERENT** (2 entries: `065a-032`, `065b-025`): pronoun
  referents checked against established local context (the challenge
  raised at `065a-031` for the first; the sin-offering subject
  established at `065b-024` for the second). Both resolve correctly.

All are VERIFIED.

## Aggregate results (150 entries)

| Disposition | Count | Rate |
|---|---|---|
| VERIFIED | 150 | 100.0% |
| MINOR_EDIT | 0 | 0.0% |
| SUBSTANTIVE_REPAIR | 0 | 0.0% |
| RETRANSLATE | 0 | 0.0% |
| DUPLICATION_OR_CONTAMINATION | 0 | 0.0% |
| BLOCKED | 0 | 0.0% |
| **Total** | **150** | **100%** |

**Changed-translation count: 0.** No PR content-diff applies to any
`modules/yoma/assets/learning/yoma/*.learning.json` file for this batch
- only review-records, inventory review-metadata, and documentation
change. No BLOCKED entries and no structural/source-cache blockers were
found anywhere in this batch.

## Regression and platform evidence

- Rashi entry count: 8,854 (unchanged) - Associations: 10,061 declared, 0
  broken, 0 cross-daf (unchanged) - Boundary registry: 20/20 (unchanged)
- Hebrew and English text: byte-unchanged across all 150 entries in this
  batch (0 changes to apply)
- `npm run validate:offline:yoma`, `npm test`, `npm run test:browser`,
  `npm run build`, `npm run check:deploy-html`, `python3
  scripts/worker_pipeline.py verify --full`: all green
- 20th-parent-batch checkpoint (triggered by `step6-batch-029`'s merge,
  the batch immediately preceding this one): exhaustive 8-shard browser
  workflow confirmed 173/173 daf, 8,854 entries, 215 passed, 0 failed at
  commit `4ba5c487`; deploy confirmed green at the same commit

## Status

**Batch 030: COMPLETE.** All 150 entries reviewed with an assigned final
disposition; 0 entries left in an ambiguous state; 0 BLOCKED. This is
the tenth consecutive batch this session (`002`, `003`, `023`, `024`,
`025`, `026`, `027`, `028`, `029`, `030`) whose principal finding is
negative-but-well-evidenced and traced to a concrete root cause:
historical-defect flags all predate completed repair PRs and are stale,
not live defects. Blind QA (100%, full coverage): 150/150
CONFIRMED_VERIFIED, 0 escalations.
