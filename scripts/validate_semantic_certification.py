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


def base_source_payload(module: str, ref: str, daf: str, sugya: Dict[str, Any]) -> Dict[str, Any] | None:
    raw = load_json_at(ref, f"modules/{module}/assets/talmuddev/{daf}.json")
    if not isinstance(raw, dict):
        return None
    lines = raw.get("lines") or []
    lr = sugya.get("lineRange") or {}
    start, end = lr.get("startVilnaLine"), lr.get("endVilnaLine")
    if not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < start or end > len(lines):
        return None
    return {
        "module": module,
        "daf": daf,
        "sugyaId": sugya.get("id"),
        "lineRange": lr,
        "lineMap": sugya.get("lines") or [],
        "sefariaRefs": sugya.get("sefariaRefs") or [],
        "rawHebrew": lines[start - 1 : end],
    }


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
        current_source = {
            "module": module,
            "daf": daf,
            "sugyaId": sid,
            "lineRange": sugya.get("lineRange") or {},
            "lineMap": sugya.get("lines") or [],
            "sefariaRefs": sugya.get("sefariaRefs") or [],
        }
        raw_now = json.loads((raw_dir(module) / f"{daf}.json").read_text(encoding="utf-8"))
        lr = sugya.get("lineRange") or {}
        s, e = lr.get("startVilnaLine"), lr.get("endVilnaLine")
        if isinstance(s, int) and isinstance(e, int) and 1 <= s <= e <= len(raw_now.get("lines") or []):
            current_source["rawHebrew"] = (raw_now.get("lines") or [])[s - 1 : e]
        else:
            current_source["rawHebrew"] = ["<INVALID-RANGE>"]
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
