#!/usr/bin/env python3
"""Read DATA_VERSION from modules/yoma/learning_data.js and sync it to VERSION, package.json, index.html, and manifest.js."""
import re, json, sys
from pathlib import Path

root = Path(__file__).parent.parent

# Read DATA_VERSION from the active module's learning_data.js
data_js = (root / "modules" / "yoma" / "learning_data.js").read_text()
m = re.search(r'const DATA_VERSION\s*=\s*"([^"]+)"', data_js)
if not m:
    print("ERROR: DATA_VERSION not found in modules/yoma/learning_data.js", file=sys.stderr)
    sys.exit(1)
ver = m.group(1)

# VERSION file
(root / "VERSION").write_text(ver + "\n")

# package.json
pkg_path = root / "package.json"
pkg = json.loads(pkg_path.read_text())
pkg["version"] = ver
pkg_path.write_text(json.dumps(pkg, indent=2) + "\n")

# index.html cache busters
html_path = root / "index.html"
html = re.sub(r'v=[0-9][0-9.]*', f'v={ver}', html_path.read_text())
html_path.write_text(html)

# manifest.js dataVersion
manifest_path = root / "manifest.js"
manifest = re.sub(r'dataVersion:\s*"[^"]+"', f'dataVersion: "{ver}"', manifest_path.read_text())
manifest_path.write_text(manifest)

print(f"synced to v{ver}")
