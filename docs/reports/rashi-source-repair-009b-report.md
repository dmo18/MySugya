# Rashi source-repair report: `rashi-yoma-009b-001`

Step 6 PR A of the Rashi translation-quality campaign (see
`docs/reports/rashi-full-corpus-review-strategy.md` for Step 5's evidence
record and recommendation, `docs/reports/data/rashi-source-blockers.json`
for the machine-readable evidence record this report accompanies). This
is the dedicated source-repair evidence report the campaign's own stop
condition required before touching a Hebrew-source cache file: **the only
file this campaign edit touches under `modules/yoma/assets/talmuddev/`
is `9b.json`, and the only value inside it that changes is `rashi[0]`.**

## The defect

`modules/yoma/assets/talmuddev/9b.json`'s `rashi[0]` (the Hebrew source
for `rashi-yoma-009b-001`, daf 9b, vilnaLine 1) began with a leaked HTML
fragment:

```
span class="five">ששהו את קיניהן. שהיו מביאות במלאות ימי לידתן ליטהר לאכול בקדשים והם היו בעלי גיאות והיו מתרשלין בהקרבתן והנשים
```

The literal text `span class="five">` (19 characters) was prefixed
directly onto the real Hebrew, with no separator. It is missing only the
opening `<` of what should have been `<span class="five">`; the rest of
the tag is intact.

Found during Step 4 batch 1 (2026), recorded `BLOCKED` (a structural stop,
Hebrew is immutable baseline - never translation-edited). Confirmed
isolated at that time: a corpus-wide scan of all 8,854 `he` fields found
exactly this one occurrence.

## Reconfirmation (this PR, three independent sources)

Per this PR's own explicit instruction not to guess and to reconfirm
against the strongest available evidence, three independent checks were
performed - not merely a re-citation of Step 5's prior findings:

1. **Local static analysis** (Step 5, re-verified): the stored value's
   exact corruption, traced through the ingestion pipeline (below).
2. **Fresh live re-fetch of `talmud.dev`'s current API**
   (`https://www.talmud.dev/api/daf/Yoma/9b`, performed during this PR):
   the identical defect is still present in talmud.dev's own raw data -
   the first `\r\n`-delimited line of `rashi.hebrew` reads `span
   class="five">ששהו את קיניהן. </span>שהיו מביאות...`, missing the same
   opening `<` in the exact same place. The very next line's
   `<span class="five">מהשתרע.</span>...` is well-formed, confirming this
   is a single missing character upstream, not a systemic defect.
3. **Independent second authoritative source** (Sefaria API, Vilna
   Edition, `Rashi_on_Yoma.9b.1`,
   `https://www.sefaria.org/api/texts/Rashi_on_Yoma.9b.1`): returned
   `ששהו את קיניהן - שהיו מביאות במלאות ימי לידתן ליטהר לאכול בקדשים והם
   היו בעלי גיאות והיו מתרשלין בהקרבתן והנשים ממתינות שם...` - matching
   the corrected text exactly, from a source independent of talmud.dev
   entirely.

Mechanical proof: applying the ingestion script's own `strip_html()`
regex (`re.sub(r"<[^>]+>", "", s)`) to the live-fetched raw line, with its
missing `<` restored, produces a string byte-identical to removing the
19-character artifact from the stored value:

```python
>>> strip_html('<span class="five">ששהו את קיניהן. </span>שהיו מביאות...')
'ששהו את קיניהן. שהיו מביאות...'
```

This is not an invented correction - it is the ingestion pipeline's own
already-proven rule (used successfully on the other 40 lines of this same
file) applied to the one line where a missing upstream `<` defeated it.

## Where the corruption entered

Traced end to end:

1. `scripts/fetch_talmuddev.py` fetches `https://www.talmud.dev/api/daf/Yoma/9b`
   and reads `rashi.hebrew` (one string, `\r\n`-delimited print lines).
2. `split_lines()` splits on `\r\n`, then `strip_html()`
   (`re.sub(r"<[^>]+>", "", s)`) strips tags from each line.
3. `strip_html()`'s regex requires a literal `<` to match anything; a tag
   missing its opening `<` cannot match and passes through unchanged.
4. The resulting line list is written verbatim to
   `modules/yoma/assets/talmuddev/9b.json`'s `rashi` array.
5. `build_learning_data.py`'s `load_rashi_lines()` reads that array
   directly as the `he` field for every Rashi entry on that daf -
   byte-for-byte, no re-parsing.
6. `python3 scripts/build_learning_data.py` writes this value into
   `learning_data.js` as `rashi-yoma-009b-001`'s `he` field.

**Determination: upstream, confirmed via live re-fetch (item 2 above),
not an ingestion-script bug.** Every other tag in the same daf's API
response is well-formed and was correctly stripped, ruling out a
systemic ingestion defect - this is a single missing character in
talmud.dev's own markup, specific to this one line.

## The fix

Narrowest possible correction, applied at the earliest correct canonical
layer (the raw source cache, not a generated output):

- **Old value** (`modules/yoma/assets/talmuddev/9b.json`'s `rashi[0]`):
  `span class="five">ששהו את קיניהן. שהיו מביאות במלאות ימי לידתן ליטהר
  לאכול בקדשים והם היו בעלי גיאות והיו מתרשלין בהקרבתן והנשים`
- **Corrected value**: `ששהו את קיניהן. שהיו מביאות במלאות ימי לידתן
  ליטהר לאכול בקדשים והם היו בעלי גיאות והיו מתרשלין בהקרבתן והנשים`
- **Exact removed artifact**: the literal leading substring `span
  class="five">` (19 characters), nothing else.
- **Canonical file changed**: `modules/yoma/assets/talmuddev/9b.json`,
  confirmed via `git diff` - exactly one line changed in exactly one of
  the 173 talmuddev source files.

## Generated files regenerated

- `modules/yoma/learning_data.js` - `python3 scripts/build_learning_data.py`,
  then `python3 scripts/build_literal_layer.py --apply` (the second step
  is required: the first alone drops the separately-injected `en_lit`
  layer entirely, discovered and corrected during this PR - the resulting
  diff after both steps is exactly one line, `rashi-yoma-009b-001`'s `he`
  field, with `en_lit` coverage unaffected).
- `modules/yoma/coverage.json` - regenerated, confirmed byte-unchanged
  (entry/sugya counts unaffected).
- `docs/reports/data/rashi-translation-quality-inventory.json` - this
  entry's `he`, `primaryDisposition`, and `reviewerEvidence` fields only,
  hand-patched via the campaign's established exact-literal-string-
  substitution editing pattern (never a full regeneration, which would
  reset all 200 pilot entries' review state to `UNREVIEWED`). Freshness
  reconfirmed: `python3 scripts/generate_rashi_translation_inventory.py --check`
  passes.

## Proof no other entry changed

- `git diff --stat` against `origin/main`: exactly one line changed in
  `modules/yoma/assets/talmuddev/9b.json`; exactly one `he` field changed
  in `learning_data.js` (`rashi-yoma-009b-001` only); `coverage.json`
  byte-identical.
- A fresh corpus-wide scan of all 8,854 inventory `he` fields for `span
  class`, `<`, or `>` after the fix found **zero hits** - confirms this
  was the only instance and the fix introduced no new artifact.

## Fresh semantic translation review (post-repair)

The prior `BLOCKED` disposition was a structural stop on the Hebrew, not
a semantic verdict on the English - per the campaign's standing rule, a
repaired Hebrew source still requires a normal, full entry-level review;
the prior status is never carried over automatically.

- **Hebrew read independently** (corrected value, above).
- **Linked Gemara read** (`yoma-009b-l01`): "that they deferred the
  sacrifice of their bird-offerings by women after childbirth;
  nevertheless, the verse ascribes to them as if they lay with them" -
  the Gemara's own English identifies the referent as Eli's sons, who
  delayed sacrificing women's post-childbirth bird-offerings.
- **English compared**: `'That they delayed their bird-offerings' - for
  the women would bring them at the completion of their days of
  childbirth, to be purified so as to eat consecrated food, and they were
  arrogant men and were lax in offering them, and the women` - faithful
  and complete: the dibbur-hamatchil quote convention is correct,
  "arrogant men" is an accurate idiomatic rendering of `בעלי גיאות`
  ("possessors of haughtiness"), "lax" correctly renders `מתרשלין`, and
  the entry correctly stops at "and the women" - matching the Hebrew's
  own line break (the sentence completes in `rashi-yoma-009b-002`,
  confirmed against that neighbor's own English opening, "would wait
  there until they offered them...").
- **Disposition**: **VERIFIED**. No defect found; no English change.
- **Independent second pass**: re-derived from the Hebrew and Gemara
  context a second time, independently (elevated scrutiny warranted for
  a former source-blocker, beyond what a plain `VERIFIED` normally
  requires) - **CONFIRMED**, same conclusion.

## Worker task type used

No existing worker task type authorized touching
`modules/<module>/assets/talmuddev/*` - every Rashi-related type's
`allowedFiles`/`forbiddenFiles` scopes only the enrichment layer
(`rashiTranslations[*].en`/`.linkedGemaraLineIds`) or (for
`rashi-structural-repair`) entry structure, never the raw Hebrew source
cache; `docs-tooling` explicitly forbids it. Per the governing directive's
explicit instruction ("if no task type safely authorizes this change,
stop and report instead of bypassing worker scope"), this was reported to
the user before proceeding. The user selected creating a new, narrowly-
scoped `rashi-source-repair` task type as part of this PR
(`scripts/worker_task_types.json`), authorized only for an isolated,
single-entry, evidence-backed correction to the raw source cache - never
a bulk edit, never a guess, never an ingestion-script change. The manifest
carries the required `sourceRepairEvidence` authorization, satisfied by
this report and the companion evidence record.

## Historical fact preserved

This entry was `BLOCKED` from Step 4 batch 1 until this repair. The
original finding is preserved unchanged in
`docs/reports/rashi-pilot-batch-1-report.md` (with a resolution addendum
appended, not a rewrite) and in
`docs/reports/data/rashi-source-blockers.json`'s `history` array.

## Validation

- `python3 modules/yoma/scripts/generate_rashi_translation_inventory.py --check` - PASS
- `python3 modules/yoma/scripts/validate_rashi.py` - PASS (he/talmud.dev order-and-count)
- `python3 modules/yoma/scripts/audit_rashi_association.py --exhaustive-corpus` - 8,854 entries, 10,061 associations, 0 broken, 0 cross-daf
- `python3 modules/yoma/scripts/validate_rashi_boundary_authorizations.py` - 20 authorized, 20 in corpus, 20/20 matched, 0 stale, 0 duplicate, 0 unauthorized
- `npm run validate:offline:yoma` - PASS
- `npm test` - PASS
- `npm run test:browser` - PASS
- `npm run build` / `npm run check:deploy-html` - PASS
- `python3 scripts/worker_pipeline.py verify --full` - PASS

## Scope

No Gemara, Mishnah, `argumentFlow`, `sourceRefs`, literal, renderer,
module, fixture, workflow, or platform change. No other Rashi English
changed. No association, boundary, or entry-count change. VERSION bumped
once.
