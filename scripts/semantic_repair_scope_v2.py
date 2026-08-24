#!/usr/bin/env python3
"""Whole-daf semantic repair scope guard.

This guard lets one semantic PR repair every affected authored field on one daf
without splitting the work into repeated field-specific repair loops. It does
not decide correctness. The source-first certification gate does that review
bookkeeping separately.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = ROOT / ".semantic-repair-manifest.json"

SUPPORT_FILES = {
    ".semantic-repair-manifest.json",
    ".worker-manifest.json",
    "VERSION",
    "package.json",
    "package-lock.json",
    # Deterministic regeneration triggered by the VERSION bump above (via
    # generate_rashi_docs.py) and required by check:rashi-docs:yoma's
    # freshness gate in the same validate:offline:yoma chain this scope
    # guard also runs in. Content is version/commit stamps only.
    "docs/rashi-audit-backlog.md",
}


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(args), cwd=ROOT, text=True, capture_output=True)


def load_manifest(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    for key in ("schemaVersion", "type", "module", "daf", "sugyaIds", "firstReviewId"):
        if key not in data:
            raise ValueError(f"missing manifest key {key}")
    if data["schemaVersion"] != "1.0":
        raise ValueError("schemaVersion must be 1.0")
    if data["type"] not in {"semantic-daf-repair", "semantic-daf-certify"}:
        raise ValueError("unsupported semantic manifest type")
    if not isinstance(data["sugyaIds"], list) or not data["sugyaIds"]:
        raise ValueError("sugyaIds must be a nonempty array")
    if len(set(data["sugyaIds"])) != len(data["sugyaIds"]):
        raise ValueError("sugyaIds must be unique")
    if not isinstance(data["firstReviewId"], str) or not data["firstReviewId"].strip():
        raise ValueError("firstReviewId must be nonblank")
    return data


def git_json(ref: str, path: str) -> Any | None:
    p = run("git", "show", f"{ref}:{path}")
    if p.returncode != 0:
        return None
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        return None


def changed_files(base: str) -> list[str]:
    p = run("git", "diff", "--name-only", base, "HEAD")
    if p.returncode != 0:
        raise RuntimeError(p.stderr or "git diff failed")
    return [line.strip() for line in p.stdout.splitlines() if line.strip()]


def sugya_map(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {item.get("id"): item for item in doc.get("sugyot", []) if item.get("id")}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="origin/main")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    args = parser.parse_args()

    try:
        manifest = load_manifest(Path(args.manifest))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"SEMANTIC SCOPE FAIL: {exc}")
        sys.exit(1)

    module = manifest["module"]
    daf = manifest["daf"]
    targets = set(manifest["sugyaIds"])
    learning = f"modules/{module}/assets/learning/{module}/{daf}.learning.json"
    registry = f"docs/reports/data/{module}-semantic-certifications.json"
    generated = {f"modules/{module}/learning_data.js", f"modules/{module}/coverage.json"}
    allowed_reports_prefix = "docs/reports/semantic-"
    allowed_data_prefix = "docs/reports/data/semantic-"

    files = changed_files(args.base)
    errors: list[str] = []

    for path in files:
        allowed = (
            path == learning
            or path == registry
            or path in generated
            or path in SUPPORT_FILES
            or path.startswith(allowed_reports_prefix)
            or path.startswith(allowed_data_prefix)
        )
        if not allowed:
            errors.append(f"{path}: outside one-daf semantic scope")

    protected_prefixes = (
        f"modules/{module}/assets/talmuddev/",
        f"modules/{module}/assets/daftexts/",
        f"modules/{module}/assets/literal_en/",
        f"modules/{module}/source_store.js",
        ".github/workflows/",
        "githooks/",
        "shared/",
        "scripts/worker_",
    )
    for path in files:
        if path.startswith(protected_prefixes):
            errors.append(f"{path}: protected from semantic repair PRs")

    old_doc = git_json(args.base, learning)
    head_path = ROOT / learning

    if manifest["type"] == "semantic-daf-certify":
        if learning in files:
            errors.append("certification-only PR may not edit learning content")
    else:
        if not isinstance(old_doc, dict) or not head_path.exists():
            errors.append("repair PR requires the same daf learning file at base and head")
        else:
            new_doc = json.loads(head_path.read_text(encoding="utf-8"))
            if old_doc.get("daf") != new_doc.get("daf"):
                errors.append("top-level daf identity changed")
            if old_doc.get("canonicalRef") != new_doc.get("canonicalRef"):
                errors.append("canonicalRef changed")
            if old_doc.get("rashiTranslations") != new_doc.get("rashiTranslations"):
                errors.append("rashiTranslations changed in semantic enrichment PR")

            old_map = sugya_map(old_doc)
            new_map = sugya_map(new_doc)
            old_ids = set(old_map)
            new_ids = set(new_map)
            if old_ids != new_ids:
                errors.append("sugya id set changed; use a dedicated structural escalation")
            unknown = targets - new_ids
            if unknown:
                errors.append(f"manifest names unknown sugya ids: {sorted(unknown)}")

            for sid in sorted(old_ids | new_ids):
                if sid not in targets and old_map.get(sid) != new_map.get(sid):
                    errors.append(f"{sid}: sibling changed but is absent from manifest")

            summary_changed = old_doc.get("summary") != new_doc.get("summary")
            if summary_changed and targets != new_ids:
                errors.append("daf summary changed, so every sugya on the daf must be included in the manifest")

            # Glossary is daf-level authored semantic content (schema 2.0
            # fingerprints it into every sugya's semanticFingerprint, see
            # semantic_certification.semantic_payload), so a repair may only
            # touch it under the same whole-daf scope as the summary: every
            # sugya on the daf named in the manifest. This replaces an
            # earlier unconditional "glossary changed" ban that blocked
            # legitimate same-daf glossary corrections found during the
            # campaign (e.g. stale 9a glossary content left behind by a
            # one-sugya-scoped repair).
            glossary_changed = old_doc.get("glossary") != new_doc.get("glossary")
            if glossary_changed and targets != new_ids:
                errors.append("daf glossary changed, so every sugya on the daf must be included in the manifest")

            coordinate_keys = ("lineRange", "lines", "sefariaRefs")
            boundary_changed = False
            for sid in targets & old_ids & new_ids:
                before = old_map[sid]
                after = new_map[sid]
                if any(before.get(key) != after.get(key) for key in coordinate_keys):
                    boundary_changed = True
                    break
            if boundary_changed and targets != new_ids:
                errors.append("source coordinates changed, so every sugya on the daf must be included in the manifest")

            # A repair that changes ONLY a daf-level semantic field (summary
            # or glossary) legitimately touches no individual sugya body;
            # summary_changed/glossary_changed already enforced the correct
            # full-daf scope for that case above, so it is exempted here
            # rather than forced to also fabricate an unrelated sugya edit.
            if (
                not summary_changed and not glossary_changed
                and not any(old_map.get(sid) != new_map.get(sid) for sid in targets)
            ):
                errors.append("repair manifest names no sugya whose authored content changed")

    if registry not in files:
        errors.append("semantic certification registry must change")
    if ".semantic-repair-manifest.json" not in files:
        errors.append("semantic repair manifest must change in this PR")

    if errors:
        print(f"SEMANTIC SCOPE FAIL ({daf})")
        for item in errors:
            print(f"  ERROR {item}")
        sys.exit(1)

    print(f"OK: semantic scope limited to {daf}, {len(targets)} target sugya(s)")
    print("Meaning is not certified by this scope check. The semantic certification ratchet must pass separately.")


if __name__ == "__main__":
    main()
