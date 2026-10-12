from pathlib import Path
import sys,json,hashlib,tarfile,collections,datetime
root=Path.cwd();sys.path.insert(0,str(root))
from oc_v2.score import score_record
from harness.h200_generate_v2 import PROTOCOL
base=root/'analysis/h200-v2-20261002'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((base/'mistral-archive-receipt.json').read_text());archive=base/'mistral-complete.tar.gz'
assert archive.stat().st_size==receipt['bytes'] and sha(archive)==receipt['sha256']
extract=base/'mistral';extract.mkdir(exist_ok=True)
with tarfile.open(archive,'r:gz') as t:
 for member in t.getmembers():
  p=Path(member.name)
  assert member.isfile() and not p.is_absolute() and '..' not in p.parts
 for member in t.getmembers():
  target=extract/member.name
  assert extract.resolve() in target.resolve().parents
  target.parent.mkdir(parents=True,exist_ok=True)
  with t.extractfile(member) as source:
   content=source.read()
  if target.exists():assert target.read_bytes()==content
  else:target.write_bytes(content)
lock=json.loads((root/'docs/access-v2/final-lock.json').read_text())
for section in ['input_sha256','code_sha256']:
 for path,digest in lock[section].items():assert sha(root/path)==digest,(section,path)
for d in lock['model_plans'].values():assert sha(root/d['path'])==d['sha256']
reference=json.loads((root/'harness/weights_reference.json').read_text())['models']
models=['mistral_small3']
results={};scorefiles=[]
for model in models:
 data=base/'mistral'
 mp=data/'analysis/mistral-complete-manifest.json'
 manifest=json.loads(mp.read_text())
 for path,info in manifest['files'].items():
  p=data/path;assert p.stat().st_size==info['bytes'] and sha(p)==info['sha256'],path
 results[model]={}
 for phase in ['discovery']:
  r=data/'responses'/phase/model
  if not r.exists():assert model=='nemotron3_nano30b' and phase=='pilot';continue
  run=json.loads((r/'run.json').read_text());summary=json.loads((r/('summary-access-v2-'+phase+'-'+model+'.json')).read_text());runtime=json.loads((r/('runtime-access-v2-'+phase+'-'+model+'.json')).read_text())
  plan=root/'items/access-v2'/('model-plans/discovery-'+model+'.jsonl' if phase=='discovery' else phase+'.jsonl')
  plans=[json.loads(x) for x in plan.read_text().splitlines() if x.strip()]
  raw=r/'responses.jsonl';responses=[json.loads(x) for x in raw.read_text().splitlines() if x.strip()];ids=[x['prompt_id'] for x in responses]
  expected={p['prompt_id'] for p in plans}|{p['prompt_id']+'#2' for p in plans if p.get('next_step')}
  assert len(ids)==len(set(ids))==len(expected) and set(ids)==expected
  runsha=hashlib.sha256(json.dumps(run,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
  runner='harness/h200_generate_v2.py' if model=='gemma4_31b' and phase in ['pilot','discovery'] else 'harness/h200_generate_idle_v2.py'
  assert run['prompts_sha256']==sha(plan) and run['runner_sha256']==sha(root/runner)
  assert run['protocol']==PROTOCOL and run['revision']==reference[model]['revision']
  assert summary['run_sha256']==runsha==runtime['run_sha256'] and all(x['run_sha256']==runsha and x['model']==model for x in responses)
  assert sha(raw)==summary['responses_sha256'] and summary['records']==summary['planned']==len(expected) and summary['interrupted_chunks']==0
  statuses=dict(collections.Counter(x['status'] for x in responses));assert statuses==summary['status']
  items={i['id']:i for i in json.loads((root/'items/access-v2'/(phase+'-items.json')).read_text())['items']}
  replies={x['prompt_id']:x for x in responses};scored=[score_record(p,items[p['item']],replies) for p in plans]
  for s in scored:s['model']=model
  scorefile=data/'scores'/phase/(model+'.jsonl')
  regenerated=''.join(json.dumps(s,ensure_ascii=False,sort_keys=True)+'\n' for s in scored).encode()
  assert hashlib.sha256(regenerated).hexdigest()==sha(scorefile),(model,phase,'score recheck')
  assert runtime['cuda_visible_devices']=='GPU-63686987-a70f-607d-9886-af187b67a14a'
  results[model][phase]={'actual_records':len(responses),'scored_endpoints':len(scored),'status_counts':statuses,'physical_gpu_uuid':runtime['cuda_visible_devices'],'no_missing_or_duplicate_ids':True,'frozen_plan_sha256':sha(plan),'runner_sha256':run['runner_sha256'],'responses_sha256':sha(raw),'scores_sha256':sha(scorefile),'frozen_scorer_recomputed_exact_match':True}
  if phase!='pilot':scorefiles.append(str(scorefile))
report={'verified_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'new_archive_sha256':receipt['sha256'],'all_archive_file_digests_match':True,'scientific_inputs_and_code_unchanged':True,'models':results,'total_actual_records':sum(s['actual_records'] for phases in results.values() for s in phases.values()),'total_scored_endpoints_including_pilot':sum(s['scored_endpoints'] for phases in results.values() for s in phases.values()),'confirmatory_actual_records':0,'actual_human_annotations':0,'full_eleven_model_campaign_complete':False,'analysis_score_files':scorefiles}
(base/'mistral-verification.json').write_text(json.dumps(report,indent=2)+'\n')
for model,phases in results.items():print(model,phases['discovery']['actual_records'],phases['discovery']['status_counts'])
print(json.dumps({k:v for k,v in report.items() if k not in ['models','analysis_score_files']},indent=2))
