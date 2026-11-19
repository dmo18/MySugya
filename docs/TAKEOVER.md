# Takeover audit

Audit date: 2026-11-19. Version: 15.600. Commit: `4c983a2`.
Nothing in the product was changed during this audit.

## What this project is

MySugya is a Talmud study web app. It shows one page (daf) at a
time with Hebrew, English, Rashi commentary, and learning aids.
Yoma is the only tractate so far: 173 daf, 492 sugyot (topics).

## Main parts

| Part | What it does |
|---|---|
| `app.jsx`, `styles.css` | The app screen and its look |
| `manifest.js` | List of tractates the app can load |
| `modules/yoma/` | All Yoma text and learning content (protected) |
| `scripts/` | Build, checks, and certification tools |
| `tests/` | Automatic checks, including real browser tests |
| `.github/workflows/` | Automatic test and publish on GitHub |
| `ops/systemd-user/` | Timer files for the "Rabbi" automation host |

## How to run it

1. `npm ci` (install)
2. `npm test` (build plus all checks)
3. `npm run test:browser` (browser checks)
4. `npm run serve` (local preview on port 4173)

Maintainer rules live in `CLAUDE.md`. Current open work lives in
`docs/reports/open-items.md`.

## Baseline measured on 2026-11-19

| Check | Result |
|---|---|
| Install (`npm ci`) | Pass |
| `npm test` | Pass (exit 0) |
| Built page safety check | Pass |
| Browser tests | 21 passed, 1 skipped |
| Dependency audit (`npm audit`) | 0 vulnerabilities |
| Secret scan of tracked files | 0 hits |
| Latest GitHub runs on `main` | Pages, Cloudways, Rashi shards: success |
| Semantic certification | 95 of 492 certified, 397 not yet |

Browser test note: this cloud machine ships a newer browser build
than the pinned Playwright expects. A link outside the repo
(`/opt/pw-browsers/chromium_headless_shell-1228`) fixed it for this
session only. GitHub's own runs are not affected.

## Known issues and risks

1. Learning content is only 19% certified (95 of 492), yet all of it
   is live on the public site. Next in the queue: daf 18b.
2. Every merge into `main` publishes automatically, twice: GitHub
   Pages (after tests) and a `cloudways` branch (no tests, force
   push, write permission). `CLAUDE.md` says Cloudways is out of
   scope, but the workflow still runs on every merge.
3. PR #663 (Yoma 18b certification) has been open since 2026-11-11
   and `main` has moved on since then.
4. No linter (automatic code style and mistake checker) is set up.
5. No LICENSE file, so reuse terms for the code are undefined.
6. `CLAUDE.md` says to commit to `main`. This session works on a
   branch and merges by pull request instead, which is safer.

## Things the project brought with it (not used without approval)

| Item | What it is |
|---|---|
| `githooks/pre-commit` | Runs version sync and smoke tests before each commit. Not active on a fresh copy. |
| `ops/systemd-user/*` | Timer for the Rabbi quota refresh on another machine. Not installed here. |
| Rabbi / OpenClaw scripts | Automated certification campaign. Documented as disabled. |

No bundled skills, plugins, MCP servers, or `.claude/` settings were
found in the repository.

## Security baseline items that apply

- Secrets: none in code or git. Applies.
- Dependencies: 2 runtime (React), 2 dev, exact or locked. Applies.
- Output encoding and safe links in the app. Applies (guards are
  already tested by `npm test`).
- Login, payments, personal data, uploads: none exist. Not applicable.
