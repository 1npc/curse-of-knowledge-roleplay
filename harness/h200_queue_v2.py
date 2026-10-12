"""Run the frozen per-model campaign only on idle physical GPU 6 or 7.

Own queue/locks/logs live in the new task root. Never terminate another GPU job.
All outcome errors stop that model with a durable failure record; no automatic
outcome-driven retry, replacement model, or opportunistic use of other GPUs.
"""
from pathlib import Path
import argparse,fcntl,json,os,subprocess,sys,time,hashlib,shutil

ALLOWED={'6':'GPU-18a3d1e0-628c-7817-3018-0844b06e30c9','7':'GPU-00ecc257-2646-98af-1e10-3b94f6004c00'}
def idle(gpu):
 r=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True)
 row=next(x.split(', ') for x in r.splitlines() if x.startswith(gpu+', '))
 if row[1]!=ALLOWED[gpu]:raise RuntimeError('Physical GPU UUID changed')
 apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid','--format=csv,noheader'],text=True)
 return ALLOWED[gpu] not in apps and float(row[2])<100 and float(row[3])<=5
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--gpu',choices=ALLOWED,required=True);a=ap.parse_args()
 root=a.root;code=root/'code';ops=root/'operations';py=root/'.venv/bin/python'
 ops.mkdir(exist_ok=True);lock=(ops/f'gpu{a.gpu}.worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 final=json.loads((code/'docs/access-v2/final-lock.json').read_text());spec=json.loads((code/'docs/access-v2/spec-lock.json').read_text())
 for name,expected in final['code_sha256'].items():
  if hashlib.sha256((code/name).read_bytes()).hexdigest()!=expected:raise RuntimeError('Frozen source mismatch '+name)
 for name,expected in final['input_sha256'].items():
  if hashlib.sha256((code/name).read_bytes()).hexdigest()!=expected:raise RuntimeError('Frozen input mismatch '+name)
 for entry in final['model_plans'].values():
  if hashlib.sha256((code/entry['path']).read_bytes()).hexdigest()!=entry['sha256']:raise RuntimeError('Frozen model plan mismatch')
 env=os.environ.copy();env.update(OC=str(root),OC_PHYSICAL_GPU=a.gpu,CUDA_VISIBLE_DEVICES=ALLOWED[a.gpu],CUDA_DEVICE_ORDER='PCI_BUS_ID',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',VLLM_WORKER_MULTIPROC_METHOD='spawn')
 def state_update(fn):
  with (ops/'queue.lock').open('a+') as qlock:
   fcntl.flock(qlock,fcntl.LOCK_EX);p=ops/'queue.json'
   d=json.loads(p.read_text()) if p.exists() else {'models':{m:{'status':'pending'} for m in ['gemma4_31b','qwen35_9b','glm47_flash','nemotron3_nano30b','qwen38_27b','gpt_oss_20b','phi4','gemma4_12b','falcon_h1_34b','mistral_small3','seed_oss_36b']}}
   value=fn(d);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(d,indent=2)+'\n');os.replace(tmp,p);return value
 def claim(d):
  for m,r in d['models'].items():
   if r['status']=='pending':r.update(status='running',gpu=a.gpu,pid=os.getpid(),started_unix=time.time());return m
  return None
 def run(cmd,log,runenv=env):
  with log.open('ab') as f:subprocess.run(cmd,cwd=code,env=runenv,stdout=f,stderr=subprocess.STDOUT,check=True)
 while True:
  if not state_update(lambda d:any(r['status']=='pending' for r in d['models'].values())):break
  # Runtime restoration may still be in progress. A file is written only
  # after importing the pinned engine and checking pip dependency consistency.
  if not (ops/'runtime-ready.json').exists() or not idle(a.gpu):time.sleep(45);continue
  model=state_update(claim)
  if model is None:print('No pending models',flush=True);break
  print('MODEL_START',model,'GPU',a.gpu,flush=True)
  try:
   verified=ops/'weights-verified.json';d=json.loads(verified.read_text()) if verified.exists() else {'models':{}}
   if not d['models'].get(model,{}).get('ok'):
    ref=json.loads((code/'harness/weights_reference.json').read_text())['models'][model]
    required=sum(v['bytes'] for v in ref['files'].values())+(20<<30)
    while shutil.disk_usage(root).free<required:time.sleep(45)
    downloadenv=env.copy();downloadenv.pop('HF_HUB_OFFLINE');downloadenv.pop('TRANSFORMERS_OFFLINE');downloadenv.update(HTTP_PROXY='http://127.0.0.1:3128',HTTPS_PROXY='http://127.0.0.1:3128',HF_HOME=str(root/'cache/huggingface'),HF_XET_CACHE=str(root/'cache/xet'),HF_XET_HIGH_PERFORMANCE='1')
    run([str(py),'harness/h200_download_v2.py','--root',str(root),'--model',model],root/'logs'/f'{model}-weights.log',downloadenv)
   phases=['pilot'] if model in spec['pilot_models'] else []
   phases+=['discovery']+(['confirmatory'] if model in spec['confirmatory_models'] else [])
   for phase in phases:
    while not idle(a.gpu):time.sleep(45)
    plan=code/('items/access-v2/model-plans/discovery-'+model+'.jsonl' if phase=='discovery' else 'items/access-v2/'+phase+'.jsonl')
    out=root/'responses'/phase
    run([str(py),'harness/h200_generate_v2.py','--prompts',str(plan),'--model',model,'--models',str(code/'harness/models.json'),'--reference',str(code/'harness/weights_reference.json'),'--out',str(out),'--run-id',f'access-v2-{phase}-{model}','--chunk','256'],root/'logs'/f'{phase}-{model}.log')
    raw=out/model/'responses.jsonl'
    score=root/'scores'/phase/(model+'.jsonl')
    run([str(py),'tools/score_access_v2.py','--plan',str(plan),'--items',str(code/('items/access-v2/'+phase+'-items.json')),'--responses',str(raw),'--out',str(score),'--model',model],root/'logs'/f'{phase}-{model}-score.log')
    if phase=='pilot':
     rows=[json.loads(x) for x in score.read_text().splitlines()];bad=[r for r in rows if r['status'] not in ('complete','truncated')];state=[r for r in rows if r['Q']=='state'];trunc=sum(r['status']=='truncated' for r in rows)/len(rows);yn=sum(r['answer_valid'] for r in state)/len(state)
     gate={'model':model,'pass':not bad and trunc<=.01 and yn>=.98,'bad_statuses':len(bad),'truncated_fraction':trunc,'probe_format_valid_fraction':yn,'criterion':'execution/interface only; no leakage effect selection'}
     (ops/f'pilot-{model}.json').write_text(json.dumps(gate,indent=2)+'\n')
     if not gate['pass']:raise RuntimeError('Pilot interface gate failed; preserve results and stop this model')
   state_update(lambda d:d['models'][model].update(status='finished',finished_unix=time.time()))
   print('MODEL_FINISHED',model,flush=True)
  except Exception as e:
   state_update(lambda d:d['models'][model].update(status='failed',error=repr(e),failed_unix=time.time()))
   print('MODEL_FAILED',model,repr(e),flush=True)
  finally:
   # Only this campaign's re-downloadable weight cache is evicted. Frozen
   # code, hashes, verification receipts, raw replies, scores and old NAS
   # snapshots remain. This bounds two-worker storage on the 205GiB SSD.
   cache=root/'weights'/model
   if cache.is_dir() and not cache.is_symlink():
    shutil.rmtree(cache)
    (ops/f'cache-evicted-{model}.json').write_text(json.dumps({'model':model,'path':str(cache),'evicted_unix':time.time(),'scope':'new re-downloadable task weights only; all evidence preserved'},indent=2)+'\n')
if __name__=='__main__':main()
