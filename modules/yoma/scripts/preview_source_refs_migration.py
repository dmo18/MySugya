#!/usr/bin/env python3
"""
preview_source_refs_migration.py - dry-run preview of sourceRefs
normalization. Never writes. There is no --apply flag by design.

Normalizing sourceRefs to the canonical object form is a structural-repair
change to modules/yoma/assets/learning/*, which docs-tooling may not touch.
This script exists so the migration can be reviewed in full before any such
pass is authorized, and so its lossless subset is demonstrated rather than
asserted.

It emits, per candidate ref, the exact before/after value and the evidence
that justifies it, plus a losslessness report over the whole corpus. It
refuses to propose anything for refs where two in-repo coordinates disagree
and both name a real line: those need a human reading the step text against
the Gemara, and guessing one would fabricate an anchor.

  --json            machine-readable preview
  --show-blocked    list the refs that cannot be settled mechanically
  --daf <daf>       limit to one daf
"""
import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import validate_source_refs as vsr  # noqa: E402  (same-directory helper)

LEARN_DIR = vsr.LEARN_DIR


def plan_for_daf(daf, sugyot):
    """Return (proposals, blocked, stats) for one daf.

    A proposal is only produced when the target is uniquely determined by
    data already in the repository.
    """
    anchors = vsr.build_anchor_table(vsr.derive_line_ids(sugyot))
    by_id = {a["id"]: a for a in anchors}
    by_sefaria = defaultdict(list)
    for a in anchors:
        if a["sefariaRef"]:
            by_sefaria[a["sefariaRef"]].append(a)

    proposals, blocked = [], []
    stats = Counter()

    for sugya in sugyot:
        for step in (sugya.get("argumentFlow") or []):
            refs = step.get("sourceRefs") or []
            for idx, ref in enumerate(refs):
                loc = {"daf": daf, "sugyaId": sugya.get("id"),
                       "stepId": step.get("id"), "refIndex": idx}

                if isinstance(ref, str):
                    hits = by_sefaria.get(ref, [])
                    if len(hits) != 1:
                        stats["string_unresolvable"] += 1
                        blocked.append({**loc, "reason": "string ref does not "
                                        "resolve to exactly one line id",
                                        "before": ref,
                                        "candidates": [h["id"] for h in hits]})
                        continue
                    a = hits[0]
                    # lineId and vilnaLine ARE mechanically derivable here, but
                    # the canonical object form also requires sourceType, which
                    # the string form does not carry. sourceType is not a
                    # function of the line's kind: the corpus types 15 refs on
                    # Mishnah lines as "gemara", and spells the Mishnah value
                    # both "mishnah" and "mishna". Synthesizing it would invent
                    # metadata, so this conversion is information-adding rather
                    # than lossless and stays blocked.
                    stats["string_blocked_on_sourcetype"] += 1
                    blocked.append({
                        **loc,
                        "reason": "string-to-object needs a sourceType the string "
                                  "form does not carry and that cannot be derived "
                                  "from the line's kind",
                        "before": ref,
                        "derivable": {"lineId": a["id"], "vilnaLine": a["vilnaLine"]},
                        "undeterminable": ["sourceType"],
                    })
                    continue

                if not isinstance(ref, dict):
                    stats["blocked_other"] += 1
                    blocked.append({**loc, "reason": "ref is neither string nor object",
                                    "before": repr(ref)})
                    continue

                line_id, vilna = ref.get("lineId"), ref.get("vilnaLine")
                anchor = by_id.get(line_id)
                if anchor is not None:
                    if vilna is None:
                        stats["blocked_no_vilna"] += 1
                        blocked.append({**loc, "reason": "object ref has no vilnaLine",
                                        "before": ref})
                    elif anchor["start"] <= vilna < anchor["end"]:
                        stats["already_canonical"] += 1
                    else:
                        stats["blocked_conflict"] += 1
                        blocked.append({
                            **loc,
                            "reason": "lineId and vilnaLine disagree and both name "
                                      "a real line; only the step text can settle it",
                            "before": ref,
                            "lineIdCovers": [anchor["start"], anchor["end"]],
                            "vilnaLineWouldBe": [c["id"] for c in anchors
                                                 if c["start"] <= vilna < c["end"]],
                        })
                    continue

                # lineId does not exist: repairable only if vilnaLine lands in
                # exactly one interval.
                if vilna is None:
                    stats["blocked_no_vilna"] += 1
                    blocked.append({**loc, "reason": "dangling lineId and no vilnaLine",
                                    "before": ref})
                    continue
                cands = [c for c in anchors if c["start"] <= vilna < c["end"]]
                if len(cands) == 1:
                    stats["lineid_repair"] += 1
                    after = dict(ref)
                    after["lineId"] = cands[0]["id"]
                    proposals.append({
                        **loc, "kind": "dangling-lineid-repair", "before": ref,
                        "after": after,
                        "evidence": f"vilnaLine {vilna} falls only inside "
                                    f"{cands[0]['id']} [{cands[0]['start']},"
                                    f"{cands[0]['end']})",
                    })
                else:
                    stats["blocked_ambiguous"] += 1
                    blocked.append({
                        **loc,
                        "reason": "dangling lineId; vilnaLine falls inside several "
                                  "split sub-lines, and picking one would invent an anchor",
                        "before": ref, "candidates": [c["id"] for c in cands],
                    })

    return proposals, blocked, stats


def losslessness_report(proposals):
    """Check the invariants a migration must preserve.

    Every invariant here is about what the proposals do NOT change: order,
    count, the vilnaLine coordinate, notes, and the target line's identity.
    """
    checks = []

    changed_vilna = [p for p in proposals
                     if p["kind"] == "dangling-lineid-repair"
                     and p["after"].get("vilnaLine") != p["before"].get("vilnaLine")]
    checks.append(("vilnaLine preserved on every lineId repair", not changed_vilna, len(changed_vilna)))

    dropped_notes = [p for p in proposals
                     if isinstance(p["before"], dict) and p["before"].get("note")
                     and p["after"].get("note") != p["before"].get("note")]
    checks.append(("note preserved on every object rewrite", not dropped_notes, len(dropped_notes)))

    dropped_type = [p for p in proposals
                    if isinstance(p["before"], dict)
                    and p["after"].get("sourceType") != p["before"].get("sourceType")]
    checks.append(("sourceType preserved on every object rewrite", not dropped_type, len(dropped_type)))

    synthesized = [p for p in proposals
                   if not isinstance(p["before"], dict)]
    checks.append(("no proposal invents a field the source ref did not carry",
                   not synthesized, len(synthesized)))

    changed_keys = [p for p in proposals
                    if isinstance(p["before"], dict)
                    and set(p["after"]) != set(p["before"])]
    checks.append(("proposals change values only, never the key set",
                   not changed_keys, len(changed_keys)))

    no_evidence = [p for p in proposals if not p.get("evidence")]
    checks.append(("every proposal carries in-repo evidence", not no_evidence, len(no_evidence)))

    return checks


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--show-blocked", action="store_true")
    ap.add_argument("--daf")
    args = ap.parse_args()

    paths = sorted(LEARN_DIR.glob("*.learning.json"))
    if args.daf:
        paths = [p for p in paths if p.name == f"{args.daf}.learning.json"]
        if not paths:
            sys.exit(f"ERROR: no enrichment file for daf {args.daf}")

    all_prop, all_blocked, stats = [], [], Counter()
    for path in paths:
        daf, sugyot = vsr.load_daf(path)
        p, b, s = plan_for_daf(daf, sugyot)
        all_prop.extend(p)
        all_blocked.extend(b)
        stats.update(s)

    checks = losslessness_report(all_prop)
    prop_daf = sorted({p["daf"] for p in all_prop})
    blocked_daf = sorted({b["daf"] for b in all_blocked})

    if args.json:
        print(json.dumps({
            "dryRun": True, "wrote": False,
            "stats": dict(stats),
            "proposalCount": len(all_prop), "blockedCount": len(all_blocked),
            "proposalDaf": prop_daf, "blockedDaf": blocked_daf,
            "losslessness": [{"check": c, "pass": ok, "violations": n} for c, ok, n in checks],
            "proposals": all_prop, "blocked": all_blocked,
        }, indent=2, ensure_ascii=False))
        return

    print("sourceRefs migration preview - DRY RUN, nothing is written\n")
    print(f"  files examined      : {len(paths)}")
    for k, v in sorted(stats.items()):
        print(f"    {k}: {v}")
    print(f"\n  proposals           : {len(all_prop)} across {len(prop_daf)} daf")
    print(f"  blocked             : {len(all_blocked)} across {len(blocked_daf)} daf")

    print("\n  losslessness of the proposed subset:")
    for check, ok, n in checks:
        print(f"    [{'PASS' if ok else 'FAIL'}] {check}" + ("" if ok else f" ({n} violation(s))"))

    by_kind = Counter(p["kind"] for p in all_prop)
    print("\n  proposal kinds:")
    for k, v in by_kind.most_common():
        print(f"    {k}: {v}")

    if all_prop:
        print("\n  sample proposals:")
        for p in all_prop[:5]:
            print(f"    {p['daf']} {p['sugyaId']} {p['stepId']}[{p['refIndex']}] {p['kind']}")
            print(f"      before: {p['before']}")
            print(f"      after : {p['after']}")
            print(f"      why   : {p['evidence']}")

    if args.show_blocked:
        print(f"\n  blocked refs ({len(all_blocked)}):")
        for b in all_blocked:
            print(f"    {b['daf']} {b['sugyaId']} {b['stepId']}[{b['refIndex']}]")
            print(f"      before: {b['before']}")
            print(f"      reason: {b['reason']}")
            if b.get("candidates"):
                print(f"      candidates: {b['candidates']}")
            if b.get("vilnaLineWouldBe"):
                print(f"      lineId covers {b['lineIdCovers']}, "
                      f"vilnaLine points at {b['vilnaLineWouldBe']}")
    elif all_blocked:
        print("\n  run with --show-blocked to list every blocked ref.")

    print("\nNo files were modified. Applying this migration requires a "
          "structural-repair pass; see docs/reports/source-refs-normalization-plan.md.")


if __name__ == "__main__":
    main()
