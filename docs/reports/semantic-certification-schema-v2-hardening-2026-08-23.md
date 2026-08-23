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

- `fieldInventory`: machine-enumerated by **recursing** the entire semantic
  payload (`enumerate_semantic_paths`), not a hand-curated list, so a new or
  legacy field is caught automatically. Every path is machine-classified
  SEMANTIC (authored prose/claims -- must be `SUPPORTED`, `REPAIR_REQUIRED`,
  or `BLOCKED`; `NONFACTUAL` is illegal) or STRUCTURAL (identifiers/
  coordinates/enums/slugs -- may be `NONFACTUAL`) by a fixed, narrow
  allowlist the reviewer does not control. Supporting lines are mechanically
  checked against the field's authorized range; a claim may not use a
  different daf as support unless `crossReference` is both set AND
  legitimate for that path (only `relatedSugyot` among SEMANTIC paths, or
  any STRUCTURAL path), and even then the cited daf/range must actually
  exist.
- `dafBoundary`: `rawLineCount`/`finalRawLine` mechanically checked against
  the live raw source; `dafEndState` classification.
- `boundaryLeakageSweep`: mandatory for **every** daf regardless of the
  declared `dafEndState` (a false `COMPLETE` classification cannot skip it),
  covering every SEMANTIC path with an explicit
  `importsNextDafConclusion:true/false`; an open `dafEndState` additionally
  requires a nonblank justifying `note` per entry.
- `staleContentSweep`: a fixed, mechanically-enumerated checklist of
  stale-content failure modes, each with an explicit found:true/false
  attestation; any unresolved finding blocks certification.
- `reviewerContextId` / `auditorContextId`: every review block now records a
  genuinely distinct reviewer/session/context id; the validator requires
  first-vs-second pass contexts to differ, the final auditor's context to
  differ from BOTH the first and second pass contexts, and the final
  audit's `reviewId` to differ from both passes' `reviewId` too.

See `docs/semantic-self-heal.md` ("Schema 2.0: mandatory final whole-record
audit") for the full contract and `docs/claude-semantic-campaign-runbook.md`
for the updated execution sequence.

## Round 2: closing bypasses found by independent review

Before this PR merged, an independent review of the actual implementation
(not just the PR description and green CI) found that the first cut of
schema 2.0 still contained certification bypasses. Each is fixed below.

1. **NONFACTUAL escape hatch for semantic prose.** The original validator
   let a reviewer classify any path, including summaries and quiz answers,
   as `NONFACTUAL` to skip source-support checking, and the test helper
   marked every field `NONFACTUAL` and called that clean. Fixed by the
   SEMANTIC/STRUCTURAL classification above: a reviewer no longer chooses
   the category, and `NONFACTUAL` is mechanically illegal for a SEMANTIC
   path. New test: `test_1_semantic_prose_cannot_be_marked_nonfactual_to_bypass_support`.
2. **Field enumeration was hand-curated, not exhaustive.** `enumerate_semantic_paths`
   now recurses the whole payload rather than naming fields one by one, with
   only a small allowlist of structural key names exempted. New tests prove
   a brand-new field, a legacy `visualizableElements.description` key, and a
   `quizSeeds` `distractors` array are all caught without touching the
   enumerator (`test_2..4`).
3. **Daf-level glossary wasn't fingerprinted or audited.** `semantic_payload`
   now includes `dafGlossary`; a glossary edit invalidates every sugya
   certificate on the daf, exactly like the summary (`test_5`, `test_6`).
   `semantic_repair_scope_v2.py`'s unconditional "glossary changed" ban was
   replaced with the same full-daf-scope rule already used for the summary,
   so a legitimate same-daf glossary correction (the real 9a case) is
   permitted, and a partial-scope one still fails (`test_20`, exercised
   against a disposable tar+git-init repo copy, the same fixture pattern
   `test_worker_pipeline_integration.py` already uses).
4. **`crossReference` was an unrestricted bypass.** Now legal only for a
   SEMANTIC path under `CROSS_REFERENCE_ALLOWED_SEMANTIC_TOP_KEYS`
   (`relatedSugyot`) or any STRUCTURAL path, and the cited daf/range is
   checked against the real raw source (`test_7`, `test_8`).
5. **The boundary-leakage sweep was conditional on the reviewer's own
   `dafEndState` claim.** Now unconditional, with a stricter nonblank-`note`
   requirement when the daf is declared open (`test_9`, `test_10`, `test_11`).
6. **Reviewer-context/reviewId distinctness was incomplete.** The final
   auditor's context/reviewId now must differ from the SECOND pass too, not
   only the first (`test_18`, `test_19`), and `docs/semantic-self-heal.md`
   now states plainly that distinctness is mechanically verified but not
   cryptographic proof of real isolation.
7. **Tests obtained a "clean" certificate only via the NONFACTUAL escape.**
   `clean_audit`/`realistic_final_audit` now build SEMANTIC entries as
   genuinely `SUPPORTED` with real in-range lines; `STRUCTURAL` entries
   remain `NONFACTUAL`. All pre-existing tests were re-verified against this
   realistic fixture.

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

`scripts/test_semantic_certification_v2.py` (22 tests) proves, as
generalized invariants (never hardcoded to 7a/7b or to a specific field
name):

1. A SEMANTIC path cannot be marked `NONFACTUAL` to bypass source support.
2. A brand-new field the enumerator has never seen by name is still caught
   by generic recursion, without any change to the enumerator.
3. A legacy `visualizableElements.description` key is still caught.
4. A `quizSeeds` `distractors` array is still caught.
5. Omitting the daf-level glossary from `fieldInventory` blocks certification.
6. A glossary edit after certification makes the certificate stale.
7. `crossReference` on a local field (e.g. `learning.*`) is illegal and
   blocks certification even when set.
8. A legitimate `crossReference` (`relatedSugyot`) is validated against the
   real target daf/range -- valid citations certify, out-of-range ones fail.
9. `boundaryLeakageSweep` is mandatory even when `dafEndState` is `COMPLETE`.
10. `importsNextDafConclusion: true` blocks certification regardless of the
    declared `dafEndState`.
11. An open `dafEndState` requires a nonblank `note` on every swept entry.
12. Any `staleContentSweep` category reporting `found: true` blocks
    certification.
13. Omitting even one machine-enumerated field path from `fieldInventory`
    blocks certification.
14. A `finalAudit` whose bound fingerprints do not match the current
    candidate blocks certification.
15. A semantic edit after a valid final audit makes the certificate stale.
16. Source-support lines outside the authorized daf/sugya range block
    certification, including a falsely-declared `boundarySafe: true` and a
    claim citing a different daf without `crossReference`.
17. Reusing the same reviewer context for the "independent" second pass
    blocks certification even with a different `reviewId` string.
18. The final auditor's context equalling the SECOND pass's (not just the
    first's) blocks certification.
19. The final audit's `reviewId` equalling either pass's `reviewId` blocks
    certification.
20. A same-daf glossary correction is permitted only under full-daf repair
    scope; a partial-scope one still fails (exercised against a disposable
    repo-copy fixture, not just in-process).

Plus migration-specific tests: the migration script is provably one-time
(refuses to run against an already-2.0 registry) and preserves historical
evidence untouched; the ratchet carve-out is provably narrow (fails outside
the exact 1.0-to-2.0 transition, without the migration provenance marker,
or if fingerprints were tampered with under the relabel).

`scripts/test_semantic_certification.py` (the base safety-property suite)
was updated in parallel: its audit-building helper now produces a
`realistic_final_audit` (SEMANTIC paths genuinely `SUPPORTED` with real
in-range lines, STRUCTURAL paths `NONFACTUAL`) instead of the old
all-`NONFACTUAL` shortcut, and gained explicit coverage for the
second-vs-final auditor-context check and the glossary-inclusion-in-
fingerprint property.

## Completion condition for this PR

- All existing ordinary gates (source, schema, Rashi, build, browser,
  worker-pipeline) remain intact and unmodified in behavior.
- `scripts/test_semantic_certification.py` and
  `scripts/test_semantic_certification_v2.py` pass.
- The live registry shows 53 `REVALIDATION_REQUIRED` + 439 `UNCERTIFIED`,
  zero `CERTIFIED`, under schema 2.0 -- old v1.0 certificates are visibly
  not equivalent to new-schema certification.
- CI is green on the exact tooling head.

## Remaining limitations this cannot mechanically enforce

- **Content correctness.** Nothing here proves a `SUPPORTED` claim's
  supporting lines actually say what the claim asserts, or that a
  `staleContentSweep`/`boundaryLeakageSweep` `found:false`/
  `importsNextDafConclusion:false` attestation is honest. The validator
  proves the audit is complete, fingerprint-bound, range-checked, and
  internally consistent -- it does not, and cannot, adjudicate Talmudic
  meaning. That remains the reviewer's job, backed by genuine independent
  re-derivation from source.
- **Execution provenance of reviewer contexts.** As stated in
  `docs/semantic-self-heal.md`, distinctness of `reviewId`/
  `reviewerContextId`/`auditorContextId` is mechanically verified; that
  those values correspond to an actually separate execution context (a real
  subagent/session invocation, not a relabeled continuation of the same
  reasoning) is a process discipline this repository cannot cryptographically
  verify.
- **Classification allowlist correctness.** `STRUCTURAL_LEAF_KEYS` /
  `STRUCTURAL_SCALAR_ARRAY_KEYS` / `CROSS_REFERENCE_ALLOWED_SEMANTIC_TOP_KEYS`
  are hand-authored (though narrow, and biased to default new fields into
  the stricter SEMANTIC bucket rather than exempt them). A future field
  whose key name collides with an existing structural key name (e.g. a new
  object that happens to have its own meaningful `"type"` field) would be
  under-audited until someone reviews the allowlist; the recursion itself
  guarantees the *path* is never silently missing, only that its
  classification could in principle need a second look.

No Yoma 7a/7b content repair happens in this PR. That is the next phase,
gated on this one merging.
