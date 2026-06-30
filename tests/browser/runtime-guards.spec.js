import { test, expect } from '@playwright/test';

function collectPageErrors(page) {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => {
    if (message.type() === 'error') errors.push(message.text());
  });
  return errors;
}

test.describe('Runtime guard tests', () => {
  test('landing page renders and featured preview loads without errors', async ({ page }) => {
    const pageErrors = collectPageErrors(page);
    await page.goto('/index.html');
    await expect(page.locator('.landing-hero')).toBeVisible();
    // Featured preview loads lazily via requestIdleCallback (up to 2.5 s) or setTimeout.
    // .dotd-card replaces .dotd-skeleton once module data is ready.
    await expect(page.locator('.dotd-card')).toBeVisible({ timeout: 8000 });
    expect(pageErrors).toEqual([]);
  });

  test('unknown module parameter falls back to landing without crash', async ({ page }) => {
    const pageErrors = collectPageErrors(page);
    await page.goto('/index.html?module=nonexistent');
    // No matching manifest entry - main mount calls renderLanding() and shows the landing page.
    await expect(page.locator('.landing')).toBeVisible();
    expect(pageErrors).toEqual([]);
  });

  test('invalid daf parameter falls back to first daf without crash', async ({ page }) => {
    const pageErrors = collectPageErrors(page);
    await page.goto('/index.html?module=yoma&daf=invalid9z');
    // initialDafFromUrl returns null for an unrecognized daf id; App falls back to
    // localStorage lastDaf or DAF_INDEX[0]. The daf view should still mount cleanly.
    await expect(page.locator('.daf')).toBeVisible({ timeout: 10000 });
    expect(pageErrors).toEqual([]);
  });

  test('clipboard writeText failure is caught and does not crash the page', async ({ page }) => {
    const pageErrors = collectPageErrors(page);
    await page.addInitScript(() => {
      // Remove Web Share API so the clipboard branch is exercised.
      try {
        Object.defineProperty(navigator, 'share', { value: undefined, configurable: true });
      } catch {}
      // Override clipboard.writeText to reject, verifying the .catch() is in place.
      try {
        Object.defineProperty(navigator, 'clipboard', {
          get: () => ({ writeText: () => Promise.reject(new Error('Clipboard denied')) }),
          configurable: true,
        });
      } catch {}
    });
    await page.goto('/index.html?module=yoma&daf=2a');
    await expect(page.locator('.share-btn').first()).toBeVisible();
    await page.locator('.share-btn').first().click();
    // Allow the rejected promise to settle before asserting no errors.
    await page.waitForTimeout(300);
    expect(pageErrors).toEqual([]);
  });
});
