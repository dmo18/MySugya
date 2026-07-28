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
const { groupRashiByLinkedId, rashiRendererFromUrl } = require("../../shared/rashi_association.js");

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

/* ------------------------------------------------------------------
   rashiRendererFromUrl - renderer selection after the VERSION 15.338
   cutover that made linked the production default.

   Exercises the real exported selector (never a re-implementation) against
   a stubbed window.location.search, and asserts the selection is derived
   only from the URL: nothing is written to localStorage or any other
   storage, and no value carries over between navigations.
   ------------------------------------------------------------------ */
describe("rashiRendererFromUrl", () => {
  const originalWindow = globalThis.window;

  function withSearch(search, fn) {
    const storageWrites = [];
    globalThis.window = {
      location: { search },
      localStorage: {
        setItem: (k, v) => storageWrites.push([k, v]),
        getItem: () => null,
        removeItem: k => storageWrites.push(["remove", k]),
      },
      sessionStorage: {
        setItem: (k, v) => storageWrites.push([k, v]),
        getItem: () => null,
      },
    };
    try {
      return { result: fn(), storageWrites };
    } finally {
      globalThis.window = originalWindow;
    }
  }

  it("selects linked when there is no rashiAssoc parameter (production default)", () => {
    assert.equal(withSearch("", rashiRendererFromUrl).result, "linked");
    assert.equal(withSearch("?module=yoma&daf=2a", rashiRendererFromUrl).result, "linked");
  });

  it("selects linked for an explicit ?rashiAssoc=linked (still accepted)", () => {
    assert.equal(withSearch("?rashiAssoc=linked", rashiRendererFromUrl).result, "linked");
    assert.equal(withSearch("?module=yoma&daf=2a&rashiAssoc=linked", rashiRendererFromUrl).result, "linked");
  });

  it("selects legacy only for an explicit ?rashiAssoc=legacy (rollback override)", () => {
    assert.equal(withSearch("?rashiAssoc=legacy", rashiRendererFromUrl).result, "legacy");
    assert.equal(withSearch("?module=yoma&daf=2a&rashiAssoc=legacy", rashiRendererFromUrl).result, "legacy");
  });

  it("selects linked for unknown or malformed values, never silently legacy", () => {
    for (const bad of [
      "?rashiAssoc=",
      "?rashiAssoc=LEGACY",
      "?rashiAssoc=Legacy",
      "?rashiAssoc=legacy2",
      "?rashiAssoc=lega%20cy",
      "?rashiAssoc=true",
      "?rashiAssoc=0",
      "?rashiAssoc=linked&rashiAssoc=legacy2",
      "?rashiassoc=legacy",
    ]) {
      assert.equal(withSearch(bad, rashiRendererFromUrl).result, "linked", `expected linked for ${bad}`);
    }
  });

  it("never persists the selection to localStorage or sessionStorage", () => {
    for (const search of ["", "?rashiAssoc=linked", "?rashiAssoc=legacy", "?rashiAssoc=bogus"]) {
      const { storageWrites } = withSearch(search, rashiRendererFromUrl);
      assert.deepEqual(storageWrites, [], `expected no storage writes for ${search}`);
    }
  });

  it("does not carry a selection across navigations (re-reads the URL each call)", () => {
    // A legacy visit must not pin legacy for the next, parameter-free visit.
    assert.equal(withSearch("?rashiAssoc=legacy", rashiRendererFromUrl).result, "legacy");
    assert.equal(withSearch("", rashiRendererFromUrl).result, "linked");
    // ...and the reverse ordering is equally stateless.
    assert.equal(withSearch("?rashiAssoc=linked", rashiRendererFromUrl).result, "linked");
    assert.equal(withSearch("?rashiAssoc=legacy", rashiRendererFromUrl).result, "legacy");
  });

  it("falls back to the linked default when there is no window at all", () => {
    const saved = globalThis.window;
    globalThis.window = undefined;
    try {
      assert.equal(rashiRendererFromUrl(), "linked");
    } finally {
      globalThis.window = saved;
    }
  });
});
