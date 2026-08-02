# Yoma Rashi translation style guide

Step 3 of the Rashi translation-quality campaign (see
`docs/reports/rashi-translation-quality-plan.md` for Steps 1-2). This guide is
descriptive before it is prescriptive: every convention below is drawn from
real, low-risk (`riskScore == 0` in `docs/reports/data/rashi-translation-risk-report.json`)
entries already in the corpus, not invented. Its purpose is to give Step 4-6
reviewers a shared, evidence-backed standard so that "verified" and "repaired"
dispositions are applied consistently across reviewers and across the corpus,
not to relitigate translations that already match it.

This guide governs English wording only. It never touches Hebrew text, entry
ids, daf assignment, `linkedGemaraLineIds`, or any other immutable-baseline
field listed in the campaign's governing directive.

## How to use this guide

- When an entry already matches the conventions below, that is evidence
  toward `VERIFIED`, not a reason to rewrite it into different but equally
  correct phrasing. Do not "improve" correct translations to match a personal
  preference not documented here.
- When an entry deviates from a convention below **and the deviation makes
  the translation wrong, confusing, or inconsistent with the rest of the
  corpus**, that is a `MINOR_EDIT` (style-only fix) or `STYLE_ONLY` defect
  tag, never a `WRONG_MEANING` tag on its own.
- Style conventions are advisory guidance for reviewers, not new validator
  rules. No CI gate enforces prose style. See "Automated enforcement" at the
  end of this document for what is and is not safe to check by machine.

## Names and titles

Amoraim and Tannaim are referred to by their Hebrew name transliterated, not
translated or anglicized: "Rabbi Yehudah," "Rabbi Yochanan," "Rav Natan,"
never "Judah" or "John." First reference and subsequent references use the
same form; the corpus does not abbreviate to surname-only or first-name-only
after first mention.

## Rabbi / Rav conventions

The corpus preserves the Hebrew title distinction rather than flattening
both to "Rabbi":

- **Rabbi** - the Mishnaic-era/Tannaitic title (e.g. "Rabbi Yehudah,"
  "Rabbi Yishmael").
- **Rav** - the Babylonian Amoraic title (e.g. "Rav Natan," "Rav Chisda").

Do not normalize one to the other. If a name's title in the `en` field
conflicts with the standard title for that sage, that is a
`WRONG_TECHNICAL_TERM` candidate for reviewer judgment, not an automatic
rewrite - some sages are legitimately cited both ways across sources.

## Temple terminology

`בית המקדש` renders as **Temple** (capitalized, referring to the Jerusalem
Temple), 100% stable across 8 corpus occurrences. `מזבח` renders as
**altar**, 95% stable across 262 occurrences; the exceptions are cases where
a more specific term (e.g. "the copper altar," "the golden altar") is
correctly used because Rashi is distinguishing between the two altars, not a
translation gap.

## Sacrificial terminology

The corpus uses hyphenated compound terms rather than looser phrasing:
**sin-offering** (`חטאת`), **burnt-offering** (`עולה`), **guilt-offering**
(`אשם`), and the generic **offering** (`קרבן`) when the specific type is not
the point of the sentence or has already been established. `חטאת` and `עולה`
are only 68% and 53% stable respectively because Rashi frequently uses a
pronoun or "it" once the specific offering type is already named earlier in
the same entry - that is correct English, not a defect. Do not force every
occurrence of a sacrificial noun into its full compound form if the
antecedent is already clear.

## Purity terminology

`טומאה` renders as **impurity** (93% stable), `טהרה` as **purity**. Adjectival
forms follow the same root: "ritually impure," "impure," "pure." Avoid
"unclean"/"clean" - not attested anywhere in the low-risk sample and inserts
a register the rest of the corpus does not use.

## Priesthood terminology

`כהן` renders as **kohen** (lowercase, transliterated, not "priest") when
referring to an ordinary priest; `כהן גדול` is the one term in this guide
explicitly **not** force-mapped to a single English rendering - see
`docs/reports/data/rashi-terminology-registry.json`'s `do_not_enforce` tier.
Only 13% of the 60 sampled occurrences use the literal "Kohen Gadol" string;
the rest correctly use "the High Priest," a pronoun, or an implicit
antecedent. A reviewer should judge each occurrence on whether the referent
is clear in context, not on whether it matches a fixed string.

## Measurements

Talmudic units of measure are transliterated, not converted to modern units:
**cubit** (`אמה`, 74% stable - the exceptions are plural/construct-form
sentences where "cubits" or an implicit unit already carries the meaning),
along with (where they occur) se'ah, log, and similar units left in their
Hebrew/transliterated form rather than translated to liters or converted to
an approximate modern quantity. Rashi's own numeric reasoning depends on the
named unit; converting it would misrepresent the argument, not merely
restyle it.

## Legal verbs

The corpus's normative vocabulary is consistent: **obligated**, **exempt**,
**permitted**, **forbidden** (or **prohibited**), **liable**. These map
Talmudic legal categories (chayav, patur, mutar, assur) and should not be
swapped for looser synonyms ("required to," "allowed to," "banned from")
that blur the technical distinction between, e.g., an exemption and a
prohibition.

## Logical connectors

Rashi's argumentative connectives render as plain, standard English:
**Therefore**, **However**, **Since**, **Although**, **Rather**. The corpus
does not use archaic or overly formal connectors ("Hence," "Whence," "Ergo").
Capitalize a connector only when it begins a new sentence; mid-sentence use
is lowercase ("...therefore this seventh was the seventh of the month").

## Anonymous pronouns

Where Rashi's Hebrew itself is impersonal or elliptical (a very common
construction), the corpus correctly keeps the English impersonal rather than
inventing a named subject: "they designate," "we understand," "one who
comes to serve." Do not add a specific subject that is not in the Hebrew;
that is `INVENTED_TEXT`, not a style improvement.

## Elliptical Hebrew and dibbur hamatchil fragments

Rashi routinely comments on a fragment of the Gemara/Mishnah text (the
"dibbur hamatchil," the lemma being glossed) before explaining it. The
corpus's consistent pattern:

```
"<quoted Gemara/Mishnah fragment>" - <Rashi's comment on it>
```

for example (`rashi-yoma-002a-001`):

> "Seven days before Yom Kippur they separate the Kohen Gadol" - because the
> entire Yom Kippur service depends on him...

The quoted fragment is followed by a hyphen-dash and the comment, with no
additional framing language ("this means," "referring to") unless Rashi's
own Hebrew supplies one. A dash with nothing following it is not itself a
defect if the fragment is a complete lemma-quote-boundary marker; it only
becomes a `TRUNCATED` defect when the comment that should follow the dash is
genuinely missing (see `docs/reports/rashi-translation-risk-audit.md`'s
truncation-detector correction for the full account of this distinction).

## Quotations from Gemara vs. quotations from Scripture

The corpus distinguishes the two by quotation mark style, not by added
framing text:

- **Double quotes** for a verse or Mishnah excerpt being explained as the
  dibbur hamatchil, e.g. `"Seven days before Yom Kippur they separate..."`.
- **Single quotes** for the Gemara's own phrase being glossed inline, e.g.
  `'And make for yourself' - like 'make yourself two silver trumpets'
  [Numbers 10:2]...`.

When the Gemara itself is being introduced narratively rather than quoted
verbatim, the corpus uses plain phrasing such as "the Gemara states," "the
Gemara asks," "the Gemara answers," "the Rabbis object" - not a fixed
formula, but always third person and present tense.

## Scriptural quotations

A biblical citation is followed by a bracketed verse reference when Rashi's
comment depends on the reader knowing exactly where it is from, e.g. `'make
yourself two silver trumpets' [Numbers 10:2]`. The bracket contains only the
reference, never added commentary - added commentary inside brackets is the
separate "parenthetical clarification" convention below.

## Hebrew or Aramaic terms retained in transliteration

A transliterated term follows immediately after its English gloss, in
parentheses, lowercase, no italics markup (the renderer does not support
inline italics): `"Vessels of dung" (klei gelalin) - implements made from
dried cattle dung...`, `'As it were' (kivyachol) - I have heard...`. Do not
transliterate a term that already has a stable, well-established English
equivalent in this guide's terminology registry (e.g. do not write "(mizbe'ach)"
next to "altar" - the transliteration is only added where the term itself,
not just its referent, is part of what Rashi is explaining).

## Parenthetical clarification

Square brackets `[...]`, not parentheses, mark an editorial supply the
translator is adding that is not literally in Rashi's Hebrew but is needed
for the English to parse - a missing subject, an implied word, or a note
that a phrase is elliptical: `"But say [rather]" - the Gemara introduces an
objection...`, `the work [of building the Ark] is called by their own name
[the verse credits the people themselves]`. Parentheses `(...)` are reserved
for the transliteration convention above and for verse references. Mixing
the two (using parentheses for an editorial supply, or brackets for a
transliteration) is a `PUNCTUATION`-tag candidate, not necessarily a meaning
error.

## Punctuation

- The dibbur-hamatchil dash (` - `) uses a spaced hyphen, not an em-dash or
  en-dash. Per `CLAUDE.md`'s universal rule, no em-dash or en-dash appears
  anywhere in project-authored `en` text; this applies to Rashi translations
  as much as to docs and commit messages.
- Terminal punctuation on a dibbur-hamatchil quote boundary (ending in a
  dash or comma before the next quote begins) is a corpus convention, not an
  error - see the truncation-detector note above.
- Bracketed verse references use `[Book Chapter:Verse]` with a colon between
  chapter and verse, no additional punctuation inside the brackets.

## Capitalization

Capitalize: Torah, Sages (as a collective proper noun for the rabbinic body,
not the adjective "sage"), Temple, Gemara, Mishnah, Scripture, named
festivals (Yom Kippur), named individuals and their titles (Rabbi Yehudah).
Lowercase: generic nouns even when transliterated (kohen, cubit, baraita,
tanna as a common noun), legal-verb vocabulary, connectors.

## Singular/plural consistency

"Sages" is consistently plural when referring to the collective rabbinic
voice ("the Sages hold," "the Sages imposed"), matching the Hebrew `חכמים`
which is itself plural. Do not render it as a singular collective ("the Sage
holds") - that changes the meaning from "the rabbis as a body" to an
unspecified individual.

## Recurring Rashi formulas

Some Rashi phrasings recur nearly verbatim across many entries because the
underlying Hebrew formula recurs (e.g. citation-introduction phrases, the
dibbur-hamatchil dash pattern itself, "meaning..." glosses that restate a
quoted phrase in plain language). A recurring formula rendered consistently
across entries is expected and correct - it is not evidence of the
`DUPLICATED` or template-fabrication defect tags, which apply to *unrelated*
Hebrew text sharing suspiciously identical English (see
`docs/reports/rashi-translation-risk-audit.md`'s duplicate-cluster detector).
The distinction a reviewer must make is: same Hebrew formula → same English
formula (fine); different Hebrew → identical English (defect).

## When not to expand the text

Rashi is often terse by design - a two-word gloss, a single clarifying noun,
a bare cross-reference. The corpus's correct short answers (e.g. glosses
that are just a word or short phrase) should not be padded into a full
sentence with invented explanatory content the Hebrew does not contain. Only
expand where English syntax genuinely requires a word Hebrew omits (a
copula, an implied subject) - and mark such supplied words with square
brackets per the parenthetical-clarification convention above whenever the
supply is substantive rather than purely grammatical glue.

## Terminology registry

`docs/reports/data/rashi-terminology-registry.json` records the frequency
evidence behind the terms above, split into three tiers:

- **near_invariant** (>=90% stable in the corpus today): safe to flag,
  advisory-only, when a low-risk entry contains the Hebrew term but none of
  its acceptable English renderings.
- **contextual** (roughly 50-90% stable): document the dominant rendering
  as guidance for new work; never build an automated check against this
  tier, since the minority renderings are legitimate.
- **do_not_enforce**: terms (currently just `כהן גדול`) where the dominant
  pattern in the corpus is deliberate variation, not drift, and no single
  canonical string should ever be enforced.

## Automated enforcement

Per the campaign's explicit constraint, no terminology or style check in
this guide becomes a hard validator failure. `near_invariant` terms may
support a future advisory-only, always-exit-0 reporter (matching the
existing `audit_rashi_semantic.py --report` / `audit_schema_semantics.py
--report` convention) if Step 4-6 review finds real value in it; this guide
does not itself ship one, since the campaign's Step 3 scope is the guide and
registry, not new gate-adjacent tooling. Nothing in this document changes
`validate_rashi_content.py`, `validate_rashi.py`, or any other existing
validator's pass/fail behavior.
