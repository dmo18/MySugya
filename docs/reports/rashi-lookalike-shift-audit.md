# Rashi look-alike audit: 61a, 67b, 68a, 68b, 70a, 71b

> **SUPERSEDED - ALL REMEDIATION COMPLETE.** This report's task assignments
> ("61a lines 1-45 need full reconstruction", "Haiku MUST NOT run
> rashi-repair on 67b/68a/68b/70a/71b", and the realignment
> recommendations) were all acted on and are finished. As of VERSION
> 15.338, every one of 61a, 67b, 68a, 68b, 70a, and 71b classifies
> **ALIGNED** with `lineLevelSafe=true` and no recommended task type. The
> analysis below is preserved as the historical record of how those defects
> were detected and characterized; do not read its instructions as current
> work. See `docs/reports/open-items.md` for current status.

Read-only forensic audit (audit-only manifest, Fable, VERSION 15.84 on
main). Triggered by the ESCALATED finding of PR #73: 61a vilnaLines
1-45 carry specific-looking English that is unrelated to the raw
Hebrew, and the same pattern was feared on the other stub-block daf.
No content was changed in this pass.

## Method

For each target daf, the raw Rashi lines
(`modules/yoma/assets/talmuddev/<daf>.json`, `rashi` array, 1-based
vilnaLine) were placed side by side with
`rashiTranslations[*].en` from
`modules/yoma/assets/learning/yoma/<daf>.learning.json`. Every line of
all six daf was read and judged semantically (full-daf audit, not
sampling, because the first samples failed on every daf). The judgment
was then quantified with translation-surviving anchor tokens:
parenthesized citations including amud-b forms such as `(דף נז:)`,
tractate names immediately before a daf citation such as
`דזבחים (דף טו:)`, and biblical book citations. For each anchor the
audit located the English line actually containing the corresponding
English token and recorded the signed offset.

## Classification

| daf | raw lines | allowlisted stubs | classification | evidence summary |
|-----|-----------|-------------------|----------------|------------------|
| 61a | 64 | 0 (drained in PR #73) | B: mixed. Lines 46-64 genuine (repaired); lines 1-45 fabricated | Continuous English essay (essential vs non-essential services, then Torah study replacing the Temple service) ignoring the Hebrew line by line. Hebrew anchors Shevuot 7b (L10) and Shevuot 13b (L33) appear NOWHERE in the English |
| 67b | 69 | 11 (L59-69) | S: shifted-compressed, not fabricated | Genuine translation of the whole daf compressed into EN lines 1-58; drift grows from +2 (L22) to about +13; EN L58 translates Hebrew L69. Anchors at HE L61/63/67/68 found at offsets -13/-15/-12/-13 |
| 68a | 62 | 13 (L50-62) | S: shifted-compressed, not fabricated | Full translation compressed into EN 1-49; EN L48-49 answer Hebrew L61-62 ("Where did they burn them? To the north"). Anchors at HE L34/35/55 found at offsets -9/-9/-10 |
| 68b | 60 | 9 (L52-60) | S: shifted-compressed, not fabricated | Full translation compressed into EN 1-51; EN L30 is "Hadran alach shnei se'irei" (HE L35); EN L51 covers HE L59-60. Anchor at HE L56 (Psalms 50) found at offset -11 |
| 70a | 55 | 3 (L53-55) | S: shifted-compressed, not fabricated | Full translation compressed into EN 1-52; drift peaks around +9 mid-daf (EN L28 covers HE L37); EN L52 covers HE L55. Anchor at HE L28 (Numbers 29) found at offset -7 |
| 71b | 61 | 17 (L45-61) | S: shifted-compressed, not fabricated | Most extreme case: full translation compressed into EN 1-44; EN L44 ("Kalil - entirely") translates HE L61, the daf's final word (+17 peak drift). Anchor at HE L49 (Zevachim 15b) found at offset -14 |

Class key as used here: A only documented stubs bad; B mixed, stubs
plus look-alike fabricated non-stub lines; C mostly fabricated;
D uncertain; S (new, needed by the evidence) shifted-compressed:
the non-stub English is a genuine translation of the daf but line
alignment drifts progressively ahead of the Hebrew, and the tail is
padded with stubs whose Hebrew content is already translated earlier
in the daf.

## The two failure modes

1. Fabrication (61a lines 1-45). The English reads as one continuous
   standalone essay about the daf's theme, split across vilna lines.
   Anchor signature: Hebrew citations appear nowhere in the English
   (miss), and cross-line lexical overlap with the Hebrew is near zero.
   70 percent of the daf needs reconstruction from the raw Hebrew.

2. Shift-compression (67b, 68a, 68b, 70a, 71b). The English is a
   faithful, complete translation of the daf's entire Rashi, but it
   consumes Hebrew content faster than one line per line, ends 3 to 17
   lines early, and the remainder was padded with
   "Rashi line N: continuation" stubs, which were then allowlisted as
   stub_continuation. Anchor signature: anchors found, but at large
   negative offsets that grow monotonically down the daf.

## Operational consequence: stub-only repair is unsafe on all five shifted daf

The allowlisted "stubs" on 67b/68a/68b/70a/71b are not missing
translations. The Hebrew content of those tail lines is already
translated, sitting earlier in the daf. A Haiku stub-only repair pass
(the 61a playbook) would:

- add fresh translations of the tail Hebrew, duplicating content that
  already exists a few lines up (paraphrased duplicates, which the
  repetition gate does not catch);
- leave the middle third of each daf misaligned by 5 to 17 lines;
- drain the stub allowlist entries, making the daf look repaired while
  it is actually worse.

Haiku MUST NOT run rashi-repair on 67b, 68a, 68b, 70a, or 71b. These
five daf need a full-daf realignment pass (redistribute the existing
good translation across the correct vilna lines, translating only the
genuinely uncovered remainder), which is Hebrew-alignment judgment and
therefore Fable/Sonnet work with Fable review. 61a lines 1-45 need a
full reconstruction pass (translate from raw Hebrew; nothing existing
is salvageable), also Fable/Sonnet.

## Why the current gates missed both modes

- validate:rashi:content:yoma checks patterns (placeholders, scaffold,
  filler strings, dashes, counts). Fluent fabricated prose and shifted
  genuine prose both pass.
- validate:rashi:dupes:yoma catches near-identical repeats; the shift
  duplicates would be paraphrases and the fabricated essay never
  repeats itself.
- audit:rashi:semantic:yoma (advisory) scored 61a and 68a/68b at 0 and
  the rest at 1-3 with zero shift candidates, for four concrete
  reasons found in this audit:
  1. Its citation regex character class omits the colon, so every
     amud-b citation such as `(דף נז:)` is invisible.
  2. Tractate names usually sit outside the parentheses
     (`דזבחים (דף טו:)`), and the audit only matches names inside them.
  3. Its neighbor window is 4 lines; the real drifts here are 5 to 17.
  4. It has no aggregate drift statistic; systematic monotonic drift is
     the actual signature of a shifted daf, invisible to per-line flags.

## Proposed pipeline and tooling changes (design, not implemented here)

1. Detector fixes in audit_rashi_semantic.py:
   colon-tolerant citation regex; tractate-name adjacency matching (a
   name within about 25 characters before a daf citation); citations
   split across vilna lines. These three fixes were prototyped during
   this audit and are what produced the offset evidence above.
2. Drift profile per daf: widen the anchor search window to about 25,
   report signed offsets, and classify a daf SHIFTED when two or more
   anchors sit at offset magnitude greater than 2 with a consistent
   sign, and FABRICATION-SUSPECT when the non-allowlisted region's
   anchor miss rate is high (61a lines 1-45: 2 of 2 anchors missing).
3. Preflight block on stub-only repair: rashi-repair preflight runs the
   drift profile on each target daf and FAILS when the daf classifies
   SHIFTED or FABRICATION-SUSPECT, with the message that a realignment
   or reconstruction manifest is required. Overridable only by a
   Fable-issued authorization flag on the manifest.
4. Packet-level warning: the packet generator embeds the target daf's
   drift-profile summary so any worker (and any reviewer) sees the
   classification inline before editing.
5. Registry: add a rashi-realignment task type (fableReviewRequired
   true, model fable) for the five shifted daf, distinct from
   rashi-repair and rashi-reconstruction; assign 67b/68a/68b/70a/71b
   to it and 61a lines 1-45 to rashi-reconstruction.
6. Debt-list wording: the SOP and backlog entry "61a/67b-71b stubs"
   should be restated, because on five of the six daf the stubs are a
   symptom of shift-compression, not the defect itself, and draining
   them by stub repair is the exact wrong move.

Items 1-5 belong in a docs-tooling PR (validator plus registry edits,
Fable-owned). Item 6 is recorded in the backlog note accompanying this
report.

## Scope confirmation

Read-only. No learning JSON, allowlist, generated file, validator,
registry, or workflow was modified. The in-range daf outside the named
target set (61b, 62a-67a, 69a, 69b, 70b, 71a) were not audited. 41a,
47a, 77a-88a, and nekudot were not touched. No repair was started on
any daf.
