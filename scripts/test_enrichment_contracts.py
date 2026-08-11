#!/usr/bin/env python3
"""test_enrichment_contracts.py - unit tests for the enrichment contract gate.

Exercises clean, invalid, baseline, regression and target-repair cases against
synthetic module fixtures, so no real corpus data is required or touched.

Run from repo root:
  python3 scripts/test_enrichment_contracts.py
"""
import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_enrichment_contracts as V  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    print("  %s %s%s" % ("ok  " if cond else "FAIL", name, "" if cond else " (%s)" % detail))
    if not cond:
        FAILED.append(name)


def sugya(sid, **over):
    base = {
        "id": sid,
        "display": {"title": "T", "hint": "Why does the mishna say this?"},
        "finalRuling": "The halakha follows Rabbi Yehuda.",
        "requiresUnderstanding": [],
        "prerequisiteKnowledge": ["Basic familiarity with the Temple service."],
        "topicTags": ["kohen-gadol", "yom-kippur"],
        "visualizableElements": [{"item": "The lottery of the two goats", "type": "action"}],
        "difficulty": "intro",
    }
    base.update(over)
    return base


def content(*sugyot):
    return {"2a": {"daf": "2a", "summary": "s", "sugyot": list(sugyot)}}


def rules(daf_content):
    v, _d = V.collect_violations(daf_content)
    return {k for k, ids in v.items() if ids}


# ---- 1. a fully compliant sugya produces no violations ----------------------
clean = content(sugya("yoma-002a-s01"))
check("1. clean fixture yields zero violations", rules(clean) == set(), rules(clean))

# ---- 2. each contract rule fires on its own defect --------------------------
cases = [
    ("hint_trailing_ellipsis", {"display": {"hint": "What is the reason for..."}}),
    ("hint_not_a_question", {"display": {"hint": "The Gemara derives the bathing prohibition."}}),
    ("finalRuling_not_string", {"finalRuling": {"ruling": "x", "basis": "y"}}),
    ("finalRuling_equals_hint", {"display": {"hint": "Why is the measure a large date?"},
                                 "finalRuling": "Why is the measure a large date?"}),
    ("finalRuling_prefix_of_hint",
     {"display": {"hint": "The Gemara asks whether refraining from bathing counts as affliction here?"},
      "finalRuling": "The Gemara asks whether refraining from bathing counts"}),
    ("finalRuling_unterminated",
     {"finalRuling": "The halakha follows Rabbi Yehuda and the measure is set at a large date"}),
    ("requiresUnderstanding_prose", {"requiresUnderstanding": ["Tvul yom: immersed today"]}),
    ("requiresUnderstanding_unresolved_id", {"requiresUnderstanding": ["yoma-099a-s09"]}),
    ("prerequisiteKnowledge_contains_sugya_id", {"prerequisiteKnowledge": ["yoma-002a-s01"]}),
    ("prerequisiteKnowledge_duplicate", {"prerequisiteKnowledge": ["Same note.", "Same note."]}),
    ("topicTags_invalid_slug", {"topicTags": ["Kohen-Gadol"]}),
    ("topicTags_duplicate", {"topicTags": ["kohen-gadol", "kohen-gadol"]}),
    ("visualizableElements_bare_value", {"visualizableElements": ["a bare string"]}),
    ("visualizableElements_missing_item", {"visualizableElements": [{"name": "x", "type": "y"}]}),
    ("visualizableElements_legacy_key", {"visualizableElements": [{"item": "x", "description": "y"}]}),
    ("visualizableElements_unknown_key", {"visualizableElements": [{"item": "x", "bogus": 1}]}),
    ("visualizableElements_priority_not_numeric",
     {"visualizableElements": [{"item": "x", "priority": "high"}]}),
    ("legacy_concepts_present", {"concepts": {"halachic": ["x"]}}),
    ("difficulty_invalid_enum", {"difficulty": "introductory"}),
]
for rule, over in cases:
    got = rules(content(sugya("yoma-002a-s01", **over)))
    check("2.%s fires" % rule, rule in got, "got %s" % sorted(got))

# ---- 3. requiresUnderstanding accepts a genuine resolving id ----------------
two = content(sugya("yoma-002a-s01", requiresUnderstanding=["yoma-002a-s02"]),
              sugya("yoma-002a-s02"))
check("3. resolving sugya id in requiresUnderstanding is legal", rules(two) == set(), rules(two))

# ---- 4. baseline / regression / ratchet behaviour ---------------------------
def run_gate(daf_content, baseline, targets=()):
    """Drive the gate's comparison logic directly against a synthetic baseline."""
    v, _ = V.collect_violations(daf_content)
    base_v = {k: set(x) for k, x in baseline.items()}
    problems = []
    for rule in sorted(set(list(v.keys()) + list(base_v.keys()))):
        now, was = set(v.get(rule, [])), base_v.get(rule, set())
        if now - was:
            problems.append("new:%s" % rule)
        if len(now) > len(was):
            problems.append("rose:%s" % rule)
    for sid in targets:
        if any(sid in ids for ids in v.values()):
            problems.append("target:%s" % sid)
    return problems


dirty = content(sugya("yoma-002a-s01", difficulty="introductory"))
frozen = {"difficulty_invalid_enum": ["yoma-002a-s01"]}
check("4a. known debt inside the baseline passes", run_gate(dirty, frozen) == [],
      run_gate(dirty, frozen))

new_debt = content(sugya("yoma-002a-s01", difficulty="introductory"),
                   sugya("yoma-002a-s02", difficulty="introductory"))
check("4b. a NEW violating sugya id is rejected",
      any(p.startswith("new:") for p in run_gate(new_debt, frozen)))
check("4c. a rising count is rejected",
      any(p.startswith("rose:") for p in run_gate(new_debt, frozen)))

repaired = content(sugya("yoma-002a-s01"))
check("4d. a repaired corpus passes the ratchet", run_gate(repaired, frozen) == [],
      run_gate(repaired, frozen))

# ---- 5. target-clean enforcement -------------------------------------------
check("5a. an unrepaired target fails target-clean",
      any(p == "target:yoma-002a-s01" for p in run_gate(dirty, frozen, targets=["yoma-002a-s01"])))
check("5b. a repaired target passes target-clean",
      run_gate(repaired, frozen, targets=["yoma-002a-s01"]) == [])

# ---- 6. the committed baseline is internally consistent --------------------
base = json.loads((ROOT / "scripts/baselines/enrichment_contract_debt.json").read_text())
check("6a. baseline counts match its own id lists",
      all(base["counts"][k] == len(v) for k, v in base["violations"].items()))
check("6b. baseline fingerprint matches its violations",
      base["fingerprint"] == V.fingerprint(base["violations"]))
check("6c. every baseline rule id is produced by the current rule set",
      set(base["violations"]) <= set(rules(content(sugya("yoma-002a-s01", **{
          "display": {"hint": "x..."}, "finalRuling": {"a": 1},
          "requiresUnderstanding": ["prose"], "topicTags": ["Bad Tag"],
          "visualizableElements": ["bare"], "concepts": {"x": []},
          "difficulty": "introductory"})))) | set(base["violations"]),
      "rule ids drifted")

# ---- 7. the three new task types reject out-of-scope paths -----------------
REG = json.loads((ROOT / "scripts/worker_task_types.json").read_text())["taskTypes"]


def owns(task, path):
    """Is path reachable (mutable, flagMutable or deleteOnly) for this task type?"""
    js = REG[task].get("jsonScope") or {}
    reach = list(js.get("mutable") or []) + list(js.get("deleteOnly") or [])
    for _flag, ps in (js.get("flagMutable") or {}).items():
        reach += list(ps)
    for owner in reach:
        if owner == path or path.startswith(owner + ".") or path.startswith(owner + "["):
            return True
        if owner.endswith("[*]"):
            stem = owner[:-3]
            if path.startswith(stem) and (path == stem or path[len(stem):].startswith((".", "[*]"))):
                return True
    return False


OUT_OF_SCOPE = [
    "sugyot[*].lines[*].he", "sugyot[*].lines[*].en", "sugyot[*].lines[*].en_lit",
    "sugyot[*].lineRange", "sugyot[*].id", "sugyot[*].sugyaNumber",
    "sugyot[*].argumentFlow[*]", "sugyot[*].misconceptions[*]", "sugyot[*].quizSeeds[*]",
    "rashiTranslations[*].he", "rashiTranslations[*].linkedGemaraLineIds",
]
for task in ("legacy-concepts-purge", "enrichment-schema-migration",
             "audited-sugya-enrichment-repair"):
    leaked = [p for p in OUT_OF_SCOPE if owns(task, p)]
    check("7. %s rejects every out-of-scope path" % task, not leaked, "reachable: %s" % leaked)

check("7a. legacy-concepts-purge reaches ONLY sugyot[*].concepts",
      owns("legacy-concepts-purge", "sugyot[*].concepts")
      and not owns("legacy-concepts-purge", "sugyot[*].display.hint")
      and not owns("legacy-concepts-purge", "sugyot[*].finalRuling"))
check("7b. legacy-concepts-purge is delete-only (no mutable paths)",
      (REG["legacy-concepts-purge"]["jsonScope"].get("mutable") or []) == [])
check("7c. enrichment-schema-migration cannot touch display, learning or finalRuling",
      not owns("enrichment-schema-migration", "sugyot[*].display.hint")
      and not owns("enrichment-schema-migration", "sugyot[*].learning.coreMove")
      and not owns("enrichment-schema-migration", "sugyot[*].finalRuling"))
check("7d. enrichment-schema-migration reaches its authorized migration paths",
      all(owns("enrichment-schema-migration", p) for p in
          ("sugyot[*].requiresUnderstanding[*]", "sugyot[*].prerequisiteKnowledge[*]",
           "sugyot[*].visualizableElements[*]", "sugyot[*].difficulty")))
check("7e. audited-sugya-enrichment-repair reaches its authorized repair paths",
      all(owns("audited-sugya-enrichment-repair", p) for p in
          ("summary", "sugyot[*].display.hint", "sugyot[*].learning.takeaway.text",
           "sugyot[*].finalRuling", "sugyot[*].topicTags[*]",
           "sugyot[*].visualizableElements[*]", "sugyot[*].prerequisiteKnowledge[*]")))
check("7f. audited-sugya-enrichment-repair cannot recreate the removed concepts field",
      not owns("audited-sugya-enrichment-repair", "sugyot[*].concepts"))
check("7g. takeaway.type and alternateAngles stay behind their authorization flags",
      REG["audited-sugya-enrichment-repair"]["jsonScope"]["flagMutable"].get("authorizeTakeawayType")
      == ["sugyot[*].learning.takeaway.type"]
      and REG["audited-sugya-enrichment-repair"]["jsonScope"]["flagMutable"].get("authorizeAlternateAngles")
      == ["sugyot[*].alternateAngles"])
check("7h. audited-sugya-enrichment-repair requires independent review",
      REG["audited-sugya-enrichment-repair"].get("independentReviewRequired") is True
      and REG["audited-sugya-enrichment-repair"].get("maxBatch") == 1)

if FAILED:
    print("\n%d check(s) failed: %s" % (len(FAILED), FAILED))
    sys.exit(1)
print("\nAll enrichment-contract checks passed.")
