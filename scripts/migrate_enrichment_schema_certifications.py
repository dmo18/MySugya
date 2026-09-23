#!/usr/bin/env python3
"""Rebind semantic certificates after a proven representation-only migration."""
from __future__ import annotations

import argparse
import json

from semantic_certification import REPO, canonical_json
from validate_semantic_certification import (
    CERT_REGISTRY_REL,
    active_schema_migration,
    expected_schema_migration_registry,
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--module", default="yoma")
    ap.add_argument("--base", default="origin/main")
    args = ap.parse_args()
    kinds = active_schema_migration(args.module)
    if not kinds:
        raise SystemExit("active authorized enrichment-schema-migration manifest required")
    expected = expected_schema_migration_registry(args.module, args.base, kinds)
    if expected is None:
        raise SystemExit("base semantic-certification registry is missing or invalid")
    path = REPO / CERT_REGISTRY_REL.format(module=args.module)
    before = json.loads(path.read_text(encoding="utf-8"))
    path.write_text(canonical_json(expected) + "\n", encoding="utf-8")
    changed = sum(before.get("records", {}).get(sid) != rec
                  for sid, rec in expected.get("records", {}).items())
    print(f"rebound {changed} semantic-certification record(s) for {sorted(kinds)}")


if __name__ == "__main__":
    main()
