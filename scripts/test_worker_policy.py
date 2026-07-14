#!/usr/bin/env python3
"""
test_worker_policy.py - tests for the conditional semantic-review policy
and the sequential autopilot queue (scripts/worker_pipeline.py).

Pins the VERSION 15.93 process change: rashi-realignment and
rashi-reconstruction no longer require an unconditional Fable review per
PR. Instead a Sonnet worker performs a fresh post-edit self-review and a
machine-checked auto-merge gate (worker:review) decides eligibility;
every failed condition escalates to Fable and blocks merge.

Layers:
1. Registry: the two semantic types carry reviewPolicy conditional with
   escalationModel fable; the mechanical types keep their unconditional
   Fable review; the self-review and queue files are in scope.
2. Pure policy: all conditions true -> eligible (no Fable needed); EVERY
   single condition false -> blocked (negative test per condition).
3. Live gate: worker:review on a no-diff tree is blocked (nothing to
   merge, no fresh self-review), proving the gate fails closed.
4. Prompt: conditional prompts carry the self-review, auto-merge, and
   escalation instructions and never a may-not-merge Fable line.
5. Queue: create/next/advance are sequential, one PR per target,
   stop-on-escalation; out-of-order advance is rejected.

Run: python3 scripts/test_worker_policy.py   (cwd repo root)
Exit 0 on success, 1 on failure.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))
import worker_pipeline as wp

FAILURES = []
CONDITIONAL_TYPES = ("rashi-realignment", "rashi-reconstruction")
# placeholder-backfill keeps its unconditional Fable review; rashi-repair
# was already haiku-safe with no per-PR Fable review (drift block gates it).
FABLE_TYPES = ("placeholder-backfill",)


def check(name, cond, detail=""):
    status = "ok" if cond else "FAIL"
    print(f"  {status}  {name}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        FAILURES.append(name)


def test_registry():
    print("registry review policy:")
    types = wp.load_registry()
    for t in CONDITIONAL_TYPES:
        s = types[t]
        check(f"{t} reviewPolicy is conditional", wp.review_policy_of(s) == "conditional")
        check(f"{t} escalationModel is fable", s.get("escalationModel") == "fable")
        check(f"{t} has no unconditional fableReviewRequired",
              not s.get("fableReviewRequired"))
        check(f"{t} worker model stays sonnet", s.get("model") == "sonnet")
        check(f"{t} still one daf per PR (maxBatch 1)", s.get("maxBatch") == 1)
        check(f"{t} allows the self-review attestation file",
              ".worker-self-review.json" in s["allowedFiles"])
        check(f"{t} allows the queue file", ".worker-queue.json" in s["allowedFiles"])
        et = " | ".join(s["escalationTriggers"])
        for needle in ("packet id missing", "allowlist growth", "not ALIGNED",
                       "self-review finds a blocker", "more than one daf",
                       "validator or workflow modification",
                       "fields outside the manifest",
                       "CI or full verification fails"):
            check(f"{t} escalation trigger covers '{needle}'", needle in et)
    for t in FABLE_TYPES:
        check(f"{t} keeps unconditional Fable review",
              wp.review_policy_of(types[t]) == "fable")


def test_pure_policy():
    print("pure auto-merge policy:")
    all_true = {k: True for k in wp.REVIEW_CONDITIONS}
    eligible, failed = wp.evaluate_review_policy(all_true)
    check("all conditions true -> AUTO-MERGE eligible without Fable",
          eligible and not failed)
    for c in wp.REVIEW_CONDITIONS:
        conds = dict(all_true)
        conds[c] = False
        eligible, failed = wp.evaluate_review_policy(conds)
        check(f"single failure blocks merge: {c}",
              not eligible and failed == [c])


def test_live_gate_fails_closed():
    print("live worker:review gate (no diff, no self-review):")
    with tempfile.TemporaryDirectory() as td:
        mpath = Path(td) / "m.json"
        r = subprocess.run([sys.executable, "scripts/worker_pipeline.py", "manifest",
                            "--type", "rashi-realignment", "--module", "yoma",
                            "--range", "70a", "--out", str(mpath)],
                           capture_output=True, text=True, cwd=REPO)
        check("manifest generates with policy fields", r.returncode == 0)
        m = json.loads(mpath.read_text())
        check("manifest carries reviewPolicy conditional",
              m.get("reviewPolicy") == "conditional")
        check("manifest carries escalationModel fable",
              m.get("escalationModel") == "fable")
        rr = subprocess.run([sys.executable, "scripts/worker_pipeline.py", "review",
                             "--manifest", str(mpath)],
                            capture_output=True, text=True, cwd=REPO)
        check("gate blocks when unsafe conditions appear (exit nonzero)",
              rr.returncode != 0)
        check("gate names the escalation model", "ESCALATE to fable" in rr.stdout)
        check("gate reports the missing fresh self-review",
              "fresh-self-review-committed-and-clean" in rr.stdout)
        check("gate never prints eligibility on failure",
              "AUTO-MERGE-ELIGIBLE" not in rr.stdout)


def test_prompt():
    print("conditional prompt:")
    with tempfile.TemporaryDirectory() as td:
        mpath = Path(td) / "m.json"
        subprocess.run([sys.executable, "scripts/worker_pipeline.py", "manifest",
                        "--type", "rashi-realignment", "--module", "yoma",
                        "--range", "71b", "--out", str(mpath)],
                       capture_output=True, text=True, cwd=REPO)
        r = subprocess.run([sys.executable, "scripts/worker_pipeline.py", "prompt",
                            "--manifest", str(mpath)],
                           capture_output=True, text=True, cwd=REPO)
        out = r.stdout
        check("prompt runs clean", r.returncode == 0, r.stderr[-200:])
        check("prompt mandates the fresh post-edit self-review",
              "Fresh post-edit self-review (MANDATORY" in out)
        check("prompt covers beginning/middle/tail recheck",
              "beginning, middle," in out)
        check("prompt covers citation anchors and multi-id links",
              "citation anchor" in out and "multi-id link" in out)
        check("prompt covers formerly allowlisted and truncated boundary entries",
              "formerly allowlisted" in out and "truncated boundary" in out)
        check("prompt forbids positional linking",
              "vilna line number or positional offset" in out)
        check("prompt requires worker:review before merge",
              "npm run worker:review" in out and "AUTO-MERGE-ELIGIBLE" in out)
        check("prompt authorizes merge without operator sign-off",
              "No operator authorization is needed" in out)
        check("prompt continues to the next queued target",
              "next queued target" in out)
        check("prompt does NOT carry the unconditional Fable no-merge line",
              "may NOT merge" not in out)
        check("prompt escalates to fable", "hand off to fable" in out)


def test_queue():
    print("autopilot queue:")
    with tempfile.TemporaryDirectory() as td:
        qpath = Path(td) / "q.json"
        base = [sys.executable, "scripts/worker_pipeline.py", "queue", "--file", str(qpath)]
        r = subprocess.run(base + ["--type", "rashi-realignment", "--module", "yoma",
                                   "--targets", "71b,41a"],
                           capture_output=True, text=True, cwd=REPO)
        check("queue creates", r.returncode == 0, r.stderr[-200:])
        q = json.loads(qpath.read_text())
        check("queue is ordered", q["targets"] == ["71b", "41a"])
        check("queue is stop-on-escalation", q["policy"] == "stop-on-escalation")
        r = subprocess.run(base, capture_output=True, text=True, cwd=REPO)
        check("next target is the head (one PR per target)",
              "Next target: 71b. One PR for this daf only" in r.stdout)
        check("next prints the full bounded command sequence",
              "--range 71b" in r.stdout and "worker:review" in r.stdout)
        check("queue instructs stop on escalation",
              "Stop the queue on ANY escalation condition" in r.stdout)
        r = subprocess.run(base + ["--advance", "41a"],
                           capture_output=True, text=True, cwd=REPO)
        check("out-of-order advance rejected", r.returncode != 0)
        r = subprocess.run(base + ["--advance", "71b"],
                           capture_output=True, text=True, cwd=REPO)
        check("sequential advance works", r.returncode == 0)
        r = subprocess.run(base, capture_output=True, text=True, cwd=REPO)
        check("queue then serves 41a", "Next target: 41a" in r.stdout)
        r = subprocess.run(base + ["--advance", "41a"],
                           capture_output=True, text=True, cwd=REPO)
        r = subprocess.run(base, capture_output=True, text=True, cwd=REPO)
        check("drained queue reports complete", "Queue complete." in r.stdout)


def main():
    test_registry()
    test_pure_policy()
    test_live_gate_fails_closed()
    test_prompt()
    test_queue()
    if FAILURES:
        print(f"\nFAILED: {len(FAILURES)} check(s): {FAILURES}")
        sys.exit(1)
    print("\nOK: all worker policy tests passed.")


if __name__ == "__main__":
    main()
