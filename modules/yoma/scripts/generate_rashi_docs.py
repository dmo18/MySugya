#!/usr/bin/env python3
"""
generate_rashi_docs.py - regenerate the live-truth sections of
docs/rashi-audit-backlog.md (the scaffold-status table and the CURRENT
STATUS summary block) from the committed scaffold-debt baseline, the
corpus's rashiTranslations counts, and the curated task-type map.

Historical narrative sections ("Batch N findings", per-daf "resolved"
write-ups) are preserved untouched; this only rewrites the two
machine-generated regions marked with HTML comments:

  <!-- rashi-status-summary:begin --> ... <!-- rashi-status-summary:end -->
  <!-- scaffold-status-table:begin --> ... <!-- scaffold-status-table:end -->

Usage:
  python3 scripts/generate_rashi_docs.py           # write the doc
  python3 scripts/generate_rashi_docs.py --check   # exit 1 if doc is stale
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
LEARN_DIR = ROOT / "assets" / "learning" / "yoma"
BASELINE = SCRIPTS / "baselines" / "rashi_scaffold_debt.json"
TASK_MAP = SCRIPTS / "rashi_task_type_map.json"
DOC = REPO_ROOT / "docs" / "rashi-audit-backlog.md"
VERSION_FILE = REPO_ROOT / "VERSION"

sys.path.insert(0, str(SCRIPTS))
import audit_rashi_scaffold as asc  # noqa: E402


def git_head_short():
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                              cwd=REPO_ROOT, capture_output=True, text=True,
                              check=True)
        return out.stdout.strip()
    except Exception:
        return "unknown"


def live_version():
    return VERSION_FILE.read_text().strip()


def build_table():
    baseline = json.loads(BASELINE.read_text())
    by_daf = {}
    for e in baseline["entries"]:
        by_daf.setdefault(e["daf"], []).append(e)

    task_map = json.loads(TASK_MAP.read_text())
    curated = task_map["entries"]
    default_plain = task_map["defaultForPlainMetaOnly"]
    default_recon = task_map["defaultForReconstructionDebt"]
    default_resolved = task_map["defaultForResolved"]

    head = git_head_short()

    # Every daf that currently has debt, plus every daf the curated map or
    # the previous table already tracks (so resolved daf keep their row).
    tracked_daf = set(by_daf) | set(curated) | set(_previous_row_daf())

    rows = []
    for daf in sorted(tracked_daf, key=asc.daf_sort_key):
        path = LEARN_DIR / f"{daf}.learning.json"
        if not path.exists():
            continue
        total = len(json.loads(path.read_text()).get("rashiTranslations", []))
        entries = by_daf.get(daf, [])
        contaminated = len(entries)
        rules_present = {e["rule"] for e in entries}
        severity = f"{round(100 * contaminated / total)}%" if total else "0%"
        status = "resolved" if contaminated == 0 else "open"
        if daf in curated:
            task = curated[daf]
        elif contaminated == 0:
            task = default_resolved
        elif rules_present <= {"plain-meta-scaffold"}:
            task = default_plain
        else:
            task = default_recon
        rows.append((daf, contaminated, total, severity, task, status, head))
    return rows, len(baseline["entries"]), len({e["daf"] for e in baseline["entries"]})


def _previous_row_daf():
    if not DOC.exists():
        return []
    text = DOC.read_text()
    m = re.search(
        r"<!-- scaffold-status-table:begin.*?-->\n(.*?)\n<!-- scaffold-status-table:end -->",
        text, re.DOTALL)
    if not m:
        return []
    lines = m.group(1).strip().split("\n")[2:]
    out = []
    for line in lines:
        cols = [c.strip() for c in line.strip("|").split("|")]
        if cols:
            out.append(cols[0])
    return out


# The 2b/3a/3b/7b low-severity cluster is a separately-tracked pre-existing
# workstream (see docs/rashi-audit-backlog.md history): 3 of its 4 daf are
# classified rashi-repair, but 3b alone is rashi-reconstruction, which would
# otherwise sort first purely by daf number. Excluded from "next target" so
# the pointer reflects the active campaign's real queue, not this cluster.
SEPARATELY_TRACKED_CLUSTER = {"2b", "3a", "3b", "7b"}


def next_target(rows):
    for daf, contaminated, _total, _sev, task, status, _hv in rows:
        if daf in SEPARATELY_TRACKED_CLUSTER:
            continue
        if status == "open" and task == "rashi-reconstruction":
            return daf
    for daf, contaminated, _total, _sev, task, status, _hv in rows:
        if daf in SEPARATELY_TRACKED_CLUSTER:
            continue
        if status == "open":
            return daf
    return "none - all tracked daf resolved"


def render_table(rows):
    lines = [
        "<!-- scaffold-status-table:begin (regenerate with "
        "`python3 scripts/generate_rashi_docs.py`; do not hand-edit rows) -->",
        "| daf | contaminated | total | severity | task recommendation | status | last verified |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for daf, contaminated, total, severity, task, status, hv in rows:
        lines.append(f"| {daf} | {contaminated} | {total} | {severity} | {task} | {status} | {hv} |")
    lines.append("<!-- scaffold-status-table:end -->")
    return "\n".join(lines)


def render_summary(rows, total_debt, affected_daf):
    version = live_version()
    head = git_head_short()
    target = next_target(rows)
    resolved = sum(1 for r in rows if r[5] == "resolved")
    open_count = sum(1 for r in rows if r[5] == "open")
    lines = [
        "<!-- rashi-status-summary:begin (regenerate with "
        "`python3 scripts/generate_rashi_docs.py`; do not hand-edit) -->",
        f"- Current VERSION: {version}",
        f"- Generated from commit: {head} (the commit this doc was generated "
        "from, necessarily pre-merge for the PR that carries this change; it "
        "will differ from live main's HEAD immediately after that PR merges "
        "by design, since a PR's own merge commit does not exist yet at "
        "generation time. Not a staleness signal; see the freshness gate for "
        "what actually indicates staleness.)",
        f"- Total scaffold-debt entries (all rules, current inventory): {total_debt}",
        f"- Unique affected daf: {affected_daf}",
        f"- Tracked daf in status table: {len(rows)} ({resolved} resolved, {open_count} open)",
        f"- Current next reconstruction target: {target}",
        "- Rule families: scaffold-prefix / line-number-scaffold / hebrew-passthrough "
        "(the original \"Rashi: opens ...\" family) and plain-meta-scaffold (the same "
        "translator-position narration without the literal word \"Rashi\": \"Opens 'X':\", "
        "\"continuing:\", \"closing:\", \"Then opens\").",
        "- Historical narrative sections below (\"Batch N findings\", per-daf \"resolved\" "
        "write-ups) are preserved as historical fact; they do NOT reflect current status. "
        "The table above and this summary are the only current-truth sections.",
        "<!-- rashi-status-summary:end -->",
    ]
    return "\n".join(lines)


def apply(doc_text, rows, total_debt, affected_daf):
    new_summary = render_summary(rows, total_debt, affected_daf)
    new_table = render_table(rows)
    doc_text = re.sub(
        r"<!-- rashi-status-summary:begin.*?-->.*?<!-- rashi-status-summary:end -->",
        new_summary, doc_text, count=1, flags=re.DOTALL)
    doc_text = re.sub(
        r"<!-- scaffold-status-table:begin.*?-->.*?<!-- scaffold-status-table:end -->",
        new_table, doc_text, count=1, flags=re.DOTALL)
    return doc_text


def parse_current_summary(text):
    m = re.search(
        r"<!-- rashi-status-summary:begin.*?-->\n(.*?)\n<!-- rashi-status-summary:end -->",
        text, re.DOTALL)
    if not m:
        return {}
    body = m.group(1)
    out = {}
    v = re.search(r"Current VERSION:\s*(\S+)", body)
    if v:
        out["version"] = v.group(1)
    td = re.search(r"Total scaffold-debt entries.*?:\s*(\d+)", body)
    if td:
        out["total_debt"] = int(td.group(1))
    ad = re.search(r"Unique affected daf:\s*(\d+)", body)
    if ad:
        out["affected_daf"] = int(ad.group(1))
    nt = re.search(r"Current next reconstruction target:\s*(.+)", body)
    if nt:
        out["next_target"] = nt.group(1).strip()
    return out


def parse_current_table(text):
    m = re.search(
        r"<!-- scaffold-status-table:begin.*?-->\n(.*?)\n<!-- scaffold-status-table:end -->",
        text, re.DOTALL)
    if not m:
        return {}
    lines = m.group(1).strip().split("\n")[2:]
    out = {}
    for line in lines:
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) != 7:
            continue
        daf, contaminated, total, _sev, _task, status, _hv = cols
        out[daf] = {"contaminated": int(contaminated), "total": int(total), "status": status}
    return out


def check_freshness(rows, total_debt, affected_daf, current_text):
    """Semantic freshness check: compares the fields the doc claims to
    live-computed truth. Deliberately ignores the volatile per-row "last
    verified" commit hash, the summary's "Generated from commit" line, and
    exact table formatting/whitespace. These commit-hash fields cannot be
    hard-enforced against live main: a PR's docs are always generated before
    that PR's own merge commit exists, so the recorded commit necessarily
    differs from main's HEAD the moment the PR merges, through no fault of
    the content. Enforcing equality here would make the gate fail on every
    single merge. The fields the operator's freshness criteria actually care
    about (VERSION, aggregate counts, next target, per-daf status/counts) are
    the ones checked below."""
    problems = []

    summary = parse_current_summary(current_text)
    live_version_str = VERSION_FILE.read_text().strip()
    if summary.get("version") != live_version_str:
        problems.append(f"documented VERSION {summary.get('version')!r} != live {live_version_str!r}")
    if summary.get("total_debt") != total_debt:
        problems.append(f"documented total debt {summary.get('total_debt')!r} != live {total_debt}")
    if summary.get("affected_daf") != affected_daf:
        problems.append(f"documented affected-daf count {summary.get('affected_daf')!r} != live {affected_daf}")

    live_target = next_target(rows)
    if summary.get("next_target") != live_target:
        problems.append(f"documented next target {summary.get('next_target')!r} != live {live_target!r}")

    doc_table = parse_current_table(current_text)
    live_by_daf = {r[0]: r for r in rows}
    for daf, live in live_by_daf.items():
        _daf, contaminated, total, _sev, _task, status, _hv = live
        doc_row = doc_table.get(daf)
        if doc_row is None:
            problems.append(f"{daf}: missing from documented table (live has debt/history)")
            continue
        if doc_row["contaminated"] != contaminated:
            problems.append(f"{daf}: documented contaminated={doc_row['contaminated']} != live {contaminated}")
        if doc_row["total"] != total:
            problems.append(f"{daf}: documented total={doc_row['total']} != live {total}")
        if doc_row["status"] != status:
            problems.append(f"{daf}: documented status={doc_row['status']!r} != live {status!r}")
    for daf in doc_table:
        if daf not in live_by_daf:
            problems.append(f"{daf}: documented but no longer tracked live "
                             f"(daf file missing or dropped from baseline+curated map)")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if the committed doc's counts/status/target diverge "
                         "from live repository truth (ignores the volatile per-row "
                         "commit hash and exact formatting)")
    opts = ap.parse_args()

    rows, total_debt, affected_daf = build_table()
    current = DOC.read_text()

    if opts.check:
        problems = check_freshness(rows, total_debt, affected_daf, current)
        if problems:
            print("STALE: docs/rashi-audit-backlog.md does not match live repository truth:")
            for p in problems:
                print(f"  - {p}")
            sys.exit("Run: python3 scripts/generate_rashi_docs.py")
        print("OK: docs/rashi-audit-backlog.md is fresh.")
        return

    updated = apply(current, rows, total_debt, affected_daf)
    DOC.write_text(updated)
    print(f"wrote {DOC} ({len(rows)} tracked daf, {total_debt} debt entries "
          f"across {affected_daf} daf)")


if __name__ == "__main__":
    main()
