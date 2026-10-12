"""Finalize queued evidence without modifying frozen generation or old studies."""
from pathlib import Path
import argparse,collections,hashlib,json,os,subprocess,time

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();root=a.root;code=root/'code';ops=root/'operations';py=root/'.venv/bin/python'
 while True:
  queue=ops/'queue.json'
  if not queue.exists() or not (ops/'runtime-ready.json').exists():time.sleep(45);continue
  state=json.loads(queue.read_text())
  if all(r['status'] in ('finished','failed') for r in state['models'].values()):break
  time.sleep(45)
 spec=json.loads((code/'docs/access-v2/spec-lock.json').read_text());scores=[];materialized=[]
 for model,job in state['models'].items():
  phases=(['pilot'] if model in spec['pilot_models'] else [])+['discovery']+(['confirmatory'] if model in spec['confirmatory_models'] else [])
  for phase in phases:
   plan=code/('items/access-v2/model-plans/discovery-'+model+'.jsonl' if phase=='discovery' else 'items/access-v2/'+phase+'.jsonl')
   out=root/'responses'/phase/model;raw=out/'responses.jsonl';score=root/'scores'/phase/(model+'.jsonl')
   if not raw.exists():
    out.mkdir(parents=True,exist_ok=True);rows=[]
    for chunk in sorted((out/'chunks').glob('*chunk-*.jsonl')):rows.extend(json.loads(x) for x in chunk.read_text().splitlines() if x.strip())
    rows.sort(key=lambda r:r['prompt_id']);assert len({r['prompt_id'] for r in rows})==len(rows)
    raw.write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rows))
    materialized.append({'model':model,'phase':phase,'recovered_raw_records':len(rows),'job_status':job['status'],'note':'Missing planned endpoints are explicitly zero-scored, not fabricated raw model replies.'})
   if not score.exists():
    subprocess.run([str(py),str(code/'tools/score_access_v2.py'),'--plan',str(plan),'--items',str(code/('items/access-v2/'+phase+'-items.json')),'--responses',str(raw),'--out',str(score),'--model',model],check=True)
   if phase!='pilot':scores.append(score)
 report=root/'analysis/results.json';report.parent.mkdir(exist_ok=True)
 subprocess.run([str(py),str(code/'tools/analyze_access_v2.py'),'--scores',*[str(p) for p in scores],'--out',str(report)],check=True)
 d=json.loads(report.read_text());statuses=collections.Counter()
 for f in scores:
  for ln in f.read_text().splitlines():statuses[json.loads(ln)['status']]+=1
 d['execution']={'queue':state,'all_models_finished':all(r['status']=='finished' for r in state['models'].values()),'endpoint_status':dict(statuses),'materialized_missing_phases':materialized,'human_validation_complete':False,'inference_caution':'Do not treat a failed/unfinished model or provisional AI assessment as submission-ready scientific validation.'}
 report.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
 (ops/'campaign-finalized.json').write_text(json.dumps({'finalized_unix':time.time(),'all_models_finished':d['execution']['all_models_finished'],'report':str(report),'report_sha256':hashlib.sha256(report.read_bytes()).hexdigest(),'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2)+'\n');print(json.dumps(d['execution'],indent=2),flush=True)
if __name__=='__main__':main()
