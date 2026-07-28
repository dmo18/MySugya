#!/usr/bin/env node
/**
 * rashi-browser-shard-runner.mjs - runs the exhaustive Rashi linked-
 * association browser assertion for ONE contiguous shard of the 173-daf
 * corpus, and writes a per-shard result JSON that
 * combine-rashi-browser-shards.mjs later merges into the single artifact
 * the renderer-readiness gate consumes (see
 * check-rashi-browser-shard-artifact.mjs).
 *
 * Running all 173 daf through tests/browser/rashi-association.spec.js in
 * one process is reserved for a sharded workflow (run-rashi-association.mjs
 * --exhaustive-corpus deliberately stops after the data-level audit for
 * exactly this reason). This script IS that sharded workflow's per-shard
 * unit: .github/workflows/rashi-browser-shards.yml runs it once per matrix
 * entry, each covering a disjoint contiguous slice of the real, authoritative
 * daf order (from audit_rashi_association.py --list-daf - never a
 * hardcoded or re-derived daf list).
 *
 * Usage:
 *   node scripts/rashi-browser-shard-runner.mjs --shard-index 0 --shard-count 8 --out shard-0.json
 *
 * The spec itself (tests/browser/rashi-association.spec.js) is reused
 * completely unmodified: this script only narrows YOMA_ASSOC_PLAN_PATH to
 * this shard's own daf range, exactly the same mechanism
 * run-rashi-association.mjs already uses for a single --range invocation.
 */
import { spawnSync } from 'node:child_process';
import { mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = resolve(fileURLToPath(import.meta.url), '..');
const ROOT = resolve(__dirname, '..');

function parseArgs(argv) {
  const opts = { shardIndex: null, shardCount: null, out: null };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--shard-index') opts.shardIndex = Number(argv[++i]);
    else if (argv[i] === '--shard-count') opts.shardCount = Number(argv[++i]);
    else if (argv[i] === '--out') opts.out = argv[++i];
  }
  if (opts.shardIndex === null || opts.shardCount === null || !opts.out) {
    console.error('Usage: rashi-browser-shard-runner.mjs --shard-index N --shard-count M --out FILE');
    process.exit(2);
  }
  if (opts.shardIndex < 0 || opts.shardIndex >= opts.shardCount) {
    console.error(`--shard-index ${opts.shardIndex} out of range for --shard-count ${opts.shardCount}`);
    process.exit(2);
  }
  return opts;
}

/** Contiguous, deterministic partition: every daf appears in exactly one
 * shard, shard sizes differ by at most 1, and concatenating shard 0..N-1's
 * slices in order reproduces the full list exactly. */
export function shardSlice(dafList, shardIndex, shardCount) {
  const n = dafList.length;
  const base = Math.floor(n / shardCount);
  const extra = n % shardCount;
  // The first `extra` shards get one additional daf so every daf is covered.
  const start = shardIndex * base + Math.min(shardIndex, extra);
  const size = base + (shardIndex < extra ? 1 : 0);
  return dafList.slice(start, start + size);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const opts = parseArgs(process.argv.slice(2));
  const auditScript = resolve(ROOT, 'modules/yoma/scripts/audit_rashi_association.py');

  const listResult = spawnSync('python3', [auditScript, '--list-daf'], { cwd: ROOT, encoding: 'utf8' });
  if (listResult.status !== 0) {
    console.error('[shard-runner] failed to list daf:', listResult.stderr);
    process.exit(1);
  }
  const fullDafList = JSON.parse(listResult.stdout);
  const dafSlice = shardSlice(fullDafList, opts.shardIndex, opts.shardCount);

  if (dafSlice.length === 0) {
    console.error(`[shard-runner] shard ${opts.shardIndex}/${opts.shardCount} is empty (shardCount exceeds daf count ${fullDafList.length})`);
    process.exit(2);
  }

  console.log(`[shard-runner] shard ${opts.shardIndex}/${opts.shardCount}: ${dafSlice.length} daf (${dafSlice[0]}..${dafSlice[dafSlice.length - 1]})`);

  const planResult = spawnSync(
    'python3',
    [auditScript, '--range-from', dafSlice[0], '--range-to', dafSlice[dafSlice.length - 1], '--json'],
    { cwd: ROOT, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 }
  );
  if (!planResult.stdout) {
    console.error('[shard-runner] auditor produced no output:', planResult.stderr);
    process.exit(1);
  }
  const plan = JSON.parse(planResult.stdout);
  if (!plan.success) {
    console.error(`[shard-runner] auditor found ${plan.error_count} referential-integrity error(s) in this shard's range:`);
    for (const e of plan.errors.slice(0, 20)) console.error(`  ERROR  ${e}`);
    process.exit(1);
  }

  const scratchDir = mkdtempSync(join(tmpdir(), 'rashi-shard-'));
  const planPath = join(scratchDir, 'plan.json');
  writeFileSync(planPath, JSON.stringify(plan), 'utf8');
  console.log(`[shard-runner] plan written (${plan.daf_list.length} daf, ${plan.findings.length} entries); running browser spec...`);

  const playwrightResult = spawnSync(
    'npx',
    ['playwright', 'test', 'tests/browser/rashi-association.spec.js', '--reporter=json'],
    {
      cwd: ROOT,
      encoding: 'utf8',
      maxBuffer: 64 * 1024 * 1024,
      env: { ...process.env, YOMA_ASSOC_PLAN_PATH: planPath },
    }
  );

  let stats = { expected: 0, unexpected: 0, skipped: 0, flaky: 0 };
  try {
    const report = JSON.parse(playwrightResult.stdout);
    stats = report.stats ?? stats;
  } catch {
    console.error('[shard-runner] could not parse Playwright JSON reporter output:');
    console.error(playwrightResult.stdout);
    console.error(playwrightResult.stderr);
    process.exit(1);
  }

  const passed = stats.expected ?? 0;
  const failed = (stats.unexpected ?? 0) + (stats.flaky ?? 0);

  const result = {
    shardIndex: opts.shardIndex,
    shardCount: opts.shardCount,
    dafCovered: dafSlice,
    entries: plan.findings.length,
    passed,
    failed,
  };

  writeFileSync(opts.out, JSON.stringify(result, null, 1) + '\n', 'utf8');
  console.log(`[shard-runner] wrote ${opts.out}: ${JSON.stringify(result)}`);

  process.exit(failed === 0 && playwrightResult.status === 0 ? 0 : 1);
}
