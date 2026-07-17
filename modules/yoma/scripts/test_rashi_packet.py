#!/usr/bin/env python3
"""
test_rashi_packet.py - regression tests for the Rashi work packet
generator (make_rashi_work_packet.py) and the generated worker guidance
(rashi_prompt.py, scripts/worker_pipeline.py prompt).

Root cause pinned here (found in PR #80 review, VERSION 15.90): the
packet's segment table collected only kind "gemara" segments, so the
end-of-perek Mishnah yoma-068b-l13b was missing from 68b's legal id
table. Without that anchor the worker fell back to positional linking
(Rashi line N to the segment at vilna N), and Fable review had to
correct 50 of 60 links. These tests fail if any part of the fix
regresses:

1. the 68b table includes l13b, kind "mishna", in source order
2. sparse and suffixed ids are preserved verbatim (no dense renumbering,
   no manufactured ids)
3. full untruncated segment text is present (the old table cut at 60
   chars)
4. every id actually used by linkedGemaraLineIds across the corpus is
   present in its daf's packet table (packet-side referential
   completeness; validate_rashi_links covers the data side)
5. the generated packet, the generated per-daf prompt, and the pipeline
   prompt all forbid positional linking
6. no previously valid Gemara id was lost from the 68b table

Run: python3 scripts/test_rashi_packet.py   (cwd modules/yoma)
Exit 0 on success, 1 on failure.
"""
import json
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

SCRIPTS = Path(__file__).parent
ROOT = SCRIPTS.parent
REPO = ROOT.parent.parent
LEARN_DIR = ROOT / "assets" / "learning" / "yoma"

sys.path.insert(0, str(SCRIPTS))
import make_rashi_work_packet as pkt

FAILURES = []

# The 19 Gemara ids the 68b table held before the fix (PR #80 record);
# none may ever disappear from the table.
EXPECTED_68B_GEMARA = [
    "l01", "l02", "l06", "l07", "l10", "l13a", "l15", "l18", "l21", "l23",
    "l24", "l25", "l29", "l32", "l35", "l36", "l38", "l39", "l42",
]

ANTI_POSITIONAL_NEEDLES = ("vilna line number or positional offset",)

# Pre-existing corpus debt, documented in docs/rashi-audit-backlog.md and
# tolerated here SELF-RETIRINGLY: on these daf a few early Rashi entries
# link to a plain lNN id that exists only as an argumentFlow step id (the
# real first segments are suffix-split l01a/l01b). validate_rashi_links
# accepts them because its legal-id regex also matches argumentFlow ids.
# When a future links pass repairs these, delete the entry here and the
# strict check takes over. Never add entries.
KNOWN_PHANTOM_LINKS = {
    "43a": {"yoma-043a-l01"},
    "43b": {"yoma-043b-l01"},
    "44b": {"yoma-044b-l01"},
}


def check(name, cond, detail=""):
    status = "ok" if cond else "FAIL"
    print(f"  {status}  {name}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        FAILURES.append(name)


def strip_nikud(s):
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if not unicodedata.combining(c))


def test_68b_segment_table():
    print("68b segment table (PR #80 regression):")
    segs = pkt.local_segments_for("68b")
    ids = [s["id"] for s in segs]
    by_id = {s["id"]: s for s in segs}

    check("l13b present", "yoma-068b-l13b" in ids)
    if "yoma-068b-l13b" in by_id:
        check("l13b kind is mishna", by_id["yoma-068b-l13b"]["kind"] == "mishna",
              by_id["yoma-068b-l13b"]["kind"])
        check("l13b full text untruncated (old cut was 60 chars)",
              len(by_id["yoma-068b-l13b"]["he"]) > 60,
              str(len(by_id["yoma-068b-l13b"]["he"])))
        tail = strip_nikud(by_id["yoma-068b-l13b"]["he"][60:])
        check("l13b text reaches its own tail (not an opening excerpt)",
              "שהגיע" in tail)
    if "yoma-068b-l13a" in ids and "yoma-068b-l13b" in ids and "yoma-068b-l15" in ids:
        check("l13b in source order (after l13a, before l15)",
              ids.index("yoma-068b-l13a") < ids.index("yoma-068b-l13b")
              < ids.index("yoma-068b-l15"))
    for short in EXPECTED_68B_GEMARA:
        full = f"yoma-068b-{short}"
        check(f"pre-fix id {short} still present", full in ids)
    check("suffixed sibling ids both preserved (l13a and l13b)",
          "yoma-068b-l13a" in ids and "yoma-068b-l13b" in ids)
    check("sparse gaps preserved, no manufactured dense ids",
          all(f"yoma-068b-l{n:02d}" not in ids for n in (3, 4, 5, 8, 9)))
    check("every segment carries a kind",
          all(s.get("kind") in ("gemara", "mishna") for s in segs))
    check("every segment carries full nonempty text",
          all(s.get("he") for s in segs))


def test_corpus_link_completeness():
    print("packet-side referential completeness (all daf, self-retiring debt list):")
    missing, retired = [], []
    for lp in sorted(LEARN_DIR.glob("*.learning.json")):
        daf = lp.name.replace(".learning.json", "")
        used = set()
        for e in json.loads(lp.read_text()).get("rashiTranslations", []):
            used.update(e.get("linkedGemaraLineIds", []))
        if not used:
            continue
        table = {s["id"] for s in pkt.local_segments_for(daf)}
        known = KNOWN_PHANTOM_LINKS.get(daf, set())
        gone = sorted(used - table - known)
        if gone:
            missing.append(f"{daf}: {gone}")
        if known and not (used & known):
            retired.append(daf)
    check("every linked id appears in its daf's packet table "
          "(beyond the documented 43a/43b/44b debt)", not missing,
          "; ".join(missing[:5]))
    for daf in retired:
        print(f"  note  {daf} phantom links drained; remove its "
              f"KNOWN_PHANTOM_LINKS entry")


def test_packet_forbids_positional_linking():
    print("generated packet guidance:")
    p = pkt.packet_for("68b")
    md = pkt.to_markdown(p)
    check("packet rules state links are semantic",
          any("SEMANTIC text anchors" in r for r in p["rules"]))
    check("packet rules forbid positional linking",
          any(all(n in r for n in ANTI_POSITIONAL_NEEDLES) and "NEVER" in r
              for r in p["rules"]))
    check("packet rules allow multi-segment links when genuine",
          any("multiple local segments" in r for r in p["rules"]))
    check("packet rules bound the boundary policy",
          any("never justifies linking unrelated commentary" in r
              for r in p["rules"]))
    check("markdown id table admits Gemara AND Mishnah",
          "Gemara AND Mishnah" in md)
    check("markdown id table shows l13b with its kind",
          "yoma-068b-l13b [mishna]" in md)
    check("markdown warns against positional mapping near the table",
          "positional offset" in md)


def test_generated_prompts_forbid_positional_linking():
    print("generated prompts:")
    r = subprocess.run([sys.executable, "scripts/rashi_prompt.py", "68b",
                        "--task", "shifted-block"],
                       capture_output=True, text=True, cwd=ROOT)
    check("rashi_prompt runs clean", r.returncode == 0, r.stderr[-200:])
    check("rashi_prompt forbids positional linking",
          all(n in r.stdout for n in ANTI_POSITIONAL_NEEDLES))
    check("rashi_prompt says links are semantic", "SEMANTIC" in r.stdout)

    with tempfile.TemporaryDirectory() as td:
        mpath = Path(td) / "manifest.json"
        rm = subprocess.run([sys.executable, "scripts/worker_pipeline.py",
                             "manifest", "--type", "rashi-realignment",
                             "--module", "yoma", "--range", "68b",
                             "--out", str(mpath)],
                            capture_output=True, text=True, cwd=REPO)
        check("pipeline manifest generates", rm.returncode == 0, rm.stderr[-200:])
        rp = subprocess.run([sys.executable, "scripts/worker_pipeline.py",
                             "prompt", "--manifest", str(mpath)],
                            capture_output=True, text=True, cwd=REPO)
        check("pipeline prompt runs clean", rp.returncode == 0, rp.stderr[-200:])
        check("pipeline prompt forbids positional linking",
              all(n in rp.stdout for n in ANTI_POSITIONAL_NEEDLES))
        check("pipeline prompt states the semantic contract",
              "SEMANTIC text anchors" in rp.stdout)


def test_registry_escalation():
    print("registry escalation triggers:")
    reg = json.loads((REPO / "scripts" / "worker_task_types.json").read_text())
    for t in ("rashi-repair", "rashi-reconstruction", "rashi-realignment",
              "placeholder-backfill"):
        et = reg["taskTypes"][t]["escalationTriggers"]
        check(f"{t} escalates on unidentifiable target segment",
              any("never link positionally" in e for e in et))


def main():
    test_68b_segment_table()
    test_corpus_link_completeness()
    test_packet_forbids_positional_linking()
    test_generated_prompts_forbid_positional_linking()
    test_registry_escalation()
    if FAILURES:
        print(f"\nFAILED: {len(FAILURES)} check(s): {FAILURES}")
        sys.exit(1)
    print("\nOK: all Rashi packet tests passed.")


if __name__ == "__main__":
    main()
