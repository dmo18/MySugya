#!/usr/bin/env python3
"""
rashi_prompt.py - generate a compact, deterministic task prompt for a
bounded Sonnet worker Rashi pass, so operators do not hand-write
prompts and workers do not re-derive context.

Usage:
  python3 scripts/rashi_prompt.py 47a --task reconstruct
  python3 scripts/rashi_prompt.py 41a --task shifted-block
  python3 scripts/rashi_prompt.py 61a --task repair-stubs

Task types:
  reconstruct    full line-by-line helper reconstruction for the daf
  repair-stubs   replace documented stub/filler lines with genuine helpers
  shifted-block  remap a documented shifted-English block line by line
  links          repair linkedGemaraLineIds only (no en changes)

The prompt embeds the per-daf summary numbers, the allowed/forbidden file
rules, escalation triggers, the worker lockout rules, and the exact
command sequence (preflight, packet, verify). The full raw Hebrew comes
from the packet command, not from this prompt, to keep the prompt small.
"""
import argparse
import json
import re
import sys
from pathlib import Path

SCRIPTS = Path(__file__).parent
ROOT = SCRIPTS.parent
LEARN_DIR = ROOT / "assets" / "learning" / "yoma"
TALMUDDEV_DIR = ROOT / "assets" / "talmuddev"
ALLOW_DIR = SCRIPTS / "allowlists"

TASK_BRIEFS = {
    "reconstruct": "Reconstruct this daf's Rashi helper layer: translate EVERY raw Hebrew line genuinely, line by line, from its own Hebrew.",
    "repair-stubs": "Replace this daf's documented stub/filler helper lines with genuine translations of their own raw Hebrew. Touch only the listed lines.",
    "shifted-block": "Repair this daf's documented shifted-English block: re-derive which raw Hebrew each en describes, then rewrite each affected line so its en matches its OWN raw line. Touch only the affected block.",
    "links": "Repair this daf's linkedGemaraLineIds only. Do not change any en text.",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("daf")
    ap.add_argument("--task", required=True, choices=sorted(TASK_BRIEFS))
    opts = ap.parse_args()
    daf = opts.daf
    if not re.match(r"^\d+[ab]$", daf):
        sys.exit(f"ERROR: malformed daf {daf!r}")
    td = TALMUDDEV_DIR / f"{daf}.json"
    if not td.exists():
        sys.exit(f"ERROR: no talmuddev source for {daf}")

    raw_n = len([l for l in json.loads(td.read_text()).get("rashi", []) if l and l.strip()])
    lp = LEARN_DIR / f"{daf}.learning.json"
    trans_n = len(json.loads(lp.read_text()).get("rashiTranslations", [])) if lp.exists() else 0
    ca = json.loads((ALLOW_DIR / "rashi_content_allowlist.json").read_text())
    hits = sorted(e["vilnaLine"] for e in ca.get("entries", []) if e["daf"] == daf)
    sb = SCRIPTS / "baselines" / "rashi_scaffold_debt.json"
    scaffold_n = (sum(1 for e in json.loads(sb.read_text()).get("entries", [])
                      if e["daf"] == daf) if sb.exists() else 0)

    preflight_task = {"reconstruct": "reconstruct", "repair-stubs": "repair",
                      "shifted-block": "shifted-block", "links": "links"}[opts.task]

    print(f"""Run a bounded Yoma {daf} Rashi pass: {opts.task}.

{TASK_BRIEFS[opts.task]}

State: raw Rashi lines {raw_n}, current rashiTranslations {trans_n}, documented allowlisted lines {hits or 'none'}, scaffold-debt lines {scaffold_n}.

Procedure (exact, in order):
1. git fetch origin main and reconcile; confirm clean tree.
2. npm run rashi:preflight:yoma -- {daf} --task {preflight_task}
   If preflight fails, STOP and report. Do not work around it.
3. npm run rashi:packet:yoma -- {daf}
   The packet is your ONLY context source: raw Hebrew (ground truth), the
   only legal Gemara ids, current entries, baselines, rules.
4. Edit ONLY modules/yoma/assets/learning/yoma/{daf}.learning.json, and
   ONLY rashiTranslations en{' and linkedGemaraLineIds' if opts.task != 'links' else ''}{' (en must not change)' if opts.task == 'links' else ''}.
5. Regenerate: cd modules/yoma && python3 scripts/build_learning_data.py
   && python3 scripts/build_literal_layer.py --apply
6. Bump VERSION one patch; python3 scripts/sync_version.py
7. npm run rashi:verify:yoma -- {daf} --fast
   then npm run rashi:verify:yoma -- {daf} --full
   Every gate must pass. If the verify summary says stale allowlist
   entries exist for lines you fixed, remove EXACTLY those entries and
   re-run verify.
8. Commit (title: "Fix Yoma {daf} Rashi helpers" or as instructed), push,
   open one PR, wait for CI, merge only when green, verify main deploys.

Hard rules (mechanically enforced; violations fail CI):
- linkedGemaraLineIds are SEMANTIC text anchors. Link each Rashi comment
  to the local segment(s) whose text it explains, matched against the
  packet's full segment text (Gemara and Mishnah ids alike). NEVER
  assign links by vilna line number or positional offset. A comment may
  link to multiple segments when it genuinely spans them. Boundary
  policy (staying on the final id past the last segment) never covers
  unrelated commentary. If the correct target segment cannot be
  identified from the packet, stop and escalate; never guess.
- You may not ADD allowlist or baseline entries, ever.
- You may not edit validators, scripts, workflows, hooks, or any other daf.
- You may not edit he, sugyot, argumentFlow, learning, takeaway, glossary,
  quizSeeds, or metadata fields.
- No placeholder, filler, or template text; every en must render its own
  raw Hebrew line. No em dashes or en dashes.
- No scaffold narration ("Rashi: opens/continues/concludes ...") and no
  guessed bracket completions such as "[the Gemara]". Even where the old
  wording was partly correct, rewrite it as a direct translation of its
  own Hebrew; audit_rashi_scaffold.py fails CI on any scaffold text, and
  a reconstruction/realignment must drain its daf's scaffold-debt
  baseline entries to zero (retire them with --update-baseline).
- A validator failure means the content is wrong: fix the content or STOP.
  Never reinterpret, bypass, or weaken a gate.

Escalate (stop immediately and report) on: uncertain Hebrew meaning,
uncertain placement, count mismatches not already baselined, new semantic
audit shift candidates on {daf} beyond offset +-1, any need to touch a
file outside step 4's scope, or any gate failure you cannot fix by
correcting your own content.

Only after local verify --full passes may CI/deploy polling be handled
mechanically. Report one compact line after merge + deploy verification.""")


if __name__ == "__main__":
    main()
