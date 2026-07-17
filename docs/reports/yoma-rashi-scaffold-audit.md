# Yoma Rashi scaffold-fabrication audit

Forensic inventory of the scaffold-fabrication defect family discovered by
the corpus closure audit at VERSION 15.143 (main
`0ce607194a3268a7f291229dfc136f978ebc2040`) and re-verified line by line
against current repository content before any remediation. This report and
the machine-generated debt baseline
(`modules/yoma/scripts/baselines/rashi_scaffold_debt.json`) supersede all
earlier "batch resolved" narratives in `docs/rashi-audit-backlog.md` for the
daf listed here.

## The defect

A family of `rashiTranslations.en` values that narrate or placeholder the
line instead of translating its own raw Hebrew:

1. Scaffold narration: `Rashi: opens - ...`, `Rashi: continues - ...`,
   `Rashi: concludes '...'`, including intermediate-text, capitalization,
   punctuation, bare-verb (`Rashi continues: ...`), and synonym variants
   (`closes`, `completes`).
2. Scaffold plus editorial bracket guessing: scaffold lines padded with
   invented completions such as `[the Gemara]`, `[that the statute
   applies]`, `[for]` that have no counterpart in the Hebrew. Verified
   wrong-content example: 42a vilnaLine 1 renders "goat, [the weight is]
   two selas and that suffices" where the Hebrew says "of the goat -
   because it requires division".
3. Line-number placeholders: `Rashi on line 14: ...`,
   `[Rashi commentary on line 100]: ...`.
4. Hebrew passthrough: the en field carries the raw Hebrew itself
   (40%+ Hebrew letters), i.e. the line was never translated (72a-76b).

None of this matched `validate_rashi_content.py`'s literal placeholder
patterns, which is how it survived every prior mechanical gate.

## Detector methodology

`modules/yoma/scripts/audit_rashi_scaffold.py` (single source of truth;
regression-tested by `modules/yoma/scripts/test_scaffold_audit.py`):

| Rule | Trigger |
| --- | --- |
| `scaffold-prefix` | en begins `Rashi[:,]? (opens\|continues\|concludes\|closes\|completes\|begins\|resumes)` (case-insensitive, anchored) |
| `scaffold-bracket-guess` | a `scaffold-prefix` line that also carries 2+ bracketed insertions |
| `line-number-scaffold` | en begins `Rashi on line N` or `[Rashi commentary on line N]` |
| `hebrew-passthrough` | 40%+ of the en field's letters are Hebrew script |

All prefix rules are anchored at the start of the field: ordinary
mid-sentence English uses of "opens", "continues", or "concludes", and
legitimate bracketed citations or clarifications in direct translations,
never match (covered by explicit negative tests).

## Verified totals (current main, pre-remediation)

- Contaminated lines: **3,838** (the closure audit's 3,028 undercounted:
  its regex required a hyphen immediately after the verb and missed the
  intermediate-text, `closes`/`completes`, bare-verb, line-number, and
  passthrough variants)
- Affected daf: **86** of 173 (the closure audit reported 69; newly
  identified: 2b, 3a, 3b, 7b, 41b at full severity, 44a-46a stragglers,
  and the untranslated 72a-76b block)
- Classification: **602** class A (definite fabrication: bracket-guess,
  passthrough, line-number placeholder) and **3,236** class B (scaffold
  framing whose content may partly track the Hebrew but is not the
  required direct translation)

## False-positive analysis and known-clean controls

Zero hits, verified by regression test on every run, across:

- 50a-52b (direct-translation region)
- previously repaired direct-translation daf 61a, 67b, 68a, 68b, 70a, 71b
- 77a-88a (the completed 77a-79a and 79b-88a reconstruction campaigns)

Natural-language negative cases (mid-sentence "continues", "opens",
bracketed citations inside genuine translations, "Rashi holds that ...")
are covered by unit tests and do not match.

## Debt ratchet

The verified inventory is locked in
`modules/yoma/scripts/baselines/rashi_scaffold_debt.json` (daf, vilnaLine,
rule, hash of the exact contaminated en text). Gate semantics:

- any hit not in the baseline fails CI (no new scaffold text, ever);
- any baselined line whose text changes but still hits fails CI (an entry
  covers only the exact text it was generated from);
- the baseline only shrinks (`--update-baseline` retires entries whose
  lines no longer hit and refuses everything else); growth requires
  explicit operator authorization and never happens in worker PRs;
- reconstruction/realignment manifests snapshot their target's debt and
  worker verify/review fail unless the target ends with zero hits and
  zero remaining baseline entries, with unrelated entries byte-identical;
- `rashi_content_allowlist.json` stays at zero entries throughout.

## Remediation order

One daf per PR, reconstruction unless a fresh diagnosis proves a smaller
task type, draining the daf's baseline entries in the same PR:

1. Batch 1 (operator-ordered): 10a, 10b, 11a, 11b, 12a
2. Next recommended batch: 12b, 13a, 13b, 14a, 14b
3. Continue in daf order through 49b, then the 72a-76b passthrough block
   (class A throughout, including untranslated lines and at least one
   verified neighbor-shifted en at 75a vilnaLine 5)
4. 2b/3a/3b/7b/45b/46a stragglers may use rashi-repair only after fresh
   whole-daf semantic verification

Severity notes for planning: 41b-43b carry the heaviest class A density
(41b 48A, 42b 42A, 43a 64A, 43b 56A); 72a-76b is entirely class A.
