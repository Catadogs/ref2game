import { launchBrowser } from './runtime.mjs';
let browser;
try { browser = await launchBrowser(); console.log(JSON.stringify({ browser: browser.version(), status: 'passed' })); }
catch (e) { console.error(e.message); process.exitCode = 1; }
finally { if (browser) await browser.close(); }
