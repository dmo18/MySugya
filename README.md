# MySugya - Universal Talmud Study Companion

A React-based web application for studying the Talmud with rich enrichment, literal translations, and Vilna edition reference markers.

**Current Version:** see `VERSION`  
**Status:** Production-ready app shell with frozen Yoma corpus

---

## Quick Start

### Prerequisites

- Node.js 20+ recommended
- npm
- Python 3.6+ for validation scripts and local static serving
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/dmo18/MySugya.git
cd MySugya

# Configure git hooks, one time only
git config core.hooksPath githooks

# Install dependencies
npm ci

# Run smoke tests
npm test
```

### Run Locally

```bash
npm run serve
# Open http://localhost:4173 in your browser
```

`npm run serve` builds the production `dist/` output and serves that directory locally.

### Build for Production

```bash
python3 scripts/sync_version.py
npm run build
npm run check:deploy-html
```

Production output is written to `dist/`. Deploy `dist/` as the web root. Do not deploy the repository root as the production site, because root `index.html` is a development shell that loads Babel and React development UMD scripts.

---

## Project Structure

```text
MySugya/
  index.html                    Development app shell
  app.jsx                       React app, multi-module support
  manifest.js                   Module registry
  package.json                  Scripts and dependencies
  package-lock.json             Locked npm dependency graph
  VERSION                       Canonical repository version
  styles.css                    Universal styles
  tweaks-panel.jsx              Settings UI, generic
  daf.html                      Legacy redirect shim
  favicon.svg                   App icon
  dist/                         Production build output, generated and ignored
  .github/workflows/
    deploy-pages.yml            Build, verify, test, and deploy dist to Pages
  scripts/
    build.mjs                   Production esbuild pipeline
    build-entry.jsx             Build entry ordering
    check-deploy-html.mjs       Deploy HTML safety check
    sync_version.py             Version sync from VERSION
    build/react-shim.js         React injection for esbuild
  modules/
    yoma/                       Yoma module, 173 daf, frozen corpus
      learning_data.js          Runtime data, generated, canonical data payload
      source_store.js           Retired transitional source store
      assets/                   Frozen enrichment and layout data
      scripts/                  Build and validation tools
  tests/
    smoke/render_check.py       Production build smoke test
    browser/yoma-smoke.spec.js  Playwright browser smoke test
  githooks/
    pre-commit                  Version sync plus smoke tests
  shared/
    schema_map.js               Data schema contract
  docs/
    vilna-breaks.md             Vilna edition reference
```

---

## Modules

### Yoma

- **Corpus Status:** Frozen baseline, do not modify learning content without explicit approval
- **Current App Version:** see `VERSION`
- **Daf Range:** 2a-88a, 173 daf
- **Sugyot:** 492
- **Chapters:** 8
- **Access:** `?module=yoma`, default module

Do not hand-edit these files unless explicitly approved:

- `learning_data.js`, generated runtime data
- `source_store.js`, retired transitional source store
- `assets/`, frozen enrichment and layout data

---

## Development Workflow

### Universal Rules

1. Commit to `main` unless the active repository policy changes.
2. Keep `VERSION` as the canonical repository version.
3. Run `python3 scripts/sync_version.py` after changing `VERSION`.
4. Run smoke tests before pushing.
5. No em dashes or en dashes in project-authored output and commits. Use plain hyphen.

### Version Sync

`VERSION` is the only human-edited global platform version source. After editing it, run:

```bash
python3 scripts/sync_version.py
```

This propagates the platform version to derived locations:

- `package.json` and `package-lock.json` - npm metadata, kept in sync because npm expects them, not authoritative
- `index.html` cache busters
- `manifest.js` `dataVersion`
- `modules/yoma/learning_data.js` `DATA_VERSION` - data-layer version; shares the same value as the platform version but is semantically separate

Do not hand-edit derived files to change the version. Edit `VERSION`, then run `sync_version.py`.

---

## Validation and Testing

### Production Smoke Test

```bash
npm test
```

This builds `dist/`, serves it locally, verifies the production bundle, checks that built HTML does not contain development-only Babel or React loaders, checks the legacy redirect, and checks responsive CSS guardrails.

### Browser Smoke Test

```bash
npm run test:browser
```

This runs the Playwright Yoma smoke test against built `dist/` and covers Yoma 2a rendering, Rashi, navigation, mobile overflow, and dark mode.

### Deploy HTML Check

```bash
npm run check:deploy-html
```

Run this after `npm run build`. It fails if `dist/index.html` contains development-only loader tokens such as `text/babel`, `babel.min.js`, or React development UMD scripts.

### Yoma Module Validation

```bash
npm run validate:yoma
npm run validate:en:yoma
npm run validate:daftext:yoma
npm run validate:rashi:yoma
npm run audit:order:yoma
npm run validate:literal:yoma
```

Or run from the module directory:

```bash
cd modules/yoma
python3 scripts/validate_sefaria.py
python3 scripts/validate_en.py
python3 scripts/validate_daftext.py
python3 scripts/validate_rashi.py
python3 scripts/order_audit.py
python3 scripts/validate_literal.py
```

---

## Deployment

The live site must serve generated `dist/`, not the source repository root. The root `index.html` is kept as a development shell and intentionally references Babel and React development scripts. `npm run build` rewrites the production HTML in `dist/index.html` to use the bundled app asset.

### GitHub Pages

This repository includes a GitHub Actions workflow at `.github/workflows/deploy-pages.yml` that runs on pull requests, pushes to `main`, and manual dispatch. The workflow:

1. Runs `npm ci`.
2. Installs Playwright Chromium.
3. Runs `npm run build`.
4. Runs the dist data-version patcher.
5. Runs `npm run check:deploy-html`.
6. Runs `npm test`.
7. Runs `npm run test:browser`.
8. On pushes to `main`, uploads and deploys only `dist/` to GitHub Pages.

### Manual Hosting

For any other static host, build locally or in CI and configure the host's publish directory to `dist/`:

```bash
npm ci
python3 scripts/sync_version.py
npm run build
npm run check:deploy-html
```

If a hosting provider can only serve from the repository root, do not point it at this source tree. Use a separate deploy branch, generated artifact, or provider setting that publishes the contents of `dist/` as the site root.

---

## Literal Translation Pipeline

Extract and inject literal translations from William Davidson Edition:

```bash
npm run fetch:literal:yoma
npm run build:literal:yoma
npm run validate:literal:yoma
npm run status:literal:yoma
```

For faster literal translation fetches, split daf ranges across agents:

```bash
cd modules/yoma
python3 scripts/fetch_literal_en.py --range 2a 30b --skip-existing
python3 scripts/fetch_literal_en.py --range 31a 60b --skip-existing
```

---

## Common Tasks

### Add a Single Sugya

The Yoma corpus is frozen. Only modify Yoma learning assets with explicit approval. If approved, edit `modules/yoma/assets/learning/yoma/<daf>.learning.json`, rebuild, validate, sync version, and commit.

### Deploy to Production

Push to `main`. GitHub Actions will build, test, verify deploy HTML, and deploy `dist/` to GitHub Pages if Actions are enabled for the repository.

### Check Current Status

```bash
cat VERSION
grep DATA_VERSION modules/yoma/learning_data.js
npm test
npm run test:browser
```

---

## Documentation

- **CLAUDE.md** - Complete maintainer guide, universal rules, module system
- **SOURCES.md** - Source attribution and technology stack
- **docs/vilna-breaks.md** - Vilna edition line reference
- **modules/yoma/MODULE.md** - Yoma-specific freeze status and validators

---

## Source Attribution

### Talmud Text

- **Hebrew:** Vilna edition, Romm, 1880-1886, via Sefaria
- **English:** William Davidson Talmud, Koren, via Sefaria
- **Vilna Layout:** talmud.dev

All `he:` and `en:` fields are copied verbatim from Sefaria's API. No modifications.

### Technologies

- **Development shell:** React and ReactDOM development UMD plus Babel standalone from CDN
- **Production build:** esbuild bundles npm `react`, npm `react-dom`, `tweaks-panel.jsx`, and `app.jsx` into `dist/assets/app-<version>.js`
- **Local server:** Python HTTP server from the standard library
- **Browser tests:** Playwright Chromium

See `SOURCES.md` for full attribution.

---

## Troubleshooting

### Pre-commit hook not running?

```bash
git config core.hooksPath githooks
ls -la githooks/pre-commit
```

### Version mismatch?

```bash
cat VERSION
python3 scripts/sync_version.py
```

### Smoke tests failing?

```bash
npm test
```

### Browser smoke test failing locally?

```bash
npx playwright install --with-deps chromium
npm run test:browser
```

### Validation failing?

```bash
cd modules/yoma
python3 scripts/validate_sefaria.py
```

---

## License and Attribution

The Babylonian Talmud, Vilna edition, and Rashi commentary are public domain. The William Davidson English translation is by Koren Publishers and is used via Sefaria's non-commercial educational API for educational use.

See `SOURCES.md` for complete attribution.

---

## Version History

- See git log for detailed change history
