#!/usr/bin/env python3
"""test_yoma_tail_enrichment_audit_compat.py - proves the historical audit
checker's registry-growth tolerance is exactly what it claims to be:
later task-registry growth (legacy-concepts-purge, enrichment-schema-
migration, audited-sugya-enrichment-repair, and anything added after them)
never retroactively invalidates the merged, frozen historical record, while
a genuinely false ownership claim still fails regardless of when it was
made. Exercises the REAL functions in docs/reports/tools/
yoma_tail_enrichment_audit.py against the real committed audit and a small
number of controlled synthetic records -- never a duplicate reimplementation
of check_ownership's logic.

Run from repo root:
  python3 scripts/test_yoma_tail_enrichment_audit_compat.py
"""
import copy
import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
AUDIT_TOOL = ROOT / "docs/reports/tools/yoma_tail_enrichment_audit.py"

spec = importlib.util.spec_from_file_location("yoma_tail_enrichment_audit", AUDIT_TOOL)
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)

FAILED = []


def check(name, cond, detail=""):
    print("  %s %s%s" % ("ok  " if cond else "FAIL", name, "" if cond else " (%s)" % str(detail)[:500]))
    if not cond:
        FAILED.append(name)


# ---- 1. historical artifacts are byte-identical to git HEAD -----------------
import subprocess  # noqa: E402
for rel in ("docs/reports/data/yoma-tail-enrichment-audit.json",
           "docs/reports/yoma-tail-enrichment-audit.md"):
    r = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", rel], cwd=str(ROOT))
    check("1. %s is byte-identical to HEAD (never rewritten)" % rel, r.returncode == 0)

# ---- 2. the real registry + real merged audit reconcile with zero problems -
reg = A.load_registry()
real_audit = json.loads((ROOT / "docs/reports/data/yoma-tail-enrichment-audit.json")
                        .read_text(encoding="utf-8"))
problems = []
A.self_test(reg, problems)
check("2a. ownership resolver self-test passes against the real, current registry",
      problems == [], problems)
problems = []
A.check_ownership(real_audit["records"], reg, problems)
check("2b. every real merged audit record reconciles against the real, current registry",
      problems == [], problems[:5])

# ---- 3. registry growth is tolerated: a brand-new task type that owns an --
#         audited path, and is NOT recorded in registeredTaskOwners, must
#         NOT be reported as a problem (this is exactly what
#         AUDIT_ERA_TASK_TYPES gates).
grown_reg = copy.deepcopy(reg)
grown_reg["a-brand-new-future-task-type"] = {
    "jsonScope": {"mutable": ["sugyot[*].display.hint"], "flagMutable": {}},
}
problems = []
A.check_ownership(real_audit["records"], grown_reg, problems)
check("3. a new task type owning an audited path, absent from registeredTaskOwners, "
     "is NOT flagged (registry growth does not retroactively invalidate history)",
      problems == [], problems[:5])

# ---- 4. a FALSE ownership claim still fails, even after registry growth ----
sample = copy.deepcopy(real_audit["records"][0])
sample["registeredTaskOwners"] = list(sample.get("registeredTaskOwners", [])) + [
    {"taskType": "a-task-type-that-owns-nothing-here", "ownedPaths": [], "coverage": "mutable"}
]
grown_reg2 = copy.deepcopy(reg)
grown_reg2["a-task-type-that-owns-nothing-here"] = {
    "jsonScope": {"mutable": ["sugyot[*].nonexistentPathNeverAudited"], "flagMutable": {}},
}
problems = []
A.check_ownership([sample], grown_reg2, problems)
check("4a. a recorded owner that owns none of the record's affected paths still FAILS",
      any("owns none of its affectedFields" in p for p in problems), problems)

sample2 = copy.deepcopy(real_audit["records"][0])
real_field = sample2["affectedFields"][0]
sample2["unownedPaths"] = list(sample2.get("unownedPaths", [])) + [real_field]
problems = []
A.check_ownership([sample2], reg, problems)
check("4b. falsely declaring an ACTUALLY-owned path as unowned still FAILS",
      any("is declared unowned but" in p for p in problems), problems)

# ---- 5. dispositions are read-only: check_ownership never mutates records --
before = json.loads((ROOT / "docs/reports/data/yoma-tail-enrichment-audit.json")
                    .read_text(encoding="utf-8"))
snapshot = copy.deepcopy(before["records"])
problems = []
A.check_ownership(before["records"], reg, problems)
check("5. check_ownership does not mutate the records it inspects",
      before["records"] == snapshot)

if FAILED:
    print("\n%d check(s) failed: %s" % (len(FAILED), FAILED))
    sys.exit(1)
print("\nAll historical audit compatibility checks passed.")
