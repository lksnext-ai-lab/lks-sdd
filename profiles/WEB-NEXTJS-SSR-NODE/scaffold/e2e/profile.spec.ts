import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

test('smoke: server-rendered content is available', async ({ page }) => {
  const response = await page.goto('/');
  expect(response?.status()).toBe(200);
  await expect(page.getByTestId('server-rendered')).toBeVisible();
});

test('hydration: client interaction is attached', async ({ page }) => {
  await page.goto('/');
  const button = page.getByRole('button', { name: /Hidratación local/ });
  await button.click();
  await expect(button).toContainText('1');
});

test('accessibility: has no automatically detectable violations', async ({ page }) => {
  await page.goto('/');
  const result = await new AxeBuilder({ page }).analyze();
  expect(result.violations).toEqual([]);
});
