// node serve.mjs [port] [--root directory]; prints URL only after successful bind.
import { serve } from './runtime.mjs';
import fs from 'node:fs'; import path from 'node:path';
const args = process.argv.slice(2), i = args.indexOf('--root');
const root = i >= 0 ? args[i + 1] : process.cwd();
const port = args[0] && !args[0].startsWith('--') ? Number(args[0]) : 0;
try {
  const s = await serve(root, port);
  const entry = fs.existsSync(path.join(root, 'live/index.html')) ? '/live/index.html' : '/index.html';
  console.log(`LIVE: ${s.url}${entry}`);
  for (const sig of ['SIGINT', 'SIGTERM']) process.on(sig, async () => { await s.close(); process.exit(0); });
} catch (e) { console.error(e.message); process.exitCode = 1; }
