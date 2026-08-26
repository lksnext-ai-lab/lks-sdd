import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

test("smoke: renders the application shell", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
});

test("accessibility: has no automatically detectable violations", async ({ page }) => {
  await page.goto("/");
  const result = await new AxeBuilder({ page }).analyze();
  expect(result.violations).toEqual([]);
});
