#!/usr/bin/env node
/**
 * combine-rashi-browser-shards.mjs - merges the per-shard result files
 * written by rashi-browser-shard-runner.mjs into the single combined
 * artifact that check-rashi-browser-shard-artifact.mjs (and the
 * renderer-readiness gate) validates.
 *
 * Verifies the shards' dafCovered lists union to EXACTLY the real,
 * authoritative 173-daf list (audit_rashi_association.py --list-daf) with
 * no gaps and no overlaps, before summing entries/passed/failed and
 * stamping provenance (commit SHA, CI run id/url, generatedAt). Refuses to
 * write a combined result over partial or overlapping shard coverage - a
 * bug in the shard split must fail loudly here, not silently under-report.
 *
 * Usage (as run by .github/workflows/rashi-browser-shards.yml):
 *   node scripts/combine-rashi-browser-shards.mjs shard-*.json \
 *     --out rashi_browser_shard_result.json \
 *     --ci --commit-sha "$GITHUB_SHA" \
 *     --run-id "$GITHUB_RUN_ID" --run-url "$RUN_URL"
 *
 * Without --ci, the combined result is stamped ci:false - the readiness
 * gate rejects that as local-only evidence, never machine evidence of an
 * actual CI run, regardless of how plausible its counts look.
 */
import { spawnSync } from 'node:child_process';
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = resolve(fileURLToPath(import.meta.url), '..');
const ROOT = resolve(__dirname, '..');

/** Pure merge: shards is an array of {shardIndex, shardCount, dafCovered,
 * entries, passed, failed}; fullDafList is the authoritative ordered daf
 * list. Throws on any gap, overlap, or shard-count mismatch - never
 * silently drops or double-counts a daf. Returns the merged totals (without
 * provenance fields, which the caller attaches). */
export function mergeShards(shards, fullDafList) {
  if (shards.length === 0) throw new Error('no shard result files provided');

  const shardCounts = new Set(shards.map(s => s.shardCount));
  if (shardCounts.size !== 1) {
    throw new Error(`inconsistent shardCount across shard files: ${[...shardCounts].join(', ')}`);
  }
  const expectedShardCount = [...shardCounts][0];
  if (shards.length !== expectedShardCount) {
    throw new Error(`expected ${expectedShardCount} shard files (per shardCount), got ${shards.length}`);
  }

  const seenIndices = new Set();
  const dafSeenCount = new Map();
  for (const s of shards) {
    if (seenIndices.has(s.shardIndex)) throw new Error(`duplicate shardIndex ${s.shardIndex}`);
    seenIndices.add(s.shardIndex);
    for (const daf of s.dafCovered) {
      dafSeenCount.set(daf, (dafSeenCount.get(daf) ?? 0) + 1);
    }
  }
  for (let i = 0; i < expectedShardCount; i++) {
    if (!seenIndices.has(i)) throw new Error(`missing shardIndex ${i} of ${expectedShardCount}`);
  }

  const overlap = [...dafSeenCount.entries()].filter(([, count]) => count > 1).map(([daf]) => daf);
  if (overlap.length) throw new Error(`daf covered by more than one shard: ${overlap.join(', ')}`);

  const covered = new Set(dafSeenCount.keys());
  const missing = fullDafList.filter(d => !covered.has(d));
  if (missing.length) throw new Error(`shards did not cover ${missing.length} daf: ${missing.slice(0, 10).join(', ')}${missing.length > 10 ? ', ...' : ''}`);
  const extra = [...covered].filter(d => !fullDafList.includes(d));
  if (extra.length) throw new Error(`shards covered daf not in the authoritative list: ${extra.join(', ')}`);

  const totalEntries = shards.reduce((sum, s) => sum + s.entries, 0);
  const passed = shards.reduce((sum, s) => sum + s.passed, 0);
  const failed = shards.reduce((sum, s) => sum + s.failed, 0);

  return {
    dafCovered: fullDafList,
    totalEntries,
    passed,
    failed,
    shardCount: expectedShardCount,
  };
}

function parseArgs(argv) {
  const opts = { files: [], out: null, ci: false, commitSha: null, runId: null, runUrl: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--out') opts.out = argv[++i];
    else if (a === '--ci') opts.ci = true;
    else if (a === '--commit-sha') opts.commitSha = argv[++i];
    else if (a === '--run-id') opts.runId = argv[++i];
    else if (a === '--run-url') opts.runUrl = argv[++i];
    else opts.files.push(a);
  }
  if (!opts.out || opts.files.length === 0) {
    console.error('Usage: combine-rashi-browser-shards.mjs <shard files...> --out FILE [--ci --commit-sha SHA --run-id ID --run-url URL]');
    process.exit(2);
  }
  return opts;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const opts = parseArgs(process.argv.slice(2));
  const shards = opts.files.map(f => JSON.parse(readFileSync(f, 'utf8')));

  const auditScript = resolve(ROOT, 'modules/yoma/scripts/audit_rashi_association.py');
  const listResult = spawnSync('python3', [auditScript, '--list-daf'], { cwd: ROOT, encoding: 'utf8' });
  if (listResult.status !== 0) {
    console.error('[combine-shards] failed to list authoritative daf order:', listResult.stderr);
    process.exit(1);
  }
  const fullDafList = JSON.parse(listResult.stdout);

  let merged;
  try {
    merged = mergeShards(shards, fullDafList);
  } catch (e) {
    console.error(`[combine-shards] FAILED: ${e.message}`);
    process.exit(1);
  }

  const commitSha = opts.commitSha ?? spawnSync('git', ['rev-parse', 'HEAD'], { cwd: ROOT, encoding: 'utf8' }).stdout.trim();

  const combined = {
    schemaVersion: 1,
    generatedAt: new Date().toISOString(),
    ci: opts.ci,
    commitSha,
    workflowRunId: opts.runId,
    workflowRunUrl: opts.runUrl,
    dafCovered: merged.dafCovered,
    totalEntries: merged.totalEntries,
    passed: merged.passed,
    failed: merged.failed,
    shardCount: merged.shardCount,
  };

  writeFileSync(opts.out, JSON.stringify(combined, null, 1) + '\n', 'utf8');
  console.log(`[combine-shards] wrote ${opts.out}: ${merged.dafCovered.length} daf, ${merged.totalEntries} entries, ${merged.passed} passed, ${merged.failed} failed, ci=${opts.ci}`);
  process.exit(merged.failed === 0 ? 0 : 1);
}
