#!/usr/bin/env python3
"""
generate_phase2_inventory.py - Step 1 of Phase 2: read-only corpus inventory
for argumentFlow and sourceRefs.

Writes machine-readable JSON to docs/reports/data/ and prints a human-
readable summary. Makes no changes to any corpus file. Re-run any time to
refresh the inventory; it is a report generator, not a one-off script.

Run: cd modules/yoma && python3 scripts/generate_phase2_inventory.py
"""
import json
import re
import sys
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import validate_source_refs as vsr  # noqa: E402

ROOT = Path(__file__).parent.parent
REPO = ROOT.parent.parent
LEARN_DIR = ROOT / "assets" / "learning" / "yoma"
DATA_DIR = REPO / "docs" / "reports" / "data"

CANONICAL_STEP_TYPES = {
    "case", "question", "proposal", "challenge", "objection",
    "counter_objection", "proof", "answer", "distinction",
    "qualification", "rejection", "resolution", "takeaway",
}
STR_REF_RE = re.compile(r"^Yoma\.(\d+[ab])\.(\d+)$")


def argumentflow_inventory():
    sugyot = []
    total_steps = 0
    type_counter = Counter()
    type_daf = defaultdict(set)
    type_examples = defaultdict(list)
    malformed, non_string, empty_type = [], [], []

    for path in sorted(LEARN_DIR.glob("*.learning.json")):
        daf = path.name.replace(".learning.json", "")
        doc = json.loads(path.read_text(encoding="utf-8"))
        for s in doc.get("sugyot", []):
            sugyot.append((daf, s["id"]))
            for st in (s.get("argumentFlow") or []):
                total_steps += 1
                t = st.get("type")
                if t is None:
                    malformed.append([daf, s["id"], st.get("id")])
                    continue
                if not isinstance(t, str):
                    non_string.append([daf, s["id"], st.get("id"), repr(t)])
                    continue
                if t.strip() == "":
                    empty_type.append([daf, s["id"], st.get("id")])
                    continue
                type_counter[t] += 1
                type_daf[t].add(daf)
                if len(type_examples[t]) < 3:
                    type_examples[t].append({
                        "daf": daf, "sugyaId": s["id"],
                        "stepId": st.get("id"), "label": st.get("label"),
                    })

    in_canon = sum(v for k, v in type_counter.items() if k in CANONICAL_STEP_TYPES)
    out_canon = sum(v for k, v in type_counter.items() if k not in CANONICAL_STEP_TYPES)

    return {
        "sugyotTotal": len(sugyot),
        "argumentFlowStepsTotal": total_steps,
        "distinctTypeValues": len(type_counter),
        "malformedTypeCount": len(malformed),
        "malformed": malformed,
        "nonStringTypeCount": len(non_string),
        "nonStringType": non_string,
        "emptyTypeCount": len(empty_type),
        "emptyType": empty_type,
        "typeFrequency": dict(type_counter.most_common()),
        "typeDafSpread": {k: sorted(v) for k, v in type_daf.items()},
        "typeExamples": type_examples,
        "canonicalStepTypes": sorted(CANONICAL_STEP_TYPES),
        "stepsInCanonical13": in_canon,
        "stepsOutsideCanonical13": out_canon,
        "distinctValuesOutsideCanonical13": sum(
            1 for k in type_counter if k not in CANONICAL_STEP_TYPES),
    }


def sourcerefs_inventory():
    shapes = Counter()
    obj_keysets = Counter()
    sourcetype_values = Counter()
    missing_sourcetype = 0
    null_or_empty = 0
    str_count = obj_count = 0

    for path in sorted(LEARN_DIR.glob("*.learning.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        for s in doc.get("sugyot", []):
            for st in (s.get("argumentFlow") or []):
                refs = st.get("sourceRefs")
                if not refs:
                    null_or_empty += 1
                    continue
                for r in refs:
                    if isinstance(r, str):
                        shapes["string"] += 1
                        str_count += 1
                    elif isinstance(r, dict):
                        shapes["object"] += 1
                        obj_count += 1
                        obj_keysets[tuple(sorted(r.keys()))] += 1
                        if "sourceType" in r:
                            sourcetype_values[r.get("sourceType")] += 1
                        else:
                            missing_sourcetype += 1
                    else:
                        shapes[f"other:{type(r).__name__}"] += 1

    # classification via the canonical validator (single source of truth)
    counts, findings = vsr.run(sorted(LEARN_DIR.glob("*.learning.json")))

    return {
        "shapeCounts": dict(shapes),
        "objectKeySets": {" + ".join(k): v for k, v in obj_keysets.items()},
        "sourceTypeValues": dict(sourcetype_values),
        "missingSourceTypeOnObjectRefs": missing_sourcetype,
        "stepsWithNullOrEmptySourceRefs": null_or_empty,
        "totalStringRefs": str_count,
        "totalObjectRefs": obj_count,
        "totalRefs": str_count + obj_count,
        "classification": dict(counts),
        "soundTotal": counts["OK"] + counts["STRING_RESOLVABLE"],
        "defectiveTotal": sum(counts[c] for c in vsr.DEFECT_CLASSES),
        "mechanicallyRepairable": counts["OBJECT_DANGLING_REPAIRABLE"],
        "judgmentRequired": counts["OBJECT_DANGLING_AMBIGUOUS"] + counts["OBJECT_COORDINATE_CONFLICT"],
    }


def consumers():
    """Grep-based census of what reads argumentFlow.type and sourceRefs.
    Read-only; just documents current consumers for the inventory."""
    def grep(pattern, roots):
        hits = []
        for root in roots:
            for f in Path(root).rglob("*"):
                if f.suffix not in (".js", ".jsx", ".py", ".mjs"):
                    continue
                if "node_modules" in f.parts or "dist" in f.parts:
                    continue
                if "assets/learning" in str(f):
                    continue
                try:
                    text = f.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                if pattern in text:
                    hits.append(str(f.relative_to(REPO)))
        return sorted(set(hits))

    return {
        "argumentFlowTypeConsumers": grep("step.type", [REPO]),
        "sourceRefsConsumers": grep("sourceRefs", [REPO]),
    }


def generated_parity():
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_generated_freshness.py")],
        cwd=ROOT, capture_output=True, text=True)
    return {"exitCode": r.returncode, "output": (r.stdout + r.stderr).strip()}


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    af = argumentflow_inventory()
    sr = sourcerefs_inventory()
    cons = consumers()
    gen = generated_parity()

    (DATA_DIR / "argumentflow-inventory.json").write_text(
        json.dumps(af, indent=2, ensure_ascii=False))
    (DATA_DIR / "sourcerefs-shapes.json").write_text(
        json.dumps(sr, indent=2, ensure_ascii=False))
    (DATA_DIR / "phase2-consumers.json").write_text(
        json.dumps(cons, indent=2, ensure_ascii=False))

    print("=== argumentFlow ===")
    print(f"  sugyot: {af['sugyotTotal']}")
    print(f"  steps: {af['argumentFlowStepsTotal']}")
    print(f"  distinct type values: {af['distinctTypeValues']}")
    print(f"  malformed/non-string/empty: "
          f"{af['malformedTypeCount']}/{af['nonStringTypeCount']}/{af['emptyTypeCount']}")
    print(f"  in canonical 13: {af['stepsInCanonical13']}")
    print(f"  outside canonical 13: {af['stepsOutsideCanonical13']} "
          f"({af['distinctValuesOutsideCanonical13']} distinct values)")

    print("\n=== sourceRefs ===")
    print(f"  total refs: {sr['totalRefs']} (string {sr['totalStringRefs']}, "
          f"object {sr['totalObjectRefs']})")
    print(f"  object key-sets: {sr['objectKeySets']}")
    print(f"  sourceType values: {sr['sourceTypeValues']}")
    print(f"  missing sourceType: {sr['missingSourceTypeOnObjectRefs']}")
    print(f"  sound: {sr['soundTotal']}  defective: {sr['defectiveTotal']}")
    print(f"    mechanically repairable: {sr['mechanicallyRepairable']}")
    print(f"    judgment required: {sr['judgmentRequired']}")

    print("\n=== consumers ===")
    print("  argumentFlow.type:", cons["argumentFlowTypeConsumers"])
    print("  sourceRefs:", cons["sourceRefsConsumers"])

    print("\n=== generated/source parity ===")
    print(" ", gen["output"])

    print(f"\nWrote {DATA_DIR / 'argumentflow-inventory.json'}")
    print(f"Wrote {DATA_DIR / 'sourcerefs-shapes.json'}")
    print(f"Wrote {DATA_DIR / 'phase2-consumers.json'}")


if __name__ == "__main__":
    main()
