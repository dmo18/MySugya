# argumentFlow category contract: decision record

**Status: implemented. Zero corpus content edits.** This is Phase 2A of
`docs/platform-closure-plan.md`.

## The decision

`category` is **derived from a versioned registry**
(`shared/argument_step_taxonomy.json`), never stored on the argumentFlow
step itself. A step's authored `type` is untouched; `category` is a pure
function of `type`, looked up at render/validation time.

This was one of three options the plan named: stored explicitly per step,
derived from a registry, or stored-and-cross-validated. Derivation wins on
every axis that matters here:

- **Zero content risk.** No edit to any `modules/yoma/assets/learning/*.json`
  file was needed to reach 100% category coverage. The frozen Yoma corpus
  is untouched by this entire phase.
- **Tractate portability.** A new tractate that reuses an existing `type`
  value (`question`, `proof`, ...) gets its category for free. A genuinely
  new `type` value needs one registry line, not a per-sugya migration.
- **Auditability.** One file is the single source of truth. There is no
  second copy to drift: `scripts/generate_argument_taxonomy.py` regenerates
  `app.jsx`'s embedded lookup tables from the JSON byte-for-byte, and
  `validate_argument_taxonomy.py`'s R6 check fails the gate if they ever
  diverge.
- **No silent drift.** Coverage is asserted, not assumed: R3 fails the
  build the moment a corpus type has no registry entry, so a future content
  PR that introduces a new `type` value is caught immediately rather than
  silently falling through to a guessed category.

**Rejected: stored explicitly per step.** Would mean writing a `category`
field into 1,953 argumentFlow steps across 173 frozen-adjacent content
files, for a value that is 100% mechanically determined by `type`. Zero
semantic gain, non-zero risk to content that CLAUDE.md requires explicit
approval to touch, and it reintroduces exactly the drift risk (a step whose
`type` and `category` disagree) that derivation makes structurally
impossible.

**Rejected: stored-and-cross-validated.** Same content-risk cost as
"stored explicitly," with a validator bolted on to catch the drift that
choice invites. Derivation gets the validation guarantee for free by
construction.

## What the registry looks like

`shared/argument_step_taxonomy.json`:

```json
{
  "categories": {
    "<id>": { "en": "...", "he": "..." | null, "symbol": "...",
              "definition": "...", "inclusionCriteria": "...",
              "exclusionCriteria": "...", "examples": ["..."] }
  },
  "typeToCategory": { "<observed type>": "<category id>" }
}
```

`scripts/generate_argument_taxonomy.py` regenerates the
`ARGUMENT_CATEGORIES` / `ARGUMENT_TYPE_TO_CATEGORY` block in `app.jsx`
between marker comments from this JSON. `stepMetaFor` looks up a step's
category via `ARGUMENT_TYPE_TO_CATEGORY`, takes `sym`/`he` from
`ARGUMENT_CATEGORIES`, but **always displays the step's own `type`,
humanized, as the `en` label** - never the category's name. This is the
mechanism that satisfies "type must not be destructively collapsed into
category": many types share one category's visual treatment, but every
step still reads as itself.

## Category vocabulary: 21 categories, evidence-based

The original 13 `controlledValues.argumentStepType` values are preserved
as categories unchanged (`case`, `question` renamed `inquiry`, `proposal`
renamed `position`, `challenge`, `objection`, `counter_objection`, `proof`
renamed `support`, `answer`, `distinction`, `qualification`, `rejection`,
`resolution`, `takeaway`) - renaming a category id does not change what a
step displays, since the step's own type name is what's shown, not the
category's.

Eight new categories were added because real discourse-function evidence
demanded them, not to fit an aesthetic count:

| category | why it earned its own slot |
|---|---|
| `ruling` | 515 steps (26% of the corpus) state a concrete settled halakhic fact, often one of several enumerated in sequence. Sampling showed this is a distinct discourse move from `resolution` (which settles a *live dispute*) - a `ruling` step frequently follows another `ruling` step (214 of 515 do), functioning as itemized legal content, not argument. |
| `elaboration` | 212 steps (11%). Sampling across daf 2a-19b showed this continues/expands the immediately preceding point regardless of whether the content is legal-logical or purely descriptive (Temple architecture measurements alongside halakhic detail) - a distinct function from both `reasoning` and `description`. |
| `dispute` | 44 steps presenting two or more named authorities' views as one unit ("R. Meir vs. Rabbis"). Talmudic literature treats a machloket as a first-class structural unit distinct from a single `position`; the evidence bears this out. |
| `narrative` | 60 steps of aggadic/theological/historical storytelling with no halakhic disposition. |
| `description` | 47 steps of physical/architectural/factual background that is neither a legal case (`case`) nor a story (`narrative`). |
| `procedure` | 33 steps narrating the physical execution of a ritual step by step, including tallies of acts performed - distinct from `ruling` (states law about the act) and `narrative` (tells a story). |
| `support` | Absorbs `proof` (the original canonical value) plus `citation`, `derivation`, `premise`, `tradition` - all bring textual/traditional evidence for a position, a coherent evidentiary function. |
| `meta` | 9 steps that organize the discussion's form (a transition, a digression marker, a summary of the discussion) rather than its halakhic content. |

Every one of the 106 non-canonical `type` values was reviewed against real
step text before assignment (see `docs/reports/data/argumentflow-inventory.json`
for the corpus-wide frequency table and per-type examples this review used).
High-frequency types (`ruling`, `elaboration`, `analysis`, `narrative`,
`dispute`, `claim`, `conclusion`, `principle`, `derivation`, `reason`,
`premise`, `explanation`, `application`, `detail`, `position`, `description`,
`implication`, `statement`, `citation` - together over 85% of non-canonical
volume) were sampled across multiple daf and, for `ruling` specifically,
checked against its structural position (first/mid/last in a step sequence)
and neighboring step types before assignment, per the plan's requirement to
inspect representative examples rather than classify from the string alone.

No arbitrary catch-all exists. Every one of the 119 observed values has an
explicit, reviewed entry; `validate_argument_taxonomy.py`'s R3 check fails
if any corpus type lacks one.

## Hebrew and symbols: only where genuinely established

Per the plan's explicit requirement, a category's `he` (Hebrew display
label) is `null` unless the term is an established, accurate Talmudic term
for that discourse function - never a literal translation manufactured to
fill the field. Concretely:

- `dispute` -> `מַחֲלוֹקֶת` (machloket): the standard term for a Sages'
  disagreement.
- `ruling` -> `פְּסָק` (psak): the standard term for a halakhic ruling.
- `narrative` -> `אַגָּדָה` (aggadah): the standard term for non-legal
  Talmudic narrative.
- The 13 original canonical categories keep their existing, already-vetted
  Hebrew terms.
- `description`, `reasoning`, `elaboration`, `procedure`, `meta` have `he:
  null` and the neutral symbol `○`. I do not have confident, established
  single Hebrew terms for these as category labels, and inventing one
  "merely to fill metadata" is explicitly prohibited. `validate_argument_
  taxonomy.py`'s R5 check enforces this: every non-null `he` value must
  contain genuine Hebrew characters, which catches an accidental
  placeholder but cannot by itself catch a *wrong* term - the discipline of
  leaving it `null` when unsure is what actually prevents fabrication.

## Two bugs caught and fixed during construction

Recorded here because they are exactly the kind of drift this design is
meant to prevent, and because a future edit to the registry should not
reintroduce them:

- `answer` (the canonical type, 27 steps, established Hebrew `תֵּירוּץ`,
  a direct reply within an ongoing exchange) was initially folded into the
  `resolution` category (the sugya's overall concluding disposition,
  `מַסְקָנָא`). These are genuinely distinct discourse functions that happen
  to share a checkmark symbol in the pre-existing `STEP_META`; `answer` was
  restored to its own category.
- `proposal` (13 steps, established Hebrew `הַצָּעָה`, symbol `✎`) was
  renamed into a broader `position` category, but the category definition
  did not initially carry `proposal`'s established Hebrew/symbol forward.
  Fixed so `position` uses `הַצָּעָה`/`✎`, since `proposal` is the most
  representative member of that category and its term already fits.

Both were caught by `validate_argument_taxonomy.py`'s R1 dead-category
check and by manual review before merge, not left for a later pass to find.

## Validation added

`modules/yoma/scripts/validate_argument_taxonomy.py`, seven checks (R1-R7):
registry integrity, no duplicate/conflicting mappings, 100% corpus
coverage, no malformed type values, no invented Hebrew, renderer/registry
byte-parity, and no category outside `inquiry` carrying the Question
symbol/term. 27 unit tests in `test_validate_argument_taxonomy.py` exercise
each rule against synthetic fixtures plus the real corpus.

## Migration status

**There is no migration to run.** Because category is derived rather than
stored, 100% category coverage was reached the moment the registry was
completed - Phase 2A's "Step 3: implement category coverage" and this
document's Step 2 contract are the same artifact. All 492 sugyot and all
1,953 argumentFlow steps have valid category coverage as of this PR, with
zero content files touched.

## Future-tractate implications

A new tractate that authors `argumentFlow` steps needs no category work at
all if it reuses existing `type` values. If it introduces a genuinely new
discourse-function `type`, one registry entry is added (with real Hebrew
only if genuinely established) and `validate_argument_taxonomy.py` proves
coverage immediately - no per-sugya migration, ever.

## Stop conditions that did not trigger

None of the plan's argumentFlow stop conditions applied: no category
required invented semantics (every category was built from and named after
real discourse-function evidence), no category erased a meaningful specific
distinction (every original `type` string survives unchanged; category is
purely additive), and no Hebrew label or symbol was invented to fill a
field (five categories deliberately carry `he: null`).
