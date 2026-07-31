# Phase 3 Step 1: replication-blocker inventory

**Status: read-only audit, verified against main `be70ba9` (VERSION 15.377).
Not a restatement of `docs/reports/replication-readiness.md`'s prose - every
blocker below was re-checked against current main, and one new blocker
(entry 8) and one new blocker class the existing audit tool cannot see
(entry 9) were found in the process.**

Machine-readable form: `docs/reports/data/phase3-inventory.json`. Full
per-entrypoint detail (purpose, module-selection mechanism, hardcoded
assumption, input/output paths, validators/generators invoked, implicit
read/write, unknown/no-module behavior, required change, regression risk,
fixture/Yoma proof required) lives there; this document summarizes it and
defines the acceptance matrix and PR sequence.

## Why 8, not 7

`docs/reports/replication-readiness.md` documents 7 Yoma-pinned shared
tools. Re-running the audit tool that produced that table
(`npm run audit:replication -- --json`) against current main shows **8**:
`scripts/generate_argument_taxonomy.py` was added during Phase 2A (the
argumentFlow category-registry mechanism), after the 7-file table was last
written, and it hardcodes `modules/yoma/learning_data.js`. The audit tool
itself already classifies it correctly as PINNED; the written table simply
predates it.

## A blocker class the existing audit tool cannot see

`scripts/audit_replication_readiness.py`'s `SCAN_GLOBS` cover
`scripts/*.py`, `scripts/*.mjs`, `shared/*.js`, browser/unit/smoke test
files, and workflow YAML - but never `*.json`. `scripts/worker_task_types.json`,
the registry that declares every worker task type's file/JSON-path scope
contract, hardcodes **116** literal `modules/yoma` occurrences across its
~13 task-type entries, and every one of them feeds directly into
`worker_pipeline.py`'s scope enforcement. This is entry 9 below. It is a
config-data blocker, not a code blocker, but it sits on the same trust
boundary the worker pipeline depends on (allowed vs. forbidden file
scope), so Phase 3 cannot be complete without addressing it.

## The 9 replication blockers

| # | entrypoint | reads Yoma implicitly | writes Yoma implicitly | unknown-module behavior (live-verified) |
|---|---|---|---|---|
| 1 | `scripts/worker_pipeline.py` (13 subcommands) | yes | yes | **silently accepted** - manifest's `module` field takes the unknown value, but every path stays `modules/yoma/...`. Live-reproduced: `manifest --type rashi-repair --module bogus-module --range 2a` succeeds and writes `allowedFiles: ["modules/yoma/assets/learning/yoma/<daf>.learning.json", ...]` |
| 2 | `scripts/test_worker_policy.py` | no (test-only) | no | n/a - hardcoded Yoma-shaped fixture strings, no module parameter exercised |
| 3 | `scripts/audit-rashi-renderer-readiness.mjs` | yes | no | no module parameter exists at all |
| 4 | `scripts/check-rashi-browser-shard-artifact.mjs` | yes | no | no module parameter exists at all |
| 5 | `scripts/run-rashi-association.mjs` | yes | no | no module parameter exists at all |
| 6 | `scripts/combine-rashi-browser-shards.mjs` | yes | no | no module parameter exists at all |
| 7 | `scripts/rashi-browser-shard-runner.mjs` | yes | no | no module parameter exists at all |
| 8 | `scripts/generate_argument_taxonomy.py` | yes | no (writes shared `app.jsx`) | no module parameter exists at all |
| 9 | `scripts/worker_task_types.json` (registry, 116 refs) | yes | n/a (config data) | the registry itself has no module concept; every type's declared paths are Yoma paths regardless of the requesting manifest's module |

Already generic, confirmed by the fixture-check portion of the existing
audit tool plus direct inspection - **no change required**:
`scripts/build.mjs`, `app.jsx`, `manifest.js`, `playwright.config.js`,
`scripts/worker_schema_scope.json`, and the three deployment workflow YAML
files (module selection in those happens through the npm scripts/`.mjs`
tools above, not the workflow files themselves).

Not a blocker, tracked separately as clone cost (not required by Phase 3's
acceptance criteria, since those require generic commands to work
correctly given an explicit module, not zero per-module duplication): 31
`modules/yoma/scripts/*.py` files name their own module id, and 46 of the
repository's npm scripts are `:yoma`-suffixed with no generic sibling.

## Proposed PR sequence for the remainder of Phase 3

Each PR branches from freshly merged `origin/main`, bumps VERSION once,
and must leave Yoma's generated data byte-identical (proven per PR, not
just at the end).

1. **This PR (Step 1)** - inventory only, no code changes beyond this
   report and its machine-readable companion. Establishes the blocker list
   and acceptance matrix below.
2. **Step 2** - canonical module descriptor schema + resolver
   (`shared/module_registry.js` or equivalent for the JS side,
   `scripts/module_resolver.py` for the Python side, backed by one
   canonical descriptor source both read). Strict validation: unknown
   module, malformed descriptor, missing required field, path traversal,
   feature inconsistency, non-publishable-fixture-as-production all
   rejected. No fixture corpus yet - resolver tests use synthetic
   in-memory descriptors.
3. **Step 3A** - `worker_pipeline.py` + `test_worker_policy.py` +
   `scripts/worker_task_types.json` (blockers 1, 2, 9) migrated onto the
   resolver. This is the highest-risk PR (entry 9's regression risk is
   rated High) and is kept separate from every other blocker for that
   reason.
4. **Step 3B** - source acquisition / source-store / daf-inventory /
   chapter-metadata / segmentation parameterization (none of the 9
   blockers above cover this directly since Yoma's source-acquisition
   scripts already live under `modules/yoma/scripts/` and name their own
   module by convention; this PR defines the *shared* acquisition
   contract the fixture will use, per Phase 3 Step 3B of the governing
   plan).
5. **Step 3C** - semantic/schema validator parameterization
   (`validate_source_refs.py`, `validate_argument_taxonomy.py`,
   `validate_schema_completeness.py` and friends already live per-module
   under `modules/yoma/scripts/`; this PR proves the *shared contracts*
   they implement are expressible against a second module without
   duplicating Yoma-specific content policy into a universal rule).
6. **Step 3D** - blockers 3-7 (the Rashi renderer-readiness/shard tooling)
   plus `generate_argument_taxonomy.py` (blocker 8), all migrated onto the
   resolver, plus explicit capability-driven enable/disable behavior for
   Rashi and literal-translation features.
7. **Step 4** - build/runtime module selection, browser-test
   parameterization, documentation-generation parameterization, and the
   CI/deployment PR (required build check verifies both Yoma and the
   fixture; GitHub Pages continues to select Yoma explicitly).
8. **Step 5+6** - the synthetic fixture module itself
   (`tests/fixtures/modules/<fixture-key>`) plus the empty-module
   onboarding end-to-end test with Yoma-isolation proof (tree-digest
   before/after, path-access tracing).
9. **Step 8** - final reconciliation PR: update
   `docs/platform-closure-plan.md`, `docs/reports/open-items.md`,
   `docs/reports/platform-readiness.md`, `docs/new-tractate-onboarding.md`,
   `README.md`, `CLAUDE.md`; record disposition of all 9 blockers; mark
   Phase 3 COMPLETE or BLOCKED with the exact remaining blocker.

A boundary is adjusted only if implementation reveals the split above is
technically unsafe (for example, if the resolver cannot be proven correct
without the fixture existing first - in which case Step 5's fixture
scaffold would need to move earlier, and this document will record that
change with a reason when it happens, not silently).

## Phase 3 acceptance matrix

Tracked here and re-verified at Step 8 closure. `-` means not yet
attempted; this PR is read-only and changes none of these to a pass.

| # | criterion | status |
|---|---|---|
| 1 | canonical module descriptor exists | **pass** - Step 2: `docs/reports/module-descriptor-contract.md`, `modules/yoma/module.json` (Yoma's real descriptor) |
| 2 | canonical module resolver exists | **pass** - Step 2: `scripts/module_resolver.py` and `shared/module_resolver.js`, both reject unknown/malformed/traversal/inconsistent input and never fall back to Yoma; `scripts/test_module_resolver.py` (24 checks) and `tests/unit/module-resolver.test.mjs` (18 checks) all pass |
| 3 | generic commands use explicit module selection | - |
| 4 | unknown module fails | - (currently silently accepted, blocker 1/9) |
| 5 | malformed module fails | - |
| 6 | no generic requested-module path silently falls back to Yoma | - (currently does, blockers 1/9) |
| 7 | worker manifests are module-aware | - |
| 8 | worker scope checks are module-aware | - |
| 9 | source acquisition is module-aware | - |
| 10 | daf and chapter metadata are module-aware | - |
| 11 | segmentation is module-aware | - |
| 12 | learning-data generation is module-aware | - |
| 13 | sourceRefs validation is module-aware | - |
| 14 | argumentFlow validation is module-aware | - |
| 15 | general schema validation is module-aware | - |
| 16 | Rashi behavior is capability-driven | - |
| 17 | literal behavior is capability-driven | - |
| 18 | build is module-aware | - |
| 19 | browser testing is module-aware | - |
| 20 | docs generation is module-aware | - |
| 21 | production deployment selects Yoma explicitly | **already true** (`deploy-pages.yml` builds the repo as-is; `manifest.js`'s first entry is Yoma; no module ambiguity exists in the single-module deploy today) |
| 22 | fixture is non-publishable | - (fixture does not exist yet) |
| 23 | fixture can be scaffolded from empty state | - |
| 24 | fixture can ingest synthetic local source | - |
| 25 | fixture can generate all required artifacts | - |
| 26 | fixture validates | - |
| 27 | fixture builds | - |
| 28 | fixture passes browser tests | - |
| 29 | fixture documentation generates | - |
| 30 | fixture worker scope passes | - |
| 31 | fixture operations do not read or write Yoma content | - |
| 32 | Yoma operations do not depend on fixture content | **already true** (Yoma predates the fixture; no code path references it) |
| 33 | Yoma content and counts remain unchanged | **already true today**; must be re-proven after every subsequent PR |
| 34 | required build check verifies Yoma and fixture | - |
| 35 | GitHub Pages still serves the merged Yoma VERSION | **already true**; must be re-verified after every merge |
| 36 | 0 open PRs | true at Step 1 start; re-verify at every PR boundary |
| 37 | 0 open issues | true at Step 1 start; re-verify at every PR boundary |
| 38 | clean working tree | true at Step 1 start; re-verify at every PR boundary |

Phase 3 remains BLOCKED, not complete, until every row above reads pass -
per the governing directive, a partial pass is never characterized as
accepted residue.

## Confirmation

No real second tractate was started or selected as part of this Step 1
work. No Yoma content, Rashi association, or argumentFlow/sourceRefs
contract was touched. Phase 4 was not started.
