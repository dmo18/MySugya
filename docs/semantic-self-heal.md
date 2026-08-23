# MySugya semantic self-heal protocol

## Purpose

This protocol closes the gap that allowed structurally valid but semantically wrong enrichment to be marked reviewed and frozen.

The governing rule is simple:

> Passing validators is not evidence that an explanation is true. Semantic correctness exists only when a source-first review record is bound by hash to the exact source and exact semantic payload it reviewed.

Legacy `review: "reviewed"` values are historical metadata only. They never confer semantic certification.

## Why this is required

The repository already has strong gates for source provenance, schema shape, Rashi structure and placement, generated-file freshness, PR scope, worker manifests, allowlist monotonicity, browser rendering, and deployment. Those controls remain mandatory.

They cannot by themselves prove that an English explanation, argument step, summary, quiz answer, misconception correction, speaker attribution, quantity, or ruling actually matches its Gemara range. A coherent family of fields can repeat the same wrong interpretation and therefore pass internal-consistency checks together.

The semantic certification layer prevents that failure from being confused with a green engineering build.

## Certification states

State is derived from live data, not trusted from a stored label.

- `UNCERTIFIED`: no certification record exists. This is the default.
- `REPAIR_REQUIRED`: a source-first first pass found one or more semantic defects.
- `REPAIRED_PENDING_REVIEW`: the current content awaits an independent source-first second pass. This state is also used after a clean first pass because one reviewer alone cannot certify.
- `PENDING_FINAL_AUDIT`: both source-first passes are present, have different review ids and reviewer contexts, and the second pass says `CONFIRMED` against the exact current candidate. The candidate is now finalized but has not yet received the mandatory schema-2.0 final whole-record audit (see below). It is not certified.
- `CERTIFIED`: both source-first passes, a passing final whole-record audit fingerprint-bound to the exact final candidate, and every fingerprint match the live corpus.
- `STALE`: a record says certified but the source or semantic payload (or the final audit's own bound fingerprints) changed after certification.
- `REVALIDATION_REQUIRED`: a record was certified under the retired schema 1.0, which lacked the mandatory final whole-record audit. It never reads as CERTIFIED regardless of fingerprint freshness. See "Schema 2.0" below.
- `BLOCKED`: the source or correct interpretation cannot be resolved responsibly.
- `INVALID`: malformed certification metadata.

A record missing from the registry is never inferred clean from old review docs, commit messages, passing gates, neighboring fields, or historical frozen status.

## Schema 2.0: mandatory final whole-record audit

An independent audit demonstrated that schema 1.0's contract -- two source-first
passes plus a free-text "every field was checked" declaration -- was
insufficient. On Yoma 7a/7b, the raw daf ends mid-thought, but fields other
than the one a repair touched (quiz, finalRuling, secondary prose) still
asserted the conclusion the Gemara only reaches on the following daf. Schema
1.0's registry certified both records anyway.

Schema 2.0 requires every CERTIFIED record to carry a `finalAudit` block,
produced strictly AFTER the first and second source-first passes (see the
`PENDING_FINAL_AUDIT` state above), fingerprint-bound to the exact final
`sourceFingerprint`/`semanticFingerprint` being certified. It has three parts:

### Machine-generated field inventory

`scripts/semantic_certification.py`'s `enumerate_semantic_paths(sugya)`
mechanically enumerates every semantically authored field/leaf actually
present in the finished record: the shared daf summary, `lineRange` and line
ownership, every populated `display.*` and `learning.*` field, every
`argumentFlow` step's label/speaker/text/sourceRefs, `quizSeeds`
questions/answers, `misconceptions`, `finalRuling`, `alternateAngles`,
`prerequisiteKnowledge`, `requiresUnderstanding`, `relatedSugyot`,
`visualizableElements` prose, `topicTags`, and `conceptRefs` where present.
This list is produced by code from the live payload, not written by a
reviewer -- the validator fails if any expected path is missing or if the
audit contains duplicate/ambiguous entries for the same path.

Each `fieldInventory` entry carries:

- `path`: the enumerated field path
- `verdict`: `SUPPORTED` / `REPAIR_REQUIRED` / `BLOCKED` / `NONFACTUAL`
- `supportingLines`: for `SUPPORTED`, a nonempty list of `{daf, startVilnaLine, endVilnaLine}` the claim rests on
- `boundarySafe`: true/false, mechanically re-derived and cross-checked -- a reviewer cannot declare it true while the supporting lines actually fall outside the authorized range
- `crossReference`: true only when the field is explicitly a pointer to another daf/sugya rather than a claim about the current one (e.g. "continues on 8a")
- `note`: optional

Supporting lines for an ordinary sugya field must fall inside that sugya's
own authorized `lineRange` on the current daf. The shared `dafSummary` path
may cite any line on the current daf (a page-level claim is not scoped to
one sugya's range). A claim may never use a *different* daf as source
support unless `crossReference` is explicitly true -- this is the mechanical
form of "it is true on 8a does not justify stating it as established on
7b." Any `REPAIR_REQUIRED`/`BLOCKED` verdict in the inventory means the
record is not ready to certify at all.

### Absolute physical daf-boundary contract

`finalAudit.dafBoundary` records `rawLineCount` and `finalRawLine`, both
mechanically checked against the live `talmuddev` raw source for that daf --
a reviewer cannot merely assert a daf ends mid-thought without the exact
final line matching reality. `dafEndState` is one of `COMPLETE`,
`MID_WORD`, `MID_SENTENCE`, `MID_QUESTION`, `MID_PROOF`, `MID_ARGUMENT`,
`OTHER_OPEN_CONTINUATION`.

Whenever `dafEndState` is not `COMPLETE`, the audit must also include an
`openEndingFieldSweep` covering every expected field path with an explicit
`importsNextDafConclusion: true/false`. Any `true` blocks certification --
the field must be repaired (made explicitly unresolved, or point forward
without asserting the result) before a fresh audit can pass.

### Mandatory post-repair stale-content sweep

`finalAudit.staleContentSweep.entries` is a fixed, mechanically-enumerated
checklist (`STALE_SWEEP_CATEGORIES` in `semantic_certification.py`) covering
stale original errors, stale/contradictory speaker attribution, old
conclusions left in secondary fields, false closure, next-daf content leaked
backward, claims unsupported by the physical daf, and stale
quiz/finalRuling/summary/learning/misconception/relatedSugya/visualizable
prose, plus stale `sourceRefs` and out-of-range references. Every category
must be present with an explicit `found: true/false`; any `found: true`
blocks certification until repaired and re-audited.

### Real review independence

A different `reviewId` string inside the same reasoning context is not
independence. Every review block (`firstPass`, `secondPass`) now requires a
`reviewerContextId`, and `finalAudit` requires an `auditorContextId` -- each
naming a genuinely distinct reviewer/session/context, never a fabricated
string. The validator requires `firstPass.reviewerContextId` to differ from
`secondPass.reviewerContextId`, and `finalAudit.auditorContextId` to differ
from `firstPass.reviewerContextId`. In this environment, a genuinely fresh
isolated context means a separate subagent invocation (e.g. via the Agent
tool) that has not seen the first-pass reasoning -- not a second persona
inside the same conversation. If a genuinely fresh, isolated review context
is unavailable, do not record a pass; leave the record where it is and say
so.

### Recording a final audit

```bash
python3 scripts/semantic_review_state.py first --module yoma \
  --sugya yoma-024a-s01 --review-id session-A --reviewer-context-id agent-A \
  --verdict VERIFIED --evidence-file /tmp/024a-first.json
python3 scripts/semantic_review_state.py second --module yoma \
  --sugya yoma-024a-s01 --review-id session-B --reviewer-context-id agent-B \
  --verdict CONFIRMED --evidence-file /tmp/024a-second.json
python3 scripts/semantic_review_state.py final-audit --module yoma \
  --sugya yoma-024a-s01 --review-id session-C --auditor-context-id agent-C \
  --audit-file /tmp/024a-final-audit.json --commit-ref HEAD
```

The `--audit-file` JSON must contain `dafBoundary`, `fieldInventory`, and
`staleContentSweep` (and `openEndingFieldSweep` when the daf ending is not
`COMPLETE`). `final-audit` validates the payload with the same
`validate_final_audit` function the CI ratchet uses, so a broken audit is
rejected before it is ever written to the registry.

### Migration: schema 1.0 is not grandfathered

Every record certified under schema 1.0 (Yoma 2a-10a as of this hardening)
was relabeled `REVALIDATION_REQUIRED` by the one-time
`scripts/migrate_certification_schema_v2.py` migration. Historical
`firstPass`/`secondPass` evidence and fingerprints are preserved for
reference, but the record never reads as CERTIFIED again until it receives
a real schema-2.0 final audit and genuinely independent review. See
`docs/claude-semantic-campaign-runbook.md` for the retroactive revalidation
sequence.

## The two fingerprints

Each certificate binds two independent hashes.

### `sourceFingerprint`

Includes module, daf, sugya id, declared Vilna line range, line and Sefaria mapping, Sefaria refs, and the exact raw Hebrew lines from the authoritative talmuddev cache in that range.

If source text, boundaries, or mappings change, the certificate is stale.

### `semanticFingerprint`

Includes all authored learner-facing sugya content except source coordinates and review metadata, plus the daf-level summary. This includes display and learning fields, argumentFlow, quizzes, misconceptions, topic tags, prerequisites, visualizable elements, final ruling, difficulty, glossary, related sugyot, and other authored semantic fields.

If any meaningful semantic field changes, the certificate is stale automatically. The daf summary is included in every sugya certificate on that daf so a page-level claim cannot change under still-green child records.

Rashi remains governed by its dedicated full-corpus translation and association system. A final module freeze requires both strict sugya certification and all Rashi gates and review campaigns complete.

## Whole-daf review is the default campaign unit

The self-heal campaign works daf by daf, not symptom by symptom and not field family by field family.

That is deliberate. A late correction to a daf summary or a sugya boundary can affect several records at once. Reviewing the whole daf before certifying any of its sugyot prevents an early certificate from being invalidated merely because the reviewer discovered the real page structure later in the same daf.

Generate the first-pass packet with:

```bash
python3 scripts/semantic_daf_packet.py --module yoma --daf 24a
```

The packet presents the complete authoritative Hebrew page first. The reviewer must independently map topic transitions and sugya boundaries before reading the current enrichment. Then the reviewer checks the daf summary and every semantic field of every sugya on the page.

The per-sugya state commands in `semantic_self_heal.py` remain useful for status and diagnostics, but they do not replace the whole-daf review packet.

## Independent review

Two semantic passes are mandatory.

### First pass

The reviewer reads the complete Hebrew daf first, reconstructs its flow and boundaries independently, consults relevant Rashi as commentary evidence, and only then compares all current enrichment.

Legal first-pass outcomes per sugya are `VERIFIED`, `REPAIR_REQUIRED`, or `BLOCKED`.

Agreement among existing enrichment fields is never evidence.

### Second pass

Generate a separate packet:

```bash
python3 scripts/semantic_daf_packet.py --module yoma --daf 24a --second-pass
```

The independent packet deliberately omits first-pass findings and reasoning. The second reviewer re-derives the page from the source and may return `CONFIRMED`, `REJECTED`, or `BLOCKED` for each candidate record.

The first and second passes must carry different `reviewId` values AND different `reviewerContextId` values -- a genuinely distinct reviewer/session/context, not just a different label. A worker cannot certify its own pass twice, and a different label inside the same reasoning context is not independence either.

## Live self-heal state

The certification registry is not a hand-maintained completion list. Effective state is recalculated from the live source and semantic fingerprints.

Useful commands:

```bash
python3 scripts/semantic_self_heal.py --module yoma status
python3 scripts/semantic_self_heal.py --module yoma next
python3 scripts/validate_semantic_certification.py --module yoma --report
```

The first unfinished record receives one of `AUDIT`, `REPAIR`, `INDEPENDENT_REVIEW`, `FINAL_AUDIT`, or `BLOCKED`. In execution, Claude groups the next records by daf and reviews that whole daf before certifying it.

A real ambiguity is a stop condition, not permission to guess.

## Recording review state

The reviewer does not hand-edit fingerprint values. Use `semantic_review_state.py` to record completed review decisions and stamp fingerprints only after an independent confirmation.

Examples:

```bash
python3 scripts/semantic_review_state.py first --module yoma --sugya yoma-024a-s01 --review-id session-A --reviewer-context-id agent-A --verdict REPAIR_REQUIRED --evidence-file /tmp/024a-first.json
python3 scripts/semantic_review_state.py repaired --module yoma --sugya yoma-024a-s01 --repair-ref HEAD
python3 scripts/semantic_review_state.py second --module yoma --sugya yoma-024a-s01 --review-id session-B --reviewer-context-id agent-B --verdict CONFIRMED --evidence-file /tmp/024a-second.json
python3 scripts/semantic_review_state.py final-audit --module yoma --sugya yoma-024a-s01 --review-id session-C --auditor-context-id agent-C --audit-file /tmp/024a-final-audit.json --commit-ref HEAD
```

A clean first pass still requires the independent second pass, AND the mandatory final whole-record audit ("Schema 2.0" above), before the record can become `CERTIFIED`. A CONFIRMED second pass alone only reaches `PENDING_FINAL_AUDIT`.

## Holistic repair rule

A semantic repair is holistic at the daf and affected-sugya level. The first pass must list all problems it found before editing. The repair then fixes the entire contaminated record in one pass rather than opening separate display, learning, quiz, and argumentFlow loops.

For a target sugya the repair may need to change display, learning, argumentFlow, quizSeeds, misconceptions, tags, prerequisites, source refs, finalRuling, or source coordinates. Raw Hebrew and Rashi source content are never changed merely to make enrichment fit.

Create the semantic PR manifest with:

```bash
python3 scripts/make_semantic_repair_manifest.py --module yoma --daf 24a --type semantic-daf-repair --review-id session-A --all-sugyot
```

Use `--all-sugyot` whenever the daf summary or source boundaries change. The holistic scope gate protects all sibling sugyot and forbids raw-source or Rashi changes.

After a repair:

1. regenerate deterministic output
2. run every existing source, schema, Rashi, generated-file, build, and browser gate
3. run the independent whole-daf second semantic pass
4. record the confirmed states and fresh fingerprints
5. run the semantic certification ratchet
6. merge only after CI is green
7. re-read live state and advance to the next daf

The queue is derived again after every merge. Claude never relies on a stale handwritten to-do list.

## CI enforcement

Every pull request runs the semantic certification ratchet.

During bootstrap, existing untouched uncertified debt may remain. However:

- any changed source or semantic payload must leave the PR freshly `CERTIFIED`
- a previously certified record may never silently regress
- semantic repair PRs are limited to one daf and explicit target sugyot
- raw source and Rashi source files remain protected
- normal non-semantic PRs still use the existing worker pipeline scope gate

A `.semantic-repair-manifest.json` change routes the PR through the dedicated holistic semantic scope checker. The semantic certification ratchet still runs afterward and is the final truth-state gate.

## Bootstrap and permanent strict mode

The current Yoma enrichment corpus predates this certification system. It is therefore bootstrapped as uncertified rather than grandfathered.

The initial registry records independently reproduced defects, but it does not assume that unlisted records are clean. Claude must work through all 173 daf and all 492 sugyot source-first.

When all 492 sugyot pass:

```bash
python3 scripts/validate_semantic_certification.py --module yoma --strict
```

then, and only then, set `strictMode` to `true`. From that point any missing, stale, blocked, or uncertified sugya fails CI and deployment.

## Required final freeze definition

A module may be called semantically frozen only when all of the following are true at the same commit:

1. strict semantic certification is 100 percent
2. every certificate fingerprint matches live source and semantic content
3. every daf summary and every sugya boundary was covered by the source-first daf campaign
4. all source provenance and schema gates pass
5. all Rashi translation, association, boundary, structural, and rendering gates pass
6. generated data is fresh
7. browser tests pass
8. no semantic blocker exists
9. CI is green on the exact commit being deployed

No report, historical completion claim, old `reviewed` flag, or green non-semantic validator can substitute for those conditions.
