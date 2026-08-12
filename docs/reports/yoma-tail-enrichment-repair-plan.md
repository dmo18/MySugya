# Yoma tail-enrichment repair plan

Companion to `docs/reports/data/yoma-tail-enrichment-repair-queue.json`.

The merged audit (`docs/reports/yoma-tail-enrichment-audit.md`) is historical evidence and is never rewritten. This plan and the queue carry the actionable state.

- Audit source SHA: `3aa90cde8c50f8489e2e7ca6f4bbe7ffe034f9d5`
- Queued records: **82** (every audit record whose overall disposition is not VERIFIED, exactly once)
- Contract authority: `docs/reports/yoma-enrichment-contract-decision.md`
- Gate: `scripts/validate_enrichment_contracts.py`, TWO layered comparisons run
  together: (1) the frozen historical baseline (`--targets` for target-clean),
  which never shrinks on its own and only bounds debt to the campaign's
  original envelope; (2) the merge-base monotonic ratchet (`--compare-ref
  <merge-base>`), which compares this PR against current main and is what
  actually stops a later PR from reintroducing a violation an earlier PR
  already fixed. See "Two-layer enrichment-contract gate" below.

## Queue totals

| Dimension | Counts |
|---|---|
| Semantic disposition | MINOR_EDIT_NEEDED 9, SUBSTANTIVE_REPAIR_NEEDED 24, VERIFIED 49 |
| Mechanical disposition | MINOR_EDIT_NEEDED 53, STRUCTURAL_OR_SCHEMA_DECISION 29 |
| Removed `concepts` scheduled for purge | 33 |
| Carrying migration prerequisites | 33 |

## Supersession recorded here, not in the audit

The 29 records whose `finalRuling` exactly copies `display.hint` carry `STRUCTURAL_OR_SCHEMA_DECISION` in the merged audit because the contract was open when it was written. The `finalRuling` contract decision closes that question: a non-empty `finalRuling` equal to `display.hint` is invalid. Those records are now ordinary repairable defects. Their historical audit dispositions are left untouched by design.

## Execution order

1. prerequisite contract/tooling and migrations (not queue rows)
2. yoma-082b-s01
3. yoma-087b-s03
4. yoma-080a-s01
5. yoma-080b-s03
6. remaining substantive records in daf order
7. minor semantic records
8. parent daf summaries after all sugyot on each daf are settled
9. finalRuling-only mechanical repairs after each underlying hint is confirmed

Step 1 is tooling and migration work and does not appear as queue rows. Steps 2 onward map to `queuePosition` in the queue file.

### Step 8 (parent summaries) enforcement status

This plan previously stated that "parent daf summaries [are repaired] after
all sugyot on each daf are settled" without saying what enforces that. As of
this revision it is **partially enforced mechanically, not fully**:

- `normalize_audit_pointer` (`scripts/worker_pipeline.py`) correctly maps a
  `/summary` pointer onto the literal `<daf>.summary` affectedFields
  template, and `json_scope_check` requires that string to appear in the
  affectedFields of at least one manifest-named audit record for that same
  daf before a `/summary` edit is authorized at all. This much IS
  mechanically enforced today.
- What is **NOT** mechanically enforced: that every OTHER sugya-level record
  on that same daf has already reached a "settled" progress status
  (`FIXED_PENDING_REVIEW` or later) before the `/summary` edit lands. A
  manifest naming only the `<daf>.summary`-bearing record, with the rest of
  that daf's records still `NOT_STARTED`, currently passes scope and
  prerequisite checks. Enforcing the full "settled" precondition would
  require a same-daf progress-status cross-check inside
  `audit_repair_prerequisite_errors` or `json_scope_check`; that has not been
  built. Until it is, Step 8's daf-level sequencing is a WORKFLOW convention
  for whoever assembles each repair PR, not a gate the tooling itself
  enforces. This paragraph is the accurate statement of that gap; do not read
  the numbered list above as claiming otherwise.

## Two-layer enrichment-contract gate

The frozen historical baseline (`scripts/baselines/yoma_enrichment_contract_debt.json`)
enumerates the ORIGINAL legacy debt from when this campaign started and is
never rewritten by an ordinary repair PR; it answers "is the corpus still
inside the envelope of debt the campaign started with?" It does NOT, by
itself, make repaired counts stay repaired across separate merged PRs: a
value that has always been within that frozen envelope compares clean
against it forever, so a later, unrelated PR can silently put an
already-fixed invalid value right back and the frozen-baseline comparison
alone would accept it.

The merge-base monotonic ratchet (`compare_to_merge_base`, invoked via
`--compare-ref <this PR's actual git merge-base>`) closes that gap: it reads
the SAME module's generated data at the merge-base with real `git show`
data (never a hand-maintained snapshot) and requires current occurrences to
be a multiset subset of the merge-base's occurrences, rule by rule, sugya by
sugya. A previously-merged improvement can therefore never be silently
regressed by a later PR, even though the regressed value would still fall
inside the frozen envelope. Both checks run and both must pass; neither
replaces the other. `scripts/worker_pipeline.py`'s `verify` and `ci-check`
subcommands run the merge-base ratchet automatically whenever a PR changes
the active module's learning data, independent of task type.

## Prerequisites before any semantic repair

1. **`legacy-concepts-purge`** - corpus-wide deletion of `sugyot[*].concepts` (492 sugyot).
2. **`enrichment-schema-migration`** - `requiresUnderstanding` prose to `prerequisiteKnowledge` (404 sugyot), `visualizableElements` shape normalization (432 sugyot missing `item`), `difficulty` `introductory` to `intro` (112 sugyot).

Both are mechanical. Until they land, no sugya can pass `--targets` target-clean, because every sugya still carries the removed `concepts` field. That ordering is enforced by the gate rather than by convention.

**This is now enforced by a SEPARATE, dedicated gate, not only by
target-clean.** `audit_repair_prerequisite_errors` (`scripts/worker_pipeline.py`)
blocks `audited-sugya-enrichment-repair` manifest generation AND preflight,
independent of semantic target-clean, until (a) `legacy_concepts_present` is
exactly zero across the WHOLE corpus, and (b) every named record's own
`migrationPrerequisites` (declared per-sugya in
`docs/reports/data/yoma-tail-enrichment-repair-queue.json`, e.g.
`requiresUnderstanding-prose-to-prerequisiteKnowledge`,
`visualizableElements-shape-normalization`, `difficulty-introductory-to-intro`)
are clean for that exact sugya. Unrelated ordinary debt elsewhere in the
corpus never blocks an otherwise-satisfied check.

## Progress lifecycle (one-PR repair)

`docs/reports/data/yoma-tail-enrichment-repair-progress.json` tracks each
queued record through `NOT_STARTED -> IN_PROGRESS -> FIXED_PENDING_REVIEW ->
APPROVED_PENDING_MERGE -> COMPLETE` (plus `BLOCKED`, requiring a
`blockerReason`, resolving back to `IN_PROGRESS`). This supports a single
content-repair PR end to end:

1. the repair PR's own commits walk NOT_STARTED through APPROVED_PENDING_MERGE
   (each transition on its own commit; legality is checked across the FULL
   commit history from merge-base to head, not just the two endpoints, so an
   intermediate walk is never rejected as a false "skip");
2. `APPROVED_PENDING_MERGE` requires a non-empty `reviewer` and
   `independentReviewResult` -- the explicit pre-merge "approved" checkpoint
   from an independent reviewer;
3. after squash-merge, the effective `COMPLETE` state is DERIVED
   (`derive_effective_status`) from evidence bound to the exact audit
   record: the squash commit must be an ancestor of main, its own
   `.worker-manifest.json` (read from that commit, never the working tree)
   must be type `audited-sugya-enrichment-repair` naming this sugyaId in
   `auditRecordIds`, that manifest's target daf must match this sugyaId's
   own daf in the repair queue, and the commit's diff must actually touch
   that exact daf's `*.learning.json` -- plus the already-approved progress
   state. A correctly-manifested repair for a different sugya or daf never
   derives `COMPLETE` here. No second, progress-only PR is required just to
   hand-edit the file to `COMPLETE`.

Progress-record changes in any one PR are scoped to exactly that PR's
manifest `auditRecordIds`; every other record must stay byte-identical, and
no record may carry a field outside the schema (`status`, `prNumber`,
`repairCommit`, `mergedCommit`, `version`, `reviewer`,
`independentReviewResult`, `blockerReason`).

## First four repairs

| # | Sugya | Daf | Why first |
|---|---|---|---|
| 1 | `yoma-082b-s01` | 82b | Fabricated framing: display/learning describe an invented pikuach-nefesh question; the source is the martyrdom sevara. |
| 2 | `yoma-087b-s03` | 87b | Fabricated framing: display describes a Hadran/Tu BeAv closing absent from the source; the sugya is neila. |
| 3 | `yoma-080a-s01` | 80a | Ruling contradicts the source and the sugya own argumentFlow: source says olive-bulk, display says egg-bulk. |
| 4 | `yoma-080b-s03` | 80b | Ruling inverted: source says excessive eating is exempt, display says it creates liability. |

## Per-daf workload (one daf per repair PR)

| Daf | Queued sugyot |
|---|---|
| 77a | 4 |
| 77b | 4 |
| 78a | 5 |
| 78b | 4 |
| 79a | 1 |
| 79b | 1 |
| 80a | 3 |
| 80b | 3 |
| 81a | 4 |
| 81b | 2 |
| 82a | 4 |
| 82b | 2 |
| 83a | 5 |
| 83b | 4 |
| 84a | 3 |
| 84b | 4 |
| 85a | 6 |
| 85b | 4 |
| 86a | 4 |
| 86b | 5 |
| 87a | 5 |
| 87b | 3 |
| 88a | 2 |

## Required task types

- `audited-sugya-enrichment-repair` for every queue row: semantic, max one daf per PR, independent review required, manifest must name the audit record ids, and every changed path must appear in those records' `affectedFields`.
- `legacy-concepts-purge` and `enrichment-schema-migration` for the prerequisites above.

## Status

Every record is `NOT_STARTED`. No repair has begun.
