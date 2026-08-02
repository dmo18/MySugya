# Rashi translation-quality campaign, Step 4, batch 4 report

Covers pilot-cohort entries at cohort index 150-199 (50 entries, 26 daf:
56b, 57a, 57b, 58a, 58b, 59a, 59b, 60a, 60b, 61b, 62a, 62b, 63a, 63b, 64a,
64b, 65a, 65b, 66a, 66b, 67a, 69a, 69b, 70b, 71a), the fourth and final
review batch, completing the 200-entry pilot cohort. Method identical to
batches 1-3.

## Totals

| Disposition | Count |
|---|---|
| VERIFIED | 45 |
| MINOR_EDIT | 1 |
| SUBSTANTIVE_REPAIR | 4 |
| RETRANSLATE | 0 |
| DUPLICATION_OR_CONTAMINATION | 0 |
| BLOCKED | 0 |
| **Total reviewed** | **50** |

Changed translations: 5. Second-pass results: 5/5 CONFIRMED.

Defect tags: SHIFTED (2), WRONG_LOGIC (1), OMITTED_TEXT (1), WRONG_MEANING (1).

**Campaign pilot totals after batch 4 (final): 200/200 cohort entries
reviewed** - 177 VERIFIED, 11 MINOR_EDIT, 10 SUBSTANTIVE_REPAIR, 2
RETRANSLATE, 1 BLOCKED. 22 changed translations. 8,654/8,854 corpus entries
remain UNREVIEWED (the pilot is a sample, not the full corpus - see the
Step 4 reconciliation report for the full-corpus estimate and Step 5
recommendation).

## Changed translations

### rashi-yoma-056b-001 (daf 56b) - SUBSTANTIVE_REPAIR

- Hebrew: `לכשיבקע. נחוש לו כלומר לא חיישינן לשמא יבקע`
- Old English: `'When it bursts' - we take precaution for it, meaning we are not concerned that it might burst, since it is possible`
- New English: `'When it bursts' - are we concerned about it? Meaning, we are not concerned that it might burst, since it is possible`
- Evidence: old English rendered `נחוש לו` as an assertion ("we take precaution for it") immediately followed by its own explanation flatly contradicting it ("meaning we are not concerned..."). `נחוש לו` functions here as the Gemara's rhetorical question form, answered by what follows - not a standalone assertion. Confirmed by the full sentence spanning into the next (unchanged) entry: "...since it is possible to hand it over to a guardian," which only makes sense as the reason we are *not* concerned.
- Second pass: CONFIRMED.

### rashi-yoma-059b-001 / rashi-yoma-059b-002 (daf 59b) - SUBSTANTIVE_REPAIR / MINOR_EDIT (paired fix)

- 059b-001 old: `'But only by rabbinic law' - the one who says one may be liable for misuse of sacred property means only by rabbinic law, to pay`
- 059b-001 new: `'But only by rabbinic law' - the one who says one may be liable for misuse of sacred property`
- 059b-002 old: `the principal, but not to add the additional fifth`
- 059b-002 new: `says it is only rabbinic, to pay the principal, but not to add the additional fifth`
- Evidence: 059b-001's own Hebrew (`אלא מדרבנן. מאן דאמר מועלין`) ends mid-clause with no predicate. The old English supplied a full predicate that duplicated 059b-001's own opening ("only by rabbinic law") and additionally imported "to pay" - a word belonging to 059b-002's own Hebrew (`לשלם`). Since both entries are in this cohort, both were corrected together: 059b-001 now ends where its own Hebrew ends, and 059b-002 restores its own dropped opening (`מדרבנן קאמר`, "states it is only rabbinic") that the old English had skipped.
- Second pass: CONFIRMED for both.

### rashi-yoma-065a-001 / rashi-yoma-065a-002 (daf 65a) - SUBSTANTIVE_REPAIR (paired fix)

- 065a-001 old: `...regarding the second of the second pair, and atonement is achieved through the first,`
- 065a-001 new: `...regarding the second of the second pair, and the first that was rejected`
- 065a-002 old: `the rejected one - why? If this were like an individual's counterpart dying...`
- 065a-002 new: `'It is atoned' - why? If this were like an individual's counterpart dying...`
- Evidence: 065a-001's own Hebrew ends `ובראשון שנדחה` ("and the first that was rejected/deferred") - a noun phrase. Old English added "atonement is achieved through the first," anticipating 065a-002's own opening word `יתכפר` (unambiguously about atonement, root כפר). 065a-002's old English then substituted "the rejected one" - the word that actually belongs to 065a-001's own Hebrew (`שנדחה`) - for its own untranslated `יתכפר`. Both entries had their content swapped; both are corrected here, staying close to the literal Hebrew rather than resolving the deeper halakhic argument (the scapegoat-pair substitution rules), to avoid overreach on a genuinely technical passage.
- Second pass: CONFIRMED for both, with moderate-not-total confidence flagged explicitly in the inventory evidence given the passage's legal complexity - the word-level correction (יתכפר ≠ "rejected") is unambiguous even where the fuller halakhic nuance would need more sugya expertise to fully resolve.

## A third confirmation of the "cross-entry anticipation" pattern - and a case where it is NOT a defect

Two of this batch's three multi-entry fixes (59b, 65a) are the same shape
found in batch 2: a word belonging to one entry's own Hebrew gets
translated early or late by a *neighboring* entry. Unlike batch 2 (where
the neighbor was always out of cohort, so only one side could be
corrected), all four entries here are in the cohort, so both sides of each
pair were corrected together.

This batch also surfaced the first clear **negative case**: `rashi-yoma-
065b-002`'s Hebrew opens with `צבור` (communal), a word the *preceding*
entry's translation (065b-001, unchanged) had already folded into its own
quoted phrase ("'Communal offerings are different'"). Reviewed and
confirmed VERIFIED, not a defect - the completed phrase is fully and
correctly expressed exactly once, nothing is lost or falsified, and 065b-
002 correctly moves on to its own remaining content. The distinguishing
test applied throughout this campaign: cross-entry anticipation is a
defect only when it causes omission (content never appears anywhere) or
fabrication (invented content); quoting a natural, complete phrase one
word early with nothing lost is not.

## The historically flagged daf, again

This batch reviewed several entries on daf 63b (`needs realignment`) and
found both entries faithful (another two false positives for that
daf-level flag, adding to batch 1's finding). No entries from the
`needs reconstruction` bucket appeared in this batch's daf set.

## Detector precision (this batch, n=50)

Two of the five defects carried zero automated risk signals
(rashi-yoma-056b-001, riskScore 0). The three daf-59b/65a defects carried
the daf-level INVENTED_TEXT signal (a true positive at the daf level, though
as established across the campaign, that signal fires uniformly across a
flagged daf regardless of per-entry accuracy).

## Validation and deployment evidence

- `python3 modules/yoma/scripts/check_rashi_pr_scope.py --base origin/main` - OK, 3 learning JSON files, only `en` changed
- `npm run check:rashi-translation-inventory:yoma` - inventory matches live corpus exactly
- `npm run validate:offline:yoma` - all gates pass
- `python3 modules/yoma/scripts/audit_rashi_association.py --exhaustive-corpus` - 8,854 entries, 0 broken, 0 cross-daf, unchanged
- `python3 modules/yoma/scripts/validate_rashi_boundary_authorizations.py` - 20/20, unchanged
- `npm test`, `npm run test:browser`, `npm run build`, `npm run check:deploy-html` - all pass
- Hebrew text confirmed byte-unchanged (git diff against origin/main shows only 5 `en:` lines differ)
- 8,654 of 8,854 entries remain `UNREVIEWED` after this batch (200/8,854 now reviewed - the complete pilot)
