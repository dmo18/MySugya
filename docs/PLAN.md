# Plan

Written: 2026-11-19 at VERSION 15.600. Status: approved by owner redirect, running.

Owner answers that shape this plan:

- Scope: safety fixes first, then re-validate every daf from 2a.
- PR #663 (old 18b attempt): ignore it, redo 18b fresh.
- Merging: automatic when every gate passes (merging publishes).

## Milestone 1: Safety

### Task 1. Test before the Cloudways publish

- Files: `.github/workflows/deploy-cloudways.yml`
- Depends on: nothing
- Decision: keep the publish, but run `npm test` and
  `npm run check:deploy-html` before the push step. Do not change
  what gets published. Narrow nothing else.
- Accept: the push step cannot run when a test fails.
- Proof: workflow file review plus a green run on `main` after merge.
- Model: Sonnet. Review: Opus.

### Task 2. Add a linter

- Files: `package.json`, `package-lock.json`, new `eslint.config.mjs`,
  `.github/workflows/deploy-pages.yml` (one new step)
- Depends on: nothing
- Decision: ESLint, exact pinned version, dev dependency only.
  Reason for the new dependency: the project has no automatic code
  mistake checker. Scope: `app.jsx`, `tweaks-panel.jsx`,
  `manifest.js`, `shared/`, `scripts/*.mjs`, `tests/`. Never lint
  `modules/`, `dist/`, or generated data. Start with rules that
  catch real mistakes only (undefined names, unused variables as
  warnings, unreachable code). Do not reformat or refactor existing
  code. Any real mistake found is reported, not silently rewritten.
- Accept: `npm run lint` exits 0, `npm audit` shows 0
  vulnerabilities, `npm test` and browser tests still pass.
- Proof: those four commands.
- Model: Sonnet. Review: Opus.

Milestone 1 ends with a security review by a fresh Opus subagent,
a version bump through `scripts/sync_version.py`, one pull request,
and an automatic merge.

## Owner redirect (2026-11-19)

"Assume nothing is certified. Assume existing data is fake and needs
validation for all daf. Start at the beginning."

So: the 95 existing certificates are NOT trusted. Every daf from 2a
to 88a gets a full fresh review, in order. The old 18b-first plan
is replaced by the milestones below.

## Milestone 2: Source text check, all 173 daf

### Task 3. Compare stored source text with live Sefaria

- Run every source gate (`validate:yoma`, `audit:order:yoma`,
  `validate:en:yoma`, `validate:daftext:yoma`, `validate:rashi:yoma`,
  `validate:literal:yoma`, `validate:schema:yoma`) against the live
  Sefaria service and record exact results per daf.
- Changes nothing. Any mismatch is reported, not auto-fixed.
- Model: main session (commands only).

## Milestone 3: Daf 2a (pilot)

## Milestone 4: Daf 2b, 3a, 3b, 4a, 4b

Tasks 4 to 9 are one daf each. After Milestone 4 the measured cost
per daf is reported and the remaining 167 daf continue in batches
under a new cap the owner approves.

Each daf follows `docs/claude-semantic-campaign-runbook.md` and
`docs/semantic-self-heal.md` exactly, and ignores any existing
certificate:

1. First pass and repair. A fresh Opus subagent reads the Hebrew
   source first, rebuilds the page flow, checks every field of every
   topic, and repairs the whole record in one pass through a repair
   manifest. Raw source and `rashiTranslations` stay untouched.
   Generated data is rebuilt with the normal generator.
2. Independent second pass. A fresh Fable subagent that never sees
   the first pass reasoning. Verdict per topic: CONFIRMED, REJECTED,
   or BLOCKED.
3. Final whole-record audit. Another fresh Fable subagent.
4. State changes only through `scripts/semantic_review_state.py`,
   starting again from `first` even when the record already reads
   CERTIFIED. No hand-written fingerprints. Review ids from this
   run start with `rv3-` so fresh work is distinguishable.
5. All gates in the runbook section "Mandatory gates before PR
   completion", then one pull request per daf, merged in order.

- Files per daf: `modules/yoma/assets/learning/yoma/<daf>.learning.json`,
  `modules/yoma/learning_data.js` (generated),
  `docs/reports/data/yoma-semantic-certifications.json`,
  `.semantic-repair-manifest.json`, `VERSION` and synced files.
- Accept: every topic on the daf carries a fresh `rv3-` certificate,
  reads CERTIFIED in `validate_semantic_certification.py --report`,
  the ratchet passes, and every other gate is green.
- Stop rules: a topic that cannot be resolved from the source is
  marked BLOCKED and reported, never guessed. A REJECTED verdict
  sends the record back to repair one time. A second rejection on
  the same daf stops that daf and reports it.

## Run cap

- Tasks: 9 planned, limit 11.
- Delegated tokens: limit 3,500,000.
- Five failed attempts in total stops the run.

## Preview

Live site after each merge, for example
`https://dmo18.github.io/MySugya/?module=yoma&daf=18b`, plus a
phone-size screenshot in the chat.

## Security items that apply

Secrets scan before every commit, dependency pinning and audit
(Task 2), least-privilege workflow permissions (Task 1), output
encoding guards already covered by `npm test`.

## Skills used

`security-review` and `code-review` (built in).
