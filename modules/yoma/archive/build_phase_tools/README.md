# Build Phase Tools - Archived

These scripts were used during initial corpus construction for tractate Yoma.
They are retained here for disaster recovery only. They are not part of normal
maintenance and are not called by any validator, pre-commit hook, or npm script.

## Status

Corpus is complete at 173/173 daf, 492 sugyot, 8,878 Rashi helper lines.
Corpus was frozen at v10.72 (June 2026). These tools are no longer needed
for any routine task.

## Tools

### build_daf.py
Automated daf builder for source_store.js. Fetched Sefaria he[] and en[]
arrays, detected segment types, grouped into sugyot, and inserted entries
into source_store.js. Used to build daf during the initial corpus run.

### fix_en.py
Bulk-fixed mismatched en: translations in source_store.js by fetching
Sefaria's English at the correct segment index and replacing wrong entries.
Used when validate:en reported mismatches.

### fix_order.py
Restored Vilna/Sefaria reading order inside daf of source_store.js when
content was pasted out of sequence. Used when audit:order reported inversions.

### fix_coverage.py
Closed Vilna line-coverage gaps by tiling each daf's he: fields to cover
the complete page. Run before daftext_align.py when segments were missing.

### fix_unmatched_alignment.py
Inserted Vilna line breaks into specific he: fields that daftext_align.py
could not match due to numeric abbreviations. Hardcoded fixes for 16 specific
segments. All fixes are already applied in source_store.js.

### validate_alignment.py
Dry-ran daftext_align.py on all daf to pre-check alignment before committing.
Superseded for daily maintenance by `npm run validate:daftext`, which checks
daftext provenance rather than alignment.

## If You Need These Tools

If source_store.js is ever modified (which should be rare after the freeze),
update your paths: these files are in archive/build_phase_tools/, not scripts/.
Update any script invocations accordingly before running.

Do not move these files back to scripts/ without also updating CLAUDE.md,
githooks/pre-commit, and package.json.
