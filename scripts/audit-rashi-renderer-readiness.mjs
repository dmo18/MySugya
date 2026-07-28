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
 *   - modules/yoma/scripts/allowlists/rashi_boundary_authorizations.json,
 *     validated by validate_rashi_boundary_authorizations.py (a real
 *     subprocess): every boundary (empty-link) entry in the live corpus
 *     must carry a current, non-stale, non-duplicate authorization, and the
 *     registry may never silently grow past its ratchet
 *   - audit_rashi_semantic.py --profile --json run as a real subprocess,
 *     consuming its per-daf classification/recommendedTaskType output
 *     directly (never a reimplementation of its scoring logic): readiness
 *     requires zero daf classified SHIFTED or FABRICATION-SUSPECT and zero
 *     daf with a non-null recommendedTaskType. Advisory-only findings on
 *     otherwise-ALIGNED daf (drift within tolerance, or an isolated missing
 *     anchor) never block this check, but are never suppressed either -
 *     every one is printed with its daf, exact vilnaLine, and offset or
 *     "missing" evidence in this check's own detail output.
 *   - an exhaustive, sharded browser-association CI artifact
 *     (see check-rashi-browser-shard-artifact.mjs / the
 *     rashi-browser-shards.yml workflow): the gate parses and validates the
 *     real downloaded/generated result file, rejecting it if it is missing,
 *     stale, partial (not all 173 daf), from the wrong commit, or reports
 *     any shard failure. A human stating the run happened is never treated
 *     as machine evidence.
 *
 * This script only reports. It never enables anything and never edits an
 * allowlist or the boundary registry.
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
  // Delegates to the real registry validator (a separate subprocess, not a
  // reimplementation): validate_rashi_boundary_authorizations.py checks the
  // registry against the live corpus and fails on an authorization for a
  // non-empty entry, a missing authorization, a stale authorization, a
  // duplicate, a nonexistent daf/vilnaLine, or growth past its ratchet.
  const r = run('python3', ['scripts/validate_rashi_boundary_authorizations.py'], YOMA);
  return {
    pass: r.code === 0,
    detail: r.code === 0 ? r.stdout.trim() : (r.stdout + r.stderr).trim().split('\n').slice(-6).join(' | '),
  };
});

check('semantic-link closure: no actionable defects (audit_rashi_semantic.py --profile --json)', () => {
  // Actionable vs advisory, per daf, from the real per-daf drift profile
  // (never a reimplementation of its classification logic):
  //   - actionable: daf classified SHIFTED or FABRICATION-SUSPECT, or
  //     carrying a non-null recommendedTaskType (repair work is owed)
  //   - advisory: every other daf that still has a non-zero-offset or
  //     missing anchor (findings that do not block readiness, but are
  //     never suppressed - see the 2a/4b docs/rashi-audit-backlog.md entry)
  // Readiness passes only when there are zero actionable daf. Advisory
  // findings are reported in full (daf, exact vilnaLine, kind, offset or
  // "missing") in the detail string every time this check runs, whether it
  // passes or fails.
  const r = run('python3', ['scripts/audit_rashi_semantic.py', '--profile', '--json'], YOMA);
  if (!r.stdout) return { pass: false, detail: `no output; ${r.stderr.trim().split('\n').slice(-2).join(' | ')}` };
  const profiles = JSON.parse(r.stdout);

  const actionable = profiles.filter(p =>
    p.classification === 'SHIFTED' || p.classification === 'FABRICATION-SUSPECT' || p.recommendedTaskType
  );

  const advisoryLines = [];
  for (const p of profiles) {
    if (actionable.includes(p)) continue;
    for (const a of p.anchors ?? []) {
      if (a.offset === null) {
        advisoryLines.push(`${p.daf} L${a.line} (${p.classification}): missing anchor for ${a.kind} ${JSON.stringify(a.token)}`);
      } else if (a.offset !== 0) {
        advisoryLines.push(`${p.daf} L${a.line} (${p.classification}): ${a.kind} ${JSON.stringify(a.token)} offset ${a.offset}`);
      }
    }
  }

  const detailParts = [
    `daf_examined=${profiles.length}`,
    `actionable_daf=${actionable.length}`,
    `advisory_findings=${advisoryLines.length}`,
  ];
  if (actionable.length) {
    detailParts.push('ACTIONABLE: ' + actionable.map(p => `${p.daf}=${p.classification}${p.recommendedTaskType ? `(${p.recommendedTaskType})` : ''}`).join(', '));
  }
  if (advisoryLines.length) {
    detailParts.push('advisory (not blocking): ' + advisoryLines.join(' ;; '));
  }

  return { pass: actionable.length === 0, detail: detailParts.join(' | ') };
});

check('exhaustive browser corpus association run (sharded workflow artifact)', () => {
  // Delegates entirely to check-rashi-browser-shard-artifact.mjs (a real
  // subprocess): it reads the combined result artifact produced by
  // .github/workflows/rashi-browser-shards.yml and rejects it outright if
  // missing, partial, stale/wrong-commit, local-only (not produced by the
  // actual workflow run), or reporting any failure. This script never
  // hardcodes a pass and never accepts a manually stated result in place of
  // that artifact.
  const r = run('node', ['scripts/check-rashi-browser-shard-artifact.mjs'], ROOT);
  return {
    pass: r.code === 0,
    detail: r.code === 0 ? r.stdout.trim() : (r.stdout + r.stderr).trim().split('\n').slice(-8).join(' | '),
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
