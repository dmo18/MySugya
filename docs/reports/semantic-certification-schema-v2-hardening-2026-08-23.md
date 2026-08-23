# Semantic certification schema 2.0 hardening, 2026-08-23

## Scope

Tooling-only response to an independent audit finding against the semantic
certification system introduced by `docs/reports/repository-semantic-safety-review-2026-08-22.md`.
No Yoma learning content changes in this PR.

## Confirmed gap in schema 1.0

Certification schema 1.0 required two source-first review passes with
different `reviewId` values and a free-text declaration that "every
semantic field was checked." Direct comparison against the current raw
`talmuddev` source demonstrated that this was insufficient:

- Yoma 7a's raw Hebrew ends mid-thought at the word "הא"; the conclusion
  that the tzitz atones for tumah is only completed on 7b. The 7a record was
  `CERTIFIED` under schema 1.0 while other fields (argumentFlow/quiz/prose)
  still stated the completed conclusion as though 7a reached it.
- Yoma 7b's raw Hebrew ends at "ומה", mid-way through the tzitz-to-tefillin
  kal vachomer. One repaired `argumentFlow` step correctly acknowledged the
  cutoff, but other fields in the same `CERTIFIED` record still stated the
  completed kal vachomer as an established result.

In both cases the certification evidence claimed every field had been
checked and the repair was complete. The procedure, not merely the content,
was insufficient: a free-text "everything checked" declaration and a second
`reviewId` string are not falsifiable evidence, and neither caught a
field-by-field false-closure failure on a daf that ends mid-argument.

## Root cause

Schema 1.0 bound a certificate to two fingerprints (source, semantic) and
two review passes, but never mechanically enumerated which fields those
passes were supposed to cover, never mechanically checked the physical daf
boundary against the live raw source, and never required a fresh, isolated
reviewer context (a different `reviewId` string inside the same reasoning
context is not independence).

## Correction: certification schema 2.0

`scripts/semantic_certification.py` now requires a `finalAudit` block on
every `CERTIFIED` record, produced strictly after the two source-first
passes (new `PENDING_FINAL_AUDIT` state), fingerprint-bound to the exact
final candidate:

- `fieldInventory`: machine-enumerated (`enumerate_semantic_paths`), one
  verdict + source-support entry per authored field/leaf actually present,
  with supporting lines mechanically checked against the field's authorized
  range (a claim may not use a different daf as support unless explicitly
  marked `crossReference`).
- `dafBoundary`: `rawLineCount`/`finalRawLine` mechanically checked against
  the live raw source; `dafEndState` classification; an open ending
  requires an explicit per-field `openEndingFieldSweep` proving no field
  imports the next daf's conclusion.
- `staleContentSweep`: a fixed, mechanically-enumerated checklist of
  stale-content failure modes, each with an explicit found:true/false
  attestation; any unresolved finding blocks certification.
- `reviewerContextId` / `auditorContextId`: every review block now records a
  genuinely distinct reviewer/session/context id; the validator requires
  the first and second pass contexts to differ, and the final auditor's
  context to differ from the first pass's.

See `docs/semantic-self-heal.md` ("Schema 2.0: mandatory final whole-record
audit") for the full contract and `docs/claude-semantic-campaign-runbook.md`
for the updated execution sequence.

## Migration: schema 1.0 is not grandfathered

`scripts/migrate_certification_schema_v2.py` performed a one-time,
mechanically narrow transition: every record `CERTIFIED` under schema 1.0
(Yoma 2a-10a, 53 records) was relabeled `REVALIDATION_REQUIRED`, a state
that never reads as `CERTIFIED` regardless of fingerprint freshness.
Historical `firstPass`/`secondPass` evidence and fingerprints were preserved
unchanged for reference. The registry's `schemaVersion` moved from `1.0` to
`2.0`; the migration script refuses to run against a registry that is not
exactly schema 1.0, so it cannot be reused.

The ordinary PR ratchet (`validate_semantic_certification.py --ratchet`)
forbids a previously-`CERTIFIED` record from reading as anything but
`CERTIFIED` at head. A narrow, self-disabling exception
(`allowed_schema_migration_downgrade`) permits exactly this one downgrade,
gated on the base ref's registry being schema 1.0, the head record carrying
the migration script's own provenance marker, and the fingerprints being
byte-identical before and after (so no content regression can hide behind
the relabel). Once this migration merges to `main`, `main`'s schemaVersion
is permanently 2.0, so the base-schema-1.0 condition can never be true again
in this repository's history and the exception self-disables.

## Regression coverage

`scripts/test_semantic_certification_v2.py` proves, as generalized
invariants (not hardcoded to 7a/7b):

1. An open (non-`COMPLETE`) daf ending cannot certify without a clean,
   complete `openEndingFieldSweep`; any field flagged as importing the next
   daf's conclusion blocks certification.
2. Any `staleContentSweep` category reporting `found: true` blocks
   certification.
3. Omitting even one machine-enumerated field path from `fieldInventory`
   blocks certification.
4. A `finalAudit` whose bound fingerprints do not match the current
   candidate blocks certification.
5. A semantic edit after a valid final audit makes the certificate stale.
6. Source-support lines outside the authorized daf/sugya range block
   certification, including a falsely-declared `boundarySafe: true` and a
   claim citing a different daf without `crossReference`.
7. Reusing the same reviewer context for the "independent" second pass
   blocks certification even with a different `reviewId` string.

Plus migration-specific tests: the migration script is provably one-time
(refuses to run against an already-2.0 registry) and preserves historical
evidence untouched; the ratchet carve-out is provably narrow (fails outside
the exact 1.0-to-2.0 transition, without the migration provenance marker,
or if fingerprints were tampered with under the relabel).

## Completion condition for this PR

- All existing ordinary gates (source, schema, Rashi, build, browser,
  worker-pipeline) remain intact and unmodified in behavior.
- `scripts/test_semantic_certification.py` and
  `scripts/test_semantic_certification_v2.py` pass.
- The live registry shows 53 `REVALIDATION_REQUIRED` + 439 `UNCERTIFIED`,
  zero `CERTIFIED`, under schema 2.0 -- old v1.0 certificates are visibly
  not equivalent to new-schema certification.
- CI is green on the exact tooling head.

No Yoma 7a/7b content repair happens in this PR. That is the next phase,
gated on this one merging.
