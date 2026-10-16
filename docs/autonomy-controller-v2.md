# Autonomy controller (v2)

**What it is.** `scripts/autonomy_controller.py` is a pure, deterministic
state-transition / evidence engine, standard library only. It tracks one
active MySugya work unit at a time through a fixed state machine and a fixed
evidence model, and emits JSON decisions.

**What it is not.** It never calls a model provider, never schedules work,
never launches a process, never pushes/merges/sends anything, and never
self-certifies a unit. It has no `subprocess`/`exec`/`eval` anywhere in the
module (`scripts/test_autonomy_controller.py::TestNoExecution` asserts
this). OpenClaw (or any caller) is responsible for actually doing the work;
this controller only decides whether a claimed transition is legal given
the evidence presented, and records the decision.

## Modes

`frozen`, `shadow`, `canary`, `limited`, `full`, `quarantined`, `complete`.
A work unit declares its `mode`; the controller validates it against this
fixed set but does not itself gate behavior differently per mode — mode is
part of the immutable work-unit contract for the caller to interpret.

## States and legal transitions

```
queued -> admitted -> running -> awaiting_verification -> verified -> merged -> post_merge_verified
```

Any of `queued`, `admitted`, `running`, `awaiting_verification`, `verified`
may also move to `rejected`, `blocked_operator`, `blocked_quota`, or
`expired` (terminal — the unit is closed and a new unit must be submitted).
`running`/`awaiting_verification`/`verified`/`merged` may additionally move
to `quarantined`. `post_merge_verified`, `rejected`, `blocked_operator`,
`blocked_quota`, `expired`, and `quarantined` are terminal — no outbound
transitions. See `TRANSITIONS` in the module for the exact adjacency map.

Only one work unit may be active at a time (`UNIT_ALREADY_ACTIVE`).

## Work-unit contract (immutable once admitted)

`unitId`, `unitClass`, `worktree`, `baseSha`, `allowedPaths`,
`allowedCommands` (must be a subset of the fixed `COMMAND_REGISTRY`),
`acceptanceComponents` (required evidence types), `reviewerIdentities`,
`quotaBudget` (`provider`, `remainingPercent`, optional `maxSpendPercent`).
`mode`, `status`, `correctionCount`, `repairVsReconstruction`,
`repairDecision`, and `evidenceLog` are controller-managed and mutate over
the unit's life; the fields above do not change after submission.

## Evidence model

Evidence components are typed: `deterministic`, `semantic`, `reviewer`,
`quota`, `merge`, `post_merge`, `notification_receipt`. Every component
needs `type`, a non-trivial `fingerprint`, and a numeric `submittedAt`.
The controller fails closed (returns a structured `errorCode`, changes
nothing) for:

| Condition | errorCode |
|---|---|
| not valid JSON / wrong shape | `MALFORMED_EVIDENCE` / `MALFORMED_STATE` |
| unknown evidence type or command | `UNKNOWN_EVIDENCE_TYPE` / `UNKNOWN_COMMAND` |
| required fields absent | `MISSING_EVIDENCE_FIELDS` / `MISSING_FIELDS` |
| older than its staleness window | `STALE_EVIDENCE` |
| same fingerprint+type resubmitted | `DUPLICATE_EVIDENCE` |
| same type, different outcome, no `supersedes` | `CONTRADICTORY_EVIDENCE` |
| quota evidence below configured floor | `QUOTA_INSUFFICIENT` |
| cumulative spend exceeds unit's budget cap | `OVER_BUDGET` |
| reviewer not in the unit's allowlist, or equals implementer | `REVIEWER_DENIED` |
| transition's required evidence types absent | `MISSING_REQUIRED_EVIDENCE` |
| state file changed since read (optimistic concurrency) | `CONCURRENT_MODIFICATION` |

No transition can be justified by narrative/free text alone — only the
listed structured fields are read for any decision.

## Anti-loop and correction limit

- A unit may use at most one correction (`correctionCount <= 1`,
  `CORRECTION_LIMIT_EXCEEDED` otherwise). A unit cannot start as a
  correction.
- Failure-class transitions (`rejected`, `blocked_operator`,
  `blocked_quota`, `quarantined`) require a structured `failureCategory` +
  `failingComponentType` + `failingComponentFingerprint`
  (`MISSING_FAILURE_EVIDENCE` otherwise).
- The fingerprint of a failure is `sha256` over only those structured
  fields (`failure_fingerprint()` / `structured_fingerprint()`) —
  rewording an explanation never changes it.
- On the 3rd consecutive closed unit of the same `unitClass` ending in a
  failure state, a repeat of the *same* failure fingerprint is blocked
  (`ANTI_LOOP_BLOCKED`); a genuinely new fingerprint (new failing
  evidence) is allowed through.

## Repair vs. reconstruct

`repairVsReconstruction` starts `undecided`. Once set to `repair` or
`reconstruct` via `set_repair_decision()`, it is immutable
(`REPAIR_DECISION_IMMUTABLE`) unless reopened with an approved trigger:
`new_failure_evidence`, `new_input_evidence`, or `operator_override`. Every
reopen is appended to `repairDecision.reopenHistory`, so the decision
history is append-only and auditable.

## Command registry

`COMMAND_REGISTRY` is a fixed dict of command *names* (e.g. `run_tests`,
`gh_pr_merge`) the controller recognizes for evidence-provenance checks.
The controller never executes any of them — it only validates that a work
unit's `allowedCommands` and evidence's `commandUsed` are drawn from this
closed set, never an arbitrary shell string.

## CLI

```
python3 scripts/autonomy_controller.py --state-file <path> show
python3 scripts/autonomy_controller.py --state-file <path> submit <unit.json>
python3 scripts/autonomy_controller.py --state-file <path> transition <to_state> [--evidence-file <evidence.json>]
python3 scripts/autonomy_controller.py check-fixture <fixture.json>
```

`check-fixture` is read-only: it validates a migration/shadow fixture's
shape against the live schema without ever writing to it or to any live
state file. See `scripts/fixtures/autonomy_controller_shadow_fixture.json`
for an example.

State writes use atomic rename plus optimistic concurrency: `save_state`
re-reads the file immediately before writing and fails closed
(`CONCURRENT_MODIFICATION`) if another process already advanced it.

## Rollback

The controller only touches its own state file (default
`scripts/.autonomy_controller_state.json`, gitignored) and the explicit
fixture/unit/evidence JSON files passed on the command line. To roll back,
delete or restore a prior copy of the state file — no other repository
state is touched by this module.

## Tests

```
npm run test:autonomy-controller
```

runs `scripts/test_autonomy_controller.py`, which includes adversarial
cases for malformed/unknown/missing/stale/duplicate/contradictory/
over-budget/denied evidence, illegal transitions, the correction limit,
the anti-loop gate (including the "new fingerprint still allowed" case),
repair-decision immutability, and the read-only fixture check.

## Known limitations

- This is a decision engine only; it has no knowledge of real Git/GitHub
  state and trusts whatever evidence payload it is given. Wiring it to
  real CI/PR state so evidence can't be fabricated is a separate,
  un-implemented integration step.
- Single active unit, single state file, no multi-tenant concurrency beyond
  optimistic-concurrency detection (it fails closed on a race; it does not
  queue or merge concurrent writers).
- No deployment, canary, or production-traffic proof is implemented or
  claimed here — `mode` values above `shadow` are accepted and validated
  but the controller does not itself enforce canary traffic percentages or
  similar; that remains the caller's responsibility.
