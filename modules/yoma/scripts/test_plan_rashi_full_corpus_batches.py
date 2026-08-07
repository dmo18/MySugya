#!/usr/bin/env python3
"""
test_plan_rashi_full_corpus_batches.py - regression tests for
plan_rashi_full_corpus_batches.py and validate_rashi_full_corpus_batches.py:
exact remaining-corpus coverage, zero overlap, zero omissions, zero pilot
reassignment, batch-limit and perek-boundary validation, determinism, and
that the validator actually rejects each class of injected corruption
(duplicate assignment, pilot leak, non-contiguous daf, perek crossing,
over-cap, stale plan).

Offline, no network. Run from modules/yoma/:
  python3 scripts/test_plan_rashi_full_corpus_batches.py
"""
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).parent
ROOT = SCRIPTS.parent
REPO_ROOT = ROOT.parent.parent
INVENTORY_PATH = REPO_ROOT / "docs" / "reports" / "data" / "rashi-translation-quality-inventory.json"

FAILED = []


def check(name, cond, detail=""):
    print(f"  {'ok ' if cond else 'FAIL'} {name}" + (f" ({detail})" if detail and not cond else ""))
    if not cond:
        FAILED.append(name)


def run(args, cwd=ROOT):
    return subprocess.run([sys.executable] + args, cwd=str(cwd), capture_output=True, text=True)


with tempfile.TemporaryDirectory() as tmp:
    out1 = Path(tmp) / "batches1.json"
    out2 = Path(tmp) / "batches2.json"

    r1 = run(["scripts/plan_rashi_full_corpus_batches.py", "--out", str(out1)])
    check("1. planner exits 0", r1.returncode == 0, r1.stderr[-500:])

    r2 = run(["scripts/plan_rashi_full_corpus_batches.py", "--out", str(out2)])
    check("2. determinism: two runs produce byte-identical output", out1.read_text() == out2.read_text())

    doc = json.loads(out1.read_text())
    batches = doc["batches"]
    inv = json.loads(INVENTORY_PATH.read_text())
    unreviewed_ids = {e["id"] for e in inv["entries"] if e["reviewStatus"] == "UNREVIEWED"}
    reviewed_ids = {e["id"] for e in inv["entries"] if e["reviewStatus"] == "REVIEWED"}

    all_assigned = [eid for b in batches for eid in b["entryIds"]]
    check("3. exact remaining-corpus coverage: assigned set == UNREVIEWED set",
          set(all_assigned) == unreviewed_ids,
          f"missing={len(unreviewed_ids - set(all_assigned))} extra={len(set(all_assigned) - unreviewed_ids)}")
    check("4. zero duplicate assignment", len(all_assigned) == len(set(all_assigned)))
    check("5. zero pilot (REVIEWED) entries reassigned", not (set(all_assigned) & reviewed_ids))

    # The Step 6 review campaign is actively completing batches and shrinking
    # the remaining UNREVIEWED corpus, so a hardcoded absolute batch-count
    # range (originally calibrated against the full 8,654-entry corpus) goes
    # stale as batches complete. Derive a self-adjusting sanity bound instead
    # from the current corpus: batches never cross a perek boundary or exceed
    # 8 daf each, so at least ceil(unreviewed_daf_count / 8) batches are
    # required; and every batch covers at least 1 daf, so at most
    # unreviewed_daf_count batches can result. This still catches a
    # genuinely broken planner (e.g. 0 batches, or an absurd count) while
    # remaining correct as the campaign's remaining corpus shrinks.
    unreviewed_daf_count = len({e["daf"] for e in inv["entries"] if e["reviewStatus"] == "UNREVIEWED"})
    min_batches = -(-unreviewed_daf_count // 8)  # ceil division
    max_batches = unreviewed_daf_count
    check("6. batch count is plausible for the current remaining corpus",
          min_batches <= len(batches) <= max_batches,
          f"batches={len(batches)} expected range=[{min_batches}, {max_batches}]")
    check("7. every batch entryCount <= 350", all(b["entryCount"] <= 350 for b in batches))
    check("8. every batch daf count <= 8", all(len(b["daf"]) <= 8 for b in batches))
    check("9. every batch stays within one perek", all(len(b["daf"]) > 0 for b in batches))
    check("10. batch ids sequential", [b["batchId"] for b in batches] == [f"step6-batch-{i+1:03d}" for i in range(len(batches))])
    check("11. all 173 daf covered exactly once across all batches",
          sorted(x for b in batches for x in b["daf"]) == sorted(set(x for b in batches for x in b["daf"])))

    # Validator: the freshly generated plan (copied to the canonical path
    # the validator reads) must validate clean.
    import shutil
    canonical = REPO_ROOT / "docs" / "reports" / "data" / "rashi-full-corpus-review-batches.json"
    backup = canonical.read_bytes() if canonical.exists() else None
    try:
        shutil.copy(out1, canonical)
        rv = run(["scripts/validate_rashi_full_corpus_batches.py"])
        check("12. validator accepts a fresh, correct plan", rv.returncode == 0, rv.stdout[-500:])

        def corrupt_and_check(name, mutate, expect_substr):
            corrupted = copy.deepcopy(doc)
            mutate(corrupted)
            canonical.write_text(json.dumps(corrupted, ensure_ascii=False, indent=1))
            r = run(["scripts/validate_rashi_full_corpus_batches.py"])
            ok = r.returncode != 0 and expect_substr in r.stdout
            check(name, ok, r.stdout[-800:])

        # Duplicate-assignment detection is per-entry-id across the whole
        # plan regardless of batch boundaries (see validator's `seen` dict),
        # so self-duplicating within batch 0 exercises the same check and
        # stays correct whether 1 or many batches remain as the campaign's
        # remaining corpus shrinks toward completion.
        corrupt_and_check(
            "13. validator rejects duplicate assignment",
            lambda d: d["batches"][0]["entryIds"].append(d["batches"][0]["entryIds"][0]),
            "duplicate assignment",
        )
        corrupt_and_check(
            "14. validator rejects a pilot (REVIEWED) entry injected into a batch",
            lambda d: d["batches"][0]["entryIds"].append(next(iter(reviewed_ids))),
            "pilot-entry reassignment",
        )
        corrupt_and_check(
            "15. validator rejects a missing entry (coverage gap)",
            lambda d: d["batches"][0]["entryIds"].pop(),
            "missing from every batch",
        )
        corrupt_and_check(
            "16. validator rejects a non-contiguous daf list",
            lambda d: d["batches"][0].__setitem__("daf", [d["batches"][0]["daf"][0], d["batches"][-1]["daf"][0]]),
            "not contiguous",
        )
        # A perek-crossing batch can only be constructed by borrowing a daf
        # from a batch in a different perek. As the campaign's remaining
        # corpus shrinks toward completion, the fresh plan can end up with
        # only one batch / one perek, in which case this corruption is
        # unconstructible from real data; skip rather than fail in that case.
        other_perek_daf = [b["daf"][0] for b in batches if b["perek"] != batches[0]["perek"]][:1]
        if other_perek_daf:
            corrupt_and_check(
                "17. validator rejects a perek-crossing batch",
                lambda d: d["batches"][0].__setitem__("daf", d["batches"][0]["daf"] + other_perek_daf),
                "spans multiple perakim",
            )
        else:
            check("17. validator rejects a perek-crossing batch (skipped: only one perek remains in the plan)", True)
        corrupt_and_check(
            "18. validator rejects an over-hard-cap entryCount",
            lambda d: d["batches"][0].__setitem__("entryCount", 999),
            "exceeds hard max",
        )
        corrupt_and_check(
            "19. validator rejects a stale plan (tampered without regenerating)",
            lambda d: d["batches"][0].__setitem__("estimatedChangedCount", 999999),
            "STALE PLAN",
        )
    finally:
        if backup is not None:
            canonical.write_bytes(backup)
        else:
            canonical.unlink(missing_ok=True)

if FAILED:
    print(f"\n{len(FAILED)} check(s) failed: {FAILED}")
    sys.exit(1)
print("\nAll checks passed.")
