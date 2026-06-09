const { chromium } = require('playwright');
const path = require('path');

const BASE = 'http://localhost:3000';
const OUT = path.resolve(__dirname, '..', '..', 'docs', 'screenshots');
const DEMO_EMAIL = 'demo@proptech.io';
const DEMO_PASSWORD = 'demo1234';

async function shoot(page, name) {
  // settle: wait for network idle + a beat for animations/maps
  await page.waitForLoadState('networkidle').catch(() => {});
  await page.waitForTimeout(1500);
  const file = path.join(OUT, `${name}.png`);
  await page.screenshot({ path: file, fullPage: true });
  console.log('saved', file);
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  page.setDefaultTimeout(30000);

  // --- Login page ---
  await page.goto(`${BASE}/login`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(OUT, 'login.png'), fullPage: false });
  console.log('saved login');

  // --- Authenticate with demo account ---
  await page.fill('#email', DEMO_EMAIL);
  await page.fill('#password', DEMO_PASSWORD);
  await page.click('button[type="submit"]');
  await page.waitForURL(`${BASE}/`, { timeout: 30000 });
  await shoot(page, 'dashboard');

  // --- Search ---
  await page.goto(`${BASE}/search`, { waitUntil: 'networkidle' });
  await shoot(page, 'search');

  // --- Property detail (grab first property link from search) ---
  const href = await page.locator('a[href^="/property/"]').first().getAttribute('href').catch(() => null);
  if (href) {
    await page.goto(`${BASE}${href}`, { waitUntil: 'networkidle' });
    await shoot(page, 'property-detail');
  } else {
    console.log('no property link found, skipping detail');
  }

  // --- Chat ---
  await page.goto(`${BASE}/chat`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(800);
  // try to ask a question so the screenshot shows a real RAG answer
  const input = page.locator('textarea, input[type="text"]').first();
  if (await input.count()) {
    await input.fill('Family homes near good schools under 600k');
    await page.keyboard.press('Enter');
    await page.waitForTimeout(4000);
  }
  await shoot(page, 'chat');

  // --- Saved ---
  await page.goto(`${BASE}/saved`, { waitUntil: 'networkidle' });
  await shoot(page, 'saved');

  await browser.close();
  console.log('DONE');
})().catch((e) => {
  console.error('ERROR', e);
  process.exit(1);
});
