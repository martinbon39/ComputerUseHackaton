import json,subprocess
W='/tmp/wall/v2m'
order=[('W1',None),('L1',None),('L2','≥×8 · REPLAY'),('L3','≥×4 · REPLAY'),('W2',None),('W3',None),('INF',None),('CON',None),('END',None)]
def dur(p): return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',p]))
t=0;starts={};marks=[]
for n,m in order:
    d=dur(f'{W}/seg/{n}.mp4');starts[n]=(t,t+d)
    if m: marks.append((t,t+d,m))
    t+=d
total=t
S=starts
VO=[('n01',S['W1'][0]+0.4,"Computer-use agents have a bad habit. They say “done”. And it's not done."),
('n02',None,"For Holo-3.1, that's 29 of its 51 failures."),
('n03',S['L1'][0]+0.3,"So we built Feci Guard: an outside judge that checks the screen before the agent is allowed to stop. Let's watch the duel."),
('n04',S['L2'][0]+0.2,"Same task, two real virtual machines. Left: Holo alone. Right: Holo + Feci Guard."),
('n05',S['L3'][0]+3.2,"Left says “done”. Official score: 0."),
('n06',None,"Right says “done” too. Claude checks every requirement on the screen: wrong sheet name, promotions in rows, not columns. Refused. The agent fixes both. Score: 1."),
('n07',S['W2'][0]+0.5,"And it's not one lucky run. 16 real sessions. Orange = a false “done”. The Guard refuses, with the reason, in ~6 s."),
('n08',S['W3'][0]+0.6,"Or the refused task is handed to the bigger Holo4. Green = repaired."),
('n09',S['CON'][0]+0.4,"The numbers, preregistered. Online, 120 tasks: false “done” 22.5 % → 10.8 %. Significant."),
('n10',None,"With Holo4 as the repairer (replay): 11 of 18 solved, vs 2 without the Guard."),
('n11',S['END'][0]+0.3,"Feci Guard. The agent says “done”. Now, someone checks.")]
tl=[];prev=0
for id,at,txt in VO:
    d=dur(f'{W}/vo/{id}.wav')
    if at is None or at<prev+0.25: at=prev+0.3 if at is None else prev+0.25
    tl.append((id,at,at+d,txt));prev=at+d
total=max(total,prev+0.6)
print('total',round(total,2));[print(x[0],round(x[1],2),round(x[2],2)) for x in tl];print(starts)
def ts(x):
    h=int(x//3600);m=int(x%3600//60);s=x%60;return f"{h}:{m:02d}:{s:05.2f}"
ass="""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Inter,40,&H00171717,&H00171717,&H10FAFAFA,&H00000000,0,0,0,0,100,100,0,0,3,14,0,2,160,160,36,1
Style: Mark,Inter,36,&H00FFFFFF,&H00FFFFFF,&H000F57E4,&H00000000,1,0,0,0,100,100,1,0,3,12,0,9,60,60,60,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
for id,a,b,txt in tl: ass+=f"Dialogue: 0,{ts(a)},{ts(b+0.25)},Sub,,0,0,0,,{txt}\n"
for a,b,m in marks: ass+=f"Dialogue: 1,{ts(a)},{ts(b)},Mark,,0,0,0,,{m}\n"
open(f'{W}/subs.ass','w').write(ass)
ins=[];fl=[]
for i,(id,a,b,txt) in enumerate(tl):
    ins+=['-i',f'{W}/vo/{id}.wav'];fl.append(f'[{i}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(a*1000)}|{int(a*1000)}[a{i}]')
fc=';'.join(fl)+';'+''.join(f'[a{i}]' for i in range(len(tl)))+f'amix=inputs={len(tl)}:normalize=0,apad,atrim=0:{total:.2f},loudnorm=I=-16:TP=-1.5[o]'
subprocess.run(['ffmpeg','-y','-loglevel','error',*ins,'-filter_complex',fc,'-map','[o]','-ar','48000',f'{W}/vo.wav'],check=True)
open(f'{W}/concat.txt','w').write(''.join(f"file '{W}/seg/{n}.mp4'\n" for n,_ in order))
json.dump(dict(total=total,tl=tl,starts=starts),open(f'{W}/plan.json','w'),ensure_ascii=False)
