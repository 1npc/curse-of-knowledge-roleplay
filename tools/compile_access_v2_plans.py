"""Compile eligibility and union duplicate tasks before freezing generation."""
from pathlib import Path
import sys,json,hashlib,datetime
ROOT=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(ROOT))
from tools.build_access_v2 import MAIN,METHOD,CONF,PERSIST,write_once
from oc_v2.design import items,balanced_indices

def read(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def main():
 out=ROOT/'items/access-v2';base=read(out/'discovery.jsonl');extra=read(out/'discovery-extension.jsonl');registry={}
 for model in MAIN:
  rows={r['prompt_id']:r.copy() for r in base}
  for r in extra:
   ex=r['experiments'];eligible=any((e=='E2') or (e=='E3' and model in METHOD) or (e in ('E5','E6') and model in PERSIST) for e in ex)
   if not eligible:continue
   if r['prompt_id'] in rows:
    old=rows[r['prompt_id']];assert old['messages']==r['messages'] and old.get('next_step')==r.get('next_step')
    old['experiments']=sorted(set(old['experiments']+ex))
   else:rows[r['prompt_id']]=r.copy()
  p=out/'model-plans'/f'discovery-{model}.jsonl';write_once(p,''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in sorted(rows.values(),key=lambda x:x['prompt_id'])))
  registry[model]={'first_steps':len(rows),'second_steps':sum('next_step' in r for r in rows.values()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'path':str(p.relative_to(ROOT))}
 it=items('discovery',96)
 subsets={tag:sorted(it[i]['id'] for i in balanced_indices(it,n,seed)) for tag,n,seed in [('E2',6,20261001),('E3',12,20261002),('E5_E6',8,20261003)]}
 lock={'status':'final local freeze BEFORE ANY v2 response; not external preregistration','local_date':'2026-10-02','locked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'model_plans':registry,'subsets':subsets,'input_sha256':{},'code_sha256':{},'pilot_gate':'execution/interface only: invalid tokenizer/engine statuses absent, truncation <=1%, Yes/No probe format >=98%; no leakage or effect-size threshold; translation capability reported separately','awareness':'Original-scene partial-event retention is the task endpoint; actual-input correctness reported separately for hard removal','E2':'R1 auditory scope is exhaustive audible_to_characters membership, R2 direct bool, R3 same bool plus prose','revision_history':'draft-v0..v3 preserved; all revisions preceded generation and corrected repeated contexts, balancing, locatives/stairwell, shell perspective, and task deduplication'}
 for p in out.glob('*.json*'):lock['input_sha256'][str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
 for name in ['oc_v2/design.py','oc_v2/score.py','oc_v2/analyze.py','harness/h200_generate_v2.py','harness/h200_download_v2.py','harness/h200_queue_v2.py','harness/h200_runtime_ready.py','tools/build_access_v2.py','tools/compile_access_v2_plans.py','tools/score_access_v2.py','tools/analyze_access_v2.py','tests/test_access_v2.py','harness/models.json','harness/weights_reference.json','oc/score.py','oc/patterns.py','oc/langid.py','oc/translit.py','data/valueset.json','data/mask.json','docs/access-v2/spec-lock.json']:
  p=ROOT/name;lock['code_sha256'][name]=hashlib.sha256(p.read_bytes()).hexdigest()
 p=ROOT/'docs/access-v2/final-lock.json'
 if p.exists():lock['locked_at_utc']=json.loads(p.read_text())['locked_at_utc']
 write_once(p,json.dumps(lock,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(registry,indent=2))
if __name__=='__main__':main()
