# Yoma Rashi translation-quality campaign: Step 1 state reconstruction

**Status: campaign in progress, Step 1 of 10 (read-only state
reconstruction).** This is a Yoma content-quality campaign, not a phase
of `docs/platform-closure-plan.md`. It does not reopen platform
architecture, does not touch Gemara/Mishnah source text, Rashi entry
ids, daf assignment, `linkedGemaraLineIds`, sourceRefs, argumentFlow,
the renderer, or any module/worker/deployment contract. Full
constraints in the campaign's governing directive; not restated here.

Machine-readable inventory:
`docs/reports/data/rashi-translation-quality-inventory.json` (8,854
entries). Generator: `modules/yoma/scripts/generate_rashi_translation_inventory.py`
(`--check` mode verifies the committed inventory's `he`/`en` text still
matches live `learning_data.js` - regenerate after every repair batch).

## What a Rashi entry actually is

Every entry in `learning_data.js`'s per-daf `rashiLines[]` array (source
of truth: `assets/learning/yoma/<daf>.learning.json`'s
`rashiTranslations[]`) carries exactly ten fields, per
`shared/schema_map.js`'s `rashiLine` schema:

`id`, `sourceType` (always `"rashi"`), `daf`, `vilnaLine`, `he`
(canonical - talmud.dev, matches Sefaria's Vilna edition), `en` (the
translation this campaign audits), `enSource`, `source` (always
`"talmud.dev"`), `confidence`, `linkedGemaraLineIds`.

**No entry carries a review-history or provenance-beyond-`enSource`
field.** There is no `reviewedBy`, no timestamp, no per-entry note.
Daf-level provenance has to be reconstructed from repository history
(git commits + `docs/rashi-audit-backlog.md`'s narrative), never from
the entry itself.

## Provenance: 100% AI-generated, uniformly

Checked directly against all 8,854 entries, not assumed:

- `enSource`: **`ai_helper_translation`, 8,854/8,854 (100%)**. No entry
  is `sefaria_validated` or `editorial`.
- `confidence`: **`helper`, 8,854/8,854 (100%)**. No entry is
  `validated`.
- `source`: **`talmud.dev`, 8,854/8,854** (the Hebrew's provenance,
  unrelated to English quality).
- Empty `en`: **0**.

Every English Rashi translation in the corpus was AI-generated and
carries the same "helper, not validated" confidence stamp regardless of
how much review it has actually received. `enSource`/`confidence` are
therefore uniform and carry no per-entry review signal - they answer
"how was this text produced," not "has this text been checked."

## What prior work has and has not verified

Distinguishing structural/linking validation from translation-quality
review is the single most important finding of this step, because
several existing tools have names that sound like semantic review but
are not:

| Tool | What it actually checks | Translation-quality evidence? |
|---|---|---|
| `validate_rashi.py` | he order/count vs talmud.dev, en+enSource present, no leak into Gemara | No - structural only |
| `validate_rashi_content.py` | pattern-matches known placeholder/scaffold text signatures, em/en dash, daf-level entry-count parity | No - coarse pattern detection, not fidelity |
| `validate_rashi_links.py` | `linkedGemaraLineIds` resolve to real lines | No - structural linking only |
| `validate_rashi_boundary_authorizations.py` | boundary (empty-link) registry consistency | No - structural |
| `validate_rashi_repetition.py` | duplicate/near-duplicate `en` text across entries | No - a risk *signal* (feeds Step 2), not a verdict |
| `audit_rashi_scaffold.py` | placeholder-narration text patterns ("Rashi: opens...") | No - pattern detection |
| `audit_rashi_semantic.py` | anchor-token (citation/source-name) drift and fabrication-suspect detection between an entry and its declared daf | **No - explicitly disclaimed**: its own docstring states "This cannot prove a translation correct." It flags SHIFTED/FABRICATION-SUSPECT daf-level alignment risk via surviving-translation anchor tokens, not English fidelity to the Hebrew. |
| `audit_rashi_association.py` | broken/cross-daf `linkedGemaraLineIds` targets | No - structural |

**None of the above constitute translation-quality review**, matching
the governing directive's explicit instruction not to count structural
association validation as such. They are valuable and remain in force
unchanged - they are the gates that keep structure, linking, and
scaffold-fabrication defects out - but they answer a different
question than this campaign asks.

## What genuine semantic (Hebrew-vs-English) review has happened

One thing did do real translation-quality review: a long batch-by-batch
campaign recorded in `docs/rashi-audit-backlog.md`, run from VERSION
14.67 through 15.29+, that read each daf's real Hebrew (from
`assets/talmuddev/<daf>.json`'s `rashi` array) against its English and
fixed what it found. This is genuine prior semantic work, not
structural validation - and it predates this campaign's own, stricter
A-F disposition/defect-tag rubric.

**Reconstructing its coverage precisely required combining two
sources, because git history alone cannot answer the question**: this
repository's entire pre-VERSION-15.05-era history was squashed into a
single root commit (`655b973` - confirmed via `git rev-list
--max-parents=0 main`; its message, "Fix Yoma 19b Rashi helper
alignment," is just whatever the last real commit happened to be named
before squashing, not evidence about which files it "really" touched -
the squash commit's diff necessarily touches every file that existed at
that point). `git log` can only individually attribute commits *after*
that root - roughly the second half of 19b onward. Everything before
that (most of the documented 14.67-15.03 batch narrative) is invisible
to git at file granularity by construction, exactly as
`docs/rashi-audit-backlog.md` itself already warns ("Repository history
was squashed... treat them as historical fact only").

So the generator combines:

1. **`docs/rashi-audit-backlog.md`'s "Content-quality audit coverage (as
   of VERSION 15.293)" section** - the most recent git-history-grounded
   coverage map, itself produced by directly cross-referencing every
   `rashiTranslations[].en` against its real Hebrew. This is the
   authoritative source for the 41 daf its own "Wave 1 audit" table
   individually classifies (see below), and for the remaining 132 daf's
   general "content-audited" status.
2. **Fresh `git log` per daf** (root commit excluded) as supplementary,
   independently-verifiable evidence for daf whose review happened
   post-squash.

**No Yoma content has changed since VERSION 15.293** - the entire
Phase 3/4 platform-closure campaign that ran immediately before this
one never touched `modules/yoma` content (verified repeatedly this
session via tree-digest and `git diff` proofs) - so this classification
is live, not stale.

## Per-daf provenance buckets (fresh, VERSION 15.397)

| Bucket | Daf count | Meaning |
|---|---|---|
| `content-reviewed` | 132 | At least one genuine Hebrew-vs-English semantic pass (pre-squash batch narrative or post-squash reconstruction/realignment commit) |
| `known-needs-reconstruction` | 25 | Wave 1 audit confirmed: `en` is generic filler or fabricated, unrelated to its own Hebrew line |
| `known-needs-realignment` | 9 | Wave 1 audit confirmed: `en` systematically translates an adjacent line's Hebrew instead of its own |
| `checked-no-fix-needed` | 5 | Wave 1 audit cross-referenced against Hebrew, found no genuine error (or only low-confidence, unacted-on notes) |
| `narrow-fix-only` | 2 | Wave 1 audit found and fixed one narrow, isolated error; not a full re-review |

Total: 173 daf, matching the corpus exactly.

**Critical point this campaign's rubric requires stating explicitly:**
`content-reviewed` here describes *prior* review under an *older,
narrower* method (narrow high-confidence fixes only, log-don't-guess on
ambiguity, no formal A-F disposition or defect-tag vocabulary). It is
**not** equivalent to this campaign's `VERIFIED` disposition. Per the
governing directive, **every entry in the Step 1 inventory is marked
`reviewStatus: "UNREVIEWED"`, regardless of prior review depth** -
`priorReviewDepth` is preserved as evidence for Step 5 to weigh when it
chooses a review method (entry-by-entry, evidence-backed cluster, or
hybrid), not as a substitute for review.

## Answers to Step 1's specific questions

- **Which fields contain Hebrew/English?** `he` (Hebrew), `en`
  (English) - see schema above.
- **Human-authored, generated, imported, or mixed?** 100% AI-generated
  (`ai_helper_translation`), uniformly, confirmed by direct corpus
  query.
- **Explicit provenance on entries?** No - only the uniform
  `enSource`/`confidence` stamp; all daf-level provenance is
  reconstructed externally (git history + the audit backlog).
- **Did previous audits evaluate meaning or only structure/linking?**
  Both exist, and this document distinguishes them precisely (table
  above): the eight listed validators/audits are structural or
  pattern-based; only the VERSION 14.67-15.29+ batch narrative did
  genuine Hebrew-vs-English semantic review.
- **Which known-repaired daf have stronger review evidence?** The 132
  `content-reviewed` daf, further distinguished by whether their
  evidence is independently git-verifiable (post-squash) or narrative-only
  (pre-squash, per `docs/rashi-audit-backlog.md`).
- **Were any entries already semantically reviewed?** Yes, at the daf
  level, per the buckets above - but under the older, narrower method,
  not this campaign's rubric.
- **Can prior review records be reused responsibly?** Left to Step 5,
  as directed; this document supplies the evidence needed to decide.
- **Does "resolved" in old reports mean structural or translation
  verification?** Depends on the report - this document's table
  disambiguates every tool's actual scope so that question never has to
  be guessed at again.

## Inventory schema

`docs/reports/data/rashi-translation-quality-inventory.json`:

```json
{
  "schemaVersion": 1,
  "totalEntries": 8854,
  "totalDaf": 173,
  "dafProvenanceSummary": { "content-reviewed": 132, "...": "..." },
  "dafProvenance": { "<daf>": { "depth", "provenanceSource", "postSquashCommitCount", "contentReviewCommits" } },
  "entries": [
    {
      "id", "daf", "vilnaLine", "he", "en", "enSource", "source", "confidence",
      "linkedGemaraLineIds", "priorReviewDepth",
      "riskSignals": [], "riskScore": null,
      "reviewStatus": "UNREVIEWED", "primaryDisposition": null,
      "defectTags": [], "reviewerEvidence": null,
      "repairPR": null, "finalVerificationSHA": null
    }
  ]
}
```

`riskSignals`/`riskScore` are populated by Step 2's audit tooling (not
this step - Step 1 is read-only reconstruction, no detection logic).
`reviewStatus`/`primaryDisposition`/`defectTags`/`reviewerEvidence`/
`repairPR`/`finalVerificationSHA` are populated batch by batch starting
Step 6.

## Next steps

Step 2 (risk-triage audit tooling, its own PR, no translation edits) is
next.
