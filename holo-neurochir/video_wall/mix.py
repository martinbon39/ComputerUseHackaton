import json,subprocess,os
W='/tmp/wall';tl=json.load(open(f'{W}/timeline.json'));total=tl.pop('_total')
ins=[];fl=[];i=0
for k,(a,b) in sorted(tl.items(),key=lambda x:x[1][0]):
    p=f'{W}/vo/{k}.wav'
    if not os.path.exists(p): print('missing',k); continue
    ins+=['-i',p]; fl.append(f'[{i}:a]aresample=48000,adelay={int(a*1000)}|{int(a*1000)}[a{i}]'); i+=1
fc=';'.join(fl)+';'+''.join(f'[a{j}]' for j in range(i))+f'amix=inputs={i}:normalize=0,apad,atrim=0:{total},loudnorm=I=-16:TP=-1.5[out]'
subprocess.run(['ffmpeg','-y','-loglevel','error',*ins,'-filter_complex',fc,'-map','[out]','-ar','48000',f'{W}/vo/narration.wav'],check=True)
subprocess.run(['ffmpeg','-y','-loglevel','error','-i',f'{W}/vo/narration.wav','-b:a','96k',f'{W}/vo/narration.mp3'],check=True)
print('mixed',i,'lines, total',total)
