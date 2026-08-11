# Yoma tail-enrichment repair plan

Companion to `docs/reports/data/yoma-tail-enrichment-repair-queue.json`.

The merged audit (`docs/reports/yoma-tail-enrichment-audit.md`) is historical evidence and is never rewritten. This plan and the queue carry the actionable state.

- Audit source SHA: `3aa90cde8c50f8489e2e7ca6f4bbe7ffe034f9d5`
- Queued records: **82** (every audit record whose overall disposition is not VERIFIED, exactly once)
- Contract authority: `docs/reports/yoma-enrichment-contract-decision.md`
- Gate: `scripts/validate_enrichment_contracts.py` (baseline-and-ratchet, `--targets` for target-clean)

## Queue totals

| Dimension | Counts |
|---|---|
| Semantic disposition | MINOR_EDIT_NEEDED 9, SUBSTANTIVE_REPAIR_NEEDED 24, VERIFIED 49 |
| Mechanical disposition | MINOR_EDIT_NEEDED 53, STRUCTURAL_OR_SCHEMA_DECISION 29 |
| Removed `concepts` scheduled for purge | 33 |
| Carrying migration prerequisites | 33 |

## Supersession recorded here, not in the audit

The 29 records whose `finalRuling` exactly copies `display.hint` carry `STRUCTURAL_OR_SCHEMA_DECISION` in the merged audit because the contract was open when it was written. The `finalRuling` contract decision closes that question: a non-empty `finalRuling` equal to `display.hint` is invalid. Those records are now ordinary repairable defects. Their historical audit dispositions are left untouched by design.

## Execution order

1. prerequisite contract/tooling and migrations (not queue rows)
2. yoma-082b-s01
3. yoma-087b-s03
4. yoma-080a-s01
5. yoma-080b-s03
6. remaining substantive records in daf order
7. minor semantic records
8. parent daf summaries after all sugyot on each daf are settled
9. finalRuling-only mechanical repairs after each underlying hint is confirmed

Steps 1 is tooling and migration work and does not appear as queue rows. Steps 2 onward map to `queuePosition` in the queue file.

## Prerequisites before any semantic repair

1. **`legacy-concepts-purge`** - corpus-wide deletion of `sugyot[*].concepts` (492 sugyot).
2. **`enrichment-schema-migration`** - `requiresUnderstanding` prose to `prerequisiteKnowledge` (404 sugyot), `visualizableElements` shape normalization (432 sugyot missing `item`), `difficulty` `introductory` to `intro` (112 sugyot).

Both are mechanical. Until they land, no sugya can pass `--targets` target-clean, because every sugya still carries the removed `concepts` field. That ordering is enforced by the gate rather than by convention.

## First four repairs

| # | Sugya | Daf | Why first |
|---|---|---|---|
| 1 | `yoma-082b-s01` | 82b | Fabricated framing: display/learning describe an invented pikuach-nefesh question; the source is the martyrdom sevara. |
| 2 | `yoma-087b-s03` | 87b | Fabricated framing: display describes a Hadran/Tu BeAv closing absent from the source; the sugya is neila. |
| 3 | `yoma-080a-s01` | 80a | Ruling contradicts the source and the sugya own argumentFlow: source says olive-bulk, display says egg-bulk. |
| 4 | `yoma-080b-s03` | 80b | Ruling inverted: source says excessive eating is exempt, display says it creates liability. |

## Per-daf workload (one daf per repair PR)

| Daf | Queued sugyot |
|---|---|
| 77a | 4 |
| 77b | 4 |
| 78a | 5 |
| 78b | 4 |
| 79a | 1 |
| 79b | 1 |
| 80a | 3 |
| 80b | 3 |
| 81a | 4 |
| 81b | 2 |
| 82a | 4 |
| 82b | 2 |
| 83a | 5 |
| 83b | 4 |
| 84a | 3 |
| 84b | 4 |
| 85a | 6 |
| 85b | 4 |
| 86a | 4 |
| 86b | 5 |
| 87a | 5 |
| 87b | 3 |
| 88a | 2 |

## Required task types

- `audited-sugya-enrichment-repair` for every queue row: semantic, max one daf per PR, independent review required, manifest must name the audit record ids, and every changed path must appear in those records' `affectedFields`.
- `legacy-concepts-purge` and `enrichment-schema-migration` for the prerequisites above.

## Status

Every record is `NOT_STARTED`. No repair has begun.
