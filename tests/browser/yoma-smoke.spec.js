import { test, expect } from '@playwright/test';

const DAF_2A = '/index.html?module=yoma&daf=2a';

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
