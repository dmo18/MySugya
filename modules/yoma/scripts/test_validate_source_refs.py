#!/usr/bin/env python3
"""
test_validate_source_refs.py - unit tests for the sourceRefs integrity
classifier and the dry-run migration preview.

Runs against synthetic fixtures so each defect class is exercised
deliberately, plus a small number of corpus-level assertions that would
catch the classifier silently drifting away from the real data.

Run: cd modules/yoma && python3 scripts/test_validate_source_refs.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import validate_source_refs as vsr
import preview_source_refs_migration as pre

FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}{(' - ' + detail) if detail else ''}")
        FAILURES.append(name)


def sugya(sid, daf, lines, steps):
    """Build a synthetic sugya. lines is [(vilnaLine, sefariaRef)];
    steps is [[ref, ...]]."""
    return {
        "id": sid, "_daf": daf,
        "lines": [{"vilnaLine": vl, "sefariaRef": sr} for vl, sr in lines],
        "argumentFlow": [{"id": f"step-{i+1:02d}", "sourceRefs": refs}
                         for i, refs in enumerate(steps)],
    }


def classes(sugyot, daf="10a"):
    counts, findings = vsr.classify_daf(daf, sugyot)
    return counts, findings


# ---------------------------------------------------------------- derivation
print("line-id derivation")

s = sugya("s1", "2a", [(1, "Yoma.2a.1"), (4, "Yoma.2a.2")], [])
ids = [l["id"] for l in vsr.derive_line_ids([s])]
check("pads daf and vilna line", ids == ["yoma-002a-l01", "yoma-002a-l04"], str(ids))

s = sugya("s1", "3a", [(1, "Yoma.3a.1"), (1, "Yoma.3a.2"), (5, "Yoma.3a.3")], [])
ids = [l["id"] for l in vsr.derive_line_ids([s])]
check("suffixes repeated vilna lines",
      ids == ["yoma-003a-l01a", "yoma-003a-l01b", "yoma-003a-l05"], str(ids))

s = sugya("s1", "100b", [(7, "Yoma.100b.1")], [])
check("three-digit daf needs no extra padding",
      vsr.derive_line_ids([s])[0]["id"] == "yoma-100b-l07")

# derivation must match the real generated bundle
ok, msg = vsr.verify_line_id_derivation()
check("derivation reproduces learning_data.js", ok, msg)

# ---------------------------------------------------------------- intervals
print("\nanchor intervals")

t = vsr.build_anchor_table(vsr.derive_line_ids(
    [sugya("s1", "10a", [(1, "r1"), (4, "r2"), (9, "r3")], [])]))
check("interval runs to the next line", [(a["start"], a["end"]) for a in t[:2]] ==
      [(1, 4), (4, 9)], str([(a["start"], a["end"]) for a in t]))
check("last interval is open-ended", t[-1]["end"] == vsr.VILNA_CEILING)

t = vsr.build_anchor_table(vsr.derive_line_ids(
    [sugya("s1", "10a", [(1, "r1"), (1, "r2"), (6, "r3")], [])]))
check("split sub-lines share one interval, not an empty one",
      (t[0]["start"], t[0]["end"]) == (1, 6) and (t[1]["start"], t[1]["end"]) == (1, 6),
      str([(a["start"], a["end"]) for a in t]))

# ---------------------------------------------------------------- string refs
print("\nstring refs")

base = [(1, "Yoma.10a.1"), (4, "Yoma.10a.2"), (9, "Yoma.10a.3")]
c, _ = classes([sugya("s1", "10a", base, [["Yoma.10a.2"]])])
check("resolvable string ref", c["STRING_RESOLVABLE"] == 1, str(dict(c)))

c, _ = classes([sugya("s1", "10a", base, [["Yoma.10a.99"]])])
check("string ref with no matching segment", c["STRING_UNRESOLVABLE"] == 1, str(dict(c)))

c, _ = classes([sugya("s1", "10a", base, [["Yoma.11b.1"]])])
check("string ref naming another daf", c["STRING_CROSS_DAF"] == 1, str(dict(c)))

c, _ = classes([sugya("s1", "10a", base, [["Berakhot.2a.1"]])])
check("malformed string ref", c["STRING_MALFORMED"] == 1, str(dict(c)))

# two lines sharing one sefariaRef would make a string ref ambiguous
c, _ = classes([sugya("s1", "10a", [(1, "Yoma.10a.1"), (4, "Yoma.10a.1")],
                      [["Yoma.10a.1"]])])
check("string ref matching two lines is ambiguous, not resolvable",
      c["STRING_AMBIGUOUS"] == 1, str(dict(c)))

# ---------------------------------------------------------------- object refs
print("\nobject refs")

def oref(line_id, vilna, **kw):
    return {"sourceType": "gemara", "lineId": line_id, "vilnaLine": vilna, **kw}

c, _ = classes([sugya("s1", "10a", base, [[oref("yoma-010a-l04", 4)]])])
check("vilnaLine on its own line id is sound", c["OK"] == 1, str(dict(c)))

c, _ = classes([sugya("s1", "10a", base, [[oref("yoma-010a-l04", 6)]])])
check("vilnaLine inside its line id's interval is sound", c["OK"] == 1, str(dict(c)))

c, f = classes([sugya("s1", "10a", base, [[oref("yoma-10a-l04", 4)]])])
check("unpadded daf in lineId is a repairable dangling ref",
      c["OBJECT_DANGLING_REPAIRABLE"] == 1 and f[0]["wouldBecome"] == "yoma-010a-l04",
      str(dict(c)))

c, f = classes([sugya("s1", "10a", base, [[oref("yoma-010a-l02", 4)]])])
check("sequential-index lineId is repaired via its vilnaLine",
      c["OBJECT_DANGLING_REPAIRABLE"] == 1 and f[0]["wouldBecome"] == "yoma-010a-l04",
      str(dict(c)))

split = [(1, "Yoma.10a.1"), (1, "Yoma.10a.2"), (6, "Yoma.10a.3")]
c, f = classes([sugya("s1", "10a", split, [[oref("yoma-010a-l01", 1)]])])
check("dangling ref over a split line is ambiguous, never guessed",
      c["OBJECT_DANGLING_AMBIGUOUS"] == 1 and
      f[0]["candidates"] == ["yoma-010a-l01a", "yoma-010a-l01b"], str(dict(c)))

c, f = classes([sugya("s1", "10a", base, [[oref("yoma-010a-l01", 9)]])])
check("lineId and vilnaLine naming different real lines is a conflict",
      c["OBJECT_COORDINATE_CONFLICT"] == 1 and
      f[0]["vilnaLineResolvesTo"] == ["yoma-010a-l09"], str(dict(c)))

c, _ = classes([sugya("s1", "10a", base,
                      [[{"sourceType": "gemara", "lineId": "yoma-010a-l04"}]])])
check("object ref without vilnaLine", c["OBJECT_NO_VILNALINE"] == 1, str(dict(c)))

c, f = classes([sugya("s1", "10a", base, [[oref("yoma-010a-l04", 4, sourceType="talmud")]])])
check("sourceType outside the legal set is flagged even with sound geometry",
      c["OBJECT_SOURCETYPE_INVALID"] == 1 and f[0]["legalValues"] == ["gemara", "mishnah", "unknown"],
      str(dict(c)))

c, _ = classes([sugya("s1", "10a", base, [[oref("yoma-010a-l04", 4, sourceType="mishnah")]])])
check("legal sourceType 'mishnah' passes", c["OK"] == 1, str(dict(c)))

c, _ = classes([sugya("s1", "10a", base, [[oref("yoma-010a-l04", 4, sourceType="unknown")]])])
check("the contract's explicit 'unknown' sourceType is legal",
      c["OK"] == 1, str(dict(c)))

c, _ = classes([sugya("s1", "10a", base, [[42]])])
check("ref that is neither string nor object", c["REF_NOT_STRING_OR_OBJECT"] == 1,
      str(dict(c)))

c, _ = classes([sugya("s1", "10a", base, [[]])])
check("empty sourceRefs contributes nothing", sum(c.values()) == 0, str(dict(c)))

# ---------------------------------------------------------------- preview
print("\nmigration preview")

p, b, st = pre.plan_for_daf("10a", [sugya("s1", "10a", base, [[oref("yoma-10a-l04", 4)]])])
check("repairable ref yields exactly one proposal", len(p) == 1 and not b, f"{len(p)},{len(b)}")
check("proposal only changes lineId",
      p[0]["after"]["lineId"] == "yoma-010a-l04" and
      p[0]["after"]["vilnaLine"] == p[0]["before"]["vilnaLine"] and
      p[0]["after"]["sourceType"] == p[0]["before"]["sourceType"], str(p[0]["after"]))
check("proposal carries evidence", bool(p[0]["evidence"]))

p, b, st = pre.plan_for_daf("10a", [sugya("s1", "10a", base, [["Yoma.10a.2"]])])
check("string ref is blocked, never converted by inventing sourceType",
      not p and len(b) == 1 and b[0]["undeterminable"] == ["sourceType"], str(b))
check("blocked string ref still reports what IS derivable",
      b[0]["derivable"]["lineId"] == "yoma-010a-l04", str(b))

p, b, st = pre.plan_for_daf("10a", [sugya("s1", "10a", split, [[oref("yoma-010a-l01", 1)]])])
check("ambiguous split ref is blocked with its candidates",
      not p and len(b) == 1 and len(b[0]["candidates"]) == 2, str(b))

p, b, st = pre.plan_for_daf("10a", [sugya("s1", "10a", base, [[oref("yoma-010a-l01", 9)]])])
check("coordinate conflict is blocked, not silently resolved",
      not p and len(b) == 1 and "disagree" in b[0]["reason"], str(b))

p, b, st = pre.plan_for_daf("10a", [sugya("s1", "10a", base, [[oref("yoma-010a-l04", 4)]])])
check("already-canonical ref produces neither proposal nor block",
      not p and not b and st["already_canonical"] == 1, str(dict(st)))

# losslessness must actually fail when an invariant is broken
good = [{"kind": "dangling-lineid-repair", "evidence": "x",
         "before": {"sourceType": "gemara", "lineId": "a", "vilnaLine": 4},
         "after": {"sourceType": "gemara", "lineId": "b", "vilnaLine": 4}}]
check("losslessness passes a clean proposal set",
      all(ok for _, ok, _ in pre.losslessness_report(good)))

bad = [{"kind": "dangling-lineid-repair", "evidence": "x",
        "before": {"sourceType": "gemara", "lineId": "a", "vilnaLine": 4},
        "after": {"sourceType": "gemara", "lineId": "b", "vilnaLine": 9}}]
check("losslessness catches a moved vilnaLine",
      not all(ok for _, ok, _ in pre.losslessness_report(bad)))

bad = [{"kind": "dangling-lineid-repair", "evidence": "x",
        "before": {"sourceType": "gemara", "lineId": "a", "vilnaLine": 4, "note": "n"},
        "after": {"sourceType": "gemara", "lineId": "b", "vilnaLine": 4}}]
check("losslessness catches a dropped note",
      not all(ok for _, ok, _ in pre.losslessness_report(bad)))

# ---------------------------------------------------------------- corpus
print("\ncorpus-level invariants")

paths = sorted(vsr.LEARN_DIR.glob("*.learning.json"))
counts, findings = vsr.run(paths)
total = sum(counts.values())
check("every daf is classified", len(paths) == 173, str(len(paths)))
check("no ref escapes classification",
      total == counts["OK"] + sum(counts[c] for c in vsr.DEFECT_CLASSES) +
      counts["STRING_RESOLVABLE"], str(dict(counts)))
check("no unresolvable or malformed string refs remain",
      counts["STRING_MALFORMED"] == 0 and counts["STRING_UNRESOLVABLE"] == 0 and
      counts["STRING_AMBIGUOUS"] == 0 and counts["STRING_CROSS_DAF"] == 0,
      str(dict(counts)))
check("no dangling ref lacks a containing anchor",
      counts["OBJECT_DANGLING_NO_ANCHOR"] == 0 and
      counts["OBJECT_DANGLING_NO_VILNA"] == 0, str(dict(counts)))
check("every finding names a real daf, sugya and step",
      all(f["daf"] and f["sugyaId"] and f["stepId"] for f in findings))

props, blocked = [], []
for path in paths:
    daf, sugyot = vsr.load_daf(path)
    p, b, _ = pre.plan_for_daf(daf, sugyot)
    props.extend(p)
    blocked.extend(b)
check("preview proposes exactly the mechanically repairable refs",
      len(props) == counts["OBJECT_DANGLING_REPAIRABLE"], f"{len(props)} vs {counts['OBJECT_DANGLING_REPAIRABLE']}")
check("preview blocks every judgment-class ref plus every string ref",
      len(blocked) == counts["OBJECT_DANGLING_AMBIGUOUS"] +
      counts["OBJECT_COORDINATE_CONFLICT"] + counts["STRING_RESOLVABLE"], str(len(blocked)))
check("corpus proposal set is lossless",
      all(ok for _, ok, _ in pre.losslessness_report(props)),
      str([(c, n) for c, ok, n in pre.losslessness_report(props) if not ok]))

print()
if FAILURES:
    print(f"FAILED: {len(FAILURES)} check(s): {', '.join(FAILURES)}")
    sys.exit(1)
print("All sourceRefs validator and preview checks passed.")
