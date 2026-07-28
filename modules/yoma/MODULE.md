# Yoma Module - Frozen Scope, Actively Maintained Content

Tractate Yoma: 173 daf (2a-88a), 8 chapters, 492 sugyot, 8,854 rashiLines (runtime) and 8,854 rashiTranslations (source enrichment layer).

**Status: corpus SCOPE is frozen (173 daf, 492 sugyot; no new sugyot are added). Content within that scope is actively maintained: corrections land via explicit-approval PRs following `docs/worker-pipeline-sop.md`, never as ad hoc hand-edits. See `docs/tractate-build-process.md` and `docs/rashi-audit-backlog.md` for the live record of in-scope correction work (the Yoma Rashi scaffold-fabrication remediation campaign completed at VERSION 15.290; a Rashi content-quality audit is in progress, see `docs/rashi-audit-backlog.md`'s Scope note). The `linkedGemaraLineIds` association layer is complete and referentially exhaustive (0 broken, 0 cross-daf across all 8,854 entries); the linked-renderer readiness gate reports 7/8 as of VERSION 15.337 - see `docs/reports/rashi-association-audit.md`. The linked renderer is test/audit only (`?rashiAssoc=linked`); production still uses the legacy vilnaLine-coincidence renderer.**

---

## What "frozen scope" means

No new daf, sugyot, or fields are added without a deliberate schema/scope decision (see `shared/schema_map.js` and CLAUDE.md's "Do not add schema fields casually" rule). Within the existing 173-daf/492-sugya scope, these files are corrected only via the worker pipeline (manifest, preflight, packet, verify, one PR, sequential merge), never hand-edited directly:

- `learning_data.js` - GENERATED runtime data. Do not hand-edit; rebuild it.
- `source_store.js` - Sefaria-validated Gemara he/en. Do not hand-edit.
- `assets/learning/yoma/*.learning.json` - Enrichment source, including `rashiTranslations`. Corrected only through the worker pipeline.
- `assets/talmuddev/*.json` - Vilna line source. Do not hand-edit.
- `assets/daftexts/*.txt` - Generated daftexts. Do not hand-edit; regenerate.

## Validation gates

Run from the MySugya repo root:

```
npm run validate:yoma          # he: verbatim Sefaria (all 173 daf)
npm run audit:order:yoma       # Vilna sequence, no inversions
npm run validate:en:yoma       # en: aligned to correct he: segment
npm run validate:daftext:yoma  # daftexts from talmud.dev
npm run validate:rashi:yoma    # Rashi layer integrity
npm run validate:literal:yoma  # en_lit coverage threshold
npm run validate:schema:yoma   # display/learning schema completeness (manual; not in default npm test)
npm run validate:rashi:boundary:yoma   # boundary (empty-link) authorization registry
npm run audit:rashi-renderer-readiness:yoma   # linked-renderer readiness gate (reporting only)
```

Or run directly from this directory:

```
cd modules/yoma
python3 scripts/validate_sefaria.py
python3 scripts/order_audit.py
python3 scripts/validate_en.py
python3 scripts/validate_daftext.py
python3 scripts/validate_rashi.py
python3 scripts/validate_literal.py
python3 scripts/validate_schema_completeness.py
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

## Data counts

- Daf: 173 (2a through 88a)
- Sugyot: 492
- rashiLines (runtime, in learning_data.js): 8,854
- rashiTranslations (source enrichment layer): 8,854
- linkedGemaraLineIds declared associations: 10,047 (7,648 single-link, 1,186 multi-link, 279 Mishnah, 447 suffixed-id, 0 sparse, 20 boundary/empty-link, all 20 authorized in `scripts/allowlists/rashi_boundary_authorizations.json`); 0 broken, 0 cross-daf
- Platform VERSION: see repository root `VERSION` (data-layer versions such as `DATA_VERSION` in this module's `learning_data.js` are tracked independently; see CLAUDE.md's Version management section)
