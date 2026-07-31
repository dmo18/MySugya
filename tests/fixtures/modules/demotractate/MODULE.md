# demotractate - synthetic Phase 3 replication-proof fixture

**This is not a real tractate.** Every Hebrew/English source line is an
explicit bracketed placeholder (`[FIXTURE-HE-PLACEHOLDER]`,
`[FIXTURE-EN-PLACEHOLDER]`, `[FIXTURE]`, `[FIXTURE-RASHI-*-PLACEHOLDER]`).
The subject matter is a fictional "Widget Certification Board," chosen
specifically so nothing here could be mistaken for genuine Talmud content.

## Purpose

Phase 3 of `docs/platform-closure-plan.md` requires proving the platform
can onboard, generate, validate, build, browser-test, and document a
second tractate without hidden Yoma assumptions - without selecting or
ingesting a real second tractate. This module is that proof's fixture.

## Why this lives outside `modules/`

Per the governing plan, this fixture must never be discoverable by the
`modules/*/module.json` glob that production code (the build, the
deployment workflow) uses - not by convention, but by construction. It
lives at `tests/fixtures/modules/demotractate/`, a directory `list_modules()`
and `resolve_module()` never search by default. Both resolvers
(`scripts/module_resolver.py`, `shared/module_resolver.js`) accept an
explicit `search_root` override for exactly this case; production call
sites never pass one. Verified directly: `list_modules()` with no override
returns only `["yoma"]`, and `resolve_module("demotractate")` with no
override fails `UNKNOWN_MODULE` before touching anything.

## A logical-vs-physical path note (flagged for Step 6, not resolved here)

`module.json`'s `paths.root` is `"modules/demotractate"` - not
`"tests/fixtures/modules/demotractate"` - because `validate_descriptor()`
requires `paths.root == f"modules/{key}"` unconditionally (a Step 2
design decision, confirmed in `docs/reports/module-descriptor-contract.md`'s
"Fixture discovery" section, which anticipated this fixture living outside
`modules/` while keeping `paths.*` as repo-root-relative logical paths).
Every `paths.*` field below follows the same logical `modules/demotractate/...`
shape, matching Yoma's own descriptor's convention.

This means a caller that only does `repoRoot / descriptor.paths.root`
(the pattern `worker_pipeline.py`'s `set_active_module()` uses today for
Yoma, where `search_root` defaults to `modules/` and `paths.root` happens
to agree with it) would resolve to the wrong, nonexistent physical
location for this fixture. This module's own generator
(`scripts/build_learning_data.py`) sidesteps the question entirely by
using `Path(__file__).parent`-relative paths, exactly like Yoma's own
per-module scripts - it never goes through either resolver. Making the
*shared, generic* tooling (the kind Step 3A-4B migrated) correctly derive
a fixture's physical location from `search_root + key` rather than
`repoRoot + paths.root` is real design work that Step 6 ("prove
onboarding end-to-end via the generic tooling") must do, not something
this content-only step should paper over. Recorded here explicitly so it
is not lost.

## Capability choices (documented, not defaulted)

- **`capabilities.rashi.enabled: true`** - exercised with 2 real
  `rashiTranslations` entries (daf 1a, vilna lines 1 and 3), each with a
  populated `linkedGemaraLineIds`. `scripts/allowlists/` carries the four
  ratchet files the Yoma Rashi tooling expects (content, links,
  repetition, boundary authorizations), all empty - a clean, zero-debt
  state if a generic tool is ever pointed at this fixture.
- **`capabilities.literalTranslation.enabled: false`** - deliberately the
  disabled path, so the fixture also proves a module can validly opt out
  of a capability Yoma has (no `en_lit` field appears anywhere in this
  fixture's data).
- **`capabilities.sourceAcquisition.strategy: "local-fixture"`** - the
  strategy added in Step 3B specifically for synthetic modules;
  `fixtureInputDir` points at `assets/fixture_source/`, which contains
  the tiny, committed, never-fetched raw source JSON this module's
  generator reads.

## Content inventory

3 daf (`1a`, `1b`, `2a`), 4 sugyot (2 on `1a`, 1 each on `1b`/`2a`), 1
chapter (`PERAKIM` has one entry spanning the whole range).

`argumentFlow.type` values used: `case`, `question`, `proof`,
`distinction`, `rejection`, `resolution`, `takeaway`, `answer` - 8
distinct values already registered in `shared/argument_step_taxonomy.json`
(chosen deliberately so this step needs zero changes to that shared,
cross-tractate registry), spanning 8 distinct categories.

`sourceRefs` shapes, all three legal current shapes exercised (the
legacy Sefaria-string shape is Yoma-specific migration debt and is
correctly never used here):

- same-daf object - most steps (e.g. `demo-001a-s01`/`step-01`).
- multi-ref (2 entries, 2 distinct lines) - `demo-001a-s01`/`step-03`.
- cross-daf object (`refType: "crossDaf"`) - `demo-001b-s01`/`step-02`,
  referencing back to `demo-001a-l01` on daf `1a`.
- intentionally omitted (legal - the field is optional) -
  `demo-001a-s01`/`step-02`.

## Regenerating

```
cd tests/fixtures/modules/demotractate
python3 scripts/build_learning_data.py
```

Reads `assets/fixture_source/*.source.json` and
`assets/learning/demotractate/*.learning.json`; writes `source_store.js`,
`learning_data.js`, and `coverage.json`. Do not hand-edit those three
generated files.

## What this step does not do

Not wired into `manifest.js`, not built by `scripts/build.mjs`'s default
(unqualified) invocation, not browser-tested, not validated by any
generic gate yet. Proving those end-to-end via the platform's actual
generic tooling (not a fixture-only parallel pipeline) is Phase 3 Step 6.
