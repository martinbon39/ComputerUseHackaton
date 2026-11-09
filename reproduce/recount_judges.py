#!/usr/bin/env python3
"""Row 2 and row 7 of the README: recount the three judges (A = Holo-3.1-4B judging itself, B = Holo4-27B,
C = Claude Sonnet with the Feci Guard prompt) on the same 268 labelled final screens from their raw recorded
responses. Standard library only. A copy of experiments/judge_bench/independent_recompute.py (the independent
recount) with relative paths, plus checks against the published numbers; exit 1 on mismatch.
"""
RES={}
import json,re,random,math
B=str(__import__('pathlib').Path(__file__).resolve().parent.parent/'experiments')+'/'
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
    RES[name]=(kf,len(fs),kt,len(ts))
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
    gaps.sort();RES[name]+=(round(100*gaps[int(.025*len(gaps))]),round(100*gaps[int(.975*len(gaps))]));print('  groups',G,'boot CI',round(gaps[int(.025*len(gaps))],4),round(gaps[int(.975*len(gaps))],4))

EXPECTED={'A':(35,66,97,202,-13,23),'B':(31,66,63,202,-3,33),'C':(45,66,21,202,41,74)}
NAMES={'A':'Holo-3.1-4B (self-judge)','B':'Holo4-27B','C':'Claude Sonnet (Feci Guard)'}
print('\njudge                         detected      wrongly rejected   gap CI95 (task bootstrap, pts)')
bad=0
for k,e in EXPECTED.items():
    g=RES[k]; ok=g[:4]==e[:4] and abs(g[4]-e[4])<=2 and abs(g[5]-e[5])<=2; bad+=not ok
    print(f"{'OK ' if ok else 'BAD'} {NAMES[k]:<27} {g[0]}/{g[1]:<10} {g[2]}/{g[3]:<15} [{g[4]:+d}, {g[5]:+d}]  published [{e[4]:+d}, {e[5]:+d}]")
print('268 episodes from 90 tasks; the bootstrap resamples tasks. Counts must match exactly; the CI bounds within 2 pts')
print('(this recount uses its own seed, the published CIs come from judge_bench/analyze.py).')
raise SystemExit(1 if bad else 0)
