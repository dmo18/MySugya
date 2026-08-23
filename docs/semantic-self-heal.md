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
- `CERTIFIED`: both source-first passes are present, have different review ids, the second pass says `CONFIRMED`, and both fingerprints match the live corpus.
- `STALE`: a record says certified but the source or semantic payload changed.
- `BLOCKED`: the source or correct interpretation cannot be resolved responsibly.
- `INVALID`: malformed certification metadata.

A record missing from the registry is never inferred clean from old review docs, commit messages, passing gates, neighboring fields, or historical frozen status.

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

The first and second passes must carry different `reviewId` values. A worker cannot certify its own pass twice.

## Live self-heal state

The certification registry is not a hand-maintained completion list. Effective state is recalculated from the live source and semantic fingerprints.

Useful commands:

```bash
python3 scripts/semantic_self_heal.py --module yoma status
python3 scripts/semantic_self_heal.py --module yoma next
python3 scripts/validate_semantic_certification.py --module yoma --report
```

The first unfinished record receives one of `AUDIT`, `REPAIR`, `INDEPENDENT_REVIEW`, or `BLOCKED`. In execution, Claude groups the next records by daf and reviews that whole daf before certifying it.

A real ambiguity is a stop condition, not permission to guess.

## Recording review state

The reviewer does not hand-edit fingerprint values. Use `semantic_review_state.py` to record completed review decisions and stamp fingerprints only after an independent confirmation.

Examples:

```bash
python3 scripts/semantic_review_state.py first --module yoma --sugya yoma-024a-s01 --review-id session-A --verdict REPAIR_REQUIRED --evidence-file /tmp/024a-first.json
python3 scripts/semantic_review_state.py repaired --module yoma --sugya yoma-024a-s01 --repair-ref HEAD
python3 scripts/semantic_review_state.py second --module yoma --sugya yoma-024a-s01 --review-id session-B --verdict CONFIRMED --evidence-file /tmp/024a-second.json --commit-ref HEAD
```

A clean first pass still requires the independent second command before the record can become `CERTIFIED`.

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
