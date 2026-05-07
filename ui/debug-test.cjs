const { chromium } = require('playwright');

async function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  
  const BASE_URL = 'http://localhost:8000';
  
  console.log('=== DEBUG TEST ===\n');
  
  await page.goto(BASE_URL);
  await delay(2000);
  await page.screenshot({ path: '/tmp/debug-01-dashboard.png' });
  console.log('Dashboard loaded');
  
  // Get all card text
  const cards = await page.locator('button.bg-graphite').all();
  console.log('Cards found:', cards.length);
  for (let i = 0; i < cards.length; i++) {
    const text = await cards[i].textContent();
    console.log(`  Card ${i}:`, text?.substring(0, 60));
  }
  
  // Click first card
  if (cards.length > 0) {
    await cards[0].click();
    await delay(3000);
    await page.screenshot({ path: '/tmp/debug-02-after-click.png' });
    console.log('Clicked first card');
    
    // Check URL
    console.log('Current URL:', page.url());
    
    // Check for pipeline
    const pipelineHtml = await page.locator('aside').nth(1).innerHTML().catch(e => 'ERROR: ' + e.message);
    console.log('Pipeline HTML length:', pipelineHtml.length);
    
    // Check for file tree
    const fileTreeHtml = await page.locator('aside').nth(2).innerHTML().catch(e => 'ERROR: ' + e.message);
    console.log('FileTree HTML length:', fileTreeHtml.length);
    
    // Get page HTML snippet
    const bodyHtml = await page.locator('body').innerHTML();
    console.log('Body HTML length:', bodyHtml.length);
    
    // Save full HTML for inspection
    const fs = require('fs');
    fs.writeFileSync('/tmp/debug-page.html', bodyHtml);
    console.log('Full HTML saved to /tmp/debug-page.html');
  }
  
  await browser.close();
})();
