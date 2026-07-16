#!/usr/bin/env python3
"""
test_scaffold_audit.py - regression tests for audit_rashi_scaffold.py:
detector rules (scaffold prefixes, bracket-guess combos, line-number
placeholders, Hebrew passthrough), natural-English negative cases, baseline
ratchet semantics (new/changed/covered/stale, shrink-only updates), corpus
consistency against the committed debt baseline, and known-clean controls.

Offline, no network, no git. Run from modules/yoma/:
  python3 scripts/test_scaffold_audit.py
"""
import json
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS))
import audit_rashi_scaffold as asc  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    print(f"  {'ok ' if cond else 'FAIL'} {name}" + (f" ({detail})" if detail and not cond else ""))
    if not cond:
        FAILED.append(name)


def rules(en):
    return asc.rules_for(en)


print("detector: prohibited scaffold prefixes")
check("1. exact 'Rashi: opens -' fails",
      "scaffold-prefix" in rules("Rashi: opens - a donkey was taken along"))
check("2. 'Rashi: continues -' fails",
      "scaffold-prefix" in rules("Rashi: continues - the third of the night"))
check("3. 'Rashi: concludes -' fails",
      "scaffold-prefix" in rules("Rashi: concludes - 'for keeping' - the daf ends"))
check("4a. capitalization variant fails",
      "scaffold-prefix" in rules("rashi: Continues - the measurement"))
check("4b. comma variant fails",
      "scaffold-prefix" in rules("Rashi, continues - the measurement"))
check("4c. no-colon bare-verb variant fails",
      "scaffold-prefix" in rules("Rashi continues: you could indeed require separation"))
check("4d. intermediate-text variant fails",
      "scaffold-prefix" in rules("Rashi: continues the Sakistan measurement - the inner region"))
check("4e. 'closes' variant fails",
      "scaffold-prefix" in rules("Rashi: closes the gatehouse gloss, then opens on 'marpeset'"))
check("4f. 'completes' variant fails",
      "scaffold-prefix" in rules("Rashi: completes the Ahiman comment"))

print("detector: scaffold plus bracket guessing")
r5 = rules("Rashi: opens - since [the Gemara] said [that the statute applies]")
check("5a. scaffold with 2+ bracket guesses adds bracket rule",
      "scaffold-bracket-guess" in r5)
check("5b. scaffold with one bracket stays prefix-only",
      rules("Rashi: continues - until the incense service [is performed]")
      == ["scaffold-prefix"])

print("detector: line-number and passthrough placeholders")
check("line-number 'Rashi on line 14:' fails",
      "line-number-scaffold" in rules("Rashi on line 14: אומר שיתנם בטבעות בדוחק:"))
check("line-number '[Rashi commentary on line 100]:' fails",
      "line-number-scaffold" in rules("[Rashi commentary on line 100]: ת\"ל"))
check("hebrew passthrough fails",
      "hebrew-passthrough" in rules("כתב לא יסורו. אלמא אין זזין מהן"))

print("detector: natural English never matches")
check("8a. mid-sentence 'continues' passes",
      rules("The burning of limbs continues the whole night.") == [])
check("8b. mid-sentence 'opens' passes",
      rules("He opens the censer and scoops the coals.") == [])
check("8c. 'Rashi' as translated subject without scaffold verb passes",
      rules("Rashi holds that the kometz must be exact.") == [])
check("9a. legitimate citation bracket passes",
      rules("'And the pure one shall sprinkle' [Numbers 19:19] teaches that a "
            "tevul yom is qualified [for the heifer rite].") == [])
check("9b. clarifying brackets without scaffold pass",
      rules("He stuck the kometz [to the walls of the vessel], as we hold in "
            "Menachot (26a) [regarding a full kometz].") == [])

print("baseline ratchet semantics (pure compare)")
h_new = {"daf": "5a", "vilnaLine": 3, "rule": "scaffold-prefix",
         "rules": ["scaffold-prefix"], "signature": "rashi: opens",
         "enHash": asc.en_hash("Rashi: opens - x"), "message": ""}
h_cov = dict(h_new, daf="5b", enHash=asc.en_hash("Rashi: opens - y"))
h_chg = dict(h_new, daf="5b", vilnaLine=9, enHash=asc.en_hash("Rashi: opens - z2"))
baseline = {
    ("5b", 3): {"daf": "5b", "vilnaLine": 3, "rule": "scaffold-prefix",
                "enHash": asc.en_hash("Rashi: opens - y")},
    ("5b", 9): {"daf": "5b", "vilnaLine": 9, "rule": "scaffold-prefix",
                "enHash": asc.en_hash("Rashi: opens - z1")},
    ("5b", 12): {"daf": "5b", "vilnaLine": 12, "rule": "scaffold-prefix",
                 "enHash": asc.en_hash("Rashi: opens - w")},
}
new, changed, covered, hit_keys, _ = asc.compare([h_new, h_cov, h_chg], baseline)
check("7. unbaselined scaffold line is NEW (fails gate)",
      [(h["daf"], h["vilnaLine"]) for h in new] == [("5a", 3)])
check("6. changed-but-still-contaminated baseline entry fails",
      [(h["daf"], h["vilnaLine"]) for h in changed] == [("5b", 9)])
check("covered entry is neither new nor changed",
      [(h["daf"], h["vilnaLine"]) for h in covered] == [("5b", 3)])
check("18a. repaired line surfaces as stale for retirement",
      asc.stale_entries(baseline, hit_keys, {"5a", "5b"}) == [("5b", 12)])

print("baseline update is shrink-only (14, 18)")
with tempfile.TemporaryDirectory() as td:
    tmp = Path(td) / "debt.json"
    tmp.write_text(json.dumps({"entries": [
        {"daf": "5b", "vilnaLine": 3, "rule": "scaffold-prefix",
         "enHash": asc.en_hash("Rashi: opens - y")},
        {"daf": "5b", "vilnaLine": 12, "rule": "scaffold-prefix",
         "enHash": asc.en_hash("Rashi: opens - w")},
    ]}))
    old_baseline_path = asc.BASELINE
    try:
        asc.BASELINE = tmp
        loaded = asc.load_baseline()
        check("14a. loader carries exact hashes (no silent rehash path exists)",
              loaded[("5b", 3)]["enHash"] == asc.en_hash("Rashi: opens - y"))
        data = json.loads(tmp.read_text())
        stale = {("5b", 12)}
        data["entries"] = [e for e in data["entries"]
                           if (e["daf"], e["vilnaLine"]) not in stale]
        tmp.write_text(json.dumps(data))
        check("18b. retirement shrinks the baseline",
              len(asc.load_baseline()) == 1)
    finally:
        asc.BASELINE = old_baseline_path

print("corpus consistency against committed baseline")
corpus_hits = []
for d in asc.all_daf():
    corpus_hits.extend(asc.scan_daf(d))
committed = asc.load_baseline()
new, changed, covered, hit_keys, _ = asc.compare(corpus_hits, committed)
check("17a. corpus scan count equals baseline inventory",
      len(corpus_hits) == len(committed),
      f"scan={len(corpus_hits)} baseline={len(committed)}")
check("17b. zero new hits vs committed baseline", not new, str(new[:3]))
check("17c. zero changed hits vs committed baseline", not changed, str(changed[:3]))
check("17d. zero stale entries in committed baseline",
      not asc.stale_entries(committed, hit_keys, set(asc.all_daf())))

print("known-clean negative controls")
controls_50 = ["50a", "50b", "51a", "51b", "52a", "52b"]
controls_repaired = ["61a", "67b", "68a", "68b", "70a", "71b"]
controls_77 = ["77a", "77b", "78a", "78b", "79a", "79b", "80a", "80b",
               "81a", "81b", "82a", "82b", "83a", "83b", "84a", "84b",
               "85a", "85b", "86a", "86b", "87a", "87b", "88a"]
for name, group in [("10. 50a-52b", controls_50),
                    ("repaired daf", controls_repaired),
                    ("11. 77a-88a", controls_77)]:
    dirty = [d for d in group if asc.scan_daf(d)]
    check(f"{name} clean", not dirty, str(dirty))

print("content allowlist stays empty (16)")
ca = json.loads((SCRIPTS / "allowlists" / "rashi_content_allowlist.json").read_text())
check("16. rashi_content_allowlist.json has zero entries",
      not ca.get("entries") and not ca.get("count_mismatches"))

if FAILED:
    print(f"\nFAILED: {len(FAILED)} test(s): {FAILED}")
    sys.exit(1)
print("\nOK: all scaffold-audit tests passed.")
