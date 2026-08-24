#!/usr/bin/env python3
"""Semantic self-heal campaign driver.

This is intentionally an orchestration/state tool, not an automated Talmudic
judge. Claude supplies the semantic judgment. This program supplies the parts
that must not depend on memory or trust:

- deterministic corpus ordering
- source-first work packets
- current effective certification state
- exact next action
- review templates with live fingerprints
- second-pass packets that omit first-pass reasoning

The loop is:
  AUDIT -> (CERTIFY or REPAIR) -> INDEPENDENT_REVIEW -> CERTIFY -> NEXT

It continues until strict semantic certification reports 492/492 CERTIFIED,
or stops on a genuine BLOCKED source/meaning ambiguity.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

from semantic_certification import (
    REPO,
    cert_path,
    certificate_status,
    corpus_status,
    daf_sort_key,
    fingerprints,
    load_corpus,
    load_registry,
    raw_dir,
    source_payload,
)


def action_for(state: str) -> str:
    return {
        "UNCERTIFIED": "AUDIT",
        "STALE": "AUDIT",
        "INVALID": "AUDIT",
        "REPAIR_REQUIRED": "REPAIR",
        "REPAIRED_PENDING_REVIEW": "INDEPENDENT_REVIEW",
        "PENDING_FINAL_AUDIT": "FINAL_AUDIT",
        "REVALIDATION_REQUIRED": "AUDIT",
        "CERTIFIED": "DONE",
        "BLOCKED": "BLOCKED",
        "ORPHANED_RECORD": "CLEAN_REGISTRY",
    }.get(state, "AUDIT")


def ordered_details(module: str) -> list[tuple[str, Dict[str, Any]]]:
    _, details = corpus_status(module)
    corpus = load_corpus(module)
    return sorted(
        ((sid, d) for sid, d in details.items() if sid in corpus),
        key=lambda x: (daf_sort_key(x[1]["daf"]), x[0]),
    )


def relevant_rashi(doc: Dict[str, Any], daf: str, sugya: Dict[str, Any]) -> list[Dict[str, Any]]:
    start = (sugya.get("lineRange") or {}).get("startVilnaLine", 0)
    end = (sugya.get("lineRange") or {}).get("endVilnaLine", 0)
    out = []
    for entry in doc.get("rashiTranslations") or []:
        links = entry.get("linkedGemaraLineIds") or []
        keep = False
        for link in links:
            if not isinstance(link, str):
                continue
            m = re.search(r"-l(\d+)", link)
            if m and start <= int(m.group(1)) <= end:
                keep = True
                break
        if keep:
            out.append(entry)
    return out


def packet(module: str, sid: str, second_pass: bool = False) -> Dict[str, Any]:
    corpus = load_corpus(module)
    registry = load_registry(module)
    if sid not in corpus:
        raise SystemExit(f"unknown sugya id {sid!r}")
    daf, doc, sugya = corpus[sid]
    source_fp, semantic_fp = fingerprints(module, daf, doc, sugya)
    effective, problems = certificate_status(module, daf, doc, sugya, registry["records"].get(sid))
    raw = json.loads((raw_dir(module) / f"{daf}.json").read_text(encoding="utf-8"))

    result = {
        "instructions": [
            "SOURCE-FIRST REVIEW. Read primarySource before currentEnrichment.",
            "Do not treat review:'reviewed', prior audit prose, current argumentFlow, or other enrichment fields as evidence that a claim is true.",
            "Reconstruct what the cited Hebrew range says independently, then compare every learner-facing claim against that reconstruction.",
            "Check boundaries. Content from earlier/later lines or another daf is a defect even if it is true elsewhere in Yoma.",
            "For every claimed ruling, speaker, sequence, quantity, reason, or narrative event, require support inside this source range unless the field is explicitly contextual and labeled as such.",
            "If uncertain after reading the source and relevant Rashi, mark BLOCKED. Never guess to make the queue advance.",
        ],
        "reviewMode": "INDEPENDENT_SECOND_PASS" if second_pass else "FIRST_PASS",
        "sugyaId": sid,
        "daf": daf,
        "effectiveState": effective,
        "stateProblems": problems,
        "sourceFingerprint": source_fp,
        "semanticFingerprint": semantic_fp,
        "primarySource": source_payload(module, daf, sugya),
        "sourceContext": {
            "previousRawLine": raw.get("lines", [])[max(0, (sugya["lineRange"]["startVilnaLine"] - 2))]
                if sugya["lineRange"]["startVilnaLine"] > 1 else None,
            "nextRawLine": raw.get("lines", [])[sugya["lineRange"]["endVilnaLine"]]
                if sugya["lineRange"]["endVilnaLine"] < len(raw.get("lines", [])) else None,
        },
        "relevantRashi": relevant_rashi(doc, daf, sugya),
        "currentDafSummary": doc.get("summary", ""),
        "currentEnrichment": {
            k: v for k, v in sugya.items()
            if k not in {"lines", "sefariaRefs", "review"}
        },
        "requiredVerdicts": (
            ["CONFIRMED", "REJECTED", "BLOCKED"]
            if second_pass else ["VERIFIED", "REPAIR_REQUIRED", "BLOCKED"]
        ),
    }
    if not second_pass:
        rec = registry["records"].get(sid)
        if rec:
            result["existingCertificationRecord"] = rec
    else:
        # Critical anti-anchoring rule: the independent reviewer receives no
        # first-pass rationale/issues. Only the corpus, primary source, Rashi,
        # and current candidate content are shown.
        result["independenceRule"] = "First-pass rationale intentionally omitted. Re-derive the answer from source."
    return result


def template(module: str, sid: str, review_id: str, second_review_id: str | None) -> Dict[str, Any]:
    corpus = load_corpus(module)
    if sid not in corpus:
        raise SystemExit(f"unknown sugya id {sid!r}")
    daf, doc, sugya = corpus[sid]
    source_fp, semantic_fp = fingerprints(module, daf, doc, sugya)
    if second_review_id:
        # Schema 2.0: a CONFIRMED second pass produces PENDING_FINAL_AUDIT,
        # not CERTIFIED. Use `semantic_review_state.py final-audit` afterward
        # to record the mandatory fingerprint-bound final whole-record audit
        # (dafBoundary, fieldInventory, staleContentSweep) before the record
        # can become CERTIFIED. See docs/semantic-self-heal.md.
        return {
            "sugyaId": sid,
            "daf": daf,
            "state": "PENDING_FINAL_AUDIT",
            "sourceFingerprint": source_fp,
            "semanticFingerprint": semantic_fp,
            "firstPass": {
                "reviewId": review_id,
                "sourceFirst": True,
                "reviewerContextId": "REPLACE with a genuinely distinct reviewer/session/context id",
                "verdict": "VERIFIED_OR_REPAIR_REQUIRED",
                "evidence": "REPLACE with compact source-based finding, not prior-enrichment agreement",
            },
            "secondPass": {
                "reviewId": second_review_id,
                "sourceFirst": True,
                "reviewerContextId": "REPLACE with a context id that differs from firstPass.reviewerContextId",
                "verdict": "CONFIRMED",
                "evidence": "REPLACE with independently re-derived source-based confirmation",
            },
        }
    return {
        "sugyaId": sid,
        "daf": daf,
        "state": "REPAIR_REQUIRED",
        "firstPass": {
            "reviewId": review_id,
            "sourceFirst": True,
            "reviewerContextId": "REPLACE with a genuinely distinct reviewer/session/context id",
            "verdict": "REPAIR_REQUIRED",
            "issues": [
                {
                    "field": "REPLACE",
                    "sourceLines": "REPLACE",
                    "problem": "REPLACE",
                    "requiredCorrection": "REPLACE",
                }
            ],
        },
    }


def print_status(module: str) -> None:
    counts, _ = corpus_status(module)
    total = sum(v for k, v in counts.items() if k != "ORPHANED_RECORD")
    certified = counts.get("CERTIFIED", 0)
    print(f"Semantic self-heal: {certified}/{total} freshly CERTIFIED")
    for state in sorted(counts):
        print(f"  {state:24s} {counts[state]}")
    pending = [(sid, d, action_for(d["state"])) for sid, d in ordered_details(module) if d["state"] != "CERTIFIED"]
    if pending:
        sid, d, action = pending[0]
        print(f"\nNEXT: {action} {sid} ({d['daf']})")
        if action == "BLOCKED":
            print("STOP: first unresolved item is BLOCKED. Resolve source ambiguity before continuing.")
    else:
        print("\nQUEUE COMPLETE: run validate_semantic_certification.py --strict and only then enable strictMode.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--module", default="yoma")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    nxt = sub.add_parser("next")
    nxt.add_argument("--json", action="store_true")
    pkt = sub.add_parser("packet")
    pkt.add_argument("--sugya", required=True)
    pkt.add_argument("--second-pass", action="store_true")
    tmpl = sub.add_parser("template")
    tmpl.add_argument("--sugya", required=True)
    tmpl.add_argument("--review-id", required=True)
    tmpl.add_argument("--second-review-id")
    args = ap.parse_args()

    if args.cmd == "status":
        print_status(args.module)
        return
    if args.cmd == "next":
        pending = [(sid, d, action_for(d["state"])) for sid, d in ordered_details(args.module) if d["state"] != "CERTIFIED"]
        if not pending:
            data = {"complete": True, "next": None}
        else:
            sid, d, action = pending[0]
            data = {"complete": False, "next": {"action": action, "sugyaId": sid, "daf": d["daf"], "problems": d["problems"]}}
        print(json.dumps(data, indent=2) if args.json else ("COMPLETE" if data["complete"] else f"{data['next']['action']} {data['next']['sugyaId']}"))
        return
    if args.cmd == "packet":
        print(json.dumps(packet(args.module, args.sugya, args.second_pass), indent=2, ensure_ascii=False))
        return
    if args.cmd == "template":
        print(json.dumps(template(args.module, args.sugya, args.review_id, args.second_review_id), indent=2, ensure_ascii=False))
        return


if __name__ == "__main__":
    main()
