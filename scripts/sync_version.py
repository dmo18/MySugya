#!/usr/bin/env python3
"""Sync the platform version from VERSION to npm package metadata."""
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

print(f"synced platform to v{ver}")
