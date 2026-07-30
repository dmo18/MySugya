# Cross-daf sourceRefs schema: decision record

**Status: schema defined, validated and tested. No data migration in this
document or this PR** - applying it to the two proven cases is Step 4 of
the current campaign, a separate, bounded, later PR. This is Step 3 of
the sourceRefs Phase 2B campaign (`docs/platform-closure-plan.md`).

## Why a third shape, and why not reuse Rashi's same-daf convention

`docs/reports/sourcerefs-blocker-classifications.json` (Step 2 of this
campaign) originally classified 4 of the 33 residual sourceRefs defects as
`QUALIFIED_CROSS_DAF`: cases where a step's declared content has an exact,
textually-confirmed match on a *different* daf than the one it lives on.
Yoma's Rashi-association layer already has a strict same-daf rule (a
Rashi comment may only link to Gemara/Mishnah lines on its own daf), and
it would be the path of least effort to reuse that convention here. This
campaign's operator decision was explicit that this must not happen:
Rashi's same-daf rule exists because a Rashi comment is *physically
printed* next to the daf it comments on, a constraint that has nothing to
do with what a sourceRefs citation is doing (pointing at where a step's
content is actually stated). Importing Rashi's rule would either force a
false same-daf lie onto these refs, or silently loosen Rashi's rule for
an unrelated reason. Neither is acceptable, so this is a new,
independently-designed representation.

## Re-proving the 4 candidate cases (Step 3's required first task)

Before designing anything, each of the 4 `QUALIFIED_CROSS_DAF` candidates
was re-examined against the specific failure modes Step 3 requires ruling
out: a misplaced step, a mislabeled sugya boundary, a stale import
artifact, a duplicated step, or a summary statement rather than a direct
citation. This re-proof found a real error in the Step 2 classification -
exactly the kind of finding Step 3 exists to catch:

### Confirmed genuine (2 of 4)

- **`yoma-069b-l19`** ("After the readings, the HP recited eight
  blessings: on Torah, service, thanksgiving, forgiveness, Temple,
  priests, Israel, and Jerusalem") -> **`yoma-070a-l16`**. `yoma-070a-l16`
  reads (in full): "And the High Priest recites eight blessings after the
  reading... on Torah... on the service... on the thanksgiving... on the
  forgiveness of sin... on the Temple by itself... on the priests by
  themselves... on Israel by themselves... and on the rest of the
  prayer" - an exact, itemized match. The owning sugya, `yoma-069b-s03`,
  is not misplaced or mislabeled: its own display text says "The eight
  blessings that followed are listed," and its other two steps
  (`yoma-069b-l17`, `yoma-069b-l18`) correctly cite real same-daf lines
  (`yoma-069b-l43`, `yoma-069b-l44`) within the sugya's own declared Vilna
  range (43-48). Only this one step's true content lives one daf later.
  `yoma-070a-l16` itself is not already the correct target of any step in
  its own sugya (`yoma-070a-s04`): that sugya's own two steps either have
  a dangling self-referential ref or a semantically mismatched one (see
  "New finding" below), so this line is unclaimed and free to cite
  correctly for the first time.
- **`yoma-069b-l21`** ("An additional prayer for general needs:
  supplication and petition before God for His people Israel who need
  salvation") -> **`yoma-070a-l22`**. `yoma-070a-l22` reads: "the rest of
  the prayer is: song, supplication, petition before You for Your people
  Israel who need to be saved" - an exact match. Same sugya
  (`yoma-069b-s03`), same reasoning as above.

### Reclassified after re-proof (2 of 4)

- **`yoma-071a-l15`** and **`yoma-071a-l19`** (the Shemaiah/Avtalyon
  farewell narrative and its ona'at-devarim characterization) were
  originally proposed to cite `yoma-071b-l06`, which does contain matching
  text. But re-reading the full sugya this line belongs to
  (`yoma-071b-s02`) found that sugya is *already* a complete, correctly
  self-anchored telling of this exact story: its own `display.whats`
  states "The people followed Shemaiah and Avtalyon (not the HP) as they
  left the Temple... The incident concludes with a teaching about ona'at
  devarim," and its two steps (`yoma-071b-l02`, `yoma-071b-l03`) already
  correctly cite `yoma-071b-l02` and `yoma-071b-l06` respectively. The two
  71a steps are **duplicated steps** of content that already has a
  complete, correctly-anchored home on 71b - precisely the failure mode
  Step 3 was designed to catch, not a case where "the local step is the
  genuine expression of a fact that must be cited from elsewhere." These
  two cases are corrected in `docs/reports/sourcerefs-blocker-classifications.json`
  from `QUALIFIED_CROSS_DAF` to `ABSENT_OR_UNANCHORED` in this same PR
  (a Step 2 output correction discovered by Step 3's own required
  re-proof pass, not new data analysis) - see that file for the full
  corrected evidence.

**Net result: 2 confirmed `QUALIFIED_CROSS_DAF` cases, both targeting the
same sugya (`yoma-070a-s04`) from the same owning sugya (`yoma-069b-s03`).
2 cases move to `ABSENT_OR_UNANCHORED`. The blocker table totals are now
2 `QUALIFIED_CROSS_DAF`, 29 `ABSENT_OR_UNANCHORED`, 2 `TIED_CANDIDATES`.**

### New finding, out of scope

While re-proving `yoma-070a-l16`/`yoma-070a-l22`, their own owning sugya
(`yoma-070a-s04`) turned out to have its own, different problem: its
`display.whats` describes a *third* topic ("The HP prostrated himself
eight times") that matches neither line's real content, and its own two
steps either fail to resolve (`yoma-070a-l07`, self-referential lineId)
or resolve to the right coordinate with the wrong explanatory text
(`yoma-070a-l08`, correctly resolves to `yoma-070a-l22` but describes an
unrelated "do not pass over commandments" principle). This is a
structurally-valid-but-semantically-wrong ref, a category the 33-case
review did not check for (it only reviewed the 33 mechanically-flagged
defects) and outside this campaign's scope to fix - flagged here for a
future content-scoping audit, alongside the `yoma-048b-s02` and
`yoma-066b-s03` findings from Step 2.

## The schema

```
sourceRefs[i] is ONE OF:

  same-daf object   { sourceType, lineId, vilnaLine, note? }
  string form       "Yoma.<daf>.<segment>"
  cross-daf object  { refType: "crossDaf", targetDaf, targetLineId,
                      targetVilnaLine?, sourceType?, note? }
```

The illustrative shape the operator directive sketched
(`{"lineId": "yoma-12b-l07", "daf": "12b", "vilnaLine": 7, "scope":
"cross-daf"}`) was explicitly not to be used blindly, and is not used
here. Two changes from that sketch, both required by the operator's own
design constraints:

- **No bare `lineId`/`vilnaLine` keys.** The sketch's shape differs from
  the same-daf object only by an added `daf`/`scope` field - a reader (or
  a future validator/renderer change) skimming for `ref.lineId` would
  silently treat a cross-daf ref as same-daf, using `vilnaLine`'s
  same-daf containment check against the *wrong* daf's anchor table. The
  actual schema uses `targetLineId`/`targetVilnaLine`, keys that do not
  exist on the same-daf shape at all, so no code path can confuse the two
  shapes by accident. `refType: "crossDaf"` is the explicit discriminator
  a validator or renderer switches on, checked first and rejected outright
  (`OBJECT_REFTYPE_INVALID`) if present with any other value - an
  unrecognised `refType` is never silently treated as same-daf either.
- **`targetDaf` is redundant with `targetLineId`'s own embedded daf token
  by design, not by accident.** `yoma-070a-l16` already encodes daf `70a`
  in its own id. `targetDaf` is required anyway (not left to be derived by
  string-parsing the id) so a validator can check the two agree
  (`CROSSDAF_TARGET_DAF_MISMATCH` if they don't) rather than trusting a
  string convention with no independent check.

Tractate-agnostic: no field name assumes "yoma" or any tractate-specific
vocabulary. `sourceType` is optional (unlike the same-daf shape, where an
object ref must carry a legal `sourceType` value) because a cross-daf case
may prove exact segment identity (this is what the Step 2/3 evidence
proves) without independently proving source kind; when it is present, it
is validated against the same `LEGAL_SOURCE_TYPES` set as the same-daf
shape, no separate vocabulary.

## Validation added (`modules/yoma/scripts/validate_source_refs.py`)

`classify_daf` now takes an optional third argument, `global_anchors`: a
per-daf anchor table for the whole corpus, from the new
`build_global_anchors(paths)`. `run(paths)` builds it once and passes it
to every daf's classification, so a cross-daf ref's target can be checked
against its *actual* daf's real geometry, not just the current daf's.
Direct callers that only have one daf's data (existing tests) get a
single-daf fallback table automatically, so no existing call site needed
to change.

An object ref carrying `refType` is validated through a new path, entirely
before the existing same-daf logic (which is otherwise unchanged):

| check | class on failure |
|---|---|
| `refType` present but not exactly `"crossDaf"` | `OBJECT_REFTYPE_INVALID` |
| `targetDaf` or `targetLineId` missing | `CROSSDAF_MALFORMED` |
| `targetDaf` equals the ref's own owning daf | `CROSSDAF_SAME_DAF_MISLABELED` |
| `targetLineId`'s own embedded daf token disagrees with `targetDaf` | `CROSSDAF_TARGET_DAF_MISMATCH` |
| `targetLineId` does not exist on any daf in the corpus | `CROSSDAF_TARGET_NOT_FOUND` |
| `targetLineId` exists, but on a daf other than the claimed `targetDaf` | `CROSSDAF_TARGET_DAF_MISMATCH` |
| `targetVilnaLine` present but outside `targetLineId`'s real Vilna interval on its own daf | `CROSSDAF_VILNA_MISMATCH` |
| `sourceType` present but not in `LEGAL_SOURCE_TYPES` | `OBJECT_SOURCETYPE_INVALID` (reused; same semantic check as same-daf) |
| all pass | `OK_CROSSDAF` (sound, not a defect - added alongside `OK`/`STRING_RESOLVABLE` everywhere the report distinguishes sound from unsound) |

All eight new classes (`OBJECT_REFTYPE_INVALID`, five `CROSSDAF_*`
classes) are added to `DEFECT_CLASSES` so `--strict` gates on them like
any other defect. `OK_CROSSDAF` is added to the sound-total computation
and the report's "sound" mark, and excluded from `findings` the same way
`OK` is, so it does not inflate defect-oriented counts or the "daf
carrying defects" line fixed in the previous PR.

Every check above is additive to the existing contract, not a
replacement: a same-daf ref (no `refType` key) is classified by the exact
same code path as before this PR, byte-for-byte. `OBJECT_SOURCETYPE_INVALID`
is reused rather than duplicated, since the underlying rule (a present
`sourceType` must be legal) is identical for both shapes.

## Tests added (`modules/yoma/scripts/test_validate_source_refs.py`)

A new `crossDaf object refs` section, using a new `classes_multi` helper
that builds a synthetic multi-daf global anchor table (existing tests use
single-daf synthetic fixtures, insufficient for cross-daf cases by
construction):

- valid adjacent-daf reference resolves as sound (`OK_CROSSDAF`)
- valid non-adjacent cross-daf reference is equally sound (the schema
  does not special-case distance)
- missing target line id (`CROSSDAF_TARGET_NOT_FOUND`)
- `targetDaf` disagreeing with the target id's own embedded daf token
  (`CROSSDAF_TARGET_DAF_MISMATCH`)
- a same-daf target mislabeled `crossDaf` is caught, not silently accepted
  (`CROSSDAF_SAME_DAF_MISLABELED`)
- `targetVilnaLine` outside the real interval (`CROSSDAF_VILNA_MISMATCH`),
  asserting the reported candidate list is correct
- an unsupported `sourceType` is rejected (`OBJECT_SOURCETYPE_INVALID`),
  proving the same rule applies to both shapes
- a `crossDaf` ref may omit `sourceType` entirely and still be sound -
  the one deliberate difference from the same-daf shape
- an unrecognised `refType` value is its own distinct defect
  (`OBJECT_REFTYPE_INVALID`), never silently treated as same-daf
- a malformed `crossDaf` ref missing `targetLineId` (`CROSSDAF_MALFORMED`)

The pre-existing corpus-level invariant "no ref escapes classification"
was extended to include `OK_CROSSDAF` in its total, so it stays correct
once Step 4 actually introduces cross-daf refs into the corpus (today it
is 0, so the change has no visible effect yet, but the invariant would
have silently stopped verifying totals correctly the moment a real
cross-daf ref existed without this fix).

## What this PR does not do

It does not change any `*.learning.json` file, `learning_data.js`, or any
sourceRef. The 2 confirmed cases are not migrated to the new shape here;
Step 4 applies that migration in a separate, bounded, `structural-repair`
PR, following this exact schema and re-running these exact validators
against the real data after the change.

## Stop conditions that did not trigger

No `sourceType` was invented (both confirmed cases' targets are `gemara`-
kind lines, matching evidence already established; the cross-daf schema
makes `sourceType` optional precisely so a future case without that
evidence is never tempted to guess one). No segment id and Vilna line
were treated as interchangeable (the cross-daf containment check mirrors
the same-daf rule exactly: interval containment on the target's own daf,
never equality). No step was moved daf, and no source content was moved
between daf - the two confirmed cases keep their steps exactly where they
are; only the outbound reference changes shape in Step 4. No validator
was weakened - every new check is additive, and the two reclassified
cases move to a *more* conservative outcome (`ABSENT_OR_UNANCHORED`, no
sourceRef at all), never a *less* conservative one. Phase 3 was not
started.
