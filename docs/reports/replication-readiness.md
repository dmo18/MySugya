# Replication readiness: onboarding a second tractate

**Verdict: the app and build layers are ready and need no change. The tooling
layer is not: 7 shared tools at the repo root hardcode `modules/yoma` and must
be parameterized first.**

This is the single definitive checklist. `docs/new-tractate-onboarding.md` holds
the procedure, `docs/reports/next-tractate-roadmap.md` holds the policy that no
tractate starts without operator selection. This document holds the evidence.

    npm run audit:replication            # tiered report
    npm run audit:replication -- --json  # machine-readable
    npm run audit:replication -- --strict  # exit 1 while blockers remain

**No real second tractate exists or should be created.** The audit's fixture is
synthetic and lives in a temp directory; nothing is written under `modules/`.

## What is already ready

The multi-tractate claim holds where it matters most, and the audit proves it
rather than asserting it:

- `scripts/build.mjs` allowlists module data scripts with
  `/^modules\/[a-z0-9_-]+\/learning_data\.js$/` and copies the whole `modules/`
  tree. It accepts `modules/berakhot/...` and `modules/rosh-hashanah/...`, and
  rejects `modules/Yoma/...` (uppercase) and `modules/../etc/...` (traversal).
- `app.jsx` carries the matching runtime allowlist (`isAllowedModuleDataScript`)
  and reads `?module=`, falling back to the landing page for an unknown id.
- `manifest.js` exports an array registry, not a single entry.
- `app.jsx`'s masechet index already lists all of Shas, so a new tractate
  appears in navigation without a code change.

All 8 app-layer fixture checks pass. **Nothing in the app or build pipeline
blocks a second tractate.**

## Blockers: 7 Yoma-pinned shared tools

These live at the repo root, run for every module in principle, and resolve
only for Yoma in practice.

| file | hardcoded refs | what breaks |
|---|---|---|
| `scripts/test_worker_policy.py` | 32 | policy tests assert Yoma paths |
| `scripts/worker_pipeline.py` | 28 | the entire worker pipeline |
| `scripts/audit-rashi-renderer-readiness.mjs` | 5 | renderer readiness audit |
| `scripts/check-rashi-browser-shard-artifact.mjs` | 3 | shard evidence verification |
| `scripts/run-rashi-association.mjs` | 2 | association browser runner |
| `scripts/combine-rashi-browser-shards.mjs` | 1 | shard combiner |
| `scripts/rashi-browser-shard-runner.mjs` | 1 | shard runner |

The worst is `worker_pipeline.py`. It **advertises** a module parameter:

    python3 scripts/worker_pipeline.py manifest --type rashi-repair --module yoma --range 61a

but then sets `YROOT = REPO / "modules" / "yoma"` and carries roughly twenty
literal `modules/yoma/...` prefixes for content classification, freshness
checks, and scope enforcement. **The `--module` flag is cosmetic.** A worker
manifest generated for a second tractate would silently classify against Yoma's
paths, which is worse than failing outright: scope gates would pass while
pointing at the wrong module.

This is the item to fix first, and fixing it is mechanical: thread the module id
from the existing flag into `YROOT` and derive the prefixes from it.

## Clone cost: 25 per-module files, 43 npm scripts

Not blockers, but the real cost of standing up a module:

- **25 files under `modules/yoma/scripts/` name their own module id.** Copying
  the directory means 25 edits. A `MODULE_ID` constant read from a per-module
  config would reduce this to one, and is worth doing before the second
  tractate rather than after the third.
- **43 of 63 npm scripts are `:yoma`-suffixed.** A second tractate needs 43 new
  entries, each duplicating a `cd modules/<id> && python3 scripts/...` line.
  Only 20 scripts are module-generic today.

## Checklist

Ordered. Each step is verifiable, and steps 1-3 are prerequisites for using the
pipeline at all.

### Before any content work

1. **Operator selects the tractate.** Name, scope (full or bounded daf range),
   and enrichment depth. Nothing below starts first. See
   `docs/reports/next-tractate-roadmap.md`.
2. **Parameterize the 7 pinned tools.** Thread the module id through
   `worker_pipeline.py` first, then the four `.mjs` shard/readiness tools, then
   `test_worker_policy.py`'s fixtures. Verify with
   `npm run audit:replication -- --strict` exiting 0.
3. **Introduce a per-module `MODULE_ID`** so `modules/<id>/scripts/` can be
   copied without 25 hand edits. Confirm Yoma still passes every gate
   afterwards, since this touches Yoma's frozen tooling but not its content.

### Source acquisition

4. Sefaria `he:`/`en:` fetched verbatim into `modules/<id>/source_store.js`.
   Immutable once fetched.
5. talmud.dev Vilna-line cache into `modules/<id>/assets/talmuddev/`.
6. Daftexts generated, Vilna line breaks embedded.
7. Daf list, perek boundaries and amud irregularities confirmed before
   enrichment begins.

### Schema and enrichment

8. Enrichment JSON conforms to `shared/schema_map.js` with no new fields.
9. `validate_schema_completeness.py` passes for the new module.
10. `takeaway.type` drawn only from the canonical five.
11. **`argumentFlow.type` drawn only from `controlledValues.argumentStepType`.**
    Yoma does not currently satisfy this (1,320 of 1,953 steps are outside the
    list, and they render as mislabelled Questions). A new tractate must not
    inherit that drift. See `docs/reports/sugya-schema-readiness.md`; the
    vocabulary decision pending there should be settled before enrichment
    authoring starts, not after.
12. **`sourceRefs` authored in canonical object form from the start**, with
    `lineId` naming the containing segment and `vilnaLine` the precise line.
    See `docs/reports/source-refs-normalization-plan.md` for the two coordinate
    systems and the defect classes to avoid.
13. `linkedGemaraLineIds` populated from the start. The linked renderer is the
    only renderer; there is no vilnaLine-coincidence fallback.

### Pipeline and gates

14. Confirm each task type's `allowedFiles` in `scripts/worker_task_types.json`
    resolves for the new module id, and extend deliberately if not.
15. Worker manifests generate cleanly; `npm run worker:schema-matrix` and
    `npm run worker:docs` regenerate without drift.
16. Every Yoma gate has a `<id>` equivalent wired into `package.json` and into
    `validate:offline:<id>`.
17. Confirm the sharded browser workflow's shard count suits the new tractate's
    size; the daf list comes from `audit_rashi_association.py --list-daf`, which
    is module-scoped.
18. Browser coverage: the association spec is written against the audit plan
    rather than hardcoded text, so it generalizes, but its default target daf
    needs review.

### Closing

19. Full validation chain green, build and browser suites green.
20. Product quality audit across chapters and sugya types.
21. Freeze only when the criteria in `CLAUDE.md` are met.

## Out of scope

- Creating any module directory for a non-Yoma tractate.
- Fetching source text for a non-Yoma tractate.
- Adding manifest entries for tractates that do not exist.

Current status of everything else: `docs/reports/open-items.md`.
