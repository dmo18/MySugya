import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';

/**
 * rashi-association.spec.js - browser verification of the linked Rashi
 * renderer, which is the PRODUCTION DEFAULT as of the VERSION 15.338
 * cutover. The per-daf association tests therefore navigate with no
 * rashiAssoc parameter at all, so they verify the renderer users actually
 * get. ?rashiAssoc=legacy remains a temporary rollback override onto the
 * preserved legacy vilnaLine renderer, and ?rashiAssoc=linked is still
 * accepted but no longer required; both are covered in the "Rashi renderer
 * selection" describe block at the bottom of this file.
 *
 * The plan this spec asserts against always comes from
 * modules/yoma/scripts/audit_rashi_association.py --json - never hardcoded
 * expected Hebrew/English text or target ids. Two ways to supply it:
 *
 *   - Plain `npx playwright test` / `npm run test:browser` / `npm test`:
 *     no env var set, so this file runs the auditor itself in --target mode
 *     (YOMA_ASSOC_TARGET_DAF, default "2a") - single daf, fast, so content
 *     PRs get real coverage with zero setup.
 *   - `npm run test:rashi-association:yoma` (range/corpus/exhaustive-corpus):
 *     scripts/run-rashi-association.mjs pre-runs the auditor and passes the
 *     plan via YOMA_ASSOC_PLAN_PATH; this file just reads that file.
 *
 * Exhaustive-corpus scope is intentionally never wired into plain
 * `test:browser` (thousands of navigations); it stays reserved for a
 * dedicated closure run or a sharded workflow.
 */

function collectPageErrors(page) {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => {
    if (message.type() === 'error') errors.push(message.text());
  });
  return errors;
}

// playwright.config.js's testDir/webServer run with cwd at the repo root.
const AUDIT_SCRIPT = resolve(process.cwd(), 'modules/yoma/scripts/audit_rashi_association.py');

function loadPlan() {
  if (process.env.YOMA_ASSOC_PLAN_PATH) {
    return JSON.parse(readFileSync(process.env.YOMA_ASSOC_PLAN_PATH, 'utf8'));
  }
  const targetDaf = process.env.YOMA_ASSOC_TARGET_DAF || '2a';
  try {
    const stdout = execFileSync(
      'python3',
      [AUDIT_SCRIPT, '--target', targetDaf, '--json'],
      { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 }
    );
    return JSON.parse(stdout);
  } catch (e) {
    // The auditor exits nonzero when it finds referential errors, but still
    // emits the full JSON plan on stdout - read it from the thrown error
    // rather than treating a nonzero exit as "no plan available."
    if (e.stdout) return JSON.parse(e.stdout);
    throw e;
  }
}

const plan = loadPlan();

if (!plan.success) {
  throw new Error(
    `Audit plan reports ${plan.error_count} referential-integrity error(s) in scope; ` +
    'fix the underlying data (or narrow scope) before running the browser assertion. ' +
    `First error: ${plan.errors[0]}`
  );
}

for (const daf of plan.daf_list) {
  test.describe(`Rashi linked association - daf ${daf}`, () => {
    test('every declared association renders under exactly its declared targets, with exact text', async ({ page }) => {
      const pageErrors = collectPageErrors(page);
      // Deliberately NO rashiAssoc parameter: since the VERSION 15.338
      // cutover, linked is the production default, so this asserts the
      // real default rendering path across the whole corpus (single-link,
      // multi-link, many-to-one, Mishnah, and suffixed-id cases alike),
      // not a parameter-gated preview of it.
      await page.goto(`/index.html?module=yoma&daf=${daf}`);

      // The linked default must come from the code, never from stored state.
      await expect(page).not.toHaveURL(/rashiAssoc/);
      const stored = await page.evaluate(() => localStorage.getItem('mysugya:tweaks'));
      expect(stored ?? '').not.toContain('rashiAssoc');

      const dafFindings = plan.findings.filter(f => f.daf === daf);
      const findingById = new Map(dafFindings.map(f => [f.rashi_id, f]));

      // gemaraLineId -> Set(rashiId) for every non-broken, non-boundary association.
      const expectedByLine = new Map();
      for (const f of dafFindings) {
        if (f.entry_category === 'boundary') continue;
        for (const a of f.associations) {
          if (a.is_broken) continue;
          if (!expectedByLine.has(a.target)) expectedByLine.set(a.target, new Set());
          expectedByLine.get(a.target).add(f.rashi_id);
        }
      }

      const badgeLineIds = await page.locator('.line[data-has-rashi="1"]').evaluateAll(
        els => els.map(el => el.getAttribute('data-gemara-line-id'))
      );

      // Every line the plan expects to carry a badge must actually have one -
      // catches an omitted multi-link target (or any dropped association).
      for (const expectedLineId of expectedByLine.keys()) {
        expect(badgeLineIds).toContain(expectedLineId);
      }

      for (const lineId of badgeLineIds) {
        const lineLoc = page.locator(`.line[data-gemara-line-id="${lineId}"]`);
        await lineLoc.locator('.rashi-badge').click();

        const entryLoc = page.locator(`.line[data-gemara-line-id="${lineId}"] + .rashi-inline [data-rashi-id]`);
        const expectedIds = expectedByLine.get(lineId) ?? new Set();

        // Exact count: catches duplicates under one target and unrelated
        // extra entries (a badge with more/fewer entries than declared).
        await expect(entryLoc).toHaveCount(expectedIds.size);

        const actualIds = await entryLoc.evaluateAll(els => els.map(el => el.getAttribute('data-rashi-id')));
        expect(actualIds.slice().sort()).toEqual([...expectedIds].sort());

        for (const rashiId of actualIds) {
          const entry = page.locator(`.line[data-gemara-line-id="${lineId}"] + .rashi-inline [data-rashi-id="${rashiId}"]`);
          const finding = findingById.get(rashiId);

          // The entry must self-report the line it's currently rendered
          // under, distinct from its full declared target list.
          await expect(entry).toHaveAttribute('data-rashi-linked-line-id', lineId);
          await expect(entry).toHaveAttribute('data-rashi-daf', String(finding.daf));
          await expect(entry).toHaveAttribute('data-rashi-vilna-line', String(finding.rashi_vilna_line));

          // Exact Hebrew text - never a different entry's text (no cross-pairing).
          await expect(entry.locator('.rashi-inline-he')).toHaveText(finding.rashi_he);

          if (finding.rashi_en) {
            await expect(entry.locator('.rashi-inline-en')).toHaveText(finding.rashi_en);
          }

          // The full declared target set for this entry, regardless of
          // which target we're currently looking at.
          const targetsAttr = await entry.getAttribute('data-rashi-targets');
          const renderedTargets = JSON.parse(targetsAttr);
          const declaredTargets = finding.associations.filter(a => !a.is_broken).map(a => a.target);
          expect(renderedTargets.slice().sort()).toEqual(declaredTargets.slice().sort());
        }
      }

      expect(pageErrors).toEqual([]);
    });

    test('boundary (empty-link) entries never render anywhere on the page', async ({ page }) => {
      const dafFindings = plan.findings.filter(f => f.daf === daf && f.entry_category === 'boundary');
      if (dafFindings.length === 0) test.skip(true, 'no boundary entries in scope for this daf');

      // Default (linked) mode, no parameter - authorized boundary entries
      // must render nowhere, including beneath unrelated lines.
      await page.goto(`/index.html?module=yoma&daf=${daf}`);
      const boundaryIds = new Set(dafFindings.map(f => f.rashi_id));

      const badgeLineIds = await page.locator('.line[data-has-rashi="1"]').evaluateAll(
        els => els.map(el => el.getAttribute('data-gemara-line-id'))
      );
      for (const lineId of badgeLineIds) {
        await page.locator(`.line[data-gemara-line-id="${lineId}"] .rashi-badge`).click();
        const renderedIds = await page.locator(
          `.line[data-gemara-line-id="${lineId}"] + .rashi-inline [data-rashi-id]`
        ).evaluateAll(els => els.map(el => el.getAttribute('data-rashi-id')));
        for (const id of renderedIds) {
          expect(boundaryIds.has(id)).toBe(false);
        }
      }
    });
  });
}

/* Renderer selection after the VERSION 15.338 cutover.
 *
 * The discriminator between the two renderers is structural, not cosmetic:
 * the linked path emits one [data-rashi-id] element per rendered comment
 * inside .rashi-inline, while the legacy path emits a bare .rashi-inline
 * with no such attribute. That distinction cannot be satisfied by accident
 * by the other path, so these tests genuinely prove which renderer ran. */
test.describe('Rashi renderer selection', () => {
  const daf = plan.daf_list[0];

  async function openFirstRashi(page, url) {
    await page.goto(url);
    const first = page.locator('.line[data-has-rashi="1"]').first();
    await first.locator('.rashi-badge').click();
    return first;
  }

  test('no rashiAssoc parameter uses the linked renderer (production default)', async ({ page }) => {
    const pageErrors = collectPageErrors(page);
    const line = await openFirstRashi(page, `/index.html?module=yoma&daf=${daf}`);
    const lineId = await line.getAttribute('data-gemara-line-id');
    await expect(
      page.locator(`.line[data-gemara-line-id="${lineId}"] + .rashi-inline [data-rashi-id]`).first()
    ).toBeVisible();
    expect(pageErrors).toEqual([]);
  });

  test('?rashiAssoc=linked still selects the linked renderer (accepted, not required)', async ({ page }) => {
    const pageErrors = collectPageErrors(page);
    const line = await openFirstRashi(page, `/index.html?module=yoma&daf=${daf}&rashiAssoc=linked`);
    const lineId = await line.getAttribute('data-gemara-line-id');
    await expect(
      page.locator(`.line[data-gemara-line-id="${lineId}"] + .rashi-inline [data-rashi-id]`).first()
    ).toBeVisible();
    expect(pageErrors).toEqual([]);
  });

  test('?rashiAssoc=legacy selects the preserved legacy vilnaLine renderer', async ({ page }) => {
    const pageErrors = collectPageErrors(page);
    await openFirstRashi(page, `/index.html?module=yoma&daf=${daf}&rashiAssoc=legacy`);
    // Legacy renders an open .rashi-inline that carries no [data-rashi-id]
    // child, proving the rollback path is intact and actually selected.
    await expect(page.locator('.rashi-inline').first()).toBeVisible();
    expect(await page.locator('.rashi-inline [data-rashi-id]').count()).toBe(0);
    expect(pageErrors).toEqual([]);
  });

  test('unknown rashiAssoc values fall through to linked, never silently to legacy', async ({ page }) => {
    const pageErrors = collectPageErrors(page);
    const line = await openFirstRashi(page, `/index.html?module=yoma&daf=${daf}&rashiAssoc=bogus-value`);
    const lineId = await line.getAttribute('data-gemara-line-id');
    await expect(
      page.locator(`.line[data-gemara-line-id="${lineId}"] + .rashi-inline [data-rashi-id]`).first()
    ).toBeVisible();
    expect(pageErrors).toEqual([]);
  });

  test('renderer selection is not persisted and does not survive navigation', async ({ page }) => {
    // Visit legacy explicitly, then navigate to a parameter-free URL: the
    // second visit must be linked again, and nothing may be stored.
    await openFirstRashi(page, `/index.html?module=yoma&daf=${daf}&rashiAssoc=legacy`);
    const allStorage = await page.evaluate(() => JSON.stringify({
      local: Object.fromEntries(Object.entries(localStorage)),
      session: Object.fromEntries(Object.entries(sessionStorage)),
    }));
    expect(allStorage).not.toContain('rashiAssoc');

    const line = await openFirstRashi(page, `/index.html?module=yoma&daf=${daf}`);
    const lineId = await line.getAttribute('data-gemara-line-id');
    await expect(
      page.locator(`.line[data-gemara-line-id="${lineId}"] + .rashi-inline [data-rashi-id]`).first()
    ).toBeVisible();
  });
});
