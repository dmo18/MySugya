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

# worker_pipeline.py is a sibling module in this same scripts/ directory and
# never imports this file (it only shells out to it via subprocess, see its
# own generate-repair-queue invocation), so importing it here for
# AUDIT_RECORD_TASK_TYPE carries no circular-import risk. The explicit
# sys.path insert mirrors worker_pipeline.py's own defensive pattern for
# callers that import this module without having already put scripts/ on
# the path themselves.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import worker_pipeline  # noqa: E402

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
#
# APPROVED_PENDING_MERGE is the explicit pre-merge "approved" checkpoint: an
# independent reviewer has signed off on FIXED_PENDING_REVIEW work, but the
# PR has not yet been squash-merged to main. This is what makes the one-PR
# lifecycle executable end to end: a single content-repair PR walks
# NOT_STARTED -> IN_PROGRESS -> FIXED_PENDING_REVIEW -> APPROVED_PENDING_MERGE
# entirely on its own branch (each transition committed and checked in
# sequence, see check_progress_history), and COMPLETE is then DERIVED after
# the squash merge (see derive_effective_status) rather than requiring a
# second, progress-only PR to hand-edit the file one more time. A record may
# still additionally be advanced to COMPLETE by a direct edit (e.g. by
# tooling that runs the derivation and persists its result); both paths are
# legal, but neither is required to reach effective completion.
STATUSES = ("NOT_STARTED", "IN_PROGRESS", "FIXED_PENDING_REVIEW", "APPROVED_PENDING_MERGE",
           "COMPLETE", "BLOCKED")
ALLOWED_TRANSITIONS = {
    "NOT_STARTED": {"IN_PROGRESS", "BLOCKED"},
    "IN_PROGRESS": {"FIXED_PENDING_REVIEW", "BLOCKED"},
    "FIXED_PENDING_REVIEW": {"APPROVED_PENDING_MERGE", "IN_PROGRESS", "BLOCKED"},
    "APPROVED_PENDING_MERGE": {"COMPLETE", "IN_PROGRESS", "BLOCKED"},
    "BLOCKED": {"IN_PROGRESS"},
    "COMPLETE": set(),
}
for _s in STATUSES:
    ALLOWED_TRANSITIONS.setdefault(_s, set()).add(_s)  # a no-op is always legal

# Statuses that certify an independent reviewer actually looked at the work;
# both require a non-empty reviewer and independentReviewResult on the
# record. FIXED_PENDING_REVIEW is deliberately excluded: it means review is
# PENDING, not that it happened.
REVIEW_BEARING_STATUSES = ("APPROVED_PENDING_MERGE", "COMPLETE")

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


def check_progress_field_requirements(after):
    """Per-record field requirements on the CURRENT (after) progress
    payload, independent of transition legality:

      - BLOCKED requires a non-empty blockerReason;
      - a review-bearing status (APPROVED_PENDING_MERGE, COMPLETE) requires
        a non-empty reviewer AND a non-empty independentReviewResult;
      - no progress record may carry a field outside PROGRESS_RECORD_FIELDS
        (an unknown field is exactly the kind of quiet metadata drift a
        record-scoped diff could otherwise smuggle through).

    Returns a list of problem strings (empty = compliant)."""
    problems = []
    allowed_keys = set(PROGRESS_RECORD_FIELDS)
    for sid, rec in after.items():
        extra = sorted(set(rec.keys()) - allowed_keys)
        if extra:
            problems.append("%s: progress record has unknown field(s) %s (legal fields: %s)"
                            % (sid, extra, sorted(allowed_keys)))
        status = rec.get("status")
        if status == "BLOCKED" and not str(rec.get("blockerReason") or "").strip():
            problems.append("%s: BLOCKED requires a non-empty blockerReason" % sid)
        if status in REVIEW_BEARING_STATUSES:
            if not str(rec.get("reviewer") or "").strip():
                problems.append("%s: %s requires a non-empty reviewer" % (sid, status))
            if not str(rec.get("independentReviewResult") or "").strip():
                problems.append("%s: %s requires a non-empty independentReviewResult"
                                % (sid, status))
    return problems


def check_progress_scope(before, after, allowed_ids):
    """RECORD-SPECIFIC progress scope: only sugyaIds in `allowed_ids` (a
    manifest's auditRecordIds) may have their progress record change at
    all between `before` and `after` -- every other record must be BYTE-
    IDENTICAL (dict equality, so this also catches an unnamed record
    quietly picking up an unknown field or a metadata value belonging to a
    different record). Returns a list of problem strings; allowed_ids=None
    disables the check entirely (used by the standalone --check path with
    no manifest in scope, e.g. after `generate_enrichment_repair_queue.py`
    itself regenerates the skeleton)."""
    if allowed_ids is None:
        return []
    problems = []
    allowed = set(allowed_ids)
    before_p = (before or {}).get("progress", {})
    after_p = (after or {}).get("progress", {})
    for sid in sorted(set(before_p) | set(after_p)):
        if before_p.get(sid) == after_p.get(sid):
            continue
        if sid not in allowed:
            problems.append("%s: progress record changed but is not in manifest.auditRecordIds "
                            "%s (progress edits are scoped to named records only; an unrelated "
                            "record may not be advanced, blocked, or have its metadata touched "
                            "in the same PR)" % (sid, sorted(allowed)))
    return problems


def check_progress_history(base_ref, head_ref, queue_ids, allowed_ids=None):
    """Validate every progress-file transition ACROSS THE FULL COMMIT
    HISTORY from base_ref to head_ref (git log --reverse base..head over
    the progress file), not merely the two endpoints. This is what makes
    NOT_STARTED -> IN_PROGRESS -> FIXED_PENDING_REVIEW -> ... legal within
    one PR: each individual commit-to-commit step is checked, so a branch
    that walked cleanly through every intermediate status is never
    rejected just because its two endpoints look like a "skip" when
    compared directly. Returns a list of problem strings, each prefixed
    with the offending commit for traceability."""
    r = subprocess.run(["git", "log", "--reverse", "--format=%H",
                        "%s..%s" % (base_ref, head_ref), "--", str(PROGRESS.relative_to(ROOT))],
                       cwd=str(ROOT), capture_output=True, text=True)
    commits = [c for c in r.stdout.splitlines() if c.strip()]
    problems = []
    prev = _git_show(str(PROGRESS.relative_to(ROOT)), base_ref)
    for c in commits:
        cur = _git_show(str(PROGRESS.relative_to(ROOT)), c)
        step_problems = check_progress_transitions(prev, cur, queue_ids)
        step_problems += check_progress_scope(prev, cur, allowed_ids)
        problems += ["(commit %s) %s" % (c[:10], p) for p in step_problems]
        prev = cur
    return problems


def _daf_for_sid(sid):
    """sid's own daf, looked up from the repair queue's own records (the
    queue is the durable source of truth for which daf a sugyaId belongs
    to). Returns None if the queue is unreadable or sid names no record --
    callers treat that as "cannot confirm", never as a silent match."""
    try:
        q = json.loads(QUEUE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    for rec in q.get("records", []):
        if rec.get("sugyaId") == sid:
            return rec.get("daf")
    return None


def _yoma_learning_dir():
    """The Yoma module's learningDataDir, read directly from module.json --
    this queue (and this whole file) is Yoma-specific, see AUDIT/QUEUE
    above, so there is no active-module resolution to thread through here."""
    desc = ROOT / "modules/yoma/module.json"
    d = json.loads(desc.read_text(encoding="utf-8"))
    return d["paths"]["learningDataDir"]


def derive_effective_status(sid, record, squash_commit=None, head_ref="HEAD"):
    """The effective, DERIVED status for a progress record, used for
    reporting/dashboards -- never for mutating the stored file. A record
    stored as APPROVED_PENDING_MERGE is treated as effectively COMPLETE
    only once a squash_commit is supplied and ALL of the following durable,
    sid-SPECIFIC evidence holds (checked in this order, first failure
    wins -- evidence["reason"] always names it):

      1. the stored status is genuinely APPROVED_PENDING_MERGE;
      2. the record itself already carries a non-empty reviewer and a
         non-empty independentReviewResult (the same bar
         check_progress_field_requirements enforces for any review-bearing
         status -- no controlled vocabulary, just non-empty strings);
      3. squash_commit is an ancestor of head_ref (the approved repair PR
         actually merged);
      4. squash_commit has a parseable .worker-manifest.json at repo root
         (read via the tree at that commit, not merely its own diff);
      5. that manifest's "type" is exactly
         worker_pipeline.AUDIT_RECORD_TASK_TYPE
         ("audited-sugya-enrichment-repair" -- the only task type this
         derivation ever honors);
      6. sid is named in that manifest's "auditRecordIds" (not merely "a"
         audit repair landed somewhere -- THIS sugya's repair);
      7. the manifest's single target daf (manifest["targets"][0], this
         task type always targets exactly one daf) equals sid's own daf,
         read from the repair queue;
      8. the exact target learning file for that daf --
         "{learningDataDir}/{daf}.learning.json" -- is among the files
         squash_commit's own diff touched (real content for THIS daf
         landed in THIS commit, not merely referenced by a correct-looking
         manifest).

    This is what removes the need for a second, progress-only PR just to
    flip the file to COMPLETE after merge: completion is read off real,
    durable git history (main's own commit graph) plus a manifest that
    durably and specifically names this sugya's own repair, never off any
    ancestor commit that merely happens to touch some *.learning.json file
    for an unrelated reason. Returns (effective_status, evidence-dict);
    never mutates `record`."""
    stored = record.get("status")
    evidence = {"derived": False, "squashCommit": squash_commit}
    if stored != "APPROVED_PENDING_MERGE":
        evidence["reason"] = "stored status is not APPROVED_PENDING_MERGE"
        return stored, evidence
    if not squash_commit:
        evidence["reason"] = "no squash commit supplied"
        return stored, evidence

    reviewer = str(record.get("reviewer") or "").strip()
    review_result = str(record.get("independentReviewResult") or "").strip()
    evidence["hasReviewer"] = bool(reviewer)
    evidence["hasIndependentReviewResult"] = bool(review_result)
    if not reviewer or not review_result:
        evidence["reason"] = ("record is missing a non-empty reviewer and/or "
                              "independentReviewResult")
        return stored, evidence

    anc = subprocess.run(["git", "merge-base", "--is-ancestor", squash_commit, head_ref],
                         cwd=str(ROOT), capture_output=True, text=True)
    is_ancestor = anc.returncode == 0
    evidence["isAncestorOfHead"] = is_ancestor
    if not is_ancestor:
        evidence["reason"] = "squash commit is not an ancestor of head_ref"
        return stored, evidence

    show = subprocess.run(["git", "show", "--name-only", "--format=", squash_commit],
                          cwd=str(ROOT), capture_output=True, text=True)
    touched = [l for l in show.stdout.splitlines() if l.strip()]
    evidence["touchedFiles"] = touched

    manifest = _git_show(".worker-manifest.json", squash_commit)
    evidence["hasManifestAtSquashCommit"] = manifest is not None
    if manifest is None:
        evidence["reason"] = "no parseable .worker-manifest.json at the squash commit"
        return stored, evidence

    manifest_type = manifest.get("type")
    evidence["manifestType"] = manifest_type
    if manifest_type != worker_pipeline.AUDIT_RECORD_TASK_TYPE:
        evidence["reason"] = ("manifest type %r is not %r"
                              % (manifest_type, worker_pipeline.AUDIT_RECORD_TASK_TYPE))
        return stored, evidence

    audit_record_ids = manifest.get("auditRecordIds") or []
    sid_in_ids = sid in audit_record_ids
    evidence["sidInManifestAuditRecordIds"] = sid_in_ids
    if not sid_in_ids:
        evidence["reason"] = ("sid is not named in the manifest's auditRecordIds %s"
                              % sorted(audit_record_ids))
        return stored, evidence

    targets = manifest.get("targets") or []
    manifest_target_daf = targets[0] if len(targets) == 1 else None
    evidence["manifestTargetDaf"] = manifest_target_daf
    sid_daf = _daf_for_sid(sid)
    evidence["sidDaf"] = sid_daf
    if not sid_daf or manifest_target_daf != sid_daf:
        evidence["reason"] = ("manifest target daf %r does not match sid's own daf %r"
                              % (manifest_target_daf, sid_daf))
        return stored, evidence

    target_learning_path = "%s/%s.learning.json" % (_yoma_learning_dir(), sid_daf)
    file_touched = target_learning_path in touched
    evidence["targetLearningFileTouched"] = file_touched
    evidence["targetLearningPath"] = target_learning_path
    if not file_touched:
        evidence["reason"] = "squash commit's diff did not touch %r" % target_learning_path
        return stored, evidence

    evidence["derived"] = True
    return "COMPLETE", evidence


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
    ap.add_argument("--allowed-ids", nargs="*", default=None,
                    help="restrict progress-record changes to exactly these sugyaIds (a "
                         "manifest's auditRecordIds); any other record's progress changing at "
                         "all is a failure. Omit to skip this scope check (e.g. when running "
                         "standalone with no manifest in scope).")
    ap.add_argument("--head", default="HEAD",
                    help="git ref for the head of the commit-history walk (default HEAD)")
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
        # The FULL commit-history walk is the transition-legality check
        # (required design per the one-PR repair lifecycle: a branch that
        # legally walked NOT_STARTED -> IN_PROGRESS -> FIXED_PENDING_REVIEW
        # -> ... across several commits must never be rejected just because
        # comparing only the two endpoints looks like a skip). It already
        # subsumes a plain endpoint-to-endpoint comparison: when the base
        # and head commits are adjacent (or identical), the walk reduces to
        # exactly that single step. A bare check_progress_transitions(before,
        # current, ids) call is deliberately NOT also run here -- doing so
        # would reintroduce the two-endpoint false-skip failure this design
        # exists to remove.
        prog_problems += check_progress_history(args.base, args.head, ids, args.allowed_ids)
        # Endpoint-only checks that do not need history: field requirements
        # (BLOCKED/review-bearing statuses, unknown fields) on the CURRENT
        # state, and record-specific scope (only named ids may differ from
        # base at all).
        prog_problems += check_progress_field_requirements(current.get("progress", {}))
        prog_problems += check_progress_scope(before, current, args.allowed_ids)
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
