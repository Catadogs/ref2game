// Interaction checks: --scenario FILE or repeatable --assert JS; --smoke explicitly permits no assertions.
// Legacy --keys/--shots/--eval remain available. --minfps is optional, separate from functional acceptance.
import fs from 'node:fs'; import path from 'node:path';
import { launchBrowser, serve, ready, fitView } from './runtime.mjs';
const args = process.argv.slice(2), opt = (k, d) => { const i = args.indexOf('--' + k); return i >= 0 ? args[i + 1] : d; };
const values = k => args.filter((_, i) => args[i - 1] === '--' + k);
const out = opt('out', 'frames/livecheck'); fs.mkdirSync(out, { recursive: true });
const report = { errors: [], assertions: [], evals: [], shots: [], reload: null, functional: 'not_tested' };
let browser, server;
async function assertion(page, expression, label = expression) {
  try {
    await page.waitForFunction(expression => { try { return (0, eval)(expression) === true; } catch { return false; } }, expression, { timeout: +opt('timeout', 5000) });
    report.assertions.push({ label, status: 'passed' });
  } catch (e) { report.assertions.push({ label, status: 'failed', error: e.message }); }
}
async function point(page, x, y) {
  return page.evaluate(([x, y]) => { const c = document.getElementById('c'), r = c.getBoundingClientRect(); return [r.left + x / c.width * r.width, r.top + y / c.height * r.height]; }, [x, y]);
}
async function action(page, a) {
  if (a.expect !== undefined) return assertion(page, a.expect, a.label);
  if (a.wait !== undefined) return page.waitForTimeout(a.wait);
  if (a.key) {
    if (!['press', 'down', 'up'].includes(a.action || 'press')) throw new Error('Unknown key action');
    return page.keyboard[a.action || 'press'](a.key);
  }
  if (a.click || a.move || a.down) {
    const [x, y] = await point(page, ...(a.click || a.move || a.down));
    if (a.click) return page.mouse.click(x, y);
    await page.mouse.move(x, y); if (a.down) await page.mouse.down(); return;
  }
  if (a.up) return page.mouse.up();
  if (a.wheel !== undefined) return page.mouse.wheel(0, a.wheel * 100);
  throw new Error('Unknown scenario action: ' + JSON.stringify(a));
}
try {
  let url = opt('url');
  if (!url) { server = await serve(); url = server.url + '/live/index.html'; }
  browser = await launchBrowser();
  const p = await browser.newPage();
  p.on('pageerror', e => report.errors.push(e.message));
  p.on('console', m => { if (m.type() === 'error') report.errors.push(m.text()); });
  await p.goto(url); await p.evaluate(() => sessionStorage.clear()); await p.reload(); await ready(p);
  report.view = await fitView(p, +opt('vw', 1280));
  if (opt('scenario')) {
    const scenario = JSON.parse(fs.readFileSync(opt('scenario'), 'utf8').replace(/^\uFEFF/, ''));
    if (!Array.isArray(scenario.steps) || !scenario.steps.length) throw new Error('Scenario must have nonempty steps');
    for (const step of scenario.steps) await action(p, step);
  } else {
    const events = opt('keys', 'ArrowRight:down@0, ArrowRight:up@1.5').split(',').map(s => s.trim()).filter(Boolean).map(s => {
      const m = /^([^:]+):([^@]+)@([0-9.]+)$/.exec(s);
      if (!m) throw new Error('Bad key timeline event: ' + s);
      const [, key, act, at] = m; let a;
      if (['Click', 'Move', 'Down'].includes(key)) a = { [{ Click: 'click', Move: 'move', Down: 'down' }[key]]: act.split('x').map(Number) };
      else if (key === 'Up') a = { up: true }; else if (key === 'Wheel') a = { wheel: +act }; else a = { key, action: act };
      return { at: +at, a };
    });
    const shots = opt('shots', '1,2.5').split(',').filter(Boolean).map(Number).map(at => ({ at, shot: true }));
    const start = Date.now();
    for (const e of [...events, ...shots].sort((a, b) => a.at - b.at)) {
      const delay = e.at * 1000 - (Date.now() - start); if (delay > 0) await p.waitForTimeout(delay);
      if (e.shot) { const f = path.join(out, `play_${e.at.toFixed(2)}.png`); await p.screenshot({ path: f }); report.shots.push(f); }
      else await action(p, e.a);
    }
    const remaining = +opt('for', 0) * 1000 - (Date.now() - start); if (remaining > 0) await p.waitForTimeout(remaining);
  }
  for (const expression of values('assert')) await assertion(p, expression);
  for (const expression of values('eval')) report.evals.push(await p.evaluate(expression => { try { return (0, eval)(expression); } catch (e) { return { error: e.message }; } }, expression));
  if (args.includes('--reload')) {
    if (!opt('reload-fields')) throw new Error('--reload requires --reload-fields field1,field2 (stable gameplay fields)');
    await p.waitForFunction(() => window.__reloadWatchReady === true);
    const paused = await p.evaluate(() => window.__REF2GAME_TEST__?.snapshot().paused);
    if (paused === undefined) throw new Error('Reload verification needs the template snapshot hook');
    if (!paused) await p.keyboard.press('KeyP');
    const fields = opt('reload-fields').split(',');
    const snapshot = () => p.evaluate(fields => {
      if (!SCENE.state) throw new Error('No active play state');
      const result = {};
      for (const k of fields) { if (!(k in SCENE.state)) throw new Error('Missing reload field: ' + k); result[k] = SCENE.state[k]; }
      return JSON.stringify(result);
    }, fields);
    const before = await snapshot();
    await p.evaluate(() => { window.__reloadProbe = true; });
    const loaded = p.waitForEvent('load', { timeout: 10000 });
    const file = path.join(process.cwd(), 'live/sim.js'), stat = fs.statSync(file);
    // Monotonic timestamp makes second-resolution HTTP Last-Modified change reliably.
    fs.utimesSync(file, stat.atime, new Date(Math.max(Date.now(), stat.mtimeMs) + 2000));
    await loaded; await ready(p);
    const after = await snapshot(), navigation = await p.evaluate(() => window.__reloadProbe === undefined);
    const passed = navigation && before === after;
    report.reload = { before: JSON.parse(before), after: JSON.parse(after), navigation, status: passed ? 'passed' : 'failed' };
    report.assertions.push({ label: 'reload preserves selected state', status: report.reload.status });
    if (!paused) await p.keyboard.press('KeyP');
  }
  report.performance = await p.evaluate(() => new Promise(resolve => {
    const intervals = []; let last = performance.now(); const start = last;
    const frame = now => { intervals.push(now - last); last = now; if (now - start < 1000) requestAnimationFrame(frame); else { intervals.sort((a,b) => a-b); resolve({ fps: intervals.length * 1000 / (now - start), p95ms: intervals[Math.floor(intervals.length * .95)] }); } }; requestAnimationFrame(frame);
  }));
  if (opt('minfps') && report.performance.fps < +opt('minfps')) report.errors.push('FPS below requested threshold');
  report.browser = browser.version();
  report.functional = !report.assertions.length ? 'not_tested' : report.assertions.some(a => a.status === 'failed') ? 'failed' : 'passed';
  if (!report.assertions.length && !args.includes('--smoke')) report.errors.push('No behavior assertions; provide --scenario/--assert or explicitly use --smoke');
  const f = path.join(out, 'final.png'); await p.screenshot({ path: f }); report.shots.push(f);
} catch (e) { report.errors.push(e.message); }
finally {
  if (browser) await browser.close(); if (server) await server.close();
  report.status = report.errors.length || report.functional === 'failed' ? 'failed' : 'passed';
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report)); process.exitCode = report.status === 'failed' ? 2 : 0;
}
