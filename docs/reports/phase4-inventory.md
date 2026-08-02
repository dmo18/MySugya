# Phase 4 Step 1: repository-wide status and debt inventory

**Status: read-only inventory, produced against `main` `1de8576` (VERSION
15.395, Phase 3 complete at 38/38).** Machine-readable form:
`docs/reports/data/phase4-inventory.json`. This document summarizes the
methodology and findings; the JSON carries full per-finding detail
(file, matched term, context, classification, required action, whether
it blocks Phase 4).

## Methodology

Read in full: `README.md`, `CLAUDE.md`, `docs/platform-closure-plan.md`,
`docs/reports/platform-readiness.md`, `docs/reports/open-items.md`,
`docs/new-tractate-onboarding.md`, `docs/tractate-build-process.md`,
`docs/yoma-completion-report.md`, `docs/reports/phase3-inventory.md`,
`docs/reports/replication-readiness.md`,
`docs/reports/module-descriptor-contract.md`, `modules/yoma/MODULE.md`,
plus `docs/reports/next-tractate-roadmap.md`,
`docs/reports/rashi-association-audit.md`,
`docs/reports/sugya-schema-readiness.md`,
`docs/reports/source-refs-normalization-plan.md`,
`docs/rashi-audit-backlog.md`, `docs/worker-pipeline-sop.md`,
`docs/worker-pipeline.md`, `docs/reports/task-type-reference.md`.

Grep swept all 877 git-tracked files (excluding `dist/`) for every term
the governing directive listed (TODO/FIXME/XXX/HACK, temporary,
provisional, legacy, fallback, rollback, paused, deferred, blocked,
blocker, unresolved, unknown, stale, pending, in progress, not started,
later, future work, follow-up, operator decision/owned, manual step,
partial, skipped, deprecated, workaround, allowlist, baseline,
exception, scaffold/migration debt, compatibility, hardcoded, Yoma-only,
one real module, second tractate).

`learning_data.js`, `source_store.js`, and `modules/yoma/assets/**/*.json`
were excluded from manual-debt classification (class I,
GENERATED_OR_VENDOR): these are verbatim Sefaria/talmud.dev source or
Rashi helper translations, and incidental English words like
"temporary"/"provisional" inside the Talmudic content itself are not
repository status markers.

**Zero real code-debt markers** (TODO/FIXME/XXX/HACK) exist in tracked
source. The only two grep hits for that pattern were this Phase 4
instruction text quoted verbatim inside `docs/platform-closure-plan.md`,
and `audit_schema_semantics.py`'s own regex that *detects* such markers
in enrichment content - a validator, not debt.

## Settings re-verification (Step 4, folded in here since it informed classification)

- **Branch ruleset**: `GET /repos/dmo18/MySugya/rulesets/19991220`
  succeeded via direct API call this session (the proxy did not block
  this specific endpoint) and is byte-identical to the Phase 1
  completion record: `refs/heads/main`, enforcement active, PR required,
  0 mandatory reviews, merge/squash/rebase allowed, required status
  check exactly `build`, strict policy true, deletion and
  non-fast-forward rules present, `current_user_can_bypass: "never"`.
  **No drift.**
- **Pages config endpoint**: `GET /repos/dmo18/MySugya/pages` still
  returns `403 Access to this GitHub API path is not permitted through
  this proxy` - the same environment-policy block documented in Phase
  1's completion record, re-confirmed fresh, not new drift.
- **Deployment history**: `GET /repos/dmo18/MySugya/deployments` shows
  exactly one `github-pages` deployment per merge SHA for the last 5
  merges (`1de8576`, `f442159`, `075e4fd`, `d50c180`, `b74f9dd`),
  sequential, no competing/interleaved deployment - behaviorally
  confirms no dual-publisher race.
- **Branches**: 64 non-main branches exist, all named after
  already-merged, already-squashed campaign PRs (per-daf
  rashi-reconstruction branches, `sourcerefs-phase2-step*` branches,
  etc.). Not a Phase 4 completion criterion (0 open PRs/issues and a
  clean tree are the criteria, not 0 stale branches). Not deleted, per
  the explicit instruction not to delete branches merely because they
  exist.
- **Worker manifest/queue**: `.worker-manifest.json` at HEAD is a
  historical `docs-tooling` manifest from PR F's reconciliation
  (harmless - docs-tooling manifests always carry empty `targets`).
  `npm run worker:queue` reproduces the exact, already-documented
  derivation-artifact state `docs/reports/open-items.md` explains
  ("done: none \| remaining: [79b...88a]" despite all 18 targets having
  merged commits) - unchanged, not a new finding.

## Findings requiring a documentation fix (12)

Full detail in the JSON. Six block Phase 4 completion criterion "no
completed work is still described as open" or criterion #11
(`platform-readiness.md` must become terminal); six are non-blocking
polish, fixed in the same pass since they are narrowly scoped and
low-risk.

| id | file | classification | blocks Phase 4 |
|---|---|---|---|
| F1 | `docs/platform-closure-plan.md` | COMPLETED_STALE_TEXT (Phase 3 still says BLOCKED) | yes |
| F2 | `docs/reports/platform-readiness.md` | ACTIVE_BLOCKER (must become terminal doc) | yes |
| F3 | `docs/reports/open-items.md` | COMPLETED_STALE_TEXT (fixture row) | yes |
| F4 | `docs/new-tractate-onboarding.md` | COMPLETED_STALE_TEXT (Phase 3 gate) | yes |
| F5 | `CLAUDE.md` | COMPLETED_STALE_TEXT (one-line annotation) | no |
| F6 | `docs/reports/replication-readiness.md` | VALID_HISTORICAL_RECORD, needs banner | no |
| F7 | `docs/reports/rashi-association-audit.md` | COMPLETED_STALE_TEXT (legacy renderer table) | no |
| F8 | `docs/reports/sugya-schema-readiness.md` | VALID_HISTORICAL_RECORD, needs banner | no |
| F9 | `docs/reports/source-refs-normalization-plan.md` | VALID_HISTORICAL_RECORD, needs updated banner | no |
| F10 | `docs/tractate-build-process.md` | documentation gap (no module.json mention) | yes |
| F11 | `docs/new-tractate-onboarding.md` + `next-tractate-roadmap.md` | documentation gap | yes |
| F12 | `docs/reports/next-tractate-roadmap.md` | minor tense error | no |

## Explicitly not Phase 4 blockers

- **Rashi content-quality (translation accuracy) audit** - genuine,
  ongoing, already correctly classified OPEN-ACTIONABLE in
  `docs/reports/open-items.md`. Distinct from and predates the Phase
  3/4 platform-closure campaign. Phase 4's completion criteria require
  Rashi *structural*/renderer gates (corpus validation, association,
  boundary registry, readiness 8/8), never translation-quality audit
  completion. Not touched - touching it would risk reopening Rashi
  semantic repair, explicitly prohibited by this campaign's
  constraints.
- **Nekudot/vowelization audit** - OUT_OF_SCOPE, unchanged.
- **331 canonical string sourceRefs** - OUT_OF_SCOPE by permanent
  decision, unchanged.
- **Cloudways / mysugya.com** - OUT_OF_SCOPE, unchanged.
- **64 stale merged-PR branches** - historical git-ref residue, not a
  completion criterion, not deleted.

## Disposition

All 12 findings are documentation-only corrections: no Yoma content, no
validator, no schema, no allowlist, and no CI gate is touched. Applied
in the cleanup PR that ships alongside this inventory.
