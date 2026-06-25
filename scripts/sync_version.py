#!/usr/bin/env python3
"""Sync the repository version from VERSION to generated and package metadata."""
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

# Yoma runtime data. This is generated, but DATA_VERSION is intentionally synced here
# so the app footer and deployed data version stay aligned with VERSION.
data_path = root / "modules" / "yoma" / "learning_data.js"
data = data_path.read_text()
data_next = re.sub(r'const DATA_VERSION\s*=\s*"[^"]+"', f'const DATA_VERSION = "{ver}"', data, count=1)
if data_next == data:
    print("ERROR: DATA_VERSION not found in modules/yoma/learning_data.js", file=sys.stderr)
    sys.exit(1)
data_path.write_text(data_next)

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

# index.html cache busters
html_path = root / "index.html"
html = re.sub(r'v=[0-9][0-9.]*', f'v={ver}', html_path.read_text())
html_path.write_text(html)

# manifest.js dataVersion
manifest_path = root / "manifest.js"
manifest = re.sub(r'dataVersion:\s*"[^"]+"', f'dataVersion: "{ver}"', manifest_path.read_text())
manifest_path.write_text(manifest)

print(f"synced to v{ver}")
