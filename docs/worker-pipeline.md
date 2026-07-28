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
  registry is a pipeline change: Sonnet only, via a docs-tooling
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

Task types (17 as of VERSION 15.82): rashi-repair, rashi-reconstruction,
placeholder-backfill, gemara-learning, display-only-edit,
learning-copy-edit, glossary-edit, quiz-edit, summary-edit,
structural-repair, metadata-review-status, literal-layer,
generated-refresh, audit-only, docs-tooling, deployment-verify, and
nekudot (PAUSED). The authoritative per-type reference is generated:
docs/reports/task-type-reference.md (`npm run worker:docs`). The
canonical process document is docs/worker-pipeline-sop.md.

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
  RASHI_ALLOWLIST_RESTRUCTURE=1 (docs-tooling PRs only).
- Workers stop and escalate on semantic uncertainty; Sonnet owns
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

Historical snapshot, not re-verified row by row since. Several items below
(61a stubs, 7a/9b-adjacent work) have since completed - see
`docs/rashi-audit-backlog.md` for current per-daf status and
`docs/reports/rashi-association-audit.md` for the current Rashi
linked-association/renderer-readiness state (8/8; linked renderer became
the production default at VERSION 15.338)
rather than trusting this table's specifics.

| Work item | Task type | Model | Batch | Mechanical tier? | Notes |
|---|---|---|---|---|---|
| 61a stubs (L46-64) | rashi-repair | sonnet | 1 daf/PR | yes | mechanical; packet lists exact lines |
| 67b/68a/68b/70a/71b stubs | rashi-repair | sonnet | 1 daf/PR | yes | after 61a merges green |
| 41a shifted block (+42a L50 lead) | rashi-repair (shifted-block prompt) | sonnet | 1 daf/PR | no | semantic re-derivation; use rashi:prompt:yoma --task shifted-block |
| 8a/9a phantom counts | rashi-structural-repair (--authorize allowStructure) | sonnet | 1 daf/PR | no | entry deletion needs explicit structure authorization |
| 77a-88a filler (~765 lines) | placeholder-backfill | sonnet | 1 daf/PR, then 2-3 | yes | worker executes packets; independent Sonnet review before merge |
| 47a+ reconstruction | rashi-reconstruction | sonnet | 1 daf/PR | no | conditional review gate; resume only after defect backlog drained |
| Gemara-learning edits | gemara-learning | sonnet | 1 daf/PR | no | field-level jsonScope gate active since 15.81/15.82; passes require operator authorization and a fresh manifest (Rashi gate hands off to the worker gate) |
| literal/en_lit refresh | literal-layer | sonnet | range | yes | mechanical; literal gate protects coverage |
| Nekudot/vowelization | nekudot | sonnet | n/a | no | PAUSED in registry; needs validator design first |
| Docs/tooling | docs-tooling | sonnet | n/a | no | pipeline integrity work |
| Generated refresh | generated-refresh | sonnet | n/a | yes | freshness gate proves output |
| Deploy verification | deployment-verify | sonnet | n/a | yes | read-only lifecycle: no VERSION bump, no PR |

## Hardening pass (VERSION 15.81): project-data-safe gates

- Gemara-learning field gate: `worker:scope` now performs a strict JSON
  diff for gemara-learning PRs with exact JSON-pointer errors. Mutable:
  sugyot[*].display.{whats,hint,title}, learning.{ahaMoment,memoryAnchor,
  learnerQuestion,coreTension,coreMove,learningBlocker}, and
  learning.takeaway.text. Everything else (rashiTranslations, any he,
  ids, lineRange, argumentFlow, takeaway.type, glossary, quizSeeds,
  metadata) is immutable unless the manifest carries an explicit
  authorization flag (--authorize authorizeGlossary / authorizeQuizSeeds /
  authorizeTakeawayType / allowStructure; operator-issued only). Cross-daf
  edits fail: every changed learning JSON must be a manifest target.
  The Rashi scope gate hands field enforcement for such PRs to this gate
  ONLY when a fresh gemara-learning manifest is part of the PR (both
  gates run in the same CI job; without the manifest full Rashi rules
  apply, so nothing is weakened).
- Placeholder-backfill: maxBatch 2 enforced at manifest generation and at
  scope time; `worker:verify` prints a per-daf allowlisted-lines
  before/after completion summary and hard-fails if the content
  allowlist grew for a target daf.
- Literal-layer: verify reports the coverage lines and impacted
  literal_en file count; scope fails generated-output changes that have
  no literal_en source change (use generated-refresh for that).
- Generated-refresh: scope fails if any modules/yoma/assets source file
  changed alongside the generated outputs.
- New task type audit-only: read-only audits (corpus scans, semantic
  reports, validator dry runs, backlog reconciliation). May write only
  docs/reports/* artifacts and backlog process notes; CI fails an
  audit-only PR that touches any content, script, or workflow file.
- Manifest lifecycle: a manifest is per-PR (stale copies identical to the
  base do not count); targets must cover every changed learning JSON;
  optional authorizations are validated against the registry at
  generation time; maxBatch is embedded in the manifest.
- Machine-readable final report: `npm run worker:report -- --manifest
  .worker-manifest.json` emits the JSON report template prefilled with
  task type, targets, VERSION, branch, changed files, and allowlist
  delta; the worker fills PR/merge/deploy fields and posts it verbatim.
- Independent review gate: task types flagged independentReviewRequired
  (rashi-reconstruction, placeholder-backfill, gemara-learning) print a
  REVIEW GATE notice in verify output: the worker may open the PR and
  poll CI but may NOT merge; an independent Sonnet review comes first. This is a procedural
  gate; enable branch-protection required reviews to make it mechanical.

## Schema-wide coverage (VERSION 15.82)

Every schema-controlled path in Yoma learning JSON is now classified in
scripts/worker_schema_scope.json (85 paths) and mechanically
cross-checked against the registry by `npm run worker:schema-matrix`
(also run inside ci-check on every manifest-bearing PR). The scope gate
is a generic jsonScope engine: per-type mutable path patterns, flag
authorizations, structure detection with exact JSON pointers. Seven new
task types cover the previously unowned paths: display-only-edit
(mechanical tier), learning-copy-edit, glossary-edit, quiz-edit,
summary-edit, structural-repair (allowStructure required), and
metadata-review-status (all judgment-required). See
docs/reports/schema-pipeline-coverage.md for the full matrix, the
15-case negative-test battery, the 12 dry runs, the worker operating
envelope, and the roadmap.
