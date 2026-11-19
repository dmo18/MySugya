# Status

Updated: 2026-11-19. Version: 15.600.

## Done

- Takeover audit. See `docs/TAKEOVER.md`.

## In progress

- Waiting for the owner to choose the next piece of work.

## Next (proposed, not approved)

1. Decide what to do with PR #663 (Yoma 18b certification).
2. Continue semantic certification from daf 18b (397 sugyot left).
3. Add tests before the Cloudways publish step, or switch it off.
4. Add a linter.

## Decisions made

| Decision | Reason |
|---|---|
| Work on a branch and merge by pull request | Merging to `main` publishes the live site |
| Did not enable `githooks/pre-commit` yet | It came with the repo; owner approves first |
| No version bump for audit docs | Docs only, no product change |

## Known issues

See "Known issues and risks" in `docs/TAKEOVER.md`.

## Open security findings

- Critical or high: none found.
- Medium: Cloudways workflow publishes on every merge with no
  tests and a force push.
