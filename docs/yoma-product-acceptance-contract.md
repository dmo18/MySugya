# Yoma product acceptance contract (v2)

**Status: contract definition only.** This document and its machine-readable
companion, `docs/reports/data/yoma-product-acceptance-contract.json`, define
what "Yoma is fully usable and accurate" means in checkable terms. Neither
this unit nor the JSON file certifies that Yoma currently meets the
contract. Every requirement starts `UNVERIFIED` and stays that way until a
later unit runs its acceptance command(s) or produces conforming
review-record(s) and records the evidence.

This document does not supersede `docs/platform-closure-plan.md` or
`docs/reports/open-items.md`. Those remain the day-to-day inventory and
phased platform plan. This contract is a separate, narrower artifact: a
fixed list of product-level requirements with a deterministic validator,
so "is Yoma done" has one answer that does not depend on reading narrative
prose.

## Operator-approved product boundary

Yoma must be fully usable and accurate, including:

- all existing Gemara/source layers and translations, with translation
  **accuracy and source alignment** verified separately from mere
  structural/literal-layer presence
- Rashi text, translation accuracy/alignment (separate from generic Rashi
  content-quality checks), and associations
- learning enrichments (ideas, quizzes, arguments, explanations, takeaways)
- navigation, rendering, and search — search is an existing feature (the
  "Jump to daf" modal) and is mandatory where present, not optional
- a reproducible build
- exact production release verification

This unit does not edit Yoma content. Preserving all data is a hard
constraint (`YOMA-NO-ENRICHMENT-DATA-DELETION`): no requirement in this
contract may be satisfied by deleting enrichment data.

## Requirement record shape

Each entry in the JSON requirements array has:

| Field | Meaning |
|---|---|
| `id` | Stable identifier. Never reused for a different requirement. |
| `category` | One of `corpus`, `source-layer`, `translation`, `rashi`, `enrichment`, `navigation`, `build`, `release`, `policy`. |
| `mandatory` | `true` unless the requirement is explicitly optional for v1. |
| `verificationMode` | `deterministic`, `semantic`, `both`, or `external`. Determines which evidence component types are *required* (see below). |
| `scopeStatement` | Prose describing the requirement's scope. For `translation`, `rashi`, and `enrichment` categories, must state exhaustive corpus coverage (containing both "all" and "sugyot"), not a sample. |
| `independentReviewRequired` | When `true`, every `semantic`/`external` evidence component must include `independentReviewer` in `reviewRecordRequiredFields`, so the reviewer cannot be the same reasoning context that implemented the change. |
| `evidenceComponents` | Array of typed evidence components (see below). This is where acceptance commands and review-record schemas actually live; there is no flat top-level `sourceClass`/`acceptanceCommand` anymore. |
| `status` | One of `UNVERIFIED`, `PASS`, `FAIL`, `BLOCKED`, `NOT_APPLICABLE`. Top-level `status` may only be `PASS` if every evidence component required by `verificationMode` is itself `PASS`. |
| `repairVsReconstruction` | `undecided` (default), `repair`, or `reconstruct` — see policy below. |
| `repairDecision` | `null` while `undecided`. Required object (`decidedAt`, `decisionEvidence`, `contentScopeFingerprint`, `reopenHistory`) once a `repair`/`reconstruct` decision is made. |
| `evidenceRefs` | Top-level evidence refs supporting the requirement as a whole. Empty while `UNVERIFIED`. |

## Evidence components

`verificationMode` determines which component types are *required*:

| Mode | Required component types |
|---|---|
| `deterministic` | `deterministic` |
| `semantic` | `semantic` |
| `both` | `deterministic` **and** `semantic` |
| `external` | `external` |

Each component is its own object with its own `sourceClass`,
`acceptanceCommand`, `exactCommitBinding`, `status`, and `evidenceRefs` — not
a single shared command for the whole requirement. This means a `both`-mode
requirement cannot be satisfied by one script's exit code alone; it needs
independently recorded deterministic *and* semantic evidence.

- **deterministic** component: the `acceptanceCommand`'s exit code is the
  evidence. `PASS` requires exit code 0 recorded at the bound commit.
  A `ci-workflow` component's `acceptanceCommand` must never be a mutating
  dispatch (e.g. `gh workflow run ...`) — the validator fails closed on the
  literal substring `"gh workflow run"` in any `ci-workflow` component. Use a
  read-only evidence command instead (e.g. `gh run view` of an already
  completed run).
- **semantic** component: a review record naming a reviewer, a timestamp, a
  disposition, evidence references, scope coverage, whether the review was
  source-first, and whether enrichment fields were preserved
  (`reviewRecordRequiredFields`). When `independentReviewRequired` is true,
  the record must also name an `independentReviewer`. The validator checks
  the record's *shape*, never the judgment inside it.
- **external** component: evidence from a source outside this repository
  (a live production check, an external text edition, etc.). In addition to
  the base review-record fields, it must record `edition`, `license`, and
  `sourceProvenance` so it can be re-checked later.

A requirement's top-level `status` can only be `PASS` if every evidence
component required by its `verificationMode` independently reports `PASS` —
this catches the case where, say, a deterministic gate is green but the
semantic review was never actually done (or vice versa).

## Repair-vs-reconstruction policy

Each requirement's `repairVsReconstruction` decision starts `undecided` and
stays that way (`repairDecision: null`) until evidence-based triage actually
happens. It is never set to `repair` or `reconstruct` prematurely just
because the requirement exists. The decision is scoped to a specific content
scope / work unit (see `contentScopeFingerprint`), not blindly applied
product-wide, since "repair" may be correct for one sugya and wrong for
another.

Once a decision is made, it is durable and is recorded as a `repairDecision`
object:

| Field | Meaning |
|---|---|
| `decidedAt` | Timestamp of the decision. |
| `decisionEvidence` | What evidence justified choosing repair vs. reconstruct. |
| `contentScopeFingerprint` | Exact content/scope the decision applies to (not necessarily the whole requirement). |
| `reopenHistory` | Durable list of any later reopenings and why. |

Reopening a settled decision requires one of:

- a newly failing test that did not fail before,
- new authoritative evidence that was not available when the decision was
  made,
- a changed source (e.g., an external edition was revised), or
- a specific, named current defect (not a general "let's double-check").

A vague "let's redo this to be safe" is never sufficient grounds to reopen
a requirement that already carries a `PASS` or a settled `repairDecision`.

## No invented evidence

Existing completion claims in `docs/reports/open-items.md` and
`docs/platform-closure-plan.md` are **not** automatically imported as `PASS`
into this contract. This contract's validator only ever treats a requirement
as evidenced when every evidence component required by its mode carries its
own `evidenceRefs` and `exactCommitBinding`. Until that happens, every
requirement here reports `UNVERIFIED`, even where strong prior evidence
exists elsewhere in the repository.

## Validator

`scripts/validate_product_contract.py` is the deterministic gate over the
JSON file itself (not over Yoma's data). It fails closed on:

- malformed JSON or a missing required field (including `scopeStatement`,
  `independentReviewRequired`, `evidenceComponents`, `repairDecision`) on any
  requirement,
- a duplicate requirement `id`, or any `id` unknown to the registry baked
  into the validator (so an entry cannot be silently added or removed from
  the JSON without the validator's own registry changing in the same diff),
  checked bidirectionally (registry ↔ file, both directions),
- an `id` referencing a `verificationMode`, `category`, `sourceClass`, or
  `status` value outside the declared enums,
- a `translation`/`rashi`/`enrichment`-category requirement whose
  `scopeStatement` does not express exhaustive corpus scope,
- a `repairVsReconstruction` of `repair`/`reconstruct` with no (or an
  incomplete) `repairDecision` object, or an `undecided` requirement whose
  `repairDecision` is not `null`,
- a requirement missing a required component type for its `verificationMode`
  (e.g. a `both`-mode requirement with only a `semantic` component), or a
  duplicate component type,
- any evidence component whose `status` is `PASS`/`FAIL` but has no
  `evidenceRefs` or no `exactCommitBinding` (evidence-free status claims),
- a `ci-workflow` component whose `acceptanceCommand` contains the literal
  substring `"gh workflow run"` (mutating dispatch masquerading as
  validation),
- a `semantic`/`external` component with incomplete
  `reviewRecordRequiredFields`, or missing `independentReviewer` when
  `independentReviewRequired` is `true`,
- a requirement whose top-level `status` is `PASS` while any of its required
  evidence components is not itself `PASS` (contradictory evidence).

Run it with:

```bash
python3 scripts/validate_product_contract.py
```

It exits non-zero on any violation and prints a per-requirement summary
table including the honest current `status` of every requirement. It never
upgrades a status itself; it only validates that the recorded status is
internally consistent with its own evidence fields.
