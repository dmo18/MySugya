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
    const bad = JSON.parse(JSON.stringify(VALID_FIXTURE));
    bad.key = "missingfieldmod";
    bad.paths.root = "modules/missingfieldmod";
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
    const bad = JSON.parse(JSON.stringify(VALID_FIXTURE));
    bad.key = "inconmod";
    bad.paths.root = "modules/inconmod";
    bad.capabilities.rashi = { enabled: true };
    writeDescriptor(root, "inconmod", bad);
    assertThrowsCode(() => resolveModule("inconmod", REPO_ROOT, root), "FEATURE_INCONSISTENCY");
  });

  it("disabled capability declaring config anyway", () => {
    const root = mkTempRoot();
    const bad = JSON.parse(JSON.stringify(VALID_FIXTURE));
    bad.key = "disabledmod";
    bad.paths.root = "modules/disabledmod";
    bad.capabilities.rashi = { enabled: false, allowlistsRoot: "modules/disabledmod/x" };
    writeDescriptor(root, "disabledmod", bad);
    assertThrowsCode(() => resolveModule("disabledmod", REPO_ROOT, root), "FEATURE_INCONSISTENCY");
  });

  it("a non-publishable-fixture rule: synthetic + publishable=true is rejected", () => {
    const root = mkTempRoot();
    const bad = JSON.parse(JSON.stringify(VALID_FIXTURE));
    bad.key = "pubsynthmod";
    bad.paths.root = "modules/pubsynthmod";
    bad.publishable = true;
    writeDescriptor(root, "pubsynthmod", bad);
    assertThrowsCode(() => resolveModule("pubsynthmod", REPO_ROOT, root), "FEATURE_INCONSISTENCY");
  });

  it("buildRuntime.dataScript disagreeing with paths.learningDataFile", () => {
    const root = mkTempRoot();
    const bad = JSON.parse(JSON.stringify(VALID_FIXTURE));
    bad.key = "driftmod";
    bad.paths.root = "modules/driftmod";
    bad.buildRuntime.dataScript = "modules/driftmod/OTHER_FILE.js";
    writeDescriptor(root, "driftmod", bad);
    assertThrowsCode(() => resolveModule("driftmod", REPO_ROOT, root), "FEATURE_INCONSISTENCY");
  });

  it("paths.root disagreeing with the module's own directory key", () => {
    const root = mkTempRoot();
    const bad = JSON.parse(JSON.stringify(VALID_FIXTURE));
    bad.key = "rootmismatchmod";
    // paths.root deliberately left as the original fixture value
    writeDescriptor(root, "rootmismatchmod", bad);
    assertThrowsCode(() => resolveModule("rootmismatchmod", REPO_ROOT, root), "MALFORMED_DESCRIPTOR");
  });
});

describe("resolveModule: no implicit Yoma fallback", () => {
  it("requesting 'yoma' against a root with no yoma descriptor fails cleanly", () => {
    const root = mkTempRoot();
    assertThrowsCode(() => resolveModule("yoma", REPO_ROOT, root), "UNKNOWN_MODULE");
  });
});
