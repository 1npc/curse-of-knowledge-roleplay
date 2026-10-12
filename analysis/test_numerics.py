"""Remote-only numeric regression tests; all data are synthetic."""
import random
import unittest
import numpy as np
import pandas as pd
from full_analysis import Engine, bootstrap_weights, hypothesis_series, prepare, adjust, summarize, FLAGS
from confirmatory import Units, statistics


class TestNumerics(unittest.TestCase):
    def fixture(self):
        rng=random.Random(23); records=[]; old={}; items=[f'S{i:02}' for i in range(1,9)]
        def add(model,item,lang,version,arm,cell,S,D='D0',Q='content',step=1,probe=False):
            ht=rng.random()<(.2 if arm=='M1g' else .8); hf=rng.random()<.06
            score=dict(R=False,hit_t=ht,hit_f=hf,U2=probe,LD_deny=False)
            r=dict(model=model,item=item,lang=lang,version=version,arm=arm,cell=cell,S=S,D=D,Q=Q,step=step,
                   status='complete',score=score,probe_answer='no',probe_expected='no')
            old.setdefault(model,[]).append(r)
            x={k:v for k,v in r.items() if k!='score'}
            x.update({k:score.get(k,False) for k in FLAGS})
            x.update({'set':'main','world':'cyberpunk','mode':'direct','character':'Kerry','probe_correct':True,
                      'place_target':ht,'object_target':False,'place_foil':hf,'object_foil':False,'both_foil':False,
                      'attributed':False,'synthetic_missing':False,'prompt_id':str(len(records))})
            records.append(x)
        for model in ['m1','m2']:
            for item in items:
                for lang in ['zh','ja']:
                    for v in ['A','B']: add(model,item,lang,v,'probe_translate','C+T-','real',probe=True)
                    add(model,item,lang,'A','probe_state','C-T-','real')
                    for cell,S,D in [('C-T-','real','D0'),('C-T-','real','D1'),('C-T-_flag','real','D0'),
                                     ('Einaud_S','english','D0'),('Einaud','english','D0'),('C-T+','real','D0')]:
                        for v in ['A','B']:
                            for Q in ['content','plan']:
                                add(model,item,lang,v,'main',cell,S,D,Q)
                                if D=='D0' and cell in ('C-T-','Einaud_S','C-T+'):
                                    add(model,item,lang,v,'M1g',cell,S,D,Q,step=2)
        return prepare(pd.DataFrame(records)),old,items
    def test_aggregated_estimands_equal_row_reference(self):
        d,data,items=self.fixture(); old=Units(data); old.eligible_h5b={'m1':True,'m2':True}
        units=old.passing(); W=bootstrap_weights(items,12)
        e=Engine(d,items,units,W)
        series,_,_,_=hypothesis_series(e,{'m1':True,'m2':True})
        for b in range(len(W)):
            ref=statistics(old,dict(zip(items,W[b].astype(int))))
            for h in ref:
                self.assertAlmostEqual(series[h][b],ref[h],places=12,msg=f'{h}, draw {b}')
    def test_status_handling_keeps_missing_in_denominator(self):
        d,_,items=self.fixture()
        idx=d[(d.arm=='M1g') & (d.cell=='C-T-')].index[0]
        d.loc[idx,'status']='upstream_failure'
        primary=prepare(d); worst=prepare(d,'worst_failed_mitigation')
        self.assertEqual(len(primary),len(worst))
        self.assertEqual(primary.loc[idx,'target'],0.)
        self.assertEqual(worst.loc[idx,'target'],1.)
    def test_adjustments_and_threshold(self):
        self.assertEqual(adjust({'a':.01,'b':.03,'c':.04}),{'a':.03,'b':.06,'c':.06})
        self.assertAlmostEqual(adjust({'a':.01,'b':.03,'c':.04},'bh')['b'],.04)
        self.assertEqual(summarize(np.zeros(21),0)['p_one'],1.)


if __name__=='__main__':unittest.main()
