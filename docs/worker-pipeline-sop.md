# MySugya Worker Pipeline: Standard Operating Procedure

The canonical process for ALL bounded data/tooling work in this
repository, proven on the Yoma pilot (VERSION 15.75 through 15.82) and
intended to be reused for every future tractate/module. Companion
references:

- docs/reports/task-type-reference.md - all task types (generated;
  regenerate with `npm run worker:docs`)
- docs/reports/schema-coverage-matrix.md - all schema paths (generated)
- docs/reports/schema-pipeline-coverage.md - coverage report, dry runs,
  readiness matrix, roadmap
- docs/worker-pipeline.md - pipeline design history and policies
- docs/rashi-workflow.md - Rashi-specific enforcement details
- docs/yoma-pilot-lessons.md - why this process exists
- docs/new-tractate-onboarding.md - starting a new module

## The universal loop

Every pass, regardless of task type, is exactly this:

```
1  npm run worker:manifest  -- --type <type> [--module yoma] [--range <daf|a-b>] \
                               [--authorize <flag>] --out .worker-manifest.json
2  npm run worker:preflight -- --manifest .worker-manifest.json     # STOP on failure
3  npm run worker:packet    -- --manifest .worker-manifest.json     # sole context source
4  npm run worker:prompt    -- --manifest .worker-manifest.json     # if handing to a worker
5  perform ONLY the edits the manifest allows
6  run the manifest's generationCommands (if any), e.g.
     cd modules/yoma && python3 scripts/build_learning_data.py
     cd modules/yoma && python3 scripts/build_literal_layer.py --apply
7  bump VERSION one patch; python3 scripts/sync_version.py
8  npm run worker:verify -- --manifest .worker-manifest.json --fast
9  npm run worker:verify -- --manifest .worker-manifest.json --full
10 commit (INCLUDING .worker-manifest.json), push -u, open ONE PR
11 wait for CI (build job runs validate:offline:yoma, the Rashi scope
   check, and the worker manifest check)
12 merge ONLY when green AND only if the task type does not require
   Fable review (fableReviewRequired types: request review, do not merge)
13 verify Deploy Cloudways Branch and Deploy GitHub Pages for the merge
   commit
14 npm run worker:report -- --manifest .worker-manifest.json ; fill the
   PR/merge/deploy fields; post the JSON verbatim
15 stop and await the next authorization
```

Direct gate commands, when needed individually: `validate:offline:yoma`
(all nine offline gates), `check:generated:yoma` (freshness),
`worker:scope` (scope only), `worker:schema-matrix` (registry/inventory
consistency), `worker:docs` (regenerate reference docs).

## Model roles (non-negotiable)

- Fable: owns the pipeline, schema, validators, registry, allowlist
  growth, structure edits, new task types, workflow and docs changes,
  branch cleanup, process hardening, and every escalation. Fable is
  the REVIEWER for semantic daf PRs, not the worker: Fable does not
  perform ordinary daf content work, and acts as the semantic worker
  only when explicitly substituting because Sonnet is unavailable.
- Sonnet: the default WORKER for all semantic daf work: Hebrew/Rashi
  translation, placement judgments, shifted-daf realignment, and
  fabricated-daf reconstruction (rashi-realignment and
  rashi-reconstruction carry model: sonnet in the registry; Haiku is
  not allowed on them). Sonnet may also review or escalate.
- Only Fable/Sonnet may issue manifests carrying --authorize flags or
  run with RASHI_ALLOWLIST_RESTRUCTURE=1.
- Haiku (or another small model): executes mechanical bounded tasks
  strictly inside a generated manifest/prompt/packet, and only where
  the task type's model field says haiku (haiku-safe). Haiku CANNOT:
  take a sonnet or fable task; add allowlist or baseline entries;
  authorize structure edits; override, weaken, or reinterpret a
  validator; edit the registry, validators, workflows, or hooks; merge
  a fableReviewRequired PR without review. Haiku CAN poll CI/deploy
  mechanically, but only after local `worker:verify --full` has passed.
- A red gate always means the content or scope is wrong. The only two
  legal responses are: fix your own work, or stop and escalate.

## Operator quickstart (what do I paste to Haiku?)

1. Pick the task type from docs/reports/task-type-reference.md; check
   the readiness matrix in docs/reports/schema-pipeline-coverage.md says
   Haiku may take it.
2. Generate and commit nothing yet; run:
   `npm run worker:manifest -- --type <type> --module yoma --range <daf> --out .worker-manifest.json`
   `npm run worker:prompt -- --manifest .worker-manifest.json`
3. Paste the generated prompt to the worker verbatim. Do not hand-write
   or embellish worker prompts.
4. Reading failures:
   - preflight failure lines say exactly what is unsafe (dirty tree,
     inactive hooks, stale generated data, paused type, non-repair task
     on an allowlisted daf). Fix the environment or re-scope; never
     bypass.
   - verify failure prints per-gate PASS/FAIL plus JSON-pointer scope
     errors and allowlist deltas. An added allowlist entry is always the
     worker's error.
5. CI states: a CANCELLED run (pages concurrency group superseding an
   older run during sequential merges) is not a failure; only the latest
   commit's runs must be green. The native "pages build and deployment"
   tracker lags the two named Deploy workflows by a few minutes; the
   named workflows are authoritative.
6. Escalate to Fable when: any stop condition in the prompt fires, a
   gate stays red after fixing content, the worker proposes touching an
   out-of-scope file, or anything requires an --authorize flag.
7. Final report: `npm run worker:report`, fill in PR/merge/deploy, post
   verbatim. One compact block; no narration.

## Branch hygiene (standard cleanup rule)

- After a worker PR merges AND the two main deploy workflows are green
  for the merge commit, delete the merged worker branch (remote).
- Do not leave stale claude/* worker branches around; a branch whose
  head is reachable from main and whose PR is merged or closed is
  cleanup debt.
- NEVER delete: main; the cloudways branch (deploy target of the
  Deploy Cloudways Branch workflow); any branch that is the head of an
  OPEN pull request.
- If a branch's status is uncertain (head not reachable from main, no
  associated PR, unclear owner), report it instead of deleting it.
- Branch cleanup is Fable's job (a hygiene/tooling pass), not a worker
  task.
- Remote-session credentials may be push-scoped to the designated
  branch only (branch deletion returns 403). In that case Fable
  produces the classified deletion list and the repository admin
  deletes via the GitHub branches page, which marks merged branches
  itself.

## Consistency policies (single source summary)

- VERSION: one patch bump per PR via VERSION + scripts/sync_version.py;
  never hand-edit package.json versions. Data-layer versions are
  separate.
- Generated files (learning_data.js, coverage.json): regeneration only;
  the freshness gate proves byte-identity in CI, the hook, and verify.
- No em dashes or en dashes in any project-authored output (CLAUDE.md
  rule; enforced for helper English by the content gate and for changed
  files by worker:verify).
- Content PRs never touch workflow files; workflow edits require a
  docs-tooling manifest (CI-enforced).
- Allowlists/baselines only shrink; growth requires
  RASHI_ALLOWLIST_RESTRUCTURE=1 in a Fable tooling PR (CI-enforced).
- Branch protection (admin, manual): require PR; required check `build`
  (it contains all offline gates plus both scope checks); require
  up-to-date branches; block force pushes; restrict bypass. Do not
  enable worker auto-merge before this is configured.
- Drift gate: `audit:rashi:drift:yoma` classifies every daf (SHIFTED /
  FABRICATION-SUSPECT / ALIGNED / INSUFFICIENT-ANCHORS). Repair-type
  preflight (rashi-repair, placeholder-backfill) FAILS on a daf that is
  not haiku-safe; the remedies are rashi-realignment (shifted) and
  rashi-reconstruction (fabricated), Sonnet worker by default with
  Fable review (Fable substitutes as worker only when Sonnet is
  unavailable). Override is Fable-only: manifest authorizeDriftOverride
  plus FABLE_DRIFT_OVERRIDE=1. Tests: npm run test:drift:yoma (in npm
  test).
- Known deferred content debt lives in docs/rashi-audit-backlog.md:
  61a lines 1-45 fabricated (rashi-reconstruction, Fable/Sonnet);
  67b/68a/68b/70a/71b shifted-compressed (rashi-realignment,
  Fable/Sonnet; stub-only repair FORBIDDEN there, drift gate enforces);
  41a shifted block (+42a L50 lead); 8a/9a phantom counts; 77a-88a
  filler; plus the drift-profile triage backlog recorded at VERSION
  15.85. 47a+ reconstruction is paused until the debt is drained.
  Nekudot is paused in the registry pending validator design.
