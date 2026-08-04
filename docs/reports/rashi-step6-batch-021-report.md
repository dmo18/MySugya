# Rashi translation-quality campaign, Step 6 batch 021 report

Batch `step6-batch-021` of the full-corpus review defined in
`docs/reports/rashi-full-corpus-review-strategy.md` (Step 5). Selected as
the next batch per the strategy document's recommended order (position 9,
systemic-candidate-dense priority group; prioritization only, not evidence
of defect). Full per-entry evidence lives in
`docs/reports/data/rashi-step6-batch-021-review-records.json` (validated
against the Step 5 contract).

## Batch scope (frozen from the committed batch plan, unmodified)

- **Batch id**: `step6-batch-021`
- **Perek**: 5
- **Daf**: 48a, 48b, 49a, 49b, 50a, 50b (6 daf)
- **Tier**: `normal`
- **Entries**: 289
- **Risk-tier counts** (Step 2 automated triage, advisory only): high 0, medium 31, zero-risk 258
- **Historical-provenance counts** (Step 1): `content-reviewed` 289
- **Estimated changed count** (Step 5 projection): 31.8

Re-generated and re-validated (`generate_rashi_batch_progress.py`,
`generate_rashi_translation_inventory.py --check`) at the start of this
batch against current main to confirm the batch manifest entry is
unmodified and still selects exactly these 289 entries, that all 289 were
still UNREVIEWED, and that they were assigned only to `step6-batch-021`
(0 overlap with any other batch). A fresh review packet
(`generate_rashi_review_packets.py --batch-id step6-batch-021`) was
generated and used as the basis for review. No entry outside the batch
was edited.

## Single PR (under the change-count cap)

The confirmed changed count (34) is under the 40-changes-per-PR limit
despite this being the largest batch entry-count-wise so far this
session, so it is applied as a single PR covering only the two daf that
actually carry changes (50a, 50b) - the third consecutive Step 6 batch
this session (after `step6-batch-022` and `step6-batch-004`) not to
require a multi-child split.

## Method

Every entry was reviewed against its own Hebrew, its linked Gemara/Mishnah
context, neighboring Rashi entries (required wherever a Vilna line ends
mid-clause or mid-comment), the style guide, and the terminology registry -
never from the existing English alone. Risk scores and systemic-candidate
membership were treated as advisory only.

**First pass**: all 289 entries reviewed individually. Result: 255
VERIFIED, 34 MINOR_EDIT, 0 SUBSTANTIVE_REPAIR, 0 RETRANSLATE, 0
DUPLICATION_OR_CONTAMINATION, 0 BLOCKED.

**Second pass**: 100% of the 34 MINOR_EDIT entries independently
re-reviewed (re-derived from Hebrew and context again). Result: **34/34
CONFIRMED**, 0 MODIFIED, 0 REJECTED, 0 REMAINED_BLOCKED.

**Blind QA**: a deterministic 12.9% sample (33 of the 255 provisionally
VERIFIED entries, selected two ways fixed before any evidence text was
read: every 9th entry in canonical batch order, plus the first
risk-signaled VERIFIED entry per daf not already captured by that rule -
covering all 6 daf and both risk-signaled and zero-risk entries). Result:
**33/33 CONFIRMED_VERIFIED, 0 escalations.** No expansion of the sample
was required.

## Systemic-candidate review

### Family 1: fabricated "New comment:" scaffold text, plus three newly observed label synonyms

31 of this batch's 289 entries (10.7%) carry the base "New comment:"
defect, the same dominant pattern already confirmed in batches 040, 041,
039, 005, 038, 037, 022, and 004. All 31 occur on 50a and 50b; none occur
on 48a, 48b, 49a, or 49b.

**Wording-variant handling**: this batch contains three previously-unseen
fabricated-label synonyms, each found by a corpus-wide check (confirming
exactly one occurrence corpus-wide in every case) before deciding on a
fix:

- **`"New difficulty:"`** - one occurrence, `rashi-yoma-050a-003`. Hebrew
  `"קושיא הוא"` ('it is a difficulty') is genuine content, already
  correctly rendered later in the same sentence via `"- this is a
  difficulty, for it is written"`; the prepended `"New difficulty:"`
  label immediately before the quoted lemma has no Hebrew basis at that
  position (same class of defect as the base "New comment:" family, with
  "difficulty" substituted for "comment"). Fix: removed entirely, same
  treatment as the base family.
- **`"Rashi's textual note:"`** - one occurrence, `rashi-yoma-050a-040`.
  Hebrew ends `"ה"ג והתניא"` (`ה"ג` = הכי גרסינן, 'this is the correct
  reading', followed by the quoted continuation), matching the corpus's
  established convention for reading-confirmation notes (cf. 37a L66,
  42a L3, 57b L35, 74b L34, 80a L60/62, and the `"Textual note:"` /
  `"New comment, textual note:"` synonyms already fixed in step6-batch-037
  and step6-batch-022). The label is followed by an unquoted descriptive
  clause (`"the correct reading is 'but it was taught:"`), not a bare
  quoted lemma, so per the established convention the first letter is
  capitalized after removal: `"The correct reading is 'but it was
  taught:"`.
- **`"Proof-text:"`** - one occurrence, `rashi-yoma-050b-037`. Hebrew
  `"וקרבן יחיד הוא ויצף הברזל (מ"ב ו)"` has no colon or other marker
  before the quoted biblical citation `"ויצף הברזל"` ('and the iron
  floated', II Kings 6) - Rashi cites the prooftext directly, with no
  separate introductory label. Fix: removed entirely, letting the quoted
  citation begin directly, same treatment as the base family.

A broader scan for other capitalized-word-colon patterns turned up two
false positives, checked and confirmed non-defective: `"Alternatively:"`
(`rashi-yoma-048b-002`) faithfully renders the genuine Hebrew `"לשון
אחר"` ('another version/wording'), and `"Yochanan:"`
(`rashi-yoma-050b-009`) is simply the tail end of a rabbi's name split
across the entry boundary (`"...Rabbi Abahu said in the name of Rabbi
Yochanan:..."`), not a scaffold label.

None of the three new synonyms is common enough corpus-wide to warrant a
new named systemic family (per the directive's instruction not to create
new families); each is recorded here as an advisory note and folded into
the existing scaffold-removal disposition.

**Disposition for all 34: CONFIRMED_DEFECT.** Fix: remove the fabricated
label(s) (capitalizing the following word only where it introduces an
unquoted descriptive sentence, per `rashi-yoma-050a-040`'s note above)
and let the next quoted lemma or sentence begin directly, per the
corpus's own established convention - verified individually for every
occurrence that the remaining text, once joined, is grammatically
coherent and semantically unchanged. MINOR_EDIT, defect tag
`INVENTED_TEXT`.

No new systemic family was created for this PR.

### Family 2: cross-entry word anticipation

5 candidates in this batch, all daf-boundary single-word/marker stubs
(`rashi-yoma-048b-026`, `rashi-yoma-049a-064`, `rashi-yoma-049b-021`,
`rashi-yoma-050a-069`, `rashi-yoma-050b-067`). **Disposition:
FALSE_POSITIVE for all 5.** Same low-precision OVEREXPLAINED length-ratio
trigger already confirmed in batches 040, 041, 039, 005, 038, 037, 022,
and 004. `rashi-yoma-048b-026`'s Hebrew is the bare word `"זר"`
('a non-priest'), rendered as the bare quoted catchword `"'A
non-priest'"` with no continuation annotation at all - confirmed against
the corpus (49a's actual opening comment begins `"'A non-priest, a
mourner, a drunkard, and one with a blemish' - ..."`, matching exactly) as
yet another accepted phrasing template for this family (alongside the
"(continues on X)" and "is the catchword anticipating X's opening
comment" templates already seen in prior batches). Left unchanged,
VERIFIED.

## Other risk-signaled entries (outside both systemic families)

23 additional medium-risk entries (3 of which overlap with the scaffold
family above and are resolved by that fix) were flagged by Step 2's
automated triage (`TRUNCATED`, `PUNCTUATION`, `FRAGMENT`,
`CONTEXT_MISMATCH`) but fall outside both authorized systemic-candidate
families. All confirmed **FALSE_POSITIVE** for their respective signals:
this corpus splits Rashi comments across Vilna-line entries, so a line
ending mid-clause is the normal, correct shape of a continuing entry -
confirmed in every case by reading the immediately following vilnaLine
entry, which completes the clause. The one `CONTEXT_MISMATCH` signal
(`rashi-yoma-050a-041`) is explained by Rashi directly quoting the same
baraita phrase the linked Gemara line's own English translates, not by a
copied Gemara translation - confirmed by comparing both texts side by
side. All are VERIFIED.

## Aggregate results (289 entries)

| Disposition | Count | Rate |
|---|---|---|
| VERIFIED | 255 | 88.2% |
| MINOR_EDIT | 34 | 11.8% |
| SUBSTANTIVE_REPAIR | 0 | 0.0% |
| RETRANSLATE | 0 | 0.0% |
| DUPLICATION_OR_CONTAMINATION | 0 | 0.0% |
| BLOCKED | 0 | 0.0% |
| **Total** | **289** | **100%** |

**Changed-translation count: 34** (English to be applied in this single
PR). Second-pass results: 34/34 CONFIRMED. Defect-tag totals:
`INVENTED_TEXT` 34 (31 from the base "New comment:" scaffold family,
plus the three newly observed synonym instances: "New difficulty:",
"Rashi's textual note:", and "Proof-text:").

No BLOCKED entries and no structural/source-cache blockers were found
anywhere in this batch.

## Regression and platform evidence

- Rashi entry count: 8,854 (unchanged) - Associations: 10,061 declared, 0
  broken, 0 cross-daf (unchanged) - Boundary registry: 20/20 (unchanged)
- Hebrew text: byte-unchanged across all 289 entries in this batch
- `npm run validate:offline:yoma`, `npm test`, `npm run test:browser`,
  `npm run build`, `npm run check:deploy-html`, `python3
  scripts/worker_pipeline.py verify --full`: all green

## Status

**Batch 021: COMPLETE.** All 289 entries reviewed with an assigned final
disposition, applied in a single PR; 0 entries left in an ambiguous
state; 0 BLOCKED. Final disposition totals: 255 VERIFIED, 34 MINOR_EDIT,
0 SUBSTANTIVE_REPAIR, 0 RETRANSLATE, 0 DUPLICATION_OR_CONTAMINATION, 0
BLOCKED. Changed-translation count: 34 (all `INVENTED_TEXT`). Second
pass: 34/34 CONFIRMED. Blind QA: 33/33 CONFIRMED_VERIFIED, 0
escalations. Both authorized systemic-candidate families resolved
(scaffold: 34 CONFIRMED_DEFECT, applied; anticipation: 5 FALSE_POSITIVE,
unchanged).

This is the 10th parent batch completed this session (001, 040, 041,
039, 005, 038, 037, 022, 004, 021), triggering the every-5-completed
-parent-batches checkpoint per the campaign directive.
