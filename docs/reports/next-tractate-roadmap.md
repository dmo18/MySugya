# Next tractate: roadmap and prerequisites

**Classification: DEFERRED-ROADMAP. Every non-Yoma tractate is product
roadmap, not incomplete Yoma work.**

Yoma is complete in scope (173 daf, 492 sugyot) and actively maintained. The
absence of Berakhot, Shabbat, Sukkah, or any other tractate is not a defect,
not a gap in the Yoma campaign, and not a backlog item. Nothing in the
repository is blocked on it.

**No new tractate module may be created without explicit operator
selection.** A worker or agent must never start one on its own initiative,
and must never treat "only one tractate exists" as work to be corrected.

## Why this is roadmap and not debt

The platform is already multi-tractate by construction: `manifest.js` is a
module registry, the app reads `?module=`, and every validator, gate, and
worker task type is written against a module id rather than against Yoma
specifically. Adding a tractate is therefore a *content acquisition and
enrichment project*, not an architectural change. Its cost is dominated by
source ingestion and enrichment authoring, both of which need operator
direction on scope, priority, and budget.

## Prerequisites before any next tractate begins

These must be satisfied in order. `docs/new-tractate-onboarding.md` holds the
detailed procedure; this is the gate list.

### 1. Operator selection
An operator names the tractate and confirms scope (full tractate or a bounded
daf range) and the intended enrichment depth. Nothing below starts first.

### 2. Module descriptor and source acquisition
- `modules/<id>/module.json` created per
  `docs/reports/module-descriptor-contract.md`'s schema (or scaffolded
  first with `python3 scripts/scaffold_module.py --key <id> --search-root
  <path>`), so the module resolves via `scripts/module_resolver.py`/
  `shared/module_resolver.js` and every generic tool that depends on
  it (`worker_pipeline.py`, `validate_module_schema.mjs`, `build.mjs
  --module`).
- Sefaria `he:`/`en:` fetched verbatim into `modules/<id>/source_store.js`;
  these fields are immutable once fetched.
- talmud.dev Vilna-line cache fetched into `modules/<id>/assets/talmuddev/`.
- Daftexts generated and Vilna line breaks embedded.
- Confirm the tractate's daf list, perek boundaries, and any amud
  irregularities before enrichment begins.

### 3. Schema validation
- Enrichment JSON conforms to `shared/schema_map.js` with no new fields.
  Adding a schema field is a separate, deliberate decision.
- `validate_schema_completeness.py` passes for the new module.
- `takeaway.type` values drawn only from the canonical five.

### 4. Worker manifests and task types
- The task-type registry (`scripts/worker_task_types.json`) is module-generic
  today; confirm each type's `allowedFiles` patterns resolve correctly for
  the new module id, and extend deliberately if not.
- Worker manifests generate cleanly for the new module.
- `npm run worker:schema-matrix` and `npm run worker:docs` regenerate without
  drift.

### 5. Tests and gates
- Every Yoma gate has a `<id>` equivalent wired into `package.json` and into
  `validate:offline:<id>`.
- Browser coverage: the Rashi association spec is written against the audit
  plan rather than hardcoded text, so it generalizes, but its default target
  daf and any module-specific selectors need review.
- The sharded browser workflow's daf list comes from
  `audit_rashi_association.py --list-daf`, which is module-scoped; confirm
  the shard count suits the new tractate's size.

### 6. Renderer expectations
The linked `linkedGemaraLineIds` renderer is the only renderer - there is
no rollback path. A new tractate is expected to populate
`linkedGemaraLineIds` from the start; the legacy vilnaLine-coincidence
renderer no longer exists (removed at VERSION 15.346) and is not a
supported authoring model. See
`docs/reports/legacy-renderer-retirement-policy.md`.

## Explicitly out of scope for the current campaign

- Creating any module directory for a non-Yoma tractate.
- Fetching source text for a non-Yoma tractate.
- Adding manifest entries for tractates that do not exist.

Current status of everything else: `docs/reports/open-items.md`.
