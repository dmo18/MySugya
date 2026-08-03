#!/usr/bin/env python3
"""
test_validate_rashi_review_records.py - regression tests for
validate_rashi_review_records.py: proves the validator actually enforces
every rejection rule in the Step 5 review-record contract
(docs/reports/data/rashi-review-record-contract.json), not just that it
accepts well-formed input. Each check below builds a single-field
violation against an otherwise-valid record and asserts the validator's
error list is non-empty and names the right field - the same
injection-testing pattern used by test_plan_rashi_full_corpus_batches.py
for the batch planner.

Offline, no network. Run from modules/yoma/:
  python3 scripts/test_validate_rashi_review_records.py
"""
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).parent
ROOT = SCRIPTS.parent
REPO_ROOT = ROOT.parent.parent
DATA_DIR = REPO_ROOT / "docs" / "reports" / "data"
INVENTORY_PATH = DATA_DIR / "rashi-translation-quality-inventory.json"
BATCHES_PATH = DATA_DIR / "rashi-full-corpus-review-batches.json"

sys.path.insert(0, str(SCRIPTS))
from validate_rashi_review_records import validate_records, git_show_inventory  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    print(f"  {'ok ' if cond else 'FAIL'} {name}" + (f" ({detail})" if detail and not cond else ""))
    if not cond:
        FAILED.append(name)


def errors_mentioning(errors, substr):
    return [e for e in errors if substr in e]


inv = json.loads(INVENTORY_PATH.read_text())
inv_by_id = {e["id"]: e for e in inv["entries"]}
batches_doc = json.loads(BATCHES_PATH.read_text())
batch = batches_doc["batches"][0]
batch_id = batch["batchId"]
other_batch = batches_doc["batches"][1]

entry_id = batch["entryIds"][0]
live = inv_by_id[entry_id]


def verified_record(eid=entry_id):
    e = inv_by_id[eid]
    return {
        "batchId": batch_id, "entryId": eid, "daf": e["daf"],
        "hebrew": e["he"], "originalEnglish": e["en"], "proposedEnglish": None,
        "firstPassDisposition": "VERIFIED", "defectTags": [], "firstPassEvidence": None,
        "secondPass": {"required": False, "status": None, "evidence": None, "finalEnglish": None},
        "blindQA": {"selected": False, "result": None, "evidence": None},
        "finalDisposition": "VERIFIED", "structuralStop": None, "repairPR": None, "finalVerificationSHA": None,
    }


def changed_record(eid=entry_id):
    e = inv_by_id[eid]
    proposed = e["en"] + " (comma inserted)"
    return {
        "batchId": batch_id, "entryId": eid, "daf": e["daf"],
        "hebrew": e["he"], "originalEnglish": e["en"], "proposedEnglish": proposed,
        "firstPassDisposition": "MINOR_EDIT", "defectTags": ["PUNCTUATION"],
        "firstPassEvidence": "missing comma before the relative clause",
        "secondPass": {"required": True, "status": "CONFIRMED",
                       "evidence": "independently re-read, comma correctly restores the clause boundary",
                       "finalEnglish": proposed},
        "blindQA": {"selected": False, "result": None, "evidence": None},
        "finalDisposition": "MINOR_EDIT", "structuralStop": None, "repairPR": None, "finalVerificationSHA": None,
    }


def doc_for(records, reviewed=None, disposition_counts=None, changed=None):
    return {
        "batchId": batch_id,
        "records": records,
        "totals": {
            "batchId": batch_id,
            "reviewedCount": len(records) if reviewed is None else reviewed,
            "dispositionCounts": disposition_counts if disposition_counts is not None else {},
            "changedCount": 0 if changed is None else changed,
            "secondPassCounts": {}, "blindQASampleSize": 0, "blindQAEscalationCount": 0,
        },
    }


# 1. positive control: a well-formed VERIFIED-only doc has zero errors.
d1 = doc_for([verified_record()], disposition_counts={"VERIFIED": 1})
check("1. well-formed VERIFIED-only doc passes with zero errors", validate_records(d1) == [], validate_records(d1))

# 2. positive control: a well-formed doc mixing VERIFIED + a real change passes.
second_id = batch["entryIds"][1]
d2 = doc_for([verified_record(), changed_record(second_id)],
             disposition_counts={"VERIFIED": 1, "MINOR_EDIT": 1}, changed=1)
check("2. well-formed VERIFIED+MINOR_EDIT doc passes with zero errors", validate_records(d2) == [], validate_records(d2))

# 3. unknown entry
r = verified_record()
r["entryId"] = "rashi-yoma-999z-999"
d = doc_for([r], disposition_counts={"VERIFIED": 1})
errs = validate_records(d)
check("3. unknown entryId is rejected", bool(errors_mentioning(errs, "unknown entry")), errs)

# 4. outside batch: a real entryId that belongs to a different batch
outside_id = other_batch["entryIds"][0]
r = verified_record(outside_id)
r["batchId"] = batch_id  # keep declaring THIS batch even though the entry lives in the other one
d = doc_for([r], disposition_counts={"VERIFIED": 1})
errs = validate_records(d)
check("4. entry from a different batch is rejected as outside batch", bool(errors_mentioning(errs, "outside batch")), errs)

# 5. missing firstPassDisposition
r = verified_record()
r["firstPassDisposition"] = None
d = doc_for([r], disposition_counts={"VERIFIED": 1})
errs = validate_records(d)
check("5. missing firstPassDisposition is rejected", bool(errors_mentioning(errs, "firstPassDisposition")), errs)

# 6. missing finalDisposition
r = verified_record()
r["finalDisposition"] = None
d = doc_for([r], disposition_counts={})
errs = validate_records(d)
check("6. missing finalDisposition is rejected", bool(errors_mentioning(errs, "finalDisposition")), errs)

# 7. changed English without second-pass confirmation
r = changed_record()
r["secondPass"]["status"] = None
d = doc_for([r], disposition_counts={"MINOR_EDIT": 1}, changed=1)
errs = validate_records(d)
check("7. changed English with secondPass.status=None is rejected",
      bool(errors_mentioning(errs, "changed English without second-pass confirmation")), errs)

r = changed_record()
r["secondPass"]["status"] = "REJECTED"
d = doc_for([r], disposition_counts={"MINOR_EDIT": 1}, changed=1)
errs = validate_records(d)
check("7b. changed English with secondPass.status=REJECTED is rejected",
      bool(errors_mentioning(errs, "changed English without second-pass confirmation")), errs)

# 8. BLOCKED without a specific evidence gap
r = verified_record()
r["firstPassDisposition"] = "BLOCKED"
r["finalDisposition"] = "BLOCKED"
r["structuralStop"] = "unclear"
r["secondPass"] = {"required": True, "status": "REMAINED_BLOCKED", "evidence": "still no resolution", "finalEnglish": None}
d = doc_for([r], disposition_counts={"BLOCKED": 1})
errs = validate_records(d)
check("8. BLOCKED with a generic structuralStop ('unclear') is rejected",
      bool(errors_mentioning(errs, "BLOCKED without a specific evidence gap")), errs)

r2 = dict(r)
r2["structuralStop"] = None
d = doc_for([r2], disposition_counts={"BLOCKED": 1})
errs = validate_records(d)
check("8b. BLOCKED with structuralStop=None is rejected",
      bool(errors_mentioning(errs, "BLOCKED without a specific evidence gap")), errs)

# 9. immutable-field change: hebrew differs from live corpus
r = verified_record()
r["hebrew"] = r["hebrew"] + " EXTRA"
d = doc_for([r], disposition_counts={"VERIFIED": 1})
errs = validate_records(d)
check("9. hebrew differing from the live corpus value is rejected as an immutable-field change",
      bool(errors_mentioning(errs, "immutable-field change: hebrew")), errs)

# 10. immutable-field change: originalEnglish differs from live corpus
r = verified_record()
r["originalEnglish"] = r["originalEnglish"] + " EXTRA"
d = doc_for([r], disposition_counts={"VERIFIED": 1})
errs = validate_records(d)
check("10. originalEnglish differing from the live corpus value is rejected as an immutable-field change",
      bool(errors_mentioning(errs, "immutable-field change: originalEnglish")), errs)

# 11. unsupported defect tag
r = changed_record()
r["defectTags"] = ["NOT_A_REAL_TAG"]
d = doc_for([r], disposition_counts={"MINOR_EDIT": 1}, changed=1)
errs = validate_records(d)
check("11. a defect tag outside the fixed vocabulary is rejected", bool(errors_mentioning(errs, "unsupported defect tag")), errs)

# 12. unsupported finalDisposition value
r = verified_record()
r["finalDisposition"] = "MOSTLY_FINE"
d = doc_for([r], disposition_counts={})
errs = validate_records(d)
check("12. a finalDisposition outside the six fixed values is rejected", bool(errors_mentioning(errs, "finalDisposition")), errs)

# 13. totals mismatch: reviewedCount lies about record count
d = doc_for([verified_record()], reviewed=99, disposition_counts={"VERIFIED": 1})
errs = validate_records(d)
check("13. a totals.reviewedCount that disagrees with the actual record count is rejected",
      bool(errors_mentioning(errs, "totals mismatch: reviewedCount")), errs)

# 14. totals mismatch: dispositionCounts lies
d = doc_for([verified_record()], disposition_counts={"VERIFIED": 5})
errs = validate_records(d)
check("14. a totals.dispositionCounts that disagrees with actual dispositions is rejected",
      bool(errors_mentioning(errs, "totals mismatch: dispositionCounts")), errs)

# 15. duplicate record for the same entryId within one batch
d = doc_for([verified_record(), verified_record()], disposition_counts={"VERIFIED": 2})
errs = validate_records(d)
check("15. two records for the same entryId in one batch is rejected as a duplicate",
      bool(errors_mentioning(errs, "duplicate record")), errs)

# 16. VERIFIED record carrying non-empty defectTags
r = verified_record()
r["defectTags"] = ["PUNCTUATION"]
d = doc_for([r], disposition_counts={"VERIFIED": 1})
errs = validate_records(d)
check("16. a VERIFIED record with non-empty defectTags is rejected", bool(errs), errs)


def rejected_second_pass_record(eid=entry_id):
    """A first pass found a defect, but an independent second pass rejected the
    finding and reverted the entry to VERIFIED - the exact scenario Step 6
    batch 001 hit for rashi-yoma-002a-054, where the validator's original
    proposedEnglish nullness check (keyed off firstPassDisposition) directly
    contradicted the contract's own stated rule (keyed off finalDisposition)."""
    e = inv_by_id[eid]
    return {
        "batchId": batch_id, "entryId": eid, "daf": e["daf"],
        "hebrew": e["he"], "originalEnglish": e["en"], "proposedEnglish": None,
        "firstPassDisposition": "SUBSTANTIVE_REPAIR", "defectTags": [],
        "firstPassEvidence": "first-pass evidence for a proposal later rejected",
        "secondPass": {"required": True, "status": "REJECTED",
                       "evidence": "independently re-derived; first pass's proposal does not hold",
                       "finalEnglish": None},
        "blindQA": {"selected": False, "result": None, "evidence": None},
        "finalDisposition": "VERIFIED", "structuralStop": None, "repairPR": None, "finalVerificationSHA": None,
    }


# 17. positive control: a REJECTED second pass reverting a changed firstPassDisposition
# to a VERIFIED finalDisposition, with proposedEnglish correctly null, passes cleanly.
d = doc_for([rejected_second_pass_record()], disposition_counts={"VERIFIED": 1})
errs = validate_records(d)
check("17. a REJECTED-second-pass record (finalDisposition VERIFIED, proposedEnglish null) passes",
      errs == [], errs)

# 18. the null-on-VERIFIED rule still catches a real violation: a REJECTED second pass
# that leaves a stale non-null proposedEnglish behind is rejected (keyed by finalDisposition).
r = rejected_second_pass_record()
r["proposedEnglish"] = r["originalEnglish"] + " (stale proposal left behind)"
d = doc_for([r], disposition_counts={"VERIFIED": 1})
errs = validate_records(d)
check("18. a REJECTED-second-pass record with a stale non-null proposedEnglish is rejected",
      bool(errors_mentioning(errs, "proposedEnglish set but finalDisposition is VERIFIED")), errs)

# 19. the "missing proposedEnglish" requirement still applies for a changed firstPassDisposition
# whose second pass is NOT REJECTED (i.e. the REJECTED exception isn't overly broad).
r = changed_record()
r["proposedEnglish"] = None
d = doc_for([r], disposition_counts={"MINOR_EDIT": 1}, changed=1)
errs = validate_records(d)
check("19. missing proposedEnglish is still rejected when secondPass.status is CONFIRMED, not REJECTED",
      bool(errors_mentioning(errs, "missing proposedEnglish")), errs)

# 20. git_show_inventory smoke test: reads a real ref, returns the expected shape.
base_inv = git_show_inventory("HEAD")
check("20. git_show_inventory('HEAD') returns a parsed inventory with the expected shape",
      isinstance(base_inv.get("entries"), list) and len(base_inv["entries"]) > 0
      and all(k in base_inv["entries"][0] for k in ("id", "he", "en")))

# 21. --base changes which state hebrew/originalEnglish are checked against: a record whose
# originalEnglish matches a BASE-ref snapshot (not the live corpus, which has since "moved on"
# to a new en, simulating a batch PR that bundles its own content edit) passes with base_ref set,
# and is correctly rejected as stale when compared against the live corpus with base_ref unset -
# this is the exact scenario Step 6 batch 001 hit for real.
import validate_rashi_review_records as vrr  # noqa: E402
real_git_show_inventory = vrr.git_show_inventory

synthetic_pre_batch_inv = {
    "entries": [dict(e) for e in inv["entries"]],
}
for e in synthetic_pre_batch_inv["entries"]:
    if e["id"] == entry_id:
        e["en"] = "a pre-batch English value the live corpus no longer has"

vrr.git_show_inventory = lambda base_ref: synthetic_pre_batch_inv
try:
    r = verified_record()
    r["originalEnglish"] = "a pre-batch English value the live corpus no longer has"
    d = doc_for([r], disposition_counts={"VERIFIED": 1})
    errs_with_base = validate_records(d, base_ref="fake-base-ref")
    errs_without_base = validate_records(d, base_ref=None)
finally:
    vrr.git_show_inventory = real_git_show_inventory

check("21a. originalEnglish matching the BASE-ref snapshot (not live) passes when --base is given",
      errs_with_base == [], errs_with_base)
check("21b. the same record is correctly rejected as stale when compared against live with no --base",
      bool(errors_mentioning(errs_without_base, "immutable-field change: originalEnglish")), errs_without_base)

# 22. positive control: a REMAINED_BLOCKED second pass (a confirmed finding whose fix is blocked
# by something outside the entry's own English, e.g. an allowlist ratchet gate) also requires
# proposedEnglish to be null, matching the same finalDisposition-BLOCKED rule REJECTED uses -
# the exact scenario Step 6 batch 001 hit for rashi-yoma-004b-061.
r = changed_record()
r["proposedEnglish"] = None
r["finalDisposition"] = "BLOCKED"
r["structuralStop"] = "confirmed defect, but applying the fix is blocked by an unrelated allowlist ratchet gate"
r["secondPass"] = {"required": True, "status": "REMAINED_BLOCKED",
                   "evidence": "independently re-derived; same defect and fix confirmed, application blocked",
                   "finalEnglish": None}
d = doc_for([r], disposition_counts={"BLOCKED": 1})
errs = validate_records(d)
check("22. a REMAINED_BLOCKED record (finalDisposition BLOCKED, proposedEnglish null) passes",
      errs == [], errs)

if FAILED:
    print(f"\n{len(FAILED)} check(s) failed: {FAILED}")
    sys.exit(1)
print("\nAll checks passed.")
