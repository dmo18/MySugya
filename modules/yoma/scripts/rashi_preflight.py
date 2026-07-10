#!/usr/bin/env python3
"""
rashi_preflight.py - single preflight command for bounded Rashi work on one
daf or a range. Verifies the environment is safe to start and prints the
per-daf state a worker needs.

Usage:
  python3 scripts/rashi_preflight.py 47a
  python3 scripts/rashi_preflight.py 47a-47b            # inclusive range
  python3 scripts/rashi_preflight.py 61a --task repair  # repair mode

FAILS (exit 1) when:
  - the git tree is dirty
  - core.hooksPath is not set to githooks (guards inactive)
  - generated learning_data.js/coverage.json are stale
  - a target daf is malformed or has no talmuddev source
  - a target daf has unresolved allowlist/baseline hits and --task is not
    'repair' (reconstruction on top of undocumented-or-deferred defects is
    how scope creep starts; repairs must be explicitly declared)
  - a target daf's drift profile (audit_rashi_semantic --profile) says
    SHIFTED or FABRICATION-SUSPECT and --task is a line-level mode
    ('repair' or 'links'): stub-only work there duplicates content and
    cements misalignment. Use rashi-realignment (shifted) or
    rashi-reconstruction (fabricated) under Fable/Sonnet. Override is
    Fable-only: FABLE_DRIFT_OVERRIDE=1 plus, at the worker-pipeline
    level, a manifest carrying authorizeDriftOverride.

Otherwise prints, per daf: raw Rashi count, current entry count, real local
Gemara id count, empty-link percentage, allowlist/baseline hits, semantic
audit hits, plus the allowed content-PR file set and the exact post-edit
commands. Offline except local git.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import audit_rashi_semantic

SCRIPTS = Path(__file__).parent
ROOT = SCRIPTS.parent
REPO = ROOT.parent.parent
LEARN_DIR = ROOT / "assets" / "learning" / "yoma"
TALMUDDEV_DIR = ROOT / "assets" / "talmuddev"
DATA_JS = ROOT / "learning_data.js"
ALLOW_DIR = SCRIPTS / "allowlists"

POST_EDIT = [
    "cd modules/yoma && python3 scripts/build_learning_data.py",
    "cd modules/yoma && python3 scripts/build_literal_layer.py --apply",
    "edit VERSION (one patch bump), then python3 scripts/sync_version.py",
    "npm run rashi:verify:yoma -- <daf> --fast   (then --full before the PR)",
]
ALLOWED_FILES = [
    "modules/yoma/assets/learning/yoma/<daf>.learning.json (target daf only)",
    "modules/yoma/learning_data.js + coverage.json (regeneration only)",
    "VERSION, package.json, package-lock.json (sync_version.py only)",
    "docs/rashi-audit-backlog.md (repair record)",
    "modules/yoma/scripts/allowlists/* (REMOVE stale entries only)",
]


def sh(args, cwd=REPO):
    return subprocess.run(args, capture_output=True, text=True, cwd=cwd)


def daf_sort_key(d):
    m = re.match(r"(\d+)([ab])", d)
    return (int(m.group(1)), m.group(2))


def expand_targets(spec):
    m = re.match(r"^(\d+[ab])-(\d+[ab])$", spec)
    if not m:
        if not re.match(r"^\d+[ab]$", spec):
            sys.exit(f"ERROR: malformed daf spec {spec!r} (want e.g. 47a or 47a-48b)")
        return [spec]
    all_daf = sorted((p.name.replace(".json", "") for p in TALMUDDEV_DIR.glob("*.json")),
                     key=daf_sort_key)
    lo, hi = daf_sort_key(m.group(1)), daf_sort_key(m.group(2))
    out = [d for d in all_daf if lo <= daf_sort_key(d) <= hi]
    if not out:
        sys.exit(f"ERROR: range {spec!r} matches no daf")
    return out


# Task modes that edit individual lines in place. On a daf whose drift
# profile says SHIFTED or FABRICATION-SUSPECT, line-level edits duplicate
# content and cement misalignment (docs/reports/rashi-lookalike-shift-audit.md),
# so these modes are blocked there. Realignment/reconstruction modes are the
# remedies and stay allowed.
DRIFT_BLOCKED_TASKS = {"repair", "links"}
DRIFT_OVERRIDE_ENV = "FABLE_DRIFT_OVERRIDE"


def drift_block_error(profile, task, env=None):
    """Return the blocking error string for this daf/task, or None.
    Override requires the Fable-only environment variable (mirroring the
    RASHI_ALLOWLIST_RESTRUCTURE precedent); worker prompts never mention
    it, so a worker following its generated packet cannot trip it."""
    if task not in DRIFT_BLOCKED_TASKS or profile is None or profile["haikuSafe"]:
        return None
    env = os.environ if env is None else env
    if env.get(DRIFT_OVERRIDE_ENV) == "1":
        return None
    return (f"{profile['daf']}: drift profile classifies this daf "
            f"{profile['classification']} (anchors found {profile['anchorsFound']}, "
            f"missing {profile['anchorsMissing']}, max offset {profile['maxAbsOffset']}); "
            f"stub-only {task} work is forbidden here. Use "
            f"{profile['recommendedTaskType']} under Fable/Sonnet instead. "
            f"Override requires a Fable-issued manifest authorization "
            f"(authorizeDriftOverride) plus {DRIFT_OVERRIDE_ENV}=1.")


def gemara_ids(daf):
    text = DATA_JS.read_text()
    starts = [(m.group(1), m.start()) for m in re.finditer(r"// YOMA (\S+)", text)]
    for i, (d, s) in enumerate(starts):
        if d == daf:
            e = starts[i + 1][1] if i + 1 < len(starts) else len(text)
            return re.findall(r'id:\s*"(yoma-[0-9]+[ab]-l[0-9]+[ab]?)",\s*kind:\s*"gemara"',
                              text[s:e])
    return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec", help="daf (47a) or inclusive range (47a-48b)")
    ap.add_argument("--task", default="reconstruct",
                    choices=["reconstruct", "repair", "links", "shifted-block"],
                    help="repair-type tasks may target daf with existing allowlist hits")
    opts = ap.parse_args()
    targets = expand_targets(opts.spec)
    errors = []

    branch = sh(["git", "rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
    dirty = sh(["git", "status", "--porcelain"]).stdout.strip()
    hooks = sh(["git", "config", "core.hooksPath"]).stdout.strip()
    version = (REPO / "VERSION").read_text().strip()

    print(f"VERSION: {version}")
    print(f"branch:  {branch} ({'DIRTY' if dirty else 'clean'})")
    print(f"hooks:   core.hooksPath={hooks or '(unset)'}")
    if dirty:
        errors.append("git tree is dirty; commit or stash before starting")
    if hooks != "githooks":
        errors.append("core.hooksPath is not 'githooks'; run: git config core.hooksPath githooks")

    fresh = sh([sys.executable, str(SCRIPTS / "check_generated_freshness.py")], cwd=ROOT)
    print(f"freshness: {'OK' if fresh.returncode == 0 else 'STALE'}")
    if fresh.returncode != 0:
        errors.append("generated learning_data.js/coverage.json are stale; regenerate first")

    content_allow = json.loads((ALLOW_DIR / "rashi_content_allowlist.json").read_text())
    allow_lines = {}
    for e in content_allow.get("entries", []):
        allow_lines.setdefault(e["daf"], []).append(e["vilnaLine"])
    count_mm = {c["daf"]: c for c in content_allow.get("count_mismatches", [])}
    rep_base = json.loads((ALLOW_DIR / "rashi_repetition_baseline.json").read_text())
    rep_daf = {e["daf"] for e in rep_base.get("entries", [])}

    for daf in targets:
        td = TALMUDDEV_DIR / f"{daf}.json"
        if not td.exists():
            errors.append(f"{daf}: no talmuddev source")
            continue
        raw = [l for l in json.loads(td.read_text()).get("rashi", []) if l and l.strip()]
        lp = LEARN_DIR / f"{daf}.learning.json"
        trans = json.loads(lp.read_text()).get("rashiTranslations", []) if lp.exists() else []
        ids = gemara_ids(daf)
        empty = sum(1 for e in trans if not e.get("linkedGemaraLineIds"))
        hits = sorted(allow_lines.get(daf, []))
        profile = audit_rashi_semantic.profile_daf(daf)

        print(f"\n=== {daf} ===")
        print(f"raw Rashi lines:      {len(raw)}")
        print(f"rashiTranslations:    {len(trans)}"
              + (f"  (documented count mismatch: {count_mm[daf]['note'][:60]})" if daf in count_mm else ""))
        print(f"real Gemara ids:      {len(ids)}  ({', '.join(i.split('-')[-1] for i in ids)})")
        print(f"empty links:          {empty}/{len(trans)}"
              + (f" ({100*empty/len(trans):.0f}%)" if trans else ""))
        print(f"content allowlist:    {hits or 'none'}")
        print(f"repetition baseline:  {'yes' if daf in rep_daf else 'none'}")
        if profile:
            print(f"drift profile:        {profile['classification']} "
                  f"(anchors {profile['anchorsFound']} found / {profile['anchorsMissing']} missing, "
                  f"max offset {profile['maxAbsOffset']}); "
                  f"haiku-safe for line-level work: {'yes' if profile['haikuSafe'] else 'NO'}")

        blocked = bool(hits) or daf in count_mm or daf in rep_daf
        if blocked and opts.task not in ("repair", "shifted-block", "links"):
            errors.append(f"{daf}: has unresolved allowlist/baseline hits; "
                          f"task {opts.task!r} is not a repair task. Use --task repair "
                          f"(or fix the plan) before starting.")
        drift_err = drift_block_error(profile, opts.task)
        if drift_err:
            errors.append(drift_err)

    print("\n## Allowed files for this content PR")
    for f in ALLOWED_FILES:
        print(f"- {f}")
    print("\n## Post-edit commands")
    for c in POST_EDIT:
        print(f"- {c}")

    if errors:
        print("\nPREFLIGHT FAILED:")
        for e in errors:
            print(f"  ERROR  {e}")
        sys.exit(1)
    print(f"\nOK: preflight passed for {', '.join(targets)} (task: {opts.task}).")


if __name__ == "__main__":
    main()
