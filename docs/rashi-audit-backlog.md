# Rashi audit backlog

> Current repository-wide status: `docs/reports/open-items.md`.

Read-only tracking note for suspected Rashi helper-translation misalignments
found incidentally while doing other work. This is not a Rashi validation
report; `validate:rashi:yoma` already checks structural alignment (he order/
count, en+enSource presence, no leak into Gemara). This note is for
translation-quality or content-alignment concerns that the structural
validator cannot catch.

Do not act on entries here without an explicit Rashi pass. Do not edit
`modules/yoma/` Rashi content based on this note alone.

## CURRENT STATUS: scaffold-fabrication remediation (live, machine-generated)

The summary and table immediately below are regenerated from live
repository truth by `modules/yoma/scripts/generate_rashi_docs.py` (source:
the committed scaffold-debt baseline, current `rashiTranslations` counts,
and the curated task-type map). Do not hand-edit either region; regenerate
with `python3 scripts/generate_rashi_docs.py` and the freshness gate
(`npm run check:rashi-docs:yoma`) will fail the build if this doc drifts
from the baseline.

<!-- rashi-status-summary:begin (regenerate with `python3 scripts/generate_rashi_docs.py`; do not hand-edit) -->
- Current VERSION: 15.374
- Generated from commit: 6df20cb (the commit this doc was generated from, necessarily pre-merge for the PR that carries this change; it will differ from live main's HEAD immediately after that PR merges by design, since a PR's own merge commit does not exist yet at generation time. Not a staleness signal; see the freshness gate for what actually indicates staleness.)
- Total scaffold-debt entries (all rules, current inventory): 0
- Unique affected daf: 0
- Tracked daf in status table: 93 (93 resolved, 0 open)
- Current next reconstruction target: none - all tracked daf resolved
- Rule families: scaffold-prefix / line-number-scaffold / hebrew-passthrough (the original "Rashi: opens ..." family) and plain-meta-scaffold (the same translator-position narration without the literal word "Rashi": "Opens 'X':", "continuing:", "closing:", "Then opens").
- Historical narrative sections below ("Batch N findings", per-daf "resolved" write-ups) are preserved as historical fact; they do NOT reflect current status. The table above and this summary are the only current-truth sections.
<!-- rashi-status-summary:end -->

Context on the two rule families tracked in the table:

- The original family (`scaffold-prefix`, `line-number-scaffold`,
  `hebrew-passthrough`) is meta-narration that names "Rashi" explicitly
  ("Rashi: opens/continues/concludes ..."), bracket-guessed editorial
  completions, line-number placeholders, or untranslated Hebrew passthrough.
- The `plain-meta-scaffold` family is the same translator-position
  narration defect with the literal word "Rashi" dropped ("Opens 'X':",
  "continuing:", "closing:", "Then opens 'Y':"). It was found via a
  corpus-wide forensic audit after the original detector's literal "Rashi"
  anchor was found not to catch it; see the "Batch N findings" history
  below for how this was discovered.
- The "Batch N resolved" narratives in this file are historical notes, NOT
  proof of current semantic correctness. Repository history was squashed
  (this entire file entered git in a single commit), so those claims cannot
  be verified against commits; treat them as historical fact only. The
  table above and the summary above are the only current-truth sections.
- The machine-generated debt inventory
  (`modules/yoma/scripts/baselines/rashi_scaffold_debt.json`) is the
  current source of truth for what remains open; it shrinks (and may only
  shrink) as daf are repaired. `rashi_content_allowlist.json` remains at
  zero entries and is unaffected.
- The paused nekudot/vowelization audit (Scope note below) is a separate
  concern and remains paused; nothing in the scaffold remediation touches
  it.

### Machine-generated scaffold status by daf

<!-- scaffold-status-table:begin (regenerate with `python3 scripts/generate_rashi_docs.py`; do not hand-edit rows) -->
| daf | contaminated | total | severity | task recommendation | status | last verified |
| --- | --- | --- | --- | --- | --- | --- |
| 2b | 0 | 29 | 0% | rashi-repair (after fresh semantic verification) | resolved | 6df20cb |
| 3a | 0 | 38 | 0% | rashi-repair (after fresh semantic verification) | resolved | 6df20cb |
| 3b | 0 | 49 | 0% | rashi-reconstruction | resolved | 6df20cb |
| 4a | 0 | 56 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 7b | 0 | 18 | 0% | rashi-repair (after fresh semantic verification) | resolved | 6df20cb |
| 10a | 0 | 35 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 10b | 0 | 21 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 11a | 0 | 43 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 11b | 0 | 39 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 12a | 0 | 66 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 12b | 0 | 62 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 13a | 0 | 29 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 13b | 0 | 28 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 14a | 0 | 58 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 14b | 0 | 59 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 15a | 0 | 66 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 15b | 0 | 66 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 16a | 0 | 61 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 16b | 0 | 62 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 17a | 0 | 45 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 17b | 0 | 33 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 18a | 0 | 58 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 18b | 0 | 34 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 19a | 0 | 58 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 19b | 0 | 68 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 20a | 0 | 41 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 20b | 0 | 62 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 21a | 0 | 62 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 21b | 0 | 46 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 22a | 0 | 65 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 22b | 0 | 35 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 23a | 0 | 45 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 23b | 0 | 65 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 24a | 0 | 47 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 24b | 0 | 65 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 25a | 0 | 61 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 25b | 0 | 62 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 26a | 0 | 42 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 26b | 0 | 61 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 27a | 0 | 53 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 27b | 0 | 44 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 28a | 0 | 45 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 28b | 0 | 79 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 29a | 0 | 56 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 29b | 0 | 54 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 30a | 0 | 54 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 30b | 0 | 51 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 31a | 0 | 37 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 31b | 0 | 63 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 32a | 0 | 62 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 32b | 0 | 55 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 33a | 0 | 64 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 33b | 0 | 60 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 34a | 0 | 46 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 34b | 0 | 40 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 35a | 0 | 14 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 35b | 0 | 58 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 36a | 0 | 54 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 36b | 0 | 62 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 37a | 0 | 71 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 37b | 0 | 25 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 38a | 0 | 37 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 38b | 0 | 49 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 39a | 0 | 59 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 39b | 0 | 65 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 40a | 0 | 65 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 40b | 0 | 43 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 41b | 0 | 74 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 42a | 0 | 52 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 42b | 0 | 60 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 43a | 0 | 65 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 43b | 0 | 59 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 44a | 0 | 60 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 44b | 0 | 60 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 45a | 0 | 44 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 45b | 0 | 29 | 0% | rashi-repair (after fresh semantic verification) | resolved | 6df20cb |
| 46a | 0 | 32 | 0% | rashi-repair (after fresh semantic verification) | resolved | 6df20cb |
| 47a | 0 | 64 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 47b | 0 | 65 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 48a | 0 | 42 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 48b | 0 | 26 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 49a | 0 | 64 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 49b | 0 | 21 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 72a | 0 | 31 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 72b | 0 | 100 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 73a | 0 | 65 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 73b | 0 | 58 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 74a | 0 | 55 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 74b | 0 | 42 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 75a | 0 | 49 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 75b | 0 | 46 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 76a | 0 | 47 | 0% | none (repaired and verified) | resolved | 6df20cb |
| 76b | 0 | 44 | 0% | none (repaired and verified) | resolved | 6df20cb |
<!-- scaffold-status-table:end -->

The remediation campaign runs one daf per PR (order and per-batch bounds in
the audit report). A daf moves to repaired when its PR merges with the
scaffold gate green and its baseline entries retired.

## Linked-renderer closure status (VERSION 15.337)

Current, verified state of the `linkedGemaraLineIds` association layer and
the linked-Rashi-renderer readiness gate. Full detail, mechanism
descriptions, and the historical PR-introduction snapshot are in
`docs/reports/rashi-association-audit.md` (see its own "Current closure
status" section, added at the same time as this one); this is the short
version for backlog tracking.

- **8,854** `rashiTranslations`/`rashiLines` entries across all 173 daf.
- **10,047** declared associations: 7,648 single-link, 1,186 multi-link,
  279 Mishnah targets, 447 suffixed-id targets, 0 sparse, 20 boundary
  (empty-link), **0 broken, 0 cross-daf** - confirmed by
  `audit_rashi_association.py --exhaustive-corpus`.
- 7a and 9b Rashi corrections are complete (PR #326: 7a realignment, 53
  entries; PR #327: 9b full reconstruction, 41 entries).
- All 20 boundary (empty-link) entries (4b L61; 61a L46-64) are recorded
  in `modules/yoma/scripts/allowlists/rashi_boundary_authorizations.json`
  and pass `validate_rashi_boundary_authorizations.py` - each is a Rashi
  comment whose underlying Gemara content is truncated at the daf's own
  final line and completes on the next daf, where cross-daf linking is
  prohibited. Ratchet: 20/20.
- Semantic-link drift audit (`audit_rashi_semantic.py --profile`): 0 daf
  classified SHIFTED or FABRICATION-SUSPECT, 0 daf with a recommended
  repair task. 14 advisory-only findings remain on otherwise-ALIGNED (or
  INSUFFICIENT-ANCHORS) daf - never suppressed, always reported in full
  by the readiness gate - including the original 2a (L3 offset -1 citing
  12b; L19 missing anchor for 69b) and 4b (L44 offset -1, Bamidbar) finds.
- An automated sharded browser-association workflow
  (`.github/workflows/rashi-browser-shards.yml`) covers all 173 daf across
  8 shards, with a combiner that stamps the result with commit SHA and CI
  provenance. It first ran against commit `d1e4715` as workflow run
  `30399334278`, producing artifact `rashi-browser-shard-result` (id
  `8704117259`): 8 shards, 173/173 daf, 8,854 entries, 183 passed, 0
  failed.
- Renderer readiness (`npm run audit:rashi-renderer-readiness:yoma`):
  **8/8** with that artifact supplied.
- **Cutover done at VERSION 15.338**: the linked renderer is now the
  production default. `?rashiAssoc=legacy` is a temporary rollback
  override onto the preserved legacy vilnaLine renderer (not deleted);
  `?rashiAssoc=linked` is still accepted but no longer required; unknown
  values resolve to linked. The 20 authorized boundary entries remain
  intentionally unrendered. See `docs/reports/rashi-association-audit.md`.
- Unrelated to this closure: a daf-24b comparison against the live
  Sefaria API found only a benign Unicode combining-mark ordering
  difference from the local talmud.dev-based text (no content
  divergence); and `mysugya.com` (Cloudways) was observed serving an
  older bundle than the current, authoritative GitHub Pages deployment -
  see CLAUDE.md's URL policy note. Neither is Rashi-association work and
  neither is touched by it.

## Scope note

A dedicated Rashi content-quality audit pass (translation accuracy and
mischaracterization, beyond the completed scaffold-fabrication campaign
above) is now IN PROGRESS. See "Content-quality audit coverage" below
for the git-history-grounded coverage map and findings.

The nekudot/vowelization correctness audit of the `he:` fields (which
the structural validator `validate:rashi:yoma` does not check - it only
checks alignment: he order/count vs. Vilna, en+enSource presence, no
leak into Gemara) remains a separate, not-yet-started pass.

## Content-quality audit coverage (as of VERSION 15.293)

Coverage map built directly from git commit history (searching `main`
for reconstruction/realignment/repair/recovery commit messages per
daf), not from the machine-generated scaffold-status table above: once
a daf's scaffold-debt count hits zero its task recommendation always
reads "none (repaired and verified)" whether that's because it was
actually reconstructed or because it was simply never scaffold-
contaminated to begin with, so that table cannot answer "was this
daf's content ever verified." Git history can.

**132 of 173 daf** have at least one genuine reconstruction,
realignment, structural-repair, or recovery commit and are considered
content-audited. **41 daf never had any such pass**: 2a; 3b-9b (3b, 4a,
7b now separately covered by the scaffold campaign, see below; 4b, 5a,
5b, 6a, 6b, 7a, 8b, 9b remained gap); 41b-43b were separately covered
by the scaffold campaign; 53a-60b (16 daf); 61b-67a (12 daf); 69a-69b;
70b-71a. (3b and 7b were reconstructed by the scaffold campaign
immediately prior to this audit and are excluded from the gap count
below; the remaining 39-daf gap is what was actually audited.)

### Wave 1 audit (this pass, 41 daf assigned in 5 batches)

Method: for each daf, cross-reference every `rashiTranslations[].en`
against its real Rashi Hebrew (`assets/talmuddev/<daf>.json`'s `rashi`
array, confirmed to match Sefaria's Vilna edition) at the matching
`vilnaLine`. Fix only high-confidence, narrow, isolated errors
(citation mistakes, single-clause fabrications). Log anything systemic
or ambiguous rather than attempting a partial fix that would misrepresent
the daf's true state.

**Result: this was not a light spot-check.** Two daf had one narrow,
fixable error each (see table below). The other 39 daf split into three
severity tiers, all requiring the same heavier remediation the scaffold
campaign used elsewhere in the corpus - none are fixable by narrow
content edits:

| Tier | Daf | Count | What's wrong |
|---|---|---|---|
| Fixed | 2a, 54a | 2 | One fabricated clause (2a L55) and one wrong verse citation (54a L1), both narrow single-line fixes. |
| Clean / minor | 4b, 7a, 8b, 9b, 56a | 5 | No genuine errors found, or only low-confidence notes logged (not acted on). |
| Needs reconstruction | 53a, 53b, 54b, 55a (tail), 55b (tail), 56b (tail), 57a, 57b, 58a, 58b, 59a, 59b, 60a, 60b, 61b, 62a, 62b, 63a, 64a, 64b, 65a, 65b, 66a, 66b, 6b | ~25 | `en` text is generic essay-style filler or wholesale fabrication unrelated to its own line's Hebrew (the same severity as the scaffold campaign's targets, but without the literal "Rashi: opens/continues" marker phrases the scaffold detector looks for, so it was never flagged). 65a/65b/66a/66b additionally have no `he` field at all (unbuilt). 6b has cross-daf content duplicated in from 7a. |
| Needs realignment | 5a, 5b, 6a, 67a, 69a, 69b, 70b, 71a, 63b (partial) | ~9 | `he` is present and correctly ordered, but `en` systematically translates an adjacent line's Hebrew instead of its own (the same drift pattern already fixed for these daf's siblings 67b/68a/68b/70a/71b). |

Full per-daf findings tables with excerpts are preserved in the PRs
that reported this wave (see PR history); this section is the durable
summary. The 2 narrow fixes (2a, 54a) are merged separately from this
documentation update.

**Recommendation**: the ~25 reconstruction-tier and ~9 realignment-tier
daf need the same one-daf-per-PR worker pipeline used for the scaffold
campaign (`rashi-reconstruction` / `rashi-realignment` task types).
This is comparable in scale to a meaningful fraction of that campaign
and has not yet been started as of this writing.

## Status

As of VERSION 15.28: schema backfill is complete, the perek-level semantic
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
captured lines it echoes rather than forcing artificial breaks. At
VERSION 15.17 (see "24a, full daf" below) the run continued to the
four-capital-services sugya, confirming the 23b/24a boundary is
clean and fixing all 47 of 24a's entries in two sub-chunks (47/47
resolved). At VERSION 15.18 (see "24b, full daf" below) the run
closed out at the bounded 21a-24b endpoint, confirming the 24a/24b
boundary is clean, confirming 24b's own final line ends mid-word
rather than at a perek close, and fixing all 65 of 24b's entries in
two sub-chunks (65/65 resolved). This completed the bounded fast
alignment run: 8 daf (21a-24b), 430 entries fixed, no daf deferred. A
second bounded run resumed at VERSION 15.19 (see "25a, full daf"
below), covering 25a-28b; the mandatory raw-count preflight check
(introduced after 22b's orphaned-entry surprise) was run before any
edit and matched cleanly (61/61), and all 61 of 25a's entries were
fixed in a single list-indexed pass after two prior daf (23a, 23b) in
the first run had shown manually-typed dictionary keys drift by one
position at DH boundaries. No
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

## 24a, full daf (VERSION 15.17), two sub-chunks, the four capital services

Continuing the fast alignment run. Before any edit, the 23b/24a
boundary was re-verified read-only: 23b's truncated final word
"לרבות" (to include) is completed by 24a's opening "לרבות את
השחקים" (to include the worn ones) in both the Gemara and Rashi
columns, continuing Rabbi's second answer about the sash cleanly. No
edit was made to 23b. The entry-count check was run again first:
`len(rashiTranslations)` (47) matched talmud.dev's non-empty raw
Rashi array length (47) before any translation work began.

24a's Gemara side has 10 real captured lines (`l01a`, `l01b`, `l04`,
`l06`, `l08`, `l13`, `l16`, `l22`, `l25`, `l26`; `l01a` and `l01b`
share the same `vilna_line` since two adjacent Gemara statements were
grouped under one Vilna line stamp) against 30 raw Gemara print
lines, and its Rashi side has 47 raw print lines carrying the same
generic descriptive-style placeholder text as the daf before it.

All 47 raw Rashi print lines were read against the raw Gemara text
and the 10 real captured line ids, using the same multi-DH rule as
prior daf. The correspondence: vilnaLine 1-2 (the worn garments are
still valid, cross-referencing Zevachim) to `l01a`; 3-6 (Rabbi Yehuda
and Rabbi Dosa's dispute over whether donning the turban and sash is
itself a service) to `l04`; 7-13 (why a verse was needed to include
the Yom Kippur garments) to `l06`; 14-24 (deriving the ash-removal's
minimum handful from the tithe-offering or the Midianite tribute) to
`l08`; 25-26 (the four services carrying capital liability for a
non-priest) to `l13`; 27-38 (the verse's own exclusions: a gift-
service, not a removal-service; a complete service, not one followed
by another) to `l16`; 39-43 (the inner sprinklings and the leper's
oil, included via "any matter of the altar") to `l22`; 44-46 (Levi's
alternate derivation from the doubled "matter") to `l25`; 47 (the
boundary case below) to `l26`. `l01b` (Rabbi Dosa's ruling that the
worn garments are fit for an ordinary priest, sharing `l01a`'s Vilna
line) has no separately dedicated vilnaLine, since the single raw
Rashi comment spanning vilnaLine 1-2 stays anchored at its own
opening DH rather than splitting mid-comment; this is the same
pattern already documented for co-located real lines elsewhere in
this run.

vilnaLine 47, the daf's final truncated word "ולמבית" (and to
inside), is the same kind of boundary case as the prior daf endings
in this run: per the policy, it is linked to `yoma-024a-l26`, 24a's
own final locally captured Gemara line (Levi's derivation via "any
matter"), even though the DH's own point is itself still open at the
point of truncation, continuing onto 24b.

All 47 entries were fixed across two sub-chunks (vilnaLine 1-24, then
25-47). 24a is fully resolved, 47/47, with real translations
replacing every generic placeholder and every linkedGemaraLineIds
value corrected to its real zero-padded `yoma-024a-lXX` target.

## 24b, full daf (VERSION 15.18), two sub-chunks, closing the fast alignment run at 21a-24b

Continuing and closing out the bounded fast alignment run. Before any
edit, the 24a/24b boundary was re-verified read-only: 24a's truncated
final word "ולמבית" (and to inside) is completed by 24b's opening
"ולמבית לפרוכת" (and to inside the curtain) in both the Gemara and
Rashi columns, continuing Levi's derivation of the inner sprinklings
cleanly. No edit was made to 24a. The entry-count check was run again
first: `len(rashiTranslations)` (65) matched talmud.dev's non-empty
raw Rashi array length (65) before any translation work began. 24b's
own final Gemara line ends mid-word ("מַאי") rather than with a
Hadran formula, confirming this is a standard truncation boundary,
not a perek close (Yoma's Perek 2 continues past 24b).

24b's Gemara side has 18 real captured lines (`l01`, `l03`, `l06`,
`l07`, `l09a`, `l09b`, `l12`, `l14`, `l15`, `l20`, `l23`, `l26`,
`l31`, `l35`, `l37`, `l39`, `l41`, `l43`; `l09a`/`l09b` share one
Vilna line, the same pattern already seen at `l01a`/`l01b` on 24a)
against 45 raw Gemara print lines, and its Rashi side has 65 raw
print lines carrying the same generic descriptive-style placeholder
text as the daf before it.

All 65 raw Rashi print lines were read against the raw Gemara text
and the 18 real captured line ids, using the same multi-DH rule as
prior daf. The correspondence: vilnaLine 1-4 (the gift-service inside
the curtain) to `l01`; 5-8 (the complete-service reading of the same
verse) to `l03`; 9-13 (why the verse repeats "and he shall serve")
to `l06`; 14-15 (a removal-service in the Sanctuary itself) to `l07`;
16-19 (why the verse writes "and to inside" rather than "inside")
to `l09a`; 20-28 (the "if so" challenges: the showbread, the dishes,
the ash-pan) to `l09b`; 29-32 (arranging the candelabrum) to `l12`;
33-41 (kindling the tinder, the priestly garments required) to `l15`;
42-46 (arranging the wood-pile and the two logs) to `l20`; 47-52
(Rav and Rabbi Yochanan's dispute over whether arranging the two logs
is a complete service) to `l23`; 53-59 (the specific capital-liability
services: sprinkling, the bird offerings, the libations) to `l26`;
60-61 (the boundary case for the lottery's four daily rounds) to
`l35`; 62 (why they gather with noise) to `l37`; 63 (which garments
for the lottery) to `l39`; 64-65 (the boundary case below, the
attendants who received the priests' garments) to `l43`. `l14` (the
straightforward "lighting is not itself a service" clause), `l31`
(Levi's own baraita enumerating the capital-liability services, whose
own DH gets folded into the following comment by the multi-DH rule),
and `l41` (Rav Nachman and Rav Sheshet's dueling justifications for
their own view, likewise folded into the DH that follows) all have
no dedicated vilnaLine of their own in this daf's column, the same
established folding pattern seen throughout this run.

vilnaLine 65, the daf's final truncated word "שלא" (that not), is
the same kind of boundary case as every other daf ending in this
run: per the policy, it is linked to `yoma-024b-l43`, 24b's own final
locally captured Gemara line (the account of stripping the
attendants of their garments), even though the DH's own point is
itself still open at the point of truncation, continuing onto 25a.

All 65 entries were fixed across two sub-chunks (vilnaLine 1-32, then
33-65). 24b is fully resolved, 65/65, with real translations
replacing every generic placeholder and every linkedGemaraLineIds
value corrected to its real zero-padded `yoma-024b-lXX` target.

This closes the bounded fast Rashi alignment run covering 21a through
24b (8 daf: 21a, 21b, 22a, 22b, 23a, 23b, 24a, 24b), fixing 430
entries total (62 + 46 + 65 + 35 + 45 + 65 + 47 + 65, after 22b's 14
orphaned entries were removed rather than counted). No daf in this
range was deferred. The run also produced two corpus-quality
findings applicable beyond this range: the orphaned-entries anomaly
(only 22b, now documented as a check to run before every future daf)
and the one-daf-early misattribution of real content (22a's stub
carrying 22b's own Saul/David material, the same pattern already on
record for 11b/12a).

## 25a, full daf (VERSION 15.19), two sub-chunks, resuming the run at 25a-28b

Resuming the fast alignment run into new territory (25a-28b). Before
any edit, the 24b/25a boundary was re-verified read-only: 24b's
truncated final word "שלא" (that not) is completed by 25a's opening
"שלא זכו לפייס" (who did not win the lottery) in both the Gemara and
Rashi columns, continuing the account of stripping the attendants of
their garments cleanly. No edit was made to 24b. The mandatory
preflight raw-count check was run first: talmud.dev's non-empty raw
Rashi array for 25a has 61 lines, and the prior enrichment JSON's
`rashiTranslations` also had 61 entries - an exact match, so no
orphaned-entry cleanup was needed here, and no sign of one-daf-early
content misattribution was found on inspection of the prior stub
text.

25a's Gemara side has 12 real captured lines (`l01`, `l03`, `l07`,
`l10`, `l17`, `l19`, `l25`, `l28`, `l35` [mishna], `l37`, `l40`,
`l42`) against 49 raw Gemara print lines, and its Rashi side has 61
raw print lines carrying the same generic descriptive-style
placeholder text as the daf before it. This daf also crosses a
mishna/gemara boundary mid-page (the second lottery's Mishna opens at
`l35`), the first mishna transition encountered mid-daf in this
resumed run; Rashi's own comment on the Mishna's opening word ("מִי
שׁוֹחֵט" - who slaughters) was handled the same as any other DH,
confirming the multi-DH rule applies uniformly across the
mishna/gemara boundary.

All 61 raw Rashi print lines were read against the raw Gemara text
and the 12 real captured line ids, using the same multi-DH rule as
prior daf. Given repeated indexing slips on the previous two daf in
this run (23a, 23b) from manually typed dictionary keys, this daf's
fix was built differently: translations were written as an ordered
list matching talmud.dev's raw array position for position, with
`vilnaLine` derived automatically from list index rather than typed
by hand, and cross-checked against the raw text at each of the
daf's DH-boundary lines before being applied. The correspondence:
vilnaLine 1-4 (the ordinary-garment stripping, resolved by the
baraita on trouser priority) to `l03`; 5-6 (dressing them in sacred
trousers so they would not stand naked) to `l07`; 7-14 (the Chamber
of Hewn Stone's layout, the lottery's circular gathering) to `l10`;
15-20 (the priest whose mother made him a fine tunic) to `l17`; 21-26
(no sitting in the Temple courtyard except for the House of David) to
`l19`; 27-28 (the lottery must occur in the house of God) to `l25`;
29 (the second lottery's Mishna opening) to `l35`; 30-48 (the
thirteen priestly roles enumerated by the Mishna, including the
libation and meal-offering portions) to `l37`; 49 (the daily-offering
was slaughtered in the order it would walk) to `l40`; 50-61 (the
Gemara's own question of whether the lottery repeats per service)
to `l42`. `l01` (the Gemara's own opening question, folded into the
vilnaLine 1 comment that ultimately targets `l03`) and `l28` (the
follow-up "if it had one entrance" hypothesis, superseded before any
dedicated comment addresses it) have no dedicated vilnaLine of their
own, the same established folding pattern seen throughout this run.

vilnaLine 61, the daf's final truncated word "לא" (no), is the same
kind of boundary case as every other daf ending in this run: per the
policy, it is linked to `yoma-025a-l42`, 25a's own final locally
captured Gemara line (the Gemara's own question about lottery
frequency), even though the DH's own point is itself still open at
the point of truncation, continuing onto 25b.

All 61 entries were fixed in a single list-indexed pass (the switch
away from manually keyed sub-chunks was itself the fix for the
indexing slips noted above). 25a is fully resolved, 61/61, with real
translations replacing every generic placeholder and every
linkedGemaraLineIds value corrected to its real zero-padded
`yoma-025a-lXX` target.

## 25b, full daf (VERSION 15.20)

Continuing the resumed run. Before any edit, the 25a/25b boundary was
re-verified read-only: 25a's truncated final word "לא" (no) is
completed by 25b's opening "תא שמע רבי יהודה אומר לא היה פייס למחתה"
in both the Gemara and Rashi columns, continuing the Gemara's own
question about lottery frequency cleanly. No edit was made to 25a.
The mandatory preflight raw-count check was run first: talmud.dev's
non-empty raw Rashi array for 25b has 62 lines, and the prior
enrichment JSON's `rashiTranslations` also had 62 entries, an exact
match, so no orphaned-entry cleanup was needed here, and no sign of
one-daf-early content misattribution was found on inspection of the
prior stub text.

25b's Gemara side has 16 real captured lines (`l01`, `l03`, `l04`,
`l06`, `l08`, `l11`, `l14`, `l15`, `l18`, `l20`, `l23`, `l28`, `l34`,
`l35`, `l38`, `l40`) against 44 raw Gemara print lines, and its Rashi
side has 62 raw print lines carrying the same generic descriptive-
style placeholder text as the daf before it.

All 62 raw Rashi print lines were read against the raw Gemara text
and the 16 real captured line ids, using the same multi-DH rule as
prior daf, continuing the list-indexed methodology adopted at 25a
(translations written as an ordered list matching talmud.dev's raw
array position for position, `vilnaLine` derived automatically from
list index, cross-checked against the raw text at each DH-boundary
line before being applied; one transcription slip during drafting,
a stray comma splitting one list entry into two arguments, was
caught by the script's own length assertion before any file was
written, and a second slip, an off-by-one shift in the target ids
around vilnaLine 35-59 from a miscounted line span, was caught by
side-by-side comparison against the raw array before applying and
fully corrected). The correspondence: vilnaLine 1-10 (the fire-pan
lottery background, Rabbi Yehuda's paraphrase of the mishna) to
`l01`; 11-14 (the incense's rarity and enriching effect) to `l06`;
15-21 (who receives the blood, due to the sprinkling's own dearness)
to `l11`; 22-26 (sometimes the slaughterer is a non-priest) to `l14`;
27-28 (ben Katin, the twelve spigots) to `l15`; 29-35 (thirteen
lottery services, the sanctification of hands and feet) to `l18`;
36-37 (the baraita confirming the receiver, from Tractate Tamid) to
`l20`; 38-41 (the order of the animal's walking, flaying) to `l23`;
42-56 (the order of cutting up, the carrying to the ramp, the
disputed cutting-up and prizing sequences) to `l28`; 57 (the
"choice cut" verse challenge) to `l34`; 58-60 (the two tanna'im's
size-versus-fat criterion) to `l35`; 61-62 (the extra verse teaching
the fat's own precedence) to `l40`. `l03` (the alternate view that
other services do require a lottery), `l04` (the "some say" version
of that alternate view), `l08` (the baraita about twelve priests
accompanying the daily-offering's winner), and `l38` (the reasoning
for why the leg accompanies the head) have no dedicated vilnaLine of
their own in this daf's column, the same established folding pattern
seen throughout this run.

vilnaLine 62, the daf's final truncated word "למאי" (for what), is
the same kind of boundary case as every other daf ending in this
run: per the policy, it is linked to `yoma-025b-l40`, 25b's own final
locally captured Gemara line (the extra verse teaching the fat's
precedence), even though the DH's own point is itself still open at
the point of truncation, continuing onto 26a.

All 62 entries were fixed in a single list-indexed pass. 25b is fully
resolved, 62/62, with real translations replacing every generic
placeholder and every linkedGemaraLineIds value corrected to its
real zero-padded `yoma-025b-lXX` target.

## 25b, vilnaLine 30-35 (VERSION 15.29), second correction found by the 20a-29b audit

The compact structural + full-content audit of 20a-29b (run after the
20b fix above) found a second, smaller contiguous English-helper
content shift, this time introduced during this session's own build
of 25b rather than inherited as pre-existing content. Full raw-vs-en
comparison of vilnaLine 18-45 found the drift begins as a partial
merge at vilnaLine 30 (which had folded in the opening clause of
vilnaLine 31's own Hebrew), runs as a clean one-line-ahead shift
through vilnaLine 34, partially resolves with a duplicated phrase at
vilnaLine 35 ("for the receiving"), and is fully correct again from
vilnaLine 36 onward (36's own `en` was already correct describing its
own raw text and was left unchanged).

`linkedGemaraLineIds` was checked against the real captured Gemara
lines for the whole span and found correct throughout: vilnaLine
29-35 all correctly target `l18` (the Gemara's own line proving the
thirteen-priest count via the sprinkler-is-the-receiver derivation,
long enough to cover Rashi's multi-line elaboration on why the
sanctification of hands and feet is required for the receiving even
though the slaughtering itself is valid by a non-priest). No
placement error was found, so per instruction no `linkedGemaraLineIds`
values were changed; only the `en` field was rewritten for vilnaLine
30 through 35 (6 entries), each now describing its own raw Hebrew
print line.

This is the second instance of this exact failure mode found in this
audit (after 20b), but unlike 20b this one was introduced during this
session's own fast-alignment build rather than inherited - a reminder
that the full-index, no-sampling verification discipline established
for id-mapping slips applies equally to the `en` text itself, not just
to `linkedGemaraLineIds`.

## 26a, full daf (VERSION 15.21)

Continuing the resumed run. Before any edit, the 25b/26a boundary was
re-verified read-only: 25b's truncated final word "למאי" (for what)
is completed by 26a's opening "למאי אתא לכדתניא כיצד היה עושה" in
both the Gemara and Rashi columns, continuing the question about the
extra verse teaching the fat's own precedence cleanly. No edit was
made to 25b. The mandatory preflight raw-count check was run first:
talmud.dev's non-empty raw Rashi array for 26a has 42 lines, and the
prior enrichment JSON's `rashiTranslations` also had 42 entries, an
exact match, so no orphaned-entry cleanup was needed here, and no
sign of one-daf-early content misattribution was found on inspection
of the prior stub text.

26a's Gemara side has 15 real captured lines (`l01`, `l03` [mishna],
`l06`, `l07`, `l11a`, `l11b`, `l18`, `l22`, `l24`, `l26`, `l28`,
`l31`, `l34`, `l35`, `l37`) against 38 raw Gemara print lines. This
daf's real-line ids include a lettered pair, `l11a`/`l11b`, the first
time this run has encountered that naming convention rather than a
plain zero-padded number; both were confirmed as real, distinct
captured lines before being used as link targets. Its Rashi side has
42 raw print lines carrying the same generic descriptive-style
placeholder text as the daf before it.

All 42 raw Rashi print lines were read against the raw Gemara text
and the 15 real captured line ids, using the same multi-DH rule and
list-indexed methodology as the prior two daf. The correspondence:
vilnaLine 1-7 (why the verse needed to teach the fat's inclusion,
the honor of covering the slaughtering-place) to `l01`; 8-10 (the
mishna's newcomers-for-the-incense clause) to `l03`; 11-12 (because
it enriches) to `l06`; 13 (the challenge from the burnt-offering
verse) to `l07`; 14-15 (that verse is about what is uncommon) to
`l11a`; 16-18 (one who issues rulings, in accordance with the
halakha) to `l11b`; 19-20 (who won it in the morning wins it in the
evening) to `l18`; 21-23 (since the priestly watches are renewed) to
`l26`; 24-27 (why the assumed schedule would multiply lotteries) to
`l28`; 28-36 (the mishna's own fourth clause, who carries the limbs
up the ramp to the altar, addressed out of Gemara-linear order after
the surrounding Gemara discussion concludes) to `l03`; 37 (not proper
conduct, so as not to appear burdened) to `l34`; 38-41 (Rabbi
Eliezer ben Yaakov's own view does not track Rabbi Yehuda's) to
`l35`. `l22` and `l24` (the stacked, near-identical baraita
objections about the evening lottery) and `l31` (Rabbi Eliezer ben
Yaakov's own baraita, self-explanatory and folded into the DH that
follows) have no dedicated vilnaLine of their own in this daf's
column, the same established folding pattern seen throughout this
run.

vilnaLine 42, the daf's final truncated word "דלא" (not), is the
same kind of boundary case as every other daf ending in this run:
per the policy, it is linked to `yoma-026a-l37`, 26a's own final
locally captured Gemara line (the Gemara's own question about
finding a tanna who taught five lottery rounds), even though the
DH's own point is itself still open at the point of truncation,
continuing onto 26b.

All 42 entries were fixed in a single list-indexed pass. 26a is fully
resolved, 42/42, with real translations replacing every generic
placeholder and every linkedGemaraLineIds value corrected to its
real zero-padded `yoma-026a-lXX` target.

## 26b, full daf (VERSION 15.22)

Continuing the resumed run. Before any edit, the 26a/26b boundary was
re-verified read-only: 26a's truncated final word "דלא" (not) is
completed by 26b's opening "ההוא דלא כרבי אליעזר בן יעקב ודלא כרבי
יהודה" in both the Gemara and Rashi columns, continuing the Gemara's
own question about finding a tanna who taught five lottery rounds
cleanly. No edit was made to 26a. The mandatory preflight raw-count
check was run first: talmud.dev's non-empty raw Rashi array for 26b
has 61 lines, and the prior enrichment JSON's `rashiTranslations`
also had 61 entries, an exact match, so no orphaned-entry cleanup was
needed here, and no sign of one-daf-early content misattribution was
found on inspection of the prior stub text.

26b's Gemara side has 16 real captured lines (`l01`, `l02` [mishna],
`l05`, `l10`, `l15`, `l18`, `l24`, `l26`, `l28`, `l30`, `l31a`,
`l31b`, `l32` [mishna], `l39`, `l40`, `l41`) against 43 raw Gemara
print lines, continuing the lettered-suffix convention seen for the
first time at 26a (`l31a`/`l31b` here, both carrying `vilna_line: 31`
since two distinct Gemara clauses share one raw print line). Its
Rashi side has 61 raw print lines carrying the same generic
descriptive-style placeholder text as the daf before it. This daf
also crosses two mishna/gemara boundaries mid-page (the third
Mishna's daily-offering count at `l02`, and the fourth Mishna's ram
and bull counts at `l32`).

All 61 raw Rashi print lines were read against the raw Gemara text
and the 16 real captured line ids, using the same multi-DH rule and
list-indexed methodology as the prior three daf. The correspondence:
vilnaLine 1-2 (the baraita is not like either Rabbi Eliezer ben
Yaakov or Rabbi Yehuda) to `l01`; 3-9 (the mishna's own count clauses
for the daily-offering, the festival water libation, one priest with
the jug) to `l02`; 10-17 (the afternoon and Shabbat additions, the
two logs of wood) to `l05`; 18-24 (the Gemara's proof that the water
libation applies only in the morning) to `l10`; 25-35 (the pourer
raising his hand, the Sadducee priest pelted with etrogim) to `l15`;
36-40 (the proposal that one priest could arrange the wood twice in
the morning) to `l24`; 41 (the challenge that the verse should have
repeated the same verb) to `l28`; 42-47 (the baraita's four possible
totals: thirteen, fourteen, fifteen, sixteen) to `l30`; 48 (the
challenge that a baraita teaches seventeen) to `l31a`; 49-57 (the
resolution: that baraita follows Rabbi Yehuda, not Rabbi Eliezer ben
Yaakov, with Rashi's own extended discussion of what can and cannot
be inferred about a priest for the fire-pan) to `l31b`; 58 (the
fourth Mishna's ram and bull clauses) to `l32`; 59-60 (in what case
is this said, an individual may sacrifice alone, the flaying and
cutting up are equal) to `l39`. `l18` (Rabbi Shimon ben Yochai's own
baraita deriving the two-logs requirement from the verse, whose
substance Rashi had already glossed while covering `l05`), `l26`
(the Gemara's "if the Merciful One wrote it twice" reasoning, folded
into the same comment anchored to `l24`), and `l40` (the Gemara's own
near-verbatim restatement of the mishna's flaying and cutting up
clause, already covered by Rashi's comment on `l39`) have no
dedicated vilnaLine of their own in this daf's column, the same
established folding pattern seen throughout this run. The vl10-17
and vl36-40 spans in particular required a judgment call, since their
content closely paraphrases the derivation that a nearby real line
supplies without a fresh independent lemma of its own opening; both
were resolved on the positional-anchoring principle (anchor to the
comment's own opening catchword) already established in the boundary
policy, rather than requiring an exact phrase match to the linked
line's own text.

vilnaLine 61, the daf's final truncated word "האי" (this), is the
same kind of boundary case as every other daf ending in this run:
per the policy, it is linked to `yoma-026b-l41`, 26b's own final
locally captured Gemara line (Hizkiya's proof from the verse about
placing fire that flaying and cutting up do not require priesthood),
even though the DH's own point is itself still open at the point of
truncation, continuing onto 27a.

All 61 entries were fixed in a single list-indexed pass (one
transcription slip, a three-way split of one raw line's content
across three list entries that left the final truncated entry
missing entirely, was caught by the script's own length assertion
before any file was written, and corrected by merging back to the
correct two-entry span before re-running). 26b is fully resolved,
61/61, with real translations replacing every generic placeholder and
every linkedGemaraLineIds value corrected to its real zero-padded
`yoma-026b-lXX` target.

## 27a, full daf (VERSION 15.23), dangling-link finding (distinct from the generic-stub pattern)

Continuing the resumed run. Before any edit, the 26b/27a boundary was
re-verified read-only: 26b's truncated final word "האי" (this) is
completed by 27a's opening "האי מבעיא ליה לגופיה" in both the Gemara
and Rashi columns, continuing Hizkiya's proof from the verse about
placing fire cleanly. No edit was made to 26b. The mandatory
preflight raw-count check was run first: talmud.dev's non-empty raw
Rashi array for 27a has 53 lines, and the prior enrichment JSON's
`rashiTranslations` also had 53 entries, an exact match, so no
orphaned-entry cleanup was needed on count grounds.

27a is a new failure mode, distinct from every daf fixed so far in
this run. Its prior `en` text did not show the generic
descriptive-style placeholder pattern ("Rashi: opens/continues/
concludes" boilerplate) seen on every other daf in this run; instead
it read as plausible, content-specific prose tracking the sugya's own
legal reasoning. But checking every `linkedGemaraLineIds` value
against the daf's 13 real captured Gemara line ids (`l01`, `l06`,
`l09`, `l11`, `l14`, `l17`, `l19`, `l20`, `l24`, `l25`, `l27`, `l31`,
`l33`) found 5 entries pointing to ids that do not exist anywhere in
`learning_data.js` for this daf: vilnaLine 2 linked to a nonexistent
`l03`, vilnaLine 3 to `l05`, vilnaLine 4 to `l07`, vilnaLine 7 to
`l13`, and vilnaLine 10 to `l22`. These are dangling references, not
generic filler; the `en` text they attached to also did not survive
scrutiny once compared word-for-word against the raw Rashi Hebrew
line by line, so the whole daf was rebuilt using the same
list-indexed methodology as every other daf in this run, rather than
patching only the 5 confirmed-dangling entries.

All 53 raw Rashi print lines were read against the raw Gemara text
and the 13 real captured line ids, using the multi-DH rule. One
transcription slip mid-draft, where two raw lines' content was
folded into a single list entry partway through the vl19-46 span
(dropping the total below 53 and shifting every id after that point
by one), was caught by the script's own length assertion and by a
full recount against every target id before any file was written;
the list was rebuilt from scratch with one tuple per raw line and
re-verified index by index before applying. The correspondence:
vilnaLine 1-6 (this verse is needed for itself, Rav Shimi bar Ashi's
account of Abaye explaining slaughtering by a non-priest to his son)
to `l01`; 7-12 (the verse teaches: and he shall slaughter, and the
priests shall present) to `l06`; 13-18 (by inference, from the
receiving onward is a priestly requirement) to `l09`; 19-23 (I would
have said this, since it does not preclude atonement) to `l11`; 24-26
(rather, from here: and the sons of Aaron the priests shall arrange)
to `l14`; 27-29 (but say it excludes the arrangement of the two wood
logs) to `l17`; 30-38 (this should not enter your mind, carrying wood
does not require priesthood) to `l20`; 39-46 (why do I need "and they
shall arrange," since priesthood is written in them) to `l24`; 47
(that it requires six, the meat by five) to `l31`; 48-53 (Rav
Hamnuna's resolution: the verse about wood on the fire is an extra
phrase, teaching six priests for the wood arrangement) to `l33`.
`l19` (a short one-line objection, "on the contrary, a similar
arrangement should exclude," folded into the comment anchored to
`l20`), `l25` (the Gemara's own restatement of the same
carrying-limbs-versus-carrying-wood point already covered while
explaining `l20`), and `l27` (a near-duplicate restatement of `l20`'s
own point, likewise folded) have no dedicated vilnaLine of their own
in this daf's column. The vl30-38 span required the same kind of
positional-anchoring judgment call as 26b's vl10-17 and vl36-40: `l20`
and `l27` state almost the same fact twice in the Gemara, and since
the Rashi comment picks up immediately after the `l20`-anchored
comment without a fresh independent catchword, it was kept anchored
to `l20` rather than jumped ahead to `l27`.

vilnaLine 53, the daf's final truncated word "הוי" (is), is the same
kind of boundary case as every other daf ending in this run: per the
policy, it is linked to `yoma-027a-l33`, 27a's own final locally
captured Gemara line (Rav Hamnuna's resolution of the six-priests
derivation), even though the DH's own point is itself still open at
the point of truncation, continuing onto 27b.

All 53 entries were fixed in a single list-indexed pass. 27a is fully
resolved, 53/53, with every entry's `en` text and linkedGemaraLineIds
now verified against the raw Rashi Hebrew and the real captured line
ids, correcting both the 5 confirmed dangling links and the
surrounding entries that had not been independently checked before.

## 27b, full daf (VERSION 15.24), second dangling-link daf in a row

Continuing the resumed run. Before any edit, the 27a/27b boundary was
re-verified read-only: 27a's truncated final word "הוי" (is) is
completed by 27b's opening "הוי אומר זה טלה" in both the Gemara and
Rashi columns, continuing Rav Hamnuna's resolution of the six-priests
derivation cleanly. No edit was made to 27a. The mandatory preflight
raw-count check was run first: talmud.dev's non-empty raw Rashi array
for 27b has 44 lines, and the prior enrichment JSON's
`rashiTranslations` also had 44 entries, an exact match on count.

However, following the practice adopted after 27a's discovery, every
existing `linkedGemaraLineIds` value was independently checked
against the daf's real captured Gemara line ids before trusting the
count match, since a dangling link does not always show up as a raw
count mismatch. 27b's real ids are `l01a`, `l01b`, `l04`, `l06`,
`l07`, `l10`, `l16`, `l20`, `l23`, `l26`, `l28` (11 total, spanning 30
raw Gemara print lines; `l01a` and `l01b` both carry `vilna_line: 1`
since two distinct Gemara statements share the daf's first raw print
line, the same lettered-pair convention seen at 26a's `l11a`/`l11b`
and 26b's `l31a`/`l31b`). Checking every prior entry against this set
found 7 dangling references to ids that do not exist anywhere in
`learning_data.js` for this daf: vilnaLine 1 to a nonexistent `l01`,
vilnaLine 2 to `l02`, vilnaLine 3 to `l03`, vilnaLine 5 to `l05`,
vilnaLine 8 to `l08`, vilnaLine 9 to `l09`, and vilnaLine 11 to `l11`.
This is the same failure mode found on 27a (not the generic
descriptive-style placeholder pattern), now confirmed on a second
consecutive daf, so the whole daf was rebuilt using the list-indexed
methodology rather than patching only the confirmed-dangling entries.

All 44 raw Rashi print lines were read against the raw Gemara text
and the 11 real captured line ids, using the multi-DH rule. One
transcription slip mid-draft, where two raw lines' content was
merged into a single list entry at the `l01a`/`l01b` boundary
(dropping the total to 43 and shifting every id after that point by
one), was caught by the script's own length assertion and by a
per-target-id count check before any file was written; the merged
entry was split back into its two original lines and the full list
re-verified index by index before applying. The correspondence:
vilnaLine 1-12 (you must say this is the lamb, why the young bull's
own wood and fire verses do not require a fresh arranging) to
`l01a`; 13-14 (liable, the non-priest dismantles it) to `l01b`; 15-17
(but isn't there the limbs and the fats, already counted among the
four services) to `l06`; 18-19 (but isn't there the removal of the
ashes) to `l07`; 20 (and do you have any service valid at night and
invalid by a non-priest, recapping Rabbi Zeira's own objection out of
strict Gemara-linear order once the surrounding exchange resolves) to
`l04`; 21-24 (it is a daytime service, since it is written: and the
priest shall burn wood on it in the morning) to `l10`; 25-27 (is that
to say a daytime service requires a lottery) to `l16`; 28-32 (but
didn't we learn, if the time for slaughtering has arrived) to `l23`;
33-41 (on the day of your slaughtering, that which has no
rectification, that which has rectification) to `l26`; 42-43 (that
has after it, the arranging of a service) to `l28`. `l20` (a
near-duplicate variant of `l16`'s own "is that to say a daytime
service" challenge, adding the death-penalty element, absorbed into
the same comment anchored to `l16`) has no dedicated vilnaLine of its
own in this daf's column, the same established folding pattern seen
throughout this run. As with 27a's vl30-38 and 26b's vl10-17 and
vl36-40, vilnaLine 20's placement (positioned after the `l06`/`l07`
exchange resolves rather than immediately after `l04` itself) was a
positional-anchoring judgment call rather than a strict linear match,
consistent with the established boundary policy.

vilnaLine 44, the daf's final truncated word "והרי" (but isn't
there), is the same kind of boundary case as every other daf ending
in this run: per the policy, it is linked to `yoma-027b-l28`, 27b's
own final locally captured Gemara line (the second version of Rabbi
Zeira's objection, that a service followed by another service should
not be invalid for a non-priest), even though the DH's own point is
itself still open at the point of truncation, continuing onto 28a.

All 44 entries were fixed in a single list-indexed pass. 27b is fully
resolved, 44/44, with every entry's `en` text and linkedGemaraLineIds
now verified against the raw Rashi Hebrew and the real captured line
ids, correcting both the 7 confirmed dangling links and the
surrounding entries that had not been independently checked before.
Combined with 27a, this closes out a second consecutive dangling-link
daf; both are documented here as a distinct systemic finding from the
generic-stub pattern that dominated 21a through 26b, worth checking
for specifically (independently of the raw-count preflight) on every
remaining daf in this run.

## 28a, full daf (VERSION 15.25), third dangling-link daf in a row, perek boundary

Continuing the resumed run. Before any edit, the 27b/28a boundary was
re-verified read-only: 27b's truncated final word "והרי" (but isn't
there) is completed by 28a's opening "והרי אברים ופדרים" in both the
Gemara and Rashi columns, continuing the second version of Rabbi
Zeira's objection cleanly. No edit was made to 27b. The mandatory
preflight raw-count check was run first: talmud.dev's non-empty raw
Rashi array for 28a has 45 lines, and the prior enrichment JSON's
`rashiTranslations` also had 45 entries, an exact match on count.

As with 27a and 27b, every existing `linkedGemaraLineIds` value was
independently checked against the daf's real captured Gemara line ids
before trusting the count match. 28a's real ids are `l01`, `l05`,
`l07`, `l10`, `l11`, `l14`, `l18`, `l21`, `l23`, `l24` (mishna), `l30`
(11 total, spanning 34 raw Gemara print lines). Checking every prior
entry against this set found 6 dangling references to nonexistent
ids: vilnaLine 2 to `l02`, vilnaLine 3 to `l03`, vilnaLine 4 to `l04`,
vilnaLine 6 to `l06`, vilnaLine 8 to `l08`, and vilnaLine 10 to `l25`.
This is the third consecutive daf with this failure mode rather than
the generic descriptive-style placeholder pattern, so the whole daf
was rebuilt using the list-indexed methodology.

This daf also contains a perek boundary: raw Gemara line 23 (`l23`)
is the standalone formula "הדרן עלך בראשונה" ("we take our leave of
you, Barishona"), closing Perek 2 (named for its own opening word,
Barishona), distinct from the "Shivat Yamim" perek-close already
documented at 21b. `l23`'s own `en` field is correctly empty in
`learning_data.js`, since the formula needs no translation. The raw
Rashi array itself also carries this same formula as its own entry
(vilnaLine 19), apparently because the print layout centers the
hadran phrase across both columns; it was treated the same way,
linked to `l23` with no substantive commentary content of its own.
Perek 3 (also opening with "אמר להם הממונה," elaborating in more
detail on the appointed priest's dawn announcement already introduced
at the end of Perek 2) begins immediately after at `l24`, the daf's
mishna.

All 45 raw Rashi print lines were read against the raw Gemara text
and the 11 real captured line ids, using the multi-DH rule. The
correspondence: vilnaLine 1-5 (a girsa note on which version of
Rabbi Zeira's question belongs here) to `l01`; 6-7 (since it is a
complete service) to `l05`; 8-9 (a girsa note that a stretch of text
through "due to the incident that occurred" is not read in Rashi's
own version) to `l11`; 10-18 (we too have learned it, that arranging
the two logs is a complete service, not the completion of the
woodpile's arranging) to `l18`; 19 (the perek-closing formula itself)
to `l23`; 20-35 (the appointed priest is the deputy High Priest, the
watchman's exchange about dawn, the moonlight mistake) to `l24`; 36-45
(they brought down the High Priest, covering one's legs, sanctifying
hands and feet) to `l30`. `l07` (Rava's own objection that a lottery
should be required), `l10` (the Gemara's own resolution that a
separate lottery was in fact already implied), `l14` (a near-duplicate
restatement of the "complete service requires a lottery" challenge),
and `l21` (the answer distinguishing services with and without a
remedy) have no dedicated vilnaLine of their own in this daf's
column; `l07`, `l10`, and `l14` in particular fall within the same
stretch Rashi's own girsa note (vilnaLine 8-9) explicitly says his
text omits, which is consistent with them having no dedicated
comment.

vilnaLine 45, the daf's final entry, is the truncated Gemara-section
marker "גמ'" itself (the start of Perek 3's Gemara discussion on its
own opening mishna, with no further text captured on this daf): per
the policy, it is linked to `yoma-028a-l30`, 28a's own final locally
captured Gemara line, even though the Gemara's own discussion had not
yet been opened at the point of truncation, continuing onto 28b.

All 45 entries were fixed in a single list-indexed pass. 28a is fully
resolved, 45/45, with every entry's `en` text and linkedGemaraLineIds
now verified against the raw Rashi Hebrew and the real captured line
ids, correcting both the 6 confirmed dangling links and the
surrounding entries that had not been independently checked before.
This closes out a third consecutive dangling-link daf (27a, 27b,
28a), reinforcing that the dangling-link failure mode is now a
standing check to run on every remaining daf in this corpus,
independent of the raw-count preflight.

## 28b, full daf (VERSION 15.26), fourth dangling-link daf in a row, closes the 25a-28b run

Continuing and closing the resumed run. Before any edit, the 28a/28b
boundary was re-verified read-only: 28a's truncated final "word" was
the bare Gemara-section marker "גמ'" (marking the start of Perek 3's
own discussion with no further text captured on 28a), completed by
28b's opening "גמ' תניא ר' ישמעאל אומר ברק ברקאי" in both the Gemara
and Rashi columns, opening the baraita on the dawn-announcement
formula cleanly. No edit was made to 28a. The mandatory preflight
raw-count check was run first: talmud.dev's non-empty raw Rashi array
for 28b has 79 lines, and the prior enrichment JSON's
`rashiTranslations` also had 79 entries, an exact match on count.

As with the three preceding daf, every existing `linkedGemaraLineIds`
value was independently checked against the daf's real captured
Gemara line ids before trusting the count match. 28b's real ids are
`l01`, `l07`, `l08`, `l10`, `l16`, `l19`, `l25`, `l32`, `l34`, `l36`,
`l37`, `l39`, `l41`, `l42`, `l44`, `l45` (16 total, spanning 47 raw
Gemara print lines). Checking every prior entry against this set found
8 dangling references to nonexistent ids: vilnaLine 2 to `l02`,
vilnaLine 4 to `l09`, vilnaLine 6 to `l11`, vilnaLine 7 to `l12`,
vilnaLine 8 to `l13`, vilnaLine 9 to `l14`, vilnaLine 10 to `l15`, and
vilnaLine 16 to `l46` (which does not exist at all, the closest real
id being `l45`). This is the fourth consecutive daf with this failure
mode, so the whole daf was rebuilt using the list-indexed methodology.

All 79 raw Rashi print lines were read against the raw Gemara text
and the 16 real captured line ids, using the multi-DH rule. One
transcription slip mid-draft, where one raw line's own multi-DH
transition ("he himself said - this is the one on the roof" opening
one comment, then "to Hebron - it is a question" opening another, both
appearing on the SAME raw print line) was incorrectly split across
two list entries, leaving the total at 80 rather than 79, was caught
by the script's own length assertion and by a per-target-id count
check before any file was written; the two entries were merged back
into one (the whole line correctly targets whichever real line the
LAST-opened dibbur hamatchil on it belongs to, per the established
multi-DH rule) and the full list re-verified index by index before
applying. A separate transcription slip, where the target ids were
accidentally typed with the `028a-` prefix from the daf just closed
rather than `028b-`, was caught immediately by a plain text search
across the whole draft before the count check even ran.

The correspondence: vilnaLine 1-2 (the light has risen, to hire
workers) to `l07`; 3-12 (the prayer of Abraham, the walls blacken) to
`l08`; 13-14 (shall we arise and derive a halakha from Abraham) to
`l10`; 15-23 (when it occurs on the eve of Shabbat, one needed to
hurry the offering) to `l16`; 24-34 (they were not perfectly aligned,
astronomy, all the kings of east and west) to `l19`; 35 (who draws
and gives drink) to `l32`; 36-37 (the seven Noahide mitzvot) to `l34`;
38-39 (even the joining of cooked foods) to `l36`; 40 (and he
interprets the dream, meaning he both asks and answers) to `l37`;
41-47 (he himself said, this is the one on the roof, if you wish say)
to `l41`; 48-62 (are they confused, a column of sun light, a cloudy
day, learn from this) to `l42`; 63 (to spread hides) to `l44`; 64-79
(the hazy light of the sun, a jar of vinegar, dazzling sunlight) to
`l45`. `l01` (the four tanna'im's own wordings for the dawn
announcement, folded per the multi-DH rule since the daf's opening
raw print line both closes a comment on Rabbi Akiva's own phrase and
opens the comment that targets `l07`, and the whole line's target is
therefore `l07`, not `l01`), `l25` (the elders-in-Egypt, Isaac, and
Jacob citation chain, self-explanatory and requiring no dedicated
Rashi gloss), and `l39` (a near-duplicate restatement of the
roof-versus-ground exchange, absorbed into the comment anchored to
`l41`, whose own opening phrase matches the raw text more precisely)
have no dedicated vilnaLine of their own in this daf's column.

vilnaLine 79, the daf's final truncated word "הרהורי" (musings of),
is the same kind of boundary case as every other daf ending in this
run: per the policy, it is linked to `yoma-028b-l45`, 28b's own final
locally captured Gemara line (Rav Nachman's teaching about hazy
sunlight and dazzling light), even though the DH's own point is
itself still open at the point of truncation, continuing onto 29a.

All 79 entries were fixed in a single list-indexed pass. 28b is fully
resolved, 79/79, with every entry's `en` text and linkedGemaraLineIds
now verified against the raw Rashi Hebrew and the real captured line
ids, correcting both the 8 confirmed dangling links and the
surrounding entries that had not been independently checked before.

This closes the bounded fast Rashi alignment run covering 25a through
28b (8 daf: 25a, 25b, 26a, 26b, 27a, 27b, 28a, 28b), fixing 61 + 62 +
42 + 61 + 53 + 44 + 45 + 79 = 447 entries total. No daf in this range
was deferred. The run also produced one major corpus-quality finding
applicable beyond this range: the dangling-linkedGemaraLineIds failure
mode (first found at 27a and confirmed on every daf through 28b),
distinct from the generic descriptive-style placeholder pattern that
dominated 21a through 26b, worth checking for specifically on every
remaining daf in this corpus regardless of whether the raw-count
preflight passes cleanly.

## 29a, full daf (VERSION 15.27), fifth dangling-link daf, resuming the run at 29a-32b

Resuming the fast alignment run into new territory (29a-32b). Before
any edit, the 28b/29a boundary was re-verified read-only: 28b's
truncated final word "הרהורי" (musings of) is completed by 29a's
opening "הרהורי עבירה קשו מעבירה" in both the Gemara and Rashi
columns, continuing Rav Nachman's teaching about hazy sunlight and
dazzling light cleanly. No edit was made to 28b. The mandatory
preflight raw-count check was run first: talmud.dev's non-empty raw
Rashi array for 29a has 56 lines, and the prior enrichment JSON's
`rashiTranslations` also had 56 entries, an exact match on count.

Per the practice established in the 25a-28b run, every existing
`linkedGemaraLineIds` value was independently checked against the
daf's real captured Gemara line ids before trusting the count match.
29a's real ids are `l01`, `l03`, `l06`, `l09`, `l15`, `l18`, `l24`,
`l27`, `l28` (9 total, spanning 32 raw Gemara print lines). Checking
every prior entry against this set found 6 dangling references to
nonexistent ids: vilnaLine 2 to `l02`, vilnaLine 3 to `l05`, vilnaLine
5 to `l08`, vilnaLine 6 to `l10`, vilnaLine 8 to `l19`, and vilnaLine
9 to `l22`. This is the fifth consecutive daf with this failure mode
(after 27a, 27b, 28a, 28b), so the whole daf was rebuilt using the
list-indexed methodology.

All 56 raw Rashi print lines were read against the raw Gemara text
and the 9 real captured line ids, using the multi-DH rule. One
boundary slip mid-draft, where a line transitioning from the machloket
about whether the Scroll of Esther renders the hands impure into the
comment establishing the dawn/prayer analogy was assigned to the
wrong side of the transition, was caught by comparing the raw text
against the target id before applying and corrected (the line
concluding "since it is not a book" still belongs to the same comment
as the lines before it, not the one opening immediately after). The
correspondence: vilnaLine 1-8 (thoughts of transgression, the odor of
meat, the end of summer, a heated oven) to `l01`; 9-21 (a fever in
the winter, a cold oven, relearning old material, mortar from mortar)
to `l03`; 22-23 (what is the reason of Rabbi) to `l06`; 24-29 (this
hind is not stated precisely, why was Esther likened to a hind) to
`l09`; 30-33 (that works out well according to the one who said, a
dispute over whether the scroll renders the hands impure) to `l15`;
34-41 (establishes it in accordance with Rabbi Binyamin bar Yefet,
why were the prayers of the righteous likened to a hind) to `l18`;
42-48 (when, if we say, is there no alternative to the High Priest,
is there moonlight) to `l24`; 49-51 (this is what is meant: and on
Yom Kippur when they said the light flashed) to `l27`; 52-56 (not
this alone, but even the pinching of the bird, what was, was) to
`l28`. All 9 of this daf's real captured Gemara lines received a
dedicated comment; none were folded.

vilnaLine 56, the daf's final truncated word "הוא" (it/he), is the
same kind of boundary case as every other daf ending in this run: per
the policy, it is linked to `yoma-029a-l28`, 29a's own final locally
captured Gemara line (the baraita on pinching a bird and taking the
handful of a meal-offering at night), even though the DH's own point
is itself still open at the point of truncation, continuing onto 29b.

All 56 entries were fixed in a single list-indexed pass. 29a is fully
resolved, 56/56, with every entry's `en` text and linkedGemaraLineIds
now verified against the raw Rashi Hebrew and the real captured line
ids, correcting both the 6 confirmed dangling links and the
surrounding entries that had not been independently checked before.

## 29b, full daf (VERSION 15.28), sixth dangling-link daf in a row

Continuing the resumed run. Before any edit, the 29a/29b boundary was
re-verified read-only: 29a's truncated final word "הוא" (it/he) is
completed by 29b's opening, which itself repeats 29a's own final
Gemara word "נהדרה" (let us return it) before continuing "ונהדר
ונקמצה ביממא" (and let us return it and take the handful during the
day), in both the Gemara and Rashi columns, continuing the baraita on
pinching a bird and taking a handful at night cleanly. No edit was
made to 29a. The mandatory preflight raw-count check was run first:
talmud.dev's non-empty raw Rashi array for 29b has 54 lines, and the
prior enrichment JSON's `rashiTranslations` also had 54 entries, an
exact match on count.

Per the now-standard practice, every existing `linkedGemaraLineIds`
value was independently checked against the daf's real captured
Gemara line ids before trusting the count match. 29b's real ids are
`l01`, `l03`, `l08`, `l10`, `l13`, `l16`, `l20` (7 total, spanning 23
raw Gemara print lines). Checking every prior entry against this set
found 3 dangling references to nonexistent ids: vilnaLine 2 to `l05`,
vilnaLine 3 to `l07`, and vilnaLine 5 to `l12`. This is the sixth
consecutive daf with this failure mode, so the whole daf was rebuilt
using the list-indexed methodology.

All 54 raw Rashi print lines were read against the raw Gemara text
and the 7 real captured line ids, using the multi-DH rule. The
correspondence: vilnaLine 1-3 (he taught it, service vessels
consecrate even not at their proper time) to `l01`; 4-20 (anything
sacrificed during the day, at night, is consecrated, in any case it
teaches, to be sacrificed, to be disqualified by remaining overnight)
to `l03`; 21-34 (disqualified, a girsa note that the reading may omit
the word "disqualified" since the conclusion of the sugya treats the
first day's arrangement as no arrangement at all, citing Rabbeinu
Chananel of Rome's explicit reading) to `l08`; 35-36 (how shall he
proceed: he shall leave it, it should become consecrated and
disqualified) to `l10`; 37-44 (Rava said: this one who raises the
objection raises it well, but a day is a lack of time) to `l13`;
45-53 (when Shabbat evening arrives, one who removed it beforehand,
it becomes as if a monkey arranged it) to `l16`. All 7 of this daf's
real captured Gemara lines received a dedicated comment; none were
folded.

vilnaLine 54, the daf's final truncated word "מצוה" (mitzva, i.e. a
matter of proper conduct), is the same kind of boundary case as every
other daf ending in this run: per the policy, it is linked to
`yoma-029b-l20`, 29b's own final locally captured Gemara line (Rabbi
Abba's teaching that one learns proper conduct from the requirement
to sanctify hands as well as feet), even though the DH's own point is
itself still open at the point of truncation, continuing onto 30a.

All 54 entries were fixed in a single list-indexed pass. 29b is fully
resolved, 54/54, with every entry's `en` text and linkedGemaraLineIds
now verified against the raw Rashi Hebrew and the real captured line
ids, correcting both the 3 confirmed dangling links and the
surrounding entries that had not been independently checked before.
This closes out a sixth consecutive dangling-link daf (27a, 27b, 28a,
28b, 29a, 29b), further confirming the dangling-link check is now the
default expectation, not an edge case, for the remainder of this
corpus.

## 30a, full daf (VERSION 15.31), seventh dangling-link daf, worse than prior six

Resuming forward production after the 20a-29b audit closed clean. The
29a/29b to 30a boundary was independently re-verified read-only before
any edit: 29b's truncated final word "מצוה" (a matter of proper
conduct) is completed by 30a's opening, which begins with a fresh
dibbur hamatchil ("מצוה לשפשף בידו") rather than a direct word
continuation, but both concern the same "proper conduct" teaching
about hand-sanctification and the mitzva to wipe away drops of urine,
consistent with 29b's own final locally captured Gemara line (Rabbi
Abba's teaching). No edit was made to 29b.

The mandatory preflight raw-count check was run first: talmud.dev's
non-empty raw Rashi array for 30a has 54 lines, matching the prior
enrichment JSON's 54 `rashiTranslations` entries, an exact count
match - independently re-confirmed rather than trusted from any
earlier note.

Checking every existing `linkedGemaraLineIds` value against 30a's 9
real captured Gemara/mishna ids (`l01`, `l04`, `l08`, `l13`, `l18`,
`l22` (mishna), `l28`, `l33`, `l35`) found this daf worse than the
prior six dangling-link daf: only vilnaLine 1 had a live id, vilnaLine
2, 3, 5, and 7 pointed to nonexistent unpadded ids, and vilnaLine
10-54 (45 entries) had `linkedGemaraLineIds` entirely empty. The whole
daf carried the older generic descriptive-style filler text (for
example, "Mitzva to brush urine drops off legs so they cannot be
seen." at vilnaLine 1), not per-print-line translations. The whole
daf was rebuilt using the list-indexed methodology.

All 54 raw Rashi print lines were read against the raw Gemara/mishna
text and the 9 real captured line ids, using the multi-DH rule. The
correspondence: vilnaLine 1-2 (the mitzva to wipe away urine drops,
so as not to appear to have a severed member) to `l01`; 3 (feces at
its own place, forbidden for reciting the Shema) to `l04`; 4-12 (the
partition in the bathroom, the Rav Huna/Rav Chisda dispute over
reciting the Shema with unseen feces, citing Psalms 35) to `l08`;
13-27 (the halakha of washing hands during a meal, one hand or two,
returning the pitcher to the guests, citing Tosefta Berachot) to
`l13`; 28-34 (washing is only required before eating, not merely
continued drinking, lest he take bread in his hand; bare "מתני'"
marker at the end of vilnaLine 34 stays with `l18` per the same
convention already documented at 20a, since no new gloss content
begins until the following line) to `l18`; 35-43 (the mishna's own
five immersions and ten sanctifications, the Beit HaParva exception)
to `l22`; 44-49 (Ben Zoma's question on why the immersion is
required, deriving it from a change of sacred-to-sacred domain) to
`l28`; 50-53 (Rabbi Yehuda's view that the immersion is a mere
formality, not a Torah-level obligation) to `l33`. `l35` receives no
dedicated mid-daf vilnaLine (it opens only at the daf's own final
truncated word, per the boundary case below).

vilnaLine 54, the daf's final truncated word "באחולי" (in the
profanation of), is the same kind of boundary case as every other daf
ending in this run: per the policy, it is linked to `yoma-030a-l35`,
30a's own final locally captured Gemara line (the Gemara's opening
question "in what do they disagree"), even though the DH's own point
is itself still open at the point of truncation. 30b's own opening
line ("באחולי עבודה. אם לא טבל שחרית ועבד") was read read-only to
confirm this word begins a dibbur hamatchil about whether failing to
immerse before serving invalidates the service performed, continuing
onto 30b; no edit was made to 30b.

All 54 entries were fixed in a single list-indexed pass, verified by
a full side-by-side comparison of every index against the raw array
before applying. 30a is fully resolved, 54/54. This is the seventh
consecutive dangling-link daf found in this corpus (27a, 27b, 28a,
28b, 29a, 29b, 30a), and the first where the majority of entries had
no link at all rather than a wrong one.

## 30b, full daf (VERSION 15.32), eighth dangling-link daf in a row

Continuing the run. Before any edit, the 30a/30b boundary was
re-verified read-only: 30a's truncated final word "באחולי" (in the
profanation of) is completed by 30b's opening "באחולי עבודה. אם לא
טבל שחרית ועבד" (regarding the profanation of the service - if he did
not immerse in the morning and served anyway), continuing the same
dibbur hamatchil cleanly in both the Gemara and Rashi columns. No
edit was made to 30a.

The mandatory preflight raw-count check was run first: talmud.dev's
non-empty raw Rashi array for 30b has 51 lines, matching the prior
enrichment JSON's 51 `rashiTranslations` entries exactly, independently
re-confirmed.

Checking every existing `linkedGemaraLineIds` value against 30b's 12
real captured ids (`l01`, `l02`, `l07`, `l09`, `l12`, `l13`, `l17`,
`l20`, `l23`, `l27`, `l32`, `l36`) found the same pattern as 30a: only
vilnaLine 1 and 2 had live (if partially wrong) ids, vilnaLine 3-11
pointed to nonexistent unpadded ids, and vilnaLine 13-51 (39 entries)
had `linkedGemaraLineIds` entirely empty, carrying the older generic
descriptive-style filler text throughout. The whole daf was rebuilt
using the list-indexed methodology.

All 51 raw Rashi print lines were read against the raw Gemara text
and the 12 real captured line ids, using the multi-DH rule. The
correspondence: vilnaLine 1-2 (the profanation-of-service dispute
itself, Ben Zoma versus Rabbi Yehuda) to `l01`; 3-8 (Ben Zoma's own
proof from the High Priest baraita, citing Zevachim 19b) to `l02`;
9-12 (Ben Zoma's own view rests on a positive commandment, citing
Leviticus 16) to `l07`; 13-21 (does Rabbi Yehuda hold this reasoning,
the leper baraita, standing at the Gate of Nikanor) to `l09`; 22-26
(the reason a leper needs no morning immersion, since he already
immersed the evening before) to `l12`; 27-34 (why the questioner
raised this, the Chamber of Lepers, Rabbi Yehuda's "any person"
reading) to `l13`; 35-38 (the four-way split on immersion and
mind-wandering) to `l17`; 39-42 (Ravina's own reading of Rabbi
Yehuda, a leper treads in impurity) to `l27`; 43-50 (Abaye's question
to Rav Yosef, whether the Rabbis hold like Ben Zoma) to `l32`. `l20`
(the mind-wandering sprinkling requirement) and `l23` (the two
resolutions distinguishing intent to enter the Temple) have no
dedicated vilnaLine of their own in this daf's column, the same
established folding pattern seen throughout this run.

vilnaLine 51, the daf's final truncated word "חוצץ" (interposes), is
the same kind of boundary case as every other daf ending in this run:
per the policy, it is linked to `yoma-030b-l36`, 30b's own final
locally captured Gemara line (Abaye's question to Rav Yosef about
Rabbi Yehuda's formality-only view of immersion), even though the
DH's own point is itself still open at the point of truncation. 31a's
own opening line ("חוצץ או אינו חוצץ. לר' יהודה דאמר מפני סרך טבילה
בעלמא היא") was read read-only to confirm this word begins the
dibbur hamatchil asking whether an interposition invalidates the
immersion given Rabbi Yehuda's view, continuing onto 31a; no edit was
made to 31a.

All 51 entries were fixed in a single list-indexed pass, verified by
a full side-by-side comparison of every index against the raw array
before applying. 30b is fully resolved, 51/51. This is the eighth
consecutive dangling-link daf found in this corpus (27a, 27b, 28a,
28b, 29a, 29b, 30a, 30b).

## 31a, full daf (VERSION 15.33), ninth dangling-link daf, one drafting slip self-caught

Continuing the run. Before any edit, the 30b/31a boundary was
re-verified read-only: 30b's truncated final word "חוצץ" (interposes)
is completed by 31a's opening "חוצץ או אינו חוצץ. לר' יהודה דאמר
מפני סרך טבילה בעלמא היא", continuing the same dibbur hamatchil
cleanly in both the Gemara and Rashi columns. No edit was made to
30b.

The mandatory preflight raw-count check was run first: talmud.dev's
non-empty raw Rashi array for 31a has 37 lines, matching the prior
enrichment JSON's 37 `rashiTranslations` entries exactly.

Checking every existing `linkedGemaraLineIds` value against 31a's 6
real captured ids (`l01`, `l02`, `l07`, `l10`, `l14`, `l20`) found the
same pattern as the prior daf: vilnaLine 2-4 pointed to nonexistent
unpadded ids, and vilnaLine 7-37 (31 entries) had `linkedGemaraLineIds`
entirely empty, carrying the older generic descriptive-style filler
text throughout. The whole daf was rebuilt using the list-indexed
methodology.

All 37 raw Rashi print lines were read against the raw Gemara text
and the 6 real captured line ids, using the multi-DH rule. The
correspondence: vilnaLine 1-3 (whether an interposition invalidates
this immersion, given it is merely a formality) to `l01`; 4-12
(whether partial entry counts as entry, the long-knife hypothetical,
its irrelevance to the offering's own validity per Zevachim 32b) to
`l02`; 13-16 (the question restated for Ben Zoma and for the Rabbis
who disagree with Rabbi Yehuda, identifying both disputants) to `l07`;
17-35 (Rashi's own extended geographic and structural excursus on Ein
Eitam's height, tracing the verse in Joshua 15 and the Zevachim 54b
account of the Temple's siting, then the mikveh-construction
reasoning for the specific twenty-three-cubit figure) to `l14`; 36
(the Ulam's exceptional forty-by-twenty measurement) to `l20`. `l10`
(the Rabbis' own elaboration of the "let it be asked" question) has
no dedicated vilnaLine of its own in this daf's column, the same
established folding pattern seen throughout this run.

One drafting slip was caught and fixed before applying: the initial
draft merged vilnaLine 35's own content ("for water to rise to a
mountain that is higher") with vilnaLine 36's opening clause ("than
the place from which it springs"), assigning the combined phrase to
vilnaLine 35 alone and leaving vilnaLine 36 to open directly with the
unrelated Ulam citation. The mandatory post-edit full-index
comparison against the raw array caught this before commit; the split
was corrected so vilnaLine 35 ends at its own raw line's own content
and vilnaLine 36 opens with its own raw line's own content before the
Ulam citation.

vilnaLine 37, the daf's final truncated word "והאיכא" (but is there
not), is the same kind of boundary case as every other daf ending in
this run: per the policy, it is linked to `yoma-031a-l20`, 31a's own
final locally captured Gemara line (the Ulam's exceptional
measurement), even though the DH's own point is itself still open at
the point of truncation. 31b's own opening line ("והאיכא אמה. עובי
תקרה על חלל השער") was read read-only to confirm this word begins a
dibbur hamatchil about an added cubit of ceiling thickness over the
gate's own chamber, continuing onto 31b; no edit was made to 31b.

All 37 entries were fixed in a single list-indexed pass, verified by
a full side-by-side comparison of every index against the raw array
before applying (including the one caught-and-corrected slip above).
31a is fully resolved, 37/37. This is the ninth consecutive
dangling-link daf found in this corpus (27a, 27b, 28a, 28b, 29a, 29b,
30a, 30b, 31a).

## 31b, full daf (VERSION 15.34), tenth dangling-link daf, densest sugya of the run

Continuing the run. Before any edit, the 31a/31b boundary was
re-verified read-only: 31a's truncated final word "והאיכא" (but is
there not) is completed by 31b's opening "והאיכא אמה. עובי תקרה על
חלל השער", continuing the same dibbur hamatchil cleanly in both the
Gemara and Rashi columns. No edit was made to 31a.

The mandatory preflight raw-count check was run first: talmud.dev's
non-empty raw Rashi array for 31b has 63 lines, matching the prior
enrichment JSON's 63 `rashiTranslations` entries exactly.

Checking every existing `linkedGemaraLineIds` value against 31b's 10
real captured ids (`l01`, `l04`, `l08` (mishna), `l12`, `l16`, `l18`,
`l22`, `l27`, `l29`, `l37`) found the same pattern as the prior daf:
vilnaLine 4-9 pointed to nonexistent unpadded ids, and vilnaLine
11-63 (53 entries) had `linkedGemaraLineIds` entirely empty, carrying
the older generic descriptive-style filler text throughout. The whole
daf was rebuilt using the list-indexed methodology.

This is the densest sugya encountered in the run so far: a single
real mishna line (`l08`) spans the entire High Priest vestry
procedure from drying off through the daily-offering's notching, and
a single real gemara line (`l22`) carries Rav Pappa's full analysis
including the two-sanctification derivation from the repeated verb
"and he shall bathe," requiring unusually careful line-by-line
tracking since both Rabbi Meir's view (within `l22` itself) and the
Rabbis' contrasting view (`l27`, opening only after `l22`'s own text
concludes) share overlapping vocabulary ("מקיש פשיטה ללבישה," "מה
לבישה... אף פשיטה") that could otherwise be mistaken for a repeated
citation of the same real line rather than two adjacent ones.

The correspondence: vilnaLine 1-2 (the cubit of ceiling and plaster
accounted for) to `l01`; 3-6 (the minimal marble thickness, then why
specifically linen garments for the sheet) to `l04`; 7-22 (the whole
undressing-through-daily-offering mishna, including the "notched it,"
"on his behalf" idiom traced to the Book of Ezra) to `l08`; 23 (the
morning incense's own placement in the service order) to `l12`; 24-30
(heating water for an elderly or delicate High Priest, the verbs for
"tempering" traced to Genesis, Beitza, and Jeremiah) to `l16`; 31-44
(the Rabbanan's report to Rav Pappa that the mishna does not match
Rabbi Meir, since he reverses the sanctification/undressing order)
to `l18`; 45-57 (Rav Pappa's resolution and Rabbi Meir's own view,
deriving two sanctifications from the doubled "and he shall bathe")
to `l22`; 58-59 (the Rabbis' contrasting view, opening only once
`l22`'s own text is fully glossed) to `l27`; 60-62 (the Rabbanan's
challenge from a baraita, and Rav Pappa's reply) to `l29`.

vilnaLine 63, the daf's final truncated word "עשרה" (ten), is the
same kind of boundary case as every other daf ending in this run: per
the policy, it is linked to `yoma-031b-l37`, 31b's own final locally
captured Gemara line ("granted according to Rabbi Meir, this is how
you find it"), even though the DH's own point is itself still open
at the point of truncation. 32a's own opening line ("עשרה קידושין.
לחמש טבילות") was read read-only to confirm this word begins a
dibbur hamatchil about the ten sanctifications for the mishna's five
immersions, continuing onto 32a; no edit was made to 32a.

All 63 entries were fixed in a single list-indexed pass, verified by
a full side-by-side comparison of every index against the raw array
before applying; no drafting slips survived to the applied version
this time. 31b is fully resolved, 63/63. This is the tenth
consecutive dangling-link daf found in this corpus (27a, 27b, 28a,
28b, 29a, 29b, 30a, 30b, 31a, 31b).

## 32a, full daf (VERSION 15.35), eleventh dangling-link daf, closes the 30a-32b run

Continuing the run. Before any edit, the 31b/32a boundary was
re-verified read-only: 31b's truncated final word "עשרה" (ten) is
completed by 32a's opening "עשרה קידושין. לחמש טבילות", continuing
the same dibbur hamatchil cleanly in both the Gemara and Rashi
columns. No edit was made to 31b.

The mandatory preflight raw-count check was run first: talmud.dev's
non-empty raw Rashi array for 32a has 62 lines, matching the prior
enrichment JSON's 62 `rashiTranslations` entries exactly.

Checking every existing `linkedGemaraLineIds` value against 32a's 10
real captured ids (`l01`, `l03`, `l07`, `l10`, `l16`, `l24`, `l27`,
`l29`, `l31`, `l37`) found the same pattern as the prior daf:
vilnaLine 5-7 pointed to nonexistent unpadded ids, and vilnaLine
11-62 (52 entries) had `linkedGemaraLineIds` entirely empty, carrying
the older generic descriptive-style filler text throughout. The whole
daf was rebuilt using the list-indexed methodology.

One drafting slip was caught and fixed before applying: the initial
draft merged vilnaLine 6's own content ("Meir, he does not sanctify
at all, since he does not come") with vilnaLine 7's opening clause
("to wear sacred garments. Then opens 'and Aaron shall come to'"),
assigning the combined phrase to a single entry tagged with `l03`
alone, silently dropping vilnaLine 6's own `l01` target. Counting
`ITEMS` against the raw array (61 vs. 62) caught the discrepancy
immediately, before any full-index comparison was even needed; the
merge was split back into its own two entries, vilnaLine 6 keeping
`l01` and vilnaLine 7 opening `l03`, matching the raw print-line
boundary exactly.

Two real captured lines needed careful disambiguation because their
own text shares near-identical phrasing: `l22`/`l27`'s equivalent
pair in 31b ("מקיש פשיטה ללבישה, מה לבישה... אף פשיטה") recurs here
between `l27` (Rebbi's own two-sanctification derivation) and the
handoff into `l29`/`l31` (Rabbi Elazar b'Rabbi Shimon's kal vachomer
and its own "מה לבישה טעון קידוש" verse-exposition, phrased almost
identically to the earlier design). Close reading of each real line's
own full text (not just its opening words) was required to place
vilnaLine 60's "מה לבישה טעון קידוש" gloss correctly against `l31`
rather than the more obvious-seeming `l29`.

The correspondence: vilnaLine 1-6 (the nine-versus-ten sanctification
count for the Rabbis, the last sanctification's own placement) to
`l01`; 7-28 (why Aaron comes to the Tent of Meeting only to remove
the ladle and fire-pan, Rashi's extended excursus on the passage's
own out-of-order verse sequence) to `l03`; 29-45 (Rav Chisda's
tradition of five immersions and ten sanctifications, Rashi's full
accounting of which service is performed in which garment) to `l07`;
46-51 (Rabbi Yehuda's own verse derivation, "from service to
service") to `l10`; 52-56 (Rebbi's alternate verse derivation from
the linen-tunic passage) to `l16`; 57-58 (Rebbi's derivation of the
two sanctifications from the doubled "and bathe") to `l27`; 59
(Rabbi Elazar b'Rabbi Shimon's kal vachomer opening) to `l29`; 60-61
(the verse basis for the kal vachomer's own conclusion, and why he
does not also derive sanctification from "and he shall remove and
bathe") to `l31`. `l24` (the mishna's own five-service enumeration,
already covered by Rashi's parallel accounting under `l07`) has no
dedicated vilnaLine of its own in this daf's column, the same
established folding pattern seen throughout this run.

vilnaLine 62, the daf's final truncated word "כפרתן" (their
atonement), is the same kind of boundary case as every other daf
ending in this run: per the policy, it is linked to `yoma-032a-l37`,
32a's own final locally captured Gemara line (deriving the golden
garments from white and the reverse), even though the DH's own point
is itself still open at the point of truncation. 32b's own opening
line ("כפרתן מרובה. שמשמש בהן כל ימות השנה") was read read-only to
confirm this word begins a dibbur hamatchil comparing the broader
atonement of garments worn all year to the narrower atonement of the
inner Yom Kippur service, continuing onto 32b; no edit was made to
32b.

All 62 entries were fixed in a single list-indexed pass, verified by
a full side-by-side comparison of every index against the raw array
before applying (including the one caught-and-corrected slip above).
32a is fully resolved, 62/62. This is the eleventh consecutive
dangling-link daf found in this corpus (27a, 27b, 28a, 28b, 29a, 29b,
30a, 30b, 31a, 31b, 32a), and closes the 30a-32b portion of the
resumed run pending 32b.

## 32b, full daf (VERSION 15.36), twelfth dangling-link daf, closes the 30a-32b run

Continuing the run. Before any edit, the 32a/32b boundary was
re-verified read-only: 32a's truncated final word "כפרתן" (their
atonement) is completed by 32b's opening "כפרתן מרובה. שמשמש בהן כל
ימות השנה", continuing the same dibbur hamatchil cleanly in both the
Gemara and Rashi columns. No edit was made to 32a.

The mandatory preflight raw-count check was run first: talmud.dev's
non-empty raw Rashi array for 32b has 55 lines, matching the prior
enrichment JSON's 55 `rashiTranslations` entries exactly.

Checking every existing `linkedGemaraLineIds` value against 32b's 14
real captured ids (`l01`, `l06`, `l11`, `l14`, `l17`, `l20`, `l24`,
`l27`, `l28`, `l34`, `l38`, `l42`, `l47`, `l49`) found the same
pattern as the prior daf: vilnaLine 2-10 and 13 pointed to
nonexistent unpadded ids, and vilnaLine 15-55 (41 entries) had
`linkedGemaraLineIds` entirely empty, carrying the older generic
descriptive-style filler text throughout. The whole daf was rebuilt
using the list-indexed methodology.

Three consecutive real captured lines (`l11`, `l14`, `l17`) fold with
no dedicated vilnaLine of their own - the largest single fold run
found in this corpus so far. Close reading confirmed this rather than
assumed it: vilnaLine 9-10's own gloss ("golden garments are also
sacred") bridges directly from `l06`'s citation into `l20`'s own text
("but this is written regarding immersion"), with no raw print line
in between quoting any phrase unique to `l11`'s reverse kal-vachomer
(white garments' lesser atonement implying golden garments' greater
one must also require immersion) or `l14`'s rebuttal (distinguishing
white garments by their use in the innermost sanctum). Since both
`l11` and `l14` restate a kal-vachomer structure essentially already
covered on 32a, Rashi's own commentary here moves directly to the
newer two-sanctifications derivation without separately glossing
them.

The correspondence: vilnaLine 1-2 (the golden garments' own greater
atonement, and why that alone does not obligate immersion) to `l01`;
3-9 (Rebbi's own verse derivation from the sacred-linen-tunic
passage, and why golden garments count as "sacred" too) to `l06`;
10-13 (the verse's own literal subject is immersion, redirected to
sanctification since immersion is independently derived) to `l20`;
14-19 (why the two-sanctification derivation implies a sacred
place, and why the first immersion is exempt as a later rabbinic
enactment) to `l24`; 20-21 (Rabbi Yehuda's own alternate source for
immersion) to `l27`; 22-33 (Rav Chisda's account of how Rebbi's view
differs from both Rabbi Meir's and the Rabbis', with the two-
sanctification placement worked out relative to undressing and
dressing) to `l28`; 34-36 (Rav Acha bar Yaakov's rule that all agree
the second sanctification follows dressing) to `l34`; 37-45 (Rav
Acha the son of Rava's reconciliation of Rav Chisda and Rav Acha bar
Yaakov, and the resulting sanctification count for Rebbi) to `l38`;
46 (Ulla's "majority of two" measure for the daily-offering's
notching) to `l42`; 47-50 (Rabbi Yochanan and Reish Lakish's
agreement, and why the mishna needed to state both the bird's and
the animal's own majority rule) to `l47`; 51-54 (the possibility that
an incomplete slaughter is only rabbinically invalid, since the
concern is solely for the blood) to `l49`.

vilnaLine 55, the daf's final truncated word "לכך" (therefore), is
the same kind of boundary case as every other daf ending in this
run: per the policy, it is linked to `yoma-032b-l49`, 32b's own final
locally captured Gemara line, even though the DH's own point is
itself still open at the point of truncation. 33a's own opening line
("לכך שנינו כו'. ממשנה יתירא חדא בחולין וחדא בקדשים") was read
read-only to confirm this word begins a dibbur hamatchil explaining
why the mishna's teaching is needed twice, once for non-sacred and
once for sacred slaughter, continuing onto 33a; no edit was made to
33a.

All 55 entries were fixed in a single list-indexed pass, verified by
a full side-by-side comparison of every index against the raw array
before applying; no drafting slips survived to the applied version.
32b is fully resolved, 55/55. This is the twelfth consecutive
dangling-link daf found in this corpus (27a, 27b, 28a, 28b, 29a, 29b,
30a, 30b, 31a, 31b, 32a, 32b), and closes the resumed 30a-32b run.

## 33a, full daf (VERSION 15.37), thirteenth dangling-link daf, escalated from Haiku and resolved

Took over this daf after Haiku escalated: it could not confidently
infer the fold pattern between 33a's 64 raw talmud.dev Rashi print-
lines and the daf's real captured Gemara lines. Independently
re-read `assets/talmuddev/33a.json` (64 raw Rashi lines, 45 raw Gemara
lines) and `learning_data.js`'s actual built content before touching
anything.

The 32a/32b boundary and 32b/33a boundary were both already verified
read-only in the prior 32b entry above (33a's own opening line "לכך
שנינו כו'" was confirmed there to continue 32b's truncated "לכך"); no
further boundary work was needed at the 33a start.

The key discovery: 33a's real captured Gemara "lines" objects (the
ones with `he`/`en` gemara text, matching `validate_rashi.py`'s and
the app's actual render target) are `l01`, `l03`, `l09`, `l14`, `l17`,
`l22`, `l23`, `l27`, `l31`, `l32`, `l37`, `l41` - twelve ids, taken
from the Gemara's own `vilna_line` numbering, not from raw print-line
position. The daf's separate `argumentFlow` annotations use a
different, overlapping-but-distinct set of ids (`l07`, `l11`, `l13`,
`l16`, `l20`, `l35` do not exist as real `lines` objects at all - they
are argumentFlow-only conceptual-step markers). The 12 entries Haiku
had already assigned (vilnaLine 1-12) used a mix of both id sets,
so 6 of the 12 (`l07`, `l11`, `l13`, `l16`, `l20`, `l35`) pointed at
non-existent Gemara line objects - a different failure mode from the
generic-stub problem on vilnaLine 13-64, but still wrong. All 64
entries were rebuilt from scratch against the 12 real ids.

Reconstructing the real dibbur-hamatchil boundaries (roughly 30
distinct Rashi comments across the 64 print-lines) and cross-checking
each against the Gemara's own quoted phrases: vilnaLine 1-3 (the
rov-simanim conclusion and "mitzva to finish") to `l01`; vilnaLine
4-19 (Abaye's introduction through the incense-arrangement and
two-log setup, in the overview list) to `l03` - the largest fold on
this daf, since Rashi glosses this long overview list term by term
without a new Gemara line being captured until the list's next
raw-print-line clause; vilnaLine 20-26 (the blood/incense/limbs/
meal-offering/libation chain) to `l09`; vilnaLine 27-35 (libations to
musaf, and the "aleha hashlem" derivation) to `l14`; vilnaLine 36-38
(the "mokda"/"tukad" baraita gloss) to `l17`; vilnaLine 39-43 (the
"ve'eifoch ana" reversal question and its "great atonement" answer)
to `l22`; vilnaLine 44 (the "if you wish say" alternate answer's
close) to `l23`; vilnaLine 45-47 ("uve'er aleha") to `l27`; vilnaLine
48-58 (the Exodus 30 verse derivation through the facilitator/
"mechusar kefara" reasoning) to `l32` - the second-largest fold;
vilnaLine 59 (Rabbi Yirmeya's "category of wood") to `l37`; vilnaLine
60-64 (Abaye's "I learned it as tradition," Rava's Reish Lakish
citation, and the daf's own truncated final word) to `l41`. `l31`
(the "aleha is written twice" line) gets no dedicated Rashi comment
at all - Rashi moves directly from glossing `l27` to `l32` without a
separate gloss on this short, self-explanatory clause, the same kind
of no-fold gap already documented for 32b's `l11`/`l14`.

Several raw print-lines straddle a comment boundary (the tail of one
dibbur hamatchil and the head of the next on the same physical line).
Per the established convention, these were linked to the newly-opened
comment's Gemara line, with the English describing both halves.

vilnaLine 64, the daf's final raw print-line, is the single truncated
word "וכי" ("and behold"), matching the same truncation pattern as
every other daf boundary in this run; it is linked to `l41`, 33a's
own final locally captured Gemara line, continuing onto 33b (no edit
made to 33b).

All 64 entries were rebuilt in a single indexed pass (`fix_33a.py`,
not committed - a one-off local script), verified by recomputing the
Gemara-line-id distribution against the reconstructed comment
boundaries before applying. `validate:yoma`, `audit:order:yoma`,
`validate:en:yoma`, `validate:daftext:yoma`, `validate:rashi:yoma`,
`validate:literal:yoma`, and `validate:schema:yoma` all pass; `npm
test` and `npm run test:browser` (10/10) both pass. 33a is fully
resolved, 64/64. This is the thirteenth consecutive dangling-link daf
found in this corpus (27a, 27b, 28a, 28b, 29a, 29b, 30a, 30b, 31a,
31b, 32a, 32b, 33a). Haiku can resume the run at 33b.

## 33b, full daf (VERSION 15.38), fourteenth dangling-link daf, closes the run at 33b

Escalated from Haiku, same failure mode as every daf since 27a: of the
60 raw talmud.dev Rashi print-lines, only 13 were assigned
(vilnaLine 1-13), and that assignment mixed 5 ids that match real
captured Gemara lines (`l01`, `l07`, `l09`, `l20`, `l28`) with 8 ids
that do not exist as real `lines` objects at all (`l03`, `l08`, `l10`,
`l11`, `l12`, `l14`, `l17`, `l24` - argumentFlow-only conceptual
markers); vilnaLine 14-60 carried the generic
"Rashi commentary on line N of 33b" stub filler.

Independently re-read `assets/talmuddev/33b.json` (60 raw Rashi lines,
45 raw Gemara lines) and `learning_data.js`'s actual built content
before touching anything. The 33a/33b boundary was already verified:
33a's own final vilnaLine 64 is the truncated word "וכי" ("and
behold"), and 33b's raw Gemara line 1 opens "וכי עייל להיכל" - the
same word completing itself at the top of 33b, confirming no edit was
needed on either side of that seam.

The daf's real captured Gemara "lines" objects (the ones with he/en
gemara text) are `l01`, `l07`, `l09`, `l16`, `l18`, `l20`, `l26`,
`l28`, `l30`, `l35`, `l39`, `l41`, `l43` - thirteen ids, taken from the
Gemara's own vilna_line numbering. All 60 Rashi entries were rebuilt
from scratch against these 13 real ids, reconstructing the dibbur-
hamatchil boundaries by walking the raw Hebrew print-lines end to end
and cross-referencing each comment's opening lemma against the
Gemara's own quoted phrases.

Three of the daf's real Gemara lines get no dedicated Rashi comment at
all: `l30` (Ravina and Rav Ashi's exchange over whether the two-log
"in the morning" is superfluous), `l35` (the "what is different, five
lamps first" question and its wood-count answer), and `l39` (the
verse ordering the two lamps before the incense). A direct text search
confirmed none of their distinctive vocabulary (מייתר, אוקימנא,
חברתה, שנא, רובא, פחותות, קודמת לקטורת) appears anywhere in the raw
Rashi array, so this is a genuine content gap rather than a mapping
error - the same kind of no-fold gap already documented for 32b's
`l11`/`l14` and 33a's `l31`, just three lines wide this time because
Rashi treats the whole `l20`-through-`l39` stretch (the two "in the
morning" derivations for Reish Lakish's and Rabbi Yochanan's views) as
one continuous argument and only glosses the specific difficulties he
flags.

vilnaLine 1-12 (the altar-before-menorah layout and the two-log/
phylactery-order questions building to "let us stand it alongside
them - so why pulled outward") fold to `l01`; vilnaLine 13-19 (Reish
Lakish's "do not bypass a mitzva," applied to phylactery order) to
`l07`; vilnaLine 20-23 (the two extraneous "in the morning" instances
for the two logs) to `l09`; vilnaLine 24-29 (the "here three, here
two" count proof from Exodus 29) to `l16`; vilnaLine 30-32 ("although
here two and here two," the atonement-priority reasoning) to `l18`;
vilnaLine 33-38 ("if so, on what basis do you pause," Abba Shaul's
view) to `l20`; vilnaLine 39-44 (quoting ahead to Reish Lakish's own
answer, "to increase the sense of transition," and "well: to allow
time to go out and come in") to `l26`; vilnaLine 45-53 ("but according
to Rabbi Yochanan," the challenge that no other service can fill the
gap since everything is verse-ordered) to `l28`; vilnaLine 54-57 ("to
the matter with only one mention of morning," the daily-offering
verse) to `l41`; vilnaLine 58-60 ("from where is it derived that no
matter may precede," closing with the truncated "ת"ל") to `l43`.
Several raw print-lines straddle a comment boundary (the tail of one
dibbur hamatchil and the head of the next on the same physical line);
per the established convention, these were linked to the newly-opened
comment's Gemara line, with the English describing both halves.

vilnaLine 60, the daf's final raw print-line, is the single truncated
word "ת"ל" ("the verse teaches"); per the same boundary convention
used at every other daf seam in this run, it is linked to `l43`, 33b's
own final locally captured Gemara line, continuing onto 34a (no edit
made to 34a). Note for the record: the escalation brief assumed the
final line would link to `yoma-033b-l45`, but no `l44` or `l45` object
exists for this daf - a direct grep of `learning_data.js` confirms
`l43` is the last real captured Gemara line, the same pattern as
33a's own final line (`l41`, not a higher-numbered id).

All 60 entries were rebuilt in a single indexed pass (a one-off local
script, not committed), verified by recomputing the Gemara-line-id
distribution against the reconstructed comment boundaries before
applying. `validate:yoma`, `audit:order:yoma`, `validate:en:yoma`,
`validate:daftext:yoma`, `validate:rashi:yoma`, `validate:literal:yoma`,
and `validate:schema:yoma` all pass; `npm test` and `npm run
test:browser` (10/10) both pass. 33b is fully resolved, 60/60. This is
the fourteenth consecutive dangling-link daf found in this corpus
(27a, 27b, 28a, 28b, 29a, 29b, 30a, 30b, 31a, 31b, 32a, 32b, 33a, 33b),
closing out the run through 33b. Haiku can resume at 34a.

## 34a, full daf (VERSION 15.39), fifteenth dangling-link daf, escalated from Haiku, first of a 34a-35b batch

Batch escalation from Haiku (34a, 34b, 35a, 35b). Before any edit, the
33b/34a boundary was re-verified read-only: 33b's truncated final word
"ת\"ל" ("the verse teaches") is completed by 34a's opening raw Rashi
print-line, "ת\"ל וערך עליה העולה וגו'" ("the verse teaches: and he
shall place the burnt-offering upon it, etc."), the exact phrase 33b's
own final Gemara line quotes. No edit was made to 33b.

Same failure mode as every daf since 27a: of the daf's 46 raw
talmud.dev Rashi print-lines, only 12 were assigned (vilnaLine 1-12),
and only 3 of those 12 ids (`l01`, `l03`, `l24`) match real captured
Gemara lines; the other 9 (`l06`, `l09`, `l11`, `l13`, `l16`, `l19`,
`l22`, `l27`, `l30`) do not exist as `lines` objects for this daf, and
even the 3 real ids were attached to the wrong vilnaLine. vilnaLine
13-46 had no `linkedGemaraLineIds` at all (empty arrays).

The daf's real captured Gemara "lines" objects are `l01`, `l02a`,
`l02b`, `l03`, `l05`, `l08`, `l10`, `l12`, `l15`, `l16`, `l21`, `l24` -
twelve ids, taken directly from the raw print-line position
(`vilna_line` matches the numeric part of the id, with `l02a`/`l02b`
splitting one raw Gemara print line's two clauses into separate
captured lines). All 46 Rashi entries were rebuilt from scratch against
these 12 real ids by walking the raw Hebrew print-lines end to end and
matching each comment's opening lemma against the Gemara's own quoted
phrases.

The correspondence: vilnaLine 1-2 (the verse "ve'arach aleha ha'olah"
proves the burnt-offering is placed first) to `l01`; vilnaLine 3-5
(the "olah u-mincha" derivation that the meal-offering follows the
burnt-offering immediately) to `l02a`; vilnaLine 6-11 (the griddle-cake
is itself a meal-offering, so it too is tied to the tamid, proven from
the Numbers 28 tenth-ephah verse) to `l02b`; vilnaLine 12-16 ("zevach
u-nesachim" proving libations follow the sacrifice, then the Gemara's
own "tannai hi" - Rabbi Yishmael and Rabbi Akiva's dispute in Pesachim
58a) to `l03`; vilnaLine 17-19 ("ba-yom" implying full daylight, not
early morning) to `l05`; vilnaLine 19-24 (the "chuka chuka" verbal
analogy between the griddle-cakes' and frankincense-vessels' "chok
olam" phrasing) to `l08`; vilnaLine 25-26 (the question of why the
analogy is not extended to the libations too) to `l10`; vilnaLine
26-30 (the Rabbis' view that the incense interrupts before the lamps
are trimmed, glossing the mishna's own "between the blood and the
lamps") to `l12`; vilnaLine 30-32 ("actually it is the Rabbis' view,
and the mishna is not being precise about the full order") to `l15`;
vilnaLine 32-37 (the afternoon incense's relation to the limbs and
libations, and the morning-meal-offering/limb ordering analogy) to
`l16`; vilnaLine 37-40 (the "is it written like the limbs of the
morning" rejection of the analogy's extension to limbs) to `l21`;
vilnaLine 40-46 (the "quarter-hin" libation verse and Rabbi Yehuda
HaNasi's "morning is derived from evening" baraita) to `l24`.

vilnaLine 46, the daf's final raw print-line, is the single truncated
word "רבי" ("Rabbi"), the opening word of Rabbi [Yehuda HaNasi]'s
statement that continues onto 34b's own opening Rashi line ("רבי אומר
של ערבית משל שחרית..."), confirmed against 34b's raw Rashi array
before this fix was applied. Per the established boundary convention,
it is linked to `l24`, 34a's own final locally captured Gemara line; no
edit was made to 34b.

All 46 entries were rebuilt in a single indexed pass (a one-off local
script, not committed), verified by recomputing the Gemara-line-id
distribution and re-scanning `learning_data.js` for any remaining
linkedGemaraLineIds not present in the daf's real `lines` objects
(none found) before applying. `validate:yoma`, `audit:order:yoma`,
`validate:en:yoma`, `validate:daftext:yoma`, `validate:rashi:yoma`,
`validate:literal:yoma`, and `validate:schema:yoma` all pass; `npm
test` and `npm run test:browser` (10/10) both pass. 34a is fully
resolved, 46/46. This is the fifteenth consecutive dangling-link daf
found in this corpus (27a, 27b, 28a, 28b, 29a, 29b, 30a, 30b, 31a, 31b,
32a, 32b, 33a, 33b, 34a). Continuing the escalated 34a-35b batch at 34b.

## 34b, full daf (VERSION 15.40), sixteenth dangling-link daf, second of the 34a-35b escalated batch

Continuing the escalated batch. Before any edit, the 34a/34b boundary
was re-verified read-only: 34a's truncated final word "רבי" ("Rabbi")
is completed by 34b's opening raw Rashi print-line, "רבי אומר של ערבית
משל שחרית" ("Rabbi says: the evening is derived from the morning"),
matching the Gemara's own opening line 1 ("רַבִּי אוֹמֵר: עַרְבִית
מִשֶּׁל שַׁחֲרִית"). No edit was made to 34a.

Same failure mode again: of the 40 raw talmud.dev Rashi print-lines,
several were assigned (vilnaLine 1-8ish) but pointed at ids that do not
exist for this daf (`l01`, `l03`, `l11`, `l13` used without the `a`/`b`
suffix that the real captured lines actually carry, plus `l18`, `l22`
used where the real ids are `l17`/`l18`/`l23`), and multiple vilnaLine
entries in the middle of the daf had empty `linkedGemaraLineIds`
despite non-generic-looking `en` text.

The daf's real captured Gemara/mishna "lines" objects are `l01a`,
`l01b`, `l05`, `l08`, `l13`, `l17`, `l18` (the mishna beginning "they
brought him to the Parva chamber"), and `l23` - eight ids. All 40
Rashi entries were rebuilt from scratch against these eight real ids.

The correspondence: vilnaLine 1 (Rabbi's "evening from morning" and
the "one lamb" proof-text) to `l01a`; vilnaLine 2-4 (why both the
"one" and "your choice vows" derivations are needed - beautifying a
voluntary offering versus paying an obligatory debt in full) to `l05`;
vilnaLine 4-13 (the heated iron bars for the elderly/frail High
Priest's immersion water, "eshet" as a thick block, the tempering
question and Abaye's "unintentional" answer) to `l08`; vilnaLine 13-19
(the challenge from the leprous convert's circumcision beraita,
testing whether Abaye's own view is even consistent) to `l13`;
vilnaLine 19-27 (Abaye's own follow-up limiting the "unintentional"
leniency to Torah-level prohibitions, since tempering the immersion
water is only a rabbinic-level shevut concern) to `l17`; vilnaLine
28-31 (the mishna itself: the Parva chamber, the sequence of
undressing and sanctifying, Rabbi Meir's reversed order) to `l18`;
vilnaLine 32-39 (the morning Pelusium-linen garments versus the
afternoon Hodu/Cush-linen garments, with the Targum Yonatan citation
for "Hodu") to `l23`. `l01b` (Rabbah bar Ulla's own formal proof
"le-cheves ha-echad ... hevei omer zeh tamid shel shachar") gets no
dedicated Rashi comment of its own - Rashi's single comment on
vilnaLine 1 glosses Rabbi's opening position directly by previewing
this proof rather than commenting on it a second time when Rabbah bar
Ulla states it formally, the same kind of no-fold gap already
documented for earlier daf in this run.

vilnaLine 40, the daf's final raw print-line, is the single truncated
word "גמ'" ("Gemara"), the start of the next section-heading;
confirmed against 35a's raw Rashi array ("גמ' פרווה אמגושא...") before
this fix was applied, showing it opens 35a's own Gemara-heading
comment. Per the established boundary convention it is linked to
`l23`, 34b's own final locally captured Gemara line; no edit was made
to 35a.

All 40 entries were rebuilt in a single indexed pass (a one-off local
script, not committed), verified by recomputing the Gemara-line-id
distribution and re-scanning `learning_data.js` for any remaining
linkedGemaraLineIds not present in the daf's real `lines`/mishna
objects (none found) before applying. `validate:yoma`,
`audit:order:yoma`, `validate:en:yoma`, `validate:daftext:yoma`,
`validate:rashi:yoma`, `validate:literal:yoma`, and
`validate:schema:yoma` all pass; `npm test` and `npm run test:browser`
(10/10) both pass. 34b is fully resolved, 40/40. This is the sixteenth
consecutive dangling-link daf found in this corpus (27a, 27b, 28a,
28b, 29a, 29b, 30a, 30b, 31a, 31b, 32a, 32b, 33a, 33b, 34a, 34b).
Continuing the batch at 35a.

## 35a, full daf (VERSION 15.41), seventeenth dangling-link daf, third of the 34a-35b escalated batch

Continuing the escalated batch. Before any edit, the 34b/35a boundary
was re-verified read-only: 34b's truncated final word "גמ'" ("Gemara")
is completed by 35a's opening raw Rashi print-line, "גמ' פרווה אמגושא"
("Gemara: Parva - a sorcerer"), matching the Gemara's own opening line
1 ("גְּמָ׳ מַאי ״פַּרְוָה״? אָמַר רַב יוֹסֵף: פַּרְוָה אַמְגּוּשָׁא").
No edit was made to 34b.

This short daf (11 raw Gemara print-lines, 14 raw Rashi print-lines)
had all 14 `rashiTranslations` entries with empty `linkedGemaraLineIds`
- fully dangling rather than mismapped to wrong-but-real ids, the same
pattern as the tail of 33b and other daf in this run.

The daf's real captured Gemara "lines" objects are `l01`, `l02`, `l04`,
and `l08` - four ids. All 14 Rashi entries were rebuilt from scratch
against these four real ids. The correspondence: vilnaLine 1-2 ("Parva
- a sorcerer, who built it and whose name was Parva") to `l01`;
vilnaLine 2-11 (the Tanna's "number" question - why state "all
together thirty" when eighteen and twelve already total thirty, and
the answer that thirty is a fixed total permitting mixing between the
morning and afternoon garment allowances) to `l04`; vilnaLine 12-13
("linen, linen" written four times regarding the morning garments,
proving they must be the choicest linen) to `l08`. `l02` (the fine-
linen privacy screen, "so that he would recognize that the day's
service is in linen garments") gets no dedicated Rashi comment at all
- Rashi moves directly from glossing `l01` to `l04` without a separate
gloss on this short, self-explanatory clause, the same kind of no-fold
gap already documented for earlier daf in this run.

vilnaLine 14, the daf's final raw print-line, is the single truncated
word "מיתיבי" ("they raised an objection"), confirmed against 35b's
raw Rashi array ("מיתיבי גרסינן ברישא...") before this fix was
applied, matching 35b's own opening Gemara line ("מיתיבי ולבשו בגדים
אחרים..."). Per the established boundary convention it is linked to
`l08`, 35a's own final locally captured Gemara line; no edit was made
to 35b.

All 14 entries were rebuilt in a single indexed pass (a one-off local
script, not committed), verified by recomputing the Gemara-line-id
distribution and re-scanning `learning_data.js` for any remaining
linkedGemaraLineIds not present in the daf's real `lines` objects
(none found) before applying. `validate:yoma`, `audit:order:yoma`,
`validate:en:yoma`, `validate:daftext:yoma`, `validate:rashi:yoma`,
`validate:literal:yoma`, and `validate:schema:yoma` all pass; `npm
test` and `npm run test:browser` (10/10) both pass. 35a is fully
resolved, 14/14. This is the seventeenth consecutive dangling-link daf
found in this corpus (27a, 27b, 28a, 28b, 29a, 29b, 30a, 30b, 31a, 31b,
32a, 32b, 33a, 33b, 34a, 34b, 35a). Continuing the batch at 35b.

## 35b, full daf (VERSION 15.42), eighteenth dangling-link daf, closes the 34a-35b escalated batch

Continuing and closing the escalated batch. Before any edit, the
35a/35b boundary was re-verified read-only: 35a's truncated final word
"מיתיבי" ("they raised an objection") is completed by 35b's opening
raw Rashi print-line, "מיתיבי גרסינן ברישא..." ("we read 'they raise
an objection' first..."), matching the Gemara's own opening line 1
("מֵיתִיבִי: וְלָבְשׁוּ בְּגָדִים אֲחֵרִים..."). No edit was made to
35a.

This is the largest daf in the batch: 53 raw Gemara print-lines, 58 raw
Rashi print-lines, and all 58 `rashiTranslations` entries had empty
`linkedGemaraLineIds` before this fix (fully dangling, like 35a).

The daf's real captured Gemara/mishna "lines" objects are `l01`, `l02`,
`l03`, `l07`, `l12`, `l16`, `l20`, `l27`, `l32`, `l36`, `l39`, `l43`,
`l47`, `l49` (the mishna beginning "he came to his bull"), and `l50` -
fifteen ids. All 58 Rashi entries were rebuilt from scratch against
these fifteen real ids.

The correspondence: vilnaLine 1-12 (Rashi's own editorial note on
reading order, then the full analysis locating "and they shall wear
other garments" specifically on Yom Kippur via the Ezekiel-supported
verse about the outer court) to `l01`; vilnaLine 13-20 (both sides of
"is it not that 'other' means more distinguished," and the resolution
that it means lesser, since the second immersion's service only
clears the vessels rather than atoning) to `l02`; vilnaLine 21-31
("an individual's service" - the ladle and fire-pan clearing that
falls to whichever priest wears his own tunic, then "provided he gives
it to the community," including Rashi's own alternate explanation and
its difficulty) to `l03`; vilnaLine 32-38 (the "two ten-thousands"
value of Rabbi Elazar ben Charsom's mother's tunic, the "six-ply
thread" cross-reference, and the "wine in a glass" simile for how
sheer the linen was) to `l12`; vilnaLine 39-42 (the structural preview
of the poor/rich/wicked baraita: Hillel, Rabbi Elazar, and Joseph as
the three test cases) to `l16`; vilnaLine 43-44 ("trafa'ik," Hillel's
daily half-dinar wage) to `l20`; vilnaLine 45 ("they unloaded him" of
the snow) to `l27`; vilnaLine 46-49 ("angarya," the forced-labor
incident where Rabbi Elazar ben Charsom's own servants failed to
recognize him) to `l36`; vilnaLine 50-52a ("meshadelto," Potiphar's
wife's enticement, and "she wore for him") to `l39`; vilnaLine 52b-57
(the next mishna: the bull's head to the south and face west, the
Gemara's question about why it does not simply say "tail east, head
west," and the priest standing to the east) to `l49`. `l07` (Rabbi
Yishmael ben Pabi's hundred-maneh tunic story), `l32` (Rabbi Elazar ben
Charsom's thousand villages and ships), `l43` (Potiphar's wife's
threats and the thousand silver talents), and `l47` (the "in this
world"/"in the world to come" reading and the baraita's closing
sentence) get no dedicated Rashi comment at all in this daf's raw
column - Rashi picks up specific difficult words within these longer
aggadic narratives (like "trafa'ik" and "angarya") rather than glossing
every clause, the same kind of no-fold gap already documented
repeatedly in this run, just more frequent here given how much of this
daf is continuous aggada.

vilnaLine 58, the daf's final raw print-line, is the single word
"גמ'" ("Gemara") - not a mid-word truncation like the boundary markers
on most other daf in this run, but the section-heading label that
opens the next comment (on the confession formula in `l50`). Checked
against 36a's own raw Rashi array, which begins directly with its own
first real comment ("מאן שמעת ליה דאמר בין אולם ולמזבח...") rather than
repeating this heading - so unlike the 34b/35a seam, this is not a
literal word split across the daf boundary, just talmud.dev's line-
splitting placing the trailing heading marker on 35b's side. Per the
same established convention used for every other final-line boundary
case in this run, it is linked to `l50`, 35b's own final locally
captured Gemara line; no edit was made to 36a.

All 58 entries were rebuilt in a single indexed pass (a one-off local
script, not committed), verified by recomputing the Gemara-line-id
distribution and re-scanning `learning_data.js` for any remaining
linkedGemaraLineIds not present in the daf's real `lines`/mishna
objects (none found) before applying. `validate:yoma`,
`audit:order:yoma`, `validate:en:yoma`, `validate:daftext:yoma`,
`validate:rashi:yoma`, `validate:literal:yoma`, and
`validate:schema:yoma` all pass; `npm test` and `npm run test:browser`
(10/10) both pass. 35b is fully resolved, 58/58. This is the
eighteenth consecutive dangling-link daf found in this corpus (27a,
27b, 28a, 28b, 29a, 29b, 30a, 30b, 31a, 31b, 32a, 32b, 33a, 33b, 34a,
34b, 35a, 35b), closing out the escalated 34a-35b batch. Haiku can
resume at 36a.

## 36a, full daf (VERSION 15.43), nineteenth dangling-link daf, first of the explicitly user-approved 36a-52b frozen-corpus exception batch

Per direct user authorization (not agent-declared) covering 36a through
52b only, scoped to `rashiTranslations` (`linkedGemaraLineIds` and `en`
fields), this daf was resolved. 54 raw Rashi print-lines, 30 real
captured Gemara lines (`l01` through `l30`); all 54
`rashiTranslations` entries had empty `linkedGemaraLineIds` before this
fix (fully dangling).

The correspondence: vilnaLine 1-5 (the opening DH identifying "between
the vestibule and the altar" as north for slaughtering the most sacred
offerings, tracing it to the mishna's own bull-slaughter location) to
`l01`; vilnaLine 6-12 (the thirty-two-cubit width of the altar itself
and why only the portion of the courtyard directly opposite it counts
as "north," sourced from "on the side of the altar, northward") to
`l04`; vilnaLine 13-16 (extending "north" to include the area between
vestibule and altar even off that exact line) to `l06`; vilnaLine
17-19 (Rebbi's further extension to the full eleven-cubit priests'
tread-path) to `l07`; vilnaLine 20-30 (the long digression on "beit
hachalifot," the vestibule's fifteen-cubit overhang and its
twenty-four sacred-knife alcove windows) to `l08`; vilnaLine 31-34
("all agree it is invalid" there, since the altar is not visible, and
that this view is Rabbi Elazar b'Rabbi Shimon's alone) to `l09`;
vilnaLine 35-38 (unpacking "now, Rabbi against Rabbi Yosei adds" as a
non-literal formulation) to `l11`; vilnaLine 39-41 (the resolution that
the far point is valid for Rabbi Yosei but not for Rabbi Elazar) to
`l12`; vilnaLine 42-43 (why the mishna cannot follow Rebbi's broader
view) to `l13`; vilnaLine 44 (the alternative placement between the
altar's own north wall and the courtyard's north wall) to `l14`;
vilnaLine 45 (three short DHs sharing one raw print-line: the location
confirmed, then the High Priest's-weakness reason for bringing it
close) to `l16`; vilnaLine 46 ("for Rebbi too," the same weakness
reason, then "let us place it explicitly") to `l18`; vilnaLine 47
(why not facing away from the altar - "lest he pass excrement") to
`l19`; vilnaLine 48 (the resulting orientation of the bull's body) to
`l20`; vilnaLine 49 (the mishna's own semicha positions: north, west,
east) to `l21`; vilnaLine 50 (the confession formula: "sin of a
sin-offering," and the burnt-offering's confession over gleanings,
forgotten sheaves, and the corner) to `l24`; vilnaLine 51 (the Tosefta
citation excluding "poor man's tithe" from that same confession list)
to `l26`; vilnaLine 52-53 (Rabbi Akiva's view that a burnt-offering
atones only for a positive commandment or a negative one convertible
to a positive one) to `l27`-`l28`.

vilnaLine 45 is a three-DH-per-print-line case (not previously this
dense in the run): "ממש התם הוא" concludes the prior DH, "אלא מאי אית
לך למימר" opens a new one, and "משום חולשא דכהן" opens a third, all
within one raw Rashi line; it was kept as a single entry describing all
three transitions rather than force-split, consistent with the
established multi-DH-per-line convention.

vilnaLine 54, the daf's final truncated word "בלאו" ("with a negative
commandment"), matches `l30`'s own text exactly (`l30` is itself just
this one word, "בלאו"), confirming the daf boundary lines up cleanly;
the DH continues onto 36b per the established boundary convention. No
edit was made to 36b at this stage.

All 54 entries were rebuilt in a single indexed pass, verified by a
full side-by-side comparison of every index against the raw array
before applying; no drafting slips survived to the applied version.
`validate:schema:yoma`, `validate:yoma`, `validate:en:yoma`,
`validate:daftext:yoma`, `validate:rashi:yoma`, `validate:literal:yoma`,
and `audit:order:yoma` all pass (the latter's 9 pre-existing warnings
at 39a, 47a, 51b, 77b, 79b are unrelated to this daf and untouched);
`npm test` and `npm run test:browser` (10/10) both pass. 36a is fully
resolved, 54/54. This is the nineteenth consecutive dangling-link daf
found in this corpus (27a through 36a), and the first daf fixed under
the explicit, directly-user-granted 36a-52b frozen-corpus exception.

## 36b, full daf (VERSION 15.44), twentieth dangling-link daf, second of the 36a-52b batch

Before any edit, the 36a/36b boundary was re-verified read-only: 36a's
truncated final word "בלאו" (with a negative commandment) is completed
by 36b's own opening Gemara line 1, "בלאו דנבילה קא מיפלגי" (they
dispute regarding a negative commandment of an unslaughtered carcass),
confirming a clean continuation with no edit needed to 36a.

62 raw Rashi print-lines, 46 real captured Gemara lines (`l01` through
`l46`); all 62 `rashiTranslations` entries had empty
`linkedGemaraLineIds` before this fix (fully dangling).

The correspondence: vilnaLine 1-5 (the opening DH on why the negative
commandment of eating an unslaughtered carcass cannot itself be
diverted to the positive "give it to the stranger" commandment) to
`l01`; vilnaLine 6-18 (Rabbi Akiva's and Rabbi Yosei HaGelili's
competing views on whether the same logic applies to gleanings,
forgotten sheaves, and the corner) to `l02`; vilnaLine 19-20 (Abaye's
unifying view that all agree the negative commandment of an
unslaughtered carcass is a proper one) to `l03`; vilnaLine 21-23
(introducing the parallel dispute over "you shall leave") to `l04`;
vilnaLine 24-26 (Rabbi Yosei's reasoning, explained before Rabbi
Akiva's even though the Gemara states Akiva's view first in the same
sentence) to `l06`; vilnaLine 27-29 (Rabbi Akiva's reasoning) to `l05`;
vilnaLine 30-31 (the scapegoat's confession formula, sins before
transgressions) to `l08`-`l09`; vilnaLine 32-34 (the rebellious/spiteful
sinner, and the two prooftexts about the king of Moab and Livna) to
`l13`-`l15`; vilnaLine 35-37 (why one confesses unwitting sins even
after confessing intentional ones) to `l18`; vilnaLine 38 (turning
intentional sins into unwitting ones through repentance) to `l27`;
vilnaLine 39-40 (Moshe's own verse as the scriptural support) to `l31`;
vilnaLine 41-44 (the prayer leader who structured the Yom Kippur
liturgy on the High Priest's own service order, closing with the Hosea
verse) to `l32`; vilnaLine 45-46 (the baraita on "and he shall atone"
being words of confession) to `l35`; vilnaLine 47-48 (the same
confession language for the scapegoat) to `l38`; vilnaLine 49-52 (the
gezeirah shavah's rejection as proof that atonement means only through
blood) to `l40`; vilnaLine 53-54 (the first proof from Aaron's own bull
verse) to `l41`; vilnaLine 55-57 (the proof that the bull was not yet
slaughtered when "he shall atone" is stated, so the atonement must be
verbal) to `l42`; vilnaLine 58-59 (why a different reason was still
needed) to `l43`; vilnaLine 60 (the rejected derivation from the inner
goat) to `l44`; vilnaLine 61 (the reason that derivation fails, since
the inner goat's atonement is through blood and has no confession) to
`l45`.

vilnaLine 24-29 is a reverse-order explanation: the Gemara states
Rabbi Akiva's view before Rabbi Yosei HaGelili's in one sentence
("דרבי עקיבא סבר תעזוב מעיקרא משמע ורבי יוסי הגלילי סבר השתא משמע"),
but Rashi explains Yosei's reasoning first (vilnaLine 24-26) and
Akiva's second (vilnaLine 27-29). This was verified as a deliberate
Rashi ordering choice, not a transcription error, since each comment's
own wording ("יוסי סבר השתא משמע" / "ור"ע סבר... מעיקרא") matches its
respective clause exactly; `linkedGemaraLineIds` reflects the actual
content match (`l06` then `l05`) rather than forcing strict left-to-
right monotonicity.

A first drafting pass of this fix mis-keyed vilnaLine 26 onward,
producing a one-line-ahead content shift for roughly the second half
of the daf (each `en` describing the next vilnaLine's raw Hebrew
instead of its own). This was caught during the mandatory full
side-by-side review before applying, not after; the entire vilnaLine
26-62 span was rebuilt line-by-line against the raw array a second
time and reverified clean before writing to disk.

vilnaLine 62, the daf's final truncated word "ומנין" ("and from
where"), matches `l46`'s own text exactly (`l46` is itself just this
one word), confirming the daf boundary lines up cleanly; the DH
continues onto 37a. No edit was made to 37a at this stage.

All 62 entries were rebuilt in a single indexed pass (after the
one drafting correction above), verified by a full side-by-side
comparison of every index against the raw array before applying; no
further slips survived to the applied version. `validate:schema:yoma`,
`validate:yoma`, `validate:en:yoma`, `validate:daftext:yoma`,
`validate:rashi:yoma`, `validate:literal:yoma`, and `audit:order:yoma`
all pass (the same 9 pre-existing warnings at 39a, 47a, 51b, 77b, 79b
are unrelated to this daf and untouched); `npm test` and
`npm run test:browser` (10/10) both pass. 36b is fully resolved, 62/62.
This is the twentieth consecutive dangling-link daf found in this
corpus (27a through 36b), the second daf fixed under the explicit
36a-52b frozen-corpus exception.

## 36a and 36b, linkedGemaraLineIds correction (VERSION 15.45), self-caught methodology error

Before starting 37a, a preflight check on 37a's real captured Gemara
ids revealed that the real `kind: "gemara"` paragraph ids in
`learning_data.js` are sparse (one id per paragraph, named by the
paragraph's own starting Vilna line, not one id per raw talmud.dev
print-line). The 36a and 36b fixes above had wrongly assumed a dense,
sequential id scheme (one id per raw print-line), producing
`linkedGemaraLineIds` values that mostly pointed at ids that do not
exist anywhere in `learning_data.js`.

A direct check confirmed the scope: 36a had 44 of 54 entries pointing
at non-existent ids (only 9 real ids exist for 36a: `l01`, `l02`,
`l09`, `l12`, `l15`, `l17`, `l20`, `l27`, `l29`); 36b had 53 of 62
entries wrong (only 11 real ids exist for 36b: `l03`, `l04`, `l06`,
`l13`, `l18`, `l28`, `l31`, `l34`, `l37`, `l40`, `l43`). A sweep of
27a through 36b confirmed this error was isolated to 36a and 36b (this
session's own work); 27a-35b, done by earlier agent passes, used the
correct sparse-id methodology already (one minor false alarm was
raised and cleared during the sweep: 35b vilnaLine 52-57's `l49` id is
a valid `kind: "mishna"` entry, not an error).

Both daf were corrected by re-deriving each entry's real id from the
real paragraph text (extracted directly from `learning_data.js`),
keeping every already-verified `en` description unchanged and only
replacing `linkedGemaraLineIds`. For 36a, several ranges collapse into
a single real id since one real paragraph spans what this session
had wrongly split into 4-7 separate fake ids (e.g. vilnaLine 6-32, the
entire "כנגד המזבח / בין האולם ולמזבח / רבי מוסיף / מן החליפות ולפנים
/ הכל מודים שפסול" span, is all one real paragraph, `l02`). For 36b,
vilnaLine 1-18 (the opening dispute framing and the Rabbi
Akiva/Rabbi Yosei HaGelili gleanings dispute, before Abaye's own
ruling) has no dedicated real id in 36b at all; since the boundary
policy forbids cross-daf `linkedGemaraLineIds` and no earlier id
exists on the 36b side, these entries are anchored to `l03` (36b's
own first real id) as a symmetric start-of-daf boundary case,
analogous to how a final truncated entry anchors to the daf's own
last real id.

Also corrected: both daf's final truncated entries had been linked to
a fabricated next-integer id (36a to a nonexistent `l30`, 36b to a
nonexistent `l46`) instead of the daf's actual final real id (`l29`
for 36a, `l43` for 36b); both are now corrected to the real ids.

This does not affect the live app: `linkedGemaraLineIds` is declared
`optional`/`status: "helper"` in `shared/schema_map.js`
("best-effort by dibur hamatchil, usable by tutor/image/learning
tools for context") and is not read anywhere in `app.jsx`; no
validator checks referential integrity of this field, which is why
the error passed every gate cleanly the first time. It was caught by
a manual cross-check against `learning_data.js` before starting 37a,
not by any automated gate.

`validate:schema:yoma`, `validate:yoma`, `validate:en:yoma`,
`validate:daftext:yoma`, `validate:rashi:yoma`, `validate:literal:yoma`,
and `audit:order:yoma` all pass; `npm test` and `npm run test:browser`
(10/10) both pass. No Rashi Hebrew, `en` text, or Gemara-learning
fields were touched in this correction pass, only
`linkedGemaraLineIds` values. Going forward for 37a onward, real ids
are extracted directly from `learning_data.js` (via a regex over
`kind: "gemara"` and `kind: "mishna"` entries, including the `l01a`/
`l01b` letter-suffixed split-line variant seen in some daf) before
building any vilnaLine-to-id mapping, rather than assumed from
talmud.dev's raw per-line array length.

## 37a, full daf (VERSION 15.46), twenty-first dangling-link daf, third of the 36a-52b batch

First daf fixed using the corrected methodology: real ids (17 total:
`l01`, `l05`, `l09`, `l16` (mishna), `l20`, `l23`, `l28`, `l30`, `l31`,
`l33`, `l35`, `l39`, `l44`, `l51`, plus three more folded into these
ranges) were extracted directly from `learning_data.js` before
building any mapping, confirmed against their own paragraph text.

71 raw Rashi print-lines, all fully dangling before this fix. The
correspondence: vilnaLine 1-3 (the gezeirah shavah source for the
confession word "anna") to `l01`; vilnaLine 4-8 (Abaye's own reasoning
for why the heifer-whose-neck-is-broken cannot derive from Chorev) to
`l05`; vilnaLine 9-11 (the baraita on invoking the Divine Name) to
`l09`; vilnaLine 12-27 (the new mishna's own opening through the
kalpi/lots/Ben Gamla details) to `l16`; vilnaLine 28-33 (Ben Katin's
laver spigots and mechanism) to `l20`; vilnaLine 34-41 (Helena's
menorah, the sotah tablet, and Nikanor's doors) to `l23`; vilnaLine
42-49 (the true Gemara discussion opening, on why "north of the altar"
implies the altar itself is not in the north) to `l28`; vilnaLine
50-52 (reconciling the mishna's opening clause with Rabbi Eliezer ben
Yaakov's own view) to `l30`; vilnaLine 53-59 (the bull's exact
position, close to the entrance because of the High Priest's
weakness) to `l31`; vilnaLine 60-64 (the three-who-walk-together
baraita and its angelic prooftext) to `l33`; vilnaLine 65-66 (Rav
Shmuel bar Pappa's reading, "so that his teacher be covered") to `l35`;
vilnaLine 67-69 (the two-lots baraita, why not two lots on the same
goat) to `l39`; vilnaLine 70 (the tzitz comparison, "should this too
be so") to `l44`; vilnaLine 71 (the daf's final truncated word) to
`l51`, the daf's own final real captured line (boundary policy;
Rashi's own comment on the "twelve spigots" recap at `l47` and the
mechanism at `l50` has no dedicated entry, a no-fold gap since Rashi
already explained both terms earlier at `l20`).

`validate:schema:yoma`, `validate:yoma`, `validate:en:yoma`,
`validate:daftext:yoma`, `validate:rashi:yoma`, `validate:literal:yoma`,
and `audit:order:yoma` all pass (the same 9 pre-existing warnings at
39a, 47a, 51b, 77b, 79b are unrelated); `npm test` and
`npm run test:browser` (10/10) both pass. A post-edit zero-bogus-id
check confirmed every `linkedGemaraLineIds` value resolves to a real
`learning_data.js` entry. 37a is fully resolved, 71/71. This is the
twenty-first consecutive dangling-link daf found in this corpus (27a
through 37a), the third daf fixed under the explicit 36a-52b
frozen-corpus exception.

## 37b, full daf (VERSION 15.47), twenty-second dangling-link daf, fourth of the 36a-52b batch

Real ids extracted directly from `learning_data.js` first, per the
corrected methodology: 6 real ids for this short daf (`l01`, `l04`,
`l08`, `l12`, `l14`, `l17`). 25 raw Rashi print-lines, all fully
dangling before this fix.

The correspondence: vilnaLine 1-3 (the vessel-handle and knife-handle
terminology, glossing "handles of axes and sickles") to `l01`;
vilnaLine 4-6 (the sun's own sparks marking the time for the morning
Shema) to `l04`; vilnaLine 7-18 (the priestly-watch/delegation dispute
over who recites first, its scriptural source, and the resolution
that "the rest of the people" is the true audience for the sign) to
`l08`; vilnaLine 19-21 (the Gittin cross-reference on writing a
practice scroll, and the acrostic method) to `l12`; vilnaLine 22-24
(the priest writing the sotah scroll by copying the acrostic tablet)
to `l14`; vilnaLine 25 (the daf's final truncated word) to `l17`, the
daf's own final real captured line (boundary policy).

Zero-bogus-id check confirmed all 25 `linkedGemaraLineIds` resolve to
real ids. `validate:schema:yoma`, `validate:yoma`, `validate:en:yoma`,
`validate:daftext:yoma`, `validate:rashi:yoma`, `validate:literal:yoma`,
and `audit:order:yoma` all pass (same 9 pre-existing unrelated
warnings); `npm test` and `npm run test:browser` (10/10) both pass.
37b is fully resolved, 25/25. This is the twenty-second consecutive
dangling-link daf found in this corpus (27a through 37b), the fourth
daf fixed under the 36a-52b frozen-corpus exception.

## 38a, full daf (VERSION 15.48), twenty-third dangling-link daf, fifth of the 36a-52b batch

Real ids extracted directly from `learning_data.js` first: 16 ids
including a letter-suffixed split-line pair (`l01a`, `l01b`) from the
carryover of 37b's own final truncated word "בסירוגין," which turns
out to be its own tiny one-word real paragraph (`l01a`) before the
Nikanor-doors story proper begins at `l01b`.

37 raw Rashi print-lines, all fully dangling before this fix. The
correspondence: vilnaLine 1-3 (completing the acrostic-letter
explanation for the sotah scroll begun on 37b) to `l01a`; vilnaLine
4-5 (the Nikanor-doors storm-at-sea story opening) to `l01b`;
vilnaLine 6-7 (reaching the harbor) to `l06`; vilnaLine 8-12 (the "our
rafters/covenant of the sea" wordplay and the gates changing to gold
except Nikanor's copper ones) to `l11`; vilnaLine 13-14 (the new
mishna's own opening, Hugras ben Levi) to `l16`; vilnaLine 15-17
(ben Kamtzar's four-quill writing technique) to `l17`; vilnaLine 18-20
(Beit Garmu's bread-baking technique the Alexandrian bakers could not
replicate) to `l18`; vilnaLine 21 (their doubled wages) to `l21`;
vilnaLine 22 (why they are praised) to `l24`; vilnaLine 23-26 (Beit
Avtinas's incense-blending and smoke-column technique) to `l27`;
vilnaLine 27 (Rabbi Yishmael's own closing line to Beit Garmu's
descendant, "and diminished their honor") to `l36`; vilnaLine 28-29
(Rabbi Akiva's report of the rising-smoke sign) to `l38`; vilnaLine 30
(the scroll of spice-names) to `l41`; vilnaLine 31-36 (ben Azzai's own
maxim, "by your own name they shall call you") to `l44`; vilnaLine 37
(the daf's final truncated word) to `l44`, the daf's own final real
captured line (boundary policy).

Zero-bogus-id check confirmed all 37 `linkedGemaraLineIds` resolve to
real ids. `validate:schema:yoma`, `validate:yoma`, `validate:en:yoma`,
`validate:daftext:yoma`, `validate:rashi:yoma`, `validate:literal:yoma`,
and `audit:order:yoma` all pass (same 9 pre-existing unrelated
warnings); `npm test` and `npm run test:browser` (10/10) both pass.
38a is fully resolved, 37/37. This is the twenty-third consecutive
dangling-link daf found in this corpus (27a through 38a), the fifth
daf fixed under the 36a-52b frozen-corpus exception.

## 38b, full daf (VERSION 15.49), twenty-fourth dangling-link daf, sixth of the 36a-52b batch

Real ids extracted directly from `learning_data.js` first: 16 ids
(`l01`, `l03`, `l06`, `l14`, `l19`, `l21`, `l23`, `l26`, `l29`, `l32`,
`l35`, `l39`, `l41`, `l44`, `l46`, `l49`). 49 raw Rashi print-lines,
all fully dangling before this fix.

The correspondence: vilnaLine 1-6 ("and from what is yours" and no
kingdom touching another's, illustrated by Belshazzar falling at night
and Tachpanches by day) to `l01`; vilnaLine 7-9 (Hugras ben Levi's
singing technique, finger between the lips) to `l03`; vilnaLine 10-14
(the "rakvivut/rust" wordplay and Doeg's own mother measuring him
daily) to `l14` (skipping `l06`'s own ben Kamtzar writing-technique
recap entirely, a no-fold gap, since Rashi already explained this
technique in 38a); vilnaLine 15-19 (Zecharia the priest-prophet, the
Doeg naming objection, "see what became of him") to `l19`; vilnaLine
20-22 ("a righteous person of his own accord... a wicked person
through his fellow") to `l21`; vilnaLine 23-25 ("I who conceal from
Abraham," the blessing that follows) to `l23`; vilnaLine 26 (Ovadia,
who dwelled between Achav and Izevel) to `l29` (skipping `l26`'s own
Sodom-derivation content, another no-fold gap); vilnaLine 27-28 (the
blessing/curse parallel) to `l32`; vilnaLine 29-30 ("and He saw the
light") to `l35`; vilnaLine 31-33 ("and He set the world upon them")
to `l41`; vilnaLine 34-35 ("the feet of His pious ones," the Lavan
prooftext) to `l44`; vilnaLine 36-40 (the singular/plural chasid
grammar point folding into "he no longer sins" and the two-strikes
rule) to `l46`; vilnaLine 41-48 (the "if for scoffers... if for the
humble" verse and the doors of impurity/purity opening themselves) to
`l49`; vilnaLine 49 (the daf's final truncated word) to `l49`, the
daf's own final real captured line (boundary policy).

Zero-bogus-id check confirmed all 49 `linkedGemaraLineIds` resolve to
real ids. `validate:schema:yoma`, `validate:yoma`, `validate:en:yoma`,
`validate:daftext:yoma`, `validate:rashi:yoma`, `validate:literal:yoma`,
and `audit:order:yoma` all pass (same 9 pre-existing unrelated
warnings); `npm test` and `npm run test:browser` (10/10) both pass.
38b is fully resolved, 49/49. This is the twenty-fourth consecutive
dangling-link daf found in this corpus (27a through 38b), the sixth
daf fixed under the 36a-52b frozen-corpus exception.

## 39a, full daf (VERSION 15.50), twenty-fifth dangling-link daf, seventh of the 36a-52b batch

Real ids extracted directly from `learning_data.js` first: 17 ids
(`l01`, `l03`, `l06`, `l10`, `l13`, `l14`, `l17`, `l19`, `l20`, `l21`,
`l24`, `l27`, `l28`, `l29`, `l32`, `l35`, `l38`). 59 raw Rashi
print-lines, all fully dangling before this fix.

The correspondence: vilnaLine 1 (the naphtha-buyer story carried over
from 38b, folding directly into "sin numbs the heart") to `l01`;
vilnaLine 2 (a person who defiles himself a little is left to defile
himself greatly) to `l06`; vilnaLine 3-4 (the parallel for
sanctification) to `l10`; vilnaLine 5 (the new mishna's own opening,
"we return to you") to `l13`; vilnaLine 6-12 (shaking the urn, the two
lots, the goats' own positions) to `l14`; vilnaLine 13-16 (why he must
not feel for the lot by touch) to `l19`; vilnaLine 17-24 (the profane
urn, the Torah's mercy on Israel's property, with Rashi's own extended
kal vachomer from leprous-house pottery through valuable and righteous
property) to `l21`; vilnaLine 25-26 (if the lot came up in the
deputy's own right hand) to `l24`; vilnaLine 27-29 ("since it did not
come up in his own hand," the High Priest's mind troubled) to `l27`;
vilnaLine 30-35 (why the deputy stands at the right, with Rashi's own
two-answer discussion citing Rabbi Yitzchak HaLevi and his own
teacher) to `l29`; vilnaLine 36-55 (the crimson tongue whitening, the
western lamp burning, its testimony to the Divine Presence, and the
extended dispute over which lamp is "western") to `l32`; vilnaLine
56 (the fire of the arrangement growing stronger by itself) to `l35`;
vilnaLine 57-58 (blessing withdrawn from the omer offerings, and the
doubled portions the modest priests would not take) to `l38`;
vilnaLine 59 (the daf's final truncated word) to `l38`, the daf's own
final real captured line (boundary policy).

A drafting slip was caught before applying: the first draft omitted a
dedicated entry for vilnaLine 13 ("when he invokes the Divine Name")
entirely, causing every subsequent entry to describe the next
vilnaLine's own raw Hebrew instead of its own (a one-line-ahead shift
for the rest of the daf). This was caught by the mandatory
`len(ITEMS) == len(raw)` assertion failing (58 vs 59) before any
application; the missing entry was located and inserted, and a full
side-by-side comparison of every index against the raw array confirmed
correctness before the second, corrected application.

Zero-bogus-id check confirmed all 59 `linkedGemaraLineIds` resolve to
real ids. `validate:schema:yoma`, `validate:yoma`, `validate:en:yoma`,
`validate:daftext:yoma`, `validate:rashi:yoma`, `validate:literal:yoma`,
and `audit:order:yoma` all pass (same 9 pre-existing unrelated
warnings); `npm test` and `npm run test:browser` (10/10) both pass.
39a is fully resolved, 59/59. This is the twenty-fifth consecutive
dangling-link daf found in this corpus (27a through 39a), the seventh
daf fixed under the 36a-52b frozen-corpus exception.

## 39b, full daf (VERSION 15.51), twenty-sixth dangling-link daf, eighth of the 36a-52b batch

Real ids extracted directly from `learning_data.js` first: 19 ids
including two letter-suffixed split-line pairs (`l01a`/`l01b`,
`l47a`/`l47b`, `l50a`/`l50b` - three pairs total). 65 raw Rashi
print-lines, all fully dangling before this fix.

The correspondence: vilnaLine 1 (the "chometz/robber" wordplay
carried over as the tail of 39a's own truncated word) to `l01a`;
vilnaLine 2 (the Sanhedrin cross-reference on attending to the
plaintiff first) to `l01b`; vilnaLine 3 (priests refraining from the
explicit-Name blessing) to `l12`; vilnaLine 4-5 (the Sanctuary doors
opening by themselves, Zecharia's own prophecy) to `l16`; vilnaLine
6-8 (the ten Divine-Name invocations, the confession formulas) to
`l32`; vilnaLine 9-10 (Shimon HaTzaddik's own voice heard as far as
Jericho) to `l35`; vilnaLine 11 (a bride's own perfuming) to `l36`;
vilnaLine 12-13 (the goats of Michmar sneezing from the incense scent)
to `l39`; vilnaLine 14-28 (the lot-raising-versus-placement dispute
over what is indispensable) to `l42`; vilnaLine 29-58 (the extended
sugya on Rabbi Yehuda's and Rabbi Nechemia's own positions on
indispensability for white-garment services, including Rashi's own
long parenthetical aside on why the lottery is not classified as
"avoda") to `l43`; vilnaLine 59-60 ("all agree it is indispensable,"
the alternate version's own opening) to `l47b`; vilnaLine 61-64 (the
resolution that a superfluous verse teaches indispensability
specifically here) to `l50b`; vilnaLine 65 (the daf's final truncated
word) to `l50b`, the daf's own final real captured line (boundary
policy). `l47a`'s own two-word transition marker ("some say") and
`l50a`'s own objection text get no dedicated Rashi comment, a no-fold
gap consistent with the pattern seen throughout this corpus.

A drafting slip in the first pass of the vilnaLine 29-58 span (a dense
halachic sugya) produced 28 entries for what needed to be 30, caught
by the mandatory `len(ITEMS) == len(raw)` assertion failing (63 vs 65)
before any application; the entire span was rebuilt line-by-line
against the raw array a second time, and a full side-by-side
comparison of all 65 entries confirmed correctness before applying.

Zero-bogus-id check confirmed all 65 `linkedGemaraLineIds` resolve to
real ids. `validate:schema:yoma`, `validate:yoma`, `validate:en:yoma`,
`validate:daftext:yoma`, `validate:rashi:yoma`, `validate:literal:yoma`,
and `audit:order:yoma` all pass (same 9 pre-existing unrelated
warnings); `npm test` and `npm run test:browser` (10/10) both pass.
39b is fully resolved, 65/65. This is the twenty-sixth consecutive
dangling-link daf found in this corpus (27a through 39b), the eighth
daf fixed under the 36a-52b frozen-corpus exception.

## 40a, full daf (VERSION 15.52), twenty-seventh dangling-link daf, ninth of the 36a-52b batch

Escalated from a prior session that got stuck on one placement question
(see below). Real ids extracted directly from `learning_data.js` first:
15 ids (`l01`, `l03`, `l04`, `l07`, `l10`, `l15a`, `l15b`, `l16`, `l19`,
`l21`, `l23`, `l27`, `l28`, `l29`, `l31`), including one letter-suffixed
split pair (`l15a`/`l15b`, the two clauses of one baraita sentence: "the
bull disqualifies the goat" and "the goat does not disqualify the bull,
regarding the inner sprinklings"). 65 raw Rashi print-lines, all fully
dangling before this fix.

**The escalated question.** The phrase "at the inner gifts" (`במתנות
שבפנים`) appears twice in 40a's real Gemara text: once in `l15b`'s own
text (the baraita's original statement) and again in `l27` (a later
challenge quoting it back: "but it explicitly teaches 'at the inner
gifts'!"). Raw Rashi vilnaLine 51 ("`במתנות שבפנים. קאמרי דסדר הפר
מעכב את השעיר`") glosses this phrase, and it was unclear from the
Hebrew alone which occurrence it targets.

Resolved to `l15b`, not `l27`, on two independent grounds. First,
textual: the catchword "at the inner gifts" is quoted verbatim only in
`l15b`'s own text; `l27`'s text is "but it explicitly teaches 'at the
inner gifts'!", a challenge that reuses the phrase but is not itself
the phrase's source. Second, and decisively, positional: Rashi's print
comments run strictly in the Gemara's own linear order down the page.
Comments unambiguously matching `l16` (vilnaLine 53-54), `l19`
(vilnaLine 55-57), `l21` (vilnaLine 58-61), `l23` (vilnaLine 62), and
`l29` (vilnaLine 63) all appear later in the print sequence than
vilnaLine 51. Since `l27` comes after `l23` in the Gemara's own order,
a comment on `l27` would have to appear after the comments on `l16`,
`l19`, `l21`, and `l23` in the print, not before them. VilnaLine 51
appears before all of them, so it cannot be commenting on `l27`. The
comment's own content confirms this: it clarifies the scope of the
baraita's original two-clause statement ("they mean that this
qualifies the sequencing whereby the bull disqualifies the goat"),
which is what a first-pass gloss on `l15b` does, not what a
challenge-response gloss on `l27` would say.

The correspondence: vilnaLine 1-2 (with a one-word tail into vilnaLine
3, "Nechemia's:") the setup naming which Tanna the emended baraita
fits, to `l01`; vilnaLine 3-7 (the emendation "teach: it is a mitzva to
place," with Rashi's own proof from the verses being written once for
placing but twice for raising) to `l03`; vilnaLine 8-9 (the "and to
confess" clause) to `l04`; vilnaLine 10-18 ("if we say he did not
place," Rabbi Shimon's view on raising, and the goat-died baraita
cross-referenced to 62a) to `l07`; vilnaLine 19-36 ("Rabbi Shimon did
not know," Rashi's own two-branch resolution distinguishing actual
drawing from placing, closing with the reason for both being folded
into the confession) to `l10`; vilnaLine 37-48 (the long service-order
comment on "the bull disqualifies the goat," listing the full
confession/lottery/sprinkling sequence) to `l15a`; vilnaLine 49-51 ("the
goat does not disqualify the bull" and the "at the inner gifts"
qualifier, per the escalated resolution above) to `l15b`; vilnaLine 52
(continuing "if he advanced it for the goat, regarding the sprinkling
between the poles," which returns to elaborate `l15a`'s own case) back
to `l15a`; vilnaLine 53-54 ("what is this referring to," restating the
question with "at the inner gifts") to `l16`; vilnaLine 55-57 ("in the
Sanctuary, on the curtain" and "'statute' is written of them") to
`l19`; vilnaLine 58-61 ("rather, is it not that he advanced the bull's
inner gifts before the drawing" and the sequencing-implies-drawing
challenge) to `l21`; vilnaLine 62 ("that he advanced the bull's gifts,"
on the altar, with the Leviticus 16 proof-text) to `l23`; vilnaLine 63
("and granted that by sequence it is not indispensable, the drawing
itself is") to `l29`; vilnaLine 64 ("and they follow their own
reasoning," Rashi's own girsa note on reading order) to `l31`;
vilnaLine 65 (the daf's final truncated word, "let it stand") to `l31`,
the daf's own final real captured line (boundary policy; confirmed
against 40b's own opening Rashi line, "let it stand, alive," which
continues the same dibbur hamatchil). `l27` and `l28` (the challenge
itself and its "rather, it's Rabbi Shimon's" answer) get no dedicated
Rashi comment, a no-fold gap consistent with the pattern seen
throughout this corpus.

Zero-bogus-id check confirmed all 65 `linkedGemaraLineIds` resolve to
real ids. `validate:schema:yoma`, `validate:yoma`, `validate:en:yoma`,
`validate:daftext:yoma`, `validate:rashi:yoma`, `validate:literal:yoma`,
and `audit:order:yoma` all pass (same 9 pre-existing unrelated
warnings); `npm test` and `npm run test:browser` (10/10) both pass.
40a is fully resolved, 65/65. This is the twenty-seventh consecutive
dangling-link daf found in this corpus (27a through 40a), the ninth
daf fixed under the 36a-52b frozen-corpus exception.

## 40b, full daf (VERSION 15.53), twenty-eighth dangling-link daf, tenth of the 36a-52b batch, closes the 37b-40b run

Real ids extracted directly from `learning_data.js` first: 12 ids
(`l01`, `l04`, `l07`, `l09`, `l11`, `l15`, `l17`, `l20`, `l22`, `l25`,
`l27`, `l29`). 43 raw Rashi print-lines, all fully dangling before
this fix. No pre-existing bogus ids found (clean starting state,
unlike 36a/36b).

The correspondence: vilnaLine 1-4 (the "he shall stand alive" verse,
proving a dead goat must be replaced) to `l01`; vilnaLine 5-9 (Rabbi
Yehuda's own reading, that atonement means through blood, so
confession does not preclude) to `l04`; vilnaLine 10-13 (Rabbi
Shimon's own view, and Rashi's own note that the two disputed points,
lottery and confession, cannot both be established) to `l07`;
vilnaLine 14-18 (Rashi's further elaboration on the same "and when he
has finished atoning" verse, tracing exactly how long the goat must
stay alive) to `l04` (Rashi returns to elaborate the Rabbi Yehuda
citation a second time before moving on, rather than strict
line-by-line advance); vilnaLine 19-23 ("it came up on the left," and
the "do not give room to the Sadducees" caution) to `l09`; vilnaLine
24 (why we would otherwise switch the lot back) to `l11`; vilnaLine
25-28 (once the lot has risen, placement is no longer indispensable
though still a mitzva) to `l17`; vilnaLine 29 ("and the Name does
not" designate without a lottery) to `l25`; vilnaLine 30-42 (the
kal vachomer from bird-offerings, that if the lottery designates a
sin-offering versus a burnt-offering, the name should too) to `l27`;
vilnaLine 43 (the daf's final truncated word) to `l29`, the daf's own
final real captured line (boundary policy). `l15`, `l20`, and `l22`
get no dedicated Rashi comment, no-fold gaps since they restate
positions (Rava's own rephrasing) that Rashi had already glossed via
the parallel Sadducee/Azazel material.

Zero-bogus-id check confirmed all 43 `linkedGemaraLineIds` resolve to
real ids. `validate:schema:yoma`, `validate:yoma`, `validate:en:yoma`,
`validate:daftext:yoma`, `validate:rashi:yoma`, `validate:literal:yoma`,
and `audit:order:yoma` all pass (same 9 pre-existing unrelated
warnings); `npm test` and `npm run test:browser` (10/10) both pass.
40b is fully resolved, 43/43. This is the twenty-eighth consecutive
dangling-link daf found in this corpus (27a through 40b), the tenth
daf fixed under the 36a-52b frozen-corpus exception, and closes the
37b-40b run agreed as the checkpoint before the next report.

## 40b, vilnaLine 13-19 (VERSION 15.54), post-session English-helper shift correction

A post-session read-only verification of 40b (prior to starting 41a audit) found one one-line-ahead shifted-English block affecting vilnaLine 14-18. The block described the Gemara line correctly (l04, Rashi's elaboration on the "when he has finished atoning" verse), but the English helper text for each vilnaLine was describing the *next* vilnaLine's raw Hebrew instead of its own. Edge-bleed inspection of vilnaLine 12-20 confirmed the shift started at vilnaLine 14 (which absorbed opening words from HE 14 but continued with content from HE 15) and ran through vilnaLine 18 (which was only "the confession," re-syncing with HE 19's opening word). linkedGemaraLineIds for the block all pointed to l04 and were correct; only the en fields needed repair.

Repair method: each vilnaLine 14-18 en was rewritten to describe its own raw Rashi print line only, preserving structure ("Rashi: opens/continues/concludes") and word-level accuracy. No linkedGemaraLineIds values were changed. Vilnaline 13 and 19-20 were verified to be in correct alignment and left unchanged. Zero-bogus-id check and full validation/build/test suite confirm all 43 linkedGemaraLineIds still resolve to real ids and the block now correctly maps per-line en to per-line raw Hebrew. 40b remains fully resolved, 43/43.

## 20b, vilnaLine 19-35 (VERSION 15.29), pre-existing content-shift correction found by spot check

A post-hoc spot check of the completed 21a-29b work (sampling 40
entries across 20a, 20b, 21a, 22b, 23a, 24b, 25a, 26b, 27a, 27b, 28a,
28b, 29a, 29b) found one failure: 20b vilnaLine 31's `en` text
described vilnaLine 32's own raw Hebrew, not its own. Dumping all 41
entries of 20a and all 62 entries of 20b side by side (raw Hebrew
against `en`) confirmed this is isolated to 20b and is a pre-existing
issue inherited from before this run began at 21a; 20a and the rest of
20b (vilnaLine 1-18, 33-62) show no shift.

Re-inspecting vilnaLine 18-35 (wider than the original 20-32 estimate,
per instruction, to catch edge bleed) against the raw Hebrew found the
actual affected span is vilnaLine 19-35 (17 entries, not 13): the
drift starts as a partial two-line merge at vilnaLine 19 (which had
folded in the first clause of vilnaLine 20's own Hebrew), runs as a
clean one-line-ahead shift from vilnaLine 20 through 31, partially
resolves with a duplicated phrase at vilnaLine 32, then re-drifts as a
merge through vilnaLine 33-35 before resolving cleanly at vilnaLine 36
(vilnaLine 36's own `en` was already correct and was left unchanged).

`linkedGemaraLineIds` was checked against the real captured Gemara
lines for the whole span and found correct throughout: vilnaLine
19 to `l02`, 20-32 to `l05` (one real line, itself long enough to
span the mishna's daily/Yom Kippur/Festival removal-timing rules that
Rashi's comment tracks across all thirteen print lines), 33-35 to
`l11`. No placement error was found, so per instruction no
`linkedGemaraLineIds` values were changed; only the `en` field was
rewritten for vilnaLine 19 through 35, each now describing its own
raw Hebrew print line rather than a neighbor's.

## Quality audit of 20a-29b (VERSION 15.29), full raw-vs-en re-verification

After the two content-shift corrections above (20b vilnaLine 19-35,
25b vilnaLine 30-35), a full audit was run across all twenty daf from
20a through 29b before resuming forward production at 30a. Two
layers were checked for every daf:

Structural (scripted): raw non-empty Rashi line count against
`rashiTranslations` entry count, `vilnaLine` sequence contiguity,
every `linkedGemaraLineIds` value checked against the real captured
ids for that daf (dangling-link check), no empty `linkedGemaraLineIds`,
and the final truncated entry's boundary-policy compliance (linked to
the daf's own final locally captured line). All twenty daf passed
every structural check with no exceptions.

Content (full manual re-verification, not sampling): every raw Rashi
print line for all twenty daf was read against its own `en` field and
`linkedGemaraLineIds` target, checking for the same one-line-ahead
content-shift pattern found in 20b and 25b. 20a, 21a, 21b, 22a, 22b,
23a, 23b, 24a, 24b, 25a, 26a, 26b, 27a, 27b, 28a, 28b, 29a, and 29b
all passed with no shift found anywhere in any of them. Only the two
already-documented and already-corrected spans (20b vilnaLine 19-35,
25b vilnaLine 30-35) were found across the entire 20a-29b range.

No further corrections were needed. The 20a-29b audit is closed.

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

## Fable process audit findings (VERSION 15.74, read-only, post 44a-46b recovery)

A full read-only process and tooling audit was run after the 44a-46b
recovery (PRs #58-#63). It confirmed the recovery itself but surfaced
the following corpus and process findings, recorded here for the
eventual repair passes. No content was changed by the audit or by the
Phase 1 tooling PR that added this section.

### Corpus findings (new, not previously documented)

1. 41a shifted-English block: around vilnaLine 25-34 the en content
   runs roughly four raw print lines ahead of its Hebrew (en at
   vilnaLine 27 describes raw line 31's "vehe'eshir" comment; en at 28
   describes raw line 32's "ve'achar kach"). Same drift failure mode
   as the documented 12b finding. Needs a bounded remap pass.
2. 42a vilnaLine 52 and 42b vilnaLine 60 still carry literal
   "orphaned Rashi content" placeholder text; the 44a-46b recovery
   scope did not include 41a-43b.
3. 7b, 8a, 8b, 9a, 9b: 117 linkedGemaraLineIds values reference
   Gemara line ids that do not exist in learning_data.js (for
   example yoma-008a-l02). These are captured one-by-one in
   scripts/allowlists/rashi_links_allowlist.json as a ratchet
   baseline; remove entries as they are repaired.
4. 8a and 9a: the enrichment layer carries more rashiTranslations
   entries than raw talmud.dev print lines (41 vs 35, and 22 vs 18).
   The extra phantom entries are silently dropped by
   build_learning_data.py at generation time, which is why
   validate:rashi:yoma never saw them. Captured in the content
   allowlist's count_mismatches section.
5. Undocumented stub blocks: 61a (vilnaLine 46-64, "Rashi commentary
   line N."), and 67b/68a/68b/70a/71b ("Rashi line N: continuation
   of previous comment."), roughly 72 entries total. Same class as
   the 77a-88a filler below but previously unrecorded.
6. 77a-88a filler (about 765 entries) remains the known deferred
   pass already documented above. Together with items 2 and 5 this
   puts the current scaffold total at 839 entries across 31 daf, all
   captured in scripts/allowlists/rashi_content_allowlist.json as a
   ratchet baseline.

### Process findings

- validate:rashi:yoma is structural only; any non-empty en passes.
  This is how the bad 44a-46b batch, the stub blocks, and the
  77a-88a filler all reached main.
- Before the Phase 1 tooling PR, CI ran no Yoma validators at all
  (build, render smoke, and browser smoke only).
- linkedGemaraLineIds was never validated anywhere; app.jsx does not
  currently consume the field, so bogus ids are latent data
  corruption rather than a user-facing break.
- The pre-commit hook is inert unless a clone has run
  git config core.hooksPath githooks. Every working clone must run it.

### Phase 1 tooling added in response (VERSION 15.75)

- scripts/validate_rashi_content.py (npm run validate:rashi:content:yoma):
  fails on placeholder/scaffold patterns, bracketed line stubs,
  "orphaned", known filler strings, em/en dashes, and
  rashiTranslations-vs-raw count mismatches; reports short en fields.
  Pre-existing violations are tolerated via
  scripts/allowlists/rashi_content_allowlist.json (ratchet: never add,
  only remove).
- scripts/validate_rashi_links.py (npm run validate:rashi:links:yoma):
  fails on nonexistent or cross-daf linkedGemaraLineIds; reports
  per-daf empty-link percentages. Pre-existing 7b-9b bogus ids
  tolerated via scripts/allowlists/rashi_links_allowlist.json.
- scripts/check_generated_freshness.py (npm run check:generated:yoma):
  fails if regenerating learning_data.js and coverage.json from the
  enrichment JSON plus literal layer would change the committed bytes;
  always restores the working tree.
- npm run validate:offline:yoma chains all offline gates and now runs
  in CI on every PR and push (deploy-pages.yml).
- githooks/pre-commit now runs the three new guards whenever Yoma
  module data is staged.

### Status

47a reconstruction is paused until this Phase 1 tooling is merged and
green. Content repairs for items 1-5 above are separate, individually
scoped passes and were intentionally NOT made in the tooling PR.

### Repair record: 7b-9b bogus linkedGemaraLineIds fixed (VERSION 15.76)

Corpus finding 3 above is resolved. All 117 bogus ids on 7b, 8a, 8b,
9a, and 9b were repaired in a bounded mechanical pass. Diagnosis: the
enrichment had linked every Rashi line at vilna line V to a Gemara id
lV, assuming an id exists for every vilna line, but the real id space
is sparse (ids exist only where Gemara segments start; each id's
number equals its segment's starting vilna line, verified against
learning_data.js). Every bogus target had delta zero to its own
entry's vilnaLine, so each was remapped to the real id of the Gemara
segment containing that vilna line (the nearest preceding real id),
preserving the original placement intent. Spot checks against raw
Rashi Hebrew and Gemara text confirmed correct anchoring (for example
7b vilnaLine 5, a comment on R. Yehuda's forehead-plate position, now
anchors to l04, R. Yehuda's own statement). Only linkedGemaraLineIds
values changed; no en, he, or Gemara-learning fields were touched.
scripts/allowlists/rashi_links_allowlist.json is now empty and must
stay empty for new work. Findings 1, 2, 4, and 5 above (41a shift,
42a/42b leftovers, 8a/9a phantom entry counts, 61a/67b-71b stubs)
remain open, and 47a remains paused pending those decisions.

### Phase 2/3 tooling added (VERSION 15.77)

Tooling-only pass, no content changes. Added on top of the Phase 1 gates:

- scripts/check_rashi_pr_scope.py (npm run check:rashi-pr-scope:yoma):
  content PRs may change only rashiTranslations en/linkedGemaraLineIds,
  only allowed files, never workflows; allowlists are remove-only.
  Runs in CI on pull requests and in the pre-commit hook.
- scripts/validate_rashi_repetition.py (npm run validate:rashi:dupes:yoma):
  fails on new within-daf exact-duplicate or skeleton-template repetition;
  the documented bracket-heavy 41b/42b skeletons are baselined in
  scripts/allowlists/rashi_repetition_baseline.json (ratchet). Wired into
  validate:offline:yoma and CI.
- scripts/audit_rashi_semantic.py (npm run audit:rashi:semantic:yoma):
  advisory ranked report of likely shifted-English blocks via Hebrew
  citation anchors. It independently re-flags the confirmed 41a shift
  (Leviticus citation at vilnaLine 27 surfacing in the en of vilnaLine 24)
  and surfaces a new lead at 42a vilnaLine 50 (Numbers citation surfacing
  at vilnaLine 46, offset -4), consistent with the 41a-43b batch being
  suspect. Report-only; never blocks CI.
- scripts/make_rashi_work_packet.py (npm run rashi:packet:yoma -- <daf>):
  deterministic per-daf work packet (raw Hebrew, legal Gemara ids from the
  generated id space, current state, validator baselines, rules, post-edit
  commands) for bounded worker-model passes.
- docs/rashi-workflow.md documents the guarded operating model: Fable
  builds guardrails and handles semantic escalation; small models may work
  only inside the gates, may not override failures, and may not add
  allowlist entries; no content PR merges unless all offline gates pass.

### Repair record: 42a/42b leftover placeholder lines fixed (VERSION 15.78)

Corpus finding 2 from the Fable audit is resolved. 42a vilnaLine 52 and
42b vilnaLine 60 each carried literal "End of orphaned Rashi content"
placeholder text. Both raw lines are single truncated Hebrew words that
begin a comment continuing onto the next daf, the same pattern as the
documented 10a vilnaLine 35 and 11a vilnaLine 43 cases: 42a line 52 is
"lemishmeret" (Numbers 19:9), whose comment body is 42b's first raw
Rashi line (the ashes require safekeeping until the sprinkling water is
prepared); 42b line 60 is "deapik", whose comment body is 43a's first
raw Rashi line (one who brought out a donkey along with the heifer).
Both en fields now state the cross-daf continuation with the actual
content. linkedGemaraLineIds were left unchanged (both already valid
local anchors consistent with each daf's closing block). The two
corresponding content allowlist entries were removed after the
validator reported them stale (ratchet 839 to 837). Remaining open:
41a shifted block, 8a/9a phantom entry counts, 61a/67b-71b stubs,
77a-88a filler. 47a remains paused.

### Automation hardening pass (VERSION 15.79)

Tooling only, no content changes. Added: rashi:preflight:yoma (single
preflight command with hard environment/daf checks and per-daf state),
rashi:verify:yoma (single post-edit verification with fast/full modes,
allowlist-delta hard fail, scoped advisory semantic output),
rashi:prompt:yoma (deterministic worker prompt generator per task type),
and an allowlist growth lockout in the PR scope gate that now applies to
ALL PRs including tooling PRs, with RASHI_ALLOWLIST_RESTRUCTURE=1 as the
only authorized escape hatch. docs/rashi-workflow.md documents the
standard automation loop and the recommended GitHub branch protection
settings (manual admin configuration; not changeable from repo code).
Open content defects are unchanged: 41a shifted block (plus the 42a
vilnaLine 50 semantic lead), 8a/9a phantom entry counts, 61a/67b-71b
stubs, 77a-88a filler. 47a remains paused.

### Project-wide worker pipeline added (VERSION 15.80)

Tooling only, no content changes. scripts/worker_task_types.json (nine
task types with scope contracts, models, pause flags) and
scripts/worker_pipeline.py (manifest/preflight/packet/prompt/verify/
scope/ci-check) generalize the Rashi loop to all bounded work. CI now
additionally requires a per-PR .worker-manifest.json for any PR that
changes module content, and a docs-tooling manifest for any PR that
touches workflow files. Rashi task types delegate to the existing Rashi
tooling; no gate was weakened. Dry runs executed for 61a (rashi-repair,
Haiku-safe), 41a (rashi-repair manifest, Fable-only per matrix), 77a-77b
(placeholder-backfill), and this PR itself (docs-tooling). The readiness
matrix in docs/worker-pipeline.md records recommended model, batch size,
and Haiku-readiness for every remaining work category. Open content
defects unchanged; 47a remains paused.

### Worker pipeline hardening (VERSION 15.81, process note)

Tooling only. The worker pipeline gained: a strict gemara-learning JSON
field gate with pointer-level errors and Fable-issued authorization
flags; a manifest-aware hand-off in the Rashi scope gate (defers field
rules to the stricter worker gate only when a fresh gemara-learning
manifest is in the PR; both gates run in CI); placeholder-backfill
maxBatch 2 plus per-daf allowlist completion summaries with a hard fail
on growth; literal-layer coverage delta reporting and generated-vs-
source consistency rules; a generated-refresh sources-unchanged rule;
an audit-only task type limited to docs/reports/* and backlog notes; a
machine-readable worker:report template; and a REVIEW GATE notice for
fableReviewRequired task types. No gate weakened; no content changed;
all documented content defects and 47a/nekudot remain untouched.

### Schema-wide pipeline coverage (VERSION 15.82, process note)

Tooling only. All 85 schema-controlled learning JSON paths are now
classified (scripts/worker_schema_scope.json) and mechanically owned:
the worker scope gate became a generic jsonScope engine with exact
JSON-pointer errors, seven enrichment task types were added, and
worker:schema-matrix fails any drift between inventory and registry.
A 15-case negative-test battery and 12 task-type dry runs all pass.
One schema-drift observation recorded: argumentFlow sourceRefs entries
are strings on some daf and objects on others; normalization deferred
to a future structural-repair pass. No content changed; all documented
defects and 47a/nekudot remain untouched.

### Documentation standardization (VERSION 15.83, process note)

Documentation only. The pipeline is now a documented MySugya standard:
docs/worker-pipeline-sop.md (canonical SOP, model roles, operator
quickstart, consistency policies), docs/yoma-pilot-lessons.md (case
study of the original failures and what each gate catches),
docs/new-tractate-onboarding.md (safety checklist required before any
new module's content work), and two machine-generated references
regenerated by npm run worker:docs: docs/reports/task-type-reference.md
(all 17 task types) and docs/reports/schema-coverage-matrix.md (all 85
classified schema paths). CLAUDE.md points to the SOP. Outdated
statements in docs/worker-pipeline.md (nine task types; gemara-learning
gate pending) were corrected. No content changed; all documented
defects and 47a/nekudot remain untouched.

### Repair record: 61a stub lines 46-64 fixed (VERSION 15.84, first worker-pipeline pass)

The 19 documented "Rashi commentary line N." stubs on 61a (vilnaLine
46-64) were replaced with genuine translations of their own raw Hebrew
(the "one chatat" comment conclusion, the Rabbi Yaakov log-of-metzora
distinction block, and the truncated "asham" cross-daf continuation
onto 61b). Only rashiTranslations en changed; linkedGemaraLineIds were
left in this daf's uniform existing state (empty; the daf-wide link
completion is separate documented work). The 19 content allowlist
entries were removed after the validator reported them stale (ratchet
837 to 818).

ESCALATED NEW FINDING (report only, not fixed in this pass): 61a
vilnaLines 1-45, which the audit had counted as genuine because they
carry specific-looking text, are fabricated. Sampled entries (40-45)
contain inspirational filler about Torah study replacing the Temple
service, unrelated to their raw Hebrew (line 40's Hebrew concerns
interrupted blood applications). 61a therefore needs a full
reconstruction pass for lines 1-45 in its own scoped authorization,
and the same look-alike fabrication pattern should be assumed possible
on the other stub-block daf (67b/68a/68b/70a/71b) until checked.

### Look-alike audit: 61a fabrication confirmed; 67b/68a/68b/70a/71b are SHIFTED, not stub-missing (VERSION 15.84 main, read-only audit)

Read-only Fable audit of all six daf named in the PR #73 escalation;
full report with per-line evidence and anchor offsets in
docs/reports/rashi-lookalike-shift-audit.md. Findings:

- 61a lines 1-45 confirmed fabricated across the whole block (a
  continuous essay about the daf's theme, unrelated to the Hebrew line
  by line; the Hebrew's Shevuot 7b and 13b citations appear nowhere in
  the English). Needs full reconstruction, Fable/Sonnet.
- 67b, 68a, 68b, 70a, 71b are NOT fabricated. Each carries a genuine,
  complete translation of the daf's entire Rashi, compressed into too
  few lines: alignment drifts ahead by up to +13/+13/+11/+9/+17 lines
  respectively, the translation ends early, and the tail was padded
  with the allowlisted stub_continuation stubs. The stub lines' Hebrew
  content is already translated earlier in each daf.
- Consequence: stub-only repair (the 61a playbook) is FORBIDDEN on
  these five daf. It would create paraphrased duplicates, leave the
  middle of each daf misaligned, and drain allowlist entries while
  making the daf worse. They need a full-daf realignment pass instead
  (Fable/Sonnet, Fable review).
- The debt-list phrase "61a/67b-71b stubs" is therefore misleading:
  on five of the six daf the stubs are a symptom, not the defect.
- The advisory semantic audit scored these daf 0 to 3 with zero shift
  candidates; four concrete detector gaps (colon-less citation regex,
  tractate names outside parentheses, 4-line window, no drift
  aggregate) are documented in the report with a proposed fix,
  preflight block, packet warning, and a rashi-realignment task type.

No content changed; no repair started; 41a, 47a, 77a-88a, and nekudot
untouched.

### Drift detection and realignment workflow (VERSION 15.85, tooling only)

Tooling/process only; no content changed. Implements the guardrails
proposed by the VERSION 15.84 look-alike audit
(docs/reports/rashi-lookalike-shift-audit.md):

- audit_rashi_semantic.py rebuilt: colon-tolerant amud citations,
  tractate names adjacent to daf citations, gematria daf-number anchors,
  split-citation tolerance, search window 25, and a per-daf drift
  profile (--profile; npm run audit:rashi:drift:yoma) classifying
  SHIFTED / FABRICATION-SUSPECT / ALIGNED / INSUFFICIENT-ANCHORS.
- rashi_preflight now FAILS line-level tasks (repair, links) on a daf
  whose profile is SHIFTED or FABRICATION-SUSPECT, naming the required
  remedy. Override is Fable-only: manifest authorizeDriftOverride plus
  FABLE_DRIFT_OVERRIDE=1; neither alone unblocks (proven by dry runs).
- The Rashi work packet embeds each daf's drift profile with an explicit
  STOP warning when not haiku-safe.
- New task type rashi-realignment (fable, Fable review, maxBatch 1) for
  shifted-compressed daf; worker:verify hard-fails a realignment PR
  whose post-edit profile is still not aligned.
- Task assignments recorded: 61a lines 1-45 -> rashi-reconstruction
  (Fable/Sonnet); 67b/68a/68b/70a/71b -> rashi-realignment
  (Fable/Sonnet); stub-only repair FORBIDDEN on those five daf
  (mechanically enforced); 47a+ reconstruction remains paused; nekudot
  remains paused.
- Tests: npm run test:drift:yoma (43 checks; wired into npm test):
  synthetic classifier fixtures, block/override semantics, and
  self-retiring live assertions for the documented daf.

ESCALATED TRIAGE BACKLOG (report only, from the first corpus-wide drift
scan): beyond the six audited daf, the profile flags 30 more daf that
need Fable triage before any Haiku line-level work (the preflight block
covers them automatically). SHIFTED: 5a, 5b, 6a, 7a, 41a (41a already
documented). FABRICATION-SUSPECT (anchors repeatedly absent from the
English; spot checks found 61a-style essay filler on 61b, 50a, 52b and
untranslated bracket placeholders on 73a): 18a-adjacent false positives
were eliminated, remaining flags are 41b, 47b, 48a, 50a, 50b, 51a, 51b,
52a, 52b, 53a, 53b, 57b, 58b, 59a, 60a, 60b, 61b, 66b, 72b, 73a, 73b,
74a, 75a, 76b, 9b. FABRICATION-SUSPECT means "needs Fable review", not
"proven fabricated": partial-coverage translations of long Hebrew lines
can also trip it (9b looks like that case). The 77a-88a filler daf are
already fully allowlisted, so their misses are excluded by design.

### Repair record: 61a lines 1-45 reconstructed (VERSION 15.86, rashi-reconstruction pass)

The fabricated block on 61a (vilnaLine 1-45, essay-style filler about
Yom Kippur services unrelated to the printed Rashi) was reconstructed
line by line from the raw Hebrew in assets/talmuddev/61a.json under the
rashi-reconstruction task type (Fable, manifest-scoped, Fable
self-review). Lines 46-64 (repaired in the VERSION 15.84 pass) were
byte-verified unchanged. linkedGemaraLineIds were populated for lines
1-45 following the corpus convention (one Gemara id per line,
continuation lines repeat the id), with every lemma verified against
the actual 61a Gemara segments: l01a (incense), l01b (Ulla / "he put
the goat's blood first"), l07 (first braita: innermost sanctum /
Sanctuary / altar), l10 ("they were all equated"), l13 (Rabbi Shimon),
l19 (second braita: "when he has finished atoning"), l22 ("from here
they said"), l34 ("one sin offering I told you").

Post-edit drift profile: ALIGNED, 6 anchors found, 0 missing, all
offsets zero (the Shevuot 7b and 13b citations now resolve on their
exact lines). The self-retiring 61a live assertion in
test_drift_profile.py now skips, as designed. 61a is no longer in the
fabrication-suspect set; it leaves the triage backlog above.

### Repair record: 67b realigned (VERSION 15.87, first rashi-realignment pass)

The SHIFTED/compressed daf 67b was realigned line by line under the
rashi-realignment task type (Fable, manifest-scoped, maxBatch 1, Fable
self-review). The old entries 1-58 held genuine content-paraphrase that
drifted progressively (offset 0 at the top, -2 by line 22, -12..-15 in
the tail); entries 59-69 were allowlisted stubs. Every entry's en now
translates its own raw Hebrew vilna line, reusing the existing faithful
phrasing where it matched; the previously stub-covered tail (he 59-69,
the corrupted-girsa discussion, the dissection braita, and the
gezeirah shavah) is translated from its own Hebrew, so no duplicate
paraphrase remains from the compressed run. linkedGemaraLineIds were
populated for all 69 lines with lemmas verified against the actual 67b
Gemara segments (l01, l02, l05, l08, l10, l12, l16, l17, l20, l26,
l28, l31, l37, l41, l42; Mishnah commentary he 35-57 links to l31/l37
whose vilna ranges hold the Mishnah text; he 69 uses the final-id
boundary policy).

The 11 stub_continuation allowlist entries for 67b (lines 59-69) were
reported stale by validate_rashi_content after the edit and removed
(ratchet direction: allowlist shrinks by 11).

Post-edit drift profile: ALIGNED, 11 anchors found, 0 missing, all
offsets zero (Lev. 16 L1, Gen. 6 L18, 1 Sam. 30 L22, Gen. 47 L23,
Lev. 16 L42, Pesachim 65b + Sotah 15a L61, Sotah 14b L63, Lev. 1 L67,
Lev. 4 L68). The self-retiring 67b live assertion in
test_drift_profile.py now skips. 67b leaves the shifted set; 68a, 68b,
70a, 71b, and 41a remain queued for their own realignment passes.

### Repair record: 68a realigned (VERSION 15.89, second rashi-realignment pass, Sonnet worker)

The SHIFTED/compressed daf 68a was realigned line by line under the
rashi-realignment task type (worker model: sonnet per the VERSION
15.88 role correction; Fable review required). The old 49 entries held
genuine content-paraphrase that progressively compressed 62 raw Rashi
lines into 49 English entries (offset 0 near the top, building to
-9/-10/-13 by the tail); entries 50-62 were allowlisted stubs. Every
entry's en now translates its own raw Hebrew vilna line, reusing the
existing faithful phrasing split at the correct line boundaries; the
old compressed English already fully covered the content that would
land on raw lines 48-62 (entries 36-49), so the previously stubbed
tail required redistribution only, no invented translation.

linkedGemaraLineIds were populated for all 62 lines with lemmas
verified against the full (untruncated) text of all 10 Gemara segments
(l01, l03, l07, l10, l12, l16, l17, l23, l25, l31); the chatat-chatat
excursus (he 31-47) has no separate Gemara id between l17 and l23, so
it continues on l17 per the boundary policy.

The 13 stub_continuation allowlist entries for 68a (lines 50-62) were
reported stale by validate_rashi_content after the edit and removed
(ratchet direction: allowlist shrinks by 13).

Post-edit drift profile: ALIGNED, 5 anchors found, 0 missing, all
offsets zero (Zevachim 39a + Menachot 27a L34/L35, Numbers 19 L55).
The self-retiring 68a live assertion in test_drift_profile.py now
skips. 68a leaves the shifted set; 68b, 70a, 71b, and 41a remain
queued for their own realignment passes.

### Repair record: 68b realigned (VERSION 15.90, third rashi-realignment pass, Sonnet worker)

The SHIFTED daf 68b was realigned line by line under the
rashi-realignment task type (worker model: sonnet; Fable review
required). The he field was already correctly aligned to its own raw
Hebrew vilna line for all 60 lines; only en had drifted (offsets 0 at
the top, -3 by line 31, -5 by line 37, -11 by line 56), and entries
52-60 were allowlisted stubs. Every entry's en was retranslated from
its own raw Hebrew line, so no old compressed phrasing needed
redistribution; the previously stubbed tail (he 52-60, the
eight-blessing enumeration and closing fragment) is translated fresh
from its own Hebrew, with no duplicate paraphrase.

linkedGemaraLineIds were populated for all 60 lines. The worker's
initial pass linked positionally (Rashi line N to the segment at
vilna N); Fable review found that wrong for he 18-59 and relinked
semantically, with each comment tied to the segment whose text it
explains: he 18-28 (amru lo, dirkaot relay men) to l13b, the
end-of-perek Mishnah segment the packet id table had omitted; he
29-32 (Beit Chadudo, holchin mil) to l15 (R' Yehuda's sign); he 33-34
(naaseit mitzvato) to l21; he 35 (hadran) to l23, the actual hadran
id; he 36-41 (ba likrot, bigdei butz, itztalit) to l24; he 42-52
(chazan/rosh ha-knesset, ach be-asor, chumash ha-pekudim, korei al
peh) to l25; he 53-58 (the eight blessings) to l29; he 59 to l29 plus
l38/l39 (its Gemara lemmas nitnu lehanot and sheina hu de-la); he 60
(ve-seifa) to l42. A daf-citation split across two raw Hebrew lines
(he 37 "(דף" / he 38 "ה:)") was resolved by keeping the "(daf 5b)"
citation together on line 37's English, matching the parenthetical's
Hebrew opening. Known tooling gap for a future docs-tooling pass:
make_rashi_work_packet.py omitted l13b from the legal id table
(its kind is "mishna", not "gemara"), which forced the worker's
positional fallback for the ch. 6 tail.

The 9 stub_continuation allowlist entries for 68b (lines 52-60) were
reported stale by validate_rashi_content after the edit and removed
(ratchet direction: allowlist shrinks by 9).

Post-edit drift profile: ALIGNED, 3 anchors found, 0 missing, all
offsets zero (Yoma 66b L31, Megillah 5b L37, Psalms 50/Tehillim L56).
The self-retiring 68b live assertion in test_drift_profile.py now
skips. 68b leaves the shifted set; 70a, 71b, and 41a remain queued for
their own realignment passes.

### Tooling record: packet generator now emits Mishnah segments and the semantic linking contract (VERSION 15.91, docs-tooling, Fable)

Root cause fixed. make_rashi_work_packet.py's legal id table was built
from a regex that required kind "gemara", so any kind "mishna" segment
was silently dropped, and each segment's Hebrew was truncated to its
first 60 characters. On 68b this omitted yoma-068b-l13b (the
end-of-perek Mishnah); with no legal anchor for the ch. 6 tail
commentary and only text openings to match against, the PR #80 worker
fell back to positional linking (Rashi line N to the segment at vilna
N) and Fable review had to correct 50 of 60 links. The same read-only
audit shows the next queued realignment daf carry the same exposure:
70a's table would have dropped yoma-070a-l27 [mishna] (1 of 23
segments) and 71b's would have dropped yoma-071b-l11 [mishna] (1 of
15); both tables are now complete, in source order, with suffixed
pairs (l41a/l41b, l53a/l53b) preserved and current links resolving.

The fix, tooling and docs only (no learning JSON or generated data
content changed):

- local_segments_for() collects every kind-bearing segment, gemara AND
  mishna, in source order, deduplicated, with kind, vilna_line, and
  FULL untruncated Hebrew text. Ids come only from the generated data;
  sparse and suffixed ids pass through verbatim and nothing is
  renumbered or manufactured.
- Packet rules now state the semantic contract: linkedGemaraLineIds
  are semantic text anchors matched by dibbur hamatchil, quoted
  phrase, subject, or discussion against the full segment text; never
  assigned by vilna line number or positional offset; multi-segment
  links are legal when a comment genuinely spans segments; boundary
  policy covers only commentary continuing the final segment's own
  discussion; an unidentifiable target is an escalation, never a
  guess. rashi_prompt.py and the worker_pipeline.py prompt carry the
  same language, and all four Rashi task types gained the escalation
  trigger in the registry (worker docs regenerated).
- Regression tests (scripts/test_rashi_packet.py, wired into npm test
  as test:packet:yoma): l13b present with kind mishna in source order;
  the 19 pre-fix 68b Gemara ids all retained; sparse gaps and suffixed
  siblings preserved; full text beyond the old 60-char cut; packet-side
  referential completeness across every daf; anti-positional language
  asserted in the packet, the per-daf prompt, and the pipeline prompt.

New deferred debt discovered by the completeness test (self-retiring
KNOWN_PHANTOM_LINKS entries in test_rashi_packet.py): on 43a (rashi
vilna 1-3), 43b (1), and 44b (1-4), early helper entries link to a
plain lNN id (yoma-043a-l01, yoma-043b-l01, yoma-044b-l01) that exists
only as an argumentFlow step id; the real first segments are the
suffix-split l01a/l01b. validate_rashi_links accepts these because its
legal-id regex also matches argumentFlow ids. A future scoped links
pass should relink those eight entries to l01a/l01b semantically and
drain the test's debt list; the validator regex tightening should ride
the same pass so the gate and the packet table agree.

### Repair record: 70a realigned (VERSION 15.92, fourth rashi-realignment pass, Sonnet worker)

The SHIFTED daf 70a was realigned line by line under the
rashi-realignment task type (worker model: sonnet; Fable review
required). All 55 raw Rashi lines already had current entries (no
missing lines), but en had drifted (offset 0 near the top, -2 by line
16, -7 by line 28), and entries 53-55 were allowlisted stubs. Every
entry's en was retranslated directly from its own raw Hebrew vilna
line, reusing the existing translation's genuine phrasing where it
mapped to the correct line and redistributing it there; the previously
stubbed tail (he 53-55, the concluding verse-based proof for the
mussaf-goat sequencing) is translated fresh from its own Hebrew, with
no duplicate paraphrase.

linkedGemaraLineIds were populated for all 55 lines, verified against
the full (untruncated) text of all 23 local segments in this daf's id
table (l01, l02, l03, l07, l10, l15, l16, l22, l24, l26, l27 [mishna],
l28, l31, l32, l34, l36, l37, l39, l41a, l41b, l43, l44, l46) using the
packet fix from the tooling PR that preceded this pass (l27's Mishnah
kind is present and correctly ordered). Representative mappings: he
1-2 (two short dibburim on the same print line) to [l01, l02]; he 9
("ketikonah") to l16 despite the seven-line gap, because "כתיקנה" only
occurs in l16's text and boundary/positional proximity is not a
legitimate substitute for a textual match; he 10-19 (the hiddur-mitzvah
excursus, Exodus 15 citation) to l22, the segment whose "to show its
appearance to the many" phrase the excursus explains; he 26 (Mishnah
"seven lambs") to l28, since "שִׁבְעַת כְּבָשִׂים" lives in l28's text,
not in l27 (the Mishnah segment itself, which covers the vestment-
changing sequence and has no Rashi comment linking to it on this daf);
he 31-34 (Rabbi Eliezer's bull-timing question) to l41a rather than
the topically-adjacent l37/l39 Akiva dispute, because l41a's own text
("וְתוּ: פַּר הָעוֹלָה לְרַבִּי אֱלִיעֶזֶר דְּשַׁיְּירֵיהּ") is what he
31 quotes almost verbatim; he 43 (the Akiva textual-variant point
about "יצא ועשה") to l28, where that Mishnah phrase actually appears,
rather than to l46 where the surrounding discussion continues; he
44-54 (the closing mussaf-sequencing block, closing with the "besides
the sin-offering of atonement" verse-proof) to l46, the final segment
whose own content this entire block explains start to finish. Several
print lines carry two dibburim spanning adjacent segments and were
linked to both (he 1, 3, 5, 10, 20, 23, 26, 30, 31, 37, 40, 41), per
the multi-segment-link rule; no line was linked to the final id as an
unrelated-content boundary fallback, since he 55's truncated
continuation ("ואחר") is itself still explaining l46's content, cut
off by the amud boundary.

The 3 stub_continuation allowlist entries for 70a (lines 53-55) were
reported stale by validate_rashi_content after the edit and removed
(ratchet direction: allowlist shrinks by 3).

Post-edit drift profile: ALIGNED, 2 anchors found, 0 missing, all
offsets zero (Exodus 15 at L16, Numbers 29 at L28). 70a leaves the
shifted set; 71b and 41a remain queued for their own realignment
passes.

### Repair record: 71b realigned (VERSION 15.94, fifth rashi-realignment pass, Sonnet worker, conditional review)

The SHIFTED daf 71b was realigned line by line under the
rashi-realignment task type (worker model: sonnet; conditional review
policy from PR #83, no routine Fable review). All 61 raw Rashi lines
had current entries, but en had drifted (offsets -1/-1/0/-1 near the
top from four citation anchors, -14 at line 49), and entries 45-61 (17
lines, the bulk of the daf's shesh/bad and me'il/choshen strand-count
sugya) were allowlisted stubs. Every entry's en was retranslated
directly from its own raw Hebrew vilna line; the previously stubbed
tail is translated fresh, with no duplicate paraphrase.

linkedGemaraLineIds were populated for all 61 lines against the full
untruncated text of all 15 local segments (l01, l02, l06, l11 [mishna],
l16, l19, l26, l31, l33, l41, l46, l51, l53a, l53b, l56). l02 and l46
carry no Rashi comment on this daf and are legitimately unused (not
every segment requires a link). Representative mappings: he 1's first
dibbur ("me-re'ach mayim") links to l01, the verse fragment it quotes,
while its second dibbur ("le-sof ato Shemaya ve-Avtalyon") links to
l06, which the Gittin/Bava Metzia/Vayikra excursus (he 3-9) continues
to explain; he 44's "ben nechar" links to l33 rather than the
topically-adjacent l31, because l33 is where the Ezekiel citation
"ben nechar erel lev" actually appears; he 50-53's "mah lehalan
esrim ve-arba'ah" links to l41 (which states 24), not the numerically
similar but textually distinct l46 (which states 28); he 61's
truncated "kalil" links to l56, the final local segment, because it is
the literal next word of the same Exodus 28:31 verse ("ve-asita et
me'il ha-ephod") that l56 quotes, cut off by the amud boundary, not an
unrelated-content fallback. 7 print lines carry two dibburim spanning
adjacent segments and are linked to both (he 1, 10, 33, 42, 44, 50,
54, 56).

The 17 stub_continuation allowlist entries for 71b (lines 45-61) were
reported stale by validate_rashi_content after the edit and removed
(ratchet direction: allowlist shrinks by 17).

Post-edit drift profile: ALIGNED, 6 anchors found, 0 missing, all
offsets zero (Gittin 57b L4, Bava Metzia 58b L6, Vayikra 25 L7,
Zevachim 15b L49). Corpus-wide semantic audit: 0 shift candidates.
Fresh Sonnet self-review recorded in .worker-self-review.json;
worker:review reported AUTO-MERGE-ELIGIBLE with no escalation. 71b
leaves the shifted set; 41a remains queued for its own realignment
pass.

### Repair record: 41a realigned (VERSION 15.95, sixth rashi-realignment pass, Sonnet worker, conditional review)

The SHIFTED daf 41a was realigned line by line under the
rashi-realignment task type (worker model: sonnet; conditional review
policy, no routine Fable review). Unlike 68a/68b/70a/71b, 41a had no
allowlisted stubs; all 56 lines already carried genuine content in a
nonstandard "Rashi: opens/continues - [bracketed paraphrase]" style,
overwhelmingly compressed onto a single segment id: lines 33-56 (24 of
56 lines) all pointed at yoma-041a-l33 regardless of their own content.
Two Gemara-tractate daf-number citations (Sanhedrin 86a at line 2,
Shevuot 7a at line 28) were present in Hebrew but never rendered in the
old English, which is why the audit tool reported them as missing
anchors going in.

Every entry's en was retranslated directly from its own raw Hebrew
vilna line, replacing the bracket-paraphrase style with direct
translation and including both previously-dropped citations.
linkedGemaraLineIds were populated for all 56 lines against the full
text of all 15 local segments (l01, l04, l06, l08, l10, l12, l13, l15,
l21, l22, l25, l26, l28, l31, l33); l08, l10, l12, l15, l21 carry no
Rashi comment on this daf and are legitimately unused. Representative
mappings: he 9's "ve-lakcha ve-asa" links to l06, the verse it quotes,
after he 3-8 finish explaining l04's own rule; he 15-21's extended
"veha hacha" gloss links to l13, the exact phrase being unpacked, using
l10's kal vachomer only as background (not a separate link); he 33-43
(the case's practical unwinding: rich-person's offering, adding
chatat-money) links first to l22 (the case setup) then l25 (the
top-up rule) at the genuine content transition in he 35, which carries
no printed colon but is a defensible content-based split (verified
against both segments' subject matter); he 46-53 (Rav Sheshet's
challenge and Rava's/Rav Chisda's "kevar amar" resolution) links
through l26, l28, l31 as each is quoted or answered in turn; he 54-56
(Rabbi Chagga's alternative resolution, then the amud-boundary
truncation) links to l33, the segment introducing that citation,
including the final truncated word "mai" (he 56) which is confirmed as
the direct continuation of l33's own sentence (ending mid-clause with
a comma), not an unrelated fallback. 8 print lines carry two dibburim
spanning adjacent segments and are linked to both (he 9, 15, 22, 35,
44, 46, 48, 54).

No allowlist entries existed for 41a before or after this pass; no
allowlist file changed.

Post-edit drift profile: ALIGNED, 4 anchors found, 0 missing, all
offsets zero (Sanhedrin 86a L2, Vayikra 5 L27, Shevuot 7a L28).
Corpus-wide semantic audit: 0 shift candidates. Fresh Sonnet
self-review recorded in .worker-self-review.json; worker:review
reported AUTO-MERGE-ELIGIBLE with no escalation. 41a leaves the
shifted set. The autopilot queue (71b, 41a) is now drained.

### Repair record: 8a structurally repaired (VERSION 15.98, first rashi-structural-repair pass, Fable worker)

The baselined 8a entry-count mismatch (41 rashiTranslations vs 35 raw
print lines) is repaired. Root mechanism, established from the
authoritative talmuddev source before editing: the original enrichment
generated entries on the GEMARA line axis (8a's Gemara segments run to
vilna 41, ending in the catchword shezeh at l41) instead of the RASHI
print-line axis (35 raw lines, ending in the same catchword at raw
35). Entries 36-41 were phantoms keyed to Gemara lines 36-41 whose
actual Rashi lives partly on 8a raw 30-35 and partly on 8b's column
(8b raw 1-4, already covered by 8b's own complete 50/50 entries;
boundary ownership verified against 7b, 8a, and 8b before editing,
and 7b/8b were not touched).

The repair rebuilt rashiTranslations on the raw axis: 35 entries,
vilnaLine 1..35, each en translating its own raw print line (reusing
the genuine content of the old comment-paraphrases where it matched),
and linkedGemaraLineIds assigned semantically against the full text of
all 16 local segments: raw 1-2a (echad zeh, shlishi u-shevi'i, kohen
ha-soref dibburim) to l14, the baraita quoting them; raw 2b-9a (the
dechuya/hetter explanations) to l21; raw 9b-10a (hazaah kelal lama li)
to l23; raw 10b-19 (tevila bizmanah mitzvah both sides, Bamidbar 19
derivation, Kiddushin 62a citation) to l26; raw 20-25 (lo yirchatz,
tevila shel mitzvah, korech alav gemi) to l28, the baraita quoting all
three; raw 26-29 (vekayma lan, Shabbat 120b) to l32; raw 30-34 (lo
makshinan) to l35; raw 35 (the shezeh catchword) to l41, the segment
consisting of that word. The 8 unused ids are legitimate: l01-l11 (the
tzitz sugya, Rashi on 7b's column) and l36-l39 (the R. Chanina
resolution, Rashi on 8b's column). Multi-id lines: 2, 9, 10, each at a
printed dibbur-boundary colon.

The 8a count_mismatches baseline entry was removed only after the
content gate passed green without it (the tolerance NOTE no longer
fires); no allowlist entries were added anywhere.

Post-repair profile: ALIGNED, 4 anchors found, 0 missing, all offsets
zero (previously 2 found at -1 with 2 missing). Corpus semantic audit:
0 shift candidates. 9a remains the last count-mismatch baseline.

### Repair record: 9a structurally repaired (VERSION 15.100, second rashi-structural-repair pass, Fable worker)

The baselined 9a entry-count mismatch (22 rashiTranslations vs 18 raw
print lines) is repaired; the mechanism is the same Gemara-axis
generation established for 8a (9a's Gemara segments run to vilna 22,
ending in the catchword sheshahu at l22; the Rashi column has 18 print
lines ending in the same catchword), verified independently from the
9a sources rather than copied from the 8a solution. Entries 19-22 were
phantoms narrating the Temple-years and Shiloh aggada (l08, l13, l17),
segments on which 9a's Rashi column carries no comments at all; the
boundary against 8b and 9b was checked (both counts already at parity,
neither touched).

rashiTranslations rebuilt on the raw axis: 18 entries, vilnaLine
1..18, each en translating its own raw print line, links assigned
semantically against the full text of all 7 local segments: raw 1-2a
(lefi sheshalach, Sotah 48a) to l01; raw 2b-11a (hamotzi mechavero,
nafreshu venasku) to l02, the segment quoting both dibburim; raw
11b-17 (chovtin otan, lo atrechunhu, pursei) to l05, which quotes all
three; raw 18 (the sheshahu catchword) to l22, the segment consisting
of that word. Multi-id lines: 2 and 11, each at a printed
dibbur-boundary colon. The unused ids (l08, l13, l17) are legitimate.

The 9a count_mismatches baseline entry was removed only after the
content gate passed green without it; the count_mismatches section is
now EMPTY, and no allowlist entries were added anywhere.

Post-repair profile: INSUFFICIENT-ANCHORS (haiku-safe), the single
Sotah 48a anchor found at offset 0 (previously missing entirely).
Corpus semantic audit: 0 shift candidates. With 8a (VERSION 15.98/99)
and 9a both repaired, the structural count-mismatch backlog is
drained.

### Repair record: 42a vilnaLine 25-52 relinked and rewritten (VERSION 15.101, rashi-realignment, Sonnet worker)

The 42a vilnaLine 50 lead documented above (VERSION 15.79) turned out
not to be an isolated placement issue once checked against current
main and the raw Hebrew: the actual defect was a genuine multi-line
block spanning vilnaLine 25-52 (28 of 52 entries). Lines 1-24 were
reread and confirmed already correct (untouched).

Two compounding problems, found by direct Hebrew-to-English and
Hebrew-to-segment comparison rather than the anchor-based drift tool
(which only found 5 sparse anchors and reported ALIGNED, too sparse to
trigger its threshold): (1) linkedGemaraLineIds for 25-31 all pointed
to l25 and for 32-52 all pointed to l32, a positional lazy fallback
rather than semantic matching; (2) the English for lines 39-52 had
drifted two raw lines ahead of its own vilnaLine (en39 was translating
raw41's content, and so on down the block), which used up all the real
untranslated content by en48 and left vl49-51 as generic
non-translating filler ("[End of the detailed discussion...]", etc.)
duplicating what vl52 already said correctly.

Rebuilt each of lines 25-52 to translate its own numbered raw print
line and relinked by direct phrase matching against the local segment
table: 25-28 to l19 (continuing the Aharon/chukah Leviticus 16 verse
citation already open at vilnaLine 19-24); 29-34 to l21 (continuing
Rashi's own gloss on "shechitah lav avodah hi... shani parah dekidshei
bedek habayit"); 35 dual-linked l21+l22 (the bridge phrase "velo chen
dechen hu" quotes l22's "velo kol dechen hu" verbatim); 36-40 to l22
(the negaim a fortiori and its Leviticus 13 citation); 41 dual-linked
l22+l25 (concludes the Leviticus 13 citation, opens the "veshachat
otah lefanav" quotation matching l25 verbatim); 42-44 to l25 (the
Rav/Shmuel dispute over paro); 45 to l29 (exact match on "shelo yasiach
da'ato mimenah"); 46-47 to l32 (quotes l32's "hashta hu demitkashra
parah" verbatim); 48-51 to l36 (quotes l36's "lemautei mai" verbatim
and continues the same Numbers 19 citation l36 itself was truncated
mid-quoting); 52 unchanged (already correctly closed on l36 for the
daf-boundary truncated "lemishmeret", the same word documented at
VERSION 15.78). The originally flagged vilnaLine 50 is resolved as
part of this same l36 continuation, not as a standalone lead. l16, the
Gemara segment l31, and the second half of l29 (Shmuel's derivation)
remain legitimately without a Rashi comment on this daf; no ids were
invented, and no allowlist entries existed for 42a to remove.

Post-repair profile: ALIGNED, 5 anchors found, 0 missing, all offsets
zero (previously up to +2). Corpus semantic audit: 0 shift candidates.
Remaining open items are unchanged: 61a/67b-71b stubs, 77a-88a filler.
47a remains paused.

### 47a-52b Rashi semantic recovery campaign opened (VERSION 15.102), 47a reconstructed (rashi-reconstruction, Sonnet worker)

The 47a pause is lifted. Fresh diagnosis (raw count, current entries,
full segment table, drift profile) confirmed the daf's prior "suspected
reconstruction" lead: all 64 rashiTranslations entries were completely
unlinked and the English was 100 percent fabricated thematic narration
unrelated to the actual raw Hebrew (for example, closing with "47a is
one of the most humanly memorable pages of the Yoma tractate"). No
partial salvage was possible; classified rashi-reconstruction.

Rebuilt all 64 entries against the raw Hebrew and the 19-id local
segment table: vl1-6 the spoon/coal-pan Gemara and its Leviticus 16
proof text (l01, l05, l13); vl7-13 the nesi'im comparison and the
great/small-quantity hand-assignment reasoning (l20, l24); vl14-24 the
Kimchit zered/arsan etymology including a Berachot 37a citation at
vl19 (l27); vl25-32 the alternate "sh'chivat zera" etymology with a
Ruth 3 citation (l32); vl33-34 the Yom Kippur/tzinnora scene-setting,
dual-linked to l35 and l37 since the identical phrase recurs in both
Kimchit-son incidents; vl35-38 the Yerushalmi citation glossing
Kimchit's own words (l40); vl39-42 the kumtzo-baraita text and its
gloss (l43); vl43-48 the chofnav/kumtzo distinction and its gezeirah
shavah, dual-linked at the vl48 seam into l45; vl49-55 the "kach hayta
midatah" resolution, dual-linked at vl54 into l47a's forward citation
to 49a; vl56-60 the "dilma" alternative reading, dual-linked at the
seam into l48; vl61-63 closing the kometz baraita (l48). vl64
("uvmachavat") was checked against 47b's actual first raw Rashi line
(confirmed from source): it extends l48's just-closed kometz-precision
rule to griddle/pan offerings, so it is linked to l48 as a genuine
boundary continuation, truncated at the daf edge and continuing on
47b, not a positional catch-all.

All 5 of the semantic audit's citation anchors (Leviticus 16, Berachot
37a, Leviticus 2, the 49a forward-citation) now land at offset 0
(previously +24, missing, -19, missing). Post-repair profile: ALIGNED,
5 anchors found, 0 missing. Corpus semantic audit: 0 shift candidates.
No allowlist entries existed for 47a to remove. This opens the
47a-52b recovery campaign (queue committed in .worker-queue.json);
remaining targets: 47b, 48a, 48b, 49a, 49b, 50a, 50b, 51a, 51b, 52a,
52b. 61a/67b-71b stubs and 77a-88a filler remain open and out of
scope for this campaign.

### 47b reconstructed (VERSION 15.103, rashi-reconstruction, Sonnet worker)

Fresh diagnosis confirmed the same pattern as 47a: raw count 65 =
entries 65 (structurally sound), but all 65 entries were unlinked and
the drift profile was FABRICATION-SUSPECT (0 of 8 citation anchors
found). The English was fabricated thematic narration unrelated to the
raw Hebrew (for example closing with "That's the Talmud being the
Talmud" and "Perfect preparation for Rav Pappa's dilemmas"). Classified
rashi-reconstruction.

Rebuilt all 65 entries against the raw Hebrew and the 13-id local
segment table: vl1-9 the machavat/marcheshet difficulty with its
Hullin and forward 49b citations (l01); vl10-11 the bein habeinayim
opening (l05); vl12-15 the Menachot 9a citation on diminished shirayim
(l11); vl16-20 the kol shemimenu laishim exclusion with its Leviticus
2 citation (l17); vl21-32 the lesheim eitzim ruling and Rabbi
Eliezer's Zevachim 77b dispute (l19); vl33-39 the demaktzi shemeini
fat-fingers explanation (l23); vl40-51 the gezeirah shavah tying
kometz overflow to the chafinah vessel question (l26); vl52-56 Rav
Pappa's actual question with its Sukkah 37a citation (l30); vl57-64
the natural-grip and alternate-grip kometz descriptions (l32, l34,
l35). vl65 ("divkeih", truncated) was checked against 48a's actual
first raw Rashi line (confirmed from source), which opens "divkeih
lekometz bedofnei demana... kayma lan bemasechet Menachot (26a)" -
this confirms it is a genuine continuation of l37's own truncated
"ba'ei" (he asked), so it stays linked to l37 rather than being forced
or left unlinked.

All 8 of the semantic audit's citation anchors (the 49b forward
citation, Menachot 9a, Leviticus 2, Zevachim 77b, Sukkah 37a, and
their corresponding name tokens) now land at offset 0, versus entirely
missing before. Post-repair profile: ALIGNED, 8 anchors found, 0
missing. Corpus semantic audit: 0 shift candidates. No allowlist
entries existed for 47b to remove. Remaining campaign targets: 48a,
48b, 49a, 49b, 50a, 50b, 51a, 51b, 52a, 52b.

### 48a reconstructed (VERSION 15.104, rashi-reconstruction, Sonnet worker)

Fresh diagnosis confirmed the same pattern: raw count 42 = entries 42
(structurally sound), all 42 entries unlinked, drift profile
FABRICATION-SUSPECT (1 of 6 anchors found). Classified
rashi-reconstruction.

Rebuilt all 42 entries against the raw Hebrew and the 11-id local
segment table: vl1-4 the stuck-to-the-wall kometz question with its
Menachot 26a citation, including a legitimate forward gloss on the
word "tefufot" that belongs to a later segment (l01, l07); vl5-8 the
blood-on-the-floor Mishnah and its Zevachim 32a citation (l10); vl8-13
the mena hanei milei baraita on dam hanefesh and the gorin-umosifin
exegesis (l12, l19); vl13-27 the wrong-intent-in-incense question with
its full gezeirah shavah to the meal offering and Menachot 83a
citation, concluding into "posel et kulam" (l23, l27); vl28-31 the
eleven stringencies and Chagigah 20b citation (l27, l30); vl32-41
Rashi's own critical question about the Me'ilah 10a Mishnah (l30).
vl42 ("chishev", truncated) was checked against 48b's actual first raw
Rashi line (confirmed from source), which opens with the coal-raking
intent question - a direct extension of l30's own machshava theme, so
it links to l30 as a genuine boundary continuation. l04, l14, and l20
(the inverted-vessel question, the mikra-derasha reasoning for dam
hanefesh, and the scattered-incense question) are confirmed legitimate
content gaps with no Rashi comment.

All 6 of the semantic audit's citation anchors (Menachot 26a, the 32a
forward-reference, Menachot 83a, Chagigah 20b, Me'ilah 10a, and their
name tokens) now land at offset 0, versus only 1 of 6 found before.
Post-repair profile: ALIGNED, 6 anchors found, 0 missing. Corpus
semantic audit: 0 shift candidates. No allowlist entries existed for
48a to remove. Remaining campaign targets: 48b, 49a, 49b, 50a, 50b,
51a, 51b, 52a, 52b.

### 48b reconstructed (VERSION 15.106, rashi-reconstruction, Sonnet worker, anchor-poor-safe)

Fresh diagnosis: raw count 26 = entries 26 (structurally sound), all
26 entries unlinked, and the prior English invented a pigul/wrong-
intent-during-eating storyline unrelated to the actual Hebrew (which
covers whether preparatory coal-raking counts as a service act, then
whether left-hand carrying invalidates it). Classified
rashi-reconstruction.

Rebuilt all 26 entries against the raw Hebrew and the 4-id local
segment table: vl1-8 the raking-as-service question, dual-linked at
the seam into the left-hand-carrying question (l01a, l01b); vl9-18 the
receiving/tossing/carrying priesthood analysis with its Chagigah 11a
citation (l01b); vl19-22 the right-leg-carrying Mishnah proof (l05);
vl23-26 the atonement-dependent-carrying distinction (l07). vl26 (a
truncated word) was checked against 49a's own raw Rashi source and,
per the documented 10a vilnaLine 35 precedent, stays linked to l07 as
the daf's own closest local anchor regardless of the new topic it
opens on 49a.

This daf's raw Rashi genuinely contains only one citation (Chagigah
11a), split across two raw print lines so the anchor scanner's
per-line adjacency window can never pair the tractate name with its
daf number; the classifier therefore reports INSUFFICIENT-ANCHORS
rather than ALIGNED regardless of translation correctness (ALIGNED
requires 2+ anchors). This is the daf that prompted the anchor-poor-
safe review-gate exception added in PR #95 (VERSION 15.105,
docs-tooling): worker:review now accepts INSUFFICIENT-ANCHORS for
rashi-reconstruction/rashi-realignment when exactly one genuine
citation exists, is found at offset 0, no anchor is missing, and the
self-review's anchorPoorAttestation block confirms no citation was
invented, moved, or duplicated to satisfy the detector - all of which
hold here. No allowlist entries existed for 48b to remove. Remaining
campaign targets: 49a, 49b, 50a, 50b, 51a, 51b, 52a, 52b.

### 49a realigned (VERSION 15.107, rashi-realignment, Sonnet worker)

Fresh diagnosis confirmed the previously-suspected "mixed" state: raw
count 64 = entries 64 (structurally sound), all 64 entries unlinked,
and classification ALIGNED but with only 2 of 4 citation anchors
found. Manual line-by-line comparison found most entries were genuine,
if imprecisely bounded, translations rather than fabricated, with a
real localized shift around vilnaLine 16-24 (the English anticipated
content from raw lines one or more positions ahead of its own
vilnaLine). Classified rashi-realignment.

Rebuilt all 64 entries so each translates only its own raw print line,
linked semantically against the 20-id local segment table: vl1-7 the
zar/onen/shikor/ba'al-mum disqualification list and its Zevachim 16a
citation (l01, l03); vl8-14 the text-critical note and the
itztaba-bench elaboration (l08, l10); vl15-19 Rav Pappa's chafinah
dilemma into Rabbi Yehoshua ben Levi's scoop-and-die question (l12,
l15); vl19-31 Rabbi Chanina's paraphrase and the shachalayim/cress
remedy digression proving seniority (l15, l17); vl32-43 Rabbi
Chanina's refined restatement and the bull-not-blood ruling with its
Leviticus 16 citation (l32, l34); vl44-59 Rabbi Chanina's
incense-before-slaughter ruling and Rashi's proof of Yehoshua ben
Levi's position (l36, l38, l41); vl59-63 Rav Pappa's and Rav Huna's
opposing positions on chofen-chozer-vechofen (l41, l46, l43). vl64 (a
truncated word) was checked against 49b's actual first raw Rashi line
(confirmed from source), which opens describing the mechanics of "the
second scooping, which is inside" - directly explaining l46's own
"is its measure inside like its measure outside" question, so it links
there as the semantically correct anchor. l47 and l48 are confirmed
legitimately unused by any Rashi comment on 49a.

All 4 of the semantic audit's citation anchors (Zevachim 16a,
Deuteronomy 18, Leviticus 16, and their name tokens) now land at
offset 0, versus 2 of 4 found before. Post-repair profile: ALIGNED, 4
anchors found, 0 missing. Corpus semantic audit: 0 shift candidates.
No allowlist entries existed for 49a to remove. Remaining campaign
targets: 49b, 50a, 50b, 51a, 51b, 52a, 52b.

### 49b realigned via zero-anchor-safe evidence tier (VERSION 15.109, rashi-realignment, Sonnet worker)

Fresh diagnosis confirmed the previously-suspected shifted state: raw
count 21 = entries 21 (structurally sound), all 21 entries unlinked,
and a genuine internal shift where raw5 ("reaches the height of his
palm, and he then turns it back") was skipped entirely, with two
adjacent entries redundantly describing the same later action.
Classified rashi-realignment.

Rebuilt all 21 entries so each translates only its own raw print line,
linked semantically against the 9-id local segment table: vl1-7 the
second, inside incense-scooping mechanics into the Pesach-registration
opening (l01, l16); vl7-15 the register/withdraw rules, the
"mihyot miseh" derivation, and Mar Zutra's firstborn-donkey-redemption
objection (l16, l18a, l18b); vl16-20 the calf/wild-animal/kilayim/koi
exclusions from "sheep" (l18b). vl21 (a truncated word) was checked
against 50a's own raw Rashi source and, per the documented 10a
vilnaLine 35 precedent, stays linked to l18b as the daf's closest
local anchor. l20 and l22 are confirmed legitimately unused.

Unlike every other daf in this campaign, 49b's raw Rashi contains
ZERO citation anchors of any kind (0 found, 0 missing, both before and
after this edit) - a more extreme case than 48b's single split
citation. Its classification is therefore INSUFFICIENT-ANCHORS and can
never become ALIGNED, and it did not qualify for the anchor-poor-safe
exception added in PR #95/#96 either, since that exception requires
exactly one genuine anchor, not zero.

Rather than extend the one-anchor exception ad hoc, PR #98 generalized
the review gate into a source-relative, 3-tier citation-evidence policy
(multi-anchor-safe, one-anchor-safe, zero-anchor-safe) dispatched
purely on the daf's own anchor count. 49b qualifies for the new
zero-anchor-safe tier: two independent scans (the primary drift-profile
scanner and an independent whole-text parenthetical regex search) both
confirm zero citation-like text anywhere in the raw Hebrew, corroborated
by a full manual reread of all 21 lines, with the self-review's
zeroAnchorAttestation block confirming no citation was invented, moved,
or duplicated and no semantic uncertainty remains. Merged under
zero-anchor-safe. Remaining campaign targets: 50a, 50b, 51a, 51b, 52a,
52b.
