"""Write v2 cell estimates and the pre-generation confirmatory family."""
from pathlib import Path
import argparse,json,sys,collections,hashlib
ROOT=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(ROOT))
from oc_v2.analyze import Bootstrap,model_skeleton_vector,confirmatory,paired_delta

def main():
 p=argparse.ArgumentParser();p.add_argument('--scores',type=Path,nargs='+',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 rows=[]
 for f in a.scores:rows.extend(json.loads(x) for x in f.read_text().splitlines() if x.strip())
 unique={(r['model'],r['set'],r['prompt_id']) for r in rows};assert len(unique)==len(rows),'duplicate scored endpoints'
 groups=collections.defaultdict(list);keys=('model','set','boundary','representation','method','Q','delay','accessible')
 for r in rows:groups[tuple(r[k] for k in keys)].append(r)
 boot=Bootstrap();cells=[]
 for key,group in sorted(groups.items()):
  q=key[5];field={'state':'state_correct','translate':'U2','decision':'choose_A','awareness':'awareness_correct'}.get(q,'D')
  cell=dict(zip(keys,key));cell.update(metric=field,**boot.vector(model_skeleton_vector(group,[key[0]],field)),planned=len(group),complete=sum(r['valid'] for r in group));cells.append(cell)
 lock=json.loads((ROOT/'docs/access-v2/spec-lock.json').read_text())
 final=json.loads((ROOT/'docs/access-v2/final-lock.json').read_text());contrasts=[]
 discovery=[r for r in rows if r['set']=='discovery'];available={r['model'] for r in discovery}
 def contrast(label,scope,models,field,left,right):
  models=[m for m in models if m in available]
  if not models:return
  selected=[r for r in scope if r['model'] in models];delta=paired_delta(selected,models,field,left,right)
  v=boot.vector(delta);v.pop('p_one_sided',None);v.pop('null',None);contrasts.append({'contrast':label,'models':models,'metric':field,**v})
 role=lambda r:r['Q'] in ('content','plan') and r['delay']==0
 for boundary in ('Hear','Understand','See','Receive'):
  byb=[r for r in discovery if r['boundary']==boundary]
  e1=[r for r in byb if role(r) and r['representation']=='R2' and r['method']=='full']
  contrast('E1 accessible-minus-inaccessible '+boundary,e1,lock['main_models'],'D',lambda r:r['accessible'],lambda r:not r['accessible'])
  e2=[r for r in byb if role(r) and r['item'] in final['subsets']['E2'] and r['method']=='full' and not r['accessible']]
  for rep in ('R1','R3'):contrast('E2 '+rep+'-minus-R2 '+boundary,e2,lock['main_models'],'D',lambda r:r['representation']==rep,lambda r:r['representation']=='R2')
  e3=[r for r in byb if role(r) and r['item'] in final['subsets']['E3']]
  for method in ('prose','self_filter','hard','view'):
   control=lambda r:r['method']=='full' and r['representation']=='R2'
   treatment=lambda r:r['representation']=='R3' and r['method']=='full' if method=='prose' else r['representation']=='R2' and r['method']==method
   contrast('E3 forbidden leak reduction '+method+' '+boundary,[r for r in e3 if not r['accessible']],lock['method_models'],'D',control,treatment)
   contrast('E3 accessible use delta '+method+' '+boundary,[r for r in e3 if r['accessible']],lock['method_models'],'hit_t',treatment,control)
  e5=[r for r in byb if r['Q']=='plan' and r['item'] in final['subsets']['E5_E6'] and not r['accessible'] and r['representation']=='R2']
  for method in ('full','view'):
   for delay in (2,4):contrast(f'E5 delay{delay}-minus-delay0 {method} {boundary}',[r for r in e5 if r['method']==method],lock['persistence_models'],'D',lambda r:r['delay']==delay,lambda r:r['delay']==0)
   e6=[r for r in byb if r['Q']=='decision' and r['method']==method and not r['accessible']]
   contrast('E6 fixed-A choice A-minus-B '+method+' '+boundary,e6,lock['persistence_models'],'choose_A',lambda r:r['version']=='A',lambda r:r['version']=='B')
 report={'cells':cells,'exploratory_paired_contrasts':contrasts,'cell_caution':'Descriptive cells cover their planned union. Scientific contrasts use the frozen paired E2/E3/E5/E6 skeleton subsets, never compare unmatched union cells.','source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in a.scores},'annotation_status':'AI proxy only; real human assessment pending','confirmatory':None}
 expected=set(lock['confirmatory_models']);available={r['model'] for r in rows if r['set']=='confirmatory'}
 if expected<=available:report['confirmatory']=confirmatory(rows,lock['confirmatory_models'])
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print('Scored cells',len(cells),'confirmatory ready',report['confirmatory'] is not None)
if __name__=='__main__':main()
