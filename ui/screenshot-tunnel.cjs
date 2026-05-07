const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  
  const url = 'https://subscription-pull-instantly-holland.trycloudflare.com';
  
  await page.goto(url);
  await page.waitForTimeout(3000);
  await page.screenshot({ path: '/tmp/oracle-tunnel-dashboard.png', fullPage: false });
  console.log('Tunnel dashboard screenshot saved');
  
  // Click first investigation
  const cards = await page.locator('button.bg-graphite').all();
  if (cards.length > 0) {
    await cards[0].click();
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/tmp/oracle-tunnel-detail.png', fullPage: false });
    console.log('Tunnel detail screenshot saved');
  }
  
  await browser.close();
})();
