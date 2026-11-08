import json,subprocess,base64,os,tempfile
H=os.path.expanduser('~/osw')
R={'o':'results_test_gh_orig_modal_test/pyautogui/screenshot/Holo-3.1-4B-modal-orig','m':'results_test_gh_merge_cua_b050/pyautogui/screenshot/Holo-3.1-4B-merge_cua_b050'}
PAIRS=[('libreoffice_impress/b8adbc24-cef2-4b15-99d5-ecbe7ff445eb','Impress'),('chrome/9f935cce-0a9f-435f-8007-817732bfc0a5','Chrome'),('os/bedcedc4-4d72-425e-ad62-21960b11fe0d','Système')]
tmp=tempfile.mkdtemp()
def img(p):
    o=os.path.join(tmp,'x.jpg')
    subprocess.run(['ffmpeg','-y','-loglevel','error','-i',p,'-vf','scale=960:-2','-q:v','6',o],check=True)
    return 'data:image/jpeg;base64,'+base64.b64encode(open(o,'rb').read()).decode()
def act(tc):
    t=tc['tool_name']
    if t=='click': return f"click — {tc.get('element','')} ({tc['x']}, {tc['y']})"
    if t=='write': return f"write — « {tc['content']} »"
    if t=='hotkey': return "hotkey — "+"+".join(tc['keys'])
    if t=='scroll': return f"scroll {tc['direction']} ({tc['x']}, {tc['y']})"
    if t=='wait': return f"wait {tc['seconds']} s"
    if t=='answer': return "answer — « "+tc['content']+" »"
    return t
def load(k,d):
    base=f'{H}/{R[k]}/{d}'
    score=float(open(base+'/result.txt').read().strip())
    steps=[]
    for l in open(base+'/traj.jsonl'):
        j=json.loads(l)
        steps.append(dict(n=j['step_num'],note=j['note'],thought=j['thought'],action=act(j['tool_call']),answer=j['tool_name']=='answer',img=img(f"{base}/{j['screenshot_file']}")))
    return dict(score=int(score),steps=steps)
data=[]
for d,lab in PAIRS:
    ins=json.load(open(f'{H}/rtg/Env/OSWorld/evaluation_examples/examples/{d}.json'))['instruction']
    data.append(dict(label=lab,instruction=ins,o=load('o',d),m=load('m',d)))
    assert data[-1]['o']['score']==0 and data[-1]['m']['score']==1
html=open('template.html').read().replace('/*DATA*/null',json.dumps(data,ensure_ascii=False))
open('demo_faux_fini.html','w').write(html)
print(len(html)/1e6,'MB')
