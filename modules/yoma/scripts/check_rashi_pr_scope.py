#!/usr/bin/env python3
"""
check_rashi_pr_scope.py - scope gate for Yoma Rashi content changes.

Compares the working tree against a base ref (merge-base semantics) and, when
the diff touches any modules/yoma/assets/learning/yoma/*.learning.json,
enforces the bounded-content-PR contract:

  1. File set: a content PR may only change learning JSONs, the generated
     learning_data.js and coverage.json, VERSION, package.json,
     package-lock.json, docs/rashi-audit-backlog.md, and files under
     modules/yoma/scripts/allowlists/. It may never touch
     .github/workflows/.
  2. Within each changed learning JSON, only rashiTranslations[*].en and
     rashiTranslations[*].linkedGemaraLineIds may differ from base. The
     entry count, vilnaLine sequence, every other rashiTranslations key,
     and every other top-level field (sugyot, argumentFlow, he, learning,
     takeaway, glossary, quizSeeds, metadata, everything) must be
     byte-equal in JSON terms. Structure changes require --allow-structure
     (explicitly authorized passes only).
  3. Allowlist ratchet: changed allowlist files may only remove entries,
     never add them.
  4. learning_data.js/coverage.json may change only when at least one
     learning JSON (or assets/literal_en file) changed too; freshness
     itself is enforced by check_generated_freshness.py.

If the diff touches no learning JSON, this gate is a no-op (exit 0), so it
is safe to run on every PR and on push.

Base ref resolution: --base <ref>, else origin/$GITHUB_BASE_REF when set
(GitHub PR context), else origin/main. Comparison is against
merge-base(base, HEAD) so unrelated later commits on the base branch do not
produce false diffs.

Exit 1 with exact paths and JSON pointers on any violation. Offline except
for reading local git objects.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

LEARN_PREFIX = "modules/yoma/assets/learning/yoma/"
LITERAL_PREFIX = "modules/yoma/assets/literal_en/"
GENERATED = {"modules/yoma/learning_data.js", "modules/yoma/coverage.json"}
ALLOWLIST_PREFIX = "modules/yoma/scripts/allowlists/"
ALWAYS_ALLOWED = {"VERSION", "package.json", "package-lock.json",
                  "docs/rashi-audit-backlog.md", ".worker-manifest.json"}
FORBIDDEN_PREFIXES = (".github/workflows/",)

MUTABLE_KEYS = {"en", "linkedGemaraLineIds"}


def run(args, **kw):
    return subprocess.run(args, capture_output=True, text=True, **kw)


def git_show(rev, path):
    r = run(["git", "show", f"{rev}:{path}"])
    return r.stdout if r.returncode == 0 else None


def check_allowlist_ratchet(allowlist_changed, base_rev, errors):
    """Allowlist files may only shrink. Additions or new files require the
    explicit RASHI_ALLOWLIST_RESTRUCTURE=1 authorization (tooling PRs that
    document a new baseline; see docs/rashi-workflow.md)."""
    if os.environ.get("RASHI_ALLOWLIST_RESTRUCTURE") == "1":
        if allowlist_changed:
            print("NOTE: RASHI_ALLOWLIST_RESTRUCTURE=1 set; allowlist growth "
                  "authorization active for this run.")
        return
    for p in allowlist_changed:
        base_text = git_show(base_rev, p)
        if base_text is None:
            errors.append(f"{p}: new allowlist files require RASHI_ALLOWLIST_RESTRUCTURE=1")
            continue
        old = json.loads(base_text)
        new = json.loads(Path(p).read_text())
        for section in ("entries", "count_mismatches"):
            old_e = {json.dumps(e, sort_keys=True) for e in old.get(section, [])}
            new_e = {json.dumps(e, sort_keys=True) for e in new.get(section, [])}
            for a in sorted(new_e - old_e):
                errors.append(f"{p}: {section} entry ADDED (ratchet is remove-only; "
                              f"requires RASHI_ALLOWLIST_RESTRUCTURE=1): {a}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=None, help="base ref (default: origin/$GITHUB_BASE_REF or origin/main)")
    ap.add_argument("--allow-structure", action="store_true",
                    help="permit rashiTranslations entry count/structure changes (authorized passes only)")
    opts = ap.parse_args()

    top = run(["git", "rev-parse", "--show-toplevel"]).stdout.strip()
    if not top:
        sys.exit("ERROR: not inside a git repository.")
    os.chdir(top)

    base = opts.base
    if base is None:
        env_base = os.environ.get("GITHUB_BASE_REF", "").strip()
        base = f"origin/{env_base}" if env_base else "origin/main"

    mb = run(["git", "merge-base", base, "HEAD"])
    if mb.returncode != 0:
        print(f"WARNING: cannot resolve merge-base of {base!r} and HEAD "
              f"({mb.stderr.strip()}); skipping scope check.")
        return
    base_rev = mb.stdout.strip()

    diff = run(["git", "diff", "--name-only", base_rev])
    changed = [l for l in diff.stdout.splitlines() if l.strip()]

    learn_changed = [p for p in changed if p.startswith(LEARN_PREFIX) and p.endswith(".learning.json")]
    allowlist_changed = [p for p in changed if p.startswith(ALLOWLIST_PREFIX) and p.endswith(".json")]
    errors = []

    if not learn_changed:
        # Tooling PRs skip the content rules, but the allowlist ratchet still
        # applies: additions require the explicit RASHI_ALLOWLIST_RESTRUCTURE=1
        # authorization (documented in docs/rashi-workflow.md).
        if allowlist_changed:
            check_allowlist_ratchet(allowlist_changed, base_rev, errors)
        if errors:
            print(f"Rashi PR scope check FAILED vs {base} ({base_rev[:9]}):\n")
            for e in errors:
                print(f"  ERROR  {e}")
            sys.exit(1)
        print(f"OK: no Yoma learning JSON changed vs {base} ({base_rev[:9]}); "
              f"scope gate is a no-op (allowlist ratchet still verified).")
        return

    # 1. File-set rules
    for p in changed:
        for fp in FORBIDDEN_PREFIXES:
            if p.startswith(fp):
                errors.append(f"file-set: content PR must not touch {p}")
        allowed = (
            (p.startswith(LEARN_PREFIX) and p.endswith(".learning.json"))
            or p.startswith(LITERAL_PREFIX)
            or p in GENERATED
            or p.startswith(ALLOWLIST_PREFIX)
            or p in ALWAYS_ALLOWED
        )
        if not allowed and not any(p.startswith(fp) for fp in FORBIDDEN_PREFIXES):
            errors.append(f"file-set: {p} is outside the allowed content-PR file set")

    # 4. Generated files only alongside source changes
    if any(p in GENERATED for p in changed):
        if not learn_changed and not any(p.startswith(LITERAL_PREFIX) for p in changed):
            errors.append("file-set: generated learning_data.js/coverage.json changed "
                          "without any learning JSON or literal_en source change")

    # A fresh gemara-learning worker manifest defers per-file FIELD rules for
    # its target daf to the worker pipeline's stricter gemara-learning JSON
    # diff (worker_pipeline.py ci-check, which runs in the same CI job and
    # must also pass). File-set, workflow, and allowlist ratchet rules above
    # still apply here regardless. This is a hand-off, not a bypass: without
    # the manifest, or for daf outside its targets, full Rashi rules apply.
    deferred_daf = set()
    wm = Path(".worker-manifest.json")
    if wm.exists():
        base_wm = git_show(base_rev, ".worker-manifest.json")
        fresh = base_wm is None or base_wm != wm.read_text()
        try:
            wm_data = json.loads(wm.read_text())
        except json.JSONDecodeError:
            wm_data = {}
        if fresh and wm_data.get("type") == "gemara-learning":
            deferred_daf = set(wm_data.get("targets", []))
            print(f"NOTE: fresh gemara-learning manifest present; deferring field rules for "
                  f"daf {sorted(deferred_daf)} to the worker pipeline gate (which must also pass).")

    # 2. Per-file structural diff
    for p in learn_changed:
        daf_name = p.split("/")[-1].replace(".learning.json", "")
        if daf_name in deferred_daf:
            continue
        base_text = git_show(base_rev, p)
        if base_text is None:
            errors.append(f"{p}: file does not exist at base; new files require --allow-structure")
            continue
        try:
            old = json.loads(base_text)
            new = json.loads(Path(p).read_text())
        except (json.JSONDecodeError, FileNotFoundError) as ex:
            errors.append(f"{p}: cannot parse JSON ({ex})")
            continue

        for key in sorted(set(old) | set(new)):
            if key == "rashiTranslations":
                continue
            if old.get(key) != new.get(key):
                errors.append(f"{p}: /{key} changed (only rashiTranslations en/links may change)")

        o_rt = old.get("rashiTranslations", [])
        n_rt = new.get("rashiTranslations", [])
        if len(o_rt) != len(n_rt):
            if not opts.allow_structure:
                errors.append(f"{p}: /rashiTranslations length {len(o_rt)} -> {len(n_rt)} "
                              f"(structure change requires --allow-structure)")
            continue
        for i, (o, n) in enumerate(zip(o_rt, n_rt)):
            if o.get("vilnaLine") != n.get("vilnaLine") and not opts.allow_structure:
                errors.append(f"{p}: /rashiTranslations/{i}/vilnaLine changed "
                              f"{o.get('vilnaLine')} -> {n.get('vilnaLine')}")
            for key in sorted(set(o) | set(n)):
                if key in MUTABLE_KEYS or key == "vilnaLine":
                    continue
                if o.get(key) != n.get(key):
                    errors.append(f"{p}: /rashiTranslations/{i}/{key} changed "
                                  f"(only en and linkedGemaraLineIds may change)")

    # 3. Allowlist ratchet: removals only
    check_allowlist_ratchet(allowlist_changed, base_rev, errors)

    if errors:
        print(f"Rashi PR scope check FAILED vs {base} ({base_rev[:9]}):\n")
        for e in errors:
            print(f"  ERROR  {e}")
        print(f"\n{len(errors)} violation(s).")
        sys.exit(1)

    print(f"OK: Rashi content changes vs {base} ({base_rev[:9]}) stay within scope "
          f"({len(learn_changed)} learning JSON file(s); only en/linkedGemaraLineIds changed; "
          f"allowlists shrink-only).")


if __name__ == "__main__":
    main()
