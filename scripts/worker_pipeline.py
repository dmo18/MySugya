#!/usr/bin/env python3
"""
worker_pipeline.py - project-wide bounded-worker task pipeline.

One driver, six subcommands, all fed by scripts/worker_task_types.json:

  manifest   emit a machine-readable task manifest (stdout or --out FILE)
  preflight  environment + target safety checks for a manifest
  packet     task-type-specific work packet (context source of truth)
  prompt     compact worker prompt for the task
  verify     post-edit verification (--fast / --full)
  scope      general PR scope validation for the manifest's task type
  ci-check   CI enforcement: content PRs must carry a valid manifest

Usage examples:
  python3 scripts/worker_pipeline.py manifest --type rashi-repair --module yoma --range 61a
  python3 scripts/worker_pipeline.py manifest --type docs-tooling --out .worker-manifest.json
  python3 scripts/worker_pipeline.py preflight --manifest .worker-manifest.json [--dry-run]
  python3 scripts/worker_pipeline.py packet --manifest .worker-manifest.json
  python3 scripts/worker_pipeline.py prompt --manifest .worker-manifest.json
  python3 scripts/worker_pipeline.py verify --manifest .worker-manifest.json --fast|--full
  python3 scripts/worker_pipeline.py scope --manifest .worker-manifest.json [--base REF]
  python3 scripts/worker_pipeline.py ci-check --base origin/main

Rashi task types delegate to the existing, proven Rashi tooling
(rashi_preflight/make_rashi_work_packet/rashi_verify/check_rashi_pr_scope)
so nothing is duplicated or weakened. Offline except local git.
"""
import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
REGISTRY = Path(__file__).parent / "worker_task_types.json"
YSCRIPTS = REPO / "modules" / "yoma" / "scripts"
YROOT = REPO / "modules" / "yoma"
MANIFEST_DEFAULT = REPO / ".worker-manifest.json"

RASHI_TYPES = {"rashi-repair", "rashi-reconstruction", "placeholder-backfill"}
CONTENT_PREFIXES = ("modules/yoma/assets/learning/", "modules/yoma/assets/literal_en/",
                    "modules/yoma/assets/talmuddev/", "modules/yoma/assets/daftexts/")


def sh(args, cwd=REPO, env=None):
    e = dict(os.environ, **(env or {}))
    return subprocess.run(args, capture_output=True, text=True, cwd=cwd, env=e)


def load_registry():
    return json.loads(REGISTRY.read_text())["taskTypes"]


def load_manifest(path):
    m = json.loads(Path(path).read_text())
    types = load_registry()
    if m.get("type") not in types:
        sys.exit(f"ERROR: manifest type {m.get('type')!r} not in registry")
    return m, types[m["type"]]


def expand_range(spec):
    if not spec:
        return []
    m = re.match(r"^(\d+[ab])(?:-(\d+[ab]))?$", spec)
    if not m:
        sys.exit(f"ERROR: malformed range {spec!r}")
    if not m.group(2):
        return [m.group(1)]
    def key(d):
        mm = re.match(r"(\d+)([ab])", d)
        return (int(mm.group(1)), mm.group(2))
    td = YROOT / "assets" / "talmuddev"
    all_daf = sorted((p.name.replace(".json", "") for p in td.glob("*.json")), key=key)
    lo, hi = key(m.group(1)), key(m.group(2))
    out = [d for d in all_daf if lo <= key(d) <= hi]
    if not out:
        sys.exit(f"ERROR: range {spec!r} matches no daf")
    return out


def file_allowed(path, spec, targets):
    """A changed file is in scope only if it matches the allowed set.
    The forbiddenFiles list is documentation for prompts; enforcement is
    allowlist-style (anything not explicitly allowed is a violation)."""
    for pat in spec.get("allowedFiles", []):
        if "<daf>" in pat:
            if any(fnmatch.fnmatch(path, pat.replace("<daf>", d)) for d in targets):
                return True
            continue
        if fnmatch.fnmatch(path, pat) or (pat.endswith("/*") and path.startswith(pat[:-1])):
            return True
    return False


def pattern_to_regex(pat):
    """'sugyot[*].learning.takeaway.text' -> compiled regex matching the
    JSON pointer '/sugyot/<n>/learning/takeaway/text' and anything below it."""
    body = "/".join(seg.replace("[*]", "/\\d+") for seg in pat.split("."))
    return re.compile("^/" + body + "(/.*)?$")


def json_leaf_diff(old, new, ptr, leaves, structure):
    """Collect changed-leaf JSON pointers and array structure changes."""
    if isinstance(old, dict) and isinstance(new, dict):
        for k in sorted(set(old) | set(new)):
            if k not in old or k not in new:
                leaves.append(f"{ptr}/{k}")
            else:
                json_leaf_diff(old[k], new[k], f"{ptr}/{k}", leaves, structure)
    elif isinstance(old, list) and isinstance(new, list):
        if len(old) != len(new):
            structure.append(f"{ptr} array length {len(old)} -> {len(new)}")
            return
        for i, (a, b) in enumerate(zip(old, new)):
            json_leaf_diff(a, b, f"{ptr}/{i}", leaves, structure)
    else:
        if old != new:
            leaves.append(ptr)


def json_scope_check(mb, changed, m, spec, errors):
    """Generic per-task JSON scope engine, driven by the registry's
    jsonScope: {mutable: [path patterns], flagMutable: {flag: [patterns]},
    structureFlag}. Reports exact JSON-pointer violations. Array entry
    add/remove/reorder surfaces as a structure error unless the manifest
    carries the structure flag."""
    scope = spec.get("jsonScope")
    if not scope:
        return
    flags = set(m.get("authorizations", []))
    allowed_rx = [pattern_to_regex(p) for p in scope.get("mutable", [])]
    for flag, pats in scope.get("flagMutable", {}).items():
        if flag in flags:
            allowed_rx += [pattern_to_regex(p) for p in pats]
    structure_ok = scope.get("structureFlag") and scope["structureFlag"] in flags
    targets = set(m.get("targets", []))

    for p in changed:
        if not (p.startswith("modules/yoma/assets/learning/") and p.endswith(".learning.json")):
            continue
        daf = p.split("/")[-1].replace(".learning.json", "")
        if daf not in targets:
            errors.append(f"{p}: daf {daf} is not in the manifest targets {sorted(targets)} (no cross-daf edits)")
            continue
        r = sh(["git", "show", f"{mb}:{p}"])
        if r.returncode != 0:
            errors.append(f"{p}: does not exist at base; new files require structure authorization")
            continue
        old, new = json.loads(r.stdout), json.loads((REPO / p).read_text())
        leaves, structure = [], []
        json_leaf_diff(old, new, "", leaves, structure)
        for s in structure:
            ptr = s.split(" array length")[0]
            # A structure change entirely under an authorized mutable path
            # (e.g. growing a flag-authorized container array) is permitted;
            # anything else needs the explicit structure flag.
            if any(rx.match(ptr) for rx in allowed_rx):
                continue
            if not structure_ok:
                errors.append(f"{p}: {s} (requires --authorize {scope.get('structureFlag', 'allowStructure')})")
        for ptr in leaves:
            if not any(rx.match(ptr) for rx in allowed_rx):
                errors.append(f"{p}: {ptr} changed (outside the {m['type']} mutable path set)")


def allowlist_ratchet_inline(mb, policy, errors):
    """Remove-only allowlist enforcement for non-Rashi task types."""
    if policy == "restructure-with-env" and os.environ.get("RASHI_ALLOWLIST_RESTRUCTURE") == "1":
        return
    for p in sorted((YSCRIPTS / "allowlists").glob("*.json")):
        rel = p.relative_to(REPO).as_posix()
        r = sh(["git", "show", f"{mb}:{rel}"])
        old = json.loads(r.stdout) if r.returncode == 0 else {}
        new = json.loads(p.read_text())
        for section in ("entries", "count_mismatches"):
            oe = {json.dumps(e, sort_keys=True) for e in old.get(section, [])}
            ne = {json.dumps(e, sort_keys=True) for e in new.get(section, [])}
            for a in sorted(ne - oe):
                errors.append(f"{rel}: {section} entry ADDED (policy {policy}): {a}")


# ---------------- manifest ----------------

def cmd_manifest(opts):
    types = load_registry()
    if opts.type not in types:
        sys.exit(f"ERROR: unknown task type {opts.type!r}. Known: {', '.join(sorted(types))}")
    spec = types[opts.type]
    targets = expand_range(opts.range) if opts.range else []
    if spec["requiresTarget"] and not targets:
        sys.exit(f"ERROR: task type {opts.type!r} requires --range")
    auths = opts.authorize or []
    legal = set(spec.get("optionalAuthorizations", []))
    for a in auths:
        if a not in legal:
            sys.exit(f"ERROR: authorization {a!r} is not defined for type {opts.type!r} "
                     f"(legal: {sorted(legal) or 'none'})")
    max_batch = spec.get("maxBatch")
    if max_batch and len(targets) > max_batch:
        sys.exit(f"ERROR: {len(targets)} targets exceed maxBatch {max_batch} for {opts.type!r}; "
                 f"split the range into smaller PRs")
    manifest = {
        "type": opts.type,
        "module": opts.module,
        "targets": targets,
        "model": spec["model"],
        "paused": spec.get("paused", False),
        "fableReviewRequired": spec.get("fableReviewRequired", False),
        "authorizations": auths,
        "maxBatch": max_batch,
        "allowedFiles": spec["allowedFiles"],
        "allowedJsonPaths": spec["allowedJsonPaths"],
        "forbiddenFiles": spec["forbiddenFiles"],
        "allowlistPolicy": spec["allowlistPolicy"],
        "structurePolicy": spec["structurePolicy"],
        "requiredValidators": spec["requiredValidators"],
        "generationCommands": spec["generationCommands"],
        "buildTestCommands": spec["buildTestCommands"],
        "escalationTriggers": spec["escalationTriggers"],
    }
    out = json.dumps(manifest, indent=1)
    if opts.out:
        Path(opts.out).write_text(out + "\n")
        print(f"manifest written to {opts.out}")
    else:
        print(out)


# ---------------- preflight ----------------

def cmd_preflight(opts):
    m, spec = load_manifest(opts.manifest)
    errors, notes = [], []
    if m.get("paused"):
        errors.append(f"task type {m['type']!r} is PAUSED; requires explicit unpausing (registry change)")

    dirty = sh(["git", "status", "--porcelain"]).stdout.strip()
    branch = sh(["git", "rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
    hooks = sh(["git", "config", "core.hooksPath"]).stdout.strip()
    version = (REPO / "VERSION").read_text().strip()
    pkg = json.loads((REPO / "package.json").read_text())["version"]
    lock = json.loads((REPO / "package-lock.json").read_text())["version"]

    print(f"branch: {branch} ({'DIRTY' if dirty else 'clean'}), VERSION {version}, "
          f"package {pkg}, lock {lock}, hooksPath {hooks or '(unset)'}")
    if dirty:
        (notes if opts.dry_run else errors).append("git tree is dirty" + (" (tolerated: --dry-run)" if opts.dry_run else "; commit or stash first"))
    if hooks != "githooks":
        errors.append("core.hooksPath inactive; run: git config core.hooksPath githooks")
    if not (version == pkg == lock):
        errors.append(f"VERSION/package/lock out of sync: {version}/{pkg}/{lock}")

    wf = (REPO / ".github" / "workflows" / "deploy-pages.yml").read_text()
    for needle in ("validate:offline:yoma", "check:rashi-pr-scope:yoma"):
        if needle not in wf:
            errors.append(f"CI workflow is missing required gate {needle!r}")

    if m["type"] in RASHI_TYPES or m.get("generationCommands"):
        fresh = sh([sys.executable, "scripts/check_generated_freshness.py"], cwd=YROOT)
        print(f"generated freshness: {'OK' if fresh.returncode == 0 else 'STALE'}")
        if fresh.returncode != 0:
            errors.append("generated data stale; regenerate before starting")

    if m["type"] in RASHI_TYPES:
        task = load_registry()[m["type"]].get("rashiPreflightTask", "reconstruct")
        for daf in m["targets"]:
            r = sh([sys.executable, "scripts/rashi_preflight.py", daf, "--task", task], cwd=YROOT)
            per_daf_errors = [l for l in r.stdout.splitlines() if l.strip().startswith("ERROR") and daf in l]
            ok = r.returncode == 0 or (opts.dry_run and not per_daf_errors)
            print(f"rashi preflight {daf} ({task}): {'OK' if ok else 'FAIL'}")
            for l in per_daf_errors:
                errors.append(l.strip())
    elif m["targets"]:
        for daf in m["targets"]:
            if not (YROOT / "assets" / "talmuddev" / f"{daf}.json").exists():
                errors.append(f"{daf}: no talmuddev source")

    for l in notes:
        print(f"NOTE: {l}")
    if errors:
        print("\nWORKER PREFLIGHT FAILED:")
        for e in errors:
            print(f"  ERROR  {e}")
        sys.exit(1)
    print(f"\nOK: worker preflight passed for type {m['type']}"
          + (f", targets {', '.join(m['targets'])}" if m["targets"] else "")
          + (" [dry-run]" if opts.dry_run else "") + ".")


# ---------------- packet ----------------

def cmd_packet(opts):
    m, spec = load_manifest(opts.manifest)
    t = m["type"]
    if t in RASHI_TYPES:
        for daf in m["targets"]:
            r = sh([sys.executable, "scripts/make_rashi_work_packet.py", daf], cwd=YROOT)
            print(r.stdout)
        return
    if spec.get("jsonScope") and m["targets"]:
        for daf in m["targets"]:
            lj = json.loads((YROOT / "assets" / "learning" / "yoma" / f"{daf}.learning.json").read_text())
            print(f"# Gemara-learning packet: {daf}")
            print(f"sugyot: {len(lj['sugyot'])}")
            for s in lj["sugyot"]:
                d = s.get("display", {})
                print(f"\n## {s['id']} (vilna {s['lineRange']['startVilnaLine']}-{s['lineRange']['endVilnaLine']})")
                print(f"title: {d.get('title','')}")
                print(f"argumentFlow ids: {[af['id'].split('-')[-1] for af in s.get('argumentFlow', [])]}")
                print(f"learning keys: {sorted((s.get('learning') or {}).keys())}")
            print("\nschema contract: shared/schema_map.js; gate: validate:schema:yoma")
        return
    if t == "literal-layer":
        r = sh(["npm", "run", "status:literal:yoma"], cwd=REPO)
        print(r.stdout[-2000:])
        print("commands: fetch_literal_en.py --range <a> <b> --skip-existing; then build_literal_layer.py --apply; gate: validate:literal:yoma")
        return
    if t == "docs-tooling":
        print("# Docs/tooling packet")
        print("affected commands: see package.json scripts block")
        print("required green: validate:offline:yoma, build, check:deploy-html, npm test, test:browser")
        print("docs likely needing updates: docs/worker-pipeline.md, docs/rashi-workflow.md, docs/rashi-audit-backlog.md")
        return
    if t == "generated-refresh":
        print("# Generated-refresh packet")
        for c in spec["generationCommands"]:
            print(f"run: {c}")
        print("then: npm run check:generated:yoma must pass; only learning_data.js/coverage.json may differ")
        return
    if t == "deployment-verify":
        print("# Deployment-verify packet")
        print("check Deploy Cloudways Branch and Deploy GitHub Pages for the target commit; then live site VERSION")
        print("no file changes permitted")
        return
    if t == "audit-only":
        print("# Audit-only packet")
        print("read-only: corpus scans, audit:rashi:semantic:yoma, validator dry runs, backlog reconciliation")
        print("output only under docs/reports/ (plus backlog process notes); no content or generated edits")
        return
    if t == "nekudot":
        print("# Nekudot packet: task type is PAUSED. No packet is issued.")
        return


# ---------------- prompt ----------------

def cmd_prompt(opts):
    m, spec = load_manifest(opts.manifest)
    t = m["type"]
    tgt = ", ".join(m["targets"]) if m["targets"] else "(no daf target)"
    lines = [
        f"Run a bounded MySugya worker pass: type {t}, module {m['module']}, target {tgt}.",
        "",
        spec["description"],
        "",
        f"Recommended model: {m['model']}. Haiku may take this task only if the model field says haiku"
        " (haiku-with-fable-review means Haiku executes and Fable reviews the PR before merge).",
        "",
        "Procedure:",
        f"1. Reconcile to origin/main; confirm clean tree.",
        f"2. npm run worker:preflight -- --manifest .worker-manifest.json   (STOP on failure)",
        f"3. npm run worker:packet -- --manifest .worker-manifest.json     (sole context source)",
        "4. Perform ONLY the edits the manifest allows:",
        f"   allowed files: {json.dumps(m['allowedFiles'])}",
        f"   allowed JSON paths: {json.dumps(m['allowedJsonPaths'])}",
        f"   forbidden: {json.dumps(m['forbiddenFiles'])}",
    ]
    if m["generationCommands"]:
        lines.append("5. Regenerate: " + " && ".join(m["generationCommands"]))
    lines += [
        "6. Bump VERSION one patch; python3 scripts/sync_version.py",
        "7. npm run worker:verify -- --manifest .worker-manifest.json --fast",
        "   then npm run worker:verify -- --manifest .worker-manifest.json --full",
        "8. Commit .worker-manifest.json together with the work, push, one PR, wait for CI, merge when green, verify both deploy workflows.",
        "",
        f"Allowlist policy: {m['allowlistPolicy']}. You may NEVER add allowlist or baseline entries.",
        f"Structure policy: {m['structurePolicy']}.",
        "You may not override, weaken, or reinterpret any validator. A red gate means your content or scope is wrong.",
        "",
        "Escalate (stop immediately and report) on:",
    ]
    lines += [f"- {e}" for e in m["escalationTriggers"]]
    lines += [
        "- any need to touch a file outside the allowed set",
        "",
        "Final report format (one compact block): task type, targets, PR number and merge commit,",
        "VERSION, gates status, deploy status, allowlist delta, anything escalated.",
    ]
    print("\n".join(lines))


# ---------------- scope ----------------

def resolve_base(base):
    if base:
        return base
    env_base = os.environ.get("GITHUB_BASE_REF", "").strip()
    return f"origin/{env_base}" if env_base else "origin/main"


def cmd_scope(opts):
    m, spec = load_manifest(opts.manifest)
    base = resolve_base(opts.base)
    mb = sh(["git", "merge-base", base, "HEAD"]).stdout.strip()
    if not mb:
        print(f"WARNING: cannot resolve merge-base of {base!r}; skipping scope check.")
        return
    changed = [l for l in sh(["git", "diff", "--name-only", mb]).stdout.splitlines() if l.strip()]
    errors = []

    for p in changed:
        if not file_allowed(p, spec, m["targets"]):
            errors.append(f"{p}: outside the {m['type']} allowed file set")
    if not spec["allowedFiles"] and changed:
        errors.append(f"task type {m['type']} permits no file changes; {len(changed)} file(s) changed")

    if m["type"] in RASHI_TYPES:
        # Field-level enforcement reuses the proven Rashi validator.
        r = sh([sys.executable, "scripts/check_rashi_pr_scope.py", "--base", base], cwd=YSCRIPTS.parent)
        if r.returncode != 0:
            errors.append("check_rashi_pr_scope failed:\n" + r.stdout[-1200:])
        max_batch = m.get("maxBatch")
        if max_batch and len(m.get("targets", [])) > max_batch:
            errors.append(f"manifest targets {len(m['targets'])} exceed maxBatch {max_batch} "
                          f"for {m['type']} (split into smaller PRs)")
    else:
        # Non-Rashi types: inline allowlist ratchet (the Rashi validator's
        # field rules do not apply to these diffs).
        allowlist_ratchet_inline(mb, m["allowlistPolicy"], errors)
        json_scope_check(mb, changed, m, spec, errors)
        if m["type"] == "generated-refresh":
            src_changed = [p for p in changed if p.startswith("modules/yoma/assets/")]
            if src_changed:
                errors.append(f"generated-refresh PR changed source files: {src_changed} "
                              f"(generated outputs only)")
        if m["type"] == "literal-layer":
            gen_only = [p for p in changed if p in ("modules/yoma/learning_data.js", "modules/yoma/coverage.json")]
            src = [p for p in changed if p.startswith("modules/yoma/assets/literal_en/")]
            if gen_only and not src:
                errors.append("literal-layer PR changed generated output without any "
                              "assets/literal_en source change (use generated-refresh instead)")

    # Manifest lifecycle: every changed learning JSON must be a manifest target
    if m["type"] not in ("docs-tooling",):
        for p in changed:
            if p.startswith("modules/yoma/assets/learning/") and p.endswith(".learning.json"):
                daf = p.split("/")[-1].replace(".learning.json", "")
                if daf not in m.get("targets", []):
                    errors.append(f"{p}: changed but daf {daf!r} is not in manifest targets "
                                  f"{m.get('targets', [])} (regenerate the manifest to cover it)")

    if errors:
        print(f"WORKER SCOPE CHECK FAILED (type {m['type']}, base {base}):\n")
        for e in errors:
            print(f"  ERROR  {e}")
        sys.exit(1)
    print(f"OK: {len(changed)} changed file(s) within {m['type']} scope vs {base}.")


# ---------------- verify ----------------

def cmd_verify(opts):
    m, spec = load_manifest(opts.manifest)
    results = []

    if m["type"] in RASHI_TYPES and m["targets"]:
        cmd = [sys.executable, "scripts/rashi_verify.py", *m["targets"]]
        if opts.full:
            cmd.append("--full")
        r = sh(cmd, cwd=YROOT)
        print(r.stdout[-3000:])
        results.append(("rashi-verify", r.returncode == 0))
    else:
        r = sh(["npm", "run", "validate:offline:yoma"])
        results.append(("offline-gates", r.returncode == 0))
        if r.returncode != 0:
            print(r.stdout[-1500:])
        if opts.full:
            for name, cmd in [("build", ["npm", "run", "build"]),
                              ("deploy-html", ["npm", "run", "check:deploy-html"]),
                              ("unit+render", ["npm", "test"]),
                              ("browser", ["npm", "run", "test:browser"])]:
                if not spec["buildTestCommands"]:
                    break
                rr = sh(cmd)
                results.append((name, rr.returncode == 0))
                if rr.returncode != 0:
                    print(rr.stdout[-1200:])

    # scope + hygiene for every type
    scope_ns = argparse.Namespace(manifest=opts.manifest, base=opts.base)
    try:
        cmd_scope(scope_ns)
        results.append(("worker-scope", True))
    except SystemExit as ex:
        results.append(("worker-scope", ex.code in (0, None)))

    version = (REPO / "VERSION").read_text().strip()
    pkg = json.loads((REPO / "package.json").read_text())["version"]
    results.append(("version-sync", version == pkg))

    mb = sh(["git", "merge-base", resolve_base(opts.base), "HEAD"]).stdout.strip()
    changed = sh(["git", "diff", "--name-only", mb]).stdout.split() if mb else []
    dash_bad = []
    if mb:
        for p in changed:
            fp = REPO / p
            if fp.suffix in (".py", ".md", ".json", ".yml", ".js", ".jsx") and fp.exists():
                if p.startswith("modules/yoma/assets/talmuddev/") or p == "modules/yoma/learning_data.js":
                    continue
                txt = fp.read_text(errors="ignore")
                if "\u2014" in txt or "\u2013" in txt:
                    if not p.startswith("modules/yoma/assets/"):
                        dash_bad.append(p)
    results.append(("no-dashes", not dash_bad))
    for p in dash_bad:
        print(f"  dash found in {p}")

    # Per-daf allowlist completion summary (placeholder/rashi repair tasks)
    if m["targets"] and mb:
        ca_path = YSCRIPTS / "allowlists" / "rashi_content_allowlist.json"
        r = sh(["git", "show", f"{mb}:{ca_path.relative_to(REPO).as_posix()}"])
        old_entries = json.loads(r.stdout).get("entries", []) if r.returncode == 0 else []
        new_entries = json.loads(ca_path.read_text()).get("entries", [])
        print("\nper-daf allowlist completion:")
        shrank_or_equal = True
        for daf in m["targets"]:
            before = sum(1 for e in old_entries if e["daf"] == daf)
            after = sum(1 for e in new_entries if e["daf"] == daf)
            print(f"  {daf}: allowlisted lines {before} -> {after}")
            if after > before:
                shrank_or_equal = False
        if m.get("type") == "placeholder-backfill" and not shrank_or_equal:
            results.append(("allowlist-shrink", False))

    # Literal-layer coverage delta
    if m["type"] == "literal-layer":
        cov = sh([sys.executable, "scripts/validate_literal.py"], cwd=YROOT)
        for line in cov.stdout.splitlines():
            if line.startswith(("Coverage:", "Has en_lit:", "Non-empty:")):
                print(f"  {line.strip()}")
        impacted = [p for p in changed if p.startswith("modules/yoma/assets/literal_en/")]
        print(f"  literal_en files impacted: {len(impacted)}")

    print("\n============ worker:verify summary ============")
    fail = False
    for name, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        fail |= not ok
    if fail:
        print("\nWORKER VERIFY FAILED. Fix your content/scope or STOP AND ESCALATE.")
        sys.exit(1)
    if m.get("fableReviewRequired"):
        print("\nREVIEW GATE: this task type requires Fable review of the PR before merge. "
              "Workers may open the PR and poll CI, but may NOT merge; request Fable review "
              "and stop.")
    nxt = "commit (include .worker-manifest.json), push, open the PR" if opts.full else \
          "npm run worker:verify -- --manifest .worker-manifest.json --full"
    print(f"\nWORKER VERIFY PASSED ({'full' if opts.full else 'fast'}). Next: {nxt}")


# ---------------- schema-matrix ----------------

SCHEMA_SCOPE = Path(__file__).parent / "worker_schema_scope.json"


def cmd_schema_matrix(opts):
    """Cross-check the schema inventory against the task-type registry.

    For every classified path, compute which task types can edit it (via
    their jsonScope mutable/flagMutable patterns, or the Rashi contract for
    rashiTranslations en/links). FAIL if: a path classified as editable has
    no owning task type; a path classified immutable/generated-only IS
    reachable by some type's mutable patterns; or an inventory entry is
    missing a known classification. Print the full matrix with --print."""
    inv = json.loads(SCHEMA_SCOPE.read_text())["paths"]
    types = load_registry()
    legal_class = {"immutable", "haiku-manifest", "fable-only", "flag-only",
                   "generated-only", "deprecated"}
    RASHI_MUTABLE = {"rashiTranslations[*].en", "rashiTranslations[*].linkedGemaraLineIds[*]"}
    errors = []
    matrix = {}

    for path, cls in inv.items():
        if cls not in legal_class:
            errors.append(f"{path}: unknown classification {cls!r}")
            continue
        owners, flag_owners = [], []
        if path in RASHI_MUTABLE:
            owners += ["rashi-repair", "rashi-reconstruction", "placeholder-backfill"]
        ptr = "/" + "/".join(seg.replace("[*]", "/0") for seg in path.split("."))
        for tname, tspec in types.items():
            scope = tspec.get("jsonScope")
            if not scope:
                continue
            if any(pattern_to_regex(p).match(ptr) for p in scope.get("mutable", [])):
                owners.append(tname)
            for flag, pats in scope.get("flagMutable", {}).items():
                if any(pattern_to_regex(p).match(ptr) for p in pats):
                    flag_owners.append(f"{tname}({flag})")
        matrix[path] = {"class": cls, "taskTypes": sorted(set(owners)),
                        "flagTaskTypes": sorted(set(flag_owners))}

        if cls in ("haiku-manifest", "fable-only") and not owners:
            errors.append(f"{path}: classified {cls} but NO task type can edit it")
        if cls == "flag-only" and not flag_owners:
            errors.append(f"{path}: classified flag-only but no flagMutable pattern reaches it")
        if cls in ("immutable", "generated-only", "deprecated") and owners:
            errors.append(f"{path}: classified {cls} but reachable by {owners}")
        if cls == "haiku-manifest":
            ok = any(types[o].get("haikuAllowed") or types[o].get("model") in ("haiku", "haiku-with-fable-review")
                     for o in owners)
            if not ok:
                errors.append(f"{path}: classified haiku-manifest but no owning type permits haiku")

    if opts.print_matrix:
        print(json.dumps(matrix, indent=1))
    if errors:
        print("SCHEMA MATRIX CHECK FAILED:\n")
        for e in errors:
            print(f"  ERROR  {e}")
        sys.exit(1)
    n_by = {}
    for v in matrix.values():
        n_by[v["class"]] = n_by.get(v["class"], 0) + 1
    print(f"OK: schema matrix consistent: {len(matrix)} paths "
          f"({', '.join(f'{k}={v}' for k, v in sorted(n_by.items()))}); "
          f"every editable path has an owning task type and no immutable path is reachable.")


# ---------------- docs ----------------

def cmd_docs(opts):
    """Regenerate the machine-generated reference docs from the registry and
    schema inventory: docs/reports/task-type-reference.md and
    docs/reports/schema-coverage-matrix.md. Run after any registry or
    inventory change and commit the result."""
    types = load_registry()
    L = ["# Worker task-type reference (generated)",
         "",
         "Generated by `npm run worker:docs` from scripts/worker_task_types.json.",
         "Do not hand-edit; regenerate after registry changes.", ""]
    for name in sorted(types):
        s = types[name]
        L.append(f"## {name}")
        L.append("")
        L.append(s["description"])
        L.append("")
        L.append(f"- model: {s['model']}"
                 + ("; PAUSED" if s.get("paused") else "")
                 + (f"; Fable review required" if s.get("fableReviewRequired") else ""))
        L.append(f"- haiku allowed: {'yes' if s.get('haikuAllowed') or s.get('model') in ('haiku', 'haiku-with-fable-review') else 'no'}")
        L.append(f"- max batch: {s.get('maxBatch', 1 if s.get('requiresTarget') else 'n/a')}")
        L.append(f"- allowed files: {', '.join(s['allowedFiles']) or 'none (read-only task)'}")
        if s.get("jsonScope"):
            L.append(f"- mutable JSON paths: {', '.join(s['jsonScope']['mutable'])}")
            for flag, pats in sorted(s["jsonScope"].get("flagMutable", {}).items()):
                L.append(f"- with --authorize {flag}: {', '.join(pats)}")
        elif s.get("allowedJsonPaths"):
            L.append(f"- mutable JSON paths: {', '.join(s['allowedJsonPaths'])}")
        L.append(f"- allowlist policy: {s['allowlistPolicy']}; structure policy: {s['structurePolicy']}")
        L.append(f"- required validators: {', '.join(s['requiredValidators']) or 'none'}")
        L.append("- stop conditions:")
        for e in s["escalationTriggers"]:
            L.append(f"  - {e}")
        L.append("")
    (REPO / "docs" / "reports" / "task-type-reference.md").write_text("\n".join(L))

    inv = json.loads(SCHEMA_SCOPE.read_text())["paths"]
    M = ["# Schema coverage matrix (generated)",
         "",
         "Generated by `npm run worker:docs` from scripts/worker_schema_scope.json.",
         "Consistency with the registry is enforced by `npm run worker:schema-matrix`",
         "(run in CI on every manifest-bearing PR). High-risk paths (structure, ids,",
         "sourceRefs, Hebrew, argumentFlow, quiz/misconception content) are Fable-only",
         "because their correctness requires semantic or structural judgment that",
         "pattern gates cannot verify.", "",
         "| path | classification |", "|---|---|"]
    for path in sorted(inv):
        M.append(f"| `{path}` | {inv[path]} |")
    M.append("")
    M.append("Known drift: argumentFlow sourceRefs entries are plain strings on some")
    M.append("daf and objects on others; normalization is deferred to a future")
    M.append("structural-repair pass (documented in docs/rashi-audit-backlog.md).")
    (REPO / "docs" / "reports" / "schema-coverage-matrix.md").write_text("\n".join(M) + "\n")
    print("wrote docs/reports/task-type-reference.md and docs/reports/schema-coverage-matrix.md")


# ---------------- report ----------------

def cmd_report(opts):
    """Emit the machine-readable final report template, prefilled with what
    is derivable locally. The worker fills prNumber/mergeCommit/deploys
    after merge and posts the JSON block verbatim."""
    m, spec = load_manifest(opts.manifest)
    base = resolve_base(None)
    mb = sh(["git", "merge-base", base, "HEAD"]).stdout.strip()
    changed = [l for l in sh(["git", "diff", "--name-only", mb]).stdout.splitlines() if l.strip()] if mb else []
    ca = YSCRIPTS / "allowlists" / "rashi_content_allowlist.json"
    r = sh(["git", "show", f"{mb}:{ca.relative_to(REPO).as_posix()}"]) if mb else None
    old_n = len(json.loads(r.stdout).get("entries", [])) if r and r.returncode == 0 else None
    new_n = len(json.loads(ca.read_text()).get("entries", []))
    report = {
        "taskType": m["type"],
        "targets": m["targets"],
        "version": (REPO / "VERSION").read_text().strip(),
        "branch": sh(["git", "rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip(),
        "filesChanged": changed,
        "allowlistDelta": {"before": old_n, "after": new_n},
        "fableReviewRequired": m.get("fableReviewRequired", False),
        "prNumber": "<fill after PR creation>",
        "mergeCommit": "<fill after merge>",
        "gates": "<fill: verify --full result>",
        "deploys": {"cloudways": "<fill>", "githubPages": "<fill>"},
        "escalations": [],
    }
    print(json.dumps(report, indent=1))


# ---------------- ci-check ----------------

def cmd_ci_check(opts):
    base = resolve_base(opts.base)
    mb = sh(["git", "merge-base", base, "HEAD"]).stdout.strip()
    if not mb:
        print(f"WARNING: cannot resolve merge-base of {base!r}; skipping ci-check.")
        return
    changed = [l for l in sh(["git", "diff", "--name-only", mb]).stdout.splitlines() if l.strip()]
    content_changed = [p for p in changed if p.startswith(CONTENT_PREFIXES)]
    workflow_changed = [p for p in changed if p.startswith(".github/workflows/")]
    # The manifest counts as part of the PR if it exists and is new or
    # different relative to the base (a stale leftover identical to the base
    # does not count; every PR must bring its own manifest).
    manifest_present = False
    if MANIFEST_DEFAULT.exists():
        r = sh(["git", "show", f"{mb}:.worker-manifest.json"])
        manifest_present = r.returncode != 0 or r.stdout != MANIFEST_DEFAULT.read_text()

    if not content_changed and not workflow_changed:
        print("OK: no module content or workflow changes; manifest not required.")
        return

    if not manifest_present:
        if content_changed:
            print("CI MANIFEST CHECK FAILED:\n")
            print("  ERROR  module content changed but no .worker-manifest.json is part of this PR.")
            print("  Generate one, e.g.:")
            print("    npm run worker:manifest -- --type rashi-repair --module yoma --range <daf> --out .worker-manifest.json")
            print("  and commit it with the content change.")
            sys.exit(1)
        # workflow-only change without manifest: require docs-tooling manifest
        print("CI MANIFEST CHECK FAILED:\n")
        print("  ERROR  workflow files changed but no .worker-manifest.json (docs-tooling) is part of this PR.")
        print("  Workflow edits require an explicit docs-tooling manifest and pipeline-level review.")
        sys.exit(1)

    m, spec = load_manifest(MANIFEST_DEFAULT)
    if workflow_changed and m["type"] != "docs-tooling":
        print(f"CI MANIFEST CHECK FAILED: workflow files changed but manifest type is {m['type']!r}, not docs-tooling.")
        sys.exit(1)
    # Registry/inventory consistency is part of every manifest-bearing PR.
    matrix_ns = argparse.Namespace(print_matrix=False)
    cmd_schema_matrix(matrix_ns)
    scope_ns = argparse.Namespace(manifest=str(MANIFEST_DEFAULT), base=opts.base)
    cmd_scope(scope_ns)
    print(f"OK: PR carries a valid {m['type']} manifest and passes its scope contract.")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("manifest")
    p.add_argument("--type", required=True)
    p.add_argument("--module", default="yoma")
    p.add_argument("--range", default=None)
    p.add_argument("--out", default=None)
    p.add_argument("--authorize", action="append", default=None,
                   help="grant an optional authorization defined by the task type "
                        "(e.g. authorizeQuizSeeds); repeatable; Fable-issued only")

    for name in ("preflight", "packet", "prompt"):
        p = sub.add_parser(name)
        p.add_argument("--manifest", default=str(MANIFEST_DEFAULT))
        if name == "preflight":
            p.add_argument("--dry-run", action="store_true")

    p = sub.add_parser("verify")
    p.add_argument("--manifest", default=str(MANIFEST_DEFAULT))
    p.add_argument("--fast", action="store_true")
    p.add_argument("--full", action="store_true")
    p.add_argument("--base", default=None)

    p = sub.add_parser("scope")
    p.add_argument("--manifest", default=str(MANIFEST_DEFAULT))
    p.add_argument("--base", default=None)

    p = sub.add_parser("ci-check")
    p.add_argument("--base", default=None)

    p = sub.add_parser("report")
    p.add_argument("--manifest", default=str(MANIFEST_DEFAULT))

    p = sub.add_parser("schema-matrix")
    p.add_argument("--print", dest="print_matrix", action="store_true")

    sub.add_parser("docs")

    opts = ap.parse_args()
    {"manifest": cmd_manifest, "preflight": cmd_preflight, "packet": cmd_packet,
     "prompt": cmd_prompt, "verify": cmd_verify, "scope": cmd_scope,
     "ci-check": cmd_ci_check, "report": cmd_report,
     "schema-matrix": cmd_schema_matrix, "docs": cmd_docs}[opts.cmd](opts)


if __name__ == "__main__":
    main()
