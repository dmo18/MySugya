#!/usr/bin/env python3
"""Build a source-first review packet for an entire daf.

Whole-daf review is the default campaign unit. It prevents a page summary or
sugya-boundary correction discovered late in the daf from invalidating semantic
certificates issued earlier on the same page.

The independent second-pass packet intentionally omits prior review evidence.
"""
from __future__ import annotations

import argparse
import json
import re
from typing import Any, Dict

from semantic_certification import certificate_status, fingerprints, load_corpus, load_registry, raw_dir


def rashi_for_sugya(doc: Dict[str, Any], sugya: Dict[str, Any]) -> list[Dict[str, Any]]:
    lr = sugya.get("lineRange") or {}
    start, end = lr.get("startVilnaLine", 0), lr.get("endVilnaLine", 0)
    out = []
    for entry in doc.get("rashiTranslations") or []:
        for link in entry.get("linkedGemaraLineIds") or []:
            if not isinstance(link, str):
                continue
            m = re.search(r"-l(\d+)", link)
            if m and start <= int(m.group(1)) <= end:
                out.append(entry)
                break
    return out


def build_packet(module: str, daf: str, second_pass: bool) -> Dict[str, Any]:
    corpus = load_corpus(module)
    registry = load_registry(module)
    rows = [(sid, doc, sugya) for sid, (d, doc, sugya) in corpus.items() if d == daf]
    rows.sort(key=lambda x: x[2].get("sugyaNumber", 0))
    if not rows:
        raise SystemExit(f"unknown/empty daf {daf!r}")
    doc = rows[0][1]
    raw = json.loads((raw_dir(module) / f"{daf}.json").read_text(encoding="utf-8"))

    sugyot = []
    for sid, _, sugya in rows:
        source_fp, semantic_fp = fingerprints(module, daf, doc, sugya)
        state, problems = certificate_status(module, daf, doc, sugya, registry["records"].get(sid))
        item = {
            "sugyaId": sid,
            "sugyaNumber": sugya.get("sugyaNumber"),
            "declaredLineRange": sugya.get("lineRange"),
            "lineMap": sugya.get("lines") or [],
            "sefariaRefs": sugya.get("sefariaRefs") or [],
            "effectiveCertificationState": state,
            "certificationProblems": problems,
            "sourceFingerprint": source_fp,
            "semanticFingerprint": semantic_fp,
            "relevantRashi": rashi_for_sugya(doc, sugya),
            "currentEnrichment": {
                k: v for k, v in sugya.items()
                if k not in {"lines", "sefariaRefs", "review", "rashiTranslations"}
            },
        }
        if not second_pass and registry["records"].get(sid):
            item["existingReviewRecord"] = registry["records"][sid]
        sugyot.append(item)

    return {
        "reviewMode": "INDEPENDENT_SECOND_PASS" if second_pass else "FIRST_PASS",
        "module": module,
        "daf": daf,
        "instructions": [
            "Read authoritativeHebrewLines from beginning to end before reading current enrichment.",
            "Independently map the daf's topic transitions and sugya boundaries from source.",
            "Then inspect the daf summary and every semantic field of every sugya, not only fields previously flagged.",
            "A true statement that belongs to another line range or another daf is still a defect here.",
            "Check quantities, names, speakers, rulings, reasons, chronology, proof texts, disputes and conclusions explicitly.",
            "Use relevantRashi as commentary evidence, never as a substitute for reading the Gemara source.",
            "If a boundary change is needed, review all sugyot on this daf together before certification.",
            "Do not use old review flags, prior completion reports, or agreement among enrichment fields as proof.",
            "If meaning cannot be resolved responsibly, return BLOCKED rather than guessing.",
        ],
        "authoritativeHebrewLines": [
            {"vilnaLine": i + 1, "he": line}
            for i, line in enumerate(raw.get("lines") or [])
        ],
        "currentDafSummary": doc.get("summary", ""),
        "sugyot": sugyot,
        "requiredOutput": {
            "dafSummaryVerdict": "VERIFIED | REPAIR_REQUIRED | BLOCKED",
            "perSugya": "one verdict and source-based evidence entry for every sugya on the daf",
            "boundaryVerdict": "VERIFIED | REPAIR_REQUIRED | BLOCKED",
            "repairScope": "if any defect exists, list every affected field before editing so the repair is holistic",
        },
        "independenceRule": (
            "First-pass evidence is intentionally omitted. Re-derive all conclusions from source."
            if second_pass else None
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--module", default="yoma")
    ap.add_argument("--daf", required=True)
    ap.add_argument("--second-pass", action="store_true")
    args = ap.parse_args()
    print(json.dumps(build_packet(args.module, args.daf, args.second_pass), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
