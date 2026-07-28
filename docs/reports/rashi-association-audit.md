# Rashi linkedGemaraLineIds renderer and audit

## Production cutover (VERSION 15.338)

The linked renderer is now the **production default**. Renderer selection
lives in `rashiRendererFromUrl` (`shared/rashi_association.js`), is read
fresh from the URL on every call, and is never persisted to localStorage or
any other storage:

| URL | Renderer |
|---|---|
| no `rashiAssoc` parameter | linked (production default) |
| `?rashiAssoc=linked` | linked (still accepted, no longer required) |
| `?rashiAssoc=legacy` | legacy (temporary rollback override) |
| unknown or malformed value | linked |

The legacy vilnaLine-coincidence renderer has **not** been deleted; it
remains intact in `app.jsx` behind `?rashiAssoc=legacy`. In linked mode
`linkedGemaraLineIds` is authoritative: no vilnaLine fallback, multi-linked
comments render beneath every declared target, several comments may render
beneath one target, Mishnah and suffixed ids stay exact, and the 20
authorized empty-link boundary entries render nowhere. No Rashi content,
association data, or the boundary registry changed in the cutover.

The closure evidence below (8/8 readiness at VERSION 15.337) is what
authorized this cutover and remains accurate.

## Closure status (VERSION 15.337)

Everything below "Background" is the historical record of the PR that
introduced the linked renderer and its data auditor (VERSION 15.157) -
**superseded** by subsequent work and preserved here as history, not
current state. For the live numbers, re-run the commands shown; this
section is a snapshot as of VERSION 15.337.

- 8,854 `rashiTranslations` entries across all 173 daf; 10,047 declared
  associations (7,648 single-link, 1,186 multi-link, 279 Mishnah, 447
  suffixed-id, 0 sparse, 20 boundary); **0 broken, 0 cross-daf** -
  `audit_rashi_association.py --exhaustive-corpus` is fully green (the
  43a/43b/44b bug this report documents below, and the 43a/43b/44b/7a/9b
  content debt referenced further down, are all resolved: 7a via PR #326,
  9b via PR #327).
- The boundary-authorization registry
  (`modules/yoma/scripts/allowlists/rashi_boundary_authorizations.json`,
  validated by `validate_rashi_boundary_authorizations.py`) now exists and
  is fully populated: all 20 boundary entries (4b L61; 61a L46-64)
  authorized, ratchet 20/20, 0 stale/duplicate/unauthorized.
- The readiness gate's semantic-link check now consumes
  `audit_rashi_semantic.py --profile --json`'s per-daf `classification`/
  `recommendedTaskType` directly: 0 daf SHIFTED or FABRICATION-SUSPECT, 0
  daf with a recommended task. 14 advisory-only findings remain on
  otherwise-ALIGNED/INSUFFICIENT-ANCHORS daf and are never suppressed -
  see the readiness gate's own output for the full list with exact
  offsets, including the 2a and 4b findings this report's Limitations
  section originally flagged as out of scope.
- A sharded browser-association workflow
  (`.github/workflows/rashi-browser-shards.yml`) now exists, splitting all
  173 daf across 8 CI matrix jobs and combining their results into one
  artifact stamped with commit SHA and CI provenance
  (`scripts/combine-rashi-browser-shards.mjs`,
  `scripts/check-rashi-browser-shard-artifact.mjs`). It rejects missing,
  partial, stale/wrong-commit, local-only, or failed evidence outright. It
  first ran against commit `d1e4715` as workflow run `30399334278`,
  producing artifact `rashi-browser-shard-result` (id `8704117259`): 8
  shards, 173/173 daf, 8,854 entries, 183 passed, 0 failed.
- Renderer readiness: **8/8** (`npm run audit:rashi-renderer-readiness:yoma`)
  once that artifact was supplied. This is the evidence that authorized the
  VERSION 15.338 production cutover recorded at the top of this document.

---

Status as of VERSION 15.157 (historical). This document distinguishes what
is implemented and locally verified from what remains open. Nothing here
should be read as a corpus-closure claim: production still renders Rashi
via the legacy vilnaLine-coincidence path by default, and the
referential-integrity audit currently fails on three known-bad daf (see
below).

## Background

The Gemara/Mishnah knowledge layer (`learning_data.js`) stores an explicit
`linkedGemaraLineIds` array on every `rashiLines[]` entry - the authoritative
declaration of which Gemara/Mishnah line(s) that Rashi comment belongs to.
The production renderer (`app.jsx`, legacy path) has never read this field.
Instead it matches a Rashi entry to a Gemara line by numeric coincidence:
`rashi.vilnaLine === line.vilna_line`. That happens to work when a daf's
Rashi entries line up 1:1 with Gemara lines, which is common, but it is not
what `linkedGemaraLineIds` was built to express, and it silently drops
multi-link associations (a Rashi comment declared against two Gemara lines
renders under at most one, by accident of which vilnaLine matched first).

## What this PR implements

### Renderer (app.jsx + shared/rashi_association.js)

- `shared/rashi_association.js` is a plain script (matching the existing
  `manifest.js` convention: loaded unbundled via its own `<script>` tag in
  both `index.html` and the production build, never passed through
  esbuild). It exports two pure functions:
  - `groupRashiByLinkedId(rashiLines)` - builds `Map<gemaraLineId,
    rashiEntry[]>` strictly from declared `linkedGemaraLineIds`. An entry
    with no declared targets is never attached anywhere (no vilnaLine
    fallback).
  - `rashiRendererFromUrl()` - reads the test-only `?rashiAssoc=linked`
    query parameter fresh on every call. Never written to localStorage;
    absent or any other value means `"legacy"`.
- `app.jsx`'s `Sugya` component now branches on `rashiRenderer`: `"legacy"`
  (default, unchanged rendering) or `"linked"` (test/audit only). The linked
  path's toggle key is `line.id` (not `vilna_line`), and a rendered entry
  carries `data-rashi-id`, `data-rashi-daf`, `data-rashi-vilna-line`, and
  `data-rashi-linked-line-id` (the line currently rendering it, distinct
  from its full declared target list in `data-rashi-targets`).
- `Line` carries `data-gemara-line-id={line.id}` in both paths, giving
  tests a stable selector that doesn't depend on visual position.
- **Why a separate shared file instead of defining the functions directly
  in `app.jsx`:** the whole point is that the unit test must import the
  exact production function, not a copy. An earlier version of this file
  defined `module.exports = {...}` directly and was bundled via
  `scripts/build-entry.jsx`; esbuild detected that CommonJS pattern and
  wrapped the file in its own module scope, which silently broke the
  production bundle (`groupRashiByLinkedId is not defined` at runtime,
  caught by `tests/browser/rashi-association.spec.js`'s legacy-path check
  before this PR was pushed). The fix was to stop bundling the file at all
  and load it unbundled, exactly like `manifest.js`.

### Data auditor (modules/yoma/scripts/audit_rashi_association.py)

Rewritten on top of `_js_parser.py`'s structural parser (the same one
`validate_literal.py` / `validate_en.py` / `order_audit.py` depend on) rather
than regex-scanning whole daf blocks. Two parser additions were made to
`_js_parser.py` for this (`extract_string_array_field`, `parse_rashi_fields`
/ `parse_rashi_lines_array`), each covered in `test_js_parser.py`.

Validity is **exact id equality only** - no `startswith`/prefix tolerance
anywhere. A target is valid only if it is the literal `id` of an object
inside that daf's own `lines: [...]` array. Both Gemara and Mishnah lines
live in that same array (distinguished only by `kind: "gemara"` /
`kind: "mishna"`); neither gets special-cased.

Modes: `--target DAF` (default `2a`), `--range-from`/`--range-to` (exact
inclusive range), `--corpus` (honest sample: first/middle/last Rashi entry
per daf plus every multi-link/Mishnah/suffixed/sparse/boundary entry in the
whole corpus), `--exhaustive-corpus` (every entry, every daf). Daf scope is
derived by parsing the real `"<daf>": { ... }` blocks that exist in
`learning_data.js` - never a hardcoded numeric range - so the tool cannot
manufacture a daf that isn't actually there (the real corpus ends at `88a`;
there is no `88b`).

`--json` emits the exact plan (including real `he`/`en`/`kind` for both the
Rashi entry and its resolved target) that the browser spec asserts against.

**A pre-existing bug this rewrite catches** (silently missed by
`validate_rashi_links.py`'s existing whole-block regex, because that regex
also matches `argumentFlow[].id` fields that happen to reuse the
`yoma-NNNa-lNN` id shape): on `43a`/`43b`/`44b`, three Rashi entries declare
`linkedGemaraLineIds: ["yoma-043a-l01"]` (or the `43b`/`44b` equivalent), but
the real Gemara line objects on those daf are suffixed - only
`yoma-043a-l01a` and `yoma-043a-l01b` exist, never a bare `l01`. Confirmed
with `python3 modules/yoma/scripts/audit_rashi_association.py --range-from
43a --range-to 44b`:

```
Counts: daf=4 rashi_entries=244 declared_associations=243 single_link=243
multi_link=0 mishnah=6 suffixed=1 sparse=0 boundary=1 broken=8
8 error(s) found.
```

This is scaffold/content debt already tracked in
`docs/rashi-audit-backlog.md`'s remediation queue; fixing it is out of scope
for this PR (see "Universal rules" in `CLAUDE.md`: no scaffold content
remediation bundled with tooling work).

### Test coverage

**`modules/yoma/scripts/test_rashi_association_audit.py`** (24 tests, all
against the real exported functions - `analyze_daf`, `select_target_daf`,
`sample_entries_for_daf`, `summarize`, `daf_pad` - with synthetic in-memory
fixtures, not the generated file): nonexistent target, the exact 43a-style
bug (bare id accepted only when it is the real id, never collapsed into or
out of a suffixed sibling), cross-daf target, arbitrary nonexistent
"Mishnah-shaped" target (kind is read from the resolved line object, never
guessed from the id string), empty link (boundary, non-fatal), multi-link
completeness, sparse-gap detection, every `select_target_daf` mode including
rejection of a request for a daf that was never parsed out of the file.

**`tests/unit/rashi-association.test.mjs`** (12 tests, importing
`groupRashiByLinkedId` from `shared/rashi_association.js` via
`createRequire` - never a re-implementation): single-link, multi-link (both
targets), many-to-one, empty-link never attached, vilnaLine-coincidence
negative control, suffixed-id distinctness (a bare id is never treated as
equivalent to its suffixed sibling), Mishnah/Gemara id-agnosticism, no
cross-entry bleed (an unrelated target never picks up another entry), no
Hebrew/English cross-pairing, null/undefined safety.

**`tests/browser/rashi-association.spec.js`** (Playwright, valid syntax
throughout - no Python string literals, no invented `shouldFail` fixture, no
`Locator.scroll()`, no truthiness assertions on Locator objects, no
`test.fail()`/manual-throw negative tests): asserts, for every declared
association in scope, exact Rashi id, exact Hebrew text (`toHaveText`),
exact English text when non-empty, exact current target line id
(`data-rashi-linked-line-id`), the complete declared target set
(`data-rashi-targets`), no rendering under an undeclared target, no
duplicate rendering under one target, and occurrence under every declared
target for multi-link entries. A second test confirms boundary (empty-link)
entries never render anywhere on the daf. A third confirms the legacy path
(no `?rashiAssoc` param) is unaffected.

The plan the spec asserts against always comes from
`audit_rashi_association.py --json`, read either from a file
(`YOMA_ASSOC_PLAN_PATH`, set by `scripts/run-rashi-association.mjs` for
range/corpus runs) or, when that env var is absent, generated on the spot in
`--target` mode (default daf `2a`, chosen because it has real multi-link and
Mishnah coverage - 9 multi-link and 13 Mishnah entries as of this VERSION).
This means plain `npx playwright test` / `npm run test:browser` / `npm test`
exercises real multi-link/Mishnah coverage with zero setup, and a
content-only PR never has to touch a test file to get that coverage.

Negative-failure-mode coverage is split across the layer actually
responsible for each mode, not duplicated into the browser spec:

| Failure mode | Covered by |
|---|---|
| nonexistent target | `test_rashi_association_audit.py` |
| bare id vs. suffixed sibling (both directions) | `test_rashi_association_audit.py` |
| cross-daf target | `test_rashi_association_audit.py` |
| arbitrary nonexistent Mishnah-shaped target | `test_rashi_association_audit.py` |
| empty link (boundary, non-fatal) | `test_rashi_association_audit.py` |
| omitted multi-link target | `rashi-association.test.mjs` (grouping) + browser spec (rendering) |
| unrelated extra target | `rashi-association.test.mjs` |
| Hebrew/English cross-pairing | `rashi-association.test.mjs` |
| accidental vilnaLine fallback | `rashi-association.test.mjs` |
| valid-but-semantically-wrong target | **not covered** - see Limitations |

### Readiness gate (scripts/audit-rashi-renderer-readiness.mjs)

Checks the repository's real ratchet files - there is no separate
`scaffold_debt.json`; the content/scaffold debt ratchet **is**
`modules/yoma/scripts/allowlists/rashi_content_allowlist.json`
(`entries[]` + `count_mismatches[]`):

1. `rashi_content_allowlist.json` entries + count_mismatches == 0
2. `rashi_links_allowlist.json` entries == 0
3. `rashi_repetition_baseline.json` entries == 0
4. `check_generated_freshness.py` passes (run as a real subprocess)
5. `audit_rashi_association.py --exhaustive-corpus` reports zero broken/
   cross-daf associations
6. every boundary (empty-link) entry has explicit authorization - **there is
   no authorization registry for this in the repository today**, so this
   condition is reported as failing whenever any boundary entries exist. It
   cannot report passing without either that registry being built and
   populated, or the boundary count reaching zero through real linking work.
7. `audit_rashi_semantic.py`'s "Totals:" summary (shift candidates /
   missing-anchor flags / generic flags) is zero - the closest existing real
   proxy for semantic-link closure; there is no dedicated closure file.
8. an exhaustive browser corpus run - **never auto-verified**. Running the
   full browser spec against every daf in one process is reserved for a
   dedicated closure pass or a sharded CI workflow; this check always
   reports "not automatically checked" and never claims a manual step that
   didn't happen.

Real output at the time this report was written (VERSION 15.157; superseded
- see the sections at the top of this document for the VERSION 15.337
closure numbers, now 8/8, and the VERSION 15.338 production cutover):

```
3/8 checks pass.
NOT READY
```

Passing: content allowlist (emptied by remediation work landed on `main`
since this PR branched), links allowlist (already emptied at VERSION
15.76), generated freshness. Failing: repetition baseline (2 entries),
referential-integrity audit (8 broken - the 43a/43b/44b bug above),
boundary authorization (2,174 unlinked entries with no registry), semantic
proxy (44/130/9 flags), and the always-manual exhaustive browser check.
**This is the correct, honest state** - none of this remediation is in
scope for this PR. These exact counts will keep moving as unrelated
remediation PRs land; re-run the command for the current numbers rather
than trusting this snapshot.

## Limitations

- **Referential-integrity auditing cannot catch semantic mismatches.** If a
  Rashi comment declares `linkedGemaraLineIds: ["yoma-002a-l05"]` and `l05`
  is a real line but the *wrong* one for that comment, this auditor will not
  flag it - the id is syntactically valid. Only content review (or a future
  semantic-alignment tool) can catch that class of error.
- **`sparse` is currently a vacuous category.** It is defined as a gap in a
  Rashi entry's own `vilnaLine` sequence within a daf, but
  `build_learning_data.py`'s `load_rashi_lines()` assigns `vilnaLine` as
  `enumerate(rashi_he) + 1` - strictly sequential by construction - so this
  category can never be nonzero under the current generation pipeline. It
  is kept (rather than removed) because the classification is well-defined
  and inexpensive, and because a future change to that generator could make
  it meaningful; `test_rashi_association_audit.py` tests it directly with a
  synthetic fixture that does contain a gap, so the logic itself is proven
  correct even though it never fires against real data today.
- **Exhaustive-corpus browser verification has not been run** as part of
  this PR (only `--target` and `--range` modes were exercised locally,
  documented below). It is deliberately excluded from `npm test`/
  `test:browser` (thousands of navigations) and is reserved for a future
  closure pass or sharded workflow.

## What was actually run locally for this PR

```
node --check tests/browser/rashi-association.spec.js        # OK
npm run test:rashi-association-unit                           # 12/12 pass
npm run test:rashi-association-audit:yoma                    # 24/24 pass
python3 modules/yoma/scripts/test_js_parser.py                # 57/57 pass (8 new)
npm run test:rashi-association:yoma -- --target 2a            # audit + browser: pass
npm run test:rashi-association:yoma -- --range 2a 3b          # audit + browser: pass
npm run audit:rashi-association:yoma -- --target 11a          # pass, 0 errors
npm run audit:rashi-association:yoma -- --exhaustive-corpus    # FAILS: 8 errors (43a/43b/44b, known, tracked)
npm run audit:rashi-renderer-readiness:yoma                    # 2/8, NOT READY (honest, expected)
npx playwright test                                            # full suite incl. this spec: all pass
```

`npm run audit:rashi-association:yoma -- --exhaustive-corpus` is expected to
exit nonzero until 43a/43b/44b are repaired; that is correct behavior, not a
bug in this PR.

## Rollout status

- Production renders Rashi via the **legacy** vilnaLine-coincidence path,
  unchanged by this PR.
- The **linked** path is reachable only via `?rashiAssoc=linked`, used
  exclusively by tests and the audit tooling in this PR. It is not linked
  from any UI control and is never written to localStorage.
- No claim is made here about corpus-wide closure, CI success on any
  particular commit, or a timeline for cutover. The readiness gate exists
  precisely so that claim can never be made without evidence.
