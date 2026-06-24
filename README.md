# MySugya - Universal Talmud Study Companion

A React-based web application for studying the Talmud with rich enrichment, literal translations, and Vilna edition reference markers.

**Current Version:** 12.4  
**Status:** Production-ready (Yoma module frozen)

---

## Quick Start

### Prerequisites
- Node.js (npm)
- Python 3.6+ (for validation scripts)
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/dmo18/MySugya.git
cd MySugya

# Configure git hooks (one time only)
git config core.hooksPath githooks

# Install dependencies
npm install

# Run smoke tests
npm test
```

### Run Locally

```bash
npm run serve
# Open http://localhost:4173 in your browser
```

### Build for Production

```bash
npm run build
npm run check:deploy-html
```

Production output is written to `dist/`. Deploy `dist/` as the web root; do not deploy the repository root because the root `index.html` is a development shell that loads Babel and React development UMD scripts.

---

## Project Structure

```
MySugya/
├── index.html              Development app shell
├── dist/                   Production build output (generated)
├── app.jsx                 React app (multi-module support)
├── manifest.js             Module registry
├── package.json            Scripts & dependencies
├── VERSION                 Version file (auto-synced)
├── styles.css              Universal styles
├── tweaks-panel.jsx        Settings UI (generic)
│
├── modules/
│   └── yoma/              Yoma module (173 daf, frozen)
│       ├── learning_data.js     Runtime data (generated)
│       ├── source_store.js      Sefaria text (validated)
│       └── scripts/             Build & validation tools
│
├── scripts/
│   └── sync_version.py    Pre-commit version sync
│
├── githooks/
│   └── pre-commit          Auto-runs version sync & tests
│
├── shared/
│   └── schema_map.js       Data schema contract
│
├── tests/
│   └── smoke/              Smoke test suite
│
└── docs/
    └── vilna-breaks.md     Vilna edition reference
```

---

## Modules

### Yoma (יוֹמאָ)
- **Status:** Frozen at v10.75
- **Daf Range:** 2a-88a (173 daf)
- **Sugyot:** 492
- **Chapters:** 8
- **Access:** `?module=yoma` (default)

**Do Not Modify:**
- `learning_data.js` - Generated from source
- `source_store.js` - Sefaria-validated text
- `assets/` - Frozen enrichment & layout data

### Adding a New Masechta

See **Part B** of [CLAUDE.md](CLAUDE.md) for the complete 14-step pipeline.

---

## Development Workflow

### Universal Rules
1. **No branches** - Commit directly to `main`
2. **Version on every commit** - Edit `DATA_VERSION` in active module's `learning_data.js`
3. **Pre-commit hook** - Auto-syncs version to VERSION, package.json, index.html, manifest.js
4. **Run smoke tests** - `npm test` before pushing
5. **No em/en dashes** - Use plain hyphen (`-`) in output & commits

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
const DATA_VERSION = "12.4";  // Change here
```

The pre-commit hook automatically syncs to:
- `VERSION`
- `package.json`
- `index.html` cache busters
- `manifest.js`

---

## Validation & Testing

### Smoke Tests
Verify shell loads, routes work, responsive CSS present:

```bash
npm test
```

### Yoma Module Validation

Complete validation suite:

```bash
# Sefaria text validation (2240 he: fields)
npm run validate:yoma

# English alignment to Hebrew
npm run validate:en:yoma

# Vilna daftext sources
npm run validate:daftext:yoma

# Rashi layer integrity
npm run validate:rashi:yoma

# Vilna sequence (no inversions)
npm run audit:order:yoma
```

Or run from module directory:

```bash
cd modules/yoma
python3 scripts/validate_sefaria.py
python3 scripts/validate_en.py
python3 scripts/validate_daftext.py
python3 scripts/validate_rashi.py
python3 scripts/order_audit.py
```

---

## Literal Translation Pipeline (Yoma)

Extract & inject literal translations from William Davidson Edition:

```bash
# Fetch literal text from Sefaria (all daf)
npm run fetch:literal:yoma

# Inject into learning_data.js
npm run build:literal:yoma

# Validate coverage (>= 95%)
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

The live site must serve the generated `dist/` directory, not the source repository root. The root `index.html` is kept as a development shell and intentionally references Babel and React development scripts; `npm run build` rewrites the production HTML in `dist/index.html` to use the bundled asset instead.

### GitHub Pages

This repository includes a GitHub Actions workflow at `.github/workflows/deploy-pages.yml` that deploys to GitHub Pages on every push to `main` and on manual `workflow_dispatch` runs. The workflow:

1. Runs `npm ci`.
2. Runs `npm run build`.
3. Runs `npm run check:deploy-html` to fail deployment if `dist/index.html` contains `text/babel`, `babel.min.js`, or `react.development.js`.
4. Uploads and publishes only `dist/` to GitHub Pages.

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
- **Frontend:** React (CDN via Babel)
- **Backend:** Python HTTP server (stdlib)
- **Build Tools:** Python scripts

See [SOURCES.md](SOURCES.md) for full attribution.

---

## Common Tasks

### Add a Single Sugya
Edit `modules/yoma/assets/learning/yoma/<daf>.learning.json`, rebuild, validate:

```bash
npm run build:literal:yoma
npm run validate:yoma
git add -A && git commit -m "Update 2a sugya"
```

### Deploy to Production
Push to main - CI/CD pipelines (when configured) will handle deployment.

```bash
git push origin main
```

### Check Current Status
View what's frozen, what's in progress, version:

```bash
cat VERSION
grep DATA_VERSION modules/yoma/learning_data.js
cat CLAUDE.md  # See "Do not do these things"
```

### Run a Specific Daf Check
Single Sefaria validation:

```bash
curl -s "https://www.sefaria.org/api/texts/Yoma.2a?context=0" | python3 -c "import sys, json; data = json.load(sys.stdin); print(f'he fields: {len(data[\"he\"])}, en fields: {len(data[\"text\"])}')"
```

---

## Documentation

- **[CLAUDE.md](CLAUDE.md)** - Complete maintainer guide, universal rules, module system
- **[SOURCES.md](SOURCES.md)** - Source attribution & technology stack
- **[docs/vilna-breaks.md](docs/vilna-breaks.md)** - Vilna edition line reference
- **[modules/yoma/MODULE.md](modules/yoma/MODULE.md)** - Yoma-specific freeze status & validators

---

## Contributing

1. Ensure `git config core.hooksPath githooks` is set
2. Make changes to the active module
3. Run validation tests: `npm run validate:*`
4. Bump version in `modules/yoma/learning_data.js`
5. Commit: `git commit -m "Clear, descriptive message"`
6. Push: `git push origin main`

The pre-commit hook will auto-sync the version and run smoke tests.

---

## Troubleshooting

### Pre-commit hook not running?
```bash
git config core.hooksPath githooks
ls -la githooks/pre-commit  # Should be executable (rwxr-xr-x)
```

### Version mismatch?
The pre-commit hook auto-syncs. If manual changes needed:
```bash
python3 scripts/sync_version.py
```

### Smoke tests failing?
```bash
npm test  # Run to see detailed output
```

### Validation failing?
```bash
cd modules/yoma
python3 scripts/validate_sefaria.py  # Detailed error messages
```

---

## License & Attribution

The Babylonian Talmud (public domain), Vilna edition (public domain), Rashi commentary (public domain), and William Davidson English translation (© Koren Publishers, used via Sefaria's non-commercial educational API) are reproduced here for educational use.

See [SOURCES.md](SOURCES.md) for complete attribution.

---

## Version History

- **12.4** - Current
- See git log for detailed change history

---

**Questions?** See [CLAUDE.md](CLAUDE.md) or check the repository issue tracker.
