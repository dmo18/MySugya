# Platform readiness: Phase 2 snapshot

**Status: Phase 2 readiness snapshot, not the Phase 4 terminal closure
document.** `docs/platform-closure-plan.md` defines
`docs/reports/platform-readiness.md` as Phase 4's terminal evidence
document, and Phase 4 explicitly "requires Phases 1, 2, and 3 all
complete" and "cannot start early." At the time this file was created,
Phase 1 and Phase 2 are complete but **Phase 3 has not started** (by
explicit governing instruction: this campaign was scoped to Phase 2
only, and Phase 3 must not be started as part of it). This document
therefore records the evidence for Phase 2's completion only, using the
filename Phase 4 will later reuse and expand. When Phase 3 and Phase 4
actually run, this file is expected to be superseded with the full
four-phase terminal record; until then, treat every claim below as
scoped strictly to Phase 2, not the whole platform.

## What this document is not

- It is not a claim that Phase 3 (tractate-agnostic replication) is
  complete. Phase 3 has not started.
- It is not a claim that Phase 4 (final repository closure) has run.
  Phase 4 has not started and cannot start until Phase 3 finishes.
- It does not restate Phase 1 (production publishing and repository
  protection) evidence in full; see `docs/platform-closure-plan.md`'s
  Phase 1 section and `docs/reports/open-items.md`'s COMPLETED section
  for that record.

## Phase 2 completion evidence

Phase 2 (`docs/platform-closure-plan.md`) covers two independent
contracts: the `argumentFlow` category/type schema (2A) and the
`sourceRefs` canonical schema (2B). Both are complete.

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
- `python3 scripts/validate_source_refs.py --strict` (run from
  `modules/yoma/`): exit code 0, 0 defects.
- Of the original 550 defective refs identified by
  `docs/reports/source-refs-normalization-plan.md`: 412 mechanical
  repairs, 105 of 138 judgment-required repairs by textual evidence,
  and all 33 of the subsequently classified residue
  (`docs/reports/sourcerefs-blocker-classifications.json`) now
  resolved - 2 `QUALIFIED_CROSS_DAF` migrated, 29
  `ABSENT_OR_UNANCHORED` removed, and the final 2 `TIED_CANDIDATES`
  (`yoma-044b-l01`, `yoma-063a-l03a`) repaired in a final, tightly
  scoped re-adjudication (PRs #368-#369) using evidence the prior
  five-way classification pass had not fully exploited:
  - `yoma-044b-l01` (44b): resolved as a two-ref repair on the
    existing compound step (`yoma-044b-l01a` + `yoma-044b-l01b`,
    preserving authored order), not a step split - multiple
    `sourceRefs` per step is an already-legal, already-used corpus
    shape (21 precedent steps), and `app.jsx` never reads
    `sourceRefs`, so there is no renderer or navigation risk.
  - `yoma-063a-l03a` (63a): resolved to `yoma-063a-l10` using the
    step's own `speaker` field ("Rav Dimi from Eretz Yisrael"), a
    verbatim match to `l10`'s transmission formula, whose conclusion
    (exempt) genuinely supports the ruling the step cites - unlike the
    other candidate, `yoma-063a-l17` (introduced by Ravin, concluding
    liable, which would contradict rather than support).
- No `sourceType` was invented in either repair; both reuse `gemara`,
  independently confirmed from each target's own content.
- No Hebrew/English source text, Rashi data, argumentFlow
  text/type/category, speaker field, sugya boundary, renderer, or
  validator was changed to reach this state.

### Test and build evidence at Phase 2 closure

Recorded at the point this snapshot was written (VERSION and commit
recorded in the closure PR that introduces this file; see
`docs/platform-closure-plan.md`'s Phase 2 section and
`docs/reports/open-items.md` for the merge SHAs of PRs #368 and #369):

- `validate:offline:yoma` (all 12 gates, including
  `validate_source_refs.py --strict`): green.
- `npm test`: green.
- `npm run test:browser`: green.
- `npm run build` / `npm run check:deploy-html`: green.
- GitHub Pages deployment: green for the PR #369 merge commit
  (`3c81ce1`, workflow run `30598090265`, conclusion `success`).
- 0 open PRs, 0 open issues at the time of this snapshot.

## Phase 3 and Phase 4: explicitly not started

No `modules/<masechta>/` other than `modules/yoma/` exists. No
replication-tooling parameterization work (`docs/reports/replication-readiness.md`)
has been performed as part of this campaign. Phase 4's dependency
("Requires Phases 1, 2, and 3 all complete. Cannot start early.") is not
met, and no work in this campaign attempted to meet it. This file will
need a Phase 3 and Phase 4 pass before it can honestly claim to be the
terminal closure document `docs/platform-closure-plan.md` describes.
