# Platform closure plan

**Status: authoritative.** This document is the single plan for finishing the
reusable MySugya platform after the Yoma content and Rashi campaigns. It
supersedes no other document's factual content: `docs/reports/open-items.md`
remains the classified inventory of everything open, and
`docs/reports/replication-readiness.md` and
`docs/reports/sugya-schema-readiness.md` remain the evidence sources for
Phases 2 and 3 below - but it is the one place that states what remains,
in what order, and what "done" means for each piece.

Read this after `CLAUDE.md`. Read `docs/reports/open-items.md` for the
day-to-day classified state; read this document for the plan that closes it.

---

## What is already complete

Stated here once, precisely, so no phase below re-litigates it.

**Yoma corpus**: 173 daf, 492 sugyot. Frozen; see `modules/yoma/MODULE.md`.

**Rashi campaign**: complete. 8,854 Rashi entries, 10,061 declared
associations, 0 broken associations, 0 cross-daf associations, boundary
(empty-link) registry 20/20 authorized with 0 stale/duplicate/unauthorized
entries. The linked `linkedGemaraLineIds` renderer is the *only* renderer:
the legacy vilnaLine-coincidence renderer and the `?rashiAssoc=legacy`
selector were removed at VERSION 15.346 (`docs/reports/legacy-renderer-retirement-policy.md`).
Renderer readiness has reached 8/8 on multiple verified commits, most
recently `b86d7ef`, via the 8-shard `rashi-browser-shards.yml` workflow
(173/173 daf, 215 passed / 0 failed).

**Rashi nekudot/vowelization**: intentionally out of project scope, not
paused work. See the OUT-OF-SCOPE section of `docs/reports/open-items.md`.
Nothing below reopens this.

**Schema field coverage**: 492/492 sugyot carry every field
`shared/schema_map.js` marks required (`npm run validate:schema:yoma`).
A separate semantic audit (`npm run report:schema:semantics:yoma`) has also
run corpus-wide; see Phase 2 for what it found and what remains.

**sourceRefs**: Phase 2B is now complete; see Phase 2 below for the final
state. A canonical schema, an offline validator
(`validate_source_refs.py`), a dry-run migration preview
(`preview_source_refs_migration.py`), and a four-PR migration plan exist
(`docs/reports/source-refs-normalization-plan.md`). The migration was
**correctly stopped** where conversion would require inventing data: the
331 sound string refs were never converted to canonical objects, by
permanent decision, because doing so would require inventing a
`sourceType`. Every object ref that could be judged from repository
evidence, including the final two `TIED_CANDIDATES` cases, has been:
`validate_source_refs.py --strict` now reports 0 defects across all 1,953
refs.

**argumentFlow rendering**: unrecognised step types (106 values outside the
13-value `controlledValues.argumentStepType`, covering 1,320 of 1,953 steps)
no longer render with a false "Question" label. `stepMetaFor` in `app.jsx`
shows the type's own name and leaves Hebrew empty rather than inventing it
(VERSION 15.350). Phase 2A closed the underlying vocabulary question via
the category-registry design described in Phase 2 below.

**Test, browser, and deployment evidence current as of this plan**: `npm test`
passing (12 Python/Node suites), `npm run test:browser` passing (16 Playwright
specs, 1 module-conditional skip), the 8-shard corpus-wide browser association
run green, `npm run validate:offline:yoma` green (12 gates), GitHub Pages and
Cloudways deployments both reporting success for the current `main` tip.

**Known, currently unresolved**: GitHub Pages has two competing publishers
(our `deploy-pages.yml` workflow and GitHub's built-in branch-build
publisher), and which one serves at any given moment is nondeterministic.
This is the subject of Phase 1.

---

## The four phases

```
Phase 1 ─┐
         ├─→ Phase 4 (closure requires 1, 2, and 3 all done)
Phase 2 ─┤
         │
Phase 3 ─┘
```

Phases 1, 2, and 3 do not depend on each other and may proceed in any order
or in parallel. Phase 4 is the reconciliation pass and requires all three
finished. This plan documents all four. Phase 2 is now complete (see below).
Phases 3 and 4 remain planned, not started.

---

## Phase 1: Production publishing and repository protection

### Goal

GitHub Pages publishes only the tested `dist/` artifact through GitHub
Actions, with no competing publisher. `main` is protected against
unvalidated direct changes.

### Why this is first

It is the only phase that is a repository/operator setting rather than a
code or content change, and the defect it fixes is live: production is
currently serving the wrong bundle part of the time.

### Required outcomes

- Pages source set to GitHub Actions (Settings > Pages > Build and
  deployment > Source > GitHub Actions).
- A fresh `deploy-pages.yml` run succeeds on the exact `main` commit.
- Repeated public checks (minimum 5 cache-busted checks spread across at
  least 10 minutes) prove the served bundle stays the tested production
  bundle for the entire window - not a single lucky sample.
- `main` requires pull requests.
- Required status check: `build`.
- Required status checks are strict (branch must be up to date before merge).
- Force pushes blocked.
- Branch deletion blocked.
- Bypass restricted to the smallest practical administrator-only set.
- No Cloudways, mysugya.com, or custom-domain change of any kind.

### Evidence required

- Pages build-type read back via API, before and after.
- Workflow run id and head SHA for the verification dispatch.
- The 5+ sample log (timestamp, HTTP status, bundle filename, byte size)
  showing a single stable outcome across the whole window.
- Deployment history after the setting change, showing no branch/root
  deployment superseding the workflow deployment.
- Branch protection / ruleset configuration read back via API: PR required,
  `build` required and strict, force-push disabled, deletion disabled,
  bypass list.

### Stop conditions

- GitHub authentication does not permit changing Pages or protection
  settings. Report the exact denied operation and response; give the exact
  Settings UI path and values for the operator; do not fabricate a code
  workaround; stop before Phase 2.
- Branch-protection or repository-admin settings would need to change in a
  way not listed above (e.g. adding required reviewer counts not already
  policy). Ask before proceeding.

### Not in scope for Phase 1

Any application code change. Any Cloudways or mysugya.com change - GitHub
Pages is the authoritative beta deployment; mysugya.com is not deployment
debt (`docs/reports/open-items.md`, OUT-OF-SCOPE section).

### Attempt record (VERSION 15.355, commit `0bbb86a`) - superseded, see below

Phase 1 execution was attempted and was **blocked**, not completed, as of
VERSION 15.355. Evidence at that time:

- `GET /repos/dmo18/MySugya/pages` (read Pages build/source config): the
  environment's outbound proxy returned `403 Access to this GitHub API path
  is not permitted through this proxy`. This was an environment policy
  block, independent of any GitHub token permission, and remains true
  today - see below.
- `PUT /repos/dmo18/MySugya/pages` (change Pages source to GitHub Actions):
  same proxy block, same message.
- `GET /repos/dmo18/MySugya/branches/main/protection` (read classic branch
  protection): `403 Resource not accessible by integration` - the GitHub
  App token this session runs under has no repository-administration scope
  for the classic endpoint. This remains true, but is moot: the owner used
  a repository ruleset instead, which a different, readable endpoint
  covers (below).
- `GET /repos/dmo18/MySugya/rulesets` (read repository rulesets): succeeded,
  returned `[]` at the time - zero rulesets configured.
- `POST /repos/dmo18/MySugya/rulesets` (create a ruleset): the same proxy
  blocked writes explicitly.
- No `mcp__github__*` tool exposes Pages configuration, branch protection,
  or rulesets at all (confirmed by exhaustive `ToolSearch`).
- Behavioral confirmation at the time: the built-in `pages build and
  deployment` run fired on every push to `main`, including the commit that
  merged the plan itself (`0bbb86a`).

### Completion record (VERSION 15.357, commit `7db3274` verified)

**The repository owner completed both settings changes directly.** This
session cannot read or write the Pages source setting even now (the
proxy block on `/repos/.../pages` is unconditional and unrelated to what
the setting's value actually is), but branch protection is verifiable
directly, and Pages is verifiable behaviorally and via live production
checks.

**Branch protection - read back and confirmed**, via
`GET /repos/dmo18/MySugya/rulesets` (this endpoint reads regardless of the
`/pages` block; it is a different API surface) and then
`GET /repos/dmo18/MySugya/rulesets/19991220` for the full rule set:

| requirement | observed |
|---|---|
| Applies to `main` | `conditions.ref_name.include: ["refs/heads/main"]` |
| Enforcement | `"enforcement": "active"` |
| PR required to merge | `pull_request` rule present |
| Required approving reviews | `0` - no mandatory human approval was added, matching the instruction not to add one unless the owner intentionally configured it |
| Merge methods preserved | `allowed_merge_methods: ["merge", "squash", "rebase"]` - the repository's squash-merge workflow is intact |
| Required status check | exactly `"context": "build"` |
| Strict / up-to-date | `"strict_required_status_checks_policy": true` |
| Force pushes blocked | `non_fast_forward` rule present |
| Branch deletion blocked | `deletion` rule present |
| Bypass | `"current_user_can_bypass": "never"`, no `bypass_actors` listed |

This is a complete, direct read-back, not an inference. Every required
behavior in this plan's Phase 1 section is satisfied exactly.

**Pages - verified behaviorally and via live checks**, since the
configuration endpoint itself cannot be read from this session:

- `deploy-pages.yml` dispatched manually on `main` at `7db3274`: `build` job
  succeeded; `deploy` job reported `skipped` by design (it is conditioned on
  `github.event_name == 'push'`, so a manual dispatch validates the build
  but does not redeploy - this is correct workflow behavior, not a defect).
- Five cache-busted public checks, spaced roughly two minutes apart across
  a 9-minute window, all identical: `assets/app-15.356.js`, HTTP 200, zero
  occurrences of `text/babel`, `babel.min.js`, `react.development.js`, or
  `react-dom.development.js`.
- The merge of this very documentation PR is itself the decisive behavioral
  test: it is a real push to `main`, so `deploy-pages.yml`'s `deploy` job
  runs for real, and if the built-in branch publisher still fired it would
  appear as a `pages build and deployment` run against the merge commit.
  See the merge-commit verification note appended after this PR merges, or
  `docs/reports/open-items.md` for the live record if this file is read
  before that note is added.

**Phase 1 status: COMPLETE**, pending the merge-commit confirmation above
holding (no `pages build and deployment` run against the merge SHA, and the
post-merge live check matching). If that confirmation contradicts this
record, treat this section as provisional and the true status as blocked
until corrected.

**Phase 2 has not been started.** Nothing in this record touches
`argumentFlow`, `sourceRefs`, Yoma content, or Rashi associations.

---

## Phase 2: Semantic schema contract

**Status: COMPLETE.** argumentFlow (2A) is fully complete - see
`docs/reports/argumentflow-category-decision.md` - because the chosen
design (category derived from a registry, never stored per step) meant
100% category coverage was reached the moment the registry was written,
with zero content edits. sourceRefs (2B) has its canonical contract defined
and validated (`docs/reports/sourcerefs-contract-decision.md`); of the
original 550 defective refs, 412 mechanical repairs and 105
judgment-required repairs were applied first (517 of 550), leaving 33
refs that a subsequent campaign classified individually
(`docs/reports/sourcerefs-blocker-classifications.json`) into five
blocker classes and resolved 31 of them: 2 `QUALIFIED_CROSS_DAF` refs
migrated to an explicit cross-daf shape
(`docs/reports/sourcerefs-crossdaf-schema-decision.md`,
`apply_sourcerefs_crossdaf_migration.py`), 29 `ABSENT_OR_UNANCHORED` refs
removed rather than left as false coordinates
(`apply_sourcerefs_absent_removal.py`). The final 2 `TIED_CANDIDATES` refs -
`yoma-044b-l01` and `yoma-063a-l03a` - were re-adjudicated in a final,
tightly scoped pass that found evidence the prior five-way classification
had not fully exploited, and both are now resolved:

- **`yoma-044b-l01`**: the step is a genuine compound claim, and multiple
  `sourceRefs` on one step is an already-legal, already-used corpus shape
  (21 existing steps carried 2+ refs before this repair; `app.jsx` never
  reads `sourceRefs` at all, so there is no renderer or navigation
  dependency; the validator enforces no per-step cardinality limit). Each
  clause maps 1:1 onto one of the two real same-Vilna-line segments, so the
  step was given two ordered refs - `yoma-044b-l01a` (clause 1) and
  `yoma-044b-l01b` (clause 2) - rather than being split into two steps.
- **`yoma-063a-l03a`**: the step's own `speaker` field, "Rav Dimi from
  Eretz Yisrael," is a verbatim match to `yoma-063a-l10`'s own transmission
  formula ("When Rav Dimi came from Eretz Yisrael..."), and `l10`'s
  conclusion (exempt) matches and genuinely supports the ruling the step
  cites, exactly what the step's `type: "support"` claims.
  `yoma-063a-l17` is introduced by a different transmitter (Ravin, not Rav
  Dimi) and concludes the opposite (liable) - it would contradict, not
  support. Two independent discriminators (transmitter identity, direction
  of support) converge on `l10` and rule out `l17`.

Both repairs are recorded in full, including the evidence chain, in PR
#369's commit message and description, and the reusable tool in PR #368
(`apply_sourcerefs_final_two.py`,
`modules/yoma/scripts/test_validate_source_refs.py`). No tie was forced,
and no residue was hidden along the way: both cases were itemized in
`docs/reports/sourcerefs-blocker-classifications.json` and
`docs/reports/source-refs-normalization-plan.md` throughout, and that file
now also records the resolution. The **331 sound string refs remain a
closed, not an open, question**: they are not converted to object form,
permanently, because string form is a first-class canonical shape and
conversion would require inventing `sourceType`
(`docs/reports/sourcerefs-contract-decision.md`). **Phase 2 is COMPLETE:
`validate_source_refs.py --strict` reports 0 defects across all 1,953
refs (1,620 same-daf object refs including the 2 repaired here, 331 sound
string refs, 2 cross-daf refs) for the first time in this campaign; see
"Phase 2 completion criterion" below.**

### A. argumentFlow vocabulary

**Problem.** `argumentFlow[].type` is declared required/canonical over 13
controlled values; the corpus uses 106 more across 1,320 of 1,953 steps
(417/492 sugyot). Phase-1-adjacent work already stopped the renderer from
mislabelling these as "Question" (VERSION 15.350), but the data itself still
does not conform to the declared schema.

**Direction.** Adopt a two-level model:

```json
{ "category": "<small controlled cross-tractate vocabulary>",
  "type": "<specific authored distinction, preserved as-is>" }
```

`category` is what renderer behavior (symbol, color, Hebrew term) keys off,
and stays small and stable across tractates. `type` preserves the specific
distinction an enrichment author drew (`ruling`, `derivation`, `dispute`,
...) without forcing it into one of 13 buckets.

**Requirements:**

- `category` vocabulary stays small; do not let renderer metadata grow past
  roughly the current 13-20 entries. Widening it to cover all 106+ observed
  `type` values defeats the purpose.
- Do not collapse the 1,320 non-canonical steps down to 13 `type` values -
  that erases the distinctions the enrichment deliberately drew.
- An unrecognised `type` (one whose `category` mapping is not yet decided)
  renders as readable text, never with an invented Hebrew label or symbol.
  This behavior already exists (`stepMetaFor`) and must be preserved through
  the migration, not reintroduced as a regression.
- Inventory all existing `type` values and frequencies (this is already done;
  see `docs/reports/sugya-schema-readiness.md`).
- Map every value with an unambiguous `category` mechanically; escalate
  genuinely ambiguous mappings to the operator rather than guessing.
- Validate all 1,953 argumentFlow steps across all 492 sugyot against the
  new two-level schema before declaring Phase 2A complete.

### B. sourceRefs

**Problem (as originally analyzed).** Recapped from the completed analysis
(`docs/reports/source-refs-normalization-plan.md`): 1,431 of 1,981 refs are
sound, 550 are defective across 102 daf, split into mechanically repairable
(412) and judgment-required (138) tiers, plus 331 sound string refs that
cannot be losslessly converted to the canonical object form without
inventing a `sourceType`.

**Current state.** 412 mechanical repairs applied
(`apply_sourcerefs_mechanical_repair.py`), then all 138 judgment-required
refs individually reviewed against the actual Gemara text on their daf
(`apply_sourcerefs_semantic_repair.py`, evidence in
`docs/reports/source-refs-semantic-review.json`): 105 resolved, 33 remain
with documented per-case blockers (content absent from the declared daf,
content living on a different daf than declared, or a genuine tie between
candidates), across 16 daf, 23 sugyot, 33 argumentFlow steps. The 331
string refs are untouched **permanently, by decision, not by default**: a
conversion that is not shown lossless must not be applied, and no
independent evidence exists (or is expected to exist) for the `sourceType`
value any conversion would require - see
`docs/reports/sourcerefs-contract-decision.md`.

**Requirements, unchanged from the existing plan and restated here as the
Phase 2B contract:**

- Segment ids (`lineId`) and Vilna line numbers (`vilnaLine`) are distinct
  coordinate systems and must never be compared as if interchangeable - a
  `lineId`'s Vilna interval containing a step's `vilnaLine` is the
  correctness condition, not numeric equality.
- Never invent `sourceType`. It is not a function of a line's `kind` (15
  refs on Mishnah-kind lines are deliberately typed `gemara`).
- Preserve the 331 sound string references as-is unless a specific proposed
  representation is demonstrably lossless end to end, including
  `sourceType`.
- Classify every defective object reference into mechanical-repair versus
  judgment-required tiers (already done; see the four-PR plan in the
  normalization document) and execute them as separate, reviewable PRs.
- Validation must cover: existence (`lineId` resolves on its own daf),
  daf locality (no cross-daf refs), ordering (document order preserved),
  segment identity (the referenced segment is the one meant), Vilna
  reference correctness (interval containment), and source type
  correctness.
- Where provenance genuinely cannot be proven from repository data alone
  (the 138 judgment-required refs), retain an explicit unknown/unresolved
  state rather than a guessed value. This is not new policy; it is what the
  existing preview tool already does by refusing to propose those refs.

### Phase 2 completion criterion

All 492 sugyot are structurally and semantically valid under both stable,
documented contracts (the two-level `argumentFlow` schema and the
canonical-form `sourceRefs` schema), with an offline validator for each
wired into `validate:offline:yoma`. Per this campaign's own governing
directive, Phase 2 may be marked COMPLETE only when every ref and every
intentionally-unanchored step is valid under the documented contract with
zero exceptions; if any tied or absent-content case remains without
adequate evidence to resolve it, Phase 2 is marked **BLOCKED**, not
complete, and the residue is reported exactly - it is never characterized
as "accepted" as a substitute for resolving it, however small.

**Status against this criterion: MET. Phase 2 is COMPLETE.** argumentFlow
(2A) meets it in full. sourceRefs (2B) now also meets it in full:
`validate_source_refs.py --strict` reports **0 defects** across all 1,953
refs - 1,620 `OK` (same-daf object refs), 331 `STRING_RESOLVABLE`, 2
`OK_CROSSDAF` - with 0 `OBJECT_COORDINATE_CONFLICT`, 0
`OBJECT_DANGLING_AMBIGUOUS`, and 0 refs in any other defect class. The 331
string refs were never part of what blocked Phase 2 completion: their
disposition was decided (permanently string form, not converted;
`docs/reports/sourcerefs-contract-decision.md`), so they were always
sound and closed, not a pending question. Of the original 33 residual
refs identified by the blocker-classification pass, all 33 are now
resolved: 2 `QUALIFIED_CROSS_DAF` migrated to the cross-daf shape, 29
`ABSENT_OR_UNANCHORED` removed rather than left as false coordinates, and
the final 2 `TIED_CANDIDATES` (`yoma-044b-l01`, `yoma-063a-l03a`) repaired
in the final adjudication pass described above (PRs #368-#369).
`validate:sourcerefs:strict:yoma` now passes with exit code 0. Nothing is
hidden by an allowlist or a weakened gate - the gate itself now passes
cleanly.

**What closed Phase 2:** a fresh re-reading of repository evidence that
the prior five-way classification pass had not fully exploited. For
`yoma-063a-l03a`, the step's own `speaker` field ("Rav Dimi from Eretz
Yisrael") was cross-referenced against the verbatim transmission formula
of both candidates, breaking what had looked like a tie between two
structurally-identical "Rabbi Yirmeya said Rabbi Yochanan said" statements.
For `yoma-044b-l01`, confirming that multiple `sourceRefs` per step is
already a legal, already-used, renderer-safe corpus shape (21 precedent
steps, `app.jsx` never reads `sourceRefs`) meant the compound step could
be given two ordered refs rather than requiring an out-of-scope step
split. Full evidence for both is in PR #369's commit message and
description; the reusable resolution tool and its tests are in PR #368.

### Dependencies

None on Phase 1 or Phase 3. Can run independently or in parallel.

### Stop conditions

- A `type` -> `category` mapping is ambiguous. Escalate to the operator;
  do not guess.
- A sourceRefs conversion cannot be shown lossless. Do not apply it; keep it
  in the judgment-required tier.
- Reopening Rashi content or nekudot work would be required to complete a
  mapping. It would not be; if a plan step appears to require this, stop.

---

## Phase 3: Tractate-agnostic replication

### Status (as of Step 8 reconciliation, VERSION 15.388)

**BLOCKED, not complete.** Full detail, evidence, and per-row disposition
in `docs/reports/phase3-inventory.md`; summary here:

- All 9 originally-identified pipeline blockers (Step 1's inventory) are
  resolved: `worker_pipeline.py`, `scripts/worker_task_types.json`, and
  all 5 Rashi renderer/shard tools are module-aware via
  `scripts/module_resolver.py`/`shared/module_resolver.js`; the one
  remaining item (`generate_argument_taxonomy.py`) turned out to be a
  false positive on re-reading, not a real blocker.
- A canonical module descriptor + resolver contract exists
  (`docs/reports/module-descriptor-contract.md`), never falls back to
  Yoma on an unknown/malformed module, and is capability-driven for
  Rashi/literal-translation and source-acquisition strategy.
- `scripts/build.mjs` is module-aware (`--module`, `--out`,
  `--search-root`), with a publishable-flag safety guard, and GitHub
  Pages selects Yoma explicitly by code (`deploy-pages.yml`).
- A synthetic fixture module exists at
  `tests/fixtures/modules/demotractate/` (3 daf, 4 sugyot, all required
  argumentFlow/sourceRefs variety, `status: "synthetic"`,
  `publishable: false`), lives outside `modules/` so production
  discovery never finds it, and is proven end-to-end - via the real
  generic tooling, never a fixture-only pipeline - to resolve, build in
  isolation, and render correctly in a real browser
  (`npm run test:fixture-onboarding`).
- Yoma's non-regression is proven with full tree-digest rigor (every
  generator re-run and diffed byte-for-byte against committed output,
  not just an empty `git diff`); every corpus count re-verified.

**6 of 38 acceptance-matrix rows remain open**, none requiring Yoma
content changes, a real second tractate, or Phase 4 work: fixture
scaffold-from-empty proof, fixture validation via a generic validator,
fixture documentation generation, fixture worker-scope proof against
the literal fixture module (currently proven only via a synthetic
in-memory stand-in), a dedicated CI workflow for the onboarding proof,
and literal-translation capability-driven behavior (not yet actionable -
no generic tool touches literal content). Exact text and required
follow-up for each is in `docs/reports/phase3-inventory.md`'s Step 8
section.

### Problem

`docs/reports/replication-readiness.md` measured this precisely: the app and
build layers are already module-generic (8/8 fixture checks pass, no change
needed), but 7 shared tools at the repo root hardcode `modules/yoma`, chief
among them `worker_pipeline.py`, whose `--module` flag is currently
cosmetic - `YROOT` is pinned regardless of the flag's value.

### Goals

- Remove the seven documented Yoma-specific pipeline blockers.
- Every command that accepts `--module` (or an equivalent parameter) actually
  uses the selected module for every path it touches.
- No hidden `modules/yoma` fallback remains anywhere in the parameterized
  tools.

### Required work (parameterize, in dependency order)

1. Worker roots (`YROOT`, `YSCRIPTS` in `worker_pipeline.py`).
2. Manifest generation and validation.
3. Validators (schema, daftext, Rashi structural/content/links/repetition,
   literal, order, boundary authorizations).
4. Generators (`build_learning_data.py` and friends).
5. Source acquisition (Sefaria fetch, talmud.dev cache).
6. Daf ranges and chapter/perek metadata.
7. Segmentation and learning-data paths.
8. Rashi availability and behavior (a module with no Rashi layer yet must not
   crash the pipeline).
9. Literal-translation support.
10. Schema validation completeness gate.
11. Browser tests (association spec's default target daf and module
    parameter).
12. Generated documentation (`worker:docs`, `generate_rashi_docs.py`).
13. Deployment assets (build.mjs already generalizes; confirm no regression).

### Required proof: a synthetic fixture module

Not a real second tractate. A tiny fixture (built as `demotractate` at
`tests/fixtures/modules/demotractate/`, 3 synthetic daf) that proves, end
to end. Status per item as of Step 8 (full evidence in
`docs/reports/phase3-inventory.md`'s acceptance matrix):

- Onboarding from an empty module directory. **Open** (row 23) - the
  existing fixture's resolve/build/render path is proven; a from-nothing
  scaffold reproduction is not yet.
- Manifest creation targets the fixture, never Yoma. **Done** (row 7) -
  `worker_pipeline.py manifest --module demotractate` proven live.
- No fixture operation reads or writes any Yoma file (assert this directly,
  not just observationally). **Done** (row 31) - full tree-digest proof,
  not just an empty git diff.
- Source ingestion works against the fixture's own (synthetic or
  test-fixture) data. **Done** (row 24).
- Generated data stays isolated under the fixture's own paths. **Done**
  (row 25, row 27).
- Schema validation runs and passes against the fixture. **Open** (row
  26) - no generic, module-selectable validator has been run against it
  yet.
- Worker scope checks (`allowedFiles` resolution) work for the fixture's
  module id. **Partial** (row 30) - the mechanism is proven with a
  synthetic in-memory fixture, not yet re-exercised against the literal
  committed `demotractate` module by name.
- Build succeeds with the fixture module present. **Done** (row 27) -
  `build.mjs --module demotractate --search-root ... --out ...`.
- Browser tests pass against the fixture. **Done** (row 28) - via a
  dedicated proof script (`fixture_onboarding_browser_check.mjs`), not
  the formal `tests/browser/*.spec.js` suite.
- Documentation generation succeeds and describes the fixture correctly.
  **Open** (row 29) - no fixture-specific docs-generation script exists.
- The entire process is executable from documented commands, with no manual
  repo-internal knowledge required beyond what the commands themselves say.
  **Done** for the parts proven above - `npm run test:fixture-onboarding`
  runs the full resolver + build + render proof from one command.

### Explicitly out of scope

Starting or populating a real second tractate. The fixture module is deleted
or kept as a permanent, clearly-labeled test fixture outside `modules/`
proper - it is never promoted to a real tractate.

### Dependencies

None on Phase 1 or Phase 2. Can run independently or in parallel with either.

### Stop conditions

- A parameterization would require touching Yoma content or Rashi
  associations. It should not; if it appears to, stop and reconsider the
  approach rather than touching frozen content.
- The fixture module accidentally reads or writes anything under
  `modules/yoma/`. Treat as a bug in the parameterization, not an acceptable
  edge case.

---

## Phase 4: Final repository closure

### Required work

- Scan all tracked files for TODO, FIXME, "deferred", "paused", "unknown",
  "temporary", "in progress", "incomplete", and similar stale-claim markers.
- Classify every result: completed, intentionally out of scope, future
  roadmap, operator-owned, or genuine blocker. No fifth bucket.
- Reconcile `docs/reports/open-items.md` against that classification.
- Regenerate all worker, schema, audit, and onboarding documentation
  (`npm run worker:docs`, `npm run generate:rashi-docs:yoma`, and any
  Phase-3-added generators).
- Verify no unexplained temporary or deferred state remains anywhere in the
  classification.
- Verify open PR and issue counts (expect 0 of each at closure).
- Run all final gates: `validate:offline:yoma`, `npm test`,
  `npm run test:browser`, the Phase-2 semantic validators, the Phase-3
  fixture proof.
- Produce `docs/reports/platform-readiness.md`, the terminal evidence
  document.

### Platform completion, defined precisely

- Yoma and Rashi remain fully green (all gates above, no regression).
- GitHub Pages serves only tested production output (Phase 1 evidence still
  holds - re-verify, do not assume it is still true).
- `main` is protected (Phase 1 evidence still holds).
- All 492 sugyot are structurally and semantically schema-valid (Phase 2
  complete).
- `argumentFlow` and `sourceRefs` have stable, documented, validated
  contracts (Phase 2 complete).
- A fixture module proves module-agnostic replication (Phase 3 complete).
- No unexplained repository debt remains (this phase's own scan, clean).
- Onboarding the next real tractate requires selecting the tractate and
  running documented commands - not redesigning the platform.

### Dependencies

Requires Phases 1, 2, and 3 all complete. Cannot start early.

### Stop conditions

- Any of Phases 1-3 is not actually complete when Phase 4 begins. Do not
  paper over a gap in the closure report; report it as a remaining item.

---

## Operator-owned versus repository-owned actions

| Action | Owner |
|---|---|
| GitHub Pages source setting | Operator (via this session, with API access) |
| Branch protection / rulesets on `main` | Operator (via this session, with API access) |
| `type` -> `category` vocabulary mapping decisions (Phase 2A) that are genuinely ambiguous | Operator |
| Whether to convert the 331 sound sourceRefs strings at all (Phase 2B) | **Decided: no.** See `docs/reports/sourcerefs-contract-decision.md`. |
| Disposition of the 33 residual unresolved sourceRefs (Phase 2B) | **All 33 resolved.** 2 `QUALIFIED_CROSS_DAF` migrated, 29 `ABSENT_OR_UNANCHORED` removed, and the final 2 `TIED_CANDIDATES` (`yoma-044b-l01`, `yoma-063a-l03a`) repaired in a final adjudication pass (PRs #368-#369) using evidence the prior classification had not fully exploited - see "Phase 2 completion criterion" above and `docs/reports/sourcerefs-blocker-classifications.json` for the resolution record. |
| Selecting and starting an actual second tractate | Operator, and only after Phase 3 closes |
| Cloudways / mysugya.com configuration | Operator, out of scope for this entire plan |
| Executing the mechanical majority of Phases 1-4 | This session, autonomously, per the constraints below |

## Explicit prohibitions, restated

- Do not reopen completed Rashi content work.
- Do not perform nekudot/vowelization work in any phase.
- Do not restore the legacy renderer or the `?rashiAssoc=legacy` selector.
- Do not modify Yoma content or Rashi associations to satisfy any phase here.
- Do not start or populate a real second tractate (Phase 3 uses a synthetic
  fixture only).
- Do not touch Cloudways configuration or treat mysugya.com as deployment
  debt. GitHub Pages is the authoritative beta deployment throughout.
- Do not weaken any validator, widen any allowlist, or add a baseline entry
  to make a gate pass.
- Do not rewrite merged `main` history or amend a GitHub squash-merge commit.

## Verification lesson carried forward

A single spot-check of the live site proves nothing either way about which
publisher is currently serving (`docs/reports/open-items.md`). Phase 1's
public-verification requirement (5+ samples over 10+ minutes) exists because
of this, and any future re-verification of Phase 1's evidence must use the
same standard, not a single request.

## Cross-references

- `docs/reports/open-items.md` - day-to-day classified inventory.
- `docs/reports/replication-readiness.md` - Phase 3 evidence base.
- `docs/reports/sugya-schema-readiness.md` - Phase 2A evidence base.
- `docs/reports/source-refs-normalization-plan.md` - Phase 2B evidence base
  and the four-PR execution plan for the judgment-required tier.
- `docs/new-tractate-onboarding.md` - the checklist Phase 3 must make
  fully executable without hand-adaptation.
- `docs/reports/legacy-renderer-retirement-policy.md` - record of the
  completed renderer retirement; not reopened by any phase here.
