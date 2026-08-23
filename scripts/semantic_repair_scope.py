#!/usr/bin/env python3
"""Scope gate for holistic semantic self-heal PRs.

Why this exists separately from the older field-by-field worker types:
semantic defects routinely contaminate several fields together. Forcing a wrong
sugya through display-edit, learning-copy-edit, quiz-edit and structural-repair
as separate PRs recreates the exact repair loop this project is eliminating.

A semantic self-heal PR is instead bounded by *content ownership* rather than
field family:

- exactly one daf
- one or more explicitly named sugya ids on that daf
- arbitrary authored semantic/source-coordinate fields on those named sugyot
- optional daf summary
- immutable raw Hebrew/Rashi source files
- no changes to unlisted sibling sugyot
- no rashiTranslations changes
- certification registry must change and the certification ratchet is the final
  truth gate

This checker is deterministic. It never decides what the Gemara means.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / ".semantic-repair-manifest.json"

ALLOWED_SUPPORT_PATHS = {
    ".semantic-repair-manifest.json",
    ".worker-manifest.json",
    "VERSION",
    "package.json",
    "package-lock.json",
}
ALLOWED_SUPPORT_PREFIXES = (
    "docs/reports/data/",
    "docs/reports/semantic-",
)


def sh(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(args), cwd=REPO, text=True, capture_output=True)


def load_manifest(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    required = ["schemaVersion", "type", "module", "daf", "sugyaIds", "firstReviewId"]
    missing = [k for k in required if k not in data]
    if missing:
        raise ValueError(f"manifest missing required keys: {missing}")
    if data["schemaVersion"] != "1.0":
        raise ValueError("semantic repair manifest schemaVersion must be 1.0")
    if data["type"] not in {"semantic-daf-repair", "semantic-daf-certify"}:
        raise ValueError("type must be semantic-daf-repair or semantic-daf-certify")
    if not isinstance(data["sugyaIds"], list) or not data["sugyaIds"]:
        raise ValueError("sugyaIds must be a nonempty list")
    if len(data["sugyaIds"]) != len(set(data["sugyaIds"])):
        raise ValueError("sugyaIds contains duplicates")
    if not isinstance(data["firstReviewId"], str) or not data["firstReviewId"].strip():
        raise ValueError("firstReviewId must be nonblank")
    return data


def git_json(ref: str, path: str) -> Any | None:
    r = sh("git", "show", f"{ref}:{path}")
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def changed_files(base: str) -> list[str]:
    r = sh("git", "diff", "--name-only", base, "HEAD")
    if r.returncode != 0:
        raise RuntimeError(r.stderr or f"cannot diff {base}..HEAD")
    return [x.strip() for x in r.stdout.splitlines() if x.strip()]


def by_id(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {s.get("id"): s for s in doc.get("sugyot", []) if s.get("id")}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--manifest", default=str(MANIFEST))
    args = ap.parse_args()

    try:
        manifest = load_manifest(Path(args.manifest))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"SEMANTIC REPAIR SCOPE FAILED: {exc}")
        sys.exit(1)

    module = manifest["module"]
    daf = manifest["daf"]
    target_ids = set(manifest["sugyaIds"])
    learn_rel = f"modules/{module}/assets/learning/{module}/{daf}.learning.json"
    generated = {
        f"modules/{module}/learning_data.js",
        f"modules/{module}/coverage.json",
    }
    registry = f"docs/reports/data/{module}-semantic-certifications.json"

    errors: list[str] = []
    changed = changed_files(args.base)

    for path in changed:
        if path == learn_rel or path in generated or path in ALLOWED_SUPPORT_PATHS or path == registry:
            continue
        if path.startswith(ALLOWED_SUPPORT_PREFIXES):
            continue
        errors.append(f"{path}: outside holistic semantic-repair file scope")

    # Raw authoritative sources and Rashi source assets can never be repaired to
    # make an enrichment answer fit. A source defect is a different campaign.
    forbidden_prefixes = (
        f"modules/{module}/assets/talmuddev/",
        f"modules/{module}/assets/daftexts/",
        f"modules/{module}/assets/literal_en/",
        f"modules/{module}/source_store.js",
        "shared/",
        "scripts/worker_",
        ".github/workflows/",
        "githooks/",
    )
    for path in changed:
        if path.startswith(forbidden_prefixes):
            errors.append(f"{path}: authoritative source/pipeline file forbidden in semantic content PR")

    old_doc = git_json(args.base, learn_rel)
    new_path = REPO / learn_rel
    if manifest["type"] == "semantic-daf-repair":
        if not isinstance(old_doc, dict) or not new_path.exists():
            errors.append(f"{learn_rel}: both base and head learning documents are required")
        else:
            new_doc = json.loads(new_path.read_text(encoding="utf-8"))
            if old_doc.get("daf") != new_doc.get("daf"):
                errors.append("top-level daf may not change")
            if old_doc.get("canonicalRef") != new_doc.get("canonicalRef"):
                errors.append("canonicalRef may not change in semantic repair")
            if old_doc.get("glossary") != new_doc.get("glossary"):
                errors.append("top-level glossary may not change in semantic repair")
            if old_doc.get("rashiTranslations") != new_doc.get("rashiTranslations"):
                errors.append("rashiTranslations may not change in semantic repair")

            old_map, new_map = by_id(old_doc), by_id(new_doc)
            if set(old_map) != set(new_map):
                errors.append("sugya id set may not change in ordinary semantic-daf-repair; use a dedicated source/boundary escalation")
            unknown = target_ids - set(new_map)
            if unknown:
                errors.append(f"manifest targets unknown sugya ids: {sorted(unknown)}")
            for sid in sorted(set(old_map) | set(new_map)):
                if sid in target_ids:
                    continue
                if old_map.get(sid) != new_map.get(sid):
                    errors.append(f"{sid}: sibling sugya changed but is not named in semantic repair manifest")

            # At least one target must actually change for a repair PR.
            if not any(old_map.get(sid) != new_map.get(sid) for sid in target_ids):
                errors.append("semantic-daf-repair changes no named target sugya")

    elif learn_rel in changed:
        errors.append("semantic-daf-certify may not change learning content")

    if registry not in changed:
        errors.append(f"{registry}: semantic PR must update the certification registry")

    # Manifest itself must be changed on every semantic PR. This prevents a
    # stale manifest left on main from routing unrelated future PRs into this path.
    if ".semantic-repair-manifest.json" not in changed:
        errors.append(".semantic-repair-manifest.json must change on every semantic PR")

    if errors:
        print(f"SEMANTIC REPAIR SCOPE FAILED ({manifest['type']} {daf}):")
        for e in errors:
            print(f"  ERROR {e}")
        sys.exit(1)

    print(
        f"OK: holistic semantic scope clean for {manifest['type']} {daf}, "
        f"targets {sorted(target_ids)}, {len(changed)} changed file(s)."
    )
    print("NOTE: scope passing does not certify meaning. The semantic certification ratchet must also pass.")


if __name__ == "__main__":
    main()
