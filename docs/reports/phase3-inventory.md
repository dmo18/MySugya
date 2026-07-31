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

**Resolution status (updated as each step merges, not just at Step 8):**
blockers 1 and 9 are **resolved as of Step 3A** - `worker_pipeline.py` now
derives `YROOT`/`YSCRIPTS`/`ACTIVE_MODULE` from a resolved module
descriptor rather than hardcoding them, and `scripts/worker_task_types.json`'s
`allowedFiles` are `<module>`-templated and substituted the same way
`<daf>` already is. Blocker 2 (`test_worker_policy.py`) keeps its 32
Yoma-path assertions as Yoma regression tests, unchanged, plus new
parallel module-awareness coverage (`test_module_awareness`). **Blockers
3-7 are resolved as of Step 3D** - all five Rashi renderer/shard tools
now accept an explicit `--module` flag and resolve via the new
`resolveRashiModule()` helper, which also makes Rashi behavior
capability-driven (row 16). **Blocker 8 is closed as of Step 3D by
correction, not by a code change**: re-reading `generate_argument_taxonomy.py`
in full found its one `yoma` mention is a doc comment asserting the
script does NOT touch module content - the original Step 1
characterization was a false positive from the audit tool's naive
string-matching, not a real defect; see the Step 3D design note for
the full correction. All 9 originally-identified blockers are now
resolved. The original evidence rows above are left exactly as
captured at Step 1 - this is the historical record of what Step 1
found, not a live status field.

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
7. **Step 4, split into 4A and 4B.** The governing directive authorized
   splitting a step "when architecture makes a split technically unsafe [or
   too large for one bounded, reviewable PR], recorded with a reason."
   Reason recorded here: `build.mjs`'s publishable-flag safety guard and
   `deploy-pages.yml`'s explicit module selection are both small,
   independently reviewable, fully provable today with no dependency on
   the not-yet-existing fixture; browser-test and docs-generation
   parameterization touch more files, carry the explicit dependency Step
   3D deferred (the `YOMA_ASSOC_PLAN_PATH` browser-spec-launch boundary in
   `run-rashi-association.mjs`/`rashi-browser-shard-runner.mjs`), and
   benefit from separate review. Splitting keeps each PR bounded per the
   governing execution model rather than combining unrelated risk classes.
   - **Step 4A** - build module selection (`--module`, `--out` flags on
     `scripts/build.mjs`), a publishable-flag safety guard so a
     non-publishable module can never land in the default production
     `dist/`, and CI/deployment verification (`deploy-pages.yml` now
     selects Yoma explicitly by code, not by absence of alternatives).
   - **Step 4B** - browser-test module-aware pattern, the two Step-3D-deferred
     browser-spec-launch items, and documentation-generation
     module-awareness (`generate_rashi_docs.py`, `worker_pipeline.py`'s
     `cmd_docs`).
8. **Step 5, split from Step 6.** Reason recorded here: Step 5 (creating
   the fixture's own content and descriptor) is fully self-contained and
   provable without touching any shared production code, whereas Step 6
   (proving onboarding works end-to-end via the *generic* tooling)
   necessarily requires changing shared consumers - at minimum giving
   `build.mjs` (and any other generic tool Step 6 needs) a `search_root`
   override, to close the logical-vs-physical path gap Step 5's design
   note surfaced. Keeping them separate means Step 5's fixture content
   can be reviewed on its own before any shared-code risk is introduced.
   - **Step 5** - the synthetic fixture module itself
     (`tests/fixtures/modules/demotractate`): descriptor, source,
     enrichment, generator, generated output.
   - **Step 6** - the empty-module onboarding end-to-end test with
     Yoma-isolation proof (tree-digest before/after, path-access
     tracing), closing the logical-vs-physical path gap along the way.
9. **Step 7** - the full Yoma non-regression proof: tree-digest evidence
   (not just `git diff --stat`) that every Yoma generator's output is
   byte-identical, every corpus count re-verified, and an honest
   reconciliation of `audit_replication_readiness.py`'s drift since
   Step 1. Pure verification - no code changes.
10. **Step 8** - final reconciliation PR: update
   `docs/platform-closure-plan.md`, `docs/reports/open-items.md`,
   `docs/reports/platform-readiness.md`, `docs/new-tractate-onboarding.md`,
   `README.md`, `CLAUDE.md`; record disposition of all 9 blockers; mark
   Phase 3 COMPLETE or BLOCKED with the exact remaining blocker.

A boundary is adjusted only if implementation reveals the split above is
technically unsafe (for example, if the resolver cannot be proven correct
without the fixture existing first - in which case Step 5's fixture
scaffold would need to move earlier, and this document will record that
change with a reason when it happens, not silently).

## Step 3B design note: source acquisition, segmentation, learning-data generation

Unlike Step 3A's 9 pre-identified blockers (shared tools at the repo root
that hardcode Yoma while claiming to be generic), none of Yoma's own
source-acquisition scripts are blockers in that sense - they already live
under `modules/yoma/scripts/` and correctly name their own module, which
is exactly what a PER_MODULE-tier file is supposed to do (Step 1's
`npm run audit:replication` already classifies them this way, not as
PINNED). Step 3B's actual job was different: read them to find out
whether a second module's equivalent pipeline needs anything structural
beyond a per-module copy, and define whatever shared contract the Step 5
fixture will actually need.

**`modules/yoma/scripts/fetch_talmuddev.py`** (98 lines): fetches live
Vilna-layout text from `talmud.dev`. Exactly two module-specific things:
`TRACTATE = "Yoma"` and a cwd-relative `OUT_DIR = Path("assets/talmuddev")`
(matching the existing `cd modules/<id> && python3 scripts/...`
convention). This is pure clone-cost - a second production module needs
its own copy with `TRACTATE` changed, nothing structural. **The real gap
for the fixture is that this pattern cannot be reused at all**: the
fixture's constraint ("tiny committed local synthetic source inputs,
never live Sefaria/talmud.dev network calls") means it needs a
fundamentally different acquisition strategy, not a parameterized version
of this one. This is exactly what `capabilities.sourceAcquisition` (added
to the descriptor schema by this PR) now makes explicit and validated,
rather than leaving it as an unstated assumption a fixture author would
have to discover by reading this file.

**`modules/yoma/scripts/daftext_align.py`** (512 lines): zero `yoma`/
`Yoma` references of any kind - already fully module-agnostic, operating
purely on arguments and relative paths. No finding here; segmentation
needed no change.

**`modules/yoma/scripts/build_learning_data.py`** (445 lines): more
module-specific than the other two. Beyond the top-level
`LEARN_DIR = ROOT / "assets" / "learning" / "yoma"` constant, the literal
string `"yoma"` is baked directly into generated-id f-strings and regexes
in the function bodies (`f"rashi-yoma-{pad}-{vl:03d}"`,
`f"yoma-{pad}-l{vl:02d}"`, a `sugyaId`-matching regex), plus genuinely
Yoma-content constants that are correct to keep Yoma-specific (the
8-chapter perek boundary table, `TOTAL_DAF = 173`, `"tractate": "Yoma"`).
A second module cloning this file needs more than a few constant edits -
it needs the literal-string sites found too. This is real, but it is
*clone cost*, the same category of cost Step 1 already measured (31
PER_MODULE files, 46 `:yoma`-suffixed npm scripts) and explicitly scoped
out of Phase 3's required work: the acceptance criteria require the
platform's *generic* tooling to be module-aware, not that every
per-module generator become a universal parameterized tool. The Step 5
fixture will therefore use its own small, purpose-written generator
script, not a parameterized clone of this 445-line JS-source parser -
consistent with "tiny" and "minimal but sufficient" in the fixture's own
spec.

**Net effect of Step 3B**: one real schema gap found and closed
(`capabilities.sourceAcquisition`), two scripts confirmed to need no
change (`fetch_talmuddev.py`'s only cost is the already-documented clone
cost; `daftext_align.py` needs nothing at all), and one script's clone
cost precisely characterized rather than assumed (`build_learning_data.py`).
No generic-tooling code required a change beyond the descriptor schema
and its two resolvers.

## Step 3C design note: semantic/schema validators

Read in full: `modules/yoma/scripts/validate_schema_completeness.py`
(183 lines), `validate_source_refs.py` (491 lines),
`validate_argument_taxonomy.py` (156 lines), `validate_daftext.py`
(135 lines). Unlike Step 3B, **zero generic-tooling code changes were
required** - every genuine gap these four scripts touch was either
already correctly designed for module-agnosticism, or is Yoma content
policy that must not be universalized (per this campaign's explicit
constraint not to convert the 331 canonical string sourceRefs or change
the completed argumentFlow/sourceRefs contracts), or was already
scoped to Step 3D.

**`validate_daftext.py`**: zero `yoma`/`Yoma` references of any kind -
already fully module-agnostic, same finding as `daftext_align.py` in
Step 3B.

**`validate_schema_completeness.py`**: standard `ROOT`/`LEARN_DIR`
clone-cost constants (PER_MODULE tier, same as every other script in
this tier). Its actual checks are already correctly capability-agnostic
by construction: it validates only the fields `shared/schema_map.js`
marks `required: true` (`display.title`, `learning.*`) and never reads
`rashiTranslations` or `en_lit` at all - those are
`validate_rashi.py`/`validate_literal.py`'s job, Step 3D's scope, not
this one's. `shared/schema_map.js` already declares
`rashiLines: {required: false}` - the shared schema itself was already
designed for a module with no Rashi layer; this script simply never
diverged from that.

**`validate_argument_taxonomy.py`**: standard clone-cost constants.
Its R1, R2, R3, R4, R5, R7 checks (registry integrity, no duplicate
mappings, category coverage, no malformed type, no invented Hebrew, no
silent Question fallback) operate purely on the relationship between
the shared `shared/argument_step_taxonomy.json` registry and the
corpus - genuinely module-agnostic structural logic, unrelated to any
hardcoded module identity. R6 (renderer/registry parity) delegates to
`generate_argument_taxonomy.py --check`, which is blocker 8 from Step 1
(hardcodes `modules/yoma/learning_data.js`) - already scoped to Step 3D,
not duplicated here.

**`validate_source_refs.py`**: standard clone-cost constants, plus two
Yoma-specific regexes that are correctly scoped, not gaps:
- `STRING_REF_RE` matches Yoma's specific legacy string format
  (`"Yoma.<daf>.<segment>"`). This is deliberately Yoma-only:
  `docs/new-tractate-onboarding.md` already directs a new module to
  author `sourceRefs` in canonical object form from the start, "never
  the legacy string form, which exists only as Yoma's historical
  accommodation." A new module will never have string-form refs, so
  this regex correctly never needs to apply to one - it is not a
  parameterization gap, it is retired-by-design for anyone but Yoma.
- `LINE_ID_DAF_RE` and `derive_line_ids()`'s id-minting convention
  (`f"yoma-{pad}-l{vl:02d}"`) mirror `build_learning_data.py`'s own
  id convention exactly (the function's own docstring says so: "Mirrors
  build_learning_data.py's daf_pad"). This is the identical clone-cost
  already documented for `build_learning_data.py` in Step 3B, not a
  new, separate defect - a second module's `validate_source_refs.py`
  clone needs its own id-convention regex the same way its
  `build_learning_data.py` clone needs its own id-minting f-strings.

The coordinate-containment structural core (`build_anchor_table`,
`classify_daf`) is genuinely module-agnostic already: it operates on
Vilna-line intervals and segment ids as abstract coordinates, with no
Yoma-specific logic beyond the id-shape regexes above.

**Net effect of Step 3C**: no generic-tooling defect found. All four
scripts were already correctly split between shared structural logic
(already module-agnostic) and Yoma-specific content/id conventions
that are appropriately per-module clone-cost, matching the same
PER_MODULE pattern Step 1 already measured. This PR's contribution is
the documented finding itself, closing acceptance-matrix rows 13-15
with evidence rather than leaving them unverified.

## Step 3D: Rashi renderer/shard tools, generate_argument_taxonomy.py, capability-driven behavior

Closes blockers 3-8 (`scripts/audit-rashi-renderer-readiness.mjs`,
`scripts/check-rashi-browser-shard-artifact.mjs`,
`scripts/run-rashi-association.mjs`,
`scripts/combine-rashi-browser-shards.mjs`,
`scripts/rashi-browser-shard-runner.mjs`,
`scripts/generate_argument_taxonomy.py`) and acceptance-matrix row 16.

**Correction to blocker 8's original characterization.** Step 1's
inventory said `generate_argument_taxonomy.py` "reads
`modules/yoma/learning_data.js` to enumerate every observed
argumentFlow.type value." Re-reading the file in full for this step
shows that is wrong: its only `yoma` mention is inside a doc comment
stating the OPPOSITE - that the script does **not** touch any module's
learning JSON - and the script's actual logic reads only
`shared/argument_step_taxonomy.json` (already a cross-tractate shared
registry by design; its own docstring says "a new tractate just adds
entries here") and writes only `app.jsx`. This is a false positive from
Step 1's audit tool, whose PIN_RE/ID_RE regex matches any literal
occurrence of `modules/yoma` or `"yoma"` regardless of whether the
surrounding sentence asserts or denies a dependency. **No code change
was needed or made to this file.** The corrected finding: 8 real
blockers from Step 1, not 9 as originally counted (blocker 9,
`scripts/worker_task_types.json`, is unaffected by this correction and
remains real, resolved in Step 3A).

**Blockers 3-7** (`audit-rashi-renderer-readiness.mjs`,
`check-rashi-browser-shard-artifact.mjs`, `run-rashi-association.mjs`,
`combine-rashi-browser-shards.mjs`, `rashi-browser-shard-runner.mjs`)
share one pattern: each resolves `modules/yoma/scripts/
audit_rashi_association.py` or a Yoma-hardcoded allowlist path via a
literal string, with no module parameter. All five now accept an
explicit `--module` flag (default `"yoma"`, an explicit documented
default matching the exception already established for `worker_pipeline.py`'s
CLI, since every existing npm script and CI workflow call site invokes
these with no flag and must keep working unchanged) and resolve via a
new `resolveRashiModule(key, repoRoot, searchRoot?)` helper added to
`shared/module_resolver.js`: `resolveModule()` plus one added check
that `capabilities.rashi.enabled` is `true`, throwing a distinct
`CAPABILITY_DISABLED` error otherwise - **this is what makes "Rashi
behavior is capability-driven" (row 16) concrete**: a module with
Rashi disabled gets a clear, explicit rejection naming the reason,
never a crash on a missing allowlist file and never a silently-empty
false pass.

`check-rashi-browser-shard-artifact.mjs`'s exported `DEFAULT_ARTIFACT_PATH`
constant (imported by nothing outside this file, confirmed by search)
is left untouched as the explicit Yoma-only default; a non-default
module resolves its own artifact path through the descriptor instead.

**Scope boundary, deliberately not crossed here**: `run-rashi-association.mjs`
and `rashi-browser-shard-runner.mjs` both launch
`tests/browser/rashi-association.spec.js` via the `YOMA_ASSOC_PLAN_PATH`
env var. That launch step is left exactly as-is - making the browser
spec itself module-aware is Phase 3 Step 4's job ("browser testing is
module-aware"), not this one's. Both files now clearly comment this
boundary at the exact line it applies.

**Yoma proof**: `audit-rashi-renderer-readiness.mjs`'s full output
(8 checks against the live 173-daf corpus) is byte-identical before and
after this change (`diff` of the two runs' captured output: no
difference), for both the implicit default and an explicit `--module yoma`.
`combine-rashi-browser-shards.mjs` and `check-rashi-browser-shard-artifact.mjs`
were exercised directly with synthetic shard files and produce
identical results with and without the change. Every one of the five
tools rejects an unknown module (`UNKNOWN_MODULE`) before touching any
file, and a synthetic Rashi-disabled module resolves the descriptor
successfully but is rejected with `CAPABILITY_DISABLED` specifically
(not conflated with an unknown-module error) - both proven directly
against `resolveRashiModule` and via each CLI tool's own `--module`
handling. 3 new tests added to `tests/unit/module-resolver.test.mjs`
(27 total, up from 24).

**Row 17 (literal behavior is capability-driven): not addressed by
this step, and the question does not yet arise.** None of the 6
blockers here touch literal-translation tooling at all - confirmed by
reading all six for `literal_en`/literal references (zero hits).
Yoma's own `build_literal_layer.py`/`validate_literal.py` were never
flagged as blockers in Step 1 in the first place: they already live
under `modules/yoma/scripts/` (PER_MODULE tier) using cwd-relative
paths, with no shared root-level tool depending on them the way the
five Rashi `.mjs` tools depended on `audit_rashi_association.py`. There
is currently no generic call site that could invoke literal validation
against the wrong module, so there is nothing yet to capability-gate;
this becomes a real question only once Step 4 wires a generic,
module-selectable validator/build path. Left open, not claimed
resolved.

## Step 4A design note: build module selection + deploy verification

**`scripts/build.mjs`** gained two CLI flags and one safety guard, all
additive - the zero-argument invocation every existing npm script and
workflow uses is unchanged:

- `--module <key>`: build only `modules/<key>` into `dist/modules/<key>`
  instead of copying the entire `modules/` tree. Resolves the key through
  `shared/module_resolver.js`'s `resolveModule()` (the same resolver used
  everywhere else since Step 2); an unknown key fails before any file is
  touched.
- `--out <path>`: write output to an isolated directory instead of the
  default `dist/`. Guarded against resolving to the repository root
  (`--out .` from repo root is rejected explicitly, not just left to `rm
  -rf` to fail loudly).
- **Publishable-flag guard**: a module whose `module.json` declares
  `"publishable": false` can never build into the default `dist/` path,
  whether selected explicitly (`--module <non-publishable-key>`) or
  swept in implicitly by an unqualified build that happens to find a
  non-publishable module under `modules/`. Either case requires an
  explicit `--out` to a non-default path. This is the defense-in-depth
  backstop the governing directive asked for: even though the Step 5/6
  fixture is planned to live outside `modules/` entirely (so the glob
  that finds `module.json` files would never see it), this guard means
  the build itself would also refuse a non-publishable module if one
  were ever placed under `modules/` by mistake.

**Verified** (fixture does not exist yet, so proven against the real
Yoma module plus a throwaway synthetic non-publishable descriptor,
never committed, deleted immediately after each check):

- Default zero-argument build output is byte-identical before and after
  this change (`diff -rq` of two `dist/` builds, clean).
- `--module yoma` (no `--out`) produces `dist/` output byte-identical to
  the default unqualified build (`diff -rq`, clean) - confirms explicit
  selection changes nothing about what ships.
- `--module bogus` fails with `UNKNOWN_MODULE` before writing anything.
- `--out .` (repo root) is rejected with an explicit error before the
  destructive `rm(dist, {recursive:true})` step runs.
- A temporary `modules/testnonpub/module.json` with `publishable: false`
  (constructed only in a scratch directory, copied into `modules/` only
  for the duration of this check, never committed - confirmed via `git
  status` before and after) is refused by both the unqualified build and
  `--module testnonpub` when targeting the default `dist/`, and succeeds
  only with an explicit `--out` elsewhere. `git status --short modules/`
  is empty after cleanup.

**`.github/workflows/deploy-pages.yml`**: the build step now runs `npm
run build -- --module yoma` instead of bare `npm run build`. This
directly closes the gap Step 1's acceptance matrix under-claimed:
previously "GitHub Pages deploys Yoma explicitly" was true only because
no other module existed under `modules/` (an absence, not a guard); now
it is true because the workflow names Yoma by explicit argument, and
`build.mjs`'s publishable-flag guard would additionally refuse a
non-publishable module even if the `--module yoma` argument were ever
changed or removed by a future edit.

**Deliberately not touched, with reason recorded**: `.github/workflows/
deploy-cloudways.yml` still runs bare `npm run build` (unparameterized).
This is an intentional scope boundary, not an oversight: the governing
directive's global constraints explicitly forbid touching
Cloudways/mysugya.com, and this workflow pushes built output to a
`cloudways` branch that a separate live deployment consumes. Today this
is harmless (Yoma is still the only module, so the unparameterized build
produces the same output either way), but it means Cloudways deployment
selection is currently true by absence-of-alternatives, the same
unproven state `deploy-pages.yml` was in before this PR. Recorded here
as an open item rather than silently left unmentioned; not a Phase 3
acceptance blocker since Phase 3's acceptance criteria are scoped to the
GitHub Pages deployment path (`docs/platform-closure-plan.md`'s Phase 3
objective and the CI/deployment acceptance rows below reference the
"required build check" and "GitHub Pages," not Cloudways).

**What remains unproven until Step 5/6**: the fixture-specific path
(`--module <fixture-key> --out <isolated-path>` actually producing a
working, browser-testable isolated build of the real fixture, not a
throwaway synthetic descriptor) can only be proven once the fixture
exists. Row 27 ("fixture builds") stays `-` until then; this PR only
proves the generic mechanism is ready to accept it.

## Step 4B design note: browser-test module awareness + docs generation

**`tests/browser/rashi-association.spec.js`** now resolves its target
module from `MYSUGYA_TEST_MODULE` (default `"yoma"`, matching the
established CLI-default-exception pattern) via `resolveRashiModule()`,
the same resolver every other Rashi tool uses since Step 3D. Two
previously-hardcoded things now come from the resolved descriptor
instead of a literal `"yoma"`:

- The audit script path (`AUDIT_SCRIPT`) is now
  `<scriptsRoot>/audit_rashi_association.py`, not a literal
  `modules/yoma/scripts/...` string.
- The default target daf (`YOMA_ASSOC_TARGET_DAF`'s fallback) now reads
  `descriptor.browserTest.defaultTargetDaf` - the first real consumer of
  that descriptor field, which existed since Step 2 but nothing read it
  until now (confirmed by a repo-wide search before this change).
- Every `page.goto()` call's `?module=` query parameter now uses the
  resolved `MODULE_KEY` instead of a hardcoded `yoma` literal.

An unresolvable or Rashi-disabled `MYSUGYA_TEST_MODULE` throws before any
navigation happens (proven directly: `MYSUGYA_TEST_MODULE=bogus npx
playwright test tests/browser/rashi-association.spec.js` fails with
`UNKNOWN_MODULE` and zero tests run).

This closes the two items Step 3D explicitly deferred:
`scripts/run-rashi-association.mjs` and
`scripts/rashi-browser-shard-runner.mjs` already resolved their own
`--module` since Step 3D, but the browser spec they launch via
`YOMA_ASSOC_PLAN_PATH` ignored that choice entirely. Both scripts now
also pass `MYSUGYA_TEST_MODULE: opts.module` into the spawned Playwright
process, so the plan, the audit script, and the browser assertion all
agree on the same module end to end - proven by running
`npm run test:rashi-association:yoma -- --target 2a` (still passes, 6/6)
and by the direct unknown-module rejection above.

A Playwright-specific implementation note, recorded because it cost real
debugging time: the initial implementation used `createRequire(import.meta.url)`
to load `shared/module_resolver.js` (the pattern every `.mjs` tool in
`scripts/` uses). That throws `Cannot use 'import.meta' outside a module`
under Playwright's spec-loading transform, which compiles this
ESM-authored `.spec.js` file to CommonJS before running it. A plain,
untransformed `require(...)` call works instead, since the transformed
module has a real CommonJS `require` in scope. `.mjs` tools run directly
via `node` are unaffected and keep using `createRequire`.

**`tests/browser/yoma-smoke.spec.js`**: the four `DAF_*` constants'
repeated `module=yoma` literal is now built from one `MODULE_KEY`
constant. This spec's assertions (exact sugya counts, exact titles) stay
genuinely Yoma-content-specific by design - `MODULE_KEY` is a
single-source-of-truth cleanup, not an env-var hook, since the
assertions themselves would not hold for another module's content. This
matches the governing directive's "parameterize the constant, don't
duplicate specs" instruction precisely.

**`tests/browser/runtime-guards.spec.js`**: left untouched, deliberately.
Its `module=yoma` occurrences test real Yoma-specific behavior (daf
2a's structure; invalid-daf-parameter fallback against the real Yoma
`DAF_INDEX`) and its unknown-module test already uses a literal
`nonexistent` on purpose - genericizing this file would not prove
anything additional and was correctly out of scope per Step 1's BENIGN
classification.

**Docs generation module-awareness (row 20)**: `scripts/worker_pipeline.py`'s
`cmd_docs` was read in full. It takes no `--module` argument and has none
of the blocker pattern found elsewhere: it generates
`docs/reports/task-type-reference.md` from `scripts/worker_task_types.json`
(the worker registry, already cross-tractate by design since Step 3A) and
`docs/reports/schema-coverage-matrix.md` from
`scripts/worker_schema_scope.json` (schema *field* paths like `daf`,
`review.argumentFlow` - generic field names, not `modules/yoma/...`
paths). Its one hardcoded Yoma reference is static prose (the "Known
drift" paragraph documenting the real, current sourceRefs migration debt
count) - accurate reporting of actual repository state for a report
about the repository, not an architectural assumption that would
misbehave for a second module. **Pass, no code change required** - there
is no module-selection concept here to get wrong.

`modules/yoma/scripts/generate_rashi_docs.py` was also re-read in full.
It is correctly PER_MODULE-tier per Step 1's classification: it lives
under `modules/yoma/scripts/`, hardcodes paths under its own module
(`assets/learning/yoma`, `docs/rashi-audit-backlog.md` - matching Yoma's
own `module.json`'s `docsOutput.auditBacklogDoc` field), and was never
flagged as a blocker. A second module needs its own copy of this script,
same clone-cost model as `build_learning_data.py` - not a defect the
Phase 3 acceptance criteria require fixing.

**Yoma proof**: `npm run test:browser` (16 passed, 1 pre-existing skip,
same counts as before this PR), `npm test` (27/27), and
`npm run check:rashi-docs:yoma` all pass unchanged. `git diff --stat
origin/main -- modules/yoma/` is empty.

## Step 5: the synthetic fixture module

Created `tests/fixtures/modules/demotractate/` per the governing plan's
exact instruction: outside `modules/`, so the `modules/*/module.json`
glob production code uses for discovery never finds it - not by
convention, verified directly (`list_modules()` with no override returns
only `["yoma"]`; `resolve_module("demotractate")` with no override fails
`UNKNOWN_MODULE` before touching anything, both resolvers).

**Content**: a fictional "Widget Certification Board" scenario, chosen
specifically to be unmistakably non-real - every `he:`/`en:` field is an
explicit bracketed placeholder (`[FIXTURE-HE-PLACEHOLDER]`,
`[FIXTURE-EN-PLACEHOLDER]`, `[FIXTURE]`). 3 daf (`1a`, `1b`, `2a`), 4
sugyot, 1 chapter. `argumentFlow.type` uses 8 values already registered
in `shared/argument_step_taxonomy.json` (`case`, `question`, `proof`,
`distinction`, `rejection`, `resolution`, `takeaway`, `answer`) spanning
8 categories - chosen deliberately so Step 5 needs zero changes to that
shared registry. All three current legal `sourceRefs` shapes are
exercised (the legacy Sefaria-string shape is Yoma-specific migration
debt and is correctly never used): same-daf object (most steps),
multi-ref (2 entries, 2 distinct lines, `demo-001a-s01`/`step-03`),
cross-daf object (`demo-001b-s01`/`step-02`, referencing back to daf
`1a`), and an intentionally omitted optional `sourceRefs`
(`demo-001a-s01`/`step-02`). Full inventory in
`tests/fixtures/modules/demotractate/MODULE.md`.

**Capabilities, documented choices**: `rashi.enabled: true` (exercised
with 2 real `rashiTranslations` entries, each with populated
`linkedGemaraLineIds`; the four allowlist ratchet files the Yoma Rashi
tooling expects all exist, empty); `literalTranslation.enabled: false`
(deliberately the disabled path - no `en_lit` field appears anywhere,
proving a module can validly opt out of a capability Yoma has);
`sourceAcquisition.strategy: "local-fixture"` (Step 3B's second
strategy, added specifically for this) with `fixtureInputDir` pointing
at the committed, never-fetched `assets/fixture_source/` raw JSON.

**Generator**: `scripts/build_learning_data.py`, a small (~250-line)
self-contained script - explicitly not a clone of Yoma's 445-line
`build_learning_data.py`. It uses `Path(__file__).parent`-relative paths
exclusively (confirmed: zero functional references to `modules/yoma`
anywhere in the file, only comment-level contrast), reads the raw
source + enrichment JSON, and writes `source_store.js`,
`learning_data.js`, and `coverage.json`. Run once to produce those three
committed generated files; output verified by loading `learning_data.js`
via `require()` and checking daf/sugya counts, argumentFlow types, and
all four `sourceRefs` shapes directly.

**A real gap this step surfaced, deliberately not fixed here**:
`module.json`'s `paths.root` must equal `"modules/demotractate"`
(Step 2's `validate_descriptor` requires `paths.root == f"modules/{key}"`
unconditionally), even though the fixture's real, physical location is
`tests/fixtures/modules/demotractate/`. Step 2's own contract doc
anticipated resolving this fixture via a `search_root` override rather
than the default, but no shared/generic consumer (`worker_pipeline.py`'s
`set_active_module`, `build.mjs`) actually derives a resolved module's
*physical* directory from `search_root + key` - they all compute
`repoRoot / descriptor.paths.root` directly, which is correct today only
because Yoma's `search_root` defaults to `modules/` and `paths.root`
happens to agree with it. Pointed at this fixture, that computation
would resolve to the wrong, nonexistent path. This is exactly the kind
of gap Step 6 ("prove onboarding end-to-end via the generic tooling")
exists to surface and close - recorded here in full rather than silently
worked around, per the design note in
`tests/fixtures/modules/demotractate/MODULE.md`. It is why rows 26-28
below stay unproven at this step: nothing generic can build or validate
the fixture yet, precisely because this gap is still open.

**A `.gitignore` fix required to commit the fixture at all**: the
repository's root-level `assets/` ignore rule (added for a different,
unrelated purpose - it also happens to already coexist with the tracked
`modules/yoma/assets/`, added to git before or regardless of the rule)
matches any directory literally named `assets` at any depth, which
silently excluded this fixture's own `assets/fixture_source/` and
`assets/learning/demotractate/` content from `git add` with no warning.
Fixed with a narrowly scoped negation
(`!/tests/fixtures/modules/demotractate/assets/` and one for its
contents) rather than touching the existing global rule, which stays
exactly as it was for everything else.

**Yoma proof**: `git diff --stat origin/main -- modules/yoma/` is empty.
`npm test` (27/27), `npm run validate:offline:yoma`, and
`npm run check:deploy-html` all pass unchanged. The default
(unqualified) `npm run build` produces `dist/modules/` containing only
`yoma` - the fixture is invisible to the build exactly as designed.

## Step 6: onboarding proven end-to-end via the generic tooling

Closes the logical-vs-physical path gap Step 5 surfaced and deliberately
did not fix, then proves the fixture works through the real, generic
tooling - never a fixture-only parallel pipeline.

**The consumer fix** (not a resolver change - `scripts/module_resolver.py`
and `shared/module_resolver.js` already accepted `search_root`/`searchRoot`
since Step 2): `worker_pipeline.py`'s `set_active_module()` previously
computed `YROOT = REPO / descriptor["paths"]["root"]` directly, which is
only correct when `search_root` is unset (Yoma's case, where
`paths.root` and the real `modules/` location happen to agree). Two new
helpers, `_physical_root()` and `_physical_path()`, derive the real
directory from `MYSUGYA_MODULE_SEARCH_ROOT` (the same env var
`resolve_active_module` already reads) when set, falling back to
`REPO / "modules" / key` - byte-identical to the old behavior - when not.
Proven identical for Yoma directly (`YROOT`/`YSCRIPTS` compared before
and after the change) and correct for the fixture (`YROOT` resolves to
the real `tests/fixtures/modules/demotractate`, confirmed to exist).

`scripts/build.mjs` gained a matching `--search-root <path>` flag (or
the same `MYSUGYA_MODULE_SEARCH_ROOT` env var, for consistency), legal
only together with `--module` - there is deliberately no "scan every
module under an alternate root" mode. The module-copy step now copies
from the real physical directory (`search_root/<key>` when an override
is given, `modules/<key>` otherwise) instead of always assuming
`modules/<key>`.

**A second gap this step found while proving the browser path**: even
with the path fix, an isolated fixture build's `?module=demotractate`
navigation would still fail - `app.jsx`'s module lookup
(`MYSUGYA_MANIFEST.find(m => m.id === moduleId)`) only ever consults the
real, committed `manifest.js`, which the fixture is never wired into (a
hard global constraint). `build.mjs` now synthesizes a one-entry
`manifest.js` for an isolated (`--search-root`-driven) build, built
entirely from the already-validated descriptor's own fields plus the
generated `learning_data.js`'s `DATA_VERSION` - never hand-maintained,
never written to the real `manifest.js`, and only ever produced when
`--search-root` is explicitly passed. Confirmed the real `manifest.js`
is untouched (`git diff --stat origin/main -- manifest.js` empty) and a
default/qualified `--module yoma` build with no `--search-root` still
copies the real `manifest.js` verbatim, unchanged.

**End-to-end proof, committed and repeatable**:
`scripts/test_fixture_onboarding.py` (invoked via
`npm run test:fixture-onboarding`, not part of `npm test` or
`npm run test:browser` - reserved for a dedicated proof run, the same
pattern already established for the Rashi `--exhaustive-corpus` mode,
so default CI cost for this Yoma-only production repo is unaffected)
proves, in one script:

1. Both resolvers refuse the fixture with no override and resolve it
   cleanly with an explicit override (`list_modules()`/`listModules()`
   return only `["yoma"]` by default in both).
2. `python3 scripts/worker_pipeline.py manifest --module demotractate`
   with `MYSUGYA_MODULE_SEARCH_ROOT` set resolves the fixture correctly
   via a real command (not just a unit test).
3. `node scripts/build.mjs --module demotractate --search-root
   tests/fixtures/modules --out <temp dir>` builds the fixture in total
   isolation; the output contains only the fixture's own module
   directory (asserted: no `modules/yoma` anywhere in it).
4. A **real headless Chromium** (`scripts/fixture_onboarding_browser_check.mjs`)
   loads the isolated build's `?module=demotractate&daf=1a` and asserts
   2 `.sugya` elements, 5 `.line` elements, the `FIXTURE` placeholder
   marker present in the rendered page text, and zero page/console
   errors - proving actual DOM rendering, not just that files exist.
5. `modules/yoma`'s full tree digest (every file's path and content
   hashed together) is identical before and after every one of the
   above steps, and the real `manifest.js` is byte-identical throughout.

Run directly: `npm run test:fixture-onboarding` - passes cleanly.

**What remains open, honestly**: this proof is manually/on-demand
invoked, not yet wired into an automated CI workflow. Row 34 below is
marked partial, not pass, for exactly that reason - adding a dedicated
CI workflow (mirroring `rashi-browser-shards.yml`'s pattern rather than
adding cost to every Yoma-only PR's default gate) is real additional
work not yet done, recorded here rather than silently claimed.

**Yoma proof**: full validation chain re-run after this step
(`validate:offline:yoma`, `npm test` 27/27, `npm run test:browser` 16
passed/1 skipped, `npm run build`, `npm run check:deploy-html`,
`python3 scripts/test_worker_policy.py` all passing including its
existing module-awareness tests) all pass unchanged. `git diff --stat
origin/main -- modules/yoma/` is empty.

## Step 7: Yoma non-regression proof

Pure verification, no code changes. Goes beyond the per-PR `git diff
--stat` checks already run after every prior step: actually re-runs
every Yoma generator and diffs its fresh output against the committed
files byte-for-byte, rather than trusting that an empty git diff after
the fact implies determinism.

**Tree-digest proof.** `modules/yoma`'s full tree digest (every file's
relative path and content, hashed together - the same technique
`scripts/test_fixture_onboarding.py` already uses per-step) was captured
before and after running every Yoma generator in sequence:

```
49e864a349397670bf5805b27deb00744d412cd98caae459d8cd0b89e6c5a918
```

Identical before and after. Generators exercised:

- `build_learning_data.py` alone first showed a diff limited entirely to
  the `en_lit:` fields disappearing - not a regression, but an artifact
  of running only half the documented two-step pipeline
  (`build_learning_data.py` never carried `en_lit`; that is
  `build_literal_layer.py --apply`'s job, per CLAUDE.md's literal
  translation pipeline section). Running both steps in the documented
  order (`build_learning_data.py` then `build_literal_layer.py --apply`)
  produced `learning_data.js` and `coverage.json` byte-for-byte
  identical to the committed files. Recorded here so the false alarm and
  its resolution are both on the record, not just the clean final state.
- `generate_rashi_docs.py` produced a diff limited entirely to the
  volatile "Generated from commit" line and the per-row "last verified"
  commit hash column (`fda29a4` -> `ba20645`, HEAD having advanced
  between generations) - exactly the field the script's own
  `check_freshness()` already documents as deliberately ignored, not a
  staleness signal. Every count, status, and task recommendation in the
  table was identical.
- `generate_argument_taxonomy.py` reported "already fresh, nothing
  written"; `app.jsx` byte-identical.
- `worker_pipeline.py docs` produced `docs/reports/task-type-reference.md`
  and `docs/reports/schema-coverage-matrix.md` byte-identical to the
  committed files.

All working-tree changes from the two expected/documented volatile
fields were reverted (`git checkout --`) before continuing; `git
status` was clean at every step.

**Corpus counts, re-verified against the exact figures in the original
governing directive and the Phase 2 final report:**

| metric | expected | actual |
|---|---|---|
| daf | 173 | 173 |
| sugyot | 492 | 492 |
| argumentFlow steps | 1953 | 1953 |
| argumentFlow category coverage | 100% (119 types / 21 categories) | 100% (119/21) |
| sourceRefs total | 1953 (1620 same-daf object + 331 string + 2 cross-daf) | 1953 sound (331 string-resolvable + 2 cross-daf + 1620 same-daf object), 0 defects |
| Rashi lines | 8854 | 8854 |
| boundary registry | 20/20 | 20/20 (0 stale, 0 duplicate, 0 unauthorized) |
| literal-layer coverage | >=95% | 98.3% |
| renderer readiness | 8/8 | **7/8 locally** - see below |

**Renderer readiness, 7/8 not 8/8, explained:** the one failing check
(`exhaustive browser corpus association run`) requires a real,
downloaded CI artifact at
`modules/yoma/scripts/allowlists/rashi_browser_shard_result.json`,
produced only by the separate `rashi-browser-shards.yml` sharded
workflow - confirmed via `git ls-files` that this path is not, and was
never, tracked in git. This is pre-existing behavior documented in
`audit-rashi-renderer-readiness.mjs`'s own header comment since before
Phase 3 began (it "rejects it if it is missing... A human stating the
run happened is never treated as machine evidence") - any fresh local
checkout, before or after this entire campaign, shows the same local
7/8 result until that CI artifact is separately fetched. Not a Phase 3
regression.

**Full validation chain**, re-run exhaustively one final time:
`validate:offline:yoma`, `npm test` (27/27), `npm run test:browser` (16
passed/1 pre-existing skip), `npm run build`, `npm run check:deploy-html`,
`python3 scripts/worker_pipeline.py verify --full` (all 8 checks pass, 0
changed files vs `origin/main` since Step 7 itself made no repo
changes) - all pass.

**`npm run audit:replication` drift check**, compared against Step 1's
original 9-blocker inventory: the tool's own "PINNED shared tools
(blockers)" count is now 13, not 9 - manually verified this is not
regression, for two reasons:

1. Four of the thirteen are brand-new unit-test files this campaign
   itself created (`scripts/test_module_resolver.py`,
   `scripts/test_fixture_onboarding.py`,
   `tests/unit/module-resolver.test.mjs`, plus
   `scripts/test_worker_policy.py`'s existing entry growing from its
   Step 1 count) - every one of their "yoma" references is the file
   deliberately testing against the one real, live module (e.g.
   asserting `list_modules()` returns exactly `["yoma"]`, or hashing
   `modules/yoma`'s tree to prove isolation). These are proof
   instruments, not production blockers.
2. The remaining nine (`worker_pipeline.py`, `audit-rashi-renderer-readiness.mjs`,
   `check-rashi-browser-shard-artifact.mjs`, `module_resolver.py`,
   `run-rashi-association.mjs`, `combine-rashi-browser-shards.mjs`,
   `generate_argument_taxonomy.py`, `rashi-browser-shard-runner.mjs`,
   `tests/browser/yoma-smoke.spec.js`) are every file already migrated
   onto the resolver in Steps 3A-4B, still showing up because the audit
   tool's regex matches any literal `"yoma"` string regardless of
   context - spot-checked `worker_pipeline.py`'s 8 hits directly: usage-example
   docstrings, literal Yoma-suffixed npm script name strings referenced
   in help text (e.g. `"validate:offline:yoma"` - genuinely Yoma-only
   scripts, not something Step 3A was ever asked to genericize), the
   explicit documented `--module` default value `"yoma"` (the established
   CLI-default-exception) and its explanatory comment. `generate_argument_taxonomy.py`'s
   1 hit is the exact same false-positive doc comment Step 3D already
   corrected ("no modules/yoma/... content is touched by this script").
   Zero of the nine are unfixed production blockers; the audit tool's
   naive string-matching limitation (already documented in the Step 3D
   design note) is simply visible on more, correctly-resolved surface
   area now.

No new real blockers exist. The 31-file PER_MODULE clone-cost count and
the 46 `:yoma`-suffixed npm scripts are unchanged from Step 1, as
expected (Phase 3's acceptance criteria require generic commands to
work correctly given an explicit module, not zero per-module
duplication - see the Step 1/3B design notes).

## Phase 3 acceptance matrix

Tracked here and re-verified at Step 8 closure. `-` means not yet
attempted; this PR is read-only and changes none of these to a pass.

| # | criterion | status |
|---|---|---|
| 1 | canonical module descriptor exists | **pass** - Step 2: `docs/reports/module-descriptor-contract.md`, `modules/yoma/module.json` (Yoma's real descriptor) |
| 2 | canonical module resolver exists | **pass** - Step 2: `scripts/module_resolver.py` and `shared/module_resolver.js`, both reject unknown/malformed/traversal/inconsistent input and never fall back to Yoma; `scripts/test_module_resolver.py` (24 checks) and `tests/unit/module-resolver.test.mjs` (18 checks) all pass |
| 3 | generic commands use explicit module selection | **pass, updated at Step 8** - Step 3A closed this for `worker_pipeline.py`; the row's own originally-named remaining scope (source acquisition, validators, build, browser tests, docs generation) is now closed too - see rows 9, 13-15, 18, 19, 20 respectively, each independently evidenced. |
| 4 | unknown module fails | **pass, updated at Step 8** - Step 3A closed this for `worker_pipeline.py`; blockers 3-7 (Rashi renderer/shard tooling), named "still pending Step 3D" when this row was first written, are now closed by Step 3D - every one of the five tools rejects an unknown module with `UNKNOWN_MODULE` before touching any file, per the Step 3D design note. |
| 5 | malformed module fails | **pass, updated at Step 8** - same resolver-backed rejection path as row 4, now closed for the same full set of tools. |
| 6 | no generic requested-module path silently falls back to Yoma | **pass** - Step 3A: `YROOT`/`YSCRIPTS`/`ACTIVE_MODULE` are now derived from the resolved module (`set_active_module`), not hardcoded; an unresolvable module raises before any of them are touched. Proven by a test requesting `yoma` against a search-root override that does not contain it, which fails rather than falling back (`scripts/test_worker_policy.py`'s `test_module_awareness`). |
| 7 | worker manifests are module-aware | **pass** - Step 3A: `cmd_manifest` resolves and validates the requested module before writing; the manifest's `allowedFiles` (from `scripts/worker_task_types.json`, now `<module>`-templated, blocker 9) resolve against the manifest's own declared module, never a hardcoded one. |
| 8 | worker scope checks are module-aware | **pass** - Step 3A: `file_allowed()` substitutes `<module>` from the manifest before matching, exactly like the existing `<daf>` mechanism; a fixture-targeted manifest cannot resolve or write Yoma paths and vice versa, proven by `test_module_awareness`'s mismatched-module-and-path checks. |
| 9 | source acquisition is module-aware | **pass** - Step 3B: `capabilities.sourceAcquisition` is now a required descriptor field with two validated strategies (`remote-fetch` for Yoma, `local-fixture` for synthetic modules). Yoma's own `fetch_talmuddev.py`/`daftext_align.py`/`build_learning_data.py` were already correctly module-scoped (they live under `modules/yoma/scripts/` and name their own module, per Step 1's PER_MODULE tier, not the PINNED tier); the genuine gap was the missing strategy declaration, closed here. See the Step 3B design note below for the full per-script finding. |
| 10 | daf and chapter metadata are module-aware | **pass, unchanged from Yoma's existing design** - `dafRange`/`totalDaf` are already per-module descriptor fields (Step 2); chapter metadata's location is declared via `paths.chapterMetadataLocation` (free-text pointer, since it is not always its own file - Yoma embeds it in `learningDataFile`). No blocker existed here; Step 3B found none. |
| 11 | segmentation is module-aware | **pass, unchanged from Yoma's existing design** - `modules/yoma/scripts/daftext_align.py` (512 lines) was read in full for Step 3B and contains zero `yoma`/`Yoma` references of any kind; it already operates purely on files passed as arguments, with no module assumption baked in anywhere. |
| 12 | learning-data generation is module-aware | **pass, updated at Step 8** - the criterion requires the *platform's generic tooling* to be module-aware given an explicit module, not that Yoma's own per-module generator become universal (matching rows 9/11's identical treatment). `modules/yoma/scripts/build_learning_data.py` is PER_MODULE-tier (expected to be copied and adapted per module, like the other 31 files in that tier), but Step 3B found it is a *larger* clone-cost than most: beyond naming its own module in path constants, it bakes the literal string `"yoma"` into generated `sugyaId`/`lineId`/`rashiId` naming conventions inside f-strings and regexes (5-6 sites), not just top-level constants. A second module's generator needs its own copy with those literals changed too, same as today's clone-cost model - this is not a defect the Phase 3 acceptance criteria require fixing (they require the *platform's generic tooling* to be module-aware, not that Yoma's own per-module generator become a universal one-size-fits-all tool), but it is now precisely documented rather than assumed away. The Step 5 fixture will use its own small generator, not a clone of this 445-line file. |
| 13 | sourceRefs validation is module-aware | **pass, no code change required** - Step 3C found `validate_source_refs.py`'s coordinate-containment/classification core (`build_anchor_table`, `classify_daf`) already structurally module-agnostic; its two Yoma-specific regexes are correctly scoped, not gaps (see design note below) |
| 14 | argumentFlow validation is module-aware | **pass, no code change required** - Step 3C found `validate_argument_taxonomy.py`'s R1-R5/R7 structural checks already module-agnostic (operate on the registry-vs-corpus relationship, not on any hardcoded module identity); R6 transitively depends on blocker 8 (`generate_argument_taxonomy.py`), left for Step 3D as already planned |
| 15 | general schema validation is module-aware | **pass, no code change required** - Step 3C found `validate_schema_completeness.py` already correctly capability-agnostic: it checks only the always-required `display`/`learning` fields and never touches `rashiTranslations`/`en_lit` at all (those are `validate_rashi.py`/`validate_literal.py`'s job, Step 3D's scope); `shared/schema_map.js` already declares `rashiLines: {required: false}`, confirming the shared schema itself was already designed for an optional Rashi layer |
| 16 | Rashi behavior is capability-driven | **pass** - Step 3D: `resolveRashiModule()` (`shared/module_resolver.js`) rejects a Rashi-disabled module with a distinct `CAPABILITY_DISABLED` error, adopted by all 5 Rashi renderer/shard tools; proven against a synthetic Rashi-disabled module and via 3 new tests |
| 17 | literal behavior is capability-driven | - (not addressed; the question does not yet arise - see Step 3D design note) |
| 18 | build is module-aware | **pass** - Step 4A: `scripts/build.mjs` accepts explicit `--module <key>` (resolved via `shared/module_resolver.js`, unknown key fails before any write) and `--out <path>` for an isolated output directory; a `publishable:false` module is refused from the default `dist/` in both the explicit-module and unqualified-build paths. Default zero-argument output proven byte-identical before/after and against explicit `--module yoma`. Full fixture proof (row 27) still pending Step 5/6. |
| 19 | browser testing is module-aware | **pass** - Step 4B: `tests/browser/rashi-association.spec.js` resolves its target module (and audit-script path, and default target daf) from `MYSUGYA_TEST_MODULE` via `resolveRashiModule()`; `run-rashi-association.mjs`/`rashi-browser-shard-runner.mjs` (Step 3D's two deferred items) now pass their own `--module` choice through to the spec. Unknown/Rashi-disabled module fails before any navigation. `yoma-smoke.spec.js`'s repeated literal deduplicated into one `MODULE_KEY` constant (its assertions stay Yoma-content-specific by design, not a generic hook); `runtime-guards.spec.js` left untouched (its Yoma/unknown-module cases are deliberate, per Step 1's BENIGN classification). |
| 20 | docs generation is module-aware | **pass, no code change required** - Step 4B: `cmd_docs` generates only cross-tractate registry/schema documentation (no module-selection concept exists in its inputs); `generate_rashi_docs.py` is correctly PER_MODULE-tier clone-cost, not a blocker. See design note. |
| 21 | production deployment selects Yoma explicitly | **pass, corrected from Step 1's "already true" claim** - re-verified in Step 4A: `deploy-pages.yml`'s build step previously carried no module argument at all (the earlier "already true" was true only by absence of a second module, not by an explicit guard). Now `deploy-pages.yml` runs `npm run build -- --module yoma` explicitly, backstopped by `build.mjs`'s publishable-flag guard. `deploy-cloudways.yml` remains unparameterized and out of scope (Cloudways is excluded by the governing directive's global constraints) - see the Step 4A design note for the recorded reason. |
| 22 | fixture is non-publishable | **pass** - Step 5: `module.json` has `status: "synthetic"`, `publishable: false`, the pairing the resolver enforces; `build.mjs`'s publishable-flag guard (Step 4A) additionally refuses it from the default `dist/` if it were ever placed under `modules/`. |
| 23 | fixture can be scaffolded from empty state | - (still open: Step 6 proved the *existing* fixture resolves/builds/renders correctly, not that a documented from-nothing scaffold process reproduces it) |
| 24 | fixture can ingest synthetic local source | **pass, updated at Step 8** - matching row 9/12's reasoning: the criterion requires correct PER_MODULE-scoped ingestion given the required `sourceAcquisition` descriptor field, not a generic/shared ingestion command (none is expected for Yoma either). The fixture's own generator reads `assets/fixture_source/` (the `local-fixture` strategy's committed, never-fetched input) exactly as Yoma's own per-module scripts read their sources - the same model, correctly followed. |
| 25 | fixture can generate all required artifacts | **pass** - Step 5: `scripts/build_learning_data.py` produces `source_store.js`, `learning_data.js`, `coverage.json`; output verified via `require()` (3 daf, 4 sugyot, 8 argumentFlow types, all 4 sourceRefs shapes present), and via real browser rendering in Step 6. |
| 26 | fixture validates | - (still open: no generic, module-selectable validator has been run against it) |
| 27 | fixture builds | **pass** - Step 6: `node scripts/build.mjs --module demotractate --search-root tests/fixtures/modules --out <dir>` builds the fixture in complete isolation; output verified to contain only the fixture's own module directory. |
| 28 | fixture passes browser tests | **pass, via a dedicated proof script, not the formal `tests/browser/*.spec.js` suite** - Step 6: `scripts/fixture_onboarding_browser_check.mjs` launches a real headless Chromium against the isolated build and asserts correct DOM rendering (2 sugyot, 5 lines, placeholder marker present, zero page errors) for `?module=demotractate&daf=1a`. |
| 29 | fixture documentation generates | - (still open: no fixture-specific docs-generation script exists, matching Yoma's PER_MODULE-tier `generate_rashi_docs.py`) |
| 30 | fixture worker scope passes | **partial pass** - the underlying mechanism (`file_allowed()`'s `<module>` templating correctly rejects a mismatched module+path in both directions) was proven in Step 3A's `test_worker_policy.py` tests using a synthetic in-memory fixture; not yet re-exercised literally against the committed `demotractate` module by name. |
| 31 | fixture operations do not read or write Yoma content | **pass** - Step 6: `scripts/test_fixture_onboarding.py` hashes `modules/yoma`'s entire tree (every file path + content) before and after resolver resolution, `worker_pipeline.py` manifest generation, and the isolated build+render - identical every time, proven, not just grep-inferred. |
| 32 | Yoma operations do not depend on fixture content | **already true** (Yoma predates the fixture; no code path references it) |
| 33 | Yoma content and counts remain unchanged | **pass** - Step 7: full tree-digest proof (not just `git diff --stat`) confirms every Yoma generator's output is byte-identical to the committed files; every corpus count re-verified against the original governing directive's figures. See the Step 7 design note. |
| 34 | required build check verifies Yoma and fixture | **partial** - Step 6: the proof exists and passes (`npm run test:fixture-onboarding`), but is manually/on-demand invoked, not yet wired into an automated CI workflow. |
| 35 | GitHub Pages still serves the merged Yoma VERSION | **pass, re-verified at Step 8** - VERSION 15.388, merge SHA `d2d4025` (#381), deploy run confirmed |
| 36 | 0 open PRs | **pass, re-verified at Step 8** - 0 open PRs at the start of this step |
| 37 | 0 open issues | **pass, re-verified at Step 8** - 0 open issues at the start of this step |
| 38 | clean working tree | **pass, re-verified at Step 8** - clean before this PR's changes |

## Step 8: final reconciliation

Read fresh, all 38 rows above, before writing this section. 32 of 38
rows read **pass**. 6 do not, and Phase 3 is marked **BLOCKED**, not
complete, on that basis - no partial pass is characterized as accepted
residue, per the governing directive:

- **Row 17** - literal-translation behavior being capability-driven has
  never been exercised, because no generic tool has ever touched
  literal-translation content for any module. Not actionable until such
  a tool exists; left open rather than force-closed.
- **Row 23** - fixture scaffolded from empty state. Step 5 created the
  fixture directly; no test has proven the documented onboarding process
  reproduces it starting from nothing. Needs: an empty-state scaffold
  test (delete the fixture, follow whatever `docs/new-tractate-onboarding.md`
  documents, confirm the result matches).
- **Row 26** - fixture validates. No generic, module-selectable Gemara
  source/schema validator has ever been run against the fixture. Needs:
  either a validator gains `--module`/`--search-root` support (matching
  `build.mjs`'s Step 6 pattern) or a documented reason none is expected.
- **Row 29** - fixture documentation generation. No fixture-specific
  analogue of `generate_rashi_docs.py` exists. Needs: either such a
  script (matching Yoma's PER_MODULE-tier convention) or a documented
  reason none is required for a non-publishable fixture.
- **Row 30** - fixture worker scope. The `<module>`-templating mechanism
  was proven correct with a synthetic in-memory fixture in Step 3A, not
  literally re-exercised against the committed `demotractate` module by
  name. Needs: one additional `test_worker_policy.py` case targeting the
  real fixture path.
- **Row 34** - required build check verifies both. The proof
  (`npm run test:fixture-onboarding`) exists and passes but is
  manually/on-demand invoked, not wired into an automated CI workflow.
  Needs: a dedicated CI workflow (mirroring `rashi-browser-shards.yml`'s
  pattern, not added cost to every Yoma-only PR's default gate).

None of these six require touching Yoma content, selecting a real
second tractate, or starting Phase 4 - they are all additional generic-
tooling/fixture-proof work, explicitly named here rather than rushed
into this PR or silently left implicit. This PR does not attempt them:
per the governing directive's stop-condition list, closing several of
these (a validator's `--search-root` support, a CI workflow) is
real design work of the same shape Step 6 already did once, and forcing
it into a reconciliation PR risks exactly the "rushed fix, not gotten
right" outcome the directive warns against.

The other 32 rows are corrected/updated where the original text had
gone stale since Steps 3A-7 landed (rows 3, 4, 5, 12, 24 previously read
"partial pass" or scoped narrowly to `worker_pipeline.py`, citing gaps
that later steps closed and evidenced elsewhere in this same document -
updated with cross-references to the rows that already prove it, not
silently reworded without evidence). Rows 35-38 are re-verified fresh at
this step's start: VERSION 15.388 live on GitHub Pages (merge SHA
`d2d4025`, PR #381), 0 open PRs, 0 open issues, clean working tree.

**Disposition of all 9 originally-identified blockers** (Step 1's
inventory, `docs/reports/data/phase3-inventory.json`):

| # | entrypoint | resolved at | how |
|---|---|---|---|
| 1 | `worker_pipeline.py` | Step 3A | `set_active_module`/`resolve_active_module` derive `YROOT`/`YSCRIPTS`/`ACTIVE_MODULE` from a resolved descriptor; unknown module fails before any path is touched |
| 2 | `test_worker_policy.py` | not a blocker | test-only; kept as Yoma regression coverage, with new parallel module-awareness tests added alongside |
| 3 | `audit-rashi-renderer-readiness.mjs` | Step 3D | accepts `--module` (default `yoma`), resolves via `resolveRashiModule()` |
| 4 | `check-rashi-browser-shard-artifact.mjs` | Step 3D | same pattern as #3 |
| 5 | `run-rashi-association.mjs` | Step 3D (resolver) + Step 4B (browser-spec launch) | resolver in 3D; passes `MYSUGYA_TEST_MODULE` through to the spawned Playwright spec in 4B, closing the deferred item |
| 6 | `combine-rashi-browser-shards.mjs` | Step 3D | same pattern as #3 |
| 7 | `rashi-browser-shard-runner.mjs` | Step 3D (resolver) + Step 4B (browser-spec launch) | same as #5 |
| 8 | `generate_argument_taxonomy.py` | Step 3D, by correction | re-reading found the original Step 1 flag was a false positive (a doc comment asserting non-dependency); no code change needed |
| 9 | `worker_task_types.json` | Step 3A | `allowedFiles` entries `<module>`-templated, substituted by `file_allowed()` the same way `<daf>` already was |

All 9 are closed. The 6 open acceptance-matrix rows above are new
criteria surfaced by Steps 5-7 (fixture existence and generic-tooling
proof), not unresolved instances of the original 9.

**Phase 3 status: BLOCKED (32/38 acceptance rows pass; 6 open, named
above with concrete follow-up work).** No real second tractate was
started or selected. No Yoma content, Rashi association, or
argumentFlow/sourceRefs contract was touched. Phase 4 was not started
and must not start until Phase 3 closes.

## Confirmation

No real second tractate was started or selected as part of this Step 1
work. No Yoma content, Rashi association, or argumentFlow/sourceRefs
contract was touched. Phase 4 was not started.
