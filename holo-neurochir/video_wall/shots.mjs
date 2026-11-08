import {chromium} from '/home/orbit/ooper-brand/tools/node_modules/playwright-core/index.mjs';
const [,,page,...ts]=process.argv;
const b=await chromium.launch({executablePath:process.env.CHROME});const p=await b.newPage({viewport:{width:1920,height:1080}});
p.on('pageerror',e=>console.log('ERR',e.message));
await p.goto('file://'+page+'?capture');await p.waitForTimeout(1500);await p.evaluate(()=>document.fonts.ready);
for(const t of ts){await p.evaluate(t=>render(t),+t);await p.waitForTimeout(150);await p.screenshot({path:`/tmp/wall/shot_${t}.jpg`,type:'jpeg',quality:80});}
await b.close();
