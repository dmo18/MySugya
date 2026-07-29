# New tractate/module onboarding checklist

How to bring a second masechta into MySugya without repeating the Yoma
pilot's failures. Content work on the new module may not begin until
every checklist item is done. The build pipeline itself (source store,
daftexts, Vilna breaks, enrichment) is documented in
docs/tractate-build-process.md; this checklist covers the SAFETY layer.

**Prerequisite this checklist assumes but does not yet guarantee**: items 3
and 5 below assume the shared worker/validator tooling actually generalizes
per module. As measured in `docs/reports/replication-readiness.md`, it does
not yet - 7 shared tools at the repo root hardcode `modules/yoma`, and
`worker_pipeline.py`'s `--module` flag is currently cosmetic. That
parameterization work is Phase 3 of `docs/platform-closure-plan.md` and must
be complete, proven against the synthetic fixture module described there,
before this checklist can be followed as written for a real tractate.

## 1. Data source inventory

- [ ] Sefaria refs and talmud.dev cache fetched for every daf
- [ ] source_store.js populated verbatim (he/en untouched)
- [ ] raw Rashi line counts recorded per daf (they become gate baselines)

## 2. Schema mapping

- [ ] enrichment JSON follows shared/schema_map.js; any new field goes
      through a schema change (docs-tooling PR) FIRST
- [ ] run the corpus path walk (see scripts/worker_schema_scope.json
      generation) and extend the inventory with any module-specific paths
- [ ] classify every new path (immutable / manifest-editable / judgment-required /
      flag-only / generated-only / deprecated) and assign an owning task
      type; `npm run worker:schema-matrix` must pass

## 3. Validator adaptation

- [ ] port the module validators (sefaria, en, daftext, rashi structural,
      content, links, repetition, literal, order, schema completeness)
      with module-correct paths and id prefixes
- [ ] wire them into an offline chain and into CI BEFORE any content PR
- [ ] pre-commit hook covers the new module's data paths

## 4. Generated file policy

- [ ] learning_data.js equivalent is generated-only from day one
- [ ] freshness check (regenerate + byte-compare + restore) wired into
      the chain, hook, and CI

## 5. Manifests and task types

- [ ] registry entries reuse the existing task types with module-correct
      allowedFiles (the <daf> patterns and module paths)
- [ ] worker:manifest/preflight/packet/prompt/verify run green in
      --dry-run against the new module

## 6. Baseline allowlists

- [ ] start EMPTY; a new module has no tolerated defects
- [ ] if migration imports known-bad legacy content, document each
      violation in the module backlog and load it as a ratchet baseline
      in the same PR that documents it (RASHI_ALLOWLIST_RESTRUCTURE=1,
      docs-tooling only); the list may only shrink afterwards

## 7. Required first dry runs (no content edits)

- [ ] one repair-type manifest, one reconstruction-type, one audit-only,
      one docs-tooling: manifest + preflight + packet + prompt all green
- [ ] negative tests: illegal field edit, cross-daf edit, allowlist
      growth, workflow edit in a content manifest - all must fail with
      exact pointers

## 8. Branch protection

- [ ] required check `build` (containing the module's offline gates and
      both scope checks), PR-required, up-to-date-required, force pushes
      blocked - configured by an admin before the first worker pass

## 9. First worker task

- [ ] choose the smallest, most mechanical, fully gate-covered task
      (single daf, repair-type, machine-checkable completion)
- [ ] generate the prompt with worker:prompt; never hand-write it
- [ ] one daf per PR until two consecutive green passes; then at most
      the type's maxBatch

## 10. Ongoing discipline

- [ ] every defect found later: document in the module backlog first,
      allowlist as ratchet baseline second, repair in its own scoped
      pass third; remove entries as the validator reports them stale
- [ ] regenerate reference docs (`npm run worker:docs`) after any
      registry/inventory change
- [ ] declare the module frozen only per CLAUDE.md's freeze definition
