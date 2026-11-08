import {chromium} from '/home/orbit/ooper-brand/tools/node_modules/playwright-core/index.mjs';
import {spawn} from 'child_process';
const [,, page, segjson]=process.argv;const fps=25;const SEG=JSON.parse(segjson);
const b=await chromium.launch({executablePath:process.env.CHROME});const p=await b.newPage({viewport:{width:1920,height:1080}});
p.on('pageerror',e=>console.log('ERR',e.message));
await p.goto('file://'+page+'?capture');await p.waitForTimeout(1500);await p.evaluate(()=>document.fonts.ready);
await p.addStyleTag({content:'#sub{display:none!important}'});
for(const s of SEG){
 if(s.marker)await p.evaluate(m=>{document.getElementById('marker').innerHTML=m},s.marker);
 const out=`/tmp/wall/v2m/seg/${s.name}.mp4`;
 const ff=spawn('ffmpeg',['-y','-loglevel','error','-f','image2pipe','-framerate',String(fps),'-c:v','mjpeg','-i','-','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-r',String(fps),out],{stdio:['pipe','inherit','inherit']});
 const n=Math.round((s.t1-s.t0)/s.speed*fps);
 for(let i=0;i<n;i++){await p.evaluate(t=>render(t),s.t0+i/fps*s.speed);const buf=await p.screenshot({type:'jpeg',quality:90});if(!ff.stdin.write(buf))await new Promise(r=>ff.stdin.once('drain',r));}
 ff.stdin.end();await new Promise(r=>ff.on('close',r));console.log('seg',s.name,n);
}
await b.close();
