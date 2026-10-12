"""Check completed independent AI audits without converting them into human gold."""
from pathlib import Path
import csv,json,hashlib,datetime,zipfile
ROOT=Path(__file__).resolve().parents[1];V=ROOT/'analysis/validation-access-v2';A=V/'ai-proxy'
def read(p):
 with p.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 report={'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'type':'Two independent AI proxy judgments; NOT human certification','actual_human_annotations':0,'adjudication':'No new gold adjudication; disagreements retained for human review','tasks':{},'source_sha256':{}}
 flagged=[]
 for task,fields in [('content',['use_place_1','use_object_1','use_place_2','use_object_2']),('awareness',['acknowledges_occurrence','claims_content_knowledge'])]:
  blank=read(V/f'blind-{task}-A.csv');aa=read(A/f'annotator-A-{task}.csv');bb=read(A/f'annotator-B-{task}.csv')
  assert len(blank)==len(aa)==len(bb)
  ids=[r['blind_id'] for r in blank];assert len(set(ids))==len(ids)
  labels=fields+(['paraphrase','denial','refusal','foreign_echo_only'] if task=='content' else [])+['uncertain']
  humanfields=labels+['evidence']
  for original,a,b in zip(blank,aa,bb):
   for key,val in original.items():
    if key in humanfields:assert val==''
    else:assert a[key]==b[key]==val,(task,original['blind_id'],key)
   for r in [a,b]:
    assert all(r[k] in ['0','1','U'] for k in labels)
    assert r['evidence'].strip()
   disagree=[f for f in fields if a[f]!=b[f]]
   uncertain=a['uncertain']!='0' or b['uncertain']!='0' or any(a[f]=='U' or b[f]=='U' for f in fields)
   if disagree or uncertain:
    flagged.append({'task':task,'blind_id':original['blind_id'],'response':original['response'],'different_fields':';'.join(disagree),'uncertain_in_either':int(uncertain),'A_labels':json.dumps({f:a[f] for f in labels}),'B_labels':json.dumps({f:b[f] for f in labels}),'A_evidence':a['evidence'],'B_evidence':b['evidence']})
  info={'rows':len(blank),'A_uncertain':sum(r['uncertain']!='0' for r in aa),'B_uncertain':sum(r['uncertain']!='0' for r in bb),'primary_label_disagreement_rows':sum(any(a[f]!=b[f] for f in fields) for a,b in zip(aa,bb)),'review_rows':sum(r['task']==task for r in flagged),'by_field':{}}
  for field in fields:
   pairs=[(a[field],b[field]) for a,b in zip(aa,bb)];defined=[(x,y) for x,y in pairs if x!='U' and y!='U'];info['by_field'][field]={'binary_pairs':len(defined),'binary_agreements':sum(x==y for x,y in defined),'binary_agreement_fraction':sum(x==y for x,y in defined)/len(defined) if defined else None,'pairs_with_U':len(pairs)-len(defined)}
  report['tasks'][task]=info
  for f in [V/f'blind-{task}-A.csv',V/f'blind-{task}-B.csv',A/f'annotator-A-{task}.csv',A/f'annotator-B-{task}.csv']:report['source_sha256'][str(f.relative_to(ROOT))]=sha(f)
 original=read(V/'native-stimuli.csv');native=read(A/'native-stimuli-reviewed.csv');assert len(original)==len(native)
 for o,n in zip(original,native):assert all(n[k]==v for k,v in o.items())
 report['native_stimuli']={'rows':len(native),'AI_meaning_supported':sum(r['ai_meaning_correct']=='1' for r in native),'AI_meaning_uncertain':sum(r['ai_meaning_correct']=='U' for r in native),'AI_uncertain':sum(r['ai_uncertain']!='0' for r in native),'native_human_reviewers':0}
 report['source_sha256'][str((A/'native-stimuli-reviewed.csv').relative_to(ROOT))]=sha(A/'native-stimuli-reviewed.csv')
 report['total_unique_response_items']=sum(t['rows'] for t in report['tasks'].values());report['total_independent_AI_response_annotations']=2*report['total_unique_response_items'];report['review_queue_rows']=len(flagged)
 with (A/'disagreements-for-review.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,list(flagged[0]));w.writeheader();w.writerows(flagged)
 (A/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
 finalfiles=[p for p in A.iterdir() if p.is_file() and (p.name.endswith('-content.csv') or p.name.endswith('-awareness.csv') or p.name.endswith('-method.md') or p.name in ['native-stimuli-reviewed.csv','summary.json','disagreements-for-review.csv','scorer-comparison.json'])]
 with zipfile.ZipFile(ROOT/'deliverables/access-v2-ai-review.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in finalfiles:z.write(p,'ai-proxy/'+p.name)
  z.write(V/'protocol.md','protocol.md');z.write(V/'manifest.json','sampling-manifest.json')
 print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256']},indent=2))
if __name__=='__main__':main()
