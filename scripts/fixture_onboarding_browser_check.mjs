#!/usr/bin/env node
/**
 * fixture_onboarding_browser_check.mjs - the browser-rendering half of
 * Phase 3 Step 6's onboarding proof (scripts/test_fixture_onboarding.py
 * drives this; it is not meant to be run standalone in normal use).
 *
 * Launches a real headless Chromium against an already-running static
 * server (an isolated build.mjs --module <key> --search-root <root>
 * --out <dir> output) and asserts the app shell actually renders the
 * requested module's content - not just that the files exist on disk.
 *
 * Usage:
 *   node fixture_onboarding_browser_check.mjs <baseUrl> <module> <daf>
 *     <expectedSugyaCount> <expectedLineCount> <expectedMarker>
 */
import { chromium } from '@playwright/test';

const [baseUrl, moduleKey, daf, expectedSugyaCount, expectedLineCount, expectedMarker] = process.argv.slice(2);

async function main() {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', (e) => errors.push(e.message));
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });

    await page.goto(`${baseUrl}/index.html?module=${moduleKey}&daf=${daf}`);
    await page.waitForSelector('.sugya', { timeout: 10000 });

    const sugyaCount = await page.locator('.sugya').count();
    const lineCount = await page.locator('.line').count();
    const bodyText = await page.locator('body').innerText();

    const problems = [];
    if (sugyaCount !== Number(expectedSugyaCount)) {
      problems.push(`expected ${expectedSugyaCount} .sugya elements, got ${sugyaCount}`);
    }
    if (lineCount !== Number(expectedLineCount)) {
      problems.push(`expected ${expectedLineCount} .line elements, got ${lineCount}`);
    }
    if (!bodyText.includes(expectedMarker)) {
      problems.push(`expected page text to contain ${JSON.stringify(expectedMarker)}`);
    }
    if (errors.length) {
      problems.push(`page errors: ${JSON.stringify(errors)}`);
    }

    if (problems.length) {
      console.error('FAIL: ' + problems.join(' | '));
      process.exitCode = 1;
    } else {
      console.log(
        `OK: module=${moduleKey} daf=${daf} rendered ${sugyaCount} sugyot, ` +
        `${lineCount} lines, marker present, zero page errors`
      );
    }
  } finally {
    await browser.close();
  }
}

main();
