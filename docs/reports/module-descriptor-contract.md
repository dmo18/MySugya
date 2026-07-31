# Module descriptor contract

**Status: canonical, Phase 3 Step 2 of `docs/platform-closure-plan.md`.**
Defines the one schema every module (Yoma, any future real tractate, and
the Phase 3 synthetic fixture) must satisfy, and the resolver contract
that reads it. This is the smallest architecture consistent with the
repository: one JSON descriptor per module, read by both a Python
resolver (for `scripts/*.py` and `worker_pipeline.py`, migrated onto it
starting Step 3A) and a JS resolver (for `build.mjs` and future `.mjs`
tools, migrated onto it starting Step 4).

This PR defines the descriptor and resolver only. Nothing that currently
reads `modules/yoma` paths directly is migrated onto it yet - that is
Steps 3A-4, tracked in `docs/reports/phase3-inventory.md`'s PR sequence.
`manifest.js` (the browser-runtime registry `app.jsx` reads via
`?module=`) is deliberately untouched: it is a different, narrower
contract for a different consumer (the browser bundle), and conflating
it with this build/pipeline-facing descriptor would leak tooling-only
fields into client JavaScript. The two may share a `key`/`id` value for
the same module, but one is not derived from the other in this PR.

## File location

One descriptor per module, colocated with the module it describes:

    modules/<key>/module.json

Discovered by globbing `modules/*/module.json`, never by a registry file
listing module keys separately - the descriptor's own presence at that
path *is* the registration. This mirrors the existing `MODULE.md`
convention (`modules/yoma/MODULE.md`) and avoids a second place that can
drift out of sync with which module directories actually exist.

The Phase 3 synthetic fixture (Step 5) does **not** live under `modules/`
and is therefore never discovered by this glob - see "Fixture discovery"
below.

## Schema

```json
{
  "key": "yoma",
  "displayNameEn": "Yoma",
  "displayNameHe": "יוֹמאָ",
  "sefariaTractate": "Yoma",
  "status": "production",
  "publishable": true,
  "seder": "Moed",
  "dafRange": { "first": "2a", "last": "88a" },
  "totalDaf": 173,
  "paths": {
    "root": "modules/yoma",
    "scriptsRoot": "modules/yoma/scripts",
    "sourceAssetsRoot": "modules/yoma/assets",
    "generatedAssetsRoot": "modules/yoma/assets",
    "sourceStore": "modules/yoma/source_store.js",
    "learningDataDir": "modules/yoma/assets/learning/yoma",
    "learningDataFile": "modules/yoma/learning_data.js",
    "coverageFile": "modules/yoma/coverage.json",
    "chapterMetadataLocation": "embedded in learningDataFile (PERAKIM constant)"
  },
  "schemaMapRef": "shared/schema_map.js",
  "capabilities": {
    "rashi": { "enabled": true, "allowlistsRoot": "modules/yoma/scripts/allowlists" },
    "literalTranslation": { "enabled": true, "assetsDir": "modules/yoma/assets/literal_en" }
  },
  "browserTest": { "defaultTargetDaf": "2a" },
  "docsOutput": { "auditBacklogDoc": "docs/rashi-audit-backlog.md" },
  "buildRuntime": { "dataScript": "modules/yoma/learning_data.js" }
}
```

### Field reference

| field | required | meaning |
|---|---|---|
| `key` | yes | Stable module identifier. Also the machine-safe slug: must match `^[a-z][a-z0-9_-]*$`. One field satisfies both "stable key" and "slug" - a module never needs two different spellings of its own id. |
| `displayNameEn` | yes | English display name. |
| `displayNameHe` | no | Hebrew display name; `null` when not yet established (never fabricated - see `CLAUDE.md`'s prohibition on inventing Hebrew). |
| `sefariaTractate` | no | The Sefaria API tractate name used for source acquisition. `null` for a `status: "synthetic"` module, which has no real source system. |
| `status` | yes | `"production"` or `"synthetic"`. Drives the publishable/fixture distinction; see below. |
| `publishable` | yes | Boolean. Must be `false` whenever `status` is `"synthetic"` - a synthetic module can never be publishable, and the resolver rejects a descriptor that claims otherwise (`FEATURE_INCONSISTENCY`). A `"production"` module may still set this `false` before its content is ready; the deploy step (Step 4D) will only ever select `publishable: true` modules. |
| `seder` | no | Descriptive metadata; `null` allowed. |
| `dafRange` | yes | `{first, last}` amud identifiers, or `null` for a module whose page identifiers are not daf-shaped (kept as an explicit escape hatch; not exercised by Yoma or the Step 5 fixture, which both use daf-shaped ids). |
| `totalDaf` | yes | Integer count matching the module's own page inventory. |
| `paths.root` | yes | Module root, relative to the repository root. Must equal `modules/<key>` for any module discovered via the `modules/*/module.json` glob (enforced - a descriptor whose `paths.root` disagrees with its own directory is `MALFORMED_DESCRIPTOR`, catching a copy-paste error). |
| `paths.scriptsRoot` | yes | Per-module scripts directory. |
| `paths.sourceAssetsRoot` | yes | Root for source-derived assets (talmud.dev cache, daftexts, raw fetched text). |
| `paths.generatedAssetsRoot` | yes | Root for generated assets (enrichment JSON, coverage). May equal `sourceAssetsRoot` (Yoma's does; both are `modules/yoma/assets`). |
| `paths.sourceStore` | yes | The module's `source_store.js` equivalent. |
| `paths.learningDataDir` | yes | Directory holding one `<daf>.learning.json` per page. |
| `paths.learningDataFile` | yes | The generated runtime data file (`learning_data.js` equivalent). |
| `paths.coverageFile` | yes | The generated coverage summary. |
| `paths.chapterMetadataLocation` | no | Free-text pointer to where chapter/perek metadata lives, since it is not always its own file (Yoma embeds `PERAKIM` inside `learningDataFile`). Documented, not schema-validated beyond being present as a string when non-null. |
| `schemaMapRef` | yes | Path to the shared enrichment schema this module's learning JSON conforms to. Every module today points at the same `shared/schema_map.js`; the field exists so a future module-specific schema extension has somewhere to be declared without a resolver change. |
| `capabilities.rashi.enabled` | yes | Boolean. When `true`, `capabilities.rashi.allowlistsRoot` is required (`FEATURE_INCONSISTENCY` if missing). When `false`, the field must be absent or `null` - a disabled feature declaring configuration for itself is also `FEATURE_INCONSISTENCY`, since it signals confusion about which is authoritative. |
| `capabilities.literalTranslation.enabled` | yes | Same enabled/config-required-together rule, with `assetsDir`. |
| `browserTest.defaultTargetDaf` | no | Default daf/page the module's browser smoke test targets. |
| `docsOutput.auditBacklogDoc` | no | Where this module's generated audit backlog doc lives. |
| `buildRuntime.dataScript` | yes | The path `app.jsx`/`build.mjs` load at runtime - must equal `paths.learningDataFile` (checked; disagreement is `FEATURE_INCONSISTENCY`, since these naming the same file twice with different values is exactly the kind of drift a single source of truth is supposed to prevent). |

## Resolver contract

Python: `scripts/module_resolver.py`, function `resolve_module(key, repo_root=None) -> ModuleDescriptor`.
JS: `shared/module_resolver.js`, function `resolveModule(key, repoRoot)` (CommonJS-exported, browser-harmless like the rest of `shared/`).

Both implementations validate the same rules, independently (no code
sharing across languages), so a Python-side bug and a JS-side bug are
not the same bug:

1. **Accept an explicit module key.** No implementation-side default.
   Every caller must pass one; there is no implicit "yoma" anywhere in
   the resolver itself. (Callers such as npm `:yoma`-suffixed aliases
   still hardcode `--module yoma` explicitly at the call site - that is
   a convenience alias calling the generic interface explicitly, not an
   implicit default inside the generic interface. Distinguishing these
   two is the whole point of this contract.)
2. **Reject path traversal in the key itself** before any path is
   touched: the key must match `^[a-z][a-z0-9_-]*$`; anything containing
   `/`, `..`, backslashes, or characters outside that pattern is
   `INVALID_KEY`, rejected before any filesystem access.
3. **Resolve only a registered, valid module**: `modules/<key>/module.json`
   must exist. Missing file is `UNKNOWN_MODULE`. Present but not valid
   JSON, or valid JSON that is not an object, is `MALFORMED_DESCRIPTOR`.
4. **Reject missing required fields** individually named in the field
   reference table above - `MISSING_FIELD: <field path>`.
5. **Reject inconsistent feature declarations** - the specific checks in
   the field reference table (`paths.root` vs. directory, `synthetic`
   vs. `publishable`, capability `enabled` vs. required companion config,
   `buildRuntime.dataScript` vs. `paths.learningDataFile`) -
   `FEATURE_INCONSISTENCY: <reason>`.
6. **Return canonical, repository-relative paths** for everything under
   `paths` (already relative in the descriptor; the resolver's contract
   is to keep them relative and never silently rebase them to an
   absolute path a caller didn't ask for - callers that need absolute
   paths join against their own known repo root).
7. **Distinguish production from synthetic fixtures** via `status` and
   `publishable`, exposed on the returned descriptor unchanged.
8. **Never silently replace an invalid requested module with Yoma.** An
   error is raised (Python: `ModuleResolutionError` with a `.code`
   attribute from the list above; JS: an `Error` with a `.code`
   property) - it is the caller's responsibility to handle that error,
   not the resolver's to guess a fallback.

### Fixture discovery

The Step 5 synthetic fixture lives outside `modules/` (per the governing
plan: "a dedicated fixture tree such as `tests/fixtures/modules/<fixture-key>`",
excluded from normal runtime discovery and from GitHub Pages). Both
resolvers therefore accept an optional second parameter - a search root
- defaulting to `modules/` but overridable by test/fixture callers to
`tests/fixtures/modules/` (or wherever Step 5 ultimately places it).
Production code paths (the build, the deployment workflow, and any
`:yoma`-suffixed alias) never pass that override, so a fixture can never
be resolved through a production call site by construction, not by
convention alone.

## What this PR does not do

- Does not touch `worker_pipeline.py`, `scripts/worker_task_types.json`,
  `build.mjs`, `app.jsx`, or any of the other 8 blockers from
  `docs/reports/phase3-inventory.md` - those are migrated onto this
  resolver starting Step 3A.
- Does not create the Step 5 fixture corpus. The resolver's fixture-root
  override and its tests use small in-memory/temp-directory synthetic
  descriptors to prove the mechanism, not the real fixture module.
- Does not change `manifest.js` or any Yoma runtime behavior.

## Yoma proof

`modules/yoma/module.json` is Yoma's real descriptor, added by this PR.
It resolves cleanly through both resolvers with 0 validation errors, and
every path it declares matches the real, already-existing Yoma paths
byte-for-byte (there was nothing to invent - every field was read from
the current repository state, not designed in the abstract first). No
existing Yoma file was moved, renamed, or altered to make this descriptor
valid.
