#!/usr/bin/env python3
"""
validate_source_refs.py - referential-integrity gate for argumentFlow
sourceRefs.

An argumentFlow step may carry sourceRefs[] anchoring that step to specific
source lines. Two shapes exist in the corpus today:

  string form  "Yoma.<daf>.<segment>"  - a Sefaria segment reference
  object form  {sourceType, lineId, vilnaLine, note?}

The canonical form is the object form. See
docs/reports/source-refs-normalization-plan.md for the full schema, the
current defect inventory, and why normalization is not yet applied.

WHAT THIS CHECKS

The rendered line id space is coarser than Vilna line numbering: a line id
is minted only where a Sefaria segment starts, so one line id covers a
half-open Vilna interval [start, next-start). A ref is referentially sound
when:

  string form  the ref resolves to exactly one line id on its own daf via
               that line's sefariaRef
  object form  lineId exists on the ref's daf, AND vilnaLine falls inside
               that line id's Vilna interval

Line ids are derived here with the same rule build_learning_data.py uses
(zero-padded daf, zero-padded Vilna line, letter suffix when one Vilna line
carries more than one segment), so this runs offline against the enrichment
JSON with no build step and no network.

EXIT BEHAVIOUR

Default (report mode) prints the full classification and exits 0. It is a
reporting tool, not a gate, because the corpus carries a known inventory of
legacy refs that predate the current line-id convention.

--strict exits 1 on any defect. This is the mode a future structural-repair
pass turns on once the backlog in the plan document is cleared. --strict is
deliberately NOT wired into validate:offline:yoma yet; wiring it in before
the backlog is cleared would only produce a red gate nobody can turn green.
"""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
LEARN_DIR = ROOT / "assets" / "learning" / "yoma"

STRING_REF_RE = re.compile(r"^Yoma\.(\d+[ab])\.(\d+)$")
DAF_RE = re.compile(r"^(\d+)([ab])$")
VILNA_CEILING = 10 ** 6


def daf_pad(daf):
    """'2a' -> '002a'. Mirrors build_learning_data.py's daf_pad."""
    m = DAF_RE.match(daf)
    if not m:
        return None
    return f"{int(m.group(1)):03d}{m.group(2)}"


def derive_line_ids(sugyot):
    """Reproduce build_learning_data.py's line-id assignment from the
    enrichment JSON alone.

    The builder mints ids from source_store.js, but it also hard-fails
    unless each sugya's enrichment lines[] has the same length and order as
    its source lines[], so deriving from the enrichment reproduces the same
    ids. verify_line_id_derivation() proves this against the built
    learning_data.js.

    Returns a list of {id, vilnaLine, sefariaRef, sugyaId} in document
    order.
    """
    all_vl = [ln.get("vilnaLine") for s in sugyot for ln in s.get("lines", [])]
    vl_freq = Counter(all_vl)
    vl_seen = {}
    out = []
    for sugya in sugyot:
        for ln in sugya.get("lines", []):
            vl = ln.get("vilnaLine")
            pad = daf_pad(sugya.get("_daf", ""))
            if vl_freq[vl] > 1:
                vl_seen[vl] = vl_seen.get(vl, 0) + 1
                suffix = chr(ord("a") + vl_seen[vl] - 1)
                lid = f"yoma-{pad}-l{vl:02d}{suffix}"
            else:
                lid = f"yoma-{pad}-l{vl:02d}"
            out.append({
                "id": lid,
                "vilnaLine": vl,
                "sefariaRef": ln.get("sefariaRef"),
                "sugyaId": sugya.get("id"),
            })
    return out


def build_anchor_table(lines):
    """Attach each line id's half-open Vilna interval [start, end).

    end is the next line's Vilna number that is strictly greater, so the
    suffixed lines sharing one Vilna number (l01a, l01b, ...) all share that
    number's interval rather than collapsing to an empty range.
    """
    table = []
    for i, ln in enumerate(lines):
        nxt = next(
            (m["vilnaLine"] for m in lines[i + 1:] if m["vilnaLine"] > ln["vilnaLine"]),
            VILNA_CEILING,
        )
        table.append({**ln, "start": ln["vilnaLine"], "end": nxt})
    return table


def load_daf(path):
    """Return (daf, sugyot) with each sugya tagged with its daf."""
    daf = path.name.replace(".learning.json", "")
    doc = json.loads(path.read_text(encoding="utf-8"))
    sugyot = doc.get("sugyot", [])
    for s in sugyot:
        s["_daf"] = daf
    return daf, sugyot


def classify_daf(daf, sugyot):
    """Classify every sourceRefs element on one daf.

    Returns (counts:Counter, findings:list). Each finding is a dict with a
    'class' key; see CLASSES below for the vocabulary.
    """
    anchors = build_anchor_table(derive_line_ids(sugyot))
    by_id = {a["id"]: a for a in anchors}
    by_sefaria = defaultdict(list)
    for a in anchors:
        if a["sefariaRef"]:
            by_sefaria[a["sefariaRef"]].append(a)

    def containing(vl):
        return [a for a in anchors if a["start"] <= vl < a["end"]]

    counts = Counter()
    findings = []

    def add(cls, sugya, step, ref, **extra):
        counts[cls] += 1
        if cls != "OK":
            findings.append({
                "class": cls, "daf": daf, "sugyaId": sugya.get("id"),
                "stepId": step.get("id"), "ref": ref, **extra,
            })

    for sugya in sugyot:
        for step in (sugya.get("argumentFlow") or []):
            for ref in (step.get("sourceRefs") or []):
                if isinstance(ref, str):
                    m = STRING_REF_RE.match(ref)
                    if not m:
                        add("STRING_MALFORMED", sugya, step, ref)
                        continue
                    if m.group(1) != daf:
                        add("STRING_CROSS_DAF", sugya, step, ref)
                        continue
                    hits = by_sefaria.get(ref, [])
                    if len(hits) == 1:
                        add("STRING_RESOLVABLE", sugya, step, ref,
                            resolvesTo=hits[0]["id"])
                    elif len(hits) > 1:
                        add("STRING_AMBIGUOUS", sugya, step, ref,
                            candidates=[h["id"] for h in hits])
                    else:
                        add("STRING_UNRESOLVABLE", sugya, step, ref)
                    continue

                if not isinstance(ref, dict):
                    add("REF_NOT_STRING_OR_OBJECT", sugya, step, repr(ref))
                    continue

                line_id = ref.get("lineId")
                vilna = ref.get("vilnaLine")
                anchor = by_id.get(line_id)

                if anchor is None:
                    if vilna is None:
                        add("OBJECT_DANGLING_NO_VILNA", sugya, step, ref)
                        continue
                    cands = containing(vilna)
                    if len(cands) == 1:
                        add("OBJECT_DANGLING_REPAIRABLE", sugya, step, ref,
                            wouldBecome=cands[0]["id"])
                    elif len(cands) > 1:
                        add("OBJECT_DANGLING_AMBIGUOUS", sugya, step, ref,
                            candidates=[c["id"] for c in cands])
                    else:
                        add("OBJECT_DANGLING_NO_ANCHOR", sugya, step, ref)
                    continue

                if vilna is None:
                    add("OBJECT_NO_VILNALINE", sugya, step, ref)
                elif anchor["start"] <= vilna < anchor["end"]:
                    add("OK", sugya, step, ref)
                else:
                    add("OBJECT_COORDINATE_CONFLICT", sugya, step, ref,
                        lineIdInterval=[anchor["start"], anchor["end"]],
                        vilnaLineResolvesTo=[c["id"] for c in containing(vilna)])

    return counts, findings


# Defect classes that must be empty for --strict to pass. OK and
# STRING_RESOLVABLE are sound; STRING_RESOLVABLE is still listed as a
# migration candidate rather than a defect.
DEFECT_CLASSES = [
    "STRING_MALFORMED", "STRING_CROSS_DAF", "STRING_AMBIGUOUS",
    "STRING_UNRESOLVABLE", "REF_NOT_STRING_OR_OBJECT",
    "OBJECT_DANGLING_NO_VILNA", "OBJECT_DANGLING_REPAIRABLE",
    "OBJECT_DANGLING_AMBIGUOUS", "OBJECT_DANGLING_NO_ANCHOR",
    "OBJECT_NO_VILNALINE", "OBJECT_COORDINATE_CONFLICT",
]

# Defects a migration can settle mechanically from repo data alone.
MECHANICAL_CLASSES = ["OBJECT_DANGLING_REPAIRABLE"]

# Defects that need a human reading the step text against the Gemara,
# because two in-repo coordinates disagree and both name a real line.
JUDGMENT_CLASSES = ["OBJECT_DANGLING_AMBIGUOUS", "OBJECT_COORDINATE_CONFLICT"]


def run(paths):
    counts = Counter()
    findings = []
    for path in paths:
        daf, sugyot = load_daf(path)
        c, f = classify_daf(daf, sugyot)
        counts.update(c)
        findings.extend(f)
    return counts, findings


def verify_line_id_derivation():
    """Prove derive_line_ids reproduces the built learning_data.js ids.

    Reads the ids out of the generated bundle textually (no node), grouped
    by daf, and compares against the derivation. Returns (ok, message).
    """
    bundle = ROOT / "learning_data.js"
    if not bundle.exists():
        return True, "learning_data.js absent; derivation check skipped"
    text = bundle.read_text(encoding="utf-8")
    built = defaultdict(list)
    for m in re.finditer(r'\{ id: "yoma-(\d{3}[ab])-l(\d{2}[a-z]?)"', text):
        built[m.group(1)].append(f"yoma-{m.group(1)}-l{m.group(2)}")

    mismatches = []
    for path in sorted(LEARN_DIR.glob("*.learning.json")):
        daf, sugyot = load_daf(path)
        pad = daf_pad(daf)
        derived = [ln["id"] for ln in derive_line_ids(sugyot)]
        if derived != built.get(pad, []):
            mismatches.append(daf)
    if mismatches:
        return False, f"derivation disagrees with learning_data.js on: {', '.join(mismatches)}"
    total = sum(len(v) for v in built.values())
    return True, f"derivation reproduces all {total} built line ids across {len(built)} daf"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 on any defect (post-backlog gating mode)")
    ap.add_argument("--json", action="store_true", help="emit findings as JSON")
    ap.add_argument("--daf", help="limit to one daf, e.g. 67a")
    ap.add_argument("--class", dest="cls", help="show findings of one class only")
    args = ap.parse_args()

    paths = sorted(LEARN_DIR.glob("*.learning.json"))
    if args.daf:
        paths = [p for p in paths if p.name == f"{args.daf}.learning.json"]
        if not paths:
            sys.exit(f"ERROR: no enrichment file for daf {args.daf}")

    counts, findings = run(paths)
    if args.cls:
        findings = [f for f in findings if f["class"] == args.cls]

    derivation_ok, derivation_msg = verify_line_id_derivation()
    defects = sum(counts[c] for c in DEFECT_CLASSES)
    mechanical = sum(counts[c] for c in MECHANICAL_CLASSES)
    judgment = sum(counts[c] for c in JUDGMENT_CLASSES)
    total = sum(counts.values())

    if args.json:
        print(json.dumps({
            "files": len(paths), "totalRefs": total, "counts": dict(counts),
            "defects": defects, "mechanical": mechanical, "judgment": judgment,
            "derivationOk": derivation_ok, "derivationMessage": derivation_msg,
            "findings": findings,
        }, indent=2, ensure_ascii=False))
    else:
        print(f"sourceRefs referential integrity - {len(paths)} file(s), {total} refs\n")
        print(f"  line-id derivation: {'OK' if derivation_ok else 'FAILED'} - {derivation_msg}\n")
        for cls, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
            mark = "     " if cls in ("OK", "STRING_RESOLVABLE") else "  X  "
            print(f"{mark}{cls}: {n}")
        print(f"\n  sound                     : {counts['OK'] + counts['STRING_RESOLVABLE']}")
        print(f"  defects                   : {defects}")
        print(f"    mechanically repairable : {mechanical}")
        print(f"    needs human judgment    : {judgment}")
        affected = sorted({f["daf"] for f in findings})
        print(f"  daf carrying defects      : {len(affected)}")
        if args.cls and findings:
            print(f"\n  findings for {args.cls}:")
            for f in findings:
                print(f"    {f['daf']} {f['sugyaId']} {f['stepId']}: {f['ref']}")

    if not derivation_ok:
        sys.exit(1)
    if args.strict and defects:
        if not args.json:
            print(f"\nSTRICT: {defects} defect(s). See "
                  f"docs/reports/source-refs-normalization-plan.md.")
        sys.exit(1)
    if not args.json and not args.strict:
        print("\nReport mode: exit 0. Run with --strict to gate on defects.")


if __name__ == "__main__":
    main()
