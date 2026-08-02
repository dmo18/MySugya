# Rashi translation-quality campaign, Step 4, batch 1 report

Covers pilot-cohort entries at cohort index 0-49 (50 entries, 27 daf: 2a,
2b, 3a, 3b, 4a, 4b, 5a, 5b, 6a, 6b, 7a, 7b, 8a, 8b, 9a, 9b, 10a, 10b, 11a,
11b), the first review batch out of the 200-entry frozen pilot cohort
(`docs/reports/data/rashi-pilot-cohort.json`). Full review packets:
`docs/reports/data/rashi-pilot-review-packets.json`.

Method: for every entry, the Hebrew Rashi was read independently, its
linked Gemara/Mishnah line(s) and surrounding context were read, and the
current English was compared against that reading - never against the
existing English as a starting assumption. Style-guide sections and
terminology-registry entries flagged by the packet were applied without
forcing advisory-only terminology. Every SUBSTANTIVE_REPAIR, RETRANSLATE,
MINOR_EDIT, and the one BLOCKED entry received an independent second pass
(re-derived from Hebrew and context again, not just re-reading the proposed
fix) before being finalized below.

## Totals

| Disposition | Count |
|---|---|
| VERIFIED | 40 |
| MINOR_EDIT | 4 |
| SUBSTANTIVE_REPAIR | 4 |
| RETRANSLATE | 1 |
| DUPLICATION_OR_CONTAMINATION | 0 |
| BLOCKED | 1 |
| **Total reviewed** | **50** |

Changed translations: 9. Second-pass results: 9/9 CONFIRMED (the 1 BLOCKED
entry's second pass reconfirmed the structural stop, not a translation).

Defect tags across all findings: OVEREXPLAINED (2), WRONG_MEANING (2),
OMITTED_TEXT (2), SHIFTED (1), PUNCTUATION (1), WRONG_TECHNICAL_TERM (1),
HEBREW_LEFT_UNTRANSLATED (1), WRONG_LOGIC (1), INVENTED_TEXT (1).

## Changed translations

| Entry | Daf | Disposition | Defect tags |
|---|---|---|---|
| rashi-yoma-002a-011 | 2a | SUBSTANTIVE_REPAIR | SHIFTED, OVEREXPLAINED |
| rashi-yoma-002b-007 | 2b | MINOR_EDIT | PUNCTUATION |
| rashi-yoma-003b-007 | 3b | SUBSTANTIVE_REPAIR | OVEREXPLAINED |
| rashi-yoma-004a-001 | 4a | SUBSTANTIVE_REPAIR | WRONG_MEANING, WRONG_TECHNICAL_TERM |
| rashi-yoma-006a-008 | 6a | SUBSTANTIVE_REPAIR | OMITTED_TEXT |
| rashi-yoma-006b-001 | 6b | MINOR_EDIT | HEBREW_LEFT_UNTRANSLATED |
| rashi-yoma-007b-001 | 7b | RETRANSLATE | WRONG_MEANING, WRONG_LOGIC |
| rashi-yoma-008b-006 | 8b | MINOR_EDIT | OMITTED_TEXT |
| rashi-yoma-011a-001 | 11a | MINOR_EDIT | INVENTED_TEXT |

### rashi-yoma-002a-011 (daf 2a) - SUBSTANTIVE_REPAIR

- Hebrew: `דחיישת למיתה: אין לדבר סוף.`
- Old English: `"There is no end to the matter" - the Rabbis object: if we worry about death, the backup wife might also die, and so on without end.`
- New English: `Since he feared death - "there is no end to the matter"`
- Evidence: the Hebrew is two clauses - the tail of the comment on the *preceding* entry's dibbur hamatchil ("אם כן"), then a new quote ("there is no end to the matter"). The old English imported "the backup wife might also die" from the *next* entry's Hebrew (`שמא גם זו תמות`, rashi-yoma-002a-012 - not present in this entry at all) and added framing ("the Rabbis object") absent from this entry's Hebrew. Confirmed against the linked Mishnah (yoma-002a-l04): the quoted phrase is the Sages' reply to Rabbi Yehuda; this entry's own Hebrew covers only "since he feared death" plus the new quote.
- Second pass: CONFIRMED.

### rashi-yoma-002b-007 (daf 2b) - MINOR_EDIT

- Hebrew: `כדאמרינן לקמן (דף כב.): הכי`
- Old English: `as we say further on (22a)? This is`
- New English: `as we say further on (22a): this is`
- Evidence: the Hebrew has a colon before "הכי" ("thus/so"), not a question mark; the sentence is declarative, with no interrogative particle anywhere in it.
- Second pass: CONFIRMED.

### rashi-yoma-003b-007 (daf 3b) - SUBSTANTIVE_REPAIR

- Hebrew: `עד כאן לא פליגי. תירוצא הוא:`
- Old English: `'Until here they do not disagree' - this phrase [introduces] the resolution [of the dispute], not a continuation of the debate.`
- New English: `'Until here they do not disagree' - this is the resolution:`
- Evidence: the second Hebrew clause is two words ("תירוצא הוא", "it is the resolution"). The old English's "not a continuation of the debate" is an interpretive gloss with no anchor in either clause.
- Second pass: CONFIRMED.

### rashi-yoma-004a-001 (daf 4a) - SUBSTANTIVE_REPAIR

- Hebrew: `לטומאת ביתו. שמא אם יזקק לאשתו ותראה דם בשעת ביאה ונמצא`
- Old English: `'About the impurity of his house' - lest, if he unites with his wife, she sees blood during intercourse and it turns out`
- New English: `'Concerning the impurity of his wife' - lest, if he unites with his wife, she sees blood during intercourse and it turns out`
- Evidence: "ביתו" ("his house") is the established wife-euphemism - the same word is explicitly resolved to "his wife" earlier in this Mishnah's own gloss (rashi-yoma-002a-009: "ביתו - זו אשתו"), and this entry's own next clause names "אשתו" (his wife) directly. Translating the euphemism literally as "his house" misleadingly suggests tzara'at bayit (leprosy of a house, an unrelated halakha) rather than the actual topic.
- Second pass: CONFIRMED. Detector note: this defect carried **zero** automated risk signals (riskScore 0) - a purely semantic/idiom catch no heuristic could have found.

### rashi-yoma-006a-008 (daf 6a) - SUBSTANTIVE_REPAIR

- Hebrew: `גדול לא זהו אבנטו של כהן הדיוט`
- Old English: `is not the ordinary priest's belt,`
- New English: `of the High Priest - this is not the ordinary priest's belt,`
- Evidence: the Hebrew has two components - "גדול" (continuing the prior entry's "שהוא של" = "that it belongs to [the Kohen] Gadol") and "לא זהו אבנטו של כהן הדיוט" ("this is not the belt of an ordinary priest"). The old English dropped "גדול" entirely, leaving the prior entry's "we learn it is" dangling and losing the Gadol/Hedyot (High Priest/ordinary priest) contrast that is the entire point of the derivation.
- Second pass: CONFIRMED.

### rashi-yoma-006b-001 (daf 6b) - MINOR_EDIT

- Hebrew: `שמטמא משכב ומושב. אפילו עשר מצעות זו על גב זו וטמא מת`
- Old English: `'That he renders a bed or seat impure' - even ten mattresses piled one atop another; whereas a tamei met`
- New English: `'That he renders a bed or seat impure' - even ten mattresses piled one atop another; whereas one impure through corpse-contact (tamei met)`
- Evidence: "טמא מת" was left as a bare transliteration with no English gloss, unlike the corpus's convention of glossing a transliterated term immediately (e.g. rashi-yoma-011b-001: "'Beit sha'ar' - a small house that they make...").
- Second pass: CONFIRMED. Note: daf 6b is Step-1-flagged "needs reconstruction" ("confirmed fabricated/filler"), but this entry (together with rashi-yoma-006b-002, which completes its sentence exactly) is coherent and faithful aside from this one gloss gap - see "Daf-level historical flags vs. entry-level findings" below.

### rashi-yoma-007b-001 (daf 7b) - RETRANSLATE

- Hebrew: `הא אינו נושא וכו'. הא לשון מעתה הוא מעתה אי אתה מוצא שיהא`
- Old English: `'It bears only...' etc. - the word 'ha' [here] means 'from now'; from now on you will not find that it bears`
- New English: `'It does not bear...' etc. - the word 'ha' [here] means 'from now'; from now on you will not find that it bears`
- Evidence: "אינו נושא" is unambiguous present-tense negation ("[it] does not bear/carry"); there is no "אלא" (only/except) anywhere in the fragment that would license a restrictive-positive reading. The old English inverted the polarity to a positive-with-restriction - the opposite of the Hebrew. The rest of the entry (explaining "הא" as an inferential particle, "from now on you will not find that it bears...") is consistent with the negative reading, not the inverted one.
- Second pass: CONFIRMED. Detector note: zero risk signals (riskScore 0) - another purely semantic catch (a negation flip) invisible to length/pattern heuristics.

### rashi-yoma-008b-006 (daf 8b) - MINOR_EDIT

- Hebrew: `נמי האי. שזה מזין עליו כל שבעה`
- Old English: `'this' - that upon this one they sprinkle all seven,`
- New English: `'This one too' - that upon this one they sprinkle all seven,`
- Evidence: "נמי" ("also/too") signals this case is analogous to one already discussed; the old English dropped it, losing the comparative signal.
- Second pass: CONFIRMED.

### rashi-yoma-011a-001 (daf 11a) - MINOR_EDIT

- Hebrew: `כל השערים. שערי מזרח עזרה: אחד שערי מדינות. יש מדינה`
- Old English: `'All the gates' - the eastern gates of the Temple courtyard. New comment: 'the gates of provinces alike' - there is a province`
- New English: `'All the gates' - the eastern gates of the Temple courtyard. 'The gates of provinces alike' - there is a province`
- Evidence: the Hebrew has no structural marker (no "ד"א"/"another interpretation" or similar) between its two dibbur-hamatchil clauses - they are simply colon-separated, the same as every other multi-clause entry in this batch. The old English inserted an editorial narration phrase, "New comment:", corresponding to nothing in the Hebrew - the same kind of fabricated structural narration the corpus's scaffold-audit tooling targets elsewhere, though this specific phrase evaded that pattern list.
- Second pass: CONFIRMED. Detector note: zero risk signals - a third semantic-only catch.

## BLOCKED entry

### rashi-yoma-009b-001 (daf 9b) - BLOCKED, structural stop

The stored Hebrew (`he`) field for this entry begins with a leaked HTML
fragment: `span class="five">ששהו את קיניהן...` - an opening
`<span class="five">` tag lost its `<` and the rest leaked verbatim into
the Hebrew text field, directly ahead of the real Hebrew (`ששהו את
קיניהן...`). Confirmed via direct read of `modules/yoma/learning_data.js`
and traced to the `he` field sourced from the talmud.dev cache, not this
campaign's enrichment layer - repairing it is a Hebrew-source data-quality
fix, out of this campaign's scope (Hebrew text is immutable baseline).

Confirmed **isolated**: a corpus-wide scan of all 8,854 `he` fields for
`span class` or any `<`/`>` character found exactly one match - this entry
only. This is not touched, edited, or worked around; it is recorded
BLOCKED with the finding above as its evidence and reported for a separate
Hebrew-source repair pass.

## Detector precision (this batch, n=50)

| Risk signal | Flagged | Real defect found | Verified anyway | Precision |
|---|---|---|---|---|
| OVEREXPLAINED | 2 | 2 | 0 | 100% |
| WRONG_REFERENT | 1 | 1 | 0 | 100% |
| INVENTED_TEXT (daf-level, "needs reconstruction") | 3 | 1 | 2 | 33% |
| CONTEXT_MISMATCH (daf-level, "needs realignment") | 13 | 1 | 12 | 8% |
| TRUNCATED | 19 | 1 | 18 | 5% |
| FRAGMENT | 1 | 0 | 1 | 0% |

n is small per-tag in a single batch; treat as directional, not final -
final precision figures are computed corpus-wide across all four batches in
the Step 4 reconciliation report.

**Three of the nine real defects found in this batch carried zero
automated risk signals** (riskScore 0): rashi-yoma-004a-001 (a
wife/house-euphemism mistranslation), rashi-yoma-007b-001 (a negation
inversion), and rashi-yoma-011a-001 (fabricated scaffold narration). None
of Step 2's detectors are designed to catch idiom resolution, polarity
flips, or narration phrases outside its known scaffold-pattern list - this
is exactly the class of defect that requires genuine semantic reading and
cannot be found by automated triage alone. This is the single most
important finding for the Step 5 methodology recommendation: a
cluster-only or detector-only review strategy would have missed all three.

## Daf-level historical flags vs. entry-level findings

Daf 5a, 5b, and 6a are Step-1-classified "needs realignment" (the en
systematically translates an adjacent line's Hebrew instead of its own,
per the VERSION 15.293 Wave 1 audit). This batch reviewed 11 entries across
those three daf and found genuine misalignment in exactly **one** (6a-008,
above) - the other 10 matched their own Hebrew correctly. Daf 6b is
similarly flagged "needs reconstruction" (confirmed fabricated/filler); of
the 3 entries reviewed there, 2 were faithful and coherent (6b-002, 6b-023)
and the third (6b-001) had only a minor gloss gap, not fabrication.

This does not mean the daf-level flags are wrong - the underlying Wave 1
audit found real, documented problems on these daf, and this batch's
low-single-digit sample cannot rule out worse concentrations elsewhere on
the same daf. But it does mean **the flag does not imply every entry on a
flagged daf is defective**: a bulk reconstruction pass triggered purely by
the daf-level flag, without per-entry verification, would have discarded
and rewritten several entries that were already correct. See the Step 4
reconciliation report for how this shapes the Step 5 recommendation.

## Validation and deployment evidence

- `python3 modules/yoma/scripts/check_rashi_pr_scope.py --base origin/main` - OK, 9 learning JSON files, only `en` changed
- `npm run validate:offline:yoma` - all gates pass
- `python3 modules/yoma/scripts/audit_rashi_association.py --exhaustive-corpus` - 8,854 entries, 0 broken, 0 cross-daf, unchanged
- `python3 modules/yoma/scripts/validate_rashi_boundary_authorizations.py` - 20/20, unchanged
- `npm test`, `npm run test:browser`, `npm run build`, `npm run check:deploy-html` - all pass
- `python3 scripts/worker_pipeline.py verify --full` - see PR description for the run captured at merge time
- Hebrew text confirmed byte-unchanged for all 50 reviewed entries (git diff shows only `en` fields differ from origin/main)
- 8,804 of 8,854 entries remain `UNREVIEWED` after this batch (50 reviewed)
