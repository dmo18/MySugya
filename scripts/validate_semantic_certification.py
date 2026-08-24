#!/usr/bin/env python3
"""Validate MySugya source-first semantic certification.

Modes:

  --report
      Report effective certification state. Never treats review:"reviewed"
      as certification.

  --strict
      Fail unless every sugya is currently CERTIFIED and fresh.

  --ratchet --base <git-ref>
      PR gate used during bootstrap. Existing uncertified corpus is allowed to
      remain temporarily, but any sugya whose source or semantic payload changes
      versus the merge base MUST be fresh CERTIFIED on the PR head. A previously
      certified sugya may never silently become stale or uncertified.

Once the bootstrap campaign reaches 100%, set strictMode true in the registry.
Then the default invocation also behaves as --strict.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

from semantic_certification import (
    CERT_SCHEMA_VERSION,
    REPO,
    canonical_json,
    certificate_status,
    corpus_status,
    digest,
    learning_dir,
    load_corpus,
    load_registry,
    raw_dir,
    semantic_payload,
)


def allowed_schema_migration_downgrade(
    base_schema: Any,
    head_schema: Any,
    old_record: Dict[str, Any],
    new_record: Any,
) -> bool:
    """Narrow, self-disabling ratchet exception for the one-time semantic
    certification schema 1.0 -> 2.0 migration (see
    scripts/migrate_certification_schema_v2.py).

    The ordinary ratchet forbids a base-CERTIFIED record from reading as
    anything but CERTIFIED at head -- that is what stops a real content
    regression from hiding behind a relabeled certificate. This function
    carves out exactly one legitimate case: the migration script downgrading
    a schema-1.0 CERTIFIED record to REVALIDATION_REQUIRED because schema
    1.0 lacked the mandatory final whole-record audit, with no content
    change hiding underneath the relabel.

    All of the following must hold, or this returns False and the ordinary
    ratchet failure stands:

    - the transition is exactly base schema "1.0" -> head schema
      CERT_SCHEMA_VERSION (today "2.0"); once this migration merges to main,
      main's schemaVersion is permanently >= 2.0, so base can never again be
      "1.0" and this condition can never be true again in this repository's
      history
    - the head record carries the migration script's own `migration`
      provenance marker (never hand-authorable through the ordinary review
      workflow, which only ever writes REPAIR_REQUIRED / PENDING_FINAL_AUDIT
      / CERTIFIED / BLOCKED)
    - the head record's sourceFingerprint/semanticFingerprint are byte-
      identical to what they were at base, proving the underlying candidate
      did not change -- only its certification label did
    """
    if base_schema != "1.0" or head_schema != CERT_SCHEMA_VERSION:
        return False
    if not isinstance(new_record, dict) or new_record.get("state") != "REVALIDATION_REQUIRED":
        return False
    migration = new_record.get("migration")
    if not isinstance(migration, dict) or migration.get("fromSchemaVersion") != "1.0":
        return False
    if new_record.get("sourceFingerprint") != old_record.get("sourceFingerprint"):
        return False
    if new_record.get("semanticFingerprint") != old_record.get("semanticFingerprint"):
        return False
    return True


def git_show(ref: str, rel: str) -> str | None:
    p = subprocess.run(
        ["git", "show", f"{ref}:{rel}"],
        cwd=REPO,
        text=True,
        capture_output=True,
    )
    return p.stdout if p.returncode == 0 else None


def load_json_at(ref: str, rel: str) -> Any | None:
    text = git_show(ref, rel)
    if text is None:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def base_sugya_map(module: str, ref: str) -> Dict[str, Tuple[str, Dict[str, Any], Dict[str, Any]]]:
    """Build the base-ref corpus only from files that still exist at ref."""
    current_dafs = [p.name.replace(".learning.json", "") for p in learning_dir(module).glob("*.learning.json")]
    out: Dict[str, Tuple[str, Dict[str, Any], Dict[str, Any]]] = {}
    rel_dir = f"modules/{module}/assets/learning/{module}"
    for daf in current_dafs:
        doc = load_json_at(ref, f"{rel_dir}/{daf}.learning.json")
        if not isinstance(doc, dict):
            continue
        for sugya in doc.get("sugyot", []):
            sid = sugya.get("id")
            if sid:
                out[sid] = (daf, doc, sugya)
    return out


def source_payload_or_invalid(module: str, daf: str, sugya: Dict[str, Any], lines: list) -> Dict[str, Any]:
    """Build a comparable source payload even when lineRange is out of bounds.

    A sugya can carry an out-of-bounds lineRange in the corpus (a real
    boundary defect to be fixed through the semantic campaign, not silently
    patched here). That must not be conflated with "no comparable payload":
    the full raw daf is embedded so a genuine edit to the underlying source
    text is still detected as a payload change, while two invalid ranges
    that differ only in which sugya/daf they belong to, or that are byte
    identical between base and head, still compare correctly as unchanged.
    """
    lr = sugya.get("lineRange") or {}
    start, end = lr.get("startVilnaLine"), lr.get("endVilnaLine")
    payload = {
        "module": module,
        "daf": daf,
        "sugyaId": sugya.get("id"),
        "lineRange": lr,
        "lineMap": sugya.get("lines") or [],
        "sefariaRefs": sugya.get("sefariaRefs") or [],
    }
    if isinstance(start, int) and isinstance(end, int) and 1 <= start <= end <= len(lines):
        payload["rawHebrew"] = lines[start - 1 : end]
    else:
        payload["rawHebrew"] = {"invalidRange": True, "rawLineCount": len(lines), "rawLines": lines}
    return payload


def base_source_payload(module: str, ref: str, daf: str, sugya: Dict[str, Any]) -> Dict[str, Any] | None:
    raw = load_json_at(ref, f"modules/{module}/assets/talmuddev/{daf}.json")
    if not isinstance(raw, dict):
        return None
    return source_payload_or_invalid(module, daf, sugya, raw.get("lines") or [])


def changed_semantic_sugyot(module: str, base: str) -> list[tuple[str, str]]:
    current = load_corpus(module)
    old = base_sugya_map(module, base)
    changed: list[tuple[str, str]] = []
    for sid in sorted(set(current) | set(old)):
        if sid not in current:
            changed.append((sid, "sugya removed"))
            continue
        if sid not in old:
            changed.append((sid, "sugya added"))
            continue
        daf, doc, sugya = current[sid]
        old_daf, old_doc, old_sugya = old[sid]
        raw_now = json.loads((raw_dir(module) / f"{daf}.json").read_text(encoding="utf-8"))
        current_source = source_payload_or_invalid(module, daf, sugya, raw_now.get("lines") or [])
        old_source = base_source_payload(module, base, old_daf, old_sugya)
        if old_source is None or digest(current_source) != digest(old_source):
            changed.append((sid, "source payload changed"))
            continue
        if digest(semantic_payload(doc, sugya)) != digest(semantic_payload(old_doc, old_sugya)):
            changed.append((sid, "semantic payload changed"))
    return changed


def print_status(module: str) -> tuple[Dict[str, int], Dict[str, Dict[str, Any]]]:
    counts, details = corpus_status(module)
    total = sum(v for k, v in counts.items() if k != "ORPHANED_RECORD")
    print(f"Semantic certification status for {module}: {total} corpus sugyot")
    for key in sorted(counts):
        print(f"  {key:24s} {counts[key]}")
    return counts, details


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--module", default="yoma")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--ratchet", action="store_true")
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    try:
        registry = load_registry(args.module)
        counts, details = corpus_status(args.module)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"SEMANTIC CERTIFICATION INVALID: {exc}")
        sys.exit(1)

    strict = args.strict or bool(registry.get("strictMode"))
    failures: list[str] = []

    if strict:
        for sid, d in details.items():
            if d["state"] != "CERTIFIED":
                failures.append(f"{sid}: {d['state']} ({'; '.join(d['problems'])})")

    changed: list[tuple[str, str]] = []
    if args.ratchet:
        changed = changed_semantic_sugyot(args.module, args.base)
        current = load_corpus(args.module)
        for sid, why in changed:
            if sid not in current:
                failures.append(f"{sid}: {why}; semantic deletion requires an explicit certified replacement/removal process")
                continue
            daf, doc, sugya = current[sid]
            effective, problems = certificate_status(
                args.module, daf, doc, sugya, registry["records"].get(sid)
            )
            if effective != "CERTIFIED":
                failures.append(
                    f"{sid}: {why}, but head is {effective}; every changed semantic/source payload "
                    f"must carry a fresh two-pass source-first certificate ({'; '.join(problems)})"
                )

        # A base CERTIFIED record must not be weakened even if no learning
        # payload changed, for example by deleting only its registry entry.
        base_reg = load_json_at(args.base, f"docs/reports/data/{args.module}-semantic-certifications.json")
        if isinstance(base_reg, dict):
            current_corpus = load_corpus(args.module)
            for sid, old_record in (base_reg.get("records") or {}).items():
                if old_record.get("state") != "CERTIFIED" or sid not in current_corpus:
                    continue
                daf, doc, sugya = current_corpus[sid]
                effective, problems = certificate_status(
                    args.module, daf, doc, sugya, registry["records"].get(sid)
                )
                if effective != "CERTIFIED":
                    if allowed_schema_migration_downgrade(
                        base_reg.get("schemaVersion"),
                        registry.get("schemaVersion"),
                        old_record,
                        registry["records"].get(sid),
                    ):
                        continue
                    failures.append(
                        f"{sid}: was CERTIFIED at base but is now {effective} "
                        f"({'; '.join(problems)}); certification may only stay fresh or be replaced by a fresh certificate"
                    )

    if args.json:
        print(canonical_json({
            "module": args.module,
            "strict": strict,
            "counts": counts,
            "changed": [{"sugyaId": sid, "reason": why} for sid, why in changed],
            "failures": failures,
        }))
    else:
        print_status(args.module)
        if args.ratchet:
            print(f"  changed source/semantic payloads vs {args.base}: {len(changed)}")
            for sid, why in changed[:30]:
                print(f"    {sid}: {why}")
            if len(changed) > 30:
                print(f"    ... {len(changed) - 30} more")

    if failures:
        print("\nSEMANTIC CERTIFICATION GATE FAILED:")
        for msg in failures[:80]:
            print(f"  ERROR {msg}")
        if len(failures) > 80:
            print(f"  ... {len(failures) - 80} more")
        sys.exit(1)

    if strict:
        print("\nOK: every sugya is freshly source-first CERTIFIED.")
    elif args.ratchet:
        print("\nOK: semantic certification ratchet passed. Existing bootstrap debt did not grow.")
    else:
        print("\nREPORT ONLY: bootstrap debt is visible but not treated as certified.")


if __name__ == "__main__":
    main()
