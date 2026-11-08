import json,subprocess
W='/tmp/wall/v2m';V='/tmp/wall/v3'
segs=[('W1',f'{W}/seg/W1.mp4',None),('PAPER',f'{V}/PAPER.mp4','PAPER · main.pdf, real pages'),('GH',f'{V}/GH.mp4','github.com/martinbon39/ComputerUseHackaton'),('TERM',f'{V}/TERM.mp4','real run · jury_kit/quickstart.sh'),
('L1',f'{V}/L1.mp4','screen recording · cockpit → duel page'),('L2',f'{W}/seg/L2.mp4','≥×8 · REPLAY'),('L3',f'{V}/L3.mp4','≥×4 · REPLAY'),('CON',f'{W}/seg/CON.mp4',None),('END',f'{W}/seg/END.mp4',None)]
def dur(p): return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',p]))
t=0;S={};marks=[]
for n,p,m in segs:
    d=dur(p);S[n]=(t,t+d)
    if m: marks.append((t,t+d,m))
    t+=d
total=t
VO=[('n01',S['W1'][0]+0.3,"Computer-use agents have a bad habit. They say “done”. And it's not done."),
('n02',None,"For Holo-3.1, that's 29 of its 51 failures."),
('p21',S['PAPER'][0]+0.2,"We wrote it all up in a 30-page paper. First question: can we fix this inside the model?"),
('p22',None,"We probed activations, steered them, merged weights, and tried ~15 edits, including AlphaEdit, a closed-form weight edit."),
('p23',None,"A real causal lever, but a blind one. AlphaEdit cuts false successes from 15/16 to 8/16. It also cuts true ones, from 15/16 to 3/16."),
('p24',None,"Online, the weight merge gives +1.9 pts, interval [−4.3, +8.0]. No gain."),
('p25',None,"Diagnosis: the model does not know when its own “done” is false. So the check has to come from outside."),
('p26',S['GH'][0]+0.2,"Everything is public: code, data, and the raw journal of the night. One script re-checks the headline numbers offline."),
('p27',S['L1'][0]+0.2,"So we built Feci Guard, an outside judge. Same task, two real virtual machines: Holo alone, and Holo with the Guard."),
('n05',None,"Left says “done”. Official score: 0."),
('n06',None,"Right says “done” too. Claude checks every requirement on the screen: wrong sheet name, promotions in rows, not columns. Refused. The agent fixes both. Score: 1."),
('n09',S['CON'][0]+0.3,"The numbers, preregistered. Online, 120 tasks: false “done” 22.5 % → 10.8 %. Significant."),
('n10',None,"With Holo4 as the repairer (replay): 11 of 18 solved, vs 2 without the Guard."),
('n11',S['END'][0]+0.3,"Feci Guard. The agent says “done”. Now, someone checks.")]
tl=[];prev=0
for id,at,txt in VO:
    d=dur(f'{W}/vo/{id}.wav')
    if at is None or at<prev+0.2: at=prev+0.25
    tl.append((id,at,at+d,txt));prev=at+d
total=max(total,prev+0.5)
print('total',round(total,2));[print(x[0],round(x[1],2),round(x[2],2)) for x in tl];print({k:(round(a,1),round(b,1)) for k,(a,b) in S.items()})
def ts(x): return f"{int(x//3600)}:{int(x%3600//60):02d}:{x%60:05.2f}"
ass=open(f'{W}/subs.ass').read().split('[Events]')[0]+"""[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
for id,a,b,txt in tl: ass+=f"Dialogue: 0,{ts(a)},{ts(b+0.2)},Sub,,0,0,0,,{txt}\n"
for a,b,m in marks: ass+=f"Dialogue: 1,{ts(a)},{ts(b)},Mark,,0,0,0,,{m}\n"
open(f'{V}/subs.ass','w').write(ass)
ins=[];fl=[]
for i,(id,a,b,txt) in enumerate(tl):
    ins+=['-i',f'{W}/vo/{id}.wav'];fl.append(f'[{i}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(a*1000)}|{int(a*1000)}[a{i}]')
fc=';'.join(fl)+';'+''.join(f'[a{i}]' for i in range(len(tl)))+f'amix=inputs={len(tl)}:normalize=0,apad,atrim=0:{total:.2f},loudnorm=I=-16:TP=-1.5[o]'
subprocess.run(['ffmpeg','-y','-loglevel','error',*ins,'-filter_complex',fc,'-map','[o]','-ar','48000',f'{V}/vo.wav'],check=True)
open(f'{V}/concat.txt','w').write(''.join(f"file '{p}'\n" for n,p,m in segs))
