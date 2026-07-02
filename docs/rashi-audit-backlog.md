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

As of VERSION 14.76: schema backfill is complete, the perek-level semantic
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
from 11b's truncated final word; 12a vilnaLine 17-66, a separate Kohen
Gadol investiture sugya, remains open for a future batch. The
descriptive-style systemic finding is still open beyond the lines fixed
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
