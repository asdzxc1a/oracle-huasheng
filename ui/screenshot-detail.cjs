const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  
  // Get an investigation ID from the API
  const resp = await fetch('http://localhost:8000/api/investigations');
  const investigations = await resp.json();
  const invId = investigations[0]?.id;
  
  if (invId) {
    await page.goto(`http://localhost:8000/investigation/${invId}`);
    await page.waitForTimeout(2000);
    await page.screenshot({ path: '/tmp/oracle-detail.png', fullPage: false });
    console.log('Detail screenshot saved to /tmp/oracle-detail.png');
  }
  
  await browser.close();
})();
