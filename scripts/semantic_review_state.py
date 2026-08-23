#!/usr/bin/env python3
"""Safely update the semantic certification registry from completed reviews.

This tool records decisions. It never makes them. Reviewers supply verdicts and
evidence after reading a source-first packet. Every review pass is bound to the
exact source and semantic fingerprints visible to that reviewer.

Examples:

  # First pass found a defect
  python3 scripts/semantic_review_state.py first --module yoma \
    --sugya yoma-024a-s01 --review-id session-A --verdict REPAIR_REQUIRED \
    --evidence-file /tmp/024a-first.json

  # After repair, mark it ready for independent review
  python3 scripts/semantic_review_state.py repaired --module yoma \
    --sugya yoma-024a-s01 --repair-ref HEAD

  # Independent source-first reviewer confirms current content
  python3 scripts/semantic_review_state.py second --module yoma \
    --sugya yoma-024a-s01 --review-id session-B --verdict CONFIRMED \
    --evidence-file /tmp/024a-second.json --commit-ref HEAD

A first-pass REPAIR_REQUIRED record cannot become CERTIFIED unless `repaired`
has been recorded and the candidate actually differs from what the first reviewer
saw. REJECTED returns the record to REPAIR_REQUIRED. BLOCKED stops the queue.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Dict

from semantic_certification import cert_path, fingerprints, load_corpus, load_registry


def read_evidence(path: str | None) -> Any:
    if not path:
        return "No separate evidence file supplied."
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8"))


def resolve_ref(ref: str) -> str:
    p = subprocess.run(["git", "rev-parse", ref], text=True, capture_output=True)
    return p.stdout.strip() if p.returncode == 0 and p.stdout.strip() else ref


def write_registry(module: str, registry: Dict[str, Any]) -> None:
    path = cert_path(module)
    path.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def get_target(module: str, sid: str):
    corpus = load_corpus(module)
    if sid not in corpus:
        raise SystemExit(f"unknown sugya id {sid!r}")
    return corpus[sid]


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    first = sub.add_parser("first")
    first.add_argument("--module", default="yoma")
    first.add_argument("--sugya", required=True)
    first.add_argument("--review-id", required=True)
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
    second.add_argument("--verdict", choices=["CONFIRMED", "REJECTED", "BLOCKED"], required=True)
    second.add_argument("--evidence-file")
    second.add_argument("--commit-ref", default="HEAD")

    args = ap.parse_args()
    module, sid = args.module, args.sugya
    daf, doc, sugya = get_target(module, sid)
    source_fp, semantic_fp = fingerprints(module, daf, doc, sugya)
    registry = load_registry(module)
    records = registry.setdefault("records", {})
    current = records.get(sid) or {"sugyaId": sid, "daf": daf}

    if args.cmd == "first":
        current = {
            "sugyaId": sid,
            "daf": daf,
            "state": (
                "BLOCKED" if args.verdict == "BLOCKED"
                else "REPAIR_REQUIRED" if args.verdict == "REPAIR_REQUIRED"
                else "REPAIRED_PENDING_REVIEW"
            ),
            "firstPass": {
                "reviewId": args.review_id,
                "sourceFirst": True,
                "verdict": args.verdict,
                "reviewedSourceFingerprint": source_fp,
                "reviewedSemanticFingerprint": semantic_fp,
                "evidence": read_evidence(args.evidence_file),
            },
        }
        # A clean first pass is not CERTIFIED. It still needs the independent
        # second pass, hence REPAIRED_PENDING_REVIEW as the generic pending state.
        records[sid] = current
        write_registry(module, registry)
        print(f"Recorded first pass: {sid} -> {current['state']}")
        return

    if args.cmd == "repaired":
        first_pass = current.get("firstPass")
        if not isinstance(first_pass, dict) or first_pass.get("verdict") != "REPAIR_REQUIRED":
            raise SystemExit("repaired transition requires an existing firstPass REPAIR_REQUIRED record")
        # Record the repair action even before the independent review. The final
        # certificate validator separately proves that the reviewed candidate
        # actually differs from the first-pass known-bad candidate.
        current["state"] = "REPAIRED_PENDING_REVIEW"
        current["repairRef"] = resolve_ref(args.repair_ref)
        for k in ("sourceFingerprint", "semanticFingerprint", "secondPass", "certifiedAtCommit"):
            current.pop(k, None)
        records[sid] = current
        write_registry(module, registry)
        print(f"Recorded repair: {sid} -> REPAIRED_PENDING_REVIEW")
        return

    first_pass = current.get("firstPass")
    if not isinstance(first_pass, dict):
        raise SystemExit("second transition requires an existing firstPass")
    if first_pass.get("reviewId") == args.review_id:
        raise SystemExit("independent second pass must use a different reviewId")

    # Do not let a known-bad first pass skip the explicit repair transition.
    if first_pass.get("verdict") == "REPAIR_REQUIRED" and not current.get("repairRef"):
        raise SystemExit("REPAIR_REQUIRED first pass must record `repaired` before second review")

    second_block = {
        "reviewId": args.review_id,
        "sourceFirst": True,
        "verdict": args.verdict,
        "reviewedSourceFingerprint": source_fp,
        "reviewedSemanticFingerprint": semantic_fp,
        "evidence": read_evidence(args.evidence_file),
    }

    if args.verdict == "BLOCKED":
        current["state"] = "BLOCKED"
        current["secondPass"] = second_block
    elif args.verdict == "REJECTED":
        current["state"] = "REPAIR_REQUIRED"
        current["secondPass"] = second_block
        current.pop("sourceFingerprint", None)
        current.pop("semanticFingerprint", None)
        current.pop("certifiedAtCommit", None)
    else:
        current.update({
            "state": "CERTIFIED",
            "sourceFingerprint": source_fp,
            "semanticFingerprint": semantic_fp,
            "secondPass": second_block,
            "certifiedAtCommit": resolve_ref(args.commit_ref),
        })

    records[sid] = current
    write_registry(module, registry)
    print(f"Recorded second pass: {sid} -> {current['state']}")


if __name__ == "__main__":
    main()
