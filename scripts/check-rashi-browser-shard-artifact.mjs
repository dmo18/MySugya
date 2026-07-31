#!/usr/bin/env node
/**
 * check-rashi-browser-shard-artifact.mjs - validates the combined,
 * sharded browser-association result artifact produced by
 * .github/workflows/rashi-browser-shards.yml (via
 * rashi-browser-shard-runner.mjs + combine-rashi-browser-shards.mjs)
 * before the renderer-readiness gate will accept it as evidence that the
 * exhaustive 173-daf browser association run passed.
 *
 * This is the ONLY mechanism by which "exhaustive browser corpus
 * association run" can pass in scripts/audit-rashi-renderer-readiness.mjs.
 * It never hardcodes a pass and never accepts a manually stated result -
 * only a real generated file, checked against the live repository's own
 * authoritative daf list and current commit:
 *
 *   - missing:    no file at the expected path
 *   - partial:    dafCovered is not exactly the full 173-daf set
 *   - stale/wrong-commit: commitSha does not match the current HEAD
 *   - local-only: ci !== true (the file was not produced by the actual
 *                 workflow's combine step, which is the only caller that
 *                 passes --ci)
 *   - failed:     failed > 0, or entries/passed/failed disagree
 *
 * Usage:
 *   node scripts/check-rashi-browser-shard-artifact.mjs [path]
 * Default path: modules/yoma/scripts/allowlists/rashi_browser_shard_result.json
 * (override with the RASHI_BROWSER_SHARD_RESULT_PATH env var).
 */
import { spawnSync } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const __dirname = resolve(fileURLToPath(import.meta.url), '..');
const ROOT = resolve(__dirname, '..');
const require = createRequire(import.meta.url);

export const DEFAULT_ARTIFACT_PATH = resolve(ROOT, 'modules/yoma/scripts/allowlists/rashi_browser_shard_result.json');

/** Pure validation: artifact is the parsed JSON (or null if the file did
 * not exist / did not parse), fullDafList is the authoritative ordered daf
 * list, currentCommitSha is the live repo's HEAD. Returns a list of error
 * strings (empty means valid). No filesystem or process access here, so
 * every failure mode can be exercised with synthetic fixtures. */
export function validateArtifact(artifact, fullDafList, currentCommitSha) {
  if (!artifact) return ['no artifact found (missing evidence)'];

  const errors = [];

  if (artifact.ci !== true) {
    errors.push(`local-only evidence: ci=${JSON.stringify(artifact.ci)} (only the workflow's combine step, run with --ci, produces valid evidence)`);
  }

  if (artifact.commitSha !== currentCommitSha) {
    errors.push(`stale or wrong-commit evidence: artifact commitSha=${JSON.stringify(artifact.commitSha)}, current HEAD=${JSON.stringify(currentCommitSha)}`);
  }

  const covered = Array.isArray(artifact.dafCovered) ? artifact.dafCovered : [];
  const coveredSet = new Set(covered);
  const missing = fullDafList.filter(d => !coveredSet.has(d));
  const extra = covered.filter(d => !fullDafList.includes(d));
  const duplicates = covered.length !== coveredSet.size;
  if (missing.length || extra.length || duplicates) {
    errors.push(
      `partial or invalid daf coverage: ${covered.length}/${fullDafList.length} daf listed`
      + (missing.length ? `, missing ${missing.length} (e.g. ${missing.slice(0, 5).join(', ')})` : '')
      + (extra.length ? `, ${extra.length} not in the authoritative list` : '')
      + (duplicates ? ', contains duplicate daf entries' : '')
    );
  }

  if (typeof artifact.failed !== 'number' || artifact.failed > 0) {
    errors.push(`failed evidence: failed=${JSON.stringify(artifact.failed)} (must be exactly 0)`);
  }

  if (typeof artifact.totalEntries !== 'number' || typeof artifact.passed !== 'number') {
    errors.push('missing or non-numeric totalEntries/passed fields');
  }

  return errors;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const moduleArg = process.argv.indexOf('--module');
  const moduleKey = moduleArg !== -1 ? process.argv[moduleArg + 1] : 'yoma';
  const { resolveRashiModule } = require('../shared/module_resolver.js');
  let descriptor;
  try {
    descriptor = resolveRashiModule(moduleKey, ROOT);
  } catch (e) {
    console.error(`FAILED: ${e.code}: ${e.message}`);
    process.exit(1);
  }

  const positional = process.argv.slice(2).filter((a, i, arr) =>
    a !== '--module' && arr[i - 1] !== '--module');
  const path = positional[0]
    ?? process.env.RASHI_BROWSER_SHARD_RESULT_PATH
    ?? (moduleKey === 'yoma'
      ? DEFAULT_ARTIFACT_PATH
      : resolve(ROOT, descriptor.paths.scriptsRoot, 'allowlists', 'rashi_browser_shard_result.json'));

  let artifact = null;
  if (existsSync(path)) {
    try {
      artifact = JSON.parse(readFileSync(path, 'utf8'));
    } catch (e) {
      console.error(`FAILED: could not parse ${path}: ${e.message}`);
      process.exit(1);
    }
  }

  const auditScript = resolve(ROOT, descriptor.paths.scriptsRoot, 'audit_rashi_association.py');
  const listResult = spawnSync('python3', [auditScript, '--list-daf'], { cwd: ROOT, encoding: 'utf8' });
  if (listResult.status !== 0) {
    console.error('FAILED: could not determine the authoritative daf list:', listResult.stderr);
    process.exit(1);
  }
  const fullDafList = JSON.parse(listResult.stdout);
  const currentCommitSha = spawnSync('git', ['rev-parse', 'HEAD'], { cwd: ROOT, encoding: 'utf8' }).stdout.trim();

  const errors = validateArtifact(artifact, fullDafList, currentCommitSha);
  if (errors.length) {
    console.error(`FAILED: browser shard artifact at ${path} rejected:`);
    for (const e of errors) console.error(`  - ${e}`);
    process.exit(1);
  }

  console.log(
    `OK: browser shard artifact valid - ${artifact.dafCovered.length}/${fullDafList.length} daf, `
    + `${artifact.totalEntries} entries, ${artifact.passed} passed, ${artifact.failed} failed, `
    + `commit ${artifact.commitSha}, ci=${artifact.ci}.`
  );
}
