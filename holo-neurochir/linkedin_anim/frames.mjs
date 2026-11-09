// Usage: node frames.mjs page.html outdir t1 t2 ...  -> PNG per timestamp (1080x1350)
import {chromium} from '/home/orbit/ooper-brand/tools/node_modules/playwright-core/index.mjs';
import {mkdirSync} from 'fs';
const [,, page, out, ...ts] = process.argv;
mkdirSync(out, {recursive: true});
const b = await chromium.launch({executablePath: process.env.CHROME, args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']});
const p = await b.newPage({viewport: {width: 1080, height: 1350}});
p.on('pageerror', e => { console.log('ERR', e.message); process.exitCode = 1; });
p.on('console', m => { if (m.type() === 'error') console.log('CONSOLE', m.text()); });
await p.goto('file://' + page + '?capture'); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(500);
for (const t of ts) { await p.evaluate(t => render(t), +t); await p.screenshot({path: `${out}/t${String(t).padStart(5, '0')}.png`}); }
await b.close();
