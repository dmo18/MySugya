# Platform readiness: terminal closure record

**This is the Phase 4 terminal platform-readiness document**, not an
interim snapshot. It supersedes this file's own prior content (a Phase 2
snapshot, preserved below in "Phase 2 completion evidence" as accurate
history of that phase's closure) and both the "Phase 3 in progress"
and "Phase 4 not started" notes that file carried - both are now false;
Phase 3 and Phase 4 are complete.

## 1. Executive status

**PLATFORM READY.**

- Final VERSION: `15.397` (bumped by the PR that carries this document;
  regenerate `git log -1 -- VERSION` to confirm live).
- Final main SHA: the merge commit of this PR. Generated pre-merge (a
  PR's own merge commit does not exist at generation time, the same
  caveat `generate_rashi_docs.py` documents elsewhere in this repo) -
  the verified state this document is built from is `d1adec2`
  (VERSION 15.396, PR #389 merged), with this PR's own changes layered
  on top and independently re-verified before merge (see the final gate
  table, section 10).
- Certification date: this PR's merge (see the PR/commit history for
  the exact timestamp).
- Production URL: `https://dmo18.github.io/MySugya/`.

## 2. Phase disposition

| Phase | Status | Evidence |
|---|---|---|
| 1: Production publishing and repository protection | **COMPLETE** | `docs/platform-closure-plan.md`'s Phase 1 completion record; re-verified this session by direct API read-back of ruleset `19991220` (byte-identical to the original record, no drift) and behavioral Pages checks (see section 3). |
| 2: Semantic schema contract (argumentFlow + sourceRefs) | **COMPLETE** | `docs/platform-closure-plan.md`'s Phase 2 completion criterion. `validate_argument_taxonomy.py` 100% category coverage; `validate_source_refs.py --strict` 0 defects across 1,953 refs. Re-run fresh this session (section 4). |
| 3: Tractate-agnostic replication | **COMPLETE, 38/38** | `docs/reports/phase3-inventory.md`'s full acceptance matrix. Step 8 closed 32/38; a six-row closure campaign (PRs #383-#388) closed the remaining 6 (rows 17, 23, 26, 29, 30, 34). Re-verified fresh this session (section 6, section 7). |
| 4: Final repository closure | **COMPLETE** | This document. Step 1-3 inventory and cleanup: `docs/reports/phase4-inventory.md` (PR #389). Step 5 full terminal verification: this session, evidence throughout this document. Step 7-8: this document and its merge. |

## 3. Production controls

- **Pages source**: cannot be read directly this session (`GET
  /repos/dmo18/MySugya/pages` returns `403 Access to this GitHub API
  path is not permitted through this proxy` - an environment-policy
  block, unconditional, unrelated to the setting's actual value;
  unchanged from the original Phase 1 record). Confirmed instead by
  direct evidence: `GET /repos/dmo18/MySugya/deployments
  ?environment=github-pages` shows exactly one deployment per merge SHA
  for the most recent 5 merges (`d1adec2`, `1de8576`, `f442159`,
  `075e4fd`, `d50c180`), sequential, no competing/interleaved
  deployment - behaviorally rules out a dual-publisher race. Live
  `curl` checks throughout this entire campaign (dozens of checks
  across ~10 separate merges) have never once returned a mismatched
  bundle.
- **Required workflow**: `.github/workflows/deploy-pages.yml`'s `build`
  job. It now runs, in order: offline Yoma gates, an explicit
  `--module yoma` production build, deploy-HTML safety check, `npm
  test`, `npm run test:browser`, `npm run test:fixture-onboarding`, and
  `npm run test:module-scaffold` (the last two added by Phase 3's
  six-row closure campaign, PR #387/row 34) - so the fixture-onboarding
  and scaffold-from-empty proofs are enforced on every PR, not merely
  passed once and left to bit-rot.
- **Branch ruleset**: `GET /repos/dmo18/MySugya/rulesets/19991220`
  succeeded via direct API call this session and is byte-identical to
  the original Phase 1 completion record: applies to `refs/heads/main`,
  enforcement `active`, PR required, 0 mandatory approving reviews,
  merge/squash/rebase all allowed, required status check exactly
  `build`, `strict_required_status_checks_policy: true`, `deletion` and
  `non_fast_forward` rules present, `current_user_can_bypass: "never"`,
  no bypass actors. **No drift.**
- **Deployment artifact contract**: `deploy-pages.yml`'s `deploy` job
  uploads only `dist/` (built by the `build` job's explicit `--module
  yoma` invocation) as artifact `github-pages`, deployed via
  `actions/deploy-pages@v4`. `scripts/build.mjs` refuses to build any
  `publishable: false` module into the default `dist/` output
  (confirmed by `docs/reports/phase3-inventory.md`'s Step 4A design
  note and re-exercised by this session's fixture/scaffold proofs,
  which always build to an isolated `--out` directory, never `dist/`).
- **Fixture publication guard**: `demotractate`'s `module.json`
  declares `status: "synthetic"`, `publishable: false` (the pairing the
  resolver enforces - a synthetic module can never be publishable).
  The fixture lives at `tests/fixtures/modules/demotractate/`, outside
  `modules/`, so production module discovery (`modules/*/module.json`
  glob) never finds it regardless of the publishable flag. Two
  independent guards, not one.

## 4. Yoma corpus

Recomputed fresh this session, not copied from an earlier snapshot:

- **Daf**: 173 (2a-88a).
- **Sugyot**: 492, all schema-complete (`validate_schema_completeness.py`:
  492/492 checked, 0 failing; `quizSeeds` 754 checked, 0 incomplete;
  `misconceptions` 551 checked, 0 malformed).
- **argumentFlow**: 1,953 steps, 119 distinct `type` values, 100%
  mapped to a `category` via `shared/argument_step_taxonomy.json`
  (`validate_argument_taxonomy.py`: 100% coverage, 0 malformed values,
  app.jsx/registry byte-parity confirmed).
- **sourceRefs**: 1,953 total refs, **0 defects** of any class
  (`validate_source_refs.py --strict`, run fresh): 1,620 `OK` (same-daf
  object), 331 `STRING_RESOLVABLE` (canonical, permanently retained
  string form - `docs/reports/sourcerefs-contract-decision.md`), 2
  `OK_CROSSDAF` (explicit cross-daf shape -
  `docs/reports/sourcerefs-crossdaf-schema-decision.md`).
  `daf carrying defects: 0`.
- **Literal translation coverage**: 2,300 Gemara lines, 2,267 carry
  `en_lit`, 2,262 non-empty - **98.3% coverage** (threshold 95%,
  `validate_literal.py`).
- **Generic module validation**: `node scripts/validate_module_schema.mjs
  --module yoma` - schema-complete, `capabilities.rashi.enabled=true`
  with 8,854 real `rashiLines`, `capabilities.literalTranslation.enabled=true`
  with 2,262 real `en_lit` fields (capability declarations match corpus
  content in both directions).
- **Advisory, non-blocking**: `npm run audit:schema:semantics:yoma`
  (gate mode) reports C6/C9/C10 findings. C6 (`argumentFlow.type` inside
  the original 13-value controlled list) is a pre-Phase-2A question the
  corpus was deliberately never made to satisfy - Phase 2A's two-level
  `category`/`type` design (see section 2/Phase 2 above) intentionally
  allows `type` to be any authored value, with `category` (not `type`)
  the controlled, renderer-facing vocabulary. This script's C6 check
  predates that redesign and was never updated to match it; it is
  deliberately not wired into `validate:offline:yoma`
  (`docs/reports/sugya-schema-readiness.md`, updated this session with
  a resolved-status banner). C9/C10 (repeated quiz questions/
  misconceptions across a handful of sugyot) are the same class of
  advisory-not-blocking finding as the 14 semantic findings
  `docs/reports/open-items.md` already documents for Rashi. None of
  these are Phase 4 completion criteria and none were touched.

## 5. Rashi

Recomputed fresh this session:

- **Entry count**: 8,854 `rashiTranslations` (source) / 8,854
  `rashiLines` (runtime), both across all 173 daf.
- **Association count**: 10,061 declared `linkedGemaraLineIds`
  associations (7,634 single-link, 1,200 multi-link, 279 Mishnah, 449
  suffixed-id, 0 sparse, 20 boundary/empty-link) - recomputed live via
  `npm run audit:rashi-association:yoma -- --exhaustive-corpus`; these
  exact counts differ slightly from an older cached figure in
  `docs/reports/open-items.md` (10,047/7,648/1,186/447 at VERSION
  15.357) because the corpus has evolved since that snapshot (Phase 2B
  sourceRefs repairs, etc.) - this document uses the fresh recomputation,
  not the stale cached one, per this campaign's own "recompute, do not
  blindly copy" requirement.
- **Broken / cross-daf**: **0 broken, 0 cross-daf** across all 10,061
  associations.
- **Boundary registry**: 20 authorized entries, 20 boundary entries in
  corpus, all matched, 0 stale, 0 duplicate, 0 unauthorized - ratchet
  20/20 (`validate_rashi_boundary_authorizations.py`).
- **Renderer readiness**: **8/8, READY**, using fresh CI artifact
  evidence for the current merge SHA, not a stale or local-only run:
  - `rashi-browser-shards.yml` dispatched fresh this session via
    `workflow_dispatch` on `main` (commit `d1adec2`) - run id
    `30727598582`, all 8 shards + combine job completed successfully.
  - Combined artifact `rashi-browser-shard-result` (artifact id
    `8826912998`): `ci: true`, `commitSha: d1adec2f8ed...`, 173/173 daf
    covered, `totalEntries: 8854`, `passed: 215`, `failed: 0`.
  - `node scripts/audit-rashi-renderer-readiness.mjs` with that artifact
    placed locally: all 8 checks pass, including "exhaustive browser
    corpus association run (sharded workflow artifact)" - the check
    that a local-only run cannot satisfy by design
    (`check-rashi-browser-shard-artifact.mjs` requires `ci: true`, a
    matching commit SHA, and full 173/173 daf coverage).
  - Semantic-link closure: 173 daf examined, 0 actionable defects, 13
    advisory (non-blocking) findings, matching the standing count in
    `docs/reports/open-items.md`.
- **Renderer**: `linkedGemaraLineIds` is the only association mechanism.
  The legacy vilnaLine-coincidence renderer and the `?rashiAssoc`
  selector were removed at VERSION 15.346; there is no rollback path.
  Confirmed by `npm run test:browser`'s
  `tests/browser/rashi-association.spec.js` suite (16 specs pass, 1
  module-conditional skip).

## 6. Module-agnostic platform

All proven fresh this session, against real committed content, not
just design documents:

- **Descriptor**: `docs/reports/module-descriptor-contract.md`;
  `modules/yoma/module.json` (real) and
  `tests/fixtures/modules/demotractate/module.json` (synthetic) both
  resolve cleanly.
- **Resolvers**: `scripts/module_resolver.py` /
  `shared/module_resolver.js`. `python3 scripts/test_module_resolver.py`
  and `node tests/unit/module-resolver.test.mjs` both pass fresh; both
  reject unknown/malformed/traversal/inconsistent input and never fall
  back to Yoma.
- **Generic capability-aware validator**: `scripts/validate_module_schema.mjs`
  (Phase 3 Step 9A). Proven fresh against both Yoma and `demotractate`
  (section 4, section 7) - schema completeness and capability-vs-content
  consistency (rashi/literal-translation enabled-with-content,
  disabled-with-zero-content, in both directions) for both a real,
  frozen, production module and a synthetic one.
- **Generic scaffold**: `scripts/scaffold_module.py` (Phase 3 Step 9D).
  Proven fresh this session via `npm run test:module-scaffold`: two
  independent throwaway modules scaffolded from an empty directory
  (capabilities disabled, capabilities enabled), each resolving,
  validating, building in isolation, and rendering in a real headless
  browser. `modules/yoma`'s tree confirmed byte-identical before and
  after.
- **Worker pipeline**: `scripts/worker_pipeline.py`. Module-aware
  since Phase 3 Step 3A; re-exercised fresh this session (`python3
  scripts/test_worker_policy.py`, all checks pass including the
  committed-fixture-by-name checks from Phase 3 Step 9B/row 30) and via
  `python3 scripts/worker_pipeline.py verify --full` (8/8 gates pass).
- **Generic docs generation**: `scripts/generate_module_docs.py` (Phase
  3 Step 9C). Proven fresh this session:
  `python3 scripts/generate_module_docs.py --module demotractate
  --search-root tests/fixtures/modules --check` reports fresh; also
  proven generic against real Yoma content via a scratch-only dry run
  in Phase 3 Step 9C (never re-run against Yoma's real docs output this
  session to avoid writing into the repo unnecessarily - the mechanism
  was already proven and is unchanged).
- **Build isolation**: `scripts/build.mjs --module <key> --search-root
  <path> --out <dir>`. Proven fresh via `test:fixture-onboarding` and
  `test:module-scaffold`: isolated builds never touch `dist/`, the real
  `manifest.js`, or `modules/yoma`.
- **Capability dispatch**: `resolveRashiModule()`
  (`shared/module_resolver.js`) rejects a Rashi-disabled module with a
  distinct `CAPABILITY_DISABLED` error (Phase 3 Step 3D); the generic
  validator additionally checks capability-vs-content consistency for
  both rashi and literalTranslation (Phase 3 Step 9A).
- **CI enforcement**: `deploy-pages.yml`'s required `build` job runs
  `test:fixture-onboarding` and `test:module-scaffold` (section 3).

## 7. Synthetic fixture proof

- **Key**: `demotractate`. **Location**: `tests/fixtures/modules/demotractate/`
  (outside `modules/`, never discovered by production module discovery).
- **Non-production status**: `module.json` declares `status:
  "synthetic"`. **Non-publishable status**: `publishable: false`
  (resolver-enforced pairing).
- **Daf/sugya counts**: 3 daf (1a, 1b, 2a), 4 sugyot, 9 argumentFlow
  steps across 8 distinct types, all 4 legal `sourceRefs` shapes
  exercised.
- **Supported semantic shapes**: `capabilities.rashi.enabled=true` (2
  real `rashiTranslations`), `capabilities.literalTranslation.enabled=false`
  (0 `en_lit` fields - both capability states proven correct by the
  generic validator, section 4/6).
- **Onboarding command**: `python3 scripts/scaffold_module.py --key
  <id> --search-root <path> [--rashi enabled|disabled] [--literal
  enabled|disabled]` (proven against two fresh throwaway modules this
  session, section 6).
- **Validation command**: `node scripts/validate_module_schema.mjs
  --module demotractate --search-root tests/fixtures/modules` -
  re-run fresh this session, passes cleanly.
- **Build command**: `node scripts/build.mjs --module demotractate
  --search-root tests/fixtures/modules --out <dir>` - re-run fresh via
  `test:fixture-onboarding`.
- **Browser command**: `node scripts/fixture_onboarding_browser_check.mjs
  <baseUrl> demotractate 1a 2 5 FIXTURE` - re-run fresh, 2 sugyot, 5
  lines, marker present, zero page errors.
- **Docs command**: `python3 scripts/generate_module_docs.py --module
  demotractate --search-root tests/fixtures/modules [--check]` - re-run
  fresh this session, fresh.
- **Isolation proof**: `npm run test:fixture-onboarding` and `npm run
  test:module-scaffold` both hash `modules/yoma`'s entire tree (every
  file path + content) before and after every operation - re-run fresh
  this session, byte-identical every time. `git diff --stat 5c37c33
  d1adec2 -- modules/yoma/` (the Step 8 baseline through the latest
  merge, spanning the entire six-row closure campaign plus Phase 4
  Steps 1-3) is empty.

## 8. Repository reconciliation

- **Status-marker inventory**: `docs/reports/phase4-inventory.md` (+
  `docs/reports/data/phase4-inventory.json`). All 877 tracked files
  swept for every term the governing directive listed. **Zero real
  code-debt markers** (TODO/FIXME/XXX/HACK) in tracked source. 12
  documentation defects found, all fixed in PR #389 (six blocked Phase
  4, six were non-blocking polish).
- **Open-items terminal counts**: `docs/reports/open-items.md`. 1
  genuinely OPEN-ACTIONABLE item remains (Rashi translation-quality
  audit coverage - real, ongoing Yoma content work, explicitly outside
  this platform-closure campaign's scope, not a Phase 4 completion
  criterion, not touched). 0 PAUSED. 0 UNKNOWN-OPERATOR. All Phase 1-3
  work is COMPLETED. Nekudot, mysugya.com/Cloudways, and the 331 string
  sourceRefs remain OUT-OF-SCOPE by permanent decision. Additional
  tractates remain DEFERRED-ROADMAP pending explicit operator
  selection.
- **Open PRs**: 0 (re-checked fresh this session).
- **Open issues**: 0 (re-checked fresh this session).
- **Working tree**: clean (re-checked fresh this session, before this
  PR's own changes).
- **Known roadmap**: additional tractates
  (`docs/reports/next-tractate-roadmap.md`); Rashi translation-quality
  audit coverage completion (`docs/rashi-audit-backlog.md`).
- **Explicit out-of-scope**: nekudot/vowelization audit; the 331
  canonical string sourceRefs (permanent decision, not a gap);
  Cloudways/mysugya.com configuration.
- **Branches**: 64 non-main branches exist, all corresponding to
  already-merged, already-squashed campaign PRs. Not a Phase 4
  completion criterion; not deleted.

## 9. Next-tractate readiness

The platform is proven ready to onboard a real second tractate. Exact
first commands, once an operator selects one:

```bash
# 1. Scaffold (or hand-author) the module descriptor
python3 scripts/scaffold_module.py --key <id> --search-root modules \
  --rashi disabled --literal disabled
# (scaffold_module.py refuses to write into modules/ by default as a
#  safety guard against accidental real-module creation from this
#  command alone - hand-author modules/<id>/module.json directly per
#  docs/reports/module-descriptor-contract.md's schema instead, using
#  the scaffold's throwaway output only as a shape reference)

# 2. Confirm it resolves
python3 scripts/module_resolver.py <id>

# 3. Source acquisition (per docs/tractate-build-process.md's ingestion
#    order and docs/new-tractate-onboarding.md's safety checklist)
cd modules/<id>
python3 scripts/fetch_talmuddev.py       # per-module script, adapted from Yoma's
# ... source_store.js populated verbatim from Sefaria, daftexts generated,
#     Vilna line breaks embedded, enrichment JSON authored per
#     shared/schema_map.js, learning_data.js built

# 4. Validation sequence
node scripts/validate_module_schema.mjs --module <id>
python3 scripts/validate_schema_completeness.py   # per-module, adapted from Yoma's
# ... plus the module's own adapted validate_sefaria.py, validate_en.py,
#     validate_daftext.py, validate_rashi.py (if rashi enabled),
#     validate_literal.py (if literal enabled), order_audit.py

# 5. Worker manifest sequence (docs/new-tractate-onboarding.md sections 5-9)
npm run worker:manifest -- --type docs-tooling --module <id>
npm run worker:preflight -- --manifest .worker-manifest.json
npm run worker:packet -- --manifest .worker-manifest.json
# ... one repair-type, one reconstruction-type, one audit-only manifest,
#     all dry-run green, before any content PR

# 6. Add to manifest.js (separate, narrower, browser-runtime contract -
#    see docs/reports/module-descriptor-contract.md)

# 7. CI: every Yoma gate needs a <id> equivalent wired into package.json
#    and validate:offline:<id>; branch protection already covers any
#    module via the single required "build" check
```

**Publication prohibition until approval**: `scripts/build.mjs` refuses
to build a `publishable: false` module into the default `dist/`;
`deploy-pages.yml` explicitly builds `--module yoma` only. A new
tractate is never deployed by default - promoting it to production
requires an explicit, separate decision to set `publishable: true` and
update the deploy workflow's module selection, exactly mirroring how
Yoma itself is the only module ever selected today.

**No real second tractate was started or selected during this closure
campaign or Phase 4.** `demotractate` remains the only non-Yoma
`module.json` anywhere in the repository, and it lives outside
`modules/` permanently.

## 10. Final gate table

All re-run fresh this session against `main` `d1adec2` (VERSION 15.396)
plus this PR's own documentation-only changes on top, before merge:

| Command | Result | Evidence |
|---|---|---|
| `npm run validate:offline:yoma` (12 gates) | PASS | all gates green, see section 4 |
| `python3 scripts/validate_source_refs.py --strict` | PASS | 0 defects / 1,953 refs |
| `python3 scripts/validate_schema_completeness.py` | PASS | 492/492 sugyot |
| `node scripts/validate_module_schema.mjs --module yoma` | PASS | 173 daf, 492 sugyot, 1953 steps, both capabilities correct |
| `node scripts/validate_module_schema.mjs --module demotractate --search-root tests/fixtures/modules` | PASS | 3 daf, 4 sugyot, both capabilities correct |
| `npm run audit:rashi-association:yoma -- --exhaustive-corpus` | PASS | 0 broken, 0 cross-daf, 10,061 associations |
| `node scripts/audit-rashi-renderer-readiness.mjs` (with fresh CI artifact) | PASS | 8/8 READY |
| `rashi-browser-shards.yml` workflow dispatch | SUCCESS | run id `30727598582`, artifact id `8826912998`, 173/173 daf, 215 passed, 0 failed |
| `npm test` | PASS | 27/27 |
| `python3 scripts/test_worker_policy.py` | PASS | all checks including committed-fixture row-30 checks |
| `python3 scripts/test_module_resolver.py` | PASS | all checks |
| `npm run test:browser` | PASS | 16 passed, 1 skipped |
| `npm run test:fixture-onboarding` | PASS | full resolver+build+render proof |
| `npm run test:module-scaffold` | PASS | both capability states, from-empty |
| `npm run build` / `npm run check:deploy-html` | PASS | no dev-loader tokens |
| `python3 scripts/worker_pipeline.py verify --full` | PASS | 8/8 gates |
| Open PRs | 0 | re-checked fresh |
| Open issues | 0 | re-checked fresh |
| Working tree | clean | re-checked fresh, before this PR |
| `git diff --stat 5c37c33 d1adec2 -- modules/yoma/` | empty | Yoma unchanged across the entire six-PR closure campaign + Phase 4 Steps 1-3 |
| Live bundle check | `app-15.396.js` | matches merge SHA `d1adec2` at time of this document's generation; re-verify after this PR's own merge for VERSION 15.397 |

---

## Phase 2 completion evidence (historical, preserved from the original Phase 2 snapshot this file once was)

Phase 2 (`docs/platform-closure-plan.md`) covers two independent
contracts: the `argumentFlow` category/type schema (2A) and the
`sourceRefs` canonical schema (2B). Both are complete; current, fresh
counts are in section 4 above. The record below is preserved as
historical evidence of how Phase 2 was originally closed (VERSION
15.376-15.377, PRs #368-#369) and is superseded by section 4 wherever
the two disagree in exact figures (the corpus has evolved since; the
contracts have not changed).

### 2A: argumentFlow

- 492/492 sugyot, 1,953 argumentFlow steps.
- 119 distinct `type` values observed (13 original canonical + 106
  more), all mapped to a `category` via the versioned registry
  `shared/argument_step_taxonomy.json` - never stored per step, so
  100% category coverage was reached without editing any content file.
- `validate_argument_taxonomy.py`: 100% coverage, 0 malformed values,
  app.jsx/registry byte-parity confirmed.
- See `docs/reports/argumentflow-category-decision.md` for the full
  design record.

### 2B: sourceRefs

- **1,953 total refs**, 0 defects of any class, for the first time in
  this campaign:
  - 1,620 `OK` (same-daf object refs) - key-shapes: 1,199
    `lineId + sourceType + vilnaLine`, 421
    `lineId + note + sourceType + vilnaLine`.
  - 331 `STRING_RESOLVABLE` (legacy string form, permanently retained
    by decision - `docs/reports/sourcerefs-contract-decision.md`).
  - 2 `OK_CROSSDAF` (explicit cross-daf object shape -
    `docs/reports/sourcerefs-crossdaf-schema-decision.md`).
- `sourceType` values: `gemara` (1,619), `mishnah` (3). 0 missing, 0
  invented (every value independently confirmed from the target
  segment's own real content, never derived from a line's `kind`).
- Of the original 550 defective refs identified by
  `docs/reports/source-refs-normalization-plan.md`: 412 mechanical
  repairs, 105 of 138 judgment-required repairs by textual evidence,
  and all 33 of the subsequently classified residue
  (`docs/reports/sourcerefs-blocker-classifications.json`) now
  resolved - 2 `QUALIFIED_CROSS_DAF` migrated, 29
  `ABSENT_OR_UNANCHORED` removed, and the final 2 `TIED_CANDIDATES`
  (`yoma-044b-l01`, `yoma-063a-l03a`) repaired in a final, tightly
  scoped re-adjudication (PRs #368-#369) using evidence the prior
  five-way classification pass had not fully exploited.
- No Hebrew/English source text, Rashi data, argumentFlow
  text/type/category, speaker field, sugya boundary, renderer, or
  validator was changed to reach this state.

GitHub Pages deployment at Phase 2 closure: green for the PR #369 merge
commit (`3c81ce1`, workflow run `30598090265`, conclusion `success`).
