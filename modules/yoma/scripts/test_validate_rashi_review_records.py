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
from validate_rashi_review_records import validate_records  # noqa: E402

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

if FAILED:
    print(f"\n{len(FAILED)} check(s) failed: {FAILED}")
    sys.exit(1)
print("\nAll checks passed.")
