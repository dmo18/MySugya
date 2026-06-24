#!/usr/bin/env python3
import sys
import time
import urllib.request
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PORT = 4173
BASE = f"http://127.0.0.1:{PORT}"
DIST = ROOT / "dist"
VERSION = (ROOT / "VERSION").read_text().strip()


def fetch(path: str) -> str:
    with urllib.request.urlopen(BASE + path, timeout=10) as r:
        return r.read().decode("utf-8", errors="replace")


def assert_contains(html: str, needle: str, label: str):
    if needle not in html:
        raise AssertionError(f"Missing {label}: {needle}")


def re_search_bundle(html: str) -> str:
    import re
    match = re.search(r'src="(assets/app-[^"]+\.js)"', html)
    if not match:
        raise AssertionError("Missing production bundle script tag")
    return match.group(1)


def main() -> int:
    subprocess.run(["npm", "run", "build"], cwd=str(ROOT), check=True)

    server = subprocess.Popen(
        ["python3", "-m", "http.server", str(PORT), "--bind", "127.0.0.1", "--directory", str(DIST)],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        time.sleep(0.6)
        index_html = fetch("/index.html")
        daf_html = fetch("/daf.html?daf=15a")

        assert_contains(index_html, "id=\"root\"", "root mount")
        assert_contains(index_html, f"assets/app-{VERSION}.js", "versioned production app bundle")
        assert_contains(index_html, f"manifest.js?v={VERSION}", "versioned manifest script")
        bundle_html_match = re_search_bundle(index_html)
        bundle_js = fetch("/" + bundle_html_match)
        assert_contains(bundle_js, "createRoot", "React production bundle code")
        if "text/babel" in index_html or "babel.min.js" in index_html or "react.development.js" in index_html:
            raise AssertionError("Built output should not load Babel or React development UMD scripts")

        assert_contains(daf_html, "window.location.replace", "legacy redirect")
        assert_contains(daf_html, "index.html", "redirect target")

        # Basic responsiveness guardrails in stylesheet
        styles = (ROOT / "styles.css").read_text(encoding="utf-8")
        for needle in ["@media (max-width: 720px)", "@media (max-width: 560px)"]:
            if needle not in styles:
                raise AssertionError(f"Missing responsive CSS rule: {needle}")

        # Transliteration option intentionally removed per product decision
        app = (ROOT / "app.jsx").read_text(encoding="utf-8")
        if "Transliteration" in app:
            raise AssertionError("Transliteration UI should be removed")

        # Mobile browser guardrail: argument-flow data remains in the DOM, but
        # the native details wrapper defaults closed at phone widths.
        assert_contains(bundle_js, "argument-flow-disclosure", "mobile argument flow details wrapper")
        assert_contains(bundle_js, "Argument flow", "argument flow disclosure label")
        assert_contains(bundle_js, "(max-width: 720px)", "mobile argument flow breakpoint")
        assert_contains(bundle_js, "matchMedia", "browser media query detection")
        if "!window.matchMedia(\"(max-width: 720px)\").matches" not in bundle_js:
            raise AssertionError("Argument flow should default collapsed when the mobile media query matches")

        print("OK: built pages render and key UI hooks are present")
        return 0
    except Exception as e:
        print(f"FAIL: {e}")
        return 1
    finally:
        server.terminate()
        try:
            server.wait(timeout=2)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    sys.exit(main())
