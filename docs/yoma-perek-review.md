# Yoma Perek-Level Contextual Review

Conducted after full schema backfill (492/492 sugyot, GitHub main at commit
5ce0a3d, VERSION 14.58). Analysis date: 2026-07-01.

Scope: sequence coherence across each perek, display titles, learner
questions, core tensions, core moves, takeaways, aha moments, and memory
anchors, read in context against neighboring sugyot. Does not cover Rashi
content (frozen; separate audit backlog in docs/rashi-audit-backlog.md).

Method: every sugya's title was read in daf order per perek to check the
narrative arc. A programmatic pass compared learnerQuestion, ahaMoment, and
memoryAnchor text across all 492 sugyot to surface exact duplicates and
non-canonical takeaway.type values. Flagged sugyot were then read in full
(display, learning, argumentFlow) against the underlying daftext where
needed to confirm or reject each finding before it was recorded here.

## Summary

- 492 sugyot across 8 peraqim reviewed.
- No duplicate display titles found.
- No missing required fields found.
- 57 sugyot carry non-canonical `takeaway.type` values (Perek 1-3, early
  backfill batches). The app does not render this field; deferred to a
  schema normalization pass.
- 1 low-risk, unambiguous wording fix applied (21b/yoma-021b-s03).
- 8 sugyot documented as requiring new authored content (crosswired or
  near-duplicate aha/memory anchor content). Not fixed; each needs
  judgment about what the correct content should say.
- 1 sugya documented as an internal contradiction that could not be
  resolved from the daftext alone (45a/yoma-045a-s02).
- One finding from an earlier, interrupted review pass was re-checked and
  found to be incorrect (66b/yoma-066b-s03 is not crosswired); it is
  removed from the issues list below.
- One finding from the earlier pass (57b/yoma-057b-s01, "three bowls") was
  re-checked and confirmed accurate as written; no fix applied.

---

## Perek 1: Shivat Yamim

Hebrew: שִׁבְעַת יָמִים | English: Shivat Yamim
Daf range: 2a-21b | Sugyot: 114

### Flow summary

Opens with the Mishnah's seven-day separation rule and its gezerah shavah
derivation (2a-4a). Pivots through inauguration requirements (4b-5b), the
Kohen Gadol's belt and separation reasons (6a), impurity debates (6b-8a),
the Parhedrin chamber and bakers' tithe obligations (8b-9a), the aggadic
block on the two Temple destructions (9a-9b), a mezuza digression (10a-12a),
the lottery race and its violent end, replacement-Kohen-Gadol rules
(12b-14a), the night vigil (14a-20a), and closes with the list of Temple
miracles and the dual-source altar-fire ruling (20b-21b).

The gezerah shavah chain (2a-4a) is scaffolded with genuine stakes at each
step: each verse considered and rejected narrows the derivation until only
Yom Kippur remains. The aggadic destruction block (9a-9b) gives each motif
(idolatry/immorality/bloodshed vs. sinat chinam, the length of exile, who
stood in the Jordan) its own sugya, which is appropriate given how much
independent content each carries.

### Issues found

**FIX APPLIED - 21b/yoma-021b-s03 (terminology error in ahaMoment):**
The ahaMoment used "the eternal flame (ner tamid)" where the sugya's own
topic, argument, and daftext are entirely about the altar fire (the two
wood arrangements and the dual heavenly/human fire requirement derived from
Vayikra 6:6, "eish tamid tukad al ha-mizbeach"). "Ner tamid" refers to the
menorah's continual lamp (Shemot 27:20), a different mitzvah on a different
vessel. Checked against modules/yoma/assets/daftexts/21b.txt: the daftext
discusses "אש של מערכה" (fire of the arrangement) and fire descending from
heaven vs. brought by a human; there is no mention of the menorah anywhere
in this sugya's line range. Fixed: replaced "the eternal flame (ner tamid)"
with "the eternal altar fire (eish tamid)" in the ahaMoment.

**REQUIRES NEW CONTENT - 9b/yoma-009b-s02 and 9b/yoma-009b-s03
(substantial content overlap):**
Both sugyot cover the same aggadic passage (sinat chinam equals the three
cardinal sins combined) with the same learnerQuestion core ("how can sinat
chinam be equal to all three cardinal sins combined"), the same coreTension,
coreMove, ahaMoment logic, and memoryAnchor structure, differing mainly in
wording rather than in angle. (An earlier review pass described the two
learnerQuestions as "word-for-word identical" - on re-checking, they are
not word-for-word identical, s03's is a shorter subset of s02's wording, but
the overlap across every other learning field is still substantial enough
that a learner gets the same conceptual moment twice with no progression.)
Titles differ ("First Temple: three cardinal sins..." vs. "Second Temple
destroyed...") but the learning scaffolding does not differentiate the two.
Status: one of the two sugyot needs a distinct ahaMoment and memoryAnchor
that adds a genuinely new angle. Requires judgment about which angle to
add; not applied.

**REQUIRES NEW CONTENT - 5a/yoma-005a-s02 (aha content mismatch):**
The learnerQuestion, coreTension, coreMove, and takeaway all correctly focus
on the sugya's actual open-ended stub: R. Yitzchak bar Bisna's derivation of
R. Yochanan's "kachah" principle only covers requirements written in the
inauguration passage itself, and the daf ends without resolving how
requirements written elsewhere are included. The ahaMoment, however,
pivots to the baraita's "michal mikol makom" combination rule (rivui/
meshicha), which is genuinely part of this sugya's own shortSummary content
(discussed earlier in the same sugya) but is not the specific unresolved-
question angle that the learnerQuestion/coreTension/coreMove/takeaway are
built around. This is a narrower problem than a straightforward crosswired
paste from another sugya: the ahaMoment content belongs to this sugya, just
not to the angle the rest of the learning fields commit to. Status: needs a
new ahaMoment addressing the open-question character of the kachah scope
limit. Requires judgment; not applied.

**SCHEMA TYPE - 49 sugyot (2a-20b, non-canonical takeaway.type):**
Listed in the schema normalization table at the end of this document. The
app does not render this field. Deferred.

### Observations

- Three transitional "bridge" sugyot in Perek 2 territory do not apply
  here; Perek 1 has no comparable bridge sugyot worth flagging.
- The Rome/Persia aggadic digression (10a) and the mezuza rules (10a-12a)
  are contextually detached from the surrounding Parhedrin-chamber material
  but are accurately labeled as such in their own titles and hints.

---

## Perek 2: Barishonah

Hebrew: בָּרִאשׁוֹנָה | English: Barishonah
Daf range: 22a-28a | Sugyot: 32

### Flow summary

Opens with the Saul/David digression triggered by the word "mispar," then
returns to the lottery tie-break procedure, the stabbing incident, and the
lottery mechanics in detail (23a-25b). Covers daily service preparations
(25b-27a), wood arrangement debates (27b-28a), and closes with the last
lottery/service details before Perek 3's dawn opens Yom Kippur. The arc
reads as coherent: the lottery as a system of order, contrasted with the
pre-lottery disorder (the race and the violence that ended it). The Saul/
David aggadah is spread across three sugyot (22a s01, 22b s03, 22b s04)
with genuinely distinct content in each (the mispar trigger, why "I have
sinned" saved David but not Saul, David's confession over Nov); the
stabbing narrative (22a s02) is well-scaffolded on its own.

### Issues found

**DEFERRED - 22a/yoma-022a-s01 (forward reference in ahaMoment):**
The ahaMoment references the stabbing incident (s02) before the learner has
reached it. Same daf, functions as narrative setup rather than a genuine
error. Low severity; no change made.

**SCHEMA TYPE - 2 sugyot (27b s02, 28a s01, `halachic_distinction`):**
Deferred to normalization pass.

### Observations

- 23b/yoma-023b-s01 (Jerusalem exempt from egla arufa) is a mild contextual
  detour inside the lottery chapter; its learnerQuestion grounds it in
  Jerusalem's unique status and the memoryAnchor is specific. Not flagged
  as an error.

---

## Perek 3: Amar Lahem HaMemoneh

Hebrew: אָמַר לָהֶם הַמְמוּנֶּה | English: Amar Lahem HaMemoneh
Daf range: 28b-39b | Sugyot: 62

### Flow summary

Traces the Kohen Gadol's morning preparations on Yom Kippur: dawn
confirmation (28b-29a), the tamid's timing rules (29a-29b), immersion
disputes and the five-immersions/ten-sanctifications count structure
(30a-32b), the full Yom Kippur service order (Abaye's sequence at 33a), the
day's confessions and the lot ceremony for the two goats (32b-37a), the
Temple architecture and craftsman aggada (Ben Katin's spigots, Nicanor's
doors, Beit Avtinas) at 37a-38b, and closes with the Shimon HaTzaddik
miracles and the omens that preceded the Temple's destruction (39a). This
is architecturally the strongest perek: nearly every early topic is a
readiness criterion leading toward the lot ceremony, and the closing
Shimon HaTzaddik material gives the whole perek a natural historical
bookend.

### Issues found

**SCHEMA TYPE - 6 sugyot (28b s02, 29a s02, 29b s01, 30a s01, 30a s02,
30b s01, `halachic_distinction`):**
Deferred to normalization pass.

### Observations

- The five-immersions/ten-sanctifications count (31a-32b) recurs later as
  its own topic in Perek 6 (60a) and again in Perek 7 (70b), each time in
  more or less detail. This is not a duplication defect: it reflects the
  Mishnah's own structure, where a later chapter restates part of the
  day's full sequence before elaborating its own portion. Noted here so
  the recurrence is not mistaken for redundant scaffolding.
- The chamtzan transition at 39b (technically the first sugya of Perek 4)
  is short but apt; its learnerQuestion asks what the term actually
  captures rather than just noting the change in era.

---

## Perek 4: Hotzi'u Lo

Hebrew: הוֹצִיאוּ לוֹ | English: Hotzi'u Lo
Daf range: 39b-47b | Sugyot: 41

### Flow summary

Covers the lot-drawing ceremony for the two goats (39b-42a): right-hand-lot
preference, designation formula, remediation when the lot falls wrong.
Pivots into the scapegoat's escort to the cliff (42b-43b), the incense
dispute between Pharisees and Sadducees (43b-44a), and the kometz procedure
(44a-47b): the coal pan specifications, incense measures, and timing. The
lot ceremony and kometz procedure are distinct topics, but both are
precision-dependent rituals where small deviations carry legal
consequences, which gives the perek a thematic throughline even though the
subject matter changes.

### Issues found

**AMBIGUOUS - DEFERRED - 45a/yoma-045a-s02 (internal contradiction, re-checked
2026-07-01, still unresolved from local corpus):**
The coreMove and takeaway state that the peras measure "remains constant"
or "stays constant" between ordinary-day and Yom Kippur incense. The
display.hint, ahaMoment, memoryAnchor, and finalRuling all say the Yom
Kippur quantity is different. The misconceptions.correction field sides
with "constant," matching coreMove/takeaway; argumentFlow states only the
ordinary-day peras and is silent on Yom Kippur. So within this sugya's own
fields the split is 3 (constant) vs. 4 (different), with argumentFlow
taking no side.

Re-checked against modules/yoma/assets/daftexts/45a.txt: this sugya's own
line range (Vilna line 7) is still a single truncated Mishnah citation,
"בכל יום מקריב פרס שחרית וכו'" ("every day he offers a peras in the
morning, etc."), with the actual "today" (Yom Kippur) comparison elided by
"etc." This file's rashiTranslations array uses an older per-Sefaria-segment
schema (empty he: fields, no source/confidence metadata) rather than this
project's standard per-Vilna-line schema; its entry for this exact segment
("On ordinary days, a peras (half-measure) of incense was offered in the
morning and evening") also only paraphrases the same truncated line and
adds nothing about Yom Kippur.

A corpus-wide search across all 173 Yoma learning JSON files for "melo
chofnav," "chofnav," and "peras" found zero hits outside this single sugya
- no other daf in this project's embedded corpus corroborates or refutes
either framing. The "additive structure" theory recorded in the previous
version of this note (daily peras continues unchanged, Yom Kippur
separately adds a melo chofnav handful per Vayikra 16:12) was drawn from
outside Judaic knowledge, not from any content present in this project's
local corpus, and should not be treated as a locally-sourced finding.
Resolving this requires consulting the fuller Mishnah/Gemara text (Yoma
44b-45a) or a secondary source beyond what this corpus currently embeds.
Flagged; not fixed. Do not rewrite either side without that broader
source review - a local-only fix here would risk asserting a specific
halachic conclusion (same vs. different vs. additive) that the embedded
corpus cannot itself verify.

### Observations

- The coal-pan specification cluster (44b s03 through s06) covers four
  distinct parameters (material, grade, capacity, weight) in separate
  sugyot with differentiated titles and learnerQuestions.

---

## Perek 5: Taraf BaKalpi

Hebrew: טָרַף בַּקַּלְפִּי | English: Taraf BaKalpi
Daf range: 47b-57b | Sugyot: 60

### Flow summary

Two phases: kometz boundary-case analysis continuing from Perek 4 (47b-49b),
then the blood service in the Holy of Holies and on the golden altar
(49b-57b). The blood-service sugyot develop a counting-toward-certainty
principle systematically across multiple sugyot (the "once up, seven down"
formula and its extensions), creating genuine intra-perek coherence. Five
consecutive unresolved (teiku) kometz dilemmas at 48a are technically
differentiated by distinct fact patterns but do produce a monotonous
stretch for a learner reading straight through.

### Issues found

**CONFIRMED ACCURATE - NO FIX NEEDED - 57b/yoma-057b-s01 (bowl confusion
memory anchor):**
An earlier review pass flagged the memoryAnchor's "Three bowls" phrasing as
possibly premature, since only two bowls (bull and goat blood) exist at
this point in the service and the mixed third bowl is not introduced until
58a in Perek 6. On re-checking this sugya's own argumentFlow, it explicitly
covers two scenarios in sequence: (1) the bull and goat bowls confused with
each other, and (2) "some blood from two bowls spills into an empty third
bowl" - the sugya itself introduces the third-bowl variant as part of its
own argument, before the "combined bowl" of the next perek. The
memoryAnchor's "Three bowls" phrasing is accurate for the variant case this
sugya actually discusses. No change made.

---

## Perek 6: Shnei Se'irei

Hebrew: שְׁנֵי שְׂעִירֵי | English: Shnei Se'irei
Daf range: 57b-68b | Sugyot: 59

### Flow summary

Opens with the outer blood service sequence and the scapegoat's third
confession (58a-58b), the Torah reading and eight blessings summarized as
part of the day's order (59a), the day's garment changes and immersions
(59a-60b), then traces the scapegoat ceremony through its dispatch to
Azazel (61a-67b), and ends with the burning requirements and the signal
chain confirming the goat reached the wilderness (68a-68b). The
replacement-goat cluster (62a-65b) is organized around a single governing
question (what happens when the pair is disrupted?) with clear logical
progression. The atonement-theology sugyot (61a-61b) sit well against the
surrounding procedural material.

### Issues found

**CORRECTION TO EARLIER REVIEW - 66b/yoma-066b-s03 is not crosswired:**
An earlier review pass claimed this sugya's ahaMoment and memoryAnchor
carried Urim VeTummim content that belonged to a different sugya. On
re-reading the sugya directly, this is incorrect: 66b/yoma-066b-s03's
title ("Five Afflictions: The Body Joins the Soul in Yom Kippur"), display,
learnerQuestion, coreTension, coreMove, ahaMoment, and memoryAnchor are all
consistently about the five Yom Kippur afflictions and contain no Urim
VeTummim material. A corpus-wide search for the specific phrases claimed
("Urim belongs to the king," "not a personal oracle") found them only in
73b/yoma-073b-s03 (see Perek 8 below), not here. This entry is removed
from the issues list; no fix needed at 66b.

### Observations

- 66b/yoma-066b-s02 (the meta-Talmudic passage on students' questions
  preserved as Torah) sits between the Azazel ceremony and the guide's
  return. This is where the Talmud places this discussion; the
  scaffolding is accurate to that placement. No error.

---

## Perek 7: Ba Lo Kohen Gadol

Hebrew: בָּא לוֹ כֹּהֵן גָּדוֹל | English: Ba Lo Kohen Gadol
Daf range: 68b-73b | Sugyot: 35

### Flow summary

After the atonement services, the Kohen Gadol performs the public closing
ceremonies: Torah reading (69a-70a), eight blessings and prostrations, the
five-immersions/ten-sanctifications architecture restated in more detail
(70b), vestment changes, and an aggadic passage on the three crowns and the
Shemaiah/Avtalyon-adjacent material (71b-72b), closing with the protocol
for consulting the Urim VeTummim (72b-73a). The Torah-reading cluster is
the perek's intellectual peak; the vestment section's aggadic material
provides a natural pause before the more technical Urim VeTummim protocol
that closes the perek.

### Issues found

**REQUIRES NEW CONTENT - 72b/yoma-072b-s03 (ahaMoment, memoryAnchor,
display all copied from 72b/yoma-072b-s02):**
72b/yoma-072b-s03's title ("The Gate Without a Courtyard: When Torah Stays
on the Outside"), learnerQuestion, coreTension, coreMove, and takeaway are
all correctly about external Torah learning without internalization - a
distinct topic from s02. However, this sugya's display.whats, display.hint,
ahaMoment, and memoryAnchor are all identical, word for word, to
72b/yoma-072b-s02's fields (the three-crowns sugya: "the crown of Torah is
the only one that has no dynasty," "zar vs. zeir"). Confirmed by direct
comparison of both sugyot's JSON. Status: needs a new display.whats,
display.hint, ahaMoment, and memoryAnchor for the gate-without-a-courtyard
concept. Requires judgment about what to write; not applied.

---

## Perek 8: Yom HaKippurim Oser

Hebrew: יוֹם הַכִּפּוּרִים אוֹסֵר | English: Yom HaKippurim Oser
Daf range: 73b-88a | Sugyot: 104

### Flow summary

Opens with the tail end of the Urim VeTummim discussion and the transition
into the new Mishnah on the five Yom Kippur prohibitions (73b), the chatzi
shiur dispute and the affliction-scope sugyot (74a-77b), the measures for
each prohibition (78a-81b), the pikuach nefesh escalation (82a-85a), and
closes with the atonement-mechanism theology and the tractate's Hadran
(85b-88a). At 104 sugyot this is the longest perek, but it reflects the
tractate's own structure: the Yom Kippur framework moving outward from the
Temple service to all of Israel. The pikuach nefesh escalation is
pedagogically well-built: cases increase in urgency and each introduces a
distinct new principle. The manna digression (74b-76a) is contextually
detached from the surrounding halachic material but is labeled accurately
as an aggadic digression in its own titles.

### Issues found

**REQUIRES NEW CONTENT - 73b/yoma-073b-s03 (ahaMoment and memoryAnchor
copied from the Urim VeTummim sugyot):**
This sugya's title ("The Five Afflictions of Yom Kippur..."), display.whats,
learnerQuestion, coreTension, coreMove, and takeaway are all correctly
about the five-fold derivation of afflictions from "ta'anu et
nafshoteichem." The ahaMoment ("The Urim VeTummim was not a personal
oracle - it was reserved for national decisions by the king") and
memoryAnchor ("The Urim belongs to the king, not the individual...") are
Urim VeTummim content belonging to 73b/yoma-073b-s02, immediately before
it in the same daf file. Confirmed by direct comparison. Status: needs a
new ahaMoment and memoryAnchor for the five-afflictions derivation.
Requires judgment about what to write; not applied.

**REQUIRES NEW CONTENT - 74a/yoma-074a-s02 and 74a/yoma-074a-s03 (identical
ahaMoment and memoryAnchor across two distinct sugyot):**
The two sugyot have distinct titles, learnerQuestions, coreTensions, and
coreMoves (s02 is the R. Yochanan/Reish Lakish biblical-vs-rabbinic chatzi
shiur dispute; s03 is specifically what the Mishnah's word "forbidden"
adds beyond the karet penalty). Their ahaMoment and memoryAnchor text is
word-for-word identical between the two. Confirmed by corpus-wide exact-
match search. Status: one of the two needs a distinct ahaMoment/
memoryAnchor matching its own angle. Requires judgment; not applied.

**REQUIRES NEW CONTENT - 74b/yoma-074b-s01 (ahaMoment and memoryAnchor
belong to 74b/yoma-074b-s02, not this sugya):**
74b/yoma-074b-s01's title, learnerQuestion, and coreTension are about
whether temperature exposure counts as a Yom Kippur affliction. Its
ahaMoment ("Yom Kippur affliction is about the act of eating itself...")
and memoryAnchor ("Climbing the severity ladder: karet, death, lav, no
prohibition...") are both about 74b/yoma-074b-s02's actual topic (the
severity ladder for eating violations), and are word-for-word identical to
s02's own ahaMoment and memoryAnchor. Confirmed by corpus-wide exact-match
search and direct comparison. Status: needs a new ahaMoment/memoryAnchor
about why temperature exposure does not count as active affliction.
Requires judgment; not applied.

**REQUIRES NEW CONTENT - 74b/yoma-074b-s04 (ahaMoment and memoryAnchor
belong to 74b/yoma-074b-s03, not this sugya):**
74b/yoma-074b-s04's title, learnerQuestion, and coreTension are about how
visual engagement with food connects to the danger of "setting eyes on
wine." Its ahaMoment ("The manna was food that came without natural hunger
satisfaction...") and memoryAnchor ("Blind people eat but can't be
satisfied...") are both s03's actual topic (the manna/blind-people
derivation about eyes and satiation) and are word-for-word identical to
s03's own fields. Confirmed by corpus-wide exact-match search and direct
comparison. Status: needs a new ahaMoment/memoryAnchor about the wine
danger. Requires judgment; not applied.

### Observations

- A broader heuristic scan (title/learnerQuestion keyword overlap against
  ahaMoment/memoryAnchor text) flagged 27 additional sugyot across the
  full corpus for manual review. All but the ones listed above were
  checked and found to be accurate paraphrases, not content mismatches
  (for example, 58b/yoma-058b-s02 and 84b/yoma-084b-s03 both use figurative
  language in their ahaMoment that does not share keywords with the title,
  but the content itself is correct for the sugya).

---

## Content fix applied in this review pass

| Sugya | Field | Problem | Fix applied |
|-------|-------|---------|-------------|
| 21b/yoma-021b-s03 | ahaMoment | "the eternal flame (ner tamid)" used for an altar-fire topic; ner tamid is the menorah lamp, a different mitzvah | "the eternal flame (ner tamid)" -> "the eternal altar fire (eish tamid)" |

---

## Content errors requiring human review (new content authoring needed)

| Sugya | Error | What is needed |
|-------|-------|----------------|
| 9b/yoma-009b-s02 and s03 | Substantial overlap in learnerQuestion, coreTension, coreMove, ahaMoment, memoryAnchor across two distinct sugyot | One sugya needs a distinct ahaMoment and memoryAnchor that adds a genuinely new angle |
| 5a/yoma-005a-s02 | ahaMoment discusses the combination rule (part of this sugya's own content) instead of the open-question angle the rest of the fields commit to | New ahaMoment addressing the open-question character of the kachah scope limit |
| 72b/yoma-072b-s03 | display.whats, display.hint, ahaMoment, and memoryAnchor are copied verbatim from 72b/yoma-072b-s02 (three crowns), not this sugya's gate-without-courtyard topic | New display.whats, display.hint, ahaMoment, and memoryAnchor |
| 73b/yoma-073b-s03 | ahaMoment and memoryAnchor are Urim VeTummim content copied from 73b/yoma-073b-s02, not this sugya's five-afflictions topic | New ahaMoment and memoryAnchor for the five-afflictions derivation |
| 74a/yoma-074a-s02 and s03 | ahaMoment and memoryAnchor are word-for-word identical across two sugyot with distinct topics | One sugya needs distinct ahaMoment/memoryAnchor |
| 74b/yoma-074b-s01 | ahaMoment and memoryAnchor are word-for-word identical to s02's (severity ladder), not this sugya's temperature-exposure topic | New ahaMoment/memoryAnchor about temperature exposure not counting as affliction |
| 74b/yoma-074b-s04 | ahaMoment and memoryAnchor are word-for-word identical to s03's (manna/blind people), not this sugya's wine-danger topic | New ahaMoment/memoryAnchor about the danger of setting eyes on wine |

## Content requiring source-text review before any fix (ambiguous)

| Sugya | Error | What is needed |
|-------|-------|----------------|
| 45a/yoma-045a-s02 | coreMove/takeaway/misconceptions.correction say the peras measure is constant between ordinary days and Yom Kippur; display.hint/ahaMoment/memoryAnchor/finalRuling say it is different. argumentFlow states only the ordinary-day peras and is silent on Yom Kippur. Re-checked 2026-07-01: the sugya's own truncated daftext line still does not resolve which framing it intends, and a corpus-wide search found zero corroborating mentions of "peras," "chofnav," or "melo chofnav" outside this one sugya. Any additive-structure resolution (peras continues, plus a separately added handful) would rely on outside Judaic knowledge, not on content present in this corpus. | Human review against the fuller Mishnah/Gemara text of Yoma 44b-45a, or a secondary source, before deciding how to rewrite either side |

---

## Schema normalization: non-canonical takeaway.type values

57 sugyot (Perek 1-3, early backfill batches) carry non-canonical
`takeaway.type` values. The app does not render this field. Canonical
mapping:

| Non-canonical value          | Canonical replacement    |
|------------------------------|--------------------------|
| halakhic                     | legal_principle          |
| halachic_distinction         | legal_principle          |
| practical_application        | legal_principle          |
| practical                    | legal_principle          |
| behavioral_norm              | legal_principle          |
| legal_mechanism              | legal_principle          |
| legal_structure               | legal_principle          |
| legal_reasoning               | logical_principle        |
| historical-halakhic          | legal_principle          |
| aggadic                      | conceptual               |
| conceptual_distinction       | conceptual               |
| spiritual_principle          | conceptual               |
| theological                  | conceptual               |
| methodological               | logical_principle        |
| analytical                   | logical_principle        |
| dialectical                  | logical_principle        |
| hermeneutical                | derivation_principle     |
| hermeneutical_principle      | derivation_principle     |
| textual_principle            | derivation_principle     |
| legal_derivation              | derivation_principle     |
| reasoning_method              | derivation_principle     |

Fix status: deferred. Requires edits across 57 learning JSON files.
Commit separately from this review pass.
