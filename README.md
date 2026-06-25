# MySugya - Universal Talmud Study Companion

A React-based web application for studying the Talmud with rich enrichment, literal translations, and Vilna edition reference markers.

**Current Version:** 12.27  
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
npm run build
npm run check:deploy-html
```

Production output is written to `dist/`. Deploy `dist/` as the web root. Do not deploy the repository root as the production site, because root `index.html` is a development shell that loads Babel and React development UMD scripts.

---

## Project Structure

```
MySugya/
├── index.html              Development app shell
├── app.jsx                 React app, multi-module support
├── manifest.js             Module registry
├── package.json            Scripts and dependencies
├── package-lock.json       Locked npm dependency graph
├── VERSION                 Version file, auto-synced
├── styles.css              Universal styles
├── tweaks-panel.jsx        Settings UI, generic
├── daf.html                Legacy redirect shim
├── favicon.svg             App icon
│
├── dist/                   Production build output, generated and ignored
│
├── scripts/
│   ├── build.mjs                 Production esbuild pipeline
│   ├── build-entry.jsx           Build entry ordering
│   ├── check-deploy-html.mjs     Deploy HTML safety check
│   ├── sync_version.py           Pre-commit version sync
│   └── build/react-shim.js       React injection for esbuild
│
├── modules/
│   └── yoma/                     Yoma module, 173 daf, frozen corpus
│       ├── learning_data.js      Runtime data, generated, canonical
│       ├── source_store.js       Retired transitional source store
│       ├── assets/               Frozen enrichment and layout data
│       └── scripts/              Build and validation tools
│
├── tests/
│   ├── smoke/render_check.py       Production build smoke test
│   └── browser/yoma-smoke.spec.js  Playwright browser smoke test
│
├── githooks/
│   └── pre-commit               Auto-runs version sync and smoke tests
│
├── shared/
│   └── schema_map.js            Data schema contract
│
└── docs/
    └── vilna-breaks.md          Vilna edition reference
```

---

## Modules

### Yoma (יוֹמאָ)
- **Corpus Status:** Frozen baseline, do not modify learning content without explicit approval
- **Current App/Data Version:** 12.27
- **Daf Range:** 2a-88a (173 daf)
- **Sugyot:** 492
- **Chapters:** 8
- **Access:** `?module=yoma` (default)

**Do Not Modify by hand:**
- `learning_data.js` - generated runtime data
- `source_store.js` - retired transitional source store
- `assets/` - frozen enrichment and layout data

### Adding a New Masechta

See **Part B** of [CLAUDE.md](CLAUDE.md) for the complete 14-step pipeline.

---

## Development Workflow

### Universal Rules
1. Commit to `main` unless the active repository policy changes.
2. Version on every commit that changes runtime/data behavior - edit `DATA_VERSION` in the active module's `learning_data.js`.
3. Pre-commit hook auto-syncs version to `VERSION`, `package.json`, `index.html`, and `manifest.js`.
4. Run smoke tests before pushing.
5. No em/en dashes in project-authored output and commits - use plain hyphen (`-`).

### Git Setup

```bash
# On fresh clone, activate hooks
git config core.hooksPath githooks

# Verify configuration
git config core.hooksPath
# Output: githooks
```

### Bumping Version

The version is centralized in one place:

```javascript
// modules/yoma/learning_data.js
const DATA_VERSION = "12.27";  // Change here when bumping
```

The pre-commit hook automatically syncs to:
- `VERSION`
- `package.json`
- `index.html` cache busters
- `manifest.js`

---

## Validation and Testing

### Production Smoke Tests

```bash
npm test
```

This builds `dist/`, serves it locally, verifies the versioned production bundle, checks that built HTML does not contain development-only Babel or React loaders, checks the legacy redirect, and checks responsive CSS guardrails.

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

Complete validation suite:

```bash
# Sefaria text validation
npm run validate:yoma

# English alignment to Hebrew
npm run validate:en:yoma

# Vilna daftext sources
npm run validate:daftext:yoma

# Rashi layer integrity
npm run validate:rashi:yoma

# Vilna sequence, no inversions
npm run audit:order:yoma

# Literal translation coverage
npm run validate:literal:yoma
```

Or run from module directory:

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

## Literal Translation Pipeline (Yoma)

Extract and inject literal translations from William Davidson Edition:

```bash
# Fetch literal text from Sefaria, all daf
npm run fetch:literal:yoma

# Inject into learning_data.js
npm run build:literal:yoma

# Validate coverage, default threshold from validator
npm run validate:literal:yoma

# Show progress without exiting non-zero
npm run status:literal:yoma
```

### Parallel Fetching

For faster literal translation fetches, split daf ranges across agents:

```bash
cd modules/yoma
python3 scripts/fetch_literal_en.py --range 2a 30b --skip-existing
python3 scripts/fetch_literal_en.py --range 31a 60b --skip-existing
# ... etc
```

See [CLAUDE.md](CLAUDE.md) for full parallel agent instructions.

---

## Deployment

The live site must serve generated `dist/`, not the source repository root. The root `index.html` is kept as a development shell and intentionally references Babel and React development scripts; `npm run build` rewrites the production HTML in `dist/index.html` to use the bundled app asset.

### GitHub Pages

This repository includes a GitHub Actions workflow at `.github/workflows/deploy-pages.yml` that runs on pull requests, pushes to `main`, and manual dispatch. The workflow:

1. Runs `npm ci`.
2. Installs Playwright Chromium.
3. Runs `npm run build`.
4. Runs `npm run check:deploy-html`.
5. Runs `npm test`.
6. Runs `npm run test:browser`.
7. On pushes to `main`, uploads and deploys only `dist/` to GitHub Pages.

### Manual Hosting

For any other static host, build locally or in CI and configure the host's publish directory to `dist/`:

```bash
npm ci
npm run build
npm run check:deploy-html
```

If a hosting provider can only serve from the repository root, do not point it at this source tree. Use a separate deploy branch, generated artifact, or provider setting that publishes the contents of `dist/` as the site root.

---

## Source Attribution

### Talmud Text
- **Hebrew:** Vilna edition (Romm, 1880-1886) via Sefaria
- **English:** William Davidson Talmud (Koren) via Sefaria
- **Vilna Layout:** talmud.dev

All `he:` and `en:` fields are copied verbatim from Sefaria's API. No modifications.

### Technologies
- **Development shell:** React and ReactDOM development UMD plus Babel standalone from CDN
- **Production build:** esbuild bundles npm `react`, npm `react-dom`, `tweaks-panel.jsx`, and `app.jsx` into `dist/assets/app-<version>.js`
- **Local server:** Python HTTP server from the standard library
- **Browser tests:** Playwright Chromium

See [SOURCES.md](SOURCES.md) for full attribution.

---

## Common Tasks

### Add a Single Sugya

The Yoma corpus is frozen. Only modify Yoma learning assets with explicit approval. If approved, edit `modules/yoma/assets/learning/yoma/<daf>.learning.json`, rebuild, validate, and bump version:

```bash
npm run build:literal:yoma
npm run validate:yoma
git add -A && git commit -m "Update 2a sugya"
```

### Deploy to Production

Push to `main`. GitHub Actions will build, test, verify deploy HTML, and deploy `dist/` to GitHub Pages.

```bash
git push origin main
```

### Check Current Status

```bash
cat VERSION
grep DATA_VERSION modules/yoma/learning_data.js
npm test
npm run test:browser
```

### Run a Specific Daf Check

Single Sefaria validation:

```bash
curl -s "https://www.sefaria.org/api/texts/Yoma.2a?context=0" | python3 -c "import sys, json; data = json.load(sys.stdin); print(f'he fields: {len(data[\"he\"])}, en fields: {len(data[\"text\"])}')"
```

---

## Documentation

- **[CLAUDE.md](CLAUDE.md)** - Complete maintainer guide, universal rules, module system
- **[SOURCES.md](SOURCES.md)** - Source attribution and technology stack
- **[docs/vilna-breaks.md](docs/vilna-breaks.md)** - Vilna edition line reference
- **[modules/yoma/MODULE.md](modules/yoma/MODULE.md)** - Yoma-specific freeze status and validators

---

## Contributing

1. Ensure `git config core.hooksPath githooks` is set.
2. Make changes.
3. Run relevant tests and validators.
4. Bump version in `modules/yoma/learning_data.js` when runtime or data behavior changes.
5. Commit with a clear message.
6. Push to `main`.

The pre-commit hook will auto-sync the version and run smoke tests for relevant UI/data changes.

---

## Troubleshooting

### Pre-commit hook not running?

```bash
git config core.hooksPath githooks
ls -la githooks/pre-commit  # Should be executable
```

### Version mismatch?

The pre-commit hook auto-syncs. If manual changes are needed:

```bash
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

The Babylonian Talmud (public domain), Vilna edition (public domain), Rashi commentary (public domain), and William Davidson English translation (© Koren Publishers, used via Sefaria's non-commercial educational API) are reproduced here for educational use.

See [SOURCES.md](SOURCES.md) for complete attribution.

---

## Version History

- **12.27** - Current
- See git log for detailed change history

---

**Questions?** See [CLAUDE.md](CLAUDE.md) or check the repository issue tracker.
