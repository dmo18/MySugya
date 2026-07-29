# Open items and current status

One concise, classified inventory of everything the repository still tracks as
open, paused, deferred, historical, completed, or unknown. Produced by a
read-only repository-wide sweep at **VERSION 15.338, commit `ef58878`**,
updated through the Step 2 review at **VERSION 15.341**.

This is the single current source of truth for "what is still outstanding".
Where a longer document disagrees with this one, this one is current and the
other is a historical record; superseded sections in those documents are
labelled in place.

The ordered plan that closes the remaining platform work (production
publishing and repository protection, the argumentFlow/sourceRefs schema
contracts, tractate-agnostic replication, and final closure) is
`docs/platform-closure-plan.md`. This document remains the classified
day-to-day inventory; that one is the phased execution plan.

Classification key:

| Class | Meaning |
|---|---|
| **OPEN-ACTIONABLE** | Real work, authorized, can start now |
| **PAUSED** | Blocked pending authorization or missing tooling |
| **DEFERRED-ROADMAP** | Intentional future scope, not a defect |
| **HISTORICAL** | Superseded record, preserved deliberately |
| **COMPLETED** | Done and verified |
| **UNKNOWN-OPERATOR** | Needs an operator/admin decision or action |

---

## Current verified platform state (VERSION 15.357, `main`)

- Corpus: Yoma, 173 daf (2a-88a), 492 sugyot, 8,854 `rashiTranslations` and
  8,854 runtime `rashiLines`.
- Associations: 10,047 declared `linkedGemaraLineIds` (7,648 single-link,
  1,186 multi-link, 279 Mishnah, 447 suffixed-id, 0 sparse, 20 boundary),
  **0 broken, 0 cross-daf**.
- Renderer: **linked is the only renderer.** It became the production
  default at VERSION 15.338 and the legacy renderer plus the `?rashiAssoc`
  selector were removed at VERSION 15.346. A leftover `?rashiAssoc` value of
  any kind, including the retired `legacy`, is ignored and renders linked.
  Nothing about renderer choice is persisted.
- Renderer readiness: **8/8**.
- Deployment: **GitHub Pages (https://dmo18.github.io/MySugya/) is the
  authoritative beta deployment**, serving VERSION 15.338.

### Cutover evidence (recorded here as the durable record)

| Item | Value |
|---|---|
| Cutover VERSION | 15.338 |
| Merge commit | `ef58878fd5c8ad4593909786edf02ac984bc365c` |
| Cutover PR | #331 |
| Browser shard workflow run | `30403330781` |
| Combined artifact | `rashi-browser-shard-result`, id `8705825544` |
| Shards | 8 |
| Daf coverage | 173/173, zero missing, zero duplicate |
| Rashi entries | 8,854 |
| Tests | **215 passed, 0 failed** |
| Readiness gate | 8/8 READY at the exact merge commit |

The pre-cutover 8/8 authorization run was workflow `30399334278` / artifact id
`8704117259` at commit `d1e4715` (173/173 daf, 8,854 entries, 183 passed, 0
failed). Both artifacts were verified independently: zip digest, exact commit
SHA, `ci=true`, per-shard union equal to the authoritative daf list, and
per-shard test-count arithmetic reproduced from first principles.

---

## OPEN-ACTIONABLE

| Item | Detail |
|---|---|
| Rashi translation-quality audit coverage | The corpus-wide translation-quality (not scaffold, not association) audit is not yet complete for every daf. A git-history-grounded coverage map exists in `docs/rashi-audit-backlog.md` but predates the 7a/9b repairs and the post-15.293 work. Reconstructing an exact per-daf audited/unaudited/uncertain list is the next actionable step. |

| `argumentFlow.type` controlled vocabulary | **Mislabelling fixed at 15.350; the vocabulary decision is still open.** `schema_map.js` declares the field required and canonical over 13 values; the corpus uses 106 more across 1,320 of 1,953 steps (417/492 sugyot, 163/173 daf). The renderer no longer mislabels them: `stepMetaFor` shows an unrecognised type's own name instead of falling back to the `question` entry, and leaves Hebrew empty rather than inventing it. What remains is editorial and mutually exclusive: widen `controlledValues.argumentStepType` (each new `STEP_META` row needs a Hebrew term and symbol, which cannot be invented) or re-type the 1,320 steps down to 13 (lossy, `structural-repair` scope). A new tractate must not inherit this drift. See `docs/reports/sugya-schema-readiness.md`. |
| Replication tooling parameterization | 7 shared tools at the repo root hardcode `modules/yoma`, chief among them `worker_pipeline.py`, whose `--module` flag is cosmetic because `YROOT` is pinned. Blocks any second tractate from using the worker pipeline. Not urgent while Yoma is the only module. See `docs/reports/replication-readiness.md`. |

Nothing else is currently blocked on code.

---

## PAUSED

| Item | Why paused | Unblocking condition |
|---|---|---|
| `argumentFlow.sourceRefs` normalization | **Unblocked as tooling, now blocked on content judgment.** The canonical schema, validator (`npm run validate:sourcerefs:yoma`), unit tests, and dry-run migration preview (`npm run preview:sourcerefs:yoma`) all exist as of VERSION 15.347. The migration is still not applied: of 550 defective refs across 102 daf, 412 are mechanically repairable with all losslessness invariants passing, but 138 need a human reading the step text against the Gemara, and the 331 sound string refs cannot be converted without inventing a `sourceType`. Full inventory and four-PR plan: `docs/reports/source-refs-normalization-plan.md`. | Operator authorization for the judgment PRs (plan PRs 1 and 2), which are `structural-repair` scope. Nothing renders `sourceRefs` today, so nothing is blocked on it. |

---

## OUT-OF-SCOPE (intentional, not paused, not backlog)

These are settled decisions. They are not work waiting for a trigger, and no
worker or agent should treat them as incomplete.

| Item | Decision |
|---|---|
| Nekudot / vowelization of `he:` fields | **Intentionally out of project scope.** Not paused work, not a backlog item, and not a gap in the Yoma campaign. No nekudot audit, no nekudot validator design, and no unpausing of the `nekudot` task type is authorized. The type remains `paused: true` in `scripts/worker_task_types.json` as a guard, not as a queued item. `validate_rashi.py` checks Hebrew alignment only and that is the intended scope. No `rashiTranslations[*].he` edit is authorized on vowelization grounds. Reopening this requires an explicit operator decision that changes project scope. |
| mysugya.com / Cloudways deployment | GitHub Pages is the authoritative beta deployment. The custom domain serving an older bundle is **not** stale deployment debt and is not to be repaired by this campaign. |

---

## DEFERRED-ROADMAP

| Item | Detail |
|---|---|
| Additional tractates (all non-Yoma) | Product roadmap, **not** incomplete Yoma work. No module exists for any other tractate and none should be started without operator selection. Prerequisites are listed in `docs/new-tractate-onboarding.md`; the definitive, evidence-backed checklist is `docs/reports/replication-readiness.md`. |

---

## UNKNOWN-OPERATOR

| Item | Observed state | Action owner |
|---|---|---|

Nothing currently requires operator/admin action. Both items previously
listed here (`main` branch protection, the GitHub Pages dual-publisher race)
were resolved by the repository owner at VERSION 15.357 and moved to
COMPLETED below.

---

## COMPLETED

| Item | Evidence |
|---|---|
| Scaffold-fabrication remediation campaign | 0 debt entries across 0 daf; `audit_rashi_scaffold.py` clean; content allowlist empty. |
| `linkedGemaraLineIds` association layer | 0 broken, 0 cross-daf across 10,047 associations. |
| Linked-renderer cutover | VERSION 15.338 at `ef58878`; see the evidence table above. |
| `takeaway.type` normalization | **0 non-canonical values remain.** All corpus values are within the canonical set (`logical_principle`, `derivation_principle`, `legal_principle`, `conceptual`, `open_question`). The "57 sugyot carry non-canonical values" statement in `docs/yoma-perek-review.md` describes the pre-Phase-4 state and is superseded. |
| Worker queue `.worker-queue.json` (rashi-reconstruction 79b-88a) | **All 18 targets have merged reconstruction commits on `main`.** See the note below on why the derived status reads "none". |
| 61a, 67b, 68a, 68b, 70a, 71b | All six daf named in `docs/reports/rashi-lookalike-shift-audit.md` as needing reconstruction/realignment were repaired and now classify **ALIGNED** with `lineLevelSafe=true` and no recommended task type. That report's remediation instructions are historical. |
| `docs-tooling` scope gap for `modules/yoma/MODULE.md` | **Resolved at VERSION 15.340** (PR #333): the single documentation path was added to `allowedFiles`, with regression tests pinning that every corpus path stays refused. |
| Legacy renderer retirement | **Done at VERSION 15.346** by explicit operator decision. The legacy vilnaLine branch, the `?rashiAssoc` selector, and the legacy map/state were removed; `linkedGemaraLineIds` is the only association mechanism. A leftover `?rashiAssoc` value of any kind is ignored and renders linked. See `docs/reports/legacy-renderer-retirement-policy.md` (now closed). |
| 7a, 9b corrections | 7a realignment (53 entries, PR #326); 9b full reconstruction (41 entries, PR #327). |
| `main` branch protection | **Resolved at VERSION 15.357** (Phase 1 of `docs/platform-closure-plan.md`, operator-configured). Confirmed by direct API read-back of repository ruleset `19991220`: applies to `refs/heads/main`, enforcement active, PR required, 0 mandatory approving reviews (none added beyond what the owner configured), squash/merge/rebase all still allowed, required status check exactly `build`, strict/up-to-date enforcement true, force pushes and branch deletion both blocked, `current_user_can_bypass: "never"` with no bypass actors listed. Full table in the plan document's Phase 1 completion record. |
| GitHub Pages dual-publisher race | **Resolved at VERSION 15.357** (Phase 1 of `docs/platform-closure-plan.md`, operator-configured). The Pages configuration endpoint itself remains unreadable from any session (environment proxy blocks `/repos/.../pages` unconditionally), so this is confirmed behaviorally and via live checks rather than by reading the setting's value directly: five cache-busted public checks spaced across a 9-minute window all served the identical `assets/app-15.356.js` at HTTP 200 with zero development-loader tokens, and the merge of the Phase 1 evidence PR (a real push to `main`) produced no competing `pages build and deployment` run against the merge commit. See the plan document's Phase 1 completion record for the full evidence chain, including the prior directly-observed defect this resolves (VERSION 15.352-15.353, both outcomes of the race caught live). |

### Worker queue: completed, with an explained derived status

`npm run worker:queue` currently prints `done (derived from merged PRs): none |
remaining: [79b ... 88a]`. **This is a derivation artifact, not an
inconsistency, and no content work should be restarted because of it.**

`derive_queue_progress` intentionally derives progress from a single piece of
durable evidence: the `.worker-manifest.json` currently at `origin/main`. It
marks targets done only when that manifest's type, module, and single target
all match the queue. The manifest at `origin/main` now targets `9b`
(rashi-reconstruction from PR #327), which is outside this queue's target
list, so the derivation correctly declines to advance anything and reports
`none`.

Independent verification shows every one of the 18 targets (79b, 80a, 80b,
81a, 81b, 82a, 82b, 83a, 83b, 84a, 84b, 85a, 85b, 86a, 86b, 87a, 87b, 88a) has
a merged reconstruction commit on `main`. The campaign is **complete**.

The queue definition remains tracked and unmodified on purpose: it is an
immutable record of what that campaign committed to. `--advance` is retired by
design, progress is never written back, and rewriting or deleting the
definition would destroy the audit trail without changing any derived result.
The correct reading is: *this queue describes a finished campaign; its
derivation window has moved past it.*

---

## HISTORICAL (preserved, superseded sections labelled in place)

| Document | Status |
|---|---|
| `docs/reports/rashi-lookalike-shift-audit.md` | Historical. Its "needs reconstruction" / "MUST NOT run rashi-repair" instructions for 61a and 67b-71b were acted on and are complete. |
| `docs/yoma-perek-review.md` | Historical perek-by-perek review. Its non-canonical `takeaway.type` counts are superseded (now 0). |
| `docs/yoma-completion-report.md` | Historical phase record (VERSION 14.43-14.66). |
| `docs/reports/rashi-association-audit.md` | Carries a current section at the top plus the historical VERSION 15.157 introduction record. |
| `docs/reports/yoma-rashi-scaffold-audit.md` | Historical description of the scaffold gate and ratchet; debt is now zero. |
| `docs/worker-pipeline.md` readiness matrix | Historical VERSION 15.80 snapshot, labelled as such. |

---

## Standing constraints (not open items, but binding)

- **The 20 boundary entries (4b L61; 61a L46-64) are authorized and
  intentionally unrendered.** They are recorded in
  `modules/yoma/scripts/allowlists/rashi_boundary_authorizations.json` and
  validated by `validate_rashi_boundary_authorizations.py` (ratchet 20/20, 0
  stale, 0 duplicate, 0 unauthorized). Each is a comment whose Gemara content
  is truncated at the daf's final line and completes on the next daf, where
  cross-daf linking is prohibited. They are **not** a defect and **not** a
  backlog item.
- **The 14 semantic findings are advisory and do not authorize content
  edits.** All 173 daf classify with zero SHIFTED, zero
  FABRICATION-SUSPECT, and zero recommended task types. The 14 remaining
  findings sit on otherwise ALIGNED (or INSUFFICIENT-ANCHORS) daf and are
  reported in full by the readiness gate every run, never suppressed. They
  become actionable only if a fresh audit promotes one.
- **Daf 24b is a benign Unicode-normalization finding, not a content
  defect.** A direct comparison against the live Sefaria API found only a
  combining-mark ordering difference (dagesh/tsere sequence) between the
  local talmud.dev-derived text and Sefaria's; the consonantal and
  vocalization content is identical. No source-text change is warranted, and
  24b source text must not be edited on the strength of this finding.
- **GitHub Pages is the authoritative beta deployment.** mysugya.com and
  Cloudways/custom-domain configuration are out of scope.

---

## Branch protection: recommended vs actual (VERSION 15.357, resolved)

**Superseded.** As of VERSION 15.341 every recommendation below was
unenforced; as of **VERSION 15.357** the repository owner configured
ruleset `19991220` and every recommendation is now enforced, confirmed by a
direct API read-back rather than inferred:

| Recommendation | State at 15.341 | State at 15.357 |
|---|---|---|
| Require a pull request before merging | Not enforced (`protected: false`) | **Enforced** (`pull_request` rule active) |
| Require status checks to pass (`build`) | Not enforced (enforcement `off`, zero contexts) | **Enforced** (`required_status_checks`, context exactly `build`) |
| Require branches up to date before merging | Not enforced | **Enforced** (`strict_required_status_checks_policy: true`) |
| Block force pushes | Not enforced | **Enforced** (`non_fast_forward` rule) |
| Restrict deletions | Not enforced | **Enforced** (`deletion` rule) |
| Restrict who can bypass | Not enforced (zero rulesets) | **Enforced** (`current_user_can_bypass: "never"`, no bypass actors) |

**Classification: COMPLETED.** This was an operator/admin action; no
repository code change was possible or made. Full ruleset detail in
`docs/platform-closure-plan.md`'s Phase 1 completion record.

## Legacy renderer retirement

**Completed at VERSION 15.346** by explicit operator decision. The legacy
renderer, its selector, and its rollback path no longer exist;
`linkedGemaraLineIds` is the only association mechanism.
`docs/reports/legacy-renderer-retirement-policy.md` is retained as the
closed historical record.

## Next tractate

**DEFERRED-ROADMAP.** All non-Yoma tractates are product roadmap, not
incomplete Yoma work. Prerequisites and gate list:
`docs/reports/next-tractate-roadmap.md`. No module may be created without
explicit operator selection.

## Cross-references

Current-status documents that point here: `README.md`, `CLAUDE.md`,
`modules/yoma/MODULE.md`, `docs/rashi-audit-backlog.md`,
`docs/reports/rashi-association-audit.md`, `docs/yoma-completion-report.md`,
`docs/yoma-perek-review.md`, `docs/worker-pipeline.md`.
