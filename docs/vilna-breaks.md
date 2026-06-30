# Vilna Column Break System

## What it is

Each `he:` field in `learning_data.js` can contain `\n` sequences that render as hard line
breaks (CSS `white-space: pre-wrap` on `.line-he`). Placing these breaks at the same
word positions as the Vilna Shas printed column mirrors the visual rhythm of the
canonical printed Talmud.

## Where the scans are

`assets/daf-scans/yoma_XXa.pdf` — 173 PDFs (2a–88a). GIFs are no longer used.
`scripts/vilna_lines.py` reads PDFs directly via PyMuPDF; no separate GIF conversion needed.

### Primary source: talmud.dev API (preferred over PDF pipeline)

`talmud.dev/api/daf/Yoma/<daf>` returns unvowelized Gemara text in **exact Vilna print order**
with `\r\n` per printed column line. This is faster and more reliable than PDF/OCR.

```bash
# Cache one daf locally
python3 scripts/fetch_talmuddev.py 2a    # → assets/talmuddev/2a.json
# Cache all daf
python3 scripts/fetch_talmuddev.py --all --skip-existing
```

Output (`assets/talmuddev/<daf>.json`):
- `lines[]` — unvowelized Gemara strings, one per Vilna printed line
- `rashi[]` — unvowelized Rashi strings, one per Vilna printed line

Use these unvowelized tokens to locate break positions in the vowelized Sefaria `he:` text.
Fall back to the PDF pipeline below only if talmud.dev is unavailable.

## Column anatomy

Each Vilna page has three columns:

| Position | Content |
|----------|---------|
| Right    | Rashi commentary |
| **Center** | **Main Gemara text ← match breaks to THIS column** |
| Left     | Tosafot commentary |

## Vowelized text vs. Vilna unvoweled

The Vilna print is unvoweled. Our `he:` fields contain Sefaria's fully vowelized text.

**Rule: match WORD POSITIONS only** — which token ends each Vilna center-column line.
Never estimate by character count or by the ~6–7 word guideline; those are
orientation hints only, not a substitute for reading the scan.

---

## PDF pipeline (fallback when talmud.dev is unavailable)

**Not currently available.** The scripts `vilna_lines.py`, `vilna_position.py`, and
`daf_extract.py` are not in the repo, `assets/daf-scans/` is empty, and
`docs/vilna-index/` is empty. Use talmud.dev exclusively.

If this pipeline is ever restored, the workflow is:
1. Fetch PDFs via `scripts/daf_extract.py` into `assets/daf-scans/`
2. Generate line strips via `scripts/vilna_lines.py Xa`
3. Record `docs/vilna-index/Xa.json` with token counts and last words per line
4. Apply breaks via `scripts/vilna_position.py Xa`

### Step 3 — validate

```bash
npm run validate -- Xa
```

The validator strips `\n` before comparing to Sefaria, so break positions are
invisible to the content check — only text correctness is verified. Fix any reported
differences before committing (usually a vowel mark inconsistency — kamatz vs sheva,
dagesh, or combining-character order).

### Step 4 — commit

Bump version and commit. Pair two adjacent daf per version bump when both validate.
Edit `VERSION`, run `python3 scripts/sync_version.py` (updates `package.json` and
`package-lock.json`). Cache busters in `index.html` are injected at build time and
do not need manual edits. Update the status table below in the same commit.

---

## Important: do not estimate

Estimating ~6–7 words per line and calling the result "confirmed" is the failure mode
that produced wrong breaks on 2a segs 6 and 7 (and likely others done before this
pipeline existed). Estimated positions carry no scan evidence; they just happened to
survive context compaction with "confirmed" labels.

If a strip is illegible for a specific line, leave that segment unbroken and note it
in the index `_note` field. Do not guess.

---

## Duplicate `he:` texts (substring ordering)

When the same Sefaria text is used in two `he:` entries (one is a substring of the
other), process the **longer** text first. After it receives embedded `\n` breaks, the
shorter plain text no longer appears inside it, and the shorter replacement safely
targets only its own occurrence.

---

## Per-daf checklist

Before marking a daf done:

- [ ] `scripts/vilna_lines.py Xa` run; montage images read and line endings recorded
- [ ] `docs/vilna-index/Xa.json` written with counts + lastwords for every segment > 8 words
- [ ] `scripts/vilna_position.py Xa` ran with 0 assertion failures
- [ ] `npm run validate -- Xa` passes with 0 errors
- [ ] Substring ordering respected (longer before shorter) for any duplicate he: texts
- [ ] Status table below updated

---

## Daf status

All content rebuilt from scratch in v8.5 using talmud.dev as the Vilna source.
The vilna-index pipeline (vilna_lines.py, vilna_position.py, docs/vilna-index/) is
not currently in use - talmud.dev lines[] is the authoritative source for all
Vilna break positions. Daftext files (assets/daftexts/) exist for 2a-88a; only
2a and 2b currently have talmuddev JSON cached.

| Daf | Status   | Version | Notes |
|-----|----------|---------|-------|
| 2a  | ✓ done   | v8.6    | talmud.dev L1-L39; 39 lines; L39 catchword shown |
| 2b  | ✓ done   | v8.6    | talmud.dev L1-L30; 30 lines |
| 3a+ | pending  |         | daftext files exist (2a-88a); talmuddev JSON not yet cached |

---

## Notes

- Seg 1 of 3a is the mnemonic `פָּזֵ״ר קֶשֶׁ״ב.` — one line, no breaks needed.
- Segments with 8 or fewer words fit on one Vilna line — skip them.
- Segments that span a page boundary (e.g., seg 12 of 3b-2 continues on 3a text)
  may appear truncated; apply breaks only to the text that is present.
- Kamatz (ָ) and sheva (ְ) look nearly identical in many fonts. If `vilna_position.py`
  reports a `lastwords` mismatch rather than a token count mismatch, check that the
  anchor uniquely identifies the right segment.
- 13a has two entries both labelled `seg: 6` — a long "question" entry and a short
  "objection" entry whose text is a substring of the long one. Replace long first.
