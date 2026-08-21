import { existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const args = process.argv.slice(2);
const option = (name, fallback) => {
  const index = args.indexOf(name);
  return index >= 0 && args[index + 1] ? args[index + 1] : fallback;
};

process.env.HOSTNAME = option('--host', process.env.HOSTNAME ?? '0.0.0.0');
process.env.PORT = option('--port', process.env.PORT ?? '3000');

const server = resolve('.next/standalone/server.js');
if (!existsSync(server)) {
  throw new Error('Missing standalone server; run npm run build first.');
}
await import(pathToFileURL(server).href);
