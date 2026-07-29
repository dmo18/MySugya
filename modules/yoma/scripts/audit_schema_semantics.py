#!/usr/bin/env python3
"""
audit_schema_semantics.py - semantic readiness audit for every sugya.

validate_schema_completeness.py answers "is the field present and non-blank?".
That is necessary but not sufficient: a sugya can carry all required fields and
still be unusable, because a value can be a placeholder, a duplicate of another
sugya's text, too short to mean anything, or outside the controlled vocabulary
the schema and the renderer expect.

This audit answers the harder question, over all 492 sugyot:

  C1  coverage        every required display/learning field present and non-blank
  C2  no placeholders no stub/TODO/TBD markers anywhere in the sugya
  C3  substance       no required field degenerately short
  C4  distinctness    no required field duplicated within a sugya or across sugyot
  C5  takeaway type   takeaway.type inside controlledValues.takeawayType
  C6  step type       argumentFlow[].type inside controlledValues.argumentStepType
  C7  labelled       argumentFlow[].type has a real STEP_META entry in app.jsx,
                      so it renders with a Hebrew term and symbol rather than
                      falling back to its bare name
  C8  quiz shape      question and answer present, question tests a distinction
  C9  quiz distinct   no quiz question repeated across the corpus
  C10 misconceptions  shape correct, no correction duplicated across the corpus

C3 uses an absolute floor, not a percentile. A percentile floor flags roughly
that percentile of the corpus no matter how good the corpus is, so it can never
pass and measures nothing. Observed min/median per field are printed alongside
the result as context.

C8 does not length-check answers. The corpus's shortest answers are correct
terse answers to factual questions ("Two sela.", "R. Yehuda."), so a word floor
would flag good content; it tests the question for generic prompts instead.

C6 and C7 read their vocabularies out of shared/schema_map.js and app.jsx
directly, so this audit cannot drift from what the schema declares or what the
app can actually render.

Offline, no network. Exit 1 on any failing check unless --report.
"""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
REPO = ROOT.parent.parent
LEARN_DIR = ROOT / "assets" / "learning" / "yoma"
SCHEMA_MAP = REPO / "shared" / "schema_map.js"
APP_JSX = REPO / "app.jsx"

REQUIRED_LEARNING = ["learnerQuestion", "coreTension", "coreMove",
                     "ahaMoment", "learningBlocker", "memoryAnchor"]
REQUIRED_DISPLAY = ["title"]

# Deliberately narrow. An earlier draft also matched "to be filled", which
# fired on Yoma 64a's real sentence about the dead goat's slot needing to be
# filled. A placeholder detector that flags correct content is worse than
# none, so this only matches markers that cannot occur in finished prose.
PLACEHOLDER_RE = re.compile(
    r"\b(TBD|TODO|FIXME|XXX|lorem ipsum|coming soon)\b|"
    r"\bplaceholder\b|\bto be (added|written|determined)\b", re.I)

# Absolute degeneracy floor, not a percentile. A percentile floor is
# self-fulfilling: it flags roughly that percentile of the corpus no matter
# how good the corpus is, so it can never pass and measures nothing. This
# asks the real question instead - is the value too short to carry meaning?
# The corpus minimum across all six required fields is 7 words.
MIN_FIELD_WORDS = 5

# Quiz answers are NOT length-checked. The corpus's shortest answers are
# correct terse answers to factual questions ("Two sela.", "R. Yehuda."), and
# a word floor would flag good content. The real standard is that the
# question tests a distinction, which GENERIC_QUESTION_RES tests directly.
GENERIC_QUESTION_RES = [re.compile(p, re.I) for p in [
    r"^what is the (halakha|halacha|ruling|law)\??$",
    r"^what does the gemara (conclude|say|teach|hold)\??$",
    r"^what is the (conclusion|answer|principle|idea)\??$",
    r"^what do we learn( from this| here)?\??$",
    r"^what is the point of this (sugya|passage)\??$",
]]


def read_controlled_values(name):
    """Pull one controlledValues list out of shared/schema_map.js.

    Read from the schema rather than restated here, so widening the schema
    automatically widens this audit and the two can never disagree.
    """
    text = SCHEMA_MAP.read_text(encoding="utf-8")
    m = re.search(name + r"\s*:\s*\[(.*?)\]", text, re.S)
    if not m:
        return None
    return set(re.findall(r'"([^"]+)"', m.group(1)))


def read_step_meta_keys():
    """Pull the STEP_META keys out of app.jsx.

    These are the step types the renderer has a Hebrew term and symbol for.
    Anything else goes through stepMetaFor's fallback and is shown with its
    own humanised name and no Hebrew. That is correct but unpolished: the
    learner sees "Ruling" rather than a term plus symbol. Before VERSION
    15.350 the fallback was STEP_META.question, which actively mislabelled
    these steps as Questions; that part is fixed.
    """
    text = APP_JSX.read_text(encoding="utf-8")
    m = re.search(r"const STEP_META = \{(.*?)\n\};", text, re.S)
    if not m:
        return None
    return set(re.findall(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:", m.group(1), re.M))


def load_sugyot():
    out = []
    for path in sorted(LEARN_DIR.glob("*.learning.json")):
        daf = path.name.replace(".learning.json", "")
        doc = json.loads(path.read_text(encoding="utf-8"))
        for s in doc.get("sugyot", []):
            out.append((daf, s))
    return out


def blank(v):
    return v is None or (isinstance(v, str) and not v.strip())


def field_word_stats(sugyot):
    """min/median word count per required field, reported for context only.

    These are observations, never thresholds: C3 gates on MIN_FIELD_WORDS.
    """
    stats = {}
    for field in REQUIRED_LEARNING:
        counts = sorted(len(((s.get("learning") or {}).get(field) or "").split())
                        for _, s in sugyot)
        stats[field] = {"min": counts[0], "median": counts[len(counts) // 2]}
    return stats


def audit():
    sugyot = load_sugyot()
    step_types = read_controlled_values("argumentStepType")
    takeaway_types = read_controlled_values("takeawayType")
    meta_keys = read_step_meta_keys()
    stats = field_word_stats(sugyot)

    findings = defaultdict(list)

    # cross-sugya duplicate detection
    field_index = defaultdict(lambda: defaultdict(list))
    quiz_index = defaultdict(list)
    misc_index = defaultdict(list)

    for daf, s in sugyot:
        sid = s.get("id")
        where = {"daf": daf, "sugyaId": sid}
        display = s.get("display") or {}
        learning = s.get("learning") or {}

        # C1 coverage
        for f in REQUIRED_DISPLAY:
            if blank(display.get(f)):
                findings["C1"].append({**where, "detail": f"missing display.{f}"})
        for f in REQUIRED_LEARNING:
            if blank(learning.get(f)):
                findings["C1"].append({**where, "detail": f"missing learning.{f}"})
        takeaway = learning.get("takeaway")
        if not isinstance(takeaway, dict) or blank(takeaway.get("text")):
            findings["C1"].append({**where, "detail": "missing learning.takeaway.text"})

        # C2 placeholders
        for m in PLACEHOLDER_RE.finditer(json.dumps(s, ensure_ascii=False)):
            findings["C2"].append({**where, "detail": f"placeholder marker {m.group(0)!r}"})

        # C3 substance
        for f in REQUIRED_LEARNING:
            v = learning.get(f) or ""
            n = len(v.split())
            if v and n < MIN_FIELD_WORDS:
                findings["C3"].append({**where,
                                       "detail": f"learning.{f} is {n} words, floor {MIN_FIELD_WORDS}"})

        # C4 distinctness - within sugya
        seen = {}
        for f in REQUIRED_LEARNING:
            v = (learning.get(f) or "").strip()
            if not v:
                continue
            if v in seen:
                findings["C4"].append({**where,
                                       "detail": f"learning.{f} is identical to learning.{seen[v]}"})
            seen[v] = f
            field_index[f][v].append((daf, sid))

        # C5 takeaway type
        if isinstance(takeaway, dict) and takeaway_types:
            t = takeaway.get("type")
            if t not in takeaway_types:
                findings["C5"].append({**where, "detail": f"takeaway.type {t!r} not in controlled values"})

        # C6 / C7 step types
        for st in (s.get("argumentFlow") or []):
            t = st.get("type")
            step_where = {**where, "stepId": st.get("id")}
            if step_types and t not in step_types:
                findings["C6"].append({**step_where, "detail": f"argumentFlow.type {t!r} not in controlled values"})
            if meta_keys and t not in meta_keys:
                findings["C7"].append({**step_where,
                                       "detail": f"argumentFlow.type {t!r} has no STEP_META entry; "
                                                 f"renders with its bare name and no Hebrew term"})

        # C8 quiz shape
        for i, q in enumerate(s.get("quizSeeds") or []):
            if not isinstance(q, dict):
                findings["C8"].append({**where, "detail": f"quizSeeds[{i}] is not an object"})
                continue
            if blank(q.get("question")) or blank(q.get("answer")):
                findings["C8"].append({**where, "detail": f"quizSeeds[{i}] missing question or answer"})
                continue
            qtext = (q.get("question") or "").strip()
            if any(g.match(qtext) for g in GENERIC_QUESTION_RES):
                findings["C8"].append({**where,
                                       "detail": f"quizSeeds[{i}] is a generic prompt that tests no "
                                                 f"distinction: {qtext!r}"})
            quiz_index[qtext].append((daf, sid))

        # C10 misconception shape
        for i, mc in enumerate(s.get("misconceptions") or []):
            if not isinstance(mc, dict):
                findings["C10"].append({**where, "detail": f"misconceptions[{i}] is not an object"})
                continue
            if blank(mc.get("misconception")) or blank(mc.get("correction")):
                findings["C10"].append({**where, "detail": f"misconceptions[{i}] incomplete"})
                continue
            misc_index[(mc.get("correction") or "").strip()].append((daf, sid))

    # C4 cross-sugya duplicates
    for f, values in field_index.items():
        for v, locs in values.items():
            if len(locs) > 1:
                findings["C4"].append({
                    "daf": locs[0][0], "sugyaId": locs[0][1],
                    "detail": f"learning.{f} is byte-identical across {len(locs)} sugyot: "
                              f"{', '.join(a + '/' + b for a, b in locs)}"})

    # C9 duplicate quiz questions
    for q, locs in quiz_index.items():
        if len(locs) > 1:
            findings["C9"].append({
                "daf": locs[0][0], "sugyaId": locs[0][1],
                "detail": f"quiz question repeated in {len(locs)} sugyot "
                          f"({', '.join(a + '/' + b for a, b in locs)}): {q[:80]!r}"})

    for c, locs in misc_index.items():
        if len(locs) > 1:
            findings["C10"].append({
                "daf": locs[0][0], "sugyaId": locs[0][1],
                "detail": f"misconception correction repeated in {len(locs)} sugyot "
                          f"({', '.join(a + '/' + b for a, b in locs)})"})

    return sugyot, findings, stats, {
        "argumentStepType": sorted(step_types) if step_types else None,
        "takeawayType": sorted(takeaway_types) if takeaway_types else None,
        "stepMetaKeys": sorted(meta_keys) if meta_keys else None,
    }


CHECKS = [
    ("C1", "coverage: every required display/learning field present"),
    ("C2", "no placeholder or stub markers"),
    ("C3", f"substance: no required field under {MIN_FIELD_WORDS} words"),
    ("C4", "distinctness: no required field duplicated within or across sugyot"),
    ("C5", "takeaway.type inside controlled values"),
    ("C6", "argumentFlow.type inside controlled values"),
    ("C7", "argumentFlow.type has a STEP_META label (Hebrew term + symbol)"),
    ("C8", "quizSeeds shape and non-generic questions"),
    ("C9", "no quiz question repeated across the corpus"),
    ("C10", "misconceptions shape and distinctness"),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--report", action="store_true",
                    help="always exit 0 (status reporting, not gating)")
    ap.add_argument("--check", help="show all findings for one check, e.g. C6")
    args = ap.parse_args()

    sugyot, findings, stats, vocab = audit()
    total = len(sugyot)

    # a sugya is "ready" when it contributes no finding to any check
    bad_sugyot = {(f["daf"], f["sugyaId"])
                  for fs in findings.values() for f in fs}
    ready = total - len(bad_sugyot)

    if args.json:
        print(json.dumps({
            "sugyotTotal": total, "sugyotReady": ready,
            "coverage": f"{ready}/{total}",
            "minFieldWords": MIN_FIELD_WORDS,
            "fieldWordStats": stats, "vocabularies": vocab,
            "checks": [{"id": c, "description": d,
                        "pass": not findings[c], "findings": len(findings[c])}
                       for c, d in CHECKS],
            "findings": {c: findings[c] for c, _ in CHECKS if findings[c]},
        }, indent=2, ensure_ascii=False))
    else:
        print(f"Sugya semantic readiness - {total} sugyot across "
              f"{len(set(d for d, _ in sugyot))} daf\n")
        print(f"  degeneracy floor: {MIN_FIELD_WORDS} words. Observed per field "
              f"(min/median): "
              f"{', '.join(f'{k}={v[chr(109)+chr(105)+chr(110)]}/{v[chr(109)+chr(101)+chr(100)+chr(105)+chr(97)+chr(110)]}' for k, v in stats.items())}\n")
        for c, d in CHECKS:
            n = len(findings[c])
            print(f"  [{'PASS' if not n else 'FAIL'}] {c}  {d}" +
                  ("" if not n else f"  ({n} finding(s))"))
        print(f"\n  sugyot with zero findings : {ready}/{total}")
        print(f"  sugyot with findings      : {len(bad_sugyot)}")

        if args.check:
            fs = findings.get(args.check, [])
            print(f"\n  all {len(fs)} finding(s) for {args.check}:")
            for f in fs:
                step = f" {f['stepId']}" if f.get("stepId") else ""
                print(f"    {f['daf']} {f['sugyaId']}{step}: {f['detail']}")
        else:
            for c, _ in CHECKS:
                if findings[c]:
                    print(f"\n  {c} sample:")
                    for f in findings[c][:3]:
                        step = f" {f['stepId']}" if f.get("stepId") else ""
                        print(f"    {f['daf']} {f['sugyaId']}{step}: {f['detail']}")
            print("\n  Use --check C6 to list every finding for a check.")

    failing = [c for c, _ in CHECKS if findings[c]]
    if failing and not args.report:
        sys.exit(1)


if __name__ == "__main__":
    main()
