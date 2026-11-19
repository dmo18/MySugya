# Nothing beyond the page

Owner decision, 2026-11-19. This is the acceptance standard for every
learner-facing field in a Yoma learning record. It applies to authors,
repairers, second-pass reviewers, and final auditors alike, so that all
of them judge by the same checkable rule.

## The rule

Every sentence in every semantic field may say only what the sugya's own
lines say, or what Rashi on those lines says. This includes teaching
fields: takeaways, aha moments, memory anchors, core tension, core move,
reasoning-pattern notes, learning blockers, misconceptions, quiz answers,
hints, prerequisites, and visual descriptions. Daf-level fields (summary,
glossary) may rest on any line of the same daf, and on nothing else.

## Checklist (each item is a defect when violated)

1. Added circumstance. A fact, setting, motive, or adverb the lines do
   not state (for example "publicly", "private", "final speech").
2. Unstated reason. A "because" or purpose the lines do not give, or a
   reason the page gives for a different clause.
3. Generalized rule. A single case restated as a general principle, a
   halachic rule, or "how the Talmud works". A takeaway must restate what
   this sugya says, not what it teaches about other cases.
4. Decided dispute. Presenting one side of an undecided dispute as the
   ruling. `finalRuling` stays empty unless the lines state a decision.
5. Evaluative label. "Classic", "famous", "fundamental", "methodological
   dispute", "paradigm", and similar labels the page does not use.
6. Wrong layer. Attributing to the Mishnah what the Gemara says, to the
   Gemara what Rashi says, or to a speaker what the anonymous Gemara says.
   Rashi-derived detail must be worded as Rashi's explanation.
7. Loose quotation. A verse or statement quoted or paraphrased differently
   from the wording on the page.
8. Wrong referent. A pronoun or possessive that points at the wrong
   subject (for example "its service" for the parah's acts).
9. Out of range. A claim resting on lines outside the sugya's own
   lineRange, on a later sugya, or on another daf. "The discussion
   continues on the next amud" is allowed; its outcome is not.
10. Settled too early. Words like "proves", "must", "establishes" for a
    derivation that is still under challenge within the daf.
11. Mismatched type. A metadata value (an argumentFlow step `type`, a
    takeaway `type`, a `topicTags` slug) that describes something the
    step or sugya does not do or say.
12. Unsupported metadata. A `role` or `priority` on a visual element that
    cannot be justified from the source is removed, not invented.

## What is not a defect

- Plain connective wording that adds no claim.
- A faithful translation choice among accepted renderings, used
  consistently within the record.
- The accepted coordinate convention that the final raw line of a daf
  may be owned by no sugya's lineRange.
- Style preference alone.

A reviewer who rejects a field must name the checklist item it violates.
An observation that fits no item is an advisory and does not reject.
