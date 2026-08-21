import {
  AngularNodeAppEngine,
  createNodeRequestHandler,
  isMainModule,
  writeResponseToNodeResponse,
} from '@angular/ssr/node';
import express from 'express';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const serverDirectory = dirname(fileURLToPath(import.meta.url));
const browserDirectory = resolve(serverDirectory, '../browser');
const app = express();
const engine = new AngularNodeAppEngine();

app.use(express.static(browserDirectory, { maxAge: '1y', index: false }));
app.use((request, response, next) => {
  engine
    .handle(request)
    .then((result) => result ? writeResponseToNodeResponse(result, response) : next())
    .catch(next);
});

if (isMainModule(import.meta.url)) {
  const port = Number(process.env['PORT'] ?? 4000);
  app.listen(port, () => console.log(`Angular SSR listening on ${port}`));
}

export const reqHandler = createNodeRequestHandler(app);
