# Rashi translation-quality campaign, Step 6 batch 027 report

Batch `step6-batch-027` of the full-corpus review defined in
`docs/reports/rashi-full-corpus-review-strategy.md` (Step 5). Selected as
the next batch per the strategy document's recommended order (position
17, high-risk (dense) priority group; prioritization only, not evidence
of defect). Full per-entry evidence lives in
`docs/reports/data/rashi-step6-batch-027-review-records.json` (validated
against the Step 5 contract).

## Batch scope (frozen from the committed batch plan, unmodified)

- **Batch id**: `step6-batch-027`
- **Perek**: 6
- **Daf**: 59b, 60a, 60b, 61a (4 daf)
- **Tier**: `dense`
- **Entries**: 167 (59b=12, 60a=50, 60b=41, 61a=64)
- **Historical-provenance counts** (Step 1): `known-needs-reconstruction`
  103 (61.7%, across 59b/60a/60b), `content-reviewed` 64 (all on 61a)

Unlike the five immediately preceding batches (which were 65-100%
`known-needs-reconstruction`), this batch is mixed: daf 59b, 60a, and
60b carry the familiar stale reconstruction flag, while daf 61a's 64
entries are separately classified `content-reviewed` from a standalone
commit that reconstructed 61a lines 1-45 from raw Hebrew, predating this
session. 19 of 61a's 64 entries (Vilna lines 46-64) additionally fall
within the pre-authorized boundary range documented in
`modules/yoma/scripts/allowlists/rashi_boundary_authorizations.json`
(ratchet 20/20, a closed matter per `CLAUDE.md`): one continuous Rashi
comment on Rabbi Yaakov's metzora log-of-oil distinction, truncated at
61a's own final line and completing on 61b, hence its authorized empty
`linkedGemaraLineIds`. That authorization concerns rendering/linking
only; the translation-quality question is independent and was reviewed
like every other entry in this batch.

Re-generated and re-validated (`generate_rashi_batch_progress.py`,
`generate_rashi_translation_inventory.py --check`) at the start of this
batch against current main to confirm the batch manifest entry is
unmodified and still selects exactly these 167 entries, that all 167
were still UNREVIEWED, and that they were assigned only to
`step6-batch-027` (0 overlap with any other batch). A fresh review
packet (`generate_rashi_review_packets.py --batch-id step6-batch-027`)
was generated and used as the basis for review. No entry outside the
batch was edited.

## Method and key finding: the "needs-reconstruction" flags are stale for the three affected daf

Following the `step6-batch-003`/`023`/`024`/`025`/`026` precedent, `git
log --oneline --all -- modules/yoma/assets/learning/yoma/<daf>.learning.json`
was checked for every daf in this batch **before** reading the flagged
entries at face value:

```
59b: 89baa27 Yoma 59b: full Rashi reconstruction (14 entries) (#303)
60a: 779bf42 Yoma 60a: full Rashi reconstruction (52 entries) (#304)
60b: 5b225d6 Yoma 60b: full Rashi reconstruction (43 entries) (#305)
61a: a1c403a Reconstruct 61a Rashi lines 1-45 from raw Hebrew
```

**All four daf in this batch were already reconstructed**, in PRs #303,
#304, #305 respectively for 59b/60a/60b, well before the VERSION 15.293
Wave 1 audit whose finding the current Step 2 risk-signal generator and
batch-planning `known-needs-reconstruction` provenance bucket still
cite for those three daf. As with the five prior stale-flag batches this
session, the classification metadata was never refreshed to reflect
that the underlying content problem had already been fixed. 61a's own
reconstruction (lines 1-45, a standalone commit) is reflected correctly
in its `content-reviewed` classification and was not itself stale.

All 167 entries were nonetheless read individually and independently
re-derived from their own Hebrew (never from the existing English
alone), cross-checked against neighboring entries' Hebrew, linked
Gemara/Mishnah context, the style guide, and the terminology registry.
Every one of the 103 flagged entries was individually confirmed to be a
faithful, specific, non-generic translation of its own Hebrew line - not
filler, not fabricated, and not shifted from a neighbor. The 64
`content-reviewed` 61a entries, including the 19 boundary-range entries,
were confirmed equally faithful.

**First pass**: all 167 entries reviewed individually. Result: **167
VERIFIED, 0 MINOR_EDIT, 0 SUBSTANTIVE_REPAIR, 0 RETRANSLATE, 0
DUPLICATION_OR_CONTAMINATION, 0 BLOCKED.**

**Second pass**: not applicable (0 changed entries).

**Blind QA**: given the mixed provenance, a full-coverage sample was
used for all 103 `known-needs-reconstruction`-flagged entries, all 19
pre-authorized 61a boundary entries, and all 4 daf-boundary anticipation
stubs, plus a deterministic every-6th-entry sample (8 of 45) of the
remaining plain `content-reviewed` 61a entries - a combined sample of
130 of 167 (77.8%). Each was independently re-derived from the raw
Hebrew a second time, deliberately independent of the first-pass
reasoning and the PR #303/#304/#305 history lookups. Result: **130/130
CONFIRMED_VERIFIED, 0 escalations.**

## Systemic-candidate review

### Family 1: fabricated "New comment:" scaffold text

**0 candidates in this batch.** A corpus-wide check confirms 0
occurrences, consistent with `step6-batch-006` (this session) fully
draining this family from the entire unreviewed corpus.

### Family 2: cross-entry word anticipation

4 candidates in this batch, all daf-boundary single-word/fragment
stubs: `rashi-yoma-059b-014` (Hebrew "ובגדי", deferred to 60a),
`rashi-yoma-060a-052` (Hebrew "רבי", deferred to 60b),
`rashi-yoma-060b-043` (Hebrew "בקטורת", deferred to 61a), and
`rashi-yoma-061a-064` (Hebrew "אשם", deferred to 61b). **Disposition:
FALSE_POSITIVE for all 4.** Same low-precision OVEREXPLAINED
length-ratio trigger already confirmed throughout this session. Left
unchanged, VERIFIED.

## Other risk-signaled entries (outside both systemic families)

- **TRUNCATED** (5 entries: `059b-012`, `060b-013`, `060b-020`,
  plus 9 entries on 61a: `061a-005`, `061a-006`, `061a-014`,
  `061a-019`, `061a-020`, `061a-021`, `061a-032`, `061a-056`): all
  confirmed **FALSE_POSITIVE** - each ends mid-clause on a function
  word because this corpus splits Rashi comments across Vilna-line
  entries, and the immediately following vilnaLine entry completes the
  clause in every case (verified individually).
- **WRONG_REFERENT** (1 entry: `060b-025`): pronoun referent ("one
  master... one master") checked against the immediately preceding
  entry's established context (the two disputants introduced at
  `060b-023/024`). Resolves correctly. **FALSE_POSITIVE.**

All are VERIFIED.

## Aggregate results (167 entries)

| Disposition | Count | Rate |
|---|---|---|
| VERIFIED | 167 | 100.0% |
| MINOR_EDIT | 0 | 0.0% |
| SUBSTANTIVE_REPAIR | 0 | 0.0% |
| RETRANSLATE | 0 | 0.0% |
| DUPLICATION_OR_CONTAMINATION | 0 | 0.0% |
| BLOCKED | 0 | 0.0% |
| **Total** | **167** | **100%** |

**Changed-translation count: 0.** No PR content-diff applies to any
`modules/yoma/assets/learning/yoma/*.learning.json` file for this batch
- only review-records, inventory review-metadata, and documentation
change. No BLOCKED entries and no structural/source-cache blockers were
found anywhere in this batch. The 19 boundary-range 61a entries were
reviewed for translation quality only; their authorized empty-link
status was not touched.

## Regression and platform evidence

- Rashi entry count: 8,854 (unchanged) - Associations: 10,061 declared, 0
  broken, 0 cross-daf (unchanged) - Boundary registry: 20/20 (unchanged)
- Hebrew and English text: byte-unchanged across all 167 entries in this
  batch (0 changes to apply)
- `npm run validate:offline:yoma`, `npm test`, `npm run test:browser`,
  `npm run build`, `npm run check:deploy-html`, `python3
  scripts/worker_pipeline.py verify --full`: all green

## Status

**Batch 027: COMPLETE.** All 167 entries reviewed with an assigned final
disposition; 0 entries left in an ambiguous state; 0 BLOCKED. This is
the seventh consecutive batch this session (`002`, `003`, `023`, `024`,
`025`, `026`, `027`) whose principal finding is negative-but-well-
evidenced: for the three reconstruction-flagged daf, the historical
`INVENTED_TEXT`/`known-needs-reconstruction` classification is confirmed
stale, not a live defect; for daf 61a's `content-reviewed` entries
(including the 19 pre-authorized boundary entries), the existing
classification is confirmed accurate. Blind QA (77.8%, full coverage of
every flagged/boundary/anticipation entry plus a deterministic sample of
the remainder): 130/130 CONFIRMED_VERIFIED, 0 escalations.
