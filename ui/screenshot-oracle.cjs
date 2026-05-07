const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  
  await page.goto('http://localhost:8000/');
  await page.waitForTimeout(2000);
  await page.screenshot({ path: '/tmp/oracle-dashboard.png', fullPage: false });
  console.log('Dashboard screenshot saved to /tmp/oracle-dashboard.png');
  
  const cards = await page.locator('button.bg-graphite').all();
  if (cards.length > 0) {
    await cards[0].click();
    await page.waitForTimeout(2000);
    await page.screenshot({ path: '/tmp/oracle-investigation.png', fullPage: false });
    console.log('Investigation screenshot saved to /tmp/oracle-investigation.png');
  }
  
  await browser.close();
})();
