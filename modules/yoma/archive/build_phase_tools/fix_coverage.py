#!/usr/bin/env python3
"""
fix_coverage.py — close Vilna line-coverage gaps by tiling each daf's fields.

Every he: field is located in the daf's Sefaria text stream. Each field is
then extended forward (with verbatim Sefaria raw text) to reach the next
field's start; the first field is extended back to the page start and the
last to the page end. Result: the concatenation of all fields reproduces the
complete daf — every Vilna line is covered.

Fields whose letters are unchanged by tiling are left untouched (preserving
existing line breaks). Run daftext_align.py --all --apply --force afterwards
to re-break and re-stamp vilna_line.

Usage:
  python3 scripts/fix_coverage.py 13a            # dry-run, one daf
  python3 scripts/fix_coverage.py --all --apply
"""

import json
import re
import sys
import time
import unicodedata
import urllib.request

DATA_JS = "source_store.js"
HEBL = re.compile(r"[א-ת]")
COMBINING = re.compile(r"[֑-ׇ]")
CLOSE_PUNCT = set('.,!?:;״׳"\')]}—־')
OPEN_PUNCT = set('״׳"\'([{')
CLOSE_TAGS = ("</b>", "</strong>", "</big>", "</i>", "<br>")
OPEN_TAGS = ("<b>", "<strong>", "<big>", "<i>")


def letters_of(s):
    return "".join(ch for ch in unicodedata.normalize("NFC", s) if HEBL.match(ch))


def fetch_raw(daf_id):
    url = f"https://www.sefaria.org/api/texts/Yoma.{daf_id}?lang=he&context=0"
    req = urllib.request.Request(url, headers={"User-Agent": "YomaCoverage/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return [unicodedata.normalize("NFC", s) for s in data.get("he", []) if s.strip()]


def encode_js(txt):
    return txt.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def parse_fields(content):
    """Yield (daf, value_start, value_end, decoded_text) for he: in lines arrays."""
    raw = content.split("\n")
    offsets = []
    off = 0
    for l in raw:
        offsets.append(off)
        off += len(l) + 1
    daf_re = re.compile(r'^\s*"(\d+[ab])":\s*\{')
    he_re = re.compile(r'\bhe\s*:\s*"((?:[^"\\]|\\.)*)"')
    daf = None
    in_lines = False
    depth = 0
    for i, l in enumerate(raw):
        m = daf_re.match(l)
        if m:
            daf = m.group(1)
            in_lines = False
            continue
        if daf is None:
            continue
        if not in_lines and re.search(r'\blines\s*:\s*\[', l):
            in_lines = True
            depth = l.count("[") - l.count("]")
            continue
        if in_lines:
            depth += l.count("[") - l.count("]")
            if depth <= 0:
                in_lines = False
                continue
            hm = he_re.search(l)
            if hm:
                vs = offsets[i] + hm.start(1)
                ve = offsets[i] + hm.end(1)
                txt = hm.group(1).replace('\\"', '"').replace("\\\\", "\\").replace("\\n", " ")
                yield (daf, vs, ve, txt)


def build_stream(segs):
    """joined raw + list of raw positions of each Hebrew letter."""
    joined = " ".join(segs)
    pos = [i for i, ch in enumerate(joined) if HEBL.match(ch)]
    stream = "".join(joined[i] for i in pos)
    return joined, pos, stream


def fatten(joined, start, end):
    """Expand [start, end) over attached nikud, punctuation and tags."""
    # forward: combining marks first, then closing punct/tags (not crossing letters)
    n = len(joined)
    while end < n and COMBINING.match(joined[end]):
        end += 1
    moved = True
    while moved:
        moved = False
        while end < n and joined[end] in CLOSE_PUNCT:
            end += 1
            moved = True
        for t in CLOSE_TAGS:
            if joined.startswith(t, end):
                end += len(t)
                moved = True
    # backward: opening punct/tags directly attached
    moved = True
    while moved:
        moved = False
        while start > 0 and joined[start - 1] in OPEN_PUNCT:
            start -= 1
            moved = True
        for t in OPEN_TAGS:
            if start >= len(t) and joined[start - len(t):start] == t:
                start -= len(t)
                moved = True
    return start, end


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    apply_mode = "--apply" in sys.argv
    do_all = "--all" in sys.argv

    with open(DATA_JS, encoding="utf-8") as f:
        content = f.read()

    by_daf = {}
    for daf, vs, ve, txt in parse_fields(content):
        by_daf.setdefault(daf, []).append([vs, ve, txt])

    if do_all:
        dafs = sorted(by_daf, key=lambda x: (int(x[:-1]), x[-1]))
    else:
        dafs = args
    if not dafs:
        print("give daf names or --all")
        sys.exit(1)

    patches = []
    for daf in dafs:
        if daf not in by_daf:
            continue
        try:
            segs = fetch_raw(daf)
        except Exception as e:
            print(f"[{daf}] SKIP fetch: {e}")
            continue
        time.sleep(0.25)
        joined, pos, stream = build_stream(segs)

        located = []
        cursor = 0
        for f in by_daf[daf]:
            tgt = letters_of(f[2])
            if not tgt:
                continue
            p = stream.find(tgt, cursor)
            if p == -1:
                p = stream.find(tgt)
            if p == -1:
                print(f"[{daf}] WARN: field not in stream: {tgt[:30]}…")
                continue
            located.append((p, p + len(tgt), f))
            cursor = p
        located.sort(key=lambda x: x[0])

        changed = 0
        for idx, (s, e, f) in enumerate(located):
            new_s = 0 if idx == 0 else s
            new_e = located[idx + 1][0] if idx + 1 < len(located) else len(stream)
            if new_e < e:
                new_e = e
            if (new_s, new_e) == (s, e):
                continue
            raw_s = pos[new_s]
            raw_e = pos[new_e - 1] + 1
            raw_s, raw_e = fatten(joined, raw_s, raw_e)
            new_he = re.sub(r"\s+", " ", joined[raw_s:raw_e]).strip()
            if letters_of(new_he) == letters_of(f[2]):
                continue
            patches.append((f[0], f[1], encode_js(new_he)))  # (vs, ve, repl)
            changed += 1
            add = (new_s != s) and "head" or ""
            add += "+" if (new_e != e and new_s != s) else ""
            add += (new_e != e) and "tail" or ""
            print(f"[{daf}] extend {add}: +{(s-new_s)+(new_e-e)} letters  "
                  f"“{letters_of(f[2])[:25]}…”")
        if changed:
            print(f"[{daf}] {changed} field(s) extended")

    print(f"\n{len(patches)} field rewrites")
    if apply_mode and patches:
        patches.sort(key=lambda x: x[0], reverse=True)
        for vs, ve, repl in patches:
            assert content[ve] == '"', "patch offsets corrupt — aborting"
            content = content[:vs] + repl + content[ve:]
        with open(DATA_JS, "w", encoding="utf-8") as f:
            f.write(content)
        print("source_store.js written.")
    elif not apply_mode:
        print("(dry-run — use --apply to write)")


if __name__ == "__main__":
    main()
