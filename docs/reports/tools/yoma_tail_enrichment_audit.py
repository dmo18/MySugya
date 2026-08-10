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


# ---------------------------------------------------------------- ownership
REGISTRY = ROOT / "scripts/worker_task_types.json"


def load_registry():
    return json.loads(REGISTRY.read_text(encoding="utf-8"))["taskTypes"]


def normalize_path(field):
    """Map an affectedFields entry onto a registry-style JSON path."""
    f = field
    if f in ("<daf>.summary", "summary"):
        return "summary"
    if f.startswith("sugyot[*]."):
        return f
    f = f.replace("[]", "[*]")
    for bare in ("topicTags", "requiresUnderstanding", "visualizableElements",
                 "misconceptions", "quizSeeds", "relatedSugyot", "conceptRefs"):
        if f == bare:
            f = bare + "[*]"
    if f.startswith("visualizableElements[*]."):
        f = "visualizableElements[*]"
    if f.startswith("argumentFlow"):
        f = "argumentFlow[*]"
    return "sugyot[*]." + f


def path_matches(owner_path, target):
    """True when the registry path and the target refer to the same data."""
    if owner_path == target:
        return True
    for a, b in ((owner_path, target), (target, owner_path)):
        if b.startswith(a + ".") or b.startswith(a + "["):
            return True
        if a.endswith("[*]"):
            stem = a[:-3]
            if b.startswith(stem) and (b == stem or b[len(stem):].startswith((".", "[*]"))):
                return True
    return False


def owners_for(target, reg):
    """Return [(taskType, 'mutable'|'flagMutable', authorization|None)]."""
    out = []
    for name, d in reg.items():
        if d.get("paused"):
            continue
        js = d.get("jsonScope") or {}
        hit = None
        for p in js.get("mutable") or []:
            if path_matches(p, target):
                hit = (name, "mutable", None)
                break
        if hit is None:
            for flag, paths in (js.get("flagMutable") or {}).items():
                if any(path_matches(p, target) for p in paths):
                    hit = (name, "flagMutable", flag)
                    break
        if hit:
            out.append(hit)
    return out


def single_type_covers(reg, targets):
    for name, d in reg.items():
        if d.get("paused"):
            continue
        js = d.get("jsonScope") or {}
        owned = list(js.get("mutable") or [])
        for _f, ps in (js.get("flagMutable") or {}).items():
            owned += list(ps)
        if targets and all(any(path_matches(o, t) for o in owned) for t in targets):
            return name
    return None


def check_ownership(recs, reg, problems):
    """Prove every affected path is either owned by a recorded task type or
    explicitly listed in unownedPaths."""
    for r in recs:
        rec_owners = {o["taskType"] for o in r.get("registeredTaskOwners", [])}
        declared_unowned = set(r.get("unownedPaths", []))
        derived_owners = set()
        for f in r["affectedFields"]:
            tgt = normalize_path(f)
            os_ = owners_for(tgt, reg)
            if not os_:
                if f not in declared_unowned:
                    problems.append("%s: path %r has no registry owner but is not in unownedPaths"
                                    % (r["sugyaId"], f))
                continue
            if f in declared_unowned:
                problems.append("%s: path %r is declared unowned but %s owns it"
                                % (r["sugyaId"], f, sorted(n for n, _k, _a in os_)))
            derived_owners |= {n for n, _k, _a in os_}
        # every recorded owner must actually follow from the affected fields
        for name in rec_owners - derived_owners:
            problems.append("%s: registeredTaskOwners lists %r which owns none of its affectedFields"
                            % (r["sugyaId"], name))
        for name in derived_owners - rec_owners:
            problems.append("%s: %r owns an affected path but is missing from registeredTaskOwners"
                            % (r["sugyaId"], name))
        # required optional authorizations must be recorded
        for o in r.get("registeredTaskOwners", []):
            d = reg.get(o["taskType"], {})
            need = set()
            if o.get("coverage") == "flagMutable" and o.get("requiredAuthorizations"):
                need |= set(o["requiredAuthorizations"])
            if d.get("structurePolicy") == "requires-authorization" and o["taskType"] == "structural-repair":
                need.add("allowStructure")
            missing = need - set(o.get("requiredAuthorizations") or [])
            if missing:
                problems.append("%s: %s omits required authorization %s"
                                % (r["sugyaId"], o["taskType"], sorted(missing)))
            for a in o.get("requiredAuthorizations") or []:
                if a not in (d.get("optionalAuthorizations") or []) + (d.get("requiredAuthorizations") or []):
                    problems.append("%s: %s records authorization %r that the registry does not define"
                                    % (r["sugyaId"], o["taskType"], a))
        # atomicity must follow from ownership
        owned_targets = [normalize_path(f) for f in r["affectedFields"] if f not in declared_unowned]
        covering = single_type_covers(reg, owned_targets) if owned_targets else None
        expected_atomic = bool(declared_unowned) or (bool(r["affectedFields"]) and covering is None)
        if bool(r.get("atomicRepairDecisionRequired")) != expected_atomic:
            problems.append("%s: atomicRepairDecisionRequired=%s but ownership implies %s"
                            % (r["sugyaId"], r.get("atomicRepairDecisionRequired"), expected_atomic))
        marker = r.get("derivedSummaryMarker")
        if marker == "TASK_TYPE_DECISION_REQUIRED" and not expected_atomic:
            problems.append("%s: TASK_TYPE_DECISION_REQUIRED set without an unowned path or atomicity gap"
                            % r["sugyaId"])


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

    reg = load_registry()

    # every stored aggregate must equal the value derived from the records
    def derived_counter(field):
        return dict(collections.Counter(r[field] for r in recs))

    for key, field in (("bySemanticDisposition", "semanticDisposition"),
                       ("byMechanicalDisposition", "mechanicalDisposition"),
                       ("byOverallDisposition", "overallDisposition")):
        if derived_counter(field) != report["totals"].get(key):
            problems.append("totals.%s drifted: stored=%s derived=%s"
                            % (key, report["totals"].get(key), derived_counter(field)))

    tag = collections.Counter()
    for r in recs:
        for x in r["defectTags"]:
            tag[x] += 1
    if dict(tag) != report["totals"].get("byDefectTag"):
        problems.append("totals.byDefectTag drifted")

    mf = collections.Counter()
    for r in recs:
        for x in r["mechanicalFlags"]:
            mf[x] += 1
    if dict(mf) != report["totals"].get("byMechanicalFlag"):
        problems.append("totals.byMechanicalFlag drifted: stored=%s derived=%s"
                        % (report["totals"].get("byMechanicalFlag"), dict(mf)))

    owner_ct = collections.Counter()
    auth_ct = collections.Counter()
    unowned_inv = collections.Counter()
    n_prereq = n_unowned = n_atomic = 0
    for r in recs:
        for o in r.get("registeredTaskOwners", []):
            owner_ct[o["taskType"]] += 1
            for a in o.get("requiredAuthorizations") or []:
                auth_ct[a] += 1
        for u in r.get("unownedPaths", []):
            unowned_inv[normalize_path(u)] += 1
        if r.get("prerequisiteContractDecisions"):
            n_prereq += 1
        if r.get("unownedPaths"):
            n_unowned += 1
        if r.get("atomicRepairDecisionRequired"):
            n_atomic += 1
    for key, derived in (("byRegisteredTaskOwner", dict(owner_ct)),
                         ("requiredAuthorizationsAcrossRecords", dict(auth_ct)),
                         ("unownedPathInventory", dict(unowned_inv)),
                         ("recordsWithPrerequisiteContractDecisions", n_prereq),
                         ("recordsWithUnownedPaths", n_unowned),
                         ("recordsRequiringAtomicTaskDecision", n_atomic)):
        if report["totals"].get(key) != derived:
            problems.append("totals.%s drifted: stored=%s derived=%s"
                            % (key, report["totals"].get(key), derived))

    if "byRecommendedTaskType" in report["totals"]:
        problems.append("totals.byRecommendedTaskType is ambiguous and must be removed or redefined")

    expanded = report["totals"].get("affectedFieldListsExpanded")
    if not isinstance(expanded, int) or expanded < 0 or expanded > len(recs):
        problems.append("totals.affectedFieldListsExpanded is not a plausible record count")

    for key, want in (("primaryCohort", len(cohort_all)),
                      ("controls", len(recs) - len(cohort_all))):
        if report["totals"].get(key) != want:
            problems.append("totals.%s stored=%s expected=%d"
                            % (key, report["totals"].get(key), want))

    # per-record mechanical flags must match the recomputed inventory
    byid = {r["sugyaId"]: r for r in rows}
    drift = [r["sugyaId"] for r in recs
             if r["sugyaId"] in byid and sorted(r["mechanicalFlags"]) != sorted(byid[r["sugyaId"]]["flags"])]
    if drift:
        problems.append("mechanicalFlags drift on %d record(s): %s" % (len(drift), drift[:5]))

    # real path ownership, authorizations and atomicity
    check_ownership(recs, reg, problems)
    print("  registered task owners: %s" % dict(owner_ct))
    print("  unowned paths: %s" % sorted(unowned_inv))
    print("  prerequisite-contract records=%d unowned records=%d atomic-decision records=%d"
          % (n_prereq, n_unowned, n_atomic))

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

    # ---- Markdown must carry every stored aggregate ----
    def md_needs(text, label):
        if text not in md:
            problems.append("Markdown missing/stale: %s" % label)

    for table_key in ("bySemanticDisposition", "byMechanicalDisposition", "byOverallDisposition"):
        for k, v in report["totals"][table_key].items():
            if ("| %s | %d |" % (k, v)) not in md:
                problems.append("Markdown %s row for %s=%d not found" % (table_key, k, v))
    for k, v in report["totals"]["byDefectTag"].items():
        md_needs("| %s | %d |" % (k, v), "byDefectTag %s=%d" % (k, v))
    for k, v in report["totals"]["byMechanicalFlag"].items():
        md_needs("| %s | %d |" % (k, v), "byMechanicalFlag %s=%d" % (k, v))
    for k, v in report["totals"]["byRegisteredTaskOwner"].items():
        md_needs("| %s | %d |" % (k, v), "byRegisteredTaskOwner %s=%d" % (k, v))
    for label, v in (("recordsWithPrerequisiteContractDecisions", n_prereq),
                     ("recordsWithUnownedPaths", n_unowned),
                     ("recordsRequiringAtomicTaskDecision", n_atomic),
                     ("affectedFieldListsExpanded", expanded)):
        md_needs("**%d**" % v, "%s=%d stated in Markdown" % (label, v))
    md_needs("**%d**" % len(recs), "record count")
    md_needs("**%d**" % len(cohort_all), "cohort count")
    for stale in ("84 cohort", "enrichment-repair", "lack registered owners", "no registered type owns"):
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
