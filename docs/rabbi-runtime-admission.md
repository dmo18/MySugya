# Rabbi pre-model runtime admission gate

**Implementation status:** Source-controlled gate scripts and tests are present in this repository. These do not change the user's OpenClaw server by themselves. The existing Rabbi autonomous campaign is stopped by operator safety controls. This runbook must not be interpreted as permission to restart it.

## Why this exists

The legacy Yoma OpenClaw automation was scheduled every 5 minutes with a two-hour `agentTurn` timeout and no per-job fallback override. A disabled job and the earlier deterministic autonomy controller are not sufficient once a future operator enables it: the controller cannot intercept a model call it never sees, and a provider quota read from inside Rabbi already costs a model invocation.

OpenClaw 2026.10.5 supports a native `trigger.script` condition on an `agentTurn` job. On each due tick it can call a deterministic local command before launching a model. This change adds:

- `scripts/rabbi_cron_trigger.js`: headless condition that invokes a dedicated private-installed Python check and returns `fire:false` on all malformed/ambiguous/missing output, quota refusal, or error. It cannot launch an LLM itself.
- `scripts/rabbi_cron_admission.py`: requires a private explicit authorization marker, reads a recently cached **Rabbi-scoped** quota snapshot without calling OpenClaw, evaluates the 35% weekly admission floor and 30% reserve, and atomically reserves a UTC-day slot in a private ledger. The authorization cap and absolute supported maximum are both **2 starts per UTC day**.
- `scripts/rabbi_quota_gate.py`: deterministic quota interpreter and standalone, bounded live CLI probe; never ask an LLM to invent quota evidence.
- `scripts/rabbi_quota_refresh.py`: host-side, model-free refresh of an explicitly Rabbi-scoped quota snapshot; stores only source ID, collection time and quota-window numbers in private mode-0600 storage.
- `ops/systemd-user/mysugya-rabbi-quota-refresh.service` and `.timer`: refresh four times daily, about three minutes ahead of the four fixed UTC cron opportunities. These are **templates**, not automatically activated in the operator's runtime.
- `scripts/test_rabbi_cron_admission.py`, `scripts/test_rabbi_quota_refresh.py`, and `scripts/test_rabbi_cron_trigger.mjs`: network-free positive, stale-snapshot, sanitation and denial tests.

## Before installation

The operator has a verified, PRIVATE OpenClaw backup, including scheduler snapshots. Review current GitHub `main` and CI, current live job ID, installed OpenClaw CLI flags, and the true operator-stop ledger before any changes. Preserve other jobs and agent isolation (especially Jarvis). No cron command in this section enables or force-runs Rabbi.

## Install while the campaign is DISABLED

Obtain four files from the reviewed commit of MySugya, and copy them together to a private runtime-controlled directory `~/.local/share/mysugya/` (they contain no secrets):

- `scripts/rabbi_quota_gate.py`
- `scripts/rabbi_cron_admission.py`
- `scripts/rabbi_cron_trigger.js`
- `scripts/rabbi_quota_refresh.py`

Run `python3 -m py_compile` for all three Python files, run their deterministic tests, then use OpenClaw's supported CLI:

```bash
openclaw cron edit <rabbi-campaign-id> \
  --cron '0 2,8,14,20 * * *' \
  --tz Etc/UTC \
  --timeout-seconds 900 \
  --fallbacks "" \
  --trigger-script "$HOME/.local/share/mysugya/rabbi_cron_trigger.js"
```

### IMPORTANT: Rabbi-only Swarm limits do not bound ordinary subagents

**Verified against OpenClaw 2026.10.5 on 2026-10-22:** these four previously suggested per-agent paths are INVALID and must not be retried:

- `agents.entries.rabbi.subagents.maxConcurrent`
- `agents.entries.rabbi.subagents.maxChildrenPerAgent`
- `agents.entries.rabbi.subagents.maxSpawnDepth`
- `agents.entries.rabbi.subagents.runTimeoutSeconds`

The live CLI rejected each with `Config validation failed: agents.entries.rabbi.subagents: Unrecognized key`; none of those writes was saved. OpenClaw exposes ordinary subagent concurrency, child admission, nesting depth and default timeout under **`agents.defaults.subagents`**, which can affect *all* agents including Jarvis. **Do not silently move these four settings to the global defaults**: it would violate Rabbi/Jarvis isolation. Inspect the active version's `openclaw config schema --json` before any other new key is proposed.

The live CLI DID accept the Rabbi-scoped Swarm limits below, and `openclaw config validate` passed:

```json
{
  "maxConcurrent": 2,
  "maxChildrenPerGroup": 2,
  "maxTotalPerGroup": 4
}
```

They were set under `agents.entries.rabbi.tools.swarm`. Inspect with **read-only** `openclaw config get agents.entries.rabbi.tools.swarm`. Verify effective behavior in a future controlled canary: a valid saved config does not establish that the active Gateway has reloaded it.

These limits apply ONLY to Swarm collector children. They do **not** cap ordinary `sessions_spawn` children, any Codex-native subagents, ACP workers, external subprocesses, or workers in independent sessions. Ordinary child execution remains a known quota-risk gap. Before enabling Rabbi, choose and verify a Rabbi-scoped permission/runner policy that bounds these launch paths, or use an operator-approved global limit after explicitly assessing Jarvis impact. A 15-minute parent cron timeout is not proof that detached workers stop.

The job MUST remain disabled. Confirm via `openclaw cron get <id> --json` that it is still owned by `rabbi`, is still `enabled:false`, retains `payload.kind:agentTurn`, has the **fixed UTC four-times-daily cron** expression `0 2,8,14,20 * * *` with `Etc/UTC`, `payload.timeoutSeconds:900`, explicit empty `payload.fallbacks:[]`, and a nonempty `trigger.script`. A different schema or behavior means STOP and roll back the scheduler from the private snapshot.

**No operator marker is created during installation.** As a result, ordinary due evaluations would refuse even if the job were accidentally enabled (manual forced `cron run` remains a separate bypass; see below). Do not create the marker merely because usage passes its quota check.

## Future authorization only after actual recovery

Once the existing operator-stop reason is resolved and recorded, post-merge tests and independent scholarly canaries pass, model/subagent timeouts and concurrency are bounded, and the user authorizes resumption, the operator may create the following PRIVATE `0600` file at `~/.local/state/mysugya/rabbi-autonomy-approval.json`:

```json
{
  "schemaVersion": 1,
  "agentId": "rabbi",
  "campaignId": "mysugya-yoma-remediation",
  "authorized": true,
  "maxStartsPerUtcDay": 2
}
```

The gate refuses absent, malformed, symlinked, weak-permission, mismatched or unauthorized markers. Remove this file and disable the automation immediately when the operator stops the campaign. Never commit it.

The gate's private ledger is `~/.local/state/mysugya/rabbi-admissions.json`, with mode `0600`; it reserves an admission slot BEFORE the model is launched.

**Permission boundary caveat:** `0600` protects these files from *other Unix users* but does not protect them from Rabbi if its shell tools run as the same operating-system user as the OpenClaw Gateway. A shell-capable Rabbi process could modify the approval file or admission ledger or use a forced cron command. These checks are valuable against accidental scheduler starts, but they are **NOT a tamper-resistant model-spending cap**. Before authorizing production autonomy, enforce a separate OS/sandbox identity or owner-only launch/control boundary that Rabbi cannot modify, and verify the effective `exec`, `cron`, `gateway` and `sessions_spawn` policies. A `tools.deny` entry alone cannot inspect what commands an allowed shell `exec` performs. Do not assume private paths are isolated just because the files have restrictive permissions. A failed model run still uses that slot. Corrupt or future-dated state blocks further admission. Zero new work until the next UTC date is an acceptable failure mode; don't reset this ledger to evade caps.

To diagnose without invoking Rabbi: `python3 ~/.local/share/mysugya/rabbi_cron_admission.py`. It will return `{"admitted":false}` with a reason when unapproved or quota-blocked. **Warning:** with an actual authorization marker and sufficient quota, that command reserves a daily start even though it does not run a model; normally inspect with the cheaper `python3 ~/.local/share/mysugya/rabbi_quota_gate.py` and `openclaw cron get` until fully ready. Do not use the admission script as a high-frequency monitor.

## Live diagnostic findings: quota probe and sandbox (2026-10-22)

The installed OpenClaw 2026.10.5 `openclaw sandbox explain --agent rabbi` reports **runtime: direct, mode: off, scope: agent**. The tool surface permits `exec`, `process` and `sessions_spawn`. Merely listing `Sandbox tool policy` allow/deny rules does not establish execution isolation when sandbox mode is off. An unsandboxed shell-capable Rabbi running under the same host user can bypass local approval/ledger files or the scheduler via OS commands. The existing job MUST remain disabled.

Per-agent sandbox policy at `agents.entries.rabbi.sandbox` can isolate Rabbi without changing Jarvis. However activating Docker sandboxing can remove access to the existing host checkout, provider CLI, and native Codex execution surfaces. The default Docker sandbox has no network; do not flip the switch blindly or mount private `.openclaw` state or the host Docker socket into the sandbox. Inspect the local runtime's image, repository/workspace location, enabled per-agent GitHub identity, container access needs and Codex adapter before choosing an enforceable, working arrangement. See the official OpenClaw Codex approval/sandbox reference. Any native pre-run trigger that invokes a host-installed Python script MUST be tested again after sandboxing; its `exec` may follow the agent's sandbox policy and fail closed when host tools/paths are inaccessible.

The first live `python3 ~/.local/share/mysugya/rabbi_quota_gate.py` returned `admitted:false` because its `openclaw status --usage --agent rabbi --json` subprocess was killed after **55 seconds**, not because it successfully evaluated the reported weekly quota. The first scheduled-admission implementation imposed an even shorter **18-second** subprocess timeout with a **12-second** OpenClaw status deadline. These conflicting deadlines could make the gate perpetually deny even with a valid account.

The initial quota script's 55-second timeout and an earlier 18-second cron subprocess timeout caused fail-closed denials without evaluating the actual weekly quota. The upstream native trigger has a **30-second** maximum wall-clock budget (verified in the `v2026.10.5` `src/cron/trigger-script.ts`). Increasing its subprocess allowance to 100 seconds INSIDE the native trigger would be incorrect.

The corrected design uses an explicit, model-free, **host-side** `rabbi_quota_refresh.py` with a 90-second OpenClaw status deadline and a 100-second subprocess timeout. It keeps sanitized `usage.updatedAt`, week/5h percent-used windows, and source ID, but no auth token, account identity or host details. A local systemd user timer refreshes the cache four times per day at **01:57, 07:57, 13:57 and 19:57 UTC**. The actual OpenClaw cron schedule, once separately authorized, is **02:00, 08:00, 14:00 and 20:00 UTC**. This deliberately avoids costly repeated polling.

`rabbi_cron_admission.py` now checks only the local source-tagged, owner-private cache. The ordinary native trigger therefore never waits for a slow provider query. Each observation must still be at most **five minutes** old. Both the weekly and five-hour OpenAI quota windows are mandatory; missing, stale, malformed, duplicated, errored or below-floor quota evidence DENIES admission. If the snapshot refresh fails, it removes an earlier snapshot and fails closed. A successful refresh during low quota still records the true low number; it does not authorize a run.

The two user-systemd unit templates are in `ops/systemd-user/`. Review them, copy them into the operator's private `~/.config/systemd/user/` and enable ONLY the quota-refresh timer after a manual read-only/low-quota dry run confirms schema and timing. Never run `systemctl --user start` on the *agentTurn* job here; installing the refresh timer does not authorize Rabbi. Verify schedule syntax with `systemd-analyze calendar` on the actual host. Back up old job and config before editing, and verify its enabled state remains false.

**Isolation remains unproven:** Docker and its default sandbox image were not available from the current SSH shell; the user's initial `openclaw models status --agent rabbi --json` took 14.5 seconds but exposed no usable quota fields. Gateway `usage.status` RPC is cached and may be faster, but upstream `v2026.10.5` scopes that RPC by the Gateway's legacy/default auth owner rather than the requested Rabbi agent, so it is NOT automatically an acceptable substitute for `--agent rabbi` quota evidence. The OpenClaw sandbox supports Docker, Podman and SSH backends; determine availability and whether a separate restricted Unix/SSH identity can host Rabbi's tools, Git checkout and Codex adapter without affecting Jarvis before enabling a sandbox. Never flip `sandbox.mode=all` blindly.

**No false sense of security:** same-Unix-user `0600` state is writable by unsandboxed Rabbi, and detached/forced launches bypass this cron gate. This is a correctness and accidental-overspend guard pending separate enforceable execution isolation, not a total quota firewall.

## Important limits (not optional)

This is a bounded scheduled admission gate, **not an absolute token governor**. Native OpenClaw scheduler `--timeout-seconds` limits the parent agent turn, not necessarily every independently spawned Codex-native child or external worker. A single model call can spend quota while running. Prove subagent-level runtime/concurrency restrictions and the new Yoma source-verification process in a canary before authorizing the private marker.

**Forced manual runs bypass `trigger.script`.** Do not grant Rabbi autonomous rights to force-run or edit its own campaign cron; restrict such capabilities at the OpenClaw policy boundary. The user/operator may force-run only as an exceptional, explicitly authorized experiment, never as a workaround. A model can also run through channels outside this scheduler, so this gate does not replace per-agent tool/model policy.

If a new model or Anthropic reviewer route is introduced, audit its own capacity, per-unit budget and fallback behavior before the new provider may run. An OpenAI-only gate cannot enforce Anthropic quota or Codex-native subordinate execution limits.

Start conservatively: one work unit per scheduled tick, four fixed UTC opportunities six hours apart, 15-minute parent timeout, maximum two daily admissions, no fallback retry to alternate providers. Increase only after evidence shows high quality and low provider burn. Keep the operator safety stop independent from the quota floor so a reset never automatically restarts previously blocked work.
