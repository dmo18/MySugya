#!/usr/bin/env node
/**
 * rashi-association.test.mjs - Unit tests for groupRashiByLinkedId
 *
 * Imports the exact production function from shared/rashi_association.js
 * (the same file app.jsx loads in the browser). This file never
 * re-implements or copies the function, so production and test cannot drift.
 */

import { test, describe, it } from "node:test";
import assert from "node:assert";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { groupRashiByLinkedId } = require("../../shared/rashi_association.js");

describe("groupRashiByLinkedId", () => {
  it("should handle empty input", () => {
    const map = groupRashiByLinkedId(null);
    assert.equal(map.size, 0);
  });

  it("should handle undefined input", () => {
    const map = groupRashiByLinkedId(undefined);
    assert.equal(map.size, 0);
  });

  it("should group single-link entries", () => {
    const rashiLines = [
      { id: "r1", linkedGemaraLineIds: ["l1"] }
    ];
    const map = groupRashiByLinkedId(rashiLines);
    assert.equal(map.size, 1);
    assert.equal(map.get("l1").length, 1);
    assert.equal(map.get("l1")[0].id, "r1");
  });

  it("should group multi-link entries under all targets", () => {
    const rashiLines = [
      { id: "r1", linkedGemaraLineIds: ["l1", "l2"] }
    ];
    const map = groupRashiByLinkedId(rashiLines);
    assert.equal(map.size, 2);
    assert.equal(map.get("l1").length, 1);
    assert.equal(map.get("l2").length, 1);
    assert.equal(map.get("l1")[0].id, "r1");
    assert.equal(map.get("l2")[0].id, "r1");
  });

  it("should handle many-to-one mapping (same target)", () => {
    const rashiLines = [
      { id: "r1", linkedGemaraLineIds: ["l1"] },
      { id: "r2", linkedGemaraLineIds: ["l1"] }
    ];
    const map = groupRashiByLinkedId(rashiLines);
    assert.equal(map.size, 1);
    assert.equal(map.get("l1").length, 2);
  });

  it("should not attach entries with empty linkedGemaraLineIds", () => {
    const rashiLines = [
      { id: "r1", linkedGemaraLineIds: [] }
    ];
    const map = groupRashiByLinkedId(rashiLines);
    assert.equal(map.size, 0);
  });

  it("should not use vilnaLine coincidence as fallback", () => {
    const rashiLines = [
      { id: "r1", vilnaLine: 5, linkedGemaraLineIds: [] }
    ];
    const map = groupRashiByLinkedId(rashiLines);
    // Entry should not be attached anywhere, even though vilnaLine looks
    // like it could coincidentally match a Gemara line number.
    assert.equal(map.size, 0);
  });

  it("should distinguish suffixed line IDs", () => {
    const rashiLines = [
      { id: "r1", linkedGemaraLineIds: ["l1a"] },
      { id: "r2", linkedGemaraLineIds: ["l1b"] }
    ];
    const map = groupRashiByLinkedId(rashiLines);
    assert.equal(map.size, 2);
    assert.equal(map.get("l1a").length, 1);
    assert.equal(map.get("l1b").length, 1);
    // A bare "l1" must never be treated as equivalent to "l1a"/"l1b".
    assert.equal(map.has("l1"), false);
  });

  it("should treat Mishnah and Gemara target ids identically (no special-casing)", () => {
    const rashiLines = [
      { id: "r1", linkedGemaraLineIds: ["yoma-002a-l01"] },
      { id: "r2", linkedGemaraLineIds: ["yoma-002a-l02"] }
    ];
    const map = groupRashiByLinkedId(rashiLines);
    assert.equal(map.size, 2);
    assert.equal(map.get("yoma-002a-l01").length, 1);
    assert.equal(map.get("yoma-002a-l02").length, 1);
  });

  it("should never attach an entry under a target it did not declare", () => {
    const rashiA = { id: "rA", he: "he-A", en: "en-A", linkedGemaraLineIds: ["l1"] };
    const rashiB = { id: "rB", he: "he-B", en: "en-B", linkedGemaraLineIds: ["l2"] };
    const map = groupRashiByLinkedId([rashiA, rashiB]);
    // l1 must contain only rA; an unrelated extra target (rB under l1) would
    // mean two entries with disjoint declared targets bled into each other.
    assert.equal(map.get("l1").length, 1);
    assert.equal(map.get("l1")[0].id, "rA");
    assert.equal(map.get("l2").length, 1);
    assert.equal(map.get("l2")[0].id, "rB");
  });

  it("should never pair one entry's Hebrew with another entry's English", () => {
    const rashiA = { id: "rA", he: "he-A", en: "en-A", linkedGemaraLineIds: ["l1"] };
    const rashiB = { id: "rB", he: "he-B", en: "en-B", linkedGemaraLineIds: ["l1"] };
    const map = groupRashiByLinkedId([rashiA, rashiB]);
    const atL1 = map.get("l1");
    assert.equal(atL1.length, 2);
    // Each grouped object must retain its own original he/en pairing - the
    // grouping step must never construct a new object that recombines
    // fields from two different source entries.
    const byId = Object.fromEntries(atL1.map(r => [r.id, r]));
    assert.equal(byId.rA.he, "he-A");
    assert.equal(byId.rA.en, "en-A");
    assert.equal(byId.rB.he, "he-B");
    assert.equal(byId.rB.en, "en-B");
  });

  it("should handle null/undefined entry fields safely", () => {
    const rashiLines = [
      { id: "r1", linkedGemaraLineIds: undefined },
      { id: "r2", linkedGemaraLineIds: null },
      { id: "r3", linkedGemaraLineIds: ["l1"] }
    ];
    const map = groupRashiByLinkedId(rashiLines);
    assert.equal(map.size, 1);
    assert.equal(map.get("l1").length, 1);
    assert.equal(map.get("l1")[0].id, "r3");
  });
});
