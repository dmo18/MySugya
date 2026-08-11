#!/usr/bin/env python3
"""test_enrichment_contracts.py - unit tests for the enrichment contract gate.

Exercises clean, invalid, baseline, regression, same-sugya-worsening,
module-isolation and target-repair cases directly against the REAL
production functions the CLI entry point (main()) calls -- collect_violations,
fingerprint_baseline, compare_to_baseline, verify_baseline_integrity -- not a
duplicate simplified reimplementation of the gate logic. A subprocess smoke
test at the end also drives the actual `python3 scripts/
validate_enrichment_contracts.py` CLI end to end against the real committed
Yoma baseline.

Run from repo root:
  python3 scripts/test_enrichment_contracts.py
"""
import json
import pathlib
import subprocess
import sys

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
    v, _d, _o = V.collect_violations(daf_content)
    return {k for k, ids in v.items() if ids}


def make_baseline(violations, occurrences, module="yoma"):
    """Assemble a baseline payload using the REAL fingerprint_baseline
    function, mirroring write_baseline's shape without reimplementing its
    comparison semantics."""
    counts = {k: len(v) for k, v in violations.items()}
    return {
        "schemaVersion": V.SCHEMA_VERSION,
        "module": module,
        "ruleRegistry": sorted(V.RULES),
        "counts": counts,
        "occurrences": occurrences,
        "fingerprint": V.fingerprint_baseline(V.RULES, occurrences),
        "violations": violations,
    }


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
    ("finalRuling_unterminated", {"finalRuling": "Short but no period"}),  # no length threshold
    ("finalRuling_trailing_ellipsis", {"finalRuling": "The ruling trails off..."}),
    ("requiresUnderstanding_not_list", {"requiresUnderstanding": "yoma-002a-s02"}),
    ("requiresUnderstanding_prose", {"requiresUnderstanding": ["Tvul yom: immersed today"]}),
    ("requiresUnderstanding_unresolved_id", {"requiresUnderstanding": ["yoma-099a-s09"]}),
    ("prerequisiteKnowledge_not_list", {"prerequisiteKnowledge": "not a list"}),
    ("prerequisiteKnowledge_contains_sugya_id", {"prerequisiteKnowledge": ["yoma-002a-s01"]}),
    ("prerequisiteKnowledge_duplicate", {"prerequisiteKnowledge": ["Same note.", "Same note."]}),
    ("topicTags_not_list", {"topicTags": ""}),
    ("topicTags_not_list", {"topicTags": {}}),
    ("topicTags_invalid_slug", {"topicTags": ["Kohen-Gadol"]}),
    ("topicTags_duplicate", {"topicTags": ["kohen-gadol", "kohen-gadol"]}),
    ("visualizableElements_not_list", {"visualizableElements": ""}),
    ("visualizableElements_not_list", {"visualizableElements": {}}),
    ("visualizableElements_not_list", {"visualizableElements": 0}),
    ("visualizableElements_bare_value", {"visualizableElements": ["a bare string"]}),
    ("visualizableElements_missing_item", {"visualizableElements": [{"name": "x", "type": "y"}]}),
    ("visualizableElements_legacy_key", {"visualizableElements": [{"item": "x", "description": "y"}]}),
    ("visualizableElements_unknown_key", {"visualizableElements": [{"item": "x", "bogus": 1}]}),
    ("visualizableElements_field_not_string", {"visualizableElements": [{"item": "x", "type": ""}]}),
    ("visualizableElements_field_not_string", {"visualizableElements": [{"item": "x", "label": 5}]}),
    ("visualizableElements_priority_not_numeric",
     {"visualizableElements": [{"item": "x", "priority": "high"}]}),
    ("visualizableElements_priority_not_numeric",
     {"visualizableElements": [{"item": "x", "priority": True}]}),  # bool is not a real numeric
    ("legacy_concepts_present", {"concepts": {"halachic": ["x"]}}),
    ("legacy_concepts_present", {"concepts": None}),   # key presence, not truthiness
    ("legacy_concepts_present", {"concepts": {}}),
    ("legacy_concepts_present", {"concepts": []}),
    ("difficulty_invalid_enum", {"difficulty": "introductory"}),
]
for rule, over in cases:
    got = rules(content(sugya("yoma-002a-s01", **over)))
    check("2.%s fires (%r)" % (rule, over), rule in got, "got %s" % sorted(got))

# ---- 3. requiresUnderstanding accepts a genuine resolving id ----------------
two = content(sugya("yoma-002a-s01", requiresUnderstanding=["yoma-002a-s02"]),
              sugya("yoma-002a-s02"))
check("3. resolving sugya id in requiresUnderstanding is legal", rules(two) == set(), rules(two))

# ---- 3a. every rule in the registry appears with an empty list when clean ---
v_clean, _d, occ_clean = V.collect_violations(clean)
check("3a. every registered rule is present (possibly empty) on a clean corpus",
      set(v_clean.keys()) == set(V.RULES) and all(v == [] for v in v_clean.values()),
      sorted(k for k, v in v_clean.items() if v))
check("3a2. occurrences dict also carries every registered rule",
      set(occ_clean.keys()) == set(V.RULES))

# ---- 4. baseline / regression / ratchet behaviour via the REAL comparator ---
dirty = content(sugya("yoma-002a-s01", difficulty="introductory"))
_, _, dirty_occ = V.collect_violations(dirty)
dirty_v, _, _ = V.collect_violations(dirty)
frozen = make_baseline(dirty_v, dirty_occ)

problems, improved = V.compare_to_baseline(dirty_v, dirty_occ, frozen, [])
check("4a. known debt inside the baseline passes unchanged", problems == [], problems)

new_debt_content = content(sugya("yoma-002a-s01", difficulty="introductory"),
                           sugya("yoma-002a-s02", difficulty="introductory"))
nd_v, _, nd_occ = V.collect_violations(new_debt_content)
problems2, _ = V.compare_to_baseline(nd_v, nd_occ, frozen, [])
check("4b. a NEW violating sugya id is rejected", any("NEW debt" in p for p in problems2), problems2)

repaired = content(sugya("yoma-002a-s01"))
rep_v, _, rep_occ = V.collect_violations(repaired)
problems3, improved3 = V.compare_to_baseline(rep_v, rep_occ, frozen, [])
check("4c. reaching zero for a baselined rule passes", problems3 == [], problems3)
check("4c2. reaching zero prints the exact decrease", any("difficulty_invalid_enum" in m for m in improved3),
      improved3)

# ---- 4d. RULE-REGISTRY test: a rule the baseline references but the code no
#          longer produces is rejected, even though it is otherwise silent ---
ghost_baseline = make_baseline(
    {"a_rule_that_was_deleted": ["yoma-002a-s01"]},
    {"a_rule_that_was_deleted": [{"sugyaId": "yoma-002a-s01", "path": "x", "index": None,
                                  "fingerprint": "deadbeef00000000"}]},
)
problems4, _ = V.compare_to_baseline(rep_v, rep_occ, ghost_baseline, [])
check("4d. deleting a rule implementation fails the gate",
      any("not a currently registered rule" in p for p in problems4), problems4)

# ---- 4e. renaming a rule (no RULE_MIGRATIONS entry) fails identically -------
renamed_baseline = make_baseline(
    {"difficulty_invalid_enum_OLD_NAME": ["yoma-002a-s01"]},
    {"difficulty_invalid_enum_OLD_NAME": [{"sugyaId": "yoma-002a-s01", "path": "difficulty",
                                           "index": None, "fingerprint": "cafef00d00000000"}]},
)
problems5, _ = V.compare_to_baseline(rep_v, rep_occ, renamed_baseline, [])
check("4e. renaming a rule without a reviewed RULE_MIGRATIONS entry fails",
      any("not a currently registered rule" in p for p in problems5), problems5)

# ---- 4f. an explicit, reviewed RULE_MIGRATIONS entry is honored -------------
saved_migrations = dict(V.RULE_MIGRATIONS)
try:
    V.RULE_MIGRATIONS.clear()
    V.RULE_MIGRATIONS["difficulty_invalid_enum_OLD_NAME"] = "difficulty_invalid_enum"
    problems6, _ = V.compare_to_baseline(dirty_v, dirty_occ, renamed_baseline, [])
    check("4f. a reviewed RULE_MIGRATIONS rename is honored (no false failure)",
          not any("not a currently registered rule" in p for p in problems6), problems6)
finally:
    V.RULE_MIGRATIONS.clear()
    V.RULE_MIGRATIONS.update(saved_migrations)

# ---- 5. target-clean enforcement -------------------------------------------
problems7, _ = V.compare_to_baseline(dirty_v, dirty_occ, frozen, ["yoma-002a-s01"])
check("5a. an unrepaired target fails target-clean", any(p.startswith("target ") for p in problems7),
      problems7)
problems8, _ = V.compare_to_baseline(rep_v, rep_occ, frozen, ["yoma-002a-s01"])
check("5b. a repaired target passes target-clean", problems8 == [], problems8)

# ---- 5c. --rules narrows target-clean to the named rules only --------------
# Target is CLEAN for difficulty but DIRTY for topicTags: a difficulty-scoped
# target-clean check must pass despite the unrelated topicTags debt.
mixed = content(sugya("yoma-002a-s01", difficulty="intro", topicTags=["Bad Tag"]))
mixed_v, _, mixed_occ = V.collect_violations(mixed)
mixed_base = make_baseline(mixed_v, mixed_occ)
p_scoped, _ = V.compare_to_baseline(mixed_v, mixed_occ, mixed_base, ["yoma-002a-s01"],
                                    rules_filter=["difficulty_invalid_enum"])
check("5c. rule-scoped target-clean ignores debt outside the named rules",
      p_scoped == [], p_scoped)
p_unscoped, _ = V.compare_to_baseline(mixed_v, mixed_occ, mixed_base, ["yoma-002a-s01"])
check("5d. unscoped target-clean still sees every rule's debt",
      any(p.startswith("target ") for p in p_unscoped), p_unscoped)

# ---- 6. SAME-SUGYA WORSENING: occurrence-level ratchet ----------------------
one_bad_tag = content(sugya("yoma-002a-s01", topicTags=["Bad Tag"]))
ob_v, _, ob_occ = V.collect_violations(one_bad_tag)
tag_baseline = make_baseline(ob_v, ob_occ)

two_bad_tags = content(sugya("yoma-002a-s01", topicTags=["Bad Tag", "Also Bad"]))
tb_v, _, tb_occ = V.collect_violations(two_bad_tags)
p_grow, _ = V.compare_to_baseline(tb_v, tb_occ, tag_baseline, [])
check("6a. adding a SECOND invalid topic tag to an already-dirty sugya fails",
      any("count rose" in p for p in p_grow), p_grow)

swapped_tag = content(sugya("yoma-002a-s01", topicTags=["Totally Different Bad Tag"]))
sw_v, _, sw_occ = V.collect_violations(swapped_tag)
p_swap, _ = V.compare_to_baseline(sw_v, sw_occ, tag_baseline, [])
check("6b. swapping one invalid tag for a DIFFERENT invalid tag (same count) fails",
      any("same-sugya worsening" in p for p in p_swap), p_swap)

zero_tags = content(sugya("yoma-002a-s01", topicTags=[]))
zt_v, _, zt_occ = V.collect_violations(zero_tags)
p_zero, imp_zero = V.compare_to_baseline(zt_v, zt_occ, tag_baseline, [])
check("6c. removing the invalid tag entirely passes", p_zero == [], p_zero)
check("6c2. full repair prints the exact decrease", any("-> 0" in m for m in imp_zero), imp_zero)

one_bad_ve = content(sugya("yoma-002a-s01",
                           visualizableElements=[{"item": "x", "priority": "bad"}]))
ov_v, _, ov_occ = V.collect_violations(one_bad_ve)
ve_baseline = make_baseline(ov_v, ov_occ)
two_bad_ve = content(sugya("yoma-002a-s01",
                           visualizableElements=[{"item": "x", "priority": "bad"},
                                                 {"item": "y", "priority": "also-bad"}]))
tv_v, _, tv_occ = V.collect_violations(two_bad_ve)
p_ve_grow, _ = V.compare_to_baseline(tv_v, tv_occ, ve_baseline, [])
check("6d. adding ANOTHER invalid visualizableElement to an already-dirty sugya fails",
      any("count rose" in p for p in p_ve_grow), p_ve_grow)

fixed_ve = content(sugya("yoma-002a-s01", visualizableElements=[{"item": "x"}]))
fv_v, _, fv_occ = V.collect_violations(fixed_ve)
p_ve_fix, imp_ve_fix = V.compare_to_baseline(fv_v, fv_occ, ve_baseline, [])
check("6e. removing the only violation in a multi-field-dirty sugya passes",
      p_ve_fix == [], p_ve_fix)

# ---- 7. baseline integrity verification -------------------------------------
ok_base = make_baseline(dirty_v, dirty_occ)
check("7a. an internally-consistent baseline passes integrity verification",
      V.verify_baseline_integrity(ok_base, "yoma") == [])

tampered_counts = json.loads(json.dumps(ok_base))
tampered_counts["counts"] = {k: v + 1 for k, v in tampered_counts["counts"].items()}
check("7b. a baseline whose counts disagree with its own occurrences fails integrity",
      len(V.verify_baseline_integrity(tampered_counts, "yoma")) > 0)

tampered_fp = json.loads(json.dumps(ok_base))
tampered_fp["fingerprint"] = "0" * 64
check("7c. a baseline whose fingerprint disagrees with its own payload fails integrity",
      len(V.verify_baseline_integrity(tampered_fp, "yoma")) > 0)

# ---- 8. MODULE-BASELINE ISOLATION -------------------------------------------
check("8a. a module cannot silently reuse another module's baseline",
      any("does not match" in p for p in V.verify_baseline_integrity(ok_base, "some-other-module")))
check("8b. the baseline path is unambiguous and module-specific",
      V.baseline_path("yoma").name == "yoma_enrichment_contract_debt.json"
      and V.baseline_path("shabbat").name == "shabbat_enrichment_contract_debt.json"
      and V.baseline_path("yoma") != V.baseline_path("shabbat"))

# ---- 9. the committed Yoma baseline is internally consistent ---------------
committed = json.loads(V.baseline_path("yoma").read_text())
check("9a. committed baseline passes its own integrity verification",
      V.verify_baseline_integrity(committed, "yoma") == [],
      V.verify_baseline_integrity(committed, "yoma"))
check("9b. committed baseline's ruleRegistry equals the current RULES registry",
      set(committed["ruleRegistry"]) == set(V.RULES),
      sorted(set(committed["ruleRegistry"]) ^ set(V.RULES)))

# ---- 10. the three enrichment task types reject out-of-scope paths ---------
REG = json.loads((ROOT / "scripts/worker_task_types.json").read_text())["taskTypes"]


def owns(task, path):
    """Is path reachable (mutable, flagMutable, or deleteOnly) for this task type?"""
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
    check("10. %s rejects every out-of-scope path" % task, not leaked, "reachable: %s" % leaked)

check("10a. legacy-concepts-purge reaches ONLY sugyot[*].concepts (delete-only)",
      owns("legacy-concepts-purge", "sugyot[*].concepts")
      and not owns("legacy-concepts-purge", "sugyot[*].display.hint")
      and not owns("legacy-concepts-purge", "sugyot[*].finalRuling"))
check("10b. legacy-concepts-purge is delete-only (no mutable paths)",
      (REG["legacy-concepts-purge"]["jsonScope"].get("mutable") or []) == []
      and (REG["legacy-concepts-purge"]["jsonScope"].get("deleteOnly") or []) == ["sugyot[*].concepts"])
check("10c. enrichment-schema-migration cannot touch display, learning or finalRuling",
      not owns("enrichment-schema-migration", "sugyot[*].display.hint")
      and not owns("enrichment-schema-migration", "sugyot[*].learning.coreMove")
      and not owns("enrichment-schema-migration", "sugyot[*].finalRuling"))
check("10d. enrichment-schema-migration reaches its authorized migration paths",
      all(owns("enrichment-schema-migration", p) for p in
          ("sugyot[*].requiresUnderstanding[*]", "sugyot[*].prerequisiteKnowledge[*]",
           "sugyot[*].visualizableElements[*]", "sugyot[*].difficulty")))
check("10e. audited-sugya-enrichment-repair reaches its authorized repair paths",
      all(owns("audited-sugya-enrichment-repair", p) for p in
          ("summary", "sugyot[*].display.hint", "sugyot[*].learning.takeaway.text",
           "sugyot[*].finalRuling", "sugyot[*].topicTags[*]",
           "sugyot[*].visualizableElements[*]", "sugyot[*].prerequisiteKnowledge[*]")))
check("10f. audited-sugya-enrichment-repair cannot recreate the removed concepts field",
      not owns("audited-sugya-enrichment-repair", "sugyot[*].concepts"))
check("10g. takeaway.type and alternateAngles stay behind their authorization flags",
      REG["audited-sugya-enrichment-repair"]["jsonScope"]["flagMutable"].get("authorizeTakeawayType")
      == ["sugyot[*].learning.takeaway.type"]
      and REG["audited-sugya-enrichment-repair"]["jsonScope"]["flagMutable"].get("authorizeAlternateAngles")
      == ["sugyot[*].alternateAngles"])
check("10h. audited-sugya-enrichment-repair requires independent review",
      REG["audited-sugya-enrichment-repair"].get("independentReviewRequired") is True
      and REG["audited-sugya-enrichment-repair"].get("maxBatch") == 1)

# ---- 11. real CLI subprocess smoke test against the committed Yoma state ---
r = subprocess.run([sys.executable, "scripts/validate_enrichment_contracts.py", "--module", "yoma"],
                   cwd=str(ROOT), capture_output=True, text=True)
check("11. the real CLI entry point passes against the committed Yoma baseline",
      r.returncode == 0, (r.stdout + r.stderr)[-1200:])
check("11a. the CLI reports the registered rule count",
      "registered rules: %d" % len(V.RULES) in r.stdout, r.stdout[:200])

r2 = subprocess.run([sys.executable, "scripts/validate_enrichment_contracts.py", "--module", "yoma",
                     "--targets", "yoma-002a-s01", "--rules", "visualizableElements_not_list"],
                    cwd=str(ROOT), capture_output=True, text=True)
check("11b. the real CLI accepts --rules/--targets rule-scoped mode",
      r2.returncode == 0, (r2.stdout + r2.stderr)[-800:])

r3 = subprocess.run([sys.executable, "scripts/validate_enrichment_contracts.py", "--module", "yoma",
                     "--rules", "not-a-real-rule"],
                    cwd=str(ROOT), capture_output=True, text=True)
check("11c. the real CLI rejects an unknown --rules value",
      r3.returncode != 0 and "unknown rule id" in (r3.stdout + r3.stderr), (r3.stdout + r3.stderr)[-400:])

# ---- 12. finalRuling terminal-punctuation matching (exact contract) --------
ACCEPTED_ENDINGS = [
    "The halakha follows Rabbi Yehuda.",
    "Is the measure really a large date?",
    "The Gemara rejects this!",
    'The ruling states, "it is permitted."',
    "The Sages held it is permitted.'",
    "See the parallel discussion (Yoma 4a.)",
    "See the parallel ruling [ibid.]",
    'The Gemara asks, "why?"',
    'The Gemara answers, "no!"',
]
for text in ACCEPTED_ENDINGS:
    got = rules(content(sugya("yoma-002a-s01", finalRuling=text)))
    check("12a. accepted finalRuling ending %r" % text[-6:],
          "finalRuling_unterminated" not in got, sorted(got))

REJECTED_ENDINGS = [
    "The halakha follows Rabbi Yehuda:",
    "The halakha follows Rabbi Yehuda;",
    'The ruling states "it is permitted"',
    "The Sages held it is permitted'",
    "See the parallel discussion (Yoma 4a)",
    "See the parallel ruling [ibid]",
    'A bare closer after a comma, "it is permitted,"',
    'A bare closer after a word: "quoted"',
]
for text in REJECTED_ENDINGS:
    got = rules(content(sugya("yoma-002a-s01", finalRuling=text)))
    check("12b. rejected finalRuling ending %r" % text[-6:],
          "finalRuling_unterminated" in got, sorted(got))

# ---- 13. ARRAY-OCCURRENCE IDENTITY is stable across index shifts (req 7) ---
# Two invalid topic tags; remove the first so the second shifts from index 1
# to index 0. The ratchet must PASS (the surviving occurrence's identity
# does not depend on its array position).
two_bad = content(sugya("yoma-002a-s01", topicTags=["Bad One", "Bad Two"]))
two_bad_v, _, two_bad_occ = V.collect_violations(two_bad)
two_bad_baseline = make_baseline(two_bad_v, two_bad_occ)

shifted_one = content(sugya("yoma-002a-s01", topicTags=["Bad Two"]))
shifted_v, _, shifted_occ = V.collect_violations(shifted_one)
p_shift, imp_shift = V.compare_to_baseline(shifted_v, shifted_occ, two_bad_baseline, [])
check("13a. removing one invalid topic tag lets the survivor's index shift "
      "and still PASSES (stable identity)", p_shift == [], p_shift)
check("13a2. the index shift is reported as an improvement (2 -> 1)",
      any("topicTags_invalid_slug" in m and "2 -> 1" in m for m in imp_shift), imp_shift)

# Same scenario for visualizableElements_bare_value (a different array rule).
two_bad_ve2 = content(sugya("yoma-002a-s01", visualizableElements=["bare one", "bare two"]))
tv2_v, _, tv2_occ = V.collect_violations(two_bad_ve2)
tv2_baseline = make_baseline(tv2_v, tv2_occ)
shifted_ve2 = content(sugya("yoma-002a-s01", visualizableElements=["bare two"]))
sv2_v, _, sv2_occ = V.collect_violations(shifted_ve2)
p_ve_shift, imp_ve_shift = V.compare_to_baseline(sv2_v, sv2_occ, tv2_baseline, [])
check("13b. removing one invalid visualizableElement lets the survivor's "
      "index shift and still PASSES (stable identity)", p_ve_shift == [], p_ve_shift)

# After the shift, replacing the surviving value with a genuinely DIFFERENT
# invalid value (still at index 0) must FAIL against the original two-item
# baseline: it is not covered by the baseline's fingerprint multiset.
replaced_after_shift = content(sugya("yoma-002a-s01", topicTags=["A Totally New Bad Tag"]))
rep2_v, _, rep2_occ = V.collect_violations(replaced_after_shift)
p_replaced, _ = V.compare_to_baseline(rep2_v, rep2_occ, two_bad_baseline, [])
check("13c. replacing the surviving value with a different invalid value fails",
      any("same-sugya worsening" in p for p in p_replaced), p_replaced)

# Adding an IDENTICAL extra invalid value (duplicate, same fingerprint once
# index is stripped) must still FAIL via multiset/Counter semantics, not be
# masked by set semantics.
one_bad_tag2 = content(sugya("yoma-002a-s01", topicTags=["Same Bad Tag"]))
ob2_v, _, ob2_occ = V.collect_violations(one_bad_tag2)
ob2_baseline = make_baseline(ob2_v, ob2_occ)
duplicated = content(sugya("yoma-002a-s01", topicTags=["Same Bad Tag", "Same Bad Tag"]))
dup_v, _, dup_occ = V.collect_violations(duplicated)
p_dup, _ = V.compare_to_baseline(dup_v, dup_occ, ob2_baseline, [])
check("13d. adding an identical extra invalid value fails (multiset growth, "
      "not masked by shared fingerprint)", any("count rose" in p for p in p_dup), p_dup)

# strip_array_index sanity: array index removed, non-array path untouched.
check("13e. strip_array_index removes numeric array indices",
      V.strip_array_index("topicTags[3]") == "topicTags[]")
check("13f. strip_array_index leaves a non-array path untouched",
      V.strip_array_index("finalRuling") == "finalRuling")
check("13g. fingerprint_occurrence is index-independent for otherwise identical occurrences",
      V.fingerprint_occurrence("topicTags_invalid_slug", "yoma-002a-s01", "topicTags[0]", "Bad Tag")
      == V.fingerprint_occurrence("topicTags_invalid_slug", "yoma-002a-s01", "topicTags[7]", "Bad Tag"))

if FAILED:
    print("\n%d check(s) failed: %s" % (len(FAILED), FAILED))
    sys.exit(1)
print("\nAll enrichment-contract checks passed.")
