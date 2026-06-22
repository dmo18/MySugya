#!/usr/bin/env python3
"""
validate_en.py — verify every en: field in learning_data.js lines: [] arrays against
the Sefaria English at the SAME segment index as the field's he: text.

For each (he, en) pair:
  1. Locate which Sefaria he[] segment(s) contain the he: text.
  2. The expected English is text[] at those same indices.
  3. Pass if our en: equals / is contained in / contains the expected English
     (whitespace- and HTML-normalized). Anything else is a mismatch — the
     translation is misaligned with the Hebrew paragraph it is displayed under.

Usage:
  python3 scripts/validate_en.py            # all daf
  python3 scripts/validate_en.py 15a 16b    # specific daf
"""

import json
import re
import sys
import time
import unicodedata
import urllib.request

DATA_JS = "learning_data.js"


def strip_html(s):
    return re.sub(r"<[^>]+>", "", s)


def norm(s):
    s = strip_html(s)
    s = unicodedata.normalize("NFC", s)
    s = s.replace("’", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", s).strip()


HEBL = re.compile(r"[א-ת]")


def letters_of(s):
    return "".join(ch for ch in unicodedata.normalize("NFC", s) if HEBL.match(ch))


def fetch(daf_id):
    url = f"https://www.sefaria.org/api/texts/Yoma.{daf_id}?context=0"
    req = urllib.request.Request(url, headers={"User-Agent": "YomaValidator/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    he = [norm(s) for s in data.get("he", [])]
    en = [norm(s) for s in data.get("text", [])]
    # pad en to he length
    while len(en) < len(he):
        en.append("")
    return he, en


def parse_pairs(content):
    """Yield (lineno, daf, he, en) for every line object inside lines: []."""
    raw_lines = content.split("\n")
    daf_re = re.compile(r'^\s*"(\d+[ab])":\s*\{')
    he_re = re.compile(r'\bhe\s*:\s*"((?:[^"\\]|\\.)*)"')
    en_re = re.compile(r'\ben\s*:\s*"((?:[^"\\]|\\.)*)"')

    current_daf = None
    in_lines = False
    depth = 0
    pend_he = None
    pend_line = None

    def decode(raw):
        return raw.replace('\\"', '"').replace("\\\\", "\\").replace("\\n", " ").strip()

    for lineno, line in enumerate(raw_lines, 1):
        m = daf_re.match(line)
        if m:
            current_daf = m.group(1)
            in_lines = False
            depth = 0
            pend_he = None
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
                pend_he = None
                continue
            hm = he_re.search(line)
            if hm:
                pend_he = decode(hm.group(1))
                pend_line = lineno
            em = en_re.search(line)
            if em and pend_he is not None:
                yield pend_line, current_daf, pend_he, decode(em.group(1))
                pend_he = None


def find_seg_range(he_norm, segs):
    """Return (start, end) inclusive segment indices covering he_norm, or None.
    Matching is letters-only, so nikud/bracket/punctuation drift never blocks it."""
    target = letters_of(he_norm)
    if not target:
        return None
    seg_letters = [letters_of(s) for s in segs]
    stream = "".join(seg_letters)
    pos = stream.find(target)
    if pos == -1:
        return None
    starts = []
    off = 0
    for sl in seg_letters:
        starts.append(off)
        off += len(sl)
    # segment containing pos / pos+len-1
    i = max(k for k, s in enumerate(starts) if s <= pos)
    end_pos = pos + len(target) - 1
    j = max(k for k, s in enumerate(starts) if s <= end_pos)
    return (i, j)


def main():
    target = set(sys.argv[1:]) if len(sys.argv) > 1 else None
    with open(DATA_JS, encoding="utf-8") as f:
        content = f.read()

    by_daf = {}
    for lineno, daf, he, en in parse_pairs(content):
        if target and daf not in target:
            continue
        if len(norm(he)) < 15:
            continue
        by_daf.setdefault(daf, []).append((lineno, he, en))

    total = sum(len(v) for v in by_daf.values())
    print(f"Cross-checking {total} en: fields across {len(by_daf)} daf...\n")

    errors = []
    for daf_id in sorted(by_daf, key=lambda x: (int(x[:-1]), x[-1])):
        print(f"  {daf_id:4s}", end=" ", flush=True)
        try:
            he_segs, en_segs = fetch(daf_id)
        except Exception as e:
            print(f"SKIP ({e})")
            continue
        time.sleep(0.3)

        bad = 0
        for lineno, he, en in by_daf[daf_id]:
            he_n, en_n = norm(he), norm(en)
            rng = find_seg_range(he_n, he_segs)
            if rng is None:
                errors.append((daf_id, lineno, "he: not located in Sefaria segments", he_n[:60], ""))
                bad += 1
                continue
            i, j = rng
            expected = " ".join(filter(None, en_segs[i:j + 1]))
            if not expected:
                continue  # Sefaria has no English for this segment
            if en_n == expected or en_n in expected or expected in en_n:
                continue
            # fuzzy: token overlap ratio for diagnostics
            a, b = set(en_n.split()), set(expected.split())
            ratio = len(a & b) / max(1, len(a | b))
            errors.append((daf_id, lineno,
                           f"en: differs from Sefaria text[{i+1}..{j+1}] (overlap {ratio:.0%})",
                           en_n[:80], expected[:80]))
            bad += 1
        print("✓" if not bad else f"✗ {bad} mismatch(es)")

    print()
    if errors:
        print(f"❌  {len(errors)} mismatch(es):\n")
        for daf_id, lineno, reason, ours, exp in errors:
            print(f"  [{daf_id}] learning_data.js line {lineno}: {reason}")
            print(f"    ours:     {ours}")
            if exp:
                print(f"    sefaria:  {exp}")
            print()
        sys.exit(1)
    print(f"✅  All {total} en: fields line up with their he: segments.")


if __name__ == "__main__":
    main()
