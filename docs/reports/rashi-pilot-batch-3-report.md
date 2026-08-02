# Rashi translation-quality campaign, Step 4, batch 3 report

Covers pilot-cohort entries at cohort index 100-149 (50 entries, 32 daf:
24b, 25a, 25b, 26a, 26b, 27a, 27b, 28a, 28b, 29a, 29b, 30a, 30b, 31a, 31b,
32a, 32b, 33a, 33b, 34a, 34b, 35a, 35b, 36a, 36b, 37a, 37b, 38a, 38b, 39a,
39b, 40a, 40b, 41a, 41b, 53a, 53b, 54b, 55a, 55b), the third review batch.
Method identical to batches 1-2.

## Totals

| Disposition | Count |
|---|---|
| VERIFIED | 48 |
| MINOR_EDIT | 0 |
| SUBSTANTIVE_REPAIR | 1 |
| RETRANSLATE | 1 |
| DUPLICATION_OR_CONTAMINATION | 0 |
| BLOCKED | 0 |
| **Total reviewed** | **50** |

Changed translations: 2. Second-pass results: 2/2 CONFIRMED.

Defect tags: WRONG_MEANING (1), WRONG_LOGIC (1), INVENTED_TEXT (1).

Running campaign totals after batch 3: 150/200 cohort entries reviewed (132
VERIFIED, 10 MINOR_EDIT, 6 SUBSTANTIVE_REPAIR, 2 RETRANSLATE, 1 BLOCKED), 17
changed translations, 8,704/8,854 corpus entries still UNREVIEWED.

## Changed translations

### rashi-yoma-027a-001 (daf 27a) - RETRANSLATE

- Hebrew: `גמ' האי מבעיא ליה לגופיה. דניבעי כהן מיעוטא מנא לן להפשט`
- Old English: `Gemara: this verse would seem redundant, teaching only what is obvious - for we need to know from where we derive the priest-exclusion for flaying`
- New English: `Gemara: this verse is needed for its own sake - for we need to know from where we derive the priest-exclusion for flaying`
- Evidence: `מבעיא ליה לגופיה` is standard Talmudic terminology asserting a verse IS needed for its own (non-obvious) teaching - i.e. NOT redundant; it is the Gemara's stock rejection of a proposed extra derivation from an already-necessary verse. The old English inverted this to "would seem redundant." Directly confirmed against this entry's own linked Gemara line, already present in the corpus (William Davidson Edition): "But that verse...**is needed for its own sake**, to teach that the wood must be brought by a priest; it should not be interpreted as an inference that other services...may be performed by non-priests" - the corpus's own official Gemara translation states the opposite of what the old Rashi translation claimed.
- Second pass: CONFIRMED, with the strongest available corroboration - the corpus's own adjacent Gemara translation of the identical phrase.

### rashi-yoma-053b-002 (daf 53b) - SUBSTANTIVE_REPAIR

- Hebrew: `תרום רישיך. תהיה ראש ישיבת הכרך: התם מיבעי ליה למיקם.`
- Old English: `this on his own. 'May your head be raised' - may you become head of the great yeshiva. 'There he must pause' -`
- New English: `'May your head be raised' - may you become head of the great yeshiva. 'There he must pause' -`
- Evidence: this entry's Hebrew begins fresh with an unrelated dibbur hamatchil ("may your head be raised") - a blessing, with no textual connection to perception or self-sufficiency. The old English's opening fragment, "this on his own.", has zero basis in either this entry's Hebrew or the preceding entry's (rashi-yoma-053b-001, also in this cohort and confirmed VERIFIED - its own Hebrew is a complete, self-contained clause ending in a colon, needing no continuation). Unlike the cross-entry word-anticipation defects found in earlier batches (real content misattributed to the wrong entry), this phrase corresponds to no Hebrew anywhere in either entry - pure fabrication, matching daf 53b's Step-1 historical characterization ("confirmed generic filler or fabricated") for this specific entry.
- Second pass: CONFIRMED.

## The historically "needs reconstruction" daf: a much lower defect rate than expected

This batch reviewed 10 entries across daf 53a, 53b, 54b, and 55a-55b - all
part of Step 1's `KNOWN_NEEDS_RECONSTRUCTION` bucket, the strongest
historical-debt category, whose own characterization is "confirmed generic
filler or fabricated." Of those 10 entries, **9 were faithful and
correctly translated**; only 1 (`rashi-yoma-053b-002`, above) contained
real fabrication.

This is the most consequential single finding across batches 1-3 for the
Step 5 recommendation. It does not mean the daf-level flag is wrong - the
Wave 1 audit that produced it (VERSION 15.293) found real, specific
problems, and a 10-entry sample from four daf cannot rule out worse
concentrations in the entries this batch did not happen to select. But it
means a full-corpus strategy that bulk-reconstructs every entry on a
flagged daf, without individual verification, would discard and rewrite
several entries that are already correct - wasted effort at best, and a
real risk of introducing NEW defects into currently-faithful translations
at worst. See the Step 4 reconciliation report for how this and batch 1's
matching finding (on the `needs realignment` daf) shape the Step 5
methodology recommendation.

## Detector precision (this batch, n=50)

Both defects found had risk signals attached (unlike batches 1-2's mostly
zero-signal findings): `rashi-yoma-027a-001` had no automated flag
(riskScore 0 - a third purely semantic-only catch across the campaign so
far), while `rashi-yoma-053b-002` carried the daf-level INVENTED_TEXT
signal (a true positive, though the signal fires uniformly across the
whole daf regardless of per-entry accuracy - see the finding above).

## Validation and deployment evidence

- `python3 modules/yoma/scripts/check_rashi_pr_scope.py --base origin/main` - OK, 2 learning JSON files, only `en` changed
- `npm run check:rashi-translation-inventory:yoma` - inventory matches live corpus exactly
- `npm run validate:offline:yoma` - all gates pass
- `python3 modules/yoma/scripts/audit_rashi_association.py --exhaustive-corpus` - 8,854 entries, 0 broken, 0 cross-daf, unchanged
- `python3 modules/yoma/scripts/validate_rashi_boundary_authorizations.py` - 20/20, unchanged
- `npm test`, `npm run test:browser`, `npm run build`, `npm run check:deploy-html` - all pass
- Hebrew text confirmed byte-unchanged (git diff against origin/main shows only 2 `en:` lines differ)
- 8,704 of 8,854 entries remain `UNREVIEWED` after this batch
