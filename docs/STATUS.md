# Status

Updated: 2026-11-19. Version: 15.603.

## Done

- Takeover audit. See `docs/TAKEOVER.md`.
- Safety (PR #669, merged): the Cloudways publish runs tests first
  and one at a time; ESLint 9.39.5 added (`npm run lint`).
- Source text check against live Sefaria, all 173 daf: 5 of 7 gates
  pass, two single-line mismatches (see Known issues).
- Daf 2a re-validated from the Hebrew (PR #670, merged). All 6
  topics carry fresh `rv3-` certificates. The old certificates on 2a
  were not reliable: the fresh first pass found 61 defects, 32 of
  them wrong meaning.
- Owner standard recorded:
  `docs/reports/semantic-nothing-beyond-the-page.md`.

## In progress

- Paused by owner decision after 2a, for a cost report.

## Next (needs owner decision)

- Daf 2b. A fresh first pass is already done and found all 5 topics
  need repair (54 defects). Findings are saved, not applied:
  `docs/reports/data/semantic-yoma-2b-rv3-first-pass-findings.json`.
- Then 3a onward. 89 other certificates predate this run and are
  not trusted; 397 topics have no certificate.

## Measured cost of daf 2a (delegated tokens)

| Step | Tokens |
|---|---|
| First pass and all repairs (1 context) | 335k |
| Independent second passes (8 rounds) | 963k |
| Final whole-record audits | 239k |
| Total for 2a | 1,537k |

Run total including safety work: about 1,712k, plus the 2b first
pass, whose usage was lost in a container restart.

Why 2a cost so much: the acceptance standard was only fixed at
round 5. Rounds 1 to 4 chased reviewer-to-reviewer differences.
After the checklist existed, each review round found less and the
record converged.

## Process lessons for the next daf

1. Give the checklist to the first-pass reviewer and repairer from
   the start, so the first repair already meets it.
2. Sweep for out-of-range content per topic (item 9) before any
   second pass; the final audit is the strictest check of it.
3. Only the Hebrew Rashi counts as Rashi.
4. Re-review only the topics whose own fields changed. A change to
   the shared summary or glossary sends all topics back, so get the
   daf-level fields right first.
5. A content pull request may contain only the daf record, generated
   data, registry and manifest. Evidence files go in a separate
   docs pull request with a docs-tooling manifest.
6. Workflow or tooling edits need a `.worker-manifest.json` of type
   docs-tooling, and new files must sit in an allowed folder.
7. After a version bump, run
   `cd modules/yoma && python3 scripts/generate_rashi_docs.py`.

## Decisions made

| Decision | Reason |
|---|---|
| Work on a branch and merge by pull request | Merging to `main` publishes the live site |
| `githooks/pre-commit` not enabled | It came with the repo; owner has not approved it. Its checks are run by hand |
| Lint config lives in `scripts/` | Project pipeline does not allow new root files |
| 2a topic 6 keeps its line range (ends at line 38) | 136 daf leave trailing lines unowned; a one-daf change would break that convention |
| Nothing beyond the page | Owner decision, 2026-11-19 |
| Up to 4 repair rounds per daf while improving | Owner decision, 2026-11-19 |

## Known issues

See "Known issues and risks" in `docs/TAKEOVER.md`.

Source check against live Sefaria on 2026-11-19:

- 24b Hebrew: one line differs at character 230 (a comma). The
  maintainer guide calls this a known harmless difference. Not
  trusted until re-checked when the run reaches 24b.
- 54b English: one line differs from Sefaria (89% overlap). New
  finding. Raw source is never edited without owner approval.
- 2a English Rashi helper text (protected layer) overstates the
  Hebrew Rashi in places ("signals to all", "formally"). Reported
  by a reviewer; not changed.
- `modules/yoma/source_store.js` records 2a topic 2 as ending at
  Vilna line 13; the learning record says 14 and the Hebrew supports
  14. Reported by a reviewer; not changed.
- `scripts/rabbi_cron_trigger.js` is excluded from lint because it
  is a function body, not a standalone file.
- PR #663 (old 18b attempt) is still open and untouched.

## Open security findings

- Critical or high: none.
- Resolved: Cloudways publish now runs tests first and cannot
  overlap with another publish run. Its force push remains.
- Info: ESLint 9 is marked deprecated by npm. Plan a move to
  ESLint 10 later.
