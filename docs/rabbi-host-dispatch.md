# Rabbi host-only dispatcher and proposed same-host SSH isolation

**Status: uninstalled, disabled, unapproved.** This is a deployment design, not proof
that the live OpenClaw server is isolated. Do not activate timers or launch Rabbi
before separate operator authorization and live negative security tests.

## Why a separate dispatcher is needed

OpenClaw 2026.10.5 can sandbox an agent with \`agents.entries.rabbi.sandbox\` and
backend \`ssh\`. Only tools are sandboxed; the Gateway and plugin-control plane
remain on the host. On the current host, Docker, Podman and bwrap are unavailable.
A dedicated, unprivileged Unix account on the SAME host, accessible through
localhost SSH, is a candidate that avoids installing a container engine.
**Using SSH back into the owner account is not isolation.**

Native \`trigger.script\` evaluations use the agent's sandbox context. After
Rabbi is moved to a restricted SSH identity, a trigger cannot safely read
private approval and quota files belonging to the owner account. Copying
those files into Rabbi's writable workspace would negate the boundary.

For this reason, this proposal keeps the original OpenClaw Rabbi campaign
DISABLED and uses an owner-controlled user-systemd timer for candidate starts:

1. The already-defined host \`rabbi_quota_refresh.py\` service obtains Rabbi-scoped
   OpenAI quota about three minutes before a candidate start.
2. The independent host \`rabbi_host_dispatch.py\` process verifies the exact
   disabled campaign, isolated session, explicit OpenAI model pin, empty
   fallback list, native trigger presence and 900-second maximum timeout.
3. It obtains a non-blocking private lock, evaluates explicit operator approval
   plus a fresh quota snapshot, and reserves one of at most two daily starts.
4. Only then it invokes OpenClaw's documented \`cron run <id> --wait\` operator
   entry point. Forced manual runs intentionally skip \`trigger.script\`;
   this permission belongs exclusively to the owner identity, never Rabbi.
5. The dispatcher waits for completion and **never retries an uncertain run**.
   Unknown or failed runs still consume their daily admission slot.

The existing OpenClaw campaign remains disabled permanently in this option;
systemd supplies the candidate schedule. Thus no agent-sandbox exceptions are
necessary to run the quota admission gate. The old in-trigger gate stays as
defense in depth if an operator later redesigns native scheduling, but it is
NOT what admits these protected external starts.

## Installation prerequisites that must be proven first

- Confirm localhost sshd and a working separate restricted account. Confirm
  the owner can provision its SSH key and audit SSH host-key pinning.
- Confirm the Gateway rejects unauthenticated local-loopback administrative
  requests from the remote Unix identity. Keep all gateway tokens and agent
  provider credentials owned by the separate owner Unix identity.
- Check that OpenClaw SSH execution never forwards Gateway credentials to
  the restricted account, and that all Rabbi \`exec\` and file access land there.
- Configure \`agents.entries.rabbi.sandbox.mode=all\`, \`backend=ssh\`,
  \`scope=agent\`, and Rabbi's target and identity, without touching
  \`agents.defaults.sandbox\` or Jarvis. Verify the installed schema first.
- Deny Rabbi's \`cron\`, \`gateway\`, \`sessions_spawn\`, \`subagents\`, and
  other model/delegation tools until worker containment is verified.
  Shell execution in a distinct identity must not have a mounted Docker
  socket, Gateway token or owner private filesystem access.
- Confirm whether native Codex/Claude adapters create privileged Gateway-side
  workers, and prohibit unbounded native child execution in the first canary.
  A 15-minute parent timeout alone does not bound detached children.
- Confirm the actual Rabbi model and set an explicit OpenAI model pin on the
  DISABLED job using the installed, version-supported command. The dispatcher
  intentionally denies a job without this pin.
- Prove operator-stop semantics and a bounded source-first Yoma 2a canary
  before creating the approval marker or enabling any dispatcher timer.

## Host-only deployment shape

Install the reviewed commit copies of \`rabbi_host_dispatch.py\`,
\`rabbi_cron_admission.py\`, \`rabbi_quota_gate.py\`, and
\`rabbi_quota_refresh.py\` into \`~/.local/share/mysugya\` as the owner user.
Keep this directory inaccessible and not writable by the SSH sandbox identity.
Install the example service and timer templates to
\`~/.config/systemd/user\` but DO NOT enable or start them yet.

Create a PRIVATE \`0600\` environment file at
\`~/.config/mysugya/rabbi-dispatch.env\` only after live verification:

\`\`\`ini
RABBI_JOB_ID=<actual verified private job UUID>
RABBI_EXPECTED_MODEL=<exact approved openai/model route>
RABBI_OPENCLAW_BIN=<verified absolute path to openclaw>
\`\`\`

The script defaults to inspection only. Running it without \`--dispatch\`
can inspect readiness but cannot reserve quota or start Rabbi. Even with
\`--dispatch\`, the separate private authorization marker is mandatory.
The systemd timer schedule is 02:00, 08:00, 14:00, and 20:00 UTC;
the independent refresh timer runs at 01:57, 07:57, 13:57 and 19:57 UTC.
Verify unit parsing with \`systemd-analyze calendar\` before installation.

**This does not create an absolute token limit.** It bounds scheduled parent
admissions only. Network-accessible Codex/Claude CLI credentials in Rabbi's
restricted home, native Gateway plugins, independent child agent starts, human
manual overrides and untrusted remote accounts each require separate controls.
Do not deploy before verifying those paths fail closed.
