"""Hardware-only campaign continuation after authorization to pick unused GPUs.

Uses unchanged frozen plans, protocol, scoring and analysis. Weights are supplied
and verified separately; at most two worker slots run, and other jobs are never
terminated. The original GPU-6/7-only queue and runner remain preserved.
"""
from pathlib import Path
import argparse,fcntl,hashlib,json,os,subprocess,time,shutil

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def update(root,fn):
 ops=root/'operations'
 with (ops/'queue.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);p=ops/'queue.json';d=json.loads(p.read_text());v=fn(d)
  tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(d,indent=2)+'\n');os.replace(tmp,p);return v
def idle(gpu,uuid):
 rows=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True)
 row=next(x.split(', ') for x in rows.splitlines() if x.startswith(gpu+', '))
 if row[1]!=uuid:raise RuntimeError('GPU identity changed')
 apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid','--format=csv,noheader'],text=True)
 return uuid not in apps and float(row[2])<100 and float(row[3])<=5
def pick_gpu(root,allowed):
 for gpu,uuid in allowed.items():
  f=(root/'operations'/f'idle-gpu-{gpu}.lock').open('a+')
  try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:f.close();continue
  if idle(gpu,uuid):return gpu,uuid,f
  f.close()
 return None
def environment(root,gpu,uuid):
 e=os.environ.copy();e.update(OC=str(root),OC_PHYSICAL_GPU=gpu,CUDA_VISIBLE_DEVICES=uuid,CUDA_DEVICE_ORDER='PCI_BUS_ID',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',VLLM_WORKER_MULTIPROC_METHOD='spawn',CUDA_HOME='/usr/local/cuda')
 e['PATH']=str(root/'.venv/bin')+':/usr/local/cuda/bin:'+e.get('PATH','');return e
def run(root,cmd,log,env):
 with (root/'logs'/log).open('ab') as f:subprocess.run(cmd,cwd=root/'code',env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
def phase(root,model,name,gpu,uuid):
 code=root/'code';py=str(root/'.venv/bin/python');plan=code/('items/access-v2/model-plans/discovery-'+model+'.jsonl' if name=='discovery' else 'items/access-v2/'+name+'.jsonl')
 env=environment(root,gpu,uuid)
 while not idle(gpu,uuid):time.sleep(30)
 run(root,[py,'harness/h200_generate_idle_v2.py','--prompts',str(plan),'--model',model,'--models',str(code/'harness/models.json'),'--reference',str(code/'harness/weights_reference.json'),'--out',str(root/'responses'/name),'--run-id',f'access-v2-{name}-{model}','--chunk','256'],f'{name}-{model}.log',env)
 score_phase(root,model,name)
def score_phase(root,model,name):
 code=root/'code';plan=code/('items/access-v2/model-plans/discovery-'+model+'.jsonl' if name=='discovery' else 'items/access-v2/'+name+'.jsonl')
 run(root,[str(root/'.venv/bin/python'),'tools/score_access_v2.py','--plan',str(plan),'--items',str(code/('items/access-v2/'+name+'-items.json')),'--responses',str(root/'responses'/name/model/'responses.jsonl'),'--out',str(root/'scores'/name/(model+'.jsonl')),'--model',model],f'{name}-{model}-score.log',os.environ.copy())
def audit(root):
 code=root/'code';final=json.loads((code/'docs/access-v2/final-lock.json').read_text())
 for name,expected in {**final['code_sha256'],**final['input_sha256']}.items():
  if sha(code/name)!=expected:raise RuntimeError('Frozen source/input mismatch '+name)
 for rec in final['model_plans'].values():
  if sha(code/rec['path'])!=rec['sha256']:raise RuntimeError('Frozen plan mismatch')
 amendment=json.loads((code/'docs/access-v2/hardware-amendment.json').read_text())
 for name,expected in amendment['operational_code_sha256'].items():
  if sha(code/name)!=expected:raise RuntimeError('Operational source mismatch '+name)
 return amendment['allowed_gpu_uuid']
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--slot',choices=['1','2'],required=True);ap.add_argument('--finish-gemma-child');a=ap.parse_args();root=a.root
 lock=(root/'operations'/f'idle-worker-slot-{a.slot}.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 allowed=audit(root);spec=json.loads((root/'code/docs/access-v2/spec-lock.json').read_text())
 if a.finish_gemma_child:
  # The original generating child continues without interruption; only its
  # waiting controller was replaced after the user's hardware instruction.
  p=Path('/proc')/a.finish_gemma_child/'cmdline'
  while True:
   try:alive=p.exists() and b'h200_generate_v2.py' in p.read_bytes()
   except FileNotFoundError:alive=False
   if not alive:break
   time.sleep(15)
  try:
   s=root/'responses/discovery/gemma4_31b/summary-access-v2-discovery-gemma4_31b.json'
   if not s.exists():raise RuntimeError('Original discovery child failed; preserve partial replies and do not retry')
   score_phase(root,'gemma4_31b','discovery')
   confirm=root/'responses/confirmatory/gemma4_31b/summary-access-v2-confirmatory-gemma4_31b.json'
   if confirm.exists():score_phase(root,'gemma4_31b','confirmatory')
   else:
    if (confirm.parent/'run.json').exists():raise RuntimeError('Original confirmatory attempt did not finish; preserve it without a retry')
    chosen=None
    while chosen is None:chosen=pick_gpu(root,allowed);time.sleep(1 if chosen else 20)
    gpu,uuid,glock=chosen
    try:phase(root,'gemma4_31b','confirmatory',gpu,uuid)
    finally:glock.close()
   update(root,lambda d:d['models']['gemma4_31b'].update(status='finished',finished_unix=time.time(),continuation='hardware authorization only; original discovery child retained'))
   print('MODEL_FINISHED gemma4_31b',flush=True)
  except Exception as e:
   update(root,lambda d:d['models']['gemma4_31b'].update(status='failed',error=repr(e),failed_unix=time.time()));print('MODEL_FAILED gemma4_31b',repr(e),flush=True)
 while True:
  q=json.loads((root/'operations/queue.json').read_text())
  if all(x['status'] in ['finished','failed'] for x in q['models'].values()):break
  verified=json.loads((root/'operations/weights-verified.json').read_text())['models']
  ready=[m for m,s in q['models'].items() if s['status']=='pending' and verified.get(m,{}).get('ok') and Path(verified[m]['path']).is_dir()]
  chosen=pick_gpu(root,allowed) if ready else None
  if chosen is None:time.sleep(30);continue
  gpu,uuid,glock=chosen
  def claim(d):
   for m in ready:
    if d['models'][m]['status']=='pending':d['models'][m].update(status='running',gpu=gpu,pid=os.getpid(),started_unix=time.time(),worker_slot=a.slot);return m
  model=update(root,claim)
  if model is None:glock.close();continue
  print('MODEL_START',model,'UNUSED_GPU',gpu,flush=True)
  try:
   phases=(['pilot'] if model in spec['pilot_models'] else [])+['discovery']+(['confirmatory'] if model in spec['confirmatory_models'] else [])
   for name in phases:
    phase(root,model,name,gpu,uuid)
    if name=='pilot':
     rows=[json.loads(x) for x in (root/'scores/pilot'/(model+'.jsonl')).read_text().splitlines()];state=[x for x in rows if x['Q']=='state'];bad=sum(x['status'] not in ['complete','truncated'] for x in rows);trunc=sum(x['status']=='truncated' for x in rows)/len(rows);yn=sum(x['answer_valid'] for x in state)/len(state)
     gate={'model':model,'pass':bad==0 and trunc<=.01 and yn>=.98,'bad_statuses':bad,'truncated_fraction':trunc,'probe_format_valid_fraction':yn,'criterion':'execution/interface only; no leakage effect selection'}
     (root/'operations'/f'pilot-{model}.json').write_text(json.dumps(gate,indent=2))
     if not gate['pass']:raise RuntimeError('Pilot interface gate failed; no outcome-driven retry')
   update(root,lambda d:d['models'][model].update(status='finished',finished_unix=time.time()));print('MODEL_FINISHED',model,flush=True)
  except Exception as e:
   update(root,lambda d:d['models'][model].update(status='failed',error=repr(e),failed_unix=time.time()));print('MODEL_FAILED',model,repr(e),flush=True)
  finally:
   glock.close();cache=root/'weights'/model
   if cache.is_dir() and not cache.is_symlink():
    shutil.rmtree(cache);(root/'operations'/f'cache-evicted-{model}.json').write_text(json.dumps({'model':model,'path':str(cache),'evicted_unix':time.time(),'scope':'new re-downloadable weights only; frozen inputs, replies, scores and NAS snapshots preserved'},indent=2))
if __name__=='__main__':main()
