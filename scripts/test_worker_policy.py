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


def write_evidence(path, ttype="rashi-realignment", module="yoma", targets=None):
    path.write_text(json.dumps({"type": ttype, "module": module,
                                "targets": targets or []}))


def test_queue():
    print("autopilot queue (derived progress, no mutation, no main pushes):")
    with tempfile.TemporaryDirectory() as td:
        qpath = Path(td) / "q.json"
        ev = Path(td) / "evidence.json"
        base = [sys.executable, "scripts/worker_pipeline.py", "queue", "--file", str(qpath)]

        r = subprocess.run(base + ["--type", "rashi-realignment", "--module", "yoma",
                                   "--targets", "71b,41a"],
                           capture_output=True, text=True, cwd=REPO)
        check("queue creates", r.returncode == 0, r.stderr[-200:])
        q = json.loads(qpath.read_text())
        check("queue is ordered", q["targets"] == ["71b", "41a"])
        check("queue is stop-on-escalation", q["policy"] == "stop-on-escalation")
        check("definition is immutable (no runtime done field)", "done" not in q)
        check("creation says commit once with the first manifest",
              "FIRST target's manifest commit" in r.stdout)

        # No evidence yet: nothing done, head is next.
        write_evidence(ev, ttype="docs-tooling", targets=[])
        r = subprocess.run(base + ["--evidence", str(ev)],
                           capture_output=True, text=True, cwd=REPO)
        check("no matching merged evidence -> nothing done",
              "done (derived from merged PRs): none" in r.stdout)
        check("next target is the head (one PR per target)",
              "Next target: 71b. One PR for this daf only" in r.stdout)
        check("next prints the full bounded command sequence",
              "--range 71b" in r.stdout and "worker:review" in r.stdout)
        check("queue requires deploy verification before the next target",
              "deploy workflows are green" in r.stdout)
        check("queue instructs stop on escalation",
              "Stop the queue on ANY escalation condition" in r.stdout)
        check("queue never instructs a push to main",
              "git push" not in r.stdout and "push to main" not in r.stdout.replace(
                  "NEVER a direct push to main", "").replace(
                  "never pushed to main", ""))

        # Mutation is impossible: --advance is retired.
        r = subprocess.run(base + ["--advance", "71b"],
                           capture_output=True, text=True, cwd=REPO)
        check("--advance is retired (cannot mutate queue state)", r.returncode != 0)
        check("--advance error explains derivation", "derived from merged PR" in r.stdout
              or "derived from merged PR" in r.stderr)

        # Merged evidence for target 1 -> target 2 is next; file untouched.
        before = qpath.read_bytes()
        write_evidence(ev, targets=["71b"])
        r = subprocess.run(base + ["--evidence", str(ev)],
                           capture_output=True, text=True, cwd=REPO)
        check("merged 71b evidence -> 41a is next", "Next target: 41a" in r.stdout)
        check("derivation marks 71b done", "['71b']" in r.stdout)
        check("status derivation never writes the queue file",
              qpath.read_bytes() == before)

        # A merely-local/unmerged, foreign-type, or foreign-target manifest
        # is not evidence: failed or escalated targets never become done.
        write_evidence(ev, ttype="rashi-repair", targets=["71b"])
        r = subprocess.run(base + ["--evidence", str(ev)],
                           capture_output=True, text=True, cwd=REPO)
        check("foreign-type manifest advances nothing",
              "done (derived from merged PRs): none" in r.stdout)
        write_evidence(ev, targets=["12b"])
        r = subprocess.run(base + ["--evidence", str(ev)],
                           capture_output=True, text=True, cwd=REPO)
        check("out-of-queue target advances nothing",
              "done (derived from merged PRs): none" in r.stdout)
        write_evidence(ev, targets=["71b", "41a"])
        r = subprocess.run(base + ["--evidence", str(ev)],
                           capture_output=True, text=True, cwd=REPO)
        check("multi-target manifest is never evidence (one PR per daf)",
              "done (derived from merged PRs): none" in r.stdout)

        # Final-target completion: clean, no state write, no push needed.
        write_evidence(ev, targets=["41a"])
        r = subprocess.run(base + ["--evidence", str(ev)],
                           capture_output=True, text=True, cwd=REPO)
        check("final merged target -> queue complete", "Queue complete." in r.stdout)
        check("completion needs no state commit and leaves the tree clean",
              "No queue-state commit is needed" in r.stdout
              and qpath.read_bytes() == before)

        # Resume after container/session recycling: derivation is a pure
        # function of (tracked definition, origin/main evidence); a fresh
        # process with no prior state reproduces the same answer.
        r2 = subprocess.run(base + ["--evidence", str(ev)],
                            capture_output=True, text=True, cwd=REPO)
        check("completion resumes identically after recycling",
              r2.stdout == r.stdout)


def test_structural_repair_type():
    print("rashi-structural-repair task type:")
    types = wp.load_registry()
    s = types["rashi-structural-repair"]
    check("model is fable", s["model"] == "fable")
    check("escalation model is fable", s.get("escalationModel") == "fable")
    check("review policy is conditional (self-review + auto-merge gate)",
          wp.review_policy_of(s) == "conditional")
    check("one daf per PR (maxBatch 1)", s.get("maxBatch") == 1)
    check("allowStructure authorization is REQUIRED",
          s.get("requiredAuthorizations") == ["allowStructure"])
    check("mutable JSON surface is only rashiTranslations",
          s.get("allowedJsonPaths") == ["rashiTranslations"])
    check("allowlist policy stays remove-only", s["allowlistPolicy"] == "remove-only")
    et = " | ".join(s["escalationTriggers"])
    for needle in ("line ownership is ambiguous", "disagree materially",
                   "more than one daf", "allowlist growth",
                   "validator or workflow modification"):
        check(f"escalation trigger covers '{needle}'", needle in et)

    check("structure flag reserved to authorized structural manifests only",
          wp.structure_authorized(
              {"type": "rashi-structural-repair", "authorizations": ["allowStructure"]}, s)
          and not wp.structure_authorized(
              {"type": "rashi-realignment", "authorizations": ["allowStructure"]}, s)
          and not wp.structure_authorized(
              {"type": "rashi-structural-repair", "authorizations": []}, s))

    with tempfile.TemporaryDirectory() as td:
        # Ordinary types cannot even mint an allowStructure manifest.
        r = subprocess.run([sys.executable, "scripts/worker_pipeline.py", "manifest",
                            "--type", "rashi-realignment", "--module", "yoma",
                            "--range", "8a", "--authorize", "allowStructure",
                            "--out", str(Path(td) / "x.json")],
                           capture_output=True, text=True, cwd=REPO)
        check("realignment manifest cannot carry allowStructure", r.returncode != 0)

        # A structural manifest WITHOUT the authorization fails preflight.
        mpath = Path(td) / "m.json"
        subprocess.run([sys.executable, "scripts/worker_pipeline.py", "manifest",
                        "--type", "rashi-structural-repair", "--module", "yoma",
                        "--range", "8a", "--out", str(mpath)],
                       capture_output=True, text=True, cwd=REPO)
        r = subprocess.run([sys.executable, "scripts/worker_pipeline.py", "preflight",
                            "--manifest", str(mpath), "--dry-run"],
                           capture_output=True, text=True, cwd=REPO)
        check("preflight rejects structural manifest lacking allowStructure",
              r.returncode != 0 and "requires the explicit --authorize allowStructure" in r.stdout)

        # WITH the authorization the required-auth check is satisfied.
        subprocess.run([sys.executable, "scripts/worker_pipeline.py", "manifest",
                        "--type", "rashi-structural-repair", "--module", "yoma",
                        "--range", "8a", "--authorize", "allowStructure",
                        "--out", str(mpath)],
                       capture_output=True, text=True, cwd=REPO)
        r = subprocess.run([sys.executable, "scripts/worker_pipeline.py", "preflight",
                            "--manifest", str(mpath), "--dry-run"],
                           capture_output=True, text=True, cwd=REPO)
        check("authorized structural manifest passes the required-auth check",
              "requires the explicit --authorize" not in r.stdout)

        # The review gate gains the raw-parity condition, valued from the
        # authoritative source (state-independent expectation).
        # Base HEAD resolves in every environment (including CI's shallow
        # PR checkout, where origin/main may be absent); the raw-parity
        # condition is computed before any git dependency regardless.
        m = json.loads(mpath.read_text())
        conds, _ = wp.gather_review_conditions(m, types["rashi-structural-repair"],
                                               "HEAD")
        check("structural review gate checks entry-count-and-order vs raw",
              "entry-count-and-order-match-raw" in conds)
        raw_n = len([l for l in json.loads(
            (REPO / "modules/yoma/assets/talmuddev/8a.json").read_text()).get("rashi", [])
            if l and l.strip()])
        ent = json.loads((REPO / "modules/yoma/assets/learning/yoma/8a.learning.json"
                          ).read_text()).get("rashiTranslations", [])
        expected = (len(ent) == raw_n
                    and [e.get("vilnaLine") for e in ent] == list(range(1, raw_n + 1)))
        check("raw-parity condition reflects the authoritative source",
              conds["entry-count-and-order-match-raw"] == expected)


def test_structural_deferral_in_scope_validator():
    print("scope validator structural deferral (single point of truth):")
    sys.path.insert(0, str(REPO / "modules" / "yoma" / "scripts"))
    from check_rashi_pr_scope import structural_deferral
    types = wp.load_registry()
    good = {"type": "rashi-structural-repair", "targets": ["8a"],
            "authorizations": ["allowStructure"]}
    check("fresh authorized single-target structural manifest grants its daf only",
          structural_deferral(good, types, fresh=True) == {"8a"})
    check("a STALE manifest grants nothing",
          structural_deferral(good, types, fresh=False) == set())
    check("a realignment manifest grants nothing even with a forged authorization",
          structural_deferral({**good, "type": "rashi-realignment"}, types, True) == set())
    check("missing authorization grants nothing",
          structural_deferral({**good, "authorizations": []}, types, True) == set())
    check("multi-target manifest grants nothing (one daf per PR)",
          structural_deferral({**good, "targets": ["8a", "9a"]}, types, True) == set())
    check("unknown type grants nothing",
          structural_deferral({**good, "type": "nope"}, types, True) == set())


def _prof(classification, anchors, anchors_missing=None):
    """Build a minimal synthetic drift profile for anchor_poor_safe/
    drift_ok_for_type unit tests. anchors_missing defaults to the count
    of anchors whose offset is None."""
    if anchors_missing is None:
        anchors_missing = len([a for a in anchors if a.get("offset") is None])
    return {"classification": classification, "anchors": anchors,
            "anchorsFound": len(anchors) - anchors_missing,
            "anchorsMissing": anchors_missing,
            "haikuSafe": classification in ("ALIGNED", "INSUFFICIENT-ANCHORS")}


def _sr(attest_overrides=None, missing=False):
    if missing:
        return {}
    att = {"onlyOneGenuineCitation": True, "citationTranslatedOnOwnLine": True,
           "noCitationInventedMovedOrDuplicated": True, "noSemanticUncertaintyRemains": True}
    if attest_overrides:
        att.update(attest_overrides)
    return {"daf": "48b", "anchorPoorAttestation": att}


def test_anchor_poor_safe():
    print("anchor-poor-safe review-gate exception:")

    one_ok = [{"line": 16, "kind": "dafnum", "token": "11a", "offset": 0}]
    good_sr = _sr()

    # 1. ALIGNED continues to pass (exception never invoked).
    ok, key, note = wp.drift_ok_for_type("rashi-reconstruction",
                                          _prof("ALIGNED", [{"line": 4, "kind": "name",
                                                              "token": "x", "offset": 0},
                                                             {"line": 9, "kind": "name",
                                                              "token": "y", "offset": 0}]),
                                          None)
    check("1. ALIGNED passes without invoking the exception", ok and key is None)

    # 2. One genuine anchor, offset 0, no missing anchors: pass.
    ok2, reason2 = wp.anchor_poor_safe(_prof("INSUFFICIENT-ANCHORS", one_ok), good_sr)
    check("2. one anchor, offset 0, self-review attests: passes", ok2, reason2)

    # 3. One genuine anchor, nonzero offset: fail.
    bad_offset = [{"line": 16, "kind": "dafnum", "token": "11a", "offset": 3}]
    ok3, reason3 = wp.anchor_poor_safe(_prof("INSUFFICIENT-ANCHORS", bad_offset), good_sr)
    check("3. nonzero offset fails", not ok3)

    # 4. One found anchor plus one missing anchor: fail.
    two_one_missing = [{"line": 4, "kind": "name", "token": "x", "offset": 0},
                        {"line": 16, "kind": "dafnum", "token": "11a", "offset": None}]
    ok4, reason4 = wp.anchor_poor_safe(_prof("INSUFFICIENT-ANCHORS", two_one_missing), good_sr)
    check("4. one found plus one missing anchor fails (not exactly one)", not ok4)

    # 5. Zero anchors: fail.
    ok5, reason5 = wp.anchor_poor_safe(_prof("INSUFFICIENT-ANCHORS", []), good_sr)
    check("5. zero anchors fails", not ok5)

    # 6. SHIFTED: fail (2+ same-sign anchors, so exactly-one check excludes it).
    shifted_anchors = [{"line": 4, "kind": "name", "token": "x", "offset": 5},
                        {"line": 9, "kind": "name", "token": "y", "offset": 4}]
    ok6, reason6 = wp.anchor_poor_safe(_prof("SHIFTED", shifted_anchors), good_sr)
    check("6. SHIFTED fails", not ok6)
    ok6b, _, _ = wp.drift_ok_for_type("rashi-realignment", _prof("SHIFTED", shifted_anchors), good_sr)
    check("6b. SHIFTED never eligible via drift_ok_for_type either", not ok6b)

    # 7. FABRICATION-SUSPECT: fail (2+ consecutive missing anchors).
    fab_anchors = [{"line": 4, "kind": "name", "token": "x", "offset": None},
                   {"line": 9, "kind": "name", "token": "y", "offset": None}]
    ok7, reason7 = wp.anchor_poor_safe(_prof("FABRICATION-SUSPECT", fab_anchors), good_sr)
    check("7. FABRICATION-SUSPECT fails", not ok7)

    # 8. Self-review says an additional citation may exist (attestation false): fail.
    ok8, reason8 = wp.anchor_poor_safe(_prof("INSUFFICIENT-ANCHORS", one_ok),
                                        _sr({"noCitationInventedMovedOrDuplicated": False}))
    check("8. self-review flags a possible extra/invented citation: fails", not ok8)

    # 9. Self-review missing or stale (no attestation block at all): fail.
    ok9, reason9 = wp.anchor_poor_safe(_prof("INSUFFICIENT-ANCHORS", one_ok), _sr(missing=True))
    check("9a. missing self-review fails", not ok9)
    ok9b, reason9b = wp.anchor_poor_safe(_prof("INSUFFICIENT-ANCHORS", one_ok), None)
    check("9b. None self-review fails", not ok9b)

    # 10. A semantic-audit shift-candidate warning is a SEPARATE, pre-existing
    # condition (semantic-audit-zero-shift-candidates) untouched by this
    # exception; confirm it still independently blocks overall eligibility
    # even when drift-profile-ALIGNED (via the exception) passes.
    all_true = {k: True for k in wp.REVIEW_CONDITIONS}
    all_true["semantic-audit-zero-shift-candidates"] = False
    eligible10, failed10 = wp.evaluate_review_policy(all_true)
    check("10. semantic-audit-zero-shift-candidates still gates independently",
          not eligible10 and failed10 == ["semantic-audit-zero-shift-candidates"])

    # 11. The exception applies only to rashi-reconstruction/rashi-realignment;
    # any other type (including a hypothetical future one) stays at strict
    # ALIGNED-only, never granted the exception.
    for other_type in ("rashi-repair", "placeholder-backfill", "some-future-type"):
        ok11, key11, _ = wp.drift_ok_for_type(other_type,
                                               _prof("INSUFFICIENT-ANCHORS", one_ok), good_sr)
        check(f"11. {other_type} does not get the anchor-poor-safe exception",
              not ok11 and key11 is None)

    # 12. rashi-structural-repair keeps its existing (broader, unconditional)
    # haiku-safe policy untouched: INSUFFICIENT-ANCHORS with NO anchors at
    # all and NO self-review attestation still passes for structural repair,
    # proving its policy was not narrowed or otherwise changed by this PR.
    ok12, key12, _ = wp.drift_ok_for_type(wp.STRUCTURAL_TYPE,
                                           _prof("INSUFFICIENT-ANCHORS", []), None)
    check("12. rashi-structural-repair keeps its own unconditional haiku-safe policy",
          ok12 and key12 is None)

    # Full dispatch sanity: the anchor-poor-safe path reports its own
    # distinct condition key (not silently folded into drift-profile-ALIGNED).
    okA, keyA, noteA = wp.drift_ok_for_type("rashi-reconstruction",
                                             _prof("INSUFFICIENT-ANCHORS", one_ok), good_sr)
    check("dispatch: anchor-poor-safe reports its own distinct condition key",
          okA and keyA == "anchor-poor-safe" and "anchor-poor-safe" in noteA)
    okB, keyB, noteB = wp.drift_ok_for_type("rashi-realignment",
                                             _prof("INSUFFICIENT-ANCHORS", []), good_sr)
    check("dispatch: a failing exception attempt still reports the distinct key (for visibility)",
          not okB and keyB == "anchor-poor-safe")


def test_no_direct_main_push_anywhere():
    print("no automation path instructs a direct push to main:")
    src = (REPO / "scripts" / "worker_pipeline.py").read_text()
    check("pipeline source never invokes git push",
          '"push"' not in src and "'push'" not in src)
    with tempfile.TemporaryDirectory() as td:
        mpath = Path(td) / "m.json"
        subprocess.run([sys.executable, "scripts/worker_pipeline.py", "manifest",
                        "--type", "rashi-realignment", "--module", "yoma",
                        "--range", "71b", "--out", str(mpath)],
                       capture_output=True, text=True, cwd=REPO)
        r = subprocess.run([sys.executable, "scripts/worker_pipeline.py", "prompt",
                            "--manifest", str(mpath)],
                           capture_output=True, text=True, cwd=REPO)
        check("conditional prompt routes main changes through the PR only",
              "push, ONE PR" in r.stdout)
        check("conditional prompt states queue progress derives from the merge",
              "derives" in r.stdout and "NEVER a direct push to main" in r.stdout)


def main():
    test_registry()
    test_pure_policy()
    test_live_gate_fails_closed()
    test_prompt()
    test_queue()
    test_structural_repair_type()
    test_anchor_poor_safe()
    test_structural_deferral_in_scope_validator()
    test_no_direct_main_push_anywhere()
    if FAILURES:
        print(f"\nFAILED: {len(FAILURES)} check(s): {FAILURES}")
        sys.exit(1)
    print("\nOK: all worker policy tests passed.")


if __name__ == "__main__":
    main()
