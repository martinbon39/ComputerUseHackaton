import {chromium} from '/home/orbit/ooper-brand/tools/node_modules/playwright-core/index.mjs';
import {spawn} from 'child_process';
const [,, page, audio, out]=process.argv;const fps=25;
const b=await chromium.launch({executablePath:process.env.CHROME});const p=await b.newPage({viewport:{width:1920,height:1080}});
p.on('pageerror',e=>console.log('ERR',e.message));
await p.goto('file://'+page+'?capture');await p.waitForTimeout(1500);await p.evaluate(()=>document.fonts.ready);
const total=await p.evaluate(()=>TOTAL);
const ff=spawn('ffmpeg',['-y','-loglevel','error','-f','image2pipe','-framerate',String(fps),'-c:v','mjpeg','-i','-','-i',audio,'-c:v','libx264','-preset','medium','-crf','20','-pix_fmt','yuv420p','-r',String(fps),'-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',out],{stdio:['pipe','inherit','inherit']});
const n=Math.floor(total*fps);
for(let i=0;i<n;i++){await p.evaluate(t=>render(t),i/fps);const buf=await p.screenshot({type:'jpeg',quality:90,timeout:120000});if(i%500==0)console.log(i,'/',n);if(!ff.stdin.write(buf))await new Promise(r=>ff.stdin.once('drain',r));}
ff.stdin.end();await new Promise(r=>ff.on('close',r));await b.close();console.log('done',n);
