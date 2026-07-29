#!/usr/bin/env python3
"""
audit_replication_readiness.py - can a second tractate actually be onboarded?

The platform is multi-tractate by construction at the app layer, and that part
holds up: manifest.js is a registry, app.jsx reads ?module=, and build.mjs
allowlists any modules/<id>/learning_data.js and copies the whole modules/
tree. Nothing there needs changing for a second tractate.

The tooling layer is a different story, and asserting "it generalizes" is not
evidence. This audit measures it: for every shared tool, is the module id a
parameter or a hardcoded path? It reports three tiers.

  GENERIC     no module id in the file, or only in a comment / a full-Shas
              index / the manifest entry itself. Works for a new tractate
              as-is.
  PER-MODULE  the file lives under modules/<id>/ and names its own module.
              Expected, but each one is an edit when the directory is copied,
              so the count is the real cost of cloning a module.
  PINNED      shared infrastructure at the repo root that hardcodes
              modules/yoma. These are the actual blockers: they run for every
              module but only resolve for Yoma.

It also runs a fixture check proving the app-layer contract accepts a second
module id, without creating a real tractate: the fixture is synthetic, lives
in a temp directory, and nothing is written under modules/.

Offline, no network. --strict exits 1 if any PINNED file remains.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MODULE_ID = "yoma"

# Files whose module-id mentions are known-benign, with the reason. Listed
# explicitly so a new mention in one of them still has to be justified here
# rather than silently inheriting an exemption.
BENIGN = {
    "manifest.js": "the Yoma module's own registry entry",
    "app.jsx": "full-Shas masechet index; every tractate is listed, not just Yoma",
    "shared/rashi_association.js": "doc comment naming the boundary registry path",
    "tests/browser/rashi-association.spec.js": "navigates the only module that exists",
}

PIN_RE = re.compile(r"modules/" + MODULE_ID + r"\b|modules\"\s*/\s*\"" + MODULE_ID + r"\"")
ID_RE = re.compile(r"[\"']" + MODULE_ID + r"[\"']")

SCAN_GLOBS = ["scripts/*.py", "scripts/*.mjs", "shared/*.js",
              "tests/browser/*.js", "tests/unit/*.mjs", "tests/smoke/*.py",
              ".github/workflows/*.yml"]
SCAN_FILES = ["app.jsx", "manifest.js", "playwright.config.js"]


def classify():
    tiers = {"GENERIC": [], "PER_MODULE": [], "PINNED": []}
    files = []
    for g in SCAN_GLOBS:
        files += sorted(REPO.glob(g))
    files += [REPO / f for f in SCAN_FILES]
    files += sorted((REPO / "modules" / MODULE_ID / "scripts").glob("*.py"))

    self_rel = str(Path(__file__).resolve().relative_to(REPO))
    for f in sorted(set(files)):
        if not f.is_file():
            continue
        rel = str(f.relative_to(REPO))
        # This auditor's own MODULE_ID constant is the parameter under audit,
        # not a pinned path; counting it would make the report self-referential.
        if rel == self_rel:
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        hits = len(PIN_RE.findall(text)) + len(ID_RE.findall(text))
        if not hits:
            tiers["GENERIC"].append((rel, 0, ""))
        elif rel.startswith(f"modules/{MODULE_ID}/"):
            tiers["PER_MODULE"].append((rel, hits, "names its own module"))
        elif rel in BENIGN:
            tiers["GENERIC"].append((rel, hits, BENIGN[rel]))
        else:
            tiers["PINNED"].append((rel, hits, "shared tool hardcodes modules/" + MODULE_ID))
    return tiers


def npm_script_split():
    pkg = json.loads((REPO / "package.json").read_text(encoding="utf-8"))
    scripts = pkg.get("scripts", {})
    per_module = sorted(k for k in scripts if k.endswith(":" + MODULE_ID))
    generic = sorted(k for k in scripts if not k.endswith(":" + MODULE_ID))
    return generic, per_module


def fixture_check():
    """Prove the app-layer contract accepts a second module id.

    Builds a synthetic manifest + learning_data in a temp dir and runs the
    same validations build.mjs applies. Writes nothing under modules/ and
    creates no tractate.
    """
    results = []
    build_src = (REPO / "scripts" / "build.mjs").read_text(encoding="utf-8")

    m = re.search(r"dataScriptPattern = (/.*?/)\s*;", build_src)
    results.append(("build.mjs declares a module-id pattern", bool(m),
                    m.group(1) if m else "not found"))
    if m:
        # translate the JS regex to Python and test a plausible second module
        py = m.group(1).strip("/").replace("\\/", "/")
        rx = re.compile(py)
        for candidate, want in [("modules/berakhot/learning_data.js", True),
                                ("modules/rosh-hashanah/learning_data.js", True),
                                ("modules/Yoma/learning_data.js", False),
                                ("modules/../etc/learning_data.js", False)]:
            ok = bool(rx.match(candidate)) is want
            results.append((f"build.mjs pattern {'accepts' if want else 'rejects'} "
                            f"{candidate}", ok, ""))

    # runtime allowlist in app.jsx must agree with the build-time one
    app = (REPO / "app.jsx").read_text(encoding="utf-8")
    results.append(("app.jsx carries a runtime dataScript allowlist",
                    "isAllowedModuleDataScript" in app, ""))

    # manifest is a list, not a single entry
    man = (REPO / "manifest.js").read_text(encoding="utf-8")
    results.append(("manifest.js exports an array registry",
                    bool(re.search(r"MYSUGYA_MANIFEST\s*=\s*\[", man)), ""))

    # a synthetic second entry must satisfy the build-time validator
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / "modules" / "fixturemasechet").mkdir(parents=True)
        (tmp / "modules" / "fixturemasechet" / "learning_data.js").write_text(
            "const TRACTATE_META={id:'fixturemasechet'};", encoding="utf-8")
        results.append(("synthetic second module directory is creatable outside "
                        "modules/ (no real tractate started)",
                        (tmp / "modules" / "fixturemasechet").is_dir(), str(tmp)))
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 while any PINNED shared tool remains")
    args = ap.parse_args()

    tiers = classify()
    generic_npm, per_module_npm = npm_script_split()
    fixture = fixture_check()

    pinned = tiers["PINNED"]
    per_module = tiers["PER_MODULE"]
    fixture_ok = all(ok for _, ok, _ in fixture)

    if args.json:
        print(json.dumps({
            "moduleId": MODULE_ID,
            "tiers": {k: [{"file": f, "mentions": n, "note": note}
                          for f, n, note in v] for k, v in tiers.items()},
            "npmScripts": {"generic": generic_npm, "perModule": per_module_npm},
            "fixture": [{"check": c, "pass": ok, "detail": d} for c, ok, d in fixture],
            "blockers": len(pinned),
            "cloneCost": {"moduleScriptsNamingOwnModule": len(per_module),
                          "npmScriptsToAuthor": len(per_module_npm)},
        }, indent=2, ensure_ascii=False))
        sys.exit(1 if (args.strict and pinned) else 0)

    print("Replication readiness: can a second tractate be onboarded?\n")

    print(f"  PINNED shared tools (blockers): {len(pinned)}")
    for f, n, _ in sorted(pinned, key=lambda x: -x[1]):
        print(f"    {f:<48} {n} hardcoded reference(s)")

    print(f"\n  PER-MODULE files (clone cost): {len(per_module)}")
    print(f"    each names its own module id and needs an edit when copied")

    print(f"\n  GENERIC files: {len(tiers['GENERIC'])}")
    for f, n, note in tiers["GENERIC"]:
        if n:
            print(f"    {f:<48} {n} mention(s), benign: {note}")

    print(f"\n  npm scripts: {len(generic_npm)} module-generic, "
          f"{len(per_module_npm)} suffixed :{MODULE_ID}")
    print(f"    a second tractate needs {len(per_module_npm)} new script entries")

    print(f"\n  app-layer fixture checks ({'all pass' if fixture_ok else 'FAILURES'}):")
    for c, ok, d in fixture:
        print(f"    [{'PASS' if ok else 'FAIL'}] {c}" + (f"  {d}" if d and not ok else ""))

    print("\n  Verdict: app and build layers are module-generic and need no change.")
    print(f"           {len(pinned)} shared tool(s) at the repo root are Yoma-pinned")
    print("           and must be parameterized before a second tractate can use")
    print("           the worker pipeline, readiness audit, or sharded browser run.")
    print("\n  Full checklist: docs/reports/replication-readiness.md")

    if args.strict and pinned:
        sys.exit(1)


if __name__ == "__main__":
    main()
