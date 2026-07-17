#!/usr/bin/env node
/**
 * audit-rashi-renderer-readiness.mjs - cutover-readiness gate for the linked
 * Rashi renderer.
 *
 * Checks the REAL repository ratchet files, never invented ones:
 *   - modules/yoma/scripts/allowlists/rashi_content_allowlist.json
 *     (entries[] + count_mismatches[] - this IS the scaffold-content debt
 *     ratchet; there is no separate scaffold_debt.json in this repo)
 *   - modules/yoma/scripts/allowlists/rashi_links_allowlist.json
 *     (documented pre-existing bogus linkedGemaraLineIds; ratchet, entries
 *     must be zero for readiness even though it already is as of writing)
 *   - modules/yoma/scripts/allowlists/rashi_repetition_baseline.json
 *     (documented pre-existing within-daf en repetition; ratchet)
 *   - check_generated_freshness.py run as a real subprocess, not a string
 *     search
 *   - audit_rashi_association.py --exhaustive-corpus --json run as a real
 *     subprocess: broken/cross-daf count must be zero
 *   - audit_rashi_semantic.py run as a real subprocess: shift-candidate /
 *     missing-anchor flags must be zero (closest real proxy this repo has
 *     for "semantic-link closure state"; there is no dedicated closure file)
 *
 * Boundary (empty-link) entries require an explicit authorization registry
 * before they can be excluded from readiness. No such registry exists in
 * this repository today, so that condition is reported as NOT SATISFIED
 * whenever any boundary entries remain in scope - this script never invents
 * a passing mechanism for debt that hasn't actually been resolved.
 *
 * This script only reports. It never enables anything, never edits an
 * allowlist, and never claims a manual/future step (such as an exhaustive
 * browser corpus run - reserved for closure or a sharded workflow) has
 * passed when it has not actually been run.
 */

import { spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = resolve(fileURLToPath(import.meta.url), '..');
const ROOT = resolve(__dirname, '..');
const YOMA = resolve(ROOT, 'modules/yoma');

function readJson(path) {
  return JSON.parse(readFileSync(path, 'utf8'));
}

function run(cmd, args, cwd) {
  // The exhaustive-corpus --json plan is several MB; Node's spawnSync
  // defaults to a 1 MB maxBuffer and would silently truncate it otherwise.
  const result = spawnSync(cmd, args, { cwd, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
  return { code: result.status, stdout: result.stdout ?? '', stderr: result.stderr ?? '' };
}

const checks = [];

function check(name, fn) {
  let detail = '';
  let pass = false;
  try {
    const result = fn();
    pass = result.pass;
    detail = result.detail;
  } catch (e) {
    detail = `threw: ${e.message}`;
  }
  checks.push({ name, pass, detail });
  return pass;
}

console.log('Rashi linked-renderer readiness gate\n' + '='.repeat(60));

check('content allowlist ratchet is empty (rashi_content_allowlist.json)', () => {
  const data = readJson(resolve(YOMA, 'scripts/allowlists/rashi_content_allowlist.json'));
  const entries = data.entries?.length ?? 0;
  const mismatches = data.count_mismatches?.length ?? 0;
  return {
    pass: entries === 0 && mismatches === 0,
    detail: `entries=${entries} count_mismatches=${mismatches}`,
  };
});

check('links allowlist ratchet is empty (rashi_links_allowlist.json)', () => {
  const data = readJson(resolve(YOMA, 'scripts/allowlists/rashi_links_allowlist.json'));
  const entries = data.entries?.length ?? 0;
  return { pass: entries === 0, detail: `entries=${entries}` };
});

check('repetition baseline ratchet is empty (rashi_repetition_baseline.json)', () => {
  const data = readJson(resolve(YOMA, 'scripts/allowlists/rashi_repetition_baseline.json'));
  const entries = data.entries?.length ?? 0;
  return { pass: entries === 0, detail: `entries=${entries}` };
});

check('generated learning_data.js is fresh (check_generated_freshness.py)', () => {
  const r = run('python3', ['scripts/check_generated_freshness.py'], YOMA);
  return { pass: r.code === 0, detail: r.code === 0 ? 'fresh' : (r.stdout + r.stderr).trim().split('\n').slice(-3).join(' | ') };
});

let assocPlan = null;
check('exhaustive referential-integrity audit (audit_rashi_association.py --exhaustive-corpus)', () => {
  const r = run('python3', ['scripts/audit_rashi_association.py', '--exhaustive-corpus', '--json'], YOMA);
  if (!r.stdout) return { pass: false, detail: `no output; ${r.stderr.trim().split('\n').slice(-2).join(' | ')}` };
  assocPlan = JSON.parse(r.stdout);
  const c = assocPlan.counts;
  return {
    pass: assocPlan.success,
    detail: `broken=${c.broken} across daf=${c.daf} rashi_entries=${c.rashi_entries} `
      + `declared_associations=${c.declared_associations} multi_link=${c.multi_link} `
      + `mishnah=${c.mishnah} suffixed=${c.suffixed} sparse=${c.sparse} boundary=${c.boundary}`,
  };
});

check('every boundary (empty-link) entry has explicit authorization', () => {
  const boundaryCount = assocPlan?.counts?.boundary ?? null;
  if (boundaryCount === null) return { pass: false, detail: 'referential audit did not run' };
  // No boundary-authorization registry exists in this repository. Until one
  // is introduced and populated, this condition cannot be satisfied while
  // any boundary entries remain - reported honestly rather than invented.
  return {
    pass: boundaryCount === 0,
    detail: boundaryCount === 0
      ? 'no boundary entries in corpus'
      : `${boundaryCount} boundary entries exist and no authorization registry exists in this repo`,
  };
});

check('semantic-link closure proxy is clean (audit_rashi_semantic.py)', () => {
  // audit_rashi_semantic.py's --json flag is currently a no-op (declared but
  // unused in that script); there is also no dedicated semantic-link
  // closure file in this repo. The closest real, honest proxy is its
  // "Totals:" summary line, parsed from real stdout - never a duplicated
  // reimplementation of its scoring logic.
  const r = run('python3', ['scripts/audit_rashi_semantic.py'], YOMA);
  const m = r.stdout.match(
    /Totals:\s*(\d+)\s*shift candidate\(s\),\s*(\d+)\s*missing-anchor flag\(s\),\s*(\d+)\s*generic flag\(s\)/
  );
  if (!m) return { pass: false, detail: 'could not find a "Totals:" summary line in audit_rashi_semantic.py output' };
  const shift = Number(m[1]), missing = Number(m[2]), generic = Number(m[3]);
  return {
    pass: shift === 0 && missing === 0 && generic === 0,
    detail: `shift_candidates=${shift} missing_anchor=${missing} generic=${generic}`,
  };
});

check('exhaustive browser corpus association run (manual/sharded workflow)', () => {
  // Deliberately never auto-verified: running the full browser spec across
  // every daf in one process is reserved for closure or a sharded CI
  // workflow (see docs/reports/rashi-association-audit.md). This check can
  // never report pass on its own - only a human confirming that run
  // actually happened, and it is never invoked implicitly by this script.
  return {
    pass: false,
    detail: 'not automatically checked; run manually via '
      + '`node scripts/run-rashi-association.mjs --exhaustive-corpus` (data-only) '
      + 'plus a sharded browser workflow before claiming this satisfied',
  };
});

console.log();
for (const c of checks) {
  console.log(`  [${c.pass ? 'PASS' : 'FAIL'}] ${c.name}`);
  console.log(`         ${c.detail}`);
}

const passed = checks.filter(c => c.pass).length;
console.log('\n' + '='.repeat(60));
console.log(`${passed}/${checks.length} checks pass.`);
console.log(passed === checks.length ? 'READY' : 'NOT READY');
process.exit(passed === checks.length ? 0 : 1);
