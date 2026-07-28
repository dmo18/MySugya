#!/usr/bin/env node
/**
 * rashi-browser-shards.test.mjs - unit tests for the sharded browser-
 * association evidence pipeline: shardSlice (rashi-browser-shard-runner.mjs),
 * mergeShards (combine-rashi-browser-shards.mjs), and validateArtifact
 * (check-rashi-browser-shard-artifact.mjs).
 *
 * Imports the exact production functions - never re-implements their logic -
 * so these tests cannot drift from what the real sharded workflow and
 * renderer-readiness gate actually run. All inputs are synthetic in-memory
 * fixtures; nothing here touches the filesystem, git, or a real browser.
 */

import { describe, it } from "node:test";
import assert from "node:assert";

import { shardSlice } from "../../scripts/rashi-browser-shard-runner.mjs";
import { mergeShards } from "../../scripts/combine-rashi-browser-shards.mjs";
import { validateArtifact } from "../../scripts/check-rashi-browser-shard-artifact.mjs";

describe("shardSlice", () => {
  const daf173 = Array.from({ length: 173 }, (_, i) => `d${i}`);

  it("covers every daf exactly once across 8 shards", () => {
    const seen = new Set();
    let total = 0;
    for (let i = 0; i < 8; i++) {
      const slice = shardSlice(daf173, i, 8);
      for (const d of slice) {
        assert.ok(!seen.has(d), `${d} appeared in more than one shard`);
        seen.add(d);
      }
      total += slice.length;
    }
    assert.equal(total, 173);
    assert.equal(seen.size, 173);
  });

  it("produces contiguous slices that concatenate back to the original order", () => {
    const rebuilt = [];
    for (let i = 0; i < 5; i++) rebuilt.push(...shardSlice(daf173, i, 5));
    assert.deepEqual(rebuilt, daf173);
  });

  it("shard sizes differ by at most 1", () => {
    const sizes = Array.from({ length: 8 }, (_, i) => shardSlice(daf173, i, 8).length);
    assert.ok(Math.max(...sizes) - Math.min(...sizes) <= 1);
  });
});

describe("mergeShards", () => {
  const full = ["2a", "2b", "3a", "3b"];
  const shardA = { shardIndex: 0, shardCount: 2, dafCovered: ["2a", "2b"], entries: 10, passed: 10, failed: 0 };
  const shardB = { shardIndex: 1, shardCount: 2, dafCovered: ["3a", "3b"], entries: 12, passed: 11, failed: 1 };

  it("sums entries/passed/failed across shards covering every daf exactly once", () => {
    const merged = mergeShards([shardA, shardB], full);
    assert.deepEqual(merged.dafCovered, full);
    assert.equal(merged.totalEntries, 22);
    assert.equal(merged.passed, 21);
    assert.equal(merged.failed, 1);
  });

  it("rejects partial shard coverage (a shard index missing)", () => {
    assert.throws(() => mergeShards([shardA], full), /expected 2 shard files/);
  });

  it("rejects overlapping shard coverage (same daf claimed twice)", () => {
    const overlapping = { ...shardB, dafCovered: ["2a", "3b"] };
    assert.throws(() => mergeShards([shardA, overlapping], full), /more than one shard/);
  });

  it("rejects shards that leave a real daf uncovered", () => {
    const shrunk = { ...shardB, dafCovered: ["3a"] };
    assert.throws(() => mergeShards([shardA, shrunk], full), /did not cover/);
  });

  it("rejects inconsistent shardCount across files", () => {
    const wrongCount = { ...shardB, shardCount: 3 };
    assert.throws(() => mergeShards([shardA, wrongCount], full), /inconsistent shardCount/);
  });

  it("rejects duplicate shardIndex", () => {
    const dup = { ...shardB, shardIndex: 0 };
    assert.throws(() => mergeShards([shardA, dup], full), /duplicate shardIndex/);
  });
});

describe("validateArtifact", () => {
  const fullDaf = ["2a", "2b", "3a"];
  const sha = "abc123";

  function goodArtifact(overrides = {}) {
    return {
      schemaVersion: 1,
      ci: true,
      commitSha: sha,
      workflowRunId: "999",
      workflowRunUrl: "https://example.invalid/runs/999",
      dafCovered: fullDaf,
      totalEntries: 100,
      passed: 100,
      failed: 0,
      ...overrides,
    };
  }

  it("accepts a complete, current, CI-produced, all-passing artifact", () => {
    assert.deepEqual(validateArtifact(goodArtifact(), fullDaf, sha), []);
  });

  it("rejects a missing artifact (null)", () => {
    const errors = validateArtifact(null, fullDaf, sha);
    assert.equal(errors.length, 1);
    assert.match(errors[0], /no artifact found/);
  });

  it("rejects local-only evidence (ci is not true)", () => {
    const errors = validateArtifact(goodArtifact({ ci: false }), fullDaf, sha);
    assert.ok(errors.some(e => /local-only/.test(e)));
  });

  it("rejects stale/wrong-commit evidence (commitSha mismatch)", () => {
    const errors = validateArtifact(goodArtifact({ commitSha: "old-sha" }), fullDaf, sha);
    assert.ok(errors.some(e => /stale or wrong-commit/.test(e)));
  });

  it("rejects partial daf coverage", () => {
    const errors = validateArtifact(goodArtifact({ dafCovered: ["2a", "2b"] }), fullDaf, sha);
    assert.ok(errors.some(e => /partial or invalid daf coverage/.test(e)));
  });

  it("rejects failed evidence (failed > 0)", () => {
    const errors = validateArtifact(goodArtifact({ failed: 2 }), fullDaf, sha);
    assert.ok(errors.some(e => /failed evidence/.test(e)));
  });

  it("reports every failure mode together when several apply at once", () => {
    const errors = validateArtifact(
      goodArtifact({ ci: false, commitSha: "old-sha", failed: 1, dafCovered: ["2a"] }),
      fullDaf,
      sha
    );
    assert.equal(errors.length, 4);
  });
});
