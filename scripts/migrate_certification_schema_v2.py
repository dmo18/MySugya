#!/usr/bin/env python3
"""One-time schema migration: semantic certification registry 1.0 -> 2.0.

Schema 1.0 certified a record after two source-first review passes and a
free-text "every field was checked" declaration. An independent audit
demonstrated that insufficient: Yoma 7a/7b were CERTIFIED under schema 1.0
while stale semantic fields survived a repair. Schema 2.0 requires a
mandatory, mechanically-enumerated, fingerprint-bound final whole-record
audit before a record may read as CERTIFIED (see semantic_certification.py).

This script performs the one-time, narrow, self-disabling transition:

- every record currently CERTIFIED under schema 1.0 is relabeled
  REVALIDATION_REQUIRED, a state that can never read as CERTIFIED
  (see certificate_status in semantic_certification.py) until it receives a
  real schema-2.0 final audit and genuinely independent review
- the original firstPass, secondPass, sourceFingerprint, semanticFingerprint,
  and certifiedAtCommit are preserved untouched as historical evidence
- an explicit `migration` provenance block records that this happened, when,
  and from what schema version
- the registry's schemaVersion is bumped from "1.0" to "2.0"

It is intentionally impossible to reuse casually:

- it refuses to run unless the on-disk registry schemaVersion is exactly
  "1.0" (running it again against an already-migrated registry, or any other
  version, raises immediately)
- after this script runs once and the result is committed, main's
  schemaVersion is permanently "2.0", so the guard above can never pass
  again in this repository's history
- the narrow ratchet exception in validate_semantic_certification.py that
  allows this one downgrade (CERTIFIED -> REVALIDATION_REQUIRED) is itself
  gated on the base ref's schemaVersion being exactly "1.0", so it also
  self-disables the moment this migration merges to main

This script never edits semantic content, argumentFlow, display/learning
fields, or any authored field. Only certification-registry metadata changes.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Tuple

from semantic_certification import CERT_SCHEMA_VERSION, cert_path


def resolve_ref(ref: str) -> str:
    p = subprocess.run(["git", "rev-parse", ref], text=True, capture_output=True)
    return p.stdout.strip() if p.returncode == 0 and p.stdout.strip() else ref


def migrate(data: Dict[str, Any], migrated_at_commit: str) -> Tuple[Dict[str, Any], int]:
    """Pure transform: schema-1.0 registry dict -> schema-2.0 registry dict.

    Returns (migrated_data, count_of_records_downgraded). Raises ValueError
    if `data` is not a schema-1.0 registry, so this can never silently run
    twice or against the wrong input.
    """
    if data.get("schemaVersion") != "1.0":
        raise ValueError(
            f"refusing to migrate: registry schemaVersion is {data.get('schemaVersion')!r}, "
            "expected '1.0'. This script is one-time only and self-disables once the "
            "registry is already on schema 2.0 (or any other version)."
        )
    if not isinstance(data.get("records"), dict):
        raise ValueError("registry records must be an object keyed by sugya id")

    out = dict(data)
    out["schemaVersion"] = CERT_SCHEMA_VERSION
    records: Dict[str, Any] = {}
    migrated = 0
    for sid, record in data["records"].items():
        if not isinstance(record, dict) or record.get("state") != "CERTIFIED":
            # Non-CERTIFIED records (REPAIR_REQUIRED, REPAIRED_PENDING_REVIEW,
            # BLOCKED) are not grandfathered as trusted by anything today;
            # leave them exactly as-is, the live queue will re-derive their
            # effective state under schema 2.0 the same as it always has.
            records[sid] = record
            continue
        new_record = dict(record)
        new_record["state"] = "REVALIDATION_REQUIRED"
        new_record["migration"] = {
            "fromSchemaVersion": "1.0",
            "toSchemaVersion": CERT_SCHEMA_VERSION,
            "migratedAtCommit": migrated_at_commit,
            "migrationScript": "scripts/migrate_certification_schema_v2.py",
            "reason": (
                "Certified under schema 1.0, which required two source-first "
                "review passes plus a free-text 'every field was checked' "
                "declaration but no mechanically-enumerated, fingerprint-bound "
                "final whole-record audit. An independent audit demonstrated "
                "that gap concretely on Yoma 7a/7b. This record must receive a "
                "fresh schema-2.0 final audit and genuinely independent review "
                "before it may certify again; it does not read as CERTIFIED "
                "until then."
            ),
        }
        records[sid] = new_record
        migrated += 1
    out["records"] = records
    return out, migrated


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--module", default="yoma")
    ap.add_argument("--commit-ref", default="HEAD")
    ap.add_argument("--dry-run", action="store_true", help="report what would change without writing")
    args = ap.parse_args()

    path = cert_path(args.module)
    data = json.loads(path.read_text(encoding="utf-8"))
    migrated_data, count = migrate(data, resolve_ref(args.commit_ref))

    if args.dry_run:
        print(
            f"DRY RUN: would migrate {args.module} registry to schema {CERT_SCHEMA_VERSION}; "
            f"{count} CERTIFIED record(s) would become REVALIDATION_REQUIRED"
        )
        return

    path.write_text(json.dumps(migrated_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Migrated {args.module} certification registry: schemaVersion 1.0 -> {CERT_SCHEMA_VERSION}")
    print(f"  {count} CERTIFIED record(s) marked REVALIDATION_REQUIRED pending a schema-2.0 final audit")
    print("  Historical firstPass/secondPass evidence and fingerprints were preserved unchanged.")


if __name__ == "__main__":
    main()
