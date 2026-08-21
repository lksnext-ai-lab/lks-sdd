import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './e2e',
  use: { baseURL: 'http://127.0.0.1:4000' },
  webServer: { command: 'npm start', url: 'http://127.0.0.1:4000', timeout: 120_000 },
});
