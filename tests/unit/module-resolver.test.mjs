#!/usr/bin/env node
/**
 * module-resolver.test.mjs - Unit tests for shared/module_resolver.js.
 *
 * Imports the exact production resolver (the same file build.mjs will
 * use starting Phase 3 Step 4). Uses a temp-directory search root for
 * synthetic descriptors; Yoma resolution is proven separately against
 * the real modules/yoma/module.json.
 */
import { test, describe, it } from "node:test";
import assert from "node:assert";
import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { resolveModule, listModules, ModuleResolutionError } =
  require("../../shared/module_resolver.js");

const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");

const VALID_FIXTURE = {
  key: "fixturemasechet",
  displayNameEn: "Fixture Masechet",
  displayNameHe: null,
  sefariaTractate: null,
  status: "synthetic",
  publishable: false,
  seder: null,
  dafRange: { first: "2a", last: "3a" },
  totalDaf: 3,
  paths: {
    root: "modules/fixturemasechet",
    scriptsRoot: "modules/fixturemasechet/scripts",
    sourceAssetsRoot: "modules/fixturemasechet/assets",
    generatedAssetsRoot: "modules/fixturemasechet/assets",
    sourceStore: "modules/fixturemasechet/source_store.js",
    learningDataDir: "modules/fixturemasechet/assets/learning/fixturemasechet",
    learningDataFile: "modules/fixturemasechet/learning_data.js",
    coverageFile: "modules/fixturemasechet/coverage.json",
    chapterMetadataLocation: null,
  },
  schemaMapRef: "shared/schema_map.js",
  capabilities: {
    rashi: { enabled: false },
    literalTranslation: { enabled: false },
    sourceAcquisition: {
      strategy: "local-fixture",
      fixtureInputDir: "modules/fixturemasechet/assets/fixture_source",
    },
  },
  browserTest: { defaultTargetDaf: "2a" },
  docsOutput: {},
  buildRuntime: { dataScript: "modules/fixturemasechet/learning_data.js" },
};

function writeDescriptor(root, key, data) {
  const dir = path.join(root, key);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, "module.json"), JSON.stringify(data));
}

// A structurally valid descriptor for a fresh key, with every path field
// (not just paths.root) correctly rewritten - unlike a bare deep clone of
// VALID_FIXTURE with only key/paths.root changed, which leaves
// scriptsRoot/sourceAssetsRoot/etc. pointed at the ORIGINAL fixturemasechet
// paths and trips the unrelated "not under the module's own root" check
// before ever reaching whatever a given test actually means to exercise.
// Callers mutate the specific field(s) under test on the returned object.
function fixtureFor(key) {
  const oldRoot = VALID_FIXTURE.paths.root;
  const newRoot = `modules/${key}`;
  const rewrite = (p) => (p.startsWith(oldRoot) ? newRoot + p.slice(oldRoot.length) : p);
  const d = JSON.parse(JSON.stringify(VALID_FIXTURE));
  d.key = key;
  for (const k of Object.keys(d.paths)) {
    if (typeof d.paths[k] === "string") d.paths[k] = rewrite(d.paths[k]);
  }
  d.buildRuntime.dataScript = rewrite(d.buildRuntime.dataScript);
  if (d.capabilities.sourceAcquisition && d.capabilities.sourceAcquisition.fixtureInputDir) {
    d.capabilities.sourceAcquisition.fixtureInputDir =
      rewrite(d.capabilities.sourceAcquisition.fixtureInputDir);
  }
  return d;
}

function mkTempRoot() {
  return fs.mkdtempSync(path.join(os.tmpdir(), "module-resolver-test-"));
}

function assertThrowsCode(fn, code, message) {
  assert.throws(fn, (err) => {
    assert.ok(err instanceof Error, "should throw an Error");
    assert.equal(err.code, code, `expected code ${code}, got ${err.code}`);
    return true;
  }, message);
}

describe("resolveModule: valid Yoma resolution", () => {
  it("resolves the real modules/yoma/module.json", () => {
    const d = resolveModule("yoma", REPO_ROOT);
    assert.equal(d.key, "yoma");
    assert.equal(d.status, "production");
    assert.equal(d.publishable, true);
    assert.equal(d.paths.root, "modules/yoma");
  });

  it("lists yoma under the real modules/ tree", () => {
    const keys = listModules(REPO_ROOT);
    assert.ok(keys.includes("yoma"));
  });
});

describe("resolveModule: valid fixture resolution", () => {
  it("resolves a synthetic descriptor under a temp search root", () => {
    const root = mkTempRoot();
    writeDescriptor(root, "fixturemasechet", VALID_FIXTURE);
    const d = resolveModule("fixturemasechet", REPO_ROOT, root);
    assert.equal(d.status, "synthetic");
    assert.equal(d.publishable, false);
  });

  it("lists the fixture under the temp root only", () => {
    const root = mkTempRoot();
    writeDescriptor(root, "fixturemasechet", VALID_FIXTURE);
    assert.deepEqual(listModules(REPO_ROOT, root), ["fixturemasechet"]);
  });
});

describe("resolveModule: unknown module", () => {
  it("raises UNKNOWN_MODULE, never falls back to yoma", () => {
    const root = mkTempRoot();
    assertThrowsCode(() => resolveModule("doesnotexist", REPO_ROOT, root), "UNKNOWN_MODULE");
  });
});

describe("resolveModule: missing descriptor", () => {
  it("directory exists but module.json is missing", () => {
    const root = mkTempRoot();
    fs.mkdirSync(path.join(root, "fixturemasechet"), { recursive: true });
    assertThrowsCode(() => resolveModule("fixturemasechet", REPO_ROOT, root), "UNKNOWN_MODULE");
  });
});

describe("resolveModule: malformed descriptor", () => {
  it("invalid JSON raises MALFORMED_DESCRIPTOR", () => {
    const root = mkTempRoot();
    fs.mkdirSync(path.join(root, "brokenmod"), { recursive: true });
    fs.writeFileSync(path.join(root, "brokenmod", "module.json"), "{not valid json");
    assertThrowsCode(() => resolveModule("brokenmod", REPO_ROOT, root), "MALFORMED_DESCRIPTOR");
  });

  it("a JSON array root raises MALFORMED_DESCRIPTOR", () => {
    const root = mkTempRoot();
    fs.mkdirSync(path.join(root, "arraymod"), { recursive: true });
    fs.writeFileSync(path.join(root, "arraymod", "module.json"), "[]");
    assertThrowsCode(() => resolveModule("arraymod", REPO_ROOT, root), "MALFORMED_DESCRIPTOR");
  });
});

describe("resolveModule: missing required field", () => {
  it("raises MISSING_FIELD for an absent top-level field", () => {
    const root = mkTempRoot();
    const bad = fixtureFor("missingfieldmod");
    delete bad.totalDaf;
    writeDescriptor(root, "missingfieldmod", bad);
    assertThrowsCode(() => resolveModule("missingfieldmod", REPO_ROOT, root), "MISSING_FIELD");
  });
});

describe("resolveModule: path traversal", () => {
  it("rejects '../etc' as a key before any filesystem access", () => {
    const root = mkTempRoot();
    assertThrowsCode(() => resolveModule("../etc", REPO_ROOT, root), "INVALID_KEY");
  });

  it("rejects a key containing a slash", () => {
    const root = mkTempRoot();
    assertThrowsCode(() => resolveModule("modules/yoma", REPO_ROOT, root), "INVALID_KEY");
  });

  it("rejects an uppercase key", () => {
    const root = mkTempRoot();
    assertThrowsCode(() => resolveModule("Yoma", REPO_ROOT, root), "INVALID_KEY");
  });
});

describe("resolveModule: feature inconsistency", () => {
  it("enabled capability missing required config", () => {
    const root = mkTempRoot();
    const bad = fixtureFor("inconmod");
    bad.capabilities.rashi = { enabled: true };
    writeDescriptor(root, "inconmod", bad);
    assertThrowsCode(() => resolveModule("inconmod", REPO_ROOT, root), "FEATURE_INCONSISTENCY");
  });

  it("disabled capability declaring config anyway", () => {
    const root = mkTempRoot();
    const bad = fixtureFor("disabledmod");
    bad.capabilities.rashi = { enabled: false, allowlistsRoot: "modules/disabledmod/x" };
    writeDescriptor(root, "disabledmod", bad);
    assertThrowsCode(() => resolveModule("disabledmod", REPO_ROOT, root), "FEATURE_INCONSISTENCY");
  });

  it("a non-publishable-fixture rule: synthetic + publishable=true is rejected", () => {
    const root = mkTempRoot();
    const bad = fixtureFor("pubsynthmod");
    bad.publishable = true;
    writeDescriptor(root, "pubsynthmod", bad);
    assertThrowsCode(() => resolveModule("pubsynthmod", REPO_ROOT, root), "FEATURE_INCONSISTENCY");
  });

  it("buildRuntime.dataScript disagreeing with paths.learningDataFile", () => {
    const root = mkTempRoot();
    const bad = fixtureFor("driftmod");
    bad.buildRuntime.dataScript = "modules/driftmod/OTHER_FILE.js";
    writeDescriptor(root, "driftmod", bad);
    assertThrowsCode(() => resolveModule("driftmod", REPO_ROOT, root), "FEATURE_INCONSISTENCY");
  });

  it("paths.root disagreeing with the module's own directory key", () => {
    const root = mkTempRoot();
    const bad = fixtureFor("rootmismatchmod");
    bad.paths.root = "modules/somethingelse";
    writeDescriptor(root, "rootmismatchmod", bad);
    assertThrowsCode(() => resolveModule("rootmismatchmod", REPO_ROOT, root), "MALFORMED_DESCRIPTOR");
  });
});

describe("resolveModule: source acquisition strategy (Phase 3 Step 3B)", () => {
  it("missing capabilities.sourceAcquisition entirely is MISSING_FIELD", () => {
    const root = mkTempRoot();
    const bad = fixtureFor("nosamod");
    delete bad.capabilities.sourceAcquisition;
    writeDescriptor(root, "nosamod", bad);
    assertThrowsCode(() => resolveModule("nosamod", REPO_ROOT, root), "MISSING_FIELD");
  });

  it("an unrecognised strategy value is MALFORMED_DESCRIPTOR", () => {
    const root = mkTempRoot();
    const bad = fixtureFor("badstratmod");
    bad.capabilities.sourceAcquisition = { strategy: "telepathy" };
    writeDescriptor(root, "badstratmod", bad);
    assertThrowsCode(() => resolveModule("badstratmod", REPO_ROOT, root), "MALFORMED_DESCRIPTOR");
  });

  it("remote-fetch without sourceSystem/fetchScript is MISSING_FIELD", () => {
    const root = mkTempRoot();
    const bad = fixtureFor("remotemissingmod");
    bad.capabilities.sourceAcquisition = { strategy: "remote-fetch" };
    writeDescriptor(root, "remotemissingmod", bad);
    assertThrowsCode(() => resolveModule("remotemissingmod", REPO_ROOT, root), "MISSING_FIELD");
  });

  it("local-fixture without fixtureInputDir is MISSING_FIELD", () => {
    const root = mkTempRoot();
    const bad = fixtureFor("localmissingmod");
    bad.capabilities.sourceAcquisition = { strategy: "local-fixture" };
    writeDescriptor(root, "localmissingmod", bad);
    assertThrowsCode(() => resolveModule("localmissingmod", REPO_ROOT, root), "MISSING_FIELD");
  });

  it("remote-fetch declaring fixtureInputDir anyway is FEATURE_INCONSISTENCY", () => {
    const root = mkTempRoot();
    const bad = fixtureFor("remotewithfixturemod");
    bad.capabilities.sourceAcquisition = {
      strategy: "remote-fetch", sourceSystem: "x", fetchScript: "y",
      fixtureInputDir: "modules/remotewithfixturemod/assets/fixture_source",
    };
    writeDescriptor(root, "remotewithfixturemod", bad);
    assertThrowsCode(() => resolveModule("remotewithfixturemod", REPO_ROOT, root), "FEATURE_INCONSISTENCY");
  });

  it("local-fixture declaring sourceSystem anyway is FEATURE_INCONSISTENCY", () => {
    const root = mkTempRoot();
    const bad = fixtureFor("localwithremotemod");
    bad.capabilities.sourceAcquisition = {
      strategy: "local-fixture",
      fixtureInputDir: "modules/localwithremotemod/assets/fixture_source",
      sourceSystem: "should not be here",
    };
    writeDescriptor(root, "localwithremotemod", bad);
    assertThrowsCode(() => resolveModule("localwithremotemod", REPO_ROOT, root), "FEATURE_INCONSISTENCY");
  });
});

describe("resolveModule: no implicit Yoma fallback", () => {
  it("requesting 'yoma' against a root with no yoma descriptor fails cleanly", () => {
    const root = mkTempRoot();
    assertThrowsCode(() => resolveModule("yoma", REPO_ROOT, root), "UNKNOWN_MODULE");
  });
});
