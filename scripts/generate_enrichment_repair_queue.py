#!/usr/bin/env python3
"""generate_enrichment_repair_queue.py - derive the durable repair queue from
the merged Yoma tail-enrichment audit.

The merged audit is historical evidence and is NEVER rewritten. This tool
projects it into a separate, actionable queue that records the superseding
contract decisions, the migration prerequisites, and the task type that owns
each repair.

Run from repo root:
  python3 scripts/generate_enrichment_repair_queue.py            # write
  python3 scripts/generate_enrichment_repair_queue.py --check    # verify only
"""
import argparse
import collections
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
AUDIT = ROOT / "docs/reports/data/yoma-tail-enrichment-audit.json"
QUEUE = ROOT / "docs/reports/data/yoma-tail-enrichment-repair-queue.json"

PRIORITY_HEAD = ["yoma-082b-s01", "yoma-087b-s03", "yoma-080a-s01", "yoma-080b-s03"]

# affectedFields entries that name the removed concepts field
CONCEPTS_PREFIX = "concepts."
# affectedFields entries handled by a migration rather than a semantic repair
MIGRATION_FIELDS = {"requiresUnderstanding": "requiresUnderstanding-prose-to-prerequisiteKnowledge",
                    "visualizableElements[].name": "visualizableElements-shape-normalization",
                    "difficulty": "difficulty-introductory-to-intro"}


def audit_sha():
    r = subprocess.run(["git", "log", "-1", "--format=%H", "--", str(AUDIT.relative_to(ROOT))],
                       cwd=str(ROOT), capture_output=True, text=True)
    return (r.stdout or "").strip() or None


def daf_key(d):
    return (int(d[:-1]), 0 if d[-1] == "a" else 1)


def build():
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    recs = audit["records"]
    out = []
    for r in recs:
        sem = r["semanticDisposition"]
        mech = r["mechanicalDisposition"]
        overall = r["overallDisposition"]
        if overall == "VERIFIED":
            continue  # nothing later work depends on
        fields = r["affectedFields"]
        active = [f for f in fields if not f.startswith(CONCEPTS_PREFIX)]
        concepts = sorted(f for f in fields if f.startswith(CONCEPTS_PREFIX))
        migrations = sorted({MIGRATION_FIELDS[f] for f in fields if f in MIGRATION_FIELDS})
        resolved = []
        for d in r.get("prerequisiteContractDecisions", []):
            resolved.append({"decision": d["decision"], "status": "RESOLVED",
                             "resolvedBy": "docs/reports/yoma-enrichment-contract-decision.md"})
        # required task type
        if sem in ("SUBSTANTIVE_REPAIR_NEEDED", "MINOR_EDIT_NEEDED"):
            task = "audited-sugya-enrichment-repair"
        elif mech in ("MINOR_EDIT_NEEDED", "STRUCTURAL_OR_SCHEMA_DECISION"):
            task = "audited-sugya-enrichment-repair"
        else:
            task = "audited-sugya-enrichment-repair"
        out.append({
            "daf": r["daf"],
            "sugyaId": r["sugyaId"],
            "semanticDisposition": sem,
            "mechanicalDisposition": mech,
            "currentOverallDisposition": overall,
            "affectedActiveFields": active,
            "removedConceptsFieldScheduledForPurge": bool(concepts),
            "removedConceptsPaths": concepts,
            "prerequisiteContractDecisionsResolved": resolved,
            "migrationPrerequisites": migrations,
            "requiredRepairTaskType": task,
            "independentReviewRequired": True,
            "status": "NOT_STARTED",
            "auditSourceSha": audit["auditedSha"],
            "auditEvidenceSummary": (r["firstPassEvidence"][:180].rstrip() + "...")
            if len(r["firstPassEvidence"]) > 180 else r["firstPassEvidence"],
        })

    TIER = {"SUBSTANTIVE_REPAIR_NEEDED": 1, "MINOR_EDIT_NEEDED": 2}

    def rank(rec):
        """Named-first, then substantive by daf, then minor, then mechanical-only."""
        sid = rec["sugyaId"]
        if sid in PRIORITY_HEAD:
            return (0, PRIORITY_HEAD.index(sid), 0, "")
        tier = TIER.get(rec["semanticDisposition"], 3)
        n, side = daf_key(rec["daf"])
        return (tier, n, side, sid)

    out.sort(key=rank)
    for i, rec in enumerate(out, 1):
        rec["queuePosition"] = i

    counts = collections.Counter(r["semanticDisposition"] for r in out)
    mech_counts = collections.Counter(r["mechanicalDisposition"] for r in out)
    return {
        "schemaVersion": 1,
        "generatedFrom": "docs/reports/data/yoma-tail-enrichment-audit.json",
        "auditSourceSha": audit["auditedSha"],
        "auditArtifactCommit": audit_sha(),
        "note": ("Derived queue. The merged audit is historical evidence and is never rewritten; "
                 "progress is tracked here. finalRuling exact-hint-copies are no longer "
                 "contract-ambiguous: the finalRuling contract decision supersedes that "
                 "STRUCTURAL_OR_SCHEMA_DECISION and makes them repairable defects."),
        "orderingPolicy": [
            "1. prerequisite contract/tooling and migrations (not queue rows)",
            "2. yoma-082b-s01", "3. yoma-087b-s03", "4. yoma-080a-s01", "5. yoma-080b-s03",
            "6. remaining substantive records in daf order",
            "7. minor semantic records",
            "8. parent daf summaries after all sugyot on each daf are settled",
            "9. finalRuling-only mechanical repairs after each underlying hint is confirmed",
        ],
        "totals": {
            "queued": len(out),
            "bySemanticDisposition": dict(counts),
            "byMechanicalDisposition": dict(mech_counts),
            "withRemovedConceptsScheduledForPurge": sum(
                1 for r in out if r["removedConceptsFieldScheduledForPurge"]),
            "withMigrationPrerequisites": sum(1 for r in out if r["migrationPrerequisites"]),
        },
        "records": out,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    q = build()
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))

    problems = []
    ids = [r["sugyaId"] for r in q["records"]]
    if len(ids) != len(set(ids)):
        problems.append("duplicate sugyaId in queue")
    need = {r["sugyaId"] for r in audit["records"] if r["overallDisposition"] != "VERIFIED"}
    got = set(ids)
    if need != got:
        problems.append("coverage mismatch: missing %s extra %s"
                        % (sorted(need - got)[:5], sorted(got - need)[:5]))
    verified = {r["sugyaId"] for r in audit["records"] if r["overallDisposition"] == "VERIFIED"}
    if got & verified:
        problems.append("queue contains overall-VERIFIED records: %s" % sorted(got & verified)[:5])

    print("repair queue: %d record(s) from %d audit record(s)" % (len(ids), len(audit["records"])))
    print("  semantic  : %s" % q["totals"]["bySemanticDisposition"])
    print("  mechanical: %s" % q["totals"]["byMechanicalDisposition"])
    print("  concepts purge scheduled: %d | migration prerequisites: %d"
          % (q["totals"]["withRemovedConceptsScheduledForPurge"],
             q["totals"]["withMigrationPrerequisites"]))
    print("  every non-VERIFIED audit record appears exactly once: %s" % (need == got and len(ids) == len(set(ids))))

    if problems:
        for p in problems:
            print("  FAIL %s" % p)
        sys.exit(1)
    if args.check:
        if not QUEUE.exists():
            sys.exit("queue file missing")
        if json.loads(QUEUE.read_text(encoding="utf-8"))["records"] != q["records"]:
            sys.exit("committed queue is stale; regenerate with generate_enrichment_repair_queue.py")
        print("OK: committed queue matches the audit.")
        return
    QUEUE.write_text(json.dumps(q, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("wrote %s" % QUEUE.relative_to(ROOT))


if __name__ == "__main__":
    main()
