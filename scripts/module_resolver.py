#!/usr/bin/env python3
"""
module_resolver.py - the canonical way to resolve a module descriptor.

Phase 3 Step 2 of docs/platform-closure-plan.md. Full contract in
docs/reports/module-descriptor-contract.md. This resolver reads
modules/<key>/module.json (or, when a caller explicitly overrides the
search root - fixture callers only - <root>/<key>/module.json) and
validates it against the canonical schema.

Nothing that currently reads modules/yoma paths directly is migrated onto
this yet (that is Steps 3A-4). This module is self-contained: it does not
import worker_pipeline.py, and nothing in worker_pipeline.py imports it
yet either.

No implicit default module. Every caller passes an explicit key. No
caller in this file ever falls back to "yoma".
"""
import json
import re
from pathlib import Path
from types import MappingProxyType

REPO = Path(__file__).resolve().parent.parent
DEFAULT_SEARCH_ROOT = REPO / "modules"

KEY_RE = re.compile(r"^[a-z][a-z0-9_-]*$")

REQUIRED_TOP_FIELDS = (
    "key", "displayNameEn", "status", "publishable", "dafRange", "totalDaf",
    "paths", "schemaMapRef", "capabilities", "buildRuntime",
)
REQUIRED_PATH_FIELDS = (
    "root", "scriptsRoot", "sourceAssetsRoot", "generatedAssetsRoot",
    "sourceStore", "learningDataDir", "learningDataFile", "coverageFile",
)
VALID_STATUS = ("production", "synthetic")


class ModuleResolutionError(Exception):
    """Raised for every resolution failure. .code is one of:
    INVALID_KEY, UNKNOWN_MODULE, MALFORMED_DESCRIPTOR, MISSING_FIELD,
    FEATURE_INCONSISTENCY.
    """

    def __init__(self, code, message):
        self.code = code
        super().__init__(f"{code}: {message}")


class ModuleDescriptor:
    """Read-only wrapper around a validated descriptor dict."""

    def __init__(self, data):
        self._data = MappingProxyType(dict(data))

    def __getitem__(self, item):
        return self._data[item]

    def get(self, item, default=None):
        return self._data.get(item, default)

    def to_dict(self):
        return dict(self._data)

    @property
    def key(self):
        return self._data["key"]

    @property
    def status(self):
        return self._data["status"]

    @property
    def publishable(self):
        return self._data["publishable"]

    @property
    def is_synthetic(self):
        return self._data["status"] == "synthetic"

    @property
    def paths(self):
        return self._data["paths"]

    @property
    def capabilities(self):
        return self._data["capabilities"]

    def __repr__(self):
        return f"ModuleDescriptor(key={self.key!r}, status={self.status!r})"


def _require(cond, code, message):
    if not cond:
        raise ModuleResolutionError(code, message)


def _validate_capability(caps, name, required_config_fields):
    entry = caps.get(name)
    if entry is None:
        raise ModuleResolutionError(
            "MISSING_FIELD", f"capabilities.{name}")
    _require(isinstance(entry, dict), "MALFORMED_DESCRIPTOR",
              f"capabilities.{name} must be an object")
    _require("enabled" in entry and isinstance(entry["enabled"], bool),
              "MISSING_FIELD", f"capabilities.{name}.enabled")
    present_config = [f for f in required_config_fields if entry.get(f) is not None]
    if entry["enabled"]:
        missing = [f for f in required_config_fields if f not in present_config]
        _require(not missing, "FEATURE_INCONSISTENCY",
                  f"capabilities.{name}.enabled is true but missing: "
                  f"{', '.join('capabilities.' + name + '.' + f for f in missing)}")
    else:
        _require(not present_config, "FEATURE_INCONSISTENCY",
                  f"capabilities.{name}.enabled is false but declares "
                  f"{', '.join('capabilities.' + name + '.' + f for f in present_config)} "
                  "anyway - a disabled feature must not carry its own config")


SOURCE_ACQUISITION_STRATEGIES = ("remote-fetch", "local-fixture")


def _validate_source_acquisition(caps):
    """Unlike rashi/literalTranslation, every module has SOME source-
    acquisition strategy - there is no legal "disabled" state, so this is
    not modeled as an enabled/disabled capability. 'remote-fetch' (Yoma's
    strategy: live talmud.dev/Sefaria calls, run interactively/offline by
    an operator, never by CI) requires sourceSystem and fetchScript.
    'local-fixture' (synthetic modules only, e.g. the Phase 3 fixture)
    requires fixtureInputDir and forbids any network access - enforced
    here only as a schema requirement; the actual no-network guarantee is
    a property of what script the module points fixtureInputDir/fetchScript
    at, which this resolver cannot verify by reading JSON."""
    sa = caps.get("sourceAcquisition")
    _require(isinstance(sa, dict), "MISSING_FIELD", "capabilities.sourceAcquisition")
    strategy = sa.get("strategy")
    _require(strategy in SOURCE_ACQUISITION_STRATEGIES, "MALFORMED_DESCRIPTOR",
              f"capabilities.sourceAcquisition.strategy must be one of "
              f"{SOURCE_ACQUISITION_STRATEGIES}, got {strategy!r}")
    if strategy == "remote-fetch":
        _require(sa.get("sourceSystem") and sa.get("fetchScript"),
                  "MISSING_FIELD",
                  "capabilities.sourceAcquisition.sourceSystem and .fetchScript "
                  "(required when strategy is remote-fetch)")
        _require(not sa.get("fixtureInputDir"), "FEATURE_INCONSISTENCY",
                  "capabilities.sourceAcquisition.fixtureInputDir is set but "
                  "strategy is remote-fetch, not local-fixture")
    else:  # local-fixture
        _require(sa.get("fixtureInputDir"), "MISSING_FIELD",
                  "capabilities.sourceAcquisition.fixtureInputDir "
                  "(required when strategy is local-fixture)")
        _require(not (sa.get("sourceSystem") or sa.get("fetchScript")),
                  "FEATURE_INCONSISTENCY",
                  "capabilities.sourceAcquisition.sourceSystem/.fetchScript are "
                  "set but strategy is local-fixture, not remote-fetch - a "
                  "synthetic module must not claim a live source system")


def validate_descriptor(data, key):
    """Validate a parsed descriptor dict for the given expected key.

    Raises ModuleResolutionError on any violation. Returns nothing on
    success - callers wrap the dict in ModuleDescriptor themselves.
    """
    _require(isinstance(data, dict), "MALFORMED_DESCRIPTOR",
              "descriptor root must be a JSON object")

    for field in REQUIRED_TOP_FIELDS:
        _require(field in data and data[field] is not None,
                  "MISSING_FIELD", field)

    _require(data["key"] == key, "MALFORMED_DESCRIPTOR",
              f"descriptor key {data['key']!r} does not match its own "
              f"directory key {key!r}")
    _require(bool(KEY_RE.match(data["key"])), "MALFORMED_DESCRIPTOR",
              f"key {data['key']!r} is not a valid machine-safe slug "
              f"(must match {KEY_RE.pattern})")

    _require(data["status"] in VALID_STATUS, "MALFORMED_DESCRIPTOR",
              f"status must be one of {VALID_STATUS}, got {data['status']!r}")
    _require(isinstance(data["publishable"], bool), "MALFORMED_DESCRIPTOR",
              "publishable must be a boolean")
    if data["status"] == "synthetic":
        _require(data["publishable"] is False, "FEATURE_INCONSISTENCY",
                  "status is synthetic but publishable is true - a "
                  "synthetic fixture may never be publishable")

    _require(isinstance(data["totalDaf"], int) and data["totalDaf"] > 0,
              "MALFORMED_DESCRIPTOR", "totalDaf must be a positive integer")

    if data["dafRange"] is not None:
        dr = data["dafRange"]
        _require(isinstance(dr, dict) and "first" in dr and "last" in dr,
                  "MALFORMED_DESCRIPTOR",
                  "dafRange must be null or {first, last}")

    paths = data["paths"]
    _require(isinstance(paths, dict), "MALFORMED_DESCRIPTOR",
              "paths must be an object")
    for field in REQUIRED_PATH_FIELDS:
        _require(field in paths and paths[field], "MISSING_FIELD", f"paths.{field}")

    expected_root = f"modules/{key}"
    _require(paths["root"] == expected_root, "MALFORMED_DESCRIPTOR",
              f"paths.root {paths['root']!r} does not match the expected "
              f"module root {expected_root!r} for key {key!r}")
    for field in ("scriptsRoot", "sourceAssetsRoot", "generatedAssetsRoot",
                  "sourceStore", "learningDataDir", "learningDataFile",
                  "coverageFile"):
        p = paths[field]
        _require(isinstance(p, str) and not p.startswith("/") and ".." not in p.split("/"),
                  "MALFORMED_DESCRIPTOR",
                  f"paths.{field} must be a relative, non-traversing path, got {p!r}")
        _require(p == paths["root"] or p.startswith(paths["root"] + "/"),
                  "FEATURE_INCONSISTENCY",
                  f"paths.{field} ({p!r}) is not under the module's own "
                  f"root ({paths['root']!r})")

    caps = data["capabilities"]
    _require(isinstance(caps, dict), "MALFORMED_DESCRIPTOR",
              "capabilities must be an object")
    _validate_capability(caps, "rashi", ("allowlistsRoot",))
    _validate_capability(caps, "literalTranslation", ("assetsDir",))
    _validate_source_acquisition(caps)

    br = data["buildRuntime"]
    _require(isinstance(br, dict) and br.get("dataScript"),
              "MISSING_FIELD", "buildRuntime.dataScript")
    _require(br["dataScript"] == paths["learningDataFile"],
              "FEATURE_INCONSISTENCY",
              f"buildRuntime.dataScript ({br['dataScript']!r}) disagrees "
              f"with paths.learningDataFile ({paths['learningDataFile']!r}) "
              "- both name the same file and must not drift")


def resolve_module(key, search_root=None):
    """Resolve and validate one module descriptor.

    key: the explicit module identifier. Required; there is no default.
    search_root: directory to look for <key>/module.json under. Defaults
        to modules/ (production discovery). Fixture/test callers pass an
        explicit override (e.g. tests/fixtures/modules/); production code
        paths never do.

    Returns a ModuleDescriptor. Raises ModuleResolutionError on any
    failure - never silently substitutes another module.
    """
    if not isinstance(key, str) or not KEY_RE.match(key):
        raise ModuleResolutionError(
            "INVALID_KEY",
            f"{key!r} is not a valid module key (must match {KEY_RE.pattern})")

    root = Path(search_root) if search_root is not None else DEFAULT_SEARCH_ROOT
    descriptor_path = root / key / "module.json"

    # Defense in depth: even though KEY_RE already forbids '/', '..', and
    # backslashes, explicitly confirm the resolved path stays under root
    # before any read, so a future regex loosening can't silently reopen
    # traversal.
    try:
        resolved = descriptor_path.resolve()
        root_resolved = root.resolve()
    except OSError as e:  # pragma: no cover - defensive
        raise ModuleResolutionError("MALFORMED_DESCRIPTOR", str(e))
    if root_resolved not in resolved.parents and resolved != root_resolved:
        raise ModuleResolutionError(
            "INVALID_KEY", f"resolved path {resolved} escapes search root {root_resolved}")

    if not descriptor_path.is_file():
        raise ModuleResolutionError(
            "UNKNOWN_MODULE", f"no descriptor at {descriptor_path}")

    try:
        raw = descriptor_path.read_text(encoding="utf-8")
    except OSError as e:
        raise ModuleResolutionError("MALFORMED_DESCRIPTOR", str(e))

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ModuleResolutionError("MALFORMED_DESCRIPTOR", f"invalid JSON: {e}")

    validate_descriptor(data, key)
    return ModuleDescriptor(data)


def list_modules(search_root=None):
    """Return the sorted list of module keys discoverable under search_root
    (production default: modules/). A directory whose module.json fails
    validation is skipped, not raised - callers that need strict behavior
    should call resolve_module() on each key themselves."""
    root = Path(search_root) if search_root is not None else DEFAULT_SEARCH_ROOT
    if not root.is_dir():
        return []
    keys = []
    for child in sorted(root.iterdir()):
        if child.is_dir() and (child / "module.json").is_file():
            keys.append(child.name)
    return keys


if __name__ == "__main__":
    import argparse
    import sys

    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("key", help="module key to resolve, e.g. yoma")
    ap.add_argument("--search-root", default=None)
    args = ap.parse_args()

    try:
        d = resolve_module(args.key, search_root=args.search_root)
    except ModuleResolutionError as e:
        print(f"ERROR  {e.code}: {e}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(d.to_dict(), indent=2, ensure_ascii=False))
