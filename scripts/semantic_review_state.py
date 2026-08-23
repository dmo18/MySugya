#!/usr/bin/env python3
"""Safely update the semantic certification registry from completed reviews.

This tool records decisions. It never makes them. Reviewers supply verdicts and
evidence after reading a source-first packet. Every review pass is bound to the
exact source and semantic fingerprints visible to that reviewer.

Examples:

  # First pass found a defect
  python3 scripts/semantic_review_state.py first --module yoma \
    --sugya yoma-024a-s01 --review-id session-A --reviewer-context-id agent-A \
    --verdict REPAIR_REQUIRED --evidence-file /tmp/024a-first.json

  # After repair, mark it ready for independent review
  python3 scripts/semantic_review_state.py repaired --module yoma \
    --sugya yoma-024a-s01 --repair-ref HEAD

  # Independent source-first reviewer confirms current content
  python3 scripts/semantic_review_state.py second --module yoma \
    --sugya yoma-024a-s01 --review-id session-B --reviewer-context-id agent-B \
    --verdict CONFIRMED --evidence-file /tmp/024a-second.json

  # Mandatory schema-2.0 final whole-record audit, performed AFTER the
  # candidate above is finalized, before the record can become CERTIFIED
  python3 scripts/semantic_review_state.py final-audit --module yoma \
    --sugya yoma-024a-s01 --review-id session-C --auditor-context-id agent-C \
    --audit-file /tmp/024a-final-audit.json --commit-ref HEAD

A first-pass REPAIR_REQUIRED record cannot become CERTIFIED unless `repaired`
has been recorded and the candidate actually differs from what the first reviewer
saw. A second-pass REJECTED verdict becomes the new fingerprint-bound
REPAIR_REQUIRED first pass, so the state machine immediately knows what candidate
was rejected and can repair it without a dead-end transition. BLOCKED stops the
queue.

`--reviewer-context-id` (first/second) and `--auditor-context-id`
(final-audit) must each name a genuinely distinct reviewer/session/context --
never a second string invented inside the same reasoning context as a prior
pass. If a truly fresh, isolated review context is unavailable, do not record
a pass; leave the record where it is and say so.

A CONFIRMED second pass produces PENDING_FINAL_AUDIT, not CERTIFIED. The
mandatory final whole-record audit (`--audit-file`, schema documented in
docs/semantic-self-heal.md) is a separate, later step, fingerprint-bound to
the exact candidate the second pass just confirmed.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Dict

from semantic_certification import cert_path, fingerprints, load_corpus, load_registry, validate_final_audit


def read_evidence(path: str | None) -> Any:
    if not path:
        return "No separate evidence file supplied."
    return json.loads(Path(path).read_text(encoding="utf-8"))


def resolve_ref(ref: str) -> str:
    p = subprocess.run(["git", "rev-parse", ref], text=True, capture_output=True)
    return p.stdout.strip() if p.returncode == 0 and p.stdout.strip() else ref


def write_registry(module: str, registry: Dict[str, Any]) -> None:
    cert_path(module).write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def get_target(module: str, sid: str):
    corpus = load_corpus(module)
    if sid not in corpus:
        raise SystemExit(f"unknown sugya id {sid!r}")
    return corpus[sid]


def review_block(review_id: str, reviewer_context_id: str, verdict: str, source_fp: str, semantic_fp: str, evidence: Any) -> Dict[str, Any]:
    return {
        "reviewId": review_id,
        "reviewerContextId": reviewer_context_id,
        "sourceFirst": True,
        "verdict": verdict,
        "reviewedSourceFingerprint": source_fp,
        "reviewedSemanticFingerprint": semantic_fp,
        "evidence": evidence,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    first = sub.add_parser("first")
    first.add_argument("--module", default="yoma")
    first.add_argument("--sugya", required=True)
    first.add_argument("--review-id", required=True)
    first.add_argument("--reviewer-context-id", required=True, help="Genuinely distinct reviewer/session/context id, never fabricated")
    first.add_argument("--verdict", choices=["VERIFIED", "REPAIR_REQUIRED", "BLOCKED"], required=True)
    first.add_argument("--evidence-file")

    repaired = sub.add_parser("repaired")
    repaired.add_argument("--module", default="yoma")
    repaired.add_argument("--sugya", required=True)
    repaired.add_argument("--repair-ref", default="HEAD")

    second = sub.add_parser("second")
    second.add_argument("--module", default="yoma")
    second.add_argument("--sugya", required=True)
    second.add_argument("--review-id", required=True)
    second.add_argument("--reviewer-context-id", required=True, help="Genuinely distinct reviewer/session/context id, never fabricated")
    second.add_argument("--verdict", choices=["CONFIRMED", "REJECTED", "BLOCKED"], required=True)
    second.add_argument("--evidence-file")

    final_audit_cmd = sub.add_parser("final-audit")
    final_audit_cmd.add_argument("--module", default="yoma")
    final_audit_cmd.add_argument("--sugya", required=True)
    final_audit_cmd.add_argument("--review-id", required=True)
    final_audit_cmd.add_argument("--auditor-context-id", required=True, help="Genuinely distinct reviewer/session/context id, never fabricated")
    final_audit_cmd.add_argument("--audit-file", required=True, help="JSON file with dafBoundary, fieldInventory, staleContentSweep, and optionally openEndingFieldSweep")
    final_audit_cmd.add_argument("--commit-ref", default="HEAD")

    args = ap.parse_args()
    module, sid = args.module, args.sugya
    daf, doc, sugya = get_target(module, sid)
    source_fp, semantic_fp = fingerprints(module, daf, doc, sugya)
    registry = load_registry(module)
    records = registry.setdefault("records", {})
    current = records.get(sid) or {"sugyaId": sid, "daf": daf}

    if args.cmd == "first":
        block = review_block(args.review_id, args.reviewer_context_id, args.verdict, source_fp, semantic_fp, read_evidence(args.evidence_file))
        current = {
            "sugyaId": sid,
            "daf": daf,
            "state": (
                "BLOCKED" if args.verdict == "BLOCKED"
                else "REPAIR_REQUIRED" if args.verdict == "REPAIR_REQUIRED"
                else "REPAIRED_PENDING_REVIEW"
            ),
            "firstPass": block,
        }
        records[sid] = current
        write_registry(module, registry)
        print(f"Recorded first pass: {sid} -> {current['state']}")
        return

    if args.cmd == "repaired":
        first_pass = current.get("firstPass")
        if not isinstance(first_pass, dict) or first_pass.get("verdict") != "REPAIR_REQUIRED":
            raise SystemExit("repaired transition requires an existing firstPass REPAIR_REQUIRED record")
        current["state"] = "REPAIRED_PENDING_REVIEW"
        current["repairRef"] = resolve_ref(args.repair_ref)
        for k in ("sourceFingerprint", "semanticFingerprint", "secondPass", "finalAudit", "certifiedAtCommit"):
            current.pop(k, None)
        records[sid] = current
        write_registry(module, registry)
        print(f"Recorded repair: {sid} -> REPAIRED_PENDING_REVIEW")
        return

    if args.cmd == "final-audit":
        if current.get("state") != "PENDING_FINAL_AUDIT":
            raise SystemExit(
                "final-audit requires an existing PENDING_FINAL_AUDIT record "
                "(run `second` with --verdict CONFIRMED first)"
            )
        payload = read_evidence(args.audit_file)
        if not isinstance(payload, dict):
            raise SystemExit("--audit-file must contain a JSON object with dafBoundary, fieldInventory, staleContentSweep")
        final_audit = {
            "reviewId": args.review_id,
            "auditorContextId": args.auditor_context_id,
            "auditedSourceFingerprint": source_fp,
            "auditedSemanticFingerprint": semantic_fp,
            "dafBoundary": payload.get("dafBoundary"),
            "fieldInventory": payload.get("fieldInventory"),
            "staleContentSweep": payload.get("staleContentSweep"),
        }
        if payload.get("openEndingFieldSweep") is not None:
            final_audit["openEndingFieldSweep"] = payload["openEndingFieldSweep"]

        problems = validate_final_audit(
            module, daf, sugya, source_fp, semantic_fp, final_audit,
            current.get("firstPass"), current.get("secondPass"),
        )
        if problems:
            raise SystemExit("final audit failed validation:\n" + "\n".join(f"  - {p}" for p in problems))

        current["state"] = "CERTIFIED"
        current["finalAudit"] = final_audit
        current["certifiedAtCommit"] = resolve_ref(args.commit_ref)
        records[sid] = current
        write_registry(module, registry)
        print(f"Recorded final whole-record audit: {sid} -> CERTIFIED")
        return

    first_pass = current.get("firstPass")
    if not isinstance(first_pass, dict):
        raise SystemExit("second transition requires an existing firstPass")
    if first_pass.get("reviewId") == args.review_id:
        raise SystemExit("independent second pass must use a different reviewId")
    if first_pass.get("reviewerContextId") == args.reviewer_context_id:
        raise SystemExit("independent second pass must run in a genuinely different reviewer context than firstPass")
    if first_pass.get("verdict") == "REPAIR_REQUIRED" and not current.get("repairRef"):
        raise SystemExit("REPAIR_REQUIRED first pass must record `repaired` before second review")

    evidence = read_evidence(args.evidence_file)
    second_block = review_block(args.review_id, args.reviewer_context_id, args.verdict, source_fp, semantic_fp, evidence)

    if args.verdict == "BLOCKED":
        current["state"] = "BLOCKED"
        current["secondPass"] = second_block
    elif args.verdict == "REJECTED":
        # The independent reviewer has just performed a source-first review and
        # found this exact candidate defective. Promote that finding into the
        # next repair cycle's first pass rather than leaving an incompatible
        # VERIFIED first pass behind.
        current = {
            "sugyaId": sid,
            "daf": daf,
            "state": "REPAIR_REQUIRED",
            "firstPass": review_block(
                args.review_id,
                args.reviewer_context_id,
                "REPAIR_REQUIRED",
                source_fp,
                semantic_fp,
                {"origin": "independent-second-pass-rejection", "reviewEvidence": evidence},
            ),
        }
    else:
        # Schema 2.0: a CONFIRMED second pass locks in the candidate as
        # PENDING_FINAL_AUDIT, not CERTIFIED. The mandatory fingerprint-bound
        # final whole-record audit is a separate later step (`final-audit`),
        # so it is provably performed after the candidate is finalized.
        current.update({
            "state": "PENDING_FINAL_AUDIT",
            "sourceFingerprint": source_fp,
            "semanticFingerprint": semantic_fp,
            "secondPass": second_block,
        })
        current.pop("finalAudit", None)
        current.pop("certifiedAtCommit", None)

    records[sid] = current
    write_registry(module, registry)
    print(f"Recorded second pass: {sid} -> {current['state']}")


if __name__ == "__main__":
    main()
