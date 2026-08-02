# Rashi translation-quality campaign, Step 4, batch 2 report

Covers pilot-cohort entries at cohort index 50-99 (50 entries, 21 daf: 11b,
12a, 12b, 13a, 13b, 14a, 14b, 15a, 15b, 16a, 16b, 17a, 17b, 18a, 18b, 19a,
19b, 20a, 20b, 21a, 21b, 22a, 22b, 23a, 23b, 24a), the second review batch.
Method identical to batch 1 (`docs/reports/rashi-pilot-batch-1-report.md`):
Hebrew read independently, linked Gemara/Mishnah context read, English
compared against that reading, every change given an independent second
pass before being finalized.

## Totals

| Disposition | Count |
|---|---|
| VERIFIED | 44 |
| MINOR_EDIT | 6 |
| SUBSTANTIVE_REPAIR | 0 |
| RETRANSLATE | 0 |
| DUPLICATION_OR_CONTAMINATION | 0 |
| BLOCKED | 0 |
| **Total reviewed** | **50** |

Changed translations: 6. Second-pass results: 6/6 CONFIRMED.

Defect tags: INVENTED_TEXT (3), OMITTED_TEXT (2), SHIFTED (1).

Running campaign totals after batch 2: 100/200 cohort entries reviewed (84
VERIFIED, 10 MINOR_EDIT, 4 SUBSTANTIVE_REPAIR, 1 RETRANSLATE, 1 BLOCKED),
15 changed translations, 8,754/8,854 corpus entries still UNREVIEWED.

## Changed translations

| Entry | Daf | Disposition | Defect tags |
|---|---|---|---|
| rashi-yoma-011b-015 | 11b | MINOR_EDIT | INVENTED_TEXT |
| rashi-yoma-012b-002 | 12b | MINOR_EDIT | INVENTED_TEXT |
| rashi-yoma-013b-001 | 13b | MINOR_EDIT | INVENTED_TEXT |
| rashi-yoma-015a-003 | 15a | MINOR_EDIT | OMITTED_TEXT |
| rashi-yoma-020b-023 | 20b | MINOR_EDIT | OMITTED_TEXT |
| rashi-yoma-023a-005 | 23a | MINOR_EDIT | SHIFTED |

### The "New comment:" scaffold phrase (3 occurrences)

`rashi-yoma-011b-015`, `rashi-yoma-012b-002`, and `rashi-yoma-013b-001` all
carry the same defect first found in batch 1 (`rashi-yoma-011a-001`): the
English inserts the narration phrase "New comment:" between two Hebrew
clauses that are separated only by a colon - the same separator every other
multi-clause entry in both batches uses without any narration at all. None
of the four Hebrew fragments involved contain a structural marker (e.g.
"ד"א"/"another interpretation") that would justify a English label; the
phrase corresponds to nothing in the source. This now appears **4 times
across 2 batches (100 entries)**, which is frequent enough to be worth
flagging as a targeted, evidence-backed search candidate for a future
batch or a dedicated cluster-style pass (see Step 5 recommendation in the
Step 4 reconciliation report), rather than something to bulk-patch outside
the review process now.

- `rashi-yoma-011b-015`: `before its height rose three. New comment: 'and it is` -> `before its height rose three: and it is`
- `rashi-yoma-012b-002`: `...High Priesthood. New comment: 'their anointing consecrated them' - as it is written` -> `...High Priesthood. 'Their anointing consecrated them' - as it is written`
- `rashi-yoma-013b-001`: `...since her get is not a get. New comment: 'on condition you do not enter [the synagogue], etc.' -` -> `...since her get is not a get. 'On condition you do not enter [the synagogue], etc.' -`

By contrast, `rashi-yoma-020a-001` in this same batch legitimately uses
"Mishna:" as a structural label - because a real Mishnah genuinely begins
there. The distinction a reviewer must make: a label is fabricated when
nothing in the Hebrew marks a structural transition: it is correct when
one actually does (a new Mishnah, a new Gemara passage). Both cases appear
in this batch as a direct contrast.

### Cross-entry word anticipation (3 occurrences, all newly found)

Three entries (`rashi-yoma-015a-003`, `rashi-yoma-020b-023`,
`rashi-yoma-023a-005`) show the same shape of defect first found in batch 1
(`rashi-yoma-002a-011`): a word that belongs to THIS entry's own Hebrew was
translated one entry early (or late) by a NEIGHBORING entry, leaving this
entry's own English missing that word entirely. In all three cases here,
the neighboring entry that "borrowed" the word is outside the frozen pilot
cohort, so only the in-cohort entry was corrected - the out-of-cohort
neighbor is left untouched, per the campaign's explicit rule that entries
outside the cohort remain UNREVIEWED. This may read slightly redundant
when the two entries are viewed back to back (e.g. "...it comes out. Its
fellow comes out with it...") until the neighboring entry itself receives
review in a later phase; that is a pre-existing cross-entry style
imperfection, not a new defect introduced by this fix.

- `rashi-yoma-015a-003`: this entry's own Hebrew begins "חכמים" (the Sages), but old EN starts directly with "half a log" - "the Sages" appears instead as an anticipatory addition in the neighboring (out-of-cohort) entry's translation. Fixed: `half a log for each lamp...` -> `The Sages: half a log for each lamp...`
- `rashi-yoma-020b-023`: this entry's own Hebrew ends "דנפישי" (since they are many), but old EN renders only the bare connector "Since" - "many/numerous" appears instead in the neighboring (out-of-cohort) entry. Fixed: `'Since'` -> `'Since [the offerings] are many'`
- `rashi-yoma-023a-005`: this entry's own Hebrew ends "יוצאה" (comes out), but old EN ends "its fellow" - a word ("חבירתה") that belongs to the *next* entry, borrowed early; this entry's own "comes out" only appears in the next entry's translation. Fixed: `...its fellow` -> `...it comes out`

## Detector precision (this batch, n=50)

All 6 defects found in this batch carried **zero** automated risk signals
(riskScore 0 for all 6). Both defect families identified above (fabricated
scaffold narration, cross-entry word anticipation) are outside every
existing Step 2 detector's design - none of them check for narration
phrases beyond a fixed pattern list, and none compare an entry's English
against its *neighbors'* Hebrew to detect anticipation/lag. This
reinforces batch 1's finding: automated triage is a useful entry-selection
aid but catches only a minority of real translation defects; the corpus-
wide defect rate cannot be estimated from risk scores alone.

## Validation and deployment evidence

- `python3 modules/yoma/scripts/check_rashi_pr_scope.py --base origin/main` - OK, 6 learning JSON files, only `en` changed
- `npm run check:rashi-translation-inventory:yoma` - inventory matches live corpus exactly
- `npm run validate:offline:yoma` - all gates pass
- `python3 modules/yoma/scripts/audit_rashi_association.py --exhaustive-corpus` - 8,854 entries, 0 broken, 0 cross-daf, unchanged
- `python3 modules/yoma/scripts/validate_rashi_boundary_authorizations.py` - 20/20, unchanged
- `npm test`, `npm run test:browser`, `npm run build`, `npm run check:deploy-html` - all pass
- Hebrew text confirmed byte-unchanged (git diff against origin/main shows only 6 `en:` lines differ)
- 8,754 of 8,854 entries remain `UNREVIEWED` after this batch
