import { test, expect } from '@playwright/test';

const DAF_2A = '/index.html?module=yoma&daf=2a';
const DAF_19B = '/index.html?module=yoma&daf=19b';
const DAF_23A = '/index.html?module=yoma&daf=23a';
const DAF_87B = '/index.html?module=yoma&daf=87b';

function collectPageErrors(page) {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => {
    if (message.type() === 'error') errors.push(message.text());
  });
  return errors;
}

test.describe('Yoma daf smoke test', () => {
  test('renders daf 2a content, Rashi, previous navigation, mobile layout, and dark mode', async ({ page }) => {
    const pageErrors = collectPageErrors(page);

    await page.goto(DAF_2A);
    await expect(page.locator('.sugya')).toHaveCount(6);
    await expect(page.locator('.line')).toHaveCount(11);

    const firstRashiBadge = page.locator('.rashi-badge').first();
    await expect(firstRashiBadge).toBeVisible();
    await firstRashiBadge.click();
    await expect(page.locator('.rashi-inline').first()).toBeVisible();

    await page.getByRole('button', { name: /previous daf/i }).click();
    await expect(page.locator('.vilna-page')).toBeVisible();
    expect(pageErrors).toEqual([]);

    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(DAF_2A);
    await expect(page.locator('.sugya').first()).toBeVisible();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
    expect(overflow).toBe(false);

    // Design is locked to Mist; a stale dark-mode localStorage entry must not override it.
    await page.addInitScript(() => {
      localStorage.setItem('mysugya:tweaks', JSON.stringify({ mode: 'dark' }));
    });
    await page.goto(DAF_2A);
    const dataMode = await page.evaluate(() => document.documentElement.getAttribute('data-mode'));
    expect(dataMode).toBe('mist');
    const dataAccent = await page.evaluate(() => document.documentElement.getAttribute('data-accent'));
    expect(dataAccent).toBe('gold');
  });
});

test.describe('Yoma legacy-schema fallback (daf 87b)', () => {
  test('renders non-blank sugya titles and fallback learning content', async ({ page }) => {
    const pageErrors = collectPageErrors(page);

    await page.goto(DAF_87B);
    await expect(page.locator('.sugya')).toHaveCount(3);

    const titles = await page.locator('.sugya-title').allTextContents();
    expect(titles).toHaveLength(3);
    for (const title of titles) {
      expect(title.trim().length).toBeGreaterThan(0);
    }

    // 87b predates the canonical display/learning schema, so titles must come
    // from the fallback derivation, not display.title.
    await expect(page.locator('.sugya-title-fallback')).toHaveCount(3);

    // Each sugya renders its understanding panel twice (desktop block plus the
    // mobile <details> fold); scope to the desktop block to count per-sugya.
    const fallbackPanels = page.locator('.desktop-understanding .learn-panel-fallback');
    await expect(fallbackPanels).toHaveCount(3);
    await expect(fallbackPanels.first().locator('.learn-row')).not.toHaveCount(0);

    expect(pageErrors).toEqual([]);
  });
});

test.describe('Yoma backfilled schema (daf 19b, daf 23a)', () => {
  test('daf 19b renders canonical sugya titles and learning content with no fallback markup', async ({ page }) => {
    const pageErrors = collectPageErrors(page);

    await page.goto(DAF_19B);
    await expect(page.locator('.sugya')).toHaveCount(3);

    const titles = await page.locator('.sugya-title').allTextContents();
    expect(titles).toHaveLength(3);
    for (const title of titles) {
      expect(title.trim().length).toBeGreaterThan(0);
    }

    // 19b was backfilled with the canonical display/learning schema, so it must
    // no longer fall through to the legacy fallback rendering path.
    await expect(page.locator('.sugya-title-fallback')).toHaveCount(0);
    await expect(page.locator('.desktop-understanding .learn-panel-fallback')).toHaveCount(0);

    expect(pageErrors).toEqual([]);
  });

  test('daf 23a renders canonical sugya titles and learning content with no fallback markup', async ({ page }) => {
    const pageErrors = collectPageErrors(page);

    await page.goto(DAF_23A);
    await expect(page.locator('.sugya')).toHaveCount(3);

    const titles = await page.locator('.sugya-title').allTextContents();
    expect(titles).toHaveLength(3);
    for (const title of titles) {
      expect(title.trim().length).toBeGreaterThan(0);
    }

    // 23a was backfilled with the canonical display/learning schema, so it must
    // no longer fall through to the legacy fallback rendering path.
    await expect(page.locator('.sugya-title-fallback')).toHaveCount(0);
    await expect(page.locator('.desktop-understanding .learn-panel-fallback')).toHaveCount(0);

    expect(pageErrors).toEqual([]);
  });
});

test.describe('Share button title resolution', () => {
  test('daf 19b shares the rendered sugya title, not an undefined sugya.title', async ({ page }) => {
    const pageErrors = collectPageErrors(page);

    await page.addInitScript(() => {
      window.__shareCalls = [];
      navigator.share = (data) => {
        window.__shareCalls.push(data);
        return Promise.resolve();
      };
    });

    await page.goto(DAF_19B);
    const firstTitle = await page.locator('.sugya-title').first().textContent();
    await page.locator('.share-btn').first().click();

    const shareCalls = await page.evaluate(() => window.__shareCalls);
    expect(shareCalls).toHaveLength(1);
    expect(shareCalls[0].title).toBe(firstTitle.trim());
    expect(shareCalls[0].title).not.toBe('');
    expect(shareCalls[0].title).not.toBe('undefined');

    expect(pageErrors).toEqual([]);
  });

  test('falls back to clipboard copy when native share is unavailable', async ({ page, context }) => {
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);
    const pageErrors = collectPageErrors(page);

    await page.addInitScript(() => {
      delete navigator.share;
    });

    await page.goto(DAF_19B);
    await page.locator('.share-btn').first().click();
    await expect(page.locator('.share-btn.copied').first()).toBeVisible();

    expect(pageErrors).toEqual([]);
  });
});
