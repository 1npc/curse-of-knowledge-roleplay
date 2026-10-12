"""Descriptive tables and a fresh blind audit packet from verified v2 results.
This report layer does not modify the frozen hypotheses, scorer, or generation.
"""
from pathlib import Path
import collections,csv,datetime,hashlib,io,json,random,sys,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from oc_v2.analyze import Bootstrap,model_skeleton_vector,paired_delta
from oc_v2.design import BOUNDARIES,LEXICON
B=ROOT/'analysis/h200-v2-20261002';V=ROOT/'analysis/validation-access-v2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,data):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
def csvwrite(p,rows,fields=None):
 p.parent.mkdir(parents=True,exist_ok=True)
 stream=io.StringIO(newline='');w=csv.DictWriter(stream,fieldnames=fields or list(rows[0]));w.writeheader();w.writerows(rows);data=stream.getvalue().encode('utf-8')
 if p.exists() and p.read_bytes()!=data:raise RuntimeError('Preserve existing annotation/stimulus packet: '+str(p))
 p.write_bytes(data)
def main():
 verified=json.loads((B/'four-core-verification.json').read_text());sources=[Path(x) for x in verified['analysis_score_files']]
 rows=[json.loads(line) for p in sources for line in p.read_text().splitlines()]
 spec=json.loads((ROOT/'docs/access-v2/spec-lock.json').read_text());lock=json.loads((ROOT/'docs/access-v2/final-lock.json').read_text())
 models=spec['confirmatory_models'];boot=Bootstrap();desc=[]
 def est(label,rr,field,extra=None):
  v=boot.vector(model_skeleton_vector(rr,models,field));v.pop('p_one_sided',None);v.pop('null',None)
  record={'panel':label,'metric':field,'models':models,'endpoints':len(rr),**(extra or {}),**v};desc.append(record);return record
 role=lambda r:r['Q'] in ('content','plan') and r['delay']==0
 confirm=[r for r in rows if r['set']=='confirmatory'];discovery=[r for r in rows if r['set']=='discovery']
 for b in BOUNDARIES:
  for access in [False,True]:
   rr=[r for r in confirm if role(r) and r['boundary']==b and r['representation']=='R2' and r['method']=='full' and r['accessible']==access]
   for field in ['D','hit_t']:est('confirmatory_boundary',rr,field,{'boundary':b,'accessible':access})
 for method in ['full','hard','view']:
  for access in [False,True]:
   rr=[r for r in confirm if role(r) and r['representation']=='R2' and r['method']==method and r['accessible']==access]
   est('confirmatory_method',rr,'hit_t' if access else 'D',{'method':method,'accessible':access})
  rr=[r for r in confirm if r['Q']=='awareness' and not r['accessible'] and r['boundary']!='Hear' and r['method']==method]
  for field in ['awareness_correct','input_awareness_correct']:est('confirmatory_partial_awareness',rr,field,{'method':method})
 for b in BOUNDARIES:
  for method in ['full','view']:
   for delay in [0,2,4]:
    rr=[r for r in discovery if r['item'] in lock['subsets']['E5_E6'] and r['boundary']==b and r['Q']=='plan' and r['representation']=='R2' and r['method']==method and not r['accessible'] and r['delay']==delay]
    est('persistence',rr,'D',{'boundary':b,'method':method,'delay':delay})
   rr=[r for r in discovery if r['item'] in lock['subsets']['E5_E6'] and r['boundary']==b and r['Q']=='decision' and r['method']==method and not r['accessible']]
   delta=paired_delta(rr,models,'choose_A',lambda r:r['version']=='A',lambda r:r['version']=='B');v=boot.vector(delta);v.pop('p_one_sided',None);v.pop('null',None)
   desc.append({'panel':'decision','metric':'fixed_A_choice_A_minus_B','models':models,'boundary':b,'method':method,'endpoints':len(rr),'valid_choice_fraction':sum(r['choice_valid'] for r in rr)/len(rr),**v})
 for b in BOUNDARIES:
  for method in ['full','prose','self_filter','hard','view']:
   for access in [False,True]:
    rr=[r for r in discovery if r['item'] in lock['subsets']['E3'] and r['boundary']==b and role(r) and r['accessible']==access and ((method=='prose' and r['method']=='full' and r['representation']=='R3') or (method!='prose' and r['method']==method and r['representation']=='R2'))]
    est('discovery_method_four_core',rr,'hit_t' if access else 'D',{'boundary':b,'method':method,'accessible':access})
 model_detail=[]
 for model in models:
  mm=[r for r in confirm if r['model']==model]
  states={(r['item'],r['boundary'],r['version']):r['state_correct'] for r in mm if r['Q']=='state' and not r['accessible']}
  eligible=[r for r in mm if role(r) and r['method']=='full' and not r['accessible'] and states[r['item'],r['boundary'],r['version']]]
  detail={'model':model,'inaccessible_state_accuracy':sum(states.values())/len(states),'conditional_D':sum(r['D'] for r in eligible)/len(eligible),'eligible_roles':len(eligible)}
  for b in BOUNDARIES:
   rr=[r for r in mm if role(r) and r['boundary']==b and r['method']=='full' and not r['accessible']]
   detail[b]=sum(r['D'] for r in rr)/len(rr)
  model_detail.append(detail)
 translation=[]
 for model in models:
  for lang in ['zh','ja','es']:
   rr=[r for r in confirm if r['model']==model and r['Q']=='translate' and r['lang']==lang]
   translation.append({'model':model,'language':lang,'endpoints':len(rr),'both_canary_translation_use':sum(r['U2'] for r in rr)/len(rr),'gate':.85})
 report={'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Four prespecified core models; descriptive report, no new confirmatory tests','source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sources},'frozen_results_sha256':sha(B/'four-core-results.json'),'descriptive_estimates':desc,'confirmatory_model_detail':model_detail,'confirmatory_translation':translation,'human_labels':0}
 save(B/'paper-descriptive-results.json',report)
 # New blinded annotation sample, selected before any new human or AI labels.
 rng=random.Random(20261002);V.mkdir(exist_ok=True)
 keys=[];content=[];awareness=[]
 itemdata={phase:{i['id']:i for i in json.loads((ROOT/'items/access-v2'/(phase+'-items.json')).read_text())['items']} for phase in ['pilot','discovery','confirmatory']}
 for model in models:
  for b in BOUNDARIES:
   for method in ['full','prose','self_filter','hard','view']:
    for access in [False,True]:
     for q in ['content','plan']:
      pool=[r for r in discovery if r['model']==model and r['boundary']==b and r['item'] in lock['subsets']['E3'] and r['Q']==q and r['accessible']==access and r['delay']==0 and ((method=='prose' and r['method']=='full' and r['representation']=='R3') or (method!='prose' and r['method']==method and r['representation']=='R2'))]
      for r in rng.sample(pool,2):
       item=itemdata['discovery'][r['item']];order=['A','B'];rng.shuffle(order);uid='C-'+hashlib.sha256((r['model']+'|'+r['prompt_id']).encode()).hexdigest()[:12]
       row={'blind_id':uid,'response':r['text']}
       for n,version in enumerate(order,1):
        vals=item['langs'][item['lang']][version]
        row[f'candidate_{n}_place']='; '.join(LEXICON[vals['PLACE']]['en']);row[f'candidate_{n}_object']='; '.join(LEXICON[vals['OBJECT']]['en'])
        row[f'candidate_{n}_foreign_sentence']=vals['lines'][0]
       for field in ['use_place_1','use_object_1','use_place_2','use_object_2','paraphrase','denial','refusal','foreign_echo_only','uncertain','evidence']:row[field]=''
       content.append(row);keys.append({'blind_id':uid,'task':'semantic_content','model':model,'prompt_id':r['prompt_id'],'phase':'discovery','boundary':b,'method':method,'accessible':access,'Q':q,'stratum_population':len(pool),'stratum_sample':2,'candidate_versions':order,'target_candidate':1+order.index(r['version']),'machine_D':r['D'],'machine_target':r['hit_t'],'machine_foil':r['hit_f'],'status':r['status']})
   for method in ['full','hard','view']:
    for access in [False,True]:
     pool=[r for r in confirm if r['model']==model and r['boundary']==b and r['method']==method and r['Q']=='awareness' and r['accessible']==access]
     for r in rng.sample(pool,2):
      uid='A-'+hashlib.sha256((r['model']+'|'+r['prompt_id']).encode()).hexdigest()[:12]
      awareness.append({'blind_id':uid,'question':'Did you notice the named actor do or say anything just now?','response':r['text'],'acknowledges_occurrence':'','claims_content_knowledge':'','uncertain':'','evidence':''})
      keys.append({'blind_id':uid,'task':'event_awareness','model':model,'prompt_id':r['prompt_id'],'phase':'confirmatory','boundary':b,'method':method,'accessible':access,'stratum_population':len(pool),'stratum_sample':2,'expected_original_scene':r['expected_awareness'],'expected_actual_input':r['expected_input_awareness'],'machine_original_correct':r['awareness_correct'],'machine_input_correct':r['input_awareness_correct']})
 rng.shuffle(content);rng.shuffle(awareness)
 for annotator in ['A','B']:
  csvwrite(V/f'blind-content-{annotator}.csv',content);csvwrite(V/f'blind-awareness-{annotator}.csv',awareness)
 (V/'organizer-key.jsonl').write_text(''.join(json.dumps(k,ensure_ascii=False)+'\n' for k in keys))
 native={}
 for phase,items in itemdata.items():
  for item in items.values():
   lang=item['lang']
   for version,vals in item['langs'][lang].items():
    key=(lang,vals['lines'][0],vals['gold'][0])
    if key not in native:native[key]={'stimulus_id':'N-'+hashlib.sha256('|'.join(key).encode()).hexdigest()[:12],'language':lang,'sentence':vals['lines'][0],'intended_meaning':vals['gold'][0],'source_items':[],'meaning_correct':'','natural':'','unintended_clue':'','uncertain':'','notes':''}
    native[key]['source_items'].append(f'{phase}:{item["id"]}:{version}')
 native_rows=[{**v,'source_items':'; '.join(v['source_items'])} for v in native.values()]
 csvwrite(V/'native-stimuli.csv',native_rows)
 protocol='''# Access-boundary v2 blind validation packet

This is a newly sampled v2 packet, distinct from the older 360 + 220 response audit. Real human labels remain blank. AI labels must be written under ai-proxy/ and identified as AI judgments; they cannot certify the measurement.

Sampling was fixed with Python random seed 20261002 before inspecting new annotation labels. The semantic sample has 640 responses: two uniformly sampled responses in each model × boundary × method × access × question stratum, on the frozen E3 48-scene subset, for the four core models. The awareness sample has 192 responses: two per model × boundary × method × access stratum from the independent confirmatory set. These two populations must be analyzed separately. Sampling fractions are stored in the organizer key; use them for population-weighted certification and also report condition-specific estimates and sample counts. Do not pool the balanced audit as if it were an unstratified response census.

Give annotators only their blind CSVs and this guide. Do not provide organizer-key.jsonl, model names, conditions, machine labels, or another annotator's output. Candidate 1/2 assignment is randomized; it does not identify the target. Judging semantic content does not require knowing which candidate appeared in the scene.

For each use_place/use_object field, enter 1 for semantically used or asserted, 0 for absent, and U for unresolved. Include a correctly resolved paraphrase. A mere negated mention (e.g. "I don't know whether it is in the church") is not an affirmative semantic use; record denial separately. If content is nonetheless asserted or used to guide a plan, label that content as used even when another clause denies access. Refusal records an explicit refusal, not ordinary uncertainty about location. foreign_echo_only is 1 only when the response merely repeats untranslated foreign text without conveying its meaning in English. Fill paraphrase, denial, refusal, foreign_echo_only and uncertain with 1/0/U and add a short evidence note. Preserve the original ID, response and candidate fields exactly.

For event awareness, label acknowledges_occurrence as 1 when the response says the actor did/sent/said something, 0 when it denies or does not acknowledge any occurrence, and U when unresolved. claims_content_knowledge flags claimed knowledge of what was said/sent/put where. The organizer later compares the semantic answer with both the original-scene and actual-input golds; the two targets must remain distinct, especially for hard removal.

Two people should annotate independently before adjudication. Report agreement, adjudication counts, unresolved labels, target/foil precision, recall and F1, by boundary, representation/method and access condition where supported by sample sizes. Do not change the frozen scorer from this review and overwrite earlier results. Any human-derived correction must be a separately identified sensitivity analysis.

native-stimuli.csv deduplicates the active multilingual sentences while retaining every source item. Seek two fluent/native reviewers per language for meaning, naturalness and unintended clues. This is stimulus assessment, not a guessability questionnaire; word-form guessing still requires actual participant responses in the existing separate questionnaire.
'''
 (V/'protocol.md').write_text(protocol)
 save(V/'manifest.json',{'created_at_utc':report['created_at_utc'],'selection_seed':20261002,'semantic_responses':len(content),'awareness_responses':len(awareness),'unique_active_native_stimuli':len(native_rows),'actual_human_annotations':0,'AI_labels_initially_absent':True,'source_sha256':report['source_sha256'],'files':{p.name:sha(p) for p in V.iterdir() if p.is_file() and p.name!='manifest.json'}})
 with zipfile.ZipFile(ROOT/'deliverables/access-v2-blind-validation.zip','w',zipfile.ZIP_DEFLATED) as z:
  paths=[V/n for n in ['blind-content-A.csv','blind-content-B.csv','blind-awareness-A.csv','blind-awareness-B.csv','native-stimuli.csv','protocol.md']]
  for p in paths:z.write(p,p.name)
  z.writestr('packet-manifest.json',json.dumps({'semantic_responses':640,'awareness_responses':192,'native_stimuli':len(native_rows),'actual_human_annotations':0,'all_annotation_fields_blank':True,'files':{p.name:sha(p) for p in paths}},indent=2)+'\n')
 print('Descriptive estimates:',len(desc),'semantic sample:',len(content),'awareness sample:',len(awareness),'native stimuli:',len(native_rows))
if __name__=='__main__':main()
