# Yoma pilot lessons: why the worker pipeline exists

A concise case study of the failures that shaped the pipeline. Full
forensic detail: docs/rashi-audit-backlog.md.

## What went wrong originally

Placeholder and non-faithful Rashi helper text reached main on three
separate occasions (the 44a-46b batch, the 61a/67b-71b stubs, the
77a-88a filler; 839 scaffold lines at peak) because the validation
stack checked structure only: any non-empty English string passed every
gate. A recovery pass then found that even entries that LOOKED specific
were fabricated (44a described garment counts while the Hebrew discussed
courtyard exclusion), that English could drift lines away from its
Hebrew (the 12b and 41a shifted blocks), and that 117 link ids pointed
at Gemara lines that did not exist. Parallel PRs off one base amplified
everything: repeated VERSION/generated-file conflicts and CI
cancellations trained attention onto CI state instead of content state.

## What each gate now catches

- Content gate (validate:rashi:content:yoma): placeholder patterns,
  scaffold templates, filler strings, dashes, count mismatches. Catches
  what let all three incidents through.
- Link gate (validate:rashi:links:yoma): nonexistent and cross-daf
  linkedGemaraLineIds. Links are data wiring for future consumers; bad
  ids are silent corruption because the app does not read them yet.
- Freshness gate (check:generated:yoma): hand edits to generated files
  and source edits without regeneration. Generated files must be a pure
  function of sources or every other gate can be bypassed by editing
  output directly.
- Repetition gate (validate:rashi:dupes:yoma): a genuine translation
  almost never repeats within a daf; scaffold text always does.
- Scope gates (check:rashi-pr-scope:yoma + worker jsonScope engine):
  bound every PR to its manifest's files and JSON paths with exact
  pointer errors. Scope creep, not malice, caused most historical
  damage.
- Allowlist ratchet: baselines only shrink; a worker can never make a
  red gate green by widening the baseline.

## What cannot be automated

Semantic faithfulness. A fluent, specific, wrong translation passes
every pattern gate; the advisory semantic audit
(audit:rashi:semantic:yoma) flags citation-anchor displacement (it
independently re-found the 41a shift) but proves nothing. Therefore:
Hebrew judgment stays with Fable/Sonnet, risky task types carry a
mandatory Fable review before merge, and spot audits remain part of
every content campaign.

## The transferable lesson

Build the packets, gates, and manifests BEFORE the content work, not
after the third incident. For any new tractate: no content pass begins
until the module's validators are wired into CI, the schema paths are
classified and owned, the first dry runs are green, and the worker
prompts are generated rather than hand-written. See
docs/new-tractate-onboarding.md.
