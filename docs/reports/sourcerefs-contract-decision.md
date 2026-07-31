# sourceRefs canonical contract: decision record

**Status: contract defined and validated; Phase 2B is now COMPLETE** (see
the closing update below). No data migration is recorded in this
document itself - the mechanical and judgment-required repairs this
contract enables were applied in separate, later PRs. This is Phase 2B of
`docs/platform-closure-plan.md`.

**Update: a third shape was added later in the same campaign.** The union
below was the original decision (same-daf object vs. legacy string). A
narrower, individually-proven third shape - a cross-daf object, for the
specific case where a step's true source lives on a different daf than
its own - was added afterward; see
`docs/reports/sourcerefs-crossdaf-schema-decision.md` for its full
rationale, schema, and the two confirmed cases it applies to. The
reasoning below (why string form is not inferior, why sourceType cannot
be synthesized) is unaffected and still governs the same-daf/string
choice; it does not need to be reread through the cross-daf lens.

**Closing update, VERSION 15.376 (PR #369): Phase 2B is complete.** The
last 2 of the original 33 residual refs - `yoma-044b-l01` and
`yoma-063a-l03a`, both classified `TIED_CANDIDATES` in
`docs/reports/sourcerefs-blocker-classifications.json` - were resolved in
a final, tightly scoped re-adjudication using repository evidence the
prior five-way classification pass had not fully exploited (the
already-legal multi-ref step shape for `yoma-044b-l01`; the step's own
`speaker` field for `yoma-063a-l03a`). `validate_source_refs.py --strict`
now reports **0 defects** across all 1,953 refs. No shape defined in this
document changed to make that happen: both repairs use the existing
same-daf object shape, reuse `sourceType: "gemara"` without inventing it,
and the 331 sound string refs are untouched. See
`docs/platform-closure-plan.md`'s Phase 2 section for the full resolution
record and `docs/reports/sourcerefs-blocker-classifications.json` for the
per-case evidence.

## The decision: a discriminated union of exactly two legal shapes

```
sourceRefs[i] is ONE OF:

  object form   { sourceType, lineId, vilnaLine, note? }
  string form   "Yoma.<daf>.<segment>"
```

No other shape is legal. This was chosen over "exact segment-id strings
only" or "structured objects only" because the corpus already contains two
real, independently-legitimate representations, and one of the two chosen
alternatives requires destroying real information:

- **331 string refs are sound as-is.** Every one resolves to exactly one
  local line via that line's `sefariaRef`. Converting them to object form
  would require a `sourceType` value, and `sourceType` is not a function of
  the target line's `kind`: 15 refs elsewhere in the corpus are typed
  `gemara` while resolving to a Mishnah-kind line, an editorial judgment,
  not a mechanical fact. There is no rule that reconstructs the right value
  for a string ref's implied `sourceType`, so converting these 331 would
  mean inventing data the contract forbids inventing. Forcing "structured
  objects only" would require exactly that invention.
- **1,650 object refs already carry real evidence** (`sourceType`, `lineId`,
  `vilnaLine`, sometimes `note`) that a string can't express. Forcing
  "exact segment-id strings only" would discard `sourceType` and `note` for
  every one of them, for zero gain.

A discriminated union is the only shape that doesn't require destroying one
side's real information to satisfy uniformity.

## Segment identity vs. Vilna location: never compared as equal

This is the fact that the entire validator is built around, and getting it
wrong is what makes a naive schema unsafe.

A line id is minted only where a Sefaria segment starts, so line ids are
**coarser** than Vilna line numbering: one line id covers a half-open Vilna
interval `[start, next-start)`. A sound ref's `lineId` names the
**containing segment**; its `vilnaLine` names the **precise Vilna line**
inside that segment - the two coordinates are *supposed* to disagree
numerically. On Yoma 2a, `{lineId: "yoma-002a-l04", vilnaLine: 6}` is
correct: the segment anchored at Vilna line 4 contains Vilna line 6.

The contract's validity rule is therefore **interval containment**, never
numeric equality: `lineId` must exist on the ref's own daf, and `vilnaLine`
must fall inside that `lineId`'s Vilna interval. A validator built on
equality instead reports roughly 500 false positives on this corpus and
licenses "repairs" that silently move real anchors - this was the actual
defect found and corrected in the earlier sourceRefs analysis
(`docs/reports/source-refs-normalization-plan.md`), and this contract
document exists partly to make that distinction impossible to relitigate
by accident.

## sourceType: a controlled vocabulary, including an explicit unknown state

`sourceType` on an object ref must be one of `LEGAL_SOURCE_TYPES` =
`{"gemara", "mishnah", "unknown"}`, enforced by
`validate_source_refs.py`'s `OBJECT_SOURCETYPE_INVALID` check.

`"unknown"` is a legal value **no ref in the corpus currently uses**. It
exists so that a future repair which establishes exact segment identity
with certainty, but cannot establish source kind from repository evidence,
has a truthful value to write instead of being forced to guess `"gemara"`
or `"mishnah"`. This is the concrete form of "represent unresolved
provenance truthfully rather than guessing" - a contract requirement that
would otherwise have no way to be honored, since every currently-defective
ref already carries a `sourceType` value (the defect is always in `lineId`,
never in `sourceType`, for the 550 defects catalogued in the normalization
plan). Declaring the state now, before any repair needs it, means a future
repair PR is never tempted to invent a value merely because the schema
seems to demand one.

## Validation added

Extended `validate_source_refs.py` (not a new parallel validator - one
interpretation of the contract, not two) with `OBJECT_SOURCETYPE_INVALID`:
an object ref whose geometry (lineId + vilnaLine containment) is otherwise
sound but whose `sourceType` is outside the legal set. Checked only when
geometry is sound, so a geometrically broken ref is never double-counted.

Combined with the pre-existing checks, the full contract surface is now
covered:

| requirement | check |
|---|---|
| resolvable exact segment ids | `OBJECT_DANGLING_*` classes, `STRING_*` classes |
| correct daf locality | `STRING_CROSS_DAF` |
| valid source kind when present | `OBJECT_SOURCETYPE_INVALID` (new) |
| segment/Vilna separation (containment, not equality) | core geometry check |
| ordering, duplicates | unaffected by this contract; corpus order is preserved by construction since no ref is reordered |
| malformed object shapes | `REF_NOT_STRING_OR_OBJECT` |
| generated/source parity | `verify_line_id_derivation()`, reproduces all 2,300 built line ids |

Three new unit tests in `test_validate_source_refs.py` exercise the new
check: an illegal `sourceType` is flagged even with otherwise-sound
geometry, `"mishnah"` passes, and the contract's own `"unknown"` value
passes. The full corpus re-run confirms **zero** `OBJECT_SOURCETYPE_INVALID`
findings today - this is a new capability, not a currently-active gate.

## What this contract does not do

It does not repair anything. The 550 defective refs catalogued in
`docs/reports/source-refs-normalization-plan.md` (412 mechanically
repairable, 138 needing a human reading the step text against the Gemara)
are untouched by this PR. This document defines the target shape and the
validator that recognizes it; Phase 2 Step 4 applies the mechanical repairs
and processes the judgment-required cases against this exact contract, in
separate, bounded PRs.

## Future-tractate implications

A new tractate authoring `sourceRefs` should use the object form from the
start (`docs/new-tractate-onboarding.md` already says this). The string
form remains legal only as this tractate's historical accommodation; there
is no reason for a new tractate to introduce new string-form refs, and the
onboarding checklist does not invite it to.

## The 331 string refs: conversion decided, not required

This question was tracked as an open operator decision (PR 4 in
`docs/reports/source-refs-normalization-plan.md`). It is now closed:
**the 331 sound string refs are not converted, and no future migration may
convert them by guessing metadata.**

- String form is not a legacy shape awaiting cleanup toward object form. It
  is a first-class, permanent member of the canonical union, correct
  whenever exact segment identity is known but no additional field
  (`sourceType`, `note`) is independently evidenced.
- Object form is not inherently better than string form. It is correct only
  when every field it carries is independently supported; a structured
  shape holding a guessed `sourceType` is worse data than a string holding
  none, not better data in a nicer shape.
- Validators accept both forms today (`STRING_RESOLVABLE` and `OK` are both
  sound classes in `validate_source_refs.py`) and must continue to; renderer
  and generated-data consumers must keep handling both forms deterministically.
- No future PR may convert a string ref to object form by inferring
  `sourceType` from the target line's `kind`, from numeric coincidence, or
  from any other correlation. The only legitimate path from string to object
  form is discovering independent, documented evidence for every object
  field the conversion would add - at which point it is not a uniformity
  migration, it is a normal repair to a specific ref.

## `mishnah` vs `mishna`: not the same field, no unification

Also raised as part of PR 4. Investigated corpus-wide; the two spellings
belong to three distinct, independently-canonical vocabularies, not one
inconsistent field:

| field | spelling | occurrences | scope |
|---|---|---|---|
| `sourceRefs[].sourceType` (`LEGAL_SOURCE_TYPES`) | `mishnah` | 3 | this contract |
| source line `kind` (`controlledValues.lineKind`, `shared/schema_map.js`) | `mishna` | thousands, every daf | frozen Yoma corpus |
| `argumentFlow[].type` (free text, outside the canonical step-type vocabulary) | `mishna` | 1 (14a, `yoma-14a-s02`/`step-01`) | Phase 2A argumentFlow-vocabulary backlog |

None of the three is a misspelling of another; each is its own field's sole
value and already internally consistent. Unifying any pair would mean
renaming a field that is not broken - for `kind`, it would mean editing
frozen Yoma corpus data for zero functional gain. No normalization is
warranted, and none is performed here.

## Stop conditions that did not trigger

No `sourceType` was invented (the check that would catch this,
`OBJECT_SOURCETYPE_INVALID`, finds zero violations against real data - it
was added prospectively). No segment id and Vilna line were treated as
interchangeable (containment, not equality, is what the validator has
always checked, and this document now states it as contract rather than
implementation detail). No validator was weakened; `OBJECT_SOURCETYPE_INVALID`
is a strictly new, additive check.
