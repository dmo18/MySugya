#!/usr/bin/env python3
"""
daftext_align.py — align learning_data.js he: fields to the authoritative Vilna
line files in assets/daftexts/<daf>.txt, inserting \n at exact Vilna line
boundaries and recording vilna_line (the starting Vilna line number) on
each line entry.

Matching is token-based on Hebrew letters only (nikud, punctuation and
quotes ignored) and tolerates the txt files' Vilna conventions:
  - abbreviations:  א"ר ↔ אמר רבי, למ"ד ↔ למאן דאמר, ר' ↔ רבי …
    (generic rule: the abbreviation's letters must split into prefixes
    of the consecutive expanded words)
  - spelling drift: תרווייהו ↔ תרוייהו (edit distance ≤1, ≤2 for long)
  - merged/split words across the two sources

The learning_data.js characters themselves are never altered — only spaces flip
to \n and back. Safety invariant (asserted per field): the new string
with whitespace normalized equals the old string normalized the same
way, so Sefaria validation cannot break.

Usage:
    python3 scripts/daftext_align.py 2a 2b 3a        # dry-run, report only
    python3 scripts/daftext_align.py 2a 2b 3a --apply
    python3 scripts/daftext_align.py --all [--apply]
"""
import argparse, os, re, sys
from functools import lru_cache

DATA = 'learning_data.js'
TXTDIR = 'assets/daftexts'
HEB = re.compile(r'[א-ת]')
ABBREV_MARKS = set('"\'״׳')

# ---------------------------------------------------------------------------
# txt parsing
# ---------------------------------------------------------------------------

def parse_txt(daf):
    path = os.path.join(TXTDIR, f'{daf}.txt')
    if not os.path.exists(path):
        return None
    lines = []
    with open(path, encoding='utf-8') as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            m = re.match(r'(\d+)\s+(.*)$', raw)
            if not m:
                continue
            lines.append((int(m.group(1)), m.group(2)))
    return lines

def letters_of(text):
    return ''.join(ch for ch in text if HEB.match(ch))

def is_abbrev(word):
    """Abbreviation marks BETWEEN letters (א"ר) or a trailing geresh (ר')."""
    letters_seen = False
    for i, ch in enumerate(word):
        if HEB.match(ch):
            letters_seen = True
        elif ch in ABBREV_MARKS and letters_seen:
            rest = word[i + 1:]
            if any(HEB.match(c) for c in rest):
                return True            # mark between letters: gershayim
            if ch in "'׳":
                return True            # trailing single geresh: ר' גמ'
    return False

def txt_tokens(txt_lines, offset=0):
    """[(letters, abbrev?, line_no)] for every letter-bearing txt word."""
    toks = []
    for n, text in txt_lines:
        for w in text.split():
            letters = letters_of(w)
            if not letters:
                continue
            toks.append((letters, is_abbrev(w), n + offset))
    return toks

NEXT_DAF = {}
def build_daf_order():
    def key(d):
        return (int(d[:-1]), d[-1])
    dafs = sorted((f[:-4] for f in os.listdir(TXTDIR) if f.endswith('.txt')), key=key)
    for a, b in zip(dafs, dafs[1:]):
        NEXT_DAF[a] = b

# ---------------------------------------------------------------------------
# token similarity
# ---------------------------------------------------------------------------

def edit1(a, b, maxd):
    if abs(len(a) - len(b)) > maxd:
        return False
    # bounded Levenshtein
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        rowmin = i
        for j, cb in enumerate(b, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
            rowmin = min(rowmin, cur[j])
        if rowmin > maxd:
            return False
        prev = cur
    return prev[-1] <= maxd

# Explicit numeric and other abbreviation expansions that prefix-matching cannot handle.
# Keys are unvowelized abbreviation letter sequences. Values are lists of possible
# expansions, each a tuple of unvowelized word prefixes that match the learning_data.js tokens.
EXPLICIT_ABBREV = {
    # Hebrew numerals whose letters don't prefix the full words
    'יא':  [('אחת', 'עשרה'), ('אחד', 'עשר'), ('אחת', 'עשר'), ('אחד', 'עשרה')],
    'יב':  [('שנים', 'עשר'), ('שתים', 'עשרה'), ('שניים', 'עשר'), ('שתיים', 'עשרה')],
    'יג':  [('שלשה', 'עשר'), ('שלש', 'עשרה'), ('שלושה', 'עשר'), ('שלוש', 'עשרה')],
    'יד':  [('ארבעה', 'עשר'), ('ארבע', 'עשרה')],
    'טו':  [('חמשה', 'עשר'), ('חמש', 'עשרה'), ('חמישה', 'עשר')],
    'טז':  [('ששה', 'עשר'), ('שש', 'עשרה')],
    'יז':  [('שבעה', 'עשר'), ('שבע', 'עשרה')],
    'יח':  [('שמונה', 'עשר'), ('שמונה', 'עשרה')],
    'יט':  [('תשעה', 'עשר'), ('תשע', 'עשרה')],
    # Prefixed variants: ו+number for "and N"
    'ויא': [('ואחת', 'עשרה'), ('ואחד', 'עשר')],
    'ויב': [('ושנים', 'עשר'), ('ושתים', 'עשרה')],
    'ויג': [('ושלשה', 'עשר'), ('ושלש', 'עשרה')],
    'ויד': [('וארבעה', 'עשר'), ('וארבע', 'עשרה')],
    'ויח': [('ושמונה', 'עשר'), ('ושמונה', 'עשרה')],
    # Single-digit numbers as single-letter abbreviations
    'ג':   [('שלש',), ('שלשה',), ('שלוש',), ('שלושה',)],
    'ח':   [('שמונה',)],
    'ט':   [('תשע',), ('תשעה',)],
    'י':   [('עשר',), ('עשרה',)],
    # Common abbreviations with ד prefix
    'דתר': [('תנו', 'רבנן')],   # ד + ת"ר
    # Word variants: daftext spelling vs Sefaria spelling
    # (handled via tok_match variants below)
}

# Direct word substitutions: daftext token -> acceptable learning_data.js token
# These handle cases where the words differ but are semantically identical
TOKEN_SUBS = {
    'תרגומא': 'תרגמה',  # Aramaic word variant
    'כותיים': 'גוים',    # Sefaria uses גוים, daftext uses כותיים
    'כותים':  'גוים',
    'כותי':   'גוי',
    'בעי':    'בעו',     # Aramaic verb variant (beo/bei)
}

# Section header words that appear in learning_data.js he: fields but not in daftext.
# These are skipped at zero alignment cost.
SECTION_HEADERS = frozenset({'מתני', 'גמ'})

def tok_match(a, b):
    if a == b:
        return True
    # Check explicit token substitutions (daftext word -> learning_data.js word)
    if TOKEN_SUBS.get(a) == b or TOKEN_SUBS.get(b) == a:
        return True
    n = max(len(a), len(b))
    if n >= 7:
        return edit1(a, b, 2)
    if n >= 4:
        return edit1(a, b, 1)
    return False

def abbrev_expand(abbr, words):
    """Can abbr's letters split into nonempty prefixes of consecutive words?
    Also checks EXPLICIT_ABBREV for numeric and special cases.
    Returns number of words consumed, or 0."""
    # Check explicit table first (handles numeric abbreviations)
    if abbr in EXPLICIT_ABBREV:
        for expansion in EXPLICIT_ABBREV[abbr]:
            k = len(expansion)
            if k <= len(words):
                if all(words[i].startswith(exp) or words[i] == exp
                       for i, exp in enumerate(expansion)):
                    return k

    @lru_cache(maxsize=None)
    def go(ai, wi):
        if ai == len(abbr):
            return wi
        if wi >= len(words):
            return 0
        w = words[wi]
        for plen in range(1, min(len(w), len(abbr) - ai) + 1):
            if abbr[ai:ai + plen] == w[:plen]:
                r = go(ai + plen, wi + 1)
                if r:
                    return r
        return 0
    return go(0, 0)

# ---------------------------------------------------------------------------
# field ↔ txt alignment (cost-limited DP)
# ---------------------------------------------------------------------------

def align_tokens(dtoks, ttoks, tstart, budget):
    """Align all of dtoks against ttoks starting at tstart.
    Returns list line_of[di] (txt line per data token) or None."""
    nd, nt = len(dtoks), len(ttoks)
    sys.setrecursionlimit(20000)
    memo = {}

    def go(di, ti, cost):
        if cost > budget:
            return None
        if di == nd:
            return []
        key = (di, ti)
        if key in memo and memo[key] <= cost:
            return None
        memo[key] = cost
        if ti < nt:
            tl, tab, tline = ttoks[ti]
            d = dtoks[di]
            if tok_match(tl, d):
                r = go(di + 1, ti + 1, cost)
                if r is not None:
                    return [tline] + r
            if tab:
                k = abbrev_expand(tl, tuple(dtoks[di:di + 5]))
                if k:
                    r = go(di + k, ti + 1, cost)
                    if r is not None:
                        return [tline] * k + r
            # txt token = two data tokens merged
            if di + 1 < nd and tok_match(tl, d + dtoks[di + 1]):
                r = go(di + 2, ti + 1, cost)
                if r is not None:
                    return [tline, tline] + r
            # data token = two txt tokens merged
            if ti + 1 < nt and tok_match(tl + ttoks[ti + 1][0], d):
                r = go(di + 1, ti + 2, cost)
                if r is not None:
                    return [tline] + r
            # skip a txt token (extra word in print)
            r = go(di, ti + 1, cost + 1)
            if r is not None:
                return r
        # skip a section-header data token at zero cost (e.g. מתני׳, גמ׳)
        if dtoks[di] in SECTION_HEADERS:
            r = go(di + 1, ti, cost)
            if r is not None:
                tline = ttoks[ti][2] if ti < nt else ttoks[-1][2]
                return [tline] + r
        # skip a data token (word missing from print)
        r = go(di + 1, ti, cost + 1)
        if r is not None:
            tline = ttoks[ti][2] if ti < nt else ttoks[-1][2]
            return [tline] + r
        return None

    return go(0, tstart, 0)

def find_alignment(dtoks, ttoks, cursor):
    budget = max(2, len(dtoks) // 8)
    order = list(range(cursor, len(ttoks))) + list(range(0, cursor))
    # Skip leading section-header tokens for plausibility check
    di0 = 0
    while di0 < len(dtoks) and dtoks[di0] in SECTION_HEADERS:
        di0 += 1
    d0 = dtoks[di0] if di0 < len(dtoks) else dtoks[0]
    for ts in order:
        tl, tab, _ = ttoks[ts]
        plausible = (tok_match(tl, d0)
                     or (tab and abbrev_expand(tl, tuple(dtoks[di0:di0 + 5])))
                     or (di0 + 1 < len(dtoks) and tok_match(tl, d0 + dtoks[di0 + 1])))
        if not plausible:
            continue
        lines = align_tokens(dtoks, ttoks, ts, budget)
        if lines is not None:
            return lines, ts
    return None, None

# ---------------------------------------------------------------------------
# learning_data.js scanning (string-aware)
# ---------------------------------------------------------------------------

def daf_section(content, daf):
    m = re.search(rf'// YOMA {daf}\b', content)
    if not m:
        return None
    start = m.start()
    nxt = re.search(r'// YOMA \d+[ab]\b', content[m.end():])
    end = m.end() + nxt.start() if nxt else len(content)
    return start, end

def scan_lines_arrays(content, start, end):
    regions = []
    i = start
    while True:
        j = content.find('lines: [', i)
        if j < 0 or j >= end:
            break
        pos = content.index('[', j)
        depth = 0
        in_str = False
        while pos < end:
            c = content[pos]
            if in_str:
                if c == '\\':
                    pos += 2
                    continue
                if c == '"':
                    in_str = False
            else:
                if c == '"':
                    in_str = True
                elif c == '[':
                    depth += 1
                elif c == ']':
                    depth -= 1
                    if depth == 0:
                        break
            pos += 1
        regions.append((j, pos))
        i = pos
    return regions

def find_he_fields(content, regions):
    fields = []
    for rstart, rend in regions:
        i = rstart
        while True:
            j = content.find('he: "', i)
            if j < 0 or j >= rend:
                break
            vs = j + len('he: "')
            k = vs
            while k < rend:
                c = content[k]
                if c == '\\':
                    k += 2
                    continue
                if c == '"':
                    break
                k += 1
            fields.append((vs, k))
            i = k
    return fields

def decode_js(src):
    out = []
    i = 0
    while i < len(src):
        c = src[i]
        if c == '\\' and i + 1 < len(src):
            n = src[i + 1]
            out.append({'n': '\n', '"': '"', '\\': '\\'}.get(n, '\\' + n))
            i += 2
        else:
            out.append(c)
            i += 1
    return ''.join(out)

def encode_js(txt):
    return txt.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')

def norm_ws(s):
    return re.sub(r'[\n ]+', ' ', s).strip()

# ---------------------------------------------------------------------------
# rebuild
# ---------------------------------------------------------------------------

def rebreak(flat, line_of):
    """flat: decoded field text, single-spaced. line_of: txt line per
    letter-bearing token. Returns (new_text, vstart, vend)."""
    words = flat.split(' ')
    # map each word to a line; punctuation-only words attach forward
    wlines = []
    li = 0
    letter_idx = [i for i, w in enumerate(words) if letters_of(w)]
    for i, w in enumerate(words):
        if letters_of(w):
            wlines.append(line_of[li])
            li += 1
        else:
            wlines.append(None)
    # fill punctuation-only words with the NEXT letter word's line
    nxt = None
    for i in range(len(words) - 1, -1, -1):
        if wlines[i] is None:
            wlines[i] = nxt if nxt is not None else (wlines[0] or 0)
        else:
            nxt = wlines[i]
    out = [words[0]]
    cur = wlines[0]
    for w, wl in zip(words[1:], wlines[1:]):
        out.append('\n' if wl != cur else ' ')
        out.append(w)
        if wl != cur:
            cur = wl
    return ''.join(out), wlines[0], cur

# ---------------------------------------------------------------------------

def align_daf(content, daf, report):
    sec = daf_section(content, daf)
    if sec is None:
        report.append((daf, None, 'NO learning_data.js SECTION'))
        return content, 0, 0
    txt = parse_txt(daf)
    if not txt:
        report.append((daf, None, 'NO txt FILE'))
        return content, 0, 0

    last_line = txt[-1][0]
    ttoks = txt_tokens(txt)
    nxt = NEXT_DAF.get(daf)
    if nxt:
        nxt_txt = parse_txt(nxt)
        if nxt_txt:
            ttoks += txt_tokens(nxt_txt, offset=last_line)

    regions = scan_lines_arrays(content, *sec)
    fields = find_he_fields(content, regions)

    edits = []
    inserts = []
    cursor = 0
    ok = fail = 0
    for vs, ve in fields:
        src = content[vs:ve]
        old = decode_js(src)
        flat = norm_ws(old)
        dtoks = [letters_of(w) for w in flat.split(' ') if letters_of(w)]
        if not dtoks:
            continue
        line_of, ts = find_alignment(dtoks, ttoks, cursor)
        if line_of is None:
            fail += 1
            report.append((daf, flat[:30], 'NOT FOUND in txt'))
            continue
        new, vstart, vend = rebreak(flat, line_of)
        assert norm_ws(new) == norm_ws(old), f'{daf}: invariant broken'
        edits.append((vs, ve, encode_js(new)))
        after = ve + 2   # skip `",`
        line_begin = content.rfind('\n', 0, vs) + 1
        head = content[line_begin:vs]
        indent = ' ' * (len(head) - len(head.lstrip()))
        mvl = re.match(r'\s*vilna_line:\s*\d+,', content[after:])
        if mvl:
            edits.append((after, after + mvl.end(),
                          f'\n{indent}vilna_line: {vstart},'))
        else:
            inserts.append((after, f'\n{indent}vilna_line: {vstart},'))
        ok += 1
        cursor = ts
        spill = ' →next-page' if vend > last_line else ''
        report.append((daf, flat[:30], f'L{vstart}–L{vend}{spill}'))

    patches = [(s, e, r) for s, e, r in edits] + [(p, p, t) for p, t in inserts]
    patches.sort(key=lambda x: x[0], reverse=True)
    for s, e, r in patches:
        content = content[:s] + r + content[e:]
    return content, ok, fail

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dafs', nargs='*')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--force', action='store_true',
                    help='apply even if some fields could not be aligned')
    args = ap.parse_args()

    build_daf_order()
    if args.all:
        def key(d):
            return (int(d[:-1]), d[-1])
        dafs = sorted((f[:-4] for f in os.listdir(TXTDIR) if f.endswith('.txt')), key=key)
    else:
        dafs = args.dafs
    if not dafs:
        ap.error('give daf names or --all')

    with open(DATA, encoding='utf-8') as f:
        content = f.read()

    report = []
    tot_ok = tot_fail = 0
    for daf in dafs:
        content, ok, fail = align_daf(content, daf, report)
        tot_ok += ok
        tot_fail += fail

    cur_daf = None
    for item in report:
        daf, snippet, status = item
        if daf != cur_daf:
            print(f'\n=== {daf} ===')
            cur_daf = daf
        label = f'  {snippet}…' if snippet else ' '
        print(f'{label:<42} {status}')

    print(f'\n{tot_ok} fields aligned, {tot_fail} failed.')
    if args.apply:
        if tot_fail and not args.force:
            print('NOT writing: failures present. Use --force to apply anyway.')
            sys.exit(1)
        with open(DATA, 'w', encoding='utf-8') as f:
            f.write(content)
        print('learning_source_store.js written.')
    else:
        print('(dry-run — use --apply to write)')

if __name__ == '__main__':
    main()
