const { chromium } = require('playwright');

async function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  
  const BASE_URL = 'https://danny-march-transformation-knowledgestorm.trycloudflare.com';
  
  // 1. Dashboard
  await page.goto(BASE_URL);
  await delay(2500);
  await page.screenshot({ path: '/tmp/final-dashboard.png' });
  console.log('Dashboard screenshot saved');
  
  // 2. Create modal
  await page.locator('button:has-text("New Investigation")').first().click();
  await delay(800);
  await page.screenshot({ path: '/tmp/final-modal.png' });
  console.log('Modal screenshot saved');
  await page.keyboard.press('Escape');
  await delay(300);
  
  // 3. Investigation detail
  const cards = await page.locator('.investigation-card').all();
  if (cards.length > 0) {
    await cards[0].click();
    await delay(2500);
    await page.screenshot({ path: '/tmp/final-detail.png' });
    console.log('Detail screenshot saved');
    
    // 4. Brief view
    const briefLink = page.locator('text=brief.md').first();
    if (await briefLink.isVisible().catch(() => false)) {
      await briefLink.click();
      await delay(800);
      await page.screenshot({ path: '/tmp/final-brief.png' });
      console.log('Brief screenshot saved');
    }
    
    // 5. Video catalog view
    const catalogLink = page.locator('text=video-catalog.md').first();
    if (await catalogLink.isVisible().catch(() => false)) {
      await catalogLink.click();
      await delay(800);
      await page.screenshot({ path: '/tmp/final-catalog.png' });
      console.log('Catalog screenshot saved');
    }
  }
  
  await browser.close();
  console.log('\nAll screenshots saved to /tmp/final-*.png');
})();
