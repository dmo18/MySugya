# Rashi audit backlog

Read-only tracking note for suspected Rashi helper-translation misalignments
found incidentally while doing other work. This is not a Rashi validation
report; `validate:rashi:yoma` already checks structural alignment (he order/
count, en+enSource presence, no leak into Gemara). This note is for
translation-quality or content-alignment concerns that the structural
validator cannot catch.

Do not act on entries here without an explicit Rashi pass. Do not edit
`modules/yoma/` Rashi content based on this note alone.

## Scope note

When a dedicated Rashi helper audit pass is eventually run, it must check
both alignment (he order/count vs. Vilna, en+enSource presence, no leak
into Gemara - already covered by `validate:rashi:yoma`) and nekudot/
vowelization correctness in the `he:` fields, which the structural
validator does not check.

## Status

As of VERSION 15.16: schema backfill is complete, the perek-level semantic
review is complete, crosswired and duplicated scaffold fixes are
complete, `takeaway.type` normalization is complete, the 45a
source-review issue is resolved, and the 5a/yoma-005a-s02 follow-up is
resolved (see `docs/yoma-completion-report.md` for the full
phase-by-phase record). `validate:rashi:yoma` has passed throughout every
one of those passes, confirming structural integrity was never disturbed.

No non-Rashi Gemara-learning follow-ups remain documented as open.

A bounded two-entry Rashi helper audit pilot was run at VERSION 14.67
(see the Pilot findings table below). Both entries were fixed. A bounded
Batch 1 audit (10 more entries, all in 10b) was run at VERSION 14.68
(see Batch 1 findings below). That batch also surfaced two major
systemic findings, documented further down. A bounded Batch 2 audit (6
entries: 4 in 10a, 2 in 11a, the exact lines Batch 1 had already
Hebrew-checked) was run at VERSION 14.69, fixing all 6 documented
examples from the descriptive-style systemic finding (see Batch 2
findings below). A bounded Batch 3 audit (10b vilnaLine 12-20, the
documented remaining entries in that range) was run at VERSION 14.70
(see Batch 3 findings below), resolving 10b through vilnaLine 20;
vilnaLine 21 remained open pending a follow-up. A self-managed sequenced
pass at VERSION 14.71 ran three bounded subtasks (see Batch 4 findings
below): Subtask A closed out 10b entirely (vilnaLine 11 placement,
vilnaLine 21 content); Subtask B fixed 6 entries in 10a and 6 in 11a;
Subtask C fixed 12 more entries in 11a, resolving 11a through vilnaLine
26. Batch 5 (VERSION 14.72, see Batch 5 findings below) closed out 11a
entirely: the remaining 24 entries (vilnaLine 1, 3-8, 27-43) were fixed,
including a correction of one Batch 2 placement (vilnaLine 4). Batch 6
(VERSION 14.73, see Batch 6 findings below) closed out 10a entirely: the
remaining 25 entries (vilnaLine 1, 9-21, 25-35) were fixed. The
early-daf hotspot first identified in Batch 1 (10a, 10b, 11a) is now
fully resolved: 99 entries audited and corrected across those three daf.
Batch 7 (VERSION 14.74, see Batch 7 findings below) moved to the next
daf in the sugya, 11b, fixing vilnaLine 1-25 of its 39 descriptive-style
entries. Batch 8 (VERSION 14.75, see Batch 8 findings below) closed out
11b entirely, fixing the remaining 14 entries (vilnaLine 26-39) and
uncovering that the prior English had fabricated an entire synagogue/
tzaraat discussion that turned out to be real content misattributed by
one daf (the actual Rashi text is on 12a). The mezuza sugya spanning
10a-11b (99 + 39 = 138 entries) is now fully resolved. Batch 9 (VERSION
14.76, see Batch 9 findings below) moved to 12a and fixed vilnaLine 1-16,
the self-contained conclusion of the mezuza/tzaraat sugya continuing
from 11b's truncated final word. Batch 10 (VERSION 14.77, see Batch 10
findings below) fixed 12a vilnaLine 17-36, the remainder of Gemara
sugya s01 (tribal-boundary geography, the tannaitic dispute over
whether Jerusalem was divided, and the tzaraat/family-ownership
sequence). Batch 11 (VERSION 14.78, see Batch 11 findings below)
closed out 12a entirely, fixing the remaining 30 entries (vilnaLine
37-66, the Kohen Gadol investiture dispute proper - the mishna's two
disqualification scenarios, Rav Adda's belt proposal, Abaye's eight
garments and tzinnora counter-proposal, and the cross-daf continuation
into 12b). 12a (66 entries) is now fully resolved, bringing the
descriptive-style hotspot total to 10a-12a (99 + 39 + 66 = 204
entries). The 12b index-misalignment finding documented after Batch
11 was resolved in a dedicated remap (VERSION 14.79, see the "12b
remap" section below): all 62 entries were rebuilt from a full
raw-line reconstruction, closing 12b entirely. A self-correction at
VERSION 14.80 (see "Self-correction" under the 12b remap section)
relinked 12b vilnaLine 57-62 from an incorrect `l35` anchor to the
correct `l42` anchor after cross-referencing 13a's Gemara text
surfaced the error; 13a itself was found to have the same index-
misalignment pattern as 12b. A dedicated 13a chunk at VERSION 14.81
(see the "13a" section below) read the daf's actual Gemara-line
sequence first and fixed vilnaLine 1-17 (the halacha ruling's
cross-daf tail, the backup-wife discussion's close, and the first two
conditional-divorce formulas); vilnaLine 18-29 were initially left
unchanged after the raw-line walk hit genuine ambiguity between
competing later Gemara lines. A follow-up dedicated pass at VERSION
14.82 (see "13a vilnaLine 18-29 resolved" below) resolved that
ambiguity by cross-referencing the local English translation stored
alongside each Gemara line, fixing the remaining 12 entries and
closing 13a entirely (29/29 resolved). A dedicated 13b pass at
VERSION 14.83 (see "13b resolved" below) verified the 13a/13b
boundary (no regression), then fixed all 28 of 13b's entries by
reading the daf's sugya scaffolding first, closing 13b entirely. A
first sub-chunk of 14a at VERSION 14.84 (see "14a, vilnaLine 1-29"
below) verified the 13b/14a boundary (no regression), then fixed
14a's vilnaLine 1-29 (14a has 58 entries, above the single-chunk
threshold, so it is split in two). A second sub-chunk at VERSION
14.85 (see "14a, vilnaLine 30-58" below) fixed the remaining 29
entries, closing 14a entirely (58/58 resolved). A first sub-chunk of
14b at VERSION 14.86 (see "14b, vilnaLine 1-30" below) verified the
14a/14b boundary (no regression), then fixed 14b's vilnaLine 1-30
(14b has 59 entries, above the single-chunk threshold, so it is split
in two); vilnaLine 31-59 remained for a follow-up chunk. A second
sub-chunk at VERSION 14.87 (see "14b, vilnaLine 31-58" below) fixed
the remaining mapped entries, vilnaLine 31-58, leaving only vilnaLine
59 deferred pending the 14b/15a boundary check (58/59 resolved). A
first sub-chunk of 15a at VERSION 14.88 (see "15a, vilnaLine 1-33"
below) confirmed that boundary (15a's raw text opens "מערב עד בקר",
completing 14b's truncated "מערב"), resolved the deferred 14b
vilnaLine 59 (closing 14b entirely, 59/59), and fixed 15a's
vilnaLine 1-33 (15a has 66 entries, above the single-chunk
threshold, so it is split in two). A second sub-chunk at VERSION
14.89 (see "15a, vilnaLine 34-66" below) fixed the remaining 33
entries, closing 15a entirely (66/66 resolved). A first sub-chunk of
15b at VERSION 14.90 (see "15b, vilnaLine 1-33" below) verified the
15a/15b boundary (15b's raw text opens "אגופיה דמזבח", restating
15a's truncated final word) and fixed 15b's vilnaLine 1-33 (15b has
66 entries, split in two). A second sub-chunk at VERSION 14.91 (see
"15b, vilnaLine 34-66" below) fixed the remaining 33 entries,
closing 15b entirely (66/66 resolved), including the 16 entries that
previously had empty linkedGemaraLineIds and placeholder text. A
first sub-chunk of 16a at VERSION 14.92 (see "16a, vilnaLine 1-31"
below) verified the 15b/16a boundary (16a's raw text opens "ששיקצום
מלכי עובדי כוכבים", restating 15b's truncated final word) and fixed
16a's vilnaLine 1-31 (16a has 61 entries, split in two). A second
sub-chunk at VERSION 14.93 (see "16a, vilnaLine 32-61" below) fixed
the remaining 30 entries, closing 16a entirely (61/61 resolved),
including 20 entries that previously had empty linkedGemaraLineIds
and stub text. A first sub-chunk of 16b at VERSION 14.94 (see "16b,
vilnaLine 1-31" below) verified the 16a/16b boundary (16b's raw text
opens "עשר אמות כנגד פתחו של היכל", restating 16a's truncated final
word) and fixed 16b's vilnaLine 1-31 (16b has 62 entries, split in
two). A second sub-chunk at VERSION 14.95 (see "16b, vilnaLine
32-62" below) fixed the remaining 31 entries, closing 16b entirely
(62/62 resolved), including 37 entries that previously had empty
linkedGemaraLineIds. A first sub-chunk of 17a at VERSION 14.96 (see
"17a, vilnaLine 1-23" below) verified the 16b/17a boundary (17a's
raw text opens "אלא לאו שמע מינה ראב"י היא", restating 16b's
truncated final word) and fixed 17a's vilnaLine 1-23 (17a has 45
entries, split in two). A second sub-chunk at VERSION 14.97 (see
"17a, vilnaLine 24-45" below) fixed the remaining 22 entries,
closing 17a entirely (45/45 resolved), including 25 entries that
previously had empty linkedGemaraLineIds. A full-daf chunk for 17b
at VERSION 14.98 (see "17b" below) verified the 17a/17b boundary
(17b's raw text opens "אי אמרת בשלמא", restating 17a's truncated
final word) and fixed all 33 of 17b's entries in one pass (17b is
under the 40-entry split threshold), closing 17b entirely. A first
sub-chunk of 18a at VERSION 14.99 (see "18a, vilnaLine 1-29" below)
verified the 17b/18a boundary (18a's raw text opens "ומאי ארבע או
חמש", restating 17b's truncated final word) and fixed 18a's
vilnaLine 1-29 (18a has 58 entries, split in two). A second
sub-chunk at VERSION 15.00 (see "18a, vilnaLine 30-58" below) fixed
the remaining 29 entries, closing 18a entirely (58/58 resolved),
including 30 entries across both halves that previously had empty
linkedGemaraLineIds. A full-daf chunk for 18b at VERSION 15.01 (see
"18b" below) verified the 18a/18b boundary (18b's raw text opens
"השחלין. קרש"ין", restating 18a's truncated final word) and fixed
all 34 of 18b's entries in one pass, closing 18b entirely. A first
sub-chunk of 19a at VERSION 15.02 (see "19a, vilnaLine 1-29" below)
verified the 18b/19a boundary (19a's raw text opens "גמ' תנא ללמדו
חפינה", restating 18b's trailing Gemara-section header) and fixed
19a's vilnaLine 1-29 (19a has 58 entries, split in two). A second
sub-chunk at VERSION 15.03 (see "19a, vilnaLine 30-58" below) fixed
the remaining 29 entries, closing 19a entirely (58/58 resolved),
including 11 entries that previously had empty linkedGemaraLineIds.
A first sub-chunk of 19b at VERSION 15.04 (see "19b, vilnaLine 1-34"
below) verified the 19a/19b boundary (19b's raw text opens "הכי
קאמרי ליה", restating 19a's truncated final word) and fixed 19b's
vilnaLine 1-34 (19b has 68 entries, split in two). A second
sub-chunk at VERSION 15.05 (see "19b, vilnaLine 35-68" below) fixed
the remaining 34 entries, closing 19b entirely (68/68 resolved),
including 28 entries that previously had empty linkedGemaraLineIds.
The 12b-19b index-misalignment hotspot is now fully resolved end to
end. A first sub-chunk of 20a at VERSION 15.06 (see "20a, vilnaLine
1-20" below) verified the 19b/20a boundary (20a's raw text opens
"לפתח חטאת רובץ", restating 19b's truncated final word) and fixed
20a's vilnaLine 1-20 (20a has 41 entries, one over the 40-entry
split threshold, so it is split in two). A second sub-chunk at
VERSION 15.07 (see "20a, vilnaLine 21-41" below) fixed the
remaining 21 entries, closing 20a entirely (41/41 resolved). A first
sub-chunk of 20b at VERSION 15.08 (see "20b, vilnaLine 1-31" below)
verified the 20a/20b boundary (20b's raw text opens "ואי דאורייתא
הוא היכי מקדמינן", restating 20a's truncated final word) and fixed
20b's vilnaLine 1-31 (20b has 62 entries, split in two). A second
sub-chunk at VERSION 15.09 (see "20b, vilnaLine 32-62" below) fixed
30 of the remaining 31 entries, deferring vilnaLine 62 pending a
policy decision on cross-daf boundary anchoring. A dedicated policy
pass at VERSION 15.10 (see "Cross-daf Rashi boundary link policy"
below) reviewed the corpus precedent, reversed the vilnaLine 62
deferral, and linked it per the established convention, closing 20b
entirely (62/62 resolved). At VERSION 15.11 (see "21a, full daf"
below) a fast alignment run verified the 20b/21a boundary read-only
(21a's raw Rashi opens "וי\"א אף רידייא", the full DH continuing
20b's truncated final word, exactly as the boundary policy pass
concluded) and fixed all 62 of 21a's entries in two sub-chunks,
replacing generic descriptive-style placeholder text with real
translations and correcting every linkedGemaraLineIds value, closing
21a entirely (62/62 resolved). At VERSION 15.12 (see "21b, full daf"
below) the run continued to 21b, verifying the 21a/21b boundary
read-only (both the truncated Rashi word and the truncated Gemara
word complete cleanly on 21b's opening) and fixing all 46 of 21b's
entries in two sub-chunks, closing 21b and Perek 1 of Yoma entirely
(46/46 resolved), including a self-caught correction of an initial
mismapping (vilnaLine 40-41 moved from `l37` to `l40` after a direct
text check). At VERSION 15.13 (see "22a, full daf" below) the run
continued into Perek 2, confirming 22a opens with a clean perek
boundary (Mishna's full opening phrase, not a truncated
continuation) and fixing all 65 of 22a's entries in two sub-chunks
(65/65 resolved), including replacing one stub run's "Saul counted
Israel" tangent that turned out to be real content misattributed one
daf early (it belongs on 22b, not 22a), the same one-daf-off pattern
already documented for 11b/12a. At VERSION 15.14 (see "22b, full
daf" below) the run closed the Saul/David digression, confirming the
22a/22b boundary is clean and fixing all 35 of 22b's real entries in
a single chunk (35/35 resolved), after discovering and correcting a
structural anomaly - the prior enrichment JSON carried 14 orphaned
entries beyond talmud.dev's real 35-line Rashi array for this daf,
which build_learning_data.py silently never renders; those were
removed rather than translated. At VERSION 15.15 (see "23a, full
daf" below) the run continued to the Torah-scholar-and-snake sugya,
confirming the 22b/23a boundary is clean, confirming the entry-count
check introduced after 22b's surprise still passes here, and fixing
all 45 of 23a's entries in two sub-chunks (45/45 resolved). At
VERSION 15.16 (see "23b, full daf" below) the run closed the
garment-changing baraita, confirming the 23a/23b boundary is clean
and fixing all 65 of 23b's entries in two sub-chunks (65/65
resolved), including anchoring one unusually long, uninterrupted
22-line Rashi passage by matching its own wording to the real
captured lines it echoes rather than forcing artificial breaks. No
regression was found on 12b, 13a, 13b, or 14a in any of these passes. The descriptive-style systemic finding is still open beyond the lines fixed
so far - the scope estimate below lists the other daf using the
descriptive "Rashi:" style, none of which have been verified yet - plus
the 77a-88a
placeholder text. All need a dedicated pass of their own. This is still
small, explicitly scoped work, not the dedicated Rashi content-quality
audit described in the Scope note above. Rashi content-quality auditing
of the remaining corpus and the nekudot/vowelization audit have not
started.

## Pilot findings (VERSION 14.67)

| daf | Rashi vilnaLine | visible Rashi text (excerpt) | prior helper text | issue | classification | resolution |
|---|---|---|---|---|---|---|
| 5b | 1 | "מילתא דכתיבא בהאי ענינא. בפרשת צוואה דמלואים שנאמר בואתה תצוה" | "...which states 've-atah tetzaveh' (Exodus 28)." | Rashi names the phrase 've-atah tetzaveh' as the opening of the Tetzaveh parasha, not a verse located in Exodus 28. The literal verse 've-atah tetzaveh...' is Exodus 27:20 (confirmed via Sefaria API, Exodus 27:20 Hebrew text: "וְאַתָּ֞ה תְּצַוֶּ֣ה..."). | misaligned (citation) | Fixed: reworded to "within the parasha that opens 've-atah tetzaveh' (Exodus 27:20)", clarifying it names the parasha rather than pinpointing the inauguration verse itself. |
| 10b | 1 | "אלא אמר אביי. בשבעת ימים של פרישה לא פליג ר' יהודה דודאי מיחייב דומיא דסוכה" | "Rashi: introduces the apparent contradiction between R. Yehuda's sukka ruling and his Parhedrin ruling." | The prior helper described this comment as introducing a contradiction between two rulings. The actual Rashi comment does the opposite: it identifies "the seven" as the High Priest's seven days of separation and states plainly that Rabbi Yehuda does not disagree there, comparing it to the (undisputed) sukka obligation. The contradiction between the sukka and Parhedrin rulings is developed later in the sugya, not by this comment. | misaligned (mischaracterized the Gemara's move) | Fixed: reworded to describe what Rashi actually identifies and states, without the "introduces the contradiction" framing. |

Secondary observation (not acted on, out of pilot scope): 10b rashiTranslations
entry 1's `linkedGemaraLineIds` points to `yoma-010b-l01` ("דילמא אתי
לאפרושי..."), but the Rashi text's own dibbur hamatchil ("אלא אמר אביי")
quotes the opening of Gemara line `yoma-010b-l02` instead. `linkedGemaraLineIds`
is inert metadata (not read by `validate:rashi:yoma` or by `app.jsx`), so this
does not affect any validation gate or rendered behavior, and correcting the
English helper text did not require touching it. Flagging here for a future
dedicated pass to decide whether `linkedGemaraLineIds` should be corrected
corpus-wide.

Rashi is the next planned area of work but the full-corpus pass has not
started. This backlog remains the place to log findings from incidental
review; see `docs/tractate-build-process.md` Section 9 for how to prepare
for the dedicated pass.

## Batch 1 findings (VERSION 14.68)

All 10 entries below are in 10b, reconstructed by joining the raw
talmud.dev Rashi print-lines into their real dibbur-hamatchil-delimited
comments and comparing against the linked Gemara text in
`learning_data.js`. vilnaLine 1 was already fixed in the pilot. This
batch completes the second real comment (the Rabbis' rationale for the
Parhedrin chamber's year-round mezuza) and opens the third (Rava's sukka
challenge). All fixed via English-only rewrites; no Rashi Hebrew touched.

| daf | vilnaLine | issue | resolution |
|---|---|---|---|
| 10b | 2 | Prior text ("explains R. Yehuda's sukka requirement for a permanent-style structure") describes a topic from much later in the daf (dirat keva, vl16-20 range). Actual Hebrew here is "perisha lo palig R. Yehuda vadai" - the tail of comment 1, already covered by vilnaLine 1's fixed text. | Fixed: reworded to describe the specific word being glossed here (vadai, "certainly," not a reluctant concession). |
| 10b | 3 | Prior text ("clarifies the distinction between the two types of residence") does not match either half of the actual text: the end of comment 1 and the opening words of comment 2. | Fixed: reworded to describe the comment boundary accurately. |
| 10b | 4 | Prior text ("defines 'dirat keva'") is the wrong topic; actual Hebrew here is the Rabbis' decree rationale. | Fixed: reworded to the Rabbis' actual position. |
| 10b | 5 | Prior text ("on 'dirat anusim'") is the wrong topic; actual Hebrew continues the decree rationale. | Fixed: reworded to match. |
| 10b | 6 | Prior text ("applies the coerced-residence principle") is the wrong topic. | Fixed: reworded to Rabbi Yehuda's rejection of the decree and the start of Rashi's alternate explanation. |
| 10b | 7 | Prior text ("rabbinic decree is separate from Torah-level obligation") does not match; actual Hebrew explains why the mezuza stayed up year-round. | Fixed: reworded to match. |
| 10b | 8 | Prior text ("revisits the imprisonment concern") is out of order; actual Hebrew here precedes the imprisonment concern, not revisits it. | Fixed: reworded to match (continuation of the "recognized as a residence" point). |
| 10b | 9 | Prior text ("connects R. Yehuda's positions into a coherent framework") is the wrong topic. | Fixed: reworded to the actual imprisonment concern being introduced. |
| 10b | 10 | Prior text ("summarizes the resolution") is the wrong topic; actual Hebrew is the literal continuation of the imprisonment-concern sentence. | Fixed: reworded to match. |
| 10b | 11 | Prior text ("transitions to the new question about identifying the tanna of a related baraita") describes a topic from much later in the daf. Actual Hebrew closes the imprisonment sentence, then opens Rava's sukka challenge (dibbur hamatchil quoting Gemara line `yoma-010b-l06`). | Fixed: reworded to describe both halves accurately. |

## Batch 2 findings (VERSION 14.69)

All 6 entries below are the exact examples Batch 1 had already
Hebrew/Gemara-checked in the systemic finding section (see below), now
fixed. For each, both the English helper text and, where the checked
Gemara line was wrong, `linkedGemaraLineIds` were corrected. No Rashi
Hebrew touched.

| daf | vilnaLine | placement (before -> after) | English alignment | resolution |
|---|---|---|---|---|
| 10a | 3 | `yoma-010a-l02` (wrong) -> `yoma-010a-l10` | misaligned - described "tents of Shem" content from an earlier comment | Fixed: reworded to Rav Yosef's identification of Sabtah/Raamah/Sabteca with inner/outer Sakistan; placement corrected to l10. |
| 10a | 4 | `yoma-010a-l02` (wrong) -> `yoma-010a-l10` | misaligned - described the opening of the Genesis 10 nation list, a different comment | Fixed: reworded to Sakistan's geography (mountains, outer region encircling inner); placement corrected to l10. |
| 10a | 22 | `yoma-010a-l39` (wrong) -> `yoma-010a-l42` | misaligned - described Rome "ruling the whole world" as a Mashiach precondition, several comments earlier | Fixed: reworded to Rabbi Yehuda's challenge about other Temple chambers used as guard residences; placement corrected to l42. |
| 10a | 23 | `yoma-010a-l41` (wrong) -> `yoma-010a-l42` | misaligned - described a topic transition to the Parhedrin chamber that had already happened two comments earlier | Fixed: reworded to the end of the "guards of the house" phrase plus Rashi's gloss "it was a decree, explained further on"; placement corrected to l42 (the specific line containing "אלא לשכת פרהדרין גזירה היתה"). |
| 11a | 2 | `yoma-011a-l01` (wrong) -> `yoma-011a-l06` | misaligned - fabricated "a fully walled city ... residents pass daily," details absent from the Hebrew | Fixed: reworded to the actual content (a province surrounded by mountains and forests, reachable only through gates); placement corrected to l06, whose baraita literally contains the phrase "ve-echad sha'arei medinot" (gates of provinces) that this Rashi comment glosses. |
| 11a | 4 | `yoma-011a-l03` (wrong) -> `yoma-011a-l06` | misaligned - described "which tanna authored the baraita," a topic from later in the daf | Fixed: reworded to the place-name gloss "Akra de-Kuvei" (an arch-built structure near Machoza); placement corrected to l06, matching neighboring vilnaLine 6-7's Machoza discussion, which is already linked to l06. |

Placement note: `linkedGemaraLineIds` is inert metadata (see the pilot's
secondary observation above) - correcting it here was done because the
correct line was locally certain for all 6 entries, not because any
validator or rendered UI depends on it.

## Batch 3 findings (VERSION 14.70)

10b vilnaLine 12-20 (the 9 entries left after Batch 1 stopped at
vilnaLine 11) are fixed below. Re-derived the real comment boundaries by
joining the raw talmud.dev print-lines and comparing each to the Gemara
lines `yoma-010b-l06` (Rava's sukka challenge), `l07` (Rava's
resolution: sukka and chamber rest on separate reasons), and `l10` (the
sukka reason spelled out: Rabbi Yehuda requires a permanent dwelling,
citing Sukka 7b). Both English text and `linkedGemaraLineIds` were
corrected where wrong; no Rashi Hebrew touched.

| daf | vilnaLine | placement (before -> after) | English alignment | resolution |
|---|---|---|---|---|
| 10b | 12 | `yoma-010b-l18` (wrong) -> `yoma-010b-l06` | misaligned - described "which baraita is under discussion," a topic from much later in the daf | Fixed: reworded to the actual continuation of Rava's sukka-challenge gloss (the Rabbis exempt it, so an exempting opinion exists even for the seven days); placement corrected to l06. |
| 10b | 13 | `yoma-010b-l18` (wrong) -> `yoma-010b-l07` | misaligned - described "R. Yehuda as the tanna of the baraita," a topic from later in the daf | Fixed: reworded to the comment boundary (closes the prior thought, opens the dibbur hamatchil quoting "when they disagree is regarding the seven"); placement corrected to l07. |
| 10b | 14 | `yoma-010b-l19` (wrong) -> `yoma-010b-l07` | misaligned - described a "single-decree approach" for gates and chambers, a topic not present here | Fixed: reworded to the actual content (the seven-day dispute applies to both chamber and sukka, with positions swapped between them); placement corrected to l07. |
| 10b | 15 | `yoma-010b-l19` (wrong) -> `yoma-010b-l10` | misaligned - described what "one decree" means, a fabricated framing | Fixed: reworded to the comment boundary (closes the swapped-positions point, opens the dibbur hamatchil "and sukka, the reason is separate"); placement corrected to l10. |
| 10b | 16 | `yoma-010b-l19` (wrong) -> `yoma-010b-l10` | misaligned - described a "tanna identification question" continuing to the next daf, a fabricated framing | Fixed: reworded to the actual content (Rabbi Yehuda follows his own established reasoning); placement corrected to l10. |
| 10b | 17 | `yoma-010b-l19` (wrong) -> `yoma-010b-l10` | misaligned - described a cross-daf connection to "mezuza law discussion," not present here | Fixed: reworded to Rashi's actual citation of Rabbi Yehuda's statement in Tractate Sukkah 7b; placement corrected to l10. |
| 10b | 18 | `yoma-010b-l19` (wrong) -> `yoma-010b-l10` | misaligned - described "the phrase used to introduce the identification question," a fabricated framing | Fixed: reworded to the actual content (Rabbi Yehuda validated a sukka higher than twenty cubits); placement corrected to l10. |
| 10b | 19 | `yoma-010b-l19` (wrong) -> `yoma-010b-l10` | misaligned - described "preserving R. Yehuda's consistency" in the tanna-identification framing | Fixed: reworded to the actual content (such a tall sukka is valid only with a permanent partition); placement corrected to l10. |
| 10b | 20 | `yoma-010b-l19` (wrong) -> `yoma-010b-l10` | misaligned - described "the coercion principle for later mezuza applications," a topic from the earlier chamber discussion, not this comment | Fixed: reworded to the actual closing content (a permanent-walled structure is significant for mezuza too, closing the sukka comparison); placement corrected to l10. |

10b's rashiTranslations (21 entries total: 1 fixed in the pilot, 10
fixed in Batch 1, 9 fixed in Batch 3) are resolved through vilnaLine 20.
vilnaLine 21 (the last entry, Hebrew "כל" - the truncated start of the
mishna continuing onto 11a, matching the empty-`en` Gemara line
`yoma-010b-l19`) was not reviewed and remains open; it was out of this
batch's stated scope (vilnaLine 12-20).

Secondary observations (not acted on, out of Batch 3 scope):

- While verifying this batch, vilnaLine 11's `linkedGemaraLineIds`
  (`yoma-010b-l18`, fixed for content only in Batch 1) was also found to
  be a placement mismatch - the fixed English text describes a comment
  boundary between `l13` (the "imprisoned" concern, closing) and `l06`
  (Rava's sukka challenge, opening), not `l18`. Batch 3's scope was
  explicitly limited to vilnaLine 12-20, so this was not corrected here.
- vilnaLine 21's Hebrew ("כל") is a one-word fragment at the daf
  boundary with no clear standalone comment content to translate; a
  future pass should determine whether it needs a translation fix, a
  placement fix, or is better left as-is given its truncated nature.

## Batch 4 findings (VERSION 14.71): self-managed sequenced pass

Three bounded subtasks run in sequence, each grounded only in local
Hebrew (talmud.dev raw print-lines, reconstructed into real comment
boundaries) and local Gemara text (`learning_data.js`). No external
sources consulted; nothing deferred required outside verification that
wasn't available locally, except where explicitly noted.

### Subtask A: 10b's last two open items

| daf | vilnaLine | issue | resolution |
|---|---|---|---|
| 10b | 11 | Placement mismatch flagged in Batch 3's secondary observations: `linkedGemaraLineIds` was `yoma-010b-l18`, but the already-correct English text (fixed in Batch 1) describes a boundary between `l13` (closing) and `l06` (opening, Rava's sukka challenge). | Fixed: placement corrected to `yoma-010b-l06`. English text unchanged (was already accurate). |
| 10b | 21 | Hebrew is the single word "כל" - the truncated start of a mishna citation. Prior English fabricated "final comment connecting the Parhedrin discussion to the general principle of what constitutes a dwelling." | Fixed: confirmed via cross-daf check that this is the same Rashi comment whose continuation is 11a vilnaLine 1 ("כל השערים. שערי מזרח עזרה:", glossing the mishna's "all the gates" as the Temple courtyard's eastern gates). Reworded to state this directly, grounded in the local 11a text rather than fabricating content. Placement (`yoma-010b-l19`, matching the identical Hebrew "כׇּל" in the Gemara) was already correct. |

10b's rashiTranslations (21 entries) are now fully resolved.

### Subtask B: 6 entries in 10a, 6 in 11a

| daf | vilnaLine | placement (before -> after) | issue | resolution |
|---|---|---|---|---|
| 10a | 2 | `l02` -> `l01` | Placement only - the Hebrew ("שכינה שורה אלא במקדש ראשון...") is the tail of the same comment as vilnaLine 1, which glosses Genesis 9:27 (`l01`), not the nation list (`l02`). English was already accurate. | Fixed: placement corrected. |
| 10a | 5 | unchanged (`l10`) | English fabricated "on Gomer - identifies it with Germania"; actual Hebrew continues the Sakistan geography measurement from vilnaLine 4 (the outer circumference distance). | Fixed: reworded to the actual measurement content. |
| 10a | 6 | unchanged (`l10`) | English fabricated "on Magog - identifies it with Kandia"; actual Hebrew closes the same Sakistan measurement (one thousand parasangs). | Fixed: reworded to match. |
| 10a | 7 | `l10` -> `l15` | English fabricated "on Madai - identifies it with Macedonia"; actual Hebrew is a new comment on "out of that land went forth Asshur" (Genesis 10:11, matching `l15`), explaining Asshur left to avoid the Tower of Babel generation's plan. | Fixed: reworded and placement corrected. |
| 10a | 8 | `l10` -> `l25` | English fabricated "on Yavan - identifies it with Greece"; actual Hebrew is a new comment on the verse "and there were Ahiman, Sheshai, and Talmai" (Numbers 13:22, matching `l25`), explaining why the tanna included this tangential verse. | Fixed: reworded and placement corrected. |
| 10a | 24 | `l41` -> `l42` | English described "why the Parhedrin chamber is exceptional," a vague paraphrase; actual Hebrew is the direct continuation of vilnaLine 22-23's comment (fixed in Batch 2, already linked to `l42`) explaining the decree's rationale (avoiding the impression of imprisonment). | Fixed: reworded to continue the same comment accurately and placement corrected to match vilnaLine 22-23. |
| 11a | 9 | `l10` -> `l17` | English prematurely described "checked only twice per jubilee" content that belongs several lines later; actual Hebrew opens a new comment on "because of danger" (matching `l17`), explaining the king might suspect witchcraft. | Fixed: reworded and placement corrected. |
| 11a | 10 | `l10` -> `l17` | English described "the 1000-zuz fine," content belonging to a much later comment (`l19`); actual Hebrew completes the "danger" comment (witchcraft accusation). | Fixed: reworded and placement corrected. |
| 11a | 11 | unchanged (`l17`, already correct) | English described "shluchei mitzva einan nizzokin," content belonging to `l19`; actual Hebrew is a new comment on "is checked" (rot or theft). | Fixed: reworded, placement was already correct. |
| 11a | 12 | unchanged (`l17`, already correct) | English described "Samuel's precedent," content belonging to `l19`; actual Hebrew continues "and the public's" (gates of courtyards and provinces). | Fixed: reworded, placement was already correct. |
| 11a | 13 | `l19` -> `l17` | English described "shani sakanta d'keviya," misattributed phrasing; actual Hebrew opens "twice in the jubilee," explaining reduced-frequency checking for public property. | Fixed: reworded and placement corrected. |
| 11a | 14 | `l26` -> `l17` | English fabricated storehouse-type content (`l26` topic, much later); actual Hebrew continues the "twice in the jubilee" comment (public property should not be over-burdened). | Fixed: reworded and placement corrected. |

### Subtask C: 12 more entries in 11a (vilnaLine 15-26)

| daf | vilnaLine | placement (before -> after) | issue | resolution |
|---|---|---|---|---|
| 11a | 15 | `l26` -> `l17` | English fabricated Rav Kahana storehouse content; actual Hebrew closes the "over-burdened public property" comment. | Fixed: reworded and placement corrected. |
| 11a | 16 | `l26` -> `l19` | English fabricated "nashim ne'otot bahen" content (`l26` topic); actual Hebrew opens a new comment on "be-artavin" (the mezuza examiner's name), matching `l19`. | Fixed: reworded and placement corrected. |
| 11a | 17 | `l32` -> `l19` | English described a fabricated "Rav Yehuda's position" on wood vs. wine storehouses; actual Hebrew continues the "artavin" name gloss. | Fixed: reworded and placement corrected. |
| 11a | 18 | `l32` -> `l19` | English fabricated content; actual Hebrew opens a new comment on "kasdor" (the Roman official's title). | Fixed: reworded and placement corrected. |
| 11a | 19 | `l36` -> `l19` | English fabricated "second Rav Yehuda ruling" content; actual Hebrew opens "where the danger is permanent," glossing the ruler's standing false accusations. | Fixed: reworded and placement corrected. |
| 11a | 20 | `l36` -> `l19` | English fabricated content; actual Hebrew opens the Samuel/David-anointing verse citation ("how will I go"). | Fixed: reworded and placement corrected. |
| 11a | 21 | `l38` -> `l19` | English fabricated "nashim ne'otot bahen interpretation" content; actual Hebrew closes the Samuel citation gloss, then opens on "storehouses." | Fixed: reworded and placement corrected. |
| 11a | 22 | `l38` -> `l26` | English fabricated content; actual Hebrew explains "storehouses" means those holding wine, oil, and grain, matching `l26`. | Fixed: reworded and placement corrected. |
| 11a | 23 | `l41` -> `l26` | English fabricated "first baraita" content; actual Hebrew closes the storehouse gloss, then opens "what does make-use mean? Bathe." | Fixed: reworded and placement corrected. |
| 11a | 24 | `l41` -> `l26` | English fabricated content; actual Hebrew explains "na'ot" as a term for benefit or pleasure. | Fixed: reworded and placement corrected. |
| 11a | 25 | `l44` -> `l26` | English fabricated "dirat adam/dirat kavod" framing; actual Hebrew continues explaining the shameful nature of women bathing unclothed there. | Fixed: reworded and placement corrected. |
| 11a | 26 | `l44` -> `l26` | English fabricated "bathrooms, tanneries" content, a topic from much later; actual Hebrew concludes this specific comment (not fitting for Heaven's honor to have a mezuza present). | Fixed: reworded and placement corrected. |

11a's rashiTranslations (43 entries total) were resolved through
vilnaLine 26 as of Batch 4 (vilnaLine 2, 4, and 9-26: 20 entries fixed
across Batch 2 and Batch 4). The remaining entries were closed out in
Batch 5 below.

No deferrals were needed in Batch 4 - every line audited had a locally
certain fix (grounded in the raw talmud.dev text and the matching
Gemara line), so nothing required external source review.

## Batch 5 findings (VERSION 14.72): 11a closed out

The remaining 24 entries of 11a (vilnaLine 1, 3-8, 27-43), fixed by
reconstructing the real comment boundaries and comparing to the local
Gemara lines. This closes out 11a's rashiTranslations (43/43 resolved).

| daf | vilnaLine | placement (before -> after) | issue | resolution |
|---|---|---|---|---|
| 11a | 1 | unchanged (`l01`) | English covered only the first half of the line ("all the gates" gloss) and omitted that the line also opens a second dibbur hamatchil, "echad sha'arei medinot." | Fixed: reworded to describe both halves. |
| 11a | 3 | `l03` -> `l10` | English fabricated a Nicanor Gate history (Nikanor of Alexandria, copper doors, caretakers); actual Hebrew closes the province gloss ("like the land of Hagar") and opens the "abulei d'Machoza" comment, quoting Gemara `l10`. | Fixed: reworded and placement corrected. |
| 11a | 4 | `l06` -> `l10` | Correction of a Batch 2 placement: Batch 2 correctly rewrote the English (Machoza/Akra de-Kuvei) but anchored to `l06` by matching the then-unverified neighboring entries; the Machoza/Kuvei discussion is actually Gemara `l10`. Also refined the English: the Hebrew says the structure is built above the gates, and notes Machoza's mostly-Jewish population. | Fixed: placement corrected, English refined. |
| 11a | 5 | `l03` -> `l10` | English fabricated a "gezeira ligzeira" explanation (a `l03` topic, but not this Rashi's content); actual Hebrew continues the Kuvei gloss (gates beneath it are arch-shaped). | Fixed: reworded and placement corrected. |
| 11a | 6 | `l06` -> `l10` | English described the "abulei d'Machoza" gloss, which actually sits at vilnaLine 3; actual Hebrew here finishes the arch-strength point and opens "ve-akra de-Kuvei gufah." | Fixed: reworded and placement corrected. |
| 11a | 7 | `l06` -> `l10` | English fabricated a "Rav Safra's answer" paraphrase; actual Hebrew continues "the fort of Kuvei itself" (because of that very building). | Fixed: reworded and placement corrected. |
| 11a | 8 | unchanged (`l10`) | English paraphrased Abaye's challenge with fabricated reasoning about doorposts; actual Hebrew gives the real reason (one enters the fort through that gate). | Fixed: reworded. |
| 11a | 27 | `l45` -> `l32` | English fabricated "second baraita" framing; actual Hebrew opens the comment on "even though the women adorn themselves" (with perfumes), quoting `l32`. | Fixed: reworded and placement corrected. |
| 11a | 28 | `l48` -> `l32` | English fabricated "conflict between the two baraitot" content; actual Hebrew continues (you might think it is a dwelling; it teaches us). | Fixed: reworded and placement corrected. |
| 11a | 29 | `l48` -> `l36` | English fabricated "gatehouse exclusion" content (an 11b topic); actual Hebrew concludes "not a dwelling," then opens "ela mai it lakh lemeimar," quoting `l36`. | Fixed: reworded and placement corrected. |
| 11a | 30 | `l51` -> `l36` | English fabricated "aksenedra" content (an 11b topic); actual Hebrew continues (when you explained ne'otot as mitkashtot). | Fixed: reworded and placement corrected. |
| 11a | 31 | `l51` -> `l36` | English fabricated "marpeset" content (an 11b topic); actual Hebrew continues (baraita would contradict baraita, forcing a tannaitic dispute). | Fixed: reworded and placement corrected. |
| 11a | 32 | `l51` -> `l36` | English fabricated "three exclusion categories" content; actual Hebrew opens "ve-yesh mechayvin" (quoting `l36`): this is the tannaitic dispute, each Amora resolves per his reasoning. | Fixed: reworded and placement corrected. |
| 11a | 33-36 | `l51` -> `l36` (each) | English fabricated bathroom/tannery/bathhouse/mikveh exclusion content (topics from `l38`/`l45`, described inaccurately); actual Hebrew spells out the two resolutions: Rav Kahana (dispute is the standard case; adorning obligates per all) and Rav Yehuda (dispute is the adorning case; standard exempt per all). | Fixed: reworded as accurate continuations and placement corrected. |
| 11a | 37 | `l51` -> `l38` | English fabricated Temple Mount/sacred-space content; actual Hebrew closes the prior comment and opens "ve-she-hanashim ne'otot bahen," quoting the `l38` baraita. | Fixed: reworded and placement corrected. |
| 11a | 38-41 | `l51` -> `l38` (each) | English fabricated tiyuvta/sacred-mundane/three-part-framework content; actual Hebrew explains the referent (hay/cattle/wood structures where women bathe) and why the immersion house needed separate mention despite lacking filth. | Fixed: reworded as accurate continuations and placement corrected. |
| 11a | 42 | `l51` -> `l48` | English fabricated a "six gates" count discussion; actual Hebrew closes the immersion-house point and glosses "ve-lulin" (chicken coops, a place for raising chickens), quoting the `l48` baraita. | Fixed: reworded and placement corrected. |
| 11a | 43 | unchanged (`l51`) | English fabricated "seven gate types" content; actual Hebrew is the single word "beit," the truncated start of the "beit sha'ar" comment continuing onto 11b (confirmed against 11b's first Rashi line). Placement already matched the Gemara's identical truncated word at `l51`. | Fixed: reworded to state the cross-daf continuation. |

No deferrals were needed in Batch 5.

## Batch 6 findings (VERSION 14.73): 10a closed out

The remaining 25 entries of 10a (vilnaLine 1, 9-21, 25-35), fixed by
the same reconstruction method. This closes out 10a's rashiTranslations
(35/35 resolved), completing the early-daf hotspot (10a, 10b, 11a).
Even the aggadic name-etymology comments turned out to be fully
locally groundable: each dibbur hamatchil quotes a phrase in Gemara
line `l25` verbatim, and the glosses are self-contained (strides,
Lamentations 3 citation, plow rows, neck through the sky window), so
no external research or deferral was needed.

| daf | vilnaLine | placement (before -> after) | issue | resolution |
|---|---|---|---|---|
| 10a | 1 | unchanged (`l01`) | English was a vague paraphrase ("explains the verse... and how it connects"); actual Hebrew opens 'even though God will enlarge Japheth' - the Persians merited to build the Second Temple, yet. | Fixed: reworded for precision. |
| 10a | 9 | `l10` -> `l25` | English fabricated "on Tuval - Beit Unaiki"; actual Hebrew completes the Ahiman comment (the tanna was expounding names, so he cited this verse too). | Fixed: reworded and placement corrected. |
| 10a | 10 | `l10` -> `l25` | English fabricated "on Meshech - Musya"; actual Hebrew opens the gloss on 'who renders the land like pits' (quoting `l25` verbatim) - with his strides. | Fixed: reworded and placement corrected. |
| 10a | 11 | `l12` -> `l25` | English fabricated "on Tiras - Persia"; actual Hebrew closes the strides gloss and opens 'and Sheshai' - a term of ruin. | Fixed: reworded and placement corrected. |
| 10a | 12 | `l12` -> `l25` | English fabricated Tiras/Persia significance; actual Hebrew cites 'ruin and breaking' (Lamentations 3) and begins the one-root-letter point. | Fixed: reworded and placement corrected. |
| 10a | 13 | `l15` -> `l25` | English fabricated "proof that Persia will overcome Rome"; actual Hebrew concludes the shin-root point and opens 'furrows' - like the rows. | Fixed: reworded and placement corrected. |
| 10a | 14 | `l15` -> `l25` | English fabricated "first of three proofs"; actual Hebrew concludes 'of the plow,' then records a girsa note - the 'davar acher' reading is not in Rashi's text. | Fixed: reworded and placement corrected. |
| 10a | 15 | `l15` -> `l25` | English fabricated "second proof"; actual Hebrew opens 'the sun is a necklace' (quoting `l25`) - it appears as though his neck. | Fixed: reworded and placement corrected. |
| 10a | 16 | `l25` -> `l28` | English fabricated "third proof"; actual Hebrew concludes the sky-window image and opens a textual note on the next statement's attribution. | Fixed: reworded and placement corrected to the newly-opened comment's line. |
| 10a | 17 | unchanged (`l28`) | English fabricated "Rav's dissent... destroy synagogues" (an `l37` topic); actual Hebrew is a girsa note: the correct reading is 'Rabbi Yehoshua ben Levi said in the name of Rabbi.' | Fixed: reworded. |
| 10a | 18 | `l28` -> `l32` | English fabricated synagogue-destruction significance; actual Hebrew opens 'he stated it before one of the Sages' (quoting `l32`). | Fixed: reworded and placement corrected. |
| 10a | 19 | `l30` -> `l34` | English fabricated "how Rav's position differs"; actual Hebrew concludes (the thing stated was Rabbah bar Ulla's objection) and opens 'the Chaldeans fell' (quoting `l34`). | Fixed: reworded and placement corrected to the newly-opened comment's line. |
| 10a | 20 | `l37` -> `l34` | English fabricated nine-month-tradition content (an `l39` topic); actual Hebrew continues - Belshazzar into the hand of. | Fixed: reworded and placement corrected. |
| 10a | 21 | `l37` -> `l34` | English fabricated a Micah-verse identification; actual Hebrew concludes - Darius the Mede and Cyrus the Persian, his son-in-law. | Fixed: reworded and placement corrected. |
| 10a | 25 | unchanged (`l44`) | English said the comment "clarifies R. Yehuda's position that the chamber qualifies as a genuine residence" - backwards; actual Hebrew concludes the imprisonment concern and opens 'is not a house' (quoting `l44`). | Fixed: reworded. |
| 10a | 26 | `l44` -> `l46` | English fabricated "the Sages' counter-position"; actual Hebrew concludes (for mezuza we require a significant house) and opens 'Rabbi Yehuda obligates' (quoting `l46`). | Fixed: reworded and placement corrected to the newly-opened comment's line. |
| 10a | 27-30 | 27-28 unchanged (`l46`); 29-30 `l47` -> `l46` | English fabricated imprisonment-reason and residence-type content; actual Hebrew is one continuous gloss on 'Rabbi Yehuda obligates': regarding tithes, tevel is not obligated (even against casual eating) until it enters through the front of the house, citing 'I have removed the sacred portion from the house.' | Fixed: reworded as accurate continuations, placement corrected where wrong. |
| 10a | 31-34 | 31 `l47` -> `l46`; 32-34 `l48` -> `l46` | English fabricated dirat keva/coercion content (topics belonging to `l44`/10b); actual Hebrew glosses 'in eruv' (an unmerged sukka opening onto a shared courtyard prohibits all residents from carrying) and 'and in mezuza' (even though not made for both seasons). | Fixed: reworded as accurate continuations and placement corrected. |
| 10a | 35 | unchanged (`l48`) | English fabricated a "closing note on how the Sages' decree differs"; actual Hebrew is the single word 'ela,' the truncated start of the 'ela amar Abaye' comment continuing onto 10b (confirmed against 10b's first Rashi line). `l48` is the daf's own truncated final Gemara word, the closest local anchor. | Fixed: reworded to state the cross-daf continuation. |

No deferrals were needed in Batch 6.

## Batch 7 findings (VERSION 14.74): 11b, vilnaLine 1-25

Moved to the next daf in the same mezuza sugya (11a vilnaLine 43's
truncated comment continues directly into 11b vilnaLine 1, "beit
sha'ar"). 11b's rashiTranslations (39 entries) had the same descriptive-
style mismatch pattern, compounded by a real complication: raw print-
lines 1-3 gloss three terms (beit sha'ar, marpeset, akhsadra) in a
different order than the prior entries assumed, so the term-to-content
alignment was off by roughly one line throughout the opening block.
Raw print-lines 4-25 are dense architectural/geometric material (the
Median gate dispute over arch dimensions - foot height, opening width,
"chokkein lehashlem") where each vilnaLine is often a short fragment of
one long technical sentence; fixes here describe the specific fragment
at that position rather than summarizing the whole passage, matching
the established per-fragment convention (see Batch 1's 10b dirat-keva
fixes). Every fix was grounded directly in the raw talmud.dev text
cross-checked against the Gemara's own detailed English translation
(same measurements, same terms), so no external source was needed. This
batch covers vilnaLine 1-25 of 39; vilnaLine 26-39 remain for Batch 8.

| daf | vilnaLine | placement (before -> after) | issue | resolution |
|---|---|---|---|---|
| 11b | 1 | unchanged (`l01`) | English was reasonably close ("gatehouse... passageway... exempt") but not a precise gloss of the specific Hebrew (which glosses "shortcut," not "passageway/not a dwelling"). | Fixed: reworded for precision. |
| 11b | 2 | unchanged (`l01`) | English fabricated "aksenedra" content, a term not glossed until much later (Batch 8's vl30 area, per the prior mis-numbering); actual Hebrew closes the gatehouse gloss and opens on "marpeset" (balcony), not aksenedra. | Fixed: reworded to the actual term and content. |
| 11b | 3 | unchanged (`l01`) | English fabricated "marpeset" content, which actually belongs at vilnaLine 2; actual Hebrew closes the balcony gloss and opens "akhsadra" (portico), then a new comment "a conclusive refutation." | Fixed: reworded to the actual terms and content. |
| 11b | 4 | `l03` -> `l10` | English fabricated a bathroom/kavod exemption (an `l03` topic, but not glossed at this position); actual Hebrew closes the "tannaitic dispute" note and opens "and the Median gate" (quoting `l10`). | Fixed: reworded and placement corrected. |
| 11b | 5 | `l03` -> `l10` | English fabricated tannery-exemption content; actual Hebrew continues the Median gate gloss (made in Media) and opens "that is not roofed." | Fixed: reworded and placement corrected. |
| 11b | 6 | `l03` -> `l10` | English fabricated bathhouse-exemption content; actual Hebrew continues the unroofed-gate gloss and opens "and the Rabbis." | Fixed: reworded and placement corrected. |
| 11b | 7 | `l07` -> `l10` | English fabricated mikveh-exemption content (an `l07` topic, misattributed here); actual Hebrew continues "who exempt it, because there is no gate without four handbreadths width." | Fixed: reworded and placement corrected. |
| 11b | 8 | `l07` -> `l10` | English fabricated Temple Mount exemption content; actual Hebrew continues the dome-narrowing point. | Fixed: reworded and placement corrected. |
| 11b | 9 | `l07` -> `l15` | English fabricated "tiyuvta d'Rav Yehuda" content (that note is actually vilnaLine 3, not here); actual Hebrew closes the narrowing point and opens "and they agree that if at its foot there are ten" (quoting `l15`). | Fixed: reworded and placement corrected. |
| 11b | 10-24 | `l10`/`l15`/`l21` (varied) -> `l15` (each) | English throughout this range fabricated summary content about the "six gates" count and the chokkein lehashlem dispute in general terms, not tied to the specific fragment at each line; actual Hebrew is the granular geometric text (foot/height/width measurements for the two disputed sub-cases). | Fixed: reworded each as the accurate specific fragment; placement corrected to `l15` throughout (the line containing this entire passage). |
| 11b | 25 | `l38` -> `l21` | English fabricated a "first resolution: R. Meir vs. Rabbis" synagogue-tzaraat framing (an `l38` topic from much later); actual Hebrew opens the transition into `l21`'s specific dispute case (foot 3, width not yet 4, room to carve). | Fixed: reworded and placement corrected. |

No deferrals were needed in Batch 7.

## Batch 8 findings (VERSION 14.75): 11b closed out

The remaining 14 entries of 11b (vilnaLine 26-39), fixed by the same
reconstruction method. This closes out 11b's rashiTranslations (39/39
resolved). A significant finding: the previous English for vilnaLine
26-39 fabricated an entire synagogue/tzaraat contradiction-resolution
discussion (three resolutions: tanna dispute, city-vs-village
synagogues, caretaker's residence) attributed to Gemara lines
`l38`/`l40`/`l41`. That discussion is real (it happens in the actual
Gemara text), but Rashi's local commentary on 11b never reaches it - the
real Rashi text at vilnaLine 26-32 is still finishing the chokkein
lehashlem geometry comment from Batch 7, vilnaLine 33-38 covers two
unrelated topics (the Deuteronomy reward-verse gloss and an aggadah
about stinginess causing house-plagues), and vilnaLine 39 is a single
truncated word ("dekarkhim," of cities) that continues onto 12a. The
city-vs-village synagogue content the prior English fabricated does
turn out to be real Rashi commentary - just one daf later, confirmed by
matching 11b's vilnaLine 39 word-for-word against 12a's own first Rashi
line ("דכרכים. שהוא מקום שווקים ומתקבצים שם ממקומות הרבה..."). No new
content was invented for 11b; the fabricated material was left
undescribed here and correctly attributed to 12a instead.

| daf | vilnaLine | placement (before -> after) | issue | resolution |
|---|---|---|---|---|
| 11b | 26 | `l38` -> `l21` | English fabricated "R. Meir vs. Rabbis" content; actual Hebrew continues the chokkein lehashlem diagram note from Batch 7 (the wall does not taper to match the inner space). | Fixed: reworded and placement corrected. |
| 11b | 27-28 | `l40` -> `l21` (each) | English fabricated "city vs. village synagogues" content (this topic is real, but on 12a - see above); actual Hebrew continues the same diagram note (the wall runs long outside, relative to the inner space, in this pattern). | Fixed: reworded and placement corrected. |
| 11b | 29 | `l41` -> `l21` | English fabricated "caretaker's house" content; actual Hebrew closes the diagram note and opens "Rabbi Meir holds." | Fixed: reworded and placement corrected. |
| 11b | 30-32 | `l41` -> `l21` (each) | English fabricated "three resolutions" summary content; actual Hebrew continues Rabbi Meir's carve-to-complete reasoning (since it began with three handbreadths in a width of four, there is a doorway on it, viewed as though carved to widen it above to match the measure below). | Fixed: reworded as accurate continuations and placement corrected. |
| 11b | 33 | `l41` -> `l27` | English fabricated a "12a transition, Jerusalem's tribal division" summary; actual Hebrew opens a new comment on "so that your days be many" (Deuteronomy 11:21, quoting `l27`). | Fixed: reworded and placement corrected. |
| 11b | 34 | `l41` -> `l29` | English fabricated "tzaraat in Jerusalem" content; actual Hebrew closes the reward-verse gloss and opens "the way of your entry" (quoting `l29`, Rava's right-foot teaching). | Fixed: reworded and placement corrected. |
| 11b | 35 | `l41` -> `l29` | English fabricated "three-part contradiction resolution preserved" content; actual Hebrew continues Rava's teaching (entering the house, not exiting) and opens "to the one who." | Fixed: reworded and placement corrected. |
| 11b | 36-38 | `l41` -> `l33` (each) | English fabricated "review of 11b themes" and "parallel mezuza/tzaraat structure" content; actual Hebrew is the aggadah on "who dedicates his house to himself" - vessels reserved for personal use, not lent to neighbors, meaning that house-plagues (nega'im) come on account of stinginess (quoting `l33`). | Fixed: reworded as accurate continuations and placement corrected. |
| 11b | 39 | `l41` -> `l41b` | English fabricated a "caretaker principle recalled on 12a" summary; actual Hebrew is the single word "dekarkhim" (of cities), confirmed via cross-daf match to be the truncated start of 12a's own first Rashi comment. Placement corrected to the daf's actual final (truncated) Gemara line `l41b`, replacing a dangling reference to the nonexistent id `l41` (the real ids are `l41a`/`l41b`; this was a pre-existing broken reference not touched in prior batches since placement was out of scope until now). | Fixed: reworded to state the cross-daf continuation; placement corrected to a valid id. |

No deferrals were needed in Batch 8.

## Batch 9 findings (VERSION 14.76): 12a, vilnaLine 1-16

Moved to the next daf, 12a, which continues 11b's final truncated word
("dekarkhim," of cities). 12a's rashiTranslations has 66 entries total
(matching 66 raw talmud.dev print-lines) with the same descriptive-style
fabrication pattern, now covering two genuinely distinct topics: the
tail of the Jerusalem tribal-division/synagogue-tzaraat discussion
(vilnaLine 1-16, continuing directly from 11b) and a separate Kohen
Gadol investiture sugya (vilnaLine 17-66, roughly 50 entries, many
collapsed onto the single empty-`en` Gemara line `yoma-012a-l45`, which
is itself truncated at the daf boundary and continues onto 12b). Given
the size (66 entries, over twice the per-batch bound) and the clean
topic break at vilnaLine 16/17, this batch covers only vilnaLine 1-16 -
the complete, self-contained conclusion of the mezuza/tzaraat sugya
that has run since 10a. vilnaLine 17-66 (the investiture sugya) is new
scope, not part of the original mezuza discussion, and needs its own
dedicated batch(es).

Also found and fixed a pre-existing dangling `linkedGemaraLineIds`
reference: the prior entries pointed to `yoma-012a-l01`, `l08`, `l10`,
etc., but the real ids for the first Gemara line are `l01a`/`l01b` (a
duplicate-vilna-line split, same pattern as 11b's `l41a`/`l41b`).

| daf | vilnaLine | placement (before -> after) | issue | resolution |
|---|---|---|---|---|
| 12a | 1 | `l01` (dangling) -> `l01a` | English fabricated "opens the tribal-division discussion, R. Yehuda vs. Tanna Kama"; actual Hebrew is the direct continuation of 11b's truncated word, glossing "cities" as marketplaces with no specific owner. | Fixed: reworded and placement corrected to a valid id. |
| 12a | 2 | `l01` (dangling) -> `l01a` | English fabricated "what it means for Jerusalem to be divided"; actual Hebrew closes the cities gloss and opens on "villages" - owners identifiable, like a house of partners. | Fixed: reworded and placement corrected. |
| 12a | 3-6 | `l01` (dangling) -> `l01b` (each) | English fabricated "Tanna Kama's position" and "tzaraat of city synagogues" content; actual Hebrew closes the villages gloss and opens on "and Jerusalem does not become impure with plagues," explaining the "not divided among the tribes" view, then "I did not hear [otherwise]" for the opposing view. | Fixed: reworded as accurate continuations and placement corrected. |
| 12a | 7-10 | `l08` (dangling) -> `l01b` (each) | English fabricated "baraita detailing Temple structures" and "Lishkat HaGazit" content (an `l10` topic, described too early); actual Hebrew continues the "except for the site of the Temple alone" gloss, citing the David/Aravna threshing-floor purchase and its source in Sifrei and Zevachim 116b. | Fixed: reworded as accurate continuations and placement corrected. |
| 12a | 11 | `l08` (dangling) -> `l08` (valid) | English fabricated content already covered (misplaced) at vilnaLine 5-6; actual Hebrew opens "about what do they disagree" - Rabbi Yehuda and the Rabbis. | Fixed: reworded; placement id corrected to the valid form (no `a`/`b` split needed here). |
| 12a | 12-16 | `l10` (dangling) -> `l10` (valid) (each) | English fabricated "Altar in Benjamin's portion" and "Heikhal" content out of order; actual Hebrew is Rashi's geographic description of the Temple Mount's eastern side, courtyard measurements, and the priests' tread-area, leading toward the altar strip in Benjamin's portion. | Fixed: reworded as accurate continuations; placement id corrected to the valid form. |

No deferrals were needed in Batch 9. vilnaLine 17-66 (the Kohen Gadol
investiture sugya) remain open for a future batch.

## Batch 10 findings (VERSION 14.77): 12a, vilnaLine 17-36

Continued 12a with vilnaLine 17-36, the remaining portion of Gemara
sugya s01 (Gemara lines `l10` through `l30`, ending at the sugya
boundary right before `l33` begins sugya s02, the Kohen Gadol
investiture dispute). This range covers the tail of the tribal-boundary
geography (the altar strip crossing from Judah's portion into
Benjamin's), Rashi's gloss on "chofef" and "ushpizchan" (Deuteronomy
33:12, cited for why Benjamin is called the Divine Presence's host),
a tannaitic dispute about whether Jerusalem was divided among the
tribes, a gloss on "hides of consecrated offerings / jug / hide" (the
custom of leaving these for one's host), and the "la'achuzah" /
"to the paternal houses" / "each individual does not recognize his
own" sequence that ties back into the tzaraat-in-Jerusalem discussion
via Leviticus 14. All prior English at these lines described the
Kohen Gadol investiture/belt dispute (real content, but belonging to
vilnaLine 37+, not here) - the same fabrication pattern as every
other daf in this hotspot: plausible-sounding but wrong content,
lifted from later on the same daf.

vilnaLine 17-20 continue the single Rashi comment opened at vilnaLine
10-16 (Batch 9), so they stay linked to `yoma-012a-l10`. vilnaLine
21-23 are Rashi's "chofef" gloss, linked to `l17`. vilnaLine 24-30
cover three short DHs ("and this tanna," "hides of consecrated
offerings," "golfa"/"u-maskha") that all explain material within
`l19` (the "Jerusalem was not divided" baraita and Abaye's
host-custom statement), so they stay linked to `l19`. vilnaLine 31-34
are the "la'achuzah" / "to the paternal houses" / "and each
individual does not" sequence, linked to `l26`. vilnaLine 35-36 open
"as we answered originally, that it has dwelling in it" - Rashi's
gloss on the Gemara's own back-reference (`l30`) - and end right as
the Gemara's text moves into the disqualified-Kohen-Gadol scenario
(`l33`), which is where vilnaLine 37 and the next batch pick up.

| daf | vilnaLine | placement (before -> after) | issue | resolution |
|---|---|---|---|---|
| 12a | 17-20 | `l33` -> `l10` (each) | English fabricated "Gemara's return to the mishna's disqualified Cohen Gadol scenario" (an `l33`+ topic); actual Hebrew continues the tribal-boundary description from vilnaLine 10-16: the boundary runs westward into Benjamin's portion, except that the altar's strip crosses in from Judah's portion into the southeastern corner. | Fixed: reworded as accurate continuations; placement corrected to `l10`. |
| 12a | 21-23 | `l36` -> `l17` (each) | English fabricated "urgency of the investiture question" content; actual Hebrew glosses "chofef" (hovers) as the self-scratching of unfulfilled desire (citing Nazir 42a), then opens "ushpizchan" (their host). | Fixed: reworded and placement corrected to `l17`. |
| 12a | 24-30 | `l42`/`l45` -> `l19` (each) | English fabricated "Rav Adda's belt proposal" and "tzinnora" content (an `l36`+ topic); actual Hebrew explains "ushpizchan" (the Ark was in Benjamin's portion), then a tannaitic dispute over whether Jerusalem was divided among the tribes, then the custom of leaving a jug and hide for one's host. | Fixed: reworded as accurate continuations; placement corrected to `l19`. |
| 12a | 31-34 | `l45` -> `l26` (each) | English fabricated "Abaye's counter-proposal" and "symbolic minimum" content; actual Hebrew glosses "la'achuzah" (for a possession, Leviticus 14) and "to the paternal houses" (to families), tying tzaraat-susceptibility to individual family ownership. | Fixed: reworded and placement corrected to `l26`. |
| 12a | 35-36 | `l45` -> `l30` (each) | English fabricated "Rav Pappa's answer continues on the next daf" and "practical significance" content; actual Hebrew closes the "and each individual does not [recognize his own]" gloss, then opens "as we answered originally, that it has dwelling in it," which explains the Gemara's own back-reference before the text shifts to the disqualified-Kohen-Gadol scenario. | Fixed: reworded and placement corrected to `l30`. |

No deferrals were needed in Batch 10. vilnaLine 37-66 (the Kohen Gadol
investiture dispute proper - Rav Adda's belt proposal, Abaye's eight
garments and tzinnora, and the cross-daf continuation into 12b) remain
open for a future batch.

## Batch 11 findings (VERSION 14.78): 12a, vilnaLine 37-66 (closing 12a)

Finished 12a with vilnaLine 37-66, all of Gemara sugya s02 (lines `l33`,
`l36`, `l42`, `l45`): the Kohen Gadol investiture dispute proper. The
mishna's two disqualification scenarios (before vs. after the morning
tamid) are both on `l33`; Rav Adda bar Ahava's proposal that the belt
alone marks the investiture, plus the sub-dispute over whether the
High Priest's everyday belt matches the common priest's, is on `l36`;
Abaye's counter-proposal (eight garments plus turning a tamid limb
with an iron fork, the tzinnora) and Rav Huna's death-penalty ruling
for a non-priest who does the same are on `l42`. All prior English
described this same dispute but attached it to the wrong lines within
it (Rav Adda's belt proposal mislabeled as tied to `l42`/`l45`
instead of `l36`, Abaye's proposal split across `l36`/`l42`/`l45`
instead of consolidated on `l42`, and several lines carrying vague,
non-committal restatements like "notes the practical significance" or
"summary of the tribal-geography and investiture sections" that named
no actual Rashi content) - a milder version of the same fabrication
pattern, since the topic was already correct but the line-level
placement and specificity were not.

vilnaLine 66 is the daf's final raw print-line, a single truncated
word ("avodato," his service) matching Gemara `l45`'s own truncated
final word. Checked 12b vilnaLine 1: its rashiTranslations entry was
already correctly fixed in an earlier pass and confirms the
continuation - the raw talmud.dev text there opens "avodato
mechanchato" (his service inducts him), Rav Pappa's resolution of the
belt dispute. vilnaLine 66 was reworded to document the cross-daf
link rather than fabricate content, matching the pattern already used
at 10a-vl35, 10b-vl21, 11a-vl43, and 11b-vl39.

| daf | vilnaLine | placement (before -> after) | issue | resolution |
|---|---|---|---|---|
| 12a | 37-47 | `l45` (each) -> `l33` (each) | English fabricated generic content ("Yom Kippur context," "closing comment on the dispute," "connects back to the mishna," vague notes on garments/textual sources); actual Hebrew is Rashi's explanation of both mishna scenarios on `l33`: disqualification before the morning tamid (induct via the tamid itself, in eight garments) and disqualification after it (what then identifies the replacement as a genuine Cohen Gadol). | Fixed: reworded as accurate continuations of the real DHs "eira" and "bameh mechanchin oto"; placement corrected to `l33`. |
| 12a | 48-60 | `l45`/`l33`/`l36` (mixed) -> `l36` (each) | English fabricated or vaguely restated the belt dispute ("linguistic and contextual definition of tzinnora" on lines that do not mention tzinnora, "brief note on shared garments," generic summaries); actual Hebrew is Rav Adda's belt proposal and the sub-dispute over whether the High Priest's everyday belt equals the common priest's, all glossing `l36`. | Fixed: reworded as accurate continuations of the real DHs "be'avnet," "hanicha lemad," "zehu avneto shel kohen hedyot," and "ella lemaan de'amar"; placement corrected to `l36`. |
| 12a | 61-65 | `l36`/`l42` (mixed) -> `l42` (each) | English fabricated "timing of investiture," "Rav Adda's reasoning," and "why minimal investiture is insufficient" content not grounded in these specific lines; actual Hebrew is Abaye's counter-proposal (eight garments plus turning a tamid limb with an iron fork, the tzinnora) and Rav Huna's death-penalty ruling for a non-priest performing the same act. | Fixed: reworded as accurate continuations of the real DHs "amar Abaye," "b'tzinnora," and "chayav mitah"; placement corrected to `l42`. |
| 12a | 66 | `l45` (valid, but content fabricated) | English fabricated "final note on Abaye's position" content; actual Hebrew is a single truncated word ("avodato") matching Gemara `l45`'s own truncation, continuing onto 12b. | Fixed: reworded to document the cross-daf continuation (verified against 12b vilnaLine 1, already correctly resolved); placement id unchanged (`l45` is already correct). |

No deferrals were needed in Batch 11. This closes out 12a entirely:
all 66 rashiTranslations entries are now grounded in their local
Rashi Hebrew and correctly linked to their Gemara lines.

## 12b remap (VERSION 14.79): full raw-line reconstruction, closing 12b

Resolved the index-misalignment finding documented above (VERSION
14.78). All 62 `rashiTranslations` entries were rebuilt from a full
raw-line reconstruction of `assets/talmuddev/12b.json`'s Rashi text,
joining consecutive print-lines to find genuine dibbur-hamatchil
boundaries and cross-referencing each against the actual Gemara lines
in `learning_data.js` (`yoma-012b-l01` through `l35`), rather than
reworded in place - the prior content's index drift meant per-line
wording, not just placement, needed to be regenerated to match this
daf's real raw-line boundaries.

The reconstructed sugya: `l01` (Rav Pappa's "his service inducts him"
ruling and its Temple-vessel proof, continuing from 12a), `l04`
(Rav Dimi's tradition on the common priest's belt material and a
textual note on the correct Gemara reading), `l06` (the "is this
during the year or on Yom Kippur" analysis), `l11`-`l12` (the
resolution: on Yom Kippur both wear linen, so the distinguishing
garments are those worn in common the rest of the year), `l13`
(Ravin's tradition, clarifying Rav Dimi's), `l19` (Rav Nachman bar
Yitzchak's baraita on "he shall wear," extending to the turban and
belt), `l22` (Rabbi Dosa's teaching that the Yom Kippur garments
remain valid for the common priest, and Rabbi's two rebuttals, the
first about the belt), `l26` (Rabbi's second rebuttal and the
"worn-out garments" gloss), `l29` (Rabbi Dosa's own reasoning from the
genizah baraita), `l31` (Rabbi Meir's ruling on the replacement's
status), `l33` (Rabbi Yosei's stricter ruling), and `l35` (Rabbi
Yosei's proof from Yosef ben Ilem of Tzippori, including Rashi's
extended halachic elaboration of the "rivalry" and "we elevate but do
not lower in sanctity" reasoning, continuing to vilnaLine 62). `l41`
and `l42` (Rabbah bar bar Chana's halachic ruling, truncated) have no
corresponding Rashi commentary in this daf's raw print-lines and are
correctly unreferenced.

vilnaLine 57-61 (the "rivalry"/pashita/tumah-shechicha elaboration)
do not correspond to a distinct Gemara line id of their own - they
are Rashi's extended explanation of the halachic mechanics behind
Rabbi Yosei's ruling on `l33`/`l35`, a sub-argument the learning JSON's
Gemara scaffolding does not itemize as separate citations. These were
linked to the nearest matching real anchor (`l33` for vilnaLine 57,
`l35` for vilnaLine 58-61) rather than left unlinked or given a
fabricated id, consistent with how prior batches handled comments
that elaborate on, rather than newly cite, a Gemara line.

vilnaLine 62 is the daf's final raw print-line, a single truncated
word ("kivan," since) matching the opening word of 13a's rashi[0]
raw text ("kivan d'amrei..."), confirmed by checking `assets/talmuddev/13a.json`
directly. Documented as a cross-daf continuation rather than
fabricated, matching the established pattern.

All 62 entries' `linkedGemaraLineIds` were also corrected from the
unpadded, dangling `yoma-12b-lXX` form to the real zero-padded
`yoma-012b-lXX` ids; every id now used (`l01`, `l04`, `l06`, `l11`,
`l12`, `l13`, `l19`, `l22`, `l26`, `l29`, `l31`, `l33`, `l35`) was
confirmed present in `learning_data.js` before committing.

No deferrals were needed. This closes out 12b entirely: all 62
rashiTranslations entries are now grounded in their local Rashi
Hebrew, correctly indexed to their raw print-lines, and correctly
linked to their Gemara lines.

### Self-correction (VERSION 14.80): 12b vilnaLine 57-62 relinked from `l35` to `l42`

While starting the 13a chunk immediately after the 12b remap, cross-
referencing 13a's real Gemara text (`l01`, `l04`, `l05`, `l12`)
against 12b's own raw Rashi lines 57-62 surfaced a placement error in
the remap above: vilnaLine 58-61 had been linked to `l35` (the Yosef
ben Ilem story), but their actual content - "that if he transgressed
and served, his service is valid," "the second returns to his
service," "obviously," "lest you say [he'd be] a rival-wife during
the first's lifetime" - verbatim matches Gemara text that begins with
12b's own truncated `l42` ("the halacha [is]...") and continues fully
onto 13a's `l01` and `l04`, not the Yosef ben Ilem material at all.
The two discussions both concern "eivah"/rivalry reasoning applied to
a replacement figure, which is what caused the original misreading in
Chunk 1. vilnaLine 57 and 62 were also relinked to `l42` for
consistency (57's newly-opened content is the same overflow passage;
62's cross-daf-continuation content was unaffected but is now
correctly anchored). All 6 entries (vilnaLine 57-62) now link to
`yoma-012b-l42`, the true local anchor for this passage, with English
describing the halachic ruling and its rivalry-reasoning elaboration
that continues from 12b's truncated Halacha statement into 13a rather
than claiming precise sub-clause-level certainty about which of 13a's
several nearby Gemara lines each phrase individually explains.

## 13a: dedicated alignment pass, vilnaLine 1-17 fixed, 18-29 initially deferred

A dedicated chunk revisited 13a with the actual Gemara-line sequence
read first, rather than assumed sequentially: `yoma-013a-l01` (halacha
k'Rabbi Yosei ruling), `l04` (pashita/mahu detapina/tzara machayim),
`l05` (Rabbi Yehuda's backup-wife proposal, tumah shechicha/mita lo
shechicha), `l08` (ein ladavar sof, chayishinan lechada lo letrei),
`l12` (nimru inhu lenafshaihu, zariz hu), `l15` (u'mi sagi lei
b'takanta - the two-houses problem), `l20` (hadra kushyain, al menat
shetamuti), `l23` (al menat shelo tamuti), `l25` (al menat shetamut
achat mikem), `l27` (Rava's kol yemei chayai ruling - ein zeh
keritut), `l29a`/`l29b` (kol yemei chayei peloni - harei zeh keritut;
shelo tamut chavertich), and `l32` (truncated "lemafrea," continuing
to 13b). Reading the learning_data.js sugya scaffolding directly
(rather than inferring from raw-line order alone) also clarified the
prior 12b self-correction: sugya `yoma-13a-s01` covers only `l01`-`l04`
and is entirely about the replacement Kohen Gadol resuming service
when the original dies (confirming 12b vilnaLine 57-62's correct
anchor at `l42`), while `yoma-13a-s02` (`l05`-`l12`) is the separate
backup-wife discussion, and `yoma-13a-s03` (`l15`-`l32`) is the
conditional-divorce sugya. No regression was found on 12b; its
vilnaLine 57-62 remain correctly linked to `l42` and were not
modified in this pass.

vilnaLine 1-2 continue the cross-daf bridge from 12b's vilnaLine 62
("kivan"), and verbatim-match `l08`'s "ein ladavar sof" (there is no
end to the matter). vilnaLine 3 opens on "zariz hu" (`l12`, exact
phrase match) then opens "b'takanta" (`l15`, exact phrase match, but
its own explanation is on the next line so `l12` was kept as the
dominant anchor for vilnaLine 3). vilnaLine 4 closes the "b'takanta"
gloss then opens "hadra kushyain" and "al menat shetamuti," both
verbatim matches to `l20`. vilnaLine 5-15 continue elaborating that
same `l20` formula, including a seven-line editorial aside (vilnaLine
8-14) where Rashi explicitly comments that "this entire sugya" of
proposed resolutions is pedagogical rather than a settled ruling -
Rashi's own words, not a new Gemara citation, so kept anchored to
`l20` where it appears in the print order. vilnaLine 16 closes that
formula's failure analysis and opens "al menat shelo tamuti,"
verbatim-matching `l23`; vilnaLine 17 continues it.

All 17 fixed entries' `linkedGemaraLineIds` were also corrected from
the unpadded, dangling `yoma-13a-lXX` form to the real zero-padded
`yoma-013a-lXX` ids.

| daf | vilnaLine | placement (before -> after) | issue | resolution |
|---|---|---|---|---|
| 13a | 1-2 | `l01` (dangling) -> `l08` (each) | English already described this content reasonably but with a dangling id and without recognizing it as the direct continuation of 12b's "nimru inhu lenafshaihu" bridge into `l08`'s "ein ladavar sof" reasoning. | Fixed: reworded to frame the continuation explicitly; placement corrected to `l08`. |
| 13a | 3 | `l03` (dangling) -> `l12` (each) | English conflated the "zariz hu" gloss with unrelated framing ("the Rabbanan's distinction"); actual Hebrew is a direct explanation of `l12`'s "kohen gadol zariz hu," then opens toward `l15`. | Fixed: reworded and placement corrected to `l12`. |
| 13a | 4 | `l04` (dangling) -> `l20` (each) | English fabricated "the backup wife arrangement... parallel to the backup KG arrangement" for content that is actually `l15`'s brief close, followed immediately by `l20`'s "hadra kushyain / al menat shetamuti" opening (the dominant content on this line). | Fixed: reworded and placement corrected to `l20`. |
| 13a | 5-15 | `l05`-`l11` (mixed, dangling) -> `l20` (each) | English fabricated content describing later formulas ("al menat shelo tamuti," "kol yemei chayei peloni") out of order, out of place on lines that are still working through the first ("al menat shetamuti") formula and Rashi's own editorial aside about the pedagogical nature of these resolutions. | Fixed: reworded as accurate continuations grounded in the raw Hebrew; placement corrected to `l20`. |
| 13a | 16-17 | `l08`/`l09` (dangling) -> `l23` (each) | English fabricated formula content already misplaced elsewhere; actual Hebrew closes the `l20` formula and opens `l23`'s "al menat shelo tamuti" formula. | Fixed: reworded and placement corrected to `l23`. |

vilnaLine 18-29 were left unchanged. Continuing the raw-line walk past
vilnaLine 17 found real ambiguity: vilnaLine 18's "k'hai gavna" phrase
and vilnaLine 21's "kol yemei chayei peloni" phrase both plausibly
connect to more than one later Gemara line (`l23`'s own continuation
versus `l27`'s later, explicit "ein zeh keritut" citation; and `l25`
versus `l29a`'s near-identical "kol yemei chayei peloni" wording,
which are not adjacent in the Gemara's own line order). This is
exactly the "nested conditional-divorce sequence becomes ambiguous"
stop condition - forcing a guess here risks repeating the same kind
of misattribution just corrected in 12b. Deferred to a future
dedicated pass that resolves each of `l23`, `l25`, `l27`, `l29a`,
`l29b`, and `l32` against vilnaLine 18-29 one hypothesis at a time
before writing any fix.

## 13a vilnaLine 18-29 resolved (VERSION 14.82), closing 13a entirely

A follow-up dedicated pass resolved the vilnaLine 18-29 deferral
above by cross-referencing the local English translation stored
alongside each Gemara line in `learning_data.js` (not just the Hebrew)
against the raw Rashi print-lines, which supplied the missing
disambiguating signal. Two findings resolved the prior ambiguity.

First, vilnaLine 18's "k'hai gavna" ("in such a case") phrase is a
near-verbatim match for `l27`'s own rhetorical question ("כי האי
גוונא מי הוי גיטא" / "is a document of that sort a valid bill of
divorce?"), confirmed by the local English's near-identical wording
("Is a document of that sort a valid bill of divorce?"). Rashi asks
this question as his own bridging comment right after closing out
`l23`'s formula, before the Gemara's own text formally reaches `l27`
with Rava's citation - so vilnaLine 18 closes `l23` and opens `l27`,
not `l23` alone as first suspected.

Second, `l25`'s formula ("on condition that one of you dies") turns
out not to have its own dedicated Rashi comment in this run of raw
print-lines at all - the raw Hebrew moves directly from explaining
`l27`'s meta-question to `l29a`'s "kol yemei chayei peloni" resolution
(an exact phrase match), meaning there was no real "l25 vs l29a"
choice to make. Rashi sometimes does not comment on every Gemara
clause; `l25` is one of the lines skipped here.

With those two points settled, the remainder followed cleanly:
vilnaLine 19-20 continue explaining `l27`'s "ein zeh keritut" (not a
severance) conclusion; vilnaLine 21-25 explain `l29a`'s resolution
(a condition tied to a third party's life is a valid severance, unlike
one tied to the couple's own); vilnaLine 26-28 open and explain
`l29b`'s new formula ("on condition your counterpart does not die,"
an exact phrase match); and vilnaLine 29, a single truncated word
("im," if), is the start of a comment continuing onto 13b - confirmed
by checking `assets/talmuddev/13b.json` directly, whose rashi[0] opens
"אם מתה חבירתה" (if her counterpart dies), matching the established
cross-daf continuation pattern used throughout this hotspot.

All 12 entries' `linkedGemaraLineIds` were also corrected from the
unpadded, dangling `yoma-13a-lXX` form to the real zero-padded
`yoma-013a-lXX` ids (`l27`, `l29a`, `l29b`).

| daf | vilnaLine | placement (before -> after) | issue | resolution |
|---|---|---|---|---|
| 13a | 18-20 | `l08`/`l09` (dangling) -> `l27` (each) | English fabricated "was it a get" reasoning attached to the wrong formula; actual Hebrew closes `l23`'s formula, then opens and explains `l27`'s meta-question and its "ein zeh keritut" conclusion. | Fixed: reworded as accurate continuations; placement corrected to `l27`. |
| 13a | 21-25 | `l10`-`l12` (dangling) -> `l29a` (each) | English fabricated "v'lo ayla hi l'veit hakenesset" content that does not correspond to any of these lines' actual Hebrew; actual Hebrew opens and elaborates `l29a`'s "kol yemei chayei peloni" resolution (a condition tied to a third party's life is a valid severance). | Fixed: reworded as accurate continuations; placement corrected to `l29a`. |
| 13a | 26-28 | `l10`/`l12`/`l13` (dangling) -> `l29b` (each) | English fabricated "the inherent trap" / "staggered conditions" summary content not grounded in these lines; actual Hebrew opens and explains `l29b`'s new formula ("on condition your counterpart does not die"). | Fixed: reworded as accurate continuations; placement corrected to `l29b`. |
| 13a | 29 | `l13` (dangling) -> `l29b` (valid) | English fabricated "staggered conditions still fail" summary content; actual Hebrew is a single truncated word ("im," if) matching the opening of 13b's own raw Rashi text ("if her counterpart dies"). | Fixed: reworded to document the cross-daf continuation (verified against 13b's raw talmud.dev text); placement corrected to `l29b`. |

No deferrals remain. This closes out 13a entirely: all 29
rashiTranslations entries are now grounded in their local Rashi
Hebrew, correctly indexed to their raw print-lines, and correctly
linked to their Gemara lines.

## 13b resolved (VERSION 14.83), closing 13b entirely

Checked 13b next, following 13a. Confirmed the 13a/13b boundary first:
13a vilnaLine 29 (a single truncated word, "if") links correctly to
`yoma-013a-l29b`, and 13b's own raw talmud.dev text opens "אם מתה
חבירתה" ("if her counterpart dies"), the direct continuation - no
regression, no change needed on 13a.

13b showed the same index-misalignment pattern as 12b and 13a (real,
on-topic Rashi translation assigned to the wrong vilnaLine), plus the
same unpadded `yoma-13b-lXX` id bug. Reading the sugya scaffolding
first (`yoma-13b-s01`: `l01`-`l11`, the conditional-divorce sugya's
tail carried over from 13a; `yoma-13b-s02`: `l20`-`l22`, two
levirate-marriage objections to the "one house" premise; `yoma-13b-s03`:
`l24`-`l29`, the onen High Priest sugya) supplied the disambiguating
structure needed to walk all 28 raw print-lines with confidence.

vilnaLine 1 closes 13a's carried-over formula (`l01`) then opens a
brief gloss on `l05`'s "on condition you do not enter the synagogue"
stipulation, clarifying it applies specifically on Yom Kippur (a
detail the Gemara's own text leaves implicit). vilnaLine 2 closes that
gloss, then opens Rashi's own transitional recap ("since we said above
that 'his house' does not imply two") bridging directly into `l20`'s
formal objection - confirmed by the near-identical "אלא מעתה" phrasing
and by vilnaLine 3-4's content ("two yevamot coming from one man")
matching `l20`'s objection almost verbatim, just with "one man" in
place of the Gemara's "one house." vilnaLine 4-6 open and explain
`l22`'s parallel objection about a betrothed woman, an exact phrase
match ("ארוסה לא תתייבם"). Notably, `l05`'s "divorce both wives with
complementary conditions" formula and `l11`'s further exploration are
not otherwise commented on in this run of raw print-lines - like `l25`
on 13a, Rashi does not comment on every Gemara clause.

vilnaLine 7-21 are one continuous stretch explaining `l24`, the onen
baraita and Rava's "kol hayom" gloss: the verse source permitting the
Kohen Gadol to serve despite being an onen (Leviticus 21, expounded via
Zevachim 16a), the contrasting rule for a common priest, the
prohibition on eating consecrated food (an a fortiori inference from
the lenient ma'aser law, Deuteronomy 26), and Rava's explanation that
"the whole day" means a mitzva to actively bring him from home to
serve. vilnaLine 22-27 open and explain `l25`, Abaye's challenge to
Rava (an exact phrase match, "השתא לרבי") and its cited baraita.
vilnaLine 28, the daf's final raw print-line, is a single word
("lomar," to say) that verbatim matches Gemara `l29`'s own truncated
text, confirming the established cross-daf continuation pattern
without needing to read into 14a (out of this pass's scope).

All 28 entries' `linkedGemaraLineIds` were also corrected from the
unpadded, dangling `yoma-13b-lXX` form to the real zero-padded
`yoma-013b-lXX` ids (`l01`, `l05`, `l20`, `l22`, `l24`, `l25`, `l29`).

| daf | vilnaLine | placement (before -> after) | issue | resolution |
|---|---|---|---|---|
| 13a | 29 | `l29b` (unchanged) | Boundary check only: confirmed correct, no regression found. | No change. |
| 13b | 1-2 | `l01` (dangling) -> `l05`/`l20` | English fabricated "retroactively" reasoning attached to the wrong clause; actual Hebrew closes the 13a-carried formula, glosses `l05`'s synagogue-entry timing, then opens the transitional bridge into `l20`'s objection. | Fixed: reworded as accurate continuations; placement corrected to `l05` then `l20`. |
| 13b | 3-6 | `l01`/`l02` (dangling) -> `l20`/`l22` | English fabricated content describing formulas from elsewhere in the sugya, out of place; actual Hebrew states and explains the two levirate-marriage objections almost verbatim. | Fixed: reworded as accurate continuations; placement corrected to `l20` then `l22`. |
| 13b | 7-21 | `l06`-`l09` (dangling, mixed order) -> `l24` (each) | English fabricated or repeated content across multiple non-adjacent entries (vilnaLine 17-19 duplicated vilnaLine 9-11's topic out of order); actual Hebrew is a single continuous explanation of the onen baraita and Rava's "kol hayom" gloss. | Fixed: reworded as accurate continuations grounded in the raw Hebrew; placement corrected to `l24`. |
| 13b | 22-27 | `l08`/`l09` (dangling) -> `l25` (each) | English fabricated "final note on the section" summary content; actual Hebrew opens and explains Abaye's challenge to Rava and its cited baraita. | Fixed: reworded as accurate continuations; placement corrected to `l25`. |
| 13b | 28 | `l09` (dangling) -> `l29` (valid) | English fabricated content describing Abaye's challenge already covered elsewhere; actual Hebrew is a single word matching Gemara `l29`'s own truncated text. | Fixed: reworded to document the cross-daf continuation; placement corrected to `l29`. |

No deferrals were needed. This closes out 13b entirely: all 28
rashiTranslations entries are now grounded in their local Rashi
Hebrew, correctly indexed to their raw print-lines, and correctly
linked to their Gemara lines.

## 14a, vilnaLine 1-29 (VERSION 14.84), first half of a two-part daf

14a has 58 raw Rashi print-lines, above the 40-entry single-chunk
threshold, so it is split into two sub-chunks: vilnaLine 1-29 here,
vilnaLine 30-58 in a follow-up chunk. Verified the 13b/14a boundary
first: 13b vilnaLine 28 links correctly to `l29`, and 14a's own raw
talmud.dev text opens "לומר שאינו עובד כל היום" ("to say that he
does not serve the whole day"), the direct continuation of 13b's
truncated "לומר" - no regression, no change needed on 13b.

14a showed the same index-misalignment pattern as 12b, 13a, and 13b:
real, on-topic Rashi translation assigned to sequential-looking but
wrong ids (`yoma-14a-l01` through `l12`) that do not match the real,
vilna-line-numbered ids in `learning_data.js` (`l01`, `l10`, `l12`,
`l17`, ...). Reading the sugya scaffolding first (`yoma-14a-s01`:
`l01`-`l10`, closing the onen/backup-wife discussion carried from
13b; `yoma-14a-s02`: `l12`, the mishna on the High Priest's
sequestering-week and year-round sacrificial prerogatives;
`yoma-14a-s03`: `l17`-`l47`, the Gemara on that mishna, opening with
the red-heifer sprinkling dispute) supplied the structure.

vilnaLine 1-6 continue and close `l01` (Rav Adda bar Ahava's challenge
to Rava about the "decree lest he eat," and Rava's resolution
distinguishing Yom Kippur from the rest of the year). vilnaLine 7-13
open and close `l10` (the "but she is divorced" question about
whether mourning-status even applies, and the "is he not troubled"
answer, plus the requirement of joy for sacred service). vilnaLine
14-28 are one continuous stretch on the mishna itself (`l12`): the
daily blood-tossing and incense, tending the lamps each morning, the
year-round privilege to sacrifice any portion he chooses first.
vilnaLine 29 closes the mishna commentary and opens the transition
into the Gemara section (`l17`), matching Rav Chisda's "not according
to Rabbi Akiva" framing.

All 29 fixed entries' `linkedGemaraLineIds` were also corrected from
the unpadded, sequential-but-wrong `yoma-14a-lXX` form to the real
zero-padded `yoma-014a-lXX` ids matching the actual vilna-line
numbering (`l01`, `l10`, `l12`, `l17`).

No deferrals were needed in this sub-chunk. vilnaLine 30-58 (the bulk
of the red-heifer sprinkling dispute between Rabbi Akiva and the
Sages) remain for a follow-up chunk.

## 14a, vilnaLine 30-58 (VERSION 14.85), second half, closing 14a entirely

Completed 14a with vilnaLine 30-58, continuing the red-heifer
sprinkling dispute from where vilnaLine 29 opened at `l17`. Building
on the same sugya scaffolding (`yoma-14a-s03`: `l17`-`l47`), this
range covers `l17` (Rav Chisda's "not Rabbi Akiva" ruling), `l20`
(Rabbi Akiva vs. the Sages on sprinkling the pure/impure), `l24` (the
mishna on reusing hyssop residue), `l33` (the Rabbis' answer to
Solomon's bewilderment - who is rendered pure or impure by the
sprinkling), and `l41` (whether sprinkling requires a minimum measure,
resolved differently for the body versus a vessel). Two Gemara lines
in this range, `l28` and `l36`/`l39`, are not separately commented on
by Rashi in this run of raw print-lines - the same "not every clause
gets its own DH" pattern already documented on 13a (`l25`) and 13b
(`l05`/`l11`).

vilnaLine 58, the daf's final raw print-line, is a single word ("so
that he may dip") that does not simply close out the preceding "aval
b'mana" comment - checking 14b's raw talmud.dev text directly confirms
it is a new, truncated comment continuing onto 14b, whose rashi[0]
opens "שיטביל ראשי גבעולין ויזה" ("so that he may dip the tops of the
stalks and sprinkle"), matching the established cross-daf continuation
pattern. It was linked to `l47`, the Gemara's own truncated
continuation of `l41`'s ending, rather than back to `l41` itself.

All 29 fixed entries' `linkedGemaraLineIds` were also corrected from
the unpadded, sequential-but-wrong `yoma-14a-lXX` form to the real
zero-padded `yoma-014a-lXX` ids (`l17`, `l20`, `l24`, `l33`, `l41`,
`l47`).

No deferrals were needed. This closes out 14a entirely: all 58
rashiTranslations entries are now grounded in their local Rashi
Hebrew, correctly indexed to their raw print-lines, and correctly
linked to their Gemara lines.

## 14b, vilnaLine 1-30 (VERSION 14.86), first half of a two-part daf

14b has 59 raw Rashi print-lines, above the 40-entry single-chunk
threshold, so it is split into two sub-chunks: vilnaLine 1-30 here,
vilnaLine 31-59 in a follow-up chunk. Verified the 14a/14b boundary
first: 14a vilnaLine 58 links correctly to `l47`, and 14b's own raw
talmud.dev text opens "שיטביל ראשי גבעולין ויזה" ("so that he dips the
tops of the stems and sprinkles"), the direct continuation of 14a's
truncated "שיטביל" - no regression, no change needed on 14a.

14b showed the same index-misalignment pattern as the prior daf-boundary
daf (sequential-but-wrong ids `yoma-14b-l01` through `l10` that do not
match the real, vilna-line-numbered ids in `learning_data.js`). Reading
the sugya scaffolding first (`yoma-14b-s01`: `l01` only, closing the
red-heifer sprinkling dispute carried from 14a; `yoma-14b-s02`:
`l03`-`l14`, the mishna's service-order and its apparent contradiction
with tractate Tamid; `yoma-14b-s03`: `l16`-`l31`, continuing into the
lottery/pais and lamp-tending-versus-incense dispute) supplied the
structure.

vilnaLine 1 closes `l01` (Abaye's resolution of the sprinkling
dispute). vilnaLine 2-7 open and explain `l03` (the mishna's service
order and the contradiction raised from tractate Tamid's own mishna).
vilnaLine 8-25 open and explain `l07` (Rav Huna's attribution to Rabbi
Shimon Ish HaMitzpa, the objection from Tamid's blood-sprinkling
mishna, and the geometry of the four sprinklings on two altar
corners). vilnaLine 26-30 open `l11` (the baraita distinguishing Rabbi
Shimon Ish HaMitzpa's practice from the ordinary burnt offering's
sprinkling order).

All 30 fixed entries' `linkedGemaraLineIds` were also corrected from
the sequential-but-wrong `yoma-14b-lXX` form to the real zero-padded
`yoma-014b-lXX` ids matching the actual vilna-line numbering (`l01`,
`l03`, `l07`, `l11`).

No deferrals were needed in this sub-chunk. vilnaLine 31-59 (the
remainder of the lottery/pais discussion and the lamp-tending-versus-
incense dispute between the Rabbis and Abba Shaul) remain for a
follow-up chunk.

## 14b, vilnaLine 31-58 (VERSION 14.87), second half, closing 14b except one deferral

Continued directly from the first sub-chunk's stopping point. Read the
real Gemara lines for the remainder of the daf directly out of
`learning_data.js` (`yoma-014b-l11` through `yoma-014b-l31`, full
Hebrew and English) before touching any raw Rashi text, then walked
`assets/talmuddev/14b.json`'s raw print-lines 31-59 (1:1 with
`rashiTranslations` vilnaLine 31-59) to find dibbur-hamatchil
boundaries.

vilnaLine 31-35 continue `l11`'s baraita on Rabbi Shimon Ish
HaMitzpa's altered sprinkling order (the westward-then-southward
approach and the paused double sprinkling), closing out the same
Gemara line the first sub-chunk had already opened at vilnaLine 26.
vilnaLine 36-40 open and close `l14` (Rabbi Yochanan's resolution:
Rabbi Shimon Ish HaMitzpa authored the Yoma service order, not just
the Tamid dispute). vilnaLine 41-50 open and close `l16` (the second
lottery's thirteen service assignments, why priests disperse and
reconvene for the third lottery, and the "new" versus "veteran"
priests distinction for the incense lottery). vilnaLine 51-53 open
`l20` (Abaye's two-lamps-versus-five-lamps resolution). vilnaLine
54-58 open and close `l22` (the interposition dispute: whether
incense or the daily offering's blood-sprinkling separates the two
lamp-cleaning sessions, the Abba Shaul/Rabbanan baraita, and Abba
Shaul's own statement).

Where a single raw print-line concluded one dibbur-hamatchil and
opened a new one in the same line (for example vilnaLine 36, 41, 51,
and 54), the whole entry was linked to the newly-opened line rather
than the one being concluded, consistent with the precedent set at
vilnaLine 8 in the first sub-chunk. All 28 fixed entries'
`linkedGemaraLineIds` were corrected from the sequential-but-wrong
`yoma-14b-lXX` form (the old entries pointed at only four distinct
wrong buckets, `l07` through `l10`, for all 29 remaining entries) to
the real zero-padded ids (`l11`, `l14`, `l16`, `l20`, `l22`).

One deferral: vilnaLine 59, the daf's final raw print-line, is a
single truncated word, "מערב" (west, or possibly the start of a
longer word). The corresponding Gemara line `yoma-014b-l31` is itself
truncated ("בְּעֵידָן", "at the time of", with an empty `en:`),
confirming this is a cross-daf continuation, but the raw word on 14b
does not obviously match a continuation of "בְּעֵידָן" from local
text alone, so it needs 15a's opening raw Rashi text to confirm
before it can be fixed with confidence. Left unchanged, both `en` and
`linkedGemaraLineIds`, pending that boundary check in the 15a chunk.

14b is now 58/59 resolved; only vilnaLine 59 remains open.

## 15a, vilnaLine 1-33 (VERSION 14.88), first half of a two-part daf, closing 14b

Verified the 14b/15a boundary first: 15a's raw talmud.dev Rashi text
opens "מערב עד בקר. בנרות כתיב יערוך אותו אהרן ובניו מערב עד", the
direct completion of 14b's truncated final word "מערב". That resolves
the one deferral from the prior chunk: 14b vilnaLine 59 is the
truncated start of the dibbur hamatchil "from evening until morning"
and is now linked to `yoma-014b-l31` ("בְּעֵידָן", 14b's own truncated
final Gemara line), consistent with how every prior daf-boundary
truncation was handled (14a vilnaLine 58 to l47, and so on). 14b is
now fully resolved, 59/59.

15a has 66 raw Rashi print-lines, above the 40-entry single-chunk
threshold, so it is split into two sub-chunks: vilnaLine 1-33 here,
vilnaLine 34-66 in a follow-up chunk. 15a showed the usual
index-misalignment pattern: unpadded `yoma-15a-lXX` ids and content
drifting one or more Gemara lines off (for example vilnaLine 2-5 were
linked to `l01` but belong to `l06`, vilnaLine 21-29 were spread
across `l21`/`l25`/`l27` but all belong to `l16`).

Read the sugya scaffolding first (`yoma-15a-s01`: `l01`-`l12`, the
morning/evening incense-and-lamps derivation and Abba Shaul's "oto"
answer; `yoma-15a-s02`: `l13`-`l25`, Rav Pappa's alternative
resolution and Abaye's counter; `yoma-15a-s03`: `l27`-`l47`, the
sprinkling geometry discussion), then walked the raw print-lines.

vilnaLine 1 completes the boundary DH and explains `l01` (the baraita
"from evening until morning" quoted at the end of that line).
vilnaLine 2-6 open and explain `l06` (the oil measure, half a log per
lamp, and "you have no service valid from evening to morning").
vilnaLine 7-11 open `l12` (Abba Shaul's answer "as it is written:
oto"). vilnaLine 12-18 open `l13` (Rav Pappa's resolution, including
the sub-DHs "the mishna here" and "the lottery"). vilnaLine 19-33
open `l16` (the "say the latter clause" challenge, including the
sub-DHs "he cut it", "to clean the lamps", and "the first and last
clauses"; the last of these carries Rashi's "in wonder" gloss, which
matches the exclamatory challenge form in `l16` rather than the
"granted" concession in `l21` where the same phrase recurs).

All 33 fixed entries' `linkedGemaraLineIds` were corrected to the
real zero-padded `yoma-015a-lXX` ids (`l01`, `l06`, `l12`, `l13`,
`l16`). No deferrals in this sub-chunk. vilnaLine 34-66 (Abaye's
reply, the sin-offering/burnt-offering sprinkling derivation, the
matzlif discussion, and the truncated final word "אגופיה" continuing
onto 15b) remain for the follow-up chunk.

## 15a, vilnaLine 34-66 (VERSION 14.89), second half, closing 15a entirely

Continued directly from the first sub-chunk. vilnaLine 34-36 open
`l21` (the "it was taught first, in wonder" challenge to Rav Pappa).
vilnaLine 37-45 open and close `l25` (Abaye's reply: the first
chapter's mishna is general instruction, not a sequence, teaching
that the High Priest stays engaged in the service all seven days).
vilnaLine 46-53 open `l33` (the derivation from Numbers 28:15 that
the daily burnt offering carries sin-offering placement procedure
alongside its own). vilnaLine 53 also opens `l36` ("four that are
four", on the four corners). vilnaLine 54-56 open `l39` ("we have
not found blood that atones and atones again"). vilnaLine 57-60 open
`l41` (the "separation of placements" answer and the challenge to
put one placement below and two above the scarlet line). vilnaLine
61 opens `l42` (the sprinkling one-above-seven-below mishna cited
from 53b). vilnaLine 62-63 open `l44a` (the matzlif answer and Rav
Yehuda's "like a lasher" demonstration, including Rashi's admission
that the word matzlif is unknown to him). vilnaLine 64-65 open
`l44b` (the "tohoro of the altar" mishna, "apalgeih", and "tihara"
meaning noon). vilnaLine 66 is the daf's final truncated word
"אגופיה", the start of the dibbur hamatchil continuing on 15b,
linked to `l47` ("אַגּוּפֵיהּ", 15a's own truncated final Gemara
line), consistent with all prior boundary handling; 15b's raw text
was already confirmed to open "אגופיה דמזבח" by the 15a boundary
reconnaissance.

All 33 fixed entries' ids were corrected to the real zero-padded
`yoma-015a-lXX` form (`l21`, `l25`, `l33`, `l36`, `l39`, `l41`,
`l42`, `l44a`, `l44b`, `l47`); this daf's real id scheme includes
the split pair `l44a`/`l44b` for vilna line 44, which the old
unpadded ids collapsed into a single wrong `l44`. No deferrals. 15a
is fully resolved, 66/66.

## 15b, vilnaLine 1-33 (VERSION 14.90), first half of a two-part daf

Verified the 15a/15b boundary first: 15b's raw talmud.dev Rashi text
opens "אגופיה דמזבח. על גגו ומאי לשון טהרו", restating and completing
15a's truncated final word "אגופיה" - no regression, no change needed
on 15a.

15b has 66 raw Rashi print-lines, split into two sub-chunks:
vilnaLine 1-33 here, vilnaLine 34-66 in a follow-up chunk. 15b has
only 8 real Gemara lines (`yoma-015b-l01` through `l30`), and its
stale entries showed both the unpadded-id pattern and genuine
content drift (for example vilnaLine 3-5 were linked to `l02`,
which has no yesod text, while the Rashi there quotes `l05`'s
"עולה טעונה יסוד" verbatim).

vilnaLine 1-2 open `l01` (tohoro means the altar's roof, cleared of
that morning's incense ash, per "like the very sky for purity").
vilnaLine 3-19 open `l05` (the burnt offering requires a base; the
southeast corner had no base, with the Middot 3:1 geometry of the
base running along the north and west sides only and the Zevachim
53b explanation that the missing sides were not in Benjamin's
portion). vilnaLine 20-33 open `l09` (the "since the Master said"
citation from Rami bar Yechezkel's baraita at 58b, why "toward the
east" is borrowed wording from Zevachim's ramp discussion, and the
opening of "he encounters that one first").

All 33 fixed entries' ids were corrected to the real zero-padded
`yoma-015b-lXX` form (`l01`, `l05`, `l09`). No deferrals in this
sub-chunk. vilnaLine 34-66 (the rest of the right-turn circuit
discussion, the sin-offering/burnt-offering derivation, the Chamber
of the Lambs and Hall of the Hearth topography, and the truncated
final word "ששיקצום" continuing onto 16a) remain for the follow-up
chunk; the stale entries there include vilnaLine 51-66 with empty
`linkedGemaraLineIds` and placeholder text, a worse baseline than
usual.

## 15b, vilnaLine 34-66 (VERSION 14.91), second half, closing 15b entirely

Continued directly from the first sub-chunk. vilnaLine 34-44
continue `l09` (the "he encounters that one first" explanation: the
right-turn circuit up the ramp, why the southeast corner is skipped
for lack of a base, and why even blood placed from the pavement
follows the same circuit direction as the sin offering placed at
the corner's top). vilnaLine 45-46 open `l14` (the "perhaps for the
sin offering of the New Moon" objection and the "it cannot enter
your mind, as it is written" answer). vilnaLine 47-63 open `l19`
(the "we learned there" mishna from Tamid: why it is placed in Yoma
at all, given that the attribution pattern to Rabbi Shimon Ish
HaMitzpa is unusual; then the sub-DHs on the appointee/deputy, the
Chamber of the Lambs and its inspected lambs per Arachin 13a, the
northwest corner of the Hall of the Hearth with its fires for the
barefoot priests, the Chamber of the Seals with the four seals of
Shekalim 7b, the small Beit HaMoked chamber, and the shewbread
chamber of the house of Garmu). vilnaLine 64-65 open `l26` (the
contradiction from Middot: the four chambers opening into the Hall
of the Hearth, two in sacred ground and two not, with the pispasin
ends marking the division). vilnaLine 66 is the daf's final
truncated word "ששיקצום", linked to `l30` ("דְּרוֹמִית", 15b's own
truncated final Gemara line); 16a's raw text was confirmed to open
"ששיקצום מלכי עובדי כוכבים", the standard boundary pattern.

This sub-chunk also repaired a worse-than-usual baseline: vilnaLine
51-66 previously had EMPTY `linkedGemaraLineIds` arrays and generic
placeholder English. All 33 fixed entries now carry real zero-padded
`yoma-015b-lXX` ids (`l09`, `l14`, `l19`, `l26`, `l30`). No
deferrals. 15b is fully resolved, 66/66.

## 16a, vilnaLine 1-31 (VERSION 14.92), first half of a two-part daf

Verified the 15b/16a boundary first: 16a's raw talmud.dev Rashi text
opens "ששיקצום מלכי עובדי כוכבים. שהקטירו עליה לעבודת כוכבים",
restating and completing 15b's truncated final word "ששיקצום" - no
regression, no change needed on 15b.

16a has 61 raw Rashi print-lines, split into two sub-chunks:
vilnaLine 1-31 here, vilnaLine 32-61 in a follow-up chunk. The real
Gemara line ids for this daf were read directly from
`learning_data.js` (`yoma-016a-l01` through `l35`), and each mapping
below was grounded in the actual Hebrew of both the raw Rashi lines
and the Gemara lines.

vilnaLine 1-3 open `l01` (the Hasmoneans hiding the altar stones the
idolatrous kings defiled, Rav Huna's "who is the tanna of Middot",
and the answer "it is Rabbi Eliezer ben Yaakov"). vilnaLine 4-7 open
`l06` (the Women's Courtyard dimensions and the nazirites' "send it
under the pot" per Numbers 6). vilnaLine 8-13 open `l16` (the
Chamber of the Lepers, their eighth-day immersion for the thumb
placements, and Rabbi Eliezer ben Yaakov's "I forgot" with its
inference that the earlier clause is also his). vilnaLine 14-31 open
`l20` (the "so too it stands to reason" argument: all the walls were
high except the eastern wall, so the priest burning the red heifer
on the Mount of Olives could sight the Sanctuary entrance over it).

All 31 fixed entries carry real zero-padded `yoma-016a-lXX` ids
(`l01`, `l06`, `l16`, `l20`). No deferrals in this sub-chunk.
vilnaLine 32-61 (the sight-line geometry with the rising Temple
Mount elevations, the step-by-step cubit accounting, Rabbi Eliezer
ben Yaakov's extra step, Rav Adda bar Ahava's alternative attribution
to Rabbi Yehuda, and the truncated final word "עשר" continuing onto
16b) remain for the follow-up chunk. The stale entries in that range
include vilnaLine 42-61 with empty `linkedGemaraLineIds` and stub
text, and vilnaLine 29-38 whose English described golden-vine
material from Middot 3:8 that appears nowhere on this daf.

Note: this chunk was applied twice. The first application passed the
full validator suite but was lost, uncommitted, when the session's
container was recycled; the work was re-applied identically from the
retained fix content and re-validated before commit. No pushed
history was affected.

## 16a, vilnaLine 32-61 (VERSION 14.93), second half, closing 16a entirely

Continued directly from the first sub-chunk. vilnaLine 32-45
continue `l20` (the long "and directs his gaze and sees" comment:
the Numbers 19 sprinkling verse, the aligned gates from the Temple
Mount gate through to the Sanctuary entrance, and why the rising
Mount would hide the entrance if the eastern wall were tall, since
the Sanctuary floor sits twenty cubits above the Mount's foot).
vilnaLine 46-51 open `l23` (the chained "and we learned" citations:
gateways twenty cubits high, the soreg lattice - Rashi describes its
diagonal wooden slats and gives the Old French name prodni - the
ten-cubit chel, its twelve half-cubit steps, and the tread depth).
vilnaLine 52-53 open `l26` (the fifteen steps to the Israelite
Courtyard and the twelve steps between the Hall and the altar,
totaling nineteen and a half cubits, leaving half a cubit of
sight-line). vilnaLine 54 opens `l29` (Rabbi Eliezer ben Yaakov's
extra cubit-high step with the Levites' platform). vilnaLine 55-56
open `l30` (the "granted, if you say" argument: with his extra step
the entrance is concealed). vilnaLine 57 opens `l31` (but per the
Rabbis half a cubit remains visible). vilnaLine 58-60 open `l32`
(Rav Adda bar Ahava's alternative: the mishna is Rabbi Yehuda, whose
centered altar - nine cubits atop the thirteen and a half already
climbed - blocks the view at twenty-two and a half cubits).
vilnaLine 61 is the daf's final truncated word "עשר", linked to
`l35` ("עֶשֶׂר", 16a's own truncated final Gemara line); 16b's raw
text was confirmed to open "עשר אמות כנגד פתחו של היכל", the
standard boundary pattern.

This sub-chunk also repaired vilnaLine 42-61, which previously had
EMPTY `linkedGemaraLineIds` and stub text, and replaced English on
vilnaLine 32-38 that had drifted into golden-vine material from
Middot 3:8 appearing nowhere on this daf. All 30 fixed entries carry
real zero-padded `yoma-016a-lXX` ids (`l20`, `l23`, `l26`, `l29`,
`l30`, `l31`, `l32`, `l35`). No deferrals. 16a is fully resolved,
61/61.

## 16b, vilnaLine 1-31 (VERSION 14.94), first half of a two-part daf

Verified the 16a/16b boundary first: 16b's raw talmud.dev Rashi text
opens "עשר אמות כנגד פתחו של היכל. י' אמצעית של רחבו", restating and
completing 16a's truncated final word "עשר" - no regression, no
change needed on 16a.

16b has 62 raw Rashi print-lines, split into two sub-chunks:
vilnaLine 1-31 here, vilnaLine 32-62 in a follow-up chunk. 16b has
only 5 real Gemara lines (`yoma-016b-l01`, `l03`, `l12`, `l18`, and
the truncated `l21`). Every mapping below was grounded in the actual
Hebrew of both the raw Rashi lines and the Gemara lines, including
confirming that `l03`'s east-west measurement list ends with "ואחת
עשרה אמה אחורי בית הכפורת", which anchors the "eleven cubits" DH.

vilnaLine 1-4 open `l01` (the altar aligned opposite the Sanctuary:
ten middle cubits against the entrance, eleven to the north and
south against the remaining interior plus the six-cubit walls).
vilnaLine 5-21 open `l03` (the objection to Rav Adda: per the
unattributed Middot the courtyard is 187 by 135, with the whole
east-west breakdown - Porch, Sanctuary, traksin, Holy of Holies,
walls - spelled out in Middot and cited at 52b, ending with the
eleven open cubits behind the Ark-cover). vilnaLine 22-31 open `l12`
(the south-to-north list: ramp and altar, the space between ramp and
southern wall deferred to the latter clause, the rings north of the
altar for slaughtering most-holy offerings, the rinsing tables, and
the nenasin posts).

All 31 fixed entries carry real zero-padded `yoma-016b-lXX` ids
(`l01`, `l03`, `l12`). No deferrals in this sub-chunk. vilnaLine
32-62 (the rest of the south-to-north accounting, the "most of the
altar stands in the south" calculation with Rashi's own extended
reckoning - including his citation of his teacher Rabbeinu Yitzchak
bar Yehuda and his twice-stated reservation "my heart hesitates" -
and the truncated final word "אלא" continuing onto 17a) remain for
the follow-up chunk.

## 16b, vilnaLine 32-62 (VERSION 14.95), second half, closing 16b entirely

Continued directly from the first sub-chunk. An independent
reconnaissance pass verified the DH segmentation for this daf
against Sefaria's Rashi on Yoma 16b (exactly 11 segments, matching
the raw print-line boundaries word for word), giving a second source
of confirmation for the whole mapping. vilnaLine 32-34 open `l12`
(the "and the remainder" clause: the uncounted surplus of the 135,
with the tables' width known from Ezekiel 40, split half to the
south and half to the nenasin area). vilnaLine 35-61 open `l18`
(the single long "most of the altar stands in the south" comment:
the cubit-by-cubit reckoning from the northern wall, the eight
tables of Shekalim 9b, the conclusion that the entrance's north edge
is exposed by two cubits, the objection from the altar's own height
answered by the 13.5 plus 6 count, and then Rashi's extended personal
discussion - his first "my heart hesitates", the alternative
reckoning in which nothing of the entrance is exposed, the
explanation he heard from his teacher Rabbeinu Yitzchak bar Yehuda
splitting the twenty-five as twelve and thirteen, his second
hesitation, and his preference for his first explanation). vilnaLine
62 is the daf's final truncated word "אלא", linked to `l21`
("אֶלָּא", 16b's own truncated final Gemara line); 17a's raw text
was confirmed to open "אלא לאו שמע מינה ראב"י היא", the standard
boundary pattern.

This sub-chunk also repaired vilnaLine 32-62's baseline, of which 31
entries previously had EMPTY `linkedGemaraLineIds` and stub text
(the daf's empty-id total was 37, of which 6 fell in the first
sub-chunk's range). All 31 fixed entries carry real zero-padded
`yoma-016b-lXX` ids (`l12`, `l18`, `l21`). No deferrals. 16b is
fully resolved, 62/62.

## 17a, vilnaLine 1-23 (VERSION 14.96), first half of a two-part daf

Verified the 16b/17a boundary first: 17a's raw talmud.dev Rashi text
opens "אלא לאו שמע מינה ראב"י היא. ואיכסי ליה במעלה יתירה", restating
and completing 16b's truncated final word "אלא" - no regression, no
change needed on 16b.

17a has 45 raw Rashi print-lines, split into two sub-chunks:
vilnaLine 1-23 here, vilnaLine 24-45 in a follow-up chunk. 17a has
only 5 real Gemara lines (`yoma-017a-l01`, `l02`, `l05`, `l07`, and
the truncated `l09`). An independent reconnaissance pass verified
the DH segmentation against Sefaria's Rashi on Yoma 17a (exactly 7
segments matching the raw print-line boundaries verbatim).

The entire first sub-chunk sits inside a single enormous dibbur
hamatchil: vilnaLine 1-23 all belong to `l01` ("rather, conclude
from this that it is Rabbi Eliezer ben Yaakov"), in which Rashi
explains that the entrance is concealed by the extra step rather
than the altar (citing Rabbi Eliezer ben Yaakov's position at 37a
that the whole altar stands in the south), answers how the
unattributed Middot fits him by reworking the twenty-five-cubit
allocation (five and a half between ramp and wall), rebuts a
possible Rabbi Yehuda reading with the twenty-one-and-a-half
arithmetic that would leave only three and a half cubits for tables
and nenasin, and then begins his own preferred rereading of Rav
Adda bar Ahava's statement as aimed at the Tamid mishna.

All 23 fixed entries carry the real zero-padded id `yoma-017a-l01`.
Before this fix, vilnaLine 5-20 pointed at wrong lines (l05, l07,
l09) with English describing material from the daf's later DHs and
even from 17b, and vilnaLine 21-23 had empty ids. No deferrals in
this sub-chunk. vilnaLine 24-45 (the close of the big DH including
Rashi's textual note "we do not read: rather, conclude that it is
Rabbi Eliezer ben Yaakov", the set-off Chamber of the Lambs and the
viewing-angle DHs, the shewbread contradiction, Rav Huna son of Rav
Yehoshua's right/left-circuit resolution, and the truncated final
word "אי" continuing onto 17b) remain for the follow-up chunk.

## 17a, vilnaLine 24-45 (VERSION 14.97), second half, closing 17a entirely

Continued directly from the first sub-chunk. vilnaLine 24-26
conclude the giant `l01` DH (the baraita of Rabbi Yehuda's centered
altar, the "where do you find it" objection, and Rashi's textual
note that on his reading the girsa "rather, conclude that it is
Rabbi Eliezer ben Yaakov" is not read, the conclusion being instead
that Middot is not Rabbi Yehuda). vilnaLine 27-30 open `l02` (Rav
Adda son of Rav Yitzchak: the Chamber of the Lambs was set off,
long, standing on the west and stretching toward both corners, with
the two viewing-angle sub-DHs). vilnaLine 31-38 open `l05` (per the
established multi-DH rule vilnaLine 31 carries the "it stands to
reason it was in the southwest" opening; then the shewbread
contradiction sub-DH with the assumed right-hand circuit placing
the four chambers, against Middot's placement of the shewbread
chamber in the southeast). vilnaLine 39-44 open `l07` (Rav Huna son
of Rav Yehoshua's resolution: Middot counts by the right,
explicitly south to east to north to west, the way one circles the
House from outside, while Tamid, which spelled nothing out, can be
said to count by the left). vilnaLine 45 is the daf's final
truncated word "אי", linked to `l09` ("אִי", 17a's own truncated
final Gemara line); 17b's raw text was confirmed to open "אי אמרת
בשלמא. תנא דתמיד גופיה", the standard boundary pattern.

This sub-chunk also repaired vilnaLine 24-45's baseline, of which
all 22 entries fell in the range that previously had empty
`linkedGemaraLineIds` (vilnaLine 21-45) with stub text describing
material partly belonging to 17b. All 22 fixed entries carry real
zero-padded `yoma-017a-lXX` ids (`l01`, `l02`, `l05`, `l07`,
`l09`). No deferrals. 17a is fully resolved, 45/45.

## 17b (VERSION 14.98), full daf in one chunk, closing 17b entirely

Verified the 17a/17b boundary first: 17b's raw talmud.dev Rashi text
opens "אי אמרת בשלמא. תנא דתמיד גופיה דתני לשכת הטלאים", restating
and completing 17a's truncated final word "אי" - no regression, no
change needed on 17a.

17b has 33 raw Rashi print-lines, under the 40-entry threshold, so
it was fixed as a single full-daf chunk. It has 7 real Gemara lines
(`yoma-017b-l01`, `l06`, `l09`, `l12`, `l17`, `l23`, and the
truncated `l25`).

vilnaLine 1-16 open `l01` (the "if you say granted" argument: the
Tamid tanna concedes the chamber lay more toward the southwest and
taught by eye, so his left-hand count places the four chambers
without clashing with Middot; then the "but if you say" counter,
that if the northwest placement were exact, the leftward count would
leave the shewbread chamber in the southwest). vilnaLine 17 opens
`l06` (the "but the Master said" objection from the rightward-turns
rule at 58b, answered there as applying only to service). vilnaLine
18-24 open `l12` (the sub-DHs on the High Priest's precedence
portion: the two loaves of Shavuot, "four or five" per Shabbat,
"and it shall be for Aaron and his sons" written of the shewbread,
and "half for Aaron" with the two undivided loaves). No raw line
carries its own DH for `l09` - the usual not-every-line pattern.
vilnaLine 25-26 open `l17` ("we arrive at the Rabbis", who say he
does not take half, for less than five he would not take).
vilnaLine 27-32 open `l23` (Abaye's "the first and middle clauses
are the Rabbis", with the concession that it is not proper conduct
to give the High Priest a slice). vilnaLine 33 is the daf's final
truncated word "ומאי", linked to `l25` ("וּמַאי", 17b's own
truncated final Gemara line) continuing onto 18a.

All 33 fixed entries carry real zero-padded `yoma-017b-lXX` ids.
No deferrals. 17b is fully resolved, 33/33.

## 18a, vilnaLine 1-29 (VERSION 14.99), first half of a two-part daf

Verified the 17b/18a boundary first: 18a's raw talmud.dev Rashi text
opens "ומאי ארבע או חמש. מתי ארבע ומתי חמש", restating and completing
17b's truncated final word "ומאי" - no regression, no change needed
on 17b.

18a has 58 raw Rashi print-lines, split into two sub-chunks:
vilnaLine 1-29 here, vilnaLine 30-58 in a follow-up chunk. 18a has
17 real Gemara lines (`yoma-018a-l01` through `l39`, including the
mishna line `l12`). An independent reconnaissance pass verified the
DH segmentation against Sefaria's Rashi on Yoma 18a (exactly 22
segments matching the raw print-line boundaries verbatim), and the
mapping was re-verified against the local files after a container
restart before applying.

vilnaLine 1-2 open `l01` (when four and when five loaves, and the
Rabbis' twelve-loaf division from Sukka 56a). vilnaLine 3-5 open
`l04` (per Rabbi Yehuda: the incoming watch's two loaves are the
door-closing fee, so the division is from ten and he takes four).
vilnaLine 6-8 open `l07` (Rava: the whole baraita is Rabbi, who
holds like Rabbi Yehuda). vilnaLine 9-29 open `l09` (the long
compound DH "but what is four... this is where there is a delayed
watch": Rashi's extended explanation of the mishmar hamitakev - the
watch that arrives early or lingers around a Festival adjacent to
Shabbat, with the Sukka 55b rule that on such Shabbatot all watches
share equally). The old entries for this daf had been written
against the Gemara's vilna numbering rather than the Rashi print
lines, so most were off; vilnaLine 29 onward were empty stubs.

All 29 fixed entries carry real zero-padded `yoma-018a-lXX` ids
(`l01`, `l04`, `l07`, `l09`). No deferrals in this sub-chunk.
vilnaLine 30-58 (the rest of the delayed-watch comment, the mishna
DHs on "my lord" and the order of the day, the First/Second Temple
contrast with Marta bat Baytus, the erev Yom Kippur feeding DHs,
the zav/keri distinction, and the truncated final word "השחלין"
continuing onto 18b) remain for the follow-up chunk.

## 18a, vilnaLine 30-58 (VERSION 15.00), second half, closing 18a entirely

Continued directly from the first sub-chunk. vilnaLine 30-35
conclude the long `l09` delayed-watch comment (the one-day gap case
where the watches do not share equally and the delayed watch takes
two loaves). vilnaLine 36 opens `l11` ("if so, what is 'Rabbi says:
always five'"). vilnaLine 37-41 open the mishna line `l12` (the
sub-DHs "ishi" meaning my lord, "they read before him in the order
of the day" being Acharei Mot, and "so that he will recognize" the
animals). vilnaLine 42-48 open `l21` (the Gemara section: in the
First Temple only fitting priests were appointed; Marta bat Baytus
paying King Yannai a tarkav, half a se'ah, of gold dinars to
appoint Yehoshua ben Gamla). vilnaLine 49-52 open `l28` (the dayala
officer and Ravina's marketplace proverb). vilnaLine 53 opens `l29`
(feeding him fine flour and eggs on erev Yom Kippur morning to
loosen his bowels). vilnaLine 54-57 open `l35` (the "to heat" and
mnemonic sub-DHs close within their lines; then the zav-attribution
DH with Rashi's zov-versus-semen appearance comparison, the water
of barley dough against the bound egg white, and "they do not feed
him" during his days of examination). vilnaLine 58 is the daf's
final truncated word "השחלין", linked to `l39` (the five-things
baraita whose list the word continues); 18b's raw text was
confirmed to open "השחלין. קרש"ין", the standard boundary pattern.

The prior entries for vilnaLine 29-58 were empty stubs; the earlier
populated entries had been keyed to Gemara vilna numbers rather
than Rashi print lines, including an invented Latin etymology for
dayala and a garbled version of the zov/semen comparison, all
replaced here from the raw Hebrew. All 29 fixed entries carry real
zero-padded `yoma-018a-lXX` ids (`l09`, `l11`, `l12`, `l21`, `l28`,
`l29`, `l35`, `l39`). No deferrals. 18a is fully resolved, 58/58.

## 18b (VERSION 15.01), full daf in one chunk, closing 18b entirely

Verified the 18a/18b boundary first: 18b's raw talmud.dev Rashi text
opens "השחלין. קרש"ין", restating and completing 18a's truncated
final word "השחלין" - no regression, no change needed on 18a.

18b has 34 raw Rashi print-lines, under the 40-entry threshold, so
it was fixed as a single full-daf chunk. It has 7 real lines: the
Gemara lines `yoma-018b-l01`, `l07`, `l11`, `l17`, `l20` and the
mishna lines `l23`, `l28`. Both sub-DH anchors that could have been
ambiguous were verified against the full local Hebrew: "רבנן קלא
אית להו" sits inside `l11` and "הוא פורש ובוכה" inside `l23`.

vilnaLine 1 opens `l01` (the Old French glosses for cress, purslane,
and arugula, with the border-grown metzranaa). vilnaLine 2-7 open
`l07` (the guest who should not eat eggs or sleep in the
householder's cloak, Rav's visits to Darshish, and "who will be
mine for the day"). vilnaLine 8-10 open `l11` (Rabbi Eliezer ben
Yaakov's decree lest half-siblings born in different countries
marry, and the answer that the Sages have renown). vilnaLine 11-12
open `l17` (Rava's seven clean days from consent, lest desire
brought blood). vilnaLine 13-15 open `l20` (mere seclusion: one
with bread in his basket does not crave). vilnaLine 16-27 open the
mishna line `l23` (handing over to the elders of the priesthood,
the incense handful per Leviticus 16 and its difficulty per 47b,
the House of Avtinas, the oath against Sadducee practice per 19b,
"ishi", and "he withdraws and weeps"). vilnaLine 28-33 open the
mishna line `l28` (expounding all Yom Kippur night so he not
sleep, the not-a-darshan case, and Job/Ezra as heart-drawing
reading). vilnaLine 34 is the bare Gemara-section header "גמ'",
linked to `l28` (18b's own final line), with the Gemara's first DH
following on 19a.

All 34 fixed entries carry real zero-padded `yoma-018b-lXX` ids.
No deferrals. 18b is fully resolved, 34/34.

## 19a, vilnaLine 1-29 (VERSION 15.02), first half of a two-part daf

Verified the 18b/19a boundary first: 19a's raw talmud.dev Rashi text
opens "גמ' תנא ללמדו חפינה. מוליכין אותו לבית אבטינס", restating the
bare Gemara-section header that closed 18b - no regression, no
change needed on 18b.

19a has 58 raw Rashi print-lines, split into two sub-chunks:
vilnaLine 1-29 here, vilnaLine 30-58 in a follow-up chunk. It has
13 real Gemara lines (`yoma-019a-l01` through `l38`, including the
split pair `l36a`/`l36b` for vilna line 36). An independent
reconnaissance pass verified the DH segmentation against Sefaria's
Rashi on Yoma 19a (28 comments, all matched verbatim), including
the one genuinely order-sensitive anchor: the DH "לשכת הגולה"
glosses the chamber list in `l11` (Sefaria 3.1), not the later
elaboration in `l15`; `l15` and `l23` correctly receive no Rashi
lines at all.

vilnaLine 1 opens `l01` (the Gemara header and "to teach him the
handful-scooping"). vilnaLine 2-5 open `l05` (the Parhedrin and
Avtinas chamber glosses close within vilnaLine 2, whose newly
opened DH "on its roof" belongs to `l05`; then the mesiba spiral
and the ascent to the Parva roof). vilnaLine 6-9 open `l11` (the
Golah chamber named for the returnees' cistern, "behind the two of
them", and the level roof over all three). vilnaLine 10-13 open
`l19` (the Fuel and Offering Gates - Rashi: "I do not know why they
were so named" - and the Water Gate of the Festival libation per
Shekalim 9b). vilnaLine 14-26 open `l25` (the ten sanctifications,
"on that day" with the derivation at 32a, the Parva roof inside
the sanctified courtyard, "except this one" with the year-round
immersion rule of 30b against the Leviticus 16 sacred-place
requirement, and "beside his chamber"). vilnaLine 27-28 open `l28`
(it stands to reason Parhedrin was in the south, next to the
weekday immersion house). vilnaLine 29 opens `l30` (the start of
the "what is the reason? He rises early" comment).

All 29 fixed entries carry real zero-padded `yoma-019a-lXX` ids
(`l01`, `l05`, `l11`, `l19`, `l25`, `l28`, `l30`). No deferrals in
this sub-chunk. vilnaLine 30-58 (the rest of the early-rising
comment with the Etam spring aqueduct, the "if you say Parhedrin
was north" counter-scenario, the Sadducee and haughtiness answers,
the agency question on Rav Huna son of Rav Yehoshua, and the
trailing catchword "הכי" whose DH continues on 19b) remain for the
follow-up chunk.

## 19a, vilnaLine 30-58 (VERSION 15.03), second half, closing 19a entirely

Continued directly from the first sub-chunk. vilnaLine 30-46
continue `l30` (the long "what is the reason" comment: rising early
all seven days, the weekday immersion house fitted in the wall's
thickness above the Water Gate with spring water drawn by aqueduct
from the Etam spring, the rule that covering one's legs requires
immersion before entering the courtyard, the walk north to learn
the handful-scooping and the all-day service per 14a, the dusk
sprinkling per Rabbi Akiva's view that sprinkling renders the pure
impure, and "and rests" in the Parhedrin chamber beside the
immersion house). vilnaLine 47-52 open `l32` (the
counter-scenario: if Parhedrin were in the north, the toil of the
south-north-south circuit, with the sub-DHs on rising early, going
south, and immersing and finishing the handful-scooping in the
House of Avtinas). vilnaLine 53-54 open `l36a` ("why not?" - we
burden him deliberately, so that a Sadducee not God-fearing enough
would withdraw before accepting the office, which serves us since
they change the service). vilnaLine 55 opens `l36b`
("alternatively", so his mind not swell with pride; and "if you do
not say so", the two chambers should be adjacent). vilnaLine 56-57
open `l38` ("let us say it refutes Rav Huna" and "these priests"
are agents of the Merciful One, with the Nedarim 35b vow
consequence). vilnaLine 58 is the daf's final truncated word
"הכי", linked to `l38` (19a's own final line, whose sentence the
19b continuation answers); 19b's raw text was confirmed to open
"הכי קאמרי ליה", the standard boundary pattern.

This sub-chunk also repaired vilnaLine 48-58, which previously had
empty `linkedGemaraLineIds` and stub text, and replaced entries
whose ids pointed at a nonexistent unsplit `l36`. All 29 fixed
entries carry real zero-padded `yoma-019a-lXX` ids (`l30`, `l32`,
`l36a`, `l36b`, `l38`). No deferrals. 19a is fully resolved, 58/58.

## 19b, vilnaLine 1-34 (VERSION 15.04), first half of a two-part daf

Verified the 19a/19b boundary first: 19b's raw talmud.dev Rashi text
opens "הכי קאמרי ליה. האי דקאמרי ליה אתה שלוחנו", restating and
completing 19a's truncated final word "הכי" - no regression, no
change needed on 19a.

19b has 68 raw Rashi print-lines, split into two sub-chunks:
vilnaLine 1-34 here, vilnaLine 35-68 in a follow-up chunk. It has
16 real lines (`yoma-019b-l01` through `l49`, including the mishna
line `l40`). Every order-sensitive anchor was verified against the
full local Hebrew before applying: "שלא יתקן מבחוץ ויכניס" sits in
`l07` (so the "מבחוץ" DH is l07, not the Sadducee-incident baraita
of l09, which correctly receives no Rashi lines at all), "לא יוכל
איש לדבר" in `l36`, and both psalm phrases in `l45`. An independent
reconnaissance pass also verified the DH segmentation against
Sefaria's Rashi on Yoma 19b (28 dibburim, all matched verbatim).

vilnaLine 1-3 open `l01` ("thus they say to him": the oath is
administered by the court's understanding, against mental
reservation). vilnaLine 4-8 open `l04` (the suspicion of Sadducee
practice and "one who suspects the fit is stricken in his body",
with the Exodus 4 prooftext). vilnaLine 9-19 open `l07` ("and why
all this", "that he not prepare" the double handful per Leviticus
16, and "outside": the Sadducee exegesis of "for in a cloud I shall
appear"). vilnaLine 20-25 open `l16` ("from his nostrils", first of
the limbs to enter, per Shevuot 17b on entering an afflicted house
backward). vilnaLine 26-29 open `l22` (the Kaputal/Kevutal
peh-versus-bet gesture; the word "מתני" ending vilnaLine 26 is part
of the lemma "מתני ליה", not a mishna marker). vilnaLine 30-33 open
`l26` ("gesture, wink, point" as one term split across eyes and
fingers, per Proverbs 6). vilnaLine 34 opens `l33` (the start of
"in the first chapter" on Shema intent).

All 34 fixed entries carry real zero-padded `yoma-019b-lXX` ids
(`l01`, `l04`, `l07`, `l16`, `l22`, `l26`, `l33`). No deferrals in
this sub-chunk. vilnaLine 35-68 (the rest of the Shema-intent
comment, the "bam" derashot, the mishna on the tzerada finger and
keeping him occupied, the Gemara's tzarta-dida and kidda
demonstrations, the singing "if the Lord does not build a house",
the notables of Jerusalem, the sinning in the provinces at
Nehardea, and the truncated final word "לפתח" continuing onto 20a)
remain for the follow-up chunk.

Note: this chunk was applied twice. The first application passed
the full validator suite but was lost, uncommitted, when the
session's container was recycled a second time; the work was
re-applied identically from the retained fix content and
re-validated before commit. No pushed history was affected.

## 19b, vilnaLine 35-68 (VERSION 15.05), second half, closing 19b entirely

Continued directly from the first sub-chunk. vilnaLine 35 concludes
the `l33` "in the first chapter" comment (the Deuteronomy 6 intent
verse). vilnaLine 36-42 open `l34` (the four "bam" sub-DHs: making
audible what leaves the mouth, "and not in prayer" per I Samuel 1
as found in the Sheiltot of Rav Achai Gaon, "of them" meaning words
of Torah, and "not of other things" - children's chatter and
lightheadedness). vilnaLine 43 opens `l36` ("no man can speak" - he
has no license). vilnaLine 44-51 open the mishna line `l40` (the
tzerada finger deferred to the Gemara, "cool off" walks to dispel
sleep, and "they occupy him" until the daily offering's slaughter
when the east lights up). vilnaLine 52-57 open `l42` (the Gemara
section: "the rival of this" thumb-snap demonstration heard through
the whole study hall). vilnaLine 58-61 open `l44` ("something
novel" and the kidda bow per Sukka 53a). vilnaLine 62-65 open `l45`
("but with the mouth" they sang, and "if the Lord does not build a
house" as a warning that unaccepted service counts for nothing).
vilnaLine 66 opens `l47` (per the multi-DH rule: it closes the
psalm comment, carries "in vain do its builders labor" whole, and
opens "of the notables of Jerusalem"). vilnaLine 67 opens `l49`
(closing the notables comment, carrying "except that they would
sin" whole, and opening "interpret it" - Nehardea). vilnaLine 68 is
the daf's final truncated word "לפתח", linked to `l49` (19b's own
final line, whose mid-dialogue text the 20a verse quote completes);
20a's raw text was confirmed to open "לפתח חטאת רובץ", the standard
boundary pattern.

This sub-chunk also repaired vilnaLine 41-68, of which 28 entries
previously had empty `linkedGemaraLineIds` and identical stub text.
All 34 fixed entries carry real zero-padded `yoma-019b-lXX` ids
(`l33`, `l34`, `l36`, `l40`, `l42`, `l44`, `l45`, `l47`, `l49`).
No deferrals. 19b is fully resolved, 68/68, and with it the entire
12b-19b hotspot.

## 20a, vilnaLine 1-20 (VERSION 15.06), first half of a two-part daf

Verified the 19b/20a boundary first: 20a's raw talmud.dev Rashi text
opens "לפתח חטאת רובץ. יצה"ר מחטיאו בעל כרחו", restating and
completing 19b's truncated final word "לפתח" - no regression, no
change needed on 19b.

20a has only 5 real Gemara/mishna lines (`yoma-020a-l01`, `l07`,
`l12`, `l15`, `l18`); the sugya scaffolding confirms `l07`'s span is
vilna 7-11 (the mishna alone) and `l12`-`l18` is one sugya (the
midnight-derivation and Rav Kahana's objection). 41 raw Rashi
print-lines is one over the 40-entry split threshold, so it is split
into two sub-chunks: vilnaLine 1-20 here, vilnaLine 21-41 in a
follow-up chunk.

vilnaLine 1 closes the "at the door sin crouches" comment on `l01`
and opens the mishna DH "they remove ashes from the altar", which
belongs to `l07`. vilnaLine 2-16 continue through `l07`'s sub-DHs
(the handful-scooping procedure, "adjacent to it", "on Yom Kippur
from midnight", "and on the Festivals from the first watch" with
its Berachot 3a citation on the three night-watches, and "the
rooster's crow would not arrive" until the courtyard filled with
Festival pilgrims). vilnaLine 16-20 open `l12` (the Gemara-section
transition "where do we stand", which Rashi glosses as textually
uncertain and proposes reading as the direct citation of the
Zevachim 86a mishna on limbs forced off the altar, then "before
midnight" and "they are subject to misuse of consecrated property").

All 20 fixed entries carry real zero-padded `yoma-020a-lXX` ids
(`l01`, `l07`, `l12`). No deferrals in this sub-chunk. vilnaLine
21-41 (the rest of the misuse-of-consecrated-property discussion,
"after midnight", the Leviticus derivation of the midnight cutoff
from the two "all night" verses, and the truncated final word "ואי"
whose DH - "and if it is Torah law, how do we advance it" -
continues on 20b, anchored to `l18`, the daf's own truncated final
Gemara line covering Rav Kahana's objection) remain for the
follow-up chunk.

## 20a, vilnaLine 21-41 (VERSION 15.07), second half, closing 20a entirely

Continued directly from the first sub-chunk. vilnaLine 21-32
continue `l12` (closing "before midnight", then the full
"misuse of consecrated property" and "after midnight" comments,
including the Pesachim 26a citation on why a limb that has already
fulfilled its mitzva carries no misuse liability, and the Leviticus
5 "sins by mistake against the sacred things" prooftext). vilnaLine
33-40 open `l15` (the derivation itself: the two "all night" verses,
one for burning and one for ash removal, split in half to yield
midnight as the cutoff, including the note that the burnt offering's
flesh is only called "ash" once consumed by fire). vilnaLine 41 is
the daf's final truncated word "ואי", linked to `l18` (Rav Kahana's
objection, 20a's own truncated final Gemara line); 20b's raw text
was confirmed to open "ואי דאורייתא הוא היכי מקדמינן", the standard
boundary pattern.

All 21 fixed entries carry real zero-padded `yoma-020a-lXX` ids
(`l12`, `l15`, `l18`). No deferrals. 20a is fully resolved, 41/41.

## 20b, vilnaLine 1-31 (VERSION 15.08), first half of a two-part daf

Verified the 20a/20b boundary first: 20b's raw talmud.dev Rashi text
opens "ואי דאורייתא הוא היכי מקדמינן. גרסינן ולא גרסינן", restating
and completing 20a's truncated final word "ואי" - no regression, no
change needed on 20a.

20b has 62 raw Rashi print-lines, split into two sub-chunks:
vilnaLine 1-31 here, vilnaLine 32-62 in a follow-up chunk. 20b has
11 real lines (`yoma-020b-l01`, `l02`, `l05`, `l11`, `l13`, `l18`,
`l24`, `l28`, `l33`, `l35`, and the truncated `l40`), spanning three
sugyot (`s01`: l01-l05, vilna 1-10; `s02`: l11-l24, vilna 11-27;
`s03`: l28-l40, vilna 28-49).

vilnaLine 1-3 open `l01` (the challenge: if midnight were
Torah-fixed, why can it be advanced or delayed, since half-consumed
ash is equally fit for removal regardless of timing). vilnaLine 4-20
open `l02` (Rabbi Yochanan's resolution: the "all night...until
morning" verse gives a second morning, dawn, meaning the Torah's own
cutoff for burning is not stated, so the Sages inferred midnight;
this single long comment continues into the practical outcome that
daily removal needs only the rooster's crow, without a formal new
DH marker - not every clause gets its own dibbur hamatchil).
vilnaLine 20-31 open `l05` (Yom Kippur's High-Priest weakness
requiring an earlier start, and the Festivals' abundant offerings
requiring removal from the first watch, with the Tamid 28b citation
on the tapuach ash-heap).

All 31 fixed entries carry real zero-padded `yoma-020b-lXX` ids
(`l01`, `l02`, `l05`). No deferrals in this sub-chunk. vilnaLine
32-62 (the "who crowed" dispute between Rav and Rabbi Sheila, the
Rav-in-Rabbi-Sheila's-territory anecdote with its wool-carding and
"one elevates in sanctity but does not lower" proverbs, Gevini the
herald, King Agrippa's account of hearing the confession from three
parasangs, the sun's wheel drowning out human voices, and the
truncated final word "וי"א" continuing onto 21a) remain for the
follow-up chunk.

## 20b, vilnaLine 32-62 (VERSION 15.09), second half, one deferral

Continued directly from the first sub-chunk. An independent
reconnaissance pass verified this daf's DH segmentation against
Sefaria's Rashi on Yoma 20b (10 comment groups, matching the raw
print-line boundaries verbatim) and flagged the same two judgment
calls documented below before any edit was applied.

vilnaLine 32 concludes `l05`. vilnaLine 33-35 open `l11` (the
"kara gavra" proclamation, the appointee calling the priests to
their service). vilnaLine 36-52 open `l13` (the long anecdote: Rav
visits Rabbi Sheila's town unrecognized, serves as disseminator
translating "kriat hagever" as "kara gavra," is challenged with
"kara tarnegola," and answers with the flute-for-weavers parable).
vilnaLine 53-58 open `l18` (Rav declines Rabbi Sheila's offer to
relieve him, citing "one elevates in sanctity but does not lower,"
with the wool-carding proverb). vilnaLine 59 opens `l28` per the
multi-DH rule: it closes the `l18` comment, carries the complete
"Gevini the herald" DH (`l24`) and "as the Master said" DH (`l28`)
each opening and closing within the line, and finally opens "he
already said, I beseech the Name," left open at line end - so per
the established rule the raw line's target is the last-opened DH,
`l28`. This means `l24` (Gevini's own line) legitimately receives
no dedicated vilnaLine of its own; its entire Rashi comment is a
single clause fully nested inside vilnaLine 59, and forcing a split
would misassign real content rather than resolve a genuine gap.
vilnaLine 60 opens `l33` (the confession story concludes, then "and
there is weakness" and "and here it is daytime," both anchored to
`l33`). vilnaLine 61 opens `l35` (the sun's roar and the sawdust
wordplay, both anchored to `l35`).

vilnaLine 62, the daf's final truncated word "וי"א", was initially
deferred rather than linked. At the time, the reasoning was that
every other daf boundary in this run had resolved by linking the
truncated catchword to the daf's own final Gemara line, but that
pattern appeared to break down here: `l40` ends at a different
clause ("וְיֵשׁ אוֹמְרִים: אַף לֵידָה," the childbirth mention) than
the one this Rashi entry actually glosses. 21a's own Rashi opens
with the full DH "וי"א אף רידייא," commenting on the irrigation-angel
clause "וְיֵשׁ אוֹמְרִים אַף רִידְיָא," a further continuation of
20b's own Gemara text beyond what `l40` captures and beyond any
locally available real line id. Rather than force what looked like a
mismatched link, vilnaLine 62's `linkedGemaraLineIds` was cleared and
its `en` field replaced with a note explaining why no local target
could be determined.

A dedicated policy pass at VERSION 15.10 (see "Cross-daf Rashi
boundary link policy" below) revisited this deferral by checking the
established convention against corpus precedent rather than
assumption. That check found the deferral rested on a requirement -
that the Rashi catchword's own words must literally appear in the
linked Gemara line's text - that the convention never actually
imposed. 12b's boundary case proves this: its catchword "כיון" links
to `l42`, whose entire captured Hebrew is the unrelated word
"הֲלָכָה." Rashi and Gemara are independently typeset columns on the
same physical page, each truncated at its own trailing word at the
shared page-turn point; the link is positional (same daf, same
final captured line), not a phrase match. Under that convention,
vilnaLine 62's deferral was reversed: it is now linked to
`yoma-020b-l40`, 20b's own final locally captured Gemara line, per
the same rule every other boundary case in this run already follows.

30 of the 31 entries in this sub-chunk carry real zero-padded
`yoma-020b-lXX` ids (`l05`, `l11`, `l13`, `l18`, `l24` via `l28`'s
neighbor, `l28`, `l33`, `l35`); vilnaLine 62 now carries `l40` per
the reversal above. 20b is fully resolved, 62/62.

## Cross-daf Rashi boundary link policy (VERSION 15.10)

This section documents the general convention for daf-boundary Rashi
entries in this audit, decided during a bounded policy pass on the
20b vilnaLine 62 case above.

**Investigation.** Every prior cross-daf boundary case fixed in this
run was checked for its resolved `linkedGemaraLineIds` target: 12b to
`yoma-012b-l42`, 13a to `yoma-013a-l29b`, 13b to `yoma-013b-l29`, 14a
to `yoma-014a-l47`, 14b to `yoma-014b-l31`, 15a to `yoma-015a-l47`,
17b to `yoma-017b-l25`, and 19b to `yoma-019b-l49`. In every case the
truncated final Rashi entry of a daf links to that same daf's own
final locally captured Gemara line id. None of the eight cases links
across daf boundaries to the next daf's line id.

**Finding.** Literal phrase matching between the Rashi catchword and
the linked Gemara line's text was never a requirement of this
convention. 12b's catchword "כיון" (kivan) links to `l42`, whose full
captured text is "הֲלָכָה" (halacha), a completely different word.
This is expected: the Rashi column and the Gemara column are
independently paginated on the same physical printed page. Each
column's own trailing word is whatever that column happens to end on
at the shared page-turn point; the two need not, and generally do
not, share vocabulary. Confirmed directly against 13a's opening
Gemara text, which repeats "הלכה" as its own catchword, independent
of Rashi's "כיון."

**Decided convention.** The truncated final Rashi entry of a daf
links to that same daf's own final locally captured Gemara line id,
as a positional and mechanical anchor. This holds even when that
line's own captured text ends at an earlier clause than the one the
Rashi catchword's dibbur hamatchil actually continues into on the
next daf. Cross-daf `linkedGemaraLineIds` (linking a daf's Rashi
entry to a line id on the following daf) are not used anywhere in
this corpus and are not part of the established pattern. The `en`
field for such an entry should name the catchword, state that it is
the start of a dibbur hamatchil continuing onto the next daf, and
briefly describe what the comment actually says, drawing on the next
daf's text for that description even though the link itself stays on
the current daf.

**20b vilnaLine 62 resolution.** Applying this convention, vilnaLine
62 (catchword "וי"א") is linked to `yoma-020b-l40`, 20b's own final
locally captured Gemara line, even though `l40`'s captured text ends
at the childbirth clause one clause earlier than the irrigation-angel
clause the Rashi entry glosses. This matches the positional pattern
of every other resolved boundary case and closes the deferral opened
in the "20b, vilnaLine 32-62" section above without requiring any
edit to 21a.

## 21a, full daf (VERSION 15.11), two sub-chunks, closing 21a entirely

A fast alignment run resumed from 21a following the boundary policy
pass above. Before any edit, the 20b/21a boundary was re-verified
read-only: 21a's raw Rashi column opens with the full dibbur
hamatchil "וי\"א אף רידייא. מלאך הממונה על השקות הארץ..." (and some
say, also the irrigation angel - the angel appointed over irrigating
the earth), the exact continuation of 20b's truncated final catchword
"וי\"א", confirming the boundary decision was correct and requiring
no change to either file.

21a's Gemara side has 9 real captured lines (`l01`, `l03`, `l06`,
`l14`, `l22`, `l27`, `l29`, `l32`, `l34`) against 37 raw print lines,
and its Rashi side has 62 raw print lines carrying entirely
generic, placeholder-style `en` text ("Commentary on the five
miracles," "Commentary on the list structure," "Commentary on the
cosmic water system") with `linkedGemaraLineIds` uniformly pointing
at whichever of `l01`/`l03`/`l06` happened to be nearby, regardless
of actual content - the same descriptive-style failure pattern
documented in the systemic finding below, not yet previously
verified for this daf.

All 62 raw Rashi print lines were read against the raw Gemara text
and the 9 real captured line ids, and each vilnaLine's dibbur
hamatchil was identified and matched to the real Gemara line whose
content it actually glosses, using the same multi-DH rule as prior
daf (a raw print line that both closes one comment and opens another
is assigned to the last-opened DH). The correspondence: vilnaLine
1-4 (the Ridya passage) to `l01`; 5-10 (Rabbi Sheila's baraita on
keriat hagever) to `l03`; 11-41 (the packed-yet-spacious prostration
miracle and the eleven-cubit movement mechanics) to `l06`; 42-49
(the omer/two loaves/showbread and "the place is cramped" items from
the ten-miracles list) to `l14`; 50-54 (broken vessels, crop and
feathers, ash removal) to `l27`; 55-56 (the three-disqualification
and two-absorption count, the showbread's timing) to `l29`; 57-60
(the Ark's space and the Cherubs' miraculous wingspan) to `l32`;
61-62 (the "external miracles" summary and the pure/impure table
inference) to `l34`. `l22` (the fire/rain and smoke miracles) has
no dedicated Rashi comment in this daf's column and legitimately
carries no vilnaLine.

vilnaLine 62, the daf's final truncated word "עשוי" (made), is the
same kind of boundary case as 20b's vilnaLine 62: per the policy
above, it is linked to `yoma-021a-l34`, 21a's own final locally
captured Gemara line, even though the DH it belongs to ("מכלל שהוא
טמא") continues its explanation onto 21b. No edit was made to 21b.

All 62 entries were fixed across two sub-chunks (vilnaLine 1-31,
then 32-62, since the daf exceeds the 40-entry split threshold).
21a is fully resolved, 62/62, with real translations replacing every
generic placeholder and every linkedGemaraLineIds value corrected to
its real zero-padded `yoma-021a-lXX` target.

## 21b, full daf (VERSION 15.12), two sub-chunks, closing 21b and Perek 1 entirely

Continuing the fast alignment run from 21a. Before any edit, the
21a/21b boundary was re-verified read-only: 21a's truncated final
Rashi word "עשוי" is completed by 21b's opening dibbur hamatchil
"עשוי לנחת" (made to rest), and 21a's truncated final Gemara word
"כלי" is completed by 21b's opening Gemara text "כלי עץ העשוי לנחת"
(a wooden vessel made to rest), confirming both columns continue
cleanly with no gap. No edit was made to 21a.

21b's Gemara side has 15 real captured lines (`l01`, `l06`, `l14`,
`l15`, `l18`, `l19`, `l21`, `l25`, `l27`, `l31`, `l36`, `l37`, `l40`,
`l41`, `l42`) against 42 raw print lines, and its Rashi side has 46
raw print lines, all carrying the same generic descriptive-style
placeholder text as 21a ("Commentary on the Holy of Holies' spatial
rules," "Commentary on the divine acceptance signaled by straight
smoke") with `linkedGemaraLineIds` pointing at nearby real ids
largely disconnected from actual content.

All 46 raw Rashi print lines were read against the raw Gemara text
and the 15 real captured line ids, using the same multi-DH rule as
21a. The correspondence: vilnaLine 1-2 (wooden vessel impurity, the
sack analogy) to `l01`; 3 (the Temple pomegranate-tree miracle
citation) to `l06`; 4 (the "fixed things" catchword) to `l14`; 5-8
(the crouching-lion ember of the altar fire) to `l15`; 9-10 ("when we
say" ordinary smoke) to `l18`; 11-16 (the "I will accept it" verse
and the five things absent in the Second Temple) to `l21`; 17-26 (the
six fires baraita's explanations, Gabriel's fire, and the Sanhedrin
citation) to `l27`; 27-32 (the festival-end smoke-watching omen for
rain, north-leaning) to `l31`; 33-39 (east/west-leaning smoke and the
Gittin citation) to `l36`; 40-41 (the wind-crop mnemonic "this one
increases its own") to `l40`; 42-45 ("this is for us, that is for
them," Babylonia versus the land of Israel) to `l41`; 46 (the
perek-closing "Hadran" formula) to `l42`. `l19` (Rabbi Chanina's
"crouching like a dog" testimony, already glossed once by the
vilnaLine 5-8 comment on the phrase's first occurrence), `l25` (the
bare six-fires list header), and `l37` (the east/west/north/south
wind-quality list, superseded by the more specific comment on `l40`'s
mnemonic) all have no dedicated Rashi comment in this daf's column
and legitimately carry no vilnaLine. An initial pass mistakenly
linked vilnaLine 40-41 to `l37` before a direct text check found the
DH's own phrase "האי מרבה דידיה והאי מרבה דידיה" verbatim inside
`l40`'s captured Hebrew rather than `l37`'s; this was corrected
before regenerating `learning_data.js`.

vilnaLine 46, the daf's final raw Rashi line, is not a dibbur
hamatchil at all but the "Hadran alach Shivat Yamim" formula marking
the end of Perek 1, printed identically in both the Gemara and Rashi
columns. It is documented as such rather than force-fit into the
boundary-catchword convention, and linked to the Gemara's own
matching `l42` line for this daf.

All 46 entries were fixed across two sub-chunks (vilnaLine 1-26, then
27-46). 21b is fully resolved, 46/46, closing Perek 1 of Yoma
entirely with real translations replacing every generic placeholder
and every linkedGemaraLineIds value corrected to its real zero-padded
`yoma-021b-lXX` target.

## 22a, full daf (VERSION 15.13), two sub-chunks, opening Perek 2

Continuing the fast alignment run into Perek 2. 21b ended with the
"Hadran" perek-closing formula, and 22a opens fresh with Perek 2's
Mishna "בראשונה כל מי שרוצה לתרום" (initially, whoever wished to
remove the ashes), a complete, non-truncated phrase in both the
Gemara and Rashi columns - a clean perek boundary with no
continuation issue, unlike the mid-sentence truncations at every
other daf boundary in this run. No edit was needed to 21b.

22a's Gemara side has 13 real captured lines (`l01`, `l05`, `l07`,
`l12`, `l16`, `l18`, `l21`, `l22`, `l27`, `l30`, `l36`, `l39`, `l40`)
against 41 raw print lines, and its Rashi side has 65 raw print
lines, all carrying the same generic descriptive-style placeholder
text as 21a/21b. The prior stub's vilnaLine 10-15 ("Saul counted
Israel," the Saul/David comparison) is not fabricated - it is real
content, but it belongs to 22b's own extensive Rabbi Elazar/Saul
digression (see "22b, full daf" below), misattributed one daf early
in this stub, the same one-daf-off pattern already documented for
11b/12a. This was corrected when 22b was audited directly, confirming
why this audit reads the raw Rashi print lines of each daf directly
rather than trusting existing `en` text or its daf attribution.

All 65 raw Rashi print lines were read against the raw Gemara text
and the 13 real captured line ids, using the same multi-DH rule as
prior daf. The correspondence: vilnaLine 1-24 (the original
first-come ramp race, its danger, and the finger-count lottery
mechanics) to `l01`; 25-33 (one or two fingers, no thumbs, the
cheating countermeasure) to `l05`; 34-36 (the four daily lottery
rounds) to `l07`; 37-44 (why a lottery was not instituted from the
start) to `l12`; 45-51 (the limb-burning counter-question) to `l16`;
52-53 (no re-sanctification needed the next day) to `l18`; 54 (easier
to stay awake than rise early) to `l22`; 55-59 (the wood-arrangement
enactment and the two wood logs) to `l27`; 60 (the four cubits of
ground before the ramp) to `l36`; 61-64 (the ramp's own four cubits
and Rav Pappa's base/ledge question) to `l39`; 65 (the boundary case
below) to `l40`. `l21` (the alternate "they said" framing of the
sleep-deprivation answer) and `l30` (Rav Sheshet's "who can guarantee
it will fall to us" aside) each have their own dibbur hamatchil
opened and closed within a single raw print line whose comment
continues on to a later-opened DH; per the same multi-DH rule used
throughout this run, that raw line's vilnaLine target follows the
last-opened DH, so `l21` and `l30` legitimately carry no vilnaLine of
their own, the same pattern already seen for `l19`/`l25`/`l37` in 21b
and `l22` in 21a.

vilnaLine 65, the daf's final truncated word "או" (or), is the same
kind of boundary case as 20b's vilnaLine 62 and 21a's vilnaLine 62:
per the policy, it is linked to `yoma-022a-l40`, 22a's own final
locally captured Gemara line, even though `l40`'s own text (Rav
Pappa's base/ledge question) is itself still open at the point of
truncation and its resolution continues onto 22b.

All 65 entries were fixed across two sub-chunks (vilnaLine 1-33, then
34-65). 22a is fully resolved, 65/65, with real translations
replacing every generic placeholder (including the misattributed
Saul tangent, corrected on 22b below) and every linkedGemaraLineIds
value corrected to its real zero-padded `yoma-022a-lXX` target.

## 22b, full daf (VERSION 15.14), single chunk, closing the Saul/David digression

Continuing the fast alignment run. Before any edit, the 22a/22b
boundary was re-verified read-only: 22a's truncated final word "או"
(or) is completed by 22b's opening "או דילמא" (or perhaps) in both
the Gemara and Rashi columns, continuing Rav Pappa's base/ledge
dilemma cleanly. No edit was made to 22a.

22b's Gemara side has 21 real captured lines (`l01`, `l02`, `l07`,
`l10`, `l14`, `l17`, `l21`, `l25`, `l29`, `l31`, `l34a`, `l34b`,
`l35`, `l36`, `l38`, `l39`, `l41`, `l42`, `l44`, `l47`, `l49`) against
50 raw Gemara print lines, while talmud.dev's raw Rashi array for
this daf has only 35 non-empty print lines - noticeably sparser than
the Gemara side, since Rashi comments lightly on this daf's long
aggadic Saul/David digression, leaving several real lines (`l10`,
`l17`, `l21`, `l25`, `l29`, `l35`, `l36`, `l41`) with no dedicated
comment at all.

Before any translation work, a structural anomaly was found: the
prior enrichment JSON carried 49 `rashiTranslations` entries
(vilnaLine 1-49), but `build_learning_data.py`'s `load_rashi_lines()`
only ever looks up `vilnaLine` values 1 through the talmud.dev raw
array's own length (`vl = i + 1` for `i` in `range(len(rashi_he))`),
so any entry with `vilnaLine` beyond that length is silently
orphaned and never rendered. A spot check of every other daf fixed in
this run (20a, 20b, 21a, 21b, 22a) confirmed all of them have an
exact match between their `rashiTranslations` entry count and their
talmud.dev raw Rashi array length; 22b was the sole exception, with
14 orphaned entries (vilnaLine 36-49) beyond its real 35-line range.
These 14 entries were removed rather than translated, since they can
never render and keeping them would misrepresent the corpus's actual
coverage; this matches the established one-entry-per-real-print-line
convention followed everywhere else in this run.

All 35 raw Rashi print lines were read against the raw Gemara text
and the 21 real captured line ids, using the same multi-DH rule as
prior daf, with particular care taken on two ambiguous spans: (1) the
citation "וְהָיָה מִסְפַּר בְּנֵי יִשְׂרָאֵל כְּחוֹל הַיָּם" appears
verbatim in both `l10` and `l14`, but the comment's own logic
("implying they do have a count") only makes sense as setting up
`l14`'s explicit two-verse contradiction, not `l10`'s plain citation,
so vilnaLine 6 was anchored to `l14`, leaving `l10` uncommented; (2)
the phrase "אפרעו מיניה" (he was punished for it) appears in `l34b`,
`l35`, and `l39`, but the comment's own content ("measure for
measure: he caused [Mefivoshet] to lose his land-inheritance, so he
lost the kingdom's inheritance") only fits `l39`'s Mefivoshet/land
narrative, so vilnaLine 19-20 was anchored to `l39` rather than the
more proximate `l34b`/`l35`. The correspondence: vilnaLine 1 (Rav
Pappa's ramp-and-altar cubits resolved as "let it stand") to `l01`;
2-3 (the prohibition on counting Israel directly, the shard-count
workaround) to `l02`; 4-5 (the lamb-count workaround) to `l07`; 6
(the two-verse contradiction setup) to `l14`; 7-13 (Rav Huna's "one
whose Master assists him" maxim, Saul's one sin versus David's two)
to `l31`; 14-15 (Uriah and the incitement to count Israel) to `l34a`;
16 (the Bat Sheva incident) to `l34b`; 17-18 (the lashon hara about
Mefivoshet) to `l38`; 19-20 (measure for measure: land for kingdom)
to `l39`; 21 (the nightmare that troubled Rav Nachman) to `l42`; 22-26
(no blemish in Saul's family line, the basket of vermin) to `l44`;
27-34 (why Saul was punished, the Nachash Ha'amoni aftermath) to
`l47`; 35 (the boundary case below) to `l49`.

vilnaLine 35, the daf's final truncated word "שאינו" (who does not),
is the same kind of boundary case as the prior daf endings in this
run: per the policy, it is linked to `yoma-022b-l49`, 22b's own final
locally captured Gemara line (the "every Torah scholar" teaching),
even though the DH's own point (the well known teaching that a
scholar does not bear a grudge like a snake) continues onto 23a.

All 35 entries were fixed in a single chunk (under the 40-entry split
threshold). 22b is fully resolved, 35/35 real entries (14 orphaned
entries beyond the real range removed), with real translations
replacing every generic placeholder and every linkedGemaraLineIds
value corrected to its real zero-padded `yoma-022b-lXX` target. This
also resolves the misattribution noted in the 22a section above: the
prior stub's "Saul counted Israel" content genuinely belongs here.

## 23a, full daf (VERSION 15.15), two sub-chunks, the Torah scholar and the snake

Continuing the fast alignment run. Before any edit, the 22b/23a
boundary was re-verified read-only: 22b's truncated final word
"שאינו" (who does not) is completed by 23a's opening "שאינו נוקם
ונוטר כנחש" (who does not take revenge or bear a grudge like a
snake) in both the Gemara and Rashi columns, continuing the "every
Torah scholar" teaching cleanly. No edit was made to 22b. As a
first check specifically motivated by 22b's orphaned-entry surprise,
`len(rashiTranslations)` in the prior JSON (45) was compared against
talmud.dev's non-empty raw Rashi array length (45) before any
translation work began; they matched, so no cleanup was needed here.

23a's Gemara side has 16 real captured lines (`l01`, `l07`, `l11`,
`l15`, `l17`, `l19`, `l24`, `l28`, `l29`, `l30`, `l36`, `l39`, `l42`,
`l45`, `l47`, `l49`) against 52 raw Gemara print lines, and its Rashi
side has 45 raw print lines carrying the same generic
descriptive-style placeholder text as the daf before it.

All 45 raw Rashi print lines were read against the raw Gemara text
and the 16 real captured line ids, using the same multi-DH rule as
prior daf. Two points required particular care: (1) vilnaLine 9
("only one is counted") closes with a phrase that also appears
verbatim at the end of `l19`'s own text ("וְאֵין מוֹנִין לָהֶן אֶלָּא
אַחַת"), not just in the following `l24` challenge that quotes it
again with a different pronoun, so it was anchored to `l19` rather
than assumed to open the next real line's commentary; (2) vilnaLine
18-19 ("the third finger, he is counted... the assumption was [he
would be counted as] two") echoes wording already glossed once at
vilnaLine 12 under `l24`, but its content ("קא סלקא דעתיה", the
Gemara's initial assumption) only matches `l28`'s own question-and-
answer structure ("מַאי מוֹנִין לוֹ" - what does "counted for him"
mean?), so it was anchored to `l28`, a second, distinct comment on
the same Hebrew word rather than a duplicate. The correspondence:
vilnaLine 1-2 (bearing a grudge, distinguished from taking revenge)
to `l07`; 3 (holding it in one's heart) to `l15`; 4-9 (the sick
exception, individuals counted as one) to `l19`; 10-17 (excluding the
third finger and thumb from the count, the officer over the lash-
straps) to `l24`; 18-19 (the count clarification) to `l28`; 20-27
(the pekia strap's construction and etymology) to `l29`; 28-31 (Ben
Beivai, the wick-making) to `l30`; 32-39 (Rabbi Tzadok on the steps
of the portico, whose census the heifer-ritual falls on) to `l39`;
40 (his death shall atone for you) to `l42`; 41-42 (the four cubits'
purpose) to `l47`; 43-45 (the boundary case below) to `l49`. `l01`
(the opening definition, folded into the vilnaLine 1 comment that
ultimately targets `l07`), `l11` (the aggadic "insulted but do not
insult" teaching), `l17` (the rhetorical "extending two, is one even
a question" challenge), `l36` (the two-priests incident's plain
narrative opening), and `l45` (the "which incident came first"
question) all have no dedicated Rashi comment in this daf's column
and legitimately carry no vilnaLine.

vilnaLine 45, the daf's final truncated word "אינה" (she is not), is
the same kind of boundary case as the prior daf endings in this run:
per the policy, it is linked to `yoma-023a-l49`, 23a's own final
locally captured Gemara line (the "ten things said about Jerusalem"
list), even though the specific item this DH names is itself still
open at the point of truncation, continuing onto 23b.

All 45 entries were fixed across two sub-chunks (vilnaLine 1-22, then
23-45). 23a is fully resolved, 45/45, with real translations
replacing every generic placeholder and every linkedGemaraLineIds
value corrected to its real zero-padded `yoma-023a-lXX` target.

## 23b, full daf (VERSION 15.16), two sub-chunks, the garment-changing baraita

Continuing the fast alignment run. Before any edit, the 23a/23b
boundary was re-verified read-only: 23a's truncated final word
"אינה" (she is not) is completed by 23b's opening "אינה מביאה עגלה
ערופה" (she does not bring an axed heifer) in both the Gemara and
Rashi columns, continuing the "ten things said about Jerusalem" list
cleanly. No edit was made to 23a. The entry-count check introduced
after 22b's surprise was run again first: `len(rashiTranslations)`
(65) matched talmud.dev's non-empty raw Rashi array length (65)
before any translation work began.

23b's Gemara side has 15 real captured lines (`l01`, `l03`, `l10`,
`l12`, `l15`, `l18`, `l21`, `l24`, `l27`, `l29`, `l31`, `l34`, `l36`,
`l39`, `l41`) against 46 raw Gemara print lines, and its Rashi side
has 65 raw print lines carrying the same generic descriptive-style
placeholder text as the daf before it.

This daf's Rashi column contains an unusually long, uninterrupted
explanatory passage (vilnaLine 3-24, 22 raw print lines with no
internal DH-closing punctuation) working through the baraita on
changing garments between the tapuach-ash removal and the
outside-the-camp carrying-out. Rather than force artificial breaks,
it was read as one continuous unit and anchored at each place its own
wording most directly echoes a real captured line: vilnaLine 3-6
("thus we read in Torat Kohanim... one might think") to `l12`, since
that phrase is the baraita's own opening premise; vilnaLine 7-24 (the
extended walk through the five daily vestment changes and the tapuach
mechanics) to `l15`, since it explicitly quotes "תלמוד לומר" ("the
verse teaches"), the exact phrase that opens `l15`'s own text, before
elaborating well beyond it. Two shorter multi-DH judgment calls were
also required: vilnaLine 3's own comment on "תלמודא" (matching
`l10`'s "תָּא שְׁמַע... תַּלְמוּדָא") closes before the same raw
line immediately opens the DH that carries the whole entry to `l12`,
so `l10` receives no dedicated vilnaLine; and vilnaLine 53-59 ("he
shall wear, upon his flesh... why is it written") was anchored to
`l34` rather than the more proximate `l31`, since its content
("if you do not say so, why is 'upon his flesh' written") directly
answers `l34`'s own derivation "מֵ״עַל בְּשָׂרוֹ״ נָפְקָא". The
correspondence: vilnaLine 1-2 (Jerusalem was never divided among the
tribes) to `l01`; 3-6 to `l12`; 7-24 to `l15`; 25-34 (why the verse
says "others," lesser garments, the blemished priests) to `l18`;
35-38 (not pouring wine in soiled garments) to `l21`; 39-41 (the
dispute extends to lifting the ash too) to `l24`; 42 (a service valid
with two vessels) to `l27`; 43-46 (the linen tunic and trousers
requirement) to `l29`; 47-52 (why the turban and sash are also
included, the tunic's proper fit) to `l31`; 53-59 (the boundary case
above) to `l34`; 60 (why the trousers verse repeats "upon his flesh")
to `l36`; 61-63 (Rabbi Dosa's four extra garments) to `l39`; 64-65
(the boundary case below) to `l41`. `l03` (the aggadic father-and-
son narrative and the bloodshed-versus-purity dilemma, both already
covered similarly on 23a and not re-glossed here) has no dedicated
Rashi comment in this daf's column and legitimately carries no
vilnaLine.

vilnaLine 65, the daf's final truncated word "לרבות" (to include), is
the same kind of boundary case as the prior daf endings in this run:
per the policy, it is linked to `yoma-023b-l41`, 23b's own final
locally captured Gemara line (Rabbi's second answer about the sash),
even though the DH's own point is itself still open at the point of
truncation, continuing onto 24a.

All 65 entries were fixed across two sub-chunks (vilnaLine 1-34, then
35-65). 23b is fully resolved, 65/65, with real translations
replacing every generic placeholder and every linkedGemaraLineIds
value corrected to its real zero-padded `yoma-023b-lXX` target.

## Major systemic finding: descriptive-style Rashi helper content-to-line mismatches

While reconstructing 10b's real comment boundaries for Batch 1, the same
verification method was applied to two neighboring daf as a spot check:
10a and 11a. Both showed the same failure pattern as 10b did before that
batch: the English helper text describes a plausible-sounding but wrong
topic, usually one that belongs to a different point later in the same
daf, rather than the specific Rashi words actually at that vilnaLine.
The 6 examples first confirmed there (10a vilnaLine 3-4 and 22-23, 11a
vilnaLine 2 and 4) were fixed in Batch 2 above.

10a's remaining rashiTranslations (31 of 35 entries, all besides
vilnaLine 3, 4, 22, 23) were not fixed in either batch - the
mismatch pattern likely affects most or all of the daf, and correcting
it requires the same real-comment reconstruction done for 10b, plus new
historical/geographic research (nation identifications, Rome/Persia
eschatological material) that is out of scope for a "highest confidence,
minimal rewrite" pass. 10b vilnaLine 12-20 (Rava's sukka challenge
resolution and the dirat keva citation from Sukka 7b) have the same
confirmed mismatch pattern and were also left unfixed - Batch 1 stopped
at vilnaLine 11 to stay bounded. 11a's remaining entries (41 of 43, all
besides vilnaLine 2 and 4) were not reviewed.

Scope check: entries whose `en` text starts with "Rashi:" or "Rashi "
(the descriptive-paraphrase style seen in 10a/10b/11a, as opposed to the
direct-translation style used in daf like 5b) appear in 51 of the 173
Yoma daf, spanning roughly 2b-19b and 72a-88a. This is reported as a
scope estimate for the eventual dedicated pass, not a claim that all 51
daf are wrong - only 10a, 10b, and 11a have been directly verified
against their Gemara source so far, and all three showed the mismatch
pattern. The dedicated pass should verify each descriptive-style daf
individually rather than assume the pattern from these three examples.

Update after 12a closed (Batch 11, VERSION 14.78): 12b was checked next
as the natural continuation of the 10a-12a hotspot and does **not**
show the topic-fabrication pattern above. Its 62 `rashiTranslations`
entries are all `en`-text starting with "Rashi:" (so it matched the
scope-check heuristic), but spot-checking against the raw talmud.dev
print lines and the Gemara text shows the translations are
substantively real and on-topic for the daf's actual sugya (the belt
dispute continuing from 12a via Rav Dimi's and Ravin's traditions, the
replacement Cohen Gadol's status, the Yom Kippur-garment mishna). The
problem instead is that the `en` content is **index-misaligned**
against `vilnaLine`: at vilnaLine 3-4 and vilnaLine 45 the content is
shifted by one raw print-line (vilnaLine 3's `en` describes raw line
4's content, etc.); at vilnaLine 20 and vilnaLine 30 the drift is far
larger and non-uniform (18 and 28-30 raw lines ahead respectively,
confirmed by searching for unique terms like "דוסא" and "צרה"/"איבה"
that only occur once in the raw text); by vilnaLine 55-56 the content
is back in correct alignment. This is not a constant offset that a
simple shift-by-N could fix - it looks like the enrichment was
authored against a differently-segmented (likely DH-based, not
print-line-based) breakdown of the same real Rashi content, then
mapped onto `vilnaLine` indices incorrectly, with the misalignment
growing and shrinking unpredictably across the daf. Separately, all 62
entries' `linkedGemaraLineIds` reference unpadded ids (`yoma-12b-l01`
etc.) that do not exist in `learning_data.js`, where the real ids use
zero-padded daf numbers (`yoma-012b-l01`) - a mechanical fix, but not
useful to apply before the content-to-line mapping itself is
corrected, since the ids would still point the (currently
mislocated) content at the wrong Gemara lines.

This is a different failure mode from the topic-fabrication pattern
audited in Batches 1-11 and needs its own diagnosis and reconstruction
approach (full raw-line-by-raw-line remapping of all 62 entries, not
per-line rewording) rather than the established per-entry fix method.
No changes were made to 12b's `rashiTranslations` in this pass -
this is a documented, deferred finding pending guidance on how to
proceed.

## Major systemic finding: placeholder/generic filler text on 77a-88a

Separately from the mismatch pattern above, 765 `rashiTranslations`
entries across 23 daf (77a through 88a, the last portion of the
tractate) use one of a small number of generic filler strings instead
of any translation or explanation of the specific Rashi text:

- "Rashi clarifies the ruling and its application." - 279 entries
- "Rashi elaborates on the halachic details of this sugya." - 271 entries
- "Rashi explains the opening discussion of this topic on `<daf>`." - 143 entries (varies by daf)
- A handful of other short, non-specific fillers ("And then.", "End of
  Rashi on 54a.", "Commentary on the transition to 24a.")

None of these strings reference the actual Hebrew content of their
vilnaLine; the same filler is reused verbatim across many consecutive,
unrelated Rashi comments (confirmed via exact-string duplicate scan
across all 173 daf). This is categorically different from the
mismatch-pattern finding above (fabricated-but-plausible wrong content)
- these are stub placeholders with no content at all. `validate:rashi:yoma`
passes on all of them because the structural gate only checks that `en`
is non-empty when `he` is present; it does not check translation
quality. This needs its own dedicated pass (likely a systematic
per-line translation effort similar to the `en_lit` literal-translation
pipeline) rather than manual one-off editing, given the scale (765
lines, 23 daf).

## Entry format

| daf | line/sugya | visible Rashi text | current helper translation | why it may be misaligned | suggested correction | severity |
|---|---|---|---|---|---|---|
| | | | | | | |
