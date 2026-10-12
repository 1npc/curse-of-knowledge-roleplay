"""Scientific invariants for the new matched-access experiment."""
import unittest,json,collections
from oc_v2.design import items,make_record,world_state,project,BOUNDARIES,balanced_indices,LANGS
from oc_v2.score import score_record
from oc.build import fill_next_step
from oc_v2.analyze import Bootstrap,paired_delta,holm,confirmatory

class AccessInvariants(unittest.TestCase):
 def test_access_pair_differs_only_by_one_boundary_field(self):
  it=items('discovery',96)[0]
  for b in BOUNDARIES:
   a=world_state(it,b,'A',False,'R2');z=world_state(it,b,'A',True,'R2')
   ae=a.pop('events');ze=z.pop('events');self.assertEqual(a,z)
   changed=[k for k in ae[0] if ae[0][k]!=ze[0][k]];self.assertEqual(len(changed),1)
   self.assertIs(ae[0][changed[0]],False);self.assertIs(ze[0][changed[0]],True)
 def test_hidden_view_invariant_to_counterfactual_content(self):
  for it in items('discovery',96):
   for b in BOUNDARIES:
    for hard in (False,True):self.assertEqual(project(it,b,'A',False,hard),project(it,b,'B',False,hard))
    shell=project(it,b,'A',False)['observations'];self.assertEqual(bool(shell),b!='Hear')
 def test_disjoint_materials_and_balanced_subsets(self):
  d=items('discovery',96);c=items('confirmatory',96);p=items('pilot',20)
  self.assertEqual(len({(x['character'],x['scene']) for x in d}),96)
  self.assertEqual(len({(x['character'],x['scene']) for x in c}),96)
  self.assertFalse({x['id'] for x in d}&{x['id'] for x in c+p})
  self.assertFalse({(x['character'],x['scene']) for x in c}&{(x['character'],x['scene']) for x in d+p})
  for domain in ('social','search','planning','coordination'):
   group=[x for x in d if x['domain']==domain]
   for k in ('lang','character'):self.assertEqual(sorted(collections.Counter(x[k] for x in group).values()),[8,8,8])
  for n,seed in [(6,20261001),(12,20261002),(8,20261003)]:
   take=balanced_indices(d,n,seed);self.assertEqual(len(take),4*n)
   for domain in ('social','search','planning','coordination'):
    group=[d[i] for i in take if d[i]['domain']==domain];self.assertEqual(len(group),n)
    for k in ('lang','character'):
     v=collections.Counter(x[k] for x in group).values();self.assertLessEqual(max(v)-min(v),1)
 def test_score_failures_and_target_minus_foil(self):
  it=items('discovery',96)[0];p=make_record(it,'Receive','A',False)
  key=p['prompt_id'];gold=it['langs'][it['lang']]['A']['gold'][0]
  def s(text,status='complete'):return score_record(p,it,{key:{'text':text,'status':status,'finish_reason':'stop'}})
  self.assertEqual(s(gold)['D'],1)
  self.assertEqual(s(it['langs'][it['lang']]['B']['gold'][0])['D'],-1)
  self.assertEqual(s(gold,'truncated')['D'],0)
  self.assertEqual(score_record(p,it,{})['status'],'missing_planned')
 def test_self_filter_substitution_is_escaped_and_missing_endpoint_zero(self):
  it=items('discovery',96)[0];p=make_record(it,'Receive','A',False,method='self_filter')
  text='a "quoted" line\nwith a new line';msgs=fill_next_step(p,text)
  self.assertIn(json.dumps(text,ensure_ascii=False),msgs[0]['content'])
  self.assertEqual(score_record(p,it,{p['prompt_id']:{'text':text,'status':'complete'}})['D'],0)
 def test_awareness_distinguishes_retention_from_actual_input(self):
  it=items('discovery',96)[0];p=make_record(it,'See','A',False,method='hard',q='awareness')
  r=score_record(p,it,{p['prompt_id']:{'text':'No.','status':'complete','finish_reason':'stop'}})
  self.assertEqual(r['awareness_correct'],0);self.assertEqual(r['input_awareness_correct'],1)
 def test_paired_bootstrap_keeps_skeletons_and_model_weighting(self):
  rows=[]
  for m in ['a','b']:
   for i,x in [('one',1),('two',0)]:
    for method in ['full','view']:
     rows.append({'model':m,'item':i,'method':method,'D':x if method=='full' else 0})
  delta=paired_delta(rows,['a','b'],'D',lambda r:r['method']=='full',lambda r:r['method']=='view')
  self.assertEqual(delta,{'one':1.,'two':0.})
  b=Bootstrap(B=50);self.assertEqual(b.vector(delta)['estimate'],.5)
  self.assertEqual(b.indices(delta),b.indices({'one':8,'two':9}))
  self.assertEqual(holm({'a':.01,'b':.04,'c':.2}),{'a':.03,'b':.08,'c':.2})
 def test_confirmatory_family_and_empty_state_correct_model(self):
  rows=[]
  for m in ['a','b']:
   for item in ['one','two']:
    for boundary in BOUNDARIES:
     for ver in ['A','B']:
      for access in [False,True]:
       base={'model':m,'item':item,'set':'confirmatory','boundary':boundary,'version':ver,'accessible':access,'representation':'R2','delay':0,'status':'complete'}
       if not access:rows.append({**base,'method':'probe','Q':'state','state_correct':int(m=='a')})
       for method in ['full','view','hard']:
        for q in ['content','plan']:rows.append({**base,'method':method,'Q':q,'D':int(method=='full' or access),'hit_t':int(method=='full' or access)})
        rows.append({**base,'method':method,'Q':'awareness','awareness_correct':int(method!='hard' or access)})
  r=confirmatory(rows,['a','b'],B=200)
  self.assertEqual(r['H2']['estimate'],1.);self.assertEqual(r['H2']['empty_models'],['b'])
  self.assertEqual(r['H3_components']['accessible_target_use_delta']['estimate'],0.)
  self.assertEqual(r['H3_components']['partial_event_retention_improvement']['estimate'],1.)
  self.assertTrue(all(x<.05 for x in r['family_p_holm'].values()))
if __name__=='__main__':unittest.main()
