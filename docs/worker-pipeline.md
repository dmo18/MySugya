# MySugya worker pipeline: bounded task automation

Project-wide generalization of the guarded Rashi workflow (see
docs/rashi-workflow.md, which remains authoritative for Rashi
specifics). One registry, one driver, six commands. Added at VERSION
15.80.

## Components

- `scripts/worker_task_types.json` - the task-type registry: scope
  contract per type (allowed files, allowed JSON paths, allowlist and
  structure policy, required validators, generation and test commands,
  escalation triggers, recommended model, paused flag). Editing the
  registry is a pipeline change: Fable/Sonnet only, via a docs-tooling
  PR.
- `scripts/worker_pipeline.py` - the driver. Rashi task types delegate
  to the proven Rashi tooling; nothing is duplicated or weakened.

## Commands

```
npm run worker:manifest  -- --type <type> [--module yoma] [--range 61a|77a-78b] [--out .worker-manifest.json]
npm run worker:preflight -- --manifest .worker-manifest.json [--dry-run]
npm run worker:packet    -- --manifest .worker-manifest.json
npm run worker:prompt    -- --manifest .worker-manifest.json
npm run worker:verify    -- --manifest .worker-manifest.json --fast|--full
npm run worker:scope     -- --manifest .worker-manifest.json [--base REF]
```

Task types: rashi-repair, rashi-reconstruction, placeholder-backfill,
gemara-learning, literal-layer, nekudot (PAUSED), docs-tooling,
generated-refresh, deployment-verify.

## The loop (any task type)

1. Operator generates the manifest and commits to a work branch as
   `.worker-manifest.json` (repo root). The manifest is PER PR: each PR
   must bring its own; a stale manifest identical to the base does not
   count.
2. Worker runs preflight (STOP on failure), then packet (sole context),
   performs only the manifest-scoped edits, regenerates, bumps VERSION,
   syncs, runs verify --fast then --full, commits the manifest with the
   work, opens one PR.
3. CI runs: the 9 Yoma offline gates, the Rashi PR scope check, and the
   worker manifest check (`worker_pipeline.py ci-check`). A PR that
   changes module content without a manifest fails. A PR that changes
   workflow files without a docs-tooling manifest fails.
4. Merge only when green; verify Deploy Cloudways Branch and Deploy
   GitHub Pages for the merge commit; report; stop.

## Rules carried over from the Rashi workflow (all task types)

- Workers may not override, weaken, or reinterpret any validator.
- Workers may never ADD allowlist or baseline entries; the ratchet is
  enforced on every PR. Authorized restructuring requires
  RASHI_ALLOWLIST_RESTRUCTURE=1 (Fable-run tooling PRs only).
- Workers stop and escalate on semantic uncertainty; Fable/Sonnet owns
  Hebrew translation, placement judgment, validator design, schema and
  pipeline changes, and ambiguous repairs.
- Generated files (`learning_data.js`, `coverage.json`) change only via
  regeneration; the freshness gate proves it.
- VERSION: one patch bump per PR, always via sync_version.py. Data-layer
  versions (DATA_VERSION, manifest dataVersion) are managed separately.

## Batching policy

- One daf per PR is MANDATORY for: repairs of documented defects,
  shifted-block work, structure-affecting passes, and the first PR of
  any new task type (shakedown).
- 2-3 daf per PR is permitted for: routine reconstruction or backfill
  once the same task type has merged green at least twice consecutively,
  and never across perek boundaries.
- Merges are strictly sequential (wait for merge + deploy verification
  before starting the next PR); parallel content PRs caused the
  cancellation/conflict churn documented in the backlog.

## Failure recovery

- CI red on your PR: read the failing gate's output; fix your own
  content or scope; never adjust gates/baselines. If you cannot fix it
  by correcting your work, STOP and escalate.
- Deploy workflow red on main after merge: re-run the workflow once
  (transient infra); if still red, escalate immediately; do not stack
  further merges on a red main.
- Superseded/cancelled intermediate deploys (the `pages` concurrency
  group cancels older runs when merges land quickly): expected; only the
  LATEST commit's deploys must be green.
- Native "pages build and deployment" tracker: lags the Deploy GitHub
  Pages workflow by up to a few minutes; treat the two named Deploy
  workflows as authoritative and the tracker as eventually-consistent.

## Recommended GitHub branch protection (manual admin settings)

Not settable from repo code; configure at Settings > Branches > main:

- Require a pull request before merging: ON (no direct pushes)
- Require status checks to pass: ON; required check: `build`
- Require branches to be up to date before merging: ON
- Block force pushes: ON; Restrict deletions: ON
- Restrict who can bypass required checks: admins only (or nobody)
- Auto-merge: safe to enable ONLY with the above required checks, since
  `build` includes all offline gates, the Rashi scope check, and the
  worker manifest check; workers should still merge explicitly to keep
  the sequential-merge discipline observable.

## Readiness matrix (as of VERSION 15.80)

| Work item | Task type | Model | Batch | Haiku now? | Notes |
|---|---|---|---|---|---|
| 61a stubs (L46-64) | rashi-repair | haiku | 1 daf/PR | YES | first Haiku shakedown; packet lists exact lines |
| 67b/68a/68b/70a/71b stubs | rashi-repair | haiku | 1 daf/PR | YES | after 61a merges green |
| 41a shifted block (+42a L50 lead) | rashi-repair (shifted-block prompt) | fable/sonnet | 1 daf/PR | NO | semantic re-derivation; use rashi:prompt:yoma --task shifted-block |
| 8a/9a phantom counts | rashi-repair + --allow-structure | fable | 1 daf/PR | NO | entry deletion needs explicit structure authorization |
| 77a-88a filler (~765 lines) | placeholder-backfill | haiku-with-fable-review | 1 daf/PR, then 2-3 | PARTIAL | Haiku executes packets; Fable reviews semantic report pre-merge |
| 47a+ reconstruction | rashi-reconstruction | haiku-with-fable-review | 1 daf/PR, then 2-3 | PARTIAL | resume only after defect backlog drained |
| Gemara-learning edits | gemara-learning | fable | 1 daf/PR | NO | field-level gate pending; CI's Rashi gate currently rejects such diffs by design until an authorized pipeline update |
| literal/en_lit refresh | literal-layer | haiku | range | YES | mechanical; literal gate protects coverage |
| Nekudot/vowelization | nekudot | fable | n/a | NO | PAUSED in registry; needs validator design first |
| Docs/tooling | docs-tooling | fable | n/a | NO | pipeline integrity is Fable's job |
| Generated refresh | generated-refresh | haiku | n/a | YES | freshness gate proves output |
| Deploy verification | deployment-verify | haiku | n/a | YES | read-only |
