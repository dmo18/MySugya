// Deterministic Node tests: no OpenClaw or model/provider calls.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const path = join(dirname(fileURLToPath(import.meta.url)), "rabbi_cron_trigger.js");
const source = readFileSync(path, "utf8");
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;

async function evaluate(mockResult, throwError = false) {
  let requests = 0;
  const mockedExec = async ({ command }) => {
    requests++;
    assert.match(command, /rabbi_cron_admission.py/);
    if (throwError) throw new Error("exec unavailable");
    return mockResult;
  };
  const run = new AsyncFunction("exec", source);
  const result = await run(mockedExec);
  assert.equal(requests, 1, "gate must perform exactly one deterministic probe");
  assert.equal(typeof result.fire, "boolean");
  return result;
}

const allowed = JSON.stringify({
  admitted: true,
  provider: "openai",
  dayAdmission: 1,
  weeklyRemainingPercent: 60,
});

let result = await evaluate({ aggregated: allowed });
assert.equal(result.fire, true);
assert.match(result.message, /one controller-admitted unit/);
assert.deepEqual(result.state, { lastAdmission: "ALLOW" });

for (const bad of [
  { aggregated: "" },
  { aggregated: "not-json" },
  { aggregated: JSON.stringify({ admitted: false, reason: "quota" }) },
  { aggregated: JSON.stringify({ admitted: true, provider: "anthropic", dayAdmission: 1, weeklyRemainingPercent: 60 }) },
  { aggregated: JSON.stringify({ admitted: true, provider: "openai", dayAdmission: 7, weeklyRemainingPercent: 60 }) },
  { aggregated: JSON.stringify({ admitted: true, provider: "openai", dayAdmission: 1, weeklyRemainingPercent: 21 }) },
  { aggregated: JSON.stringify({ admitted: true, provider: "openai", dayAdmission: "1", weeklyRemainingPercent: 60 }) },
  { stdout: allowed },
  null,
]) {
  result = await evaluate(bad);
  assert.equal(result.fire, false);
}
assert.equal((await evaluate(null, true)).fire, false);
console.log("OK: Rabbi native cron trigger fail-closed tests passed");
