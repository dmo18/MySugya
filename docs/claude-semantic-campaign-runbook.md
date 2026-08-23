# Claude semantic repair campaign runbook

This is the autonomous execution contract for repairing and certifying the MySugya learning corpus. Read `docs/semantic-self-heal.md` first. Do not rely on prior completion reports, legacy `reviewed` fields, or previous conversational context as evidence of semantic correctness.

## Mission

Process Yoma from 2a through 88a until every one of the 492 sugyot is freshly source-first `CERTIFIED` at the same commit, all existing gates are green, and the semantic registry has `strictMode: true`.

Do not stop because a previous report says a daf was reviewed. Do not skip clean-looking records. Do not fix only a known issue list. Every daf must receive its own source-first review.

## Absolute rules

1. The primary Hebrew source is the authority for semantic claims. Existing enrichment is the object being tested, not evidence for itself.
2. Review a whole daf before certifying any sugya on it. Establish page flow and boundaries first.
3. Inspect every semantic field of every sugya on that daf, including the daf summary, display, learning, argumentFlow, quizSeeds, misconceptions, topic tags, prerequisites, related sugyot, visualizableElements, finalRuling, difficulty, glossary, and source-coordinate fields.
4. A true statement placed on the wrong daf or wrong source range is a defect.
5. Do not infer correctness from agreement among summary, argumentFlow, quiz, Rashi helper text, or other generated fields. Independently reconstruct the source first.
6. Relevant Rashi may clarify the Gemara, but never replace reading the Gemara source.
7. Do not change raw Hebrew, talmuddev source, literal source, or Rashi source merely to make enrichment fit. A real source defect is a separate blocked escalation.
8. Repair the entire contaminated daf/record in one pass. Do not create a sequence of display-only, learning-only, quiz-only, and argumentFlow-only fixes for the same semantic defect.
9. Every completed first pass needs a second source-first review with a different review id. The second reviewer must not be shown first-pass reasoning.
10. If meaning or source ownership remains genuinely ambiguous, mark `BLOCKED` and stop. Never guess to make the queue advance.
11. Never weaken, delete, bypass, or widen a validator to make a content repair pass.
12. After every merge, re-read live state. Never trust a stale local queue or handwritten checklist.

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

Use a fresh reviewer/session id. Do not read the first-pass evidence before deriving your verdict.

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
  --verdict CONFIRMED \
  --evidence-file <second-pass-evidence.json> \
  --commit-ref HEAD
```

## Mandatory gates before PR completion

Run all normal repository validation plus the new semantic checks. At minimum:

```bash
npm run validate:offline:yoma
python3 scripts/test_semantic_certification.py
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
