// Native OpenClaw agentTurn condition gate for MySugya Rabbi.
// Install: openclaw cron edit <campaign-id> --trigger-script <this-file>
// The CLI stores this source with the job. Keep the installed file for
// private recovery, and update the job after any deliberate policy change.
//
// No LLM calls here. exec is OpenClaw's headless native Code Mode tool;
// it executes one deterministic Python preflight. Missing/malformed
// outputs and all errors MUST mean fire:false.
//
// WARNING: forcing openclaw cron run bypasses this gate. Only the human
// operator may use the forced run mode. Keep the job DISABLED until an
// approved recovery and successful bounded canary.
try {
  const result = await exec({
    command: 'python3 "$HOME/.local/share/mysugya/rabbi_cron_admission.py"',
  });
  const raw = typeof result?.aggregated === "string"
    ? result.aggregated.trim()
    : "";
  const checked = JSON.parse(raw);
  if (
    checked !== null &&
    checked.admitted === true &&
    checked.provider === "openai" &&
    typeof checked.dayAdmission === "number" &&
    Number.isInteger(checked.dayAdmission) &&
    checked.dayAdmission >= 1 &&
    checked.dayAdmission <= 2 &&
    typeof checked.weeklyRemainingPercent === "number" &&
    checked.weeklyRemainingPercent >= 35
  ) {
    return {
      fire: true,
      message: "Approved bounded Rabbi campaign tick. Do exactly one controller-admitted unit; do not force cron, bypass quota policy, or retry identical failure evidence. Stop after this unit.",
      state: { lastAdmission: "ALLOW" },
    };
  }
} catch (_) {
  // Deny silently; sanitized reason is returned by the private Python
  // command if invoked directly by the operator for diagnostics.
}
return { fire: false, state: { lastAdmission: "DENY" } };
