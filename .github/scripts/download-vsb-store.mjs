import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const productUrl = process.env.PRODUCT_URL || 'https://ctrader.com/products/1847';
const ctid = process.env.CTID;
const password = process.env.CTPASS;
if (!ctid || !password) throw new Error('CTID/CTPASS missing');

const out = path.resolve(process.env.OUT_DIR || 'work/downloads');
const diag = path.resolve(process.env.DIAG_DIR || 'work/browser');
fs.mkdirSync(out, { recursive: true });
fs.mkdirSync(diag, { recursive: true });

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ acceptDownloads: true, locale: 'en-US' });
const page = await context.newPage();
const snap = async n => {
  try { await page.screenshot({ path: path.join(diag, `${n}.png`), fullPage: true }); } catch {}
  try { fs.writeFileSync(path.join(diag, `${n}.html`), await page.content()); } catch {}
};
const isVisible = async locator => locator.isVisible({ timeout: 1800 }).catch(() => false);

async function downloadFrom(scope) {
  const downloadLabels = [/^Download$/i, /下载/i, /下載/i];
  for (const rx of downloadLabels) {
    const direct = scope.getByText(rx, { exact: true }).first();
    if (await isVisible(direct)) {
      const wait = page.waitForEvent('download', { timeout: 20000 });
      await direct.click();
      const d = await wait;
      await d.saveAs(path.join(out, d.suggestedFilename()));
      return true;
    }
  }

  const buttons = scope.locator('button');
  for (let i = 0, n = await buttons.count(); i < n; i++) {
    const b = buttons.nth(i);
    if (!await isVisible(b)) continue;
    const label = `${await b.getAttribute('aria-label') || ''} ${await b.getAttribute('title') || ''} ${await b.innerText().catch(() => '')}`;
    if (n > 5 && !/more|menu|更多|⋯|\.\.\./i.test(label)) continue;
    try {
      await b.click();
      await page.waitForTimeout(400);
      for (const rx of downloadLabels) {
        const item = page.getByText(rx, { exact: true }).last();
        if (await isVisible(item)) {
          const wait = page.waitForEvent('download', { timeout: 20000 });
          await item.click();
          const d = await wait;
          await d.saveAs(path.join(out, d.suggestedFilename()));
          return true;
        }
      }
      await page.keyboard.press('Escape').catch(() => {});
    } catch {}
  }
  return false;
}

try {
  await page.goto('https://id.ctrader.com/login?locale=en', { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.getByPlaceholder(/Email or cTrader ID/i).first().fill(ctid);
  await page.getByPlaceholder(/Password/i).first().fill(password);
  await page.getByRole('button', { name: /Log in/i }).last().click();
  await page.waitForTimeout(3500);
  await snap('01-after-login');

  await page.goto(productUrl, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(2500);
  await snap('02-product');
  const productBody = await page.locator('body').innerText();
  if (!/Volatility Sniper Breakout BETA/i.test(productBody)) throw new Error('Wrong Store product page');
  if (!/Installed|Open/i.test(productBody)) throw new Error('VSB is not installed for this cTrader ID');

  const financeLink = page.locator('a[href*="/account/finances"]').first();
  if (!await isVisible(financeLink)) throw new Error('Account finances link missing');
  const href = await financeLink.getAttribute('href');
  await page.goto(new URL(href, page.url()).href, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(2500);

  for (const rx of [/Accept necessary/i, /Accept all/i, /接受必要/i, /全部接受/i]) {
    const cookieButton = page.getByRole('button', { name: rx }).first();
    if (await isVisible(cookieButton)) { await cookieButton.click(); break; }
  }
  await snap('03-finances');

  const purchaseLabels = [/Purchases/i, /购买记录/i, /購買記錄/i, /^购买$/i, /^購買$/i, /購入/i];
  let switched = false;
  for (const rx of purchaseLabels) {
    const candidates = [
      page.getByRole('tab', { name: rx }).first(),
      page.getByRole('link', { name: rx }).first(),
      page.getByRole('button', { name: rx }).first(),
      page.getByText(rx, { exact: true }).first()
    ];
    for (const c of candidates) {
      if (await isVisible(c)) { await c.click(); switched = true; break; }
    }
    if (switched) break;
  }
  if (switched) await page.waitForTimeout(1200);

  const search = page.getByPlaceholder(/Search|搜索|搜尋/i).first();
  if (await isVisible(search)) {
    await search.fill('Volatility Sniper Breakout BETA');
    await page.waitForTimeout(1600);
  }
  await snap('04-purchases-filtered');

  const title = page.getByText(/Volatility Sniper Breakout BETA/i).first();
  if (!await isVisible(title)) throw new Error('VSB not visible after Purchases search');
  let scope = title.locator('xpath=ancestor::tr[1]');
  if (!await scope.count()) scope = title.locator('xpath=ancestor::*[self::li or self::div][.//button][1]');
  if (!await scope.count()) scope = page;

  let ok = await downloadFrom(scope);
  if (!ok) ok = await downloadFrom(page);
  await page.waitForTimeout(800);
  await snap('05-after-download');
  const algos = fs.readdirSync(out).filter(x => x.toLowerCase().endsWith('.algo'));
  if (!ok || !algos.length) throw new Error('Download did not produce an .algo file');
  console.log(`Downloaded: ${algos.join(', ')}`);
} catch (e) {
  console.error(e?.stack || e);
  await snap('99-failure');
  process.exitCode = 1;
} finally {
  await browser.close();
}
