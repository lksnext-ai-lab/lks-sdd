import { cp, mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';

const standalone = '.next/standalone';
if (!existsSync(standalone)) {
  throw new Error('Missing .next/standalone; run this script after next build.');
}

await mkdir(`${standalone}/.next`, { recursive: true });
await cp('.next/static', `${standalone}/.next/static`, { recursive: true, force: true });
if (existsSync('public')) {
  await cp('public', `${standalone}/public`, { recursive: true, force: true });
}
