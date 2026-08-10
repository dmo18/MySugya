# Yoma tail-enrichment audit (77a-88a) - provenance-first semantic review
Audit-only pass. **No production corpus, Rashi, association, source-text, schema, renderer, validator or workflow file was modified.**
- Audited SHA: `3aa90cde8c50f8489e2e7ca6f4bbe7ffe034f9d5`
- VERSION at audit: 15.482
- Reviewed: **116** sugyot (82 primary cohort, 22+12 controls)

## Provenance boundary
display.whats/display.hint and the finalRuling-copied-from-hint pattern exist at the initial squash commit be03ff9. The Batch 16-18 canonical-schema backfill then derived display.title and learning.* from those already-defective fields, amplifying a pre-existing generation defect rather than introducing it.

Decisive evidence:
- `git log -S` places the truncated `finalRuling` stem and the `display.hint` text in the initial squash commit `be03ff9`; only `display.title` and `learning.*` first appear in `8906923` (Batch 17, 80a-84b).
- Reading `be03ff9` directly across the 76b/77a seam shows the authoring mode change: at 76a/76b `display.hint` is a short **question** and `finalRuling` an **independent halakhic statement**; from 77a `display.hint` becomes a descriptive paragraph and `finalRuling` is a verbatim copy of it, hard-cut at 149-150 characters when longer.
- The mechanical signature (`finalRuling` derived from `display.hint`) occurs in **82 sugyot across 23 daf and is confined exactly to 77a-88a**, with zero occurrences in 2a-76b.
- The backfill campaign boundaries (Batch 16 = 75a-79b, Batch 17 = 80a-84b, Batch 18 = 85a-88a) do **not** align with 77a. The cohort boundary is therefore a property of the pre-squash generation, not of the backfill.

**Conclusion: 77a-88a is a real historical generation cohort, not merely an observed symptom boundary.** The backfill amplified it into the canonical display/learning fields.

## Totals

| Disposition | Count |
|---|---|
| VERIFIED | 83 |
| SUBSTANTIVE_REPAIR_NEEDED | 24 |
| MINOR_EDIT_NEEDED | 9 |

| Defect tag | Count |
|---|---|
| WRONG_TOPIC | 28 |
| TRUNCATED | 6 |
| INVENTED_CLAIM | 6 |
| CROSS_FIELD_CONTRADICTION | 3 |
| WRONG_SPEAKER | 3 |
| TEMPLATE_CONTAMINATION | 2 |
| WRONG_RULING | 2 |
| OMITTED_SOURCE_MATERIAL | 1 |
| WRONG_SOURCE_REF | 1 |

## Confirmed defects (substantive)

Every record below carries a completed independent second pass. `argumentFlow` is correct in **all** of them; the defect is confined to `display` and `learning`.

### yoma-077a-s01 (77a) - WRONG_TOPIC, TRUNCATED, TEMPLATE_CONTAMINATION
- Source lines: `yoma-077a-l01`, `yoma-077a-l09`, `yoma-077a-l18`, `yoma-077a-l22`, `yoma-077a-l29`, `yoma-077a-l35`, `yoma-077a-l39`, `yoma-077a-l43`
- Affected fields: `display.title`, `display.whats`, `display.hint`, `learning.learnerQuestion`, `learning.coreMove`, `learning.coreTension`, `finalRuling`
- Evidence: Source is the Ezekiel 8-9 aggada (image of jealousy, Michael pleading, Gabriel and the coals, Dubiel and the Persian angel). display/learning describe 'bathing prohibition derived from verse; Ezekiel's anointing vision' - a topic absent from these 8 lines. argumentFlow is correct ('Ezekiel's vision of sun-worshippers', 'Michael pleads, Gabriel is sent to scatter the coals').

### yoma-077a-s03 (77a) - WRONG_TOPIC
- Source lines: `yoma-077a-l53`, `yoma-077a-l55`, `yoma-077a-l59`
- Affected fields: `display.title`, `display.whats`, `display.hint`, `learning.learnerQuestion`, `learning.coreMove`
- Evidence: Source derives that going barefoot is affliction (Isaiah 20:2, Jeremiah 2:25). display/learning describe pleasure vs therapeutic anointing and Na'aman - the topic of a different sugya. argumentFlow correct ('Deriving the shoe affliction from Jeremiah').

### yoma-077a-s04 (77a) - WRONG_TOPIC
- Source lines: `yoma-077a-l61`
- Affected fields: `display.title`, `display.whats`, `display.hint`, `learning.learnerQuestion`, `learning.coreMove`
- Evidence: Source derives that withholding conjugal relations is affliction. display/learning describe the sandal prohibition (the preceding sugya's subject). argumentFlow correct ('Deriving that withholding marital relations is affliction').

### yoma-077b-s02 (77b) - WRONG_TOPIC
- Source lines: `yoma-077b-l09`, `yoma-077b-l13`, `yoma-077b-l14`
- Affected fields: `display.title`, `display.whats`, `display.hint`, `learning.learnerQuestion`, `learning.coreMove`
- Evidence: Source is partial bathing/oiling, Rabban Shimon ben Gamliel on rinsing one hand, Shammai the Elder. display/learning describe marital relations as the fifth affliction. argumentFlow correct.

### yoma-078a-s03 (78a) - WRONG_TOPIC
- Source lines: `yoma-078a-l19`, `yoma-078a-l22`, `yoma-078a-l25`, `yoma-078a-l30`
- Affected fields: `display.title`, `display.whats`, `display.hint`, `learning.learnerQuestion`, `learning.coreMove`
- Evidence: Source is sitting on damp clay and cooling methods (Rabba's baby, Rava's silver cup, the pre-soaked cloth). display/learning describe a sick person wearing shoes. argumentFlow correct.

### yoma-078b-s03 (78b) - WRONG_TOPIC
- Source lines: `yoma-078b-l37`, `yoma-078b-l41`, `yoma-078b-l44a`, `yoma-078b-l44b`
- Affected fields: `display.title`, `display.whats`, `display.hint`, `learning.learnerQuestion`
- Evidence: Source: Rabbi Eliezer permits the king and bride to WASH THEIR FACES; a new mother may wear shoes; scorpion danger. display says the king wears shoes for honour. argumentFlow correct ('Who permits the king and bride to wash their faces?').

### yoma-080a-s01 (80a) - WRONG_RULING, CROSS_FIELD_CONTRADICTION
- Source lines: `yoma-080a-l01`, `yoma-080a-l05`
- Affected fields: `display.title`, `display.whats`, `learning.learnerQuestion`
- Evidence: Source: 'All the measures in the Torah connected to eating are the volume of an OLIVE-bulk, except...'. display asserts all Torah eating measures are EGG-bulk - the opposite. argumentFlow states it correctly ('All eating measures are an olive-bulk, with exceptions'), so display contradicts argumentFlow within the same sugya.

### yoma-080a-s02 (80a) - WRONG_TOPIC, INVENTED_CLAIM
- Source lines: `yoma-080a-l07`, `yoma-080a-l12`, `yoma-080a-l14`, `yoma-080a-l17`, `yoma-080a-l20`, `yoma-080a-l23`, `yoma-080a-l24`, `yoma-080a-l25`, `yoma-080a-l28`, `yoma-080a-l31`
- Affected fields: `display.title`, `display.whats`, `learning.learnerQuestion`
- Evidence: Source derives the EGG-BULK measure for IMPURE FOOD (Rabbi Abbahu, 'of all food which may be eaten'). display claims the YK eating measure is derived by gezerah shavah from matzah - no such derivation appears in these lines. argumentFlow correct.

### yoma-080b-s01 (80b) - WRONG_SPEAKER, WRONG_TOPIC
- Source lines: `yoma-080b-l01`, `yoma-080b-l02`, `yoma-080b-l08`, `yoma-080b-l12`, `yoma-080b-l17`, `yoma-080b-l20`, `yoma-080b-l23`
- Affected fields: `display.title`, `display.whats`, `learning.learnerQuestion`
- Evidence: Source is Rabbi Zeira's three objections and Rava's objection about the liquid measure (incl. Og of Bashan). display describes Rav and Shmuel measuring each other's cheeks - neither name occurs in the sugya. argumentFlow correct.

### yoma-080b-s03 (80b) - WRONG_RULING, CROSS_FIELD_CONTRADICTION
- Source lines: `yoma-080b-l32`, `yoma-080b-l34`
- Affected fields: `display.title`, `display.whats`, `learning.learnerQuestion`
- Evidence: Reish Lakish rules that one who eats in an excessive manner (achila gassa) on Yom Kippur is EXEMPT. display asserts overeating 'creates liability even without swallowing'. argumentFlow states the exemption correctly.

### yoma-082a-s02 (82a) - WRONG_TOPIC
- Source lines: `yoma-082a-l13`, `yoma-082a-l17`, `yoma-082a-l19`, `yoma-082a-l22`
- Affected fields: `display.title`, `display.whats`, `learning.learnerQuestion`
- Evidence: Source continues the mishna on TRAINING children to fast (Rabbi Yochanan, Rabba bar Shmuel's baraita, training vs completing). display describes saving a child's life overriding YK. argumentFlow correct.

### yoma-082a-s04 (82a) - WRONG_TOPIC
- Source lines: `yoma-082a-l33`, `yoma-082a-l35`
- Affected fields: `display.title`, `display.whats`, `learning.learnerQuestion`
- Evidence: Source is martyrdom (yehareg ve'al ya'avor) for forbidden relations and murder. display frames it as pikuach nefesh overriding YK - the opposite direction of the halakha. argumentFlow correct ('Source for martyrdom over relations and murder').

### yoma-082b-s01 (82b) - WRONG_TOPIC, INVENTED_CLAIM, TRUNCATED, TEMPLATE_CONTAMINATION, CROSS_FIELD_CONTRADICTION
- Source lines: `yoma-082b-l01`
- Affected fields: `display.title`, `display.whats`, `display.hint`, `learning.learnerQuestion`, `learning.coreTension`, `learning.coreMove`, `learning.ahaMoment`, `learning.learningBlocker`, `learning.memoryAnchor`, `learning.takeaway`, `finalRuling`
- Evidence: Source (yoma-082b-l01) is the sevara that one must accept death rather than commit murder: 'who says your blood is redder than his?' (the mari duray case before Rava). Every display and learning field instead describes whether Yom Kippur is violated to save a murderer's life - a question absent from the source. display.hint is additionally cut with a literal ellipsis ('...is ex...') and finalRuling is a 150-char truncated copy of that hint ('The tension betwee'). argumentFlow step-01 and the quiz material render the real sugya correctly.

### yoma-082b-s02 (82b) - WRONG_SPEAKER, OMITTED_SOURCE_MATERIAL, TRUNCATED
- Source lines: `yoma-082b-l06`, `yoma-082b-l09`
- Affected fields: `display.title`, `display.whats`, `display.hint`, `learning.learnerQuestion`, `learning.coreMove`, `finalRuling`
- Evidence: The sugya has two stories: Rabbi Yehuda HaNasi (the whisper worked) and Rabbi Chanina (the whisper did NOT work; he read the verse about the baby). 'R. Yannai' occurs nowhere in the Hebrew or English of either line. All display/learning fields attribute the whisper to R. Yannai and omit the Rabbi Chanina story entirely, losing the contrast that is the point of the pair. argumentFlow names Rabbi Yehuda HaNasi correctly.

### yoma-083b-s03 (83b) - WRONG_TOPIC, INVENTED_CLAIM
- Source lines: `yoma-083b-l29`, `yoma-083b-l33`, `yoma-083b-l34`, `yoma-083b-l36`, `yoma-083b-l37`, `yoma-083b-l38`
- Affected fields: `display.title`, `display.whats`, `learning.learnerQuestion`
- Evidence: Source is the Rabbi Meir / Rabbi Yehuda / Rabbi Yosei innkeeper narrative (reading the host's name, the dream, the withheld purse, recovering it via wine). display describes them treating a STUDENT WITH BULMOS - no student and no bulmos episode occurs in these lines. argumentFlow correct.

### yoma-084a-s03 (84a) - INVENTED_CLAIM, WRONG_TOPIC
- Source lines: `yoma-084a-l27`, `yoma-084a-l30`, `yoma-084a-l32`, `yoma-084a-l35`, `yoma-084a-l39`
- Affected fields: `display.title`, `display.whats`, `learning.learnerQuestion`
- Evidence: Source discusses TZEFIDNA (a gum/tooth disease from hot bread) and yerakon remedies. display names the illness 'Tzefardea' and glosses it as a 'snake-related illness'; tzefardea means frog and the disease in the sugya is tzefidna. argumentFlow uses 'tzefidna' correctly.

### yoma-084b-s01 (84b) - INVENTED_CLAIM, WRONG_TOPIC
- Source lines: `yoma-084b-l01`, `yoma-084b-l09`
- Affected fields: `display.title`, `display.whats`, `learning.learnerQuestion`
- Evidence: Propagates the 'Tzefardea' misnaming from 084a-s03 and attributes the proof to a 'Rabba bar Shela incident'; the source cites Rabba bar Shmuel's baraita and Rav Ashi on the mishna's wording.

### yoma-086b-s02 (86b) - WRONG_TOPIC
- Source lines: `yoma-086b-l20`, `yoma-086b-l23`, `yoma-086b-l26`
- Affected fields: `display.title`, `display.whats`, `learning.learnerQuestion`
- Evidence: Source: Rabbi Yitzchak in the name of Rabba bar Mari contrasting God with a human who has been wronged - God is appeased by words alone; Rabbi Meir on one penitent saving the world. display describes 'cancel your evil decree before the New Year', which is not in these lines. argumentFlow correct.

### yoma-086b-s03 (86b) - WRONG_TOPIC
- Source lines: `yoma-086b-l28`, `yoma-086b-l29`
- Affected fields: `display.title`, `display.whats`, `learning.learnerQuestion`
- Evidence: Source asks what demonstrates COMPLETE REPENTANCE and whether to publicise a sin (Rav Yehuda citing Rav). display describes chilul Hashem for Torah scholars - the subject of 086a-s03. argumentFlow correct.

### yoma-086b-s05 (86b) - WRONG_TOPIC
- Source lines: `yoma-086b-l36`, `yoma-086b-l38`, `yoma-086b-l41`, `yoma-086b-l44`, `yoma-086b-l46`, `yoma-086b-l49`, `yoma-086b-l51`, `yoma-086b-l53`
- Affected fields: `display.title`, `display.whats`, `learning.learnerQuestion`
- Evidence: Source is the Tosefta on NOT re-confessing sins already confessed, Rabbi Eliezer ben Yaakov, detailing the sin, and the Moses/David parable. display describes 'transgressions against teachers and communal chilul Hashem'. argumentFlow correct.

### yoma-087a-s01 (87a) - WRONG_TOPIC
- Source lines: `yoma-087a-l01`
- Affected fields: `display.title`, `display.whats`, `learning.learnerQuestion`
- Evidence: Source is Rava's self-admonition before sitting in judgement ('of his own will he goes to die'). display frames it as a halakhic distinction between willing and forced death. argumentFlow correct ('Rava's words before judging').

### yoma-087a-s02 (87a) - WRONG_TOPIC
- Source lines: `yoma-087a-l08`, `yoma-087a-l12`, `yoma-087a-l17`, `yoma-087a-l21`, `yoma-087a-l26`
- Affected fields: `display.title`, `display.whats`, `learning.learnerQuestion`
- Evidence: Source expounds 'It is not good to respect the person of the wicked' and the merit/liability the righteous and wicked bring on others. display describes YK not atoning without appeasing the wronged party - the subject of 087a-s05. argumentFlow correct.

### yoma-087b-s01 (87b) - WRONG_SPEAKER
- Source lines: `yoma-087b-l01`, `yoma-087b-l06`, `yoma-087b-l10`
- Affected fields: `display.title`, `display.whats`, `learning.learnerQuestion`
- Evidence: The slighted party in the source is RABBI CHANINA (Rav restarted the portion when Rabbi Chiyya entered; Rabbi Chanina saw the dream and withheld forgiveness). display casts the story as Rav appeasing R. Chiyya and R. Chiyya refusing. argumentFlow names Rabbi Chanina correctly.

### yoma-087b-s03 (87b) - WRONG_TOPIC, INVENTED_CLAIM
- Source lines: `yoma-087b-l41`, `yoma-087b-l45`, `yoma-087b-l49`, `yoma-087b-l51`, `yoma-087b-l52`, `yoma-087b-l53`, `yoma-087b-l54`
- Affected fields: `display.title`, `display.whats`, `learning.learnerQuestion`
- Evidence: Source is the NE'ILA sugya (priestly blessing three/four times a year, whether ne'ila is a full Amida, Ulla bar Rav before Rava, ne'ila exempting ma'ariv). display describes 'Closing of Tractate Yoma: Hadran formula; Tu BeAv' - neither the Hadran nor Tu BeAv appears in these lines. argumentFlow correct.

## Malformed but semantically recoverable

84 cohort sugyot carry the mechanical `finalRuling`-from-`hint` signature. These are separable from the semantic defects:

- Where the underlying `display.hint` is **correct**, `finalRuling` is merely a bad truncated copy and the sugya is otherwise VERIFIED.
- Where the underlying `hint` is **itself wrong** (e.g. `yoma-082b-s01`, `yoma-087b-s02`, `yoma-088a-s01`), restoring the full hint text would propagate the error. **Automatic restoration by extending the hint is explicitly not recommended.**

## Minor edits

- **yoma-077b-s01** (77b): WRONG_TOPIC, TRUNCATED - whats/hint claim the verse yields the fast obligation; the source (Laban, 'if you afflict my daughters', Rav Pappa/Shechem) concerns conjugal deprivation. learning.coreMove states this correctly, so only display is wrong
- **yoma-077b-s03** (77b): WRONG_TOPIC - Sugya is about crossing water to greet a father/teacher and Rava/Rav Yosef permitting crossings; display reduces it to 'greeting and visiting', omitting the water-crossing halakha that is the actual subject.
- **yoma-078a-s02** (78a): WRONG_TOPIC - Source is shoes/sandals while crossing water and the Rafram/Ravina exchange; display frames it purely as whether crossing constitutes prohibited bathing.
- **yoma-084b-s03** (84b): WRONG_SOURCE_REF - Source is a baraita ('The Sages taught') about saving life on SHABBAT; display labels it a Tosefta about Yom Kippur.
- **yoma-086a-s02** (86a): WRONG_TOPIC - Sugya's substance is Rabbi Matya ben Charash's question to Rabbi Elazar ben Azarya about the categories/paths of atonement; display reduces it to defining 'bearing God's name in vain'.
- **yoma-087a-s03** (87a): WRONG_TOPIC - Source treats 'I will sin and repent' (doubled) and 'I will sin and YK will atone'; display generalises to the scope of YK's atonement power.
- **yoma-087a-s04** (87a): WRONG_TOPIC - Display posits 'communal sins with a Godward dimension'; the source is the mishna's God/person division and Rav Yosef bar Chavu's rereading of the verse's second clause.
- **yoma-087b-s02** (87b): WRONG_TOPIC, TRUNCATED - Source: the main mitzva of confession is on Yom Kippur EVE at nightfall, with the Sages adding an earlier confession before eating. display asserts vidui is 'primary at Minha, optional earlier'. hint carries a literal el
- **yoma-088a-s01** (88a): WRONG_TOPIC, TRUNCATED - Source combines havdala placement with the immersion rules for a ba'al keri and the Rabbi Yosei contradiction; display covers only havdala. hint ends in a literal ellipsis; finalRuling is its truncated copy.

## False positives withdrawn

- **`yoma-083b-s02`** - the prior pass labelled this 'topic drift'. Withdrawn: the declared line range genuinely spans both the ben Teima / first tanna dispute on tevel vs teruma severity *and* the bulmos remedies, so framing it as two tannaitic approaches to treating bulmos is accurate. Disposition **VERIFIED**.
- **`display.whats` lacking terminal punctuation (172 values)** - phrase-style summaries, not truncation.
- **`NAME_NOT_IN_SOURCE` outside the cohort (17 sugyot)** - dominated by legitimate cross-daf back-references (e.g. `yoma-005a-s01` citing Reish Lakish's challenge from 3b) and by names that sit just outside a sugya's declared line range. No fabrication confirmed outside 77a-88a.

## Controls and results

- **73b-76b (22 sugyot, immediately preceding generation):** 0 substantive defects, 0 mechanical signature occurrences. The preceding campaign is clean.
- **12 sugyot from perakim 1-6**, selected independently of any defect signal: 0 substantive defects.
- Deterministic corroboration: within the cohort `argumentFlow` matches its own source **5.1x** better than `display` does (Jaccard 0.293 vs 0.057); in every control band the two are comparable (~1.2x). This is the quantitative form of the defect - `argumentFlow` tracks the source while `display`/`learning` do not.
- **No control exposed the defect family, so the cohort was not expanded.**

## Contract decisions (must precede repair)

1. `finalRuling` semantics for this cohort: independent halakhic statement (the pre-77a convention) versus summary copy. Repair shape depends on the answer.
2. Whether `display.hint` in the cohort should remain a descriptive paragraph or revert to the pre-77a question form.
3. Whether `argumentFlow` may be used as the repair source for `display`/`learning`, given it is authored evidence and not ground truth.

## Unresolved

- The 82 mechanical-signature sugyot need a per-sugya decision on whether the underlying `hint` is sound before any `finalRuling` restoration.
- Whether the pre-squash generator's misalignment also affected fields not audited here (`concepts`, `conceptRefs` are unpopulated corpus-wide and were not assessable).

## Recommended repair sequencing

1. **Contract decisions above** - nothing else is safe first.
2. **`yoma-082b-s01`, `yoma-087b-s03`, `yoma-080a-s01`, `yoma-080b-s03`** - highest severity: fabricated framing or a ruling that directly contradicts the source and the sugya's own `argumentFlow`.
3. Remaining `SUBSTANTIVE_REPAIR_NEEDED` records, daf order, one PR per daf.
4. `MINOR_EDIT_NEEDED` records.
5. **Last:** the mechanical `finalRuling` truncation, once each underlying `hint` has been adjudicated. Repairing it earlier would destroy the strongest remaining locator for defective records.
