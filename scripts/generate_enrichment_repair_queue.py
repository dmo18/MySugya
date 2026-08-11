#!/usr/bin/env python3
"""generate_enrichment_repair_queue.py - derive the durable repair queue from
the merged Yoma tail-enrichment audit, and manage its separate, mutable
progress-tracking file.

The merged audit is historical evidence and is NEVER rewritten. This tool
projects it into a separate, actionable queue that records the superseding
contract decisions, the migration prerequisites, and the task type that owns
each repair. The QUEUE itself is an IMMUTABLE derived definition: its
records, order, and "status": "NOT_STARTED" placeholder never change once
generated except by re-deriving from the audit (which is itself frozen), so
regenerating the queue is always a no-op unless the audit changes.

Actual repair progress -- which is genuinely mutable, advances PR by PR --
lives in a SEPARATE file, docs/reports/data/yoma-tail-enrichment-repair-
progress.json, keyed by sugyaId. This script both derives/checks the queue
and initializes/checks the progress file (--check validates both).

Run from repo root:
  python3 scripts/generate_enrichment_repair_queue.py            # write queue + progress skeleton
  python3 scripts/generate_enrichment_repair_queue.py --check    # verify both, in place
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
PROGRESS = ROOT / "docs/reports/data/yoma-tail-enrichment-repair-progress.json"
PROGRESS_SCHEMA_VERSION = 1

PRIORITY_HEAD = ["yoma-082b-s01", "yoma-087b-s03", "yoma-080a-s01", "yoma-080b-s03"]

# affectedFields entries that name the removed concepts field
CONCEPTS_PREFIX = "concepts."
# affectedFields entries handled by a migration rather than a semantic repair
MIGRATION_FIELDS = {"requiresUnderstanding": "requiresUnderstanding-prose-to-prerequisiteKnowledge",
                    "visualizableElements[].name": "visualizableElements-shape-normalization",
                    "difficulty": "difficulty-introductory-to-intro"}

# Supported progress statuses and their legal forward transitions. Self-
# transitions (a status "changing" to itself) are always legal no-ops.
# COMPLETE is terminal: nothing may leave it. Every other edge here is an
# intentional, reviewed part of the repair lifecycle; anything not listed
# (including any transition out of COMPLETE, or skipping backward to an
# earlier stage) is rejected as invalid/backward.
STATUSES = ("NOT_STARTED", "IN_PROGRESS", "FIXED_PENDING_REVIEW", "COMPLETE", "BLOCKED")
ALLOWED_TRANSITIONS = {
    "NOT_STARTED": {"IN_PROGRESS", "BLOCKED"},
    "IN_PROGRESS": {"FIXED_PENDING_REVIEW", "BLOCKED"},
    "FIXED_PENDING_REVIEW": {"COMPLETE", "IN_PROGRESS", "BLOCKED"},
    "BLOCKED": {"IN_PROGRESS"},
    "COMPLETE": set(),
}
for _s in STATUSES:
    ALLOWED_TRANSITIONS.setdefault(_s, set()).add(_s)  # a no-op is always legal

PROGRESS_RECORD_FIELDS = ("status", "prNumber", "repairCommit", "mergedCommit", "version",
                          "reviewer", "independentReviewResult", "blockerReason")


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
                 "this queue's records, order and NOT_STARTED status placeholder are themselves "
                 "IMMUTABLE (re-derived only from the frozen audit). Real repair progress lives "
                 "separately in docs/reports/data/yoma-tail-enrichment-repair-progress.json. "
                 "finalRuling exact-hint-copies are no longer contract-ambiguous: the finalRuling "
                 "contract decision supersedes that STRUCTURAL_OR_SCHEMA_DECISION and makes them "
                 "repairable defects."),
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


def empty_progress_record():
    return {f: (None if f != "status" else "NOT_STARTED") for f in PROGRESS_RECORD_FIELDS}


def build_progress(queue_ids, existing):
    """Merge: every queue id gets a progress record -- carried forward
    UNCHANGED from `existing` when present (this is what makes progress
    durable across queue regeneration), or a fresh NOT_STARTED skeleton
    when new. Ids in `existing` that are no longer in the queue are
    dropped (the queue only ever shrinks an id if the audit itself
    changed, which never happens in practice)."""
    out = {}
    for sid in queue_ids:
        out[sid] = dict(existing.get(sid, empty_progress_record()))
        for f in PROGRESS_RECORD_FIELDS:
            out[sid].setdefault(f, None if f != "status" else "NOT_STARTED")
    return {
        "schemaVersion": PROGRESS_SCHEMA_VERSION,
        "generatedFrom": "docs/reports/data/yoma-tail-enrichment-repair-queue.json",
        "note": ("Mutable repair-progress tracking, keyed by sugyaId. This file, NOT the queue "
                 "file, is where a semantic repair PR records its own advancing status. Status "
                 "transitions are validated against ALLOWED_TRANSITIONS in this script; COMPLETE "
                 "is terminal."),
        "progress": out,
    }


def check_progress_transitions(before, after, queue_ids):
    """Compare a before/after progress payload (each the full {"progress":
    {sugyaId: record}} dict, or None if the file did not exist at `before`)
    and return a list of problem strings. Empty list = every change is a
    legal, forward transition; unknown ids are rejected; duplicate ids are
    structurally impossible in a dict so that check is covered by the
    caller's own JSON-shape validation instead."""
    problems = []
    before_p = (before or {}).get("progress", {})
    after_p = (after or {}).get("progress", {})
    queue_set = set(queue_ids)

    unknown = set(after_p) - queue_set
    if unknown:
        problems.append("progress file references unknown sugyaId(s) not in the queue: %s"
                        % sorted(unknown)[:10])

    for sid, rec in after_p.items():
        status = rec.get("status")
        if status not in STATUSES:
            problems.append("%s: unsupported status %r (legal: %s)" % (sid, status, STATUSES))
            continue
        was = before_p.get(sid, {}).get("status", "NOT_STARTED")
        if was not in STATUSES:
            was = "NOT_STARTED"
        if status not in ALLOWED_TRANSITIONS.get(was, set()):
            problems.append("%s: illegal status transition %s -> %s (backward or skipped; "
                            "legal from %s: %s)" % (sid, was, status, was,
                                                    sorted(ALLOWED_TRANSITIONS.get(was, set()))))
    return problems


def _git_show(rel_path, ref="HEAD"):
    r = subprocess.run(["git", "show", "%s:%s" % (ref, rel_path)], cwd=str(ROOT),
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--base", default="HEAD",
                    help="git ref to diff the progress file's status transitions against "
                         "(default HEAD; a worker PR's verify step compares against its base)")
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
        print("OK: committed queue matches the audit (immutable fields verified).")

        if not PROGRESS.exists():
            sys.exit("progress file missing; run generate_enrichment_repair_queue.py to "
                     "initialize it")
        current = json.loads(PROGRESS.read_text(encoding="utf-8"))
        prog_problems = []
        if set(current.get("progress", {})) - set(ids):
            prog_problems.append("progress file references unknown sugyaId(s): %s"
                                 % sorted(set(current.get("progress", {})) - set(ids))[:10])
        for sid, rec in current.get("progress", {}).items():
            for f in PROGRESS_RECORD_FIELDS:
                if f not in rec:
                    prog_problems.append("%s: progress record missing field %r" % (sid, f))
        before = _git_show(str(PROGRESS.relative_to(ROOT)), args.base)
        prog_problems += check_progress_transitions(before, current, ids)
        # Preserve valid progress: every id the PREVIOUS committed file
        # tracked with a real (non-NOT_STARTED) status must still be
        # present, at that status or a legally-advanced one -- regeneration
        # (or any other diff) may never silently drop or reset progress.
        if before:
            for sid, rec in before.get("progress", {}).items():
                if rec.get("status") not in (None, "NOT_STARTED") and sid not in current.get("progress", {}):
                    prog_problems.append("%s: progress record disappeared (was %r)"
                                         % (sid, rec.get("status")))
        if prog_problems:
            print("\nprogress-file check FAILED:")
            for p in prog_problems:
                print("  FAIL %s" % p)
            sys.exit(1)
        print("OK: progress file is internally consistent and every transition since %s is "
              "legal." % args.base)
        return

    existing_progress = json.loads(PROGRESS.read_text(encoding="utf-8")).get("progress", {}) \
        if PROGRESS.exists() else {}
    QUEUE.write_text(json.dumps(q, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("wrote %s" % QUEUE.relative_to(ROOT))
    progress_doc = build_progress(ids, existing_progress)
    PROGRESS.write_text(json.dumps(progress_doc, ensure_ascii=False, indent=1) + "\n",
                        encoding="utf-8")
    print("wrote %s (%d progress record(s), existing progress preserved)"
          % (PROGRESS.relative_to(ROOT), len(progress_doc["progress"])))


if __name__ == "__main__":
    main()
