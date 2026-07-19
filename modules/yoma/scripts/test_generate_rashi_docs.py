#!/usr/bin/env python3
"""
test_generate_rashi_docs.py - regression tests for generate_rashi_docs.py:
table/summary rendering, the SEPARATELY_TRACKED_CLUSTER exclusion from next
target, curated vs default task-type classification, and the freshness
checker's ability to detect each class of staleness the operator specified
(VERSION mismatch, wrong aggregate counts, wrong per-daf status, wrong next
target) without being sensitive to the volatile per-row commit hash.

Offline, no network, no git mutation. Run from modules/yoma/:
  python3 scripts/test_generate_rashi_docs.py
"""
import sys
from pathlib import Path

SCRIPTS = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS))
import generate_rashi_docs as grd  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    print(f"  {'ok ' if cond else 'FAIL'} {name}" + (f" ({detail})" if detail and not cond else ""))
    if not cond:
        FAILED.append(name)


ROWS = [
    ("2b", 5, 29, "17%", "rashi-repair (after fresh semantic verification)", "open", "abc1234"),
    ("3b", 11, 49, "22%", "rashi-reconstruction", "open", "abc1234"),
    ("14b", 0, 59, "0%", "none (repaired and verified)", "resolved", "abc1234"),
    ("15a", 66, 66, "100%", "rashi-narration-repair", "open", "abc1234"),
    ("41b", 74, 74, "100%", "rashi-reconstruction", "open", "abc1234"),
    ("42a", 0, 52, "0%", "rashi-reconstruction", "resolved", "abc1234"),
]

print("next_target: skips the separately-tracked 2b/3a/3b/7b cluster")
check("1. reconstruction-classified 3b is NOT picked (cluster excluded)",
      grd.next_target(ROWS) == "41b", grd.next_target(ROWS))

print("next_target: falls back to any open daf if no reconstruction target remains")
rows_no_recon = [r for r in ROWS if r[4] != "rashi-reconstruction" or r[0] in grd.SEPARATELY_TRACKED_CLUSTER]
check("2. falls back to first open non-cluster daf",
      grd.next_target(rows_no_recon) == "15a", grd.next_target(rows_no_recon))

print("next_target: reports closure when nothing open outside the cluster")
rows_all_resolved = [r for r in ROWS if r[5] == "resolved" or r[0] in grd.SEPARATELY_TRACKED_CLUSTER]
check("3. all-resolved (outside cluster) reports closure",
      grd.next_target(rows_all_resolved) == "none - all tracked daf resolved")

print("render_table / render_summary round-trip through the parsers")
table_text = grd.render_table(ROWS)
parsed_table = grd.parse_current_table(
    f"prefix\n{table_text}\nsuffix")
check("4. parsed table has one row per input daf", len(parsed_table) == len(ROWS))
check("5. parsed row preserves contaminated/total/status",
      parsed_table["15a"] == {"contaminated": 66, "total": 66, "status": "open"})

summary_text = grd.render_summary(ROWS, total_debt=3564, affected_daf=83)
parsed_summary = grd.parse_current_summary(f"prefix\n{summary_text}\nsuffix")
check("6. parsed summary recovers total_debt", parsed_summary.get("total_debt") == 3564)
check("7. parsed summary recovers affected_daf", parsed_summary.get("affected_daf") == 83)
check("8. parsed summary recovers next_target",
      parsed_summary.get("next_target") == grd.next_target(ROWS))

print("check_freshness: detects each staleness class independently")


def doc_with(summary_rows=ROWS, summary_overrides=None, table_rows=ROWS):
    summary = grd.render_summary(summary_rows, total_debt=3564, affected_daf=83)
    if summary_overrides:
        for old, new in summary_overrides.items():
            summary = summary.replace(old, new)
    table = grd.render_table(table_rows)
    return f"intro\n{summary}\nmiddle\n{table}\ntail"


import tempfile  # noqa: E402

old_version_file = grd.VERSION_FILE
try:
    # Point at a scratch VERSION file instead of the real repository one, so
    # the check has a stable, isolated target to compare against.
    tmpdir = tempfile.mkdtemp()
    scratch_version = Path(tmpdir) / "VERSION"
    scratch_version.write_text("15.203\n")
    grd.VERSION_FILE = scratch_version

    fresh_doc = doc_with(summary_overrides={"Current VERSION: 15.203": "Current VERSION: 15.203"})
    problems = grd.check_freshness(ROWS, 3564, 83, fresh_doc)
    check("9. a doc generated from the same rows/totals is clean", not problems, str(problems))

    stale_version_doc = doc_with(summary_overrides={"Current VERSION: 15.203": "Current VERSION: 15.156"})
    problems = grd.check_freshness(ROWS, 3564, 83, stale_version_doc)
    check("10. stale VERSION is detected", any("VERSION" in p for p in problems), str(problems))

    stale_count_doc = doc_with(summary_overrides={
        "Total scaffold-debt entries (all rules, current inventory): 3564":
        "Total scaffold-debt entries (all rules, current inventory): 1023"})
    problems = grd.check_freshness(ROWS, 3564, 83, stale_count_doc)
    check("11. stale total-debt count is detected",
          any("total debt" in p for p in problems), str(problems))

    stale_target_doc = doc_with(summary_overrides={
        f"Current next reconstruction target: {grd.next_target(ROWS)}":
        "Current next reconstruction target: 3b"})
    problems = grd.check_freshness(ROWS, 3564, 83, stale_target_doc)
    check("12. stale next target is detected",
          any("next target" in p for p in problems), str(problems))

    stale_status_rows = [r if r[0] != "41b" else ("41b", 74, 74, "100%", "rashi-reconstruction", "resolved", "abc")
                         for r in ROWS]
    stale_status_doc = doc_with(table_rows=stale_status_rows)
    problems = grd.check_freshness(ROWS, 3564, 83, stale_status_doc)
    check("13. stale per-daf status (resolved-but-live-open) is detected",
          any("41b" in p and "status" in p for p in problems), str(problems))

    stale_contam_rows = [r if r[0] != "15a" else ("15a", 40, 66, "61%", "rashi-narration-repair", "open", "abc")
                         for r in ROWS]
    stale_contam_doc = doc_with(table_rows=stale_contam_rows)
    problems = grd.check_freshness(ROWS, 3564, 83, stale_contam_doc)
    check("14. stale per-daf contaminated count is detected",
          any("15a" in p and "contaminated" in p for p in problems), str(problems))

    check("15. HEAD-hash-only differences do NOT count as staleness",
          not grd.check_freshness(ROWS, 3564, 83,
                                   doc_with().replace("abc1234", "def5678")))
finally:
    grd.VERSION_FILE = old_version_file

if FAILED:
    print(f"\nFAILED: {len(FAILED)} test(s): {FAILED}")
    sys.exit(1)
print("\nOK: all generate_rashi_docs tests passed.")
