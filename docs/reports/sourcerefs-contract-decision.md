# sourceRefs canonical contract: decision record

**Status: contract defined and validated. No data migration in this
document** - the mechanical and judgment-required repairs this contract
enables are separate, later PRs (Phase 2, Steps 4). This is Phase 2B of
`docs/platform-closure-plan.md`.

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

## Stop conditions that did not trigger

No `sourceType` was invented (the check that would catch this,
`OBJECT_SOURCETYPE_INVALID`, finds zero violations against real data - it
was added prospectively). No segment id and Vilna line were treated as
interchangeable (containment, not equality, is what the validator has
always checked, and this document now states it as contract rather than
implementation detail). No validator was weakened; `OBJECT_SOURCETYPE_INVALID`
is a strictly new, additive check.
