/**
 * module_resolver.js - the canonical way to resolve a module descriptor,
 * JS side (for build.mjs and future .mjs tools, migrated onto this
 * starting Phase 3 Step 4).
 *
 * Full contract: docs/reports/module-descriptor-contract.md. Independent
 * re-implementation of scripts/module_resolver.py's validation rules -
 * deliberately not shared code across languages, so a bug in one is not
 * automatically a bug in the other.
 *
 * No implicit default module. Every caller passes an explicit key.
 *
 * Dual-usable like the rest of shared/: a plain script with no import
 * side effects when read directly, plus a CommonJS export guard for
 * Node tooling.
 */
(function (root, factory) {
  if (typeof module !== "undefined" && module.exports) {
    module.exports = factory(require("fs"), require("path"));
  } else {
    root.ModuleResolver = factory(null, null);
  }
})(typeof self !== "undefined" ? self : this, function (fs, path) {
  "use strict";

  var KEY_RE = /^[a-z][a-z0-9_-]*$/;
  var VALID_STATUS = ["production", "synthetic"];
  var REQUIRED_TOP_FIELDS = [
    "key", "displayNameEn", "status", "publishable", "dafRange", "totalDaf",
    "paths", "schemaMapRef", "capabilities", "buildRuntime",
  ];
  var REQUIRED_PATH_FIELDS = [
    "root", "scriptsRoot", "sourceAssetsRoot", "generatedAssetsRoot",
    "sourceStore", "learningDataDir", "learningDataFile", "coverageFile",
  ];

  function ModuleResolutionError(code, message) {
    var err = new Error(code + ": " + message);
    err.code = code;
    err.name = "ModuleResolutionError";
    return err;
  }

  function requireCond(cond, code, message) {
    if (!cond) throw ModuleResolutionError(code, message);
  }

  function validateCapability(caps, name, requiredConfigFields) {
    var entry = caps[name];
    requireCond(entry !== undefined && entry !== null, "MISSING_FIELD",
      "capabilities." + name);
    requireCond(typeof entry === "object" && !Array.isArray(entry),
      "MALFORMED_DESCRIPTOR", "capabilities." + name + " must be an object");
    requireCond(typeof entry.enabled === "boolean", "MISSING_FIELD",
      "capabilities." + name + ".enabled");
    var present = requiredConfigFields.filter(function (f) {
      return entry[f] !== undefined && entry[f] !== null;
    });
    if (entry.enabled) {
      var missing = requiredConfigFields.filter(function (f) {
        return present.indexOf(f) === -1;
      });
      requireCond(missing.length === 0, "FEATURE_INCONSISTENCY",
        "capabilities." + name + ".enabled is true but missing: " +
        missing.map(function (f) { return "capabilities." + name + "." + f; }).join(", "));
    } else {
      requireCond(present.length === 0, "FEATURE_INCONSISTENCY",
        "capabilities." + name + ".enabled is false but declares " +
        present.map(function (f) { return "capabilities." + name + "." + f; }).join(", ") +
        " anyway - a disabled feature must not carry its own config");
    }
  }

  var SOURCE_ACQUISITION_STRATEGIES = ["remote-fetch", "local-fixture"];

  function validateSourceAcquisition(caps) {
    // Unlike rashi/literalTranslation, every module has SOME
    // source-acquisition strategy - there is no legal "disabled" state,
    // so this is not modeled as an enabled/disabled capability.
    var sa = caps.sourceAcquisition;
    requireCond(typeof sa === "object" && sa !== null, "MISSING_FIELD",
      "capabilities.sourceAcquisition");
    var strategy = sa.strategy;
    requireCond(SOURCE_ACQUISITION_STRATEGIES.indexOf(strategy) !== -1,
      "MALFORMED_DESCRIPTOR",
      "capabilities.sourceAcquisition.strategy must be one of " +
      SOURCE_ACQUISITION_STRATEGIES.join(", ") + ", got " + strategy);
    if (strategy === "remote-fetch") {
      requireCond(!!sa.sourceSystem && !!sa.fetchScript, "MISSING_FIELD",
        "capabilities.sourceAcquisition.sourceSystem and .fetchScript " +
        "(required when strategy is remote-fetch)");
      requireCond(!sa.fixtureInputDir, "FEATURE_INCONSISTENCY",
        "capabilities.sourceAcquisition.fixtureInputDir is set but " +
        "strategy is remote-fetch, not local-fixture");
    } else {
      requireCond(!!sa.fixtureInputDir, "MISSING_FIELD",
        "capabilities.sourceAcquisition.fixtureInputDir " +
        "(required when strategy is local-fixture)");
      requireCond(!(sa.sourceSystem || sa.fetchScript), "FEATURE_INCONSISTENCY",
        "capabilities.sourceAcquisition.sourceSystem/.fetchScript are set " +
        "but strategy is local-fixture, not remote-fetch - a synthetic " +
        "module must not claim a live source system");
    }
  }

  function validateDescriptor(data, key) {
    requireCond(typeof data === "object" && data !== null && !Array.isArray(data),
      "MALFORMED_DESCRIPTOR", "descriptor root must be a JSON object");

    REQUIRED_TOP_FIELDS.forEach(function (field) {
      requireCond(data[field] !== undefined && data[field] !== null,
        "MISSING_FIELD", field);
    });

    requireCond(data.key === key, "MALFORMED_DESCRIPTOR",
      "descriptor key " + JSON.stringify(data.key) + " does not match its " +
      "own directory key " + JSON.stringify(key));
    requireCond(KEY_RE.test(data.key), "MALFORMED_DESCRIPTOR",
      "key " + JSON.stringify(data.key) + " is not a valid machine-safe slug");

    requireCond(VALID_STATUS.indexOf(data.status) !== -1, "MALFORMED_DESCRIPTOR",
      "status must be one of " + VALID_STATUS.join(", ") + ", got " + data.status);
    requireCond(typeof data.publishable === "boolean", "MALFORMED_DESCRIPTOR",
      "publishable must be a boolean");
    if (data.status === "synthetic") {
      requireCond(data.publishable === false, "FEATURE_INCONSISTENCY",
        "status is synthetic but publishable is true - a synthetic " +
        "fixture may never be publishable");
    }

    requireCond(Number.isInteger(data.totalDaf) && data.totalDaf > 0,
      "MALFORMED_DESCRIPTOR", "totalDaf must be a positive integer");

    if (data.dafRange !== null) {
      requireCond(typeof data.dafRange === "object" &&
        "first" in data.dafRange && "last" in data.dafRange,
        "MALFORMED_DESCRIPTOR", "dafRange must be null or {first, last}");
    }

    var paths = data.paths;
    requireCond(typeof paths === "object" && paths !== null, "MALFORMED_DESCRIPTOR",
      "paths must be an object");
    REQUIRED_PATH_FIELDS.forEach(function (field) {
      requireCond(!!paths[field], "MISSING_FIELD", "paths." + field);
    });

    var expectedRoot = "modules/" + key;
    requireCond(paths.root === expectedRoot, "MALFORMED_DESCRIPTOR",
      "paths.root " + JSON.stringify(paths.root) + " does not match the " +
      "expected module root " + JSON.stringify(expectedRoot));

    ["scriptsRoot", "sourceAssetsRoot", "generatedAssetsRoot", "sourceStore",
      "learningDataDir", "learningDataFile", "coverageFile"].forEach(function (field) {
      var p = paths[field];
      requireCond(typeof p === "string" && p.charAt(0) !== "/" &&
        p.split("/").indexOf("..") === -1, "MALFORMED_DESCRIPTOR",
        "paths." + field + " must be a relative, non-traversing path, got " + p);
      requireCond(p === paths.root || p.indexOf(paths.root + "/") === 0,
        "FEATURE_INCONSISTENCY",
        "paths." + field + " (" + p + ") is not under the module's own root (" + paths.root + ")");
    });

    var caps = data.capabilities;
    requireCond(typeof caps === "object" && caps !== null, "MALFORMED_DESCRIPTOR",
      "capabilities must be an object");
    validateCapability(caps, "rashi", ["allowlistsRoot"]);
    validateCapability(caps, "literalTranslation", ["assetsDir"]);
    validateSourceAcquisition(caps);

    var br = data.buildRuntime;
    requireCond(typeof br === "object" && br !== null && !!br.dataScript,
      "MISSING_FIELD", "buildRuntime.dataScript");
    requireCond(br.dataScript === paths.learningDataFile, "FEATURE_INCONSISTENCY",
      "buildRuntime.dataScript (" + br.dataScript + ") disagrees with " +
      "paths.learningDataFile (" + paths.learningDataFile + ") - both name " +
      "the same file and must not drift");
  }

  /**
   * resolveModule(key, repoRoot, searchRoot?) -> descriptor object (frozen)
   *
   * key: explicit module identifier, required, no default.
   * repoRoot: absolute path to the repository root (Node-only; required
   *   when fs/path are available).
   * searchRoot: absolute path to search under; defaults to
   *   <repoRoot>/modules (production discovery). Fixture/test callers
   *   pass an explicit override; production code paths never do.
   *
   * Throws ModuleResolutionError (Error with .code) on any failure.
   * Never silently substitutes another module.
   */
  function resolveModule(key, repoRoot, searchRoot) {
    if (typeof key !== "string" || !KEY_RE.test(key)) {
      throw ModuleResolutionError("INVALID_KEY",
        JSON.stringify(key) + " is not a valid module key (must match " + KEY_RE + ")");
    }
    if (!fs || !path) {
      throw ModuleResolutionError("MALFORMED_DESCRIPTOR",
        "resolveModule requires a Node fs/path environment");
    }
    var root = searchRoot || path.join(repoRoot, "modules");
    var descriptorPath = path.join(root, key, "module.json");

    var resolvedPath = path.resolve(descriptorPath);
    var resolvedRoot = path.resolve(root);
    var rel = path.relative(resolvedRoot, resolvedPath);
    if (rel.startsWith("..") || path.isAbsolute(rel)) {
      throw ModuleResolutionError("INVALID_KEY",
        "resolved path " + resolvedPath + " escapes search root " + resolvedRoot);
    }

    if (!fs.existsSync(descriptorPath) || !fs.statSync(descriptorPath).isFile()) {
      throw ModuleResolutionError("UNKNOWN_MODULE",
        "no descriptor at " + descriptorPath);
    }

    var raw;
    try {
      raw = fs.readFileSync(descriptorPath, "utf-8");
    } catch (e) {
      throw ModuleResolutionError("MALFORMED_DESCRIPTOR", String(e));
    }

    var data;
    try {
      data = JSON.parse(raw);
    } catch (e) {
      throw ModuleResolutionError("MALFORMED_DESCRIPTOR", "invalid JSON: " + e.message);
    }

    validateDescriptor(data, key);
    return Object.freeze(JSON.parse(JSON.stringify(data)));
  }

  function listModules(repoRoot, searchRoot) {
    var root = searchRoot || path.join(repoRoot, "modules");
    if (!fs || !fs.existsSync(root)) return [];
    return fs.readdirSync(root)
      .filter(function (name) {
        var full = path.join(root, name);
        return fs.statSync(full).isDirectory() &&
          fs.existsSync(path.join(full, "module.json"));
      })
      .sort();
  }

  return {
    resolveModule: resolveModule,
    listModules: listModules,
    validateDescriptor: validateDescriptor,
    ModuleResolutionError: ModuleResolutionError,
    KEY_RE: KEY_RE,
  };
});
