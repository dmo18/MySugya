# Yoma Module - Frozen

Tractate Yoma: 173 daf (2a-88a), 8 chapters, 492 sugyot, 8,854 rashiLines (runtime); 8,878 rashiTranslations (source enrichment layer).

**Status: FROZEN at v12.7. Do not modify any learning content.**

---

## What is frozen

- `learning_data.js` - GENERATED runtime data. Do not hand-edit.
- `source_store.js` - Sefaria-validated Gemara he/en. Do not modify.
- `assets/learning/yoma/*.learning.json` - Enrichment source. Do not modify.
- `assets/talmuddev/*.json` - Vilna line source. Do not modify.
- `assets/daftexts/*.txt` - Generated daftexts. Do not modify.

## Validation gates

Run from the MySugya repo root:

```
npm run validate:yoma        # he: verbatim Sefaria (all 173 daf)
npm run audit:order:yoma     # Vilna sequence, no inversions
npm run validate:en:yoma     # en: aligned to correct he: segment
npm run validate:daftext:yoma # daftexts from talmud.dev
npm run validate:rashi:yoma  # Rashi layer integrity
```

Or run directly from this directory:

```
cd modules/yoma
python3 scripts/validate_sefaria.py
python3 scripts/order_audit.py
python3 scripts/validate_en.py
python3 scripts/validate_daftext.py
python3 scripts/validate_rashi.py
```

All validators read from `modules/yoma/` as their working root.

## Rebuild data (only if enrichment JSON was corrected)

```
cd modules/yoma
python3 scripts/build_learning_data.py
```

Then re-run all validation gates and commit learning_data.js.

## Scripts

| Script | Purpose |
|---|---|
| `scripts/build_learning_data.py` | Generate learning_data.js from source_store.js + assets/ |
| `scripts/validate_sefaria.py` | Verify he: fields against live Sefaria API |
| `scripts/completeness_audit.py` | Every Sefaria segment represented |
| `scripts/order_audit.py` | Vilna sequence check |
| `scripts/validate_en.py` | English alignment check |
| `scripts/validate_daftext.py` | Daftext provenance from talmud.dev |
| `scripts/validate_rashi.py` | Rashi layer integrity |
| `scripts/fetch_talmuddev.py` | Refresh talmud.dev cache |
| `scripts/daftext_align.py` | Embed Vilna line breaks |

## Archive tools (disaster recovery only)

`archive/build_phase_tools/` - used during initial corpus construction only. See that directory's README.

## Data counts (frozen state)

- Daf: 173 (2a through 88a)
- Sugyot: 492
- rashiLines (runtime, in learning_data.js): 8,854
- rashiTranslations (source enrichment layer): 8,878
- Corpus version: v12.7
