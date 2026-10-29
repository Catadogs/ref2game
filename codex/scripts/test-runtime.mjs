import assert from 'node:assert/strict';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { serve } from './runtime.mjs';
// Standalone server checks use a new directory under the caller's work folder.
const base = path.resolve('work/ref2game-server-tests'); fs.mkdirSync(base, { recursive: true });
const root = fs.mkdtempSync(path.join(base, 'run-'));
fs.writeFileSync(path.join(root, 'index.html'), 'ok');
const s = await serve(root);
const request = (requestPath, method = 'GET') => new Promise((resolve, reject) => {
  const req = http.request(s.url, { path: requestPath, method }, res => {
    const chunks = []; res.on('data', chunk => chunks.push(chunk));
    res.on('end', () => resolve({ status: res.statusCode, text: Buffer.concat(chunks).toString() }));
  }); req.on('error', reject); req.end();
});
try {
  assert.deepEqual(await request('/'), { status: 200, text: 'ok' });
  assert.deepEqual(await request('/index.html', 'HEAD'), { status: 200, text: '' });
  assert.equal((await request('/missing')).status, 404);
  assert.equal((await request('/%2e%2e/outside')).status, 403);
  assert.equal((await request('/index.html', 'POST')).status, 405);
  await assert.rejects(serve(root, s.server.address().port), /EADDRINUSE/);
  console.log('Server checks passed: GET, HEAD, missing file, traversal, methods, occupied port.');
} finally { await s.close(); }
