import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

test('smoke: renders and changes local state', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { level: 1 })).toContainText('Angular');
  const button = page.getByRole('button', { name: /Verificación local/ });
  await button.click();
  await expect(button).toContainText('1');
});

test('accessibility: has no automatically detectable violations', async ({ page }) => {
  await page.goto('/');
  const result = await new AxeBuilder({ page }).analyze();
  expect(result.violations).toEqual([]);
});
