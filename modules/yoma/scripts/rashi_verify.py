#!/usr/bin/env python3
"""
rashi_verify.py - single post-edit verification command for bounded Rashi
work. Runs every gate in the right order and summarizes exactly what
changed, so a worker model does not improvise its own checklist.

Usage:
  python3 scripts/rashi_verify.py 47a            # fast: offline gates only
  python3 scripts/rashi_verify.py 47a 47b --full # adds build + tests
  --base <ref>   scope/diff base (default origin/main)

Fast mode runs, in order:
  check_generated_freshness, validate_rashi_content, validate_rashi_links,
  validate_rashi_repetition, check_rashi_pr_scope (vs base), plus the
  advisory semantic audit scoped to the target daf (printed, never fatal),
  and the remaining offline gates (schema, daftext, rashi structural,
  literal, order) via their scripts.

Full mode additionally runs from the repo root:
  npm run build, npm run check:deploy-html, npm test, npm run test:browser.

Summary includes: pass/fail per gate, files changed vs base, which JSON
fields changed in learning JSONs, allowlist entry delta (added entries are
a hard FAIL here too), semantic warnings for the target daf, and the exact
next command. Exit 1 if any hard gate failed.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).parent
ROOT = SCRIPTS.parent
REPO = ROOT.parent.parent
ALLOW_DIR = SCRIPTS / "allowlists"

FAST_GATES = [
    ("freshness", [sys.executable, "scripts/check_generated_freshness.py"]),
    ("content", [sys.executable, "scripts/validate_rashi_content.py"]),
    ("links", [sys.executable, "scripts/validate_rashi_links.py"]),
    ("repetition", [sys.executable, "scripts/validate_rashi_repetition.py"]),
    ("schema", [sys.executable, "scripts/validate_schema_completeness.py"]),
    ("daftext", [sys.executable, "scripts/validate_daftext.py"]),
    ("rashi-structural", [sys.executable, "scripts/validate_rashi.py"]),
    ("literal", [sys.executable, "scripts/validate_literal.py"]),
    ("order", [sys.executable, "scripts/order_audit.py"]),
]
FULL_STEPS = [
    ("build", ["npm", "run", "build"]),
    ("deploy-html", ["npm", "run", "check:deploy-html"]),
    ("unit+render", ["npm", "test"]),
    ("browser", ["npm", "run", "test:browser"]),
]


def sh(args, cwd):
    return subprocess.run(args, capture_output=True, text=True, cwd=cwd)


def allowlist_delta(base_rev):
    out = []
    for p in sorted(ALLOW_DIR.glob("*.json")):
        rel = p.relative_to(REPO).as_posix()
        r = sh(["git", "show", f"{base_rev}:{rel}"], REPO)
        old = json.loads(r.stdout) if r.returncode == 0 else {"entries": []}
        new = json.loads(p.read_text())
        oe = {json.dumps(e, sort_keys=True) for e in old.get("entries", [])}
        ne = {json.dumps(e, sort_keys=True) for e in new.get("entries", [])}
        if oe != ne:
            out.append((p.name, len(ne) - len(oe), len(ne - oe)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("daf", nargs="+", help="target daf, e.g. 47a")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--base", default="origin/main")
    opts = ap.parse_args()

    results = []
    for name, cmd in FAST_GATES:
        r = sh(cmd, ROOT)
        results.append((name, r.returncode == 0))
        if r.returncode != 0:
            print(f"--- {name} FAILED ---")
            print(r.stdout[-1500:])
            print(r.stderr[-500:], file=sys.stderr)

    scope = sh([sys.executable, "scripts/check_rashi_pr_scope.py", "--base", opts.base], ROOT)
    results.append(("pr-scope", scope.returncode == 0))
    if scope.returncode != 0:
        print("--- pr-scope FAILED ---")
        print(scope.stdout[-1500:])

    sem = sh([sys.executable, "scripts/audit_rashi_semantic.py", *opts.daf, "--top", "8"], ROOT)
    sem_shifts = re.findall(r"^  \S+ L\d+: Hebrew cites.*$", sem.stdout, re.M)

    if opts.full:
        for name, cmd in FULL_STEPS:
            r = sh(cmd, REPO)
            results.append((name, r.returncode == 0))
            if r.returncode != 0:
                print(f"--- {name} FAILED ---")
                print(r.stdout[-1500:])

    mb = sh(["git", "merge-base", opts.base, "HEAD"], REPO).stdout.strip()
    changed = sh(["git", "diff", "--name-only", mb], REPO).stdout.split() if mb else []
    deltas = allowlist_delta(mb) if mb else []

    print("\n================ rashi:verify summary ================")
    hard_fail = False
    for name, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        hard_fail |= not ok
    print(f"\nfiles changed vs {opts.base}: {len(changed)}")
    for f in changed:
        print(f"  {f}")
    if deltas:
        for fname, net, added in deltas:
            print(f"allowlist {fname}: net {net:+d} entries, {added} added")
            if added:
                print(f"  FAIL: allowlist entries were ADDED (workers may only remove stale entries)")
                hard_fail = True
    else:
        print("allowlists: unchanged")
    print(f"semantic audit ({', '.join(opts.daf)}): {len(sem_shifts)} shift candidate(s) [advisory]")
    for s in sem_shifts[:8]:
        print(f"  {s.strip()}")

    if hard_fail:
        print("\nVERIFY FAILED. Fix the content or STOP AND ESCALATE. "
              "Do not edit allowlists or validators.")
        sys.exit(1)
    nxt = ("commit, push, open the PR, and wait for CI"
           if opts.full else
           f"npm run rashi:verify:yoma -- {' '.join(opts.daf)} --full")
    print(f"\nVERIFY PASSED ({'full' if opts.full else 'fast'} mode). Next: {nxt}")


if __name__ == "__main__":
    main()
