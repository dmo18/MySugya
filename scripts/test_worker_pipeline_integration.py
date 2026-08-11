#!/usr/bin/env python3
"""test_worker_pipeline_integration.py - integration tests that invoke the
REAL worker_pipeline.py subcommands (manifest / preflight / scope / verify)
as subprocesses against a disposable fixture repository -- never a
duplicate, simplified reimplementation of the pipeline's logic, and never
the real working tree or its branch history.

The fixture repository is a full throwaway copy of the current repo tree
(node_modules/dist/.git excluded), git-initialized with one snapshot
commit, built fresh into a temp directory each run and discarded
afterward. All file edits and git commits in these tests happen ONLY
inside that disposable copy; nothing here ever writes to this repository's
own working tree, and modules/yoma is never touched outside the fixture.

Run from repo root (takes roughly a minute: several full worker:verify
passes, each running the offline gate suite):
  python3 scripts/test_worker_pipeline_integration.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
FAILED = []
FIXTURE = None


def check(name, cond, detail=""):
    d = str(detail)
    print("  %s %s%s" % ("ok  " if cond else "FAIL", name, "" if cond else " (%s)" % d[-900:]))
    if not cond:
        FAILED.append(name)


def run(cmd, cwd, env=None):
    e = dict(os.environ, **(env or {}))
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, env=e)


def git(*args, cwd):
    return run(["git", *args], cwd=cwd)


def wp(*args):
    return run([sys.executable, "scripts/worker_pipeline.py", *args], cwd=FIXTURE)


def out(r):
    return (r.stdout or "") + (r.stderr or "")


def make_fixture_repo():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="mysugya-worker-fixture-"))
    dest = tmp / "repo"
    dest.mkdir()
    r = subprocess.run(
        "tar --exclude=.git --exclude=node_modules --exclude=dist -cf - . | tar -xf - -C %s" % dest,
        shell=True, cwd=str(ROOT), capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    # The fixture excludes node_modules (heavy, irrelevant to worker_pipeline
    # itself) so the REAL pre-commit hook (which runs npm build/test) cannot
    # run here; replace it with a no-op inside the fixture only, so `git
    # commit` stays fast while core.hooksPath is still literally "githooks"
    # for preflight's own hooksPath check.
    hook = dest / "githooks" / "pre-commit"
    hook.write_text("#!/bin/sh\nexit 0\n")
    hook.chmod(0o755)
    git("init", "-q", cwd=dest)
    git("config", "core.hooksPath", "githooks", cwd=dest)
    # -f: the real repo's .gitignore blanket-excludes any assets/ directory
    # (re-included there only for the demotractate fixture); modules/yoma's
    # talmuddev/daftexts/learning JSON is force-tracked in the real repo's
    # history despite that rule, so a fresh `git init` here must force-add
    # it too or the fixture would silently start with zero source/learning
    # files.
    git("add", "-A", "-f", cwd=dest)
    r = git("-c", "user.email=test@test.local", "-c", "user.name=test",
           "commit", "-q", "-m", "snapshot", cwd=dest)
    assert r.returncode == 0, r.stderr
    sha = git("rev-parse", "HEAD", cwd=dest).stdout.strip()
    return dest, sha


def reset_to_base():
    git("checkout", "-q", "-B", "work", BASE_SHA, cwd=FIXTURE)
    git("clean", "-q", "-fdx", cwd=FIXTURE)


def commit(message):
    git("add", "-A", cwd=FIXTURE)
    return git("-c", "user.email=test@test.local", "-c", "user.name=test",
               "commit", "-q", "-m", message, cwd=FIXTURE)


def learning_path(daf):
    return FIXTURE / "modules/yoma/assets/learning/yoma" / (daf + ".learning.json")


def load_learning(daf):
    return json.loads(learning_path(daf).read_text())


def save_learning(daf, doc):
    learning_path(daf).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")


def rebuild_yoma():
    """The full generation pipeline check_generated_freshness.py expects:
    build_learning_data.py alone is not enough, or the freshness gate fails
    even on an otherwise-correct regeneration."""
    r1 = run([sys.executable, "scripts/build_learning_data.py"], cwd=FIXTURE / "modules/yoma")
    if r1.returncode != 0:
        return r1
    return run([sys.executable, "scripts/build_literal_layer.py", "--apply"],
              cwd=FIXTURE / "modules/yoma")


print("building disposable fixture repository (one-time tar+git-init copy)...")
FIXTURE, BASE_SHA = make_fixture_repo()
print("fixture: %s @ %s" % (FIXTURE, BASE_SHA[:12]))

try:
    # =========================================================================
    # 1-7. legacy-concepts-purge: corpus-wide manifest, required authorizations,
    #      deleteOnly production enforcement (exact deletion / null / content
    #      change / sibling change / descriptor-derived full-daf target).
    # =========================================================================
    reset_to_base()
    r = wp("manifest", "--type", "legacy-concepts-purge", "--module", "yoma",
          "--authorize", "allowDeleteRemovedField")
    check("1/2. corpus-wide purge manifest FAILS without allowCorpusWideMechanicalMigration",
          r.returncode != 0 and "allowCorpusWideMechanicalMigration" in out(r), out(r))

    r = wp("manifest", "--type", "legacy-concepts-purge", "--module", "yoma",
          "--authorize", "allowDeleteRemovedField",
          "--authorize", "allowCorpusWideMechanicalMigration",
          "--out", ".worker-manifest.json")
    check("1. corpus-wide purge manifest generates with BOTH required authorizations",
          r.returncode == 0, out(r))
    manifest = json.loads((FIXTURE / ".worker-manifest.json").read_text())
    all_daf = manifest["targets"]
    check("7. descriptor-derived target set is the full 173-daf set, explicit (not empty)",
          len(all_daf) == 173 and "2a" in all_daf and "88a" in all_daf, len(all_daf))

    r = wp("preflight", "--manifest", ".worker-manifest.json", "--dry-run")
    check("preflight passes for the corpus-wide purge manifest", r.returncode == 0, out(r))

    # Apply the REAL purge: delete the concepts key from every sugya, on
    # every daf -- exactly what the deleteOnly contract authorizes.
    deleted = 0
    for daf in all_daf:
        doc = load_learning(daf)
        for s in doc.get("sugyot", []):
            if "concepts" in s:
                del s["concepts"]
                deleted += 1
        save_learning(daf, doc)
    rb = rebuild_yoma()
    check("corpus-wide purge: build_learning_data.py regenerates cleanly", rb.returncode == 0, out(rb))
    commit("legacy-concepts-purge: corpus-wide")

    r = wp("scope", "--manifest", ".worker-manifest.json", "--base", BASE_SHA)
    check("3. exact concepts deletion (every sugya) passes production scope", r.returncode == 0, out(r))

    r = wp("verify", "--manifest", ".worker-manifest.json", "--base", BASE_SHA, "--fast")
    check("corpus-wide purge passes production verify (deleteOnly + exact-count + rule-scoped)",
          r.returncode == 0 and "concepts-purge-exact-deletion" in out(r), out(r)[-1500:])
    check("verify reports zero legacy_concepts_present debt after the purge",
          "task-scoped-enrichment-clean" in out(r) and "FAIL" not in out(r).split("task-specific")[-1][:400],
          out(r)[-800:])

    # ---- 4. setting concepts to null instead of deleting the key fails ----
    reset_to_base()
    wp("manifest", "--type", "legacy-concepts-purge", "--module", "yoma", "--range", "2a",
      "--authorize", "allowDeleteRemovedField", "--out", ".worker-manifest.json")
    doc = load_learning("2a")
    doc["sugyot"][0]["concepts"] = None
    save_learning("2a", doc)
    commit("set concepts to null instead of deleting")
    r = wp("scope", "--manifest", ".worker-manifest.json", "--base", BASE_SHA)
    check("4. setting concepts to null (not deleting the key) FAILS production scope",
          r.returncode != 0 and "deleteOnly" in out(r), out(r))

    # ---- 5. changing concepts CONTENT instead of deleting it fails --------
    reset_to_base()
    wp("manifest", "--type", "legacy-concepts-purge", "--module", "yoma", "--range", "2a",
      "--authorize", "allowDeleteRemovedField", "--out", ".worker-manifest.json")
    doc = load_learning("2a")
    doc["sugyot"][0]["concepts"] = {"halachic": ["totally-different-value"]}
    save_learning("2a", doc)
    commit("edit concepts content instead of deleting")
    r = wp("scope", "--manifest", ".worker-manifest.json", "--base", BASE_SHA)
    check("5. editing concepts CONTENT (key still present) FAILS production scope",
          r.returncode != 0 and "concepts" in out(r) and "outside the" in out(r), out(r))

    # ---- 6. changing a sibling field fails ---------------------------------
    reset_to_base()
    wp("manifest", "--type", "legacy-concepts-purge", "--module", "yoma", "--range", "2a",
      "--authorize", "allowDeleteRemovedField", "--out", ".worker-manifest.json")
    doc = load_learning("2a")
    del doc["sugyot"][0]["concepts"]
    doc["sugyot"][0]["display"]["hint"] = "A completely different hint that was never authorized?"
    save_learning("2a", doc)
    commit("delete concepts AND edit a sibling field")
    r = wp("scope", "--manifest", ".worker-manifest.json", "--base", BASE_SHA)
    check("6. changing a sibling field (display.hint) alongside the deletion FAILS scope",
          r.returncode != 0 and "display" in out(r) and "hint" in out(r), out(r))

    # =========================================================================
    # 8-10. enrichment-schema-migration: migrationKinds is required real data,
    #       restricts real diffs, and rule-scoped target-clean tolerates
    #       unrelated semantic debt.
    # =========================================================================
    reset_to_base()
    r = wp("manifest", "--type", "enrichment-schema-migration", "--module", "yoma",
          "--range", "2a", "--authorize", "authorizeMigration")
    check("8. enrichment-schema-migration manifest FAILS without --migration-kind",
          r.returncode != 0 and "migration-kind" in out(r), out(r))

    r = wp("manifest", "--type", "enrichment-schema-migration", "--module", "yoma",
          "--range", "2a", "--authorize", "authorizeMigration",
          "--migration-kind", "difficulty", "--out", ".worker-manifest.json")
    check("8b. enrichment-schema-migration manifest succeeds with a migrationKind",
          r.returncode == 0, out(r))

    # 9. a migration can edit ONLY the paths owned by its selected kind:
    # edit difficulty (owned) -> passes; edit topicTags (NOT owned by the
    # 'difficulty' kind, even though the task TYPE could touch it) -> fails.
    doc = load_learning("2a")
    doc["sugyot"][0]["difficulty"] = "intro"
    save_learning("2a", doc)
    commit("migration: edit difficulty only")
    r = wp("scope", "--manifest", ".worker-manifest.json", "--base", BASE_SHA)
    check("9. a migration editing ONLY its selected kind's path passes scope",
          r.returncode == 0, out(r))

    doc = load_learning("2a")
    doc["sugyot"][0]["topicTags"] = ["some-other-tag"]
    save_learning("2a", doc)
    commit("migration: also edit topicTags (unselected kind)")
    r = wp("scope", "--manifest", ".worker-manifest.json", "--base", BASE_SHA)
    check("9b. a migration editing a path OUTSIDE its selected migrationKinds FAILS scope",
          r.returncode != 0 and "difficulty" not in out(r).split("outside")[0][-30:], out(r))

    # 10. rule-scoped target-clean: fixing difficulty on EVERY sugya of the
    # target daf passes even though those same sugyot still carry unrelated
    # hint/topicTag/concepts debt (target-clean is per-rule, not whole-sugya).
    reset_to_base()
    wp("manifest", "--type", "enrichment-schema-migration", "--module", "yoma",
      "--range", "2a", "--authorize", "authorizeMigration",
      "--migration-kind", "difficulty", "--out", ".worker-manifest.json")
    doc = load_learning("2a")
    for sug in doc["sugyot"]:
        sug["difficulty"] = "advanced"  # every sugya on 2a now has a legal difficulty value
    save_learning("2a", doc)
    rebuild_yoma()
    commit("migration: fix difficulty enum on 2a, unrelated debt untouched")
    r = wp("verify", "--manifest", ".worker-manifest.json", "--base", BASE_SHA, "--fast")
    check("10. schema migration passes rule-scoped target-clean despite unrelated semantic debt",
          r.returncode == 0 and "task-scoped-enrichment-clean" in out(r), out(r)[-1800:])

    # =========================================================================
    # 11-13. audited-sugya-enrichment-repair: auditRecordIds is real,
    #        validated manifest data.
    # =========================================================================
    reset_to_base()
    queue = json.loads((FIXTURE / "docs/reports/data/yoma-tail-enrichment-repair-queue.json")
                       .read_text())
    real_id = queue["records"][0]["sugyaId"]
    real_daf = queue["records"][0]["daf"]

    r = wp("manifest", "--type", "audited-sugya-enrichment-repair", "--module", "yoma",
          "--range", real_daf, "--audit-record-id", "yoma-999a-s99")
    check("12. a nonexistent audit id FAILS manifest generation",
          r.returncode != 0 and "not found in the merged audit" in out(r), out(r))

    r = wp("manifest", "--type", "audited-sugya-enrichment-repair", "--module", "yoma",
          "--range", "2a", "--audit-record-id", real_id)
    check("12b. an audit id belonging to a DIFFERENT daf than --range FAILS manifest generation",
          r.returncode != 0 and "belongs to daf" in out(r), out(r))

    r = wp("manifest", "--type", "audited-sugya-enrichment-repair", "--module", "yoma",
          "--range", real_daf, "--audit-record-id", real_id, "--out", ".worker-manifest.json")
    check("11. an audit-repair manifest with a real, matching auditRecordId succeeds",
          r.returncode == 0, out(r))
    m = json.loads((FIXTURE / ".worker-manifest.json").read_text())
    check("11b. auditRecordIds is stored as real manifest data, not an authorization flag",
          m["auditRecordIds"] == [real_id] and real_id not in m["authorizations"], m)

    r = wp("preflight", "--manifest", ".worker-manifest.json", "--dry-run")
    check("preflight passes for a fresh (not-yet-COMPLETE) audit repair manifest",
          r.returncode == 0, out(r))

    # 13. a changed path absent from the named record's affectedFields fails
    rec = next(r for r in queue["records"] if r["sugyaId"] == real_id)
    audit_doc = json.loads((FIXTURE / "docs/reports/data/yoma-tail-enrichment-audit.json").read_text())
    audit_rec = next(a for a in audit_doc["records"] if a["sugyaId"] == real_id)
    doc = load_learning(real_daf)
    sug = next(s for s in doc["sugyot"] if s["id"] == real_id)
    if "difficulty" not in audit_rec["affectedFields"]:
        sug["difficulty"] = "advanced"
        save_learning(real_daf, doc)
        rebuild_yoma()
        commit("repair: touch a path NOT in this record's affectedFields")
        r = wp("scope", "--manifest", ".worker-manifest.json", "--base", BASE_SHA)
        check("13. a changed path absent from affectedFields FAILS scope",
              r.returncode != 0 and "affectedFields" in out(r), out(r))
    else:
        check("13. a changed path absent from affectedFields FAILS scope", True,
              "(skipped: difficulty happens to already be an affected field for this record)")

    # =========================================================================
    # 14. queue progress durability: advance survives regeneration; invalid
    #     transitions and unknown ids are rejected.
    # =========================================================================
    reset_to_base()
    prog_path = FIXTURE / "docs/reports/data/yoma-tail-enrichment-repair-progress.json"
    prog = json.loads(prog_path.read_text())
    prog["progress"][real_id]["status"] = "IN_PROGRESS"
    prog_path.write_text(json.dumps(prog, ensure_ascii=False, indent=1) + "\n")
    commit("advance progress to IN_PROGRESS")
    r = run([sys.executable, "scripts/generate_enrichment_repair_queue.py", "--check",
            "--base", BASE_SHA], cwd=FIXTURE)
    check("14a. a legal forward progress transition passes --check", r.returncode == 0, out(r))

    r = run([sys.executable, "scripts/generate_enrichment_repair_queue.py"], cwd=FIXTURE)
    prog_after = json.loads(prog_path.read_text())
    check("14b. progress advancement SURVIVES queue regeneration",
          prog_after["progress"][real_id]["status"] == "IN_PROGRESS", prog_after["progress"][real_id])

    commit("regenerated queue/progress")
    prog2 = json.loads(prog_path.read_text())
    prog2["progress"][real_id]["status"] = "COMPLETE"  # illegal: skips FIXED_PENDING_REVIEW
    prog_path.write_text(json.dumps(prog2, ensure_ascii=False, indent=1) + "\n")
    commit("illegal skip straight to COMPLETE")
    r = run([sys.executable, "scripts/generate_enrichment_repair_queue.py", "--check",
            "--base", BASE_SHA], cwd=FIXTURE)
    check("14c. an illegal/skipped status transition FAILS --check",
          r.returncode != 0 and "illegal status transition" in out(r), out(r))

    reset_to_base()
    prog3 = json.loads(prog_path.read_text())
    prog3["progress"]["yoma-999a-s99-not-real"] = {"status": "NOT_STARTED"}
    prog_path.write_text(json.dumps(prog3, ensure_ascii=False, indent=1) + "\n")
    commit("unknown progress id")
    r = run([sys.executable, "scripts/generate_enrichment_repair_queue.py", "--check",
            "--base", BASE_SHA], cwd=FIXTURE)
    check("unknown progress sugyaId FAILS --check",
          r.returncode != 0 and "unknown sugyaId" in out(r), out(r))

    # =========================================================================
    # 15-18. baseline ratchet reaching zero / rule deletion / same-sugya
    #        worsening / module isolation, via the REAL CLI against a
    #        disposable module copy (not the frozen real Yoma corpus).
    # =========================================================================
    reset_to_base()
    doc = load_learning("2a")
    sug = doc["sugyot"][0]
    # Force this sugya clean for difficulty_invalid_enum specifically
    # (whatever its current baselined state) and confirm the CLI still
    # passes -- reaching zero for one rule/sugya is a pass, not a failure.
    sug["difficulty"] = "intro"
    save_learning("2a", doc)
    rebuild_yoma()
    r = run([sys.executable, "scripts/validate_enrichment_contracts.py", "--module", "yoma"],
           cwd=FIXTURE)
    check("15. reaching zero for a baselined rule/sugya passes the real CLI",
          r.returncode == 0, out(r)[-800:])

    # 16. deleting a rule's implementation (production code) fails the gate.
    # Removes BOTH the RULES registry entry AND the detection block that
    # would otherwise still try to flag it -- a genuine "this check was
    # deleted from the code" scenario, not just an unused registry id.
    validator_src = (FIXTURE / "scripts/validate_enrichment_contracts.py").read_text()
    mutilated = validator_src.replace('"difficulty_invalid_enum",\n)', '\n)')
    detect_block = (
        '        # ---- difficulty -----------------------------------------------------\n'
        '        if s.get("difficulty") is not None and s.get("difficulty") not in DIFFICULTY:\n'
        '            flag("difficulty_invalid_enum", sid, "difficulty", None, s.get("difficulty"),\n'
        '                 repr(s.get("difficulty")))\n'
    )
    assert detect_block in mutilated, "detection block text drifted; update this test"
    mutilated = mutilated.replace(detect_block, "")
    assert mutilated != validator_src
    (FIXTURE / "scripts/validate_enrichment_contracts.py").write_text(mutilated)
    r = run([sys.executable, "scripts/validate_enrichment_contracts.py", "--module", "yoma"],
           cwd=FIXTURE)
    check("16. removing a rule's implementation from the real RULES registry+detector "
         "FAILS the real CLI",
          r.returncode != 0 and "not a currently registered rule" in out(r), out(r)[-800:])
    (FIXTURE / "scripts/validate_enrichment_contracts.py").write_text(validator_src)

    # 17. same-sugya occurrence growth fails via the real CLI end to end.
    reset_to_base()
    doc = load_learning("3a")
    sug2 = doc["sugyot"][0]
    sug2["topicTags"] = ["Already Bad Tag"]
    save_learning("3a", doc)
    rebuild_yoma()
    r = run([sys.executable, "scripts/validate_enrichment_contracts.py", "--module", "yoma",
            "--update-baseline"], cwd=FIXTURE)
    check("(setup) --update-baseline writes a fresh baseline for the growth test",
          r.returncode == 0, out(r)[-400:])
    doc = load_learning("3a")
    doc["sugyot"][0]["topicTags"] = ["Already Bad Tag", "A Second Bad Tag"]
    save_learning("3a", doc)
    rebuild_yoma()
    r = run([sys.executable, "scripts/validate_enrichment_contracts.py", "--module", "yoma"],
           cwd=FIXTURE)
    check("17. same-sugya occurrence growth FAILS the real CLI",
          r.returncode != 0 and ("count rose" in out(r) or "same-sugya worsening" in out(r)),
          out(r)[-1000:])

    # 18. a module cannot use another module's baseline (real CLI, real
    # module-scoped path resolution against a fixture module named 'yoma2'
    # that borrows Yoma's committed baseline).
    reset_to_base()
    src_mod = FIXTURE / "modules" / "yoma"
    dst_mod = FIXTURE / "modules" / "yoma2"
    shutil.copytree(src_mod, dst_mod)
    desc = json.loads((dst_mod / "module.json").read_text())
    desc["key"] = "yoma2"
    for f in ("root", "scriptsRoot", "sourceAssetsRoot", "generatedAssetsRoot", "sourceStore",
             "learningDataDir", "learningDataFile", "coverageFile"):
        desc["paths"][f] = desc["paths"][f].replace("modules/yoma", "modules/yoma2", 1)
    desc["buildRuntime"]["dataScript"] = desc["paths"]["learningDataFile"]
    (dst_mod / "module.json").write_text(json.dumps(desc, ensure_ascii=False, indent=1))
    learn_dir = FIXTURE / "modules/yoma2/assets/learning/yoma"
    learn_dir.rename(FIXTURE / "modules/yoma2/assets/learning/yoma2")
    baseline_src = FIXTURE / "scripts/baselines/yoma_enrichment_contract_debt.json"
    baseline_dst = FIXTURE / "scripts/baselines/yoma2_enrichment_contract_debt.json"
    shutil.copy(baseline_src, baseline_dst)
    borrowed = json.loads(baseline_dst.read_text())
    borrowed["module"] = "yoma"  # deliberately still claims to be yoma's baseline
    baseline_dst.write_text(json.dumps(borrowed, ensure_ascii=False, indent=1))
    r = run([sys.executable, "scripts/validate_enrichment_contracts.py", "--module", "yoma2"],
           cwd=FIXTURE)
    check("18. a module baseline claiming a DIFFERENT module's identity FAILS the real CLI",
          r.returncode != 0 and "does not match --module" in out(r), out(r)[-800:])

    # =========================================================================
    # 19. sourcesMustBeUnchanged is actually enforced (production verify).
    # =========================================================================
    reset_to_base()
    wp("manifest", "--type", "legacy-concepts-purge", "--module", "yoma", "--range", "2a",
      "--authorize", "allowDeleteRemovedField", "--out", ".worker-manifest.json")
    doc = load_learning("2a")
    del doc["sugyot"][0]["concepts"]
    # sneak an argumentFlow edit in alongside the authorized deletion
    if doc["sugyot"][0].get("argumentFlow"):
        doc["sugyot"][0]["argumentFlow"][0]["text"] = "An unauthorized rewritten argument step."
    save_learning("2a", doc)
    commit("purge concepts AND sneak an argumentFlow edit")
    r = wp("scope", "--manifest", ".worker-manifest.json", "--base", BASE_SHA)
    check("19. an argumentFlow edit alongside an authorized deletion FAILS production scope",
          r.returncode != 0, out(r))
    # verify_sources_unchanged is defense-in-depth on top of jsonScope; prove
    # it independently by calling it directly against the same diff.
    sys.path.insert(0, str(FIXTURE / "scripts"))
    import importlib
    if "worker_pipeline" in sys.modules:
        del sys.modules["worker_pipeline"]
    os.chdir(FIXTURE)
    wpm = importlib.import_module("worker_pipeline")
    wpm.REPO = FIXTURE
    wpm.set_active_module(wpm.resolve_active_module("yoma"))
    changed = wpm.sh(["git", "diff", "--name-only", BASE_SHA]).stdout.split()
    spec = wpm.load_registry()["legacy-concepts-purge"]
    src_ok, src_msgs = wpm.verify_sources_unchanged(spec, changed, BASE_SHA)
    check("19b. verify_sources_unchanged independently catches the argumentFlow edit",
          not src_ok and any("argumentFlow" in msg for msg in src_msgs), src_msgs)
    os.chdir(str(ROOT))

finally:
    if FIXTURE and FIXTURE.exists():
        shutil.rmtree(FIXTURE.parent, ignore_errors=True)
    print("\nfixture repository cleaned up.")

if FAILED:
    print("\n%d integration check(s) failed: %s" % (len(FAILED), FAILED))
    sys.exit(1)
print("\nAll worker-pipeline integration checks passed.")
