// Shared, portable browser and localhost runtime. No installs or global configuration changes.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

export function browserType() {
  const req = createRequire(import.meta.url);
  try { return req(process.env.PLAYWRIGHT || 'playwright').chromium; }
  catch { throw new Error('Playwright is missing. Install it locally in scripts/ or set PLAYWRIGHT to an existing package directory.'); }
}

export async function launchBrowser() {
  const chromium = browserType();
  const opts = { args: ['--use-angle=' + (process.platform === 'darwin' ? 'metal' : 'default'), '--enable-gpu', '--ignore-gpu-blocklist'] };
  if (process.env.REF2GAME_BROWSER) opts.executablePath = process.env.REF2GAME_BROWSER;
  else if (process.platform === 'win32' && !fs.existsSync(chromium.executablePath())) {
    const candidates = [
      path.join(process.env.PROGRAMFILES || 'C:/Program Files', 'Google/Chrome/Application/chrome.exe'),
      path.join(process.env['PROGRAMFILES(X86)'] || 'C:/Program Files (x86)', 'Microsoft/Edge/Application/msedge.exe'),
      path.join(process.env.LOCALAPPDATA || '', 'Google/Chrome/Application/chrome.exe'),
    ];
    opts.executablePath = candidates.find(p => fs.existsSync(p));
  }
  return chromium.launch(opts);
}

export async function serve(root = process.cwd(), port = 0) {
  root = fs.realpathSync(root);
  const types = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.png': 'image/png', '.jpg': 'image/jpeg', '.json': 'application/json', '.css': 'text/css', '.woff2': 'font/woff2', '.wav': 'audio/wav', '.mp3': 'audio/mpeg' };
  const server = http.createServer((q, r) => {
    try {
      if (!['GET', 'HEAD'].includes(q.method)) { r.writeHead(405); r.end(); return; }
      let file = path.resolve(root, '.' + decodeURIComponent(q.url.split('?')[0]));
      const inside = p => p === root || p.startsWith(root + path.sep);
      if (!inside(file)) { r.writeHead(403); r.end(); return; }
      file = fs.realpathSync(file);
      if (!inside(file)) { r.writeHead(403); r.end(); return; }
      if (fs.statSync(file).isDirectory()) file = fs.realpathSync(path.join(file, 'index.html'));
      if (!inside(file)) { r.writeHead(403); r.end(); return; }
      const st = fs.statSync(file);
      if (!st.isFile()) { r.writeHead(404); r.end(); return; }
      r.writeHead(200, { 'content-type': types[path.extname(file)] || 'application/octet-stream', 'last-modified': st.mtime.toUTCString(), 'content-length': st.size });
      if (q.method === 'HEAD') { r.end(); return; }
      const stream = fs.createReadStream(file); stream.on('error', () => r.destroy()); stream.pipe(r);
    } catch { r.writeHead(404); r.end(); }
  });
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(port, '127.0.0.1', resolve); });
  return { server, url: `http://127.0.0.1:${server.address().port}`, close: () => new Promise(resolve => { server.close(resolve); server.closeAllConnections(); }) };
}

export async function ready(page) {
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 30000 });
}

export async function fitView(page, width) {
  const view = await page.evaluate(() => {
    const c = document.getElementById('c');
    return { W: window.SIM?.VIEW?.W || c.width, H: window.SIM?.VIEW?.H || c.height };
  });
  if (!(view.W > 0 && view.H > 0)) throw new Error('Invalid game view dimensions');
  await page.setViewportSize({ width: width || view.W, height: Math.round((width || view.W) * view.H / view.W) });
  return view;
}
