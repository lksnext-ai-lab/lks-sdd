import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { expect, test } from '@playwright/test';

test('real browser mutation survives reload through API and PostgreSQL', async ({ page, browserName }) => {
  const evidenceRoot = resolve('../../.lks-sdd/fullstack');
  mkdirSync(evidenceRoot, { recursive: true });
  const requests: Array<Record<string, unknown>> = [];
  const consoleErrors: string[] = [];
  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  page.on('response', (response) => {
    const url = new URL(response.url());
    if (url.pathname.startsWith('/api/v1')) {
      requests.push({
        path: url.pathname,
        method: response.request().method(),
        status: response.status(),
        correlation_id: response.headers()['x-correlation-id'] ?? null,
      });
    }
  });

  await page.goto('/');
  await page.locator('#username').fill('lks-sdd-gate-user');
  await page.locator('#password').fill('lks-sdd-gate-password');
  await page.locator('#kc-login').click();
  await expect(page.getByText('API y PostgreSQL conectados')).toBeVisible();

  const label = `fullstack-${Date.now()}`;
  const before = resolve(evidenceRoot, 'before.png');
  const after = resolve(evidenceRoot, 'after.png');
  const reloaded = resolve(evidenceRoot, 'reloaded.png');
  await page.screenshot({ path: before });
  await page.getByLabel('Etiqueta').fill(label);
  await page.getByRole('button', { name: 'Guardar elemento' }).click();
  await expect(page.getByRole('listitem').filter({ hasText: label })).toBeVisible();
  await page.screenshot({ path: after });
  await page.reload();
  await expect(page.getByRole('listitem').filter({ hasText: label })).toBeVisible();
  await page.screenshot({ path: reloaded });

  const screenshots = [before, after, reloaded].map((path) => ({
    path: `fullstack/${path.split(/[\\/]/).pop()}`,
    sha256: createHash('sha256').update(readFileSync(path)).digest('hex'),
  }));
  writeFileSync(resolve('../../.lks-sdd/fullstack-evidence.json'), JSON.stringify({
    observations: {
      runtime_units: ['frontend', 'api', 'database', 'identity'],
      browser: browserName,
      viewport: page.viewportSize(),
      requests,
      mutation: { action: 'Guardar elemento', label },
      read_back: true,
      reload: true,
      persistence: true,
      screenshots,
      console_errors: consoleErrors,
    },
    mocks: [],
  }, null, 2));
  expect(consoleErrors).toEqual([]);
  expect(requests.some((item) => item.path === '/api/v1/items' && item.method === 'POST' && item.status === 201)).toBe(true);
});
