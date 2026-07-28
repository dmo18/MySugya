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

Every pass, regardless of task type, is exactly this. Steps 7 and 10-15
are lifecycle-dependent: a task type declaring `lifecycle: "read-only"`
(currently `deployment-verify`) MUST skip them entirely and end with the
tracked tree byte-identical. See "Task lifecycles" below.

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
   - reviewPolicy independent: request an independent Sonnet review of
     the PR, do NOT merge your own work
   - reviewPolicy conditional (rashi-realignment, rashi-reconstruction):
     record the fresh post-edit self-review in .worker-self-review.json,
     run `npm run worker:review -- --manifest .worker-manifest.json`,
     and merge WITHOUT further authorization only when it prints
     AUTO-MERGE-ELIGIBLE and CI is green on the exact final head; any
     failed condition escalates to Sonnet (the registry's escalationModel)
     and blocks the merge
   - no policy: merge when green
13 verify Deploy Cloudways Branch and Deploy GitHub Pages for the merge
   commit
14 npm run worker:report -- --manifest .worker-manifest.json ; fill the
   PR/merge/deploy fields; post the JSON verbatim
15 stop and await the next authorization
```

### Task lifecycles

Every task type declares a `lifecycle` in the registry, and the manifest
carries it:

- `pr` (default): the pass produces a tracked change, so it takes
  exactly one VERSION patch bump (step 7) and exactly one PR (steps
  10-15). Any type that may write a tracked file must be able to carry
  its own VERSION bump; `test:policy` fails the registry otherwise.
- `read-only`: the pass must end with the tracked tree byte-identical.
  It never bumps VERSION, never commits, and never opens a PR; findings
  are reported in the worker's final report block only.
  `worker:verify` enforces this directly (`read-only-no-tracked-change`),
  and the generated prompt omits the VERSION/commit/PR steps rather than
  ordering an impossible pass.

Before VERSION 15.332 this was contradictory: `audit-only` and
`deployment-verify` both forbade tracked changes in their scope contract
while the universal loop demanded a VERSION bump and a PR from every
pass, so a compliant run of either type was impossible. The resolution
splits the two cases by what they actually do. `deployment-verify` writes
nothing at all and is now genuinely `read-only`. `audit-only` does write
a tracked report artifact under `docs/reports/`, so it is a `pr` type and
its scope was widened by exactly the three version-sync files (`VERSION`,
`package.json`, `package-lock.json`) needed to carry its own bump; every
other path it was forbidden (`modules/*`, `scripts/*`, workflows, hooks)
stays forbidden.

Direct gate commands, when needed individually: `validate:offline:yoma`
(all nine offline gates), `check:generated:yoma` (freshness),
`worker:scope` (scope only), `worker:schema-matrix` (registry/inventory
consistency), `worker:docs` (regenerate reference docs).

### Allowlist-drain: starting reconstruction/realignment on pre-existing debt

Preflight blocks a rashi-reconstruction/rashi-realignment task on any
daf that already carries content-allowlist hits (`rashi_content_allowlist.json`),
because starting a broad rewrite on top of undocumented-or-deferred
defects is how scope creep starts. But when fresh diagnosis shows the
daf genuinely needs the full reconstruction/realignment - not just the
narrower repair those hits originally documented - the hits are target-
scoped repair debt the bigger fix is about to eliminate, not a reason to
narrow scope down to `--task repair`. Use `--drain-allowlist`:

```
npm run worker:manifest -- --type rashi-reconstruction --module yoma \
    --range 77a --drain-allowlist --out .worker-manifest.json
```

This snapshots daf 77a's CURRENT content-allowlist entries into the
manifest's `allowlistDrain` field (`{"authorized": true, "snapshot": [...]}`)
and authorizes `worker:preflight` to proceed past those specific hits for
that daf only. Strict conditions, checked by `validate_allowlist_drain` in
`scripts/worker_pipeline.py`:

- only `rashi-reconstruction`/`rashi-realignment` manifests qualify (both
  types already cap at one target daf per PR)
- the snapshot must equal - not merely cover - the daf's current entries
  exactly; a stale or hand-edited snapshot (missing an entry that exists,
  or claiming one that does not) is rejected
- every snapshotted entry must belong to the single target daf; a
  snapshot naming another daf's debt authorizes nothing
- allowlist additions remain forbidden throughout; the drain only ever
  narrows the ratchet

Do NOT remove the allowlist entries yourself before repairing content;
the fix comes first. After the full edit, regeneration, and VERSION bump,
`worker:verify` re-runs `validate_rashi_content.py --json` and enforces
the drain via `allowlist_drain_status`: every snapshotted entry must end
up genuinely removed, and if any remain, the check distinguishes and
fails on either condition -
"validator reports these snapshotted entries stale but they were not
removed" (a cleanup omission - remove them and re-run) or
"snapshotted entries still needed... repair gap, escalate" (the fix did
not actually resolve that line - stop and escalate, never auto-merge).
Any new entry for the target daf, or any change to another daf's
entries, fails the same gate. Remove only the entries the validator's
stale report actually names; this is the same "remove only when
validators explicitly report them stale" rule that governs every other
allowlist removal, just applied to debt that was declared up front
instead of discovered after the fact.

Ordinary task types (rashi-repair, placeholder-backfill,
rashi-structural-repair, etc.) can never carry this authorization -
`--drain-allowlist` is rejected at manifest-generation time for any
other type, and even a hand-edited manifest claiming it is ignored by
both preflight and verify.

### Repetition-drain: starting reconstruction on a FABRICATION-SUSPECT daf with baselined repetition

Preflight separately blocks a rashi-reconstruction/rashi-realignment
task on any daf that already carries within-daf skeleton-repetition
baseline hits (`rashi_repetition_baseline.json`), same rationale as the
content-allowlist block above. Unlike content-allowlist hits, this
block cannot be resolved by narrowing to `--task repair`: a daf whose
drift profile is FABRICATION-SUSPECT or SHIFTED is *also* drift-blocked
from `repair`/`links` work (stub-only edits on a misaligned or
fabricated daf cement the misalignment), and the drift block's own
recommended remedy for such a daf is reconstruction. Before VERSION
15.206 these two checks contradicted each other for a daf that was
both baselined and FABRICATION-SUSPECT (41b): reconstruct was blocked
pending repair, repair was blocked pending reconstruction, and the only
override path (`WORKER_DRIFT_OVERRIDE`) was operator-issued and unrelated
to this contradiction in the first place.

`worker:manifest` now auto-snapshots the target daf's current
repetition-baseline entries into the manifest's `repetitionDrain` field
(`{"snapshot": [...]}`, no `--authorize` flag needed) whenever a
single-target rashi-reconstruction/rashi-realignment manifest is
generated, exactly like the pre-existing `scaffoldDebt` snapshot.
`worker:preflight` lets this snapshot bypass the repetition-baseline
block only when `validate_repetition_drain` in
`scripts/worker_pipeline.py` confirms ALL of:

- the manifest is single-target and matches the daf
- the snapshot equals - not merely covers - the daf's current
  repetition-baseline entries exactly (stale or hand-edited snapshots
  are rejected, same as allowlist-drain)
- the daf's live drift profile (`audit_rashi_semantic.py --profile`)
  still recommends `rashi-reconstruction` -- this authorization only
  ever unlocks a remedy the drift classifier has already approved; it
  is not a generic override, and it never touches
  `WORKER_DRIFT_OVERRIDE` or `authorizeDriftOverride`, which remain
  exactly as they were

After the edit, `worker:verify` enforces the drain via
`repetition_drain_status`: the target daf must produce zero repetition
violations (`validate_rashi_repetition.py`) and carry zero remaining
baseline entries; the baseline diff may contain only removals, scoped
to the target, with no entry's `maxCount`/`skeleton` changed and no
change to another daf's entries. `worker:review`'s auto-merge gate
checks the same thing target-scoped
(`repetition-clean-on-target`/`repetition-baseline-shrink-only`
conditions).

Count mismatches (`rashi_content_allowlist.json`'s `count_mismatches`)
are a wholly separate, always-hard-blocked check with no drain path of
any kind, regardless of task type or manifest content - the
repetition-drain snapshot can never be used to bypass a structural
count mismatch, and `rashi_preflight.py` reports the two conditions as
distinct errors (`COUNT MISMATCH` vs `REPETITION-BASELINE`) so the
count-mismatch one is never eligible for this filtering in the first
place.

## Model policy (non-negotiable)

Sonnet is the ONLY execution and escalation model in this pipeline.
Every task type carries `model: "sonnet"` and `escalationModel:
"sonnet"`; no other model may take, review, or escalate any task type.
`test:policy` pins this across the registry, the schema inventory, the
pipeline source, the generated reference docs, and every generated
prompt, so a reintroduced route to another model fails CI rather than
shipping silently.

Capability is expressed by tier, never by model name:

- `mechanicalTier: true` marks a task type whose contract is fully
  pattern-checkable (scope, allowlists, and generated-file freshness
  decide correctness). These are the bounded, mechanical passes.
- `mechanicalTier: false` marks work whose correctness needs semantic or
  structural judgment that pattern gates cannot verify: Hebrew/Rashi
  translation, placement judgments, realignment, reconstruction,
  enrichment narrative, structure edits, and all pipeline/validator
  changes.
- `independentReviewRequired: true` (reviewPolicy `independent`) means a
  second, independent Sonnet review must approve the PR before merge;
  the worker may open the PR and poll CI but may NOT merge its own work.
- reviewPolicy `conditional` (rashi-realignment, rashi-reconstruction,
  rashi-structural-repair) means the worker records a fresh post-edit
  self-review, runs the `worker:review` auto-merge gate, and merges only
  when it prints AUTO-MERGE-ELIGIBLE and CI is green on the exact final
  head; any failed condition escalates and blocks the merge.

Regardless of tier, the same hard limits apply to every pass: no worker
adds allowlist or baseline entries; no worker authorizes structure edits
without an explicit operator-issued `--authorize allowStructure`; no
worker overrides, weakens, or reinterprets a validator; no worker edits
the registry, validators, workflows, or hooks outside a docs-tooling
manifest. Manifests carrying `--authorize` flags, and any run with
`RASHI_ALLOWLIST_RESTRUCTURE=1`, are operator-issued only.
- A red gate always means the content or scope is wrong. The only two
  legal responses are: fix your own work, or stop and escalate.
- NO model, at any tier, direct-pushes tracked changes to main. Main
  moves only by validated PR merges; any workflow that would end with a
  tracked post-merge change is a design defect to escalate, not a
  reason to push.

## Conditional semantic review and autopilot queue (VERSION 15.93)

rashi-realignment and rashi-reconstruction carry `reviewPolicy:
"conditional"` with `escalationModel: "sonnet"` in the registry (Sonnet
is the only execution and escalation model). The unconditional per-PR
independent review is removed for these two types; in its place
stand a mandatory fresh self-review and a machine-checked auto-merge
gate. No hard validation gate was weakened: scope, freshness, content,
link, repetition, drift, and schema checks all still block CI exactly
as before.

A semantic PR may auto-merge (no independent review, no operator sign-off) only when
ALL of these hold. `npm run worker:review -- --manifest
.worker-manifest.json` machine-checks all seventeen and prints
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
6. scaffold-clean-on-target: zero current scaffold-fabrication hits and
   zero remaining scaffold-debt baseline entries on the target daf
7. scaffold-baseline-shrink-only: the scaffold-debt baseline diff
   contains only removals, scoped to the target daf, with no entry
   rehashed and no unrelated daf touched
8. repetition-clean-on-target: zero current repetition violations
   (`validate_rashi_repetition.py`) and zero remaining repetition-
   baseline entries on the target daf (see the repetition-drain section
   above)
9. repetition-baseline-shrink-only: the repetition-baseline diff
   contains only removals, scoped to the target daf, with no entry's
   maxCount/skeleton modified and no unrelated daf touched
10. packet-contains-every-linked-local-id: the live packet segment
    table (Gemara AND Mishnah kinds) contains every linked id
11. all-links-legal-and-nonempty: every entry links to legal local ids
12. drift-profile-ALIGNED: for rashi-reconstruction/rashi-realignment,
   evaluated by a source-relative citation-evidence policy with three
   tiers, chosen by how many genuine detectable citations exist in the
   daf's own raw Hebrew (a fixed property of the source, independent of
   the current translation):
   - 2+ anchors (multi-anchor-safe): classification must be ALIGNED,
     every expected anchor found, zero missing, and every offset
     exactly 0 - stricter than the bare ALIGNED label, which the
     classifier can still grant with anchors missing.
   - exactly 1 anchor (one-anchor-safe): classification
     INSUFFICIENT-ANCHORS, that one anchor found at offset 0, zero
     missing, and the fresh self-review's `oneAnchorAttestation` block
     (onlyOneGenuineCitation, citationTranslatedOnOwnLine,
     noCitationInventedMovedOrDuplicated, noSemanticUncertaintyRemains)
     all explicitly true.
   - 0 anchors (zero-anchor-safe): classification INSUFFICIENT-ANCHORS,
     confirmed by an independent second source scan (a whole-text
     parenthetical search, deliberately not reusing the primary
     per-line scanner) that finds no citation-like text anywhere, plus
     the self-review's `zeroAnchorAttestation` block
     (everyRawLineRereadForCitations,
     noTractateDafChapterVerseOrOtherCitationAnywhere,
     noCitationInventedMovedOrDuplicated, noSemanticUncertaintyRemains)
     all explicitly true. Any empty `linkedGemaraLineIds` entry must be
     named in an `authorizedEmptyLinks` list citing a documented
     boundary rule, or it fails.

   Whichever tier decided the outcome, worker:review reports it as its
   own distinct PASS/FAIL line (`multi-anchor-safe` is folded into
   drift-profile-ALIGNED itself since it never relabels anything;
   `one-anchor-safe`/`zero-anchor-safe` print as separate lines) rather
   than silently relabeling the daf ALIGNED. SHIFTED and
   FABRICATION-SUSPECT can never qualify at any tier (both always carry
   2+ anchors). Citation anchors are corroborating evidence, not a
   mandatory content feature: the gate never requires inventing one,
   and the absence of citations never automatically implies
   correctness, which is why the zero-anchor tier demands the strongest
   attestation of the three. rashi-structural-repair keeps its own,
   separate, unconditional line-level-safe allowance (unaffected by any of
   this). Run `npm run worker:capability-scan -- --targets <list>`
   once per campaign (not per daf) before starting content work, to
   confirm every queued target's anchor cardinality (ZERO/ONE/MULTI)
   and packet completeness can reach a supported final state; it never
   edits content and exits nonzero if any target cannot.
13. semantic-audit-zero-shift-candidates on the target daf
14. no-stub-or-duplicate-helpers in the target daf
15. generated-files-fresh (byte-identical regeneration)
16. version-metadata-synced (VERSION == package.json == lock)
17. fresh-self-review-committed-and-clean: .worker-self-review.json is
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

When invoking the one-anchor-safe tier (item 12 above), the self-review
additionally carries a `oneAnchorAttestation` object:

```json
{"oneAnchorAttestation": {
   "onlyOneGenuineCitation": true, "citationTranslatedOnOwnLine": true,
   "noCitationInventedMovedOrDuplicated": true,
   "noSemanticUncertaintyRemains": true}}
```

When invoking the zero-anchor-safe tier, the self-review carries a
`zeroAnchorAttestation` object instead, and (only if any entry has an
empty `linkedGemaraLineIds`) an `authorizedEmptyLinks` list naming
each such vilnaLine and the documented boundary rule that permits it:

```json
{"zeroAnchorAttestation": {
   "everyRawLineRereadForCitations": true,
   "noTractateDafChapterVerseOrOtherCitationAnywhere": true,
   "noCitationInventedMovedOrDuplicated": true,
   "noSemanticUncertaintyRemains": true},
 "authorizedEmptyLinks": [
   {"vilnaLine": 12, "rule": "10a vilnaLine 35 boundary precedent"}]}
```

Escalation is MANDATORY (stop, do not merge) when any of
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
the queue simply stops where it is; the escalation is resolved, then the
queue resumes. Tests: `npm run test:policy` (part of `npm test`) covers
the policy positively (all conditions green needs no review) and negatively
(every single failed condition blocks the merge), the prompt text, the
queue derivation mechanics, and the no-direct-push guarantees.

## Operator quickstart (what do I paste to the worker?)

1. Pick the task type from docs/reports/task-type-reference.md; check
   the readiness matrix in docs/reports/schema-pipeline-coverage.md says
   the type is ready to run.
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
6. Escalate when: any stop condition in the prompt fires, a
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
- Branch cleanup is a hygiene/tooling pass, not a content worker task.
- Remote-session credentials may be push-scoped to the designated
  branch only (branch deletion returns 403). In that case the tooling pass
  produces the classified deletion list and the repository admin
  deletes via the GitHub branches page, which marks merged branches
  itself.

## Consistency policies (single source summary)

- Automation NEVER direct-pushes tracked changes to main. Every change
  to main arrives through a validated PR merge. No worker, autopilot,
  or queue step may produce a tracked post-merge change that would
  require a direct push (the queue derives progress from merged PRs for
  exactly this reason; enforced by test:policy). This applies to every
  task type and every tier without exception.
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
  RASHI_ALLOWLIST_RESTRUCTURE=1 in a docs-tooling PR (CI-enforced).
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
- Structural changes to rashiTranslations (entry count, vilnaLine
  sequence) are possible ONLY under the rashi-structural-repair task
  type (VERSION 15.97): one daf per PR, conditional review, and a
  REQUIRED explicit allowStructure authorization on the manifest
  (preflight fails without it; no other task type can mint or carry that
  authorization, so no ordinary manifest can ever make structural or
  count changes). Its review gate additionally
  requires exact post-repair entry-count and vilnaLine parity with the
  authoritative talmuddev raw lines, and accepts INSUFFICIENT-ANCHORS
  alongside ALIGNED for the drift condition (anchor-poor daf cannot
  manufacture citations). Tests: test:policy.
- Source-relative citation-evidence policy (docs-tooling, review-gate
  only): the one-anchor-safe tier first appeared narrowly scoped to
  Yoma 48b (whose entire raw Rashi carries exactly one genuine
  citation, split by an ordinary print line-wrap so the anchor
  scanner's per-line window never pairs the tractate name with its daf
  number, capping the classifier at INSUFFICIENT-ANCHORS forever
  regardless of translation quality). Generalized after Yoma 49b
  surfaced a more extreme case (zero genuine citations anywhere in the
  raw Hebrew) that the narrow one-anchor exception could not represent:
  drift-profile-ALIGNED for rashi-reconstruction/rashi-realignment is
  now a 3-tier policy keyed on the raw Hebrew's own anchor count
  (multi-anchor-safe, one-anchor-safe, zero-anchor-safe; see item 8
  above), plus `npm run worker:capability-scan` to classify an entire
  queue's anchor cardinality and packet completeness before content
  work starts, so a deterministic gate limitation is caught once for
  the whole campaign rather than daf by daf. Never touches the
  classifier itself; never accepts SHIFTED or FABRICATION-SUSPECT at
  any tier (both always carry 2+ anchors); the zero-anchor tier
  requires a stronger self-review attestation than the others, since
  the absence of citations is not itself evidence of correctness.
  Tests: test:policy.
- Drift gate: `audit:rashi:drift:yoma` classifies every daf (SHIFTED /
  FABRICATION-SUSPECT / ALIGNED / INSUFFICIENT-ANCHORS). Repair-type
  preflight (rashi-repair, placeholder-backfill) FAILS on a daf that is
  not line-level-safe; the remedies are rashi-realignment (shifted) and
  rashi-reconstruction (fabricated), Sonnet worker with the
  conditional review policy above.
  worker:verify enforces a clean post-edit profile for BOTH types.
  Override is operator-only: manifest authorizeDriftOverride
  plus WORKER_DRIFT_OVERRIDE=1. Tests: npm run test:drift:yoma (in npm
  test).
- Known deferred content debt lives in docs/rashi-audit-backlog.md:
  61a lines 1-45 fabricated (rashi-reconstruction);
  67b/68a/68b/70a/71b shifted-compressed (rashi-realignment;
  stub-only repair FORBIDDEN there, drift gate enforces);
  41a shifted block (+42a L50 lead); 8a/9a phantom counts; 77a-88a
  filler; plus the drift-profile triage backlog recorded at VERSION
  15.85. 47a+ reconstruction is paused until the debt is drained.
  Nekudot is paused in the registry pending validator design.
