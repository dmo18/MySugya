# Rabbi pre-model runtime admission gate

**Implementation status:** Source-controlled gate scripts and tests are present in this repository. These do not change the user's OpenClaw server by themselves. The existing Rabbi autonomous campaign is stopped by operator safety controls. This runbook must not be interpreted as permission to restart it.

## Why this exists

The legacy Yoma OpenClaw automation was scheduled every 5 minutes with a two-hour `agentTurn` timeout and no per-job fallback override. A disabled job and the earlier deterministic autonomy controller are not sufficient once a future operator enables it: the controller cannot intercept a model call it never sees, and a provider quota read from inside Rabbi already costs a model invocation.

OpenClaw 2026.10.5 supports a native `trigger.script` condition on an `agentTurn` job. On each due tick it can call a deterministic local command before launching a model. This change adds:

- `scripts/rabbi_cron_trigger.js`: headless condition that invokes a dedicated private-installed Python check and returns `fire:false` on all malformed/ambiguous/missing output, quota refusal, or error. It cannot launch an LLM itself.
- `scripts/rabbi_cron_admission.py`: requires a private explicit authorization marker, checks real OpenClaw provider usage via `status --usage --agent rabbi --json`, evaluates the 35% weekly admission floor and 30% reserve, and atomically reserves a UTC-day slot in a private ledger. Default recommended authorization cap is **2 starts per UTC day**; absolute supported maximum is six.
- `scripts/rabbi_quota_gate.py`: a separate, already-tested deterministic quota interpreter; never ask an LLM to invent quota evidence.
- `scripts/test_rabbi_cron_admission.py` and `scripts/test_rabbi_cron_trigger.mjs`: network-free positive and denial tests.

## Before installation

The operator has a verified, PRIVATE OpenClaw backup, including scheduler snapshots. Review current GitHub `main` and CI, current live job ID, installed OpenClaw CLI flags, and the true operator-stop ledger before any changes. Preserve other jobs and agent isolation (especially Jarvis). No cron command in this section enables or force-runs Rabbi.

## Install while the campaign is DISABLED

Obtain three files from the reviewed commit of MySugya, and copy them together to a private runtime-controlled directory `~/.local/share/mysugya/` (they contain no secrets):

- `scripts/rabbi_quota_gate.py`
- `scripts/rabbi_cron_admission.py`
- `scripts/rabbi_cron_trigger.js`

Run `python3 -m py_compile` for both Python files, run their deterministic tests, then use OpenClaw's supported CLI:

```bash
openclaw cron edit <rabbi-campaign-id> \
  --every 6h \
  --timeout-seconds 900 \
  --fallbacks "" \
  --trigger-script "$HOME/.local/share/mysugya/rabbi_cron_trigger.js"
```

Bound Rabbi's ordinary OpenClaw subagents independently from Jarvis using the per-agent overrides below, after backing up `~/.openclaw/openclaw.json` and validating the installed schema:

```bash
openclaw config set agents.entries.rabbi.subagents.maxConcurrent 2 --strict-json
openclaw config set agents.entries.rabbi.subagents.maxChildrenPerAgent 2 --strict-json
openclaw config set agents.entries.rabbi.subagents.maxSpawnDepth 1 --strict-json
openclaw config set agents.entries.rabbi.subagents.runTimeoutSeconds 600 --strict-json
openclaw config validate
```

These limits apply to ordinary OpenClaw subagent spawns; they do NOT necessarily constrain Codex-native subagents, ACP workers or Swarm collector lanes. Explicit per-spawn timeouts or separate execution policies may still be required.

The job MUST remain disabled. Confirm via `openclaw cron get <id> --json` that it is still owned by `rabbi`, is still `enabled:false`, retains `payload.kind:agentTurn`, now has `schedule.everyMs:21600000`, `payload.timeoutSeconds:900`, explicit empty `payload.fallbacks:[]`, and a nonempty `trigger.script`. A different schema or behavior means STOP and roll back the scheduler from the private snapshot.

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

The gate's private ledger is `~/.local/state/mysugya/rabbi-admissions.json`, with mode `0600`; it reserves an admission slot BEFORE the model is launched. A failed model run still uses that slot. Corrupt or future-dated state blocks further admission. Zero new work until the next UTC date is an acceptable failure mode; don't reset this ledger to evade caps.

To diagnose without invoking Rabbi: `python3 ~/.local/share/mysugya/rabbi_cron_admission.py`. It will return `{"admitted":false}` with a reason when unapproved or quota-blocked. **Warning:** with an actual authorization marker and sufficient quota, that command reserves a daily start even though it does not run a model; normally inspect with the cheaper `python3 ~/.local/share/mysugya/rabbi_quota_gate.py` and `openclaw cron get` until fully ready. Do not use the admission script as a high-frequency monitor.

## Important limits (not optional)

This is a bounded scheduled admission gate, **not an absolute token governor**. Native OpenClaw scheduler `--timeout-seconds` limits the parent agent turn, not necessarily every independently spawned Codex-native child or external worker. A single model call can spend quota while running. Prove subagent-level runtime/concurrency restrictions and the new Yoma source-verification process in a canary before authorizing the private marker.

**Forced manual runs bypass `trigger.script`.** Do not grant Rabbi autonomous rights to force-run or edit its own campaign cron; restrict such capabilities at the OpenClaw policy boundary. The user/operator may force-run only as an exceptional, explicitly authorized experiment, never as a workaround. A model can also run through channels outside this scheduler, so this gate does not replace per-agent tool/model policy.

If a new model or Anthropic reviewer route is introduced, audit its own capacity, per-unit budget and fallback behavior before the new provider may run. An OpenAI-only gate cannot enforce Anthropic quota or Codex-native subordinate execution limits.

Start conservatively: one work unit per scheduled tick, 6-hour interval, 15-minute parent timeout, maximum two daily admissions, no fallback retry to alternate providers. Increase only after evidence shows high quality and low provider burn. Keep the operator safety stop independent from the quota floor so a reset never automatically restarts previously blocked work.
