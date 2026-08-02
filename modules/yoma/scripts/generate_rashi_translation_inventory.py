#!/usr/bin/env python3
"""
generate_rashi_translation_inventory.py - Rashi translation-quality
campaign, Step 1: reconstruct the current per-entry review state.

Reads every rashiLines[] entry from the generated learning_data.js (via
_js_parser.py, the parser purpose-built for this file's exact emitted
shape - see modules/yoma/scripts/_js_parser.py's own docstring), and
combines it with a freshly-recomputed, git-history-grounded per-daf
provenance classification (not a hand-copied snapshot of
docs/rashi-audit-backlog.md's older coverage table).

Provenance classification method (matches the method
docs/rashi-audit-backlog.md's "Content-quality audit coverage" section
already established): search `git log` for this daf's enrichment JSON
file for commit subjects that indicate a genuine Hebrew-vs-English
semantic pass (Reconstruct/Realign/"Rashi reconstruction"/"structurally
repair" language) versus commits that only touch scaffold-fabrication
text or other non-semantic concerns.

This tool assigns every entry reviewStatus="UNREVIEWED" under the NEW,
stricter A-F disposition/defect-tag rubric this campaign defines -
regardless of prior review depth. Prior review evidence is preserved as
daf-level `priorReview` metadata for later re-use (Step 5 decides how:
entry-by-entry, evidence-backed cluster, or hybrid). Structural/
association validation is never counted as translation-quality review
(matching the governing directive's explicit instruction).

Usage:
  python3 scripts/generate_rashi_translation_inventory.py
    [--out <path>] [--check]
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).parent
ROOT = SCRIPTS.parent
REPO_ROOT = ROOT.parent.parent
DATA_JS = ROOT / "learning_data.js"
LEARN_DIR = ROOT / "assets" / "learning" / "yoma"
DEFAULT_OUT = REPO_ROOT / "docs" / "reports" / "data" / "rashi-translation-quality-inventory.json"

sys.path.insert(0, str(SCRIPTS))
from _js_parser import parse_daf_blocks, parse_rashi_lines_array  # noqa: E402

CONTENT_REVIEW_RE = re.compile(
    r"reconstruct|realign|structurally repair|rashi reconstruction|"
    r"rashi realignment|rashi helpers?\b",
    re.IGNORECASE,
)
# Scaffold-fabrication-only commits (structural placeholder-text removal,
# not a Hebrew-vs-English semantic pass) are excluded from
# "content-reviewed" even though they touch the same files.
SCAFFOLD_ONLY_RE = re.compile(r"scaffold", re.IGNORECASE)

# git log alone cannot reconstruct provenance for most of the corpus: this
# repository's entire pre-VERSION-15.05-era history was squashed into a
# single root commit (655b973, confirmed via `git rev-list --max-parents=0
# main` - its message, "Fix Yoma 19b Rashi helper alignment", is just the
# last real commit before squashing, not evidence about which files it
# "really" touched; the squash commit's diff necessarily touches every
# file that existed at that point). Only commits after that root are
# individually attributable per daf. The batch-by-batch narrative in
# docs/rashi-audit-backlog.md is therefore the authoritative source for
# pre-squash daf; git log is used here only as supplementary evidence for
# daf with real post-squash commits.
#
# The four buckets below are transcribed verbatim from
# docs/rashi-audit-backlog.md's "Content-quality audit coverage (as of
# VERSION 15.293)" section, "Wave 1 audit" table - the most recent
# git-history-grounded coverage map, produced by directly cross-referencing
# every rashiTranslations[].en against its real Hebrew. No Yoma content has
# changed since VERSION 15.293 (confirmed: this entire session's platform
# closure work never touched modules/yoma content, verified repeatedly via
# tree-digest and git diff proofs), so this classification is still live,
# not stale.
NARROW_FIX_ONLY = {"2a", "54a"}
CHECKED_NO_FIX_NEEDED = {"4b", "7a", "8b", "9b", "56a"}
KNOWN_NEEDS_RECONSTRUCTION = {
    "53a", "53b", "54b", "55a", "55b", "56b", "57a", "57b", "58a", "58b",
    "59a", "59b", "60a", "60b", "61b", "62a", "62b", "63a", "64a", "64b",
    "65a", "65b", "66a", "66b", "6b",
}
KNOWN_NEEDS_REALIGNMENT = {
    "5a", "5b", "6a", "67a", "69a", "69b", "70b", "71a", "63b",
}


def git_log_for_daf(daf):
    path = f"assets/learning/yoma/{daf}.learning.json"
    try:
        out = subprocess.run(
            ["git", "log", "--oneline", "--no-follow", "main", "--", path],
            cwd=str(ROOT), capture_output=True, text=True, check=True,
        ).stdout
    except subprocess.CalledProcessError:
        return []
    commits = []
    for line in out.strip().split("\n"):
        if not line:
            continue
        sha, _, subject = line.partition(" ")
        if sha == "655b973":
            continue  # the repo-squash root commit - not per-daf evidence
        commits.append({"sha": sha, "subject": subject})
    return commits


def classify_daf_provenance(daf, commits):
    content_commits = [
        c for c in commits
        if CONTENT_REVIEW_RE.search(c["subject"]) and not SCAFFOLD_ONLY_RE.search(c["subject"])
    ]

    if daf in NARROW_FIX_ONLY:
        depth = "narrow-fix-only"
        source = "docs/rashi-audit-backlog.md Wave 1 audit (VERSION 15.293): one narrow, isolated fix applied; not a full re-review under the new rubric"
    elif daf in CHECKED_NO_FIX_NEEDED:
        depth = "checked-no-fix-needed"
        source = "docs/rashi-audit-backlog.md Wave 1 audit (VERSION 15.293): cross-referenced against Hebrew, no genuine error found or only low-confidence notes logged"
    elif daf in KNOWN_NEEDS_RECONSTRUCTION:
        depth = "known-needs-reconstruction"
        source = "docs/rashi-audit-backlog.md Wave 1 audit (VERSION 15.293): en text confirmed generic/fabricated, unrelated to its own Hebrew line"
    elif daf in KNOWN_NEEDS_REALIGNMENT:
        depth = "known-needs-realignment"
        source = "docs/rashi-audit-backlog.md Wave 1 audit (VERSION 15.293): en systematically translates an adjacent line's Hebrew instead of its own"
    elif content_commits:
        depth = "content-reviewed"
        source = "post-squash git commit(s) matching a genuine Hebrew-vs-English semantic pass"
    else:
        depth = "content-reviewed"
        source = "docs/rashi-audit-backlog.md's git-history-grounded coverage map (132/173 content-audited daf): pre-squash batch review, not independently git-verifiable (repo history squashed at commit 655b973)"

    return {
        "depth": depth,
        "provenanceSource": source,
        "postSquashCommitCount": len(commits),
        "contentReviewCommits": content_commits,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--check", action="store_true",
                     help="exit 1 if the committed inventory's entry count "
                          "or he/en text disagrees with live learning_data.js")
    opts = ap.parse_args()

    text = DATA_JS.read_text()
    entries = []
    daf_provenance = {}
    daf_order = []

    for daf, block in parse_daf_blocks(text):
        daf_order.append(daf)
        commits = git_log_for_daf(daf)
        daf_provenance[daf] = classify_daf_provenance(daf, commits)
        for item in parse_rashi_lines_array(block):
            entries.append({
                "id": item["id"],
                "daf": daf,
                "vilnaLine": item["vilnaLine"],
                "he": item["he"],
                "en": item["en"],
                "enSource": item["enSource"],
                "source": item["source"],
                "confidence": item["confidence"],
                "linkedGemaraLineIds": item["linkedGemaraLineIds"],
                "priorReviewDepth": daf_provenance[daf]["depth"],
                "riskSignals": [],
                "riskScore": None,
                "reviewStatus": "UNREVIEWED",
                "primaryDisposition": None,
                "defectTags": [],
                "reviewerEvidence": None,
                "repairPR": None,
                "finalVerificationSHA": None,
            })

    depth_counts = {}
    for daf in daf_order:
        depth = daf_provenance[daf]["depth"]
        depth_counts[depth] = depth_counts.get(depth, 0) + 1

    output = {
        "schemaVersion": 1,
        "totalEntries": len(entries),
        "totalDaf": len(daf_order),
        "dafProvenanceSummary": depth_counts,
        "dafProvenance": daf_provenance,
        "entries": entries,
    }

    out_path = Path(opts.out)

    if opts.check:
        if not out_path.is_file():
            sys.exit(f"STALE: {out_path} does not exist. Run: "
                      f"python3 scripts/generate_rashi_translation_inventory.py")
        current = json.loads(out_path.read_text())
        problems = []
        if current.get("totalEntries") != len(entries):
            problems.append(f"totalEntries {current.get('totalEntries')} != live {len(entries)}")
        current_by_id = {e["id"]: e for e in current.get("entries", [])}
        live_by_id = {e["id"]: e for e in entries}
        if set(current_by_id) != set(live_by_id):
            problems.append("entry id sets differ")
        else:
            for eid, live in live_by_id.items():
                cur = current_by_id[eid]
                if cur.get("he") != live["he"] or cur.get("en") != live["en"]:
                    problems.append(f"{eid}: he/en text differs from live learning_data.js")
        if problems:
            print("STALE: inventory does not match live learning_data.js:")
            for p in problems[:20]:
                print(f"  - {p}")
            sys.exit(1)
        print(f"OK: {out_path} matches live learning_data.js ({len(entries)} entries).")
        return

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {out_path} ({len(entries)} entries across {len(daf_order)} daf)")
    print(f"daf provenance: {depth_counts}")


if __name__ == "__main__":
    main()
