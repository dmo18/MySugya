# Rashi translation-quality campaign, Step 4: pilot reconciliation and final report

Step 4 of the campaign governed by the September-session directive (see
`docs/reports/rashi-translation-quality-plan.md` for Step 1,
`docs/reports/rashi-translation-risk-audit.md` for Step 2,
`docs/reports/rashi-translation-style-guide.md` for Step 3). This document
is the terminal record for Step 4: it reconciles all four review batches,
computes corpus-wide detector precision, and makes the Step 5 methodology
recommendation. **No translation edits happen in this document or its
companion PR** except where explicitly noted as a reconciliation
correction; this is aggregation and analysis of work already merged in PRs
#394-399.

## Pilot scope

- **Cohort**: 200 unique entries, 110 daf, 7 of 8 perakim, frozen before
  review began (`docs/reports/data/rashi-pilot-cohort.json`,
  `docs/reports/rashi-pilot-cohort-methodology.md`).
- **Review packets**: `docs/reports/data/rashi-pilot-review-packets.json`
  (context only; semantic conclusions recorded separately in the
  inventory and the four batch reports).
- **Batches**: 4 PRs of 50 entries each (PR #396, #397, #398, #399), plus
  two tooling prerequisites (PR #394 cohort/packet tooling, PR #395
  worker-type registry extension) - 6 PRs total for Step 4, all merged
  sequentially through protected `main`, each verified deployed before the
  next began.
- **Method**: for every entry, the Hebrew was read independently, its
  linked Gemara/Mishnah line(s) and surrounding context were read, and the
  English was compared against that reading - never against the existing
  English as a starting assumption. Every changed or BLOCKED entry
  received an independent second semantic pass (re-derived from Hebrew and
  context again, not merely re-checked) before being finalized. Full
  per-entry evidence lives in the four batch reports
  (`docs/reports/rashi-pilot-batch-1-report.md` through `-4-report.md`)
  and the inventory's `reviewerEvidence` field for each of the 200
  entries.

## Aggregate results (all 200 entries)

| Disposition | Count | Rate |
|---|---|---|
| VERIFIED | 177 | 88.5% |
| MINOR_EDIT | 11 | 5.5% |
| SUBSTANTIVE_REPAIR | 9 | 4.5% |
| RETRANSLATE | 2 | 1.0% |
| DUPLICATION_OR_CONTAMINATION | 0 | 0.0% |
| BLOCKED | 1 | 0.5% |
| **Total** | **200** | **100%** |

**Changed-translation count: 22** (MINOR_EDIT + SUBSTANTIVE_REPAIR +
RETRANSLATE + DUPLICATION_OR_CONTAMINATION). Second-pass results:
**22/22 CONFIRMED, 0 REJECTED, 0 MODIFIED-beyond-the-original-proposal** -
every proposed repair survived independent re-derivation from Hebrew and
context unchanged.

Defect-tag totals across all findings: SHIFTED (5), OMITTED_TEXT (5),
INVENTED_TEXT (5), WRONG_MEANING (4), OVEREXPLAINED (3), WRONG_LOGIC (3),
PUNCTUATION (1), WRONG_TECHNICAL_TERM (1), HEBREW_LEFT_UNTRANSLATED (1).
No entry received more than 2 tags; no entry received a tag outside the
campaign's fixed vocabulary.

### Coverage

- **Daf**: 110 of 173 (all daf touched by the frozen cohort; not
  corpus-wide - see "Full-corpus effort estimate" below)
- **Perakim**: 7 of 8 (perek 8, daf 73b-88a, was not represented in this
  pilot's cohort; Step 5 will need explicit coverage of it)

## The one BLOCKED entry

`rashi-yoma-009b-001`'s stored Hebrew field carries a leaked HTML artifact
(`span class="five">` prefix). Confirmed isolated - a corpus-wide scan of
all 8,854 `he` fields found exactly this one occurrence. Not translation-
edited (Hebrew is immutable baseline); this is a Hebrew-source data-quality
defect requiring a separate repair pass outside this campaign's scope, and
is reported here for the record. No other entry required a structural
stop.

## Results by risk tier (Step 2 automated triage)

| Tier | Total | Changed | Changed rate |
|---|---|---|---|
| High risk (riskScore >= 9) | 71 | 7 | 10% |
| Medium risk (2-8) | 55 | 9 | 16% |
| Zero risk (riskScore 0) | 74 | 6 | 8% |

Risk tier is a weak predictor of defect presence: the highest-risk tier's
changed rate (10%) is barely different from the zero-risk tier's (8%), and
medium risk is actually highest (16%). **6 of the 22 real defects found
carried zero automated risk signals at all** - a purely semantic-only
catch rate of 27% of all defects that no existing detector could have
surfaced (`rashi-yoma-004a-001`, `-007b-001`, `-011a-001`, `-012b-002`,
`-013b-001`, `-027a-001`).

## Results by historical provenance (Step 1 classification)

| Provenance | Total | Changed | Changed rate |
|---|---|---|---|
| narrow-fix-only | 2 | 1 | 50% |
| content-reviewed | 113 | 12 | 11% |
| checked-no-fix-needed | 9 | 1 | 11% |
| known-needs-realignment | 25 | 1 | 4% |
| known-needs-reconstruction | 51 | 7 | 14% |

The two strongest historical-debt buckets - `known-needs-realignment`
("en systematically translates an adjacent line's Hebrew instead of its
own") and `known-needs-reconstruction` ("confirmed generic filler or
fabricated") - show changed rates of **4% and 14% respectively in this
sample**, far below what those characterizations would suggest if taken to
mean "most entries on this daf are wrong." This is the single most
important finding of the entire pilot for the Step 5 recommendation (see
below): batches 1 and 3 both independently found the same pattern on
different daf within these buckets (11 entries checked on daf 5a/5b/6a
found 1 real shift; 10 entries checked on daf 53a/53b/54b/55a-b found 1
real fabrication).

**This does not mean the historical flags are wrong.** The Wave 1 audit
that produced them found real, specific, documented problems, and a
handful of sampled entries per daf cannot rule out worse concentrations in
entries this pilot did not happen to select. It means the flag is
daf-level, not entry-level: treating it as "every entry here is bad" would
be a mistake with real cost (discarding and rewriting correct
translations, and risking new defects in currently-faithful entries).

## Results by daf position and perek

| Position | Total | Changed |
|---|---|---|
| Beginning third of Yoma | 100 | 13 |
| Middle third | 24 | 3 |
| End third | 36 | 6 |

| Perek | Total | Changed |
|---|---|---|
| 1 | 91 | 14 |
| 2 | 22 | 2 |
| 3 | 23 | 0 |
| 4 | 4 | 0 |
| 5 | 16 | 2 |
| 6 | 36 | 4 |
| 7 | 8 | 0 |
| 8 (not covered) | 0 | - |

No perek or daf-position shows a defect concentration dramatically
different from the corpus-wide average once sample size is accounted for;
perek 1's higher raw count reflects its correspondingly larger share of
the cohort (round-robin selection naturally over-represents perek 1
somewhat, as documented in the cohort methodology), not a
disproportionately higher rate.

## Results by translation length

| Length | Total | Changed |
|---|---|---|
| Short gloss (<=6 words) | 9 | 1 |
| Medium | 180 | 21 |
| Long explanation (>=30 words) | 11 | 0 |

No meaningful signal here either direction - length alone does not predict
defect presence.

## Results by review category (selection stratum)

Every stratum a defect was found in: `multiple_linked_gemara_lines` (19%
changed, 3/16), `purity_terminology` (18%, 2/11),
`narrative_or_contextual_explanation` (18%, 3/17), `middle_of_yoma` (17%,
4/24), `historical_reconstruction_or_realignment` (15%, 3/20),
`beginning_of_yoma` (14%, 14/100), `no_automatic_warning` (12%, 5/43),
`zero_risk` (12%, 5/40), `short_gloss`/`terminology_variance_signal` (12%
each, 1/8 each), `high_risk` (10%, 7/70), `end_of_yoma` (6%, 2/36),
`priesthood_or_temple_terminology` (6%, 1/17). Two strata found **zero**
defects: `long_explanation` (0/9) and `sacrificial_terminology` (0/13) -
both too small to conclude those categories are inherently safer, but
worth noting for Step 6 prioritization.

## Detector precision (all 200 entries, corpus-wide within the pilot)

| Signal | Flagged | Real defects found | Precision |
|---|---|---|---|
| OVEREXPLAINED | 3 | 3 | 100% |
| WRONG_REFERENT | 5 | 3 | 60% |
| INVENTED_TEXT (daf-level) | 51 | 7 | 14% |
| TRUNCATED | 65 | 3 | 5% |
| CONTEXT_MISMATCH (daf-level) | 25 | 1 | 4% |
| FRAGMENT | 1 | 0 | 0% |

**Important defects the detectors missed entirely** (zero risk signal on
the flagged entry): `rashi-yoma-004a-001` (a wife/house-euphemism
mistranslation - WRONG_MEANING), `rashi-yoma-007b-001` (a negation-polarity
inversion - WRONG_MEANING/WRONG_LOGIC), `rashi-yoma-011a-001`,
`-012b-002`, `-013b-001` (three instances of a fabricated "New comment:"
scaffold phrase - INVENTED_TEXT), and `rashi-yoma-027a-001` (a technical
Talmudic-idiom inversion, corroborated against the corpus's own adjacent
Gemara translation - WRONG_MEANING/WRONG_LOGIC). None of these six are
within the design scope of any Step 2 detector: idiom resolution, negation
polarity, and narration-phrase fabrication outside a fixed pattern list
are all invisible to length-ratio and pattern-matching heuristics.

**OVEREXPLAINED and WRONG_REFERENT are the two signals worth trusting as
priority indicators** (100% and 60% precision respectively), though both
have very small n (3 and 5 flags corpus-wide within the pilot) and should
be treated as directional, not conclusive, until validated against a
larger sample. **TRUNCATED, CONTEXT_MISMATCH, and daf-level INVENTED_TEXT
are weak predictors** (4-14% precision) - useful for surfacing candidate
daf for review, not for prioritizing individual entries within them, and
must never be treated as a verdict.

## Cross-entry word-anticipation: a distinct defect family, found independently three times

Batches 2 and 4 both found the same shape of defect: a word belonging to
one entry's own Hebrew gets translated one entry early or late by a
*neighboring* entry, leaving the affected entry's own English missing that
word (an omission) or duplicating/inventing content that belongs elsewhere
(a fabrication). Found in `rashi-yoma-002a-011` (batch 1),
`rashi-yoma-015a-003`, `-020b-023`, `-023a-005` (batch 2, all with the
out-of-cohort neighbor left untouched), and `rashi-yoma-059b-001/002`,
`-065a-001/002` (batch 4, both sides correctable since both were in
cohort). A negative-case check (`rashi-yoma-065b-002`) confirmed the
distinguishing test used throughout: anticipation is only a defect when
content is lost or falsified, not when a complete phrase is quoted once at
its natural place with nothing lost.

This pattern is systemic enough (7 confirmed instances across all four
batches) to be worth a **targeted, evidence-backed sweep** in Step 6: a
tool that compares each entry's own Hebrew word-for-word against its own
English (not the corpus-wide heuristics used in Step 2, which look at an
entry in isolation) could flag candidate cross-entry mismatches for human
confirmation, without ever auto-correcting them.

## The fabricated "New comment:" scaffold phrase: also systemic

Found 4 times (`rashi-yoma-011a-001`, `-011b-015`, `-012b-002`,
`-013b-001`), always in the same shape: two Hebrew clauses separated only
by a colon, with the English inserting a narration phrase that corresponds
to nothing in the Hebrew. A simple, low-risk, high-confidence targeted
search for the literal string `"New comment:` across all 8,854 `en`
fields would find every remaining instance in one pass - a strong
candidate for the first bounded batch of Step 6, since the fix pattern
(delete the phrase, nothing else) is uniform and mechanically verifiable
even though the *decision* to flag it required genuine semantic judgment
in this pilot (the phrase does not match any existing scaffold-narration
regex).

## Regression and platform evidence (fresh at reconciliation)

- **Rashi entry count**: 8,854 (unchanged across every batch)
- **Associations**: 10,061 declared, 0 broken, 0 cross-daf (unchanged)
- **Boundary registry**: 20 authorized, 20 in corpus, 20/20 matched, 0
  stale, 0 duplicate, 0 unauthorized (unchanged)
- **Hebrew text**: confirmed byte-unchanged in every one of the 6 Step 4
  PRs via direct `git diff` inspection of `learning_data.js` - only `en:`
  lines ever appeared in any diff
- **`npm run validate:offline:yoma`**, **`npm test`**, **`npm run
  test:browser`**, **`npm run build`**, **`npm run check:deploy-html`**,
  **`python3 scripts/worker_pipeline.py verify --full`**: all green on
  every one of the 6 PRs
- **Exhaustive Rashi browser corpus association evidence**: Phase 4
  (platform-closure, this session, PR #390) already established this gate
  PASS via a fresh dispatch of `rashi-browser-shards.yml` (run id
  `30727598582`, 173/173 daf, 215 passed, 0 failed). Since Step 4 changed
  no association, boundary, renderer, or module-contract state (only
  `rashiTranslations[*].en` text), that evidence's underlying conditions
  were unchanged - but a fresh dispatch was run anyway at this
  reconciliation point, at the campaign's own final merge commit, for
  gapless, dated evidence specific to this report: run id `30763563287`,
  artifact id `8838233113`, commit `f81844ed9811ec2657170cc0a607d7ae7dab8b21`
  (Step 4's own final merge SHA), 173/173 daf, 8,854 entries, 215 passed, 0
  failed. `node scripts/audit-rashi-renderer-readiness.mjs` with that
  artifact in place: **8/8 checks pass, READY**.
- **UNREVIEWED count**: 8,654 of 8,854 (200 reviewed, 100% of the frozen
  pilot cohort, 0% of entries outside it touched)

## Step 5 recommendation: HYBRID REVIEW

**Recommendation: hybrid review - entry-by-entry for the majority of the
corpus, with narrowly-scoped, evidence-backed cluster passes for two
specific, already-identified defect signatures.**

### Why entry-by-entry is the default, not cluster review

The pilot's central finding rules out a pure cluster/bulk-reconstruction
strategy as the primary method: **27% of confirmed defects (6/22) carried
zero automated risk signal**, and the two strongest historical-debt
buckets showed real defect rates (4% and 14%) far below what a
"reconstruct everything on this daf" policy would assume. A cluster-first
strategy driven by daf-level flags would:

- Miss all 6 zero-signal defects entirely (they are individually
  undetectable by any existing corpus-wide heuristic).
- Waste effort discarding and rewriting the 89% of `known-needs-
  realignment` entries and 86% of `known-needs-reconstruction` entries
  that are already correct.
- Risk introducing new defects into currently-faithful translations during
  bulk rewriting - a cost this pilot never incurred, because every change
  here was a targeted, evidenced, individually-second-passed correction.

### What must receive direct (entry-by-entry) review

Every entry not covered by one of the two cluster passes below. This is
still the large majority of the remaining 8,654 entries. Reviewers should
use the same method proven across all 4 batches: read Hebrew independently
first, read linked Gemara/Mishnah context, compare, and only then look at
the existing English.

### What may receive cluster-assisted review (and how every member is still individually checked)

Two, and only two, defect signatures are common and uniform enough, with
strong-enough pilot evidence, to justify a cluster-assisted pass instead of
pure independent entry-by-entry review:

1. **The "New comment:" scaffold phrase.** A deterministic corpus-wide
   search for the literal string is safe and complete (regex, not
   semantic judgment - Step 2/6 tooling can generate this list
   automatically). Each hit still requires a human (or AI-as-reviewer)
   to (a) confirm the Hebrew has no real structural marker justifying the
   label - true in all 4 pilot instances but not guaranteed corpus-wide -
   and (b) apply the exact same mechanical fix (delete the phrase). This
   is "cluster-assisted" only in candidate generation; every member still
   gets an individual confirm-and-fix step, exactly as this pilot did.
2. **Cross-entry word-anticipation.** Requires new tooling (see above) to
   generate candidates by comparing each entry's own untranslated Hebrew
   words against its own English - not a corpus-wide pattern match, a
   per-entry Hebrew-completeness check. Every candidate still requires a
   full entry-by-entry review of both the affected entry and its
   neighbor, exactly as batches 2 and 4 did, since the correct fix
   direction (which entry the word actually belongs to) requires reading
   Hebrew, not just detecting an anomaly.

No other cluster strategy is recommended. In particular, **do not**
cluster-process by daf-level historical flag alone (the pilot's central
finding directly rules this out) or by risk-tier score alone (10% vs. 8%
vs. 16% changed rate across tiers shows the score does not cluster real
defects meaningfully).

### Recommended batch size and PR count

1-10 daf per batch depending on defect density, as the campaign's original
directive specified - in practice, this pilot's 4 batches of ~20-32 daf
each (50 entries) took roughly the same reviewer effort per batch
regardless of daf count, so **batch by entry count (40-60 entries per PR,
matching the campaign's existing PR-size cap) rather than by daf count**.
At the pilot's ~11% average changed rate and the corpus's 8,654 remaining
entries, expect roughly **950 changed translations remaining** if the
pilot's rate holds corpus-wide (a projection, not a guarantee - see caveat
below).

**Full-corpus effort estimate**: 8,654 entries / 50 entries per batch =
**~173 more batch PRs** at the pilot's pace, before Step 7-10 wrap-up work.
This is a large number and should be explicitly acknowledged to the user
before Step 6 begins at that scale - the pilot took 4 content batches plus
2 tooling PRs across a single extended session; corpus-wide work at the
same rate is a multi-week-or-longer undertaking if continued at this
granularity and rigor. The user may want to discuss whether to (a)
continue at full rigor at this pace, (b) increase batch size once the
process is further proven (the campaign directive caps at 75 entries/PR),
or (c) treat the 200-entry pilot itself as sufficient sampling evidence
and prioritize the two cluster passes (points 1-2 above) plus targeted
follow-up on specific daf, deferring full entry-by-entry sweep of the
remaining ~86 daf not yet touched at all.

### How BLOCKED cases will be handled

Exactly as this pilot handled its one BLOCKED entry: full documentation of
the structural stop (what's wrong, why it's out of scope, corpus-wide
isolation-check evidence), no placeholder translation, no schema change to
represent "blocked" state (the existing inventory fields already suffice),
and the entry remains untouched pending a separately-scoped repair pass
(in this case, Hebrew-source data repair, not a translation task).

### Which automated signals remain advisory vs. useful for prioritization vs. should be retired/revised

- **Advisory only, never a verdict** (per the campaign's standing rule,
  reaffirmed by pilot evidence): all six signals in the precision table
  above.
- **Useful for prioritization** (worth reviewing first within a batch):
  OVEREXPLAINED and WRONG_REFERENT (100% and 60% precision, though small
  n - re-evaluate as more batches accumulate data).
  `historical_reconstruction_or_realignment`-flagged daf remain useful for
  *daf selection* (ensuring coverage of the areas most likely to need
  attention) even though they are weak for *entry-level* prioritization
  within those daf.
- **Should be revised, not retired**: TRUNCATED (5% precision) has
  already been narrowed once (Step 2's documented correction from a
  28%-of-corpus false-positive rate); this pilot's 5% precision on the
  narrowed version suggests it could be narrowed further or reclassified
  as "daf-selection signal" rather than "entry risk signal." CONTEXT_MISMATCH
  and daf-level INVENTED_TEXT should be explicitly re-labeled in any Step
  6 tooling as "this daf has known historical debt, entry-level status
  unconfirmed" rather than carried as a per-entry risk score at all -
  carrying them as scores implies an entry-level meaning the pilot
  disproved.
- **No signal should be retired outright** - even the weakest (FRAGMENT,
  0% precision, n=1) had too small a sample in this pilot to conclude
  it never works; it simply produced no signal either way here.

## Confirmations

- **Hebrew remained unchanged**: confirmed for all 22 changed entries and
  spot-confirmed corpus-wide via `git diff` inspection showing only `en:`
  lines in every Step 4 PR's diff against its base.
- **Final Rashi entry and association counts**: 8,854 entries, 10,061
  associations, 0 broken, 0 cross-daf.
- **Boundary registry**: 20/20, 0 stale, 0 duplicate, 0 unauthorized.
- **8,654 of 8,854 entries remain UNREVIEWED** (200 reviewed = exactly the
  frozen pilot cohort, no more, no less).
- **Step 5 was not started**: no full-corpus batch review has begun; this
  report only recommends a methodology for the user to authorize.

## Status

**Step 4: COMPLETE.** All 200 cohort entries reviewed with an assigned
disposition; 0 entries left in an ambiguous state. **Step 5 was not
started** - no full-corpus batch review has begun; this report only
recommends a methodology pending user authorization to proceed.

## Version and merge history

| PR | Purpose | Merge SHA | VERSION |
|---|---|---|---|
| #394 | Pilot cohort + review-packet tooling | `b1079219256be5f80090eae287fbc31dd487fd56` | 15.401 |
| #395 | Worker-type tooling prerequisite | `804a97335019cb4af9ac596528c2156ee7fe9c89` | 15.402 |
| #396 | Batch 1 (entries 0-49) | `44fbb4acb2f9e5c7be76d11927b8ef1f3c8f2507` | 15.403 |
| #397 | Batch 2 (entries 50-99) | `f830ab25e9b0b9561fb74cd157055c1debf6f658` | 15.404 |
| #398 | Batch 3 (entries 100-149) | `19df8b39ebfc6c91b775451b1dfd314991c1e1b6` | 15.405 |
| #399 | Batch 4 (entries 150-199) | `f81844ed9811ec2657170cc0a607d7ae7dab8b21` | 15.406 |

Starting main SHA (fresh checkout before Step 4 began): `da8830043ee96c3f8832934caac6969a309ea31b`
(VERSION 15.400, immediately after Step 3/PR #393). Final main SHA at this
reconciliation: `f81844ed9811ec2657170cc0a607d7ae7dab8b21` (VERSION 15.406).
