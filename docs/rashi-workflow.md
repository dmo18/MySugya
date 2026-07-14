# Yoma Rashi helper workflow: guarded operating model

This document defines how Rashi helper work is performed after the Phase 1
and Phase 2 guardrails (VERSION 15.75 and 15.77). It exists because
placeholder and non-faithful helper text reached main three separate times
before automated gates existed. The gates now bear the safety load; roles
are split so that no single actor can bypass them.

## Roles

- Fable builds and maintains the guardrails, performs forensic audits,
  designs repair passes, owns docs/workflow/branch hygiene, and handles
  every escalation. Since VERSION 15.93 Fable is NOT the routine per-PR
  reviewer for semantic daf work: rashi-realignment and
  rashi-reconstruction run under the conditional review policy (see
  below), and Fable reviews only when an escalation condition fires.
  Fable performs daf content work only when explicitly substituting
  because Sonnet is unavailable.
- Sonnet is the default worker for semantic daf work: Hebrew
  translation, placement judgments, shifted-daf realignment
  (rashi-realignment), and fabricated-daf reconstruction
  (rashi-reconstruction). Only Fable/Sonnet may make Hebrew translation
  or placement judgments; Haiku is not allowed on those task types. On
  the two conditional types Sonnet executes end to end: repair, fresh
  post-edit self-review, CI, the worker:review auto-merge gate, merge,
  deploy verification, and progression to the next queued target.
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

Drift profile (blocks repair-type preflight only):
`audit:rashi:drift:yoma` (audit_rashi_semantic.py --profile) classifies
every daf from citation anchors (colon-tolerant amud citations,
tractate names adjacent to daf citations, gematria daf numbers, split
citations, search window 25):

- SHIFTED: the English is genuine but displaced from its Hebrew
  (2+ distinct lines nonzero same-sign offsets including one beyond 2).
- FABRICATION-SUSPECT: 2+ consecutive non-allowlisted Hebrew citation
  anchors appear nowhere in the English.
- ALIGNED / INSUFFICIENT-ANCHORS: haiku-safe.

On a SHIFTED or FABRICATION-SUSPECT daf, `rashi_preflight` FAILS any
line-level task (repair, links): stub-only work there duplicates
content and cements misalignment. The remedies are rashi-realignment
(shifted) and rashi-reconstruction (fabricated), Sonnet worker under
the conditional review policy (Fable substitutes as worker only when
Sonnet is unavailable; Fable reviews only on escalation). Override is
Fable-only: the manifest must carry
authorizeDriftOverride AND the environment must set
FABLE_DRIFT_OVERRIDE=1; worker prompts never mention either. The work
packet embeds each daf's profile, and worker:verify enforces a clean
post-edit profile for both rashi-realignment and rashi-reconstruction
PRs. Tests: `npm run test:drift:yoma` (part of `npm test`).

## Structural repair (VERSION 15.97)

The baselined entry-count mismatches (8a: 41 entries vs 35 raw lines;
9a: 22 vs 18) are structural defects: phantom entries with no raw-line
anchor, not helper-content problems. They are handled ONLY by the
rashi-structural-repair task type: Fable worker, one daf per PR,
conditional review, and a REQUIRED explicit allowStructure manifest
authorization; preflight fails without it, and no other task type can
carry it, so ordinary line-level passes can never change entry counts.
Post-repair, the review gate requires exact entry-count and vilnaLine
parity with the talmuddev raw lines, semantic links for every entry,
and the standard fresh self-review; the count-mismatch baseline entry
is removed only when the content validator reports it stale.

## Conditional semantic review (VERSION 15.93)

rashi-realignment and rashi-reconstruction no longer require an
unconditional Fable review on every PR. The registry marks them
`reviewPolicy: "conditional"` with `escalationModel: "fable"`; the
worker (Sonnet) merges its own PR WITHOUT operator or Fable sign-off
only when every auto-merge condition holds, and otherwise escalates.
The full condition list, the fresh self-review contract
(.worker-self-review.json), the mandatory escalation conditions, and
the autopilot queue commands live in docs/worker-pipeline-sop.md
(single source). Enforcement: `npm run worker:review` (machine gate,
fails closed), `npm run worker:queue` (sequential one-PR-per-daf
autopilot, stop-on-escalation), `npm run test:policy` (positive and
negative coverage, in npm test). No offline validation gate, scope
rule, ratchet, freshness check, or drift block was weakened; the
change replaces only the human review step for the routine, fully
green case.

## Bounded work procedure (per daf)

1. Fable (or the coordinator) generates the work packet:
   `npm run rashi:packet:yoma -- <daf>` (add `--json` for machine form).
   The packet contains the raw Hebrew, the ONLY legal local segment ids
   (Gemara AND Mishnah kinds, in source order, each with its kind and
   FULL untruncated Hebrew text), current state, validator baselines,
   the rules, and the post-edit commands.
2. The worker translates every raw line from its own Hebrew. Linking is
   SEMANTIC: each Rashi comment links to the segment(s) whose text it
   explains, matched by dibbur hamatchil, quoted phrase, subject, or
   discussion against the packet's full segment text. Links are NEVER
   assigned by vilna line number or positional offset. A comment may
   link to multiple segments when it genuinely spans them. A line whose
   commentary continues the final segment's own discussion past the
   last id stays on that final id (boundary policy); boundary policy
   never covers unrelated commentary and never exempts a line from
   genuine translation. If the correct target cannot be identified from
   the packet, stop and escalate; never guess.
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

## Standard automation loop (VERSION 15.79)

Every bounded pass follows this loop; each step is a single command:

1. Preflight: `npm run rashi:preflight:yoma -- <daf> [--task repair]`
   Fails on dirty tree, inactive hooks, stale generated data, malformed
   daf, or allowlisted defects when the task is not a repair type.
2. Packet: `npm run rashi:packet:yoma -- <daf>` (context source of truth).
3. Edit: only the target daf's rashiTranslations en/linkedGemaraLineIds.
4. Regenerate + VERSION bump + sync.
5. Verify: `npm run rashi:verify:yoma -- <daf> --fast`, then `--full`
   before the PR. Prints per-gate pass/fail, files changed, allowlist
   delta (additions are a hard fail), and scoped semantic-audit warnings.
6. One PR, wait for CI, merge only when green.
7. Verify the two main deploy workflows after merge.
8. Stop, report one compact line, await the next authorization.

Worker models may handle CI/deploy polling mechanically ONLY after local
`rashi:verify:yoma --full` has passed. A worker prompt for any pass is
generated with `npm run rashi:prompt:yoma -- <daf> --task <type>`; do not
hand-write worker prompts.

## Allowlist growth lockout

The scope gate enforces the ratchet on every PR, including tooling PRs
that touch no learning JSON: allowlist entries may be removed but never
added. Authorized restructuring (a tooling PR documenting a newly
audited baseline) requires running the gate with
RASHI_ALLOWLIST_RESTRUCTURE=1, which prints a loud authorization note.
Worker models never set that variable.

## Recommended GitHub branch protection (manual settings, not in repo code)

These cannot be set from repository files; an admin should configure them
at Settings > Branches > main:

- Require status checks to pass before merging: ON
  - required check: `build` (the Deploy GitHub Pages workflow's PR job,
    which runs the 9 offline gates and the Rashi PR scope check)
- Require branches to be up to date before merging: ON (serializes
  content PRs, matching the sequential merge discipline this workflow
  already uses and preventing stale-base merges)
- Block force pushes: ON; Restrict deletions: ON
- Require a pull request before merging: ON (no direct pushes to main)
- Dismiss stale approvals on new commits: only relevant if review
  requirements are enabled; recommended ON in that case

## Semantic linking contract (VERSION 15.91)

PR #80 (68b realignment) exposed a packet-generator defect: the legal
id table collected only kind "gemara" segments, so the end-of-perek
Mishnah yoma-068b-l13b was missing, and the worker fell back to
positional linking (Rashi line N to the segment at vilna N). Fable
review had to correct 50 of 60 links. The fix (this section's version):

- make_rashi_work_packet.py emits every kind-bearing local segment,
  Gemara AND Mishnah, in source order, with kind and full untruncated
  Hebrew text; sparse and suffixed ids (l13a/l13b, l41a/l41b,
  l53a/l53b) come through verbatim and nothing is renumbered or
  manufactured. The same audit confirmed 70a (l27) and 71b (l11) each
  carry a Mishnah segment the old table would also have dropped.
- Packet rules, rashi_prompt.py, and the pipeline prompt all state the
  semantic contract explicitly and forbid positional assignment; the
  four Rashi task types escalate when a comment's target segment
  cannot be identified from the packet.
- Regression tests: `npm run test:packet:yoma` (part of `npm test`)
  pins l13b presence/kind/order, sparse-id preservation, full text,
  packet-side referential completeness for every daf, and the
  anti-positional language in every generated prompt.

## Project-wide worker pipeline (VERSION 15.80)

The Rashi loop above has been generalized to all bounded work types via
the worker pipeline: task-type registry, per-PR manifests, unified
preflight/packet/prompt/verify/scope commands, and a CI manifest check
that fails any content PR lacking a manifest and any workflow edit
lacking a docs-tooling manifest. See docs/worker-pipeline.md. Nothing in
this document is weakened: the Rashi commands remain the enforcement
core and are delegated to by the pipeline for Rashi task types.
