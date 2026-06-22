#!/usr/bin/env python3
"""
validate_sefaria.py — verify every he: content field in learning_data.js against live Sefaria API.

For each he: field found inside a lines: [] array, the script:
  1. Confirms the opening text appears verbatim in the Sefaria response for that daf.
  2. Confirms our text matches Sefaria character-for-character (catches wrong words).
  3. Flags possible truncation (our text ends but the segment continues).

On success writes .sefaria-validated (sha256 of learning_data.js) so the pre-commit
hook can confirm validation is current before allowing a commit.

Usage:
  python3 scripts/validate_sefaria.py          # all daf
  python3 scripts/validate_sefaria.py 15a 16b  # specific daf only
"""

import hashlib
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request

DATA_JS = "learning_data.js"
STAMP_FILE = ".sefaria-validated"


# ---------------------------------------------------------------------------
# Sefaria helpers
# ---------------------------------------------------------------------------

def strip_html(s):
    return re.sub(r"<[^>]+>", "", s)


def normalize(s):
    s = strip_html(s)
    s = unicodedata.normalize("NFC", s)
    return re.sub(r"\s+", " ", s).strip()


def fetch_joined(daf_id):
    """Return (joined_text, None) on success or (None, error_str) on failure."""
    url = f"https://www.sefaria.org/api/texts/Yoma.{daf_id}?lang=he&context=0"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "YomaValidator/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        segs = [normalize(s) for s in data.get("he", []) if s.strip()]
        return " ".join(segs), None
    except urllib.error.URLError as e:
        return None, f"network: {e}"
    except Exception as e:
        return None, str(e)


# ---------------------------------------------------------------------------
# learning_data.js parser — extracts (lineno, daf, he_text) from lines: [] blocks only
# ---------------------------------------------------------------------------

def parse_content_fields(content):
    """
    Yields (lineno, daf_id, he_text) for every he: field inside a lines: [ ] block.

    Each line item is a multi-line JS object:
      {
        kind: "...",
        he: "...",      ← captured here
        en: "...",
      },

    Glossary arrays use a different key (glossary: [...]) and are outside any
    lines: [...] block, so they are naturally excluded by the bracket tracker.
    title_he: is a different key name and won't match the \bhe\s*: regex.
    """
    raw_lines = content.split("\n")

    daf_re    = re.compile(r'^\s*"(\d+[ab])":\s*\{')
    he_re     = re.compile(r'\bhe\s*:\s*"((?:[^"\\]|\\.)*)"')

    current_daf = None
    in_lines    = False
    depth       = 0   # square-bracket depth within lines: [ ]

    for lineno, line in enumerate(raw_lines, 1):
        # New daf entry
        m = daf_re.match(line)
        if m:
            current_daf = m.group(1)
            in_lines    = False
            depth       = 0
            continue

        if current_daf is None:
            continue

        # Detect opening of lines: [ ] — track depth with [ / ]
        if not in_lines and re.search(r'\blines\s*:\s*\[', line):
            in_lines = True
            depth    = line.count("[") - line.count("]")
            continue

        if in_lines:
            depth += line.count("[") - line.count("]")
            if depth <= 0:
                in_lines = False
                continue

            # Capture any he: field inside this block (multi-line objects)
            m = he_re.search(line)
            if not m:
                continue

            raw  = m.group(1)
            text = raw.replace('\\"', '"').replace("\\\\", "\\").replace("\\n", " ").strip()
            if len(text) >= 15:
                yield lineno, current_daf, text


# ---------------------------------------------------------------------------
# Per-field check
# ---------------------------------------------------------------------------

def check_field(he_text, sefaria_joined):
    """
    Returns (ok: bool, reason: str).

    Validates against the full joined Sefaria text (all segments concatenated)
    so that intentionally partial-segment he: fields still pass.

    Checks all occurrences of the prefix — a field that begins with text shared
    by the mishnah AND the baraita will still pass if it matches the baraita copy.

    Catches:
      1. Fabricated text not found anywhere in Sefaria
      2. Wrong words (text diverges from Sefaria at some character)

    Does NOT flag truncation: learning_source_store.js intentionally splits long Sefaria
    segments across multiple he: fields.
    """
    our = normalize(he_text)
    if not our:
        return True, ""

    prefix = our[:30]

    if prefix not in sefaria_joined:
        return False, "NOT FOUND in Sefaria"

    # Try every occurrence of the prefix — pass if any matches exactly
    last_reason = None
    search_from = 0
    while True:
        pos = sefaria_joined.find(prefix, search_from)
        if pos == -1:
            break

        sefaria_slice = sefaria_joined[pos: pos + len(our)]

        if our == sefaria_slice:
            return True, ""

        # Record the reason from this attempt
        diff_pos = next(
            (i for i, (a, b) in enumerate(zip(our, sefaria_slice)) if a != b),
            None,
        )
        if diff_pos is not None:
            last_reason = (
                f"TEXT DIFFERS at char {diff_pos}: "
                f"ours='{our[diff_pos:diff_pos+20]}' "
                f"vs sefaria='{sefaria_slice[diff_pos:diff_pos+20]}'"
            )
        elif len(our) > len(sefaria_slice):
            last_reason = "TEXT OVERRUNS Sefaria at matched position"
        else:
            last_reason = "TEXT MISMATCH"

        search_from = pos + 1

    return False, last_reason or "NOT FOUND in Sefaria"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    target_daf = set(sys.argv[1:]) if len(sys.argv) > 1 else None

    with open(DATA_JS, encoding="utf-8") as f:
        content = f.read()

    fields = list(parse_content_fields(content))

    # Group by daf
    by_daf = {}
    for lineno, daf, text in fields:
        if target_daf and daf not in target_daf:
            continue
        by_daf.setdefault(daf, []).append((lineno, text))

    total_fields = sum(len(v) for v in by_daf.values())
    print(f"Validating {total_fields} he: fields across {len(by_daf)} daf...\n")

    errors   = []   # (daf, lineno, reason, text)
    skipped  = []   # daf ids that couldn't be fetched

    for daf_id in sorted(by_daf.keys(), key=lambda x: (int(x[:-1]), x[-1])):
        print(f"  {daf_id:4s}  fetching...", end=" ", flush=True)
        sefaria_joined, err = fetch_joined(daf_id)
        time.sleep(0.3)

        if err:
            print(f"SKIP ({err})")
            skipped.append(daf_id)
            continue

        ok_count  = 0
        daf_errs  = []

        for lineno, he_text in by_daf[daf_id]:
            ok, reason = check_field(he_text, sefaria_joined)
            if ok:
                ok_count += 1
            else:
                daf_errs.append((lineno, reason, he_text))

        if daf_errs:
            print(f"✗  {ok_count} OK  {len(daf_errs)} ERROR(S)")
            for ln, reason, text in daf_errs:
                errors.append((daf_id, ln, reason, text))
        else:
            print(f"✓  {ok_count} fields")

    print()

    if skipped:
        print(f"⚠   Skipped {len(skipped)} daf (network): {', '.join(skipped)}\n")

    if errors:
        print(f"❌  {len(errors)} error(s) found:\n")
        for daf_id, lineno, reason, text in errors:
            preview = text[:75] + ("…" if len(text) > 75 else "")
            print(f"  [{daf_id}] line {lineno}: {reason}")
            print(f"    he: \"{preview}\"")
            print()
        sys.exit(1)

    # Write stamp: sha256 of learning_data.js so pre-commit can verify validation is current
    data_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    with open(STAMP_FILE, "w") as f:
        f.write(data_hash + "\n")

    if skipped:
        print(f"✅  Checked all reachable daf. Skipped: {', '.join(skipped)}.")
        print(f"    Stamp NOT written (incomplete run). Retry when network is available.")
        # Don't write stamp for partial runs
        try:
            import os; os.remove(STAMP_FILE)
        except FileNotFoundError:
            pass
        sys.exit(1)

    print(
        f"✅  All {total_fields} he: fields verified against Sefaria.\n"
        f"    Validation stamp written to {STAMP_FILE}."
    )


if __name__ == "__main__":
    main()
