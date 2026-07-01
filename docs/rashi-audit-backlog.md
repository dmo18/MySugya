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
(see the Pilot findings table below). Both entries were fixed. This was
a small, explicitly scoped pilot, not the dedicated Rashi content-quality
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

## Entry format

| daf | line/sugya | visible Rashi text | current helper translation | why it may be misaligned | suggested correction | severity |
|---|---|---|---|---|---|---|
| | | | | | | |
