#!/usr/bin/env python3
import re
import sys
import time
import urllib.request
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PORT = 4173
BASE = f"http://127.0.0.1:{PORT}"
VERSION = (ROOT / "VERSION").read_text().strip()


def fetch(path: str) -> str:
    with urllib.request.urlopen(BASE + path, timeout=10) as r:
        return r.read().decode("utf-8", errors="replace")


def assert_contains(html: str, needle: str, label: str):
    if needle not in html:
        raise AssertionError(f"Missing {label}: {needle}")


def main() -> int:
    server = subprocess.Popen(
        ["python3", "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        time.sleep(0.6)
        index_html = fetch("/index.html")
        daf_html = fetch("/daf.html?daf=15a")

        assert_contains(index_html, "id=\"root\"", "root mount")
        assert_contains(index_html, f"app.jsx?v={VERSION}", "versioned app script")
        assert_contains(index_html, f"manifest.js?v={VERSION}", "versioned manifest script")

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

        print("OK: hosted pages render and key UI hooks are present")
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
