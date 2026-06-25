# MySugya - Claude maintainer guide

MySugya is a universal React Talmud study app. Tractates are loaded as self-contained modules. Yoma is the first module and its learning corpus is frozen. The current app and runtime data version is 12.27.

Yoma scope: 173 daf, 492 sugyot. The `en_lit:` layer stores literal translation data for Yoma. See the Literal Translation Pipeline section below.

---

## Universal rules

- Never use em dashes or en dashes in project-authored output, commit messages, code comments, or docs. Use a plain hyphen or reword. Exception: verbatim Sefaria text in `he:` and `en:` fields may keep whatever characters Sefaria returns. Do not alter those fields.
- Commit to `main` unless the active repository policy changes.
- On a fresh clone, run `git config core.hooksPath githooks` once so the pre-commit gate is active.
- Bump the version on every commit that changes runtime or data behavior: edit only `DATA_VERSION` in `modules/yoma/learning_data.js`. The pre-commit hook runs `scripts/sync_version.py`, which auto-updates `VERSION`, `package.json`, `index.html` cache busters, and `manifest.js` `dataVersion`.
- At the end of every task, state the current version from `DATA_VERSION` in `modules/yoma/learning_data.js` or the `VERSION` file.
- For single-daf lookups and one-off checks, use `curl | python3` directly in Bash when running locally.
- For bulk literal-translation fetches, launch parallel agents using the fetch scripts below. Each agent runs `fetch_literal_en.py` for its assigned daf range. Progress is tracked atomically in `progress.json`.
- URL policy: use `https://mysugya.com/...` once the domain is configured. During transition, use `https://dmo18.github.io/MySugya/...`.
- Yoma corpus is frozen. Do not modify any files under `modules/yoma/` without explicit approval.

---

## Repository structure

```
MySugya/
  index.html                    Development app shell
  app.jsx                       Universal React app, reads MYSUGYA_MANIFEST
  tweaks-panel.jsx              Universal settings panel
  styles.css                    Universal styles
  favicon.svg                   MySugya mark
  manifest.js                   Module registry
  daf.html                      Legacy redirect shim
  VERSION                       Current version, synced from active module
  package.json                  npm scripts and dependencies
  package-lock.json             Locked npm dependency graph
  playwright.config.js          Browser smoke test config
  README.md                     Public project docs
  CLAUDE.md                     Maintainer guide
  SOURCES.md                    Sources and technology attribution
  .github/workflows/
    deploy-pages.yml            Build, verify, test, and deploy dist to Pages
  scripts/
    build.mjs                   Production esbuild pipeline
    build-entry.jsx             Build entry ordering
    check-deploy-html.mjs       Dist HTML safety check
    sync_version.py             Version sync, runs on pre-commit
    build/react-shim.js         React injection for esbuild
  shared/
    schema_map.js               Canonical schema contract
  githooks/
    pre-commit                  Version sync plus smoke tests
  tests/
    smoke/render_check.py       Production build smoke test
    browser/yoma-smoke.spec.js  Playwright Yoma browser smoke test
  docs/
    vilna-breaks.md             Vilna edition reference
  modules/
    yoma/                       Frozen Yoma module, see modules/yoma/MODULE.md
```

---

## Module system

`manifest.js` exports `MYSUGYA_MANIFEST`, an array of module descriptors. The app reads the `?module=` URL param, defaulting to the first manifest entry, and dynamically loads the corresponding `dataScript`.

Each module's `learning_data.js` exports the standard globals: `TRACTATE_META`, `PERAKIM`, `DAF_INDEX`, `DAF_CONTENT`, and `DATA_VERSION`.

To add a new masechta:

1. Create `modules/<masechta>/` following the layout in `modules/yoma/`.
2. Add an entry to `manifest.js` with the correct `dataScript` path.
3. The app shell loads it automatically via `?module=<id>`.
4. Follow the 14-step process in Part B below.

---

## Version management

`DATA_VERSION` in `modules/yoma/learning_data.js` is the version source. `scripts/sync_version.py` syncs it to:

- `VERSION`
- `package.json` version
- `index.html` cache busters (`?v=`)
- `manifest.js` `dataVersion`

Bump the version by editing `DATA_VERSION` in the active module's `learning_data.js`.

Current version: 12.27.

---

## Build and deployment

Root `index.html` is a development shell. It intentionally loads React development UMD scripts and Babel standalone so JSX can run directly from source files during development.

Production must serve generated `dist/`, not the repository root.

Key commands:

```
npm run build
npm run check:deploy-html
npm test
npm run test:browser
```

`npm run build` uses `scripts/build.mjs` to:

1. Remove and recreate `dist/`.
2. Bundle `tweaks-panel.jsx` and `app.jsx` with esbuild.
3. Use npm `react` and `react-dom` through `scripts/build/react-shim.js`.
4. Copy static files and `modules/` into `dist/`.
5. Rewrite `dist/index.html` so it uses `assets/app-<VERSION>.js` instead of dev-only loaders.

`npm run check:deploy-html` fails if `dist/index.html` contains development-only loader tokens such as `text/babel`, `babel.min.js`, `react.development.js`, or `react-dom.development.js`.

GitHub Pages deployment lives at `.github/workflows/deploy-pages.yml`. It runs on pull requests, pushes to `main`, and manual dispatch. On pushes to `main`, it uploads and deploys `dist/` to GitHub Pages after build and tests pass.

---

## Required tests

### Standard smoke test

```
npm test
```

This builds `dist/`, serves it locally, checks the production bundle, verifies the legacy redirect, confirms built HTML does not contain dev-only loaders, and checks responsive CSS guardrails.

### Browser smoke test

```
npm run test:browser
```

This Playwright test covers Yoma 2a rendering, Rashi, previous navigation, mobile overflow, and dark mode.

### Yoma validation gates

Run before any commit that touches Yoma module files:

```
npm run validate:yoma
npm run audit:order:yoma
npm run validate:en:yoma
npm run validate:daftext:yoma
npm run validate:rashi:yoma
npm run validate:literal:yoma
```

Or directly from `modules/yoma/`:

```
python3 scripts/validate_sefaria.py
python3 scripts/order_audit.py
python3 scripts/validate_en.py
python3 scripts/validate_daftext.py
python3 scripts/validate_rashi.py
python3 scripts/validate_literal.py
```

See `modules/yoma/MODULE.md` for complete Yoma module docs.

---

## Literal Translation Pipeline for Yoma en_lit

The `en_lit:` field stores a direct/literal rendering extracted from the William Davidson Edition. WD uses `<b>` tags for literal translation text; plain text is Steinsaltz editorial addition. Extracting only the bold portions gives a concise literal rendering.

### Files

```
modules/yoma/
  scripts/
    fetch_literal_en.py    Fetch WD text from Sefaria, extract bold segments, save per-daf JSON
    build_literal_layer.py Inject en_lit fields from per-daf JSON into learning_data.js
    validate_literal.py    Gate: verify en_lit coverage meets threshold
  assets/literal_en/
    <daf>.json             Raw fetch output: [{sefaria_ref, en_lit, source}]
    progress.json          Completion tracking, updated atomically and safe for parallel agents
```

### npm scripts

```
npm run fetch:literal:yoma    Fetch all daf with --all --skip-existing
npm run build:literal:yoma    Inject en_lit into learning_data.js
npm run validate:literal:yoma Gate check
npm run status:literal:yoma   Show fetch progress without exiting non-zero
```

### Running parallel agents

Split the 173 daf into ranges and launch agents concurrently. Example split:

```
Agent 1:  2a - 20b   cd modules/yoma && python3 scripts/fetch_literal_en.py --range 2a 20b --skip-existing
Agent 2: 21a - 39b   cd modules/yoma && python3 scripts/fetch_literal_en.py --range 21a 39b --skip-existing
Agent 3: 40a - 57b   cd modules/yoma && python3 scripts/fetch_literal_en.py --range 40a 57b --skip-existing
Agent 4: 58a - 73b   cd modules/yoma && python3 scripts/fetch_literal_en.py --range 58a 73b --skip-existing
Agent 5: 74a - 88a   cd modules/yoma && python3 scripts/fetch_literal_en.py --range 74a 88a --skip-existing
```

`progress.json` uses `fcntl.flock` for atomic updates, so agents can run concurrently without conflict.

After all agents complete:

1. Check status: `npm run status:literal:yoma`
2. Inject into `learning_data.js`: `npm run build:literal:yoma`
3. Gate check: `npm run validate:literal:yoma`
4. Bump `DATA_VERSION` in `learning_data.js` and commit.

Use `--skip-existing` to resume a partial run.

---

## Do not do these things

- Do not modify any file under `modules/yoma/` without explicit approval.
- Do not hand-edit `modules/yoma/learning_data.js`; rebuild from source.
- Do not hand-edit `modules/yoma/assets/daftexts/*.txt`; regenerate them.
- Do not bypass the pre-commit hook with `--no-verify`.
- Do not add Tosafot or expand scope beyond current enrichment.
- Do not add schema fields casually; update `shared/schema_map.js`.
- Do not move module files without updating `manifest.js` and `scripts/sync_version.py`.
- Do not deploy the repository root as production; deploy `dist/`.

---

## Help and Features Pages

The app includes global help and features pages accessible via the Chrome navigation bar (? and * buttons). These pages document keyboard shortcuts, study modes, enrichment layers, and app capabilities.

Maintaining Help and Features Pages:

1. Help Page (`app.jsx` - `HelpPage` component):
   - Lists keyboard shortcuts under Navigation and Display Controls.
   - Documents study modes: Solo, Chavruta, Class, Online.
   - Describes enrichment layers: Whats, Hints, Aha Moments, Deep Context, Argument Flow, Rashi.
   - Lists gestures: swipe left/right, swipe down on modal, scroll behavior.

2. Features Page (`app.jsx` - `FeaturesPage` component):
   - Provides overview of reading experience.
   - Describes enrichment layer capabilities.
   - Explains study mode customization.
   - Documents navigation and progress tracking.
   - Details Rashi tools.
   - Explains collaborative features.
   - Lists customization options.
   - Notes accessibility features.

When to update:

- Add new keyboard shortcuts to both Help page and the keyboard handler logic.
- Document new study modes or enrichment layers in the Help page.
- Update Features page descriptions when adding major capabilities.
- Keep feature descriptions concise and user-focused.

Edit locations:

- `app.jsx`: `HelpPage` and `FeaturesPage` components.
- `styles.css`: Help and Features modal styling.

Changes require no version bump unless the feature itself changes.

---

# Part A: Maintaining an Existing Module

For Yoma specifically, see `modules/yoma/MODULE.md`.

The pattern generalizes: each module has its own `scripts/`, `assets/`, and `MODULE.md`. Validators run from the module directory as cwd. npm scripts in root `package.json` use `cd modules/<id> && python3 scripts/...`.

---

# Part B: Building a New Masechta

Follow the 14-step pipeline. Replace Yoma/yoma with the new masechta throughout.

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
6. **Configure and build** - update `build_learning_data.py` variables: `SOURCE_JS`, `LEARN_DIR`, `ENRICHED`. Then run: `python3 modules/<masechta>/scripts/build_learning_data.py`.
7. **Add to manifest.js** - add the new module entry with correct `dataScript` path.
8. **Validate source** - `cd modules/<masechta> && python3 scripts/validate_sefaria.py`
9. **Validate English alignment** - `python3 scripts/validate_en.py`
10. **Validate Vilna daftexts** - `python3 scripts/validate_daftext.py`
11. **Validate Rashi** - `python3 scripts/validate_rashi.py`
12. **Order audit** - `python3 scripts/order_audit.py`
13. **Smoke tests** - `npm test` from repo root.
14. **Product quality audit** - sample sugyot across all chapters and sugya types.

## Enrichment quality standards

Same as the Yoma standards. See `SOURCES.md` or the Yoma build docs for detail.

- `argumentFlow`: real logical moves only, no fabricated steps.
- `quizSeeds`: must test a real distinction. Forbidden: generic ruling prompts.
- `misconceptions`: specific learner error plus correction. Forbidden: generic "more nuanced" text.
- Rashi English: must say what Rashi adds. Forbidden: generic final-clarification language.

## Freeze definition

A masechta may be declared frozen only when:

- 100% daf coverage and all validation gates pass.
- No fabricated `argumentFlow`, quiz stubs, misconception stubs, or Rashi stub translations remain.
- Product quality audit sampling passes with no misleading sugyot.
- Live site displays the frozen version number.
