#!/usr/bin/env python3
"""
validate_rashi_review_records.py - Rashi translation-quality campaign,
Step 6 (tooling built ahead of time in Step 5): enforces the review-record
contract (docs/reports/data/rashi-review-record-contract.json) against a
batch's review-record file.

Expected input file shape:
  {
    "batchId": "step6-batch-NNN",
    "records": [ <one object per reviewed entry, per the contract> ... ],
    "totals": { "batchId", "reviewedCount", "dispositionCounts",
                "changedCount", "secondPassCounts", "blindQASampleSize",
                "blindQAEscalationCount" }
  }

Every rejection rule in the contract's "rejectionRules" section is
implemented here, each with an exact, attributable error message (record
index and entryId, never a bare "invalid"). This script assigns nothing -
it only proves a set of already-written records is internally consistent,
consistent with the live corpus/inventory, and consistent with its own
declared batch.

A real batch PR bundles the content edit (the changed entries' `en` in
`assets/learning/<module>/<daf>.learning.json` and the regenerated
`learning_data.js`/inventory) together with this review-record file, per
the campaign's established one-PR-per-batch convention. By the time this
validator runs in that PR's own CI, the live inventory already reflects
the NEW English for every changed entry - so `hebrew`/`originalEnglish`
immutability cannot be checked against the live working tree the way
`entryId`/`daf` structural checks can. Matching the exact pattern every
other campaign validator already uses (`check_rashi_pr_scope.py`'s
`git_show(base_rev, path)`), `--base` compares those two fields against
the inventory as it stood at the base ref instead - the only comparison
that can actually distinguish "this batch legitimately changed this
field" from "this field was corrupted." Omitting `--base` falls back to
the live working-tree file (useful for a quick sanity check before any
content edit has been applied, e.g. validating a still-UNREVIEWED
skeleton record set), but a batch PR whose content edit has already
landed should always pass `--base`.

Usage:
  python3 scripts/validate_rashi_review_records.py <records-file.json>
  python3 scripts/validate_rashi_review_records.py <records-file.json> --base origin/main
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).parent
ROOT = SCRIPTS.parent
REPO_ROOT = ROOT.parent.parent
DATA_DIR = REPO_ROOT / "docs" / "reports" / "data"
INVENTORY_PATH = DATA_DIR / "rashi-translation-quality-inventory.json"
BATCHES_PATH = DATA_DIR / "rashi-full-corpus-review-batches.json"
INVENTORY_REL = "docs/reports/data/rashi-translation-quality-inventory.json"

DISPOSITIONS = {"VERIFIED", "MINOR_EDIT", "SUBSTANTIVE_REPAIR", "RETRANSLATE",
                "DUPLICATION_OR_CONTAMINATION", "BLOCKED"}
CHANGED_DISPOSITIONS = {"MINOR_EDIT", "SUBSTANTIVE_REPAIR", "RETRANSLATE", "DUPLICATION_OR_CONTAMINATION"}
DEFECT_TAGS = {
    "WRONG_MEANING", "OMITTED_TEXT", "INVENTED_TEXT", "WRONG_REFERENT", "WRONG_LOGIC",
    "WRONG_TECHNICAL_TERM", "HEBREW_LEFT_UNTRANSLATED", "ARAMAIC_LEFT_UNTRANSLATED", "GRAMMAR",
    "FRAGMENT", "OVERLITERAL", "OVEREXPLAINED", "DUPLICATED", "SHIFTED", "TRUNCATED",
    "CONTEXT_MISMATCH", "TERMINOLOGY_DRIFT", "PUNCTUATION", "STYLE_ONLY", "NEEDS_EXPERT_REVIEW",
}
SECOND_PASS_STATUSES = {"CONFIRMED", "MODIFIED", "REJECTED", "REMAINED_BLOCKED"}
GENERIC_BLOCKED_PHRASES = {"unclear", "not sure", "unknown", "tbd", "n/a", ""}


def fail(errors, idx, entry_id, msg):
    errors.append(f"record[{idx}] ({entry_id}): {msg}")


def git_show_inventory(base_ref):
    r = subprocess.run(["git", "show", f"{base_ref}:{INVENTORY_REL}"],
                        capture_output=True, text=True, cwd=REPO_ROOT)
    if r.returncode != 0:
        sys.exit(f"ERROR: cannot read {INVENTORY_REL!r} at {base_ref!r}: {r.stderr.strip()}")
    return json.loads(r.stdout)


def validate_records(doc, base_ref=None):
    errors = []
    batch_id = doc.get("batchId")
    records = doc.get("records", [])

    batches_doc = json.loads(BATCHES_PATH.read_text())
    batch_by_id = {b["batchId"]: b for b in batches_doc["batches"]}
    if batch_id not in batch_by_id:
        errors.append(f"unknown batchId {batch_id!r} - not present in {BATCHES_PATH.name}")
        return errors
    batch = batch_by_id[batch_id]
    batch_entry_ids = set(batch["entryIds"])

    inv = json.loads(INVENTORY_PATH.read_text())
    inv_by_id = {e["id"]: e for e in inv["entries"]}

    # hebrew/originalEnglish immutability is checked against the base ref when
    # given (the pre-batch state), since a batch PR's own live working tree
    # already carries the content edit this same file documents - see the
    # module docstring for why comparing against the live file would be
    # meaningless in that case.
    if base_ref:
        base_inv = git_show_inventory(base_ref)
        immutable_by_id = {e["id"]: e for e in base_inv["entries"]}
    else:
        immutable_by_id = inv_by_id

    seen_ids = set()
    for idx, r in enumerate(records):
        entry_id = r.get("entryId")
        if entry_id is None:
            fail(errors, idx, "?", "missing entryId")
            continue
        seen_ids.add(entry_id)

        if entry_id not in inv_by_id:
            fail(errors, idx, entry_id, "unknown entry: not present in the live translation-quality inventory")
            continue
        if entry_id not in batch_entry_ids:
            fail(errors, idx, entry_id, f"outside batch: not listed in {batch_id}'s own entryIds")
        live = inv_by_id[entry_id]
        immutable = immutable_by_id.get(entry_id, live)

        if r.get("daf") != live["daf"]:
            fail(errors, idx, entry_id, f"daf mismatch: record says {r.get('daf')!r}, live inventory says {live['daf']!r}")

        if r.get("hebrew") != immutable["he"]:
            fail(errors, idx, entry_id, "immutable-field change: hebrew differs from the corpus value")

        if r.get("originalEnglish") != immutable["en"]:
            fail(errors, idx, entry_id, "immutable-field change: originalEnglish differs from the live pre-batch corpus value")

        first_disp = r.get("firstPassDisposition")
        if first_disp not in DISPOSITIONS:
            fail(errors, idx, entry_id, f"missing/unsupported firstPassDisposition: {first_disp!r}")
            first_disp = None

        tags = r.get("defectTags", [])
        if not isinstance(tags, list) or any(t not in DEFECT_TAGS for t in tags):
            fail(errors, idx, entry_id, f"unsupported defect tag(s): {tags!r}")
        if first_disp == "VERIFIED" and tags:
            fail(errors, idx, entry_id, "VERIFIED record carries non-empty defectTags")

        evidence = r.get("firstPassEvidence")
        if first_disp and first_disp != "VERIFIED" and not evidence:
            fail(errors, idx, entry_id, "missing firstPassEvidence for a non-VERIFIED firstPassDisposition")

        second = r.get("secondPass", {})
        needs_second = first_disp in CHANGED_DISPOSITIONS or first_disp == "BLOCKED"
        sp_status = second.get("status")
        if needs_second:
            if sp_status not in SECOND_PASS_STATUSES:
                fail(errors, idx, entry_id, f"missing/unsupported secondPass.status for firstPassDisposition {first_disp}: {sp_status!r}")
            if sp_status and not second.get("evidence"):
                fail(errors, idx, entry_id, "secondPass.status set but secondPass.evidence is empty")
        elif sp_status is not None:
            fail(errors, idx, entry_id, f"secondPass.status set ({sp_status!r}) but firstPassDisposition {first_disp} does not require a second pass")

        final_disp = r.get("finalDisposition")
        if final_disp not in DISPOSITIONS:
            fail(errors, idx, entry_id, f"missing/unsupported finalDisposition: {final_disp!r}")
            final_disp = None

        # proposedEnglish nullness is governed entirely by finalDisposition (the contract's own
        # rule: "must be null when finalDisposition is VERIFIED or BLOCKED"), not by
        # firstPassDisposition. A second pass can legitimately move a changed firstPassDisposition
        # to a VERIFIED or BLOCKED finalDisposition two different ways - REJECTED (the proposal
        # didn't hold, entry reverts to VERIFIED) or REMAINED_BLOCKED (the finding stands but
        # applying it is blocked by something outside the entry's own English, e.g. a corpus-wide
        # gate the finding's task type cannot itself authorize) - and in either case a live
        # proposedEnglish would misrepresent the record as an unresolved, still-pending change.
        # Both checks key off final_disp for exactly this reason, not off first_disp.
        proposed = r.get("proposedEnglish")
        if final_disp in CHANGED_DISPOSITIONS and not proposed:
            fail(errors, idx, entry_id, f"missing proposedEnglish for finalDisposition {final_disp}")
        if final_disp in ("VERIFIED", "BLOCKED") and proposed is not None:
            fail(errors, idx, entry_id, f"proposedEnglish set but finalDisposition is {final_disp} (must be null)")
        if proposed is not None and proposed == r.get("originalEnglish"):
            fail(errors, idx, entry_id, "proposedEnglish is identical to originalEnglish (not a real change)")

        final_english = second.get("finalEnglish") or proposed
        changed_from_original = final_english is not None and final_english != r.get("originalEnglish")
        if changed_from_original and sp_status not in ("CONFIRMED", "MODIFIED"):
            fail(errors, idx, entry_id,
                 "changed English without second-pass confirmation: English differs from originalEnglish "
                 f"but secondPass.status is {sp_status!r}, not CONFIRMED or MODIFIED")

        if final_disp == "BLOCKED":
            stop = (r.get("structuralStop") or "").strip().lower()
            if stop in GENERIC_BLOCKED_PHRASES:
                fail(errors, idx, entry_id, "BLOCKED without a specific evidence gap (structuralStop is empty or generic)")
        elif r.get("structuralStop"):
            fail(errors, idx, entry_id, "structuralStop set but finalDisposition is not BLOCKED")

        blind = r.get("blindQA", {})
        if blind.get("selected") and first_disp != "VERIFIED":
            fail(errors, idx, entry_id, "blindQA.selected is true but firstPassDisposition is not VERIFIED")
        if blind.get("result") and not blind.get("selected"):
            fail(errors, idx, entry_id, "blindQA.result set but blindQA.selected is false")
        if blind.get("result") == "ESCALATED" and final_disp == "VERIFIED":
            fail(errors, idx, entry_id, "blindQA.result is ESCALATED but finalDisposition is still VERIFIED")

    dup = {eid for eid in seen_ids if sum(1 for r in records if r.get("entryId") == eid) > 1}
    for eid in sorted(dup):
        errors.append(f"duplicate record for entryId {eid} within {batch_id}")

    # totals cross-check
    totals = doc.get("totals")
    if totals:
        from collections import Counter
        actual_disp = Counter(r.get("finalDisposition") for r in records)
        claimed_disp = totals.get("dispositionCounts", {})
        for k in set(actual_disp) | set(claimed_disp):
            if actual_disp.get(k, 0) != claimed_disp.get(k, 0):
                errors.append(f"totals mismatch: dispositionCounts[{k}] claims {claimed_disp.get(k, 0)}, actual {actual_disp.get(k, 0)}")
        if totals.get("reviewedCount") != len(records):
            errors.append(f"totals mismatch: reviewedCount claims {totals.get('reviewedCount')}, actual {len(records)}")
        actual_changed = sum(1 for r in records if r.get("finalDisposition") in CHANGED_DISPOSITIONS)
        if totals.get("changedCount") != actual_changed:
            errors.append(f"totals mismatch: changedCount claims {totals.get('changedCount')}, actual {actual_changed}")

    return errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("records_file")
    ap.add_argument("--base", default=None,
                     help="base ref for hebrew/originalEnglish immutability (e.g. origin/main); "
                          "omit to compare against the live working tree instead")
    opts = ap.parse_args()

    base = opts.base
    if base is None:
        env_base = os.environ.get("GITHUB_BASE_REF", "").strip()
        base = f"origin/{env_base}" if env_base else None

    doc = json.loads(Path(opts.records_file).read_text())
    errors = validate_records(doc, base_ref=base)
    if errors:
        print(f"Review-record validation FAILED ({len(errors)} violation(s)):\n")
        for e in errors:
            print(f"  ERROR  {e}")
        return 1
    print(f"OK: {len(doc.get('records', []))} review record(s) in {doc.get('batchId')} valid against the contract.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
