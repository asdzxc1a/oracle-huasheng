const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  
  const url = 'https://subscription-pull-instantly-holland.trycloudflare.com/investigation/zendaya-2026-05-07-cf604b';
  
  await page.goto(url);
  await page.waitForTimeout(3000);
  await page.screenshot({ path: '/tmp/oracle-tunnel-detail-direct.png', fullPage: false });
  console.log('Tunnel detail screenshot saved');
  
  await browser.close();
})();
