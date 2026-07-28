#!/bin/bash

# Committer email GitHub stamps on commits it creates itself: squash-merge,
# rebase-merge, and ordinary merge commits made via the GitHub API or the
# web UI. A commit with this committer is a merge artifact the current
# session did not author (its author field is the repo owner or whoever
# opened the PR, not this session's identity) and cannot reattribute -
# GitHub verifies (or doesn't) its own merge commits by its own rules,
# unrelated to whether this session's commits are correctly signed.
GITHUB_MERGE_COMMITTER="noreply@github.com"

# Reads '%h %G? %ce' lines on stdin (one git-log entry per line) and writes
# only the lines that should be flagged as "GitHub will show this as
# Unverified". A commit committed by GitHub itself is never flagged here,
# regardless of its own %G? status (see GITHUB_MERGE_COMMITTER above);
# every other commit is flagged exactly as before: missing signature (%G?
# == N) or a committer email other than noreply@anthropic.com (the identity
# CCR's signing key is registered to).
#
# Kept as a standalone function, not inlined into the call site, so it can
# be sourced and unit-tested directly without running the rest of this
# script: see scripts/test_stop_hook_git_check.py.
filter_unverifiable_commits() {
  awk -v github="$GITHUB_MERGE_COMMITTER" \
    '$3 == github { next } $2 == "N" || $3 != "noreply@anthropic.com"'
}

# Counts commits in "$1..HEAD" that represent real local work awaiting a
# push. Excludes commits committed by GitHub for the same reason
# filter_unverifiable_commits does: after a worker branch resets to its own
# squash-merged origin/main, the merge commit lands in upstream..HEAD only
# because this branch's own remote-tracking ref is stale (still pointing at
# the pre-merge commit), not because there is unpushed work - that work is
# already on origin/main, just under a different commit hash. A genuinely
# unpushed commit authored during this session is still counted normally.
count_unpushed_commits() {
  git log --format='%ce' "$1..HEAD" 2>/dev/null \
    | awk -v github="$GITHUB_MERGE_COMMITTER" '$1 != github' | wc -l | tr -d '[:space:]'
}

# Guard so this file can be `source`d purely for filter_unverifiable_commits
# above (e.g. from the test suite) without running the checks below, which
# assume they are the active Stop hook (read stdin, inspect the live repo).
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then

# Read the JSON input from stdin
input=$(cat)

# Check if stop hook is already active (recursion prevention)
stop_hook_active=$(echo "$input" | jq -r '.stop_hook_active')
if [[ "$stop_hook_active" = "true" ]]; then
  exit 0
fi

# Check if we're in a git repository - bail if not
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  exit 0
fi

# Bail if there's no remote to push to. Every error path below asks the user
# to "push to the remote branch" — meaningless without a remote, and
# unsatisfiable if signing also requires a source. This case arises when CCR
# was launched against a local repo with no github remote (sources=[]) and
# the container's cwd has a leftover .git from a cached resume.
if [[ -z "$(git remote)" ]]; then
  exit 0
fi

# Check for uncommitted changes (both staged and unstaged)
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "There are uncommitted changes in the repository. Please commit and push these changes to the remote branch." >&2
  exit 2
fi

# Check for untracked files that might be important
untracked_files=$(git ls-files --others --exclude-standard)
if [[ -n "$untracked_files" ]]; then
  echo "There are untracked files in the repository. Please commit and push these changes to the remote branch." >&2
  exit 2
fi

current_branch=$(git branch --show-current)
if [[ -n "$current_branch" ]]; then
  if git rev-parse "origin/$current_branch" >/dev/null 2>&1; then
    upstream="origin/$current_branch"
  else
    upstream="origin/HEAD"
  fi

  # Check for local commits that GitHub will show as "Unverified": either no
  # signature at all (%G? == N), or signed with a committer email other than
  # noreply@anthropic.com (the identity CCR's signing key is registered to) -
  # excluding commits GitHub itself committed (squash/rebase/merge via the
  # API or web UI), which are merge artifacts, not commits this session
  # authored, and are verified (or not) by GitHub's own rules regardless of
  # this session's signing setup. This case is common and expected: a
  # worker branch that resets to origin/main after every merge lands its
  # tip on exactly such a commit. Only run when commit signing is
  # configured. Note: %G? is N for unsigned commits; signed-but-locally-
  # unverifiable commits report B/U/E, so this is a reliable presence check
  # even though CCR doesn't configure local verification.
  if [[ "$(git config --type=bool commit.gpgsign 2>/dev/null)" == "true" ]]; then
    unverifiable=$(git log --format='%h %G? %ce' "$upstream..HEAD" 2>/dev/null | filter_unverifiable_commits)
    if [[ -n "$unverifiable" ]]; then
      echo "There are commit(s) on branch '$current_branch' that GitHub will show as Unverified (missing signature, or committer email is not noreply@anthropic.com):" >&2
      echo "$unverifiable" >&2
      echo "Please run 'git config user.email noreply@anthropic.com && git config user.name Claude', then 'git commit --amend --no-edit --reset-author' for the tip commit, or 'git rebase --exec \"git commit --amend --no-edit --reset-author\" $upstream' for earlier commits, then push." >&2
      exit 2
    fi
  fi

  unpushed=$(count_unpushed_commits "$upstream")
  if [[ "$unpushed" -gt 0 ]]; then
    if [[ "$upstream" == "origin/$current_branch" ]]; then
      echo "There are $unpushed unpushed commit(s) on branch '$current_branch'. Please push these changes to the remote repository." >&2
    else
      echo "Branch '$current_branch' has $unpushed unpushed commit(s) and no remote branch. Please push these changes to the remote repository." >&2
    fi
    exit 2
  fi
fi

exit 0

fi # end BASH_SOURCE guard
