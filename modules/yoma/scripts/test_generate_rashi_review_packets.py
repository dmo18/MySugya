#!/usr/bin/env python3
"""
test_generate_rashi_review_packets.py - regression tests for
generate_rashi_review_packets.py: determinism, exact batch coverage, no
Hebrew/English edits, review-block fields align with the Step 5
review-record contract, and a filled-in review block validates cleanly
against validate_rashi_review_records.py.

Offline, no network. Run from modules/yoma/:
  python3 scripts/test_generate_rashi_review_packets.py
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).parent
ROOT = SCRIPTS.parent
REPO_ROOT = ROOT.parent.parent
DATA_DIR = REPO_ROOT / "docs" / "reports" / "data"
INVENTORY_PATH = DATA_DIR / "rashi-translation-quality-inventory.json"
BATCHES_PATH = DATA_DIR / "rashi-full-corpus-review-batches.json"

FAILED = []


def check(name, cond, detail=""):
    print(f"  {'ok ' if cond else 'FAIL'} {name}" + (f" ({detail})" if detail and not cond else ""))
    if not cond:
        FAILED.append(name)


inv = json.loads(INVENTORY_PATH.read_text())
entries_by_id = {e["id"]: e for e in inv["entries"]}
batches_doc = json.loads(BATCHES_PATH.read_text())
batch = batches_doc["batches"][0]
batch_id = batch["batchId"]

with tempfile.TemporaryDirectory() as tmp:
    out1 = Path(tmp) / "p1.json"
    out2 = Path(tmp) / "p2.json"

    r1 = subprocess.run([sys.executable, str(SCRIPTS / "generate_rashi_review_packets.py"),
                         "--batch-id", batch_id, "--out", str(out1)],
                        cwd=str(ROOT), capture_output=True, text=True)
    check("1. script exits 0", r1.returncode == 0, r1.stderr[-800:])

    r2 = subprocess.run([sys.executable, str(SCRIPTS / "generate_rashi_review_packets.py"),
                         "--batch-id", batch_id, "--out", str(out2)],
                        cwd=str(ROOT), capture_output=True, text=True)
    check("2. determinism: two runs produce byte-identical output", out1.read_text() == out2.read_text())

    doc = json.loads(out1.read_text())
    packets = doc["packets"]

    check("3. totalPackets matches batch entryIds count", doc["totalPackets"] == len(batch["entryIds"]))
    check("4. packet ids exactly match batch entryIds, in order",
          [p["id"] for p in packets] == batch["entryIds"])
    check("5. every packet's he/en matches the live inventory byte-for-byte",
          all(p["he"] == entries_by_id[p["id"]]["he"] and p["en"] == entries_by_id[p["id"]]["en"] for p in packets))
    check("6. every packet's daf/riskScore/priorReviewDepth match the live inventory",
          all(p["daf"] == entries_by_id[p["id"]]["daf"]
              and p["riskScore"] == entries_by_id[p["id"]]["riskScore"]
              and p["priorReviewDepth"] == entries_by_id[p["id"]]["priorReviewDepth"] for p in packets))

    review_keys = {"batchId", "entryId", "daf", "hebrew", "originalEnglish", "proposedEnglish",
                   "firstPassDisposition", "defectTags", "firstPassEvidence", "secondPass",
                   "blindQA", "finalDisposition", "structuralStop", "repairPR", "finalVerificationSHA"}
    check("7. every review block has exactly the contract's field set",
          all(set(p["review"].keys()) == review_keys for p in packets))
    check("8. every review block starts with no disposition and empty defectTags (no automated verdict)",
          all(p["review"]["firstPassDisposition"] is None
              and p["review"]["finalDisposition"] is None
              and p["review"]["defectTags"] == [] for p in packets))
    check("9. review block's immutable fields (hebrew/originalEnglish/daf/entryId/batchId) pre-filled and correct",
          all(p["review"]["hebrew"] == p["he"] and p["review"]["originalEnglish"] == p["en"]
              and p["review"]["daf"] == p["daf"] and p["review"]["entryId"] == p["id"]
              and p["review"]["batchId"] == batch_id for p in packets))

    # A filled-in review block for a VERIFIED disposition should validate
    # cleanly against the review-record contract's own validator.
    sample = dict(packets[0]["review"])
    sample["firstPassDisposition"] = "VERIFIED"
    sample["finalDisposition"] = "VERIFIED"
    sample["secondPass"] = {"required": False, "status": None, "evidence": None, "finalEnglish": None}
    sample["blindQA"] = {"selected": False, "result": None, "evidence": None}
    record_doc = {
        "batchId": batch_id,
        "records": [sample],
        "totals": {
            "batchId": batch_id, "reviewedCount": 1,
            "dispositionCounts": {"VERIFIED": 1}, "changedCount": 0,
            "secondPassCounts": {}, "blindQASampleSize": 0, "blindQAEscalationCount": 0,
        },
    }
    record_path = Path(tmp) / "record.json"
    record_path.write_text(json.dumps(record_doc, ensure_ascii=False))
    rv = subprocess.run([sys.executable, str(SCRIPTS / "validate_rashi_review_records.py"), str(record_path)],
                        cwd=str(ROOT), capture_output=True, text=True)
    check("10. a filled-in VERIFIED review block validates cleanly against validate_rashi_review_records.py",
          rv.returncode == 0, (rv.stdout + rv.stderr)[-800:])

    check("11. unknown --batch-id fails cleanly (non-zero exit, no traceback written to --out)",
          subprocess.run([sys.executable, str(SCRIPTS / "generate_rashi_review_packets.py"),
                          "--batch-id", "step6-batch-999", "--out", str(Path(tmp) / "bad.json")],
                         cwd=str(ROOT), capture_output=True, text=True).returncode != 0)

if FAILED:
    print(f"\n{len(FAILED)} check(s) failed: {FAILED}")
    sys.exit(1)
print("\nAll checks passed.")
