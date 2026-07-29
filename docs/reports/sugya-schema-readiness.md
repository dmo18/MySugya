# Sugya schema readiness: 492 sugyot

**Field coverage: 492/492 complete. Semantic readiness: blocked by one
systemic defect affecting 417 sugyot.**

`validate_schema_completeness.py` answers "is the field present and
non-blank?" and reports 492/492. That is necessary but not sufficient, so
`audit_schema_semantics.py` asks the harder questions: is the value real, is it
distinct, and is it inside the vocabulary the schema and the renderer expect.

    npm run report:schema:semantics:yoma   # status, always exit 0
    npm run audit:schema:semantics:yoma    # gate, exit 1 on any failing check
    ... --check C6                         # every finding for one check
    ... --json                             # machine-readable report

## Result

| check | what it verifies | result |
|---|---|---|
| C1 | every required display/learning field present and non-blank | **PASS** 492/492 |
| C2 | no placeholder or stub markers | **PASS** |
| C3 | no required field degenerately short | **PASS** |
| C4 | no required field duplicated within or across sugyot | **PASS** |
| C5 | `takeaway.type` inside controlled values | **PASS** 492/492 |
| C6 | `argumentFlow.type` inside controlled values | **FAIL** 1,320 steps |
| C7 | `argumentFlow.type` has a `STEP_META` label (Hebrew term + symbol) | **FAIL** 1,320 steps |
| C8 | quizSeeds shape, questions test a distinction | **PASS** 754/754 |
| C9 | no quiz question repeated across the corpus | **FAIL** 4 |
| C10 | misconceptions shape and distinctness | **FAIL** 1 |

**Sugyot with zero findings: 75/492.** The gap is almost entirely C6/C7.

What the passes are worth stating plainly: all 492 sugyot carry every required
field, no placeholder markers exist anywhere in the corpus, no learning field is
byte-identical to another within or across sugyot, all 492 `takeaway.type`
values are inside the canonical five, and all 754 quiz questions are specific
rather than generic. That is a genuinely healthy enrichment layer.

## Blocker: `argumentFlow.type` vocabulary (C6/C7)

`shared/schema_map.js` declares `argumentFlow[].type` as `required: true`,
`status: canonical`, drawn from `controlledValues.argumentStepType`, which lists
**13** values:

    case, question, proposal, challenge, objection, counter_objection,
    proof, answer, distinction, qualification, rejection, resolution, takeaway

The corpus uses **106 additional values** across 1,953 steps:

| | count | share |
|---|---|---|
| steps whose `type` is in the controlled list | 633 | 32.4% |
| steps whose `type` is outside it | **1,320** | **67.6%** |
| sugyot affected | 417 / 492 | |
| daf affected | 163 / 173 | |

Most common offenders: `ruling` (515), `elaboration` (212), `analysis` (47),
`narrative` (45), `dispute` (44), `claim` (31), `conclusion` (29),
`principle` (29), `derivation` (29).

### This is a user-visible defect, not latent debt

Unlike `sourceRefs`, this field is rendered. Two different consumers in
`app.jsx`, and they behaved differently, so they are worth separating:

- `ArgumentFlowPanel` (the sugya view, line ~506) prints `{step.type}`
  **verbatim**. Correct-but-unpolished, never wrong: learners see the real
  token, including the literal `stub`. `styles.css` defines only 7
  `arg-step--*` classes, so most types get no type-specific styling.
- The landing-page flow demo, hero tag and peek fell back to the `question`
  entry when a type was unrecognised, so an unclassified step was shown with
  the Hebrew term for question, the symbol `?`, and the English label
  "Question" regardless of what it actually was.

**Scope of the wrong labelling, stated precisely.** The corpus figure (1,320
steps across 417 sugyot) is the size of the *data* problem. The on-screen
exposure is different and smaller: `deriveFeatured` picks a daf of the day, so
the landing page rotates through all 173 daf, one per day. Measured across that
rotation:

| surface | days showing a wrong label |
|---|---|
| flow demo (first 6 steps of the featured flow sugya) | **148 / 173** |
| hero tag (first step of the featured hero sugya) | **110 / 173** |
| sugya view (`ArgumentFlowPanel`) | 0, renders the raw type |

An earlier draft of this report said all 1,320 steps rendered as "Question".
That conflated corpus scope with screen scope and implied the sugya view
mislabelled too, which it never did. The table above is the accurate statement.

**Fixed at VERSION 15.350** by `stepMetaFor`, which shows an unrecognised type's
own name rather than another type's identity, and leaves Hebrew empty rather
than inventing it. That removes the wrong information. It does not resolve the
vocabulary question below, which stays open.

### Why this is not fixed here

Two legitimate directions, and they are mutually exclusive:

1. **Widen the vocabulary.** Add the observed types to
   `controlledValues.argumentStepType` and to `STEP_META`. Many of the 106 are
   real Talmudic step categories the 13-value list simply never covered
   (`ruling`, `derivation`, `dispute`, `narrative`). But `STEP_META` entries
   carry a Hebrew term and a symbol per type, and inventing Hebrew terminology
   for 106 categories would be fabrication, not normalization.
2. **Normalize the data down to 13.** Re-type 1,320 steps. This is lossy: it
   collapses distinctions the enrichment deliberately drew, and it edits
   `modules/yoma/assets/learning/*`, which is `structural-repair` scope.

Choosing between them is a schema and editorial decision, not a mechanical one,
and CLAUDE.md requires schema changes to be deliberate. **This needs an operator
decision before either path starts.**

A third, narrower option exists and is worth noting separately: leave the data
and the schema alone for now and change only the renderer fallback, so an
unrecognised type displays its own name rather than being mislabelled as a
Question. That removes the wrong information without deciding the vocabulary
question, but it is still a product decision about how unknown types should look.

### The `stub` step is content, not a placeholder

Yoma 5a `yoma-005a-s02` step-06 carries `type: "stub"`. Read against its text,
this is a real open question the daf ends on ("from where do we derive that
requirements not written in the inauguration passage but written elsewhere also
invalidate? This is left unresolved at the end of 5a"). It is correct content
with an unfortunate type name, and C2 correctly does not flag it as a
placeholder. It should be re-typed with whatever vocabulary decision follows,
not deleted.

## Minor findings (C9, C10)

Five duplications, all within a single daf and all plausibly deliberate:

- `72b` s02/s03 share the quiz question "What is the 'gate without a courtyard'?"
- `74a` s02/s03 share a question about `forbidden` versus `karet`
- `74b` s03/s04 share a question about Rav Yosef and the manna verse
- one further repeated quiz question
- one misconception correction repeated between two sugyot

These are redundancy, not errors: adjacent sugyot on one daf can legitimately
probe the same concept. They are reported rather than suppressed so the decision
to keep them is explicit. Low priority.

## Calibration notes

Two checks in the first draft of this audit were wrong, and the corrections are
recorded here so they are not reintroduced:

- **C3 originally used a 5th-percentile word floor.** A percentile floor flags
  roughly that percentile of the corpus no matter how good the corpus is, so it
  can never pass and measures nothing. It now uses an absolute floor of 5 words.
  Observed minimums are 7-18 words per field, so the corpus clears it honestly.
- **C8 originally length-checked quiz answers**, flagging six answers of 2-3
  words. All six are correct terse answers to factual questions ("Two sela.",
  "R. Yehuda.", "Benjamin's tribal portion."). Answer length is not a quality
  signal; C8 now tests the question for generic prompts instead, which is the
  standard CLAUDE.md actually states.
- **C2 originally matched "to be filled"**, which fired on Yoma 64a's real
  sentence about the dead goat's slot needing to be filled. The pattern is now
  restricted to markers that cannot occur in finished prose.

C6 and C7 read their vocabularies out of `shared/schema_map.js` and `app.jsx` at
runtime rather than restating them, so widening either automatically widens the
audit and the three can never drift apart.

## Status

- **Field coverage: 492/492.** Complete, and gated by
  `validate:schema:yoma` in `validate:offline:yoma`.
- **Semantic readiness: blocked** on the C6/C7 vocabulary decision.
  `audit:schema:semantics:yoma` is deliberately not wired into
  `validate:offline:yoma` until that decision lands, for the same reason
  `validate:sourcerefs:strict:yoma` is not: a red gate nobody can turn green is
  not a gate.
