const { chromium } = require('playwright');

async function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  
  const BASE_URL = 'http://localhost:8000';
  
  await page.goto(BASE_URL);
  await delay(2000);
  
  // Click first investigation card (using specific class)
  const cards = await page.locator('.investigation-card').all();
  console.log('Investigation cards found:', cards.length);
  
  if (cards.length > 0) {
    const cardText = await cards[0].textContent();
    console.log('Clicking card:', cardText?.substring(0, 50));
    await cards[0].click();
    await delay(3000);
    
    console.log('Current URL:', page.url());
    await page.screenshot({ path: '/tmp/debug-detail.png' });
    
    // Check what's on the page
    const title = await page.locator('h1').textContent().catch(() => 'no h1');
    console.log('Page title:', title);
    
    // Check for Pipeline heading
    const pipelineHeading = await page.locator('text=Pipeline').isVisible().catch(() => false);
    console.log('Pipeline visible:', pipelineHeading);
    
    // Check for file tree
    const filesHeading = await page.locator('text=FILES').first().isVisible().catch(() => false);
    console.log('Files visible:', filesHeading);
    
    // Check chat
    const chat = await page.locator('input[placeholder*="instructions"]').isVisible().catch(() => false);
    console.log('Chat visible:', chat);
  }
  
  await browser.close();
})();
