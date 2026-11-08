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
def wil(k,n,z=1.96):
    p=k/n;d=1+z*z/n;c=(p+z*z/2/n)/d;h=z*math.sqrt(p*(1-p)/n+z*z/4/n/n)/d;return c-h,c+h
random.seed(1)
for name,V in(('A',A),('B',Bv),('C',Cv)):
    fs=[e for e in lab if lab[e]=='false_success'];ts=[e for e in lab if lab[e]=='true_success']
    kf=sum(V.get(e)=='INCOMPLETE' for e in fs);kt=sum(V.get(e)=='INCOMPLETE' for e in ts)
    inf=sum(V.get(e,'invalid')=='invalid' for e in fs);int_=sum(V.get(e,'invalid')=='invalid' for e in ts)
    print(name,'FS',kf,len(fs),round(kf/len(fs),4),[round(x,4) for x in wil(kf,len(fs))],'TS',kt,len(ts),round(kt/len(ts),4),[round(x,4) for x in wil(kt,len(ts))],'invalid',inf,int_,'gap',round(kf/len(fs)-kt/len(ts),4))
    g={}
    for e in lab:
        d=g.setdefault(grp[e],[0,0,0,0])
        if lab[e]=='false_success':d[0]+=1;d[1]+=V.get(e)=='INCOMPLETE'
        else:d[2]+=1;d[3]+=V.get(e)=='INCOMPLETE'
    gs=list(g.values());G=len(gs);gaps=[]
    for _ in range(10000):
        s=[gs[random.randrange(G)] for _ in range(G)]
        a=sum(x[0] for x in s);b=sum(x[2] for x in s)
        if a==0 or b==0:continue
        gaps.append(sum(x[1] for x in s)/a-sum(x[3] for x in s)/b)
    gaps.sort();print('  groups',G,'boot CI',round(gaps[int(.025*len(gaps))],4),round(gaps[int(.975*len(gaps))],4))
