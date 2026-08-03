#!/usr/bin/env python3
"""
boundary_fingerprint_ratchet.py - identity-aware ratchet exception for
modules/<module>/scripts/allowlists/rashi_boundary_authorizations.json.

The generic allowlist ratchet (check_rashi_pr_scope.py's check_allowlist_ratchet
and worker_pipeline.py's allowlist_ratchet_inline) treats every allowlist file as
a remove-only SET of serialized-dict entries: anything present in the new state
but not the old is flagged as ADDED. That comparison is identity-blind - a
legitimate field-level edit to an EXISTING (daf, vilnaLine)-keyed entry changes
its full serialization, so it looks identical to "old entry silently removed,
brand-new entry added" under a plain set diff. For the boundary-authorizations
registry specifically, this makes it structurally impossible to ever refresh a
stale enFingerprint after a genuine, narrowly-authorized English repair to the
one Rashi entry that authorization covers.

This module is the SOLE place a registry record may be mutated in place. It:
  - identifies registry entries by (daf, vilnaLine), the registry's own existing
    de-duplication/lookup key (see validate_rashi_boundary_authorizations.py);
  - allows a record to be REMOVED at any time (existing behavior, unchanged -
    retiring an authorization once its entry is properly linked);
  - never allows a record to be ADDED (registry growth stays exclusively behind
    RASHI_ALLOWLIST_RESTRUCTURE=1, unchanged);
  - allows exactly one record to be REHASHED (its enFingerprint changed, every
    other field byte-identical) per PR, and only when all ten conditions in
    authorize_rehash() hold.

Both fingerprints are independently RECOMPUTED from the actual corpus English at
the base and head revisions - never trusted from the registry file, the
manifest, or the review record. A fingerprint is derived metadata; the gate
recomputes it rather than trusting a value supplied by the PR.

Imported directly by check_rashi_pr_scope.py (same directory) and dynamically
loaded by worker_pipeline.py (via importlib, since worker_pipeline.py's
YSCRIPTS is rebound per active module) so both callers share one
implementation instead of two independently-maintained ones.
"""
import hashlib
import json
import subprocess
from pathlib import Path

from validate_rashi_review_records import CHANGED_DISPOSITIONS

BOUNDARY_FILENAME = "rashi_boundary_authorizations.json"
REPAIR_TASK_TYPE = "rashi-boundary-translation-repair"
# Fields that are structural/rationale facts about an authorization, never
# derived metadata. Any change to one of these on an existing (daf, vilnaLine)
# record is illegal restructuring, not a fingerprint refresh.
NON_DERIVED_FIELDS = ("daf", "vilnaLine", "reason", "evidenceClassification", "boundaryRule")


def fingerprint(en_text):
    return hashlib.sha256(en_text.encode("utf-8")).hexdigest()[:16]


def _git_show(repo_root, rev, rel_path):
    r = subprocess.run(["git", "show", f"{rev}:{rel_path}"],
                        capture_output=True, text=True, cwd=repo_root)
    return r.stdout if r.returncode == 0 else None


def diff_registry_entries(old_entries, new_entries):
    """Identity-aware diff of the registry's entries[] list.
    Returns (old_by_id, new_by_id, added, removed, rehashed):
      added/removed: sorted list of (daf, vilnaLine) identities
      rehashed: sorted list of (daf, vilnaLine) identities present in both
        old and new whose serialized record differs (may be a legitimate
        fingerprint refresh, or may be illegal restructuring - the caller
        must run authorize_rehash to tell the difference)."""
    old_by_id = {(e.get("daf"), e.get("vilnaLine")): e for e in old_entries}
    new_by_id = {(e.get("daf"), e.get("vilnaLine")): e for e in new_entries}
    added = sorted(set(new_by_id) - set(old_by_id))
    removed = sorted(set(old_by_id) - set(new_by_id))
    rehashed = sorted(k for k in set(old_by_id) & set(new_by_id) if old_by_id[k] != new_by_id[k])
    return old_by_id, new_by_id, added, removed, rehashed


def _only_fingerprint_differs(old_entry, new_entry):
    for f in NON_DERIVED_FIELDS:
        if old_entry.get(f) != new_entry.get(f):
            return False
    return old_entry.get("enFingerprint") != new_entry.get("enFingerprint")


def _corpus_entry_at(repo_root, rev, learn_dir_rel, daf, vilna_line):
    """The full (daf, vilnaLine) rashiTranslations entry dict at `rev` (None
    means the live working tree). None if the daf file or the entry does not
    exist at that revision."""
    rel_path = f"{learn_dir_rel}/{daf}.learning.json"
    if rev is None:
        p = Path(repo_root) / rel_path
        text = p.read_text(encoding="utf-8") if p.exists() else None
    else:
        text = _git_show(repo_root, rev, rel_path)
    if text is None:
        return None
    try:
        doc = json.loads(text)
    except json.JSONDecodeError:
        return None
    for e in doc.get("rashiTranslations", []):
        if e.get("vilnaLine") == vilna_line:
            return e
    return None


def _corpus_en_at(repo_root, rev, learn_dir_rel, daf, vilna_line):
    """The `en` text of the (daf, vilnaLine) rashiTranslations entry at `rev`
    (None means the live working tree). None if the daf file or the entry
    does not exist at that revision."""
    entry = _corpus_entry_at(repo_root, rev, learn_dir_rel, daf, vilna_line)
    return entry.get("en") if entry is not None else None


def _corpus_daf_list(repo_root, rev, learn_dir_rel):
    if rev is None:
        d = Path(repo_root) / learn_dir_rel
        if not d.exists():
            return []
        return sorted(p.name.replace(".learning.json", "") for p in d.glob("*.learning.json"))
    r = subprocess.run(["git", "ls-tree", "-r", "--name-only", rev, "--", learn_dir_rel],
                        capture_output=True, text=True, cwd=repo_root)
    if r.returncode != 0:
        return []
    return sorted(Path(p).name.replace(".learning.json", "") for p in r.stdout.splitlines()
                  if p.endswith(".learning.json"))


def corpus_wide_en_diff(repo_root, base_rev, learn_dir_rel):
    """Every (daf, vilnaLine) whose rashiTranslations `en` text differs
    between base_rev and the live working tree, scanning the WHOLE corpus
    directly - not derived from `git diff --name-only`, so it is authoritative
    regardless of how the file-level diff is reported. This is condition 10:
    no other undeclared Rashi entry may change anywhere in the corpus."""
    dafs = sorted(set(_corpus_daf_list(repo_root, base_rev, learn_dir_rel)) |
                  set(_corpus_daf_list(repo_root, None, learn_dir_rel)))
    changed = []
    for daf in dafs:
        base_text = _git_show(repo_root, base_rev, f"{learn_dir_rel}/{daf}.learning.json")
        head_path = Path(repo_root) / learn_dir_rel / f"{daf}.learning.json"
        head_text = head_path.read_text(encoding="utf-8") if head_path.exists() else None
        base_doc = json.loads(base_text) if base_text else {"rashiTranslations": []}
        head_doc = json.loads(head_text) if head_text else {"rashiTranslations": []}
        base_en = {e["vilnaLine"]: e.get("en") for e in base_doc.get("rashiTranslations", [])}
        head_en = {e["vilnaLine"]: e.get("en") for e in head_doc.get("rashiTranslations", [])}
        for vl in sorted(set(base_en) | set(head_en)):
            if base_en.get(vl) != head_en.get(vl):
                changed.append((daf, vl))
    return changed


def authorize_rehash(repo_root, base_rev, learn_dir_rel, identity, old_entry, new_entry,
                      manifest_path, expected_module, review_record_dir="docs/reports/data"):
    """The ten-condition gate for a single rehashed (daf, vilnaLine) registry
    record. Returns (ok: bool, reason: str). Never trusts a fingerprint value
    from the manifest, the review record, or the new registry record itself -
    both the base and head fingerprints are independently recomputed from the
    actual corpus English at each revision."""
    daf, vilna_line = identity
    label = f"{daf} L{vilna_line}"

    # Condition 3 (and, trivially, 1/2: identity is the dict key both records
    # share, so it cannot itself have changed here).
    if not _only_fingerprint_differs(old_entry, new_entry):
        return False, (f"{label}: more than enFingerprint differs between the base and head "
                        f"registry records (identity, rationale, and structural fields must "
                        f"stay byte-identical for a fingerprint refresh)")

    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        return False, f"{label}: no .worker-manifest.json present to authorize a fingerprint refresh"
    try:
        m = json.loads(manifest_path.read_text())
    except json.JSONDecodeError:
        return False, f"{label}: .worker-manifest.json is not valid JSON"

    # Condition 7: the entry must be explicitly authorized by the CURRENT
    # worker task, via the one task type this mutation is scoped to.
    if m.get("type") != REPAIR_TASK_TYPE:
        return False, f"{label}: manifest type is {m.get('type')!r}, not {REPAIR_TASK_TYPE!r}"

    if m.get("module") != expected_module:
        return False, f"{label}: manifest module {m.get('module')!r} does not match {expected_module!r}"

    base_wm_text = _git_show(repo_root, base_rev, ".worker-manifest.json")
    if base_wm_text is not None and base_wm_text == manifest_path.read_text():
        return False, f"{label}: .worker-manifest.json is unchanged from base; a stale manifest cannot authorize anything"

    reg_id = m.get("registryIdentity") or {}
    if (reg_id.get("daf"), reg_id.get("vilnaLine")) != identity:
        return False, f"{label}: manifest registryIdentity {reg_id!r} does not match this rehashed entry"

    entry_id = m.get("entryId")
    if not entry_id or not isinstance(entry_id, str):
        return False, f"{label}: manifest is missing entryId"

    # Condition 8: the review record must identify the SAME entry and record
    # a second-pass-confirmed translation repair.
    review_rel = m.get("reviewRecordPath")
    if not review_rel or not isinstance(review_rel, str):
        return False, f"{label}: manifest is missing reviewRecordPath"
    review_rel_norm = review_rel.replace("\\", "/")
    if review_rel_norm.startswith("/") or ".." in Path(review_rel_norm).parts:
        return False, f"{label}: reviewRecordPath {review_rel!r} is not a safe repo-relative path"
    if not (review_rel_norm.startswith(f"{review_record_dir}/rashi-step6-batch-")
            and review_rel_norm.endswith("-review-records.json")):
        return False, f"{label}: reviewRecordPath {review_rel!r} is outside the review-record file family"
    review_path = Path(repo_root) / review_rel_norm
    if not review_path.exists():
        return False, f"{label}: reviewRecordPath {review_rel!r} does not exist"
    try:
        review_doc = json.loads(review_path.read_text())
    except json.JSONDecodeError:
        return False, f"{label}: reviewRecordPath {review_rel!r} is not valid JSON"
    record = next((r for r in review_doc.get("records", []) if r.get("entryId") == entry_id), None)
    if record is None:
        return False, f"{label}: no record for entryId {entry_id!r} in {review_rel!r}"
    if record.get("daf") != daf:
        return False, f"{label}: review record daf {record.get('daf')!r} does not match registry identity daf {daf!r}"
    second = record.get("secondPass") or {}
    if second.get("status") != "CONFIRMED":
        return False, f"{label}: review record secondPass.status is {second.get('status')!r}, not CONFIRMED"
    if record.get("finalDisposition") not in CHANGED_DISPOSITIONS:
        return False, (f"{label}: review record finalDisposition "
                        f"{record.get('finalDisposition')!r} is not a changed disposition")

    # Boundary status must not move: this type repairs the English of an
    # entry that stays unlinked, it never touches linkedGemaraLineIds.
    base_entry = _corpus_entry_at(repo_root, base_rev, learn_dir_rel, daf, vilna_line)
    head_entry = _corpus_entry_at(repo_root, None, learn_dir_rel, daf, vilna_line)
    if base_entry is None or head_entry is None:
        return False, f"{label}: cannot locate the corpus entry at the base and/or head revision"
    if base_entry.get("linkedGemaraLineIds") or head_entry.get("linkedGemaraLineIds"):
        return False, f"{label}: linkedGemaraLineIds must stay empty at both revisions (boundary status may not change)"
    if base_entry.get("linkedGemaraLineIds") != head_entry.get("linkedGemaraLineIds"):
        return False, f"{label}: linkedGemaraLineIds changed between base and head"

    # Conditions 4-6: recompute both fingerprints from the actual corpus
    # English at base and head - never trust the registry file, the
    # manifest, or the review record's own claimed values.
    base_en = base_entry.get("en")
    head_en = head_entry.get("en")
    if base_en == head_en:
        return False, f"{label}: English is unchanged between base and head; nothing to refresh a fingerprint for"

    recomputed_base_fp = fingerprint(base_en)
    recomputed_head_fp = fingerprint(head_en)
    if old_entry.get("enFingerprint") != recomputed_base_fp:
        return False, (f"{label}: base registry enFingerprint does not match the recomputed "
                        f"fingerprint of the base revision's actual English")
    if new_entry.get("enFingerprint") != recomputed_head_fp:
        return False, (f"{label}: new registry enFingerprint does not match the recomputed "
                        f"fingerprint of the head revision's actual English")
    if m.get("baseEnFingerprint") != recomputed_base_fp:
        return False, f"{label}: manifest baseEnFingerprint does not match the recomputed base fingerprint"
    if m.get("expectedNewEnFingerprint") != recomputed_head_fp:
        return False, f"{label}: manifest expectedNewEnFingerprint does not match the recomputed head fingerprint"

    # Condition 10: no other undeclared Rashi entry may change anywhere in
    # the corpus - scanned directly, not inferred from which files git
    # reports as changed.
    corpus_changes = corpus_wide_en_diff(repo_root, base_rev, learn_dir_rel)
    other = [c for c in corpus_changes if c != identity]
    if other:
        return False, (f"{label}: undeclared Rashi entry change(s) outside the authorized entry: "
                        f"{other}")
    if identity not in corpus_changes:
        return False, f"{label}: authorized entry's English did not actually change in the corpus"

    return True, (f"{label}: fingerprint refresh authorized by {REPAIR_TASK_TYPE} manifest "
                  f"+ CONFIRMED review record for {entry_id}")
