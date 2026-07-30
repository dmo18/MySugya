# argumentFlow sourceRefs: canonical schema, defect inventory, migration plan

**Status update (VERSION 15.363, Phase 2 Step 4 of
`docs/platform-closure-plan.md`): the judgment-required pass (PRs 1 and 2
below) is APPLIED, partially.** Every one of the 138 judgment-required refs
(88 `OBJECT_COORDINATE_CONFLICT` + 50 `OBJECT_DANGLING_AMBIGUOUS`) was
reviewed individually by reading the argumentFlow step's `label`/`text`
against the actual Gemara content on its daf - a full-daf search, not just
the narrow Vilna-interval candidate list the original plan below assumed
would be the only evidence available. The two classes turned out not to need
separate PRs: the same read-the-step-against-the-daf method resolves both, so
they were reviewed and shipped together rather than as PR 1 (conflicts) then
PR 2 (ambiguities). Every resolution, and the specific evidence for it, is
recorded in `docs/reports/source-refs-semantic-review.json`; the tool that
applies it is `modules/yoma/scripts/apply_sourcerefs_semantic_repair.py`.

**Result: 105 of 138 resolved (102 reassigned to a different, better-supported
segment; 3 needed only a stale `vilnaLine` correction on an already-correct
`lineId`). 33 remain UNRESOLVED**, each with its own documented blocker - not
a shortfall against the plan below so much as the plan's own anticipated
possible outcome turning out to be real: some refs' claimed content is not
present anywhere on the daf the sugya is declared on (a small number of cases
found the true content lives on an *adjacent* daf instead - e.g. a sugya
declared on 71a whose narrative content is actually on 71b - which the
per-daf `lineId` contract cannot reference), and a few are genuine ties
between two equally-supported candidates. None was forced. Full per-case
detail, including the exact evidence for every UNRESOLVED case, is in
`docs/reports/source-refs-semantic-review.json`.

The original analysis below (written before PR 3 applied, and before the
judgment pass ran) is preserved as the historical record of the defect
inventory and the reasoning that shaped the review method; only the "not
applied" / "50-88 split into two PRs" framing is superseded by what actually
ran.

**Original status: ANALYSIS COMPLETE, MIGRATION NOT APPLIED.**

The normalization pass was blocked. 412 of 550 defective refs can be repaired
mechanically, but 469 refs cannot be settled from repository data alone, and
applying only the mechanical subset would leave the corpus in a half-migrated
state that is harder to reason about than the current one. The blockers, the
exact migration, and the proposed batching are all below.

Supersedes the one-line note previously carried in
`docs/reports/schema-coverage-matrix.md` ("argumentFlow sourceRefs entries are
plain strings on some daf and objects on others; normalization is deferred to a
future structural-repair pass"). That note described the drift as a
string-versus-object formatting split. It is not. The string refs are the sound
ones: all 331 resolve cleanly. The defects are concentrated in the object form.

## Tooling

| command | what it does |
|---|---|
| `npm run validate:sourcerefs:yoma` | classify every ref, report, exit 0 |
| `npm run validate:sourcerefs:strict:yoma` | same, exit 1 on any defect |
| `npm run preview:sourcerefs:yoma` | dry-run migration preview, never writes |
| `npm run test:sourcerefs:yoma` | unit tests (wired into `npm test`) |

Useful flags: `--daf 67a`, `--class OBJECT_COORDINATE_CONFLICT`, `--json` on the
validator; `--show-blocked`, `--json` on the preview.

`validate:sourcerefs:strict:yoma` is deliberately **not** wired into
`validate:offline:yoma`. Turning it on before the backlog below is cleared would
only produce a red gate nobody can turn green. The unit tests are wired into
`npm test`, so the classifier itself is covered on every run. Wiring strict mode
in is the final step of the migration, not a prerequisite for it.

## The two coordinate systems

This is the fact that explains every defect class, and getting it wrong is what
makes naive repairs unsafe.

A rendered line id is minted only where a **Sefaria segment** starts, so line
ids are coarser than Vilna line numbering. `build_learning_data.py` mints them
as `yoma-<3-digit daf><amud>-l<2-digit Vilna line>`, adding a letter suffix when
one Vilna line carries more than one segment (`l01a`, `l01b`, and on 52b as far
as `l01f`). The corpus has 2,300 line ids over 173 daf; 60 Vilna line numbers on
53 daf carry more than one segment.

So one line id covers a half-open Vilna interval `[start, next-start)`. A
sourceRef's `lineId` names the containing **segment**; its `vilnaLine` names the
precise **Vilna line** inside that segment. The two are supposed to disagree
numerically. On Yoma 2a, step-03 of `yoma-002a-s01` carries
`{lineId: "yoma-002a-l04", vilnaLine: 6}`: the Sages' `ein la-davar sof`
objection sits at Vilna line 6, inside the segment anchored at line 4. That ref
is correct.

A ref is referentially sound when `lineId` exists on its daf **and** `vilnaLine`
falls inside that line id's interval. Any checker that instead requires
`vilnaLine == line.vilnaLine` reports ~500 false positives, and any repair that
rewrites `lineId` to the exact-match line silently moves anchors. The validator
in this repository uses interval containment for exactly this reason.

`validate_source_refs.py` re-derives line ids from the enrichment JSON alone,
using the same rule as the builder, and self-checks that derivation against the
generated `learning_data.js` (currently: reproduces all 2,300 ids across all 173
daf). That keeps the validator offline and node-free without letting it drift
from the real id space.

## Canonical schema

`shared/schema_map.js` declares `sourceRefs` as `object[]`, `status: optional`,
with the shape `{ sourceType, lineId, vilnaLine, note }`. That object form is
canonical. This document does not change the schema; it records what the
canonical form means and what it takes to reach it.

| field | required | meaning |
|---|---|---|
| `sourceType` | yes | `gemara` or `mishnah`. Editorial classification of the cited material, **not** a copy of the line's `kind`. |
| `lineId` | yes | Existing line id on the same daf, in the builder's minted form. |
| `vilnaLine` | yes | Vilna line number, which must fall inside `lineId`'s interval. |
| `note` | no | Short free text on what the step draws from the line. |

Two properties of the current data constrain any migration:

- **`sourceType` is not derivable from the line.** 15 refs on Mishnah-kind lines
  are typed `gemara` (an editorial judgment that the step cites the passage as
  Gemara argument), and the Mishnah value is spelled both `mishnah` (3 refs) and
  `mishna` (the line `kind`). There is no rule that reproduces the existing
  values, so `sourceType` cannot be synthesized for a ref that lacks it.
- **The string form carries strictly less information** than the object form: a
  Sefaria segment reference determines `lineId` and `vilnaLine` but says nothing
  about `sourceType`. Converting string to object is therefore
  information-adding, not lossless normalization.

The `mishnah`/`mishna` vocabulary split should be settled as part of the
migration, but it is a controlled-values decision, not a mechanical one, and
belongs in the same PR that touches those refs.

## Original inventory (before PR 3)

173 files, 1,953 argumentFlow steps, **1,981 sourceRefs elements**.

| class | count | sound? |
|---|---|---|
| `OK` (object, lineId exists, vilnaLine inside its interval) | 1,100 | yes |
| `STRING_RESOLVABLE` (string, resolves to exactly one line id) | 331 | yes |
| `OBJECT_DANGLING_REPAIRABLE` | 412 | no, mechanical |
| `OBJECT_COORDINATE_CONFLICT` | 88 | no, judgment |
| `OBJECT_DANGLING_AMBIGUOUS` | 50 | no, judgment |

**1,431 sound, 550 defective, across 102 daf.** No ref is malformed,
cross-daf, unparseable, or missing a `vilnaLine`: every defect is a
resolvable-in-principle coordinate problem.

## Current inventory (after PR 3)

| class | count | sound? |
|---|---|---|
| `OK` | 1,512 | yes |
| `STRING_RESOLVABLE` | 331 | yes |
| `OBJECT_DANGLING_REPAIRABLE` | 0 | (was 412; now applied) |
| `OBJECT_COORDINATE_CONFLICT` | 88 | no, judgment |
| `OBJECT_DANGLING_AMBIGUOUS` | 50 | no, judgment |

**1,843 sound, 138 defective, across 73 daf.** Only judgment-required
refs remain (PRs 1 and 2).

## Final inventory (after the semantic-repair pass)

| class | count | sound? |
|---|---|---|
| `OK` | 1,617 | yes |
| `STRING_RESOLVABLE` | 331 | yes |
| `OBJECT_DANGLING_REPAIRABLE` | 0 | mechanically resolved (PR 3) |
| `OBJECT_COORDINATE_CONFLICT` | 24 | no, exact-blocker documented |
| `OBJECT_DANGLING_AMBIGUOUS` | 9 | no, exact-blocker documented |

**1,948 sound, 33 defective, across 16 daf, 23 sugyot, 33 argumentFlow
steps.** Every one of the 33 has a recorded reason in
`docs/reports/source-refs-semantic-review.json` that a safe repair was not
possible - not a gap in the review, a documented stop.
`npm run validate:sourcerefs:yoma` reproduces the 1,948/33 split; the daf,
sugya and step counts are computed from the same run's finding list, filtered
to the genuine `DEFECT_CLASSES` (`OBJECT_COORDINATE_CONFLICT` +
`OBJECT_DANGLING_AMBIGUOUS`), never the raw finding list.

**Correction (this pass):** an earlier version of this line read "across 46
daf." That number was a reporting bug, not a different true count: the CLI's
"daf carrying defects" line was computed over the full `findings` list
returned by `validate_source_refs.py`'s `run()`, which includes every
non-`OK` classification - including the 331 sound `STRING_RESOLVABLE` refs,
which are not defects. Those 331 sound-but-non-canonical refs are spread
across far more daf than the 33 genuine defects, so counting daf over the
unfiltered list produced 46 instead of the true 16. `validate_source_refs.py`
now filters to `DEFECT_CLASSES` before computing the affected-daf set, so
the CLI's own output and this document agree.

## Current state (terminal state for this campaign)

The 33 residual refs above are now individually classified in
`docs/reports/sourcerefs-blocker-classifications.json` (2
`QUALIFIED_CROSS_DAF`, 29 `ABSENT_OR_UNANCHORED`, 2 `TIED_CANDIDATES`; see
`docs/reports/sourcerefs-blocker-table.md` for the full evidence per case
and `docs/reports/sourcerefs-crossdaf-schema-decision.md` for the new
cross-daf shape). All resolvable cases are now **applied**:

- The 2 `QUALIFIED_CROSS_DAF` cases (`yoma-069b-l19` -> `yoma-070a-l16`,
  `yoma-069b-l21` -> `yoma-070a-l22`) are migrated to the cross-daf object
  shape by `apply_sourcerefs_crossdaf_migration.py`, touching
  `modules/yoma/assets/learning/yoma/69b.learning.json` (2 refs).
- The 29 `ABSENT_OR_UNANCHORED` cases have their sourceRefs removed
  (`sourceRefs: []`, matching the corpus's own convention for other
  optional array fields left inapplicable) by
  `apply_sourcerefs_absent_removal.py`, across
  `modules/yoma/assets/learning/yoma/{48b,52b,55a,61a,67a,67b,69a,69b,70a,70b,71a,71b,72b,75a}.learning.json`
  (29 refs).
- The 2 `TIED_CANDIDATES` cases (`yoma-044b-l01`, `yoma-063a-l03a`) are
  **left blocked, deliberately, permanently**: each is a genuine tie
  between two equally-supported candidates (or, for 44b, a compound step
  whose two clauses split across two segments) with no textual basis to
  prefer one. No tie was forced; both remain documented as unresolved in
  `docs/reports/sourcerefs-blocker-classifications.json`.

`docs/reports/source-refs-semantic-review.json` and this document's
tables above are left as the static historical record of the earlier
semantic-repair pass and are not rewritten; the corpus's live
classification is always `npm run validate:sourcerefs:yoma`'s own output,
currently:

| class | count | sound? |
|---|---|---|
| `OK` | 1,617 | yes |
| `STRING_RESOLVABLE` | 331 | yes |
| `OK_CROSSDAF` | 2 | yes |
| `OBJECT_COORDINATE_CONFLICT` | 1 | no, `yoma-063a-l03a` - tied, documented |
| `OBJECT_DANGLING_AMBIGUOUS` | 1 | no, `yoma-044b-l01` - tied, documented |

**1,950 sound, 2 defective, out of 1,952 total refs** (29 fewer than the
1,981 before this pass, since the 29 removed refs are simply absent now,
not reclassified into a different sound class). Both remaining defects
are the 2 `TIED_CANDIDATES` cases; no further mechanical or textual-
evidence repair is available from repository data alone for either.

### `OBJECT_DANGLING_REPAIRABLE` (412 refs, 52 daf) - mechanical

`lineId` names no line on the daf, but `vilnaLine` falls inside exactly one
line id's interval, so the target is uniquely determined. Two sub-patterns,
both artefacts of enrichment written before the current id convention settled:

- **Unpadded daf**: `yoma-12b-l01` where the minted id is `yoma-012b-l01`
  (119 refs, 15 daf, all in the 12b-19b band).
- **Sequential index instead of Vilna line**: `yoma-067a-l05` for the fifth
  segment, where the minted id is `yoma-067a-l18`. The ref's own `vilnaLine`
  already holds the true Vilna number, so it resolves the id.

The repair rewrites `lineId` only. `sourceType`, `vilnaLine`, `note`, key order
and array order are untouched. The preview asserts this as a losslessness
invariant rather than claiming it.

### `OBJECT_DANGLING_AMBIGUOUS` (50 refs, 43 daf) - judgment

`lineId` names no line, and `vilnaLine` falls on a Vilna line split across
several segments, so containment yields more than one candidate. Example:
`11b` `yoma-011b-s04` step-04 carries `lineId: yoma-011b-l41, vilnaLine: 41`,
and Vilna 41 covers both `yoma-011b-l41a` and `yoma-011b-l41b`. The worst case
is `52b` `yoma-052b-s01`, where Vilna 1 spans six sub-lines `l01a` through
`l01f`.

Nothing in the repository says which sub-line the step meant. Picking one
fabricates an anchor, so the preview refuses to propose these.

### `OBJECT_COORDINATE_CONFLICT` (88 refs, 24 daf) - judgment

`lineId` exists **and** `vilnaLine` exists, but `vilnaLine` falls outside
`lineId`'s interval, and both coordinates name real lines. Example: `67a`
`yoma-067a-s01` carries `{lineId: "yoma-067a-l05", vilnaLine: 18}`. `l05` covers
Vilna 5-11; Vilna 18 is `yoma-067a-l18`. Both are real lines several lines
apart. This is the same sequential-index drift as the repairable class, except
that here the stale sequential id happens to collide with a real minted id, so
the contradiction cannot be resolved by construction.

Two sub-patterns:

- **Sequential-index collision** (86 refs, concentrated on 49a-54b and 67a-76b):
  as above. The `vilnaLine` is *probably* authoritative, by analogy with the
  repairable class on the same daf, but "probably" is not evidence.
- **`vilnaLine` holding a suffix ordinal** (2 refs): e.g. `55a`
  `yoma-055a-l45a` with `vilnaLine: 1` and `yoma-055a-l45b` with `vilnaLine: 2`,
  where 1 and 2 look like the `a`/`b` ordinal rather than a Vilna line.

Settling either sub-pattern needs someone to read the step's `text` and `note`
against the Gemara at both candidate lines. That is a content judgment, so it is
out of scope for a mechanical pass.

## Why the migration is not applied

The governing rule is that normalization applies only when it is mechanically
lossless and source meaning, ids, Vilna lines, order and references are all
preserved, and that ambiguous conversions stop rather than invent metadata.

- 138 refs (50 ambiguous + 88 conflicting) **cannot** be converted without
  inventing an anchor.
- 331 string refs **cannot** be converted without inventing a `sourceType`.
- The 412 mechanical repairs are individually lossless and the preview proves
  it, but shipping them alone converts a uniform "legacy ids" problem into a
  mixed corpus where a dangling id might be legacy drift or might be one of the
  138 known-unresolved cases. That is worse for the next reader, not better.

`npm run preview:sourcerefs:yoma` currently reports 412 proposals and 469
blocked, with all six losslessness invariants passing over the proposal set.
The preview has no `--apply` flag by design.

There is also a scope constraint: applying any of this edits
`modules/yoma/assets/learning/*`, which the `docs-tooling` task type forbids and
`structural-repair` owns. The analysis, tooling and this plan are docs-tooling;
the application is not.

## Migration plan

Four PRs, in order. Each is independently revertible and leaves gates green.

**PR 1 - resolve the 88 coordinate conflicts** and **PR 2 - resolve the 50
split-line ambiguities**: **APPLIED, combined, partially resolved.** Both
classes were reviewed in a single pass (`sourcerefs-semantic-tool` #355,
`sourcerefs-semantic-content` #356) instead of two separate PRs, since the
same method - read the step against the actual daf text, full-daf search, not
just the candidate list - resolves both classes and splitting them would have
meant duplicating the same per-case forensic work across two PRs. A key
discovery during the review (first found on 12a and 53a) is that the
`vilnaLine` "probably authoritative" heuristic this plan originally proposed
is not reliable by itself: for every `OBJECT_COORDINATE_CONFLICT` case, the
stored `lineId` turned out to be an exact copy of the step's own `id` string
(a naming coincidence, not evidence), so the real anchor sometimes agreed with
`vilnaLine`'s containing segment and sometimes did not - each case needed its
own textual confirmation. 105 of 138 resolved (102 reassigned, 3 needed only a
`vilnaLine` correction); 33 documented as genuinely undecidable from the
available text (see `docs/reports/source-refs-semantic-review.json` for exact
per-case evidence). Deliverable achieved: every conflicting/ambiguous ref
either corrected with recorded evidence, or left with its exact blocker
documented - not the "zero remaining" this plan originally targeted, because
that target assumed every case would be resolvable, which turned out not to
be true.

**PR 3 - apply the 412 mechanical repairs** (`structural-repair`, 52 daf).
**APPLIED.** Generated from `preview_source_refs_migration.py`, applied by
`apply_sourcerefs_mechanical_repair.py`, which detects each file's exact
pre-existing JSON serialization (the corpus is not uniformly formatted: 163
files use `indent=1`, 8 use `indent=2`) and refuses to touch a file it
cannot reproduce byte-for-byte, so the diff touches only the repaired field.
Originally planned to run last so a remaining dangling id would unambiguously
mean legacy drift; run first instead, since `OBJECT_DANGLING_REPAIRABLE`,
`OBJECT_DANGLING_AMBIGUOUS`, and `OBJECT_COORDINATE_CONFLICT` are mutually
exclusive classes with no interaction between them, so the original ordering
rationale was about interpretive convenience, not a correctness dependency.
Deliverable: zero `OBJECT_DANGLING_REPAIRABLE` - confirmed by the post-write
corpus classification.

**PR 4 - decide the string refs.** **DECIDED, both sub-decisions, this pass.
No data changed; no daf touched.** The two questions this section
originally posed:

1. **Whether the 331 string refs are converted to object form at all.**
   **Decided: no conversion, not a deferred task.** They are referentially
   sound today; converting them would require assigning 331 `sourceType`
   values with no independent evidence for any of them, which is exactly
   the kind of invented metadata the contract forbids. String form is not a
   legacy shape awaiting cleanup - it is the correct, first-class
   representation for "exact segment identity known, no further metadata
   independently supported," alongside object form for "every additional
   field independently evidenced." Both are canonical; neither is superior
   to the other. See `docs/reports/sourcerefs-contract-decision.md` for the
   full decision record. No future migration may enrich these strings by
   guessing `sourceType` from the target line's `kind` or any other
   correlation; the contract document already shows why that guess is wrong
   15 times over (Mishnah-kind lines deliberately typed `gemara`).
2. **Whether `mishnah` and `mishna` are unified, and in which direction.**
   **Decided: no unification; the two spellings are not the same field.**
   Investigation found three distinct, independent uses, each already
   internally consistent:
   - `sourceType` on object `sourceRefs` (`LEGAL_SOURCE_TYPES`): spelled
     `"mishnah"`, 3 live occurrences. Established by
     `docs/reports/sourcerefs-contract-decision.md`.
   - `kind` on source lines (`controlledValues.lineKind` in
     `shared/schema_map.js`): spelled `"mishna"`, thousands of occurrences
     across every `*.learning.json` file and the generated
     `learning_data.js`/`source_store.js`. This is frozen Yoma corpus data;
     renaming it is out of scope without explicit approval and would gain
     nothing, since the field is already 100% internally consistent.
   - `argumentFlow[].type` (free-text, outside the canonical step-type
     vocabulary): one step (14a, `yoma-14a-s02`/`step-01`) carries
     `type: "mishna"`, picked up by the `ARGUMENT_TYPE_TO_CATEGORY` fallback
     table in `app.jsx` (`mishna: "case"`). This is part of the pre-existing
     "106 non-canonical `type` values" backlog tracked under Phase 2A/the
     argumentFlow vocabulary work, unrelated to `sourceRefs` or `kind`; it is
     not touched by this decision.

   These are three separate controlled vocabularies that happen to differ
   in spelling by field, not one inconsistent spelling in need of
   normalization. None meets the bar for a safe rename (demonstrably
   synonymous within one field, no external contract depends on the old
   spelling, mechanically lossless, tested for zero regression) because
   each is already its own field's sole, self-consistent canonical value.
   No normalization tooling is warranted.

Both decisions close this backlog item. `validate:sourcerefs:strict:yoma`
remains unwired from `validate:offline:yoma` until the 33 residual defects
(Phase 2B, Steps 2-4 of the current campaign) are resolved or the corpus is
otherwise fully reconciled - wiring it now would fail CI on those 33 for
reasons unrelated to this decision. This backlog section is retained as the
historical record of the four-PR plan rather than deleted, since PRs 1-3 are
already-merged history this document still describes.

### Affected files

| PR | refs | daf | files touched |
|---|---|---|---|
| 1+2 (combined, applied) | 105 of 138 | 39 | 39 `*.learning.json`, `learning_data.js`, `coverage.json` |
| 3 (applied) | 412 | 52 | 52 `*.learning.json` |
| 4 (decided, no data change) | 0 of 331 | 0 | docs only: this file, `sourcerefs-contract-decision.md`, `open-items.md`, `platform-closure-plan.md` |

Daf overlap across PRs is real (102 distinct daf carry defects), so PRs must
merge sequentially, with `learning_data.js` regenerated once per PR.

### Risk

**No user-visible risk today.** `sourceRefs` is `status: optional` and nothing
in `app.jsx` reads it. `argumentFlow` steps render their `label`, `type`,
`speaker` and `text`; the refs are not displayed, linked or navigated. The
defects are latent data debt, not a rendering defect, which is why this is a
planned migration rather than an incident.

**The risk is forward-looking.** `shared/schema_map.js` describes `sourceRefs`
as "used by tutoring to anchor steps to specific Gemara lines". Any future
tutoring, citation or deep-link feature built on the current data would silently
anchor 28% of steps to a nonexistent or contradictory line. Building that
feature before this migration is the actual hazard.

**Migration risk was concentrated in PRs 1 and 2**, which were judgment calls
on 138 refs. A wrong call there is invisible to every gate: the ref would be
referentially sound and semantically wrong. That is why every one of the 105
applied resolutions carries its specific textual evidence in
`docs/reports/source-refs-semantic-review.json` (not a bulk pattern
application), and why the 33 unresolved cases were left alone rather than
forced. PR 3 was low-risk (mechanically derived, invariant-checked). PR 4 is
a decision, not a change.

**Regenerating `learning_data.js`** is required after each content PR;
`check_generated_freshness.py` already gates this.
