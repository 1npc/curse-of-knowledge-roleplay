"""Describe provisional AI annotations separately from genuine human packets."""
from pathlib import Path
import csv,json,collections,hashlib
ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/'analysis/ai-review-20261001'
FIELDS=['use_set1_place','use_set1_object','use_set2_place','use_set2_object','N_deny','A_explicit','refusal','echo_only']
def read(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def agree(a,b,f):
 n=len(a);both=sum(x[f]==y[f] for x,y in zip(a,b));pa=sum(x[f]=='1' for x in a)/n;pb=sum(x[f]=='1' for x in b)/n;pe=pa*pb+(1-pa)*(1-pb)
 return {'n':n,'agree':both,'agreement':both/n,'kappa':(both/n-pe)/(1-pe) if pe<1 else None,'A_positive':round(pa*n),'B_positive':round(pb*n)}
def b(x):return str(x).lower() in ('true','1')
def comparison(rows,keys,weighted=False,certain_only=False):
 c=collections.Counter();eligible=0
 for r in rows:
  if certain_only and r['uncertain']=='1':continue
  k=keys[r['audit_id']];w=1/float(k['inclusion_probability']) if weighted else 1
  s=k['target_set'];reference=(b(r['use_set'+s+'_place']) or b(r['use_set'+s+'_object'])) and not b(r['refusal']) and not b(r['echo_only'])
  pred=b(k['machine_hit_t']);c[('TP' if reference else 'FP') if pred else ('FN' if reference else 'TN')]+=w;eligible+=1
 tp,fp,fn,tn=c['TP'],c['FP'],c['FN'],c['TN']
 precision=tp/(tp+fp) if tp+fp else None;recall=tp/(tp+fn) if tp+fn else None
 return {'rows':eligible,'comparison':'machine target-any versus provisional adjudicated AI semantic target-any','weighted':weighted,'certain_only':certain_only,'confusion':{'TP':tp,'FP':fp,'FN':fn,'TN':tn},'precision':precision,'recall':recall,'f1':2*precision*recall/(precision+recall) if precision is not None and recall is not None and precision+recall else None}
def main():
 report={'provenance':'AI subagents; explicitly authorized temporary proxy; NOT human/native validation or certification','actual_human_completed':0,'adjudicator':'Annotator B revisited disputed/uncertain items; not an independent third rater','rubric_caution':'A used a broader A_explicit interpretation, including attribution. B and adjudication use explicit language-understanding/translation claims. Preserve original judgments; do not interpret disagreement as human reliability.','double_review':{},'source_sha256':{}}
 for kind,keyname in [('certification','certification-key.csv'),('miss-audit','miss-key.csv')]:
  a=read(BASE/'annotator-A'/f'{kind}.csv');d=read(BASE/'annotator-B'/f'{kind}.csv');adj=read(BASE/'adjudication'/f'{kind}.csv');assert len(a)==len(d)==len(adj)
  assert [r['audit_id'] for r in a]==[r['audit_id'] for r in d]==[r['audit_id'] for r in adj]
  assert all(r[f] in ('0','1') for r in a+d+adj for f in FIELDS+['uncertain'])
  keys={r['audit_id']:r for r in read(ROOT/'analysis/results/main-20260929/audit-private'/keyname)}
  item={'rows':len(a),'field_agreement':{f:agree(a,d,f) for f in FIELDS},'rows_disagree':sum(any(x[f]!=y[f] for f in FIELDS) for x,y in zip(a,d)),'adjudicated_uncertain':sum(r['uncertain']=='1' for r in adj),'comparison':comparison(adj,keys),'weighted_comparison':comparison(adj,keys,True),'certain_only_comparison':comparison(adj,keys,False,True)}
  report['double_review'][kind]=item
  for folder in ('annotator-A','annotator-B','adjudication'):
   p=BASE/folder/f'{kind}.csv';report['source_sha256'][str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
 paths=[BASE/'language-echo-screen/part-1-ai-screened.csv',BASE/'language-echo-screen/part-2.csv',BASE/'language-echo-screen/part-3-reviewed.csv']
 screening=[]
 for n,p in enumerate(paths,1):
  rs=read(p)
  for r in rs:r['ai_rater']=f'subagent-{n}';r['assessment_source']='AI proxy; real human assessment pending'
  screening+=rs;report['source_sha256'][str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
 assert len(screening)==3211 and len({r['audit_id'] for r in screening})==3211
 assert all(r[k] in ('0','1') for r in screening for k in ['semantic_use_set1','semantic_use_set2','pure_echo','uncertain'])
 p=BASE/'language-echo-screen/combined-ai-screen.csv'
 with p.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(screening[0]));w.writeheader();w.writerows(screening)
 report['language_echo']={'rows':len(screening),'semantic_any':sum(b(r['semantic_use_set1']) or b(r['semantic_use_set2']) for r in screening),'pure_echo':sum(b(r['pure_echo']) for r in screening),'uncertain':sum(b(r['uncertain']) for r in screening),'language_counts':dict(collections.Counter(r['language'] for r in screening)),'limitation':'Original foreign utterance unavailable in the extra queue: pure-echo judgments cannot certify verbatim echo. Raters differ in uncertainty calibration; do not pool uncertainty as an error probability.'}
 report['stimulus']=json.loads((BASE/'stimulus-review/counts.json').read_text())
 report['weighting_caution']='Certification and targeted machine-negative miss-audit are summarized separately. Their inverse-probability tables must not be combined as if sampling disjoint populations.'
 (BASE/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'double_review':{k:{x:v[x] for x in ['rows','rows_disagree','adjudicated_uncertain']} for k,v in report['double_review'].items()},'language_echo':report['language_echo']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
