import json,glob,os,sys
from PIL import Image
did=sys.argv[1]; D=f'/home/orbit/osw/duels/{did}'; O='/tmp/wall/d'; os.makedirs(O,exist_ok=True)
def frames(s): return sorted(glob.glob(f'{D}/{s}/frames/live_*.jpg'))+sorted(glob.glob(f'{D}/{s}/frames/final_*.jpg'))
def verdict(s):
    v=None
    for l in open(f'{D}/{s}/events.jsonl'):
        e=json.loads(l)
        if e['kind']=='verdict': v=e
    return v
L,R=frames('left'),frames('right'); n=max(len(L),len(R)); N=40
out={'left':[],'right':[]}
for side,fs in (('left',L),('right',R)):
    for i in range(N):
        k=min(len(fs)-1,round(i*(n-1)/(N-1)))
        dst=f'{side}_{did[:15]}_{i:02d}.jpg'
        if not os.path.exists(f'{O}/{dst}'): Image.open(fs[k]).convert('RGB').resize((768,432)).save(f'{O}/{dst}',quality=72)
        out[side].append(dst)
vl,vr=verdict('left'),verdict('right')
def res(v):
    g=v.get('guard') or {}
    s=f"official score {v['score']:.0f}"
    if g: s=f"Guard refused {g.get('refusals',0)}× → "+('agent repaired → ' if v['claimed_done'] and v['score']>=1 else ('said “done” · ' if v['claimed_done'] else 'no false “done” · '))+s
    else: s=('said “done” · ' if v['claimed_done'] else '')+s+(' · FALSE DONE' if v['claimed_done'] and v['score']<1 else '')
    return s
ts=[json.loads(l)['t'] for s_ in ('left','right') for l in open(f'{D}/{s_}/events.jsonl')]
real=max(ts)-min(ts); dur=float(os.environ.get('DUELDUR','18'))
m=json.load(open(f'{D}/meta.json'))
out.update(dur=dur,lres=res(vl),rres=res(vr),rok=vr['score']>=1,src=f"recorded duel {did[:8]} {did[9:11]}:{did[11:13]} UTC · task {m['task']} · ~{real/60:.0f} min shown in {dur:.0f} s (×{real/dur:.0f}) · ~/osw/duels/{did}")
out['kicker']='ONLINE-EVAL DUEL · BELOW: REPLAY ×%d · RECORDED LIVE 11:00 UTC ON REAL VMs · THE BUTTON STARTS A NEW RUN'%round(real/dur)
json.dump(out,open('/tmp/wall/duel.json','w'),ensure_ascii=False)
print(out['lres'],'|',out['rres'],'|',out['src'])
