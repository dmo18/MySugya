#!/usr/bin/env python3
"""validate_enrichment_contracts.py - enrichment field contract gate.

Enforces the enrichment contracts finalized in
docs/reports/yoma-enrichment-contract-decision.md:

  display.hint            a real question, never a descriptive paragraph,
                           never truncated. Every non-empty value ends with
                           "?" -- this is an ALWAYS rule, not a "normally"
                           one; there is no exception mechanism.
  finalRuling             a string, independent of display.hint, never a
                           copy or truncated prefix of it, never cut
                           mid-sentence. Every non-empty value ends with
                           terminal punctuation (the contract requires this
                           explicitly; see the decision doc) so missing
                           terminal punctuation is never treated as
                           truncation evidence on its own -- it is the
                           literal rule.
  requiresUnderstanding   resolving sugya ids only, never prose
  prerequisiteKnowledge   prose prerequisites only, never sugya ids.
                          "No placeholder boilerplate" and "meaningful
                          prerequisite" are SEMANTIC requirements this
                          validator does NOT check; only shape (list of
                          nonblank strings), duplicates, and sugya-id leakage
                          are mechanically enforceable.
  topicTags               lowercase hyphen-separated ascii slugs, no duplicates
  visualizableElements    canonical { item, type?, label?, role?, priority? }
  concepts                removed legacy field: KEY PRESENCE is the
                           violation, not value truthiness. concepts: null,
                           concepts: {}, concepts: [] all violate; only full
                           key deletion is clean.
  difficulty              controlledValues.difficulty

Current main intentionally carries known legacy debt, so this is a
BASELINE-AND-RATCHET gate rather than a clean gate, with a REGISTRY of every
rule id (see RULES below) so a rule that reaches zero violations still
reports as a registered, zero-count rule -- never silently disappears the
way a deleted/renamed rule would. Baselines are per-module
(scripts/baselines/<module>_enrichment_contract_debt.json); a module may
never reuse another module's baseline.

Debt is tracked at OCCURRENCE granularity (rule, sugyaId, index-stripped
field path, content fingerprint), not just per-sugya-id, and NOT keyed by
array index -- array index is retained on each occurrence purely as
diagnostic/report metadata, never as identity, so:

  * a NEW violating sugya id is always a failure, even if totals fall;
  * within an ALREADY-dirty sugya, an additional occurrence of the same rule
    is always a failure (occurrence count rose), using MULTISET (Counter)
    semantics so an identical invalid value repeated an extra time is
    detected even though it shares a fingerprint with its sibling;
  * within an already-dirty sugya, swapping one invalid value for a
    DIFFERENT invalid value at the same or a new location is always a
    failure (its fingerprint is not covered by the baseline's fingerprint
    multiset for that rule+sugya), even when the occurrence count does not
    rise;
  * removing one invalid array member while another unchanged invalid
    member shifts down an index is a PASS -- identity survives the shift
    because array index is excluded from the fingerprint;
  * removing one of several violations in a dirty sugya is a pass and
    prints the exact decrease.

Rules are never deleted or renamed to make the gate pass: a rule id present
in the baseline that no longer appears in RULES is a hard failure unless an
explicit, reviewed entry exists in RULE_MIGRATIONS. The baseline itself is
verified for internal integrity (module, complete rule list, counts,
occurrence inventory, fingerprint, schema version) before it is trusted.

Usage (repo root):
  python3 scripts/validate_enrichment_contracts.py --module yoma
  python3 scripts/validate_enrichment_contracts.py --module yoma --targets yoma-082b-s01
  python3 scripts/validate_enrichment_contracts.py --module yoma --rules legacy_concepts_present --targets yoma-082b-s01
  python3 scripts/validate_enrichment_contracts.py --module yoma --report
  python3 scripts/validate_enrichment_contracts.py --module yoma --update-baseline
  python3 scripts/validate_enrichment_contracts.py --module yoma --compare-ref origin/main

TWO INDEPENDENT COMPARISONS, BOTH REQUIRED

This gate runs two separate ratchets, layered, not either/or:

  1. FROZEN BASELINE CHECK (compare_to_baseline, always runs) -- current
     corpus vs. the frozen historical baseline
     (scripts/baselines/<module>_enrichment_contract_debt.json). This
     enumerates the ORIGINAL legacy debt from when the campaign started and
     is never rewritten by ordinary repairs. It answers "is the corpus still
     inside the envelope of debt the campaign started with?" It does NOT,
     by itself, stop a later PR from reintroducing a violation that a prior
     PR already fixed on main: a value that was always within the frozen
     envelope compares clean against the frozen baseline no matter what
     happened on main in between.

  2. MERGE-BASE MONOTONIC RATCHET (compare_to_merge_base, only when
     --compare-ref is supplied) -- current corpus vs. the SAME module's
     generated data at an arbitrary git ref, read with `git show
     <ref>:<learningDataFile>` (real git data, never a hand-maintained
     snapshot). This is what closes the gap above: it compares this PR
     against its own actual merge-base (current main before the PR's
     changes), so a previously-merged improvement can never be silently
     regressed by a later, unrelated PR, even though the regressed value
     would still fall inside the frozen historical envelope.

A PR passes only when BOTH checks pass. See compare_to_merge_base for the
exact subset/multiset contract.
"""
import argparse
import collections
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASELINE_DIR = ROOT / "scripts" / "baselines"
SCHEMA_VERSION = 2

DIFFICULTY = ("intro", "intermediate", "advanced")
SLUG = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
SUGYA_ID = re.compile(r"^[a-z0-9]+-\d+[ab]-s\d+$")
SENTENCE_END = re.compile(r"[.!?][\"'”\)\]]?$")
CANONICAL_VE_KEYS = {"item", "type", "label", "role", "priority"}
LEGACY_VE_KEYS = {"name", "description", "desc"}

# The complete registry of every enrichment-contract rule id. Every entry
# here is guaranteed a key in collect_violations()'s return value, even with
# zero occurrences -- this is what lets a baselined rule "reach zero" and
# still be told apart from a rule that was quietly deleted or renamed out of
# the code (see main()'s baseline comparison).
RULES = (
    "hint_not_string",
    "hint_trailing_ellipsis",
    "hint_not_a_question",
    "finalRuling_not_string",
    "finalRuling_trailing_ellipsis",
    "finalRuling_unterminated",
    "finalRuling_equals_hint",
    "finalRuling_prefix_of_hint",
    "requiresUnderstanding_not_list",
    "requiresUnderstanding_prose",
    "requiresUnderstanding_unresolved_id",
    "requiresUnderstanding_self_reference",
    "prerequisiteKnowledge_not_list",
    "prerequisiteKnowledge_blank",
    "prerequisiteKnowledge_contains_sugya_id",
    "prerequisiteKnowledge_duplicate",
    "topicTags_not_list",
    "topicTags_invalid_slug",
    "topicTags_duplicate",
    "visualizableElements_not_list",
    "visualizableElements_bare_value",
    "visualizableElements_missing_item",
    "visualizableElements_legacy_key",
    "visualizableElements_unknown_key",
    "visualizableElements_field_not_string",
    "visualizableElements_priority_not_numeric",
    "legacy_concepts_present",
    "difficulty_invalid_enum",
)

# Explicit, reviewed rule renames/removals. Empty in ordinary operation.
# A baseline entry for a rule id that is a KEY here, whose VALUE is still in
# RULES, is treated as migrated onto the new rule id for comparison purposes
# instead of failing as "rule deleted". A rule id that is a key here with
# value None is an explicitly reviewed REMOVAL (its baseline debt is
# considered permanently retired, never silently -- it must be empty at the
# time of removal, or the removal itself is rejected). Any change here is
# itself a reviewed docs-tooling change, visible in the PR diff.
RULE_MIGRATIONS = {}

NODE_EVAL = r"""
const fs = require('fs'), vm = require('vm');
const src = fs.readFileSync(process.argv[2], 'utf8');
const ctx = {};
vm.createContext(ctx);
vm.runInContext(src + "\n;globalThis.__C = DAF_CONTENT;", ctx, { timeout: 180000 });
process.stdout.write(JSON.stringify(ctx.__C));
"""


def load_daf_content(learning_data_path):
    """Evaluate the generated module data with node, exactly as the app reads it."""
    fd, path = tempfile.mkstemp(suffix=".cjs")
    try:
        os.write(fd, NODE_EVAL.encode())
        os.close(fd)
        r = subprocess.run(["node", path, str(learning_data_path)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit("failed to evaluate %s: %s" % (learning_data_path, r.stderr[-400:]))
        return json.loads(r.stdout)
    finally:
        os.unlink(path)


def resolve_module(module):
    """Locate the module's generated data file without importing module tooling."""
    desc = ROOT / "modules" / module / "module.json"
    if not desc.exists():
        raise SystemExit("unknown module %r (no %s)" % (module, desc))
    d = json.loads(desc.read_text(encoding="utf-8"))
    return ROOT / d["paths"]["learningDataFile"]


def baseline_path(module):
    """The unambiguous, module-specific baseline path. Never shared across
    modules and never falls back to another module's file."""
    return BASELINE_DIR / ("%s_enrichment_contract_debt.json" % module)


ARRAY_INDEX = re.compile(r"\[\d+\]")


def strip_array_index(path):
    """The logical field path with any array index removed (e.g.
    "topicTags[3]" -> "topicTags[]"). This is the STABLE identity path used
    for occurrence fingerprinting -- array index is diagnostic metadata only,
    never part of an occurrence's identity, so that removing one invalid
    array member and letting a later invalid member shift down one index
    does not change that surviving member's identity."""
    return ARRAY_INDEX.sub("[]", path)


def fingerprint_occurrence(rule, sid, path, value):
    """A stable content fingerprint for one occurrence, keyed by
    (rule, sugyaId, index-stripped path, value) -- NOT by array index. Any
    change in the offending value (even keeping the same rule/sugya/path)
    produces a different fingerprint, which is exactly what lets the ratchet
    reject an invalid value silently swapped for a different invalid value.
    Because array index is excluded, an unchanged invalid array member keeps
    its identity even when an earlier sibling is removed and every later
    index shifts down by one -- index is retained elsewhere purely as
    diagnostic/report metadata, never as identity."""
    if not isinstance(value, (str, int, float, bool, type(None))):
        value = repr(value)
    payload = json.dumps({"rule": rule, "sugyaId": sid, "path": strip_array_index(path),
                          "value": value}, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def collect_violations(daf_content):
    """Return (violations, detail, occurrences).

    violations: {rule_id: sorted[sugyaId]} -- every rule in RULES is present,
      with an empty list when clean.
    detail: {rule_id: [human-readable sample lines]} (first 5 per rule).
    occurrences: {rule_id: [{"sugyaId","path","index","fingerprint"}, ...]}
      -- the occurrence-level inventory the ratchet uses to detect
      same-sugya worsening. Every rule in RULES is present, with an empty
      list when clean.
    """
    v = {r: set() for r in RULES}
    detail = {r: [] for r in RULES}
    occ = {r: [] for r in RULES}
    sugyot = [(daf, s) for daf, c in daf_content.items() for s in (c.get("sugyot") or [])]
    all_ids = {s["id"] for _daf, s in sugyot}

    def flag(rule, sid, path, index, value, note):
        v[rule].add(sid)
        occ[rule].append({
            "sugyaId": sid, "path": path, "index": index,
            # index is diagnostic metadata only (kept for --report output);
            # it is deliberately excluded from the identity fingerprint so
            # array-index shifts never change an occurrence's identity.
            "fingerprint": fingerprint_occurrence(rule, sid, path, value),
        })
        if len(detail[rule]) < 5:
            detail[rule].append("%s %s: %s" % (sid, path, note))

    for daf, s in sugyot:
        sid = s["id"]
        display = s.get("display") or {}
        hint = display.get("hint")
        hint_s = hint.strip() if isinstance(hint, str) else ""

        # ---- display.hint -------------------------------------------------
        if hint is not None and not isinstance(hint, str):
            flag("hint_not_string", sid, "display.hint", None, hint, type(hint).__name__)
        if hint_s:
            if hint_s.endswith(("...", "…")):
                flag("hint_trailing_ellipsis", sid, "display.hint", None, hint_s, repr(hint_s[-24:]))
            elif not hint_s.endswith("?"):
                flag("hint_not_a_question", sid, "display.hint", None, hint_s, repr(hint_s[-40:]))

        # ---- finalRuling --------------------------------------------------
        fr = s.get("finalRuling")
        if fr is not None and not isinstance(fr, str):
            flag("finalRuling_not_string", sid, "finalRuling", None, fr, type(fr).__name__)
        fr_s = fr.strip() if isinstance(fr, str) else ""
        if fr_s:
            if fr_s.endswith(("...", "…")):
                flag("finalRuling_trailing_ellipsis", sid, "finalRuling", None, fr_s, repr(fr_s[-24:]))
            elif not SENTENCE_END.search(fr_s):
                # Missing terminal punctuation is the literal, explicit
                # contract rule (see decision doc), not a length-based
                # heuristic proxy for truncation -- there is no length
                # threshold here.
                flag("finalRuling_unterminated", sid, "finalRuling", None, fr_s, repr(fr_s[-40:]))
            if hint_s:
                if fr_s == hint_s:
                    flag("finalRuling_equals_hint", sid, "finalRuling", None, fr_s,
                         "exact copy of display.hint")
                elif hint_s.startswith(fr_s):
                    flag("finalRuling_prefix_of_hint", sid, "finalRuling", None, fr_s,
                         "prefix of display.hint (%d chars)" % len(fr_s))

        # ---- requiresUnderstanding / prerequisiteKnowledge ----------------
        ru = s.get("requiresUnderstanding")
        if ru is not None and not isinstance(ru, list):
            flag("requiresUnderstanding_not_list", sid, "requiresUnderstanding", None, ru,
                 type(ru).__name__)
        elif isinstance(ru, list):
            for i, item in enumerate(ru):
                path = "requiresUnderstanding[%d]" % i
                if not isinstance(item, str) or not SUGYA_ID.match(item):
                    flag("requiresUnderstanding_prose", sid, path, i, item, repr(str(item)[:48]))
                elif item not in all_ids:
                    flag("requiresUnderstanding_unresolved_id", sid, path, i, item, item)
                elif item == sid:
                    flag("requiresUnderstanding_self_reference", sid, path, i, item, item)

        pk = s.get("prerequisiteKnowledge")
        if pk is not None:
            if not isinstance(pk, list):
                flag("prerequisiteKnowledge_not_list", sid, "prerequisiteKnowledge", None, pk,
                     type(pk).__name__)
            else:
                seen = set()
                for i, item in enumerate(pk):
                    path = "prerequisiteKnowledge[%d]" % i
                    if not isinstance(item, str) or not item.strip():
                        flag("prerequisiteKnowledge_blank", sid, path, i, item,
                             repr(str(item)[:40]))
                        continue
                    if SUGYA_ID.match(item.strip()):
                        flag("prerequisiteKnowledge_contains_sugya_id", sid, path, i, item, item)
                    if item.strip() in seen:
                        flag("prerequisiteKnowledge_duplicate", sid, path, i, item,
                             repr(item[:40]))
                    seen.add(item.strip())

        # ---- topicTags -------------------------------------------------
        tags = s.get("topicTags")
        if tags is not None:
            if not isinstance(tags, list):
                flag("topicTags_not_list", sid, "topicTags", None, tags, type(tags).__name__)
            else:
                seen = set()
                for i, t in enumerate(tags):
                    path = "topicTags[%d]" % i
                    if not isinstance(t, str) or not SLUG.fullmatch(t):
                        flag("topicTags_invalid_slug", sid, path, i, t, repr(str(t)[:40]))
                    if isinstance(t, str):
                        if t in seen:
                            flag("topicTags_duplicate", sid, path, i, t, repr(t[:40]))
                        seen.add(t)

        # ---- visualizableElements ---------------------------------------
        ve = s.get("visualizableElements")
        if ve is not None:
            if not isinstance(ve, list):
                flag("visualizableElements_not_list", sid, "visualizableElements", None, ve,
                     type(ve).__name__)
            else:
                for i, el in enumerate(ve):
                    path = "visualizableElements[%d]" % i
                    if not isinstance(el, dict):
                        flag("visualizableElements_bare_value", sid, path, i, el,
                             repr(str(el)[:40]))
                        continue
                    item = el.get("item")
                    if "item" not in el or not isinstance(item, str) or not item.strip():
                        flag("visualizableElements_missing_item", sid, path + ".item", i,
                             el.get("item"), "keys=%s" % "+".join(sorted(el.keys())))
                    legacy = LEGACY_VE_KEYS & set(el.keys())
                    if legacy:
                        flag("visualizableElements_legacy_key", sid, path, i, sorted(legacy),
                             "+".join(sorted(legacy)))
                    unknown = set(el.keys()) - CANONICAL_VE_KEYS - LEGACY_VE_KEYS
                    if unknown:
                        flag("visualizableElements_unknown_key", sid, path, i, sorted(unknown),
                             "+".join(sorted(unknown)))
                    for key in ("type", "label", "role"):
                        if key in el and el[key] is not None:
                            val = el[key]
                            if not isinstance(val, str) or not val.strip():
                                flag("visualizableElements_field_not_string", sid,
                                     "%s.%s" % (path, key), i, val, "%s=%r" % (key, val))
                    if "priority" in el and el["priority"] is not None:
                        pr = el["priority"]
                        if isinstance(pr, bool) or not isinstance(pr, (int, float)):
                            flag("visualizableElements_priority_not_numeric", sid,
                                 path + ".priority", i, pr, type(pr).__name__)

        # ---- removed legacy concepts: KEY PRESENCE, not value truthiness --
        if "concepts" in s:
            flag("legacy_concepts_present", sid, "concepts", None, s.get("concepts"),
                 "removed field key still present (value=%r)" % (s.get("concepts"),))

        # ---- difficulty -----------------------------------------------------
        if s.get("difficulty") is not None and s.get("difficulty") not in DIFFICULTY:
            flag("difficulty_invalid_enum", sid, "difficulty", None, s.get("difficulty"),
                 repr(s.get("difficulty")))

    violations = {k: sorted(ids) for k, ids in v.items()}
    return violations, detail, occ


def fingerprint_baseline(rule_registry, occurrences):
    """Whole-baseline integrity fingerprint over the rule registry and the
    full occurrence inventory (order-independent)."""
    canon = {}
    for rule in sorted(occurrences):
        rows = sorted(occurrences[rule],
                      key=lambda o: (o["sugyaId"], o["path"], -1 if o["index"] is None else o["index"],
                                     o["fingerprint"]))
        canon[rule] = rows
    payload = json.dumps({"ruleRegistry": sorted(rule_registry), "occurrences": canon},
                         ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def verify_baseline_integrity(base, module):
    """Do not trust a baseline whose stored counts or fingerprint disagree
    with its own payload, whose module does not match, or whose schema
    version is unrecognized. Returns a list of problem strings (empty when
    the baseline is internally consistent)."""
    problems = []
    if base.get("schemaVersion") != SCHEMA_VERSION:
        problems.append("baseline schemaVersion %r != expected %r (regenerate with "
                        "--update-baseline)" % (base.get("schemaVersion"), SCHEMA_VERSION))
        return problems  # nothing else here is trustworthy at the wrong schema version
    if base.get("module") != module:
        problems.append("baseline module %r does not match --module %r; a module may never "
                        "reuse another module's baseline" % (base.get("module"), module))
    occurrences = base.get("occurrences", {})
    if set(base.get("ruleRegistry", [])) != set(occurrences.keys()):
        problems.append("baseline ruleRegistry does not match the rule keys present in its "
                        "own occurrences payload")
    recomputed_counts = {r: len({o["sugyaId"] for o in occs}) for r, occs in occurrences.items()}
    if recomputed_counts != base.get("counts"):
        mismatches = {r: (base.get("counts", {}).get(r), recomputed_counts.get(r))
                     for r in set(recomputed_counts) | set(base.get("counts", {}))
                     if base.get("counts", {}).get(r) != recomputed_counts.get(r)}
        problems.append("baseline counts do not match its own occurrence inventory: %s" % mismatches)
    expected_fp = fingerprint_baseline(base.get("ruleRegistry", []), occurrences)
    if expected_fp != base.get("fingerprint"):
        problems.append("baseline fingerprint does not match its own payload "
                        "(hand-edited or corrupted baseline; regenerate with --update-baseline)")
    return problems


def write_baseline(module, violations, occurrences):
    counts = {k: len(v) for k, v in violations.items()}
    path = baseline_path(module)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "schemaVersion": SCHEMA_VERSION,
        "module": module,
        "note": ("Frozen legacy enrichment debt for module %r, tracked at occurrence "
                 "granularity. A new violating sugya id is a failure even when totals "
                 "drop; within an already-dirty sugya, a rising occurrence count or an "
                 "invalid value swapped for a different invalid value is a failure. "
                 "Regenerate only with --update-baseline in a reviewed docs-tooling "
                 "change." % module),
        "ruleRegistry": sorted(RULES),
        "counts": counts,
        "occurrences": occurrences,
        "fingerprint": fingerprint_baseline(RULES, occurrences),
        "violations": violations,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return path


def compare_to_baseline(violations, occurrences, base, targets, rules_filter=None):
    """Core ratchet comparison. Returns (problems, improved). rules_filter,
    when given, narrows which rules are checked for TARGET-clean (the global
    corpus-wide ratchet below always covers every rule regardless)."""
    problems, improved = [], []
    base_occurrences = base.get("occurrences", {})
    base_rules = set(base_occurrences.keys())
    cur_rules = set(RULES)

    for r in sorted(base_rules - cur_rules):
        mapped = RULE_MIGRATIONS.get(r)
        if mapped in cur_rules:
            continue
        if r in RULE_MIGRATIONS and mapped is None and not base_occurrences.get(r):
            continue  # explicitly reviewed removal of an already-empty rule
        problems.append("rule %r is in the baseline but is not a currently registered rule "
                        "(rules may not be deleted or renamed to pass the gate; add a reviewed "
                        "entry to RULE_MIGRATIONS for an intentional rename/removal)" % r)

    for rule in sorted(cur_rules):
        base_occs = list(base_occurrences.get(rule, []))
        for old, new in RULE_MIGRATIONS.items():
            if new == rule:
                base_occs += base_occurrences.get(old, [])
        cur_occs = occurrences.get(rule, [])

        base_by_sugya = collections.defaultdict(list)
        for o in base_occs:
            base_by_sugya[o["sugyaId"]].append(o)
        cur_by_sugya = collections.defaultdict(list)
        for o in cur_occs:
            cur_by_sugya[o["sugyaId"]].append(o)

        for sid in sorted(set(base_by_sugya) | set(cur_by_sugya)):
            b, c = base_by_sugya.get(sid, []), cur_by_sugya.get(sid, [])
            if not b and c:
                problems.append("NEW debt for %s: %s (%d occurrence(s))" % (rule, sid, len(c)))
                continue
            if b and not c:
                improved.append("%s %s: %d -> 0 (fully repaired)" % (rule, sid, len(b)))
                continue
            if not b and not c:
                continue
            # Multiset (Counter) semantics, not set semantics: two distinct
            # occurrences of an IDENTICAL invalid value share one fingerprint
            # (index is excluded from identity, see fingerprint_occurrence),
            # so duplicate-growth must be caught by multiplicity, not mere
            # set membership.
            b_counter = collections.Counter(o["fingerprint"] for o in b)
            c_counter = collections.Counter(o["fingerprint"] for o in c)
            if len(c) > len(b):
                problems.append("count rose for %s %s: baseline %d -> now %d"
                                % (rule, sid, len(b), len(c)))
            elif c_counter - b_counter:
                # Counter subtraction keeps only fingerprints whose current
                # multiplicity exceeds the baseline's -- a non-empty result
                # means some current occurrence (by value, not by array
                # position) is not covered by the baseline's multiset for
                # this rule+sugya, whether it is a brand-new value or an
                # identical value repeated more times than the baseline had.
                problems.append("same-sugya worsening for %s %s: an invalid value changed into a "
                                "different invalid value not present in the baseline (occurrence "
                                "count %d -> %d)" % (rule, sid, len(b), len(c)))
            elif len(c) < len(b):
                improved.append("%s %s: %d -> %d" % (rule, sid, len(b), len(c)))

    active_rules = set(rules_filter) if rules_filter else cur_rules
    for sid in targets:
        hits = sorted(r for r in active_rules if sid in violations.get(r, []))
        if hits:
            problems.append("target %s is not contract-clean for rule(s) %s" % (sid, ", ".join(hits)))

    return problems, improved


def compare_to_merge_base(occurrences, ref_occurrences):
    """Merge-base monotonic ratchet. Returns a list of problem strings
    (empty when the ratchet holds).

    For every registered rule and every sugya, CURRENT invalid occurrences
    must be a multiset SUBSET of the occurrences present at --compare-ref
    (this PR's actual git merge-base, i.e. current main before this PR's
    changes). This is a SEPARATE comparison from compare_to_baseline
    (against the frozen historical baseline) and is layered on top of it,
    not a replacement -- see the module docstring.

    Why this is needed: the frozen baseline enumerates the ORIGINAL legacy
    debt and is intentionally never rewritten, so a value that has always
    been within that frozen envelope compares clean against it no matter
    what happened on main in between -- including a later, unrelated PR
    putting an already-fixed invalid value right back. Comparing against the
    actual merge-base instead of the frozen baseline is what catches that:
    if a rule+sugya was clean (or had fewer/different violations) at the
    merge-base, it must still be at least that clean now.

    Uses the SAME occurrence identity as compare_to_baseline -- (rule,
    sugyaId, index-stripped path, value fingerprint) via
    fingerprint_occurrence/strip_array_index, reused unchanged -- and the
    same Counter/multiset semantics, so duplicate multiplicity matters:
    two identical invalid occurrences at the merge-base cover one identical
    surviving occurrence now, but not two occurrences after one was
    supposedly repaired and then reintroduced.
    """
    problems = []
    for rule in sorted(RULES):
        cur_by_sugya = collections.defaultdict(list)
        for o in occurrences.get(rule, []):
            cur_by_sugya[o["sugyaId"]].append(o)
        ref_by_sugya = collections.defaultdict(list)
        for o in ref_occurrences.get(rule, []):
            ref_by_sugya[o["sugyaId"]].append(o)

        for sid in sorted(set(cur_by_sugya) | set(ref_by_sugya)):
            c, r = cur_by_sugya.get(sid, []), ref_by_sugya.get(sid, [])
            if not c:
                continue  # current is clean for this rule+sugya: never a regression
            c_counter = collections.Counter(o["fingerprint"] for o in c)
            r_counter = collections.Counter(o["fingerprint"] for o in r)
            excess = c_counter - r_counter
            if not excess:
                continue  # every current occurrence (by value AND multiplicity) already
                          # existed at the merge-base; not a regression
            if not r:
                problems.append(
                    "NEW regression for %s %s: merge-base reference had 0 occurrence(s), "
                    "current has %d (this rule/sugya was clean at the PR's merge-base and "
                    "is not clean now)" % (rule, sid, len(c)))
                continue
            if len(c) > len(r):
                problems.append(
                    "count rose for %s %s: merge-base reference had %d occurrence(s), now %d"
                    % (rule, sid, len(r), len(c)))
                continue
            deficit = r_counter - c_counter
            problems.append(
                "same-sugya regression for %s %s: merge-base reference fingerprint(s) %s are "
                "no longer present, but current carries fingerprint(s) %s that were not present "
                "at the merge-base (occurrence count merge-base %d -> current %d; an invalid "
                "value already fixed on main may have been reintroduced, or swapped for a "
                "different invalid value)"
                % (rule, sid, sorted(deficit), sorted(excess), len(r), len(c)))
    return problems


def load_ref_occurrences(module, compare_ref):
    """Load (violations, occurrences) for the given module's generated data
    AT compare_ref, using real git data (`git show <ref>:<path>`), never a
    hand-maintained snapshot. Fails closed: any resolution or parse failure
    exits nonzero with a clear error rather than silently skipping the
    merge-base ratchet."""
    learning_data_path = resolve_module(module)
    rel = learning_data_path.relative_to(ROOT).as_posix()
    r = subprocess.run(["git", "show", "%s:%s" % (compare_ref, rel)],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("ERROR: --compare-ref %r could not be resolved for %s (git show failed): %s"
                 % (compare_ref, rel, (r.stderr or "").strip()[-500:]))
    fd, tmp_path = tempfile.mkstemp(suffix=".cjs")
    try:
        os.write(fd, r.stdout.encode("utf-8"))
        os.close(fd)
        try:
            ref_data = load_daf_content(tmp_path)
        except SystemExit as ex:
            sys.exit("ERROR: --compare-ref %r module data for %s could not be parsed: %s"
                     % (compare_ref, rel, ex))
    finally:
        os.unlink(tmp_path)
    ref_violations, _ref_detail, ref_occurrences = collect_violations(ref_data)
    return ref_violations, ref_occurrences


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--module", default="yoma")
    ap.add_argument("--targets", nargs="*", default=[],
                    help="sugya ids that must be fully compliant (target-clean)")
    ap.add_argument("--rules", nargs="*", default=None,
                    help="restrict TARGET-clean enforcement to these rule ids "
                         "(the corpus-wide ratchet always covers every rule)")
    ap.add_argument("--report", action="store_true", help="print the full inventory")
    ap.add_argument("--update-baseline", action="store_true",
                    help="rewrite the committed baseline (docs-tooling change)")
    ap.add_argument("--compare-ref", default=None,
                    help="also run the merge-base monotonic ratchet: compare current "
                         "occurrences against the same module's generated data at this git "
                         "ref (e.g. this PR's actual merge-base SHA), using real `git show` "
                         "data. Layered ON TOP OF the frozen baseline check, never a "
                         "replacement for it. Fails closed if the ref or its module data "
                         "cannot be resolved/parsed.")
    args = ap.parse_args()

    if args.rules:
        unknown = [r for r in args.rules if r not in RULES]
        if unknown:
            sys.exit("ERROR: unknown rule id(s) for --rules: %s (known: %s)"
                     % (unknown, ", ".join(sorted(RULES))))

    data = load_daf_content(resolve_module(args.module))
    violations, detail, occurrences = collect_violations(data)
    counts = {k: len(v) for k, v in sorted(violations.items())}
    total = sum(counts.values())

    print("enrichment contract gate - module %s" % args.module)
    print("  registered rules: %d | violating sugya-rule pairs: %d across %d rule(s) with debt"
          % (len(RULES), total, sum(1 for c in counts.values() if c)))
    for rule in sorted(counts):
        print("    %-42s %5d" % (rule, counts[rule]))
        if args.report:
            for line in detail[rule]:
                print("        %s" % line)

    if args.update_baseline:
        path = write_baseline(args.module, violations, occurrences)
        print("\nbaseline written to %s" % path.relative_to(ROOT))
        return

    bpath = baseline_path(args.module)
    print("\nFROZEN BASELINE CHECK")
    if not bpath.exists():
        sys.exit("ERROR: missing baseline %s for module %r; run --update-baseline in a "
                 "reviewed docs-tooling change" % (bpath.relative_to(ROOT), args.module))
    base = json.loads(bpath.read_text(encoding="utf-8"))

    integrity_problems = verify_baseline_integrity(base, args.module)
    if integrity_problems:
        print("BASELINE INTEGRITY CHECK FAILED (baseline is not trusted):")
        for p in integrity_problems:
            print("  FAIL %s" % p)
        sys.exit("enrichment contract gate FAILED: baseline integrity check failed")

    problems, improved = compare_to_baseline(violations, occurrences, base, args.targets, args.rules)

    if improved:
        print("ratchet improvements:")
        for line in improved:
            print("  %s" % line)
    if args.targets:
        scope_note = (" (rules: %s)" % ", ".join(args.rules)) if args.rules else ""
        print("target-clean checked for: %s%s" % (", ".join(args.targets), scope_note))

    if problems:
        for p in problems:
            print("  FAIL %s" % p)
        print("FROZEN BASELINE CHECK FAILED (%d problem(s))" % len(problems))
    else:
        print("OK: no new enrichment-contract debt; baseline holds%s."
              % (" and %d rule(s)/sugya(s) improved" % len(improved) if improved else ""))

    mb_problems = []
    if args.compare_ref:
        print("\nMERGE-BASE MONOTONIC RATCHET")
        print("comparing against %r via `git show %s:%s`"
              % (args.compare_ref, args.compare_ref,
                 resolve_module(args.module).relative_to(ROOT).as_posix()))
        _ref_violations, ref_occurrences = load_ref_occurrences(args.module, args.compare_ref)
        mb_problems = compare_to_merge_base(occurrences, ref_occurrences)
        if mb_problems:
            for p in mb_problems:
                print("  FAIL %s" % p)
            print("MERGE-BASE MONOTONIC RATCHET FAILED (%d problem(s))" % len(mb_problems))
        else:
            print("OK: no rule/sugya regressed relative to the merge-base.")

    print()
    if problems or mb_problems:
        raise SystemExit(
            "enrichment contract gate FAILED (%d frozen-baseline problem(s), %d "
            "merge-base-ratchet problem(s))" % (len(problems), len(mb_problems)))
    print("OK: enrichment contract gate passed%s."
          % (" (frozen baseline + merge-base ratchet)" if args.compare_ref else " (frozen baseline)"))


if __name__ == "__main__":
    main()
