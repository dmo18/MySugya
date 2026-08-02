#!/usr/bin/env python3
"""
select_rashi_pilot_cohort.py - Rashi translation-quality campaign, Step 4:
deterministic pilot cohort selection.

Freezes a stratified, deterministic sample of Rashi entries for human
semantic review. Selection reads the Step 1 inventory (riskScore,
riskSignals, priorReviewDepth), the Step 2 terminology-variance report, the
Step 3 terminology registry, and live learning_data.js (he/en text, PERAKIM
ranges). It writes nothing back to any of those files - only a new cohort
record.

Every decision is deterministic: entries within a pool are always ordered
by (daf position in learning_data.js file order, vilnaLine), never by
randomness or hashing, so re-running this script against the same corpus
state reproduces byte-identical output. This matters because the campaign's
governing directive requires the cohort to be frozen before review begins
and any later replacement to be documented against the original record.

Selection method (greedy quota fill, see docs/reports/rashi-pilot-cohort-
methodology.md for the full writeup):

  1. Build one deterministic candidate pool per requirement (a sorted list
     of qualifying entry ids).
  2. Walk the requirements in priority order. For each, keep adding the
     next not-yet-selected entry from its pool until the requirement's
     minimum count is met by the CURRENT selection (so an entry already
     picked for one requirement counts toward every other requirement it
     also satisfies - this is what "overlap is permitted" means in
     practice).
  3. Top up to >=200 unique entries and >=10 daf if quota-filling left the
     total short (it does not, empirically, but the top-up is unconditional
     code, not a hope).

No semantic judgment happens here. This script only decides WHICH entries a
human reviewer will look at; it never assigns a disposition, edits English,
or reads meaning into the Hebrew.
"""
import argparse
import json
import re
import sys
from pathlib import Path

SCRIPTS = Path(__file__).parent
ROOT = SCRIPTS.parent
REPO_ROOT = ROOT.parent.parent
DATA_JS = ROOT / "learning_data.js"
DATA_DIR = REPO_ROOT / "docs" / "reports" / "data"
INVENTORY_PATH = DATA_DIR / "rashi-translation-quality-inventory.json"
REGISTRY_PATH = DATA_DIR / "rashi-terminology-registry.json"
OUT_PATH = DATA_DIR / "rashi-pilot-cohort.json"

sys.path.insert(0, str(SCRIPTS))
from audit_rashi_translation_risk import load_corpus  # noqa: E402

WORD_RE = re.compile(r"[A-Za-z']+")
SACRIFICIAL_RE = re.compile(r"קרבנ|חטאת|עול[הת]|אשם|מנח[הת]|זבח")
PRIESTHOOD_TEMPLE_RE = re.compile(r'כה"?ג|כ"ג|כהני?ם?|בית ?ה?מקדש|מזבח|היכל|מקדש')
PURITY_RE = re.compile(r"טומא|טמא|טהר")
CONNECTOR_RE = re.compile(
    r"\b(Therefore|therefore|However|Since|since|Although|because|Rather|Because)\b"
)

# Requirement -> minimum unique-entry count the final cohort must contain.
# Order matters: it is the fill priority, so a requirement listed earlier
# claims entries first when pools overlap.
REQUIREMENT_MINIMUMS = [
    ("historical_reconstruction_or_realignment", 20),
    ("high_risk", 70),
    ("medium_risk", 50),
    ("zero_risk", 40),
    ("beginning_of_yoma", 8),
    ("middle_of_yoma", 8),
    ("end_of_yoma", 8),
    ("short_gloss", 8),
    ("long_explanation", 8),
    ("sacrificial_terminology", 10),
    ("priesthood_or_temple_terminology", 10),
    ("purity_terminology", 8),
    ("narrative_or_contextual_explanation", 10),
    ("multiple_linked_gemara_lines", 10),
    ("terminology_variance_signal", 8),
    ("no_automatic_warning", 8),
]

REQUIREMENT_LABELS = {
    "historical_reconstruction_or_realignment": "from a historically reconstructed or realigned daf (Step 1 provenance)",
    "high_risk": "riskScore >= 9 (Step 2 high-risk tier)",
    "medium_risk": "2 <= riskScore <= 8 (Step 2 medium-risk tier)",
    "zero_risk": "riskScore == 0 (Step 2 lowest-risk tier)",
    "beginning_of_yoma": "daf in the first third of Yoma's daf order",
    "middle_of_yoma": "daf in the middle third of Yoma's daf order",
    "end_of_yoma": "daf in the final third of Yoma's daf order",
    "short_gloss": "English translation is a short gloss (<=6 words)",
    "long_explanation": "English translation is a long explanation (>=30 words)",
    "sacrificial_terminology": "Hebrew contains sacrificial-offering vocabulary",
    "priesthood_or_temple_terminology": "Hebrew contains priesthood or Temple vocabulary",
    "purity_terminology": "Hebrew contains purity/impurity vocabulary",
    "narrative_or_contextual_explanation": "long English with an explicit logical connector (narrative/contextual gloss, not a bare lemma quote)",
    "multiple_linked_gemara_lines": "linkedGemaraLineIds has more than one entry",
    "terminology_variance_signal": "Hebrew contains a Step 3 registry term but English does not contain any of that term's acceptable renderings",
    "no_automatic_warning": "riskScore == 0 and riskSignals is empty (no detector fired at all)",
}


def word_count(en):
    return len(WORD_RE.findall(en or ""))


def load_registry_terms():
    reg = json.loads(REGISTRY_PATH.read_text())
    terms = []
    for tier_name in ("near_invariant", "contextual", "do_not_enforce"):
        tier = reg["tiers"][tier_name]
        for t in tier["terms"]:
            hebrew = t["hebrew"]
            variants = t.get("acceptableVariants") or t.get("commonRenderings") or []
            variants = [v.lower() for v in variants if v and " " not in v.strip("()")] or [
                (t.get("canonicalRendering") or t.get("dominantRendering") or "").lower()
            ]
            terms.append((hebrew, variants, tier_name))
    return terms


def has_terminology_variance_signal(he, en, registry_terms):
    en_lower = (en or "").lower()
    for hebrew, variants, _tier in registry_terms:
        if hebrew in (he or ""):
            if not any(v and v in en_lower for v in variants):
                return True
    return False


def load_perek_ranges():
    text = DATA_JS.read_text()
    m = re.search(r"const PERAKIM = \[(.*?)\n\];", text, re.S)
    ranges = []
    for row in re.finditer(
        r'n:\s*(\d+).*?start:\s*"([0-9]+[ab])".*?end:\s*"([0-9]+[ab])"', m.group(1)
    ):
        ranges.append((int(row.group(1)), row.group(2), row.group(3)))
    return ranges


def perek_for_daf(daf, daf_order, perek_ranges):
    idx = daf_order.index(daf)
    for n, start, end in perek_ranges:
        start_idx, end_idx = daf_order.index(start), daf_order.index(end)
        if start_idx <= idx <= end_idx:
            return n
    return None


def round_robin_by_daf(ids, by_id, daf_order):
    """Reorder a pool so picks spread across daf before repeating within
    one daf: round 1 takes the earliest-vilnaLine candidate from each daf
    that has one (in daf_order sequence), round 2 takes the next from each,
    and so on. Deterministic - no randomness, just a different traversal
    order than a flat file-order sort. This is what keeps a 200-entry
    cohort from being dominated by a single dense daf like 2a (56 Rashi
    entries on its own)."""
    by_daf = {}
    for eid in ids:
        by_daf.setdefault(by_id[eid]["daf"], []).append(eid)
    for daf in by_daf:
        by_daf[daf].sort(key=lambda eid: by_id[eid]["vilnaLine"])
    ordered_daf = [d for d in daf_order if d in by_daf]
    out = []
    round_idx = 0
    while True:
        added = False
        for daf in ordered_daf:
            if round_idx < len(by_daf[daf]):
                out.append(by_daf[daf][round_idx])
                added = True
        if not added:
            break
        round_idx += 1
    return out


def build_pools(entries, daf_order, perek_ranges, registry_terms):
    n_daf = len(daf_order)
    third = n_daf / 3.0
    pools = {name: [] for name, _ in REQUIREMENT_MINIMUMS}
    for e in entries:
        idx = daf_order.index(e["daf"])
        he, en = e["he"], e["en"]
        wc = word_count(en)
        if e["priorReviewDepth"] in ("known-needs-reconstruction", "known-needs-realignment"):
            pools["historical_reconstruction_or_realignment"].append(e["id"])
        if e["riskScore"] >= 9:
            pools["high_risk"].append(e["id"])
        elif 2 <= e["riskScore"] <= 8:
            pools["medium_risk"].append(e["id"])
        if e["riskScore"] == 0:
            pools["zero_risk"].append(e["id"])
            if not e["riskSignals"]:
                pools["no_automatic_warning"].append(e["id"])
        if idx < third:
            pools["beginning_of_yoma"].append(e["id"])
        elif idx < 2 * third:
            pools["middle_of_yoma"].append(e["id"])
        else:
            pools["end_of_yoma"].append(e["id"])
        if wc <= 6:
            pools["short_gloss"].append(e["id"])
        if wc >= 30:
            pools["long_explanation"].append(e["id"])
        if SACRIFICIAL_RE.search(he):
            pools["sacrificial_terminology"].append(e["id"])
        if PRIESTHOOD_TEMPLE_RE.search(he):
            pools["priesthood_or_temple_terminology"].append(e["id"])
        if PURITY_RE.search(he):
            pools["purity_terminology"].append(e["id"])
        if wc >= 20 and CONNECTOR_RE.search(en or ""):
            pools["narrative_or_contextual_explanation"].append(e["id"])
        if len(e["linkedGemaraLineIds"]) > 1:
            pools["multiple_linked_gemara_lines"].append(e["id"])
        if has_terminology_variance_signal(he, en, registry_terms):
            pools["terminology_variance_signal"].append(e["id"])
    return pools


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT_PATH))
    ap.add_argument("--min-total", type=int, default=200)
    ap.add_argument("--min-daf", type=int, default=10)
    args = ap.parse_args()

    daf_order, rashi_by_daf, _lines_by_daf = load_corpus()
    inventory = json.loads(INVENTORY_PATH.read_text())
    inv_by_id = {e["id"]: e for e in inventory["entries"]}
    registry_terms = load_registry_terms()
    perek_ranges = load_perek_ranges()

    entries = []
    for daf in daf_order:
        for r in rashi_by_daf[daf]:
            inv = inv_by_id[r["id"]]
            entries.append({
                "id": r["id"],
                "daf": daf,
                "vilnaLine": r["vilnaLine"],
                "he": r["he"],
                "en": r["en"],
                "linkedGemaraLineIds": r["linkedGemaraLineIds"],
                "riskScore": inv["riskScore"],
                "riskSignals": inv["riskSignals"],
                "priorReviewDepth": inv["priorReviewDepth"],
            })
    by_id = {e["id"]: e for e in entries}

    pools = build_pools(entries, daf_order, perek_ranges, registry_terms)
    for name in pools:
        pools[name] = round_robin_by_daf(pools[name], by_id, daf_order)

    selected = []
    selected_set = set()
    strata_of = {}

    def satisfied_count(name):
        return sum(1 for eid in selected if eid in set(pools[name]))

    for name, minimum in REQUIREMENT_MINIMUMS:
        pool_set = set(pools[name])
        cursor = 0
        while satisfied_count(name) < minimum and cursor < len(pools[name]):
            cand = pools[name][cursor]
            cursor += 1
            if cand not in selected_set:
                selected.append(cand)
                selected_set.add(cand)
                strata_of[cand] = []
        # tag every already-selected entry that satisfies this requirement
        for eid in selected:
            if eid in pool_set and name not in strata_of[eid]:
                strata_of[eid].append(name)

    # Top-up: guarantee >= min_total unique entries and >= min_daf distinct daf.
    all_ids_sorted = round_robin_by_daf([e["id"] for e in entries], by_id, daf_order)
    cursor = 0
    while len(selected) < args.min_total and cursor < len(all_ids_sorted):
        cand = all_ids_sorted[cursor]
        cursor += 1
        if cand not in selected_set:
            selected.append(cand)
            selected_set.add(cand)
            strata_of[cand] = ["top_up_to_minimum_total"]

    covered_daf = {by_id[eid]["daf"] for eid in selected}
    if len(covered_daf) < args.min_daf:
        cursor = 0
        while len(covered_daf) < args.min_daf and cursor < len(all_ids_sorted):
            cand = all_ids_sorted[cursor]
            cursor += 1
            if by_id[cand]["daf"] not in covered_daf:
                if cand not in selected_set:
                    selected.append(cand)
                    selected_set.add(cand)
                    strata_of[cand] = ["top_up_daf_coverage"]
                covered_daf.add(by_id[cand]["daf"])

    cohort = []
    for eid in selected:
        e = by_id[eid]
        perek = perek_for_daf(e["daf"], daf_order, perek_ranges)
        strata = strata_of[eid]
        rationale = "; ".join(REQUIREMENT_LABELS.get(s, s) for s in strata)
        cohort.append({
            "id": e["id"],
            "daf": e["daf"],
            "perek": perek,
            "vilnaLine": e["vilnaLine"],
            "he": e["he"],
            "en": e["en"],
            "linkedGemaraLineIds": e["linkedGemaraLineIds"],
            "riskScore": e["riskScore"],
            "riskSignals": e["riskSignals"],
            "priorReviewDepth": e["priorReviewDepth"],
            "selectionStratum": strata,
            "selectionRationale": rationale,
        })

    cohort.sort(key=lambda c: (daf_order.index(c["daf"]), c["vilnaLine"]))

    daf_set = sorted({c["daf"] for c in cohort}, key=lambda d: daf_order.index(d))
    perek_set = sorted({c["perek"] for c in cohort})
    stratum_counts = {name: sum(1 for c in cohort if name in c["selectionStratum"]) for name, _ in REQUIREMENT_MINIMUMS}

    out = {
        "schemaVersion": 1,
        "generatedFrom": "Step 1 inventory + Step 2 risk report + Step 3 terminology registry, live learning_data.js",
        "selectionMethod": "deterministic greedy quota fill, see modules/yoma/scripts/select_rashi_pilot_cohort.py module docstring",
        "requirementMinimums": dict(REQUIREMENT_MINIMUMS),
        "requirementLabels": REQUIREMENT_LABELS,
        "totalEntries": len(cohort),
        "totalDaf": len(daf_set),
        "totalPerakim": len(perek_set),
        "dafCovered": daf_set,
        "perakimCovered": perek_set,
        "stratumCounts": stratum_counts,
        "entries": cohort,
    }

    out_path = Path(args.out)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {out_path} ({len(cohort)} entries, {len(daf_set)} daf, {len(perek_set)} perakim)")
    for name, minimum in REQUIREMENT_MINIMUMS:
        status = "OK" if stratum_counts[name] >= minimum else "SHORT"
        print(f"  {status:5s} {name}: {stratum_counts[name]} (min {minimum})")
    if len(cohort) < args.min_total:
        print(f"ERROR: total {len(cohort)} < required minimum {args.min_total}", file=sys.stderr)
        return 1
    if len(daf_set) < args.min_daf:
        print(f"ERROR: daf coverage {len(daf_set)} < required minimum {args.min_daf}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
