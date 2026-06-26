#!/usr/bin/env python3
"""
build_daf.py - Automated daf builder for Yoma source_store.js.

For each daf:
  1. Fetch Sefaria he[] and en[] via curl
  2. Detect segment types (mishna/gemara) from Hebrew markers
  3. Group into sugyot (mishna starts new sugya)
  4. Generate summary, whats, hint from English text
  5. Insert entry into source_store.js
  6. Run daftext_align (--apply --force)
  7. Run fix_en (--apply)
  8. Validate all gates

Usage:
    python3 scripts/build_daf.py 21a
    python3 scripts/build_daf.py 21a 21b 22a 22b
    python3 scripts/build_daf.py --from 21a --to 25b
    python3 scripts/build_daf.py --all-remaining
"""

import argparse, json, os, re, subprocess, sys, unicodedata

DATA = 'source_store.js'
TXTDIR = 'assets/daftexts'
TDDIR = 'assets/talmuddev'

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def strip_html(s):
    return re.sub(r'<[^>]+>', '', s)

def nfc(s):
    return unicodedata.normalize('NFC', s)

def js_escape(s):
    return (s.replace('\\', '\\\\')
             .replace('"', '\\"')
             .replace('\n', '\\n')
             .replace('\r', ''))

def run(cmd, **kw):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, **kw)

# ---------------------------------------------------------------------------
# Sefaria fetch
# ---------------------------------------------------------------------------

def fetch_sefaria(daf):
    cmd = f'curl -s "https://www.sefaria.org/api/texts/Yoma.{daf}?context=0"'
    r = run(cmd)
    if r.returncode != 0:
        raise RuntimeError(f'curl failed: {r.stderr}')
    d = json.loads(r.stdout)
    he_list = d.get('he', [])
    en_list = d.get('text', [])
    # Pad shorter list
    n = max(len(he_list), len(en_list))
    he_list += [''] * (n - len(he_list))
    en_list += [''] * (n - len(en_list))
    return he_list, en_list

# ---------------------------------------------------------------------------
# Segment type detection
# ---------------------------------------------------------------------------

MISHNA_PAT = re.compile(
    r'<big><strong>מַתְנִי[׳ּ]|'
    r'<strong>מַתְנִי[׳ּ]|'
    r'^מַתְנִי[׳ּ]'
)

GEMARA_PAT = re.compile(
    r'<big><strong>גְּמָ[׳ּ]|'
    r'<strong>גְּמָ[׳ּ]|'
    r'^גְּמָ[׳ּ]'
)

def seg_type(he_raw):
    if MISHNA_PAT.search(he_raw[:60]):
        return 'mishna'
    return 'gemara'

def clean_he(he_raw):
    """Strip HTML, normalize whitespace."""
    s = strip_html(he_raw).strip()
    s = re.sub(r'\s+', ' ', s)
    return nfc(s)

# ---------------------------------------------------------------------------
# Editorial content generation from English text
# ---------------------------------------------------------------------------

def first_sentence(text, maxlen=200):
    text = strip_html(text).strip()
    text = re.sub(r'^(GEMARA:|MISHNA:|GEMARA\.|MISHNA\.)\s*', '', text)
    text = re.sub(r'^\S+\s+\S+:\s+', '', text)  # strip "Rav X said:" style openers
    m = re.search(r'(?<=[.!?])\s', text[:maxlen])
    if m:
        return text[:m.start() + 1].strip()
    return text[:maxlen].strip()

def generate_summary(sugyot_segs):
    """Build summary from first segment of each sugya (up to 3)."""
    parts = []
    for sg in sugyot_segs[:3]:
        if not sg:
            continue
        en = strip_html(sg[0].get('en', '')).strip()
        en = re.sub(r'^(GEMARA:|MISHNA:)\s*', '', en)
        s = first_sentence(en, 180)
        if s and len(s) > 15:
            parts.append(s)
    result = ' '.join(parts)
    if len(result) > 550:
        result = result[:547] + '...'
    return result

def generate_whats(segs):
    """Summarize a sugya's content in one paragraph."""
    parts = []
    for seg in segs:
        en = strip_html(seg.get('en', '')).strip()
        en = re.sub(r'^(GEMARA:|MISHNA:)\s*', '', en)
        s = first_sentence(en, 150)
        if s and len(s) > 20:
            parts.append(s)
        if len(parts) >= 5:
            break
    result = ' '.join(parts)
    if len(result) > 600:
        result = result[:597] + '...'
    return result

INTERESTING = re.compile(
    r'\b(incident|story|remarkable|never|always|therefore|because|proof|derive|'
    r'principle|despite|however|rather|question|challenge|difficulty|'
    r'famous|taught|said|answered|objected|exception|rule)\b',
    re.IGNORECASE
)

def generate_hint(segs):
    """Find an interesting sentence for hint:."""
    candidates = []
    for seg in segs:
        en = strip_html(seg.get('en', '')).strip()
        en = re.sub(r'^(GEMARA:|MISHNA:)\s*', '', en)
        sentences = re.split(r'(?<=[.!?])\s+', en)
        for sent in sentences:
            if INTERESTING.search(sent) and len(sent) > 40:
                candidates.append(sent[:260].strip())
    if candidates:
        # prefer longer/more interesting
        candidates.sort(key=len, reverse=True)
        return candidates[0]
    # fallback: last segment first sentence
    if segs:
        en = strip_html(segs[-1].get('en', '')).strip()
        en = re.sub(r'^(GEMARA:|MISHNA:)\s*', '', en)
        return first_sentence(en, 250)
    return ''

# ---------------------------------------------------------------------------
# Sugya grouping
# ---------------------------------------------------------------------------

def group_sugyot(segments):
    """
    Group segments into sugyot.
    - Each mishna segment starts a new sugya.
    - Consecutive gemara segments stay in one sugya unless too many (>8 split by §).
    """
    sugyot = []
    current = []

    def flush():
        if current:
            sugyot.append(list(current))
            current.clear()

    for seg in segments:
        if seg['type'] == 'mishna':
            flush()
            current.append(seg)
        else:
            # Check for section break marker § in English
            en = seg.get('en', '')
            if current and seg['type'] == 'gemara':
                # § at start of English indicates new topic section in Gemara
                if re.match(r'^§|^<b>§', en.strip()):
                    flush()
            current.append(seg)

    flush()
    return sugyot

# ---------------------------------------------------------------------------
# Title generation
# ---------------------------------------------------------------------------

def sugya_title(segs):
    if not segs:
        return 'Continuation'
    en = strip_html(segs[0].get('en', '')).strip()
    en = re.sub(r'^(GEMARA:|MISHNA:|§\s*)', '', en).strip()
    # Take first 70 chars, cut at word boundary
    title = en[:75]
    if len(en) > 75:
        title = en[:75].rsplit(' ', 1)[0].rstrip(',;:')
    return title.strip() or 'Continuation'

# ---------------------------------------------------------------------------
# Perek mapping (approximate for Yoma)
# ---------------------------------------------------------------------------

def daf_perek(daf):
    n = int(daf[:-1])
    if n <= 3: return 1
    if n <= 5: return 2
    if n <= 8: return 3
    if n <= 14: return 4
    if n <= 22: return 5
    if n <= 44: return 6
    if n <= 68: return 7
    return 8

# ---------------------------------------------------------------------------
# source_store.js manipulation
# ---------------------------------------------------------------------------

def daf_already_built(content, daf):
    return f'// YOMA {daf}\n' in content or f'// YOMA {daf}\r' in content

def build_entry_text(daf, segments):
    """Generate JS text for one daf entry."""
    # Group into sugyot
    sugyot = group_sugyot(segments)
    if not sugyot:
        sugyot = [segments]

    # Summary
    summary = generate_summary(sugyot)

    out = []
    out.append(f'\n  // YOMA {daf}')
    out.append(f'  "{daf}": {{')
    out.append(f'    summary: "{js_escape(summary)}",')
    out.append(f'    sugyot: [')

    for si, sg_segs in enumerate(sugyot):
        if not sg_segs:
            continue
        title = sugya_title(sg_segs)
        whats = generate_whats(sg_segs)
        hint = generate_hint(sg_segs)

        out.append(f'      {{')
        out.append(f'        id: "{daf}-{si + 1}",')
        out.append(f'        title: "{js_escape(title)}",')
        out.append(f'        lines: [')

        for seg in sg_segs:
            he_raw = seg.get('he', '')
            en_raw = seg.get('en', '')
            typ = seg['type']
            he_clean = clean_he(he_raw)
            out.append(f'          {{ kind: "{typ}", he: "{js_escape(he_clean)}",')
            out.append(f'          vilna_line: 1, en: "{js_escape(en_raw)}" }},')

        out.append(f'        ],')
        out.append(f'        whats: "{js_escape(whats)}",')
        out.append(f'        hint: "{js_escape(hint)}"')
        out.append(f'      }},')

    out.append(f'    ],')
    out.append(f'    glossary: []')
    out.append(f'  }},')
    out.append('')

    return '\n'.join(out)

def insert_entry(content, entry_text):
    """Insert entry before the closing }; of DAF_CONTENT."""
    pos = content.rfind('\n};')
    if pos == -1:
        raise RuntimeError('Could not find closing }; in source_store.js')
    return content[:pos] + entry_text + content[pos:]

def update_daf_index(content, daf, perek):
    """Add or update the DAF_INDEX entry for this daf."""
    # Find the DAF_INDEX array bounds precisely
    dai_start = content.find('const DAF_INDEX')
    if dai_start == -1:
        return content
    dai_end = content.find('];', dai_start)
    if dai_end == -1:
        return content
    # Check if daf already in DAF_INDEX (use ,/space after id to avoid matching sugya ids)
    daf_section = content[dai_start:dai_end]
    pat = re.compile(r'id:\s*"' + re.escape(daf) + r'"[ ,]')
    if pat.search(daf_section):
        return content  # already in index
    new_entry = f'\n  {{ id: "{daf}", perek: {perek}, status: "rich", topic: "" }},'
    return content[:dai_end] + new_entry + '\n' + content[dai_end:]

# ---------------------------------------------------------------------------
# Pipeline steps
# ---------------------------------------------------------------------------

def run_daftext_align(daf):
    r = run(f'python3 scripts/daftext_align.py {daf} --apply --force')
    return r.stdout + r.stderr

def run_fix_en():
    r = run('python3 scripts/fix_en.py --apply')
    return r.stdout + r.stderr

def run_validate():
    r = run('npm run validate')
    return r.stdout + r.stderr, r.returncode == 0

def run_audit(daf):
    r = run(f'npm run audit {daf}')
    return r.stdout + r.stderr, 'MISSING 0' in r.stdout

def run_order_audit():
    r = run('npm run audit:order')
    return r.stdout + r.stderr, r.returncode == 0

def run_validate_en():
    r = run('npm run validate:en')
    return r.stdout + r.stderr, r.returncode == 0

def run_validate_daftext():
    r = run('npm run validate:daftext')
    return r.stdout + r.stderr, r.returncode == 0

def run_validate_alignment():
    r = run('npm run validate:alignment')
    return r.stdout + r.stderr, r.returncode == 0

def run_smoke():
    r = run('npm test')
    return r.stdout + r.stderr, r.returncode == 0

# ---------------------------------------------------------------------------
# Ensure talmuddev + daftext
# ---------------------------------------------------------------------------

def ensure_talmuddev(daf):
    path = os.path.join(TDDIR, f'{daf}.json')
    if not os.path.exists(path):
        print(f'  Fetching talmud.dev for {daf}...', flush=True)
        r = run(f'python3 scripts/fetch_talmuddev.py {daf}')
        if not os.path.exists(path):
            print(f'  WARNING: talmud.dev fetch failed for {daf}')
            return False
    return True

def ensure_daftext(daf):
    path = os.path.join(TXTDIR, f'{daf}.txt')
    if not os.path.exists(path):
        print(f'  Generating daftext for {daf}...', flush=True)
        r = run(f'python3 scripts/validate_daftext.py --fix {daf}')
        if not os.path.exists(path):
            print(f'  WARNING: daftext generation failed for {daf}')
            return False
    return True

# ---------------------------------------------------------------------------
# Main per-daf build
# ---------------------------------------------------------------------------

def build_one(daf, verbose=True):
    def log(msg):
        if verbose:
            print(f'  {msg}', flush=True)

    print(f'\n=== Building {daf} ===', flush=True)

    # Read source_store.js
    with open(DATA, encoding='utf-8') as f:
        content = f.read()

    if daf_already_built(content, daf):
        print(f'  SKIP: {daf} already built')
        return 'skip'

    # Fetch Sefaria
    log('Fetching Sefaria...')
    try:
        he_list, en_list = fetch_sefaria(daf)
    except Exception as e:
        print(f'  ERROR fetching Sefaria: {e}')
        return False

    if not he_list:
        print(f'  ERROR: No segments returned for {daf}')
        return False

    log(f'  {len(he_list)} segments')

    # Build segment dicts
    segments = []
    for he_raw, en_raw in zip(he_list, en_list):
        if not he_raw.strip() and not en_raw.strip():
            continue
        segments.append({
            'he': he_raw,
            'en': en_raw,
            'type': seg_type(he_raw),
        })

    if not segments:
        print(f'  ERROR: All segments empty for {daf}')
        return False

    # Ensure talmuddev and daftext exist
    ensure_talmuddev(daf)
    ensure_daftext(daf)

    # Build entry text
    entry_text = build_entry_text(daf, segments)

    # Insert into source_store.js
    new_content = insert_entry(content, entry_text)
    # Update DAF_INDEX
    new_content = update_daf_index(new_content, daf, daf_perek(daf))

    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(new_content)
    log('Inserted into source_store.js')

    # Run daftext alignment
    log('Running daftext_align...')
    align_out = run_daftext_align(daf)
    failed = re.search(r'(\d+) fields aligned, (\d+) failed', align_out)
    if failed:
        log(f'  align: {failed.group(1)} aligned, {failed.group(2)} failed (--force applied)')

    # Fix en: mismatches
    log('Running fix_en...')
    run_fix_en()

    # Validate
    log('Running npm run validate...')
    val_out, val_ok = run_validate()
    if not val_ok:
        print(f'  VALIDATE FAILED for {daf}:')
        # Print the error lines
        for line in val_out.split('\n'):
            if 'ERROR' in line or 'error' in line.lower() or daf in line:
                print(f'    {line}')
        return False

    log('validate: OK')
    return True


def run_batch_gates(dafs):
    """Run shared gates (order, en, daftext, smoke) once after a batch."""
    print('\n--- Batch gate checks ---')
    all_ok = True

    out, ok = run_order_audit()
    print(f'  order audit: {"OK" if ok else "FAIL"}')
    if not ok:
        print(out[-500:])
        all_ok = False

    out, ok = run_validate_en()
    print(f'  validate:en: {"OK" if ok else "FAIL"}')
    if not ok:
        print(out[-500:])
        all_ok = False

    out, ok = run_validate_daftext()
    print(f'  validate:daftext: {"OK" if ok else "FAIL"}')
    if not ok:
        print(out[-500:])
        all_ok = False

    out, ok = run_validate_alignment()
    print(f'  validate:alignment: {"OK" if ok else "FAIL"}')
    if not ok:
        print(out[-500:])
        all_ok = False

    out, ok = run_smoke()
    print(f'  smoke tests: {"OK" if ok else "FAIL"}')
    if not ok:
        all_ok = False

    return all_ok


# ---------------------------------------------------------------------------
# Daf range utilities
# ---------------------------------------------------------------------------

ALL_DAFS = []
for _n in range(2, 89):
    for _s in ['a', 'b']:
        if _n == 88 and _s == 'b':
            break
        ALL_DAFS.append(f'{_n}{_s}')

BUILT = {
    '2a','2b','3a','3b','4a','4b','5a','5b','6a','6b','7a','7b','8a','8b',
    '9a','9b','10a','10b','11a','11b','12a','12b','13a','13b','14a','14b',
    '15a','15b','16a','16b','17a','17b','18a','18b','19a','19b','20a','20b',
    '21a','21b','22a','22b','23a','23b','24a','24b','25a','25b','26a','26b',
    '27a','27b','28a','28b','29a','29b','30a','30b','31a','31b','32a','32b',
    '33a','33b','34a','34b','35a','35b','36a','36b','37a','37b','38a','38b',
    '39a','39b','40a','40b','41a','41b','42a','42b','43a','43b','44a','44b',
    '45a','45b','46a','46b','47a','47b','48a','48b','49a','49b','50a','50b',
    '51a','51b','52a','52b','53a','53b','54a','54b','55a',
}

def remaining_dafs():
    return [d for d in ALL_DAFS if d not in BUILT]

def daf_range(start, end):
    si = ALL_DAFS.index(start)
    ei = ALL_DAFS.index(end)
    return ALL_DAFS[si:ei + 1]

# ---------------------------------------------------------------------------
# Version bump
# ---------------------------------------------------------------------------

def bump_version():
    with open('VERSION') as f:
        ver = f.read().strip()
    major, minor = ver.split('.')
    new_ver = f'{major}.{int(minor) + 1}'
    for path, old, new in [
        ('VERSION', ver, new_ver),
        ('package.json', f'"version": "{ver}"', f'"version": "{new_ver}"'),
    ]:
        with open(path) as f: c = f.read()
        with open(path, 'w') as f: f.write(c.replace(old, new))
    for path in ['index.html', 'app.jsx']:
        with open(path) as f: c = f.read()
        with open(path, 'w') as f:
            f.write(c.replace(f'?v={ver}', f'?v={new_ver}')
                      .replace(f'APP_VERSION = "{ver}"', f'APP_VERSION = "{new_ver}"'))
    return new_ver

def git_commit_push(dafs, ver):
    daf_list = ' '.join(dafs) if len(dafs) <= 5 else f'{dafs[0]}-{dafs[-1]}'
    msg = f'Add {daf_list}: automated bulk build (v{ver})'
    run('git add source_store.js VERSION package.json index.html app.jsx .sefaria-validated')
    result = subprocess.run(
        f'git commit -m "{msg}"',
        shell=True, capture_output=True, text=True
    )
    if result.returncode != 0:
        combined = result.stdout + result.stderr
        print(f'  GIT COMMIT FAILED (pre-commit hook blocked):')
        print(combined[-800:])
        return False
    push = subprocess.run('git push -u origin main', shell=True, capture_output=True, text=True)
    if push.returncode != 0:
        print(f'  GIT PUSH FAILED: {push.stderr[-300:]}')
        return False
    print(f'  Committed and pushed: {msg}')
    return True

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dafs', nargs='*')
    ap.add_argument('--all-remaining', action='store_true')
    ap.add_argument('--from', dest='from_daf')
    ap.add_argument('--to', dest='to_daf')
    ap.add_argument('--batch-size', type=int, default=5,
                    help='Commit after this many daf (default 5)')
    ap.add_argument('--dry-run', action='store_true',
                    help='Fetch and show entry without writing')
    args = ap.parse_args()

    if args.all_remaining:
        dafs = remaining_dafs()
    elif args.from_daf and args.to_daf:
        dafs = daf_range(args.from_daf, args.to_daf)
    elif args.dafs:
        dafs = args.dafs
    else:
        ap.error('Specify daf names, --all-remaining, or --from X --to Y')

    print(f'Building {len(dafs)} daf: {dafs[0]} .. {dafs[-1]}')

    if args.dry_run:
        for daf in dafs[:2]:
            he_list, en_list = fetch_sefaria(daf)
            segments = [{'he': h, 'en': e, 'type': seg_type(h)}
                        for h, e in zip(he_list, en_list) if h.strip()]
            entry = build_entry_text(daf, segments)
            print(entry[:2000])
        return

    batch = []
    failed = []

    for i, daf in enumerate(dafs):
        result = build_one(daf)
        if result is True:
            batch.append(daf)
        elif result == 'skip':
            pass  # already built - don't add to batch
        else:
            failed.append(daf)
            print(f'  FAILED: {daf} - will skip and continue')

        # Commit batch when full or last daf
        if batch and (len(batch) >= args.batch_size or i == len(dafs) - 1):
            gates_ok = run_batch_gates(batch)
            if gates_ok:
                ver = bump_version()
                committed = git_commit_push(batch, ver)
                if committed:
                    print(f'  Batch committed: {batch}')
                else:
                    print(f'  COMMIT BLOCKED: pre-commit hook failed for {batch}')
                    failed.extend(batch)
            else:
                print(f'  WARNING: batch gates failed - not committing {batch}')
                failed.extend(batch)
            batch = []

    print(f'\n=== Done ===')
    print(f'Failed daf: {failed if failed else "none"}')
    if failed:
        sys.exit(1)

if __name__ == '__main__':
    main()
