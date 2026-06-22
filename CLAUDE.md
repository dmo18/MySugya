# MySugya - Claude maintainer guide

MySugya is a universal React Talmud study app. Tractates are loaded as self-contained modules. Yoma is the first module, frozen at v10.75 (173 daf, 492 sugyot, 8,854 rashiLines in runtime; 8,878 rashiTranslations in source enrichment layer).

---

## Universal rules (apply to all work)

- Never use em dashes or en dashes in any output, commit message, code comment, or doc. Use a plain hyphen or reword. Exception: verbatim Sefaria text in `he:`/`en:` fields may keep whatever characters Sefaria returns - do not alter those.
- Commit and push directly to main. No feature branches, no pull requests.
- On a fresh clone, run `git config core.hooksPath githooks` once so the pre-commit gate is active.
- Bump the version on every commit: edit only `DATA_VERSION` in `modules/yoma/learning_data.js`. The pre-commit hook runs `scripts/sync_version.py`, which auto-updates VERSION, package.json, index.html cache busters, and manifest.js dataVersion.
- At the end of every task, state the current version (from `DATA_VERSION` in `modules/yoma/learning_data.js` or the VERSION file).
- Never fetch Sefaria or talmud.dev via WebFetch or sub-agents. Use `curl | python3` directly in Bash, sequentially.
- URL policy: always link the live site (https://mysugya.com/...) once the domain is configured. During transition: https://dmo18.github.io/MySugya/...
- Yoma corpus is FROZEN. Do not modify any files under `modules/yoma/` without explicit approval.

---

## Repository structure

```
MySugya/
  index.html              (universal shell)
  app.jsx                 (universal React app - reads MYSUGYA_MANIFEST)
  tweaks-panel.jsx        (universal settings panel - generic)
  styles.css              (universal styles)
  favicon.svg             (MySugya mark)
  manifest.js             (module registry - MYSUGYA_MANIFEST)
  daf.html                (legacy redirect shim)
  VERSION                 (current version, synced from active module)
  package.json            (name: mysugya, all npm scripts)
  CLAUDE.md               (this file)
  SOURCES.md              (acknowledgments)
  scripts/
    sync_version.py       (version sync - runs on pre-commit)
  shared/
    schema_map.js         (canonical schema contract)
  githooks/
    pre-commit            (version sync + smoke tests)
  tests/
    smoke/
      render_check.py     (app shell smoke test)
  docs/                   (technical docs)
  modules/
    yoma/                 (FROZEN Yoma module - see modules/yoma/MODULE.md)
```

## Module system

`manifest.js` exports `MYSUGYA_MANIFEST` - an array of module descriptors. The app reads the `?module=` URL param (default: first manifest entry) and dynamically loads the corresponding `dataScript`.

Each module's `learning_data.js` exports the standard globals: `TRACTATE_META`, `PERAKIM`, `DAF_INDEX`, `DAF_CONTENT`, `DATA_VERSION`.

**To add a new masechta:**
1. Create `modules/<masechta>/` following the layout in `modules/yoma/`.
2. Add an entry to `manifest.js` with the correct `dataScript` path.
3. The app shell loads it automatically via `?module=<id>`.
4. Follow the 14-step process in Part B below.

## Version management

`DATA_VERSION` in `modules/yoma/learning_data.js` is the version source. `scripts/sync_version.py` syncs it to:
- `VERSION`
- `package.json` version
- `index.html` cache busters (`?v=`)
- `manifest.js` `dataVersion`

Bump the version on every commit by editing `DATA_VERSION` in the active module's learning_data.js.

## Mandatory smoke test

`npm test` - confirms the shell loads, manifest.js is version-busted, legacy redirect works, responsive CSS is present.

## Yoma module validation

Run before any commit that touches Yoma module files:

```
npm run validate:yoma
npm run audit:order:yoma
npm run validate:en:yoma
npm run validate:daftext:yoma
npm run validate:rashi:yoma
```

Or directly from `modules/yoma/`:
```
python3 scripts/validate_sefaria.py
```

See `modules/yoma/MODULE.md` for complete Yoma module docs.

## Do not do these things

- Do not modify any file under `modules/yoma/` without explicit approval (corpus is frozen).
- Do not hand-edit `modules/yoma/learning_data.js` - rebuild from source.
- Do not hand-edit `modules/yoma/assets/daftexts/*.txt` - regenerate them.
- Do not bypass the pre-commit hook (`--no-verify`).
- Do not add Tosafot or expand scope beyond current enrichment.
- Do not add schema fields casually - update `shared/schema_map.js`.
- Do not move module files without updating manifest.js and sync_version.py.

---

# Part A: Maintaining an Existing Module

For Yoma specifically: see `modules/yoma/MODULE.md`.

The pattern generalizes: each module has its own `scripts/`, `assets/`, and `MODULE.md`. Validators run from the module directory as cwd. npm scripts in root `package.json` use `cd modules/<id> && python3 scripts/...`.

---

# Part B: Building a New Masechta

Follow the 14-step pipeline. Replace "Yoma"/"yoma" with the new masechta throughout.

1. **Create the source store.** Fetch each daf from the Sefaria API and copy he/en verbatim into a JS source file under `modules/<masechta>/source_store.js`.

   ```bash
   curl -s "https://www.sefaria.org/api/texts/<Masechta>.<daf>?context=0"
   ```

   The response has parallel `he[]` and `text[]` arrays. Copy verbatim. Format mirrors `modules/yoma/source_store.js`. Minimal structure:

   ```js
   // BERAKHOT 2a
   "2a": {
     summary: "One-paragraph overview.",
     sugyot: [{
       id: "berakhot-002a-s01",
       lines: [{
         id: "berakhot-002a-l01", lineType: "mishnah",
         he: "<verbatim Sefaria he[0]>", en: "<verbatim Sefaria text[0]>",
         whats: "One sentence.", hint: "Optional."
       }],
       glossary: [{ he: "כרי", translit: "kri", en: "A heap; volume measure." }]
     }]
   }
   ```

2. **Fetch the talmud.dev cache** - update `fetch_talmuddev.py` masechta name, then run: `python3 modules/<masechta>/scripts/fetch_talmuddev.py --all`

3. **Generate daftexts** - `python3 modules/<masechta>/scripts/validate_daftext.py --fix`

4. **Embed Vilna line breaks** - update `MASECHTA` constant in `daftext_align.py`, then run per daf.

5. **Create enrichment JSON** - one `<daf>.learning.json` per daf in `modules/<masechta>/assets/learning/<masechta>/`.

6. **Configure and build.** Update `build_learning_data.py` variables: `SOURCE_JS`, `LEARN_DIR`, `ENRICHED`. Then: `python3 modules/<masechta>/scripts/build_learning_data.py`

7. **Add to manifest.js** - add the new module entry with correct `dataScript` path.

8. **Validate source** - `cd modules/<masechta> && python3 scripts/validate_sefaria.py`

9. **Validate English alignment** - `python3 scripts/validate_en.py`

10. **Validate Vilna daftexts** - `python3 scripts/validate_daftext.py`

11. **Validate Rashi** - `python3 scripts/validate_rashi.py`

12. **Order audit** - `python3 scripts/order_audit.py`

13. **Smoke tests** - `npm test` (from repo root)

14. **Product quality audit** - sample sugyot across all chapters and sugya types.

## Enrichment quality standards

(Same as the Yoma standards - see SOURCES.md or the Yoma build docs for detail.)

- argumentFlow: real logical moves only, no fabricated steps.
- quizSeeds: must test a real distinction. Forbidden: "What does the Gemara rule regarding..."
- misconceptions: specific learner error + correction. Forbidden: generic "more nuanced" text.
- Rashi English: must say what Rashi adds. Forbidden: "Rashi provides final clarification..."

## Freeze definition

A masechta may be declared frozen only when:
- 100% daf coverage, all 7 gates pass.
- No fabricated argumentFlow, quiz stubs, misconception stubs, Rashi stub translations.
- Product quality audit sampling passes (no misleading sugyot).
- Live site displays the frozen version number.
