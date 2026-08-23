# Repository semantic-safety review, 2026-08-22

## Scope

Independent review of the current MySugya repository at main commit
`3c6a12239d343b72fa144775675bc28d91e29d6f`, focused on whether the existing
architecture can guarantee semantic correctness of the learning corpus rather
than only structural/provenance correctness.

Reviewed planes:

- repository and module descriptors
- canonical schema contract
- Yoma learning and talmuddev source layers
- build and generated-data flow
- package scripts and offline validation suite
- Git hooks
- GitHub Actions deployment/CI workflow
- worker task-type registry
- worker manifest/preflight/packet/prompt/verify/scope/review/queue design
- schema ownership matrix
- enrichment contract/ratchet machinery
- Rashi semantic, structural, translation, association, boundary and browser systems
- semantic-readiness heuristic audit
- tail-enrichment audit/repair/closeout machinery
- current completion/open-item documentation
- direct current-main source-versus-enrichment checks on known-risk records

This report does not treat prior completion reports as proof. Current raw files
were compared directly where semantic correctness was tested.

## Confirmed strengths

The repository has unusually strong deterministic engineering controls:

1. Source provenance validators protect Hebrew/English/Vilna alignment.
2. Generated-data freshness prevents hand-edited runtime drift.
3. Schema and enrichment-contract validators detect shape and controlled-value debt.
4. The worker pipeline constrains files, JSON paths, authorizations, batch size,
   allowlist changes and generated output.
5. CI runs offline validation, manifest checks, Rashi scope checks, build, smoke,
   browser, fixture-onboarding and scaffold tests.
6. The Rashi subsystem has dedicated semantic and structural campaigns, boundary
   authorization, renderer tests, drift checks and independent review evidence.
7. Merge-base ratchets prevent known mechanical debt from silently returning.
8. The tail-enrichment repair campaign correctly introduced source-proven audit
   records and independent review for its bounded 77a-88a scope.

These controls should be retained.

## Confirmed architectural gap

No existing repository primitive means:

> this exact semantic payload was independently checked against this exact source
> payload, and that certification is automatically invalid if either changes.

The current `review` metadata is mutable editorial state, not a source-bound
certificate. Existing semantic-readiness tooling detects placeholders,
duplicates, vocabulary errors, generic questions and similar symptoms, but it
explicitly does not prove that the explanation means what the Hebrew source says.

The tail-enrichment audit is source-based but bounded to a previously identified
cohort and previously identified affected fields. Its repair task type cannot
serve as a universal corpus self-healer because it forbids changes to
argumentFlow, quizSeeds and misconceptions and requires a pre-existing merged
audit record.

The generic worker packet for learning tasks exposes existing title/keys and
argumentFlow ids, not a mandatory primary-source-first semantic packet.

Therefore a coherent but wrong record can remain internally consistent and green.

## Current-main proof that the gap is real

### Yoma 24a

The raw talmuddev source begins with the worn-garment discussion, then asks the
amount of terumat hadeshen and derives a fistful from `veherim`, then moves into
the services for which a non-priest incurs death.

The current enrichment, while marked reviewed, asserts that the worn garments
are one-quarter the size/fabric of standard garments and builds multiple display,
learning and argumentFlow claims around that proposition. That proposition is not
what the declared source range says.

Disposition: semantic repair required.

### Yoma 42a

The raw source throughout the declared range is the crimson-thread/parah-adumah
slaughter and procedure discussion.

The current enrichment, while marked reviewed, inserts Jericho customs and
`ish iti`/Azazel impurity into argumentFlow and summary claims assigned to that
same 42a range.

Disposition: semantic repair required.

### Yoma 51a

The raw 51a source is still discussing firstborn, tithe, Pesach/Pesach Sheni and
tumah classification issues.

The current enrichment states that a Mishna on 51a has the High Priest receive
the stirred bull blood and enter the Holy of Holies.

Disposition: semantic repair and boundary review required.

These are present on current main after the repository's extensive existing gate
suite and after historical completion claims. They demonstrate that semantic
certification cannot be inferred from green deterministic gates or legacy review
status.

## Root cause

The historical architecture established strong controls around a baseline before
it had a universal source-first certification primitive for that baseline.
Later systems became increasingly good at preserving, migrating and ratcheting
that state. Internal consistency and bounded audits could catch many defects but
could not establish complete semantic truth across all 492 sugyot.

The missing invariant was semantic provenance.

## Required correction

The new semantic-certification layer introduced with this review provides:

- sourceFingerprint per sugya
- semanticFingerprint per sugya
- default UNCERTIFIED state, never grandfathering `reviewed`
- first source-first review
- independent second source-first review with a different review id
- automatic STALE state after any source or semantic change
- PR ratchet requiring any changed semantic/source payload to leave fresh CERTIFIED
- eventual strict mode requiring the entire corpus to be fresh CERTIFIED
- deterministic self-heal queue driven from live state rather than a hand-written backlog
- source-first packets with first-pass reasoning hidden from second-pass reviewers

## Completion condition

The repository should not again call Yoma semantically frozen until the new
strict semantic gate passes 492/492 at the exact deployed commit, together with
all existing source/schema/Rashi/generated/browser gates.
