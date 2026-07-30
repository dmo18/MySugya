#!/usr/bin/env python3
"""
generate_sourcerefs_blocker_dossier.py - Step 2 evidence assembly for the
33 residual sourceRefs defects (Phase 2B of docs/platform-closure-plan.md).

Read-only. Assembles, per defective ref, everything a human reader needs to
classify it without guessing from line numbers alone: the full step and its
sugya's full argumentFlow context, the current ref's target text (if it
resolves), every candidate the validator's own geometry names, the full text
of every line on the declared daf, and the full text of every line on the
immediately adjacent daf (previous and next in tractate order), so a
cross-daf citation can be checked against real content rather than assumed.

Writes docs/reports/data/sourcerefs-blocker-dossier.json. This file is
reading material for the classification pass (Step 2 of the current
campaign's plan); it does not itself classify anything, and the
classification/action fields it leaves blank are filled in by hand in
docs/reports/sourcerefs-blocker-table.json, not by this script.

Run: cd modules/yoma && python3 scripts/generate_sourcerefs_blocker_dossier.py
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import validate_source_refs as vsr  # noqa: E402

ROOT = Path(__file__).parent.parent
REPO = ROOT.parent.parent
LEARN_DIR = ROOT / "assets" / "learning" / "yoma"
DATA_DIR = REPO / "docs" / "reports" / "data"

DAF_ORDER_RE = re.compile(r"^(\d+)([ab])$")


def daf_sort_key(daf):
    m = DAF_ORDER_RE.match(daf)
    return (int(m.group(1)), m.group(2))


def all_daf_in_order():
    daf = sorted(
        {p.name.replace(".learning.json", "") for p in LEARN_DIR.glob("*.learning.json")},
        key=daf_sort_key,
    )
    return daf


def adjacent_daf(daf, ordered):
    i = ordered.index(daf)
    prev_daf = ordered[i - 1] if i > 0 else None
    next_daf = ordered[i + 1] if i + 1 < len(ordered) else None
    return prev_daf, next_daf


def load_learning_data_lines():
    """Parse every {id, kind, he, vilna_line, en, en_lit, sefaria_ref}
    entry out of the generated learning_data.js, keyed by id, plus the
    per-daf id order (document order is the corpus's own line order)."""
    text = (ROOT / "learning_data.js").read_text(encoding="utf-8")
    entry_re = re.compile(
        r'\{\s*id:\s*"([^"]+)",\s*kind:\s*"([^"]+)",\s*he:\s*"((?:[^"\\]|\\.)*)"'
        r'[^}]*?vilna_line:\s*(\d+),\s*en:\s*"((?:[^"\\]|\\.)*)"'
        r'[^}]*?en_lit:\s*"((?:[^"\\]|\\.)*)"'
        r'[^}]*?sefaria_ref:\s*"([^"]+)"',
        re.DOTALL,
    )
    by_id = {}
    order_by_daf = {}
    for m in entry_re.finditer(text):
        lid, kind, he, vilna, en, en_lit, sefaria_ref = m.groups()
        daf_m = re.match(r"^yoma-(\d{3}[ab])-l", lid)
        daf = None
        if daf_m:
            pad = daf_m.group(1)
            daf = f"{int(pad[:3])}{pad[3]}"
        entry = {
            "id": lid, "kind": kind,
            "he": he.replace("\\n", "\n").replace('\\"', '"'),
            "en": en.replace("\\n", "\n").replace('\\"', '"'),
            "en_lit": en_lit.replace("\\n", "\n").replace('\\"', '"'),
            "vilnaLine": int(vilna), "sefariaRef": sefaria_ref, "daf": daf,
        }
        by_id[lid] = entry
        if daf:
            order_by_daf.setdefault(daf, []).append(lid)
    return by_id, order_by_daf


def sugya_argument_flow(daf, sugya_id):
    path = LEARN_DIR / f"{daf}.learning.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    for s in doc.get("sugyot", []):
        if s.get("id") == sugya_id:
            return s.get("argumentFlow") or []
    return []


def daf_all_steps(daf):
    """Every argumentFlow step on a daf, across all its sugyot, in order."""
    path = LEARN_DIR / f"{daf}.learning.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for s in doc.get("sugyot", []):
        for st in (s.get("argumentFlow") or []):
            out.append({"sugyaId": s.get("id"), **st})
    return out


def main():
    ordered_daf = all_daf_in_order()
    by_id, order_by_daf = load_learning_data_lines()

    paths = sorted(LEARN_DIR.glob("*.learning.json"))
    counts, findings = vsr.run(paths)
    defect_findings = [f for f in findings if f["class"] in vsr.DEFECT_CLASSES]

    review = json.loads(
        (REPO / "docs" / "reports" / "source-refs-semantic-review.json")
        .read_text(encoding="utf-8"))
    review_by_key = {
        (r["daf"], r["sugyaId"], r["stepId"]): r for r in review
        if r["decision"] == "UNRESOLVED"
    }

    dossier = []
    for f in sorted(defect_findings, key=lambda x: (daf_sort_key(x["daf"]), x["sugyaId"], x["stepId"])):
        daf, sugya_id, step_id = f["daf"], f["sugyaId"], f["stepId"]
        flow = sugya_argument_flow(daf, sugya_id)
        step = next((s for s in flow if s.get("id") == step_id), None)
        step_idx = next((i for i, s in enumerate(flow) if s.get("id") == step_id), None)

        ref = f["ref"]
        candidate_ids = []
        if f["class"] == "OBJECT_COORDINATE_CONFLICT":
            candidate_ids = f.get("vilnaLineResolvesTo", [])
        elif f["class"] == "OBJECT_DANGLING_AMBIGUOUS":
            candidate_ids = f.get("candidates", [])

        prev_daf, next_daf = adjacent_daf(daf, ordered_daf)

        def line_text(lid):
            e = by_id.get(lid)
            if not e:
                return None
            return {k: e[k] for k in ("id", "kind", "vilnaLine", "sefariaRef", "he", "en", "en_lit")}

        current_target = line_text(ref.get("lineId")) if isinstance(ref, dict) else None

        entry = {
            "daf": daf,
            "sugyaId": sugya_id,
            "stepId": step_id,
            "stepIndex": step_idx,
            "stepType": step.get("type") if step else None,
            "stepLabel": step.get("label") if step else None,
            "stepSpeaker": step.get("speaker") if step else None,
            "stepText": step.get("text") if step else None,
            "allSourceRefsOnStep": step.get("sourceRefs") if step else None,
            "defectClass": f["class"],
            "flaggedRef": ref,
            "flaggedRefResolvesLineId": current_target is not None,
            "currentTargetText": current_target,
            "candidateIds": candidate_ids,
            "candidateTexts": [line_text(c) for c in candidate_ids],
            "sugyaFullArgumentFlow": [
                {"id": s.get("id"), "type": s.get("type"), "label": s.get("label"),
                 "speaker": s.get("speaker"), "text": s.get("text"),
                 "sourceRefs": s.get("sourceRefs")}
                for s in flow
            ],
            "declaredDafAllLineIdsInOrder": order_by_daf.get(daf, []),
            "declaredDafAllLines": [line_text(lid) for lid in order_by_daf.get(daf, [])],
            "prevDaf": prev_daf,
            "prevDafAllLines": [line_text(lid) for lid in order_by_daf.get(prev_daf, [])] if prev_daf else [],
            "nextDaf": next_daf,
            "nextDafAllLines": [line_text(lid) for lid in order_by_daf.get(next_daf, [])] if next_daf else [],
            "priorReviewReason": review_by_key.get((daf, sugya_id, step_id), {}).get("reason"),
            "priorReviewIdx": review_by_key.get((daf, sugya_id, step_id), {}).get("idx"),
        }
        dossier.append(entry)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DATA_DIR / "sourcerefs-blocker-dossier.json"
    out_path.write_text(json.dumps(dossier, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out_path} - {len(dossier)} cases assembled "
          f"({sum(1 for d in dossier if d['defectClass'] == 'OBJECT_COORDINATE_CONFLICT')} "
          f"OBJECT_COORDINATE_CONFLICT, "
          f"{sum(1 for d in dossier if d['defectClass'] == 'OBJECT_DANGLING_AMBIGUOUS')} "
          f"OBJECT_DANGLING_AMBIGUOUS)")


if __name__ == "__main__":
    main()
