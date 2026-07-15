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

RASHI_TYPES = {"rashi-repair", "rashi-reconstruction", "rashi-realignment",
               "placeholder-backfill", "rashi-structural-repair"}
STRUCTURAL_TYPE = "rashi-structural-repair"
# Task types eligible for the source-relative citation-evidence policy (see
# drift_ok_for_type below). Deliberately excludes rashi-structural-repair,
# which already has its own, broader, unconditional haiku-safe allowance.
EVIDENCE_TIER_TYPES = ("rashi-reconstruction", "rashi-realignment")
ONE_ANCHOR_ATTESTATION_KEYS = (
    "onlyOneGenuineCitation",
    "citationTranslatedOnOwnLine",
    "noCitationInventedMovedOrDuplicated",
    "noSemanticUncertaintyRemains",
)
ZERO_ANCHOR_ATTESTATION_KEYS = (
    "everyRawLineRereadForCitations",
    "noTractateDafChapterVerseOrOtherCitationAnywhere",
    "noCitationInventedMovedOrDuplicated",
    "noSemanticUncertaintyRemains",
)


def structure_authorized(m, spec):
    """True only for a structural-repair manifest carrying the explicit
    allowStructure authorization. No other task type can ever pass the
    --allow-structure flag to the Rashi scope validator."""
    return (m.get("type") == STRUCTURAL_TYPE
            and "allowStructure" in m.get("authorizations", []))
DRIFT_OVERRIDE_ENV = "FABLE_DRIFT_OVERRIDE"
CONTENT_PREFIXES = ("modules/yoma/assets/learning/", "modules/yoma/assets/literal_en/",
                    "modules/yoma/assets/talmuddev/", "modules/yoma/assets/daftexts/")


def sh(args, cwd=REPO, env=None):
    e = dict(os.environ, **(env or {}))
    return subprocess.run(args, capture_output=True, text=True, cwd=cwd, env=e)


def load_registry():
    return json.loads(REGISTRY.read_text())["taskTypes"]


def review_policy_of(spec):
    """A task type's review policy: 'conditional' (worker self-review plus
    the machine-checked auto-merge gate; escalation to escalationModel),
    'fable' (unconditional Fable review before merge), or 'none'."""
    if spec.get("reviewPolicy"):
        return spec["reviewPolicy"]
    return "fable" if spec.get("fableReviewRequired") else "none"


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
        "reviewPolicy": review_policy_of(spec),
        "escalationModel": spec.get("escalationModel", "fable"),
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
    for req in spec.get("requiredAuthorizations", []):
        if req not in m.get("authorizations", []):
            errors.append(f"task type {m['type']!r} requires the explicit --authorize {req} "
                          f"authorization on the manifest (Fable-issued only)")

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
        task = spec.get("rashiPreflightTask", "reconstruct")
        # Drift-block enforcement is manifest-aware here: the underlying
        # rashi_preflight env override is honored ONLY when the manifest
        # also carries the Fable-issued authorizeDriftOverride flag. A
        # worker cannot unblock a SHIFTED/FABRICATION-SUSPECT daf by
        # setting the env var alone, and a manifest flag alone (however it
        # was generated) does nothing without the Fable-only env var.
        child_env = dict(os.environ)
        if spec.get("driftBlocked") and "authorizeDriftOverride" not in m.get("authorizations", []):
            child_env.pop(DRIFT_OVERRIDE_ENV, None)
        for daf in m["targets"]:
            r = subprocess.run([sys.executable, "scripts/rashi_preflight.py", daf, "--task", task],
                               capture_output=True, text=True, cwd=YROOT, env=child_env)
            per_daf_errors = [l for l in r.stdout.splitlines() if l.strip().startswith("ERROR") and daf in l]
            ok = r.returncode == 0 or (opts.dry_run and not per_daf_errors)
            print(f"rashi preflight {daf} ({task}): {'OK' if ok else 'FAIL'}")
            for l in per_daf_errors:
                errors.append(l.strip().removeprefix("ERROR").strip())
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
        " (haiku-with-fable-review means Haiku executes and Fable reviews the PR before merge;"
        " sonnet means Sonnet is the worker and Haiku is not allowed; fable means pipeline/tooling"
        " work owned by Fable).",
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
    if t in RASHI_TYPES:
        lines += [
            "",
            "Rashi linking contract: linkedGemaraLineIds are SEMANTIC text anchors.",
            "Match each Rashi comment to the local segment(s) whose text it explains,",
            "using the packet's full segment text (Gemara and Mishnah ids alike).",
            "Never assign links by vilna line number or positional offset. A comment",
            "may link to multiple segments when it genuinely spans them; boundary",
            "policy never covers unrelated commentary. If the correct target segment",
            "cannot be identified from the packet, stop and escalate; never guess.",
        ]
    if m["generationCommands"]:
        lines.append("5. Regenerate: " + " && ".join(m["generationCommands"]))
    lines += [
        "6. Bump VERSION one patch; python3 scripts/sync_version.py",
        "7. npm run worker:verify -- --manifest .worker-manifest.json --fast",
        "   then npm run worker:verify -- --manifest .worker-manifest.json --full",
    ]
    if review_policy_of(spec) == "conditional":
        lines += [
            "8. Fresh post-edit self-review (MANDATORY before the PR): reread the raw",
            "   Hebrew and the packet's FULL segment text from scratch, without relying",
            "   on your earlier working assumptions, and recheck: the beginning, middle,",
            "   and tail of the daf; every citation anchor; every multi-id link; every",
            "   truncated boundary entry; every formerly allowlisted entry; that every",
            "   link is semantic (never positional); that no line uses the final id as",
            "   an unrelated-content fallback. Record the result in",
            "   .worker-self-review.json:",
            '   {"daf": "<daf>", "model": "' + m["model"] + '", "rechecked": {'
            + ", ".join(f'"{c}": true' for c in SELF_REVIEW_CHECKS) + "},",
            '    "blockersFound": [], "notes": "<one line>"}',
            "   Any blocker found = escalate; do not open the PR as mergeable.",
            "9. Commit .worker-manifest.json and .worker-self-review.json together with",
            "   the work, push, ONE PR for this daf only, wait for CI.",
            "10. npm run worker:review -- --manifest .worker-manifest.json",
            "    Merge ONLY when CI is green on the exact final head AND this prints",
            "    AUTO-MERGE-ELIGIBLE. No operator authorization is needed when both hold.",
            "    Then verify BOTH deploy workflows for the merge commit.",
            "11. If a queue is active: rerun npm run worker:queue. Progress derives",
            "    automatically from the merged manifest at origin/main; there is no state",
            "    to commit and NEVER a direct push to main. Continue to the",
            "    next queued target with a fresh manifest. Stop ONLY on an escalation",
            "    condition, unexpected repository state, or an empty queue.",
            f"    On escalation: stop, do not merge, and hand off to {spec.get('escalationModel', 'fable')} with a report.",
        ]
    else:
        lines += [
            "8. Commit .worker-manifest.json together with the work, push, one PR, wait for CI, merge when green, verify both deploy workflows.",
        ]
    lines += [
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
        # Field-level enforcement reuses the proven Rashi validator. Only a
        # structural-repair manifest with the explicit allowStructure
        # authorization may relax the structure rules; every other type
        # (Haiku or Sonnet manifests included) gets the strict contract.
        scope_cmd = [sys.executable, "scripts/check_rashi_pr_scope.py", "--base", base]
        if structure_authorized(m, spec):
            scope_cmd.append("--allow-structure")
            print("NOTE: allowStructure authorization active (rashi-structural-repair manifest).")
        r = sh(scope_cmd, cwd=YSCRIPTS.parent)
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
        # Post-edit drift profile: hard gate for rashi-realignment (the
        # task's whole purpose is restoring alignment), advisory for the
        # other Rashi types.
        pr = sh([sys.executable, "scripts/audit_rashi_semantic.py", "--profile", "--json",
                 *m["targets"]], cwd=YROOT)
        try:
            profs = json.loads(pr.stdout)
            profs = profs if isinstance(profs, list) else [profs]
        except json.JSONDecodeError:
            profs = []
        bad = [f"{p['daf']}={p['classification']}" for p in profs if not p.get("haikuSafe")]
        print(f"post-edit drift profile: {', '.join(bad) if bad else 'all targets aligned'}")
        if m["type"] in ("rashi-realignment", "rashi-reconstruction", STRUCTURAL_TYPE):
            results.append(("drift-profile", not bad and bool(profs)))
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
    policy = review_policy_of(spec)
    if policy == "fable":
        print("\nREVIEW GATE: this task type requires Fable review of the PR before merge. "
              "Workers may open the PR and poll CI, but may NOT merge; request Fable review "
              "and stop.")
    elif policy == "conditional":
        print("\nCONDITIONAL REVIEW GATE: after the fresh post-edit self-review is recorded "
              "in .worker-self-review.json and CI is green on the final head, run "
              "`npm run worker:review -- --manifest .worker-manifest.json`. Merge ONLY if it "
              f"prints AUTO-MERGE-ELIGIBLE; on any failed condition, escalate to "
              f"{spec.get('escalationModel', 'fable')} instead of merging.")
    nxt = "commit (include .worker-manifest.json), push, open the PR" if opts.full else \
          "npm run worker:verify -- --manifest .worker-manifest.json --full"
    print(f"\nWORKER VERIFY PASSED ({'full' if opts.full else 'fast'}). Next: {nxt}")


# ---------------- review (conditional auto-merge gate) ----------------

SELF_REVIEW_PATH = REPO / ".worker-self-review.json"
SELF_REVIEW_CHECKS = (
    "beginningMiddleTail", "citationAnchors", "multiIdLinks",
    "truncatedBoundaryEntries", "formerlyAllowlistedEntries",
    "semanticNotPositional", "noUnrelatedFinalIdFallback",
)

# Canonical machine-checked auto-merge conditions, in report order. CI
# greenness and the verify --fast/--full runs are procedural conditions the
# worker satisfies in the loop itself (worker:review reminds about them but
# cannot observe CI from here).
REVIEW_CONDITIONS = (
    "single-target-manifest",
    "exactly-one-authorized-daf-changed",
    "scope-clean-no-structure-no-hebrew-no-forbidden-fields",
    "no-allowlist-additions",
    "allowlist-removals-limited-to-target-daf",
    "packet-contains-every-linked-local-id",
    "all-links-legal-and-nonempty",
    "drift-profile-ALIGNED",
    "semantic-audit-zero-shift-candidates",
    "no-stub-or-duplicate-helpers",
    "generated-files-fresh",
    "version-metadata-synced",
    "fresh-self-review-committed-and-clean",
)


def evaluate_review_policy(conditions):
    """Pure auto-merge policy: eligible only when EVERY condition is true.
    Returns (eligible, failed_condition_names)."""
    failed = [k for k in conditions if not conditions[k]]
    return (not failed, failed)


def independent_zero_citation_scan(daf):
    """A SECOND, independent check that a daf's raw Hebrew contains no
    citation-like text at all, deliberately not reusing anchors_of()'s
    per-line/lookahead/tractate-name-matching logic: scans the ENTIRE
    concatenated raw text for any parenthetical group whatsoever,
    whether or not its contents match a known tractate name or a daf
    number. Catches citation-like tokens (an unrecognized abbreviation,
    an "(ibid)"-style reference, a verse citation format anchors_of does
    not model) that a zero-anchor profile from the primary scanner could
    otherwise miss. Returns (ok: bool, detail: str)."""
    tpath = YROOT / "assets" / "talmuddev" / f"{daf}.json"
    if not tpath.exists():
        return False, f"no talmuddev source for {daf}"
    raw = [l for l in json.loads(tpath.read_text()).get("rashi", []) if l and l.strip()]
    whole = " ".join(raw)
    hits = re.findall(r"\(([^()]{1,60})\)", whole)
    if hits:
        return False, f"parenthetical citation-like text found: {hits[:5]}"
    return True, "no parenthetical citation-like text anywhere in the raw Hebrew"


def multi_anchor_safe(prof):
    """Case A: 2+ genuine anchors. Stricter than the bare ALIGNED label
    (which the classifier also grants to a daf with anchors still
    missing, e.g. 2 found + 2 missing): requires the classification
    itself be ALIGNED, every expected anchor found, zero missing, and
    every found offset exactly 0. Returns (ok: bool, reason: str)."""
    if not prof:
        return False, "no drift profile available"
    cls = prof.get("classification")
    if cls != "ALIGNED":
        return False, f"classification is {cls}, not ALIGNED"
    if len(prof.get("anchors", [])) < 2:
        return False, "fewer than 2 genuine anchors (not a multi-anchor daf)"
    if prof.get("anchorsMissing", 1) != 0:
        return False, f"{prof.get('anchorsMissing')} expected anchor(s) missing"
    bad_offsets = [o for o in prof.get("offsets", []) if o != 0]
    if bad_offsets:
        return False, f"offset(s) not exactly 0: {bad_offsets}"
    return True, "classification ALIGNED, every expected anchor found, zero missing, all offsets 0"


def one_anchor_safe(prof, sr):
    """Case B (Yoma 48b class of daf): a rashi-reconstruction/realignment
    daf whose raw Hebrew genuinely contains exactly one detectable
    citation may substitute for ALIGNED when ALL of the following hold,
    computed only from the drift profile and the fresh self-review (no
    file I/O, no git):

      1. prof['anchors'] has exactly one entry.
      2. that entry's offset is not None (it is found in the English).
      3. that entry's offset is exactly 0 (no displacement).
      4. prof['anchorsMissing'] is 0 (no expected anchor is missing).
      5. the self-review carries an 'oneAnchorAttestation' (or the
         legacy 'anchorPoorAttestation') block with all of
         ONE_ANCHOR_ATTESTATION_KEYS explicitly true.

    SHIFTED requires >= SHIFT_MIN_ANCHORS (2) same-sign displaced
    anchors and FABRICATION-SUSPECT requires >= FAB_MIN_CONSECUTIVE_MISSES
    (2) consecutive missing name anchors, so condition 1 alone already
    excludes both classifications from ever qualifying; this function
    never reclassifies or relabels the daf. Returns (ok: bool, reason: str)."""
    if not prof:
        return False, "no drift profile available"
    anchors = prof.get("anchors", [])
    if len(anchors) != 1:
        return False, (f"{len(anchors)} genuine detectable citation(s) in the raw Hebrew "
                        "(this tier requires exactly 1)")
    offset = anchors[0].get("offset")
    if offset is None:
        return False, "the single citation is not found anywhere in the English"
    if offset != 0:
        return False, f"the single citation is found at offset {offset}, not 0"
    if prof.get("anchorsMissing", 1) != 0:
        return False, f"{prof.get('anchorsMissing')} expected citation(s) missing"
    att = (sr or {}).get("oneAnchorAttestation") or (sr or {}).get("anchorPoorAttestation") or {}
    missing_att = [k for k in ONE_ANCHOR_ATTESTATION_KEYS if att.get(k) is not True]
    if missing_att:
        return False, f"self-review oneAnchorAttestation missing or false: {missing_att}"
    return True, ("exactly one genuine citation, found at offset 0, no missing anchors, "
                  "self-review attests no invented/moved/duplicated citation")


def zero_anchor_safe(daf, prof, sr, entries=None):
    """Case C: a rashi-reconstruction/realignment daf whose raw Hebrew
    genuinely contains ZERO detectable citations of any kind. Citation
    anchors are corroborating evidence, not a mandatory content feature,
    so their absence must not automatically imply correctness; this tier
    therefore requires a stronger full-daf attestation than the one- or
    multi-anchor tiers, computed from the drift profile, an independent
    second source scan, the fresh self-review, and (when provided) the
    daf's own entries. Returns (ok: bool, reason: str)."""
    if not prof:
        return False, "no drift profile available"
    if prof.get("classification") != "INSUFFICIENT-ANCHORS":
        return False, f"classification is {prof.get('classification')}, not INSUFFICIENT-ANCHORS"
    anchors = prof.get("anchors", [])
    if anchors:
        return False, f"{len(anchors)} genuine detectable citation(s) exist (this tier requires 0)"
    scan_ok, scan_detail = independent_zero_citation_scan(daf)
    if not scan_ok:
        return False, f"independent second scan disagrees: {scan_detail}"
    att = (sr or {}).get("zeroAnchorAttestation") or {}
    missing_att = [k for k in ZERO_ANCHOR_ATTESTATION_KEYS if att.get(k) is not True]
    if missing_att:
        return False, f"self-review zeroAnchorAttestation missing or false: {missing_att}"
    if entries is not None:
        empty_vl = {e["vilnaLine"] for e in entries if not e.get("linkedGemaraLineIds")}
        authorized = {a.get("vilnaLine") for a in (sr or {}).get("authorizedEmptyLinks", [])
                      if a.get("rule")}
        unauthorized = sorted(empty_vl - authorized)
        if unauthorized:
            return False, (f"empty linkedGemaraLineIds on vilnaLine {unauthorized} without an "
                            "authorizedEmptyLinks entry citing a documented boundary rule")
    return True, ("two independent scans confirm zero citations anywhere in the raw Hebrew, "
                  "self-review attests every line was reread with no uncertainty")


def drift_ok_for_type(m_type, daf, prof, sr, entries=None):
    """Pure dispatch (file I/O limited to the one independent-scan read
    inside zero_anchor_safe; no git): does the post-edit drift profile
    satisfy this task type's merge bar? Returns (ok, extra_condition_key_
    or_None, note) where extra_condition_key_or_None is a SECOND
    condition name to add to the conditions dict (its own PASS/FAIL
    line) only when an evidence tier is what actually decided the
    outcome; note is an empty string when there is nothing to add."""
    cls = prof["classification"] if prof else "NO-PROFILE"
    if m_type == STRUCTURAL_TYPE:
        ok = bool(prof) and prof.get("haikuSafe", False)
        note = "" if ok else f"post-edit drift profile is {cls}, not haiku-safe"
        return ok, None, note
    if m_type in EVIDENCE_TIER_TYPES:
        n_anchors = len(prof.get("anchors", [])) if prof else -1
        if n_anchors >= 2:
            ok, reason = multi_anchor_safe(prof)
            note = "" if ok else (f"post-edit drift profile is {cls}, not ALIGNED, and does not "
                                   f"satisfy the multi-anchor evidence tier: {reason}")
            return ok, None, note
        if n_anchors == 1:
            ok, reason = one_anchor_safe(prof, sr)
            if ok:
                return True, "one-anchor-safe", (
                    f"ONE-ANCHOR-SAFE: {reason} (classification remains {cls}, not relabeled ALIGNED)")
            return False, "one-anchor-safe", (
                f"post-edit drift profile is {cls}, not ALIGNED, and does not qualify for the "
                f"one-anchor-safe evidence tier: {reason}")
        if n_anchors == 0:
            ok, reason = zero_anchor_safe(daf, prof, sr, entries)
            if ok:
                return True, "zero-anchor-safe", (
                    f"ZERO-ANCHOR-SAFE: {reason} (classification remains {cls}, not relabeled ALIGNED)")
            return False, "zero-anchor-safe", (
                f"post-edit drift profile is {cls}, not ALIGNED, and does not qualify for the "
                f"zero-anchor-safe evidence tier: {reason}")
        return False, None, "no drift profile available"
    ok = cls == "ALIGNED"
    note = "" if ok else f"post-edit drift profile is {cls}, not ALIGNED"
    return ok, None, note


def gather_review_conditions(m, spec, base):
    """Collect the machine-checkable auto-merge conditions for a conditional
    review task. Every check is read-only. Returns (conditions, notes)."""
    conditions = {k: False for k in REVIEW_CONDITIONS}
    notes = []
    targets = m.get("targets", [])
    conditions["single-target-manifest"] = len(targets) == 1
    if len(targets) != 1:
        notes.append(f"manifest carries {len(targets)} targets; conditional review is one daf per PR")
        return conditions, notes
    target = targets[0]

    # Structural repair exists to restore 1:1 raw correspondence: entry
    # count and vilnaLine sequence must match the authoritative source
    # exactly after the pass. Computed before any git dependency so the
    # condition is always present and valued for structural manifests.
    if m["type"] == STRUCTURAL_TYPE:
        tpath = YROOT / "assets" / "talmuddev" / f"{target}.json"
        raw_n = len([l for l in json.loads(tpath.read_text()).get("rashi", []) if l and l.strip()])
        lp = YROOT / "assets" / "learning" / "yoma" / f"{target}.learning.json"
        ent = json.loads(lp.read_text()).get("rashiTranslations", []) if lp.exists() else []
        seq_ok = [e.get("vilnaLine") for e in ent] == list(range(1, raw_n + 1))
        conditions["entry-count-and-order-match-raw"] = len(ent) == raw_n and seq_ok
        if not (len(ent) == raw_n and seq_ok):
            notes.append(f"rashiTranslations {len(ent)} entries vs {raw_n} raw lines "
                         f"(sequence {'ok' if seq_ok else 'broken'})")

    mb = sh(["git", "merge-base", base, "HEAD"]).stdout.strip()
    if not mb:
        notes.append(f"cannot resolve merge-base of {base!r}")
        return conditions, notes
    changed = [l for l in sh(["git", "diff", "--name-only", mb]).stdout.splitlines() if l.strip()]

    learn_changed = [p for p in changed
                     if p.startswith("modules/yoma/assets/learning/") and p.endswith(".learning.json")]
    expected = f"modules/yoma/assets/learning/yoma/{target}.learning.json"
    conditions["exactly-one-authorized-daf-changed"] = learn_changed == [expected]
    if learn_changed != [expected]:
        notes.append(f"learning JSONs changed: {learn_changed or 'none'} (expected exactly [{expected}])")

    # Scope: structure, Hebrew, forbidden fields, file set (reuses the
    # hard Rashi validator via cmd_scope semantics). Structure relaxation
    # exists ONLY for an explicitly authorized structural-repair manifest.
    scope_cmd = [sys.executable, "scripts/check_rashi_pr_scope.py", "--base", base]
    if structure_authorized(m, spec):
        scope_cmd.append("--allow-structure")
    r = sh(scope_cmd, cwd=YROOT)
    conditions["scope-clean-no-structure-no-hebrew-no-forbidden-fields"] = r.returncode == 0
    if r.returncode != 0:
        notes.append("check_rashi_pr_scope failed:\n" + r.stdout[-800:])

    # Allowlist delta: additions are forbidden anywhere; removals only on
    # the target daf (a removal that survives the content gate green was by
    # definition validator-stale, since the gate re-derives violations).
    added, foreign_removed = [], []
    for p in sorted((YSCRIPTS / "allowlists").glob("*.json")):
        rel = p.relative_to(REPO).as_posix()
        rr = sh(["git", "show", f"{mb}:{rel}"])
        old = json.loads(rr.stdout) if rr.returncode == 0 else {}
        new = json.loads(p.read_text())
        for section in ("entries", "count_mismatches"):
            oe = {json.dumps(e, sort_keys=True) for e in old.get(section, [])}
            ne = {json.dumps(e, sort_keys=True) for e in new.get(section, [])}
            added += [f"{rel}:{a}" for a in sorted(ne - oe)]
            for gone in sorted(oe - ne):
                if json.loads(gone).get("daf") != target:
                    foreign_removed.append(f"{rel}:{gone}")
    conditions["no-allowlist-additions"] = not added
    conditions["allowlist-removals-limited-to-target-daf"] = not foreign_removed
    for a in added:
        notes.append(f"allowlist entry ADDED: {a}")
    for g in foreign_removed:
        notes.append(f"allowlist entry removed outside target daf: {g}")

    # Packet completeness and link legality against the live segment table.
    sys.path.insert(0, str(YSCRIPTS))
    import make_rashi_work_packet as mrwp
    import audit_rashi_semantic as ars
    table = {s["id"] for s in mrwp.local_segments_for(target)}
    lpath = YROOT / "assets" / "learning" / "yoma" / f"{target}.learning.json"
    entries = json.loads(lpath.read_text()).get("rashiTranslations", []) if lpath.exists() else []
    used = {i for e in entries for i in e.get("linkedGemaraLineIds", [])}
    empty = [e["vilnaLine"] for e in entries if not e.get("linkedGemaraLineIds")]
    illegal = sorted(used - table)
    conditions["packet-contains-every-linked-local-id"] = bool(table) and not illegal
    conditions["all-links-legal-and-nonempty"] = bool(entries) and not illegal and not empty
    if illegal:
        notes.append(f"linked ids not in the packet segment table: {illegal}")
    if empty:
        notes.append(f"entries with empty linkedGemaraLineIds: {empty}")

    # Post-edit drift: realignment/reconstruction must restore full
    # alignment (ALIGNED, tightened to zero missing anchors and all
    # offsets exactly 0), or qualify for the one-anchor-safe or
    # zero-anchor-safe evidence tier (see drift_ok_for_type); structural
    # repair on an anchor-poor daf keeps its own, broader, unconditional
    # haiku-safe allowance. drift_ok_for_type never mutates the
    # classification itself and never accepts SHIFTED or
    # FABRICATION-SUSPECT.
    prof = ars.profile_daf(target, ars.load_allowlisted())
    sr_for_drift = None
    if SELF_REVIEW_PATH.exists():
        try:
            sr_for_drift = json.loads(SELF_REVIEW_PATH.read_text())
        except json.JSONDecodeError:
            sr_for_drift = None
    ok, extra_key, note = drift_ok_for_type(m["type"], target, prof, sr_for_drift, entries)
    conditions["drift-profile-ALIGNED"] = ok
    if extra_key:
        conditions[extra_key] = ok
    if note:
        notes.append(note)

    ra = sh([sys.executable, "scripts/audit_rashi_semantic.py", target], cwd=YROOT)
    conditions["semantic-audit-zero-shift-candidates"] = "0 shift candidate(s)" in ra.stdout
    if "0 shift candidate(s)" not in ra.stdout:
        notes.append("scoped semantic audit reports shift candidates on the target daf")

    stub = [e["vilnaLine"] for e in entries
            if re.search(r"Rashi line \d+|: continuation\.?$", e.get("en", ""))]
    seen, dupes = {}, []
    for e in entries:
        seen.setdefault(e.get("en", ""), []).append(e["vilnaLine"])
    dupes = {k[:40]: v for k, v in seen.items() if len(v) > 1 and k}
    conditions["no-stub-or-duplicate-helpers"] = not stub and not dupes
    if stub:
        notes.append(f"stub-pattern helpers remain on lines {stub}")
    if dupes:
        notes.append(f"duplicate helper English: {dupes}")

    fr = sh([sys.executable, "scripts/check_generated_freshness.py"], cwd=YROOT)
    conditions["generated-files-fresh"] = fr.returncode == 0

    version = (REPO / "VERSION").read_text().strip()
    pkg = json.loads((REPO / "package.json").read_text())["version"]
    lock = json.loads((REPO / "package-lock.json").read_text())["version"]
    conditions["version-metadata-synced"] = version == pkg == lock

    # Fresh post-edit self-review: the attestation must be part of THIS
    # PR's diff (that is what makes it fresh), name the target daf, tick
    # every required recheck, and report no blockers.
    sr_ok, why = False, ""
    if ".worker-self-review.json" not in changed:
        why = ".worker-self-review.json is not part of this PR's diff (a fresh post-edit self-review is required)"
    elif not SELF_REVIEW_PATH.exists():
        why = ".worker-self-review.json missing from the working tree"
    else:
        try:
            sr = json.loads(SELF_REVIEW_PATH.read_text())
            missing = [c for c in SELF_REVIEW_CHECKS if sr.get("rechecked", {}).get(c) is not True]
            if sr.get("daf") != target:
                why = f"self-review daf {sr.get('daf')!r} does not match target {target!r}"
            elif missing:
                why = f"self-review rechecks missing or false: {missing}"
            elif sr.get("blockersFound"):
                why = f"self-review reports blockers: {sr['blockersFound']}"
            else:
                sr_ok = True
        except json.JSONDecodeError as ex:
            why = f"self-review file unparseable: {ex}"
    conditions["fresh-self-review-committed-and-clean"] = sr_ok
    if not sr_ok:
        notes.append(why)

    return conditions, notes


def cmd_review(opts):
    """Conditional-review auto-merge gate. Exit 0 with AUTO-MERGE-ELIGIBLE
    only when every machine-checked condition passes; otherwise exit 1 with
    the exact failed conditions and the escalation target."""
    m, spec = load_manifest(opts.manifest)
    policy = review_policy_of(spec)
    if policy == "fable":
        print(f"REVIEW: task type {m['type']} requires unconditional Fable review; "
              "there is no auto-merge gate. Request Fable review and stop.")
        sys.exit(1)
    if policy != "conditional":
        print(f"REVIEW: task type {m['type']} has no review gate (policy: {policy}).")
        return
    base = resolve_base(opts.base)
    conditions, notes = gather_review_conditions(m, spec, base)
    eligible, failed = evaluate_review_policy(conditions)
    print(f"Conditional review gate (type {m['type']}, targets {m.get('targets')}, base {base}):\n")
    for k in conditions:
        print(f"  {'PASS' if conditions[k] else 'FAIL'}  {k}")
    for n in notes:
        print(f"  note: {n}")
    print("\nProcedural conditions (not observable here, still mandatory):")
    print("  - worker:verify --fast and --full both passed on this head")
    print("  - CI is green on the exact final head at merge time")
    if eligible:
        print("\nAUTO-MERGE-ELIGIBLE: all machine-checked conditions pass. Merge only "
              "when CI is green on this exact head; then verify both deploy workflows "
              "and advance the queue.")
    else:
        print(f"\nESCALATE to {spec.get('escalationModel', 'fable')}: failed condition(s) "
              f"{failed}. Do NOT merge.")
        sys.exit(1)


# ---------------- queue (sequential autopilot) ----------------

QUEUE_PATH = REPO / ".worker-queue.json"


def merged_manifest_evidence(override=None):
    """The last worker manifest MERGED to origin/main: the durable evidence
    queue progress derives from. Never reads the working tree (an unmerged
    manifest is not evidence). --evidence FILE overrides for tests."""
    if override:
        try:
            return json.loads(Path(override).read_text())
        except (OSError, json.JSONDecodeError):
            return {}
    sh(["git", "fetch", "origin", "main"])  # best-effort freshness
    r = sh(["git", "show", "origin/main:.worker-manifest.json"])
    if r.returncode != 0:
        return {}
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {}


def derive_queue_progress(q, evidence):
    """Pure derivation of (done, remaining) from the immutable queue
    definition and the merged-manifest evidence. Sequential-by-design: the
    evidence names the LAST merged target for this queue's type/module;
    under the enforced one-PR-per-target sequential process, everything at
    or before that index is complete. A manifest of another type/module, a
    target outside the queue, or a merely-local (unmerged) manifest never
    advances anything, so failed or escalated targets can never become
    done."""
    targets = q["targets"]
    if (evidence.get("type") == q["type"]
            and evidence.get("module") == q["module"]
            and len(evidence.get("targets", [])) == 1
            and evidence["targets"][0] in targets):
        i = targets.index(evidence["targets"][0])
        return targets[:i + 1], targets[i + 1:]
    return [], list(targets)


def cmd_queue(opts):
    """Sequential autopilot queue: ordered targets, one PR per target,
    merge+deploy verification between targets, stop-on-escalation.

    The tracked queue file is an IMMUTABLE definition (type, module,
    ordered targets, policy) committed once alongside the first target's
    manifest. Progress is DERIVED from merged-PR evidence (the manifest at
    origin/main), never stored: there is no runtime state to mutate, so
    completing the final target leaves a clean tree and nothing ever needs
    a direct push to main. Resuming after a container or session recycle
    needs only a fresh clone: derivation is a pure function of the
    definition and origin/main."""
    qpath = Path(opts.file) if opts.file else QUEUE_PATH
    if opts.advance:
        sys.exit("ERROR: --advance is retired. Queue progress is derived from merged PR "
                 "evidence (origin/main:.worker-manifest.json); there is no runtime state "
                 "to mutate, no completion commit, and never a direct push to main.")
    if opts.targets:
        if not opts.type:
            sys.exit("ERROR: queue creation requires --type")
        types = load_registry()
        if opts.type not in types:
            sys.exit(f"ERROR: unknown task type {opts.type!r}")
        targets = [t.strip() for t in opts.targets.split(",") if t.strip()]
        for t in targets:
            if not (YROOT / "assets" / "talmuddev" / f"{t}.json").exists():
                sys.exit(f"ERROR: {t}: no talmuddev source")
        q = {"type": opts.type, "module": opts.module, "targets": targets,
             "policy": "stop-on-escalation"}
        qpath.write_text(json.dumps(q, indent=1) + "\n")
        print(f"queue definition written to {qpath}: {len(targets)} target(s), one PR per "
              "target, sequential merge+deploy, stop-on-escalation. Commit it with the "
              "FIRST target's manifest commit; it is immutable afterward (progress is "
              "derived from merged PRs, never written back).")
        return
    if not qpath.exists():
        sys.exit(f"ERROR: no queue at {qpath}; create one with --type/--targets")
    q = json.loads(qpath.read_text())
    done, remaining = derive_queue_progress(q, merged_manifest_evidence(opts.evidence))
    print(f"queue: type {q['type']}, module {q['module']}, policy {q['policy']}")
    print(f"done (derived from merged PRs): {done or 'none'} | remaining: {remaining or 'none'}")
    if remaining:
        nxt = remaining[0]
        print(f"\nNext target: {nxt}. One PR for this daf only. Before starting, verify the")
        print("previous merge's deploy workflows are green, then run the read-only capability")
        print("scan across the remaining queue once per campaign (not per daf) to catch any")
        print("unsupported anchor-cardinality or packet-completeness state before content work:")
        print(f"  npm run worker:capability-scan -- --targets {','.join(remaining)}")
        print("If it reports UNSUPPORTED for any target, stop and escalate; do not edit content")
        print("for that daf until the tooling gap is resolved. Otherwise, command sequence:")
        print(f"  npm run worker:manifest -- --type {q['type']} --module {q['module']} "
              f"--range {nxt} --out .worker-manifest.json")
        print("  npm run worker:preflight -- --manifest .worker-manifest.json")
        print("  npm run worker:packet -- --manifest .worker-manifest.json")
        print("  npm run worker:prompt -- --manifest .worker-manifest.json")
        print("  (edit, regenerate, VERSION bump, self-review, verify --fast/--full, PR, CI)")
        print("  npm run worker:review -- --manifest .worker-manifest.json")
        print("  (merge when eligible AND CI green; verify all deploy workflows; then rerun")
        print("   npm run worker:queue, and progress advances automatically from the merge)")
        print("Stop the queue on ANY escalation condition; do not continue past it.")
    else:
        print("\nQueue complete. No queue-state commit is needed and the tree stays clean:")
        print("completion is derived from merged PR evidence, never pushed to main.")


# ---------------- capability-scan ----------------

def capability_report_for(daf):
    """Read-only per-daf capability assessment: never edits content.
    Classifies the daf's raw Hebrew by anchor cardinality (ZERO, ONE,
    MULTI), confirms packet/local-segment completeness, and states
    whether the current review-gate tiers can represent a legitimate
    AUTO-MERGE-ELIGIBLE final state for it. Returns a plain dict (JSON-
    serializable) so a whole queue's results can be reported together."""
    sys.path.insert(0, str(YSCRIPTS))
    import make_rashi_work_packet as mrwp
    import audit_rashi_semantic as ars

    tpath = YROOT / "assets" / "talmuddev" / f"{daf}.json"
    lpath = YROOT / "assets" / "learning" / "yoma" / f"{daf}.learning.json"
    entry = {"daf": daf, "supported": False, "issues": []}
    if not tpath.exists():
        entry["issues"].append("no talmuddev source")
        return entry
    if not lpath.exists():
        entry["issues"].append("no learning JSON")
        return entry

    try:
        raw = [l for l in json.loads(tpath.read_text()).get("rashi", []) if l and l.strip()]
    except json.JSONDecodeError as ex:
        entry["issues"].append(f"talmuddev source unparseable: {ex}")
        return entry
    try:
        trans = json.loads(lpath.read_text()).get("rashiTranslations", [])
    except json.JSONDecodeError as ex:
        entry["issues"].append(f"learning JSON unparseable: {ex}")
        return entry

    entry["rawCount"] = len(raw)
    entry["translationCount"] = len(trans)
    if len(raw) != len(trans):
        entry["issues"].append(f"raw count {len(raw)} != translation count {len(trans)}")
    seq_ok = [e.get("vilnaLine") for e in trans] == list(range(1, len(raw) + 1))
    entry["sequenceOk"] = seq_ok
    if not seq_ok:
        entry["issues"].append("vilnaLine sequence does not match 1..raw count")

    try:
        segs = mrwp.local_segments_for(daf)
        entry["localSegmentIds"] = len(segs)
        empty_he = [s["id"] for s in segs if not (s.get("he") or "").strip()]
        if empty_he:
            entry["issues"].append(f"local segment(s) with empty Hebrew text: {empty_he}")
        if not segs:
            entry["issues"].append("zero local segment ids (packet cannot anchor any link)")
    except Exception as ex:  # noqa: BLE001 - report, never crash the scan
        entry["issues"].append(f"packet/local-segment extraction failed: {ex}")

    prof = ars.profile_daf(daf, ars.load_allowlisted())
    if not prof:
        entry["issues"].append("no drift profile available")
        return entry
    n_anchors = len(prof.get("anchors", []))
    entry["classification"] = prof["classification"]
    entry["anchorCount"] = n_anchors
    entry["anchorsFound"] = prof.get("anchorsFound")
    entry["anchorsMissing"] = prof.get("anchorsMissing")
    entry["cardinality"] = "ZERO" if n_anchors == 0 else ("ONE" if n_anchors == 1 else "MULTI")

    if prof["classification"] == "SHIFTED":
        entry["issues"].append("current profile is SHIFTED (needs rashi-realignment content work first)")
    elif prof["classification"] == "FABRICATION-SUSPECT":
        entry["issues"].append("current profile is FABRICATION-SUSPECT (needs rashi-reconstruction "
                                "content work first)")

    if entry["cardinality"] == "ZERO":
        scan_ok, scan_detail = independent_zero_citation_scan(daf)
        entry["independentZeroScan"] = scan_detail
        if not scan_ok:
            entry["issues"].append(f"independent second scan disagrees with ZERO cardinality: "
                                    f"{scan_detail}")

    entry["supportedFinalStates"] = {
        "ZERO": "zero-anchor-safe (requires full-daf self-review attestation)",
        "ONE": "one-anchor-safe (requires one-anchor self-review attestation)",
        "MULTI": "multi-anchor-safe (requires ALIGNED, zero missing, all offsets 0)",
    }[entry["cardinality"]]
    entry["supported"] = not any(
        "unparseable" in i or "no talmuddev" in i or "no learning JSON" in i
        or "no drift profile" in i or "empty Hebrew text" in i
        or "zero local segment ids" in i or "independent second scan disagrees" in i
        for i in entry["issues"])
    return entry


def cmd_capability_scan(opts):
    """Read-only preflight over an entire target list (or the tracked
    queue): classifies every daf by anchor cardinality, confirms packet
    and local-segment completeness, and states whether the review-gate
    evidence tiers can represent a legitimate final state for it. Never
    edits content. Exits 1 if any target is unsupported, so a campaign
    can be blocked before the first content PR rather than discovering a
    tooling gap mid-queue."""
    if opts.targets:
        targets = [t.strip() for t in opts.targets.split(",") if t.strip()]
    else:
        qpath = Path(opts.file) if opts.file else QUEUE_PATH
        if not qpath.exists():
            sys.exit(f"ERROR: no --targets given and no queue at {qpath}")
        targets = json.loads(qpath.read_text())["targets"]

    report = [capability_report_for(d) for d in targets]
    unsupported = [r for r in report if not r["supported"]]

    print(f"Campaign capability scan ({len(targets)} target(s)):\n")
    for r in report:
        status = "OK" if r["supported"] else "UNSUPPORTED"
        card = r.get("cardinality", "?")
        print(f"  {status:11s} {r['daf']:6s} cardinality={card:5s} "
              f"raw={r.get('rawCount', '?')} trans={r.get('translationCount', '?')} "
              f"segIds={r.get('localSegmentIds', '?')} class={r.get('classification', '?')}")
        for issue in r["issues"]:
            print(f"               note: {issue}")

    if opts.json:
        print("\n" + json.dumps(report, indent=1))

    if unsupported:
        print(f"\n{len(unsupported)} unsupported target(s): {[r['daf'] for r in unsupported]}")
        print("FAILED: campaign cannot represent a legitimate final state for every target above.")
        sys.exit(1)
    print(f"\nOK: all {len(targets)} target(s) can reach a supported final review-gate state "
          "(ZERO/ONE/MULTI anchor cardinality all covered).")


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
            owners += ["rashi-repair", "rashi-reconstruction", "rashi-realignment", "placeholder-backfill"]
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
        pol = review_policy_of(s)
        pol_txt = {"fable": "; Fable review required",
                   "conditional": f"; review: conditional auto-merge gate (worker self-review "
                                  f"+ worker:review; escalation to {s.get('escalationModel', 'fable')})",
                   "none": ""}[pol]
        L.append(f"- model: {s['model']}"
                 + ("; PAUSED" if s.get("paused") else "")
                 + pol_txt)
        L.append(f"- haiku allowed: {'yes' if s.get('haikuAllowed') or s.get('model') in ('haiku', 'haiku-with-fable-review') else 'no'}")
        L.append(f"- max batch: {s.get('maxBatch', 1 if s.get('requiresTarget') else 'n/a')}")
        if s.get("requiredAuthorizations"):
            L.append(f"- REQUIRED authorization: {', '.join(s['requiredAuthorizations'])} "
                     f"(Fable-issued; preflight fails without it)")
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
        "reviewPolicy": review_policy_of(spec),
        "selfReviewRecorded": SELF_REVIEW_PATH.exists(),
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

    p = sub.add_parser("review")
    p.add_argument("--manifest", default=str(MANIFEST_DEFAULT))
    p.add_argument("--base", default=None)

    p = sub.add_parser("queue")
    p.add_argument("--type", default=None)
    p.add_argument("--module", default="yoma")
    p.add_argument("--targets", default=None,
                   help="comma-separated ordered daf list; creates/overwrites the queue")
    p.add_argument("--advance", default=None,
                   help="RETIRED: progress derives from merged PR evidence; this flag only errors")
    p.add_argument("--file", default=None, help="queue file path (default .worker-queue.json)")
    p.add_argument("--evidence", default=None,
                   help="test override: read merged-manifest evidence from FILE instead of origin/main")

    p = sub.add_parser("capability-scan")
    p.add_argument("--targets", default=None,
                   help="comma-separated daf list; defaults to the tracked queue's targets")
    p.add_argument("--file", default=None, help="queue file path (default .worker-queue.json)")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("report")
    p.add_argument("--manifest", default=str(MANIFEST_DEFAULT))

    p = sub.add_parser("schema-matrix")
    p.add_argument("--print", dest="print_matrix", action="store_true")

    sub.add_parser("docs")

    opts = ap.parse_args()
    {"manifest": cmd_manifest, "preflight": cmd_preflight, "packet": cmd_packet,
     "prompt": cmd_prompt, "verify": cmd_verify, "scope": cmd_scope,
     "ci-check": cmd_ci_check, "report": cmd_report, "review": cmd_review,
     "queue": cmd_queue, "capability-scan": cmd_capability_scan,
     "schema-matrix": cmd_schema_matrix, "docs": cmd_docs}[opts.cmd](opts)


if __name__ == "__main__":
    main()
