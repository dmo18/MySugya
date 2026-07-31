#!/usr/bin/env python3
"""
test_worker_policy.py - tests for the conditional semantic-review policy
and the sequential autopilot queue (scripts/worker_pipeline.py).

Pins the VERSION 15.93 process change: rashi-realignment and
rashi-reconstruction no longer require an unconditional independent review
per PR. Instead a Sonnet worker performs a fresh post-edit self-review and a
machine-checked auto-merge gate (worker:review) decides eligibility;
every failed condition escalates to Sonnet and blocks merge. Sonnet is the
only execution and escalation model in the pipeline.

Layers:
1. Registry: the two semantic types carry reviewPolicy conditional with
   escalationModel sonnet; the mechanical types keep their unconditional
   independent review; the self-review and queue files are in scope.
2. Pure policy: all conditions true -> eligible (no independent review needed); EVERY
   single condition false -> blocked (negative test per condition).
3. Live gate: worker:review on a no-diff tree is blocked (nothing to
   merge, no fresh self-review), proving the gate fails closed.
4. Prompt: conditional prompts carry the self-review, auto-merge, and
   escalation instructions and never a may-not-merge independent-review line.
5. Queue: create/next/advance are sequential, one PR per target,
   stop-on-escalation; out-of-order advance is rejected.

Run: python3 scripts/test_worker_policy.py   (cwd repo root)
Exit 0 on success, 1 on failure.
"""
import os
import re
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))
import worker_pipeline as wp

# This whole file's fixtures are Yoma paths (32 of them; see the "second
# module id" section below for the parallel non-Yoma coverage added in
# Phase 3 Step 3A). Functions like gather_review_conditions and
# capability_report_for read wp.ACTIVE_MODULE rather than re-resolving a
# module themselves, since production always reaches them through
# load_manifest()'s or an explicit set_active_module() call first; a
# direct unit-test call needs the same setup. Resolving Yoma once here
# matches that production path for every direct call below.
wp.set_active_module(wp.resolve_active_module("yoma"))

FAILURES = []
CONDITIONAL_TYPES = ("rashi-realignment", "rashi-reconstruction")
# placeholder-backfill keeps its unconditional independent review; rashi-repair
# was already line-level-safe with no per-PR review (drift block gates it).
INDEPENDENT_REVIEW_TYPES = ("placeholder-backfill",)


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
        check(f"{t} escalationModel is sonnet", s.get("escalationModel") == "sonnet")
        check(f"{t} has no unconditional independentReviewRequired",
              not s.get("independentReviewRequired"))
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
    for t in INDEPENDENT_REVIEW_TYPES:
        check(f"{t} keeps unconditional independent review",
              wp.review_policy_of(types[t]) == "independent")


def test_docs_tooling_scope_boundaries():
    """docs-tooling may edit documentation (including the module-level
    MODULE.md, allowed from VERSION 15.340 to close a real maintainability
    gap), but must never reach module CONTENT or generated data.

    Uses the real production predicate wp.file_allowed, whose enforcement is
    allowlist-style: anything not explicitly allowed is a violation. This
    pins the boundary so a future allowedFiles edit cannot quietly widen the
    type into the corpus."""
    print("docs-tooling scope boundaries:")
    spec = wp.load_registry()["docs-tooling"]

    for path in ("README.md", "CLAUDE.md", "SOURCES.md",
                 "docs/reports/open-items.md", "modules/yoma/MODULE.md",
                 "modules/yoma/scripts/validate_rashi_links.py",
                 "tests/unit/rashi-association.test.mjs"):
        check(f"docs-tooling allows {path}", wp.file_allowed(path, spec, [], "yoma"))

    for path in ("modules/yoma/assets/learning/yoma/2a.learning.json",
                 "modules/yoma/assets/talmuddev/2a.json",
                 "modules/yoma/assets/daftexts/2a.txt",
                 "modules/yoma/source_store.js",
                 "modules/yoma/learning_data.js"):
        check(f"docs-tooling still refuses {path}", not wp.file_allowed(path, spec, [], "yoma"))




def test_boundary_authorized_empty_links():
    """The conditional-review gate must accept an empty linkedGemaraLineIds
    ONLY when the boundary registry authorizes it AND the self-review
    declares it, in both directions. Exercises the real shared helper
    (validate_rashi_boundary_authorizations.authorized_empty_vilna_lines)
    against synthetic registries and corpora, so the gate can never drift
    from the canonical registry validation it delegates to."""
    print("boundary-authorized empty links:")
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "vrba", REPO / "modules/yoma/scripts/validate_rashi_boundary_authorizations.py")
    vrba = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vrba)

    def auth(daf, vl, en):
        return {"daf": daf, "vilnaLine": vl, "reason": "daf-boundary truncation",
                "evidenceClassification": "daf-boundary-truncation",
                "boundaryRule": "cross-daf links prohibited",
                "enFingerprint": vrba.fingerprint(en)}

    def entry(en, linked=None):
        return {"en": en, "linkedGemaraLineIds": list(linked or [])}

    # --- real 4b L61 and all nineteen 61a authorized empties ---
    real_entries = vrba.load_registry_entries()
    real_corpus = vrba.load_corpus()
    vl4b, err4b = vrba.authorized_empty_vilna_lines("4b", real_entries, real_corpus)
    check("4b L61 authorized empty passes", 61 in vl4b and not err4b)
    vl61a, err61a = vrba.authorized_empty_vilna_lines("61a", real_entries, real_corpus)
    check("all nineteen 61a authorized empties pass",
          vl61a == set(range(46, 65)) and len(vl61a) == 19 and not err61a)

    # --- an identical empty entry WITHOUT registry authorization ---
    corpus = {("4b", 61): entry("stub"), ("4b", 60): entry("also empty")}
    got, errs = vrba.authorized_empty_vilna_lines("4b", [auth("4b", 61, "stub")], corpus)
    check("unauthorized empty entry is not authorized", 60 not in got and bool(errs))

    # --- stale fingerprint ---
    got, errs = vrba.authorized_empty_vilna_lines(
        "4b", [auth("4b", 61, "ORIGINAL")], {("4b", 61): entry("EDITED")})
    check("stale fingerprint fails", got == set() and any("stale" in e for e in errs))

    # --- duplicate registry record ---
    got, errs = vrba.authorized_empty_vilna_lines(
        "4b", [auth("4b", 61, "stub"), auth("4b", 61, "stub")], {("4b", 61): entry("stub")})
    check("duplicate registry record fails", got == set() and any("duplicate" in e for e in errs))

    # --- registry record for a missing entry ---
    got, errs = vrba.authorized_empty_vilna_lines(
        "4b", [auth("4b", 999, "ghost"), auth("4b", 61, "stub")], {("4b", 61): entry("stub")})
    check("registry record for a nonexistent entry fails",
          got == set() and any("does not exist" in e for e in errs))

    # --- an authorized entry changed to NONEMPTY ---
    got, errs = vrba.authorized_empty_vilna_lines(
        "4b", [auth("4b", 61, "stub")], {("4b", 61): entry("stub", ["yoma-004b-l47"])})
    check("authorized entry that became nonempty fails registry validation",
          got == set() and any("no longer empty-linked" in e for e in errs))

    # --- gate-level agreement between registry and self-review ---
    def gate(empty, authorized, declared, illegal=(), registry_errors=()):
        """Mirrors the gate's own boolean, kept in lockstep with
        worker_pipeline.py's condition so the semantics are asserted here."""
        empty_set = set(empty); auth_set = set(authorized); decl = set(declared)
        unauthorized = empty_set - auth_set
        undeclared = empty_set - decl
        overclaimed = decl - (empty_set & auth_set)
        return (not illegal and not registry_errors and not unauthorized
                and not undeclared and not overclaimed)

    check("authorized + declared empty passes", gate([61], [61], [61]))
    check("empty entry missing from self-review authorizedEmptyLinks fails",
          not gate([61], [61], []))
    check("extra self-review authorizedEmptyLinks claim fails",
          not gate([61], [61], [61, 60]))
    check("self-review claim for a nonempty entry fails", not gate([], [61], [61]))
    check("ordinary daf with all legal nonempty links still passes",
          gate([], [], []))
    check("broken or cross-daf nonempty link still fails",
          not gate([], [], [], illegal=["yoma-005a-l01"]))
    check("registry-wide error blocks every empty entry",
          not gate([61], [], [61], registry_errors=["stale"]))


def test_pure_policy():
    print("pure auto-merge policy:")
    all_true = {k: True for k in wp.REVIEW_CONDITIONS}
    eligible, failed = wp.evaluate_review_policy(all_true)
    check("all conditions true -> AUTO-MERGE eligible without independent review",
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
        check("manifest carries escalationModel sonnet",
              m.get("escalationModel") == "sonnet")
        rr = subprocess.run([sys.executable, "scripts/worker_pipeline.py", "review",
                             "--manifest", str(mpath)],
                            capture_output=True, text=True, cwd=REPO)
        check("gate blocks when unsafe conditions appear (exit nonzero)",
              rr.returncode != 0)
        check("gate names the escalation model", "ESCALATE to sonnet" in rr.stdout)
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
        check("prompt does NOT carry the unconditional independent-review no-merge line",
              "may NOT merge" not in out)
        check("prompt escalates to sonnet", "hand off to sonnet" in out)


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
    check("model is sonnet", s["model"] == "sonnet")
    check("escalation model is sonnet", s.get("escalationModel") == "sonnet")
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
            "lineLevelSafe": classification in ("ALIGNED", "INSUFFICIENT-ANCHORS")}


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

    # 3b. Yoma 80a class: a dafnum anchor whose digits were sourced from
    # the FOLLOWING raw line (a citation split across the print-line
    # break, e.g. he ends "(Berakhot" and next_he opens "39a)") is
    # flagged splitContinuation; offset +1 for THAT anchor is the
    # citation's own honestly-translated position, not drift, and must
    # pass. The same +1 offset on an ordinary (non-split) anchor must
    # still fail: the tolerance is narrowly scoped to the flagged token.
    multi_split_ok = [{"line": 4, "kind": "name", "token": "x", "offset": 0},
                       {"line": 9, "kind": "dafnum", "token": "39a", "offset": 1,
                        "splitContinuation": True}]
    ok3c, reason3c = wp.multi_anchor_safe(_prof("ALIGNED", multi_split_ok))
    check("3b. split-continuation dafnum at offset +1 passes", ok3c, reason3c)

    multi_unflagged_offset = [{"line": 4, "kind": "name", "token": "x", "offset": 0},
                               {"line": 9, "kind": "dafnum", "token": "39a", "offset": 1,
                                "splitContinuation": False}]
    ok3d, reason3d = wp.multi_anchor_safe(_prof("ALIGNED", multi_unflagged_offset))
    check("3c. same offset +1 WITHOUT the split flag still fails", not ok3d, reason3d)

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

    # 6b. One anchor, split-continuation dafnum at offset +1: passes.
    one_split_ok = [{"line": 16, "kind": "dafnum", "token": "39a", "offset": 1,
                      "splitContinuation": True}]
    ok6c, reason6c = wp.one_anchor_safe(_prof("INSUFFICIENT-ANCHORS", one_split_ok), good_sr1)
    check("6b. one anchor, split-continuation offset +1 passes", ok6c, reason6c)

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
    # the all-links-legal-and-empty-links-authorized and
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
    # line-level-safe policy untouched: INSUFFICIENT-ANCHORS with NO anchors at
    # all and NO self-review attestation still passes for structural repair.
    ok18, key18, _ = wp.drift_ok_for_type(wp.STRUCTURAL_TYPE, "49b",
                                           _prof("INSUFFICIENT-ANCHORS", []), None)
    check("18. rashi-structural-repair keeps its own unconditional line-level-safe policy",
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
    # 20c compares the repo's full git status before and after running the
    # scan commands, rather than asserting a specific real corpus daf's
    # file stays pristine: that daf is drawn from the live campaign queue
    # and is expected to become the worker's own in-progress content target
    # sooner or later (as happened once already with 41b/test_repetition_drain),
    # at which point a hardcoded-clean assertion on its file would fail for
    # reasons unrelated to what this test actually checks (capability-scan's
    # own read-only behavior).
    with tempfile.TemporaryDirectory() as td:
        pre_status = subprocess.run(["git", "status", "--short"],
                                     capture_output=True, text=True, cwd=REPO).stdout
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
        post_status = subprocess.run(["git", "status", "--short"],
                                      capture_output=True, text=True, cwd=REPO).stdout
        check("20c. scan never edits content (working tree untouched)",
              pre_status == post_status)

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


def test_independent_zero_citation_scan():
    print("independent zero-citation scan (citation-shape aware, not any-parenthetical):")

    # Regression for the campaign-86a gap: an ordinary editorial gloss in
    # parens, carrying neither a "daf" token nor a daf/amud punctuation
    # tail, must not be flagged as citation-like.
    check("1. non-citation gloss '(Torah)' is not citation-shaped",
          not wp._citation_shaped("תורה"))

    # Regression for the campaign-83a gap: a same-parens tractate + "daf"
    # citation must still be flagged even though the tractate name sits
    # inside the parens rather than as a bare daf/amud token alone.
    check("2. same-parens tractate+daf citation is citation-shaped",
          wp._citation_shaped('ב"ב דף צ:'))

    # A bare daf/amud marker (no "daf" word) is still citation-shaped.
    check("3. bare daf/amud tail is citation-shaped", wp._citation_shaped("נז:"))

    # A multi-word non-citation gloss without punctuation tail is not.
    check("4. multi-word non-citation gloss is not citation-shaped",
          not wp._citation_shaped("כלומר בענין אחר"))

    with tempfile.TemporaryDirectory() as td:
        tdir = Path(td) / "assets" / "talmuddev"
        tdir.mkdir(parents=True)
        saved = wp.YROOT
        wp.YROOT = Path(td)
        try:
            (tdir / "999z.json").write_text(json.dumps({
                "rashi": ["ומשמש תלמידי חכמים. ללמוד (תורה)"]}, ensure_ascii=False))
            ok, detail = wp.independent_zero_citation_scan("999z")
            check("5. daf with only a non-citation gloss scans OK (no false positive)",
                  ok, detail)

            (tdir / "998z.json").write_text(json.dumps({
                "rashi": ['ותניא (ב"ב דף צ:) אין אוצרין פירות בארץ']}, ensure_ascii=False))
            ok2, detail2 = wp.independent_zero_citation_scan("998z")
            check("6. daf with a same-parens citation is caught (no false negative)",
                  not ok2, detail2)
        finally:
            wp.YROOT = saved


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


def test_scaffold_debt_drain():
    """Target-scoped scaffold-fabrication debt drain: the baseline is a
    shrink-only ratchet; a reconstruction/realignment must leave its target
    with zero scaffold hits and zero baseline entries, and may never grow,
    rehash, or foreign-shrink the baseline."""
    print("scaffold-debt drain enforcement (shrink-only, target-scoped):")
    m = {"type": "rashi-reconstruction", "targets": ["10a"],
         "scaffoldDebt": {"snapshot": [
             {"daf": "10a", "vilnaLine": 5, "rule": "scaffold-prefix", "enHash": "aa"},
             {"daf": "10a", "vilnaLine": 13, "rule": "scaffold-prefix", "enHash": "bb"},
         ]}}
    old = [{"daf": "10a", "vilnaLine": 5, "rule": "scaffold-prefix", "enHash": "aa"},
           {"daf": "10a", "vilnaLine": 13, "rule": "scaffold-prefix", "enHash": "bb"},
           {"daf": "12a", "vilnaLine": 7, "rule": "scaffold-prefix", "enHash": "cc"}]

    new_ok = [e for e in old if e["daf"] != "10a"]
    ok, msgs = wp.scaffold_drain_status(m, "10a", old, new_ok, [])
    check("a. fully drained target with unrelated entry intact passes",
          ok and any("drained" in x for x in msgs), "; ".join(msgs))

    hit = [{"daf": "10a", "vilnaLine": 5, "rule": "scaffold-prefix", "enHash": "zz"}]
    ok_b, msgs_b = wp.scaffold_drain_status(m, "10a", old, new_ok, hit)
    check("b. remaining target scaffold hit fails (13)", not ok_b, "; ".join(msgs_b))

    ok_c, msgs_c = wp.scaffold_drain_status(m, "10a", old, old, [])
    check("c. unretired target baseline entries fail", not ok_c)

    new_d = new_ok + [{"daf": "10a", "vilnaLine": 20, "rule": "scaffold-prefix", "enHash": "dd"}]
    ok_d, msgs_d = wp.scaffold_drain_status(m, "10a", old, new_d, [])
    check("d. baseline growth is forbidden (14)", not ok_d)

    ok_e, msgs_e = wp.scaffold_drain_status(m, "10a", old, [], [])
    check("e. removing an unrelated daf's entry fails (15)", not ok_e)

    new_f = [dict(e, enHash="XX") if e["daf"] == "12a" else e for e in new_ok]
    ok_f, msgs_f = wp.scaffold_drain_status(m, "10a", old, new_f, [])
    check("f. rehashing an unrelated entry fails (15)", not ok_f)

    ok_g, msgs_g = wp.scaffold_drain_status(
        {"type": "rashi-repair", "targets": ["61a"]}, "61a", old, old, [])
    check("g. non-reconstruction/realignment types are a no-op", ok_g and not msgs_g)

    print("scaffold-debt manifest snapshot (12):")
    baseline_path = REPO / "modules" / "yoma" / "scripts" / "baselines" / "rashi_scaffold_debt.json"
    baseline_daf = sorted({e["daf"] for e in json.loads(baseline_path.read_text())["entries"]})
    with tempfile.TemporaryDirectory() as td:
        mpath = Path(td) / "m.json"
        if baseline_daf:
            debt_daf = baseline_daf[0]
            r = subprocess.run([sys.executable, "scripts/worker_pipeline.py", "manifest",
                                "--type", "rashi-reconstruction", "--module", "yoma",
                                "--range", debt_daf, "--out", str(mpath)],
                               capture_output=True, text=True, cwd=REPO)
            check("manifest generation for a debt-bearing daf succeeds", r.returncode == 0,
                  r.stderr[-200:])
            man = json.loads(mpath.read_text())
            snap = (man.get("scaffoldDebt") or {}).get("snapshot", [])
            check("manifest embeds the target's scaffold-debt snapshot",
                  bool(snap) and all(e["daf"] == debt_daf for e in snap),
                  "%s: %d" % (debt_daf, len(snap)))
        else:
            print("  note: scaffold baseline is empty (corpus fully drained); "
                  "snapshot embedding check not applicable")

        r2 = subprocess.run([sys.executable, "scripts/worker_pipeline.py", "manifest",
                             "--type", "rashi-reconstruction", "--module", "yoma",
                             "--range", "88a", "--out", str(mpath)],
                            capture_output=True, text=True, cwd=REPO)
        clean_man = json.loads(mpath.read_text())
        check("a debt-free daf's manifest carries a null scaffoldDebt field",
              r2.returncode == 0 and clean_man.get("scaffoldDebt") is None)


def test_repetition_drain():
    """Target-scoped repetition-baseline debt drain (see "Repetition-drain"
    in docs/worker-pipeline-sop.md): resolves the 41b contradiction where
    the repetition-baseline check demanded --task repair while the drift
    block forbade repair on a FABRICATION-SUSPECT daf and recommended
    reconstruction instead. Mirrors test_allowlist_drain/
    test_scaffold_debt_drain in structure. Count mismatches are a wholly
    separate, always-hard-blocked check with no drain path; nothing here
    ever touches WORKER_DRIFT_OVERRIDE or authorizeDriftOverride.

    The pure-logic checks (1-7) are fully synthetic: they mock both
    repetition_baseline_entries and audit_rashi_semantic.profile_daf, so
    they never depend on any particular daf's live classification. This
    matters because 41b -- the daf that originally exposed this
    contradiction -- is exactly the daf this feature exists to unblock;
    once resolved, its own drift profile legitimately changes to ALIGNED,
    so hardcoding it as an always-FABRICATION-SUSPECT fixture would make
    this test self-destruct on the campaign's own success. The end-to-end
    section instead detects live corpus state dynamically, same pattern as
    test_scaffold_debt_drain's baseline_daf lookup."""
    print("repetition-drain authorization (validate_repetition_drain, fully synthetic):")

    fake_entries = [
        {"daf": "99a", "skeleton": "Rashi: continues - [X].", "maxCount": 13},
        {"daf": "99b", "skeleton": "Rashi: continues - [X].", "maxCount": 12},
    ]
    fake_profiles = {
        "99a": {"classification": "FABRICATION-SUSPECT", "recommendedTaskType": "rashi-reconstruction"},
        "61a": {"classification": "ALIGNED", "recommendedTaskType": None},
    }
    orig_entries = wp.repetition_baseline_entries
    wp.repetition_baseline_entries = lambda daf=None: [
        e for e in fake_entries if daf is None or e["daf"] == daf]
    sys.path.insert(0, str(REPO / "modules" / "yoma" / "scripts"))
    import audit_rashi_semantic as ars
    orig_profile = ars.profile_daf
    ars.profile_daf = lambda daf: fake_profiles.get(daf)
    try:
        snap_99a = [e for e in fake_entries if e["daf"] == "99a"]

        # 1. matching snapshot on a synthetic FABRICATION-SUSPECT daf
        # (recommendedTaskType rashi-reconstruction) authorizes the drain.
        m1 = {"type": "rashi-reconstruction", "targets": ["99a"],
              "repetitionDrain": {"snapshot": snap_99a}}
        ok1, note1 = wp.validate_repetition_drain(m1, "99a")
        check("1. matching snapshot on a synthetic FABRICATION-SUSPECT daf authorizes the drain",
              ok1, note1)

        # 2. no repetitionDrain field at all blocks.
        m2 = {"type": "rashi-reconstruction", "targets": ["99a"]}
        ok2, note2 = wp.validate_repetition_drain(m2, "99a")
        check("2. manifest with no repetitionDrain snapshot blocks (missing snapshot)",
              not ok2, note2)

        # 3. stale snapshot (missing a currently-existing entry) blocks.
        m3 = {"type": "rashi-reconstruction", "targets": ["99a"],
              "repetitionDrain": {"snapshot": []}}
        ok3, note3 = wp.validate_repetition_drain(m3, "99a")
        check("3. stale/empty snapshot missing a currently-existing entry blocks",
              not ok3, note3)

        # 3b. snapshot claiming an entry that doesn't currently exist also blocks.
        m3b = {"type": "rashi-reconstruction", "targets": ["99a"],
               "repetitionDrain": {"snapshot": snap_99a + [
                   {"daf": "99a", "skeleton": "Rashi: opens - [Y].", "maxCount": 3}]}}
        ok3b, note3b = wp.validate_repetition_drain(m3b, "99a")
        check("3b. snapshot claiming a nonexistent entry blocks (stale-in-the-other-direction)",
              not ok3b, note3b)

        # 4. a snapshot naming a foreign daf's debt never authorizes this daf.
        m4 = {"type": "rashi-reconstruction", "targets": ["99a"],
              "repetitionDrain": {"snapshot": [
                  {"daf": "99b", "skeleton": "Rashi: continues - [X].", "maxCount": 12}]}}
        ok4, note4 = wp.validate_repetition_drain(m4, "99a")
        check("4. snapshot naming a foreign daf's entries does not authorize this daf (foreign-daf snapshot)",
              not ok4, note4)

        # 5. multi-target manifests block, even with an otherwise-valid snapshot.
        m5 = {"type": "rashi-reconstruction", "targets": ["99a", "99b"],
              "repetitionDrain": {"snapshot": snap_99a}}
        ok5, note5 = wp.validate_repetition_drain(m5, "99a")
        check("5. multi-target manifest blocks the drain authorization (multi-target snapshot)",
              not ok5, note5)

        # 6. ordinary task types can never use this authorization.
        for other_type in ("rashi-repair", "placeholder-backfill", "rashi-structural-repair"):
            m6 = {"type": other_type, "targets": ["99a"],
                  "repetitionDrain": {"snapshot": snap_99a}}
            ok6, note6 = wp.validate_repetition_drain(m6, "99a")
            check(f"6. {other_type} cannot use repetition-drain authorization", not ok6, note6)

        # 7. a daf whose drift profile does NOT recommend reconstruction
        # (synthetic ALIGNED / recommendedTaskType None) is rejected even
        # with an otherwise-perfectly-matching snapshot: this authorization
        # only unlocks an already-drift-approved remedy, it is never a
        # generic override.
        fake_entries.append({"daf": "61a", "skeleton": "Rashi: continues - [Z].", "maxCount": 5})
        m7 = {"type": "rashi-reconstruction", "targets": ["61a"],
              "repetitionDrain": {"snapshot": [
                  {"daf": "61a", "skeleton": "Rashi: continues - [Z].", "maxCount": 5}]}}
        ok7, note7 = wp.validate_repetition_drain(m7, "61a")
        check("7. a daf whose drift profile does not recommend reconstruction is rejected "
              "even with a matching snapshot", not ok7, note7)
        fake_entries.pop()
    finally:
        wp.repetition_baseline_entries = orig_entries
        ars.profile_daf = orig_profile

    print("repetition-drain post-edit enforcement (snapshot is debt to eliminate, not an exemption):")
    m = {"type": "rashi-reconstruction", "targets": ["99a"],
         "repetitionDrain": {"snapshot": [
             {"daf": "99a", "skeleton": "Rashi: continues - [X].", "maxCount": 13}]}}
    old = [{"daf": "99a", "skeleton": "Rashi: continues - [X].", "maxCount": 13},
           {"daf": "99b", "skeleton": "Rashi: continues - [X].", "maxCount": 12}]

    new_ok = [e for e in old if e["daf"] != "99a"]
    ok_a, msgs_a = wp.repetition_drain_status(m, "99a", old, new_ok, [])
    check("a. fully drained target with unrelated entry intact passes",
          ok_a and any("drained" in x for x in msgs_a), "; ".join(msgs_a))

    ok_b, msgs_b = wp.repetition_drain_status(m, "99a", old, new_ok, ["ERROR 99a: x"])
    check("b. remaining target repetition violation fails (target entry remaining "
          "after reconstruction)", not ok_b, "; ".join(msgs_b))

    ok_c, msgs_c = wp.repetition_drain_status(m, "99a", old, old, [])
    check("c. unretired target baseline entries fail (target entry remaining)", not ok_c)

    new_d = new_ok + [{"daf": "99a", "skeleton": "Rashi: opens - [Y].", "maxCount": 2}]
    ok_d, msgs_d = wp.repetition_drain_status(m, "99a", old, new_d, [])
    check("d. baseline growth is forbidden", not ok_d)

    ok_e, msgs_e = wp.repetition_drain_status(m, "99a", old, [], [])
    check("e. removing an unrelated daf's entry fails (unrelated baseline removal)", not ok_e)

    new_f = [dict(e, maxCount=99) if e["daf"] == "99b" else e for e in new_ok]
    ok_f, msgs_f = wp.repetition_drain_status(m, "99a", old, new_f, [])
    check("f. modifying an unrelated entry's maxCount fails", not ok_f)

    ok_g, msgs_g = wp.repetition_drain_status(
        {"type": "rashi-repair", "targets": ["61a"]}, "61a", old, old, [])
    check("g. non-reconstruction/realignment types are a no-op", ok_g and not msgs_g)

    print("end-to-end preflight on the real corpus (dynamic: adapts as the campaign drains debt):")
    with tempfile.TemporaryDirectory() as td:
        mpath = Path(td) / "m.json"

        # Find a currently FABRICATION-SUSPECT/SHIFTED daf to prove the
        # drift-block still applies to --task repair regardless of
        # repetition-drain (independent of whether that daf happens to
        # carry repetition debt too).
        drift_daf = None
        for d in ars.all_daf():
            prof = ars.profile_daf(d)
            if prof and prof["classification"] in ("FABRICATION-SUSPECT", "SHIFTED"):
                drift_daf = d
                break
        if drift_daf:
            r2 = subprocess.run([sys.executable, "scripts/worker_pipeline.py", "manifest",
                                 "--type", "rashi-repair", "--module", "yoma",
                                 "--range", drift_daf, "--out", str(mpath)],
                                capture_output=True, text=True, cwd=REPO)
            check(f"manifest generation for {drift_daf} repair succeeds", r2.returncode == 0,
                  r2.stderr[-200:])
            pf2 = subprocess.run([sys.executable, "scripts/worker_pipeline.py", "preflight",
                                  "--manifest", str(mpath), "--dry-run"],
                                 capture_output=True, text=True, cwd=REPO)
            check(f"repair on {drift_daf} remains blocked by the drift gate "
                  "(never bypassed by repetition-drain)",
                  pf2.returncode != 0
                  and (prof["classification"] in pf2.stdout), pf2.stdout[-500:])
        else:
            print("  note: no live FABRICATION-SUSPECT/SHIFTED daf in the corpus; "
                  "drift-block-on-repair coverage relies on test_drift_profile.py instead")

        # Find a currently repetition-baselined daf to prove manifest
        # generation embeds its snapshot, and that preflight's decision
        # (authorized vs rejected) tracks that daf's OWN live drift profile
        # rather than assuming any particular outcome.
        rep_baseline = wp.repetition_baseline_entries()
        rep_daf = sorted({e["daf"] for e in rep_baseline})[0] if rep_baseline else None
        if rep_daf:
            r = subprocess.run([sys.executable, "scripts/worker_pipeline.py", "manifest",
                                "--type", "rashi-reconstruction", "--module", "yoma",
                                "--range", rep_daf, "--out", str(mpath)],
                               capture_output=True, text=True, cwd=REPO)
            check(f"manifest generation for {rep_daf} succeeds", r.returncode == 0, r.stderr[-200:])
            man = json.loads(mpath.read_text())
            snap = (man.get("repetitionDrain") or {}).get("snapshot", [])
            check(f"manifest embeds {rep_daf}'s repetition-baseline snapshot",
                  bool(snap) and all(e["daf"] == rep_daf for e in snap), str(snap))

            pf = subprocess.run([sys.executable, "scripts/worker_pipeline.py", "preflight",
                                 "--manifest", str(mpath), "--dry-run"],
                                capture_output=True, text=True, cwd=REPO)
            rep_prof = ars.profile_daf(rep_daf)
            expect_authorized = bool(rep_prof) and rep_prof["recommendedTaskType"] == "rashi-reconstruction"
            if expect_authorized:
                # Authorization succeeds, so the daf-specific rashi_preflight
                # check itself reports OK (no kept errors) independent of
                # unrelated environment preconditions like core.hooksPath,
                # which CI's fresh checkout never configures.
                check(f"rashi_preflight itself passes {rep_daf} for reconstruct",
                      f"rashi preflight {rep_daf} (reconstruct): OK" in pf.stdout, pf.stdout[-500:])
                check(f"preflight authorizes {rep_daf} reconstruction via repetition-drain (end to end)",
                      "repetition-drain authorized" in pf.stdout, pf.stdout[-500:])
            else:
                # Correctly rejected: reconstruct is not actually the
                # drift-approved remedy for this daf, so the daf-specific
                # check must NOT report OK either -- an unauthorized
                # repetition-baseline hit is exactly as blocking as always.
                check(f"preflight correctly REJECTS {rep_daf} repetition-drain: its live drift "
                      f"profile ({rep_prof['classification'] if rep_prof else None}) does not "
                      "recommend reconstruction, so debt alone never authorizes a bypass",
                      "repetition-drain not authorized" in pf.stdout, pf.stdout[-500:])
        else:
            print("  note: repetition-baseline is currently empty; drain-authorization "
                  "end-to-end coverage relies on the synthetic checks above instead")

        # Count mismatch has no drain path at all, unlike content-allowlist
        # and repetition-baseline hits: no real count-mismatch daf currently
        # exists in the corpus to test end to end, so this is asserted at
        # the source level instead. cmd_preflight's error-filtering loop
        # special-cases exactly two substrings ("CONTENT ALLOWLIST" and
        # "REPETITION-BASELINE"); it must never special-case "COUNT
        # MISMATCH" too, since any such branch would create a bypass for a
        # structural defect that rashi_preflight.py itself never offers one
        # for. Any error line the loop does not recognize (including every
        # COUNT MISMATCH line) falls straight into kept_errors and always
        # blocks, by construction of the loop's default behavior.
        src = (REPO / "scripts" / "worker_pipeline.py").read_text()
        cp_start = src.index("def cmd_preflight")
        cp_end = src.index("\ndef ", cp_start + 10)
        cp_body = src[cp_start:cp_end]
        check("count mismatch remains blocked: cmd_preflight's error-filtering loop "
              "never special-cases 'has unresolved COUNT MISMATCH' the way it does "
              "CONTENT ALLOWLIST/REPETITION-BASELINE (so it always falls through to "
              "kept_errors); a plain comment mentioning the words is fine",
              "has unresolved COUNT MISMATCH" not in cp_body)



def test_sonnet_only_policy():
    """Sonnet is the only execution and escalation model. Pins the whole
    registry plus every generated surface a worker actually reads, so a
    reintroduced Haiku/Fable route fails CI instead of silently shipping."""
    print("sonnet-only model policy:")
    types = wp.load_registry()
    for name, s in sorted(types.items()):
        check(f"{name} model is sonnet", s.get("model") == "sonnet",
              f"got {s.get('model')!r}")
        check(f"{name} escalationModel is sonnet", s.get("escalationModel") == "sonnet",
              f"got {s.get('escalationModel')!r}")
        check(f"{name} declares an explicit mechanicalTier boolean",
              isinstance(s.get("mechanicalTier"), bool))
        check(f"{name} review policy is a known value",
              wp.review_policy_of(s) in ("conditional", "independent", "none"))
    # No retired model name may survive anywhere in the machine-read policy
    # surface: registry, schema inventory, pipeline, or generated reference docs.
    banned = re.compile(r"haiku|fable", re.I)
    for rel in ("scripts/worker_task_types.json", "scripts/worker_schema_scope.json",
                "scripts/worker_pipeline.py", "docs/reports/task-type-reference.md",
                "docs/reports/schema-coverage-matrix.md"):
        hits = [l for l in (REPO / rel).read_text().splitlines() if banned.search(l)]
        check(f"{rel} carries no retired model name", not hits,
              f"{len(hits)} line(s), first: {hits[0].strip()[:70] if hits else ''}")
    # Every generated prompt must name Sonnet and never a retired model.
    with tempfile.TemporaryDirectory() as td:
        for ttype, rng in (("rashi-reconstruction", "70a"), ("audit-only", None),
                           ("deployment-verify", None), ("docs-tooling", None)):
            mp = Path(td) / f"{ttype}.json"
            args = [sys.executable, "scripts/worker_pipeline.py", "manifest",
                    "--type", ttype, "--module", "yoma", "--out", str(mp)]
            if rng:
                args += ["--range", rng]
            subprocess.run(args, capture_output=True, text=True, cwd=REPO)
            r = subprocess.run([sys.executable, "scripts/worker_pipeline.py", "prompt",
                                "--manifest", str(mp)], capture_output=True, text=True, cwd=REPO)
            check(f"{ttype} prompt generates", r.returncode == 0, r.stderr[-160:])
            check(f"{ttype} prompt carries no retired model name",
                  not banned.search(r.stdout))
            check(f"{ttype} prompt states Sonnet is the only model",
                  "only execution and escalation model" in r.stdout)


def test_lifecycle_consistency():
    """Every task type's lifecycle must agree with its own file scope, and a
    read-only pass must be forbidden from producing any tracked change. This
    is the contradiction the pre-15.332 registry carried: audit-only and
    deployment-verify forbade tracked changes while the universal loop
    demanded a VERSION bump and a PR from every pass."""
    print("task lifecycle consistency:")
    types = wp.load_registry()
    for name, s in sorted(types.items()):
        lc = wp.lifecycle_of(s)
        check(f"{name} lifecycle is a known value", lc in wp.LIFECYCLES)
        writes = [f for f in s["allowedFiles"] if f != ".worker-manifest.json"]
        if lc == "read-only":
            check(f"{name} read-only type declares no writable files", not writes,
                  f"declares {writes}")
        else:
            # A 'pr' type must be able to carry the VERSION bump its own
            # lifecycle requires; otherwise the loop is unsatisfiable.
            if writes:
                for need in ("VERSION", "package.json", "package-lock.json"):
                    check(f"{name} pr-lifecycle type may bump {need}",
                          need in s["allowedFiles"] and need not in s["forbiddenFiles"],
                          f"allowed={need in s['allowedFiles']} "
                          f"forbidden={need in s['forbiddenFiles']}")
    check("deployment-verify is read-only",
          wp.lifecycle_of(types["deployment-verify"]) == "read-only")
    check("audit-only writes reports, so it is a pr lifecycle",
          wp.lifecycle_of(types["audit-only"]) == "pr")
    check("audit-only still cannot touch modules or scripts",
          "modules/*" in types["audit-only"]["forbiddenFiles"]
          and "scripts/*" in types["audit-only"]["forbiddenFiles"])

    with tempfile.TemporaryDirectory() as td:
        mp = Path(td) / "m.json"
        subprocess.run([sys.executable, "scripts/worker_pipeline.py", "manifest",
                        "--type", "deployment-verify", "--module", "yoma", "--out", str(mp)],
                       capture_output=True, text=True, cwd=REPO)
        m = json.loads(mp.read_text())
        check("read-only manifest carries lifecycle read-only",
              m.get("lifecycle") == "read-only")
        r = subprocess.run([sys.executable, "scripts/worker_pipeline.py", "prompt",
                            "--manifest", str(mp)], capture_output=True, text=True, cwd=REPO)
        check("read-only prompt forbids the VERSION bump",
              "Do NOT bump VERSION" in r.stdout)
        check("read-only prompt forbids opening a PR",
              "do NOT open a PR" in r.stdout or "Do NOT commit" in r.stdout)
        check("read-only prompt does not order a VERSION bump step",
              "6. Bump VERSION one patch" not in r.stdout)
        # The enforcement itself. Deterministic regardless of ambient working-tree
        # state: verify_read_only must report ok exactly when nothing changed, and
        # a VERSION bump must always surface as an offending path.
        spec_dv = types["deployment-verify"]
        ok0, changed0 = wp.verify_read_only(m, spec_dv, "HEAD")
        check("verify_read_only reports ok exactly when nothing changed",
              ok0 == (not changed0))
        probe = REPO / "VERSION"
        original = probe.read_text()
        try:
            probe.write_text("99.999\n")
            ok2, changed2 = wp.verify_read_only(m, spec_dv, "HEAD")
            check("verify_read_only fails when VERSION is bumped", not ok2)
            check("verify_read_only names the offending path",
                  any(c.endswith("VERSION") for c in changed2), f"{changed2}")
        finally:
            probe.write_text(original)


def _write_synthetic_module(root, key, extra=None):
    """Write a minimal valid synthetic module.json under root/key, matching
    the shape scripts/test_module_resolver.py's VALID_FIXTURE uses. Returns
    the descriptor dict written."""
    d = {
        "key": key,
        "displayNameEn": "Fixture " + key,
        "displayNameHe": None,
        "sefariaTractate": None,
        "status": "synthetic",
        "publishable": False,
        "seder": None,
        "dafRange": {"first": "2a", "last": "2a"},
        "totalDaf": 1,
        "paths": {
            "root": f"modules/{key}",
            "scriptsRoot": f"modules/{key}/scripts",
            "sourceAssetsRoot": f"modules/{key}/assets",
            "generatedAssetsRoot": f"modules/{key}/assets",
            "sourceStore": f"modules/{key}/source_store.js",
            "learningDataDir": f"modules/{key}/assets/learning/{key}",
            "learningDataFile": f"modules/{key}/learning_data.js",
            "coverageFile": f"modules/{key}/coverage.json",
            "chapterMetadataLocation": None,
        },
        "schemaMapRef": "shared/schema_map.js",
        "capabilities": {
            "rashi": {"enabled": False},
            "literalTranslation": {"enabled": False},
        },
        "browserTest": {"defaultTargetDaf": "2a"},
        "docsOutput": {},
        "buildRuntime": {"dataScript": f"modules/{key}/learning_data.js"},
    }
    if extra:
        d.update(extra)
    mdir = Path(root) / key
    mdir.mkdir(parents=True, exist_ok=True)
    (mdir / "module.json").write_text(json.dumps(d), encoding="utf-8")
    return d


def test_module_awareness():
    """Phase 3 Step 3A: worker_pipeline.py must actually use a requested
    module, not silently resolve Yoma regardless of what was asked for.
    Uses a synthetic, temp-directory fixture module (never the real
    modules/ tree, never a real second tractate) via
    MYSUGYA_MODULE_SEARCH_ROOT - the same override mechanism
    module_resolver.resolve_module's own search_root parameter provides,
    threaded through worker_pipeline.resolve_active_module for exactly
    this purpose."""
    print("module awareness (Phase 3 Step 3A):")

    r = subprocess.run([sys.executable, "scripts/worker_pipeline.py", "manifest",
                        "--type", "docs-tooling", "--module", "does-not-exist-anywhere"],
                       capture_output=True, text=True, cwd=REPO)
    check("unknown module fails the manifest command (nonzero exit)",
          r.returncode != 0, f"exit={r.returncode}")
    check("unknown module error names the failure, not a silent Yoma manifest",
          "cannot resolve module" in (r.stdout + r.stderr) and
          '"module": "does-not-exist-anywhere"' not in r.stdout)

    with tempfile.TemporaryDirectory() as td:
        _write_synthetic_module(td, "fixturemasechet")
        env = dict(os.environ, MYSUGYA_MODULE_SEARCH_ROOT=td)

        r = subprocess.run([sys.executable, "scripts/worker_pipeline.py", "manifest",
                            "--type", "docs-tooling", "--module", "fixturemasechet"],
                           capture_output=True, text=True, cwd=REPO, env=env)
        check("a real synthetic module resolves cleanly via the search-root override",
              r.returncode == 0, r.stderr[-500:])
        if r.returncode == 0:
            fm = json.loads(r.stdout)
            check("the generated manifest carries the requested module, not yoma",
                  fm.get("module") == "fixturemasechet")

        r2 = subprocess.run([sys.executable, "scripts/worker_pipeline.py", "manifest",
                            "--type", "docs-tooling", "--module", "yoma"],
                           capture_output=True, text=True, cwd=REPO, env=env)
        check("the override REPLACES the search root rather than adding to it: "
              "yoma is not resolvable while the override points only at the "
              "temp fixture root, proving no hidden fallback to the real "
              "modules/ tree exists once an explicit override is in effect",
              r2.returncode != 0, f"exit={r2.returncode}")

    r3 = subprocess.run([sys.executable, "scripts/worker_pipeline.py", "manifest",
                        "--type", "docs-tooling", "--module", "yoma"],
                       capture_output=True, text=True, cwd=REPO)
    check("with the override unset (normal invocation), yoma resolves exactly "
          "as before this whole test ran", r3.returncode == 0, r3.stderr[-500:])

    # structural-repair's allowedFiles are <module>-templated content paths
    # (unlike docs-tooling's modules/*/module.json, which is a deliberate
    # any-module wildcard for pipeline-config PRs, not a <module> template) -
    # the right type to prove <module> substitution actually discriminates.
    spec = wp.load_registry()["structural-repair"]
    check("file_allowed for a Yoma learning_data.js against the fixture's own "
          "module is refused (mismatched module+path is rejected)",
          not wp.file_allowed("modules/yoma/learning_data.js", spec, [], "fixturemasechet"))
    check("file_allowed for a fixture learning_data.js against yoma's own "
          "module is refused (rejected in the other direction too)",
          not wp.file_allowed("modules/fixturemasechet/learning_data.js", spec, [], "yoma"))
    check("file_allowed for a Yoma learning_data.js against yoma's own module "
          "still works (sanity - <module> templating did not break the real case)",
          wp.file_allowed("modules/yoma/learning_data.js", spec, [], "yoma"))
    check("file_allowed for a fixture learning_data.js against the fixture's "
          "own module resolves correctly (a fixture-targeted manifest can "
          "write its own fixture paths)",
          wp.file_allowed("modules/fixturemasechet/learning_data.js", spec, [], "fixturemasechet"))


def main():
    test_registry()
    test_sonnet_only_policy()
    test_lifecycle_consistency()
    test_pure_policy()
    test_live_gate_fails_closed()
    test_prompt()
    test_queue()
    test_structural_repair_type()
    test_evidence_tiers()
    test_campaign_capability_scan()
    test_independent_zero_citation_scan()
    test_allowlist_drain()
    test_scaffold_debt_drain()
    test_repetition_drain()
    test_structural_deferral_in_scope_validator()
    test_no_direct_main_push_anywhere()
    test_docs_tooling_scope_boundaries()
    test_boundary_authorized_empty_links()
    test_module_awareness()
    if FAILURES:
        print(f"\nFAILED: {len(FAILURES)} check(s): {FAILURES}")
        sys.exit(1)
    print("\nOK: all worker policy tests passed.")


if __name__ == "__main__":
    main()
