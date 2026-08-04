# Rashi translation-quality campaign, Step 6 batch 031 report

Batch `step6-batch-031` of the full-corpus review defined in
`docs/reports/rashi-full-corpus-review-strategy.md` (Step 5). Selected as
the next batch per the strategy document's recommended order (position
21, high-risk (dense) priority group; prioritization only, not evidence
of defect). Full per-entry evidence lives in
`docs/reports/data/rashi-step6-batch-031-review-records.json` (validated
against the Step 5 contract).

## Batch scope (frozen from the committed batch plan, unmodified)

- **Batch id**: `step6-batch-031`
- **Perek**: 6/7
- **Daf**: 66a, 66b, 67a (3 daf)
- **Tier**: `dense`
- **Entries**: 180 (66a=52, 66b=65, 67a=63)
- **Historical-provenance counts** (Step 1): `known-needs-reconstruction`
  117 (66a+66b), `known-needs-realignment` 63 (67a)

This is the first batch this session with a mixed reconstruction +
realignment provenance split across daf, and the second time a
`known-needs-realignment` / CONTEXT_MISMATCH daf-level flag has been
reviewed (after daf 63b in `step6-batch-029`).

An older `docs/rashi-audit-backlog.md` note additionally claimed 66a and
66b "have no `he` field at all (unbuilt)," the same claim previously made
(and confirmed stale) for 65a/65b in `step6-batch-030`. This was checked
directly against the live inventory before starting review, since an
unbuilt `he` field would be a genuine structural blocker requiring the
TRUE STOP CONDITIONS protocol rather than a routine translation check:
all 180 entries in this batch have a non-empty `he` field. The note is
stale documentation predating a later build, not a live blocker.

Re-generated and re-validated (`generate_rashi_batch_progress.py`,
`generate_rashi_translation_inventory.py --check`) at the start of this
batch against current main to confirm the batch manifest entry is
unmodified and still selects exactly these 180 entries, that all 180
were still UNREVIEWED, and that they were assigned only to
`step6-batch-031` (0 overlap with any other batch). A fresh review
packet (`generate_rashi_review_packets.py --batch-id step6-batch-031`)
was generated and used as the basis for review. No entry outside the
batch was edited.

## Method

### 66a/66b: reconstruction-flag staleness via git history

Following the `step6-batch-003`/`023`/`024`/`025`/`026`/`027`/`028`/`029`/`030`
precedent, `git log --oneline --all -- modules/yoma/assets/learning/yoma/<daf>.learning.json`
was checked for both reconstruction-flagged daf **before** reading the
flagged entries at face value:

```
66a: 411e871 Yoma 66a: full Rashi reconstruction (54 entries) (#315)
66b: cc8a8a5 Yoma 66b: full Rashi reconstruction (67 entries) (#316)
```

Both daf were already fully reconstructed, well before the VERSION
15.293 Wave 1 audit whose finding the current Step 2 risk-signal
generator and batch-planning `known-needs-reconstruction` provenance
bucket still cite. As with the nine prior stale-flag batches this
session, the classification metadata was never refreshed to reflect that
the underlying content problem had already been fixed.

All 117 entries on 66a/66b were nonetheless read individually and
independently re-derived from their own Hebrew (never from the existing
English alone), cross-checked against neighboring entries' Hebrew,
linked Gemara/Mishnah context, the style guide, and the terminology
registry. Every flagged entry was individually confirmed to be a
faithful, specific, non-generic translation of its own Hebrew line - not
filler, not fabricated, and not shifted from a neighbor.

### 67a: realignment-flag staleness via direct per-entry adjacent-line check

Unlike reconstruction flags, the 67a `known-needs-realignment` flag has
no dedicated post-fix commit in git history (`git log --oneline --all --
modules/yoma/assets/learning/yoma/67a.learning.json` shows only the
original reconstruction commit `7ecce4a` (#317) plus later unrelated
sourceRefs-repair commits `c305534`/`c8f79ec`/`777d1ad`), so staleness
could not be inferred from git alone as it was for 66a/66b. Following the
`step6-batch-029` (daf 63b) precedent, each of the 63 flagged entries was
individually read with specific attention to the described defect shape:
whether the English content actually belongs to a neighboring entry's
Hebrew rather than its own.

`docs/reports/rashi-pilot-batch-4-report.md`'s daf range includes 67a but
does not specifically call out a finding for it (unlike 63b, which was
explicitly named there with "found both entries faithful"), so this is
the first direct verification of the 67a flag specifically, rather than a
confirmation of an existing spot-check.

All 63 entries were checked against their own Hebrew and both immediate
neighbors' Hebrew. In every case the English corresponds to the entry's
own Hebrew line, with only the ordinary same-entry mid-clause
continuation into the next vilnaLine (the corpus convention already
established across this session), never a content swap with an adjacent
entry.

**First pass**: all 180 entries reviewed individually. Result: **180
VERIFIED, 0 MINOR_EDIT, 0 SUBSTANTIVE_REPAIR, 0 RETRANSLATE, 0
DUPLICATION_OR_CONTAMINATION, 0 BLOCKED.**

**Second pass**: not applicable (0 changed entries).

**Blind QA**: given this batch's mixed provenance and the second
realignment-flag daf, a full-coverage sample was used for all 180
entries (not a subsample), each independently re-checked a second time
in a separate pass, deliberately independent of the first-pass reasoning
and (for 66a/66b) the PR #315/#316 history lookups. Result: **180/180
CONFIRMED_VERIFIED, 0 escalations.**

## Systemic-candidate review

### Family 1: fabricated "New comment:" scaffold text

**0 candidates in this batch.** A corpus-wide check confirms 0
occurrences, consistent with `step6-batch-006` (this session) fully
draining this family from the entire unreviewed corpus.

### Family 2: cross-entry word anticipation

3 candidates in this batch, all daf-boundary single-word/fragment stubs:
`rashi-yoma-066a-054` (deferred to 66b), `rashi-yoma-066b-067` (deferred
to 67a), and `rashi-yoma-067a-065` (Hebrew "דכתיב", deferred to 67b,
citing the verse behind the goat's dispatch to the wilderness).
**Disposition: FALSE_POSITIVE for all 3.** Same low-precision
OVEREXPLAINED length-ratio trigger already confirmed throughout this
session. Left unchanged, VERIFIED.

## Other risk-signaled entries (outside both systemic families)

No additional TRUNCATED or WRONG_REFERENT candidates outside the two
provenance families were flagged in this batch's risk signals beyond
those already covered above.

## Aggregate results (180 entries)

| Disposition | Count | Rate |
|---|---|---|
| VERIFIED | 180 | 100.0% |
| MINOR_EDIT | 0 | 0.0% |
| SUBSTANTIVE_REPAIR | 0 | 0.0% |
| RETRANSLATE | 0 | 0.0% |
| DUPLICATION_OR_CONTAMINATION | 0 | 0.0% |
| BLOCKED | 0 | 0.0% |
| **Total** | **180** | **100%** |

**Changed-translation count: 0.** No PR content-diff applies to any
`modules/yoma/assets/learning/yoma/*.learning.json` file for this batch
- only review-records, inventory review-metadata, and documentation
change. No BLOCKED entries and no structural/source-cache blockers were
found anywhere in this batch.

## Regression and platform evidence

- Rashi entry count: 8,854 (unchanged) - Associations: 10,061 declared, 0
  broken, 0 cross-daf (unchanged) - Boundary registry: 20/20 (unchanged)
- Hebrew and English text: byte-unchanged across all 180 entries in this
  batch (0 changes to apply)
- `npm run validate:offline:yoma`, `npm test`, `npm run test:browser`,
  `npm run build`, `npm run check:deploy-html`, `python3
  scripts/worker_pipeline.py verify --full`: all green
- No exhaustive-shard checkpoint due this batch (last triggered at the
  20th parent batch, `step6-batch-029`; next due after the 25th)

## Status

**Batch 031: COMPLETE.** All 180 entries reviewed with an assigned final
disposition; 0 entries left in an ambiguous state; 0 BLOCKED. This is the
eleventh consecutive batch this session (`002`, `003`, `023`, `024`,
`025`, `026`, `027`, `028`, `029`, `030`, `031`) whose principal finding
is negative-but-well-evidenced and traced to a concrete root cause:
historical-defect flags all predate completed repair work (or, for 67a, a
now-completed direct verification) and are stale, not live defects. Blind
QA (100%, full coverage): 180/180 CONFIRMED_VERIFIED, 0 escalations. This
is also the second confirmed-stale `known-needs-realignment` daf this
session, after daf 63b in `step6-batch-029`.
