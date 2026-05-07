const { chromium } = require('playwright');

async function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  
  const BASE_URL = 'https://subscription-pull-instantly-holland.trycloudflare.com';
  
  console.log('=== COMPREHENSIVE FRONTEND TEST ===\n');
  
  // ── TEST 1: Dashboard ────────────────────────────────────────────────────
  console.log('TEST 1: Dashboard loads');
  await page.goto(BASE_URL);
  await delay(3000);
  
  const hasHeading = await page.locator('h1:has-text("Dashboard")').isVisible();
  console.log('  ✓ Dashboard heading:', hasHeading);
  await page.screenshot({ path: '/tmp/test-01-dashboard.png' });
  
  // ── TEST 2: Sidebar ──────────────────────────────────────────────────────
  console.log('\nTEST 2: Sidebar');
  const sidebar = page.locator('aside').first();
  console.log('  ✓ Sidebar found');
  await sidebar.locator('text=Actors').click();
  await delay(500);
  console.log('  ✓ Actors clicked');
  await sidebar.locator('text=Dashboard').click();
  await delay(500);
  console.log('  ✓ Dashboard clicked');
  
  // ── TEST 3: Create Modal via sidebar ─────────────────────────────────────
  console.log('\nTEST 3: Create Modal (sidebar button)');
  await sidebar.locator('button:has-text("New Investigation")').click();
  await delay(1000);
  await page.screenshot({ path: '/tmp/test-03-modal.png' });
  
  const modalTitle = await page.locator('h2:has-text("New Investigation")').isVisible();
  console.log('  ✓ Modal title visible:', modalTitle);
  
  if (modalTitle) {
    await page.locator('input[placeholder*="Zendaya"]').fill('Test Actor');
    await page.locator('input[placeholder*="drama"]').fill('Can they carry a lead role?');
    await page.locator('textarea').fill('Initial read placeholder');
    await page.locator('button[type="submit"]:has-text("Create")').click();
    await delay(2000);
    
    const newCard = await page.locator('text=Can they carry a lead role?').isVisible();
    console.log('  ✓ New card visible:', newCard);
  } else {
    console.log('  ⚠ Modal did not open - checking why');
    // Close any overlay by pressing Escape
    await page.keyboard.press('Escape');
  }
  await page.screenshot({ path: '/tmp/test-03-after-create.png' });
  
  // ── TEST 4: Investigation Detail ─────────────────────────────────────────
  console.log('\nTEST 4: Investigation Detail');
  
  // Click first completed investigation
  const cards = await page.locator('button.bg-graphite').all();
  console.log('  Found', cards.length, 'investigation cards');
  
  if (cards.length > 0) {
    await cards[0].click();
    await delay(2500);
    await page.screenshot({ path: '/tmp/test-04-detail.png' });
    
    const hasPipeline = await page.locator('h2:has-text("Pipeline")').isVisible();
    const hasFileTree = await page.locator('text=FILES').first().isVisible();
    console.log('  ✓ Pipeline visible:', hasPipeline);
    console.log('  ✓ File tree visible:', hasFileTree);
    
    // ── TEST 5: Click files ────────────────────────────────────────────────
    console.log('\nTEST 5: File Tree Navigation');
    
    const fileLinks = await page.locator('[class*="FileTree"] button, [class*="file"] button, button:has-text(".md")').all();
    console.log('  Found', fileLinks.length, 'file links');
    
    // Try clicking brief.md
    const briefLink = page.locator('text=brief.md').first();
    if (await briefLink.isVisible().catch(() => false)) {
      await briefLink.click();
      await delay(1000);
      const hasBriefContent = await page.locator('text=Actor Brief').isVisible().catch(() => false);
      console.log('  ✓ brief.md renders:', hasBriefContent);
      await page.screenshot({ path: '/tmp/test-05-brief.png' });
    }
    
    // Try clicking video-catalog.md
    const catalogLink = page.locator('text=video-catalog.md').first();
    if (await catalogLink.isVisible().catch(() => false)) {
      await catalogLink.click();
      await delay(1000);
      const hasCatalog = await page.locator('text=Video Catalog').isVisible().catch(() => false);
      console.log('  ✓ video-catalog.md renders:', hasCatalog);
      await page.screenshot({ path: '/tmp/test-05-catalog.png' });
    }
    
    // ── TEST 6: Chat panel ─────────────────────────────────────────────────
    console.log('\nTEST 6: Chat Panel');
    const chatInput = page.locator('input[placeholder*="instructions"]');
    const chatVisible = await chatInput.isVisible();
    console.log('  ✓ Chat input visible:', chatVisible);
    
    if (chatVisible) {
      await chatInput.fill('Test message from automated test');
      console.log('  ✓ Typed in chat');
      await page.screenshot({ path: '/tmp/test-06-chat.png' });
    }
    
    // ── TEST 7: Pipeline run buttons ───────────────────────────────────────
    console.log('\nTEST 7: Pipeline Run Buttons');
    const runButtons = await page.locator('text=Run').all();
    console.log('  Found', runButtons.length, 'Run buttons');
    
    if (runButtons.length > 0) {
      await runButtons[0].click();
      await delay(2000);
      console.log('  ✓ Clicked Run on agent');
      await page.screenshot({ path: '/tmp/test-07-running.png' });
    }
    
    // ── TEST 8: Back button ────────────────────────────────────────────────
    console.log('\nTEST 8: Back Navigation');
    await page.locator('button:has([data-lucide="arrow-left"])').click();
    await delay(1000);
    const onDashboard = await page.locator('h1:has-text("Dashboard")').isVisible();
    console.log('  ✓ Back to dashboard:', onDashboard);
    await page.screenshot({ path: '/tmp/test-08-back.png' });
  }
  
  // ── TEST 9: Mobile ───────────────────────────────────────────────────────
  console.log('\nTEST 9: Mobile Viewport');
  await page.setViewportSize({ width: 375, height: 667 });
  await page.goto(BASE_URL);
  await delay(1500);
  const mobileLoads = await page.locator('text=ORACLE').isVisible();
  console.log('  ✓ Mobile loads:', mobileLoads);
  await page.screenshot({ path: '/tmp/test-09-mobile.png' });
  
  await page.setViewportSize({ width: 1440, height: 900 });
  
  console.log('\n=== TEST COMPLETE ===');
  await browser.close();
})();
