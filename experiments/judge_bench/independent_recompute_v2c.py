import json,re,random,math
B='/home/orbit/projects/ComputerUseHackaton/holo-neurochir/'
man=json.load(open(B+'verif_study/manifest.json'))
if isinstance(man,dict):
    for k in ('episodes','items','manifest'):
        if k in man: man=man[k];break
lab={e['episode_id']:e['label'] for e in man}
grp={e['episode_id']:(e['domain'],e['task_id']) for e in man}
print('manifest',len(man),len(lab),len(set(grp.values())))
pat=re.compile(r'VERDICT\s*["\']?\s*:\s*["\']?\s*(INCOMPLETE|COMPLETE)\b(\s*or\s*(COMPLETE|INCOMPLETE))?',re.I)
def parse(r):
    try:
        if r.get('status')!='ok':return 'invalid'
        ch=r['response']['choices'][0]
        if ch.get('finish_reason')!='stop':return 'invalid'
        c=re.sub(r'[*`_]','',ch['message'].get('content') or '')
    except Exception: return 'invalid'
    vs=set()
    for m in pat.finditer(c):
        if m.group(2):continue
        vs.add(m.group(1).upper())
    return vs.pop() if len(vs)==1 else 'invalid'
def jl(p): return [json.loads(l) for l in open(p) if l.strip()]
A={};n=0
for r in jl(B+'verif_study/responses.jsonl'):
    rid=r['request_id']
    if rid.endswith('__t0'):
        n+=1;A[rid[:-4]]=parse(r)
print('A t0 lines',n,'unique',len(A),'in manifest',len(set(A)&set(lab)))
Bv={};cnt=0
for r in jl(B+'judge_bench/holo4_responses.jsonl'):
    cnt+=1;Bv[r.get('episode_id') or r['request_id']]=parse(r)
print('B lines',cnt,len(Bv),set(Bv)==set(lab))
Cv={};cnt=0
for r in jl(B+'judge_bench/claude_responses.jsonl'):
    cnt+=1;x=r['result'];Cv[r['episode_id']]=x['verdict'].upper() if x.get('ok') and x.get('verdict') else 'invalid'
print('C lines',cnt,len(Cv),set(Cv)==set(lab))

Dv={};cnt=0
for r in jl(B+'judge_bench/holo4_feci_responses.jsonl'):
    cnt+=1;x=r['result'];Dv[r['episode_id']]=x['verdict'].upper() if x.get('ok') and x.get('verdict') else 'invalid'
print('D lines',cnt,len(Dv),set(Dv)==set(lab))
def wil(k,n,z=1.96):
    p=k/n;d=1+z*z/n;c=(p+z*z/2/n)/d;h=z*math.sqrt(p*(1-p)/n+z*z/4/n/n)/d;return c-h,c+h
fs=[e for e in lab if lab[e]=='false_success'];ts=[e for e in lab if lab[e]=='true_success']
def tab(V):
    g={}
    for e in lab:
        d=g.setdefault(grp[e],[0,0,0,0])
        if lab[e]=='false_success':d[0]+=1;d[1]+=V.get(e)=='INCOMPLETE'
        else:d[2]+=1;d[3]+=V.get(e)=='INCOMPLETE'
    return g
V={'A':A,'C':Cv,'D':Dv}
kf=sum(Dv[e]=='INCOMPLETE' for e in fs);kt=sum(Dv[e]=='INCOMPLETE' for e in ts)
print('D FS',kf,round(kf/66,4),[round(x,4) for x in wil(kf,66)],'TS',kt,round(kt/202,4),[round(x,4) for x in wil(kt,202)],'invalid',sum(Dv[e]=='invalid' for e in fs),sum(Dv[e]=='invalid' for e in ts),'gap',round(kf/66-kt/202,4))
keys=sorted(tab(A)); T={n:tab(v) for n,v in V.items()}
def gap(n,s):
    a=sum(T[n][k][0] for k in s);b=sum(T[n][k][2] for k in s)
    return sum(T[n][k][1] for k in s)/a-sum(T[n][k][3] for k in s)/b
random.seed(7);res={'D':[],'DA':[],'DC':[]}
for _ in range(10000):
    s=[keys[random.randrange(len(keys))] for _ in keys]
    gd=gap('D',s);res['D'].append(gd);res['DA'].append(gd-gap('A',s));res['DC'].append(gd-gap('C',s))
al=list(keys)
pt={'D':gap('D',al),'DA':gap('D',al)-gap('A',al),'DC':gap('D',al)-gap('C',al)}
for k,v in res.items():
    v.sort();print(k,'point',round(pt[k],4),'CI',round(v[250],4),round(v[9749],4))
