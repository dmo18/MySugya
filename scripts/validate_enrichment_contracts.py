#!/usr/bin/env python3
"""validate_enrichment_contracts.py - enrichment field contract gate.

Enforces the enrichment contracts finalized in
docs/reports/yoma-enrichment-contract-decision.md:

  display.hint            a real question, not a descriptive paragraph
  finalRuling             a string, independent of display.hint, never a copy
                          or truncated prefix of it, never cut mid-sentence
  requiresUnderstanding   resolving sugya ids only, never prose
  prerequisiteKnowledge   prose prerequisites only, never sugya ids
  topicTags               lowercase hyphen-separated ascii slugs, no duplicates
  visualizableElements    canonical { item, type?, label?, role?, priority? }
  concepts                removed legacy field, scheduled for purge
  difficulty              controlledValues.difficulty

Current main intentionally carries known legacy debt, so this is a
BASELINE-AND-RATCHET gate rather than a clean gate:

  * every violation is classified into a stable rule id;
  * the committed baseline records the exact per-rule count and the id set;
  * a NEW violating sugya id is always a failure, even if counts fall;
  * a rising count is always a failure;
  * a falling count is a pass and prints the ratchet delta;
  * --targets enforces TARGET-CLEAN: named sugyot must be fully compliant,
    which is how a repair PR proves it left the fields it touched valid.

Rules are never deleted to make the gate pass. Rewriting the baseline
requires --update-baseline, which is a docs-tooling change and shows the
full delta so a reviewer can see what was accepted.

Usage (repo root):
  python3 scripts/validate_enrichment_contracts.py --module yoma
  python3 scripts/validate_enrichment_contracts.py --module yoma --targets yoma-082b-s01
  python3 scripts/validate_enrichment_contracts.py --module yoma --report
  python3 scripts/validate_enrichment_contracts.py --module yoma --update-baseline
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
BASELINE = ROOT / "scripts" / "baselines" / "enrichment_contract_debt.json"

DIFFICULTY = ("intro", "intermediate", "advanced")
SLUG = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
SUGYA_ID = re.compile(r"^[a-z0-9]+-\d+[ab]-s\d+$")
SENTENCE_END = re.compile(r"[.!?:;”\"')\]]$")
CANONICAL_VE_KEYS = {"item", "type", "label", "role", "priority"}
LEGACY_VE_KEYS = {"name", "description", "desc"}

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


def collect_violations(daf_content):
    """Return {rule_id: sorted[sugyaId]} plus a per-rule detail sample."""
    v = collections.defaultdict(set)
    detail = collections.defaultdict(list)
    sugyot = [(daf, s) for daf, c in daf_content.items() for s in (c.get("sugyot") or [])]
    all_ids = {s["id"] for _daf, s in sugyot}

    def flag(rule, sid, note):
        v[rule].add(sid)
        if len(detail[rule]) < 5:
            detail[rule].append("%s: %s" % (sid, note))

    for daf, s in sugyot:
        sid = s["id"]
        display = s.get("display") or {}
        hint = display.get("hint")
        hint_s = hint.strip() if isinstance(hint, str) else ""

        # ---- display.hint -------------------------------------------------
        if hint is not None and not isinstance(hint, str):
            flag("hint_not_string", sid, type(hint).__name__)
        if hint_s:
            if hint_s.endswith(("...", "…")):
                flag("hint_trailing_ellipsis", sid, repr(hint_s[-24:]))
            if not hint_s.endswith("?"):
                flag("hint_not_a_question", sid, repr(hint_s[-40:]))

        # ---- finalRuling --------------------------------------------------
        fr = s.get("finalRuling")
        if fr is not None and not isinstance(fr, str):
            flag("finalRuling_not_string", sid, type(fr).__name__)
        fr_s = fr.strip() if isinstance(fr, str) else ""
        if fr_s:
            if fr_s.endswith(("...", "…")):
                flag("finalRuling_trailing_ellipsis", sid, repr(fr_s[-24:]))
            if len(fr_s) >= 40 and not SENTENCE_END.search(fr_s):
                flag("finalRuling_unterminated", sid, repr(fr_s[-40:]))
            if hint_s:
                if fr_s == hint_s:
                    flag("finalRuling_equals_hint", sid, "exact copy of display.hint")
                elif hint_s.startswith(fr_s) and len(fr_s) >= 30:
                    flag("finalRuling_prefix_of_hint", sid,
                         "truncated prefix of display.hint (%d chars)" % len(fr_s))

        # ---- requiresUnderstanding / prerequisiteKnowledge ----------------
        ru = s.get("requiresUnderstanding")
        if ru is not None and not isinstance(ru, list):
            flag("requiresUnderstanding_not_list", sid, type(ru).__name__)
        for item in (ru or []) if isinstance(ru, list) else []:
            if not isinstance(item, str) or not SUGYA_ID.match(item):
                flag("requiresUnderstanding_prose", sid, repr(str(item)[:48]))
            elif item not in all_ids:
                flag("requiresUnderstanding_unresolved_id", sid, item)
            elif item == sid:
                flag("requiresUnderstanding_self_reference", sid, item)

        pk = s.get("prerequisiteKnowledge")
        if pk is not None:
            if not isinstance(pk, list):
                flag("prerequisiteKnowledge_not_list", sid, type(pk).__name__)
            else:
                seen = set()
                for item in pk:
                    if not isinstance(item, str) or not item.strip():
                        flag("prerequisiteKnowledge_blank", sid, repr(str(item)[:40]))
                        continue
                    if SUGYA_ID.match(item.strip()):
                        flag("prerequisiteKnowledge_contains_sugya_id", sid, item)
                    if item.strip() in seen:
                        flag("prerequisiteKnowledge_duplicate", sid, repr(item[:40]))
                    seen.add(item.strip())

        # ---- topicTags -----------------------------------------------------
        tags = s.get("topicTags") or []
        if tags and not isinstance(tags, list):
            flag("topicTags_not_list", sid, type(tags).__name__)
        else:
            seen = set()
            for t in tags:
                if not isinstance(t, str) or not SLUG.fullmatch(t):
                    flag("topicTags_invalid_slug", sid, repr(str(t)[:40]))
                if t in seen:
                    flag("topicTags_duplicate", sid, repr(str(t)[:40]))
                seen.add(t)

        # ---- visualizableElements ------------------------------------------
        for el in (s.get("visualizableElements") or []):
            if not isinstance(el, dict):
                flag("visualizableElements_bare_value", sid, repr(str(el)[:40]))
                continue
            if "item" not in el or not str(el.get("item") or "").strip():
                flag("visualizableElements_missing_item", sid,
                     "keys=%s" % "+".join(sorted(el.keys())))
            legacy = LEGACY_VE_KEYS & set(el.keys())
            if legacy:
                flag("visualizableElements_legacy_key", sid, "+".join(sorted(legacy)))
            unknown = set(el.keys()) - CANONICAL_VE_KEYS - LEGACY_VE_KEYS
            if unknown:
                flag("visualizableElements_unknown_key", sid, "+".join(sorted(unknown)))
            if "priority" in el and not isinstance(el["priority"], (int, float)):
                flag("visualizableElements_priority_not_numeric", sid,
                     type(el["priority"]).__name__)

        # ---- removed legacy concepts ----------------------------------------
        if s.get("concepts") is not None:
            flag("legacy_concepts_present", sid, "removed field still populated")

        # ---- difficulty -----------------------------------------------------
        if s.get("difficulty") is not None and s.get("difficulty") not in DIFFICULTY:
            flag("difficulty_invalid_enum", sid, repr(s.get("difficulty")))

    return {k: sorted(ids) for k, ids in v.items()}, detail


def fingerprint(violations):
    payload = json.dumps({k: violations[k] for k in sorted(violations)},
                         ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--module", default="yoma")
    ap.add_argument("--targets", nargs="*", default=[],
                    help="sugya ids that must be fully compliant (target-clean)")
    ap.add_argument("--report", action="store_true", help="print the full inventory")
    ap.add_argument("--update-baseline", action="store_true",
                    help="rewrite the committed baseline (docs-tooling change)")
    args = ap.parse_args()

    data = load_daf_content(resolve_module(args.module))
    violations, detail = collect_violations(data)
    counts = {k: len(v) for k, v in sorted(violations.items())}
    total = sum(counts.values())

    print("enrichment contract gate - module %s" % args.module)
    print("  violating sugya-rule pairs: %d across %d rule(s)" % (total, len(counts)))
    for rule in sorted(counts):
        print("    %-42s %5d" % (rule, counts[rule]))
        if args.report:
            for line in detail[rule]:
                print("        %s" % line)

    if args.update_baseline:
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(json.dumps({
            "schemaVersion": 1,
            "module": args.module,
            "note": ("Frozen legacy enrichment debt. Counts may only fall. A new violating "
                     "sugya id is a failure even when totals drop. Regenerate only with "
                     "--update-baseline in a reviewed docs-tooling change."),
            "counts": counts,
            "fingerprint": fingerprint(violations),
            "violations": violations,
        }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("\nbaseline written to %s" % BASELINE.relative_to(ROOT))
        return

    if not BASELINE.exists():
        raise SystemExit("missing baseline %s; run --update-baseline in a docs-tooling change"
                         % BASELINE.relative_to(ROOT))
    base = json.loads(BASELINE.read_text(encoding="utf-8"))
    base_v = {k: set(v) for k, v in base["violations"].items()}
    problems = []

    # A rule that vanished from the code cannot be used to pass the gate.
    for rule in base_v:
        if rule not in violations and base_v[rule]:
            if rule not in counts:
                problems.append("rule %r is in the baseline but produced no result; "
                                "rules may not be deleted to pass the gate" % rule)

    improved = []
    for rule in sorted(set(list(violations.keys()) + list(base_v.keys()))):
        now = set(violations.get(rule, []))
        was = base_v.get(rule, set())
        new_ids = sorted(now - was)
        if new_ids:
            problems.append("NEW debt for %s: %s%s"
                            % (rule, ", ".join(new_ids[:6]),
                               " (+%d more)" % (len(new_ids) - 6) if len(new_ids) > 6 else ""))
        if len(now) > len(was):
            problems.append("count rose for %s: baseline %d -> now %d" % (rule, len(was), len(now)))
        elif len(now) < len(was):
            improved.append("%s: %d -> %d" % (rule, len(was), len(now)))

    for sid in args.targets:
        hits = sorted(r for r, ids in violations.items() if sid in ids)
        if hits:
            problems.append("target %s is not contract-clean: %s" % (sid, ", ".join(hits)))

    if improved:
        print("\nratchet improvements:")
        for line in improved:
            print("  %s" % line)
    if args.targets:
        print("\ntarget-clean checked for: %s" % ", ".join(args.targets))

    print()
    if problems:
        for p in problems:
            print("  FAIL %s" % p)
        raise SystemExit("enrichment contract gate FAILED (%d problem(s))" % len(problems))
    print("OK: no new enrichment-contract debt; baseline holds%s."
          % (" and %d rule(s) improved" % len(improved) if improved else ""))


if __name__ == "__main__":
    main()
