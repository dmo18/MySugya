# OpenClaw Rabbi recovery (public, sanitized)

Rabbi is a dedicated OpenClaw agent and the autonomous operator of MySugya. Jarvis is a separate agent in the same OpenClaw installation. This public file describes reproducible behavior, never the machine's private identities, server topology or credentials. See `docs/source-first-autonomous-development.md`.

## Rebuild boundary

A public repo can reconstruct project software and policy. It CANNOT restore private identity, auth, provider tokens, exact model credentials, private memory, secrets or active runtime state. Keep those in separately encrypted, user-owned backups. Do not put a real `openclaw.json`, agent session export, OpenClaw state directory, vault contents, cron dump, SSH key, cookies, bearer token, private IP or hostnames in this repository.

1. Reinstall supported OpenClaw/runtime versions from the official project instructions and restore private agent configuration from the user's secure backup. Confirm the distinct main/Jarvis and Rabbi agents are present. Do not assume current defaults match a different OpenClaw version.
2. Clone MySugya. Confirm the latest protected `main`, `VERSION`, `CLAUDE.md`, `docs/worker-pipeline-sop.md`, `docs/semantic-self-heal.md`, this recovery guide, and tests are available from GitHub without relying on a prior chat.
3. Check the private runtime's model allowlists, scoped subagent models, budget caps, cron jobs, stop and hold files, active worktrees, watchdog and pointer state. Check live OpenClaw CLI help before using any scheduling operation. Do not publish its output to GitHub.
4. First perform READ-ONLY inspection and reconcile the ledger against actual merged GitHub commits and tests. Record the sanitized evidence and any approvals needed. Do not delete an expired hold or stop just because its timestamp has elapsed.
5. Run `openclaw config validate` and the repository's deterministic unit tests. On an isolated snapshot, run controller/adapter tests and shadow canary; then validate a semantic canary on a bounded daf, ensuring it can open a scoped PR and complete the verification chain.
   - Read-only quota preflight: `python3 scripts/rabbi_quota_gate.py --provider openai`. The expected exit is a refusal when weekly remaining is below 35%, telemetry is stale, or provider capacity is unknown. This must remain outside model execution; obtaining ALLOW does not clear a separate operator hold.
6. Only after independent approval, operational canary, passing required CI and the configured quota admission floor, explicitly retire superseded stop records through the approved operator procedure, then re-enable the EXISTING autonomous campaign job with a checked next-run time. Never silently resume a watchdog-stopped campaign.
7. Exercise one real source-verified daf work unit end-to-end, including the PR, CI, independent review, merge, post-merge evidence, token accounting, cursor advancement and failure handling. Confirm no routine human prompt is necessary.
8. If any step fails, leave the campaign disabled, preserve immutable evidence and explain the one actionable next step. Routine failed canaries do not authorize bypassing holds.

## Read-only operator diagnostics

Use the CLI commands supported by the live installed OpenClaw version. Safe initial commands are `openclaw --version`, `openclaw config validate`, `openclaw agents list`, and `openclaw cron --help`. To review active cron jobs, use the supported listing command shown by `openclaw cron --help`; do not guess the exact syntax. Do not paste raw configuration files or full scheduler state into a public PR.

For private runtime backups, capture configuration, identities, scheduling state and critical file checksums in encrypted storage accessible only to the operator. Restore to a disposable test environment before trusting a backup. Publicly publish only a redacted PASS/FAIL recovery test and the repository SHA.

## Automation contract

Once authorized and healthy, Rabbi owns implementation, scholarly work routing, tests, PR creation, authorized merge, docs, state and cost accounting. OpenClaw provides execution, credentials and scheduling, not an additional nonautonomous assistant workflow. The controller evaluates admissibility; the OpenClaw harness executes only authorized actions. Do not claim that `scripts/autonomy_controller.py` or the current `scripts/autonomy_shadow_adapter.py` executes jobs: as documented, they currently do NOT.

Existing operating floor: do not launch/resume below 35% weekly remaining; preserve 30% reserve. Existing operator hold and campaign-stop markers are not auto-cleared. Recovery of a stopped live campaign requires separate operator authorization and canary evidence.

## Documentation completeness test

From a clean clone, a future operator must be able to: install dependencies, run `npm test`, run `python3 scripts/campaign_packet.py --module yoma --daf 2a --mode source`, understand the module's schemas and data ownership, recreate a Rabbi OpenClaw agent with private credentials, identify and test the scheduler and controller, and understand precisely who may authorize a stopped campaign to resume.
