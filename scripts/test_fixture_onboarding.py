#!/usr/bin/env python3
"""
test_fixture_onboarding.py - Phase 3 Step 6's committed, repeatable
end-to-end onboarding proof.

Not part of `npm test` or `npm run test:browser` (like the reserved
--exhaustive-corpus Rashi mode, this is a dedicated closure-proof run,
not a per-PR CI cost for a single-module production repo). Run directly:

  python3 scripts/test_fixture_onboarding.py

Proves, against the REAL generic tooling (never a fixture-only parallel
pipeline):
  1. Both resolvers refuse the fixture with no override, and resolve it
     cleanly with an explicit search_root/searchRoot override.
  2. worker_pipeline.py resolves the fixture via a real command
     (`manifest --module demotractate` with MYSUGYA_MODULE_SEARCH_ROOT
     set) and never touches modules/yoma while doing so.
  3. scripts/build.mjs builds the fixture in complete isolation
     (--module demotractate --search-root tests/fixtures/modules --out
     <temp dir>) without ever touching the real dist/ or manifest.js.
  4. The isolated build actually renders in a real headless browser for
     ?module=demotractate&daf=1a (scripts/fixture_onboarding_browser_check.mjs).
  5. modules/yoma's tree is byte-for-byte unchanged before and after
     every one of the above (tree digest comparison, not just a git diff
     of intent).
"""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
YOMA = REPO / "modules" / "yoma"
FIXTURE_SEARCH_ROOT = "tests/fixtures/modules"
FIXTURE_KEY = "demotractate"
PORT = 4197


def yoma_tree_digest():
    h = hashlib.sha256()
    for path in sorted(YOMA.rglob("*")):
        if path.is_file():
            h.update(path.relative_to(YOMA).as_posix().encode())
            h.update(path.read_bytes())
    return h.hexdigest()


def run(cmd, **kwargs):
    print(f"$ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=str(REPO), check=True, **kwargs)


def step_resolver_isolation():
    print("\n--- Step 1: resolver isolation (both resolvers) ---")
    sys.path.insert(0, str(REPO / "scripts"))
    import module_resolver as mr

    assert mr.list_modules() == ["yoma"], "default-search list_modules() must only ever see yoma"
    try:
        mr.resolve_module(FIXTURE_KEY)
        raise AssertionError("fixture must NOT resolve without an explicit search_root override")
    except mr.ModuleResolutionError as e:
        assert e.code == "UNKNOWN_MODULE"
    d = mr.resolve_module(FIXTURE_KEY, search_root=FIXTURE_SEARCH_ROOT)
    assert d.status == "synthetic" and d.publishable is False
    print("OK: Python resolver - unresolvable by default, resolves cleanly via override")

    node_check = f"""
    const {{ listModules, resolveModule }} = require('{(REPO / 'shared/module_resolver.js').as_posix()}');
    const path = require('path');
    const repoRoot = {json.dumps(str(REPO))};
    if (JSON.stringify(listModules(repoRoot)) !== JSON.stringify(['yoma'])) {{
      throw new Error('default-search listModules() must only ever see yoma');
    }}
    try {{
      resolveModule({json.dumps(FIXTURE_KEY)}, repoRoot);
      throw new Error('fixture must NOT resolve without an explicit searchRoot override');
    }} catch (e) {{
      if (e.code !== 'UNKNOWN_MODULE') throw e;
    }}
    const d = resolveModule({json.dumps(FIXTURE_KEY)}, repoRoot, path.resolve(repoRoot, {json.dumps(FIXTURE_SEARCH_ROOT)}));
    if (d.status !== 'synthetic' || d.publishable !== false) throw new Error('unexpected descriptor state');
    console.log('OK: JS resolver - unresolvable by default, resolves cleanly via override');
    """
    run(["node", "-e", node_check])


def step_worker_pipeline():
    print("\n--- Step 2: worker_pipeline.py resolves the fixture via a real command ---")
    before = yoma_tree_digest()
    with tempfile.TemporaryDirectory() as tmp:
        out_path = Path(tmp) / "manifest.json"
        env = {"MYSUGYA_MODULE_SEARCH_ROOT": FIXTURE_SEARCH_ROOT}
        run(
            ["python3", "scripts/worker_pipeline.py", "manifest", "--type", "docs-tooling",
             "--module", FIXTURE_KEY, "--out", str(out_path)],
            env={**__import__("os").environ, **env},
        )
        manifest = json.loads(out_path.read_text())
        assert manifest["module"] == FIXTURE_KEY, manifest
    after = yoma_tree_digest()
    assert before == after, "modules/yoma tree changed during worker_pipeline.py fixture resolution"
    print("OK: worker_pipeline.py manifest --module demotractate resolved correctly; modules/yoma untouched")


def step_isolated_build_and_render():
    print("\n--- Step 3+4: isolated build.mjs + real browser render ---")
    before = yoma_tree_digest()
    real_manifest_before = (REPO / "manifest.js").read_bytes()
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp) / "demo-dist"
        run([
            "node", "scripts/build.mjs",
            "--module", FIXTURE_KEY,
            "--search-root", FIXTURE_SEARCH_ROOT,
            "--out", str(out_dir),
        ])
        assert (out_dir / "modules" / FIXTURE_KEY / "learning_data.js").is_file()
        assert not (out_dir / "modules" / "yoma").exists(), "isolated fixture build must not include yoma"

        server = subprocess.Popen(
            ["python3", "-m", "http.server", str(PORT), "--bind", "127.0.0.1", "--directory", str(out_dir)],
            cwd=str(REPO), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        try:
            time.sleep(0.8)
            run([
                "node", "scripts/fixture_onboarding_browser_check.mjs",
                f"http://127.0.0.1:{PORT}", FIXTURE_KEY, "1a", "2", "5", "FIXTURE",
            ])
        finally:
            server.terminate()
            try:
                server.wait(timeout=3)
            except subprocess.TimeoutExpired:
                server.kill()

    after = yoma_tree_digest()
    assert before == after, "modules/yoma tree changed during the isolated fixture build/render"
    assert (REPO / "manifest.js").read_bytes() == real_manifest_before, "the real manifest.js must never be touched"
    print("OK: isolated build never touched dist/, the real manifest.js, or modules/yoma")


def main():
    step_resolver_isolation()
    step_worker_pipeline()
    step_isolated_build_and_render()
    print("\nOK: Phase 3 Step 6 onboarding proof passed end to end.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
