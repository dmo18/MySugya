#!/usr/bin/env python3
"""
fix_unmatched_alignment.py - Insert Vilna line breaks into he: fields that
daftext_align.py cannot match due to numeric abbreviations in daftext.

The 16 segments below are hardcoded. Five of them already have correct breaks
(the algorithm verified them manually against the daftext). The remaining 11
need breaks inserted by this script.

The word-matching strategy:
  1. Strip nikud from the he: field.
  2. For each daftext line (starting at vilna_line), expand numeric and other
     abbreviations that the prefix-match algorithm cannot handle.
  3. Match daftext words to stripped-he: words in order.
  4. When the daftext line changes, insert \n in the original he: field at the
     corresponding position.

Special cases handled:
  - Numeric abbreviations (יב = 12 = שנים עשר, ח = 8 = שמונה, etc.)
  - תרגומא vs תרגמה word variant (edit distance 2)
  - מתני header word in he: not present in daftext (printed in special font)
  - High skip count when segment starts mid-daftext-line

Usage:
    python3 scripts/fix_unmatched_alignment.py [--dry-run]
"""
import argparse, os, re, sys, unicodedata

DATA = 'source_store.js'
TXTDIR = 'assets/daftexts'
HEB = re.compile(r'[א-ת]')

# ---------------------------------------------------------------------------
# Numeric and other abbreviations that prefix-matching cannot handle
# ---------------------------------------------------------------------------

# Maps unvowelized abbreviation letter-sequence -> list of possible expansions
# Each expansion is a tuple of unvowelized word prefixes (must match start of he: words).
ABBREV_EXPAND = {
    # Numeric - single digit
    'ב':   [('שניים',), ('שנים',), ('שתיים',), ('שתים',), ('בן',)],
    'ג':   [('שלשה',), ('שלש',), ('גדול',)],
    'ד':   [('ארבע',), ('ארבעה',)],
    'ה':   [('חמשה',), ('חמש',)],
    'ו':   [('ששה',), ('שש',), ('ו',)],
    'ז':   [('שבעה',), ('שבע',)],
    'ח':   [('שמונה',), ('שמונה',)],
    'ט':   [('תשע',), ('תשעה',)],
    'י':   [('עשר',), ('עשרה',), ('יוחנן',)],
    'כ':   [('עשרים',), ('כי',), ('כהן',)],
    'מ':   [('ארבעים',), ('מ',)],
    # Numeric - teens (yod-X form)
    'יא':  [('אחת', 'עשרה'), ('אחד', 'עשר'), ('אחד', 'עשרה'), ('אחת', 'עשר'),
             ('אחת', 'עשרה'), ('אחד', 'עשר')],
    'יב':  [('שנים', 'עשר'), ('שתים', 'עשרה'), ('שנים', 'עשרה'), ('שתים', 'עשר'),
             ('שניים', 'עשר'), ('שתיים', 'עשרה')],
    'יג':  [('שלשה', 'עשר'), ('שלש', 'עשרה'), ('שלושה', 'עשר'), ('שלוש', 'עשרה')],
    'יד':  [('ארבעה', 'עשר'), ('ארבע', 'עשרה')],
    'טו':  [('חמשה', 'עשר'), ('חמש', 'עשרה'), ('חמישה', 'עשר')],
    'טז':  [('ששה', 'עשר'), ('שש', 'עשרה')],
    'יז':  [('שבעה', 'עשר'), ('שבע', 'עשרה')],
    'יח':  [('שמונה', 'עשר'), ('שמונה', 'עשרה')],
    'יט':  [('תשעה', 'עשר'), ('תשע', 'עשרה')],
    # Hundreds
    'ד':   [('ארבע',), ('ארבעה',), ('ד',)],  # can also mean 4
    # Common talmudic abbreviations (gershayim form)
    'כג':  [('כהן', 'גדול')],
    'תש':  [('תא', 'שמע'), ('תנא', 'שמע')],
    'תר':  [('תנו', 'רבנן')],
    'תל':  [('תלמוד', 'לומר')],
    'יוהכ': [('יום', 'הכפורים')],
    'רה':  [('ראש', 'השנה')],
    'שמ':  [('שמע', 'מינה')],
    'מהמ': [('מהיכן', 'הני', 'מילי'), ('מנא', 'הני', 'מילי')],
    'לה':  [('לה',)],
    'דת':  [('דתנן',), ('דתניא',), ('דת',)],
    'דתר': [('תנו', 'רבנן')],   # ד prefix + ת\"ר abbreviation (daftext 48a etc)
    # Single geresh abbreviations
    'ר':   [('רבי',), ('רב',), ('ר',)],
    'א':   [('אמר',), ('א',)],
    'אר':  [('אמר', 'רב'), ('אמר', 'רבי')],
    'מה':  [('מה',), ('מהו',)],
    # Hebrew letter numbers that appear as single letters
}

# Word variants where daftext and Sefaria use different forms
# (stripped-nikud daftext_word, stripped-nikud he_word) -> True
WORD_VARIANTS = {
    ('תרגומא', 'תרגמה'): True,
    ('תרגמה', 'תרגומא'): True,
    ('בעי', 'בעו'): True,
    ('בעו', 'בעי'): True,
    # Sefaria uses גוים/גויים for Gentiles; daftext uses כותיים/כותים
    ('כותיים', 'גוים'): True,
    ('כותים', 'גוים'): True,
    ('גוים', 'כותיים'): True,
    ('גוים', 'כותים'): True,
    ('כותיים', 'גויים'): True,
    ('גויים', 'כותיים'): True,
    ('כותי', 'גוי'): True,
    ('גוי', 'כותי'): True,
    ('כוי', 'גוי'): True,
    ('גוי', 'כוי'): True,
}

def strip_nikud(s):
    """Remove Hebrew vowel marks (nikud) from a string."""
    normalized = unicodedata.normalize('NFD', s)
    return ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')

def letters_of(text):
    return ''.join(ch for ch in text if HEB.match(ch))

def is_abbrev_tok(word):
    """True if word looks like an abbreviation (geresh/gershayim between letters)."""
    letters_seen = False
    for i, ch in enumerate(word):
        if HEB.match(ch):
            letters_seen = True
        elif ch in ('"', "'", '״', '׳', '“', '”') and letters_seen:
            rest = word[i + 1:]
            if any(HEB.match(c) for c in rest):
                return True
            if ch in ("'", '׳'):
                return True
    return False

def words_match(t_letters, he_letters):
    """Return True if two letter sequences match (with tolerance for variants and edit distance)."""
    if t_letters == he_letters:
        return True
    # Check explicit variants
    if (t_letters, he_letters) in WORD_VARIANTS:
        return True
    # Edit distance: for longer words allow distance 2, shorter allow 1
    n = max(len(t_letters), len(he_letters))
    if abs(len(t_letters) - len(he_letters)) > 2:
        return False
    if n >= 5:
        # Allow edit distance 2 for words of length >= 5
        return edit_distance(t_letters, he_letters) <= 2
    if n >= 3:
        return edit_distance(t_letters, he_letters) <= 1
    return False

def edit_distance(a, b):
    """Compute Levenshtein distance."""
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for ca in a:
        cur = [prev[0] + 1]
        for j, cb in enumerate(b):
            cur.append(min(prev[j + 1] + 1, cur[j] + 1, prev[j] + (ca != cb)))
        prev = cur
    return prev[-1]

def expand_abbrev(abbr_letters, words_ahead):
    """
    Try to expand abbreviation letters against the next few words_ahead (letter sequences).
    Returns number of words consumed if expansion matches, else 0.
    Also tries prefix-based matching (the generic approach in daftext_align).
    """
    # Explicit dict lookup first
    if abbr_letters in ABBREV_EXPAND:
        for expansion in ABBREV_EXPAND[abbr_letters]:
            k = len(expansion)
            if k <= len(words_ahead):
                if all(w_data.startswith(w_exp) or w_exp == w_data
                       for w_exp, w_data in zip(expansion, words_ahead)):
                    return k
    # Generic prefix-match fallback (like daftext_align.py abbrev_expand)
    # Each letter in abbr must be a prefix of consecutive he: words
    if len(abbr_letters) <= len(words_ahead):
        ok = True
        for al, w_data in zip(abbr_letters, words_ahead):
            if not w_data.startswith(al):
                ok = False
                break
        if ok:
            return len(abbr_letters)
    return 0

def read_daftext(daf, start_line=0):
    """Return list of (line_num, text) tuples from daftext file."""
    path = os.path.join(TXTDIR, f'{daf}.txt')
    if not os.path.exists(path):
        return []
    result = []
    with open(path, encoding='utf-8') as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            m = re.match(r'(\d+)\s+(.*)', raw)
            if m:
                n = int(m.group(1))
                if n >= start_line:
                    result.append((n, m.group(2)))
    return result

def daftext_to_word_tokens(txt_lines):
    """
    Convert daftext lines to list of (letters, is_abbrev, line_num) triples.
    """
    tokens = []
    for line_num, text in txt_lines:
        for word in text.split():
            raw_letters = letters_of(word)
            if not raw_letters:
                continue
            tokens.append((raw_letters, is_abbrev_tok(word), line_num))
    return tokens

def map_breaks(he_original, daf, vilna_line, skip_matni=False):
    """
    Map Vilna line breaks from daftext into the original he: text.
    Returns (new_he_text, status_string).
    """
    txt_lines = read_daftext(daf, start_line=vilna_line)
    if not txt_lines:
        return None, 'no daftext lines'

    # Use a generous window (might need many lines for long segments)
    txt_lines = txt_lines[:50]

    # Strip nikud for matching
    he_stripped = strip_nikud(he_original)
    he_flat = re.sub(r'[\n ]+', ' ', he_stripped).strip()

    he_words = he_flat.split()
    he_letter_words = [(letters_of(w), i) for i, w in enumerate(he_words) if letters_of(w)]

    if not he_letter_words:
        return None, 'no letter words in he:'

    # Skip מתני/גמ prefix words that don't appear in daftext
    skip_prefixes = set()
    if skip_matni:
        for letters, wi in he_letter_words:
            if letters in ('מתני', 'גמ', 'מתנ'):
                skip_prefixes.add(wi)

    he_active = [(l, wi) for l, wi in he_letter_words if wi not in skip_prefixes]
    if not he_active:
        return None, 'no active he: words after prefix skip'

    txt_tokens = daftext_to_word_tokens(txt_lines)
    if not txt_tokens:
        return None, 'no daftext tokens'

    # Align: for each he: letter-word, find the corresponding txt line number
    line_of = {}  # he_word_index -> txt line_num

    hi = 0  # index into he_active
    ti = 0  # index into txt_tokens

    max_he = len(he_active)
    max_ti = len(txt_tokens)

    # Generous skip budget to handle segments that start mid-line in daftext
    skips_allowed = max(15, max_he // 3)
    skips_used = 0

    while hi < max_he and ti < max_ti:
        he_letters, he_wi = he_active[hi]
        t_letters, t_is_abbrev, t_line = txt_tokens[ti]

        # Direct/variant match
        if words_match(t_letters, he_letters):
            line_of[he_wi] = t_line
            hi += 1
            ti += 1
            continue

        # Abbreviation expansion: try expanding txt abbreviation against he: words
        if t_is_abbrev:
            ahead_he = [he_active[hi + k][0] for k in range(min(6, max_he - hi))]
            consumed = expand_abbrev(t_letters, ahead_he)
            if consumed > 0:
                for k in range(consumed):
                    line_of[he_active[hi + k][1]] = t_line
                hi += consumed
                ti += 1
                continue

        # Merged word in daftext (two he: words appear as one txt token)
        if hi + 1 < max_he:
            merged = he_letters + he_active[hi + 1][0]
            if words_match(t_letters, merged):
                line_of[he_wi] = t_line
                line_of[he_active[hi + 1][1]] = t_line
                hi += 2
                ti += 1
                continue

        # Try skipping one txt token (extra word in print not in Sefaria)
        if skips_used < skips_allowed:
            ti += 1
            skips_used += 1
            continue

        # Give up
        break

    if len(line_of) < max_he // 2:
        return None, f'alignment too sparse: {len(line_of)}/{max_he} words matched'

    # Fill unassigned he: words (including skipped prefix words) with neighbor line
    # First, propagate forward from assigned words
    all_wi_active = [wi for _, wi in he_active]
    last_line = txt_lines[0][0]
    for _, wi in he_active:
        l = line_of.get(wi, None)
        if l is not None:
            last_line = l

    # Build line-per-word map for ALL words (including punctuation-only)
    # First assign all letter words
    wi_to_line = {}

    # For skipped prefix words, use first assigned line
    first_assigned_line = txt_lines[0][0]
    for _, wi in he_active:
        if wi in line_of:
            first_assigned_line = line_of[wi]
            break

    for letters, wi in he_letter_words:
        if wi in skip_prefixes:
            wi_to_line[wi] = first_assigned_line
        elif wi in line_of:
            wi_to_line[wi] = line_of[wi]

    # Forward-fill any gaps
    last_line = first_assigned_line
    for _, wi in he_letter_words:
        if wi in wi_to_line:
            last_line = wi_to_line[wi]
        else:
            wi_to_line[wi] = last_line

    # Build word_line for ALL words (including punctuation)
    word_line = []
    last_letter_line = first_assigned_line
    for i, w in enumerate(he_words):
        if letters_of(w) and i in wi_to_line:
            last_letter_line = wi_to_line[i]
            word_line.append(last_letter_line)
        elif not letters_of(w):
            # Punctuation: look ahead for next letter word's line
            next_line = last_letter_line
            for j in range(i + 1, len(he_words)):
                if letters_of(he_words[j]) and j in wi_to_line:
                    next_line = wi_to_line[j]
                    break
            word_line.append(next_line)
        else:
            word_line.append(last_letter_line)

    # Now rebuild the original he: text inserting \n at line boundaries
    orig_words = re.sub(r'[\n ]+', ' ', he_original).strip().split()

    if len(orig_words) != len(he_words):
        return None, f'word count mismatch: orig={len(orig_words)} stripped={len(he_words)}'

    result = [orig_words[0]]
    cur_line = word_line[0] if word_line else txt_lines[0][0]

    for i, (w, wl) in enumerate(zip(orig_words[1:], word_line[1:]), 1):
        if wl != cur_line:
            result.append('\n')
            cur_line = wl
        else:
            result.append(' ')
        result.append(w)

    new_he = ''.join(result)

    # Verify invariant: stripping whitespace gives same text
    orig_norm = re.sub(r'[\n ]+', ' ', he_original).strip()
    new_norm = re.sub(r'[\n ]+', ' ', new_he).strip()
    if strip_nikud(orig_norm) != strip_nikud(new_norm):
        return None, 'invariant broken: normalized text changed'

    return new_he, 'ok'

# ---------------------------------------------------------------------------
# source_store.js manipulation
# ---------------------------------------------------------------------------

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

def get_daf_section(content, daf):
    m = re.search(rf'// YOMA {daf}\b', content)
    if not m:
        return None, None
    start = m.start()
    nxt = re.search(r'// YOMA \d+[ab]\b', content[m.end():])
    end = m.end() + nxt.start() if nxt else len(content)
    return start, end

def find_he_field(content, prefix, daf_section_start, daf_section_end):
    """
    Find a he: field whose decoded content starts with prefix (stripped of nikud).
    Returns (value_start, value_end) into content, or None.
    """
    search_start = daf_section_start
    stripped_prefix = strip_nikud(prefix)
    # Use first 20 chars of stripped prefix for matching
    match_prefix = stripped_prefix[:25]

    while True:
        j = content.find('he: "', search_start)
        if j < 0 or j >= daf_section_end:
            return None
        vs = j + 5
        k = vs
        while k < daf_section_end:
            c = content[k]
            if c == '\\':
                k += 2
                continue
            if c == '"':
                break
            k += 1
        raw = content[vs:k]
        decoded = decode_js(raw)
        flat = re.sub(r'[\n ]+', ' ', decoded).strip()
        flat_stripped = strip_nikud(flat)
        if flat_stripped.startswith(match_prefix):
            return vs, k
        search_start = k

# ---------------------------------------------------------------------------
# Hardcoded list of segments to fix
# ---------------------------------------------------------------------------

# (daf, vilna_line, he_prefix, already_has_breaks, skip_matni)
# already_has_breaks=True: breaks exist but algo cannot verify - skip this segment
# skip_matni=True: the he: has a מתני/גמ header word not present in daftext
SEGMENTS = [
    # Already have correct breaks - skip
    ('9a',  5,  'אָמַר עוּלָּא: מִתּוֹךְ שֶׁפַּ',       True,  False),
    ('16a', 6,  'חֲמֵשׁ עֶשְׂרֵה מַעֲלוֹת עוֹלו',        True,  False),
    ('16b', 1,  'עֶשֶׂר אַמּוֹת כְּנֶגֶד פִּתְח',        True,  False),
    ('16b', 9,  'וְאִי סָלְקָא דַעְתָּךְ מִדּוֹ',        True,  False),
    ('19a', 11, 'שָׁלֹשׁ שֶׁבַּצָּפוֹן: לִשְׁכַּ',       True,  False),
    # Need breaks inserted
    ('25b', 15, 'תָּא שְׁמַע: בֶּן קָטִין עָשָׂ',        False, False),
    ('26b', 30, 'תָּנֵי רַבִּי חִיָּיא: פַּיִיס',        False, False),
    ('37a', 20, 'בֶּן קָטִין עָשָׂה שְׁנֵים עָש',        False, False),
    ('37a', 35, 'תַּרְגְּמַהּ רַב שְׁמוּאֵל בַּ',        False, False),
    ('48a', 12, 'מְנָא הָנֵי מִילֵּי? תָּנוּ רַ',        False, False),
    ('48b', 1,  'בְּעוֹ מִינֵּיהּ מֵרַב שֵׁשֶׁת',        False, False),
    ('73b', 24, 'מַתְנִי׳ יוֹם הַכִּפּוּרִים אָ',        False, True),
    ('82a', 6,  'אָמַר רַב הוּנָא: בֶּן שְׁמוֹנ',        False, False),
    ('84b', 43, 'וּמִי אָמַר שְׁמוּאֵל הָכִי? ו',        False, False),
    ('85a', 1,  'וּשְׁמוּאֵל אָמַר לְפַקֵּחַ עָ',        False, False),
    ('85a', 3,  'אִם רוֹב גּוֹיִם — גּוֹי, לְמַ',        False, False),
]

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description='Insert Vilna line breaks for unmatched segments')
    ap.add_argument('--dry-run', action='store_true', help='Show changes without writing')
    args = ap.parse_args()

    with open(DATA, encoding='utf-8') as f:
        content = f.read()

    changes = []  # (vs, ve, new_js_value)
    report = []

    for daf, vilna_line, prefix, already_ok, skip_matni in SEGMENTS:
        sec_start, sec_end = get_daf_section(content, daf)
        if sec_start is None:
            report.append(f'  {daf} L{vilna_line}: section not found in source_store.js')
            continue

        loc = find_he_field(content, prefix, sec_start, sec_end)
        if loc is None:
            report.append(f'  {daf} L{vilna_line}: he: field not found (prefix: {prefix[:20]})')
            continue

        vs, ve = loc
        raw = content[vs:ve]
        decoded = decode_js(raw)

        if already_ok:
            breaks_present = '\n' in decoded
            report.append(f'  {daf} L{vilna_line}: SKIP (already has correct breaks={breaks_present})')
            continue

        # Try to add breaks
        new_he, status = map_breaks(decoded, daf, vilna_line, skip_matni=skip_matni)

        if new_he is None:
            report.append(f'  {daf} L{vilna_line}: FAILED to align - {status}')
            report.append(f'    prefix: {prefix[:40]}')
            continue

        if new_he == decoded:
            report.append(f'  {daf} L{vilna_line}: no change (single Vilna line or already aligned)')
            continue

        new_js = encode_js(new_he)
        changes.append((vs, ve, new_js))

        n_breaks = new_he.count('\n')
        report.append(f'  {daf} L{vilna_line}: inserted {n_breaks} break(s)')
        if args.dry_run:
            preview = new_he[:140].replace('\n', '[NL]')
            report.append(f'    -> {preview}')

    print('fix_unmatched_alignment.py report:')
    for line in report:
        print(line)

    if not changes:
        print('\nNo changes to apply.')
        return

    if args.dry_run:
        print(f'\n(dry-run) Would apply {len(changes)} change(s).')
        return

    # Apply changes in reverse order to preserve offsets
    changes.sort(key=lambda x: x[0], reverse=True)
    for vs, ve, new_js in changes:
        content = content[:vs] + new_js + content[ve:]

    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f'\nApplied {len(changes)} change(s) to source_store.js.')

if __name__ == '__main__':
    main()
