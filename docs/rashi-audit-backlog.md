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

As of VERSION 14.67: schema backfill is complete, the perek-level semantic
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
systemic findings, documented further down, that are explicitly NOT
resolved by Batch 1 and need a dedicated pass of their own. This is
still small, explicitly scoped work, not the dedicated Rashi
content-quality audit described in the Scope note above. Rashi
content-quality auditing of the remaining corpus and the
nekudot/vowelization audit have not started.

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

## Major systemic finding: descriptive-style Rashi helper content-to-line mismatches

While reconstructing 10b's real comment boundaries for Batch 1, the same
verification method was applied to two neighboring daf as a spot check:
10a and 11a. Both showed the same failure pattern as 10b did before this
batch: the English helper text describes a plausible-sounding but wrong
topic, usually one that belongs to a different point later in the same
daf, rather than the specific Rashi words actually at that vilnaLine.
Confirmed examples (Hebrew/Gemara-checked, not fixed, out of scope for
this batch):

- 10a vilnaLine 3-4: Hebrew is Rav Yosef's geographic identification of
  "Sakistan" (inner/outer), linked to Gemara line `yoma-010a-l10`
  ("Sabtah and Raamah and Sabteca"). Prior text describes "tents of
  Shem" / "study halls and synagogues descended from Shem's lineage,"
  a topic from a different, earlier comment entirely.
- 10a vilnaLine 22-23: Hebrew is R. Yehuda's question about Temple
  chambers used as guard residences, matching Gemara line
  `yoma-010a-l41`/`l42`. Prior text describes "what it means for Rome
  to 'rule the whole world' as a precondition for Mashiach," a topic
  from several comments earlier.
- 11a vilnaLine 2: Hebrew describes a province ("medina") surrounded by
  mountains and forests, reachable only through gates. Prior text
  fabricates "a fully walled city with proper entrance gates through
  which residents pass daily" - details not present in the Hebrew.
- 11a vilnaLine 4: Hebrew is a place-name gloss ("Akra de-Kuvei," an
  arch-built structure). Prior text describes "the question of which
  tanna authored the Temple-gates baraita," a topic from later in the
  daf (near Gemara line `yoma-011a-l03`).

10a's rashiTranslations (35 entries) were not fixed in this batch - the
mismatch pattern likely affects most or all of the daf, and correcting
it requires the same real-comment reconstruction done for 10b, plus new
historical/geographic research (nation identifications, Rome/Persia
eschatological material) that is out of scope for a "highest confidence,
minimal rewrite" pass. 10b vilnaLine 12-20 (Rava's sukka challenge
resolution and the dirat keva citation from Sukka 7b) have the same
confirmed mismatch pattern and were also left unfixed - Batch 1 stopped
at vilnaLine 11 to stay bounded. 11a was spot-checked only (2 of 43
entries); the rest were not reviewed.

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
