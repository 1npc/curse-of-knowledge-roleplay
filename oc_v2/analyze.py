"""Paired skeleton bootstrap for locally frozen v2 endpoints (stdlib only)."""
import collections,random,statistics
from oc_v2.design import BOUNDARIES

def mean(x):return sum(x)/len(x) if x else None
def quantile(x,p):
 x=sorted(x);i=(len(x)-1)*p;lo=int(i);hi=min(lo+1,len(x)-1)
 return x[lo]+(x[hi]-x[lo])*(i-lo)
def holm(ps):
 order=sorted(ps,key=ps.get);out={};last=0
 for rank,k in enumerate(order):last=max(last,min(1.,ps[k]*(len(order)-rank)));out[k]=last
 return out

class Bootstrap:
 def __init__(self,B=2000,seed=20261001):self.B=B;self.seed=seed;self.draws={}
 def indices(self,ids):
  ids=tuple(sorted(ids))
  if ids not in self.draws:
   rng=random.Random(self.seed);n=len(ids);self.draws[ids]=[[rng.randrange(n) for _ in range(n)] for _ in range(self.B)]
  return ids,self.draws[ids]
 def vector(self,values,null=0.):
  ids,draws=self.indices(values);v=[values[i] for i in ids];estimate=mean(v)
  if estimate is None:return {'estimate':None,'n_skeletons':0,'p_one_sided':1.}
  boot=[mean([v[i] for i in take]) for take in draws]
  # Centered bootstrap null, greater-than direction. The one-sided test is
  # separate from the descriptive two-sided percentile interval.
  p=(1+sum(x-estimate>=estimate-null for x in boot))/(len(boot)+1)
  return {'estimate':estimate,'ci95':[quantile(boot,.025),quantile(boot,.975)],'n_skeletons':len(ids),'p_one_sided':p,'null':null}

def model_skeleton_vector(rows,models,field):
 grouped=collections.defaultdict(list)
 for r in rows:grouped[r['model'],r['item']].append(r[field])
 ids=sorted({r['item'] for r in rows});out={}
 for i in ids:
  vals=[mean(grouped[m,i]) for m in models]
  if any(v is None for v in vals):raise ValueError('Missing planned model/skeleton endpoints')
  out[i]=mean(vals)
 return out

def paired_delta(rows,models,field,left,right):
 a=model_skeleton_vector([r for r in rows if left(r)],models,field)
 b=model_skeleton_vector([r for r in rows if right(r)],models,field)
 if set(a)!=set(b):raise ValueError('Paired contrast skeleton sets differ')
 return {i:a[i]-b[i] for i in a}

def confirmatory(rows,models,B=2000,seed=20261001):
 rows=[r for r in rows if r['set']=='confirmatory' and r['model'] in models]
 if not rows:raise ValueError('Confirmatory outcomes are not available')
 boot=Bootstrap(B,seed)
 base=lambda r:r['Q'] in ('content','plan') and r['representation']=='R2' and r['delay']==0
 full=[r for r in rows if base(r) and r['method']=='full' and not r['accessible']]
 h1={b:boot.vector(model_skeleton_vector([r for r in full if r['boundary']==b],models,'D')) for b in BOUNDARIES}
 states={(r['model'],r['item'],r['boundary'],r['version']):r['state_correct'] for r in rows if r['Q']=='state' and not r['accessible']}
 ids=sorted({r['item'] for r in full});counts=collections.defaultdict(lambda:[0.,0.])
 for r in full:
  if states[r['model'],r['item'],r['boundary'],r['version']]:
   c=counts[r['model'],r['item']];c[0]+=r['D'];c[1]+=1
 def conditional(take):
  vals=[]
  for m in models:
   num=sum(counts[m,ids[i]][0] for i in take);den=sum(counts[m,ids[i]][1] for i in take)
   if den:vals.append(num/den)
  return mean(vals)
 obs=conditional(range(len(ids)));_,draws=boot.indices(ids);cb=[conditional(x) for x in draws];defined=[x for x in cb if x is not None]
 h2={'estimate':obs,'eligible_role_responses':sum(v[1] for v in counts.values()),'empty_models':[m for m in models if not sum(counts[m,i][1] for i in ids)],'undefined_bootstraps':len(cb)-len(defined),'p_one_sided':1.}
 if obs is not None and defined:
  h2.update(ci95=[quantile(defined,.025),quantile(defined,.975)],p_one_sided=(1+sum(x-obs>=obs for x in defined))/(len(defined)+1))
 pair=[r for r in rows if base(r) and r['method'] in ('full','view')]
 leak=boot.vector(paired_delta([r for r in pair if not r['accessible']],models,'D',lambda r:r['method']=='full',lambda r:r['method']=='view'))
 useful=boot.vector(paired_delta([r for r in pair if r['accessible']],models,'hit_t',lambda r:r['method']=='view',lambda r:r['method']=='full'),null=-.05)
 aware=[r for r in rows if r['Q']=='awareness' and not r['accessible'] and r['boundary']!='Hear' and r['method'] in ('view','hard')]
 awareness=boot.vector(paired_delta(aware,models,'awareness_correct',lambda r:r['method']=='view',lambda r:r['method']=='hard'))
 h3={'forbidden_leak_reduction':leak,'accessible_target_use_delta':useful,'partial_event_retention_improvement':awareness}
 ps={'H1':max(x['p_one_sided'] for x in h1.values()),'H2':h2['p_one_sided'],'H3':max(x['p_one_sided'] for x in h3.values())}
 return {'H1_components':h1,'H2':h2,'H3_components':h3,'family_p_one_sided':ps,'family_p_holm':holm(ps),'bootstrap_replicates':B,'bootstrap_seed':seed,'status_counts':dict(collections.Counter(r['status'] for r in rows)),'annotation_status':'AI proxy only; genuine human validation pending'}
