#!/usr/bin/env node
/**
 * run-rashi-association.mjs - orchestrates the Rashi linked-association audit.
 *
 * Runs modules/yoma/scripts/audit_rashi_association.py --json once, writes
 * the exact plan (including real he/en/kind) to a scratch file, then runs
 * tests/browser/rashi-association.spec.js against that file via
 * YOMA_ASSOC_PLAN_PATH. The Playwright spec never invokes Python itself and
 * never hardcodes expected text - everything it asserts comes from this
 * plan.
 *
 * Usage:
 *   node scripts/run-rashi-association.mjs                     # default: target 2a
 *   node scripts/run-rashi-association.mjs --target 11a
 *   node scripts/run-rashi-association.mjs --range 2a 14b
 *   node scripts/run-rashi-association.mjs --corpus             # sampled, not exhaustive
 *   node scripts/run-rashi-association.mjs --exhaustive-corpus  # reserved for closure /
 *                                                                # a sharded workflow; not
 *                                                                # part of default CI
 *
 * Default target daf is 2a: it has real multi-link and Mishnah associations
 * (9 multi-link, 13 Mishnah entries as of VERSION 15.98), so the default run
 * actually exercises those code paths instead of only the plain single-link
 * case.
 */

import { spawnSync } from 'node:child_process';
import { mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const __dirname = resolve(fileURLToPath(import.meta.url), '..');
const ROOT = resolve(__dirname, '..');
const require = createRequire(import.meta.url);

function parseArgs(argv) {
  const opts = { mode: 'target', target: '2a', from: null, to: null, module: 'yoma' };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--target' && argv[i + 1]) {
      opts.mode = 'target';
      opts.target = argv[++i];
    } else if (argv[i] === '--range' && argv[i + 1] && argv[i + 2]) {
      opts.mode = 'range';
      opts.from = argv[++i];
      opts.to = argv[++i];
    } else if (argv[i] === '--corpus') {
      opts.mode = 'corpus';
    } else if (argv[i] === '--exhaustive-corpus') {
      opts.mode = 'exhaustive-corpus';
    } else if (argv[i] === '--module' && argv[i + 1]) {
      opts.module = argv[++i];
    }
  }
  return opts;
}

function auditArgsFor(opts) {
  switch (opts.mode) {
    case 'range': return ['--range-from', opts.from, '--range-to', opts.to];
    case 'corpus': return ['--corpus'];
    case 'exhaustive-corpus': return ['--exhaustive-corpus'];
    default: return ['--target', opts.target];
  }
}

const opts = parseArgs(process.argv.slice(2));
const { resolveRashiModule } = require('../shared/module_resolver.js');
let descriptor;
try {
  descriptor = resolveRashiModule(opts.module, ROOT);
} catch (e) {
  console.error(`[rashi-association] FAILED: ${e.code}: ${e.message}`);
  process.exit(1);
}
const auditScript = resolve(ROOT, descriptor.paths.scriptsRoot, 'audit_rashi_association.py');

console.log(`[rashi-association] mode=${opts.mode} scope=${JSON.stringify(opts)}`);
console.log('[rashi-association] running data auditor...');

const jsonResult = spawnSync('python3', [auditScript, ...auditArgsFor(opts), '--json'], {
  cwd: ROOT,
  encoding: 'utf8',
  // The exhaustive-corpus plan is several MB; avoid Node's 1 MB spawnSync default.
  maxBuffer: 64 * 1024 * 1024,
});

if (jsonResult.status !== 0 && !jsonResult.stdout) {
  console.error(jsonResult.stderr);
  process.exit(jsonResult.status ?? 1);
}

let plan;
try {
  plan = JSON.parse(jsonResult.stdout);
} catch {
  console.error('[rashi-association] failed to parse auditor JSON output:');
  console.error(jsonResult.stdout);
  console.error(jsonResult.stderr);
  process.exit(1);
}

console.log(`[rashi-association] counts: ${JSON.stringify(plan.counts)}`);

if (!plan.success) {
  console.error(`[rashi-association] auditor found ${plan.error_count} referential-integrity error(s):`);
  for (const e of plan.errors.slice(0, 20)) console.error(`  ERROR  ${e}`);
  if (plan.errors.length > 20) console.error(`  ... and ${plan.errors.length - 20} more`);
  console.error('[rashi-association] not running the browser spec against a plan with known errors.');
  process.exit(1);
}

if (opts.mode === 'exhaustive-corpus') {
  console.warn(
    '[rashi-association] exhaustive-corpus is reserved for closure / a sharded workflow. ' +
    'Data-level audit passed; NOT running the full browser spec against all daf in this invocation.'
  );
  process.exit(0);
}

const scratchDir = mkdtempSync(join(tmpdir(), 'rashi-assoc-'));
const planPath = join(scratchDir, 'plan.json');
writeFileSync(planPath, JSON.stringify(plan), 'utf8');
console.log(`[rashi-association] plan written to ${planPath} (${plan.daf_list.length} daf, ${plan.findings.length} entries)`);

// The browser spec (tests/browser/rashi-association.spec.js) reads
// MYSUGYA_TEST_MODULE to resolve its own module descriptor (Phase 3 Step
// 4B); passing this script's own --module choice through closes the loop
// this file's module resolution (above) opened - the plan, the audit
// script, and the browser assertion now all agree on the same module.
console.log('[rashi-association] running browser spec...');
const playwrightResult = spawnSync(
  'npx',
  ['playwright', 'test', 'tests/browser/rashi-association.spec.js'],
  {
    cwd: ROOT,
    stdio: 'inherit',
    env: { ...process.env, YOMA_ASSOC_PLAN_PATH: planPath, MYSUGYA_TEST_MODULE: opts.module },
  }
);

process.exit(playwrightResult.status ?? 1);
