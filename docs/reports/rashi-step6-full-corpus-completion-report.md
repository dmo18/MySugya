# Rashi translation-quality campaign: Step 6 full-corpus completion report

Terminal reconciliation for the Step 6 full-corpus Rashi translation
review defined in `docs/reports/rashi-full-corpus-review-strategy.md`
(Step 5). This document is the single closing record for the campaign:
it aggregates all 41 Step 6 batch PRs, the Step 4 pilot, and the
`rashi-yoma-009b-001` source-repair follow-up into one corpus-wide
result, and records the final regression evidence at campaign close.

**Status: COMPLETE.** As of VERSION 15.481, commit `2511534b1bdd4740c316f6451259fd4dda2cd543`
on `main`, all 8,854 `rashiTranslations` entries in the Yoma corpus
carry `reviewStatus: REVIEWED`. 0 entries remain `UNREVIEWED`.

## Corpus-wide totals

| Source | Entries | VERIFIED | MINOR_EDIT | SUBSTANTIVE_REPAIR | RETRANSLATE | DUPLICATION_OR_CONTAMINATION | BLOCKED |
|---|---|---|---|---|---|---|---|
| Step 4 pilot (`docs/reports/rashi-pilot-step4-final-report.md`) | 200 | 177 | 11 | 9 | 2 | 0 | 1 |
| Step 6, 41 batches (this report) | 8,654 | 8,044 | 603 | 7 | 0 | 0 | 0 |
| `rashi-yoma-009b-001` source-repair follow-up (disposition change only, not a new entry) | 0 | +1 | - | - | - | - | -1 |
| **Corpus total** | **8,854** | **8,222** | **614** | **16** | **2** | **0** | **0** |

The corpus total matches `docs/reports/data/rashi-translation-quality-inventory.json`
exactly (verified by direct count against the live file at the commit
above): 8,854 entries, 8,854 REVIEWED, 0 UNREVIEWED, dispositions
8,222 / 614 / 16 / 2 / 0 / 0 in the same order.

**Total changed-translation count across the whole campaign: 632**
(614 MINOR_EDIT + 16 SUBSTANTIVE_REPAIR + 2 RETRANSLATE), against
8,222 entries confirmed as-is (VERIFIED). Every changed or BLOCKED
entry received a complete, independent second semantic pass before its
disposition was finalized, per the Step 5 methodology's rule 7 - no
exceptions found in any of the 41 batches or the pilot.

## Step 6: all 41 batches

Executed in the order below (the strategy document's recommended
sequence). "Blind QA coverage" is full-coverage (every entry
independently re-derived from Hebrew a second time) for 31 of the 41
batches; the remaining 10 batches used a deterministic risk-weighted
subsample under the Step 5 hybrid-review escalation rule (any blind-QA
disagreement would have forced sample expansion). **0 escalations
occurred in any of the 41 batches** - every blind-QA sample, full or
partial, confirmed the first pass without exception, so no batch's
sample was ever expanded past its starting coverage.

| Order | Batch | Daf | Entries | VERIFIED | MINOR_EDIT | SUBSTANTIVE_REPAIR | Blind QA coverage |
|---|---|---|---|---|---|---|---|
| 1 | step6-batch-040 | 85b-87a | 253 | 144 | 109 | 0 | 16/253 (6%) |
| 2 | step6-batch-039 | 83a-85a | 294 | 186 | 108 | 0 | 26/294 (9%) |
| 3 | step6-batch-005 | 11b-14a | 270 | 192 | 78 | 0 | 28/270 (10%) |
| 4 | step6-batch-038 | 80a-82b | 282 | 204 | 78 | 0 | 29/282 (10%) |
| 5 | step6-batch-037 | 77a-79b | 250 | 181 | 69 | 0 | 27/250 (11%) |
| 6 | step6-batch-022 | 51a-52b | 186 | 149 | 37 | 0 | 20/186 (11%) |
| 7 | step6-batch-041 | 87b-88a | 125 | 87 | 38 | 0 | 12/125 (10%) |
| 8 | step6-batch-004 | 8b-11a | 196 | 164 | 32 | 0 | 23/196 (12%) |
| 9 | step6-batch-021 | 48a-50b | 289 | 255 | 34 | 0 | 33/289 (11%) |
| 10 | step6-batch-006 | 14b-16a | 244 | 232 | 12 | 0 | 29/244 (12%) |
| 11 | step6-batch-002 | 5a-6a | 158 | 158 | 0 | 0 | 26/158 (16%) |
| 12 | step6-batch-003 | 6b-8a | 126 | 126 | 0 | 0 | 42/126 (33%) |
| 13 | step6-batch-023 | 53a-54b | 180 | 180 | 0 | 0 | 128/180 (71%) |
| 14 | step6-batch-024 | 55a-56b | 157 | 157 | 0 | 0 | 152/157 (97%) |
| 15 | step6-batch-025 | 57a-57b | 112 | 112 | 0 | 0 | 100% (full) |
| 16 | step6-batch-026 | 58a-59a | 169 | 169 | 0 | 0 | 100% (full) |
| 17 | step6-batch-027 | 59b-61a | 167 | 167 | 0 | 0 | 130/167 (78%) |
| 18 | step6-batch-028 | 61b-62b | 171 | 171 | 0 | 0 | 100% (full) |
| 19 | step6-batch-029 | 63a-64a | 147 | 147 | 0 | 0 | 100% (full) |
| 20 | step6-batch-030 | 64b-65b | 150 | 150 | 0 | 0 | 100% (full) |
| 21 | step6-batch-031 | 66a-67a | 180 | 180 | 0 | 0 | 100% (full) |
| 22 | step6-batch-033 | 69a-70a | 137 | 137 | 0 | 0 | 100% (full) |
| 23 | step6-batch-034 | 70b-71b | 162 | 162 | 0 | 0 | 100% (full) |
| 24 | step6-batch-001 | 2a-4b | 274 | 259 | 8 | 7 | 26/274 (9%) |
| 25 | step6-batch-035 | 72a-73b | 254 | 254 | 0 | 0 | 100% (full) |
| 26 | step6-batch-009 | 22a-24a | 248 | 248 | 0 | 0 | 100% (full) |
| 27 | step6-batch-017 | 40a-42a | 286 | 286 | 0 | 0 | 100% (full) |
| 28 | step6-batch-007 | 16b-19a | 278 | 278 | 0 | 0 | 100% (full) |
| 29 | step6-batch-008 | 19b-21b | 269 | 269 | 0 | 0 | 100% (full) |
| 30 | step6-batch-010 | 24b-26b | 282 | 282 | 0 | 0 | 100% (full) |
| 31 | step6-batch-011 | 27a-28a | 138 | 138 | 0 | 0 | 100% (full) |
| 32 | step6-batch-012 | 28b-30b | 289 | 289 | 0 | 0 | 100% (full) |
| 33 | step6-batch-013 | 31a-33a | 276 | 276 | 0 | 0 | 100% (full) |
| 34 | step6-batch-014 | 33b-36a | 266 | 266 | 0 | 0 | 100% (full) |
| 35 | step6-batch-015 | 36b-39a | 297 | 297 | 0 | 0 | 100% (full) |
| 36 | step6-batch-016 | 39b-39b | 64 | 64 | 0 | 0 | 100% (full) |
| 37 | step6-batch-018 | 42b-44a | 244 | 244 | 0 | 0 | 100% (full) |
| 38 | step6-batch-019 | 44b-47a | 245 | 245 | 0 | 0 | 100% (full) |
| 39 | step6-batch-020 | 47b-47b | 65 | 65 | 0 | 0 | 100% (full) |
| 40 | step6-batch-032 | 67b-68b | 191 | 191 | 0 | 0 | 100% (full) |
| 41 | step6-batch-036 | 74a-76b | 283 | 283 | 0 | 0 | 100% (full) |
| **Total** | | | **8,654** | **8,044** | **603** | **7** | 0 escalations anywhere |

Per-batch narrative reports (method, evidence, systemic-candidate
resolution, and any provenance findings): `docs/reports/rashi-step6-batch-0NN-report.md`
for `NN` 001-041. Per-entry review records validated against the Step 5
contract: `docs/reports/data/rashi-step6-batch-0NN-review-records.json`.

## Systemic-candidate families

Both authorized cluster-assisted candidate families (Step 5 rule 5)
were fully resolved across the corpus, entry by entry, never written
back without an individual semantic pass:

- **Family 1** (fabricated `"New comment:"` scaffold text): drained to
  0 remaining candidates. Every instance found across the corpus was a
  confirmed fabrication and repaired.
- **Family 2** (cross-entry word anticipation / daf-boundary stubs):
  fully resolved. Two sub-patterns were confirmed present - standard
  explanatory-framing fragments and bare fragments lacking framing -
  both repaired entry by entry with independent Hebrew re-derivation,
  never by pattern substitution.

`generate_rashi_systemic_candidates.py` now reports 0 candidates in
both families against the fully-reviewed corpus (mechanically forced,
since both families are scanned only across UNREVIEWED entries).

## Provenance-metadata accuracy findings

The inventory's `dafProvenance[<daf>].contentReviewCommits` field was
found incomplete or inaccurate on more than one occasion during Step 6
and was never trusted at face value; each discrepancy is documented in
its batch's own report rather than silently accepted:

- **step6-batch-032** (daf 67b-68b): 68b's recorded commit count
  understated the real history.
- **step6-batch-036** (daf 74a-76b): all six daf were recorded as
  `postSquashCommitCount: 0` / "not independently git-verifiable"
  (repo history squashed at `655b973`). This was flatly wrong: a direct
  `git log` search recovered a genuine, dated post-squash commit for
  every one of the six daf (`121db53`/74a, `de12c24`/74b, `55b1f47`/75a,
  `25aa42d`/75b, `0a73f05`/76a, `e19a860`/76b, all 2026-07-20), all well
  after the squash point and well before this review campaign began.

Neither finding indicated a translation defect; both are metadata
accuracy notes preserved here so the provenance field is not
mistakenly treated as authoritative without cross-checking against
`git log` directly.

## Test-infrastructure fixes required by campaign completion

Three self-tests hardcoded assumptions about corpus state that became
false as the campaign legitimately progressed toward and reached 0
remaining batches / 0 UNREVIEWED entries. Each was root-caused as a
test-harness gap, not a content defect, verified directly against the
real terminal inventory state before being fixed, and landed as its
own narrowly-scoped `docs-tooling` PR (kept separate from the
`rashi-translation-review` batch PR that exposed it, per that task
type's file-scope contract):

- **PR #470**: `test_plan_rashi_full_corpus_batches.py` checks 13 and
  17 assumed at least 2 remaining batches; fixed for the "1 batch
  remaining" case (self-duplicating the sole batch's own entry id for
  check 13; skipping the perek-crossing check when only one perek
  remains for check 17).
- **PR #472**: the same file's checks 13-19 still assumed at least 1
  remaining batch; fixed by skipping the entire corruption-injection
  block (all seven checks) once 0 batches remain, since there is
  nothing left to corrupt.
- **PR #473**: `test_generate_rashi_systemic_candidates.py` check 6
  hard-asserted a non-empty cross-entry-word-anticipation family; fixed
  identically to the already-correct check 3 (scaffold family) pattern
  - an independent-count cross-check against the live inventory, valid
  whether the family holds candidates or is fully drained to 0.

## Closing regression evidence

The exhaustive sharded Playwright linked-association browser check
(`rashi-association.spec.js`, all 173 daf) was run twice this campaign
at completion milestones and confirmed clean both times:

- After the 40th parent batch (`step6-batch-032`, commit `26a4c73`):
  173/173 daf, 8,854 entries, 215 passed, 0 failed, 8 shards.
- **Closing checkpoint**, after the 41st and final batch
  (`step6-batch-036`, commit `2511534b1bdd4740c316f6451259fd4dda2cd543`,
  VERSION 15.481) - the exact commit at which the corpus reached 0
  UNREVIEWED:

  ```json
  {
    "schemaVersion": 1,
    "commitSha": "2511534b1bdd4740c316f6451259fd4dda2cd543",
    "workflowRunId": "31228962087",
    "totalEntries": 8854,
    "passed": 215,
    "failed": 0,
    "shardCount": 8
  }
  ```

Every one of the 41 batch PRs additionally passed the full 8-gate
worker-pipeline verify (`offline-gates`, `build`, `deploy-html`,
`unit+render`, `browser`, `worker-scope`, `version-sync`, `no-dashes`)
before merge, and each merge to `main` was confirmed deployed to
GitHub Pages before the next batch began.

## What this campaign did not touch

- **No Hebrew was edited** by any of the 41 Step 6 batches or the
  pilot. The sole Hebrew correction in the whole campaign's scope is
  the pre-Step-5 `rashi-yoma-009b-001` source repair, its own separate
  `rashi-source-repair` task type and PR, documented in
  `docs/reports/rashi-source-repair-009b-report.md` and referenced from
  the strategy document's "Resolution addendum."
- **No Tosafot or scope expansion.** Only existing `rashiTranslations`
  English entries were reviewed and, where warranted, corrected.
- **No renderer, association, or structural change.** This campaign is
  entirely orthogonal to the linked-renderer cutover (VERSION 15.338)
  and the boundary-authorization registry (20/20), both unaffected and
  unchanged.
- **The paused nekudot/vowelization audit** remains paused and
  untouched; nothing in this campaign reopens it.

## Cross-references

| Document | Role |
|---|---|
| `docs/reports/rashi-full-corpus-review-strategy.md` | Step 5 methodology, batching contract, tooling, the 41-batch recommended sequence (this report is its closing status) |
| `docs/reports/rashi-pilot-step4-final-report.md` | Step 4 pilot (200 entries), the source of the two authorized systemic-candidate families |
| `docs/reports/rashi-source-repair-009b-report.md` | The one Hebrew-source correction in scope, and its follow-up semantic review |
| `docs/reports/data/rashi-translation-quality-inventory.json` | Live per-entry disposition and provenance data, corpus-wide |
| `docs/reports/open-items.md` | Repository-wide classified status; this campaign's entry moved from OPEN-ACTIONABLE to COMPLETED alongside this report |
| `docs/rashi-audit-backlog.md` | Separate, already-closed scaffold-fabrication remediation campaign (0 debt); not to be confused with this translation-quality review |
