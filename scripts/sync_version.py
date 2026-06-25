#!/usr/bin/env python3
"""Sync the platform version from VERSION to app/package metadata."""
import json
import re
import sys
from pathlib import Path

root = Path(__file__).parent.parent
version_path = root / "VERSION"
ver = version_path.read_text().strip()

if not re.fullmatch(r"[0-9]+\.[0-9]+", ver):
    print(f"ERROR: invalid VERSION value: {ver!r}", file=sys.stderr)
    sys.exit(1)

# package.json
pkg_path = root / "package.json"
pkg = json.loads(pkg_path.read_text())
pkg["version"] = ver
pkg_path.write_text(json.dumps(pkg, indent=2) + "\n")

# package-lock.json
lock_path = root / "package-lock.json"
if lock_path.exists():
    lock = json.loads(lock_path.read_text())
    lock["version"] = ver
    if isinstance(lock.get("packages"), dict) and "" in lock["packages"]:
        lock["packages"][""]["version"] = ver
    lock_path.write_text(json.dumps(lock, indent=2) + "\n")

# index.html cache busters and visible platform footer label
html_path = root / "index.html"
html = html_path.read_text()
html = re.sub(r'v=[0-9][0-9.]*', f'v={ver}', html)
html = re.sub(r'content:\s*"Platform [^"]+"', f'content: "Platform {ver}"', html)
html_path.write_text(html)

# manifest.js platformVersion. dataVersion belongs to the module data file.
manifest_path = root / "manifest.js"
manifest = manifest_path.read_text()
manifest = re.sub(r'platformVersion:\s*"[^"]+"', f'platformVersion: "{ver}"', manifest)
manifest_path.write_text(manifest)

print(f"synced platform to v{ver}")
