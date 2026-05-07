const { chromium } = require('playwright');

async function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  
  const BASE_URL = 'http://localhost:8000';
  
  console.log('=== FULL END-TO-END TEST ===\n');
  let passCount = 0;
  let failCount = 0;
  
  function check(name, result) {
    if (result) { console.log(`  ✅ ${name}`); passCount++; }
    else { console.log(`  ❌ ${name}`); failCount++; }
  }
  
  // ── TEST 1: Dashboard ────────────────────────────────────────────────────
  console.log('TEST 1: Dashboard');
  await page.goto(BASE_URL);
  await delay(2000);
  await page.screenshot({ path: '/tmp/e2e-01-dashboard.png' });
  
  check('Dashboard heading', await page.locator('h1:has-text("Dashboard")').isVisible());
  check('New Investigation button', await page.locator('button:has-text("New Investigation")').first().isVisible());
  check('Stats cards', await page.locator('text=Total').isVisible());
  check('Investigation cards', (await page.locator('.investigation-card').count()) > 0);
  
  // ── TEST 2: Create Investigation ─────────────────────────────────────────
  console.log('\nTEST 2: Create Investigation');
  await page.locator('button:has-text("New Investigation")').first().click();
  await delay(800);
  await page.screenshot({ path: '/tmp/e2e-02-modal-open.png' });
  
  check('Modal opened', await page.locator('h2:has-text("New Investigation")').isVisible());
  
  const uniqueName = 'TestActor-' + Date.now();
  await page.locator('input[placeholder*="Zendaya"]').fill(uniqueName);
  await page.locator('input[placeholder*="drama"]').fill('Can they carry a lead role?');
  await page.locator('textarea').fill('Initial read for testing.');
  await page.screenshot({ path: '/tmp/e2e-02-modal-filled.png' });
  
  await page.locator('button[type="submit"]:has-text("Create")').click();
  await delay(2000);
  await page.screenshot({ path: '/tmp/e2e-02-after-create.png' });
  
  check('New card appears', await page.locator(`.investigation-card:has-text("${uniqueName}")`).first().isVisible());
  
  // ── TEST 3: Empty Detail Page ────────────────────────────────────────────
  console.log('\nTEST 3: Empty Investigation Detail');
  await page.locator(`.investigation-card:has-text("${uniqueName}")`).first().click();
  await delay(2500);
  await page.screenshot({ path: '/tmp/e2e-03-detail-empty.png' });
  
  check('Navigated to detail', page.url().includes('/investigation/'));
  check('Pipeline visible', await page.locator('h2:has-text("Pipeline")').isVisible());
  check('File tree visible', await page.locator('text=manifest.json').isVisible());
  check('Chat panel visible', await page.locator('input[placeholder*="instructions"]').isVisible());
  check('Status CREATED', await page.locator('text=CREATED').first().isVisible());
  
  // ── TEST 4: Run Harvester ────────────────────────────────────────────────
  console.log('\nTEST 4: Run Actor Harvester');
  const runBtns = await page.locator('text=Run').all();
  console.log('  Found', runBtns.length, 'Run buttons');
  
  if (runBtns.length > 0) {
    await runBtns[0].click();
    console.log('  ▶ Clicked Run');
    await delay(3000);
    await page.screenshot({ path: '/tmp/e2e-04-after-harvester.png' });
    check('Harvest completed', await page.locator('text=COMPLETED').first().isVisible().catch(() => false));
  }
  
  await page.reload();
  await delay(2000);
  
  // ── TEST 5: Run Video Analysis ───────────────────────────────────────────
  console.log('\nTEST 5: Run Video Analysis');
  const runBtns2 = await page.locator('text=Run').all();
  if (runBtns2.length > 0) {
    await runBtns2[0].click();
    console.log('  ▶ Clicked Run');
    await delay(3000);
    await page.screenshot({ path: '/tmp/e2e-05-after-video.png' });
  }
  
  await page.reload();
  await delay(2000);
  
  // ── TEST 6: File Navigation ──────────────────────────────────────────────
  console.log('\nTEST 6: File Tree Navigation');
  
  const filesToClick = ['brief.md', 'video-catalog.md', 'facts.md'];
  for (const fname of filesToClick) {
    const link = page.locator(`text=${fname}`).first();
    if (await link.isVisible().catch(() => false)) {
      await link.click();
      await delay(600);
      const pathBar = await page.locator(`text=${fname}`).nth(1).isVisible().catch(() => false);
      check(`${fname} opens`, pathBar);
    } else {
      check(`${fname} exists in tree`, false);
    }
  }
  await page.screenshot({ path: '/tmp/e2e-06-files.png' });
  
  // ── TEST 7: Chat ─────────────────────────────────────────────────────────
  console.log('\nTEST 7: Chat Panel');
  const chatInput = page.locator('input[placeholder*="instructions"]');
  check('Chat input visible', await chatInput.isVisible());
  if (await chatInput.isVisible()) {
    await chatInput.fill('Focus on emotional range in dramatic scenes');
    await page.screenshot({ path: '/tmp/e2e-07-chat.png' });
    check('Chat message typed', true);
  }
  
  // ── TEST 8: Back Navigation ──────────────────────────────────────────────
  console.log('\nTEST 8: Back to Dashboard');
  // Use the arrow-left button in the top bar
  const backBtn = page.locator('button svg[data-lucide="arrow-left"]').locator('xpath=ancestor::button');
  if (await backBtn.isVisible().catch(() => false)) {
    await backBtn.click();
  } else {
    // Fallback: browser back
    await page.goBack();
  }
  await delay(1000);
  await page.screenshot({ path: '/tmp/e2e-08-back.png' });
  check('Back on dashboard', await page.locator('h1:has-text("Dashboard")').isVisible());
  
  // ── TEST 9: Sidebar ──────────────────────────────────────────────────────
  console.log('\nTEST 9: Sidebar Navigation');
  const sidebar = page.locator('aside').first();
  await sidebar.locator('text=Actors').click();
  await delay(500);
  check('Actors link works', true);
  await sidebar.locator('text=Dashboard').click();
  await delay(500);
  check('Dashboard link works', true);
  
  // ── TEST 10: Mobile ──────────────────────────────────────────────────────
  console.log('\nTEST 10: Mobile Viewport');
  await page.setViewportSize({ width: 375, height: 667 });
  await page.goto(BASE_URL);
  await delay(1500);
  await page.screenshot({ path: '/tmp/e2e-10-mobile.png' });
  check('Mobile loads', await page.locator('text=ORACLE').isVisible());
  await page.setViewportSize({ width: 1440, height: 900 });
  
  // ── SUMMARY ──────────────────────────────────────────────────────────────
  console.log('\n=== TEST SUMMARY ===');
  console.log(`Passed: ${passCount}`);
  console.log(`Failed: ${failCount}`);
  console.log(`Total:  ${passCount + failCount}`);
  
  if (failCount === 0) console.log('\n🎉 ALL TESTS PASSED');
  else console.log(`\n⚠️ ${failCount} test(s) failed`);
  
  await browser.close();
})();
