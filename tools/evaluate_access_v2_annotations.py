"""Descriptive scorer audit against labeled blind forms, preserving label provenance.
AI-proxy metrics are never presented as human certification. All labeled fields
remain replaceable by real independent annotations in the same blinded schema.
"""
from pathlib import Path
import argparse,collections,csv,datetime,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
def read(path):
 with path.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def use(row,n):
 x=[row[f'use_place_{n}'],row[f'use_object_{n}']]
 if '1' in x:return 1
 if x==['0','0']:return 0
 return None
def counts(pairs):
 d={k:0 for k in ['tp','fp','fn','tn']};d['scored_pairs']=len(pairs)
 for pred,gold,weight in pairs:d['tp' if pred and gold else 'fp' if pred else 'fn' if gold else 'tn']+=weight
 d['precision']=d['tp']/(d['tp']+d['fp']) if d['tp']+d['fp'] else None
 d['recall']=d['tp']/(d['tp']+d['fn']) if d['tp']+d['fn'] else None
 d['f1']=2*d['tp']/(2*d['tp']+d['fp']+d['fn']) if 2*d['tp']+d['fp']+d['fn'] else None
 return d
def main():
 p=argparse.ArgumentParser();p.add_argument('--annotations',type=Path,nargs='+',required=True);p.add_argument('--label-type',choices=['ai_proxy','human'],required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 if a.label_type=='human' and any('ai-proxy' in str(f) for f in a.annotations):raise SystemExit('AI-proxy files cannot be relabeled as human')
 keys={r['blind_id']:r for r in map(json.loads,(ROOT/'analysis/validation-access-v2/organizer-key.jsonl').read_text().splitlines()) if r['task']=='semantic_content'}
 report={'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'label_type':a.label_type,'interpretation':'Descriptive comparison to AI proxy judgments; not human-certified scorer performance' if a.label_type=='ai_proxy' else 'Descriptive comparison to supplied human annotations; source and recruitment require separate verification','weighting':'Inverse stratified sampling fractions; exclusions disclosed. Unit is candidate semantic use (target or foil), not an independent participant.','annotators':{}}
 for f in a.annotations:
  rows=read(f);assert len(rows)==640 and {r['blind_id'] for r in rows}==set(keys)
  groups=collections.defaultdict(list);excluded=collections.Counter();mismatches=[]
  for r in rows:
   k=keys[r['blind_id']];weight=k['stratum_population']/k['stratum_sample']
   for kind,n,pred in [('target',k['target_candidate'],k['machine_target']),('foil',3-k['target_candidate'],k['machine_foil'])]:
    gold=use(r,n)
    if k['status']!='complete':excluded['noncomplete_candidates']+=1;continue
    if r['uncertain']!='0' or gold is None:excluded['uncertain_candidates']+=1;continue
    for group in ['pooled','candidate:'+kind,'boundary:'+k['boundary'],'method:'+k['method'],'access:'+str(k['accessible'])]:groups[group].append((pred,gold,weight))
    if pred!=gold:mismatches.append({'blind_id':r['blind_id'],'candidate':kind,'machine':pred,'annotation':gold,'boundary':k['boundary'],'method':k['method']})
  report['annotators'][f.name]={'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'excluded':dict(excluded),'metrics':{k:counts(v) for k,v in groups.items()},'mismatches':mismatches}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n')
 for name,d in report['annotators'].items():print(name,'AI proxy' if a.label_type=='ai_proxy' else 'supplied human',d['metrics']['pooled'],'excluded',d['excluded'])
if __name__=='__main__':main()
