#!/usr/bin/env python3
"""
validate_rashi_boundary_authorizations.py - gate for the boundary
(empty-linkedGemaraLineIds) authorization registry.

A "boundary" entry is a rashiTranslations entry whose linkedGemaraLineIds is
empty (the same entry_category audit_rashi_association.py calls "boundary").
This registry (allowlists/rashi_boundary_authorizations.json) is the only
mechanism by which such an entry is allowed to stay unlinked: every boundary
entry currently in the corpus must have a matching, current authorization,
and every authorization must describe a real, currently-boundary entry.

Fails on:
  1. an authorization for an entry that is NOT currently empty-linked
     (the underlying work was done and the authorization was never retired)
  2. a boundary entry in the corpus with no matching authorization
  3. a stale authorization (the entry's "en" text has changed since the
     enFingerprint was recorded - the reasoning may no longer apply)
  4. a duplicate authorization (same daf+vilnaLine appears twice)
  5. an authorization whose daf or vilnaLine does not exist at all
  6. registry growth beyond MAX_AUTHORIZED_ENTRIES (the current, real
     count of 20). Raising this ratchet is only valid inside an explicitly
     scoped docs-tooling PR that also documents the newly authorized
     entries - it is never bumped as an incidental part of unrelated work.

Offline, no network. Exit 1 on any failure.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
LEARN_DIR = ROOT / "assets" / "learning" / "yoma"
REGISTRY = Path(__file__).parent / "allowlists" / "rashi_boundary_authorizations.json"

MAX_AUTHORIZED_ENTRIES = 20


def fingerprint(en_text):
    return hashlib.sha256(en_text.encode("utf-8")).hexdigest()[:16]


def load_corpus():
    """Return dict (daf, vilnaLine) -> en text, for every rashiTranslations
    entry across the corpus (empty-linked or not)."""
    corpus = {}
    for path in sorted(LEARN_DIR.glob("*.learning.json")):
        daf = path.name.replace(".learning.json", "")
        trans = json.loads(path.read_text(encoding="utf-8")).get("rashiTranslations", [])
        for e in trans:
            corpus[(daf, e["vilnaLine"])] = e
    return corpus


def validate(entries, corpus, max_authorized_entries=MAX_AUTHORIZED_ENTRIES):
    """Pure validation: entries is the registry's entries[] list, corpus is
    a dict (daf, vilnaLine) -> {"linkedGemaraLineIds": [...], "en": "..."}
    for every rashiTranslations entry in scope (empty-linked or not).
    Returns a list of error strings (empty means valid). Kept separate from
    main()'s disk I/O so it can be unit-tested against synthetic fixtures:
    see test_validate_rashi_boundary_authorizations.py.
    """
    boundary_keys = {
        key for key, e in corpus.items() if not e.get("linkedGemaraLineIds")
    }

    errors = []

    if len(entries) > max_authorized_entries:
        errors.append(
            f"registry has grown to {len(entries)} entries, beyond the "
            f"MAX_AUTHORIZED_ENTRIES ratchet of {max_authorized_entries}. "
            f"Raising this ratchet is only valid inside an explicitly scoped "
            f"docs-tooling PR that documents the newly authorized entries."
        )

    seen_keys = set()
    authorized_keys = set()
    for entry in entries:
        daf = entry.get("daf")
        vl = entry.get("vilnaLine")
        key = (daf, vl)
        label = f"{daf} L{vl}"

        if key in seen_keys:
            errors.append(f"{label}: duplicate authorization (already appears earlier in the registry)")
            continue
        seen_keys.add(key)

        if key not in corpus:
            errors.append(f"{label}: authorization references a daf/vilnaLine that does not exist in the corpus")
            continue

        authorized_keys.add(key)
        live_entry = corpus[key]

        if live_entry.get("linkedGemaraLineIds"):
            errors.append(
                f"{label}: authorization exists for an entry that is no longer empty-linked "
                f"(linkedGemaraLineIds={live_entry['linkedGemaraLineIds']!r}); retire this authorization"
            )
            continue

        live_fp = fingerprint(live_entry["en"])
        if entry.get("enFingerprint") != live_fp:
            errors.append(
                f"{label}: stale authorization - recorded enFingerprint "
                f"{entry.get('enFingerprint')!r} does not match the current text's "
                f"fingerprint {live_fp!r}; re-verify and re-authorize"
            )

    missing = sorted(boundary_keys - authorized_keys)
    for daf, vl in missing:
        errors.append(f"{daf} L{vl}: boundary (empty-linked) entry has no authorization in the registry")

    return errors


def main():
    if not REGISTRY.exists():
        sys.exit(f"ERROR: {REGISTRY} not found.")

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    entries = registry.get("entries", [])
    corpus = load_corpus()
    boundary_count = sum(1 for e in corpus.values() if not e.get("linkedGemaraLineIds"))

    errors = validate(entries, corpus)

    if errors:
        print("Boundary authorization validation FAILED:\n")
        for e in errors:
            print(f"  ERROR  {e}")
        print(f"\n{len(errors)} error(s).")
        sys.exit(1)

    print(
        f"OK: boundary authorization registry valid - {len(entries)} authorized entries, "
        f"{boundary_count} boundary entries in corpus, all matched, 0 stale, 0 duplicate, "
        f"0 unauthorized, ratchet {len(entries)}/{MAX_AUTHORIZED_ENTRIES}."
    )


if __name__ == "__main__":
    main()
