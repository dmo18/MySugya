# Rashi translation-quality campaign, Step 6 batch 001 report

Batch `step6-batch-001` of the full-corpus review defined in
`docs/reports/rashi-full-corpus-review-strategy.md` (Step 5). This is
Step 6 PR B: the first HYBRID REVIEW batch, executed only after PR A
(source repair of `rashi-yoma-009b-001`) merged. Full per-entry evidence
lives in `docs/reports/data/rashi-step6-batch-001-review-records.json`
(validated against the Step 5 contract:
`python3 modules/yoma/scripts/validate_rashi_review_records.py
docs/reports/data/rashi-step6-batch-001-review-records.json --base
origin/main`).

## Batch scope

- **Batch id**: `step6-batch-001`
- **Perek**: 1
- **Daf**: 2a, 2b, 3a, 3b, 4a, 4b (6 daf)
- **Tier**: `normal`
- **Entries**: 274
- **Risk-tier counts** (Step 2 automated triage, advisory only): high 0, medium 20, zero-risk 254
- **Historical-provenance counts** (Step 1): `narrow-fix-only` 54, `content-reviewed` 162, `checked-no-fix-needed` 58
- **Estimated changed count** (Step 5 projection): 30.1 - actual: 15 applied (14 at this batch's own merge, 1 resolved by the follow-up PRs described in the Resolution addendum below)

Selected via the committed batch plan
(`docs/reports/data/rashi-full-corpus-review-batches.json`), re-generated
and re-validated at the start of this PR to confirm it is unaffected by
PR A's Hebrew correction (0 diff - `rashi-yoma-009b-001` was already
`REVIEWED`, never in the UNREVIEWED pool the planner draws from). No
pilot entry included (verified: 0 overlap with the 200 `REVIEWED`
entries). No entry outside the batch was edited.

## Method

Every entry was reviewed against its own Hebrew, its linked Gemara/
Mishnah context, neighboring Rashi entries, the style guide, and the
terminology registry - never from the existing English alone. Risk
scores and historical-provenance flags were treated as advisory only, per
the campaign's standing rule: no entry was marked VERIFIED because its
risk score was zero, because it resembled another entry, because it
belonged to a historically "clean" daf, or because no automated detector
flagged it.

**First pass**: every one of the 274 entries reviewed individually,
split by daf across parallel review passes for tractability at this
scale, each pass genuinely reading Hebrew and Gemara context per entry
(not a heuristic or template). Result: 258 VERIFIED, 8 MINOR_EDIT, 8
SUBSTANTIVE_REPAIR, 0 RETRANSLATE, 0 DUPLICATION_OR_CONTAMINATION, 0
BLOCKED.

**Second pass**: 100% of the 16 first-pass changed/BLOCKED entries
independently re-reviewed (re-derived from Hebrew and Gemara context
again, not merely re-checked against the first pass's own reasoning).
Result: **14 CONFIRMED, 1 REJECTED, 1 REMAINED_BLOCKED**. The rejected
entry, `rashi-yoma-002a-054`, reverted to VERIFIED. The
REMAINED_BLOCKED entry, `rashi-yoma-004b-061`, has a confirmed defect
and a ready fix, but applying it is blocked by an unrelated tooling gate
(a boundary-authorization ratchet), not by any remaining semantic
uncertainty - full reasoning for both below.

**Blind QA**: a deterministic 10%+ sample (26 of the 259
provisionally-VERIFIED entries, selected by positional order in the
batch's canonical entryId sequence, not by risk score or first-pass
reasoning) independently re-reviewed. Result: **26/26 CONFIRMED_VERIFIED,
0 escalations.** Per the escalation rule, since blind QA found no entry
needing repair, retranslation, contamination correction, or a structural
stop, no expansion of the second-pass sample was required and the batch
proceeded to merge as-is.

## Aggregate results (274 entries)

Current, post-resolution disposition totals (see the Resolution addendum
under "The one confirmed-but-deferred finding" below - `rashi-yoma-004b-061`
moved from BLOCKED to SUBSTANTIVE_REPAIR; every other figure is exactly as
this batch merged):

| Disposition | Count | Rate |
|---|---|---|
| VERIFIED | 259 | 94.5% |
| MINOR_EDIT | 8 | 2.9% |
| SUBSTANTIVE_REPAIR | 7 | 2.6% |
| RETRANSLATE | 0 | 0.0% |
| DUPLICATION_OR_CONTAMINATION | 0 | 0.0% |
| BLOCKED | 0 | 0.0% |
| **Total** | **274** | **100%** |

**Changed-translation count: 15** (English actually applied to the
corpus; 14 at this batch's own merge, 1 more once the follow-up PRs
resolved the boundary-fingerprint gate blocker). Second-pass results:
15/15 CONFIRMED, 1 REJECTED (reverted to VERIFIED, no change), 0 remain
BLOCKED.

Defect-tag totals across all 15 findings (all now applied):
SHIFTED (6), DUPLICATED (3), INVENTED_TEXT (3), WRONG_MEANING (3),
OMITTED_TEXT (1), WRONG_LOGIC (1), WRONG_REFERENT (1),
WRONG_TECHNICAL_TERM (1). No entry received a tag outside the campaign's
fixed vocabulary.

## The 14 applied changes

| Entry | Daf | Disposition | Tags | Finding |
|---|---|---|---|---|
| `rashi-yoma-002a-020` | 2a | MINOR_EDIT | SHIFTED | English anticipated "soft stone" content belonging to the next entry (-021), while also adding an unsupported "does not accept impurity" clause not in this line's own Hebrew. |
| `rashi-yoma-002a-021` | 2a | SUBSTANTIVE_REPAIR | DUPLICATED | Restated "not fired clay," already correctly said in -020, after -020 had already (wrongly) said it too. |
| `rashi-yoma-002a-025` | 2a | MINOR_EDIT | DUPLICATED | Anticipated the "since a tevul yom is valid" explanation that is -026's own Hebrew content, not this line's (which is only the Mishnah lemma quote). |
| `rashi-yoma-002a-047` | 2a | SUBSTANTIVE_REPAIR | OMITTED_TEXT | Dropped the clause establishing that the derivation applies to both Yom Kippur and the red heifer, jumping straight to the verse quote. |
| `rashi-yoma-002b-011` | 2b | SUBSTANTIVE_REPAIR | WRONG_MEANING, WRONG_LOGIC | "Since" mistranslated a contrastive Hebrew "rather" (הרי), inverting the passage's rebuttal into a supporting reason. |
| `rashi-yoma-002b-022` | 2b | MINOR_EDIT | DUPLICATED | "Always" anticipated the next entry's own "everywhere" (בכל מקום). |
| `rashi-yoma-002b-029` | 2b | SUBSTANTIVE_REPAIR | INVENTED_TEXT, WRONG_MEANING | Mischaracterized the PZR KSHB mnemonic as being specifically about "priestly watches' lottery divisions" (confirmed wrong: it is a six-item mnemonic distinguishing Shemini Atzeret from Sukkot generally, of which lottery is only one item). |
| `rashi-yoma-003a-013` | 3a | MINOR_EDIT | WRONG_TECHNICAL_TERM | Citation amud error: Hebrew's "(שם.)" marks amud alef (period), rendered as "55b" (amud bet); corrected to "55a," confirmed against Sefaria that the mnemonic itself is on 55a. |
| `rashi-yoma-003a-028` | 3a | SUBSTANTIVE_REPAIR | WRONG_REFERENT, SHIFTED | Prefixed "is the same as the one stated in Pinchas" before the Acharei Mot verse quote even starts, falsely attributing the quote's source; that equivalence clause belongs only at the end of the quote (in the following entry). |
| `rashi-yoma-003b-009` | 3b | MINOR_EDIT | SHIFTED | Anticipated "and a ram for a burnt-offering," which is the next entry's own opening words. |
| `rashi-yoma-003b-010` | 3b | MINOR_EDIT | SHIFTED | Never translated its own opening words ("and a ram for a burnt-offering"), since -009 had anticipated them. |
| `rashi-yoma-003b-033` | 3b | MINOR_EDIT | SHIFTED | Anticipated "one [case]," the next entry's own opening word. |
| `rashi-yoma-003b-034` | 3b | MINOR_EDIT | SHIFTED | Never translated its own opening word ("one"), since -033 had anticipated it. |
| `rashi-yoma-004a-056` | 4a | SUBSTANTIVE_REPAIR | INVENTED_TEXT | Falsely claimed "the daf ends mid-word" (the Hebrew word present, ויכסהו, is complete; only the comment is truncated) and added an unverifiable parenthetical about 4b's content. |

Six of the eight SHIFTED/DUPLICATED findings are instances of the
campaign's known cross-entry word-anticipation pattern (a word or clause
belonging to one entry's own Hebrew translated early or late by a
neighboring entry) - the same defect family Step 4 first identified and
Step 5's systemic-candidate generator tracks.

## The one rejected first-pass finding

`rashi-yoma-002a-054`: first pass proposed SUBSTANTIVE_REPAIR/
WRONG_REFERENT, arguing that the Gemara's own gezeirah shavah (verbal
analogy, l34: "מה להלן פרה אף כאן פרה") requires the word "לעשות" ("to
do") to be understood as deriving the red heifer's separation
requirement, making the existing English's attachment of the
seven-day-separation rule to "the one-day service of Yom Kippur" a
referent error. The independent second pass rejected this: Rashi's own
words in this exact comment ("...לפרוש ז' לפני עבודת יום אחד," continuing
into the neighboring entry's "יום אחד") explicitly and directly say "to
separate seven days before the service of the one day" - the sugya's
standing idiom for Yom Kippur - matching the existing English's "the
one-day service of Yom Kippur" essentially verbatim. The claimed
heifer-attachment argument rests on an inference chain about a different
word in the broader sugya's two-clause derivation, not what Rashi's own
comment on this specific word actually states. **Final disposition:
VERIFIED, no English change.** This is documented as a genuine, working
disagreement between two independent reviewers - exactly what an
independent second pass exists to catch, in either direction.

## The one confirmed-but-deferred finding: `rashi-yoma-004b-061`

`rashi-yoma-004b-061` (daf 4b) has a confirmed, well-evidenced defect: its
English carries a stray "R61:" processing artifact with no Hebrew basis
anywhere in the corpus (INVENTED_TEXT), and mistranslates the truncated
Hebrew "דבר" as "a word" rather than "a matter" - confirmed against the
entry's own continuation on daf 5a, "דבר שאין מעכב בהן לדורות" ("a matter
that does not invalidate for future generations"). This was independently
re-derived a second time with the same conclusion.

**The fix was not applied in this batch.** `rashi-yoma-004b-061` is a
"boundary" entry (empty `linkedGemaraLineIds`), and its authorization
record in `modules/yoma/scripts/allowlists/rashi_boundary_authorizations.json`
carries an `enFingerprint` keyed to its exact current English text.
Applying the fix would change that fingerprint, which the allowlist
ratchet (`check_rashi_pr_scope.py`'s `check_allowlist_ratchet`, enforced
in CI via `npm run check:rashi-pr-scope:yoma`) treats as an unauthorized
new registry entry rather than a legitimate re-fingerprint of an existing
one - the ratchet's set-based diff is not identity-aware (keyed by
daf+vilnaLine), only content-aware. No task type available to this batch
review can authorize that registry change on its own; `.github/workflows/*`
is forbidden to every task type, ruling out a same-PR workaround via the
registry's own `RASHI_ALLOWLIST_RESTRUCTURE=1` escape hatch (CI would
still run without it set). Per this task type's own escalation trigger
("any gate failure not fixable by correcting the entry's own English"),
this was reported rather than routed around; the recommended resolution
(a docs-tooling PR applying `RASHI_ALLOWLIST_RESTRUCTURE=1`, or a fix to
the ratchet's added-vs-modified detection logic so it does not need
that escape hatch for identity-preserving updates) is a decision for a
dedicated follow-up, not this batch. **Final disposition: BLOCKED**
(a tooling-gate stop, not a semantic-uncertainty stop); the confirmed
finding, proposed fix, and this exact blocker are recorded in
`docs/reports/data/rashi-step6-batch-001-review-records.json` and in the
inventory's `reviewerEvidence` for this entry, so the fix is ready to
apply the moment the registry-update path is authorized.

### Resolution addendum

This blocker history above is preserved exactly as it occurred and is not
rewritten: the entry was first found and confirmed defective during this
batch, and its fix was genuinely blocked by the allowlist ratchet's
identity-blind diff, not by any remaining semantic uncertainty. It has
since been resolved by two follow-up PRs, both scoped narrowly outside
this batch:

1. A tooling PR added `modules/yoma/scripts/boundary_fingerprint_ratchet.py`,
   an identity-aware ratchet (keyed by the registry's own existing
   `daf`+`vilnaLine` identity) that lets a boundary authorization's
   `enFingerprint` be refreshed - and only that field - when ten
   conditions all hold, independently recomputing both fingerprints from
   the actual corpus text rather than trusting the registry file, the
   manifest, or the review record. It also added the narrowly-scoped
   `rashi-boundary-translation-repair` task type, which authorizes exactly
   one boundary-authorized entry's English plus that one fingerprint
   refresh, nothing else.
2. This repair PR used that new task type to apply the fix. A fresh,
   independent second semantic pass (re-reading the raw Hebrew stub and
   its 5a continuation from scratch, not copying the batch's original
   finding forward) reconfirmed the defect and refined the wording from
   the batch's original `'Davar' - a matter; ...` proposal to
   `'Something' - the daf ends mid-word here; Rashi's comment continues on
   5a, where the lemma is completed as 'Something that does not
   invalidate for future generations.'` - matching the corpus's
   established page-boundary stub template (`rashi-yoma-005a-040`) and
   staying internally consistent with the entry this stub is truncated
   from, `rashi-yoma-005a-001`, which already renders the same completed
   lemma as "Something that does not invalidate for future generations."
   The second pass returned **CONFIRMED**; only this entry's English and
   its own authorization's `enFingerprint` changed - no other registry
   record, no Hebrew, and no other Rashi entry changed.

**Updated final disposition: SUBSTANTIVE_REPAIR** (defect tags
`INVENTED_TEXT`, `WRONG_MEANING` unchanged - they document what was
found, not an open question). Batch 001 now has zero unresolved
blockers. The review record, the translation-quality inventory, and the
aggregate table and status below are updated accordingly; the reviewed
(474) and UNREVIEWED (8,380) full-corpus totals are unaffected - only
this one entry's disposition changed.

## Tooling fix discovered during this batch

Validating this batch's own review-record file against
`validate_rashi_review_records.py` (Step 5 tooling) surfaced a genuine
bug: the validator checked `proposedEnglish` nullness and the
`originalEnglish`/`hebrew` immutable-field rules against `firstPassDisposition`
and the live working-tree inventory, respectively - both wrong for a
real batch PR, whose own content edit and review-record file land in the
same commit. Fixed in this PR (`modules/yoma/scripts/validate_rashi_review_records.py`):
`proposedEnglish` nullness now keys off `finalDisposition` (matching the
contract's own stated rule, and correctly covering both the REJECTED and
REMAINED_BLOCKED cases this batch exercised), and a new `--base` option
compares `hebrew`/`originalEnglish` against a git ref (matching the exact
pattern every other campaign validator already uses) instead of the live
file. Also extended `check_rashi_pr_scope.py`'s hardcoded file-set
constants to recognize the new Step 6 artifact types (review-records
files, batch reports, the strategy doc, and this PR's own tooling files) -
the same kind of one-time extension `check_rashi_pr_scope.py` already
received once before, in Step 4 PR B0. 6 new regression tests added
(22 total, up from 16); all pass.

## Regression and platform evidence (fresh at this batch's merge)

- **Rashi entry count**: 8,854 (unchanged)
- **Associations**: 10,061 declared, 0 broken, 0 cross-daf (unchanged)
- **Boundary registry**: 20 authorized, 20 in corpus, 20/20 matched, 0
  stale, 0 duplicate, 0 unauthorized (unchanged)
- **Hebrew text**: byte-unchanged across all 274 entries in this batch,
  confirmed via direct inspection of every changed learning JSON's diff
  (only `en` fields ever appear). Campaign-wide to date (PR A's source
  repair plus this batch): one authorized Hebrew source repair
  (`rashi-yoma-009b-001`, PR A); no unexpected Hebrew changes anywhere
  else. This is the accurate campaign statement - not "zero Hebrew
  changed across both PRs," which would misstate PR A's own intentional,
  evidence-backed correction as if it never happened.
- **`npm run validate:offline:yoma`**, **`npm test`**, **`npm run
  test:browser`**, **`npm run build`**, **`npm run check:deploy-html`**,
  **`python3 scripts/worker_pipeline.py verify --full`**: all green
- **Full-corpus progress after this batch**: 474 of 8,854 entries
  reviewed (200 pilot + 274 batch 001), 8,380 remain UNREVIEWED, 1 of 41
  Step 6 batches complete

## Status

**Batch 001: COMPLETE, zero unresolved blockers.** All 274 entries
reviewed with an assigned final disposition; 0 entries left in an
ambiguous state. `rashi-yoma-004b-061` was temporarily BLOCKED by the
allowlist ratchet's identity-blind diff (a tooling-gate stop, never an
open semantic question - see the Resolution addendum above) and has
since been resolved by two narrowly-scoped follow-up PRs; it is now
SUBSTANTIVE_REPAIR. Full-corpus progress is unchanged by this resolution:
474 of 8,854 entries reviewed, 8,380 remain UNREVIEWED. Step 6 status:
**IN PROGRESS**; `step6-batch-040` has not been started. Next batch per
the strategy document's recommended order: `step6-batch-040` (perek 8,
85b-87a, highest systemic-candidate density).
