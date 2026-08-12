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


def seed_synthetic_legacy_concepts(dest):
    """Stamp a deterministic synthetic `concepts` key onto every sugya in the
    fixture's OWN copy of the Yoma learning JSON, regardless of whether the
    ambient real corpus this fixture was tar-copied from still carries the
    legacy `concepts` field. The legacy-concepts-purge integration tests need
    a fixture baseline that reliably has this removed field present so they
    can exercise real deletion, null-instead-of-delete, content-edit, and
    sibling-edit scenarios deterministically -- never by depending on the
    real repository's own migration state, which changes exactly once this
    purge itself lands. The synthetic value's shape does not matter (the
    contract flags KEY PRESENCE, not content), so an empty dict is enough.
    Regenerates the fixture's own learning_data.js/coverage.json afterward so
    the fixture's generated-freshness gate stays internally consistent.

    The seeded value's CONTENT fingerprint differs from whatever the real,
    tar-copied frozen baseline recorded for the ORIGINAL concepts content
    (which no longer exists once the real corpus has actually been purged),
    so the fixture's own baseline is regenerated fresh (--update-baseline)
    against this now-seeded corpus too. Every OTHER rule's debt (hint,
    finalRuling, etc.) is untouched by seeding, so this reproduces identical
    entries for those rules while making legacy_concepts_present internally
    consistent with the fixture's own deterministic seeded state -- never
    with the real repository's historical baseline content."""
    learn_dir = dest / "modules/yoma/assets/learning/yoma"
    for fp in sorted(learn_dir.glob("*.learning.json")):
        doc = json.loads(fp.read_text(encoding="utf-8"))
        changed = False
        for s in doc.get("sugyot", []):
            if "concepts" not in s:
                s["concepts"] = {}
                changed = True
        if changed:
            fp.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    r1 = subprocess.run([sys.executable, "scripts/build_learning_data.py"],
                        cwd=str(dest / "modules/yoma"), capture_output=True, text=True)
    assert r1.returncode == 0, r1.stdout + r1.stderr
    r2 = subprocess.run([sys.executable, "scripts/build_literal_layer.py", "--apply"],
                        cwd=str(dest / "modules/yoma"), capture_output=True, text=True)
    assert r2.returncode == 0, r2.stdout + r2.stderr
    r3 = subprocess.run([sys.executable, "scripts/validate_enrichment_contracts.py",
                        "--module", "yoma", "--update-baseline"],
                        cwd=str(dest), capture_output=True, text=True)
    assert r3.returncode == 0, r3.stdout + r3.stderr


def make_fixture_repo():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="mysugya-worker-fixture-"))
    dest = tmp / "repo"
    dest.mkdir()
    r = subprocess.run(
        "tar --exclude=.git --exclude=node_modules --exclude=dist --exclude=__pycache__ "
        "-cf - . | tar -xf - -C %s" % dest,
        shell=True, cwd=str(ROOT), capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    # __pycache__ is gitignored, so it is never a REAL tracked file, but a
    # stray one left in the developer's own working tree (from running any
    # scripts/*.py directly) would otherwise get force-added into the
    # fixture's own initial commit below (git add -A -f), then keep getting
    # swept into every later `commit()` in these tests as a phantom scope
    # violation. Excluded above at the tar step; nothing else to do here.
    seed_synthetic_legacy_concepts(dest)
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


def reset_to_prereqs_satisfied(sids):
    """Like reset_to_base(), but starting from ONE extra commit on top of
    BASE_SHA that purges `concepts` corpus-wide and fixes the migration-
    prerequisite defects (requiresUnderstanding prose, visualizableElements
    legacy 'name' key / bare values, difficulty 'introductory') for exactly
    the named sugya ids -- mirroring a real repo where the mechanical
    migration PRs already merged before any audited-sugya-enrichment-repair
    PR opens, so that PR's own diff never has to touch migration fields.
    Returns the new base commit's sha; callers pass THIS (not BASE_SHA) to
    any subsequent wp('scope'/'verify', '--base', ...) call in the same
    test group, since requirement 5's separate migration-prerequisite gate
    (scripts/worker_pipeline.py's audit_repair_prerequisite_errors) now
    genuinely blocks manifest generation for these task types otherwise."""
    reset_to_base()
    all_daf = json.loads(wp("manifest", "--type", "legacy-concepts-purge", "--module", "yoma",
                            "--authorize", "allowDeleteRemovedField",
                            "--authorize", "allowCorpusWideMechanicalMigration").stdout)["targets"]
    sid_set = set(sids)
    for daf in all_daf:
        doc = load_learning(daf)
        changed = False
        for s in doc.get("sugyot", []):
            if "concepts" in s:
                del s["concepts"]
                changed = True
            if s.get("id") in sid_set:
                if isinstance(s.get("requiresUnderstanding"), list) and s["requiresUnderstanding"]:
                    s["requiresUnderstanding"] = []
                    changed = True
                ve = s.get("visualizableElements")
                if isinstance(ve, list) and ve:
                    new_ve = []
                    for el in ve:
                        if isinstance(el, str):
                            new_ve.append({"item": el})
                        elif isinstance(el, dict):
                            el = dict(el)
                            if "name" in el and not el.get("item"):
                                el["item"] = el.pop("name")
                            else:
                                el.pop("name", None)
                            for k in list(el.keys()):
                                if k not in ("item", "type", "label", "role", "priority"):
                                    el.pop(k, None)
                            new_ve.append(el)
                        else:
                            new_ve.append(el)
                    s["visualizableElements"] = new_ve
                    changed = True
                if s.get("difficulty") == "introductory":
                    s["difficulty"] = "intro"
                    changed = True
        if changed:
            save_learning(daf, doc)
    rebuild_yoma()
    commit("prerequisites landed for %s: corpus-wide concepts purge + per-record migrations"
          % sorted(sid_set))
    return git("rev-parse", "HEAD", cwd=FIXTURE).stdout.strip()


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
    queue = json.loads((FIXTURE / "docs/reports/data/yoma-tail-enrichment-repair-queue.json")
                       .read_text())
    real_id = queue["records"][0]["sugyaId"]
    real_daf = queue["records"][0]["daf"]
    # Prerequisites (corpus-wide concepts purge + this record's own
    # migration prerequisites) are established as ONE base commit here, so
    # this section's own diffs never have to touch migration fields --
    # requirement 5's separate prerequisite gate would otherwise legitimately
    # block every manifest generation below (this section tests SCOPE/field
    # behavior, not the prerequisite gate itself; that gate has its own
    # dedicated tests in 13a-13d against a genuinely unsatisfied fixture).
    PREREQ_BASE_11 = reset_to_prereqs_satisfied([real_id])

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
        r = wp("scope", "--manifest", ".worker-manifest.json", "--base", PREREQ_BASE_11)
        check("13. a changed path absent from affectedFields FAILS scope",
              r.returncode != 0 and "affectedFields" in out(r), out(r))
    else:
        check("13. a changed path absent from affectedFields FAILS scope", True,
              "(skipped: difficulty happens to already be an affected field for this record)")

    # =========================================================================
    # 13a-13d. MIGRATION PREREQUISITES are enforced SEPARATELY from semantic
    #          target-clean, before a manifest/preflight may even succeed.
    #          Exercised through both the real CLI (manifest generation) and
    #          a direct call to the production function preflight itself
    #          uses (audit_repair_prerequisite_errors), so both entry points
    #          are proven, not just the one that happens to write a file.
    # =========================================================================
    prereq_id = queue["records"][0]["sugyaId"]
    prereq_rec = queue["records"][0]
    prereq_daf = queue["records"][0]["daf"]
    check("(setup) the first queue record carries migration prerequisites",
          bool(prereq_rec.get("migrationPrerequisites")), prereq_rec)

    # ---- 13a. FAILS before the corpus-wide concepts purge (real CLI) ------
    reset_to_base()
    r = wp("manifest", "--type", "audited-sugya-enrichment-repair", "--module", "yoma",
          "--range", prereq_daf, "--audit-record-id", prereq_id)
    check("13a. an audit repair manifest FAILS before the corpus-wide concepts purge",
          r.returncode != 0 and "legacy concepts purge is not complete" in out(r), out(r))

    import importlib as _importlib
    sys.path.insert(0, str(FIXTURE / "scripts"))
    if "worker_pipeline" in sys.modules:
        del sys.modules["worker_pipeline"]
    os.chdir(FIXTURE)
    wpm2 = _importlib.import_module("worker_pipeline")
    wpm2.REPO = FIXTURE
    wpm2.set_active_module(wpm2.resolve_active_module("yoma"))
    pre_purge_errs = wpm2.audit_repair_prerequisite_errors([prereq_id])
    check("13a2. the production preflight function ALSO fails before the purge "
         "(direct call, same function preflight/manifest both use)",
          any("legacy concepts purge is not complete" in e for e in pre_purge_errs),
          pre_purge_errs)
    os.chdir(str(ROOT))

    # ---- 13b. still FAILS after the purge, while the target's declared
    #           migration prerequisite remains unmet for that sugya --------
    reset_to_base()
    all_daf_p = json.loads(wp("manifest", "--type", "legacy-concepts-purge", "--module", "yoma",
                              "--authorize", "allowDeleteRemovedField",
                              "--authorize", "allowCorpusWideMechanicalMigration").stdout)["targets"]
    for daf in all_daf_p:
        doc = load_learning(daf)
        for s in doc.get("sugyot", []):
            s.pop("concepts", None)
        save_learning(daf, doc)
    rebuild_yoma()
    commit("purge concepts corpus-wide, migration prerequisites still unmet")
    r = wp("manifest", "--type", "audited-sugya-enrichment-repair", "--module", "yoma",
          "--range", prereq_daf, "--audit-record-id", prereq_id)
    check("13b. still FAILS after the purge while the declared migration prerequisite "
         "remains unmet for this sugya",
          r.returncode != 0 and "migration prerequisite" in out(r)
          and "is not yet satisfied" in out(r) and prereq_id in out(r), out(r))

    os.chdir(FIXTURE)
    if "worker_pipeline" in sys.modules:
        del sys.modules["worker_pipeline"]
    wpm3 = _importlib.import_module("worker_pipeline")
    wpm3.REPO = FIXTURE
    wpm3.set_active_module(wpm3.resolve_active_module("yoma"))
    post_purge_errs = wpm3.audit_repair_prerequisite_errors([prereq_id])
    check("13b2. the production preflight function ALSO fails once the purge landed but "
         "this sugya's own migration prerequisite remains unmet",
          not any("legacy concepts purge" in e for e in post_purge_errs)
          and any("migration prerequisite" in e and "is not yet satisfied" in e
                  for e in post_purge_errs), post_purge_errs)
    os.chdir(str(ROOT))

    # ---- 13c. succeeds once the corpus-wide purge AND this sugya's
    #           declared migration prerequisites are both satisfied --------
    doc = load_learning(prereq_daf)
    sug = next(s for s in doc["sugyot"] if s["id"] == prereq_id)
    sug["requiresUnderstanding"] = []  # clears requiresUnderstanding_prose for this sugya
    if isinstance(sug.get("visualizableElements"), list):
        for el in sug["visualizableElements"]:
            if isinstance(el, dict) and "name" in el:
                el["item"] = el.pop("name")
    save_learning(prereq_daf, doc)
    rebuild_yoma()
    commit("fix this sugya's declared migration prerequisites")
    r = wp("manifest", "--type", "audited-sugya-enrichment-repair", "--module", "yoma",
          "--range", prereq_daf, "--audit-record-id", prereq_id, "--out", ".worker-manifest.json")
    check("13c. manifest generation SUCCEEDS once the global purge is complete AND this "
         "sugya's own migration prerequisites are satisfied", r.returncode == 0, out(r))
    r2 = wp("preflight", "--manifest", ".worker-manifest.json", "--dry-run")
    check("13c2. preflight ALSO succeeds under the same conditions", r2.returncode == 0, out(r2))

    # ---- 13d. unrelated ordinary debt elsewhere in the corpus never blocks
    #           an otherwise-satisfied prerequisite check (this ran against
    #           the FULL corpus, which still carries plenty of undressed
    #           semantic debt on every other sugya) ------------------------
    check("13d. an otherwise-satisfied prerequisite check is not blocked by unrelated "
         "ordinary debt elsewhere in the corpus", r.returncode == 0 and r2.returncode == 0)

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
    # 28-30. PROGRESS SCOPE IS RECORD-SPECIFIC: only manifest.auditRecordIds
    #        may have progress changes; an unrelated record advancing in the
    #        same PR fails; BLOCKED/review-bearing field requirements.
    # =========================================================================
    other_id = next(r["sugyaId"] for r in queue["records"] if r["sugyaId"] != real_id)

    # ---- 28. an unrelated record advanced in the same PR FAILS -----------
    reset_to_base()
    prog = json.loads(prog_path.read_text())
    prog["progress"][other_id]["status"] = "IN_PROGRESS"
    prog_path.write_text(json.dumps(prog, ensure_ascii=False, indent=1) + "\n")
    commit("advance an UNRELATED (not-named) record to IN_PROGRESS")
    r = run([sys.executable, "scripts/generate_enrichment_repair_queue.py", "--check",
            "--base", BASE_SHA, "--allowed-ids", real_id], cwd=FIXTURE)
    check("28. advancing a record NOT in --allowed-ids FAILS --check",
          r.returncode != 0 and "not in manifest.auditRecordIds" in out(r)
          and other_id in out(r), out(r))

    # ---- 28b. the SAME advance, with the correct allowed id named, passes
    reset_to_base()
    prog = json.loads(prog_path.read_text())
    prog["progress"][real_id]["status"] = "IN_PROGRESS"
    prog_path.write_text(json.dumps(prog, ensure_ascii=False, indent=1) + "\n")
    commit("advance the NAMED record to IN_PROGRESS")
    r = run([sys.executable, "scripts/generate_enrichment_repair_queue.py", "--check",
            "--base", BASE_SHA, "--allowed-ids", real_id], cwd=FIXTURE)
    check("28b. advancing the record actually named in --allowed-ids passes --check",
          r.returncode == 0, out(r))

    # ---- 29. BLOCKED requires a non-empty blockerReason -------------------
    reset_to_base()
    prog = json.loads(prog_path.read_text())
    prog["progress"][real_id]["status"] = "BLOCKED"  # no blockerReason set
    prog_path.write_text(json.dumps(prog, ensure_ascii=False, indent=1) + "\n")
    commit("BLOCKED with no blockerReason")
    r = run([sys.executable, "scripts/generate_enrichment_repair_queue.py", "--check",
            "--base", BASE_SHA], cwd=FIXTURE)
    check("29. BLOCKED with no blockerReason FAILS --check",
          r.returncode != 0 and "requires a non-empty blockerReason" in out(r), out(r))

    reset_to_base()
    prog = json.loads(prog_path.read_text())
    prog["progress"][real_id]["status"] = "BLOCKED"
    prog["progress"][real_id]["blockerReason"] = "Waiting on a source-text clarification."
    prog_path.write_text(json.dumps(prog, ensure_ascii=False, indent=1) + "\n")
    commit("BLOCKED with a real blockerReason")
    r = run([sys.executable, "scripts/generate_enrichment_repair_queue.py", "--check",
            "--base", BASE_SHA], cwd=FIXTURE)
    check("29b. BLOCKED with a non-empty blockerReason passes --check",
          r.returncode == 0, out(r))

    # ---- 30. a review-bearing status (APPROVED_PENDING_MERGE) requires
    #          reviewer AND independentReviewResult -------------------------
    reset_to_base()
    prog = json.loads(prog_path.read_text())
    prog["progress"][real_id]["status"] = "IN_PROGRESS"
    prog_path.write_text(json.dumps(prog, ensure_ascii=False, indent=1) + "\n")
    commit("step 1: IN_PROGRESS")
    prog["progress"][real_id]["status"] = "FIXED_PENDING_REVIEW"
    prog_path.write_text(json.dumps(prog, ensure_ascii=False, indent=1) + "\n")
    commit("step 2: FIXED_PENDING_REVIEW")
    prog["progress"][real_id]["status"] = "APPROVED_PENDING_MERGE"  # no reviewer/result set
    prog_path.write_text(json.dumps(prog, ensure_ascii=False, indent=1) + "\n")
    commit("step 3: APPROVED_PENDING_MERGE with no reviewer/independentReviewResult")
    r = run([sys.executable, "scripts/generate_enrichment_repair_queue.py", "--check",
            "--base", BASE_SHA], cwd=FIXTURE)
    check("30. APPROVED_PENDING_MERGE with no reviewer/independentReviewResult FAILS --check",
          r.returncode != 0 and "requires a non-empty reviewer" in out(r)
          and "requires a non-empty independentReviewResult" in out(r), out(r))

    prog["progress"][real_id]["reviewer"] = "second-reviewer"
    prog["progress"][real_id]["independentReviewResult"] = "APPROVED"
    prog_path.write_text(json.dumps(prog, ensure_ascii=False, indent=1) + "\n")
    commit("step 3b: APPROVED_PENDING_MERGE with reviewer and independentReviewResult set")
    r = run([sys.executable, "scripts/generate_enrichment_repair_queue.py", "--check",
            "--base", BASE_SHA], cwd=FIXTURE)
    check("30b. APPROVED_PENDING_MERGE with reviewer and independentReviewResult set "
         "passes --check", r.returncode == 0, out(r))

    # ---- 30c. an unknown progress field is rejected ------------------------
    reset_to_base()
    prog = json.loads(prog_path.read_text())
    prog["progress"][real_id]["totallyUnknownField"] = "smuggled metadata"
    prog_path.write_text(json.dumps(prog, ensure_ascii=False, indent=1) + "\n")
    commit("add an unknown progress field")
    r = run([sys.executable, "scripts/generate_enrichment_repair_queue.py", "--check",
            "--base", BASE_SHA], cwd=FIXTURE)
    check("30c. an unknown progress field FAILS --check",
          r.returncode != 0 and "unknown field" in out(r), out(r))

    # =========================================================================
    # 31. THE ONE-PR REPAIR LIFECYCLE IS EXECUTABLE: a single branch walks
    #     NOT_STARTED -> IN_PROGRESS -> FIXED_PENDING_REVIEW ->
    #     APPROVED_PENDING_MERGE across several commits (never violating the
    #     endpoint-looks-like-a-skip trap), and post-merge COMPLETE is
    #     DERIVED from squash-merge evidence -- no second repair PR, no
    #     progress-only PR.
    # =========================================================================
    PREREQ_BASE_31 = reset_to_prereqs_satisfied([real_id])
    # commit 1: the manifest that durably names this record's repair, plus
    # the actual content repair (the real edit this record authorizes),
    # plus advancing progress to IN_PROGRESS. The manifest is generated
    # through the real CLI (wp), exactly as a genuine repair PR would, and
    # lands inside the squashed commit below -- derive_effective_status now
    # requires it to bind COMPLETE to this specific record.
    r = wp("manifest", "--type", "audited-sugya-enrichment-repair", "--module", "yoma",
          "--range", real_daf, "--audit-record-id", real_id, "--out", ".worker-manifest.json")
    check("(setup) manifest for the one-PR lifecycle squash test generates successfully",
          r.returncode == 0, out(r))
    doc = load_learning(real_daf)
    sug = next(s for s in doc["sugyot"] if s["id"] == real_id)
    if "finalRuling" in audit_rec["affectedFields"]:
        sug["finalRuling"] = "The repaired finalRuling, landed in the one content-repair PR."
    elif "display.hint" in audit_rec["affectedFields"]:
        sug["display"]["hint"] = "The repaired display.hint, landed in the one content-repair PR?"
    save_learning(real_daf, doc)
    rebuild_yoma()
    prog = json.loads(prog_path.read_text())
    prog["progress"][real_id]["status"] = "IN_PROGRESS"
    prog_path.write_text(json.dumps(prog, ensure_ascii=False, indent=1) + "\n")
    commit("one-PR lifecycle: manifest + content repair + IN_PROGRESS")
    # commit 2: FIXED_PENDING_REVIEW.
    prog["progress"][real_id]["status"] = "FIXED_PENDING_REVIEW"
    prog_path.write_text(json.dumps(prog, ensure_ascii=False, indent=1) + "\n")
    commit("one-PR lifecycle: FIXED_PENDING_REVIEW")
    # commit 3: independent approval.
    prog["progress"][real_id]["status"] = "APPROVED_PENDING_MERGE"
    prog["progress"][real_id]["reviewer"] = "independent-reviewer"
    prog["progress"][real_id]["independentReviewResult"] = "APPROVED"
    prog_path.write_text(json.dumps(prog, ensure_ascii=False, indent=1) + "\n")
    commit("one-PR lifecycle: independent approval (APPROVED_PENDING_MERGE)")

    r = run([sys.executable, "scripts/generate_enrichment_repair_queue.py", "--check",
            "--base", PREREQ_BASE_31, "--allowed-ids", real_id], cwd=FIXTURE)
    check("31a. the full NOT_STARTED -> IN_PROGRESS -> FIXED_PENDING_REVIEW -> "
         "APPROVED_PENDING_MERGE walk across 3 commits passes --check (the two-endpoint "
         "comparison alone would look like an illegal skip)",
          r.returncode == 0, out(r))

    # squash-merge simulation: the whole 3-commit branch lands as ONE commit,
    # exactly like a real GitHub squash merge to main. Cut from
    # PREREQ_BASE_31 (not the original BASE_SHA) so the simulated squash
    # commit's own diff is exactly THIS repair PR's content -- mirroring a
    # real repo where the corpus-wide migration prerequisites already
    # merged in an earlier, separate PR before this repair PR ever opened.
    git("checkout", "-q", "-B", "main-sim", PREREQ_BASE_31, cwd=FIXTURE)
    sq = git("merge", "--squash", "work", cwd=FIXTURE)
    check("(setup) squash-merge simulation applies cleanly", sq.returncode == 0, out(sq))
    commit("squash-merge: one-PR repair for %s" % real_id)
    squash_sha = git("rev-parse", "HEAD", cwd=FIXTURE).stdout.strip()

    import importlib
    sys.path.insert(0, str(FIXTURE / "scripts"))
    if "generate_enrichment_repair_queue" in sys.modules:
        del sys.modules["generate_enrichment_repair_queue"]
    os.chdir(FIXTURE)
    geq = importlib.import_module("generate_enrichment_repair_queue")
    stored_record = json.loads(prog_path.read_text())["progress"][real_id]
    check("(setup) the stored record is APPROVED_PENDING_MERGE, never hand-edited to COMPLETE",
          stored_record["status"] == "APPROVED_PENDING_MERGE", stored_record)
    effective, evidence = geq.derive_effective_status(real_id, stored_record,
                                                       squash_commit=squash_sha,
                                                       head_ref=squash_sha)
    check("31b. effective status is DERIVED as COMPLETE from squash-merge evidence -- "
         "ancestor of head, a matching .worker-manifest.json naming real_id in "
         "auditRecordIds for its own target daf, and that daf's *.learning.json actually "
         "touched -- with NO second edit to the progress file itself",
          effective == "COMPLETE" and evidence.get("derived") is True,
          (effective, evidence))
    check("31c. the derivation never mutated the stored record (still APPROVED_PENDING_MERGE "
         "on disk; completion is a read, not a write)",
          json.loads(prog_path.read_text())["progress"][real_id]["status"]
          == "APPROVED_PENDING_MERGE")

    # Without squash-merge evidence (no commit supplied), the stored status
    # is returned unchanged -- derivation never happens speculatively.
    effective_none, evidence_none = geq.derive_effective_status(real_id, stored_record)
    check("31d. with no squash commit supplied, the effective status is just the stored one "
         "(no speculative derivation)",
          effective_none == "APPROVED_PENDING_MERGE" and evidence_none.get("derived") is False)

    # =========================================================================
    # 31e-31g. derive_effective_status BINDS COMPLETE TO THE SPECIFIC RECORD --
    #          an ancestor commit that merely touches SOME *.learning.json
    #          file, for any reason, is never enough on its own. Each
    #          scenario below reuses `stored_record` (APPROVED_PENDING_MERGE,
    #          with a reviewer and independentReviewResult already set) so
    #          only the squash commit's own evidence varies between cases.
    # =========================================================================

    # ---- 31e. an UNRELATED squash commit -- a genuine, correctly-manifested
    #           repair for a DIFFERENT sugya on a DIFFERENT daf -- must NOT
    #           derive COMPLETE for real_id.
    diff_daf_rec = next(rr for rr in queue["records"] if rr["daf"] != real_daf)
    diff_daf_id, diff_daf_daf = diff_daf_rec["sugyaId"], diff_daf_rec["daf"]
    diff_daf_audit = next(a for a in audit_doc["records"] if a["sugyaId"] == diff_daf_id)

    os.chdir(str(ROOT))
    base_31e = reset_to_prereqs_satisfied([diff_daf_id])
    r = wp("manifest", "--type", "audited-sugya-enrichment-repair", "--module", "yoma",
          "--range", diff_daf_daf, "--audit-record-id", diff_daf_id,
          "--out", ".worker-manifest.json")
    check("(setup) manifest for the UNRELATED sugya's own repair generates successfully",
          r.returncode == 0, out(r))
    doc = load_learning(diff_daf_daf)
    sug_diff = next(s for s in doc["sugyot"] if s["id"] == diff_daf_id)
    if "finalRuling" in diff_daf_audit["affectedFields"]:
        sug_diff["finalRuling"] = "An unrelated repair, for a completely different sugya."
    elif "display.hint" in diff_daf_audit["affectedFields"]:
        sug_diff["display"]["hint"] = "An unrelated repair, for a completely different sugya?"
    save_learning(diff_daf_daf, doc)
    rebuild_yoma()
    commit("an entirely unrelated repair, for a different sugya on a different daf")
    git("checkout", "-q", "-B", "main-sim", base_31e, cwd=FIXTURE)
    sq = git("merge", "--squash", "work", cwd=FIXTURE)
    check("(setup) unrelated-repair squash-merge simulation applies cleanly",
          sq.returncode == 0, out(sq))
    commit("squash-merge: unrelated repair for %s" % diff_daf_id)
    unrelated_squash_sha = git("rev-parse", "HEAD", cwd=FIXTURE).stdout.strip()

    os.chdir(FIXTURE)
    if "generate_enrichment_repair_queue" in sys.modules:
        del sys.modules["generate_enrichment_repair_queue"]
    geq = importlib.import_module("generate_enrichment_repair_queue")
    eff_unrelated, ev_unrelated = geq.derive_effective_status(
        real_id, stored_record, squash_commit=unrelated_squash_sha, head_ref=unrelated_squash_sha)
    check("31e. an unrelated squash commit -- a genuine, correctly-manifested repair for a "
         "DIFFERENT sugya on a DIFFERENT daf -- does NOT derive COMPLETE for real_id",
          eff_unrelated != "COMPLETE" and ev_unrelated.get("derived") is False
          and ev_unrelated.get("sidInManifestAuditRecordIds") is False,
          (eff_unrelated, ev_unrelated))

    # ---- 31f. a squash commit whose manifest correctly targets real_id's
    #           OWN daf, and whose diff DOES touch that daf's learning.json,
    #           but whose auditRecordIds names a DIFFERENT sugya sharing
    #           that same daf -- isolates the auditRecordIds check from the
    #           touched-file check (the file check alone would pass here).
    same_daf_rec = next((rr for rr in queue["records"]
                        if rr["daf"] == real_daf and rr["sugyaId"] != real_id), None)
    check("(setup) a second queue record shares real_id's own daf (needed to isolate the "
         "auditRecordIds check from the touched-file check)", same_daf_rec is not None, real_daf)
    if same_daf_rec is not None:
        other_same_daf_id = same_daf_rec["sugyaId"]
        other_same_daf_audit = next(a for a in audit_doc["records"]
                                    if a["sugyaId"] == other_same_daf_id)

        os.chdir(str(ROOT))
        base_31f = reset_to_prereqs_satisfied([other_same_daf_id])
        r = wp("manifest", "--type", "audited-sugya-enrichment-repair", "--module", "yoma",
              "--range", real_daf, "--audit-record-id", other_same_daf_id,
              "--out", ".worker-manifest.json")
        check("(setup) manifest for the OTHER same-daf sugya's repair generates successfully",
              r.returncode == 0, out(r))
        doc = load_learning(real_daf)
        sug_other = next(s for s in doc["sugyot"] if s["id"] == other_same_daf_id)
        if "finalRuling" in other_same_daf_audit["affectedFields"]:
            sug_other["finalRuling"] = "A real repair, but for the OTHER sugya on this daf."
        elif "display.hint" in other_same_daf_audit["affectedFields"]:
            sug_other["display"]["hint"] = "A real repair, but for the OTHER sugya on this daf?"
        save_learning(real_daf, doc)
        rebuild_yoma()
        commit("a real repair for the OTHER sugya sharing real_id's own daf")
        git("checkout", "-q", "-B", "main-sim", base_31f, cwd=FIXTURE)
        sq = git("merge", "--squash", "work", cwd=FIXTURE)
        check("(setup) same-daf-other-sugya squash-merge simulation applies cleanly",
              sq.returncode == 0, out(sq))
        commit("squash-merge: repair for %s (not real_id)" % other_same_daf_id)
        same_daf_squash_sha = git("rev-parse", "HEAD", cwd=FIXTURE).stdout.strip()

        os.chdir(FIXTURE)
        if "generate_enrichment_repair_queue" in sys.modules:
            del sys.modules["generate_enrichment_repair_queue"]
        geq = importlib.import_module("generate_enrichment_repair_queue")
        eff_wrong_sid, ev_wrong_sid = geq.derive_effective_status(
            real_id, stored_record, squash_commit=same_daf_squash_sha,
            head_ref=same_daf_squash_sha)
        real_daf_learning_path = "modules/yoma/assets/learning/yoma/%s.learning.json" % real_daf
        check("31f. a squash commit whose manifest does not name real_id in auditRecordIds "
             "does NOT derive COMPLETE, even though it DID touch real_id's own daf's "
             "learning.json (the manifest instead names a different sugya on that same daf) -- "
             "the derivation fails at the auditRecordIds check, before it ever reaches the "
             "separate touched-file check, so the file's actually-touched status is confirmed "
             "directly off the raw touchedFiles evidence instead of the (never-computed) "
             "targetLearningFileTouched key",
              eff_wrong_sid != "COMPLETE" and ev_wrong_sid.get("derived") is False
              and ev_wrong_sid.get("sidInManifestAuditRecordIds") is False
              and real_daf_learning_path in ev_wrong_sid.get("touchedFiles", []),
              (eff_wrong_sid, ev_wrong_sid))

    # ---- 31g. a squash commit with the CORRECT manifest for real_id (right
    #           type, right sid in auditRecordIds, right target daf) but
    #           whose diff never actually touches that daf's learning.json
    #           (only an unrelated file changed) does NOT derive COMPLETE.
    os.chdir(str(ROOT))
    base_31g = reset_to_prereqs_satisfied([real_id])
    r = wp("manifest", "--type", "audited-sugya-enrichment-repair", "--module", "yoma",
          "--range", real_daf, "--audit-record-id", real_id, "--out", ".worker-manifest.json")
    check("(setup) manifest for the correct-manifest-wrong-file test generates successfully",
          r.returncode == 0, out(r))
    scratch = FIXTURE / "docs/reports/data/_test_unrelated_touch.txt"
    scratch.write_text("unrelated change; never touches the target daf's learning.json\n")
    commit("correct manifest, but the diff never touches the target daf's learning.json")
    git("checkout", "-q", "-B", "main-sim", base_31g, cwd=FIXTURE)
    sq = git("merge", "--squash", "work", cwd=FIXTURE)
    check("(setup) correct-manifest-wrong-file squash-merge simulation applies cleanly",
          sq.returncode == 0, out(sq))
    commit("squash-merge: correct manifest, wrong (missing) file touch")
    wrong_file_squash_sha = git("rev-parse", "HEAD", cwd=FIXTURE).stdout.strip()

    os.chdir(FIXTURE)
    if "generate_enrichment_repair_queue" in sys.modules:
        del sys.modules["generate_enrichment_repair_queue"]
    geq = importlib.import_module("generate_enrichment_repair_queue")
    eff_wrong_file, ev_wrong_file = geq.derive_effective_status(
        real_id, stored_record, squash_commit=wrong_file_squash_sha,
        head_ref=wrong_file_squash_sha)
    check("31g. a squash commit with the CORRECT manifest (right type, right sid, right "
         "target daf) but whose diff never actually touches that daf's learning.json does "
         "NOT derive COMPLETE",
          eff_wrong_file != "COMPLETE" and ev_wrong_file.get("derived") is False
          and ev_wrong_file.get("sidInManifestAuditRecordIds") is True
          and ev_wrong_file.get("targetLearningFileTouched") is False,
          (eff_wrong_file, ev_wrong_file))

    os.chdir(str(ROOT))

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

    # =========================================================================
    # 20-24. RECORD-SPECIFIC AUDIT SCOPE: a named audit record binds to the
    #        exact sugya id at its exact array index, never to "any sugya
    #        that happens to share a field name with a named record".
    # =========================================================================

    # ---- 20. a named 82b record cannot authorize a change on the OTHER
    #          82b sugya (there are two named audit records on 82b, both
    #          affecting finalRuling; naming only s01 must never authorize
    #          a finalRuling edit on s02). --------------------------------
    PREREQ_BASE_20 = reset_to_prereqs_satisfied(["yoma-082b-s01", "yoma-082b-s02"])
    wp("manifest", "--type", "audited-sugya-enrichment-repair", "--module", "yoma",
      "--range", "82b", "--audit-record-id", "yoma-082b-s01", "--out", ".worker-manifest.json")
    doc = load_learning("82b")
    ids_82b = [s["id"] for s in doc["sugyot"]]
    check("(setup) 82b carries both yoma-082b-s01 and yoma-082b-s02",
          "yoma-082b-s01" in ids_82b and "yoma-082b-s02" in ids_82b, ids_82b)
    sug_s02 = next(s for s in doc["sugyot"] if s["id"] == "yoma-082b-s02")
    sug_s02["finalRuling"] = "A finalRuling edit smuggled in under the s01 audit record."
    save_learning("82b", doc)
    rebuild_yoma()
    commit("attempt: edit s02.finalRuling while only s01 is named")
    r = wp("scope", "--manifest", ".worker-manifest.json", "--base", PREREQ_BASE_20)
    check("20. a named 82b record (s01) cannot authorize a finalRuling edit on the "
         "OTHER (unnamed) 82b sugya (s02)",
          r.returncode != 0 and "yoma-082b-s02" in out(r)
          and "not named in manifest.auditRecordIds" in out(r), out(r))

    # ---- 21. same-daf, same-field edit on an UNNAMED record fails (a
    #          restatement of 20 at a different field, direct wording match
    #          with the requirement). ------------------------------------
    check("21. same-daf same-field edit on an unnamed record fails "
         "(identical scenario to 20)", r.returncode != 0, out(r))

    # ---- 22. two named records retain SEPARATE affected-field scopes:
    #          naming BOTH s01 and s02 must not union their affectedFields --
    #          learning.ahaMoment is affected for s01 but NOT for s02, so
    #          editing it on s02 must still fail even though s02 is named. --
    PREREQ_BASE_22 = reset_to_prereqs_satisfied(["yoma-082b-s01", "yoma-082b-s02"])
    audit_doc2 = json.loads((FIXTURE / "docs/reports/data/yoma-tail-enrichment-audit.json").read_text())
    aud_s01 = next(r for r in audit_doc2["records"] if r["sugyaId"] == "yoma-082b-s01")
    aud_s02 = next(r for r in audit_doc2["records"] if r["sugyaId"] == "yoma-082b-s02")
    check("(setup) learning.ahaMoment affects s01 but not s02",
          "learning.ahaMoment" in aud_s01["affectedFields"]
          and "learning.ahaMoment" not in aud_s02["affectedFields"],
          (aud_s01["affectedFields"], aud_s02["affectedFields"]))
    wp("manifest", "--type", "audited-sugya-enrichment-repair", "--module", "yoma",
      "--range", "82b", "--audit-record-id", "yoma-082b-s01",
      "--audit-record-id", "yoma-082b-s02", "--out", ".worker-manifest.json")
    doc = load_learning("82b")
    sug_s02b = next(s for s in doc["sugyot"] if s["id"] == "yoma-082b-s02")
    sug_s02b.setdefault("learning", {})["ahaMoment"] = "Borrowed from s01's affectedFields scope."
    save_learning("82b", doc)
    rebuild_yoma()
    commit("attempt: edit s02.learning.ahaMoment while both s01 and s02 are named")
    r = wp("scope", "--manifest", ".worker-manifest.json", "--base", PREREQ_BASE_22)
    check("22. naming two records does NOT union their affectedFields: s01's "
         "learning.ahaMoment scope cannot authorize the same field on s02",
          r.returncode != 0 and "yoma-082b-s02" in out(r)
          and "exact named audit record" in out(r), out(r))

    # ---- 22b. the SAME field, edited on the record that actually owns it,
    #           still passes (proves 22 is a real scope failure, not a
    #           blanket rejection of every learning.* edit). ---------------
    PREREQ_BASE_22B = reset_to_prereqs_satisfied(["yoma-082b-s01", "yoma-082b-s02"])
    wp("manifest", "--type", "audited-sugya-enrichment-repair", "--module", "yoma",
      "--range", "82b", "--audit-record-id", "yoma-082b-s01",
      "--audit-record-id", "yoma-082b-s02", "--out", ".worker-manifest.json")
    doc = load_learning("82b")
    sug_s01b = next(s for s in doc["sugyot"] if s["id"] == "yoma-082b-s01")
    sug_s01b.setdefault("learning", {})["ahaMoment"] = "Correctly scoped to the record that owns it."
    save_learning("82b", doc)
    rebuild_yoma()
    commit("edit s01.learning.ahaMoment (the record that actually owns it)")
    r = wp("scope", "--manifest", ".worker-manifest.json", "--base", PREREQ_BASE_22B)
    check("22b. editing learning.ahaMoment on the RECORD that owns it passes scope",
          r.returncode == 0, out(r))

    # ---- 23. changing a sugya's ID while editing enrichment fails --------
    PREREQ_BASE_23 = reset_to_prereqs_satisfied(["yoma-082b-s01"])
    wp("manifest", "--type", "audited-sugya-enrichment-repair", "--module", "yoma",
      "--range", "82b", "--audit-record-id", "yoma-082b-s01", "--out", ".worker-manifest.json")
    doc = load_learning("82b")
    sug_id_change = next(s for s in doc["sugyot"] if s["id"] == "yoma-082b-s01")
    sug_id_change["id"] = "yoma-082b-s01-renamed"
    sug_id_change["finalRuling"] = "Renamed the sugya id while also editing finalRuling."
    save_learning("82b", doc)
    commit("attempt: change sugya id at index 0 while editing enrichment")
    r = wp("scope", "--manifest", ".worker-manifest.json", "--base", PREREQ_BASE_23)
    check("23. changing a sugya id while editing enrichment FAILS scope",
          r.returncode != 0 and "sugya id at index" in out(r) and "changed" in out(r), out(r))

    # ---- 24. a duplicate auditRecordId fails manifest generation ---------
    reset_to_base()
    r = wp("manifest", "--type", "audited-sugya-enrichment-repair", "--module", "yoma",
          "--range", "82b", "--audit-record-id", "yoma-082b-s01",
          "--audit-record-id", "yoma-082b-s01")
    check("24. a duplicate auditRecordId FAILS manifest generation",
          r.returncode != 0 and "duplicate auditRecordIds" in out(r), out(r))

    # =========================================================================
    # 25-27. <daf>.summary NORMALIZATION: the literal template string, not a
    #        per-daf-substituted value, and daf-scoped (not sugya-indexed)
    #        authorization.
    # =========================================================================
    sys.path.insert(0, str(FIXTURE / "scripts"))
    if "worker_pipeline" in sys.modules:
        del sys.modules["worker_pipeline"]
    os.chdir(FIXTURE)
    wpm2 = importlib.import_module("worker_pipeline")
    check("25. normalize_audit_pointer('/summary', daf) returns the LITERAL "
         "template '<daf>.summary', not a per-daf-substituted value",
          wpm2.normalize_audit_pointer("/summary", "82b") == "<daf>.summary"
          and wpm2.normalize_audit_pointer("/summary", "77a") == "<daf>.summary")
    os.chdir(str(ROOT))

    # ---- 26. a summary change passes when the named audit record lists
    #          '<daf>.summary' (yoma-077a-s01 does). ------------------------
    PREREQ_BASE_26 = reset_to_prereqs_satisfied(["yoma-077a-s01"])
    wp("manifest", "--type", "audited-sugya-enrichment-repair", "--module", "yoma",
      "--range", "77a", "--audit-record-id", "yoma-077a-s01", "--out", ".worker-manifest.json")
    doc = load_learning("77a")
    doc["summary"] = "A rewritten daf summary authorized by yoma-077a-s01's <daf>.summary scope."
    save_learning("77a", doc)
    commit("edit summary, authorized by a named record that lists <daf>.summary")
    r = wp("scope", "--manifest", ".worker-manifest.json", "--base", PREREQ_BASE_26)
    check("26. a summary change PASSES when the named record lists <daf>.summary",
          r.returncode == 0, out(r))

    # ---- 27. a summary change fails when NO named record lists it
    #          (yoma-077a-s02 does not carry '<daf>.summary'). --------------
    PREREQ_BASE_27 = reset_to_prereqs_satisfied(["yoma-077a-s02"])
    wp("manifest", "--type", "audited-sugya-enrichment-repair", "--module", "yoma",
      "--range", "77a", "--audit-record-id", "yoma-077a-s02", "--out", ".worker-manifest.json")
    doc = load_learning("77a")
    doc["summary"] = "An unauthorized daf summary edit."
    save_learning("77a", doc)
    commit("edit summary while the only named record does not list <daf>.summary")
    r = wp("scope", "--manifest", ".worker-manifest.json", "--base", PREREQ_BASE_27)
    check("27. a summary change FAILS when no named record lists <daf>.summary",
          r.returncode != 0 and "<daf>.summary" in out(r), out(r))

    os.chdir(str(ROOT))

    # =========================================================================
    # 28-31. THE CRITICAL MERGE-BASE-RATCHET REGRESSION TEST. This is the test
    # that justifies the whole enrichment-regression-vs-merge-base gate: a
    # genuine, already-merged improvement to a REAL baselined-invalid value
    # must never be silently regressed by a later, unrelated PR -- even
    # though the frozen historical baseline ALONE would still accept the
    # regression, because that baseline enumerates ORIGINAL legacy debt and
    # is never rewritten by ordinary repairs, so a value inside its envelope
    # compares clean forever no matter what happened on main in between.
    #
    # Step 1: pick a sugya whose display.hint is CURRENTLY invalid in the
    #         REAL frozen baseline (scripts/baselines/yoma_enrichment_
    #         contract_debt.json) -- not an invented synthetic value, a value
    #         the frozen baseline already carries, confirmed by fingerprint.
    # Step 2: commit a legitimate improvement turning it into a
    #         contract-valid question. This is the simulated new main /
    #         merge-base (BASE_A_SHA).
    # Step 3: from BASE_A_SHA, a later PR-like commit (a display-only-edit
    #         manifest) changes the hint back to the EXACT ORIGINAL invalid
    #         value.
    # Step 4: prove all four sub-proofs from the task spec.
    # =========================================================================
    reset_to_base()
    sys.path.insert(0, str(ROOT / "scripts"))
    if "validate_enrichment_contracts" in sys.modules:
        del sys.modules["validate_enrichment_contracts"]
    import validate_enrichment_contracts as VEC

    daf_28, sid_28 = "7b", "yoma-007b-s01"
    doc28 = load_learning(daf_28)
    sug28 = next(s for s in doc28["sugyot"] if s["id"] == sid_28)
    ORIGINAL_INVALID_HINT = sug28["display"]["hint"]
    fp28 = VEC.fingerprint_occurrence("hint_not_a_question", sid_28, "display.hint",
                                      ORIGINAL_INVALID_HINT)
    real_baseline = json.loads(
        (ROOT / "scripts/baselines/yoma_enrichment_contract_debt.json").read_text())
    real_fps_28 = {o["fingerprint"] for o in real_baseline["occurrences"].get("hint_not_a_question", [])
                  if o["sugyaId"] == sid_28}
    check("28. picked a REAL baselined-invalid value: its fingerprint matches the "
         "frozen baseline's own occurrence for this sugya (not an invented value)",
          fp28 in real_fps_28, (fp28, sorted(real_fps_28)))

    # ---- 29. Base A: a legitimate improvement PR merges, turning the
    #          invalid hint into a contract-valid question. Simulated new
    #          main / merge-base. -------------------------------------------
    IMPROVED_HINT = ("Why does R. Yehuda's proof from the YK kohein gadol backfire "
                     "on R. Shimon's view?")
    sug28["display"]["hint"] = IMPROVED_HINT
    save_learning(daf_28, doc28)
    rebuild_yoma()
    commit("29. simulated improvement: fix yoma-007b-s01 display.hint (fixture only)")
    BASE_A_SHA = git("rev-parse", "HEAD", cwd=FIXTURE).stdout.strip()

    r29 = run([sys.executable, "scripts/validate_enrichment_contracts.py", "--module", "yoma"],
             cwd=FIXTURE)
    check("29. the improvement itself is contract-clean (frozen baseline holds)",
          r29.returncode == 0, out(r29))

    # ---- 30. Later PR: from Base A, revert the hint back to the EXACT
    #          original invalid value -- a display-only-edit manifest is the
    #          realistic vehicle for this kind of change. --------------------
    git("checkout", "-q", "-b", "later-pr-28", BASE_A_SHA, cwd=FIXTURE)
    wp("manifest", "--type", "display-only-edit", "--module", "yoma", "--range", daf_28,
      "--out", ".worker-manifest.json")
    doc30 = load_learning(daf_28)
    sug30 = next(s for s in doc30["sugyot"] if s["id"] == sid_28)
    sug30["display"]["hint"] = ORIGINAL_INVALID_HINT
    save_learning(daf_28, doc30)
    rebuild_yoma()
    commit("30. simulated regression: reintroduce the exact original invalid "
          "hint (fixture only)")

    # ---- 30a. Sub-proof 1: ordinary frozen-baseline comparison ALONE (no
    #           --compare-ref) ACCEPTS the restored old value -- demonstrates
    #           the gap being fixed actually existed. ------------------------
    r30a = run([sys.executable, "scripts/validate_enrichment_contracts.py", "--module", "yoma"],
              cwd=FIXTURE)
    check("30a. frozen-baseline-only comparison ALONE ACCEPTS the reintroduced "
         "old value (the gap this PR closes)",
          r30a.returncode == 0, out(r30a))

    # ---- 30b. Sub-proof 2: the new --compare-ref <merge-base> comparison
    #           REJECTS it. ---------------------------------------------------
    r30b = run([sys.executable, "scripts/validate_enrichment_contracts.py", "--module", "yoma",
               "--compare-ref", BASE_A_SHA], cwd=FIXTURE)
    check("30b. --compare-ref <merge-base> REJECTS the reintroduced old value",
          r30b.returncode != 0 and "hint_not_a_question" in out(r30b) and sid_28 in out(r30b)
          and "MERGE-BASE MONOTONIC RATCHET" in out(r30b), out(r30b))

    # ---- 30c. Sub-proof 3: `worker_pipeline.py verify` (with the new gate
    #           wired in) REJECTS it. -----------------------------------------
    r30c = wp("verify", "--manifest", ".worker-manifest.json", "--base", BASE_A_SHA)
    check("30c. worker_pipeline.py verify REJECTS the reintroduced old value "
         "(enrichment-regression-vs-merge-base gate fires)",
          r30c.returncode != 0 and "enrichment-regression-vs-merge-base" in out(r30c)
          and "FAIL  enrichment-regression-vs-merge-base" in out(r30c), out(r30c))

    # ---- 30d. Sub-proof 4: `worker_pipeline.py ci-check` REJECTS it. --------
    r30d = wp("ci-check", "--base", BASE_A_SHA)
    check("30d. worker_pipeline.py ci-check REJECTS the reintroduced old value "
         "(enrichment-regression-vs-merge-base enforced in CI)",
          r30d.returncode != 0 and "enrichment-regression-vs-merge-base" in out(r30d), out(r30d))

    # ---- 31. Sanity: the SAME manifest/base, but with the hint left at the
    #          improved value (no regression), passes verify cleanly -- proves
    #          30c/30d fail for the right reason (the reintroduced value),
    #          not for some unrelated fixture artifact. ----------------------
    git("checkout", "-q", "-b", "later-pr-clean-31", BASE_A_SHA, cwd=FIXTURE)
    wp("manifest", "--type", "display-only-edit", "--module", "yoma", "--range", daf_28,
      "--out", ".worker-manifest.json")
    doc31 = load_learning(daf_28)
    sug31 = next(s for s in doc31["sugyot"] if s["id"] == sid_28)
    sug31["display"]["title"] = sug31["display"]["title"] + " (unrelated copy touch-up)"
    save_learning(daf_28, doc31)
    rebuild_yoma()
    commit("31. unrelated display-only-edit that does not touch the fixed hint")
    r31 = run([sys.executable, "scripts/validate_enrichment_contracts.py", "--module", "yoma",
              "--compare-ref", BASE_A_SHA], cwd=FIXTURE)
    check("31. --compare-ref PASSES for an unrelated change that leaves the fix intact",
          r31.returncode == 0, out(r31))

    os.chdir(str(ROOT))

finally:
    if FIXTURE and FIXTURE.exists():
        shutil.rmtree(FIXTURE.parent, ignore_errors=True)
    print("\nfixture repository cleaned up.")

if FAILED:
    print("\n%d integration check(s) failed: %s" % (len(FAILED), FAILED))
    sys.exit(1)
print("\nAll worker-pipeline integration checks passed.")
