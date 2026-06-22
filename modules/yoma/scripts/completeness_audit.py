#!/usr/bin/env python3
"""
completeness_audit.py — the REVERSE of validate_sefaria.py.

validate_sefaria.py asks: "is every he: field in learning_data.js found in Sefaria?" (correctness)
This script asks:          "is every Sefaria segment represented in learning_data.js?" (completeness)

For each daf, it fetches the live Sefaria segments and, for each segment, measures how
much of it is quoted somewhere in that daf's he: fields. It reports:
  - FULLY/HEAVILY covered  (segment well represented)
  - PARTIAL                (a chunk is quoted, rest omitted — normal for a study companion)
  - MISSING                (no meaningful part of the segment appears anywhere)

A study companion intentionally selects representative sugya texts, so PARTIAL is expected.
MISSING segments are the real signal: a whole Gemara line with nothing quoted from it.
"""

import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request

DATA_JS = "learning_data.js"


def strip_html(s):
    return re.sub(r"<[^>]+>", "", s)


def normalize(s):
    s = strip_html(s)
    s = unicodedata.normalize("NFC", s)
    return re.sub(r"\s+", " ", s).strip()


def fetch_segments(daf_id):
    url = f"https://www.sefaria.org/api/texts/Yoma.{daf_id}?lang=he&context=0"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "YomaAudit/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return [normalize(s) for s in data.get("he", []) if s.strip()], None
    except urllib.error.URLError as e:
        return None, f"network: {e}"
    except Exception as e:
        return None, str(e)


# ---- reuse the exact parser logic from validate_sefaria.py -----------------
def parse_content_fields(content):
    raw_lines = content.split("\n")
    daf_re = re.compile(r'^\s*"(\d+[ab])":\s*\{')
    he_re = re.compile(r'\bhe\s*:\s*"((?:[^"\\]|\\.)*)"')
    current_daf = None
    in_lines = False
    depth = 0
    for lineno, line in enumerate(raw_lines, 1):
        m = daf_re.match(line)
        if m:
            current_daf = m.group(1)
            in_lines = False
            depth = 0
            continue
        if current_daf is None:
            continue
        if not in_lines and re.search(r'\blines\s*:\s*\[', line):
            in_lines = True
            depth = line.count("[") - line.count("]")
            continue
        if in_lines:
            depth += line.count("[") - line.count("]")
            if depth <= 0:
                in_lines = False
                continue
            m = he_re.search(line)
            if not m:
                continue
            raw = m.group(1)
            text = raw.replace('\\"', '"').replace("\\\\", "\\").replace("\\n", " ").strip()
            if len(text) >= 5:
                yield lineno, current_daf, text


def word_coverage(segment, joined_ours):
    """
    Fraction of the segment's word-windows that appear in our joined text.
    Uses a sliding 4-word window over the segment; a window 'hits' if it is a
    substring of our joined he: text. Returns coverage in [0,1].
    """
    words = segment.split()
    if not words:
        return 1.0
    if len(words) <= 4:
        return 1.0 if segment in joined_ours else 0.0
    windows = [" ".join(words[i:i + 4]) for i in range(len(words) - 3)]
    hits = sum(1 for w in windows if w in joined_ours)
    return hits / len(windows)


def main():
    target_daf = set(sys.argv[1:]) if len(sys.argv) > 1 else None

    with open(DATA_JS, encoding="utf-8") as f:
        content = f.read()

    by_daf = {}
    for lineno, daf, text in parse_content_fields(content):
        if target_daf and daf not in target_daf:
            continue
        by_daf.setdefault(daf, []).append(normalize(text))

    daf_list = sorted(by_daf.keys(), key=lambda x: (int(x[:-1]), x[-1]))
    print(f"Completeness audit across {len(daf_list)} daf...\n")

    missing_total = 0
    partial_total = 0
    covered_total = 0
    seg_total = 0
    missing_report = []
    skipped = []

    for daf_id in daf_list:
        segs, err = fetch_segments(daf_id)
        time.sleep(0.3)
        if err:
            print(f"  {daf_id:4s}  SKIP ({err})")
            skipped.append(daf_id)
            continue

        joined_ours = " ".join(by_daf[daf_id])
        n_missing = n_partial = n_covered = 0
        daf_missing = []

        for i, seg in enumerate(segs):
            seg_total += 1
            cov = word_coverage(seg, joined_ours)
            if cov >= 0.6:
                n_covered += 1
            elif cov > 0.0:
                n_partial += 1
            else:
                n_missing += 1
                daf_missing.append((i, seg))

        missing_total += n_missing
        partial_total += n_partial
        covered_total += n_covered

        status = "✓" if n_missing == 0 else "✗"
        print(f"  {daf_id:4s}  {status}  {len(segs):2d} segs | "
              f"covered {n_covered}  partial {n_partial}  MISSING {n_missing}")

        for idx, seg in daf_missing:
            missing_report.append((daf_id, idx, seg))

    print()
    print(f"Sefaria segments total : {seg_total}")
    print(f"  well-covered (>=60%) : {covered_total}")
    print(f"  partial   (some text): {partial_total}")
    print(f"  MISSING   (no quote) : {missing_total}")
    if skipped:
        print(f"  skipped (network)    : {', '.join(skipped)}")

    if missing_report:
        print("\n--- MISSING segments (no meaningful text in learning_data.js) ---\n")
        for daf_id, idx, seg in missing_report:
            preview = seg[:90] + ("…" if len(seg) > 90 else "")
            print(f"  [{daf_id}] seg #{idx}: {preview}")

    print("\n(PARTIAL is normal — a study companion quotes selected lines, not whole segments.)")


if __name__ == "__main__":
    main()
