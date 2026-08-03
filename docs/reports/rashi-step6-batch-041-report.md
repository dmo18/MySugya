# Rashi translation-quality campaign, Step 6 batch 041 report

Batch `step6-batch-041` of the full-corpus review defined in
`docs/reports/rashi-full-corpus-review-strategy.md` (Step 5). Full
per-entry evidence lives in
`docs/reports/data/rashi-step6-batch-041-review-records.json` (validated
against the Step 5 contract).

## Batch scope (frozen from the committed batch plan, unmodified)

- **Batch id**: `step6-batch-041`
- **Perek**: 8
- **Daf**: 87b, 88a (2 daf)
- **Tier**: `normal`
- **Entries**: 125
- **Risk-tier counts** (Step 2 automated triage, advisory only): high 0, medium 11, zero-risk 114
- **Historical-provenance counts** (Step 1): `content-reviewed` 125
- **Estimated changed count** (Step 5 projection): 13.7

Re-generated and re-validated (`generate_rashi_batch_progress.py`,
`generate_rashi_translation_inventory.py --check`) at the start of this
batch against current main to confirm the batch manifest entry is
unmodified and still selects exactly these 125 entries, that all 125 were
still UNREVIEWED, and that they were assigned only to `step6-batch-041`
(0 overlap with any other batch). A fresh review packet
(`generate_rashi_review_packets.py --batch-id step6-batch-041`) was
regenerated and confirmed byte-identical to the packet actually reviewed.
No entry outside the batch was edited. The confirmed changed count (38) is
under the 40-changes-per-PR cap, so no child-PR split or rollout
declaration was needed; this batch is a single ordinary PR.

## Method

Every entry was reviewed against its own Hebrew, its linked Gemara/Mishnah
context, neighboring Rashi entries (required wherever a Vilna line ends
mid-clause or mid-comment), the style guide, and the terminology registry -
never from the existing English alone. Risk scores and systemic-candidate
membership were treated as advisory only; a signal is a reason to look
closer, not a verdict.

**First pass**: all 125 entries reviewed individually. Result: 87
VERIFIED, 38 MINOR_EDIT, 0 SUBSTANTIVE_REPAIR, 0 RETRANSLATE, 0
DUPLICATION_OR_CONTAMINATION, 0 BLOCKED.

**Second pass**: 100% of the 38 MINOR_EDIT entries independently
re-reviewed (re-derived from Hebrew and context again, restarting from the
Hebrew rather than checking the proposed English). Result: **38/38
CONFIRMED**, 0 MODIFIED, 0 REJECTED, 0 REMAINED_BLOCKED.

**Blind QA**: a deterministic 13.8% sample (12 of the 87 provisionally
VERIFIED entries) was selected two ways, both fixed before any evidence
text was read and independent of first-pass reasoning: (1) every 9th entry
in the batch's canonical VERIFIED-entry order (10 entries: positions 0, 9,
18, ... 81), and (2) since that positional rule happened to land only on
zero-risk entries, the first risk-signaled provisionally-VERIFIED entry on
each daf not already captured by rule (1) was added (2 entries:
`rashi-yoma-087b-017` and `rashi-yoma-088a-006`), so the sample covers both
signaled and zero-risk entries on both daf as required. No entry was
replaced after selection. Result: **12/12 CONFIRMED_VERIFIED, 0
escalations.** Per the escalation rule, no expansion of the sample was
required.

## Systemic-candidate review

### Family 1: fabricated "New comment:" scaffold text

38 of this batch's 125 entries (30.4%) carry this defect, the same
dominant pattern already confirmed in batch 040.

**Root cause, confirmed against the raw source**: this daf range again has
Vilna print lines carrying more than one short Rashi comment on the same
physical line (`modules/yoma/assets/talmuddev/{87b,88a}.json`'s `rashi[]`
array shows a mid-line Hebrew colon wherever this happens). The original
AI-helper translation pass inserted the literal English label `"New
comment: "` at each such boundary instead of following the corpus's own
established convention (plain, unlabeled `'<next fragment>' - <comment>`,
e.g. `rashi-yoma-002a-001`). This label has **no Hebrew basis at all** -
the Hebrew colon is Vilna punctuation, never the words "new comment" - and
is exactly the class of fabricated structural narration this campaign's
own worker-prompt convention already forbids.

**Disposition for all 38: CONFIRMED_DEFECT.** Fix: remove the literal
string `"New comment: "` and let the next quoted fragment begin directly,
per the corpus's own established convention - verified individually for
every occurrence that the remaining text, once joined, is grammatically
coherent and semantically unchanged (the underlying translation content
was already accurate in every case checked; only the fabricated label is
removed). MINOR_EDIT, defect tag `INVENTED_TEXT` (fabricated text with no
Hebrew basis; the surrounding translation's meaning is not affected).

No new systemic family was created for this PR. The full per-entry
old/new English pairs are below and are also recorded in the
review-records file.

| Entry | Original English | Corrected English |
|---|---|---|
| `rashi-yoma-087b-001` | New comment: 'Rabbi Chiya came' - he too wished to recite the portion with him, and he returned for his sake to the beginning of | 'Rabbi Chiya came' - he too wished to recite the portion with him, and he returned for his sake to the beginning of |
| `rashi-yoma-087b-002` | the passage. New comment: 'Rav is different' - he was stringent with himself. New comment: 'he saw a dream about Rav' - he saw | the passage. 'Rav is different' - he was stringent with himself. 'he saw a dream about Rav' - he saw |
| `rashi-yoma-087b-009` | the head, and I will not be pushed aside to die for his sake. New comment: 'with' | the head, and I will not be pushed aside to die for his sake. 'with' |
| `rashi-yoma-087b-011` | Yom Kippur. New comment: 'lest his mind become confused' - on account of | Yom Kippur. 'lest his mind become confused' - on account of |
| `rashi-yoma-087b-012` | drunkenness. New comment: 'a matter of ruin' - of sin. | drunkenness. 'a matter of ruin' - of sin. |
| `rashi-yoma-087b-013` | New comment: 'from the depths of the heart' - it is a prayer. New comment: 'in Your Torah' | 'from the depths of the heart' - it is a prayer. 'in Your Torah' |
| `rashi-yoma-087b-014` | it is written - referring to 'for on this day He shall atone.' New comment: 'Master' | it is written - referring to 'for on this day He shall atone.' 'Master' |
| `rashi-yoma-087b-016` | New comment: 'on a fast day' - of rain. New comment: 'and at the ma'amadot' - | 'on a fast day' - of rain. 'and at the ma'amadot' - |
| `rashi-yoma-087b-028` | in a day. New comment: 'an additional prayer' - he prays the Amidah of seven blessings | in a day. 'an additional prayer' - he prays the Amidah of seven blessings |
| `rashi-yoma-087b-029` | like the other prayers. New comment: 'and Shmuel said, what' | like the other prayers. 'and Shmuel said, what' |
| `rashi-yoma-087b-031` | New comment: 'the night of Yom Kippur' - the eve of Yom Kippur. | 'the night of Yom Kippur' - the eve of Yom Kippur. |
| `rashi-yoma-087b-032` | New comment: 'and concludes with confession' - this is how it reads in the Tosefta: he does not | 'and concludes with confession' - this is how it reads in the Tosefta: he does not |
| `rashi-yoma-087b-034` | who forgives. New comment: 'and the Sages say' - wherever | who forgives. 'and the Sages say' - wherever |
| `rashi-yoma-087b-042` | view, indeed a refutation. New comment: 'he came down before Rava' - at Ne'ila, | view, indeed a refutation. 'he came down before Rava' - at Ne'ila, |
| `rashi-yoma-087b-045` | and one said: the closing of the gates of the Temple courtyard. New comment: 'and since' | and one said: the closing of the gates of the Temple courtyard. 'and since' |
| `rashi-yoma-087b-046` | he has prayed - once it becomes dark, he no longer needs it. New comment: 'but' | he has prayed - once it becomes dark, he no longer needs it. 'but' |
| `rashi-yoma-087b-050` | New comment: 'they raised an objection, etc.' - it teaches Ne'ila and it teaches | 'they raised an objection, etc.' - it teaches Ne'ila and it teaches |
| `rashi-yoma-087b-051` | Arvit separately. New comment: 'seven resembling eighteen' - | Arvit separately. 'seven resembling eighteen' - |
| `rashi-yoma-088a-001` | New comment: 'it is a matter of Tannaitic dispute' - whether Ne'ila exempts the evening prayer or not. New comment: 'this is how we read' | 'it is a matter of Tannaitic dispute' - whether Ne'ila exempts the evening prayer or not. 'this is how we read' |
| `rashi-yoma-088a-003` | and the woman who gave birth immerse in their usual way on the night of Yom Kippur. New comment: 'one with a seminal emission' - who is forbidden to engage in words of Torah, | and the woman who gave birth immerse in their usual way on the night of Yom Kippur. 'one with a seminal emission' - who is forbidden to engage in words of Torah, |
| `rashi-yoma-088a-004` | as we hold (Bava Kamma 82a): Ezra instituted immersion for those with a seminal emission. New comment: 'he immerses' | as we hold (Bava Kamma 82a): Ezra instituted immersion for those with a seminal emission. 'he immerses' |
| `rashi-yoma-088a-018` | evening prayer. New comment: 'this is how we read in the Tosefta' - the zav and the zavah, | evening prayer. 'this is how we read in the Tosefta' - the zav and the zavah, |
| `rashi-yoma-088a-026` | New comment: 'it is not difficult' - this is where Rabbi Yosei said here, | 'it is not difficult' - this is where Rabbi Yosei said here, |
| `rashi-yoma-088a-028` | New comment: 'where he prayed the Ne'ila prayer' - during the day, before | 'where he prayed the Ne'ila prayer' - during the day, before |
| `rashi-yoma-088a-031` | the emission. New comment: 'if he prayed, what is the reasoning' | the emission. 'if he prayed, what is the reasoning' |
| `rashi-yoma-088a-033` | all day. New comment: 'the Rabbis hold that immersion at its proper time' | all day. 'the Rabbis hold that immersion at its proper time' |
| `rashi-yoma-088a-044` | is a mitzvah. New comment: 'he shall not wash' - so that he does not erase | is a mitzvah. 'he shall not wash' - so that he does not erase |
| `rashi-yoma-088a-045` | the Name. New comment: 'he wraps a reed around it' - to protect it from | the Name. 'he wraps a reed around it' - to protect it from |
| `rashi-yoma-088a-046` | the flow of water. New comment: 'and we hold' | the flow of water. 'and we hold' |
| `rashi-yoma-088a-049` | and seeks one. New comment: 'that ruling' - that which we said above, 'Rabbi Yosei says: from Mincha onward | and seeks one. 'that ruling' - that which we said above, 'Rabbi Yosei says: from Mincha onward |
| `rashi-yoma-088a-051` | Yehuda's view. New comment: 'it is sufficient for the immersion to be the last one' - it is a Baraita | Yehuda's view. 'it is sufficient for the immersion to be the last one' - it is a Baraita |
| `rashi-yoma-088a-059` | Yosei ben Chalafta. New comment: 'and in the evening he shall rub' - on account of an interposition. New comment: 'in the evening, does this occur to you?' - | Yosei ben Chalafta. 'and in the evening he shall rub' - on account of an interposition. 'in the evening, does this occur to you?' - |
| `rashi-yoma-088a-061` | New comment: 'say instead, from the evening before' - that the day before, every person should rub himself with hot water, so that if he sees | 'say instead, from the evening before' - that the day before, every person should rub himself with hot water, so that if he sees |
| `rashi-yoma-088a-062` | a seminal emission the next day, he can immerse without an interposition. New comment: 'one who sees a seminal emission on Yom Kippur' - and not | a seminal emission the next day, he can immerse without an interposition. 'one who sees a seminal emission on Yom Kippur' - and not |
| `rashi-yoma-088a-063` | intentionally. New comment: 'his sins are forgiven' - this is a good sign: 'he shall see offspring and prolong his days.' New comment: 'he shall worry all year' - lest his fast was not accepted, and they satiated him | intentionally. 'his sins are forgiven' - this is a good sign: 'he shall see offspring and prolong his days.' 'he shall worry all year' - lest his fast was not accepted, and they satiated him |
| `rashi-yoma-088a-064` | with what is in their power to satiate him, like a servant who pours a cup for his master and then pours a pitcher of water on his face. New comment: 'and if his year passes well for him' - that he did not die, it is guaranteed that he has | with what is in their power to satiate him, like a servant who pours a cup for his master and then pours a pitcher of water on his face. 'and if his year passes well for him' - that he did not die, it is guaranteed that he has |
| `rashi-yoma-088a-065` | good deeds that protected him, and he is a person of the World to Come. New comment: 'know, for the whole world is hungry' - for marital relations, and he is satiated; and he did not fast in this, and it was not | good deeds that protected him, and he is a person of the World to Come. 'know, for the whole world is hungry' - for marital relations, and he is satiated; and he did not fast in this, and it was not |
| `rashi-yoma-088a-066` | by his own will that he was satiated, and nevertheless his year passed well for him - one must know that he is a completely righteous person. New comment: 'prolongs life' - this refers to the one who saw a seminal emission on Yom Kippur. New comment: 'suffices and causes to suffice' - | by his own will that he was satiated, and nevertheless his year passed well for him - one must know that he is a completely righteous person. 'prolongs life' - this refers to the one who saw a seminal emission on Yom Kippur. 'suffices and causes to suffice' - |

### Family 2: cross-entry word anticipation

1 candidate in this batch (`rashi-yoma-087b-057`), a daf-boundary
single-word stub: Hebrew `תנאי` (3 characters), English `"This ('a matter
of Tannaitic dispute') continues on 88a."`. **Disposition:
FALSE_POSITIVE.** This family reuses the Step 2 OVEREXPLAINED signal
(explicitly documented as low-precision for this specific defect) as its
candidate list; this entry was flagged purely because a single-Hebrew-word
source makes any English annotation look disproportionately long by the
length-ratio heuristic, not because any word was actually imported from a
neighboring entry. No anticipation defect is present. Left unchanged,
VERIFIED.

## Other risk-signaled entries (outside both systemic families)

8 additional medium-risk entries were flagged by Step 2's automated triage
but fall outside both authorized systemic-candidate families:
`rashi-yoma-087b-017`, `rashi-yoma-087b-025`, `rashi-yoma-087b-048`,
`rashi-yoma-087b-049`, `rashi-yoma-087b-053`, `rashi-yoma-088a-006`,
`rashi-yoma-088a-017`, `rashi-yoma-088a-021`. All 8 were confirmed
**FALSE_POSITIVE** for their respective signals: this corpus splits Rashi
comments across Vilna-line entries, so a line ending mid-clause is the
normal, correct shape of a continuing entry - confirmed in every case by
reading the immediately following vilnaLine entry, which completes the
clause. All 8 are VERIFIED. Two of these (`rashi-yoma-087b-017` and
`rashi-yoma-088a-006`) were also included in the blind-QA sample above and
independently reconfirmed there.

No advisory pattern observations beyond the two authorized families were
noted for this batch.

## Aggregate results (125 entries)

| Disposition | Count | Rate |
|---|---|---|
| VERIFIED | 87 | 69.6% |
| MINOR_EDIT | 38 | 30.4% |
| SUBSTANTIVE_REPAIR | 0 | 0.0% |
| RETRANSLATE | 0 | 0.0% |
| DUPLICATION_OR_CONTAMINATION | 0 | 0.0% |
| BLOCKED | 0 | 0.0% |
| **Total** | **125** | **100%** |

**Changed-translation count: 38** (all applied in this PR, 18 on daf 87b,
20 on daf 88a). Second-pass results: 38/38 CONFIRMED. Defect-tag totals:
`INVENTED_TEXT` 38 (all from the "New comment:" scaffold family; no other
defect tag occurred in this batch).

No BLOCKED entries and no structural, Hebrew, boundary, or association
defects were found anywhere in this batch. No boundary-fingerprint refresh
was needed (batch 041 makes no structural or boundary-adjacent change).

## Regression and platform evidence

- Rashi entry count: 8,854 (unchanged) - Associations: 10,061 declared, 0
  broken, 0 cross-daf (unchanged) - Boundary registry: 20/20 (unchanged)
- Hebrew text: byte-unchanged across all 125 entries in this batch
- `npm run validate:offline:yoma`, `npm test`, `npm run test:browser`,
  `npm run build`, `npm run check:deploy-html`, `python3
  scripts/worker_pipeline.py verify --full`: all green
- `python3 modules/yoma/scripts/generate_rashi_batch_progress.py` reports
  `step6-batch-041` as `complete` (not partial): 852 of 8,854 entries
  reviewed full-corpus (727 pre-batch + 125 this batch), 8,002 remain
  UNREVIEWED
- Per the directive, a fresh exhaustive 8-shard browser dispatch was not
  required for this batch (single ordinary PR, no structural or
  boundary-sensitive behavior changed) and was not run; the standard
  `npm run test:browser` Playwright gate (which already covers Yoma
  rendering and Rashi display) passed as part of this PR's own validation.

## Status

**Batch 041: COMPLETE.** All 125 entries reviewed with an assigned final
disposition in a single PR; 0 entries left in an ambiguous state; 0
BLOCKED. Final disposition totals: 87 VERIFIED, 38 MINOR_EDIT, 0
SUBSTANTIVE_REPAIR, 0 RETRANSLATE, 0 DUPLICATION_OR_CONTAMINATION, 0
BLOCKED. Changed-translation count: 38 (all `INVENTED_TEXT`, the "New
comment:" scaffold family). Second pass: 38/38 CONFIRMED. Blind QA: 12/12
CONFIRMED_VERIFIED, 0 escalations. Both authorized systemic-candidate
families resolved (scaffold: 38 CONFIRMED_DEFECT, applied; anticipation: 1
FALSE_POSITIVE, unchanged). Full-corpus progress: 852 of 8,854 entries
reviewed, 8,002 remain UNREVIEWED. Step 6 status: **IN PROGRESS**;
`step6-batch-042` (or any other later batch) has **not** been started.
