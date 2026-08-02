#!/usr/bin/env python3
"""
audit_rashi_translation_risk.py - Rashi translation-quality campaign,
Step 2: deterministic, read-only risk-triage audit.

Ranks all 8,854 Rashi entries for human semantic review. Every detector
below is a TRIAGE SIGNAL ONLY: it may raise or lower an entry's risk
score and attach a reason, but it never assigns a final disposition
(VERIFIED / MINOR_EDIT / SUBSTANTIVE_REPAIR / RETRANSLATE /
DUPLICATION_OR_CONTAMINATION / BLOCKED) and never edits English text.
That judgment is reserved for human semantic review (Steps 4-6) against
the Hebrew and its context, per the governing directive.

Reads only: learning_data.js (he/en/linkedGemaraLineIds for every daf's
Gemara lines and Rashi lines - read-only, never written), the Step 1
inventory (docs/reports/data/rashi-translation-quality-inventory.json),
and audit_rashi_semantic.py's existing --profile --json output (reused,
not reimplemented, for the SHIFTED/FABRICATION-SUSPECT daf-level signal).

Every defect tag used below is drawn from the campaign's fixed
vocabulary (WRONG_MEANING, OMITTED_TEXT, INVENTED_TEXT, WRONG_REFERENT,
WRONG_LOGIC, WRONG_TECHNICAL_TERM, HEBREW_LEFT_UNTRANSLATED,
ARAMAIC_LEFT_UNTRANSLATED, GRAMMAR, FRAGMENT, OVERLITERAL, OVEREXPLAINED,
DUPLICATED, SHIFTED, TRUNCATED, CONTEXT_MISMATCH, TERMINOLOGY_DRIFT,
PUNCTUATION, STYLE_ONLY, NEEDS_EXPERT_REVIEW) - no detector below invents
a new tag.

Usage:
  python3 scripts/audit_rashi_translation_risk.py
    [--out-dir <path>] [--top N]
"""
import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

SCRIPTS = Path(__file__).parent
ROOT = SCRIPTS.parent
REPO_ROOT = ROOT.parent.parent
DATA_JS = ROOT / "learning_data.js"
INVENTORY_PATH = REPO_ROOT / "docs" / "reports" / "data" / "rashi-translation-quality-inventory.json"
DATA_DIR = REPO_ROOT / "docs" / "reports" / "data"

sys.path.insert(0, str(SCRIPTS))
from _js_parser import parse_daf_blocks, parse_rashi_lines_array, parse_line_items_from_lines_array  # noqa: E402

HEBREW_RE = re.compile(r"[֐-׿]")
WORD_RE = re.compile(r"[A-Za-z']+")
PRONOUNS = {
    "he", "him", "his", "she", "her", "hers", "it", "its", "they", "them",
    "their", "this", "that", "these", "those", "one",
}
TRUNCATION_TAIL_WORDS = {
    "and", "the", "of", "to", "in", "that", "which", "who", "a", "an",
    "for", "with", "as", "is", "or", "but", "his", "her", "its",
}
# Scaffold/mechanical-narration patterns (matches the family
# validate_rashi_content.py and audit_rashi_scaffold.py already gate on
# corpus-wide - defense-in-depth here as a triage signal, not a
# duplicate gate; corpus is already at 0 documented scaffold debt, so
# any hit here is either a false positive or a genuinely new instance).
MECHANICAL_TEMPLATE_RE = re.compile(
    r"^(Rashi:\s*(opens|continues|concludes|explains)|"
    r"Opens ['‘“]|Continuing:|Closing:|Then opens)",
    re.IGNORECASE,
)
PLACEHOLDER_RE = re.compile(
    r"\[(TBD|TODO|PLACEHOLDER|FIXME|XXX)\]|\.\.\.\s*$|^\s*\.\.\.",
    re.IGNORECASE,
)


def load_corpus():
    """Return (daf_order, rashi_by_daf, lines_by_daf) from live
    learning_data.js. rashi_by_daf[daf] is a list of parse_rashi_fields
    dicts in file order; lines_by_daf[daf] is id -> line dict."""
    text = DATA_JS.read_text()
    daf_order = []
    rashi_by_daf = {}
    lines_by_daf = {}
    for daf, block in parse_daf_blocks(text):
        daf_order.append(daf)
        rashi_by_daf[daf] = parse_rashi_lines_array(block)
        line_items = parse_line_items_from_lines_array(block)
        lines_by_daf[daf] = {item["id"]: item for item in line_items}
    return daf_order, rashi_by_daf, lines_by_daf


def load_semantic_profile():
    """Run audit_rashi_semantic.py --profile --json once and return
    daf -> classification (ALIGNED / SHIFTED / FABRICATION-SUSPECT /
    INSUFFICIENT-ANCHORS). Reused, not reimplemented."""
    out = subprocess.run(
        [sys.executable, "scripts/audit_rashi_semantic.py", "--profile", "--json"],
        cwd=str(ROOT), capture_output=True, text=True, check=True,
    ).stdout
    profiles = json.loads(out)
    return {p["daf"]: p["classification"] for p in profiles}


def load_step1_provenance():
    inv = json.loads(INVENTORY_PATH.read_text())
    return inv["dafProvenance"]


# ---------------------------------------------------------------------
# Per-entry detectors. Each takes (entry, he, en, context) and yields
# (tag, weight, reason) tuples. context carries corpus-wide indices
# built once (duplicate index, term index, neighbor lookup, linked
# Gemara line text).
# ---------------------------------------------------------------------

def detect_empty(en):
    if not en or not en.strip():
        yield ("OMITTED_TEXT", 10, "English field is empty")


def detect_identical_to_hebrew(he, en):
    if en and he and en.strip() == he.strip():
        yield ("HEBREW_LEFT_UNTRANSLATED", 10, "English is byte-identical to the Hebrew (never translated)")


def detect_hebrew_leakage(en):
    if not en:
        return
    hits = HEBREW_RE.findall(en)
    if hits:
        yield ("HEBREW_LEFT_UNTRANSLATED", 8,
               f"{len(hits)} Hebrew-script character(s) present in the English field")


def detect_length_ratio(he, en):
    if not he or not en:
        return
    ratio = len(en) / max(len(he), 1)
    if ratio < 0.25:
        yield ("OMITTED_TEXT", 4, f"English is only {ratio:.2f}x the Hebrew's character length (possible omission)")
    elif ratio > 4.5:
        yield ("OVEREXPLAINED", 4, f"English is {ratio:.2f}x the Hebrew's character length (possible invention or merged content)")


def detect_truncation(en):
    if not en:
        return
    stripped = en.strip()
    if not stripped:
        return
    # Rashi entries conventionally end many lemma/quote segments with a
    # dash, comma, colon, or semicolon before the next segment's
    # explanation continues - this is the corpus's normal editorial
    # convention, not truncation (confirmed by spot-checking during
    # Step 2 development: flagging any trailing "-,;:" produced a ~28%
    # corpus-wide false-positive rate, entirely from this legitimate
    # pattern). Only a bare ending with NO closing punctuation at all,
    # landing on a function word, is flagged - a narrower and more
    # genuine truncation signal.
    if stripped[-1].isalnum():
        last_word = WORD_RE.findall(stripped)
        if last_word and last_word[-1].lower() in TRUNCATION_TAIL_WORDS:
            yield ("TRUNCATED", 4, f"ends abruptly with no closing punctuation, on the function word {last_word[-1]!r}")


def detect_fragment(en):
    if not en:
        return
    stripped = en.strip()
    words = WORD_RE.findall(stripped)
    if len(words) <= 3 and not stripped.endswith((".", "!", "?")):
        yield ("FRAGMENT", 3, f"very short ({len(words)} word(s)) with no closing punctuation")


def detect_unmatched_punctuation(en):
    if not en:
        return
    opens_paren = en.count("(")
    closes_paren = en.count(")")
    if opens_paren != closes_paren:
        yield ("PUNCTUATION", 3, f"unmatched parentheses: {opens_paren} '(' vs {closes_paren} ')'")
    dquotes = en.count('"')
    if dquotes % 2 == 1:
        yield ("PUNCTUATION", 2, f"odd number of double-quote characters ({dquotes})")


def detect_mechanical_template(en):
    if not en:
        return
    if MECHANICAL_TEMPLATE_RE.search(en):
        yield ("FRAGMENT", 7, "matches a known mechanical/scaffold-narration template")
    if PLACEHOLDER_RE.search(en):
        yield ("FRAGMENT", 7, "matches a known placeholder pattern ([TBD]-style or trailing ellipsis)")


def detect_pronoun_heavy(en):
    if not en:
        return
    words = [w.lower() for w in WORD_RE.findall(en)]
    if len(words) < 6:
        return
    pronoun_count = sum(1 for w in words if w in PRONOUNS)
    ratio = pronoun_count / len(words)
    if ratio > 0.35:
        yield ("WRONG_REFERENT", 2,
               f"pronoun-heavy ({pronoun_count}/{len(words)} words) with no obvious local referent check performed - human review needed")


def detect_possible_copied_gemara(en, linked_line_texts):
    if not en or not linked_line_texts:
        return
    en_norm = _normalize(en)
    for line_en in linked_line_texts:
        if not line_en:
            continue
        line_norm = _normalize(line_en)
        if len(en_norm) > 20 and (en_norm in line_norm or line_norm in en_norm):
            yield ("CONTEXT_MISMATCH", 6,
                   "English substantially overlaps its linked Gemara line's own English - "
                   "possibly a copied Gemara translation rather than a Rashi comment")
            return


def _normalize(s):
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", s.lower())).strip()


# ---------------------------------------------------------------------
# Corpus-wide (cross-entry) signals
# ---------------------------------------------------------------------

def build_duplicate_clusters(all_entries):
    """Group entries whose normalized English is identical, across
    different Hebrew source lines. A cluster of size 1 is not a
    duplicate. Returns list of clusters, each a list of entry refs."""
    by_norm = defaultdict(list)
    for e in all_entries:
        norm = _normalize(e["en"])
        if len(norm) < 15:
            continue  # too short to be a meaningful duplicate signal
        by_norm[norm].append(e)
    clusters = []
    for norm, members in by_norm.items():
        distinct_he = {m["he"] for m in members}
        if len(members) >= 2 and len(distinct_he) >= 2:
            clusters.append({
                "normalizedEnglish": norm[:200],
                "memberCount": len(members),
                "distinctHebrewCount": len(distinct_he),
                "entries": [{"id": m["id"], "daf": m["daf"], "vilnaLine": m["vilnaLine"]} for m in members],
            })
    clusters.sort(key=lambda c: -c["memberCount"])
    return clusters


def apply_duplicate_signals(all_entries, clusters, risk_by_id):
    for cluster in clusters:
        for ref in cluster["entries"]:
            risk_by_id[ref["id"]].append((
                "DUPLICATED", 6,
                f"English identical to {cluster['memberCount'] - 1} other entry/entries with different Hebrew "
                f"(cluster of {cluster['distinctHebrewCount']} distinct Hebrew source lines)",
            ))


def apply_neighboring_duplicate_signals(daf_order, rashi_by_daf, risk_by_id):
    for daf in daf_order:
        entries = rashi_by_daf[daf]
        for i in range(1, len(entries)):
            prev_en = _normalize(entries[i - 1]["en"])
            cur_en = _normalize(entries[i]["en"])
            if len(cur_en) >= 15 and prev_en == cur_en:
                risk_by_id[entries[i]["id"]].append((
                    "DUPLICATED", 8,
                    f"identical English to the immediately preceding entry ({entries[i - 1]['id']}) on the same daf",
                ))


# A small, curated set of high-frequency recurring source terms whose
# English rendering this report tracks for variance - NOT a
# terminology contract (that is Step 3's job) and NOT a pass/fail gate.
# Purely observational: which Hebrew terms get more than one distinct
# English rendering, and how many entries use each variant.
TERMINOLOGY_WATCHLIST = {
    "כהן גדול": "Kohen Gadol",
    "בית המקדש": "Temple",
    "קרבן": "offering/sacrifice",
    "טומאה": "impurity",
    "טהרה": "purity",
    "עבודה": "service/rite",
}


def build_terminology_variance(all_entries):
    variance = {}
    for hebrew_term, label in TERMINOLOGY_WATCHLIST.items():
        # Simple presence buckets from the label's slash-separated
        # candidate renderings, plus a "none of the expected" bucket -
        # a deterministic Step 2 tool cannot cluster free-form phrasing,
        # only check for known expected tokens.
        candidates = [c.strip().lower() for c in label.split("/")]
        buckets = defaultdict(int)
        matched_none = 0
        total = 0
        for e in all_entries:
            if hebrew_term not in (e["he"] or ""):
                continue
            total += 1
            en_lower = (e["en"] or "").lower()
            hit = None
            for c in candidates:
                if c in en_lower:
                    hit = c
                    break
            if hit:
                buckets[hit] += 1
            else:
                matched_none += 1
        if total == 0:
            continue
        variance[hebrew_term] = {
            "expectedLabel": label,
            "totalEntriesContainingTerm": total,
            "renderingCounts": dict(buckets),
            "noneOfExpectedRenderings": matched_none,
        }
    return variance


def apply_daf_level_signals(daf_order, rashi_by_daf, semantic_profile, step1_provenance, risk_by_id):
    for daf in daf_order:
        classification = semantic_profile.get(daf)
        provenance = step1_provenance.get(daf, {})
        depth = provenance.get("depth")
        for e in rashi_by_daf[daf]:
            if classification == "SHIFTED":
                risk_by_id[e["id"]].append((
                    "SHIFTED", 7,
                    f"daf {daf} classified SHIFTED by audit_rashi_semantic.py --profile "
                    "(anchor tokens suggest line-alignment drift)",
                ))
            elif classification == "FABRICATION-SUSPECT":
                risk_by_id[e["id"]].append((
                    "INVENTED_TEXT", 9,
                    f"daf {daf} classified FABRICATION-SUSPECT by audit_rashi_semantic.py --profile "
                    "(Hebrew anchor tokens do not appear in the English at all)",
                ))
            if depth == "known-needs-reconstruction":
                risk_by_id[e["id"]].append((
                    "INVENTED_TEXT", 9,
                    f"daf {daf} classified 'needs reconstruction' by the VERSION 15.293 Wave 1 audit "
                    "(en text confirmed generic filler or fabricated, unrelated to its own Hebrew line)",
                ))
            elif depth == "known-needs-realignment":
                risk_by_id[e["id"]].append((
                    "CONTEXT_MISMATCH", 8,
                    f"daf {daf} classified 'needs realignment' by the VERSION 15.293 Wave 1 audit "
                    "(en systematically translates an adjacent line's Hebrew instead of its own)",
                ))


def compute_risk(all_entries, daf_order, rashi_by_daf, lines_by_daf, semantic_profile, step1_provenance):
    risk_by_id = defaultdict(list)

    lines_by_daf_lookup = lines_by_daf

    for e in all_entries:
        he, en = e["he"], e["en"]
        for tag, weight, reason in detect_empty(en):
            risk_by_id[e["id"]].append((tag, weight, reason))
        for tag, weight, reason in detect_identical_to_hebrew(he, en):
            risk_by_id[e["id"]].append((tag, weight, reason))
        for tag, weight, reason in detect_hebrew_leakage(en):
            risk_by_id[e["id"]].append((tag, weight, reason))
        for tag, weight, reason in detect_length_ratio(he, en):
            risk_by_id[e["id"]].append((tag, weight, reason))
        for tag, weight, reason in detect_truncation(en):
            risk_by_id[e["id"]].append((tag, weight, reason))
        for tag, weight, reason in detect_fragment(en):
            risk_by_id[e["id"]].append((tag, weight, reason))
        for tag, weight, reason in detect_unmatched_punctuation(en):
            risk_by_id[e["id"]].append((tag, weight, reason))
        for tag, weight, reason in detect_mechanical_template(en):
            risk_by_id[e["id"]].append((tag, weight, reason))
        for tag, weight, reason in detect_pronoun_heavy(en):
            risk_by_id[e["id"]].append((tag, weight, reason))

        linked_texts = []
        daf_lines = lines_by_daf_lookup.get(e["daf"], {})
        for lid in e.get("linkedGemaraLineIds", []):
            line = daf_lines.get(lid)
            if line and line.get("en"):
                linked_texts.append(line["en"])
        for tag, weight, reason in detect_possible_copied_gemara(en, linked_texts):
            risk_by_id[e["id"]].append((tag, weight, reason))

    clusters = build_duplicate_clusters(all_entries)
    apply_duplicate_signals(all_entries, clusters, risk_by_id)
    apply_neighboring_duplicate_signals(daf_order, rashi_by_daf, risk_by_id)
    apply_daf_level_signals(daf_order, rashi_by_daf, semantic_profile, step1_provenance, risk_by_id)

    return risk_by_id, clusters


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=str(DATA_DIR))
    ap.add_argument("--top", type=int, default=100)
    opts = ap.parse_args()
    out_dir = Path(opts.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    daf_order, rashi_by_daf, lines_by_daf = load_corpus()
    all_entries = [e for daf in daf_order for e in rashi_by_daf[daf]]
    semantic_profile = load_semantic_profile()
    step1_provenance = load_step1_provenance()

    risk_by_id, clusters = compute_risk(
        all_entries, daf_order, rashi_by_daf, lines_by_daf, semantic_profile, step1_provenance
    )

    per_entry = []
    for e in all_entries:
        signals = risk_by_id.get(e["id"], [])
        score = sum(w for _, w, _ in signals)
        per_entry.append({
            "id": e["id"],
            "daf": e["daf"],
            "vilnaLine": e["vilnaLine"],
            "riskScore": score,
            "riskSignals": [{"tag": t, "weight": w, "reason": r} for t, w, r in signals],
        })
    per_entry.sort(key=lambda x: -x["riskScore"])

    daf_summary = defaultdict(lambda: {"entries": 0, "totalRiskScore": 0, "flaggedEntries": 0, "tagCounts": defaultdict(int)})
    for pe in per_entry:
        s = daf_summary[pe["daf"]]
        s["entries"] += 1
        s["totalRiskScore"] += pe["riskScore"]
        if pe["riskSignals"]:
            s["flaggedEntries"] += 1
        for sig in pe["riskSignals"]:
            s["tagCounts"][sig["tag"]] += 1
    daf_summary_out = {
        daf: {
            "entries": v["entries"],
            "totalRiskScore": v["totalRiskScore"],
            "flaggedEntries": v["flaggedEntries"],
            "avgRiskScore": round(v["totalRiskScore"] / v["entries"], 2) if v["entries"] else 0,
            "tagCounts": dict(v["tagCounts"]),
        }
        for daf, v in daf_summary.items()
    }

    tag_totals = defaultdict(int)
    for pe in per_entry:
        for sig in pe["riskSignals"]:
            tag_totals[sig["tag"]] += 1

    review_queue = per_entry[: opts.top]

    terminology_variance = build_terminology_variance(all_entries)

    risk_report = {
        "schemaVersion": 1,
        "totalEntries": len(all_entries),
        "flaggedEntries": sum(1 for pe in per_entry if pe["riskSignals"]),
        "unflaggedEntries": sum(1 for pe in per_entry if not pe["riskSignals"]),
        "tagTotals": dict(tag_totals),
        "dafSummary": daf_summary_out,
        "reviewQueueTop": review_queue,
        "allEntries": per_entry,
    }
    (out_dir / "rashi-translation-risk-report.json").write_text(
        json.dumps(risk_report, indent=1, ensure_ascii=False) + "\n"
    )

    (out_dir / "rashi-duplicate-clusters.json").write_text(
        json.dumps({"schemaVersion": 1, "clusterCount": len(clusters), "clusters": clusters},
                    indent=1, ensure_ascii=False) + "\n"
    )

    (out_dir / "rashi-terminology-variance.json").write_text(
        json.dumps({"schemaVersion": 1, "watchlist": terminology_variance}, indent=1, ensure_ascii=False) + "\n"
    )

    # Update the Step 1 inventory's riskSignals/riskScore fields
    # in place, without touching reviewStatus or any other field.
    inv = json.loads(INVENTORY_PATH.read_text())
    risk_lookup = {pe["id"]: pe for pe in per_entry}
    for entry in inv["entries"]:
        pe = risk_lookup.get(entry["id"])
        if pe is None:
            continue
        entry["riskScore"] = pe["riskScore"]
        entry["riskSignals"] = pe["riskSignals"]
        # reviewStatus, primaryDisposition, defectTags, reviewerEvidence,
        # repairPR, finalVerificationSHA are deliberately left untouched.
    INVENTORY_PATH.write_text(json.dumps(inv, indent=1, ensure_ascii=False) + "\n")

    print(f"Analyzed {len(all_entries)} entries across {len(daf_order)} daf")
    print(f"Flagged (risk score > 0): {risk_report['flaggedEntries']}  Unflagged: {risk_report['unflaggedEntries']}")
    print(f"Tag totals: {dict(tag_totals)}")
    print(f"Duplicate clusters: {len(clusters)}")
    print(f"Terminology watchlist terms with variance data: {len(terminology_variance)}")
    print(f"Wrote: {out_dir / 'rashi-translation-risk-report.json'}")
    print(f"Wrote: {out_dir / 'rashi-duplicate-clusters.json'}")
    print(f"Wrote: {out_dir / 'rashi-terminology-variance.json'}")
    print(f"Updated: {INVENTORY_PATH} (riskScore/riskSignals only)")


if __name__ == "__main__":
    main()
