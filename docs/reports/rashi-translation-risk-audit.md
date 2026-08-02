# Yoma Rashi translation-quality campaign: Step 2 risk-triage audit

**Status: campaign in progress, Step 2 of 10 (deterministic risk-triage
tooling, read-only, no translation edits).** Continues
`docs/reports/rashi-translation-quality-plan.md` (Step 1). Same
constraints: not a phase of `docs/platform-closure-plan.md`, does not
touch Hebrew, entry ids, `linkedGemaraLineIds`, boundary registry,
Gemara/Mishnah text, argumentFlow, sourceRefs, literal translations, the
renderer, or any module/worker/platform contract.

Tool: `modules/yoma/scripts/audit_rashi_translation_risk.py` (`npm run
audit:rashi:translation-risk:yoma`, no npm alias yet - run directly).
Tests: `modules/yoma/scripts/test_audit_rashi_translation_risk.py` (39
synthetic checks, one or more per detector).

**No English translation was edited by this step.** The tool only
*reads* `learning_data.js` and *writes* `riskScore`/`riskSignals` back
into the Step 1 inventory - `reviewStatus` stays `UNREVIEWED` and
`primaryDisposition` stays `null` for all 8,854 entries, confirmed
directly after every run.

## What "risk" means here

Every detector below is triage only, per the governing directive: it
raises or lowers a numeric risk score and attaches a plain-language
reason, and nothing more. No detector, individually or in combination,
assigns a final disposition. A risk score of 0 does **not** mean
"verified" - it means "no automatic signal fired," which is a much
weaker claim, and every entry's `reviewStatus` reflects that (`UNREVIEWED`,
not `VERIFIED`, regardless of score).

## Detectors

| Detector | Tag(s) | What it checks |
|---|---|---|
| `detect_empty` | `OMITTED_TEXT` | English field is empty or whitespace-only |
| `detect_identical_to_hebrew` | `HEBREW_LEFT_UNTRANSLATED` | English is byte-identical to the Hebrew |
| `detect_hebrew_leakage` | `HEBREW_LEFT_UNTRANSLATED` | Hebrew-script characters present inside the English field |
| `detect_length_ratio` | `OMITTED_TEXT` / `OVEREXPLAINED` | English length is <0.25x or >4.5x the Hebrew's character length |
| `detect_truncation` | `TRUNCATED` | English ends abruptly, with no closing punctuation at all, on a bare function word (see false-positive note below - this is deliberately narrow) |
| `detect_fragment` | `FRAGMENT` | 3 words or fewer with no closing punctuation |
| `detect_unmatched_punctuation` | `PUNCTUATION` | Unbalanced parentheses, or an odd count of double-quote characters |
| `detect_mechanical_template` | `FRAGMENT` | Matches a known scaffold-narration template or placeholder pattern (defense-in-depth; corpus-wide scaffold debt is already 0 per `audit_rashi_scaffold.py`) |
| `detect_pronoun_heavy` | `WRONG_REFERENT` | >35% of words (6+ word minimum) are common pronouns, with no automatic referent check possible |
| `detect_possible_copied_gemara` | `CONTEXT_MISMATCH` | English substantially overlaps its linked Gemara line's own English - possibly a copied Gemara translation rather than Rashi's own comment |
| `build_duplicate_clusters` (corpus-wide) | `DUPLICATED` | Identical normalized English shared across ≥2 entries with different Hebrew |
| `apply_neighboring_duplicate_signals` (corpus-wide) | `DUPLICATED` | Identical English on the immediately following same-daf entry |
| `apply_daf_level_signals` - reused, not reimplemented | `SHIFTED` / `INVENTED_TEXT` / `CONTEXT_MISMATCH` | Reuses `audit_rashi_semantic.py --profile --json`'s existing SHIFTED/FABRICATION-SUSPECT daf classification, and Step 1's `known-needs-reconstruction`/`known-needs-realignment` provenance buckets (VERSION 15.293 Wave 1 audit) |

Historically reconstructed/realigned daf are covered by the last row:
Step 1's provenance classification is fed directly into the risk model,
so daf with known, evidence-backed defects score highest without
needing a second independent detector to rediscover what is already
documented.

## Corpus-wide results (fresh run, VERSION 15.398 baseline)

- **8,854/8,854 entries analyzed.**
- **2,557 flagged** (risk score > 0), **6,297 unflagged** (risk score
  0 - unreviewed, not verified).
- Tag totals: `INVENTED_TEXT` 1,261, `TRUNCATED` 681, `CONTEXT_MISMATCH`
  486, `OVEREXPLAINED` 158, `WRONG_REFERENT` 74, `PUNCTUATION` 62,
  `FRAGMENT` 20.
- **Duplicate clusters: 0** (cross-daf identical-English contamination).
  Plausible and expected: `validate_rashi_repetition.py` and the
  completed scaffold-fabrication campaign already gate the corpus at 0
  documented near-duplicate violations; this detector checks a
  different, narrower case (exact cross-daf English match with
  different Hebrew) and corroborates rather than contradicts that.
- **Terminology watchlist: 6 terms tracked** (Kohen Gadol, Temple,
  offering/sacrifice, impurity, purity, service/rite) - purely
  observational counts of which of a small set of expected English
  tokens each term's occurrences use; not a pass/fail gate (Step 3
  defines the real terminology contract).
- Daf-level concentration matches Step 1's provenance almost exactly:
  `INVENTED_TEXT` (1,261) tracks the 25 `known-needs-reconstruction`
  daf; `CONTEXT_MISMATCH` from the daf-level signal (486) tracks the 9
  `known-needs-realignment` daf - internal consistency check passed
  (the two independently-built numbers agree).

Full per-entry data: `docs/reports/data/rashi-translation-risk-report.json`
(includes `dafSummary`, `tagTotals`, and the top-100 `reviewQueueTop`).
Duplicate clusters: `docs/reports/data/rashi-duplicate-clusters.json`.
Terminology variance: `docs/reports/data/rashi-terminology-variance.json`.

## False-positive risks and limitations (found and corrected during this step)

**`detect_truncation` was rewritten after direct spot-checking found a
~28% corpus-wide false-positive rate in its first version.** The
original heuristic flagged any English ending in a dash, comma, colon,
or semicolon. Manually inspecting a sample of the 2,453 initial hits
showed the overwhelming majority were **not** truncated: Rashi entries
conventionally quote a Hebrew lemma fragment and end that fragment with
a dash or comma before the commentary continues (e.g. `"'and he shall
bring it' -"` is a complete, correct rendering of a lemma boundary, not
a cut-off sentence). The detector now only flags a bare ending with **no
closing punctuation of any kind**, landing on a function word - narrowed
from 2,453 to 681 hits, and spot-checking the new set found the sampled
hits genuinely incomplete (see the detector's own docstring/comment for
the corrected rule). This is recorded here specifically so a future
reader does not re-introduce the wide version.

**Remaining known limitations, not yet corrected because they require
human judgment (left for Steps 4-6), not further heuristics:**

- `detect_fragment` and `detect_length_ratio`'s "too short" case will
  both fire on correct, terse single-word Rashi entries (e.g. a lemma
  translated as `"Of the"` for Hebrew `של` is a completely correct
  translation of a two-letter word, but reads as a 2-word fragment with
  no closing punctuation). This is an expected, common false-positive
  class for terse entries and is why every automatic signal is
  triage-only, never a verdict.
- `detect_length_ratio`'s "too long" case fires on legitimate editorial
  continuation notes (e.g. Hebrew `כל` paired with English explaining
  "the daf ends mid-word here; the comment continues on 7a...") - the
  length ratio is real, but the cause is a correct annotation about a
  page boundary, not invented content. Several `OVEREXPLAINED` hits in
  this run are this pattern.
- `detect_pronoun_heavy` cannot resolve what a pronoun actually refers
  to (that requires the local Gemara/Rashi context a human reviewer
  reads) - it only measures pronoun density as a proxy for "this entry
  may need a referent check," and is deliberately weighted low (weight
  2) relative to signals with stronger evidence.
- `detect_possible_copied_gemara`'s substring-overlap check can miss a
  genuinely copied translation that was lightly reworded, and can flag
  a legitimate Rashi comment that happens to closely paraphrase its
  Gemara line (rare, but Rashi occasionally does restate the line before
  commenting on it).
- `HEBREW_LEFT_UNTRANSLATED` does not distinguish Hebrew from Aramaic
  script (both use the same Unicode block) - the campaign's separate
  `ARAMAIC_LEFT_UNTRANSLATED` tag cannot be assigned automatically;
  every hit surfaces as `HEBREW_LEFT_UNTRANSLATED` and a human reviewer
  determines which language the untranslated fragment actually is.
- The terminology-variance report only checks for a small, fixed set of
  expected English tokens per watched Hebrew term (not a full
  clustering of free-form phrasing) - it is intentionally observational
  and cannot itself distinguish a legitimate contextual rendering (e.g.
  "the High Priest" as a valid alternative to "Kohen Gadol") from a
  genuine terminology drift defect. Step 3 defines the real contract;
  this report only surfaces where variance exists for a human to judge.

**No detector was tuned to hit a target defect rate.** The one
correction made (`detect_truncation`) was driven by a directly observed,
overwhelming false-positive pattern found through manual spot-checking,
not by a desire to lower or raise the flagged count.

## Prioritized review queue

Top-100 highest-risk entries by summed signal weight, in
`docs/reports/data/rashi-translation-risk-report.json`'s
`reviewQueueTop`. The five highest-scoring entries in this run are on
daf 55a, 57b, and 6b - all three are in Step 1's `known-needs-
reconstruction` bucket (VERSION 15.293 Wave 1 audit), so the
independent, entry-level signals (`TRUNCATED`, `PUNCTUATION`,
`CONTEXT_MISMATCH`) agree with the daf-level historical evidence rather
than contradicting it. Entries where multiple independent detectors
fire together (rather than a single detector alone) are a stronger
signal worth prioritizing first in the queue.

## Next steps

Step 3 (editorial style and terminology contract, its own docs/tooling
PR) is next, followed by Step 4's pilot semantic review.
