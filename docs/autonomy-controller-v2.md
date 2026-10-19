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

## Shadow-mode OpenClaw integration adapter

`scripts/autonomy_shadow_adapter.py` gives a caller (OpenClaw agent or
automation) one narrow, read-only entry point to ask "what would the
controller decide for this candidate work unit right now" without ever
executing a command, launching an agent, mutating Git/GitHub, mutating an
automation, or touching the live remediation ledger
(`scripts/.autonomy_controller_state.json`).

It never opens the live state file for writing. The `productContractId` and
`campaignId` the adapter will simulate against are fixed constants in the
module (`yoma-product-acceptance-v2` / `mysugya-yoma-remediation`) — they are
never trusted from the caller's request. On each `simulate` call it:

1. Reads a single JSON request (candidate work unit + quota/evidence
   snapshot + `productContractId`/`campaignId`/`repoSha` binding).
2. Rejects, before loading any state or simulating anything, a request whose
   `productContractId` or `campaignId` does not exactly equal the adapter's
   fixed constants (`errorCode: CONTRACT_BINDING_MISMATCH`). The adapter
   always binds against its own fixed IDs, never the caller-supplied values.
3. Verifies the request's `repoSha` matches this repo's actual current
   `git rev-parse HEAD` (`REPO_SHA_MISMATCH` otherwise) — a stale or
   wrong-repo request is rejected, not silently simulated against the wrong
   commit.
4. Builds a brand-new, in-memory controller state, or an in-memory copy of
   an explicitly supplied `readStatePath` snapshot. `readStatePath` (like
   `--output-state`, below) must resolve beneath the fixed sandbox root
   `/tmp/mysugya-autonomy-shadow`; a path outside that root, a symlink that
   escapes it, or a reserved remediation-state basename
   (`.autonomy_controller_state.json`, `remediation-progress.json`,
   `remediation-hold.json`) is rejected before the file is ever opened
   (`errorCode: PATH_OUTSIDE_SANDBOX_ROOT` / `FORBIDDEN_PATH_BASENAME`). If
   the snapshot inside the sandbox is bound to a different
   `productContractId`/`campaignId` than the adapter's fixed constants, the
   adapter fails closed (`errorCode: CROSS_CONTRACT_READ_STATE_REJECTED`)
   and leaves the file untouched — it never silently discards the mismatched
   snapshot and substitutes empty state. Campaign mode is force-set to
   `"shadow"` regardless of what the request or snapshot claims.
5. Runs `bind_contract` -> `submit_unit` -> (optional) `admitted` transition
   -> (optional) one additional requested transition entirely through the
   real controller module, so every existing fail-closed rule (schema,
   evidence, scope, anti-loop, contract fingerprint, command registry,
   etc.) applies unmodified.
6. Refuses, before calling the controller, any requested transition that is
   mutating under shadow mode (`verified`, `merged`, `post_merge_verified`)
   with `errorCode: SHADOW_FORBIDS_MUTATING_TRANSITION`, and any per-unit
   `mode` field (`errorCode: FORBIDDEN_UNIT_FIELD` — mode is
   adapter/controller-authoritative, never caller-supplied).
7. Emits exactly one JSON decision report to stdout. It writes a state
   artifact to disk only if the caller passes `--output-state`, and that
   path is subject to the same fixed-sandbox-root, symlink, traversal, and
   forbidden-basename checks as `readStatePath` above, checked before any
   evidence validation runs. The write itself is atomic (temp file +
   `os.replace`), fsyncs the temp file and its parent directory before the
   rename when the platform allows it, cleans up the temp file on any
   write error, and refuses outright (`errorCode: OUTPUT_IS_SYMLINK`) to
   write through a path that is already an existing symlink.

Standard library only. No arbitrary subprocess execution: the only
shell-adjacent action is the read-only `git rev-parse HEAD`.

### CLI

```
python3 scripts/autonomy_shadow_adapter.py simulate <request.json> [--repo-root <path>] [--output-state <path>]
```

See the module docstring in `scripts/autonomy_shadow_adapter.py` for the
exact request shape, and
`scripts/fixtures/controller_shadow_integration_fixture.json` for a template
(fill in the `FILL_IN_EXACT_GIT_HEAD_SHA` placeholders with the repo's actual
current `git rev-parse HEAD` before using it — a baked-in sha would go stale
on the next commit).

### Tests

```
npm run test:autonomy-shadow-adapter
```

runs `scripts/test_autonomy_shadow_adapter.py`, which includes adversarial
cases for: repo-sha mismatch; a caller-supplied `productContractId` or
`campaignId` that does not exactly match the adapter's fixed constants
(rejected before any state is loaded or simulated, including a
plausible-looking-but-wrong other ID); forbidden per-unit `mode`; forbidden
mutating transitions (`verified`, `merged`, `post_merge_verified`);
unregistered commands and out-of-scope changed paths; a cross-contract
`readStatePath` snapshot inside the sandbox (fails closed without silently
substituting empty state, and leaves the file untouched); `--output-state`
and `readStatePath` values outside the fixed sandbox root
(`/tmp/mysugya-autonomy-shadow`); `..` traversal outside that root; a
symlink whose target escapes the root; refusal to target any reserved
remediation-state basename (the live controller ledger, remediation
progress, or remediation hold filenames) on `--output-state`; refusal to
write through a path that is itself an existing symlink, even when that
symlink's target also resolves inside the sandbox root; atomic-write
temp-file cleanup on a write error; and confirmation that a simulation
never writes to or mutates an existing live state file it was pointed at
via `readStatePath`.

### Known limitations (adapter-specific)

- This adapter inherits every limitation of `scripts/autonomy_controller.py`
  below — it is a read-only simulation wrapper, not a separate decision
  engine.
- It does not itself gate *known, registered* commands (e.g. `gh_pr_merge`)
  by campaign mode at submission time; that remains the already-merged
  controller's command-registry policy, which this bounded integration does
  not change.
- It simulates at most one requested transition per call (plus the implicit
  `admitted` step); a caller wanting to preview a multi-step sequence must
  call it once per step, chaining `--output-state` into the next call's
  `readStatePath`.
- The fixed-root sandbox restriction (`/tmp/mysugya-autonomy-shadow`) and the
  pinned `productContractId`/`campaignId` constants mean this adapter can
  only ever simulate against the one product contract and campaign it is
  built for; using it for a different contract or campaign requires editing
  the module's constants, not a request-time parameter.
- The existing-symlink check on `--output-state`/`readStatePath` inspects the
  literal requested path only; it does not protect against a TOCTOU race
  where the path is replaced with a symlink between the check and the
  eventual write. The write itself is atomic (temp file + `os.replace`), but
  the pre-check and the write are not a single atomic operation.
- `readStatePath` and `--output-state` share the same sandboxed-path helper,
  so an existing symlink at either literal path is rejected regardless of
  where its target resolves, even though only `--output-state` is ever
  written to; this is stricter than defect-fix #5 strictly required but
  keeps the two paths' validation identical rather than subtly diverging.

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
