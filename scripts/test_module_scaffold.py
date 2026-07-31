#!/usr/bin/env python3
"""
test_module_scaffold.py - Phase 3 six-row closure campaign, row 23's
committed, repeatable "scaffolded from empty state" proof.

Not part of `npm test` or `npm run test:browser` (matching
test_fixture_onboarding.py's precedent - a dedicated closure-proof run,
not a per-PR CI cost). Run directly:

  python3 scripts/test_module_scaffold.py

Unlike test_fixture_onboarding.py (which proves the *existing, committed*
demotractate fixture resolves/builds/renders correctly), this proves a
module can be produced from NOTHING and pass through the identical
generic tooling chain:

  1. An empty temp directory has no module in it.
  2. scripts/scaffold_module.py --key <key> --search-root <temp dir>
     writes a fresh module.json + learning_data.js + coverage.json.
  3. scripts/module_resolver.py resolves it cleanly (scaffold_module.py
     already asserts this itself; re-checked here independently).
  4. scripts/validate_module_schema.mjs passes it (schema-complete,
     capability declarations match content) - proven for both a
     rashi+literal-disabled scaffold and a rashi+literal-enabled one.
  5. scripts/build.mjs --module <key> --search-root <temp dir> --out
     <temp dir> builds it in complete isolation.
  6. The isolated build renders in a real headless browser
     (scripts/fixture_onboarding_browser_check.mjs, the same generic
     browser-check tool Step 6 built - reused here unmodified).
  7. modules/yoma's tree is byte-for-byte unchanged before and after
     every one of the above.

The scaffolded module lives only in a temp directory for the duration of
this proof and is never persisted into the real repo tree.
"""
import hashlib
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
YOMA = REPO / "modules" / "yoma"
PORT = 4199

sys.path.insert(0, str(REPO / "scripts"))
import module_resolver  # noqa: E402


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


def scaffold_and_prove(key, rashi, literal, expected_line_count):
    with tempfile.TemporaryDirectory() as tmp:
        search_root = Path(tmp) / "search-root"
        search_root.mkdir()
        module_dir = search_root / key
        assert not module_dir.exists(), "temp search root must start empty"

        run(["python3", "scripts/scaffold_module.py",
             "--key", key, "--search-root", str(search_root),
             "--rashi", rashi, "--literal", literal])
        assert (module_dir / "module.json").is_file()
        assert (module_dir / "learning_data.js").is_file()
        assert (module_dir / "coverage.json").is_file()

        try:
            module_resolver.resolve_module(key)
            raise AssertionError(f"{key!r} must NOT resolve without an explicit search_root override")
        except module_resolver.ModuleResolutionError as e:
            assert e.code == "UNKNOWN_MODULE"
        d = module_resolver.resolve_module(key, search_root=str(search_root))
        assert d.status == "synthetic" and d.publishable is False
        print(f"OK: {key} unresolvable by default, resolves cleanly via override")

        run(["node", "scripts/validate_module_schema.mjs",
             "--module", key, "--search-root", str(search_root)])

        out_dir = Path(tmp) / "build-out"
        run(["node", "scripts/build.mjs",
             "--module", key, "--search-root", str(search_root), "--out", str(out_dir)])
        assert (out_dir / "modules" / key / "learning_data.js").is_file()
        assert not (out_dir / "modules" / "yoma").exists()

        server = subprocess.Popen(
            ["python3", "-m", "http.server", str(PORT), "--bind", "127.0.0.1", "--directory", str(out_dir)],
            cwd=str(REPO), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        try:
            time.sleep(0.8)
            run(["node", "scripts/fixture_onboarding_browser_check.mjs",
                 f"http://127.0.0.1:{PORT}", key, "1a", "1", str(expected_line_count), "SCAFFOLD"])
        finally:
            server.terminate()
            try:
                server.wait(timeout=3)
            except subprocess.TimeoutExpired:
                server.kill()
        print(f"OK: {key} (rashi={rashi}, literal={literal}) scaffolded from nothing, "
              f"resolved, validated, built in isolation, and rendered in a real browser")


def step_scaffold_minimal():
    print("\n--- Step 1: scaffold with both capabilities disabled ---")
    scaffold_and_prove("scafmin", "disabled", "disabled", expected_line_count=1)


def step_scaffold_capabilities_enabled():
    print("\n--- Step 2: scaffold with rashi + literal enabled ---")
    scaffold_and_prove("scafcap", "enabled", "enabled", expected_line_count=1)


def main():
    before = yoma_tree_digest()
    step_scaffold_minimal()
    step_scaffold_capabilities_enabled()
    after = yoma_tree_digest()
    assert before == after, "modules/yoma tree changed during the scaffold-from-empty-state proof"
    print("\nOK: modules/yoma tree byte-identical before and after")
    print("OK: Phase 3 row 23 scaffold-from-empty-state proof passed end to end.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
