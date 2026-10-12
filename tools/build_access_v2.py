"""Create disjoint inputs and locally freeze specification before response generation."""
from pathlib import Path
import sys,json,hashlib,datetime,collections
ROOT=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(ROOT))
from oc_v2.design import *
OUT=ROOT/'items/access-v2'
MAIN=['qwen38_27b','qwen35_9b','gemma4_31b','gemma4_12b','glm47_flash','mistral_small3','gpt_oss_20b','phi4','seed_oss_36b','nemotron3_nano30b','falcon_h1_34b']
METHOD=['gemma4_31b','glm47_flash','nemotron3_nano30b','qwen35_9b','qwen38_27b','falcon_h1_34b']
CONF=['gemma4_31b','glm47_flash','nemotron3_nano30b','qwen35_9b']
PERSIST=['gemma4_31b','glm47_flash','nemotron3_nano30b','qwen35_9b']
def write_once(p,data):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_text()==data,'Refusing to mutate frozen '+str(p)
 else:p.write_text(data)
def dump(p,d):write_once(p,json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def plan(kind,its):
 base=[];extended=[]
 rep_indices=balanced_indices(its,6,20261001) if kind=='discovery' else set()
 method_indices=balanced_indices(its,12,20261002) if kind=='discovery' else set()
 persist_indices=balanced_indices(its,8,20261003) if kind=='discovery' else set()
 for it in its:
  for b in BOUNDARIES:
   for access in (False,True):
    for ver in ('A','B'):
     base.extend(make_record(it,b,ver,access,q=q) for q in ('content','plan'))
     base.append(probe(it,b,ver,access))
  base.extend(translation_probe(it,v) for v in ('A','B'))
 if kind=='discovery':
  for it in its:
   index=int(it['id'][1:])-1
   if index in rep_indices: #24 balanced material blocks, representation arm
    for b in BOUNDARIES:
     for ac in (False,True):
      for ver in ('A','B'):
       for rep in ('R1','R3'):
        extended.extend(make_record(it,b,ver,ac,representation=rep,q=q,experiment='E2') for q in ('content','plan'))
   if index in method_indices: #48 skeletons: paired five-method/awareness arm
    for b in BOUNDARIES:
     for ac in (False,True):
      for ver in ('A','B'):
       extended.append(make_record(it,b,ver,ac,q='awareness',experiment='E3'))
       for m in ('prose','self_filter','hard','view'):
        for q in ('content','plan','awareness'):
         rep='R3' if m=='prose' else 'R2';r=make_record(it,b,ver,ac,representation=rep,method=m,q=q,experiment='E3')
         # prose baseline is exactly R3 full context and can reuse existing E2 records.
         if m=='prose':r['method']='full';r['prompt_id']=r['prompt_id'].replace('.prose.','.full.')
         extended.append(r)
   if index in persist_indices:
    for b in BOUNDARIES:
     for ac in (False,True):
      for ver in ('A','B'):
       for m in ('full','view'):
        for delay in (0,2,4):extended.append(make_record(it,b,ver,ac,method=m,q='plan',delay=delay,experiment='E5'))
        extended.append(decision(it,b,ver,ac,m))
 elif kind=='confirmatory':
  for it in its:
   for b in BOUNDARIES:
    for ac in (False,True):
     for ver in ('A','B'):
      base.append(make_record(it,b,ver,ac,q='awareness',experiment='E4'))
      for m in ('hard','view'):
       base.extend(make_record(it,b,ver,ac,method=m,q=q,experiment='E4') for q in ('content','plan','awareness'))
 def unique(rows):
  seen={}
  for r in rows:
   r['experiments']=[r['experiment']]
   if r['prompt_id'] in seen:assert r['messages']==seen[r['prompt_id']]['messages']
   else:seen[r['prompt_id']]=r
   if r['experiment'] not in seen[r['prompt_id']]['experiments']:seen[r['prompt_id']]['experiments'].append(r['experiment'])
  return list(seen.values())
 return unique(base),unique(extended)
def main():
 OUT.mkdir(exist_ok=True)
 registry={};all_items=[]
 for kind,n in [('pilot',20),('discovery',96),('confirmatory',96)]:
  its=items(kind,n)
  # Pilot uses separate content assignments/scenes and cannot enter main estimates.
  if kind=='pilot':
   for i,it in enumerate(its):it['scene']='A short calibration scene: '+it['scene']
  dump(OUT/f'{kind}-items.json',{'items':its,'kind':kind})
  base,extra=plan(kind,its)
  for name,rows in [(kind,base),(kind+'-extension',extra)]:
   if not rows:continue
   write_once(OUT/f'{name}.jsonl',''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rows))
   registry[name]={'first_steps':len(rows),'second_steps':sum('next_step' in r for r in rows),'sha256':hashlib.sha256((OUT/f'{name}.jsonl').read_bytes()).hexdigest()}
  all_items+=its
 spec={'version':'access-boundaries-v2-20261001','status':'locally frozen before any v2 response; NOT externally preregistered','annotation':'AI proxy review only; real human validation pending','main_models':MAIN,'pilot_models':['gemma4_31b','glm47_flash','qwen35_9b'],'method_models':METHOD,'confirmatory_models':CONF,'persistence_models':PERSIST,'boundaries':BOUNDARIES,'representations':{'R1':'language repertoire or audience/observer/recipient membership (no direct bool)','R2':'one boundary-specific direct bool','R3':'same bool plus explicit prose access/use rule'},'primary_estimand':'equal-model, equal-skeleton mean of same-response target-minus-foil on content and plan; unconditional; capability-conditioned secondary','bootstrap':{'unit':'paired skeleton','replicates':2000,'seed':20261001,'shared_draws':True},'confirmatory_family':{'H1':'all four full-context inaccessible leakage means >0 (intersection union)','H2':'pooled leakage >0 on independently correct access judgments; report empty units','H3':'view reduces forbidden leakage vs full, accessible target-use delta >=-.05, partial-event awareness improvement vs hard >0; intersection union'},'multiplicity':'Holm over three confirmatory tests; exploratory contrasts descriptive with CIs','failure_handling':'all planned denominators retained; incomplete/refused outputs zero use; missing self-filter stage2 explicitly materialized; no content-driven retries','capability_gate':.85,'awareness':'first Yes/No versus accessible OR retained observable shell; partial-inaccessible and Hear reported separately','persistence':'0/2/4 fixed neutral conversation exchanges, same world context; evidence of delayed contextual influence, not a latent-memory mechanism','decision':'paired A-minus-B probability choosing fixed location A; invalid choices remain denominator, report valid response rate','plans':registry,'subsets':'E2 24, E3 48, E5/E6 32; deterministic domain/character/language-balanced selection seeds 20261001/2/3 recorded in code; confirmatory96 original-character scenes; pilot20 distinct calibration contexts','generation':{'temperature':0,'top_p':1,'seed':20261001,'max_output_tokens':400,'max_model_len':8192,'thinking':'off where supported; gpt-oss low, analysis retained','precision':'bf16/native checkpoint','tensor_parallel_size':1,'gpus':[6,7]},'code_hashes':{}}
 for f in ['oc_v2/design.py','oc/score.py','oc/patterns.py','data/valueset.json','data/mask.json','tools/build_access_v2.py']:
  spec['code_hashes'][f]=hashlib.sha256((ROOT/f).read_bytes()).hexdigest()
 lock=ROOT/'docs/access-v2/spec-lock.json'
 if not lock.exists():spec['locked_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();dump(lock,spec)
 else:
  old=json.loads(lock.read_text());spec['locked_at_utc']=old['locked_at_utc'];dump(lock,spec)
 print(json.dumps(registry,indent=2))
if __name__=='__main__':main()
