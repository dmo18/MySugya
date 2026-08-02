# Rashi translation-quality campaign, Step 4: pilot cohort methodology

This document explains how `docs/reports/data/rashi-pilot-cohort.json` was
selected and how `docs/reports/data/rashi-pilot-review-packets.json` was
assembled from it. It is the companion reference for
`modules/yoma/scripts/select_rashi_pilot_cohort.py` and
`modules/yoma/scripts/generate_rashi_pilot_packets.py`.

## What this is not

Neither script performs or automates semantic review. They decide WHICH
8,854-corpus entries a human reviewer looks at (the cohort selector) and
assemble the CONTEXT a reviewer needs to look at them (the packet
generator). No script here reads Hebrew meaning, compares it to English, or
assigns a disposition. That is Step 4's actual review work, done separately
against the frozen packets.

## Selection method

Deterministic greedy quota fill, no randomness:

1. For each of 16 requirements drawn from the campaign's governing
   directive, build a candidate pool of entry ids that satisfy it.
2. Order every pool by round-robin across daf (not flat file order) so a
   single dense daf cannot dominate a requirement's quota. An earlier draft
   of this script sorted pools by plain file order and produced a cohort
   spanning only 12 daf, with 56 of 200 entries from daf 2a alone - that
   version is not what shipped. The round-robin traversal (one candidate
   per daf per pass, cycling) produced a cohort spanning 110 daf with no
   daf contributing more than 5 entries, which is the actual selection
   below.
3. Walk the 16 requirements in priority order (historical provenance
   first, then risk tiers, then the "also require representation" list).
   For each, keep adding the next not-yet-selected entry from its pool
   until the requirement's minimum is met by the entries selected SO FAR
   (across all requirements, not just this one) - this is what lets a
   single entry count toward several requirements at once, exactly as the
   governing directive permits ("overlap between historical and risk
   strata is permitted").
4. Top up (unconditionally, not just as a fallback) to at least 200 unique
   entries and at least 10 distinct daf if quota-filling left either
   short. In practice it did not: quota-filling alone reached the 200-entry
   floor exactly, and 110 daf comfortably clears the 10-daf floor.

## Requirements and results (this run)

| Requirement | Minimum | Actual |
|---|---|---|
| historical reconstruction/realignment daf | 20 | 20 |
| high risk (riskScore >= 9) | 70 | 70 |
| medium risk (2 <= riskScore <= 8) | 50 | 50 |
| zero risk (riskScore == 0) | 40 | 40 |
| beginning of Yoma (first third by daf order) | 8 | 100 |
| middle of Yoma | 8 | 24 |
| end of Yoma | 8 | 36 |
| short gloss (<=6 English words) | 8 | 8 |
| long explanation (>=30 English words) | 8 | 9 |
| sacrificial terminology | 10 | 13 |
| priesthood or Temple terminology | 10 | 17 |
| purity terminology | 8 | 11 |
| narrative/contextual explanation | 10 | 17 |
| multiple linked Gemara lines | 10 | 16 |
| terminology-variance signal | 8 | 8 |
| no automatic warning (riskScore 0, zero riskSignals) | 8 | 43 |

Totals: **200 unique entries, 110 daf, 7 of 8 perakim** (perek 8, daf 73b-88a,
is not represented in this run; the requirement is >=3 perakim, which is
comfortably met, and Step 5's full-corpus strategy will still cover it).

The "beginning of Yoma" count (100) is high relative to its minimum because
the historical-reconstruction/high-risk/medium-risk pools that fill first
happen to include a large share of early-daf entries once round-robin
spreads them out - this is a byproduct of where those strata's entries
actually live in the corpus, not a selection bias toward easy or early
material. See "duplicate-cluster and terminology-variance detail" below for
why `terminology_variance_signal` sits exactly at its floor (8): the corpus
genuinely has few entries where a registry term appears without any
acceptable rendering, since Step 3's registry was built to exclude terms
that vary for legitimate reasons in the first place.

## Duplicate-cluster note

The governing directive asks for representation from "entries with
duplicate or terminology-variance signals." Step 2's duplicate-cluster
detector found **zero** duplicate clusters corpus-wide (confirmed again as
part of this baseline reconciliation - `rashi-duplicate-clusters.json`
still reports `clusterCount: 0`). There is nothing to sample from that
pool. The `terminology_variance_signal` requirement covers the other half
of that line item and is satisfied at its floor (8 entries, all drawn from
the Step 3 registry's near-invariant, contextual, and do-not-enforce
tiers - including `כהן גדול` cases, which Step 3 already expects to show
wide, legitimate variation).

## Review packets

For every frozen cohort entry, `generate_rashi_pilot_packets.py` assembles:

- the entry's Hebrew and current English, copied verbatim from the frozen
  cohort record (a test asserts byte-for-byte match, so packet generation
  cannot silently truncate or alter what a reviewer sees);
- every linked Gemara line's Hebrew, English (William Davidson Edition),
  and literal (`en_lit`) rendering;
- up to 2 Gemara lines of context immediately before and after the linked
  line(s), so ellipsis and pronoun antecedents in the Rashi can be
  resolved without a reviewer having to separately open the full daf;
- up to 2 neighboring Rashi entries on either side, for cases where the
  same Rashi comment continues across nominal entry boundaries;
- the entry's Step 2 risk score and risk signals;
- which style-guide sections apply, derived from which selection strata
  the entry belongs to (e.g. an entry selected for `sacrificial_terminology`
  gets pointed at the style guide's "Sacrificial terminology" section);
- any Step 3 terminology-registry term whose Hebrew appears in the entry;
- the entry's Step 1 historical-provenance classification;
- a blank review record (`disposition`, `defectTags`, `evidence`,
  `finalEnglish`, `secondPass`, `structuralStop`, `repairPR`,
  `finalVerificationSHA` - all null/empty) for the actual review pass to
  fill in.

## Reproducing this cohort

```bash
cd modules/yoma
python3 scripts/select_rashi_pilot_cohort.py
python3 scripts/generate_rashi_pilot_packets.py
```

Both are read-only against the corpus and deterministic: re-running them
against an unchanged corpus reproduces byte-identical output (asserted by
`test_select_rashi_pilot_cohort.py` and
`test_generate_rashi_pilot_packets.py`). If the corpus's risk report or
terminology registry changes in a later step, re-running would select a
different cohort - which is why the cohort is frozen as a committed JSON
file rather than regenerated on demand once review begins.
