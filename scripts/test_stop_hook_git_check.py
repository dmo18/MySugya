#!/usr/bin/env python3
"""
test_stop_hook_git_check.py - regression tests for
scripts/claude-hooks/stop-hook-git-check.sh.

Pins the fix for the squash-merge-commit false positive: after a worker
branch resets to origin/main following a merge, the branch tip is a
GitHub-created squash-merge commit (committer noreply@github.com), while
the branch's own remote-tracking ref (origin/<branch>) is stale, still
pointing at the pre-merge commit. This produced two false positives from
the same root cause, in this hook's checked order:

1. The prior check flagged the merge commit as an "Unverified" commit
   needing a local identity fix, whose only remedy (rebase + force-push)
   would rewrite main's own history to correct a cosmetic badge on a
   commit this session never authored.
2. Once (1) is fixed, the merge commit still appears in the stale
   upstream..HEAD range and was counted as an "unpushed commit" awaiting a
   push - also false, since that work is already on origin/main under a
   different commit hash.

The fix: a commit committed by GitHub itself is a merge artifact, excluded
from both checks regardless of its own %G? status. Every other commit -
including any genuinely unpushed or misattributed commit sitting in the
same range - is still checked exactly as before.

Two tiers, for a documented reason:

1. Unit tests of filter_unverifiable_commits (sourced directly from the
   hook script, run against synthetic '%h %G? %ce' lines). This is the only
   way to exercise a genuinely GOOD signature status (%G?=G): CCR signs
   commits via a remote signing proxy, but this sandbox has no local copy
   of the actual public key (~/.ssh/commit_signing_key.pub is a 0-byte
   placeholder) and no gpg.ssh.allowedSignersFile, so git can never
   locally verify a real signature here - every genuinely-signed local
   commit reads %G?=N in this environment regardless of validity. Unit
   tests supply the %G? value directly and so are unaffected by that
   sandbox limitation.
2. Integration tests that build a real temporary git repo and run the full
   script end to end, covering the actual control flow (recursion guard,
   dirty tree, untracked files, the gpgsign-gated block, unpushed-commit
   counting, exit codes) with real commits and real committer emails. These
   commits are necessarily unsigned (per the limitation above), so they
   exercise the "still flags a genuinely bad commit" and "reproduces and
   fixes the reported false positive" scenarios, not the "validly signed,
   so never flagged" scenario - that one is unit-tested only, for the
   reason given above.

Run: python3 scripts/test_stop_hook_git_check.py   (cwd repo root)
Exit 0 on success, 1 on failure.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).parent.parent
HOOK = REPO / "scripts" / "claude-hooks" / "stop-hook-git-check.sh"

FAILURES = []


def check(name, cond, detail=""):
    status = "ok" if cond else "FAIL"
    print(f"  {status}  {name}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        FAILURES.append(name)


# ---------------- Tier 1: unit tests of the filter function ----------------

def run_filter(lines):
    """Feed '%h %G? %ce' lines through filter_unverifiable_commits and
    return the surviving (flagged) lines."""
    script = f'source "{HOOK}"; filter_unverifiable_commits'
    r = subprocess.run(["bash", "-c", script], input="\n".join(lines) + "\n",
                        capture_output=True, text=True)
    return [l for l in r.stdout.splitlines() if l.strip()]


def test_filter_unit():
    print("filter_unverifiable_commits unit tests:")

    # (a) correctly attributed, validly signed local commit -> not flagged
    out = run_filter(["abc1234 G noreply@anthropic.com"])
    check("(a) correctly attributed + valid signature is not flagged", out == [])

    # (b) incorrectly attributed local commit -> flagged, even with a
    # signature that git reports as good (the signature isn't the issue,
    # the committer identity is)
    out = run_filter(["abc1234 G someone-else@example.com"])
    check("(b) wrong committer email is flagged even with G signature",
          len(out) == 1 and "someone-else@example.com" in out[0])

    # (b') the other half of "incorrectly attributed": unsigned, correct
    # committer email is still flagged (missing signature alone is enough)
    out = run_filter(["abc1234 N noreply@anthropic.com"])
    check("(b') unsigned commit with correct committer is still flagged",
          len(out) == 1)

    # (c) THE FIX: a GitHub squash-merge commit at the branch tip is never
    # flagged, regardless of its own %G? status (E is what real GitHub
    # merge commits report locally: GPG-signed by GitHub's own key, which
    # this sandbox cannot verify)
    for sig in ("E", "N", "G", "B", "U"):
        out = run_filter([f"abc1234 {sig} noreply@github.com"])
        check(f"(c) GitHub committer with signature status {sig} is not flagged",
              out == [])

    # (d) a reset branch whose tip is the GitHub merge commit, with a
    # correctly-attributed, validly-signed session commit also in range
    # (the exact shape of the reported bug: stale remote-tracking ref means
    # both the merge commit and an already-fine prior commit show up in the
    # upstream..HEAD diff) -> nothing is flagged
    out = run_filter([
        "def5678 G noreply@anthropic.com",
        "abc1234 E noreply@github.com",
    ])
    check("(d) merge commit + already-fine session commit -> nothing flagged",
          out == [])

    # (d') same shape, but the session commit really is broken -> only the
    # genuinely broken one survives, the merge commit still does not
    out = run_filter([
        "def5678 N wrong@example.com",
        "abc1234 E noreply@github.com",
    ])
    check("(d') merge commit excluded, genuinely broken session commit still flagged",
          len(out) == 1 and "wrong@example.com" in out[0])

    # Order/position independence: the github line first, in the middle,
    # last - never survives filtering in any position
    out = run_filter([
        "abc1234 E noreply@github.com",
        "def5678 G noreply@anthropic.com",
        "ghi9012 E noreply@github.com",
    ])
    check("(c) github committer excluded regardless of position", out == [])


def run_count_unpushed(repo, upstream):
    r = subprocess.run(["bash", "-c", f'source "{HOOK}"; count_unpushed_commits "$1"',
                        "_", upstream], cwd=str(repo), capture_output=True, text=True)
    return r.stdout.strip()


def test_count_unpushed_unit():
    print("count_unpushed_commits unit tests:")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        remote = init_bare_remote(tmp)
        repo = init_clone(tmp, remote, "work")
        commit_file(repo, "base.txt", "base\n", "base commit")
        git(repo, "branch", "-M", "main")
        git(repo, "push", "-q", "-u", "origin", "main")

        commit_file(repo, "gh.txt", "x\n", "github merge artifact",
                    committer_email="noreply@github.com", committer_name="GitHub")
        check("a GitHub-committed commit alone counts as 0 unpushed",
              run_count_unpushed(repo, "origin/main") == "0")

        commit_file(repo, "real.txt", "y\n", "real session work")
        check("a genuine session commit alongside it is still counted (1)",
              run_count_unpushed(repo, "origin/main") == "1")


# ---------------- Tier 2: integration tests (real temp git repos) ----------------

def git(repo, *args, env=None, check_rc=True):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env)
    if check_rc and r.returncode != 0:
        raise RuntimeError(f"git {args} failed: {r.stderr}")
    return r


def init_bare_remote(tmp):
    remote = tmp / "remote.git"
    remote.mkdir()
    subprocess.run(["git", "init", "--bare", "-q", str(remote)], check=True)
    return remote


def init_clone(tmp, remote, name):
    repo = tmp / name
    subprocess.run(["git", "clone", "-q", str(remote), str(repo)], check=True)
    git(repo, "config", "user.name", "Claude")
    git(repo, "config", "user.email", "noreply@anthropic.com")
    git(repo, "config", "commit.gpgsign", "false")
    return repo


def commit_file(repo, name, content, message, committer_email=None, committer_name="Claude"):
    (repo / name).write_text(content)
    git(repo, "add", name)
    env = None
    if committer_email:
        import os
        env = dict(os.environ, GIT_COMMITTER_EMAIL=committer_email, GIT_COMMITTER_NAME=committer_name)
    git(repo, "commit", "-q", "-m", message, env=env)


def run_hook(repo, stop_hook_active=False, gpgsign=True):
    if gpgsign:
        git(repo, "config", "commit.gpgsign", "true")
    payload = json.dumps({"stop_hook_active": stop_hook_active})
    r = subprocess.run(["bash", str(HOOK)], cwd=str(repo), input=payload,
                        capture_output=True, text=True)
    return r


def test_integration_clean_repo_no_warning():
    print("integration: clean, fully-pushed repo:")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        remote = init_bare_remote(tmp)
        repo = init_clone(tmp, remote, "work")
        commit_file(repo, "f.txt", "hello\n", "initial")
        git(repo, "branch", "-M", "main")
        git(repo, "push", "-q", "-u", "origin", "main")
        r = run_hook(repo, gpgsign=False)
        check("clean pushed repo exits 0", r.returncode == 0, r.stderr[-200:])


def test_integration_reproduces_and_fixes_false_positive():
    print("integration: reproduce and fix the squash-merge false positive:")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        remote = init_bare_remote(tmp)

        # Simulate main: a base commit, then a "PR" commit authored locally
        # and pushed to a feature branch, then squash-merged into main by
        # "GitHub" (committer noreply@github.com), exactly as the real
        # GitHub API does for a squash-merge button click.
        main_repo = init_clone(tmp, remote, "main_side")
        commit_file(main_repo, "base.txt", "base\n", "base commit")
        git(main_repo, "branch", "-M", "main")
        git(main_repo, "push", "-q", "-u", "origin", "main")

        feature = init_clone(tmp, remote, "feature_side")
        git(feature, "checkout", "-q", "-b", "claude/work", "origin/main")
        commit_file(feature, "feature.txt", "feature work\n", "Real session work")
        git(feature, "push", "-q", "-u", "origin", "claude/work")
        session_commit = git(feature, "rev-parse", "HEAD").stdout.strip()

        # "GitHub" squash-merges claude/work into main: a brand new commit,
        # parented on main's own history (not on the feature branch tip),
        # committed by GitHub.
        git(main_repo, "fetch", "-q", "origin")
        git(main_repo, "checkout", "-q", "main")
        git(main_repo, "merge", "-q", "--squash", "origin/claude/work")
        import os
        env = dict(os.environ, GIT_COMMITTER_EMAIL="noreply@github.com", GIT_COMMITTER_NAME="GitHub")
        git(main_repo, "commit", "-q", "-m", "Real session work (#1)", env=env)
        git(main_repo, "push", "-q", "origin", "main")
        merge_commit = git(main_repo, "rev-parse", "HEAD").stdout.strip()
        check("squash-merge commit differs from the original session commit",
              merge_commit != session_commit)

        # Now reproduce the exact reported scenario: the feature branch
        # working copy resets its local HEAD to origin/main (the documented
        # per-daf-cycle step), but its OWN remote-tracking ref
        # (origin/claude/work) is stale, still pointing at the pre-merge
        # session commit.
        git(feature, "fetch", "-q", "origin", "main")
        git(feature, "reset", "-q", "--hard", "origin/main")
        check("feature branch HEAD now IS the squash-merge commit",
              git(feature, "rev-parse", "HEAD").stdout.strip() == merge_commit)
        check("feature branch's own remote-tracking ref is stale (still the old commit)",
              git(feature, "rev-parse", "origin/claude/work").stdout.strip() == session_commit)

        r = run_hook(feature)
        check("FIXED hook does not flag the false positive (exits 0)",
              r.returncode == 0, r.stderr)
        check("no 'Unverified' message printed", "Unverified" not in r.stderr)


def test_integration_still_flags_genuinely_bad_committer():
    print("integration: a genuinely bad committer is still flagged:")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        remote = init_bare_remote(tmp)
        repo = init_clone(tmp, remote, "work")
        commit_file(repo, "base.txt", "base\n", "base")
        git(repo, "branch", "-M", "main")
        git(repo, "push", "-q", "-u", "origin", "main")

        # An unpushed commit with a committer email that is neither
        # noreply@anthropic.com nor GitHub's merge committer: a genuine
        # identity problem the hook must still catch.
        commit_file(repo, "oops.txt", "oops\n", "Misattributed commit",
                    committer_email="someone-else@example.com")

        r = run_hook(repo)
        check("bad committer still flagged (exit 2)", r.returncode == 2, r.stderr)
        check("message names the offending commit and committer",
              "someone-else@example.com" in r.stderr)


def test_integration_reset_branch_with_fine_prior_commit():
    print("integration: reset branch, merge commit tip, fine prior commit also in range:")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        remote = init_bare_remote(tmp)

        main_repo = init_clone(tmp, remote, "main_side")
        commit_file(main_repo, "base.txt", "base\n", "base commit")
        git(main_repo, "branch", "-M", "main")
        git(main_repo, "push", "-q", "-u", "origin", "main")

        feature = init_clone(tmp, remote, "feature_side")
        git(feature, "checkout", "-q", "-b", "claude/work", "origin/main")
        # A prior, unrelated local commit already sitting on the feature
        # branch (e.g. from an earlier docs-tooling pass in the same
        # session) that was pushed once and is genuinely fine.
        commit_file(feature, "prior.txt", "prior work\n", "Prior fine session commit")
        git(feature, "push", "-q", "-u", "origin", "claude/work")

        commit_file(feature, "feature.txt", "feature work\n", "Real session work")
        git(feature, "push", "-q", "origin", "claude/work")

        git(main_repo, "fetch", "-q", "origin")
        git(main_repo, "checkout", "-q", "main")
        git(main_repo, "merge", "-q", "--squash", "origin/claude/work")
        import os
        env = dict(os.environ, GIT_COMMITTER_EMAIL="noreply@github.com", GIT_COMMITTER_NAME="GitHub")
        git(main_repo, "commit", "-q", "-m", "Real session work (#2)", env=env)
        git(main_repo, "push", "-q", "origin", "main")

        # feature's own remote-tracking ref is stale at the FIRST pushed
        # commit (before the second push), so upstream..HEAD after reset
        # spans both the second session commit AND the merge commit.
        git(feature, "fetch", "-q", "origin", "claude/work")
        stale_ref = tmp / "stale_ref_snapshot.txt"
        stale_ref.write_text(git(feature, "rev-parse", "origin/claude/work").stdout)

        git(feature, "fetch", "-q", "origin", "main")
        git(feature, "reset", "-q", "--hard", "origin/main")

        r = run_hook(feature)
        check("exits 0 despite multiple commits in range (merge commit + prior fine commit)",
              r.returncode == 0, r.stderr)


def test_integration_merge_commit_tip_with_real_unpushed_work():
    print("integration: merge commit tip PLUS a genuinely unpushed real commit is still flagged:")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        remote = init_bare_remote(tmp)

        main_repo = init_clone(tmp, remote, "main_side")
        commit_file(main_repo, "base.txt", "base\n", "base commit")
        git(main_repo, "branch", "-M", "main")
        git(main_repo, "push", "-q", "-u", "origin", "main")

        feature = init_clone(tmp, remote, "feature_side")
        git(feature, "checkout", "-q", "-b", "claude/work", "origin/main")
        commit_file(feature, "feature.txt", "feature work\n", "Real session work")
        git(feature, "push", "-q", "-u", "origin", "claude/work")

        git(main_repo, "fetch", "-q", "origin")
        git(main_repo, "checkout", "-q", "main")
        git(main_repo, "merge", "-q", "--squash", "origin/claude/work")
        import os
        env = dict(os.environ, GIT_COMMITTER_EMAIL="noreply@github.com", GIT_COMMITTER_NAME="GitHub")
        git(main_repo, "commit", "-q", "-m", "Real session work (#3)", env=env)
        git(main_repo, "push", "-q", "origin", "main")

        # Reset feature to the merged main (stale origin/claude/work tip),
        # exactly as before, but then add ANOTHER real, correctly-attributed
        # commit that has genuinely never been pushed anywhere. This commit
        # must still be flagged: the GitHub-committer exclusion must not
        # swallow real unpushed work sitting in the same upstream..HEAD range.
        git(feature, "fetch", "-q", "origin", "main")
        git(feature, "reset", "-q", "--hard", "origin/main")
        commit_file(feature, "more.txt", "more real work\n", "More real session work")

        # gpgsign=False here isolates the unpushed-count path from the
        # identity-check path (real commits in this sandbox can never carry
        # a locally-verifiable signature, so with signing gated on, this
        # commit would be caught by the Unverified check first instead -
        # also a correct exit 2, but not what this test is isolating).
        r = run_hook(feature, gpgsign=False)
        check("genuinely unpushed commit alongside the merge commit is still flagged",
              r.returncode == 2 and "1 unpushed commit" in r.stderr, r.stderr)


def main():
    test_filter_unit()
    test_count_unpushed_unit()
    test_integration_clean_repo_no_warning()
    test_integration_reproduces_and_fixes_false_positive()
    test_integration_still_flags_genuinely_bad_committer()
    test_integration_reset_branch_with_fine_prior_commit()
    test_integration_merge_commit_tip_with_real_unpushed_work()
    if FAILURES:
        print(f"\nFAILED: {len(FAILURES)} check(s): {FAILURES}")
        sys.exit(1)
    print("\nOK: all stop-hook-git-check tests passed.")


if __name__ == "__main__":
    main()
