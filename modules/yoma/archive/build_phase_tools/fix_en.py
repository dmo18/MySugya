#!/usr/bin/env python3
"""
fix_en.py — replace mismatched en: translations with Sefaria's English at the
same segment index as the field's he: text.

Two buckets:
  AUTO   — the field is the only one mapped to its segment range: its en: is
           replaced verbatim with Sefaria text[i..j].
  MANUAL — the field shares its segment range with another field (a split
           segment): the segment's English must be hand-split. These are
           written to /tmp/en_manual.json for editing, then applied with
           scripts/apply_en.py.

Usage:
  python3 scripts/fix_en.py            # dry-run
  python3 scripts/fix_en.py --apply    # write AUTO fixes to source_store.js
"""

import json
import re
import sys
import time
import unicodedata
import urllib.request

DATA_JS = "source_store.js"
HEBL = re.compile(r"[א-ת]")


def strip_html(s):
    return re.sub(r"<[^>]+>", "", s)


def norm(s):
    s = strip_html(s)
    s = unicodedata.normalize("NFC", s)
    s = s.replace("’", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", s).strip()


def letters_of(s):
    return "".join(ch for ch in unicodedata.normalize("NFC", s) if HEBL.match(ch))


def fetch(daf_id):
    url = f"https://www.sefaria.org/api/texts/Yoma.{daf_id}?context=0"
    req = urllib.request.Request(url, headers={"User-Agent": "YomaEnFix/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    he_raw = data.get("he", [])
    en_raw = data.get("text", [])
    while len(en_raw) < len(he_raw):
        en_raw.append("")
    return he_raw, en_raw


def encode_js(txt):
    return txt.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def parse_fields(content):
    """Yield (daf, he_span, en_span, he_text, en_text) for line objects.
    Spans are (value_start, value_end) into content for the quoted value."""
    daf_re = re.compile(r'^\s*"(\d+[ab])":\s*\{')
    raw = content.split("\n")
    offsets = []
    off = 0
    for l in raw:
        offsets.append(off)
        off += len(l) + 1

    he_re = re.compile(r'\bhe\s*:\s*"((?:[^"\\]|\\.)*)"')
    en_re = re.compile(r'\ben\s*:\s*"((?:[^"\\]|\\.)*)"')

    daf = None
    in_lines = False
    depth = 0
    pend = None
    for i, l in enumerate(raw):
        m = daf_re.match(l)
        if m:
            daf = m.group(1)
            in_lines = False
            pend = None
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
                pend = None
                continue
            hm = he_re.search(l)
            if hm:
                vs = offsets[i] + hm.start(1)
                ve = offsets[i] + hm.end(1)
                txt = hm.group(1).replace('\\"', '"').replace("\\\\", "\\").replace("\\n", " ")
                pend = (vs, ve, txt, i + 1)
            em = en_re.search(l)
            if em and pend:
                vs = offsets[i] + em.start(1)
                ve = offsets[i] + em.end(1)
                txt = em.group(1).replace('\\"', '"').replace("\\\\", "\\").replace("\\n", " ")
                yield (daf, pend, (vs, ve, txt, i + 1))
                pend = None


def main():
    apply_mode = "--apply" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    target = set(args) if args else None

    with open(DATA_JS, encoding="utf-8") as f:
        content = f.read()

    by_daf = {}
    for daf, he_f, en_f in parse_fields(content):
        if target and daf not in target:
            continue
        by_daf.setdefault(daf, []).append((he_f, en_f))

    auto = []      # (start, end, replacement_raw)
    manual = []    # dicts for the work file
    stats = {"checked": 0, "auto": 0, "manual": 0, "noen": 0}

    for daf in sorted(by_daf, key=lambda x: (int(x[:-1]), x[-1])):
        try:
            he_raw, en_raw = fetch(daf)
        except Exception as e:
            print(f"[{daf}] SKIP fetch: {e}")
            continue
        time.sleep(0.3)
        seg_letters = [letters_of(s) for s in he_raw]
        stream = "".join(seg_letters)
        starts = []
        off = 0
        for sl in seg_letters:
            starts.append(off)
            off += len(sl)

        # locate every field
        fields = []
        for he_f, en_f in by_daf[daf]:
            tgt = letters_of(he_f[2])
            rng = None
            if tgt:
                p = stream.find(tgt)
                if p != -1:
                    i = max(k for k, s in enumerate(starts) if s <= p)
                    j = max(k for k, s in enumerate(starts) if s <= p + len(tgt) - 1)
                    rng = (i, j)
            fields.append((he_f, en_f, rng))

        # count fields per segment
        seg_users = {}
        for _, _, rng in fields:
            if rng:
                for k in range(rng[0], rng[1] + 1):
                    seg_users[k] = seg_users.get(k, 0) + 1

        for he_f, en_f, rng in fields:
            if rng is None:
                continue
            stats["checked"] += 1
            i, j = rng
            expected_raw = " ".join(s for s in en_raw[i:j + 1] if s.strip())
            if not norm(expected_raw):
                stats["noen"] += 1
                continue
            ours = norm(en_f[2])
            exp = norm(expected_raw)
            if ours == exp or ours in exp or exp in ours:
                continue
            shared = any(seg_users[k] > 1 for k in range(i, j + 1))
            if shared:
                stats["manual"] += 1
                manual.append({
                    "daf": daf, "jsline": en_f[3],
                    "segs": f"{i+1}..{j+1}",
                    "he": he_f[2][:200],
                    "current_en": en_f[2][:200],
                    "sefaria_en": expected_raw,
                    "new_en": "",
                })
            else:
                stats["auto"] += 1
                auto.append((en_f[0], en_f[1], encode_js(expected_raw)))
                print(f"[{daf}] js:{en_f[3]} AUTO  segs {i+1}..{j+1}")

    print(f"\nchecked {stats['checked']}  auto-fix {stats['auto']}  "
          f"manual {stats['manual']}  no-sefaria-english {stats['noen']}")

    if manual:
        with open("/tmp/en_manual.json", "w", encoding="utf-8") as f:
            json.dump(manual, f, ensure_ascii=False, indent=1)
        print(f"manual cases written to /tmp/en_manual.json")

    if apply_mode and auto:
        auto.sort(key=lambda x: x[0], reverse=True)
        for s, e, repl in auto:
            content = content[:s] + repl + content[e:]
        with open(DATA_JS, "w", encoding="utf-8") as f:
            f.write(content)
        print("source_store.js written.")
    elif not apply_mode:
        print("(dry-run — use --apply to write AUTO fixes)")


if __name__ == "__main__":
    main()
