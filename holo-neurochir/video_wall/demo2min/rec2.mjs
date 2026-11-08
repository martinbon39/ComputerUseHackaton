import {chromium} from '/home/orbit/ooper-brand/tools/node_modules/playwright-core/index.mjs';
import fs from 'fs';
const T='https://profession-april-suzuki-seed.trycloudflare.com';
const COCK='https://argos.martinbonan.com/artifacts/holo-cockpit-pitch.html?t=mxemuebq._4LiqnCtUVOTDlWvqXemntf6MOMSBAh4';
const key=fs.readFileSync('/home/orbit/.duel_key','utf8').trim();
const log=(...a)=>{const s=new Date().toISOString().slice(11,19)+' '+a.join(' ');console.log(s);fs.appendFileSync('/tmp/wall/live/marks.txt',s+'\n')};
const b=await chromium.launch({executablePath:process.env.CHROME});
const c0=await b.newContext();const p0=await c0.newPage();await p0.goto(T+'/?k='+key);await p0.waitForTimeout(2500);
const st=await c0.storageState();await c0.close();log('cookie ok',st.cookies.length);
const ctx=await b.newContext({viewport:{width:1920,height:1080},recordVideo:{dir:'/tmp/wall/live/',size:{width:1920,height:1080}},storageState:st});
await ctx.addInitScript(()=>{addEventListener('DOMContentLoaded',()=>{const d=document.createElement('div');d.id='__cur';d.style.cssText='position:fixed;z-index:2147483647;width:22px;height:22px;border-radius:50%;background:rgba(20,20,20,.55);border:2px solid #fff;pointer-events:none;left:-50px;top:-50px;transform:translate(-50%,-50%);transition:transform .08s';document.body.appendChild(d);addEventListener('mousemove',e=>{d.style.left=e.clientX+'px';d.style.top=e.clientY+'px'});addEventListener('mousedown',()=>d.style.transform='translate(-50%,-50%) scale(.7)');addEventListener('mouseup',()=>d.style.transform='translate(-50%,-50%)')})});
const p=await ctx.newPage();const t0=Date.now();const mark=n=>log('MARK',n,((Date.now()-t0)/1000).toFixed(1));
async function clickEl(sel){const bb=await p.locator(sel).first().boundingBox();await p.mouse.move(bb.x+bb.width/2,bb.y+bb.height/2,{steps:25});await p.waitForTimeout(300);await p.mouse.down();await p.waitForTimeout(90);await p.mouse.up();}
await p.goto(COCK);await p.mouse.move(960,700);mark('cockpit');await p.waitForTimeout(5000);
await p.evaluate(()=>{const a=document.querySelector('a.run');if(a)a.removeAttribute('target')});
mark('click_watch');await clickEl('a.run');await p.waitForLoadState('domcontentloaded');mark('replay_page');
await p.mouse.move(1500,900,{steps:20});await p.waitForTimeout(66000);mark('replay_end');await p.waitForTimeout(6000);mark('stop');
await ctx.close();await b.close();log('saved');
