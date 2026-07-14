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
12 merge rule, by the task type's review policy:
   - reviewPolicy fable: request Fable review, do NOT merge
   - reviewPolicy conditional (rashi-realignment, rashi-reconstruction):
     record the fresh post-edit self-review in .worker-self-review.json,
     run `npm run worker:review -- --manifest .worker-manifest.json`,
     and merge WITHOUT further authorization only when it prints
     AUTO-MERGE-ELIGIBLE and CI is green on the exact final head; any
     failed condition escalates to Fable and blocks the merge
   - no policy: merge when green
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
  branch cleanup, process hardening, and every escalation. Since
  VERSION 15.93 Fable is NOT the routine per-PR reviewer for semantic
  daf work: Fable reviews a semantic PR only when an escalation
  condition fires (see the conditional review section below). Fable
  acts as the semantic worker only when explicitly substituting
  because Sonnet is unavailable.
- Sonnet: the default WORKER for all semantic daf work: Hebrew/Rashi
  translation, placement judgments, shifted-daf realignment, and
  fabricated-daf reconstruction (rashi-realignment and
  rashi-reconstruction carry model: sonnet in the registry; Haiku is
  not allowed on them). On those two types Sonnet also performs the
  fresh post-edit self-review, runs the worker:review auto-merge gate,
  merges when eligible and CI is green, verifies deployment, and
  proceeds to the next queued target; it escalates to Fable on any
  escalation condition instead of merging.
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
- NO model, at any tier, direct-pushes tracked changes to main. Main
  moves only by validated PR merges; any workflow that would end with a
  tracked post-merge change is a design defect to escalate, not a
  reason to push.

## Conditional semantic review and autopilot queue (VERSION 15.93)

rashi-realignment and rashi-reconstruction carry `reviewPolicy:
"conditional"` with `escalationModel: "fable"` in the registry. The
unconditional per-PR Fable review is removed; in its place stand a
mandatory fresh self-review and a machine-checked auto-merge gate. No
hard validation gate was weakened: scope, freshness, content, link,
repetition, drift, and schema checks all still block CI exactly as
before.

A semantic PR may auto-merge (no Fable, no operator sign-off) only when
ALL of these hold. `npm run worker:review -- --manifest
.worker-manifest.json` machine-checks the first thirteen and prints
AUTO-MERGE-ELIGIBLE or ESCALATE with the exact failed conditions:

1. single-target-manifest: the manifest carries exactly one daf
2. exactly-one-authorized-daf-changed: only that daf's learning JSON
   changed
3. scope-clean-no-structure-no-hebrew-no-forbidden-fields: the hard
   Rashi scope validator passes (no structure/count changes, no he
   edits, no Gemara-learning fields)
4. no-allowlist-additions: nothing added to any allowlist or baseline
5. allowlist-removals-limited-to-target-daf: removals only for the
   target daf (the content gate re-derives violations, so a removal
   that leaves the gate green was validator-stale by construction)
6. packet-contains-every-linked-local-id: the live packet segment
   table (Gemara AND Mishnah kinds) contains every linked id
7. all-links-legal-and-nonempty: every entry links to legal local ids
8. drift-profile-ALIGNED: post-edit profile is ALIGNED (not merely
   haiku-safe)
9. semantic-audit-zero-shift-candidates on the target daf
10. no-stub-or-duplicate-helpers in the target daf
11. generated-files-fresh (byte-identical regeneration)
12. version-metadata-synced (VERSION == package.json == lock)
13. fresh-self-review-committed-and-clean: .worker-self-review.json is
    part of THIS PR's diff, names the target daf, ticks every required
    recheck, and reports no blockers

Plus two procedural conditions the worker satisfies in the loop:
worker:verify --fast and --full both passed on the head, and CI is
green on the exact final head at merge time. Semantic-versus-positional
linking is enforced three ways: the packet/prompt contract, the ALIGNED
drift profile plus zero shift candidates, and the self-review
attestation.

The fresh self-review is performed AFTER the edit, rereading the raw
Hebrew and the packet's full segment text from scratch (never reusing
the working assumptions of the edit pass), and explicitly rechecks:
beginning, middle, and tail; every citation anchor; every multi-id
link; truncated boundary entries; every formerly allowlisted entry;
semantic versus positional linking; and no unrelated final-id fallback.
Format (committed with the PR as .worker-self-review.json):

```json
{"daf": "71b", "model": "sonnet",
 "rechecked": {"beginningMiddleTail": true, "citationAnchors": true,
   "multiIdLinks": true, "truncatedBoundaryEntries": true,
   "formerlyAllowlistedEntries": true, "semanticNotPositional": true,
   "noUnrelatedFinalIdFallback": true},
 "blockersFound": [], "notes": "one line"}
```

Escalation to Fable is MANDATORY (stop, do not merge) when any of
these occur: required packet id missing or packet text truncated or
incomplete; structure or count mismatch not already baselined;
allowlist growth would be needed; validator or workflow modification
would be needed; semantic uncertainty remains after rereading the
sources; post-edit drift profile not ALIGNED; a semantic audit shift
candidate remains; a link cannot be justified from local segment text;
the self-review finds a blocker; CI or full verification fails after
one bounded correction attempt; fields outside the manifest would be
needed; more than one daf would change in the same content PR.

Autopilot queue (`npm run worker:queue`): an ordered multi-daf plan
executed strictly one PR per target with sequential
CI/merge/deploy-verification between targets, stop-on-escalation.

```
npm run worker:queue -- --type rashi-realignment --module yoma --targets 71b,41a
npm run worker:queue                       # status + next target's commands
```

Queue lifecycle (VERSION 15.96): the tracked .worker-queue.json is an
IMMUTABLE definition (type, module, ordered targets, policy), committed
once alongside the first target's manifest commit and never written
again. Progress is DERIVED, not stored: a target is complete exactly
when its single-target manifest of the queue's type/module is the
manifest merged at origin/main; under the enforced sequential
one-PR-per-target process, everything at or before that target is
done. Consequences, all mechanically enforced and tested:

- there is no --advance and no runtime state to mutate; completing the
  final target leaves a CLEAN tree, and no queue bookkeeping ever needs
  a commit, let alone a direct push to main
- a merely-local (unmerged) manifest, a foreign-type manifest, an
  out-of-queue target, or a multi-target manifest is never evidence, so
  failed or escalated targets can never become done and progress cannot
  be advanced early or out of order
- resuming after a container/session recycle needs only a fresh clone:
  derivation is a pure function of the tracked definition and
  origin/main

The queue never batches daf into one PR (maxBatch 1 stands on both
conditional types) and never skips deploy verification. On escalation
the queue simply stops where it is; Fable resolves, then the queue
resumes. Tests: `npm run test:policy` (part of `npm test`) covers the
policy positively (all conditions green needs no Fable) and negatively
(every single failed condition blocks the merge), the prompt text, the
queue derivation mechanics, and the no-direct-push guarantees.

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

- Automation NEVER direct-pushes tracked changes to main. Every change
  to main arrives through a validated PR merge. No worker, autopilot,
  or queue step may produce a tracked post-merge change that would
  require a direct push (the queue derives progress from merged PRs for
  exactly this reason; enforced by test:policy). Model roles: this
  applies equally to Haiku, Sonnet, and Fable.
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
- Semantic linking contract (VERSION 15.91, from the PR #80 review
  finding): the Rashi work packet's legal id table carries every
  kind-bearing local segment, Gemara AND Mishnah, in source order,
  with kind and full untruncated Hebrew text; sparse and suffixed ids
  are preserved verbatim. linkedGemaraLineIds are semantic text
  anchors matched against that full text; positional assignment by
  vilna line number is forbidden in every generated packet and prompt,
  and an unidentifiable target segment is an escalation trigger on all
  four Rashi task types. Tests: npm run test:packet:yoma (in npm
  test).
- Drift gate: `audit:rashi:drift:yoma` classifies every daf (SHIFTED /
  FABRICATION-SUSPECT / ALIGNED / INSUFFICIENT-ANCHORS). Repair-type
  preflight (rashi-repair, placeholder-backfill) FAILS on a daf that is
  not haiku-safe; the remedies are rashi-realignment (shifted) and
  rashi-reconstruction (fabricated), Sonnet worker with the
  conditional review policy above (Fable substitutes as worker only
  when Sonnet is unavailable; Fable reviews only on escalation).
  worker:verify enforces a clean post-edit profile for BOTH types.
  Override is Fable-only: manifest authorizeDriftOverride
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
