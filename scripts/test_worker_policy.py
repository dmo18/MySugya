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


def _prof(classification, anchors, anchors_missing=None, offsets=None):
    """Build a minimal synthetic drift profile for the evidence-tier unit
    tests. anchors_missing defaults to the count of anchors whose offset
    is None; offsets defaults to the non-None offsets in anchors."""
    if anchors_missing is None:
        anchors_missing = len([a for a in anchors if a.get("offset") is None])
    if offsets is None:
        offsets = [a["offset"] for a in anchors if a.get("offset") is not None]
    return {"classification": classification, "anchors": anchors,
            "anchorsFound": len(anchors) - anchors_missing,
            "anchorsMissing": anchors_missing, "offsets": offsets,
            "haikuSafe": classification in ("ALIGNED", "INSUFFICIENT-ANCHORS")}


def _sr_one(attest_overrides=None, missing=False, daf="48b"):
    if missing:
        return {"daf": daf}
    att = {"onlyOneGenuineCitation": True, "citationTranslatedOnOwnLine": True,
           "noCitationInventedMovedOrDuplicated": True, "noSemanticUncertaintyRemains": True}
    if attest_overrides:
        att.update(attest_overrides)
    return {"daf": daf, "oneAnchorAttestation": att}


def _sr_zero(attest_overrides=None, missing=False, daf="49b", authorized_empty=None):
    if missing:
        return {"daf": daf}
    att = {"everyRawLineRereadForCitations": True,
           "noTractateDafChapterVerseOrOtherCitationAnywhere": True,
           "noCitationInventedMovedOrDuplicated": True, "noSemanticUncertaintyRemains": True}
    if attest_overrides:
        att.update(attest_overrides)
    out = {"daf": daf, "zeroAnchorAttestation": att}
    if authorized_empty:
        out["authorizedEmptyLinks"] = authorized_empty
    return out


def test_evidence_tiers():
    print("source-relative citation-evidence review-gate tiers:")

    multi_ok = [{"line": 4, "kind": "name", "token": "x", "offset": 0},
                {"line": 9, "kind": "name", "token": "y", "offset": 0}]
    one_ok = [{"line": 16, "kind": "dafnum", "token": "11a", "offset": 0}]
    good_sr1 = _sr_one()
    good_sr0 = _sr_zero()

    # 1. Multi-anchor ALIGNED: pass.
    ok1, key1, _ = wp.drift_ok_for_type("rashi-reconstruction", "48b",
                                         _prof("ALIGNED", multi_ok), None)
    check("1. multi-anchor ALIGNED passes", ok1 and key1 is None)

    # 2. Multi-anchor nonzero offset: fail (tightened bar: ALIGNED alone is
    # not enough, every offset must be exactly 0).
    multi_bad_offset = [{"line": 4, "kind": "name", "token": "x", "offset": 0},
                         {"line": 9, "kind": "name", "token": "y", "offset": 1}]
    ok2, reason2 = wp.multi_anchor_safe(_prof("ALIGNED", multi_bad_offset))
    check("2. multi-anchor nonzero offset fails", not ok2, reason2)

    # 3. Multi-anchor missing citation: fail (ALIGNED classification can
    # still carry missing anchors; the tightened tier requires zero missing).
    multi_missing = [{"line": 4, "kind": "name", "token": "x", "offset": 0},
                      {"line": 9, "kind": "name", "token": "y", "offset": None}]
    ok3, reason3 = wp.multi_anchor_safe(_prof("ALIGNED", multi_missing))
    check("3. multi-anchor missing citation fails", not ok3, reason3)

    # 4. One anchor at offset 0: ONE-ANCHOR-SAFE pass.
    ok4, reason4 = wp.one_anchor_safe(_prof("INSUFFICIENT-ANCHORS", one_ok), good_sr1)
    check("4. one anchor, offset 0, self-review attests: ONE-ANCHOR-SAFE passes", ok4, reason4)

    # 5. One anchor at nonzero offset: fail.
    bad_offset = [{"line": 16, "kind": "dafnum", "token": "11a", "offset": 3}]
    ok5, reason5 = wp.one_anchor_safe(_prof("INSUFFICIENT-ANCHORS", bad_offset), good_sr1)
    check("5. one anchor, nonzero offset fails", not ok5)

    # 6. One expected anchor missing: fail.
    missing_one = [{"line": 16, "kind": "dafnum", "token": "11a", "offset": None}]
    ok6, reason6 = wp.one_anchor_safe(_prof("INSUFFICIENT-ANCHORS", missing_one), good_sr1)
    check("6. one expected anchor missing fails", not ok6)

    # 7. Zero genuine anchors with complete full-daf attestation:
    # ZERO-ANCHOR-SAFE pass. Uses the real 49b talmuddev source, whose raw
    # Rashi genuinely contains no parenthetical citation-like text at all.
    ok7, reason7 = wp.zero_anchor_safe("49b", _prof("INSUFFICIENT-ANCHORS", []), good_sr0)
    check("7. zero anchors with complete attestation: ZERO-ANCHOR-SAFE passes", ok7, reason7)

    # 8. Zero-anchor claim when raw contains a citation: fail. Uses the real
    # 48b talmuddev source, whose raw Rashi genuinely contains one
    # parenthetical citation ("Chagigah 11a"); the independent second scan
    # must catch a false zero-anchor claim against that source.
    ok8, reason8 = wp.zero_anchor_safe("48b", _prof("INSUFFICIENT-ANCHORS", []),
                                        _sr_zero(daf="48b"))
    check("8. zero-anchor claim when raw contains a citation fails", not ok8, reason8)

    # 9. Zero-anchor claim with citation-like text not investigated: fail
    # (same mechanism as #8: the independent scan is what catches this).
    check("9. covered by the independent-scan mechanism exercised in #8", not ok8)

    # 10. Zero-anchor claim with incomplete self-review: fail.
    ok10, reason10 = wp.zero_anchor_safe("49b", _prof("INSUFFICIENT-ANCHORS", []),
                                          _sr_zero(missing=True))
    check("10. zero-anchor claim with incomplete self-review fails", not ok10)

    # 11. Zero-anchor claim with an unjustified link: covered structurally by
    # the pre-existing, untouched all-links-legal-and-nonempty and
    # packet-contains-every-linked-local-id conditions (semantic
    # justification of a link is a self-review matter, not machine-derivable
    # from a link id alone); confirm those conditions still gate
    # independently of the evidence tier passing.
    all_true = {k: True for k in wp.REVIEW_CONDITIONS}
    all_true["packet-contains-every-linked-local-id"] = False
    eligible11, failed11 = wp.evaluate_review_policy(all_true)
    check("11. packet-contains-every-linked-local-id still gates independently",
          not eligible11 and failed11 == ["packet-contains-every-linked-local-id"])

    # 12. Zero-anchor claim with empty links not explicitly authorized: fail.
    entries_with_empty = [{"vilnaLine": 1, "linkedGemaraLineIds": ["yoma-049b-l01"]},
                           {"vilnaLine": 2, "linkedGemaraLineIds": []}]
    ok12, reason12 = wp.zero_anchor_safe("49b", _prof("INSUFFICIENT-ANCHORS", []),
                                          good_sr0, entries_with_empty)
    check("12. unauthorized empty link fails", not ok12, reason12)
    entries_authorized = [{"vilnaLine": 1, "linkedGemaraLineIds": ["yoma-049b-l01"]},
                          {"vilnaLine": 2, "linkedGemaraLineIds": []}]
    ok12b, reason12b = wp.zero_anchor_safe(
        "49b", _prof("INSUFFICIENT-ANCHORS", []),
        _sr_zero(authorized_empty=[{"vilnaLine": 2, "rule": "documented boundary rule"}]),
        entries_authorized)
    check("12b. explicitly authorized empty link with a cited rule passes", ok12b, reason12b)

    # 13. Zero-anchor claim with a duplicate or filler helper: covered by the
    # pre-existing, untouched no-stub-or-duplicate-helpers condition.
    all_true2 = {k: True for k in wp.REVIEW_CONDITIONS}
    all_true2["no-stub-or-duplicate-helpers"] = False
    eligible13, failed13 = wp.evaluate_review_policy(all_true2)
    check("13. no-stub-or-duplicate-helpers still gates independently",
          not eligible13 and failed13 == ["no-stub-or-duplicate-helpers"])

    # 14. Zero-anchor claim with semantic warning: covered by the
    # pre-existing, untouched semantic-audit-zero-shift-candidates condition.
    all_true3 = {k: True for k in wp.REVIEW_CONDITIONS}
    all_true3["semantic-audit-zero-shift-candidates"] = False
    eligible14, failed14 = wp.evaluate_review_policy(all_true3)
    check("14. semantic-audit-zero-shift-candidates still gates independently",
          not eligible14 and failed14 == ["semantic-audit-zero-shift-candidates"])

    # 15. SHIFTED always fails, at every tier.
    shifted_anchors = [{"line": 4, "kind": "name", "token": "x", "offset": 5},
                        {"line": 9, "kind": "name", "token": "y", "offset": 4}]
    ok15, _, _ = wp.drift_ok_for_type("rashi-realignment", "48b",
                                       _prof("SHIFTED", shifted_anchors), good_sr1)
    check("15. SHIFTED fails", not ok15)

    # 16. FABRICATION-SUSPECT always fails, at every tier.
    fab_anchors = [{"line": 4, "kind": "name", "token": "x", "offset": None},
                   {"line": 9, "kind": "name", "token": "y", "offset": None}]
    ok16, _, _ = wp.drift_ok_for_type("rashi-reconstruction", "48b",
                                       _prof("FABRICATION-SUSPECT", fab_anchors), good_sr1)
    check("16. FABRICATION-SUSPECT fails", not ok16)

    # 17. The evidence-tier policy applies only to
    # rashi-reconstruction/rashi-realignment; any other type (including a
    # hypothetical future one) stays at strict ALIGNED-only.
    for other_type in ("rashi-repair", "placeholder-backfill", "some-future-type"):
        ok17, key17, _ = wp.drift_ok_for_type(other_type, "48b",
                                               _prof("INSUFFICIENT-ANCHORS", one_ok), good_sr1)
        check(f"17. {other_type} does not get an evidence-tier exception",
              not ok17 and key17 is None)

    # 18. rashi-structural-repair keeps its existing (broader, unconditional)
    # haiku-safe policy untouched: INSUFFICIENT-ANCHORS with NO anchors at
    # all and NO self-review attestation still passes for structural repair.
    ok18, key18, _ = wp.drift_ok_for_type(wp.STRUCTURAL_TYPE, "49b",
                                           _prof("INSUFFICIENT-ANCHORS", []), None)
    check("18. rashi-structural-repair keeps its own unconditional haiku-safe policy",
          ok18 and key18 is None)

    # Full dispatch sanity: each tier reports its own distinct condition key.
    okA, keyA, noteA = wp.drift_ok_for_type("rashi-reconstruction", "48b",
                                             _prof("INSUFFICIENT-ANCHORS", one_ok), good_sr1)
    check("dispatch: one-anchor-safe reports its own distinct condition key",
          okA and keyA == "one-anchor-safe" and "ONE-ANCHOR-SAFE" in noteA)
    okC, keyC, noteC = wp.drift_ok_for_type("rashi-realignment", "49b",
                                             _prof("INSUFFICIENT-ANCHORS", []), good_sr0)
    check("dispatch: zero-anchor-safe reports its own distinct condition key",
          okC and keyC == "zero-anchor-safe" and "ZERO-ANCHOR-SAFE" in noteC)
    okB, keyB, noteB = wp.drift_ok_for_type("rashi-realignment", "49b",
                                             _prof("INSUFFICIENT-ANCHORS", []), None)
    check("dispatch: a failing zero-anchor attempt still reports the distinct key (for visibility)",
          not okB and keyB == "zero-anchor-safe")


def test_campaign_capability_scan():
    print("campaign capability scan (read-only, never edits content):")

    # 19. Detects ZERO, ONE, and MULTI targets using real corpus daf.
    r_zero = wp.capability_report_for("49b")
    check("19a. 49b classified ZERO", r_zero["cardinality"] == "ZERO", r_zero)
    r_one = wp.capability_report_for("48b")
    check("19b. 48b classified ONE", r_one["cardinality"] == "ONE", r_one)
    r_multi = wp.capability_report_for("47a")
    check("19c. 47a classified MULTI", r_multi["cardinality"] == "MULTI", r_multi)

    # Both ZERO and ONE cardinality daf are supported final states (the
    # evidence-tier policy exists precisely to cover them); a real daf with
    # a nonexistent source is unsupported.
    check("19d. ZERO cardinality is a supported final state", r_zero["supported"])
    check("19e. ONE cardinality is a supported final state", r_one["supported"])
    r_missing = wp.capability_report_for("999z")
    check("19f. nonexistent daf reports unsupported with an explanatory issue",
          not r_missing["supported"] and r_missing["issues"])

    # 20. The scan blocks (nonzero exit) before content work when any
    # target is unsupported, and passes when every target is supported.
    with tempfile.TemporaryDirectory() as td:
        rr_bad = subprocess.run([sys.executable, "scripts/worker_pipeline.py",
                                  "capability-scan", "--targets", "48b,999z"],
                                 capture_output=True, text=True, cwd=REPO)
        check("20a. scan exits nonzero when any target is unsupported",
              rr_bad.returncode != 0 and "UNSUPPORTED" in rr_bad.stdout)
        rr_good = subprocess.run([sys.executable, "scripts/worker_pipeline.py",
                                   "capability-scan", "--targets", "48b,49b,47a"],
                                  capture_output=True, text=True, cwd=REPO)
        check("20b. scan exits 0 when every target is supported",
              rr_good.returncode == 0 and "OK: all 3 target" in rr_good.stdout)
        check("20c. scan never edits content (working tree untouched)",
              subprocess.run(["git", "status", "--short",
                               "modules/yoma/assets/learning/yoma/48b.learning.json"],
                              capture_output=True, text=True, cwd=REPO).stdout.strip() == "")

    # 21. The remaining 49b-52b queue passes capability preflight once the
    # anchor-poor content work has landed for 49b (its content is already
    # merged to main by the time this tooling PR is authored); 50a-52b are
    # still FABRICATION-SUSPECT at this point (content work pending), which
    # is itself a reported (not unsupported) capability-scan state: the
    # scan flags it as an issue but the daf remains representable once
    # content work reconstructs it into an ALIGNED/one/zero-anchor state.
    for daf in ("50a", "50b", "51a", "51b", "52a", "52b"):
        r = wp.capability_report_for(daf)
        check(f"21. {daf} capability-scanned without crashing (cardinality {r.get('cardinality')})",
              "cardinality" in r)


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


def test_allowlist_drain():
    print("allowlist-drain authorization (target-scoped repair debt, not new tolerance):")

    fake_entries = [
        {"daf": "77a", "vilnaLine": 16, "reason": "filler"},
        {"daf": "77a", "vilnaLine": 17, "reason": "filler"},
        {"daf": "77b", "vilnaLine": 5, "reason": "filler"},
    ]
    orig = wp.content_allowlist_entries
    wp.content_allowlist_entries = lambda daf=None: [
        e for e in fake_entries if daf is None or e["daf"] == daf]
    try:
        snap_77a = [e for e in fake_entries if e["daf"] == "77a"]

        # 1. target-scoped existing debt does not block authorized reconstruction.
        m1 = {"type": "rashi-reconstruction", "targets": ["77a"],
              "allowlistDrain": {"authorized": True, "snapshot": snap_77a}}
        ok1, note1 = wp.validate_allowlist_drain(m1, "77a")
        check("1. matching snapshot for the correct single target authorizes the drain", ok1, note1)

        # 2. unrelated-daf entries still block: a snapshot naming a foreign
        # daf's debt never authorizes this daf.
        m2 = {"type": "rashi-reconstruction", "targets": ["77a"],
              "allowlistDrain": {"authorized": True,
                                 "snapshot": [{"daf": "77b", "vilnaLine": 5, "reason": "filler"}]}}
        ok2, note2 = wp.validate_allowlist_drain(m2, "77a")
        check("2. snapshot naming a foreign daf's entries does not authorize this daf",
              not ok2, note2)

        # 3. newly added entries block: snapshot missing a currently-existing
        # entry (taken before the entry appeared, or hand-edited) is rejected,
        # not silently narrowed.
        m3 = {"type": "rashi-reconstruction", "targets": ["77a"],
              "allowlistDrain": {"authorized": True, "snapshot": [snap_77a[0]]}}
        ok3, note3 = wp.validate_allowlist_drain(m3, "77a")
        check("3. snapshot missing a currently-existing entry blocks", not ok3, note3)

        # 3b. snapshot claiming an entry that doesn't currently exist also blocks.
        m3b = {"type": "rashi-reconstruction", "targets": ["77a"],
               "allowlistDrain": {"authorized": True,
                                  "snapshot": snap_77a + [{"daf": "77a", "vilnaLine": 99, "reason": "filler"}]}}
        ok3b, note3b = wp.validate_allowlist_drain(m3b, "77a")
        check("3b. snapshot claiming a nonexistent entry blocks", not ok3b, note3b)

        # 4. missing drain intent blocks: no allowlistDrain field at all.
        m4 = {"type": "rashi-reconstruction", "targets": ["77a"]}
        ok4, note4 = wp.validate_allowlist_drain(m4, "77a")
        check("4. manifest with no allowlistDrain authorization blocks", not ok4, note4)

        # 4b. allowlistDrain present but authorized=False also blocks.
        m4b = {"type": "rashi-reconstruction", "targets": ["77a"],
               "allowlistDrain": {"authorized": False, "snapshot": snap_77a}}
        ok4b, note4b = wp.validate_allowlist_drain(m4b, "77a")
        check("4b. allowlistDrain present but not authorized blocks", not ok4b, note4b)

        # 5. multi-daf manifests block, even with an otherwise-valid snapshot.
        m5 = {"type": "rashi-reconstruction", "targets": ["77a", "77b"],
              "allowlistDrain": {"authorized": True, "snapshot": snap_77a}}
        ok5, note5 = wp.validate_allowlist_drain(m5, "77a")
        check("5. multi-target manifest blocks the drain authorization", not ok5, note5)

        # 6. ordinary task types cannot use this authorization.
        for other_type in ("rashi-repair", "placeholder-backfill", "rashi-structural-repair"):
            m6 = {"type": other_type, "targets": ["77a"],
                  "allowlistDrain": {"authorized": True, "snapshot": snap_77a}}
            ok6, note6 = wp.validate_allowlist_drain(m6, "77a")
            check(f"6. {other_type} cannot use allowlist-drain authorization", not ok6, note6)

        # 7. rashi-realignment (not just rashi-reconstruction) can also use it.
        m7 = {"type": "rashi-realignment", "targets": ["77a"],
              "allowlistDrain": {"authorized": True, "snapshot": snap_77a}}
        ok7, note7 = wp.validate_allowlist_drain(m7, "77a")
        check("7. rashi-realignment can also use allowlist-drain authorization", ok7, note7)

        # 8. empty snapshot for a daf with no existing debt is trivially valid.
        m8 = {"type": "rashi-reconstruction", "targets": ["79a"],
              "allowlistDrain": {"authorized": True, "snapshot": []}}
        ok8, note8 = wp.validate_allowlist_drain(m8, "79a")
        check("8. empty snapshot for a daf with no existing debt is valid", ok8, note8)
    finally:
        wp.content_allowlist_entries = orig

    print("allowlist-drain post-edit enforcement (snapshot is debt to eliminate, not an exemption):")

    old_entries = [
        {"daf": "77a", "vilnaLine": 16, "reason": "filler"},
        {"daf": "77a", "vilnaLine": 17, "reason": "filler"},
        {"daf": "77b", "vilnaLine": 5, "reason": "filler"},
    ]
    drained_manifest = {"type": "rashi-reconstruction", "targets": ["77a"],
                        "allowlistDrain": {"authorized": True,
                                          "snapshot": [e for e in old_entries if e["daf"] == "77a"]}}

    # a. clean drain: both 77a entries removed, 77b entry untouched -> pass.
    new_a = [{"daf": "77b", "vilnaLine": 5, "reason": "filler"}]
    ok_a, msgs_a = wp.allowlist_drain_status(drained_manifest, old_entries, new_a, set())
    check("a. fully drained snapshot with unrelated entry intact passes", ok_a, "; ".join(msgs_a))

    # b. stale entries must be removed before review passes: validator says
    # L16 no longer violates, but the entry was left in the file -> fail.
    new_b = [{"daf": "77a", "vilnaLine": 16, "reason": "filler"},
             {"daf": "77b", "vilnaLine": 5, "reason": "filler"}]
    ok_b, msgs_b = wp.allowlist_drain_status(drained_manifest, old_entries, new_b, {("77a", 16)})
    check("b. validator-confirmed-stale entry left in place fails", not ok_b, "; ".join(msgs_b))
    check("b. failure message distinguishes stale-not-removed from still-needed",
          any("stale" in msg for msg in msgs_b))

    # c. entries still needed after attempted repair trigger operator stop:
    # L16 still genuinely violates per the validator -> fail, distinct message.
    ok_c, msgs_c = wp.allowlist_drain_status(drained_manifest, old_entries, new_b, set())
    check("c. genuinely-still-violating entry fails (repair gap, escalate)", not ok_c, "; ".join(msgs_c))
    check("c. failure message says still needed / escalate",
          any("still needed" in msg or "escalate" in msg for msg in msgs_c))

    # d. any new allowlist entry for the target daf fails, even one the
    # validator would call a violation elsewhere in the corpus.
    new_d = [{"daf": "77a", "vilnaLine": 40, "reason": "filler"},
             {"daf": "77b", "vilnaLine": 5, "reason": "filler"}]
    ok_d, msgs_d = wp.allowlist_drain_status(drained_manifest, old_entries, new_d, set())
    check("d. a new allowlist entry for the target daf fails (no growth allowed)",
          not ok_d, "; ".join(msgs_d))

    # e. unrelated allowlist entries must remain byte-identical: changing the
    # 77b entry (not the target daf) fails even though 77a drained cleanly.
    new_e = [{"daf": "77b", "vilnaLine": 5, "reason": "filler_opening"}]
    ok_e, msgs_e = wp.allowlist_drain_status(drained_manifest, old_entries, new_e, set())
    check("e. an unrelated daf's entry changing fails even with a clean target drain",
          not ok_e, "; ".join(msgs_e))

    # f. a manifest with no allowlistDrain at all is a no-op (nothing to
    # enforce); ordinary PRs are unaffected by this feature.
    ordinary = {"type": "rashi-repair", "targets": ["61a"]}
    ok_f, msgs_f = wp.allowlist_drain_status(ordinary, old_entries, old_entries, set())
    check("f. a manifest without allowlistDrain is a no-op (ok, no messages)",
          ok_f and not msgs_f)

    print("allowlist-drain end-to-end manifest generation (real repo state, read-only):")
    with tempfile.TemporaryDirectory() as td:
        mpath = Path(td) / "m.json"
        r = subprocess.run([sys.executable, "scripts/worker_pipeline.py", "manifest",
                            "--type", "rashi-reconstruction", "--module", "yoma",
                            "--range", "61a", "--out", str(mpath)],
                           capture_output=True, text=True, cwd=REPO)
        check("manifest generation without --drain-allowlist succeeds", r.returncode == 0, r.stderr[-200:])
        plain = json.loads(mpath.read_text())
        check("plain manifest carries a null allowlistDrain field", plain.get("allowlistDrain") is None)

        r2 = subprocess.run([sys.executable, "scripts/worker_pipeline.py", "manifest",
                             "--type", "rashi-repair", "--module", "yoma",
                             "--range", "61a", "--drain-allowlist", "--out", str(mpath)],
                            capture_output=True, text=True, cwd=REPO)
        check("--drain-allowlist rejected for a non-reconstruction/realignment type",
              r2.returncode != 0)


def main():
    test_registry()
    test_pure_policy()
    test_live_gate_fails_closed()
    test_prompt()
    test_queue()
    test_structural_repair_type()
    test_evidence_tiers()
    test_campaign_capability_scan()
    test_allowlist_drain()
    test_structural_deferral_in_scope_validator()
    test_no_direct_main_push_anywhere()
    if FAILURES:
        print(f"\nFAILED: {len(FAILURES)} check(s): {FAILURES}")
        sys.exit(1)
    print("\nOK: all worker policy tests passed.")


if __name__ == "__main__":
    main()
