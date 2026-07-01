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

As of VERSION 14.65: schema backfill is complete, the perek-level semantic
review is complete, crosswired and duplicated scaffold fixes are
complete, `takeaway.type` normalization is complete, and the 45a
source-review issue is resolved (see `docs/yoma-completion-report.md` for
the full phase-by-phase record). `validate:rashi:yoma` has passed
throughout every one of those passes, confirming structural integrity was
never disturbed.

One non-Rashi Gemara-learning follow-up remains documented and open:
5a/yoma-005a-s02 needs new authored content for its ahaMoment (a distinct
category from the crosswire/scaffold fixes above - it requires judgment
about what to write, not a mechanical field swap). See
`docs/yoma-perek-review.md` and `docs/yoma-completion-report.md` for
details.

Rashi is the next planned area of work but has not started. No dedicated
Rashi content-quality or nekudot audit pass has been run against any
batch. No entries below. This note remains the place to log findings if
and when that pass happens; see `docs/tractate-build-process.md` Section
9 for how to prepare for it.

## Entry format

| daf | line/sugya | visible Rashi text | current helper translation | why it may be misaligned | suggested correction | severity |
|---|---|---|---|---|---|---|
| | | | | | | |
