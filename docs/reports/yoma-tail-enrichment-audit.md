# Yoma tail-enrichment audit (77a-88a) - provenance-first semantic review

Audit-only. **No production corpus, generated runtime data, Rashi content, association, source text, schema contract, renderer, validator, workflow or application file is modified.**

- Audited SHA: `3aa90cde8c50f8489e2e7ca6f4bbe7ffe034f9d5` · VERSION at audit: 15.482
- Reviewed: **116** sugyot - **82** in the primary cohort (77a-88a) plus 34 controls
- Mechanical inventory is reproducible: `python3 docs/reports/tools/yoma_tail_enrichment_audit.py [--check]`

## Provenance boundary

display.whats/display.hint and the finalRuling-copied-from-hint pattern exist at the initial squash commit be03ff9. The Batch 16-18 canonical-schema backfill then derived display.title and learning.* from those already-defective fields, amplifying a pre-existing generation defect rather than introducing it.

Decisive evidence:

- `git log -S` places the truncated `finalRuling` stem and the `display.hint` text in the initial squash commit `be03ff9`; only `display.title` and `learning.*` first appear in `8906923` (Batch 17, 80a-84b).
- Reading `be03ff9` across the 76b/77a seam shows the authoring mode change: at 76a/76b `display.hint` is a short **question** and `finalRuling` an **independent halakhic statement**; from 77a `display.hint` becomes a descriptive paragraph and `finalRuling` is a verbatim copy of it, hard-cut at 149-150 characters when longer.
- The signature occurs in **82 sugyot** and is confined exactly to 77a-88a, with zero occurrences in 2a-76b.
- Backfill batch boundaries (Batch 16 = 75a-79b, Batch 17 = 80a-84b, Batch 18 = 85a-88a) do **not** align with 77a.

**Conclusion: 77a-88a is a real historical generation cohort.** The backfill amplified a pre-existing defect into the canonical display/learning fields.

## Field coverage and the extent of contamination

**Correction to an earlier revision of this report:** A previous revision of this report stated that concepts is unpopulated corpus-wide. That was wrong: concepts is populated on all 492 Yoma sugyot, and in the defective records concepts.narrative/theological carry the same generator-derived interpretation as display.whats.

In every defective record examined, argumentFlow, misconceptions and quizSeeds track the declared source correctly. The contaminated set is display.*, learning.*, concepts, topicTags, visualizableElements, requiresUnderstanding, finalRuling and the parent daf summary.

This matters for repair: `argumentFlow`, `misconceptions` and `quizSeeds` are usable as corroborating evidence when reconstructing the contaminated fields, though they remain authored evidence and not ground truth.

Fields assessed for every record: `daf.summary`, `display.*`, `learning.*`, `argumentFlow.*(speaker,type,label,text,sourceRefs)`, `concepts`, `conceptRefs`, `requiresUnderstanding`, `misconceptions`, `quizSeeds`, `topicTags`, `visualizableElements`, `finalRuling`, `difficulty`, `alternateAngles`, `review`.

## Disposition model

overallDisposition = the more severe of semanticDisposition and mechanicalDisposition under severityOrder.

- Any record carrying FR_TRUNCATED_PREFIX_OF_HINT has mechanicalDisposition at least MINOR_EDIT_NEEDED, so it can never be overall VERIFIED.
- FR_EXACT_COPY_OF_HINT yields mechanicalDisposition STRUCTURAL_OR_SCHEMA_DECISION because its correctness depends on the unresolved finalRuling-semantics contract.
- Severity order: `VERIFIED` < `MINOR_EDIT_NEEDED` < `STRUCTURAL_OR_SCHEMA_DECISION` < `SUBSTANTIVE_REPAIR_NEEDED` < `RETRANSLATE_OR_RECONSTRUCT` < `BLOCKED`

### Semantic totals

| Disposition | Count |
|---|---|
| VERIFIED | 83 |
| MINOR_EDIT_NEEDED | 9 |
| SUBSTANTIVE_REPAIR_NEEDED | 24 |
| **Total** | **116** |

### Mechanical totals

| Disposition | Count |
|---|---|
| VERIFIED | 34 |
| MINOR_EDIT_NEEDED | 53 |
| STRUCTURAL_OR_SCHEMA_DECISION | 29 |
| **Total** | **116** |

### Overall totals

| Disposition | Count |
|---|---|
| VERIFIED | 34 |
| MINOR_EDIT_NEEDED | 39 |
| STRUCTURAL_OR_SCHEMA_DECISION | 19 |
| SUBSTANTIVE_REPAIR_NEEDED | 24 |
| **Total** | **116** |

### Mechanical flags

| Flag | Count |
|---|---|
| FR_150_CUTOFF | 55 |
| FR_TRUNCATED_PREFIX_OF_HINT | 53 |
| FR_EXACT_COPY_OF_HINT | 29 |
| HINT_TRAILING_ELLIPSIS | 9 |

### Semantic defect tags

| Tag | Count |
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

**Why the `TRUNCATED` tag total differs from the mechanical truncation count.** The TRUNCATED defect tag (6 records) is a SEMANTIC tag: it was applied only where truncation formed part of the semantic finding for that sugya. The mechanical dimension counts every occurrence independently: 53 FR_TRUNCATED_PREFIX_OF_HINT and 29 FR_EXACT_COPY_OF_HINT. The two totals therefore differ by design and are not reconcilable to one number.

## Confirmed semantic defects

Every record below carries a completed second pass with a record-specific source fact. In all of them `argumentFlow`, `misconceptions` and `quizSeeds` render the real sugya correctly.

### yoma-077a-s01 (77a) - WRONG_TOPIC, TRUNCATED, TEMPLATE_CONTAMINATION

- Overall: **SUBSTANTIVE_REPAIR_NEEDED** (semantic SUBSTANTIVE_REPAIR_NEEDED / mechanical MINOR_EDIT_NEEDED)
- Source lines: `yoma-077a-l01`, `yoma-077a-l09`, `yoma-077a-l18`, `yoma-077a-l22`, `yoma-077a-l29`, `yoma-077a-l35`, `yoma-077a-l39`, `yoma-077a-l43`
- Affected fields (14): `<daf>.summary`, `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`, `display.hint`, `display.title`, `display.whats`, `finalRuling`, `learning.coreMove`, `learning.coreTension`, `learning.learnerQuestion`, `requiresUnderstanding`, `topicTags`, `visualizableElements[].name`
- First pass: Source is the Ezekiel 8-9 aggada (image of jealousy, Michael pleading, Gabriel and the coals, Dubiel and the Persian angel). display/learning describe 'bathing prohibition derived from verse; Ezekiel's anointing vision' - a topic absent from these 8 lines. argumentFlow is correct ('Ezekiel's vision of sun-worshippers', 'Michael pleads, Gabriel is sent to scatter the coals').
- Second pass (AGREE): Re-read yoma-077a-l01..l43 from Sefaria English: the lines are Ezekiel 8:3-9:11 exposition, Michael's plea, Gabriel and the cooled embers, Dubiel and the Persian angel's letter. No verse-derivation of bathing occurs anywhere in the eight lines.
- Registered owners: display-only-edit, gemara-learning, learning-copy-edit, structural-repair (allowStructure), summary-edit
- Unowned paths: `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`
- Prerequisite contract decisions: `hint-form`, `finalRuling-semantics`, `requiresUnderstanding-semantics`
- Atomic task decision required: yes - Affected paths span several registered owners AND include paths with no registered owner.

### yoma-077a-s03 (77a) - WRONG_TOPIC

- Overall: **SUBSTANTIVE_REPAIR_NEEDED** (semantic SUBSTANTIVE_REPAIR_NEEDED / mechanical MINOR_EDIT_NEEDED)
- Source lines: `yoma-077a-l53`, `yoma-077a-l55`, `yoma-077a-l59`
- Affected fields (12): `<daf>.summary`, `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`, `display.hint`, `display.title`, `display.whats`, `finalRuling`, `learning.coreMove`, `learning.learnerQuestion`, `requiresUnderstanding`, `topicTags`
- First pass: Source derives that going barefoot is affliction (Isaiah 20:2, Jeremiah 2:25). display/learning describe pleasure vs therapeutic anointing and Na'aman - the topic of a different sugya. argumentFlow correct ('Deriving the shoe affliction from Jeremiah').
- Second pass (AGREE): Independently recovered: the three lines derive going barefoot as affliction from Isaiah 20:2 and Jeremiah 2:25. Na'aman and therapeutic anointing do not appear.
- Registered owners: display-only-edit, gemara-learning, learning-copy-edit, structural-repair (allowStructure), summary-edit
- Unowned paths: `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`
- Prerequisite contract decisions: `hint-form`, `finalRuling-semantics`, `requiresUnderstanding-semantics`
- Atomic task decision required: yes - Affected paths span several registered owners AND include paths with no registered owner.

### yoma-077a-s04 (77a) - WRONG_TOPIC

- Overall: **SUBSTANTIVE_REPAIR_NEEDED** (semantic SUBSTANTIVE_REPAIR_NEEDED / mechanical STRUCTURAL_OR_SCHEMA_DECISION)
- Source lines: `yoma-077a-l61`
- Affected fields (12): `<daf>.summary`, `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`, `display.hint`, `display.title`, `display.whats`, `finalRuling`, `learning.coreMove`, `learning.learnerQuestion`, `requiresUnderstanding`, `topicTags`
- First pass: Source derives that withholding conjugal relations is affliction. display/learning describe the sandal prohibition (the preceding sugya's subject). argumentFlow correct ('Deriving that withholding marital relations is affliction').
- Second pass (AGREE): Independently recovered: the single line asks whence refraining from conjugal relations is called affliction. The sandal prohibition is the preceding sugya's subject, not this one's.
- Registered owners: display-only-edit, gemara-learning, learning-copy-edit, structural-repair (allowStructure), summary-edit
- Unowned paths: `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`
- Prerequisite contract decisions: `hint-form`, `finalRuling-semantics`, `requiresUnderstanding-semantics`
- Atomic task decision required: yes - Affected paths span several registered owners AND include paths with no registered owner.

### yoma-077b-s02 (77b) - WRONG_TOPIC

- Overall: **SUBSTANTIVE_REPAIR_NEEDED** (semantic SUBSTANTIVE_REPAIR_NEEDED / mechanical STRUCTURAL_OR_SCHEMA_DECISION)
- Source lines: `yoma-077b-l09`, `yoma-077b-l13`, `yoma-077b-l14`
- Affected fields (13): `<daf>.summary`, `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`, `display.hint`, `display.title`, `display.whats`, `finalRuling`, `learning.coreMove`, `learning.learnerQuestion`, `requiresUnderstanding`, `topicTags`, `visualizableElements[].name`
- First pass: Source is partial bathing/oiling, Rabban Shimon ben Gamliel on rinsing one hand, Shammai the Elder. display/learning describe marital relations as the fifth affliction. argumentFlow correct.
- Second pass (AGREE): Independently recovered: the lines forbid partial bathing/oiling, record Rabban Shimon ben Gamliel on rinsing one hand, and Shammai the Elder's stringency. Marital relations are not discussed.
- Registered owners: display-only-edit, gemara-learning, learning-copy-edit, structural-repair (allowStructure), summary-edit
- Unowned paths: `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`
- Prerequisite contract decisions: `hint-form`, `finalRuling-semantics`, `requiresUnderstanding-semantics`
- Atomic task decision required: yes - Affected paths span several registered owners AND include paths with no registered owner.

### yoma-078a-s03 (78a) - WRONG_TOPIC

- Overall: **SUBSTANTIVE_REPAIR_NEEDED** (semantic SUBSTANTIVE_REPAIR_NEEDED / mechanical STRUCTURAL_OR_SCHEMA_DECISION)
- Source lines: `yoma-078a-l19`, `yoma-078a-l22`, `yoma-078a-l25`, `yoma-078a-l30`
- Affected fields (13): `<daf>.summary`, `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`, `display.hint`, `display.title`, `display.whats`, `finalRuling`, `learning.coreMove`, `learning.learnerQuestion`, `requiresUnderstanding`, `topicTags`, `visualizableElements[].name`
- First pass: Source is sitting on damp clay and cooling methods (Rabba's baby, Rava's silver cup, the pre-soaked cloth). display/learning describe a sick person wearing shoes. argumentFlow correct.
- Second pass (AGREE): Independently recovered: prohibition on sitting on damp clay, Rabba cooling with a baby, Rava with a silver cup, and the pre-soaked wrung-out cloth. No sick person and no shoes appear.
- Registered owners: display-only-edit, gemara-learning, learning-copy-edit, structural-repair (allowStructure), summary-edit
- Unowned paths: `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`
- Prerequisite contract decisions: `hint-form`, `finalRuling-semantics`, `requiresUnderstanding-semantics`
- Atomic task decision required: yes - Affected paths span several registered owners AND include paths with no registered owner.

### yoma-078b-s03 (78b) - WRONG_TOPIC

- Overall: **SUBSTANTIVE_REPAIR_NEEDED** (semantic SUBSTANTIVE_REPAIR_NEEDED / mechanical MINOR_EDIT_NEEDED)
- Source lines: `yoma-078b-l37`, `yoma-078b-l41`, `yoma-078b-l44a`, `yoma-078b-l44b`
- Affected fields (12): `<daf>.summary`, `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`, `display.hint`, `display.title`, `display.whats`, `finalRuling`, `learning.learnerQuestion`, `requiresUnderstanding`, `topicTags`, `visualizableElements[].name`
- First pass: Source: Rabbi Eliezer permits the king and bride to WASH THEIR FACES; a new mother may wear shoes; scorpion danger. display says the king wears shoes for honour. argumentFlow correct ('Who permits the king and bride to wash their faces?').
- Second pass (AGREE): Independently recovered: Rabbi Eliezer permits the king and the bride to WASH THEIR FACES; separately a new mother may wear shoes, and shoes are permitted where scorpions threaten. The king is never said to wear shoes.
- Registered owners: display-only-edit, gemara-learning, learning-copy-edit, structural-repair (allowStructure), summary-edit
- Unowned paths: `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`
- Prerequisite contract decisions: `hint-form`, `finalRuling-semantics`, `requiresUnderstanding-semantics`
- Atomic task decision required: yes - Affected paths span several registered owners AND include paths with no registered owner.

### yoma-080a-s01 (80a) - WRONG_RULING, CROSS_FIELD_CONTRADICTION

- Overall: **SUBSTANTIVE_REPAIR_NEEDED** (semantic SUBSTANTIVE_REPAIR_NEEDED / mechanical MINOR_EDIT_NEEDED)
- Source lines: `yoma-080a-l01`, `yoma-080a-l05`
- Affected fields (11): `<daf>.summary`, `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`, `display.title`, `display.whats`, `finalRuling`, `learning.learnerQuestion`, `requiresUnderstanding`, `topicTags`, `visualizableElements[].name`
- First pass: Source: 'All the measures in the Torah connected to eating are the volume of an OLIVE-bulk, except...'. display asserts all Torah eating measures are EGG-bulk - the opposite. argumentFlow states it correctly ('All eating measures are an olive-bulk, with exceptions'), so display contradicts argumentFlow within the same sugya.
- Second pass (AGREE): Independently recovered from the first line verbatim: 'All the measures in the Torah connected to eating are the volume of an olive-bulk, except...'. The universal measure is the olive-bulk; egg-bulk is the exception for impure food.
- Registered owners: display-only-edit, gemara-learning, learning-copy-edit, structural-repair (allowStructure), summary-edit
- Unowned paths: `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`
- Prerequisite contract decisions: `finalRuling-semantics`, `requiresUnderstanding-semantics`
- Atomic task decision required: yes - Affected paths span several registered owners AND include paths with no registered owner.

### yoma-080a-s02 (80a) - WRONG_TOPIC, INVENTED_CLAIM

- Overall: **SUBSTANTIVE_REPAIR_NEEDED** (semantic SUBSTANTIVE_REPAIR_NEEDED / mechanical MINOR_EDIT_NEEDED)
- Source lines: `yoma-080a-l07`, `yoma-080a-l12`, `yoma-080a-l14`, `yoma-080a-l17`, `yoma-080a-l20`, `yoma-080a-l23`, `yoma-080a-l24`, `yoma-080a-l25`, `yoma-080a-l28`, `yoma-080a-l31`
- Affected fields (11): `<daf>.summary`, `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`, `display.title`, `display.whats`, `finalRuling`, `learning.learnerQuestion`, `requiresUnderstanding`, `topicTags`, `visualizableElements[].name`
- First pass: Source derives the EGG-BULK measure for IMPURE FOOD (Rabbi Abbahu, 'of all food which may be eaten'). display claims the YK eating measure is derived by gezerah shavah from matzah - no such derivation appears in these lines. argumentFlow correct.
- Second pass (AGREE): Independently recovered: Rabbi Abbahu derives the EGG-BULK measure for IMPURE FOOD from 'of all food which may be eaten'. There is no matzah gezerah shavah and no YK measure derivation in these lines.
- Registered owners: display-only-edit, gemara-learning, learning-copy-edit, structural-repair (allowStructure), summary-edit
- Unowned paths: `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`
- Prerequisite contract decisions: `finalRuling-semantics`, `requiresUnderstanding-semantics`
- Atomic task decision required: yes - Affected paths span several registered owners AND include paths with no registered owner.

### yoma-080b-s01 (80b) - WRONG_SPEAKER, WRONG_TOPIC

- Overall: **SUBSTANTIVE_REPAIR_NEEDED** (semantic SUBSTANTIVE_REPAIR_NEEDED / mechanical STRUCTURAL_OR_SCHEMA_DECISION)
- Source lines: `yoma-080b-l01`, `yoma-080b-l02`, `yoma-080b-l08`, `yoma-080b-l12`, `yoma-080b-l17`, `yoma-080b-l20`, `yoma-080b-l23`
- Affected fields (11): `<daf>.summary`, `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`, `display.title`, `display.whats`, `finalRuling`, `learning.learnerQuestion`, `requiresUnderstanding`, `topicTags`, `visualizableElements[].name`
- First pass: Source is Rabbi Zeira's three objections and Rava's objection about the liquid measure (incl. Og of Bashan). display describes Rav and Shmuel measuring each other's cheeks - neither name occurs in the sugya. argumentFlow correct.
- Second pass (AGREE): Independently recovered: the objections are Rabbi Zeira's (three of them) and Rava's, concerning whether the liquid measure is relative to body size, including the Og of Bashan case. Neither Rav nor Shmuel appears.
- Registered owners: display-only-edit, gemara-learning, learning-copy-edit, structural-repair (allowStructure), summary-edit
- Unowned paths: `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`
- Prerequisite contract decisions: `finalRuling-semantics`, `requiresUnderstanding-semantics`
- Atomic task decision required: yes - Affected paths span several registered owners AND include paths with no registered owner.

### yoma-080b-s03 (80b) - WRONG_RULING, CROSS_FIELD_CONTRADICTION

- Overall: **SUBSTANTIVE_REPAIR_NEEDED** (semantic SUBSTANTIVE_REPAIR_NEEDED / mechanical STRUCTURAL_OR_SCHEMA_DECISION)
- Source lines: `yoma-080b-l32`, `yoma-080b-l34`
- Affected fields (11): `<daf>.summary`, `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`, `display.title`, `display.whats`, `finalRuling`, `learning.learnerQuestion`, `requiresUnderstanding`, `topicTags`, `visualizableElements[].name`
- First pass: Reish Lakish rules that one who eats in an excessive manner (achila gassa) on Yom Kippur is EXEMPT. display asserts overeating 'creates liability even without swallowing'. argumentFlow states the exemption correctly.
- Second pass (AGREE): Independently recovered: Reish Lakish rules one who eats in an excessive manner (achila gassa) on Yom Kippur is EXEMPT, and the same for a non-priest eating teruma gassa. The source states exemption, not liability.
- Registered owners: display-only-edit, gemara-learning, learning-copy-edit, structural-repair (allowStructure), summary-edit
- Unowned paths: `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`
- Prerequisite contract decisions: `finalRuling-semantics`, `requiresUnderstanding-semantics`
- Atomic task decision required: yes - Affected paths span several registered owners AND include paths with no registered owner.

### yoma-082a-s02 (82a) - WRONG_TOPIC

- Overall: **SUBSTANTIVE_REPAIR_NEEDED** (semantic SUBSTANTIVE_REPAIR_NEEDED / mechanical STRUCTURAL_OR_SCHEMA_DECISION)
- Source lines: `yoma-082a-l13`, `yoma-082a-l17`, `yoma-082a-l19`, `yoma-082a-l22`
- Affected fields (11): `<daf>.summary`, `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`, `display.title`, `display.whats`, `finalRuling`, `learning.learnerQuestion`, `requiresUnderstanding`, `topicTags`, `visualizableElements[].name`
- First pass: Source continues the mishna on TRAINING children to fast (Rabbi Yochanan, Rabba bar Shmuel's baraita, training vs completing). display describes saving a child's life overriding YK. argumentFlow correct.
- Second pass (AGREE): Independently recovered: the lines continue the mishna on training children, Rabbi Yochanan on completing the fast, Rabba bar Shmuel's baraita, and whether training equals completing. No danger-to-life case appears.
- Registered owners: display-only-edit, gemara-learning, learning-copy-edit, structural-repair (allowStructure), summary-edit
- Unowned paths: `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`
- Prerequisite contract decisions: `finalRuling-semantics`, `requiresUnderstanding-semantics`
- Atomic task decision required: yes - Affected paths span several registered owners AND include paths with no registered owner.

### yoma-082a-s04 (82a) - WRONG_TOPIC

- Overall: **SUBSTANTIVE_REPAIR_NEEDED** (semantic SUBSTANTIVE_REPAIR_NEEDED / mechanical STRUCTURAL_OR_SCHEMA_DECISION)
- Source lines: `yoma-082a-l33`, `yoma-082a-l35`
- Affected fields (11): `<daf>.summary`, `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`, `display.title`, `display.whats`, `finalRuling`, `learning.learnerQuestion`, `requiresUnderstanding`, `topicTags`, `visualizableElements[].name`
- First pass: Source is martyrdom (yehareg ve'al ya'avor) for forbidden relations and murder. display frames it as pikuach nefesh overriding YK - the opposite direction of the halakha. argumentFlow correct ('Source for martyrdom over relations and murder').
- Second pass (AGREE): Independently recovered: the lines concern surrendering one's life rather than committing forbidden relations or murder, and how the murder case teaches in both directions. This is martyrdom law, the converse of pikuach nefesh overriding.
- Registered owners: display-only-edit, gemara-learning, learning-copy-edit, structural-repair (allowStructure), summary-edit
- Unowned paths: `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`
- Prerequisite contract decisions: `finalRuling-semantics`, `requiresUnderstanding-semantics`
- Atomic task decision required: yes - Affected paths span several registered owners AND include paths with no registered owner.

### yoma-082b-s01 (82b) - WRONG_TOPIC, INVENTED_CLAIM, TRUNCATED, TEMPLATE_CONTAMINATION, CROSS_FIELD_CONTRADICTION

- Overall: **SUBSTANTIVE_REPAIR_NEEDED** (semantic SUBSTANTIVE_REPAIR_NEEDED / mechanical MINOR_EDIT_NEEDED)
- Source lines: `yoma-082b-l01`
- Affected fields (18): `<daf>.summary`, `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`, `display.hint`, `display.title`, `display.whats`, `finalRuling`, `learning.ahaMoment`, `learning.coreMove`, `learning.coreTension`, `learning.learnerQuestion`, `learning.learningBlocker`, `learning.memoryAnchor`, `learning.takeaway`, `requiresUnderstanding`, `topicTags`, `visualizableElements[].name`
- First pass: Source (yoma-082b-l01) is the sevara that one must accept death rather than commit murder: 'who says your blood is redder than his?' (the mari duray case before Rava). Every display and learning field instead describes whether Yom Kippur is violated to save a murderer's life - a question absent from the source. display.hint is additionally cut with a literal ellipsis ('...is ex...') and finalRuling is a 150-char truncated copy of that hint ('The tension betwee'). argumentFlow step-01 and the quiz material render the real sugya correctly.
- Second pass (AGREE): Independently recovered from yoma-082b-l01 verbatim: 'And with regard to the murderer himself, from where do we derive...that he should be killed rather than transgress' - the mari duray case before Rava and 'what makes you think your blood is redder?'. The sugya never asks whether YK is violated for a murderer.
- Registered owners: display-only-edit, gemara-learning, learning-copy-edit, structural-repair (allowStructure), summary-edit
- Unowned paths: `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`
- Prerequisite contract decisions: `hint-form`, `finalRuling-semantics`, `requiresUnderstanding-semantics`
- Atomic task decision required: yes - Affected paths span several registered owners AND include paths with no registered owner.

### yoma-082b-s02 (82b) - WRONG_SPEAKER, OMITTED_SOURCE_MATERIAL, TRUNCATED

- Overall: **SUBSTANTIVE_REPAIR_NEEDED** (semantic SUBSTANTIVE_REPAIR_NEEDED / mechanical MINOR_EDIT_NEEDED)
- Source lines: `yoma-082b-l06`, `yoma-082b-l09`
- Affected fields (13): `<daf>.summary`, `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`, `display.hint`, `display.title`, `display.whats`, `finalRuling`, `learning.coreMove`, `learning.learnerQuestion`, `requiresUnderstanding`, `topicTags`, `visualizableElements[].name`
- First pass: The sugya has two stories: Rabbi Yehuda HaNasi (the whisper worked) and Rabbi Chanina (the whisper did NOT work; he read the verse about the baby). 'R. Yannai' occurs nowhere in the Hebrew or English of either line. All display/learning fields attribute the whisper to R. Yannai and omit the Rabbi Chanina story entirely, losing the contrast that is the point of the pair. argumentFlow names Rabbi Yehuda HaNasi correctly.
- Second pass (AGREE): Independently recovered: yoma-082b-l06 names Rabbi Yehuda HaNasi (whisper succeeded) and yoma-082b-l09 names Rabbi Chanina (whisper failed; he read the verse about the baby). A string search for 'Yannai' and 'ינאי' across both lines returns nothing.
- Registered owners: display-only-edit, gemara-learning, learning-copy-edit, structural-repair (allowStructure), summary-edit
- Unowned paths: `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`
- Prerequisite contract decisions: `hint-form`, `finalRuling-semantics`, `requiresUnderstanding-semantics`
- Atomic task decision required: yes - Affected paths span several registered owners AND include paths with no registered owner.

### yoma-083b-s03 (83b) - WRONG_TOPIC, INVENTED_CLAIM

- Overall: **SUBSTANTIVE_REPAIR_NEEDED** (semantic SUBSTANTIVE_REPAIR_NEEDED / mechanical MINOR_EDIT_NEEDED)
- Source lines: `yoma-083b-l29`, `yoma-083b-l33`, `yoma-083b-l34`, `yoma-083b-l36`, `yoma-083b-l37`, `yoma-083b-l38`
- Affected fields (11): `<daf>.summary`, `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`, `display.title`, `display.whats`, `finalRuling`, `learning.learnerQuestion`, `requiresUnderstanding`, `topicTags`, `visualizableElements[].name`
- First pass: Source is the Rabbi Meir / Rabbi Yehuda / Rabbi Yosei innkeeper narrative (reading the host's name, the dream, the withheld purse, recovering it via wine). display describes them treating a STUDENT WITH BULMOS - no student and no bulmos episode occurs in these lines. argumentFlow correct.
- Second pass (AGREE): Independently recovered: Rabbi Meir, Rabbi Yehuda and Rabbi Yosei lodge with an innkeeper; Rabbi Meir reads the host's name, a dream discloses the purse, the host denies the deposit, and wine loosens his tongue. No student and no bulmos episode occurs.
- Registered owners: display-only-edit, gemara-learning, learning-copy-edit, structural-repair (allowStructure), summary-edit
- Unowned paths: `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`
- Prerequisite contract decisions: `finalRuling-semantics`, `requiresUnderstanding-semantics`
- Atomic task decision required: yes - Affected paths span several registered owners AND include paths with no registered owner.

### yoma-084a-s03 (84a) - INVENTED_CLAIM, WRONG_TOPIC

- Overall: **SUBSTANTIVE_REPAIR_NEEDED** (semantic SUBSTANTIVE_REPAIR_NEEDED / mechanical MINOR_EDIT_NEEDED)
- Source lines: `yoma-084a-l27`, `yoma-084a-l30`, `yoma-084a-l32`, `yoma-084a-l35`, `yoma-084a-l39`
- Affected fields (11): `<daf>.summary`, `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`, `display.title`, `display.whats`, `finalRuling`, `learning.learnerQuestion`, `requiresUnderstanding`, `topicTags`, `visualizableElements[].name`
- First pass: Source discusses TZEFIDNA (a gum/tooth disease from hot bread) and yerakon remedies. display names the illness 'Tzefardea' and glosses it as a 'snake-related illness'; tzefardea means frog and the disease in the sugya is tzefidna. argumentFlow uses 'tzefidna' correctly.
- Second pass (AGREE): Independently recovered: the disease under discussion is tzefidna, said to come from eating over-hot wheat bread, with yerakon remedies alongside. 'Tzefardea' (frog) does not occur, and nothing connects the illness to snakes.
- Registered owners: display-only-edit, gemara-learning, learning-copy-edit, structural-repair (allowStructure), summary-edit
- Unowned paths: `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`
- Prerequisite contract decisions: `finalRuling-semantics`, `requiresUnderstanding-semantics`
- Atomic task decision required: yes - Affected paths span several registered owners AND include paths with no registered owner.

### yoma-084b-s01 (84b) - INVENTED_CLAIM, WRONG_TOPIC

- Overall: **SUBSTANTIVE_REPAIR_NEEDED** (semantic SUBSTANTIVE_REPAIR_NEEDED / mechanical MINOR_EDIT_NEEDED)
- Source lines: `yoma-084b-l01`, `yoma-084b-l09`
- Affected fields (11): `<daf>.summary`, `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`, `display.title`, `display.whats`, `finalRuling`, `learning.learnerQuestion`, `requiresUnderstanding`, `topicTags`, `visualizableElements[].name`
- First pass: Propagates the 'Tzefardea' misnaming from 084a-s03 and attributes the proof to a 'Rabba bar Shela incident'; the source cites Rabba bar Shmuel's baraita and Rav Ashi on the mishna's wording.
- Second pass (AGREE): Independently recovered: the proof is Rabba bar Shmuel's baraita listing Rabbi Matya's three cases plus Rav Ashi's reading of the mishna's wording. No 'Rabba bar Shela' appears, and the disease name is tzefidna.
- Registered owners: display-only-edit, gemara-learning, learning-copy-edit, structural-repair (allowStructure), summary-edit
- Unowned paths: `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`
- Prerequisite contract decisions: `finalRuling-semantics`, `requiresUnderstanding-semantics`
- Atomic task decision required: yes - Affected paths span several registered owners AND include paths with no registered owner.

### yoma-086b-s02 (86b) - WRONG_TOPIC

- Overall: **SUBSTANTIVE_REPAIR_NEEDED** (semantic SUBSTANTIVE_REPAIR_NEEDED / mechanical MINOR_EDIT_NEEDED)
- Source lines: `yoma-086b-l20`, `yoma-086b-l23`, `yoma-086b-l26`
- Affected fields (11): `<daf>.summary`, `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`, `display.title`, `display.whats`, `finalRuling`, `learning.learnerQuestion`, `requiresUnderstanding`, `topicTags`, `visualizableElements[].name`
- First pass: Source: Rabbi Yitzchak in the name of Rabba bar Mari contrasting God with a human who has been wronged - God is appeased by words alone; Rabbi Meir on one penitent saving the world. display describes 'cancel your evil decree before the New Year', which is not in these lines. argumentFlow correct.
- Second pass (AGREE): Independently recovered: Rabbi Yitzchak in the name of Rabba bar Mari contrasts God with a wronged human - God is appeased by words alone - and Rabbi Meir adds that one penitent can bring forgiveness to the world. No New Year decree-cancelling appears.
- Registered owners: display-only-edit, gemara-learning, learning-copy-edit, structural-repair (allowStructure), summary-edit
- Unowned paths: `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`
- Prerequisite contract decisions: `finalRuling-semantics`, `requiresUnderstanding-semantics`
- Atomic task decision required: yes - Affected paths span several registered owners AND include paths with no registered owner.

### yoma-086b-s03 (86b) - WRONG_TOPIC

- Overall: **SUBSTANTIVE_REPAIR_NEEDED** (semantic SUBSTANTIVE_REPAIR_NEEDED / mechanical STRUCTURAL_OR_SCHEMA_DECISION)
- Source lines: `yoma-086b-l28`, `yoma-086b-l29`
- Affected fields (11): `<daf>.summary`, `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`, `display.title`, `display.whats`, `finalRuling`, `learning.learnerQuestion`, `requiresUnderstanding`, `topicTags`, `visualizableElements[].name`
- First pass: Source asks what demonstrates COMPLETE REPENTANCE and whether to publicise a sin (Rav Yehuda citing Rav). display describes chilul Hashem for Torah scholars - the subject of 086a-s03. argumentFlow correct.
- Second pass (AGREE): Independently recovered: the lines ask what demonstrates complete repentance and cite Rav Yehuda in the name of Rav on when a sin should be publicised. Chilul Hashem for scholars is 086a-s03's subject.
- Registered owners: display-only-edit, gemara-learning, learning-copy-edit, structural-repair (allowStructure), summary-edit
- Unowned paths: `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`
- Prerequisite contract decisions: `finalRuling-semantics`, `requiresUnderstanding-semantics`
- Atomic task decision required: yes - Affected paths span several registered owners AND include paths with no registered owner.

### yoma-086b-s05 (86b) - WRONG_TOPIC

- Overall: **SUBSTANTIVE_REPAIR_NEEDED** (semantic SUBSTANTIVE_REPAIR_NEEDED / mechanical STRUCTURAL_OR_SCHEMA_DECISION)
- Source lines: `yoma-086b-l36`, `yoma-086b-l38`, `yoma-086b-l41`, `yoma-086b-l44`, `yoma-086b-l46`, `yoma-086b-l49`, `yoma-086b-l51`, `yoma-086b-l53`
- Affected fields (11): `<daf>.summary`, `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`, `display.title`, `display.whats`, `finalRuling`, `learning.learnerQuestion`, `requiresUnderstanding`, `topicTags`, `visualizableElements[].name`
- First pass: Source is the Tosefta on NOT re-confessing sins already confessed, Rabbi Eliezer ben Yaakov, detailing the sin, and the Moses/David parable. display describes 'transgressions against teachers and communal chilul Hashem'. argumentFlow correct.
- Second pass (AGREE): Independently recovered: the Tosefta forbids re-confessing an already-confessed sin, Rabbi Eliezer ben Yaakov dissents, and the Moses/David parable follows. Transgressions against teachers do not appear.
- Registered owners: display-only-edit, gemara-learning, learning-copy-edit, structural-repair (allowStructure), summary-edit
- Unowned paths: `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`
- Prerequisite contract decisions: `finalRuling-semantics`, `requiresUnderstanding-semantics`
- Atomic task decision required: yes - Affected paths span several registered owners AND include paths with no registered owner.

### yoma-087a-s01 (87a) - WRONG_TOPIC

- Overall: **SUBSTANTIVE_REPAIR_NEEDED** (semantic SUBSTANTIVE_REPAIR_NEEDED / mechanical STRUCTURAL_OR_SCHEMA_DECISION)
- Source lines: `yoma-087a-l01`
- Affected fields (11): `<daf>.summary`, `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`, `display.title`, `display.whats`, `finalRuling`, `learning.learnerQuestion`, `requiresUnderstanding`, `topicTags`, `visualizableElements[].name`
- First pass: Source is Rava's self-admonition before sitting in judgement ('of his own will he goes to die'). display frames it as a halakhic distinction between willing and forced death. argumentFlow correct ('Rava's words before judging').
- Second pass (AGREE): Independently recovered: the single line is Rava's self-admonition before judging - 'of his own will he goes to die' - about the peril of judicial honour, not a halakhic willing/forced death distinction.
- Registered owners: display-only-edit, gemara-learning, learning-copy-edit, structural-repair (allowStructure), summary-edit
- Unowned paths: `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`
- Prerequisite contract decisions: `finalRuling-semantics`, `requiresUnderstanding-semantics`
- Atomic task decision required: yes - Affected paths span several registered owners AND include paths with no registered owner.

### yoma-087a-s02 (87a) - WRONG_TOPIC

- Overall: **SUBSTANTIVE_REPAIR_NEEDED** (semantic SUBSTANTIVE_REPAIR_NEEDED / mechanical MINOR_EDIT_NEEDED)
- Source lines: `yoma-087a-l08`, `yoma-087a-l12`, `yoma-087a-l17`, `yoma-087a-l21`, `yoma-087a-l26`
- Affected fields (11): `<daf>.summary`, `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`, `display.title`, `display.whats`, `finalRuling`, `learning.learnerQuestion`, `requiresUnderstanding`, `topicTags`, `visualizableElements[].name`
- First pass: Source expounds 'It is not good to respect the person of the wicked' and the merit/liability the righteous and wicked bring on others. display describes YK not atoning without appeasing the wronged party - the subject of 087a-s05. argumentFlow correct.
- Second pass (AGREE): Independently recovered: the lines expound 'It is not good to respect the person of the wicked' and the merit or liability the righteous and wicked accrue for others. Appeasing a wronged person is 087a-s05's subject.
- Registered owners: display-only-edit, gemara-learning, learning-copy-edit, structural-repair (allowStructure), summary-edit
- Unowned paths: `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`
- Prerequisite contract decisions: `finalRuling-semantics`, `requiresUnderstanding-semantics`
- Atomic task decision required: yes - Affected paths span several registered owners AND include paths with no registered owner.

### yoma-087b-s01 (87b) - WRONG_SPEAKER

- Overall: **SUBSTANTIVE_REPAIR_NEEDED** (semantic SUBSTANTIVE_REPAIR_NEEDED / mechanical MINOR_EDIT_NEEDED)
- Source lines: `yoma-087b-l01`, `yoma-087b-l06`, `yoma-087b-l10`
- Affected fields (11): `<daf>.summary`, `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`, `display.title`, `display.whats`, `finalRuling`, `learning.learnerQuestion`, `requiresUnderstanding`, `topicTags`, `visualizableElements[].name`
- First pass: The slighted party in the source is RABBI CHANINA (Rav restarted the portion when Rabbi Chiyya entered; Rabbi Chanina saw the dream and withheld forgiveness). display casts the story as Rav appeasing R. Chiyya and R. Chiyya refusing. argumentFlow names Rabbi Chanina correctly.
- Second pass (AGREE): Independently recovered: Rav restarted the portion when Rabbi Chiyya entered, which slighted RABBI CHANINA; Rabbi Chanina saw the dream and withheld forgiveness so Rav would leave to teach. Rabbi Chiyya is not the party refusing appeasement.
- Registered owners: display-only-edit, gemara-learning, learning-copy-edit, structural-repair (allowStructure), summary-edit
- Unowned paths: `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`
- Prerequisite contract decisions: `finalRuling-semantics`, `requiresUnderstanding-semantics`
- Atomic task decision required: yes - Affected paths span several registered owners AND include paths with no registered owner.

### yoma-087b-s03 (87b) - WRONG_TOPIC, INVENTED_CLAIM

- Overall: **SUBSTANTIVE_REPAIR_NEEDED** (semantic SUBSTANTIVE_REPAIR_NEEDED / mechanical MINOR_EDIT_NEEDED)
- Source lines: `yoma-087b-l41`, `yoma-087b-l45`, `yoma-087b-l49`, `yoma-087b-l51`, `yoma-087b-l52`, `yoma-087b-l53`, `yoma-087b-l54`
- Affected fields (11): `<daf>.summary`, `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`, `display.title`, `display.whats`, `finalRuling`, `learning.learnerQuestion`, `requiresUnderstanding`, `topicTags`, `visualizableElements[].name`
- First pass: Source is the NE'ILA sugya (priestly blessing three/four times a year, whether ne'ila is a full Amida, Ulla bar Rav before Rava, ne'ila exempting ma'ariv). display describes 'Closing of Tractate Yoma: Hadran formula; Tu BeAv' - neither the Hadran nor Tu BeAv appears in these lines. argumentFlow correct.
- Second pass (AGREE): Independently recovered: the lines are the ne'ila sugya - the priestly blessing's frequency, whether ne'ila is a full Amida or a confession, Ulla bar Rav leading before Rava, and ne'ila exempting ma'ariv. Neither the Hadran formula nor Tu BeAv occurs.
- Registered owners: display-only-edit, gemara-learning, learning-copy-edit, structural-repair (allowStructure), summary-edit
- Unowned paths: `concepts.halachic[]`, `concepts.narrative[]`, `concepts.theological[]`
- Prerequisite contract decisions: `finalRuling-semantics`, `requiresUnderstanding-semantics`
- Atomic task decision required: yes - Affected paths span several registered owners AND include paths with no registered owner.

## Minor semantic edits

- **yoma-077b-s01** (77b) - WRONG_TOPIC, TRUNCATED; overall **MINOR_EDIT_NEEDED**. whats/hint claim the verse yields the fast obligation; the source (Laban, 'if you afflict my daughters', Rav Pappa/Shechem) concerns conjugal deprivation. learning.coreMove states this correctly, so only display is wrong.
- **yoma-077b-s03** (77b) - WRONG_TOPIC; overall **STRUCTURAL_OR_SCHEMA_DECISION**. Sugya is about crossing water to greet a father/teacher and Rava/Rav Yosef permitting crossings; display reduces it to 'greeting and visiting', omitting the water-crossing halakha that is the actual subject.
- **yoma-078a-s02** (78a) - WRONG_TOPIC; overall **MINOR_EDIT_NEEDED**. Source is shoes/sandals while crossing water and the Rafram/Ravina exchange; display frames it purely as whether crossing constitutes prohibited bathing.
- **yoma-084b-s03** (84b) - WRONG_SOURCE_REF; overall **MINOR_EDIT_NEEDED**. Source is a baraita ('The Sages taught') about saving life on SHABBAT; display labels it a Tosefta about Yom Kippur.
- **yoma-086a-s02** (86a) - WRONG_TOPIC; overall **MINOR_EDIT_NEEDED**. Sugya's substance is Rabbi Matya ben Charash's question to Rabbi Elazar ben Azarya about the categories/paths of atonement; display reduces it to defining 'bearing God's name in vain'.
- **yoma-087a-s03** (87a) - WRONG_TOPIC; overall **MINOR_EDIT_NEEDED**. Source treats 'I will sin and repent' (doubled) and 'I will sin and YK will atone'; display generalises to the scope of YK's atonement power.
- **yoma-087a-s04** (87a) - WRONG_TOPIC; overall **STRUCTURAL_OR_SCHEMA_DECISION**. Display posits 'communal sins with a Godward dimension'; the source is the mishna's God/person division and Rav Yosef bar Chavu's rereading of the verse's second clause.
- **yoma-087b-s02** (87b) - WRONG_TOPIC, TRUNCATED; overall **MINOR_EDIT_NEEDED**. Source: the main mitzva of confession is on Yom Kippur EVE at nightfall, with the Sages adding an earlier confession before eating. display asserts vidui is 'primary at Minha, optional earlier'. hint carries a literal ellipsis and finalRuling is its 150-char copy.
- **yoma-088a-s01** (88a) - WRONG_TOPIC, TRUNCATED; overall **MINOR_EDIT_NEEDED**. Source combines havdala placement with the immersion rules for a ba'al keri and the Rabbi Yosei contradiction; display covers only havdala. hint ends in a literal ellipsis; finalRuling is its truncated copy.

## Malformed but semantically recoverable

- **53 records** carry `FR_TRUNCATED_PREFIX_OF_HINT`: `finalRuling` is `display.hint` hard-cut mid-sentence. Text is lost regardless of any contract decision, so these are at least `MINOR_EDIT_NEEDED` and can never be overall `VERIFIED`.
- **29 records** carry `FR_EXACT_COPY_OF_HINT`: `finalRuling` equals `display.hint` exactly. Whether that is a defect depends on the unresolved `finalRuling`-semantics contract, so these are `STRUCTURAL_OR_SCHEMA_DECISION`.
- **9 records** have a `display.hint` ending in a literal ellipsis.
- Where the underlying `display.hint` is itself semantically wrong (for example `yoma-082b-s01`, `yoma-087b-s02`, `yoma-088a-s01`), restoring the full hint text would propagate the error. **Automatic restoration by extending the hint is explicitly not recommended.**

## Task ownership

**Correction.** An earlier revision of this report asserted that finalRuling, requiresUnderstanding, topicTags, visualizableElements, difficulty and alternateAngles had no registered owner. That was wrong: it was derived from task-type descriptions and allowedFiles rather than from jsonScope. Read directly from scripts/worker_task_types.json, structural-repair holds mutable ownership of sugyot[*].finalRuling, sugyot[*].requiresUnderstanding[*], sugyot[*].topicTags[*], sugyot[*].visualizableElements[*], sugyot[*].difficulty and sugyot[*].conceptRefs[*] under allowStructure, and learning-copy-edit holds sugyot[*].alternateAngles under authorizeAlternateAngles. The only genuinely unowned paths in this audit are the object-form concepts members.

Ownership below is resolved directly from `jsonScope` in `scripts/worker_task_types.json` and is re-proved on every `--check` run.

### Registered task owners (records touched)

| Task type | Records |
|---|---|
| structural-repair | 82 |
| display-only-edit | 33 |
| gemara-learning | 33 |
| summary-edit | 33 |
| learning-copy-edit | 25 |

Counts are per record, not per path: a record is counted once for each task type owning at least one of its affected fields, so the column sums exceed the record total.

### Required authorizations

| Authorization | Records |
|---|---|
| allowStructure | 82 |

### Decision counts

- Records with prerequisite contract decisions: **82**
- Records with genuinely unowned paths: **33**
- Records requiring an atomic task decision: **33**
- Records whose affected-field list expanded in this pass: **82**

### Genuinely unowned paths

| Path | Records |
|---|---|
| `sugyot[*].concepts.halachic[*]` | 33 |
| `sugyot[*].concepts.narrative[*]` | 33 |
| `sugyot[*].concepts.theological[*]` | 33 |

These are the object-form `concepts` members. `glossary-edit` owns the list-form `sugyot[*].concepts[*].term/he/translit/def`, which does not cover the `{halachic, narrative, theological}` shape carried by 389 of the 492 Yoma sugyot. No other registry entry matches them.

**byRegisteredTaskOwner counts records, not paths: a record is counted once per task type that owns at least one of its affected fields, so the column sums exceed the record count. TASK_TYPE_DECISION_REQUIRED is now a derived marker set only where a record has genuinely unowned paths or cannot be repaired atomically under one task type. It is no longer set merely because a field needs a semantic contract decision, which is why the previous count of 82 is not reproduced.**

## False positives withdrawn

- **`yoma-083b-s02`** - the prior pass called this 'topic drift'. Withdrawn on a fresh re-read: the declared line range genuinely spans both the ben Teima / first tanna dispute on tevel versus teruma severity *and* the bulmos remedies. Semantic disposition **VERIFIED**; this is the one record where the second pass disagreed with the first.
- **`display.whats` lacking terminal punctuation (172 values)** - phrase-style summaries, not truncation.
- **`NAME_NOT_IN_SOURCE` outside the cohort (17 sugyot)** - dominated by legitimate cross-daf back-references (for example `yoma-005a-s01` citing Reish Lakish's challenge from 3b) and names sitting just outside a sugya's declared line range.

## Controls and results

- **73b-76b (22 sugyot, the immediately preceding generation):** 0 semantic defects, 0 signature occurrences.
- **12 sugyot from perakim 1-6**, selected independently of any defect signal: 0 semantic defects. Two of them (`yoma-023a-s01`, `yoma-061a-s01`) carry a 149/150-character `finalRuling` by coincidence of length only, without the hint-copy signature.
- Deterministic corroboration: within the cohort `argumentFlow` matches its own source **5.1x** better than `display` does (Jaccard 0.293 vs 0.057); in every control band the two are comparable (about 1.2x).
- **No control exposed the defect family, so the cohort was not expanded.**

## Scope conclusion

No evidence was found that this specific pre-squash generation-signature defect family extends outside 77a-88a. The controls do not establish complete semantic cleanliness for the remainder of Yoma; they were sized to test one defect family, not to audit the corpus.

## Contract decisions (must precede repair)

1. `finalRuling` semantics for this cohort: independent halakhic statement (the pre-77a convention) versus summary copy. The 29 exact-copy records cannot be dispositioned without this.
2. Whether cohort `display.hint` should remain a descriptive paragraph or revert to the pre-77a question form.
3. Ownership of `concepts`, `topicTags`, `visualizableElements`, `finalRuling` and `requiresUnderstanding` in the task-type registry.
4. Whether `argumentFlow`, `misconceptions` and `quizSeeds` may be used as the repair source for the contaminated fields, given they are authored evidence rather than ground truth.

## Unresolved

- The 82 signature-bearing sugyot need a per-sugya decision on whether the underlying `hint` is sound before any `finalRuling` restoration.
- Second-pass independence: all second passes were fresh re-reads performed in the same model context as the first pass, not by a separately instantiated reviewer. A separate Opus context is preferable and is recorded here as a known weakness of this audit.
- Whether the parent `daf.summary` for affected daf should be repaired per-sugya or rewritten once per daf after all its sugyot are settled.

## Recommended repair sequencing

1. **Contract decisions above** - nothing else is safe first.
2. **`yoma-082b-s01`, `yoma-087b-s03`, `yoma-080a-s01`, `yoma-080b-s03`** - highest severity: fabricated framing, or a ruling that directly contradicts both the source and the sugya's own `argumentFlow` (olive-bulk stated as egg-bulk; an exemption stated as liability).
3. Remaining `SUBSTANTIVE_REPAIR_NEEDED` records in daf order, one PR per daf, repairing the full affected-field list rather than display alone.
4. `MINOR_EDIT_NEEDED` records.
5. Parent `daf.summary` rewrites, once every sugya on the daf is settled.
6. **Last:** the mechanical `finalRuling` truncation, once each underlying `hint` has been adjudicated. Repairing it earlier would destroy the strongest remaining locator for defective records.
