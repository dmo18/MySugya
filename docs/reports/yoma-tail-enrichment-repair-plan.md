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

- `audited-sugya-enrichment-repair` for every queue row: semantic, max one daf per PR, independent review required, manifest must name the audit record ids, and every changed path must appear in those records' `affectedFields` (or its migrated successor field -- see "prerequisiteKnowledge successor-field scope" below).
- `legacy-concepts-purge` and `enrichment-schema-migration` for the prerequisites above.

## prerequisiteKnowledge successor-field scope

The merged audit predates the `requiresUnderstanding` prose -> `prerequisiteKnowledge`
schema migration, so any audit record whose semantic defect included prose
prerequisite material names it under the OLD field, `requiresUnderstanding`,
in `affectedFields`. Once that migration has landed for a sugya, the actual
prose lives in `prerequisiteKnowledge` instead, and without a successor-field
rule the audited-repair scope gate could never authorize touching it -- the
record's own `affectedFields` literally does not contain the string
`"prerequisiteKnowledge"`.

`scripts/worker_pipeline.py` closes this narrowly: `AUDIT_FIELD_SUCCESSOR_ALIASES`
maps `prerequisiteKnowledge` -> `requiresUnderstanding`, and
`audit_field_authorized(normalized, affected_fields)` treats a field as
authorized when it is either directly listed in `affected_fields`, or is the
successor of a field that IS listed there. `json_scope_check` calls this
helper (in place of a bare membership test) only inside its
`audited-sugya-enrichment-repair` branch, and always with the exact named
record's own `affectedFields` -- never a union across multiple named
records. Consequences, all mechanically enforced (see
`scripts/test_worker_pipeline_integration.py` checks 32a-32h):

- a record that owns `requiresUnderstanding` may repair its migrated
  `prerequisiteKnowledge` on that same sugya;
- a record that never owned `requiresUnderstanding` may not touch
  `prerequisiteKnowledge` at all;
- naming one record never authorizes a `prerequisiteKnowledge` edit on a
  sibling sugya or a different daf (the pre-existing per-sugya, per-daf
  scope checks are unchanged and still fire first);
- no other task type gains any new scope (the alias only ever applies
  inside the audit-repair branch of `json_scope_check`);
- `requiresUnderstanding` itself is completely unaffected: it still means
  resolving sugya ids only, and the alias never runs in reverse;
- `prerequisiteKnowledge`'s own contract (optional, source-supported prose)
  is unchanged;
- `task_specific_rule_scoped_targets` extends the same record's rule-scoped
  target-clean check to cover `prerequisiteKnowledge`'s own contract rules
  whenever the alias applies, so a repair that uses it is still held to a
  real target-clean bar, not merely "authorized to touch the path";
- `worker:scope`, `worker:verify` and `worker:ci-check` all enforce this
  identically, since all three route through `cmd_scope` -> `json_scope_check`.

Separately: a narrow follow-up repair on an ALREADY-effectively-COMPLETE
record (e.g. cleaning up a stale `prerequisiteKnowledge` left out of scope
by the record's first repair PR) needs no new mechanism. A merged record's
STORED progress status stays `APPROVED_PENDING_MERGE` forever -- `COMPLETE`
is derived from squash-merge evidence (see "Progress lifecycle" above), never
hand-written -- so `validate_audit_record_ids`'s "already COMPLETE" guard
never fires for it, and `APPROVED_PENDING_MERGE -> IN_PROGRESS ->
FIXED_PENDING_REVIEW -> APPROVED_PENDING_MERGE` is itself a legal transition
sequence under `ALLOWED_TRANSITIONS`. A follow-up PR may therefore re-name
the same `auditRecordId`, make a further in-scope edit (still bound by that
exact record's own `affectedFields`/successor fields, still one daf, still
independent review), and walk the lifecycle again -- while the ORIGINAL
squash commit remains an untouched, independently sufficient piece of git
history, so the original completion evidence is never falsified or
replaced. Confirmed by `scripts/test_worker_pipeline_integration.py` checks
33a-33f, including the contrasting case: a record whose stored status is
ever hand-written to the literal terminal `COMPLETE` correctly blocks any
further manifest naming it.

## Campaign completion protocol

This section documents the algorithm a fresh agent (no conversation memory)
uses to resume and finish this campaign from the repository alone.

**Sources of truth, and what each one is:**

- `docs/reports/data/yoma-tail-enrichment-repair-queue.json` -- the
  IMMUTABLE work definition: which 82 sugyot need a repair, in what
  `queuePosition` order, with what `affectedFields`/migration prerequisites.
  Never hand-edited; only re-derived from the frozen audit.
- `docs/reports/data/yoma-tail-enrichment-repair-progress.json` -- the
  MUTABLE lifecycle state, keyed by sugyaId, one record per queue row. Each
  repair PR's own commits walk its own named record(s) through
  `NOT_STARTED -> IN_PROGRESS -> FIXED_PENDING_REVIEW -> APPROVED_PENDING_MERGE`.
- The repo itself, at `origin/main`, is the campaign checkpoint. There is no
  other durable state anywhere else.

**How to compute what is actually done (never trust the stored `status`
string alone):** a record's REAL completion is whether some commit reachable
from `origin/main` carries a `.worker-manifest.json` of type
`audited-sugya-enrichment-repair` naming that exact sugyaId in
`auditRecordIds`, targeting that sugyaId's own daf, whose diff actually
touches that daf's `*.learning.json` -- see `derive_effective_status` in
`scripts/generate_enrichment_repair_queue.py` for the exact, already-tested
evidence chain. The stored `status` field only ever reaches
`APPROVED_PENDING_MERGE` through the normal one-PR lifecycle; it is
deliberately never hand-written to `COMPLETE` on an ordinary merge (that
would require a pointless second, progress-only PR). So: a record showing
`APPROVED_PENDING_MERGE` in the progress file is not necessarily still
outstanding -- check whether its `repairCommit` (or any later commit
naming it) is now an ancestor of `origin/main` before assuming more work is
needed on it.

**Resume algorithm, every time:**

1. Fetch/checkout fresh `origin/main`. Confirm no unexpected divergence from
   what the last known-good state was; reconcile before continuing if so.
2. Confirm zero conflicting open PRs.
3. Re-read the queue and progress files fresh from this checkout.
4. For every queue record, compute effective status per the derivation
   above (not the raw stored string).
5. Walk the queue's own `orderingPolicy` / `queuePosition` order, skipping
   anything effectively complete, and select the next eligible record(s) for
   the current campaign phase (see the phase list this plan's execution
   order already describes).
6. Do the work for that daf (migration if first visit, at most one
   `gemara-learning` PR for source-contradictory content outside audit
   ownership, then one `audited-sugya-enrichment-repair` PR naming every
   eligible same-daf record for the current phase).
7. Independent review, merge on green CI, confirm deploy, then go back to
   step 1.

Never skip step 1 between records -- the queue/progress files and
`origin/main` are the only state a fresh agent needs, and re-deriving
effective status from a stale local checkout is exactly the kind of drift
this protocol exists to prevent.

## Status snapshot

This section is a point-in-time snapshot for historical orientation, not a
maintained live status list (see "Campaign completion protocol" above for
why: a fresh agent must always recompute effective status from `origin/main`
rather than trust prose here). Snapshot as of the tooling PR that added this
section:

**Repaired (effectively COMPLETE, stored `APPROVED_PENDING_MERGE`, merge
evidence present):**

- `yoma-082b-s01`
- `yoma-082b-s02`
- `yoma-087b-s03`

**Known residual follow-ups, discovered from live data, not yet closed:**

1. `yoma-082b-s01` `prerequisiteKnowledge` still carries stale pre-repair
   Yom-Kippur-oriented boilerplate.
2. `yoma-082b-s02` still contains inherited R. Yannai / wrong-speaker
   learning prose in fields not authorized by its historical audit record
   (a `gemara-learning` PR, not the audited-repair mechanism, is the
   correct tool for those fields).
3. `yoma-087b-s03` `prerequisiteKnowledge` still contains stale
   Hadran-context prose.
4. The 87b parent summary remains deliberately deferred until `yoma-087b-s01`
   and `yoma-087b-s02` are repaired.
5. `yoma-080a-s01` and `yoma-080b-s03` are the next two original priority
   repairs (positions 3 and 4) and remain unrepaired as of this snapshot.

**Everything else in the queue:** `NOT_STARTED`, in `queuePosition` order.
