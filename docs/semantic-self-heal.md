# MySugya semantic self-heal protocol

## Purpose

This protocol closes the gap that allowed structurally valid but semantically
wrong enrichment to be marked reviewed and frozen.

The governing rule is simple:

> Passing validators is not evidence that an explanation is true. Semantic
> correctness exists only when a source-first review record is bound by hash to
> the exact source and exact semantic payload it reviewed.

Legacy `review: "reviewed"` values are historical metadata only. They never
confer semantic certification.

## Why this is required

The repository already has strong gates for source provenance, schema shape,
Rashi structure/placement, generated-file freshness, PR scope, worker manifests,
allowlist monotonicity, browser rendering, and deployment. Those controls are
valuable and remain mandatory.

They cannot by themselves prove that an English explanation, argument step,
summary, quiz answer, misconception correction, speaker attribution, quantity,
or ruling actually matches its Gemara range. A coherent family of fields can
all repeat the same wrong interpretation and therefore pass internal-consistency
checks together.

The semantic certification layer prevents that failure from being confused with
a green engineering build.

## Certification states

State is derived, not trusted blindly from a stored label.

- `UNCERTIFIED`: no certification record exists. This is the default.
- `REPAIR_REQUIRED`: a source-first first pass found one or more semantic defects.
- `REPAIRED_PENDING_REVIEW`: repairs were made and require an independent source-first pass.
- `CERTIFIED`: both source-first passes are present, have different review ids,
  the second pass says `CONFIRMED`, and both fingerprints match the live corpus.
- `STALE`: a record says certified but the source or semantic payload changed.
- `BLOCKED`: the source or correct interpretation cannot be resolved responsibly.
- `INVALID`: malformed certification metadata.

A record missing from the registry is never inferred clean from old review docs,
commit messages, passing gates, neighboring fields, or historical frozen status.

## The two fingerprints

Each certificate binds two independent hashes.

### `sourceFingerprint`

Includes:

- module and daf
- sugya id
- declared Vilna line range
- line/Sefaria mapping
- Sefaria refs
- exact raw Hebrew lines from the authoritative talmuddev cache in that range

If source text, boundaries, or mappings change, the certificate is stale.

### `semanticFingerprint`

Includes all authored learner-facing sugya content except source coordinates and
review metadata, plus the daf-level summary. This includes display and learning
fields, argumentFlow, quizzes, misconceptions, topic tags, prerequisites,
visualizable elements, final ruling, difficulty, glossary, related sugyot, and
other authored semantic fields.

If any meaningful semantic field changes, the certificate is stale automatically.
The daf summary is included in every sugya certificate on that daf so page-level
claims cannot change under green child records.

Rashi remains governed by its dedicated full-corpus translation and association
system. A final module freeze requires both strict sugya certification and all
Rashi gates/review campaigns complete.

## Independent review

Two semantic passes are mandatory.

### First pass

The reviewer receives the primary Hebrew source first, then local source context,
relevant linked Rashi, and only then the current enrichment. The reviewer must
independently reconstruct what the source says before comparing the enrichment.

Legal first-pass outcomes:

- `VERIFIED`
- `REPAIR_REQUIRED`
- `BLOCKED`

Agreement among existing enrichment fields is never evidence.

### Second pass

The independent reviewer receives a packet that intentionally omits first-pass
reasoning and findings. It contains the source, context, relevant Rashi, and the
current candidate content.

Legal outcomes:

- `CONFIRMED`
- `REJECTED`
- `BLOCKED`

The first and second passes must carry different `reviewId` values. A worker
cannot certify its own pass twice.

## Self-heal queue

The queue is generated from live effective state. There is no hand-maintained
list of supposedly completed sugyot.

Run:

```bash
python3 scripts/semantic_self_heal.py --module yoma status
python3 scripts/semantic_self_heal.py --module yoma next
```

The first unfinished sugya receives exactly one action:

- `AUDIT`
- `REPAIR`
- `INDEPENDENT_REVIEW`
- `BLOCKED`

For a review packet:

```bash
python3 scripts/semantic_self_heal.py --module yoma packet --sugya yoma-024a-s01
```

For the independent second pass:

```bash
python3 scripts/semantic_self_heal.py --module yoma packet --sugya yoma-024a-s01 --second-pass
```

The process advances in corpus order and does not skip a `BLOCKED` item. A real
ambiguity is a stop condition, not a reason to guess.

## Repair rule

A semantic repair is holistic at the sugya level. The reviewer must inspect all
semantic fields, not only the field where the first symptom was noticed. This
prevents the former loop where one visible error was fixed while related wrong
claims survived elsewhere in the same record.

For the target sugya, the repair may need to change display, learning,
argumentFlow, quizSeeds, misconceptions, tags, prerequisites, source refs,
finalRuling, or boundaries. The repair must remain source-driven and must not
alter immutable Hebrew merely to make enrichment fit.

After a repair:

1. regenerate deterministic output
2. run every existing source/schema/Rashi/worker gate
3. run the independent second semantic pass
4. store a fresh certificate using the live fingerprints
5. run the semantic certification gate
6. merge only after CI and required independent review are green
7. advance to the next live queue item

## Bootstrap and permanent strict mode

The current Yoma corpus predates this certification system. It is therefore
bootstrapped as uncertified rather than grandfathered.

During bootstrap, `strictMode` is `false`. The PR ratchet still enforces a hard
rule: any source or semantic payload changed by a PR must leave that PR freshly
`CERTIFIED`. Existing unmodified uncertified debt may remain only while the
campaign works through it.

The certification inventory must shrink monotonically toward 100 percent.
Previously certified records may never regress.

When all 492 sugyot pass:

```bash
python3 scripts/validate_semantic_certification.py --module yoma --strict
```

then, and only then, set `strictMode` to `true`. From that point any missing,
stale, blocked, or uncertified sugya fails CI and deployment.

## Required final freeze definition

A module may be called semantically frozen only when all of the following are
true at the same commit:

1. strict semantic certification is 100 percent
2. every certificate fingerprint matches live source and semantic content
3. all source provenance and schema gates pass
4. all Rashi translation, association, boundary, structural, and rendering gates pass
5. generated data is fresh
6. browser tests pass
7. no semantic blocker exists
8. CI is green on the exact commit being deployed

No report, historical completion claim, or old `reviewed` flag can substitute
for those conditions.
