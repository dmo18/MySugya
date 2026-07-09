# Yoma Rashi helper workflow: guarded operating model

This document defines how Rashi helper work is performed after the Phase 1
and Phase 2 guardrails (VERSION 15.75 and 15.77). It exists because
placeholder and non-faithful helper text reached main three separate times
before automated gates existed. The gates now bear the safety load; roles
are split so that no single actor can bypass them.

## Roles

- Fable (or another frontier model) builds and maintains the guardrails,
  performs forensic audits, designs repair passes, and handles every
  semantic escalation. Only Fable/Sonnet may make Hebrew translation or
  placement judgments.
- Haiku (or another small model) may perform bounded Rashi work ONLY
  inside the guardrails: executing a prepared work packet, running the
  validators, committing, and doing mechanical CI/deploy polling.
- Haiku may NOT override or reinterpret a validator failure, may NOT add
  or edit allowlist or baseline entries (the PR scope gate enforces
  remove-only), and may NOT proceed past any uncertain Hebrew meaning or
  placement. The required action on failure or uncertainty is stop and
  escalate to Fable/Sonnet.
- No content PR merges unless every offline gate passes in CI. There are
  no exceptions; a red gate means the content is wrong or the scope was
  exceeded.

## The gates

Chained by `npm run validate:offline:yoma` (also run in CI on every PR and
push, and by the pre-commit hook when Yoma data is staged):

1. `check:generated:yoma` - learning_data.js/coverage.json must be exactly
   what regeneration produces.
2. `validate:schema:yoma` - sugya display/learning schema completeness.
3. `validate:daftext:yoma` - daftext files match talmud.dev source.
4. `validate:rashi:yoma` - structural: he order/count, en present,
   enSource stamped, no leak into Gemara.
5. `validate:rashi:content:yoma` - content patterns: placeholders,
   scaffold, filler, dashes, count mismatches. Ratchet allowlist.
6. `validate:rashi:links:yoma` - linkedGemaraLineIds referential
   integrity. Ratchet allowlist (currently empty; keep it empty).
7. `validate:rashi:dupes:yoma` - within-daf template repetition. Ratchet
   baseline.
8. `audit:order:yoma` - Vilna ordering.

PR-context only (CI + hook): `check:rashi-pr-scope:yoma` - a content PR
may change only rashiTranslations en/linkedGemaraLineIds inside learning
JSONs, only allowed files overall, never workflows, and allowlists may
only shrink. Structure changes require an explicitly authorized
`--allow-structure` pass.

Advisory (never blocks): `audit:rashi:semantic:yoma` - ranked report of
likely shifted-English blocks and missing Hebrew anchors. Run it after
any content pass and before declaring a daf done; treat new shift
candidates at offset beyond +-1 as escalations.

## Bounded work procedure (per daf)

1. Fable (or the coordinator) generates the work packet:
   `npm run rashi:packet:yoma -- <daf>` (add `--json` for machine form).
   The packet contains the raw Hebrew, the ONLY legal Gemara ids, current
   state, validator baselines, the rules, and the post-edit commands.
2. The worker translates every raw line from its own Hebrew. Linking
   policy (nearest preceding Gemara id; final id for end-of-daf overflow)
   never exempts a line from genuine translation.
3. The worker edits only rashiTranslations en/linkedGemaraLineIds in that
   daf's learning JSON, regenerates, bumps VERSION, syncs.
4. The worker runs all post-edit commands from the packet. Any failure:
   stop and escalate; do not adjust gates, baselines, or allowlists.
5. One PR per bounded pass. Merge only when CI is green. Verify the main
   deploy workflows after merge.

## Escalation triggers (stop immediately)

- any validator or CI failure the packet's commands cannot explain
- uncertain Hebrew meaning or uncertain placement
- raw count vs entry count mismatch not already baselined
- the semantic audit reports a new shift candidate in the touched daf
- any need to touch a file outside the packet's scope

## Current deferred content debt (do not touch without a scoped pass)

See docs/rashi-audit-backlog.md for the authoritative list: 41a shifted
block, 42a/42b leftover placeholder lines, 8a/9a phantom entry counts,
61a/67b/68a/68b/70a/71b stubs, 77a-88a filler block. 47a onward is paused
until repairs are scheduled.
