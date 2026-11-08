import json,os,glob,re,datetime
from PIL import Image
H='/home/orbit/projects/ComputerUseHackaton/holo-neurochir'; O='/home/orbit/osw'
OUT='/tmp/wall/f'; os.makedirs(OUT,exist_ok=True)
man={e['episode_id']:e for e in json.load(open(f'{H}/verif_study/manifest.json'))}
cl={json.loads(l)['episode_id']:json.loads(l)['result'] for l in open(f'{H}/judge_bench/claude_responses.jsonl')}
def ts(s):
    return datetime.datetime.strptime(s.split('@')[0]+s.split('@')[1][:6],'%Y%m%d%H%M%S')
def steps(d,upto=None):
    fs=sorted(glob.glob(d+'/step_*.png'),key=lambda p:int(re.search(r'step_(\d+)_',p).group(1)))
    if upto: fs=[f for f in fs if int(re.search(r'step_(\d+)_',f).group(1))<=upto]
    tr=[json.loads(l) for l in open(d+'/traj.jsonl') if l.strip()]
    if upto: tr=[t for t in tr if t['step_num']<=upto]
    sec=(ts(tr[-1]['timestamp'])-ts(tr[0]['timestamp'])).total_seconds() if len(tr)>1 else 0
    return fs,sec,tr
def sample(fs,n=14):
    if len(fs)<=n: return fs
    return [fs[round(i*(len(fs)-1)/(n-1))] for i in range(n)]
def save(fs,tid,ph):
    out=[]
    for i,f in enumerate(fs):
        p=f'{OUT}/{tid}_{ph}{i:02d}.jpg'
        if not os.path.exists(p):
            Image.open(f).convert('RGB').resize((640,360),Image.LANCZOS).save(p,quality=74)
        out.append(os.path.basename(p))
    return out
def gmeta(v): return dict(lat=v.get('latency_s'),model=v.get('model'),sha=(v.get('verifier_sha') or '')[:8],cost=v.get('cost_usd'))
def reqs(v): return [dict(r=q['requirement'],s=q['status'],e=q.get('evidence','')) for q in v.get('requirements',[])]
def instr(dom,task):
    p=f'{O}/rtg/Env/OSWorld/evaluation_examples/examples/{dom}/{task}.json'
    return json.load(open(p))['instruction']
tiles=[]
def detection(eid,kind):
    e=man[eid]; fs,sec,tr=steps(e['source_dir'])
    v=cl[eid]; tid=e['task_id'][:8]
    tiles.append(dict(id=tid,kind=kind,dom=e['domain'],task=e['task_id'],run=eid.split('__')[0],instr=e['instruction'],
        A=save(sample(fs),tid,'a'),secA=sec,nA=len(fs),answer=tr[-1].get('note','')[:200],scoreA=e['score'],
        g1=dict(verdict=v['verdict'],reqs=reqs(v),**gmeta(v),src='judge_bench/claude_responses.jsonl')))
for eid,k in [('diag1__libreoffice_calc__f9584479-3d0d-4c79-affa-9ad7afdd8850','caught'),('diag1__chrome__9f3f70fc-5afc-4958-a7b7-3bb4fcb01805','caught'),
 ('diag1__vlc__8f080098-ddb1-424c-b438-4e96e5e4786e','caught'),('diag2__libreoffice_impress__ed43c15f-00cb-4054-9c95-62c880865d68','caught'),
 ('diag1__multi_apps__5df7b33a-9f77-4101-823e-02f863e1c1ae','caught'),('extra2__chrome__35253b65-1c19-4304-8aa4-6884b8218fc0','caught'),
 ('diag2__multi_apps__deec51c9-3b1e-4b9e-993c-4776f20e8bb2','caught'),('diag1__libreoffice_calc__21ab7b40-77c2-4ae6-8321-e00d3a086c73','caught'),('diag1__os__5c1075ca-bb34-46a3-a7a0-029bd7463e79','missed'),
 ('diag2__gimp__7b7617bd-57cc-468e-9c91-40c4ec2bcb3d','falsereject'),('diag1__thunderbird__a10b69e1-6034-4a2b-93e1-571d45194f75','pass'),
 ('diag1__vs_code__982d12a5-beab-424f-8d38-d2a48429e511','pass')]:
    detection(eid,k)
# Holo-3.1 self-repair (feci_demo calc 1de60575, branch k0)
D=f'{O}/feci_demo/calc_1de60575'; fs,sec,tr=steps(D+'/recorded_original')
gj=[json.loads(l) for l in open(D+'/guard_branch_k0/guard.jsonl')]
nb=sorted(glob.glob(D+'/guard_branch_k0/frames/new_*.png'))+[D+'/guard_branch_k0/guard_step_17.png']
tiles.append(dict(id='1de60575',kind='repair',dom='libreoffice_calc',task='1de60575-bb6e-4c3d-9e6a-2fa699f9f197',run='diag1',instr=instr('libreoffice_calc','1de60575-bb6e-4c3d-9e6a-2fa699f9f197'),
  A=save(sample(fs),'1de60575','a'),secA=sec,nA=len(fs),answer=tr[-1].get('note','')[:200],scoreA=float(open(D+'/recorded_original/result.txt').read()),
  g1=dict(verdict=gj[0]['verifier']['verdict'],reqs=reqs(gj[0]['verifier']),**gmeta(gj[0]['verifier']),src='feci_demo/calc_1de60575/guard_branch_k0/guard.jsonl'),
  agentB='Holo-3.1-4B',B=save(nb,'1de60575','b'),g2=dict(verdict=gj[-1]['verifier']['verdict'],reqs=reqs(gj[-1]['verifier'])),
  scoreB=1.0,secB=189.3,nB=5,control='same replay without Guard: 0/2 (re-answers "done" at once)',src='feci_repair, branch k0'))
# Escalation to Holo4 (rescue_bench)
br=[json.loads(l) for f in glob.glob(f'{O}/rescue_bench/branches.s*.jsonl') for l in open(f)]
eps={l.split('/')[-1][:8]:l.strip() for l in open(f'{H}/rescue_bench/episodes.txt') if l.strip()}
for t,k in [('37608790',0),('70bca0cc',0),('0b17a146',0)]:
    src=eps[t]; dom=src.split('/')[-2]; task=src.split('/')[-1]
    b=[x for x in br if x['task'].endswith(task) and x['arm']=='guard' and x['k']==k][0]
    ctl=[x['score'] for x in br if x['task'].endswith(task) and x['arm']=='control']
    fs,sec,tr=steps(src,upto=b['recorded_steps'])
    d=f'{O}/rescue_bench/guard/{dom}_{task}_k{k}/attempt_1'
    gj=[json.loads(l) for l in open(d+'/guard.jsonl')]
    fr=sorted(glob.glob(d+'/frames/call_*.png'))
    tiles.append(dict(id=t,kind='escalate',dom=dom,task=task,run=src.split('/')[4].replace('results_',''),instr=instr(dom,task),
      A=save(sample(fs),t,'a'),secA=sec,nA=len(fs),answer=(b.get('gate') or {}).get('answer','')[:200],scoreA=b['recorded_score'],
      g1=dict(verdict=gj[0]['verifier']['verdict'],reqs=reqs(gj[0]['verifier']),**gmeta(gj[0]['verifier']),src=f'rescue_bench/guard/{dom}_{task}_k{k}'),
      agentB='Holo4-27B',B=save(sample(fr),t,'b'),secB=b['seconds'],nB=sum(1 for l in open(d+'/frames/calls.jsonl') if l.strip()),scoreB=b['score'],
      control=f'Holo4 without Guard, same boundary: {sum(1 for c in ctl if c>=1)}/{len(ctl)}',ctl=ctl,strict=b.get('strict_replay_valid')))
json.dump(tiles,open('/tmp/wall/tiles.json','w'),ensure_ascii=False,indent=1)
for t in tiles: print(t['id'],t['kind'],t['dom'],len(t['A']),round(t['secA']),t['scoreA'],t['g1']['verdict'],t.get('scoreB'),t.get('control',''))
