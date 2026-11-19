# Status

Updated: 2026-11-19. Version: 15.601.

## Done

- Takeover audit. See `docs/TAKEOVER.md`.
- Task 1: Cloudways publish now runs tests first.
- Task 2: ESLint 9.39.5 added (`npm run lint`, 0 errors, 51
  unused-variable warnings, no real bugs found).
- Task 3: source gates run against live Sefaria for all 173 daf.
  5 of 7 pass. Two single-line mismatches, see Known issues.
- Daf 2a first pass (fresh, Opus): all 6 topics REPAIR_REQUIRED,
  60 defects (32 wrong meaning, 15 wrong placement, 6 contract,
  7 wording). The old certificates on 2a were not reliable.

## In progress

- Daf 2a repair, then independent second pass and final audit.

## Next

- Daf 2b, 3a, 3b, 4a, 4b, then cost report before the rest.

## Decisions made

| Decision | Reason |
|---|---|
| Work on a branch and merge by pull request | Merging to `main` publishes the live site |
| Did not enable `githooks/pre-commit` yet | It came with the repo; owner approves first |
| Lint config lives in `scripts/` | Project pipeline does not allow new root files |
| 2a topic 6 keeps its line range (ends at line 38) | 136 daf leave trailing lines unowned; a one-daf change would break that convention. Claims resting on line 39 are removed instead |

## Known issues

See "Known issues and risks" in `docs/TAKEOVER.md`.

Source check against live Sefaria on 2026-11-19:

- 24b Hebrew: one line differs at character 230 (a comma). The
  maintainer guide calls this a known harmless difference. Not
  trusted until re-checked when the run reaches 24b.
- 54b English: one line differs from Sefaria (89% overlap). New
  finding. To be resolved when the run reaches 54b. Raw source is
  never edited without owner approval.
- `scripts/rabbi_cron_trigger.js` is excluded from lint because it
  is a function body, not a standalone file.

## Open security findings

- Critical or high: none found.
- Resolved: Cloudways publish now runs tests first and cannot
  overlap with another publish run. Its force push remains.
- Info: ESLint 9 is marked deprecated by npm. Plan a move to
  ESLint 10 later.
- Security review of Milestone 1 (fresh reviewer): PASS, no
  critical or high findings.
