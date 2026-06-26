#!/usr/bin/env python3
"""
validate_alignment.py - Check that all he: fields in learning_data.js can be aligned
to their Vilna daftext files (dry-run of daftext_align).

Runs daftext_align --force (no --apply) for each daf found in learning_data.js and
collects any "NOT FOUND in txt" lines. Exits 1 if any are found.

Usage:
    python3 scripts/validate_alignment.py
"""
import os, re, subprocess, sys

DATA = 'learning_data.js'
TXTDIR = 'assets/daftexts'

def find_dafs_in_data():
    """Return list of daf names in Vilna order as found in learning_data.js."""
    with open(DATA, encoding='utf-8') as f:
        content = f.read()
    markers = re.findall(r'// YOMA (\d+[ab])\b', content)
    # Deduplicate while preserving order
    seen = set()
    result = []
    for d in markers:
        if d not in seen:
            seen.add(d)
            result.append(d)
    return result

def run_align_dryrun(daf):
    """Run daftext_align dry-run for one daf. Return (not_found_lines, raw_output)."""
    r = subprocess.run(
        ['python3', 'scripts/daftext_align.py', daf, '--force'],
        capture_output=True, text=True
    )
    output = r.stdout + r.stderr
    not_found = re.findall(r'(.+?)\s+NOT FOUND in txt', output)
    return not_found, output

def main():
    dafs = find_dafs_in_data()
    if not dafs:
        print('ERROR: no daf found in learning_data.js (missing // YOMA Xa markers?)')
        sys.exit(1)

    # Only check dafs that have a corresponding daftext file
    dafs_with_txt = [d for d in dafs if os.path.exists(os.path.join(TXTDIR, f'{d}.txt'))]
    skipped = [d for d in dafs if d not in dafs_with_txt]

    print(f'validate:alignment - checking {len(dafs_with_txt)} daf '
          f'({len(skipped)} skipped - no daftext file)')
    if skipped:
        print(f'  Skipped: {" ".join(skipped)}')

    all_failures = {}  # daf -> [not_found snippets]
    for daf in dafs_with_txt:
        not_found, _ = run_align_dryrun(daf)
        if not_found:
            all_failures[daf] = not_found

    if all_failures:
        total = sum(len(v) for v in all_failures.values())
        print(f'\nERROR: {total} segment(s) across {len(all_failures)} daf '
              f'cannot be aligned to Vilna daftext:\n')
        for daf, snippets in sorted(all_failures.items(),
                                    key=lambda x: (int(x[0][:-1]), x[0][-1])):
            print(f'  {daf}:')
            for s in snippets:
                print(f'    - {s.strip()}')
        print()
        print('Fix: run python3 scripts/fix_unmatched_alignment.py')
        print('     or manually insert \\n breaks in learning_data.js at Vilna line boundaries')
        sys.exit(1)

    ok = len(dafs_with_txt)
    print(f'\nOK: all {ok} daf align cleanly to Vilna daftext files.')
    sys.exit(0)

if __name__ == '__main__':
    main()
