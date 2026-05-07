import { test, expect } from "@playwright/test";

const BASE_URL = process.env.ORACLE_URL || "http://localhost:8000";

test.describe("Oracle E2E — Golden Path", () => {
  test("dashboard loads and shows investigation list", async ({ page }) => {
    await page.goto(BASE_URL);
    await expect(page.locator("text=ORACLE")).toBeVisible();
    await expect(page.locator("text=Dashboard")).toBeVisible();
    await expect(page.locator("text=Recent Investigations")).toBeVisible();
  });

  test("create investigation flow", async ({ page }) => {
    await page.goto(BASE_URL);
    
    await page.locator("text=New Investigation").first().click();
    await expect(page.locator("text=Actor Name")).toBeVisible();
    
    await page.locator('input[placeholder*="Zendaya"]').fill("Barry Allen");
    await page.locator('input[placeholder*="drama"]').fill("Can he outrun a script?");
    
    await page.locator("text=Create Investigation").click();
    await expect(page.locator("text=Barry Allen")).toBeVisible();
  });

  test("investigation detail shows pipeline and files", async ({ page }) => {
    const createRes = await page.request.post(`${BASE_URL}/api/investigations`, {
      data: {
        actor: "Starfire",
        client_question: "Can she carry an indie sci-fi?",
      },
    });
    const { id } = await createRes.json();
    
    await page.goto(`${BASE_URL}/investigation/${id}`);
    await expect(page.locator("text=Starfire")).toBeVisible();
    await expect(page.locator("text=Pipeline")).toBeVisible();
    await expect(page.locator("text=Actor Harvester")).toBeVisible();
  });

  test("run agent and view brief", async ({ page }) => {
    const createRes = await page.request.post(`${BASE_URL}/api/investigations`, {
      data: {
        actor: "Mister Miracle",
        client_question: "Can he escape any script?",
      },
    });
    const { id } = await createRes.json();
    
    await page.request.post(
      `${BASE_URL}/api/investigations/${id}/agents/actor_harvester`,
      { data: {} }
    );
    await page.waitForTimeout(3000);
    
    await page.request.post(
      `${BASE_URL}/api/investigations/${id}/agents/video_analysis`,
      { data: {} }
    );
    await page.waitForTimeout(3000);
    
    await page.goto(`${BASE_URL}/investigation/${id}`);
    await expect(page.locator("text=brief.md")).toBeVisible();
    await page.locator("text=brief.md").click();
    await expect(page.locator("text=Actor Brief")).toBeVisible();
  });
});
