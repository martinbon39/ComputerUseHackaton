// Usage: node capture.mjs page.html out.mp4 [fps]  -> deterministic frame-by-frame render of render(t), H.264 yuv420p, faststart
import {chromium} from '/home/orbit/ooper-brand/tools/node_modules/playwright-core/index.mjs';
import {spawn} from 'child_process';
const [,, page, out, fpsArg] = process.argv;
const fps = +fpsArg || 30;
const b = await chromium.launch({executablePath: process.env.CHROME, args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']});
const p = await b.newPage({viewport: {width: 1080, height: 1350}});
p.on('pageerror', e => { console.log('ERR', e.message); process.exitCode = 1; });
await p.goto('file://' + page + '?capture'); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(500);
const total = await p.evaluate(() => TOTAL);
const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
  '-vf', 'scale=in_range=pc:out_range=tv,format=yuv420p', '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-maxrate', '12M', '-bufsize', '24M', '-profile:v', 'high', '-color_range', 'tv', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-r', String(fps), '-movflags', '+faststart', out], {stdio: ['pipe', 'inherit', 'inherit']});
const n = Math.round(total * fps);
for (let i = 0; i < n; i++) {
  await p.evaluate(t => render(t), i / fps);
  const buf = await p.screenshot({type: 'jpeg', quality: 96});
  if (i % 150 === 0) console.log(i, '/', n);
  if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
}
ff.stdin.end(); await new Promise(r => ff.on('close', r)); await b.close(); console.log('done', n, 'frames');
