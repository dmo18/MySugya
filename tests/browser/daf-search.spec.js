import { test, expect } from '@playwright/test';

// Deterministic coverage for the existing "Jump to daf" search modal
// (app.jsx JumpModal, opened with Cmd/Ctrl+K). This is the real existing
// search feature in the product boundary - a client-side filter over
// daf number / topic / content-type, not full-text search - so this spec
// asserts against its actual markup (.modal-search, .modal-row, the
// "No amudim match" empty state) rather than an imagined search feature.
const MODULE_KEY = 'yoma';
const DAF_2A = `/index.html?module=${MODULE_KEY}&daf=2a`;

function collectPageErrors(page) {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => {
    if (message.type() === 'error') errors.push(message.text());
  });
  return errors;
}

async function openJumpModal(page) {
  const modifier = process.platform === 'darwin' ? 'Meta' : 'Control';
  await page.keyboard.press(`${modifier}+k`);
  await expect(page.locator('.modal-search input')).toBeVisible();
}

test.describe('Jump to daf search modal', () => {
  test('daf-number query returns the matching row', async ({ page }) => {
    const pageErrors = collectPageErrors(page);
    await page.goto(DAF_2A);
    await openJumpModal(page);

    await page.locator('.modal-search input').fill('19b');
    const rows = page.locator('.modal-row');
    await expect(rows).toHaveCount(1);
    await expect(rows.first()).toContainText('19b');

    expect(pageErrors).toEqual([]);
  });

  test('topic query returns at least one matching row', async ({ page }) => {
    const pageErrors = collectPageErrors(page);
    await page.goto(DAF_2A);
    await openJumpModal(page);

    const firstTopic = await page.evaluate(() => {
      const el = document.querySelector('.modal-row .t');
      return el ? el.textContent : null;
    });
    expect(firstTopic).toBeTruthy();

    await page.locator('.modal-search input').fill(firstTopic.slice(0, 6));
    await expect(page.locator('.modal-row').first()).toBeVisible();

    expect(pageErrors).toEqual([]);
  });

  test("content-type query 'rich' returns only RICH-badged rows", async ({ page }) => {
    const pageErrors = collectPageErrors(page);
    await page.goto(DAF_2A);
    await openJumpModal(page);

    await page.locator('.modal-search input').fill('rich');
    const rowCount = await page.locator('.modal-row').count();
    if (rowCount > 0) {
      const badgeCount = await page.locator('.modal-row .badge.rich').count();
      expect(badgeCount).toBe(rowCount);
    }

    expect(pageErrors).toEqual([]);
  });

  test('no-match query shows the empty state, not stale rows', async ({ page }) => {
    const pageErrors = collectPageErrors(page);
    await page.goto(DAF_2A);
    await openJumpModal(page);

    await page.locator('.modal-search input').fill('zzz-no-such-daf-or-topic-zzz');
    await expect(page.locator('.modal-row')).toHaveCount(0);
    await expect(page.getByText('No amudim match — try a different search.')).toBeVisible();

    expect(pageErrors).toEqual([]);
  });

  test('selecting a result navigates to that daf and closes the modal', async ({ page }) => {
    const pageErrors = collectPageErrors(page);
    await page.goto(DAF_2A);
    await openJumpModal(page);

    await page.locator('.modal-search input').fill('19b');
    await page.locator('.modal-row').first().click();

    await expect(page.locator('.modal-backdrop')).toHaveCount(0);
    await expect(page).toHaveURL(/daf=19b/);

    expect(pageErrors).toEqual([]);
  });
});
