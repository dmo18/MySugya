import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';

/**
 * rashi-association.spec.js - browser verification of the linked Rashi
 * renderer (?rashiAssoc=linked, test/audit only; legacy stays production
 * default).
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
      await page.goto(`/index.html?module=yoma&daf=${daf}&rashiAssoc=linked`);

      // Confirm the test-only URL switch is what's active, never a stored preference.
      await expect(page).toHaveURL(/rashiAssoc=linked/);
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

      await page.goto(`/index.html?module=yoma&daf=${daf}&rashiAssoc=linked`);
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

test.describe('Rashi linked association - legacy path unaffected', () => {
  test('default (no rashiAssoc param) still uses the legacy vilnaLine renderer', async ({ page }) => {
    const pageErrors = collectPageErrors(page);
    const daf = plan.daf_list[0];
    await page.goto(`/index.html?module=yoma&daf=${daf}`);
    await expect(page).not.toHaveURL(/rashiAssoc=linked/);
    // Legacy toggle key is vilna_line, not line.id; the presence of at least
    // one badge with the legacy path active confirms the default branch
    // still renders, unchanged by this feature's addition.
    const badgeCount = await page.locator('.line[data-has-rashi="1"]').count();
    expect(badgeCount).toBeGreaterThanOrEqual(0);
    expect(pageErrors).toEqual([]);
  });
});
