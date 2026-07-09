# Schema-wide worker pipeline coverage report (VERSION 15.82)

Read-only inventory plus mechanical coverage proof for every
schema-controlled path in Yoma learning JSON. Machine-readable inventory:
scripts/worker_schema_scope.json (85 classified paths). Consistency is
enforced by `npm run worker:schema-matrix`, which cross-checks the
inventory against the task-type registry's jsonScope contracts and fails
on unclassified, unowned-editable, or wrongly-reachable paths. It runs
inside `worker_pipeline.py ci-check` on every manifest-bearing PR.

## Classification summary

- immutable: 4 (daf, rashiTranslations vilnaLine/he, generated Gemara he/en)
- generated-only: 4 (enSource, source, confidence, en_lit layer)
- haiku-manifest: 7 (rashi en/links via rashi tasks; display whats/hint/
  title/oneLine/shortSummary via display-only-edit)
- fable-only: 67 (learning narrative, argumentFlow, sourceRefs, lineRange,
  ids, glossary, quizSeeds, misconceptions, concepts, review, summary,
  canonicalRef, visualizableElements, and all other structure)
- flag-only: 2 (takeaway.type, alternateAngles)
- deprecated: 1 (concepts[*].definition; use def)

Schema drift found and recorded: argumentFlow sourceRefs entries are
plain strings on some daf and {sourceType, lineId, vilnaLine} objects on
others. The engine treats both shapes as immutable outside
structural-repair; normalization is future structural-repair work.

## Task-type ownership (17 types)

Rashi en/links: rashi-repair (haiku), rashi-reconstruction and
placeholder-backfill (haiku with Fable review). Display copy:
display-only-edit (haiku, Fable review, maxBatch 2). Learning narrative +
reasoningPattern (+ takeaway.type, alternateAngles by flag):
learning-copy-edit (fable). Glossary/concepts text: glossary-edit
(fable). quizSeeds/misconceptions: quiz-edit (fable). summary:
summary-edit (fable). Structure (argumentFlow, lineRange, lines, ids,
sourceRefs, sourceLinks, visualizableElements, difficulty, finalRuling,
topicTags, relatedSugyot, conceptRefs, canonicalRef): structural-repair
(fable, requires --authorize allowStructure). review stamps:
metadata-review-status (fable). Plus literal-layer, generated-refresh,
audit-only, docs-tooling, deployment-verify, nekudot (PAUSED).

## Engine negative-test battery (all 15 PASS)

illegal takeaway.type / argumentFlow.id / sourceRefs / lineRange /
rashiTranslations-in-gemara-task / glossary-without-flag /
quizSeeds-without-flag / alternateAngles-in-display-only /
array-growth-without-allowStructure / cross-daf edit: all FAIL with
exact JSON pointers. glossary-with-flag / quizSeeds-with-flag /
alternateAngles-with-flag / array-growth-in-structural-repair /
legal-display-edit: all PASS.

## Dry runs (12/12 green: manifest + preflight + packet + prompt)

| Task type | Target | Haiku-safe | Escalation trigger highlights |
|---|---|---|---|
| rashi-repair | 61a | YES | uncertain Hebrew; unbaselined count mismatch |
| rashi-reconstruction | 47a | with Fable review | new semantic shift candidates |
| placeholder-backfill | 77a-77b | with Fable review | allowlist must shrink |
| display-only-edit | 20a | YES (Fable review) | uncertainty about sugya meaning |
| glossary-edit | 20a | NO (fable) | entry add/remove is structure |
| quiz-edit | 20a | NO (fable) | quality standards (real distinctions) |
| structural-repair | 20a | NO (fable+flag) | any structural ambiguity |
| literal-layer | 47a-48b | YES | coverage would drop below 95% |
| generated-refresh | - | YES | unexpected diff areas |
| audit-only | - | YES | report findings, never fix |
| docs-tooling | - | NO (fable) | gate weakening |
| deployment-verify | - | YES | red deploy or version mismatch |

## Haiku operating envelope

Haiku may: run generated manifests/prompts/packets for haiku-marked
types, execute edits inside jsonScope, run verify, open PRs, poll
CI/deploy after local verify --full passes, and merge ONLY
non-review-required task types. Haiku may never: add allowlist/baseline
entries, set RASHI_ALLOWLIST_RESTRUCTURE or allowStructure, edit the
registry/validators/workflows, override a red gate, or merge a
fableReviewRequired PR without review. Fable/Sonnet owns semantic
Hebrew, structure and schema changes, new task types, allowlist growth,
and ambiguous repairs.

## Roadmap after this PR

1. Haiku first: 61a rashi-repair (single-daf shakedown), then 67b, 68a,
   68b, 70a, 71b one PR each.
2. Fable: 41a shifted block (plus 42a L50 lead), then 8a/9a phantom
   counts via rashi-repair with --allow-structure.
3. Haiku with Fable review: 77a-88a placeholder-backfill, 1 daf per PR
   until two consecutive green passes, then maxBatch 2.
4. 47a+ rashi-reconstruction only after the defect backlog is drained.
5. Paused until explicitly unblocked: nekudot (needs validator design),
   gemara-learning content passes (need operator authorization),
   large-batch anything.
6. Do not enable worker auto-merge until GitHub branch protection
   (required build check, require-up-to-date, PR-required, no force
   push) is configured by an admin.
