const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  
  await page.goto('http://localhost:8000');
  await new Promise(r => setTimeout(r, 2000));
  
  await page.locator('button:has-text("New Investigation")').first().click();
  await new Promise(r => setTimeout(r, 1000));
  await page.screenshot({ path: '/tmp/test-modal-fixed.png' });
  console.log('Modal screenshot saved');
  
  await browser.close();
})();
