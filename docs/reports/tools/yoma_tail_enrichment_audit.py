#!/usr/bin/env python3
"""yoma_tail_enrichment_audit.py - audit-only, read-only mechanical inventory
for the Yoma 77a-88a tail-enrichment audit.

Deterministically reproduces cohort membership, control membership, the
finalRuling-from-hint detection and its exact-copy / truncated-prefix split,
149-150 character counts, trailing-ellipsis candidates, uniqueness and
coverage checks, and the aggregate totals derived from the committed JSON
records. It also cross-checks the Markdown report's stated aggregates.

It NEVER assigns or changes a semantic disposition: semantic verdicts are
human/model judgements recorded in the JSON and are only read here.

Usage (from repo root):
  python3 docs/reports/tools/yoma_tail_enrichment_audit.py            # report
  python3 docs/reports/tools/yoma_tail_enrichment_audit.py --check    # gate
"""
import json, re, sys, argparse, collections, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
LEARNING = ROOT / "modules/yoma/learning_data.js"
JSON_REPORT = ROOT / "docs/reports/data/yoma-tail-enrichment-audit.json"
MD_REPORT = ROOT / "docs/reports/yoma-tail-enrichment-audit.md"

COHORT_START = (77, 0)          # 77a
CONTROL1_RANGE = ((73, 1), (77, 0))   # 73b inclusive .. 77a exclusive


def daf_key(d):
    return (int(d[:-1]), 0 if d[-1] == "a" else 1)


NODE_EVAL = r"""
const fs = require('fs'), vm = require('vm');
const src = fs.readFileSync(process.argv[2], 'utf8');
const ctx = {};
vm.createContext(ctx);
vm.runInContext(src + "\n;globalThis.__C = DAF_CONTENT;", ctx, { timeout: 180000 });
process.stdout.write(JSON.stringify(ctx.__C));
"""


def load_corpus():
    """Evaluate the generated learning_data.js with node and return DAF_CONTENT.

    Node is used rather than a hand-rolled JS parser so the tool reads exactly
    what the application reads. Read-only: nothing in the repo is written.
    """
    import subprocess, tempfile, os
    fd, path = tempfile.mkstemp(suffix=".cjs")
    try:
        os.write(fd, NODE_EVAL.encode())
        os.close(fd)
        r = subprocess.run(["node", path, str(LEARNING)], capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit("failed to evaluate learning_data.js: " + r.stderr[-400:])
        return json.loads(r.stdout)
    finally:
        os.unlink(path)


def mechanical_inventory(dc):
    rows = []
    for daf in sorted(dc, key=daf_key):
        for s in dc[daf]["sugyot"]:
            k = daf_key(daf)
            if k >= COHORT_START:
                role = "PRIMARY_COHORT_77a_88a"
            elif CONTROL1_RANGE[0] <= k < CONTROL1_RANGE[1]:
                role = "CONTROL_73b_76b"
            else:
                role = "OUT_OF_SCOPE"
            fr = s.get("finalRuling")
            frs = fr.strip() if isinstance(fr, str) else ""
            hint = ((s.get("display") or {}).get("hint") or "").strip()
            flags = []
            if frs and hint:
                if frs == hint:
                    flags.append("FR_EXACT_COPY_OF_HINT")
                elif hint.startswith(frs) and len(frs) >= 30:
                    flags.append("FR_TRUNCATED_PREFIX_OF_HINT")
            if len(frs) in (149, 150):
                flags.append("FR_150_CUTOFF")
            if hint.endswith(("...", "…")):
                flags.append("HINT_TRAILING_ELLIPSIS")
            if fr is not None and not isinstance(fr, str):
                flags.append("FR_MALFORMED_TYPE")
            rows.append({"daf": daf, "sugyaId": s["id"], "role": role, "flags": flags})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="exit non-zero if the committed JSON/Markdown aggregates drift")
    args = ap.parse_args()

    dc = load_corpus()
    rows = mechanical_inventory(dc)
    report = json.loads(JSON_REPORT.read_text(encoding="utf-8"))
    recs = report["records"]
    md = MD_REPORT.read_text(encoding="utf-8")

    problems = []

    cohort_all = [r for r in rows if r["role"] == "PRIMARY_COHORT_77a_88a"]
    ctrl1_all = [r for r in rows if r["role"] == "CONTROL_73b_76b"]

    mech = collections.Counter()
    for r in rows:
        for f in r["flags"]:
            mech[f] += 1
    mech_cohort = collections.Counter()
    for r in cohort_all:
        for f in r["flags"]:
            mech_cohort[f] += 1

    print("== mechanical inventory (recomputed from learning_data.js) ==")
    print("  cohort 77a-88a sugyot        : %d" % len(cohort_all))
    print("  control 73b-76b sugyot       : %d" % len(ctrl1_all))
    for k in sorted(mech):
        print("  %-30s corpus=%-4d cohort=%d" % (k, mech[k], mech_cohort.get(k, 0)))
    sig = mech_cohort.get("FR_EXACT_COPY_OF_HINT", 0) + mech_cohort.get("FR_TRUNCATED_PREFIX_OF_HINT", 0)
    outside = (mech.get("FR_EXACT_COPY_OF_HINT", 0) + mech.get("FR_TRUNCATED_PREFIX_OF_HINT", 0)) - sig
    print("  finalRuling-from-hint signature: cohort=%d outside-cohort=%d" % (sig, outside))
    if outside != 0:
        problems.append("finalRuling-from-hint signature found outside 77a-88a (%d)" % outside)

    # coverage + uniqueness of committed records
    ids = [r["sugyaId"] for r in recs]
    print("\n== committed record set ==")
    print("  records: %d  unique ids: %d" % (len(ids), len(set(ids))))
    if len(ids) != len(set(ids)):
        problems.append("duplicate sugyaId in committed records")
    if len(ids) != report["totals"]["reviewed"]:
        problems.append("totals.reviewed does not equal record count")
    cohort_ids = {r["sugyaId"] for r in cohort_all}
    covered = {r["sugyaId"] for r in recs if r["role"] == "PRIMARY_COHORT_77a_88a"}
    if cohort_ids != covered:
        problems.append("cohort coverage mismatch: %d missing, %d extra"
                        % (len(cohort_ids - covered), len(covered - cohort_ids)))
    ctrl_ids = {r["sugyaId"] for r in ctrl1_all}
    covered1 = {r["sugyaId"] for r in recs if r["role"] == "CONTROL_73b_76b"}
    if ctrl_ids != covered1:
        problems.append("73b-76b control coverage mismatch")

    # aggregates derived from records must equal the stored totals
    for key, field in (("bySemanticDisposition", "semanticDisposition"),
                       ("byMechanicalDisposition", "mechanicalDisposition"),
                       ("byOverallDisposition", "overallDisposition")):
        derived = dict(collections.Counter(r[field] for r in recs))
        if derived != report["totals"][key]:
            problems.append("totals.%s drifted: stored=%s derived=%s"
                            % (key, report["totals"][key], derived))

    # per-record mechanical flags must match the recomputed inventory
    byid = {r["sugyaId"]: r for r in rows}
    drift = [r["sugyaId"] for r in recs
             if r["sugyaId"] in byid and sorted(r["mechanicalFlags"]) != sorted(byid[r["sugyaId"]]["flags"])]
    if drift:
        problems.append("mechanicalFlags drift on %d record(s): %s" % (len(drift), drift[:5]))

    # no unregistered task type may remain
    registry = set(json.loads((ROOT / "scripts/worker_task_types.json").read_text())["taskTypes"])
    allowed = registry | {"TASK_TYPE_DECISION_REQUIRED"}
    bad = sorted({t for r in recs for t in r["recommendedLaterTaskType"]} - allowed)
    if bad:
        problems.append("unregistered task type(s): %s" % bad)
    print("  task types used: %s" % sorted({t for r in recs for t in r["recommendedLaterTaskType"]}))

    # truncation rule: nothing truncated may be overall VERIFIED
    viol = [r["sugyaId"] for r in recs
            if "FR_TRUNCATED_PREFIX_OF_HINT" in r["mechanicalFlags"] and r["overallDisposition"] == "VERIFIED"]
    if viol:
        problems.append("truncated finalRuling marked overall VERIFIED: %s" % viol[:5])

    # second-pass completeness
    missing_sp = [r["sugyaId"] for r in recs
                  if r["semanticDisposition"] != "VERIFIED"
                  and not (r["secondPass"].get("sourceFactIndependentlyRecovered") or "").strip()]
    if missing_sp:
        problems.append("missing second-pass source fact: %s" % missing_sp[:5])
    facts = [r["secondPass"].get("sourceFactIndependentlyRecovered") for r in recs
             if r["secondPass"].get("sourceFactIndependentlyRecovered")]
    if facts and len(set(facts)) != len(facts):
        problems.append("second-pass evidence is not record-specific (duplicated text)")
    print("  second-pass records: %d, distinct evidence strings: %d" % (len(facts), len(set(facts))))

    # Markdown / JSON aggregate cross-check
    for label, n in (("VERIFIED", report["totals"]["byOverallDisposition"].get("VERIFIED", 0)),
                     ("SUBSTANTIVE_REPAIR_NEEDED", report["totals"]["byOverallDisposition"].get("SUBSTANTIVE_REPAIR_NEEDED", 0))):
        if ("| %s | %d |" % (label, n)) not in md:
            problems.append("Markdown overall total for %s does not match JSON (%d)" % (label, n))
    if ("%d" % len(cohort_all)) not in md:
        problems.append("Markdown does not state the cohort size %d" % len(cohort_all))
    for stale in ("84 cohort", "enrichment-repair"):
        if stale in md:
            problems.append("stale string present in Markdown: %r" % stale)

    print("\n== result ==")
    if problems:
        for p in problems:
            print("  FAIL " + p)
        if args.check:
            sys.exit(1)
        print("  (%d problem(s); run with --check to gate)" % len(problems))
    else:
        print("  OK: mechanical inventory, coverage, aggregates, task types and Markdown all reconcile.")


if __name__ == "__main__":
    main()
