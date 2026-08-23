# Claude semantic repair campaign runbook

This is the autonomous execution contract for repairing and certifying the MySugya learning corpus. Read `docs/semantic-self-heal.md` first, including the "Schema 2.0: mandatory final whole-record audit" section. Do not rely on prior completion reports, legacy `reviewed` fields, or previous conversational context as evidence of semantic correctness.

## Mission

Process Yoma from 2a through 88a until every one of the 492 sugyot is freshly source-first `CERTIFIED` under certification schema 2.0 at the same commit, all existing gates are green, and the semantic registry has `strictMode: true`.

Do not stop because a previous report says a daf was reviewed. Do not skip clean-looking records. Do not fix only a known issue list. Every daf must receive its own source-first review.

## Certification schema 2.0 and the legacy range (2a-10a)

An independent audit demonstrated that certification schema 1.0 -- two
source-first passes plus a free-text "every field was checked" declaration
-- was insufficient: Yoma 7a/7b were `CERTIFIED` under schema 1.0 while
fields other than the one a repair touched still asserted a conclusion the
daf does not reach until the following page. Schema 2.0 closes that gap with
a mandatory, fingerprint-bound, machine-enumerated final whole-record audit
(see `docs/semantic-self-heal.md`).

Every record certified under schema 1.0 (2a through 10a as of this
hardening) was migrated to `REVALIDATION_REQUIRED` by the one-time
`scripts/migrate_certification_schema_v2.py` script and never reads as
`CERTIFIED` again, regardless of fingerprint freshness, until it receives a
real schema-2.0 final audit and genuinely independent review. This is not a
blind restart: preserve the current candidate unless the raw source proves a
defect, but every one of those records must go through the same source-first
whole-record audit, physical-boundary check, and machine-enumerated field
inventory as new work before it may certify again.

**Do not resume forward campaign work past 10a until the entire 2a-10a range
has a fresh schema-2.0 certificate.** Work through it in daf order, exactly
as for new daf, using `python3 scripts/semantic_self_heal.py --module yoma
status` to find the next `REVALIDATION_REQUIRED` (or otherwise non-CERTIFIED)
record.

## Absolute rules

1. The primary Hebrew source is the authority for semantic claims. Existing enrichment is the object being tested, not evidence for itself.
2. Review a whole daf before certifying any sugya on it. Establish page flow and boundaries first.
3. Inspect every semantic field of every sugya on that daf, including the daf summary, display, learning, argumentFlow, quizSeeds, misconceptions, topic tags, prerequisites, related sugyot, visualizableElements, finalRuling, difficulty, glossary, and source-coordinate fields.
4. A true statement placed on the wrong daf or wrong source range is a defect.
5. Do not infer correctness from agreement among summary, argumentFlow, quiz, Rashi helper text, or other generated fields. Independently reconstruct the source first.
6. Relevant Rashi may clarify the Gemara, but never replace reading the Gemara source.
7. Do not change raw Hebrew, talmuddev source, literal source, or Rashi source merely to make enrichment fit. A real source defect is a separate blocked escalation.
8. Repair the entire contaminated daf/record in one pass. Do not create a sequence of display-only, learning-only, quiz-only, and argumentFlow-only fixes for the same semantic defect.
9. Every completed first pass needs a second source-first review with a different review id AND a genuinely different, isolated reviewer context. The second reviewer must not be shown first-pass reasoning.
10. If meaning or source ownership remains genuinely ambiguous, mark `BLOCKED` and stop. Never guess to make the queue advance.
11. Never weaken, delete, bypass, or widen a validator to make a content repair pass.
12. After every merge, re-read live state. Never trust a stale local queue or handwritten checklist.
13. Treat the physical end of a daf as absolute. If the daf ends before a conclusion is stated, the semantic treatment of that discussion on the current daf must remain unresolved -- it is permissible to say the discussion continues on the next daf, never to state the next daf's conclusion as though this daf reached it. This applies to every field, not only the one a repair happens to touch.
14. A record certified under schema 1.0 (`REVALIDATION_REQUIRED`) is not certified. Do not treat it, or any prior completion report about it, as evidence; it requires the same source-first whole-record audit as new work.

## Start

Run:

```bash
python3 scripts/validate_semantic_certification.py --module yoma --report
python3 scripts/semantic_self_heal.py --module yoma status
```

Find the earliest daf containing any non-`CERTIFIED` sugya. That entire daf is the next campaign unit.

## First-pass daf review

Generate the packet:

```bash
python3 scripts/semantic_daf_packet.py --module yoma --daf <daf> > /tmp/<daf>-first-packet.json
```

Read `authoritativeHebrewLines` from beginning to end before reading `currentDafSummary` or `currentEnrichment`.

Write a first-pass evidence file that contains:

- your review id
- daf
- independent source-flow reconstruction
- boundary verdict for every sugya
- daf-summary verdict
- one verdict for every sugya
- for each defect: exact affected fields, source lines, what the current claim says, what the source actually supports, and the required correction
- an explicit statement that every semantic field on the daf was checked, including fields that did not look suspicious

If the entire daf is correct, record `VERIFIED` first-pass state for each sugya and proceed directly to independent review. A first-pass `VERIFIED` is not certification.

If any defect exists, record the relevant first-pass states with `semantic_review_state.py` and repair the daf before second review.

## Repair

Generate the repair manifest. If the daf summary, boundaries, line maps, or Sefaria ownership needs correction, use every sugya on the daf as a target:

```bash
python3 scripts/make_semantic_repair_manifest.py \
  --module yoma \
  --daf <daf> \
  --type semantic-daf-repair \
  --review-id <first-review-id> \
  --all-sugyot
```

For an isolated semantic defect that does not change a shared summary or source ownership, explicit `--sugya` targets are allowed, but whole-daf review is still mandatory.

Make one coherent source-driven correction. Before committing, check that no unlisted sibling changed and that `rashiTranslations` is byte-identical.

Regenerate module output using the repository's normal generator. Do not hand-edit generated `learning_data.js` as authored truth.

Mark repaired records:

```bash
python3 scripts/semantic_review_state.py repaired --module yoma --sugya <id> --repair-ref HEAD
```

Do this for each repaired target.

## Independent second pass

Use a fresh reviewer/session id AND a genuinely fresh, isolated reviewer context -- in this environment, a separate subagent invocation (for example via the Agent tool) that has not seen the first-pass reasoning, not a second persona inside the same conversation. A different `reviewId` string inside the same reasoning context is not independence and must not be recorded as if it were. If a genuinely fresh isolated context is unavailable, do not record a second pass; leave the record where it is and say so rather than guessing at independence.

Do not read the first-pass evidence before deriving your verdict.

Generate:

```bash
python3 scripts/semantic_daf_packet.py --module yoma --daf <daf> --second-pass > /tmp/<daf>-second-packet.json
```

Re-read the complete Hebrew daf and independently reconstruct boundaries and meaning. Then inspect the candidate enrichment.

For each sugya:

- `CONFIRMED`: current candidate fully matches the source and its placement
- `REJECTED`: any semantic, boundary, attribution, quantity, logic, sequence, or placement defect remains
- `BLOCKED`: correctness cannot responsibly be determined from available evidence

A `REJECTED` result returns the affected record to repair. Do not patch only the reviewer comment. Repair the full affected record, regenerate, and run a new independent second pass.

For confirmed records, stamp live fingerprints only through:

```bash
python3 scripts/semantic_review_state.py second \
  --module yoma \
  --sugya <id> \
  --review-id <independent-review-id> \
  --reviewer-context-id <fresh-isolated-context-id> \
  --verdict CONFIRMED \
  --evidence-file <second-pass-evidence.json>
```

This reaches `PENDING_FINAL_AUDIT`, not `CERTIFIED`.

## Mandatory final whole-record audit

After the second pass CONFIRMS the candidate, perform the schema-2.0 final
whole-record audit against that exact finalized candidate (see
`docs/semantic-self-heal.md` for the full field-inventory, daf-boundary, and
stale-content-sweep contract). Build the audit JSON, then record it:

```bash
python3 scripts/semantic_review_state.py final-audit \
  --module yoma \
  --sugya <id> \
  --review-id <audit-review-id> \
  --auditor-context-id <fresh-isolated-context-id> \
  --audit-file <final-audit.json> \
  --commit-ref HEAD
```

`final-audit` validates the payload before writing it: a missing field path,
an out-of-range source-support claim, an unresolved stale-content finding,
or a reused reviewer context is rejected immediately rather than silently
recorded. This is the step that must not be skipped, abbreviated, or
special-cased -- it is what closes the exact gap the 7a/7b failure exposed.

## Mandatory gates before PR completion

Run all normal repository validation plus the new semantic checks. At minimum:

```bash
npm run validate:offline:yoma
python3 scripts/test_semantic_certification.py
python3 scripts/test_semantic_certification_v2.py
python3 scripts/validate_semantic_certification.py --module yoma --report
python3 scripts/semantic_repair_scope_v2.py --base <merge-base>
python3 scripts/validate_semantic_certification.py --module yoma --ratchet --base <merge-base>
npm run build
npm run check:deploy-html
npm test
npm run test:browser
npm run test:fixture-onboarding
npm run test:module-scaffold
```

Do not merge with a failing gate. Do not change a gate to make a repair mergeable.

## After merge

Re-run:

```bash
python3 scripts/semantic_self_heal.py --module yoma status
python3 scripts/validate_semantic_certification.py --module yoma --report
```

Advance to the earliest daf that still contains a non-certified record.

Do not use the previous PR's target list as the next queue. Live effective state is the queue.

## Final closure

After the last daf is complete, run:

```bash
python3 scripts/validate_semantic_certification.py --module yoma --strict
```

Then verify the existing Rashi full-corpus state and all normal validation/build/browser gates at that exact commit.

Only after strict semantic certification reports 492/492, no blockers remain, Rashi remains fully reviewed and structurally clean, generated data is fresh, and CI is green may `strictMode` be changed to `true` and Yoma be called semantically frozen.

If strict mode does not pass, the project is not complete. Continue from live state rather than writing a completion report.
