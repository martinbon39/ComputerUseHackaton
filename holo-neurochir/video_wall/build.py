import json,os,base64,glob,subprocess,sys
W='/tmp/wall'
tiles=json.load(open(f'{W}/tiles.json'))
order=['f9584479','37608790','9f3f70fc','a10b69e1','8f080098','ed43c15f','1de60575','5df7b33a','7b7617bd','0b17a146','35253b65','deec51c9','70bca0cc','21ab7b40','982d12a5','5c1075ca']
tiles=sorted(tiles,key=lambda t:order.index(t['id']))
FR={}
def b64(p): return 'data:image/jpeg;base64,'+base64.b64encode(open(p,'rb').read()).decode()
for t in tiles:
    for k in ('A','B'):
        for f in t.get(k,[]): FR[f]=b64(f'{W}/f/{f}')
SUBS=json.load(open(f'{W}/vo/subs.json'))
lines=[dict(id=a,text=SUBS.get(a,b),oral=b) for a,b in json.load(open(f'{W}/vo/lines.json'))]
online=json.load(open(f'{W}/online.json')) if os.path.exists(f'{W}/online.json') else None
if online and online.get('line'): lines.insert([l['id'] for l in lines].index('v13'),dict(id='v12',text=online['line']))
GAP={'v03':1.0,'v06':1.0,'v08':0.8,'v09':0.8,'v16':0.8,'v15':0.6,'v17':0.6,'v14':2.4}
def dur(id,txt):
    p=f'{W}/vo/{id}.wav'
    if os.path.exists(p) and os.path.getsize(p)>1000:
        return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',p]).decode())
    return len(txt)/15.5
    # oral text drives the estimate
# scene minimum lengths: phase A needs the long replays (~40 s) to finish
tl={};t=1.2
MIN_START={'v06':None}
for l in lines:
    t+=GAP.get(l['id'],0.45)
    if l['id']=='v06': t=max(t,tl['v03'][0]+29)
    if l['id']=='v09': t=max(t,tl['v08'][0]+18)
    d=dur(l['id'],l.get('oral',l['text'])); tl[l['id']]=[round(t,2),round(t+d,2)]; t+=d
tl['_total']=round(t+3.5,2)
DUEL=None
dp=f'{W}/duel.json'
if os.path.exists(dp):
    DUEL=json.load(open(dp))
    for side in ('left','right'):
        for f in DUEL[side]: FR[f]=b64(f'{W}/d/{f}')
audio=''
if os.path.exists(f'{W}/vo/narration.mp3') and '--audio' in sys.argv: audio='data:audio/mpeg;base64,'+base64.b64encode(open(f'{W}/vo/narration.mp3','rb').read()).decode()
for t in tiles:
    for k in ('el',): t.pop(k,None)
h=open(f'{W}/template.html').read()
rep={'/*TILES*/null':json.dumps(tiles,ensure_ascii=False),'/*FRAMES*/null':json.dumps(FR),'/*TL*/null':json.dumps(tl),'/*LINES*/null':json.dumps(lines,ensure_ascii=False),
 '/*ONLINE*/null':json.dumps(online,ensure_ascii=False),'/*DUEL*/null':json.dumps(DUEL,ensure_ascii=False),'/*LIVEURL*/""':json.dumps(open(f'{W}/liveurl.txt').read().strip() if os.path.exists(f'{W}/liveurl.txt') else ''),'/*AUDIO*/""':json.dumps(audio),'/*PAPER*/""':json.dumps('data:image/jpeg;base64,'+base64.b64encode(open(f'{W}/paper0.jpg','rb').read()).decode())}
for a,b in rep.items():
    assert a in h,a; h=h.replace(a,b)
out=sys.argv[1] if len(sys.argv)>1 and not sys.argv[1].startswith('--') else f'{W}/wall.html'
open(out,'w').write(h); json.dump(tl,open(f'{W}/timeline.json','w'))
print(out,len(h)//1024,'KB total',tl['_total'],{k:v for k,v in tl.items() if k!='_total'})
