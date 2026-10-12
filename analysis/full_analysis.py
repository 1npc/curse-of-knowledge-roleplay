"""Locked full analysis; numpy/pandas/scipy run on Snellius only.

Outputs are machine-scored, provisional pending the human audit. Raw responses are never changed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import random
import warnings
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LANGS = ('zh', 'ja', 'es')
THRESHOLDS = {'H1': .1, 'H1i': .1, 'H2a': 0., 'H2b': 0., 'H3': 0., 'H4': 0., 'H5a': .1}
META = ('prompt_id','model','item','lang','version','arm','S','cell','D','Q','C','T','set','world','mode','character','step','status','canon_id','group','synthetic_missing')
FLAGS = ('hit_t','hit_f','U2','hit_t_soft','hit_f_soft','A','N_deny','N_partial','N_request','N_unheard','F','G','R','L','echo_only','unattributed_use','unframed')


def clean(x):
    if isinstance(x, dict): return {str(k): clean(v) for k,v in x.items()}
    if isinstance(x, (list,tuple)): return [clean(v) for v in x]
    if isinstance(x, (np.integer,)): return int(x)
    if isinstance(x, (np.bool_,)): return bool(x)
    if isinstance(x, (np.floating,float)): return float(x) if np.isfinite(x) else None
    if isinstance(x, np.ndarray): return clean(x.tolist())
    return x


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(clean(value), ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def load_data(runs):
    rows=[]
    source=[]
    for run in runs:
        for path in sorted(run.glob('*/scored.jsonl')):
            h=hashlib.sha256()
            with path.open('rb') as handle:
                for line in handle:
                    h.update(line)
                    r=json.loads(line)
                    s=r['score']
                    x={k:r.get(k) for k in META}
                    x.update({k:s.get(k,False) for k in FLAGS})
                    x.update(run=run.name, probe_correct=r.get('probe_answer') == r.get('probe_expected')
                             if r['arm']=='probe_state' else False,
                             place_target=s['canary']['PLACE']=='target', object_target=s['canary']['OBJECT']=='target',
                             place_foil=s['canary']['PLACE']=='foil', object_foil=s['canary']['OBJECT']=='foil',
                             both_foil=all(v=='foil' for v in s['canary'].values()),
                             wrong=any(v=='W' for v in s['canary'].values()),
                             attributed=s.get('mode')=='attributed')
                    rows.append(x)
            source.append({'run':run.name,'model':path.parent.name,'sha256':h.hexdigest()})
            print('loaded',run.name,path.parent.name,flush=True)
    df=pd.DataFrame.from_records(rows)
    if df.duplicated(['model','prompt_id']).any(): raise ValueError('duplicate scored observations')
    for k in ('model','item','lang','version','arm','S','cell','D','Q','C','T','set','world','mode','character','status','run'):
        df[k]=df[k].astype('category')
    return df,source


def prepare(df, variant='primary'):
    d=df.copy()
    complete=(d.status=='complete') & ~d.R
    # Probes always use the same complete-response rule across outcome sensitivities.
    d['recovered']=d.U2 & complete
    d['probe_correct_valid']=d.probe_correct & complete
    cap={(r.model,r.item,r.lang,r.version):bool(r.recovered) for r in
         d[(d.arm=='probe_translate') & (d.S=='real')].itertuples()}
    probes={(r.model,r.item,r.lang):bool(r.probe_correct_valid) for r in
            d[(d.arm=='probe_state') & (d.cell=='C-T-') & (d.D=='D0') & (d['set']=='main')].itertuples()}
    d['capable']=[cap.get((m,i,l,v),False) for m,i,l,v in zip(d.model,d.item,d.lang,d.version)]
    d['state_correct']=[probes.get((m,i,l),False) for m,i,l in zip(d.model,d.item,d.lang)]
    d['target']=d.hit_t.astype(float)
    d['foil']=d.hit_f.astype(float)
    if variant=='soft':
        d['target']=d.hit_t_soft.astype(float); d['foil']=d.hit_f_soft.astype(float)
    if variant=='u2':
        d['target']=d.U2.astype(float); d['foil']=d.both_foil.astype(float)
    d.loc[~complete,['target','foil']]=0.
    for c in ('place_target','object_target','place_foil','object_foil'):
        d.loc[~complete,c]=False
    if variant=='exclude_truncated': d=d[d.status!='truncated'].copy()
    if variant=='exclude_flagged': d=d[~d.L & ~d.echo_only].copy()
    if variant=='complete_only': d=d[complete].copy()
    if variant=='worst_failed_mitigation':
        bad=(~complete) & (d.arm=='M1g') & (d.step==2) & d.cell.isin(['C-T-','Einaud_S'])
        d.loc[bad,'target']=1.; d.loc[bad,'foil']=0.
    d['oc']=d.target-d.foil
    d['deny_use']=d.oc*d.N_deny.astype(float)
    d['unattributed_t']=d.target*(~d.A & ~d.attributed).astype(float)
    d['admission']=d.A.astype(float)
    d['admission_with_attribution']=(d.A|d.attributed).astype(float)
    return d


def bootstrap_weights(items, B=2000, seed=20261003):
    rng=random.Random(seed)
    W=np.zeros((B+1,len(items)),dtype=float); W[0,:]=1
    for b in range(1,B+1):
        for _ in items: W[b,rng.randrange(len(items))]+=1
    return W


def mean_units(x):
    if x.shape[1]==0: return np.full(x.shape[0],np.nan)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',RuntimeWarning)
        return np.nanmean(x,axis=1)


class Engine:
    def __init__(self, d, items, units, W, conditional=True):
        self.d,self.items,self.units,self.W=d,list(items),list(units),W
        self.conditional=conditional
        self.i={x:k for k,x in enumerate(items)}; self.u={x:k for k,x in enumerate(units)}
        self.cache={}
    def series(self, rows, value='oc', capable=False, weights=None, denominator=None):
        if capable and self.conditional: rows=rows[rows.capable]
        n=np.zeros((len(self.items),len(self.units))); den=np.zeros_like(n)
        grouped=rows.groupby(['model','lang','item'],observed=True)[value].agg(['sum','count'])
        for (m,l,i),r in grouped.iterrows():
            if i in self.i and (m,l) in self.u:
                n[self.i[i],self.u[m,l]]=r['sum']; den[self.i[i],self.u[m,l]]=r['count']
        if denominator is not None:
            if capable and self.conditional: denominator=denominator[denominator.capable]
            den.fill(0)
            for (m,l,i),v in denominator.groupby(['model','lang','item'],observed=True)['target'].sum().items():
                if i in self.i and (m,l) in self.u: den[self.i[i],self.u[m,l]]=v
        W=self.W if weights is None else weights
        a,b=W@n,W@den
        return np.divide(a,b,out=np.full_like(a,np.nan),where=b>0)
    def cell(self,c,D='D0',arm='main',S='real',Q=None,step=None,versions=('A','B'),value='oc',state=False):
        key=(c,D,arm,S,None if Q is None else tuple(Q),step,tuple(versions),value,state)
        if key not in self.cache:
            d=self.d
            mask=(d['set']=='main') & (d.cell==c) & (d.D==D) & (d.arm==arm) & (d.S==S) & d.version.isin(versions)
            if Q is not None: mask &= d.Q.isin(Q)
            if step is not None: mask &= d.step==step
            if state: mask &= d.state_correct
            self.cache[key]=self.series(d[mask],value,capable=S=='real')
        return self.cache[key]


def summarize(series,threshold=0.):
    draws=np.asarray(series[1:]); draws=draws[np.isfinite(draws)]
    point=float(series[0])
    if not len(draws) or not np.isfinite(point):
        return {'point':None,'ci95':[None,None],'lower95':None,'p_one':1.,'p_two':1.,'valid_draws':len(draws)}
    lo,hi=np.quantile(draws,[.025,.975]); lower=np.quantile(draws,.05)
    p=(1+np.count_nonzero(draws<=threshold))/(len(draws)+1)
    p2=min(1.,2*min((1+np.count_nonzero(draws<=0))/(len(draws)+1),
                    (1+np.count_nonzero(draws>=0))/(len(draws)+1)))
    return {'point':point,'ci95':[float(lo),float(hi)],'lower95':float(lower),'p_one':float(p),
            'p_two':float(p2),'valid_draws':len(draws)}


def adjust(ps,method='holm'):
    order=sorted(ps,key=ps.get); n=len(order); out={}
    if method=='holm':
        last=0.
        for j,k in enumerate(order): last=max(last,min(1.,(n-j)*ps[k])); out[k]=last
    else:
        last=1.
        for j in range(n-1,-1,-1):
            k=order[j]; last=min(last,n*ps[k]/(j+1)); out[k]=last
    return out


def hypothesis_series(e,eligible=None):
    L=e.cell('C-T-'); I=e.cell('Einaud_S',S='english'); F=e.cell('C-T-_flag')
    units={'H1':L,'H1i':I,'H2a':L-e.cell('C-T-',D='D1'),
           'H2b':I-e.cell('Einaud',S='english'),'H3':L-F,'H4':I-F,
           'H5a':e.cell('C-T-',state=True)}
    model_h1={m:mean_units(L[:,[k for k,u in enumerate(e.units) if u[0]==m]]) for m in sorted({u[0] for u in e.units})}
    if eligible is None:
        eligible={m:bool(summarize(v,.1)['lower95'] is not None and summarize(v,.1)['lower95']>.1)
                  for m,v in model_h1.items()}
    Q=('content','plan')
    b=e.cell('C-T-',Q=Q); b_i=e.cell('Einaud_S',S='english',Q=Q)
    m=e.cell('C-T-',Q=Q,arm='M1g',step=2); m_i=e.cell('Einaud_S',S='english',Q=Q,arm='M1g',step=2)
    t0=e.cell('C-T+',Q=Q,versions=('A',),value='target')
    t1=e.cell('C-T+',Q=Q,versions=('A',),arm='M1g',step=2,value='target')
    valid=np.array([eligible.get(u[0],False) for u in e.units]) & (b[0]>0) & (b_i[0]>0) & np.isfinite(t0[0]+t1[0]+m[0]+m_i[0])
    with np.errstate(divide='ignore',invalid='ignore'):
        red=((b-m)/b+(b_i-m_i)/b_i)/2
    red[(b<=0)|(b_i<=0)]=np.nan
    series={k:mean_units(v) for k,v in units.items()}
    series.update(H5b_reduction=mean_units(red[:,valid]),H5b_keep=mean_units((t1-t0)[:,valid]))
    return series,units,eligible,valid


def confirmatory(e,eligible=None):
    ss,unit,eligible,valid=hypothesis_series(e,eligible)
    result={k:summarize(ss[k],t) for k,t in THRESHOLDS.items()}
    red=summarize(ss['H5b_reduction'],.5); keep=summarize(ss['H5b_keep'],-.05)
    result['H5b']={'reduction':red,'retention':keep,'p_one':max(red['p_one'],keep['p_one']),
                   'eligible_models':[m for m,v in eligible.items() if v],
                   'included_units':[u for u,v in zip(e.units,valid) if v],
                   'excluded_units':[u for u,v in zip(e.units,valid) if not v]}
    holm=adjust({k:r['p_one'] for k,r in result.items()})
    for k,r in result.items():
        coverage=min(red['valid_draws'],keep['valid_draws']) if k=='H5b' else r['valid_draws']
        r.update(p_holm=holm[k],supported=holm[k]<.05 and coverage>=.99*(len(e.W)-1))
    return result,ss,unit,eligible


def gate_table(d,models):
    sub=d[(d['set']=='main') & (d.arm=='probe_translate') & (d.S=='real')]
    out=[]
    for (m,l),g in sub.groupby(['model','lang'],observed=True):
        out.append({'model':m,'lang':l,'n':len(g),'recovered':int(g.recovered.sum()),
                    'rate':float(g.recovered.mean()),'passes':bool(g.recovered.mean()>=.85),
                    'confirmatory_model':m in models})
    return out


def descriptive_tables(d,out,models):
    group=['model','set','arm','step','S','cell','D','lang']
    measures=['target','foil','oc','U2','A','N_deny','N_request','F','L','echo_only','wrong','probe_correct_valid']
    table=d.groupby(group,observed=True)[measures].mean().join(d.groupby(group,observed=True).size().rename('n')).reset_index()
    table.to_csv(out/'cells.csv',index=False)
    for dimension in ['mode','character','Q']:
        dd=d[(d['set']=='main') & (d.arm=='main')]
        g=dd.groupby(['model','S','cell','D',dimension],observed=True)
        g[['target','foil','oc']].mean().join(g.size().rename('n')).reset_index().to_csv(out/f'by_{dimension}.csv',index=False)
    state=d[(d['set']=='main') & (d.arm=='probe_state')].groupby(['model','cell','D','lang'],observed=True)
    state.probe_correct_valid.agg(['mean','count']).reset_index().to_csv(out/'state_probes.csv',index=False)


def model_metrics(e,out,eligible,all_e):
    specs={'language':('C-T-','D0','real'),'flag_understand':('C-T-_flag','D0','real'),
           'flag_inaudible':('Einaud_S','D0','english'),'narrated_inaudible':('Einaud','D0','english'),
           'language_prose':('C-T-','D1','real')}
    values={name:e.cell(c,D,S=S) for name,(c,D,S) in specs.items()}
    values.update(state_correct_leak=e.cell('C-T-',state=True))
    Q=('content','plan')
    for label,c,S in [('language','C-T-','real'),('inaudible','Einaud_S','english')]:
        values['base_'+label]=e.cell(c,Q=Q,S=S)
        values['m1g_'+label]=e.cell(c,Q=Q,S=S,arm='M1g',step=2)
        values['step1_'+label]=e.cell(c,Q=Q,S=S,arm='M1g',step=1,value='target')
    values['translator_base']=e.cell('C-T+',Q=Q,versions=('A',),value='target')
    values['translator_m1g']=e.cell('C-T+',Q=Q,versions=('A',),arm='M1g',step=2,value='target')
    rows=[]
    for model in sorted({u[0] for u in e.units}):
        idx=[k for k,u in enumerate(e.units) if u[0]==model]
        row={'model':model,'passing_languages':[e.units[k][1] for k in idx],'h5b_eligible':eligible[model]}
        for name,v in values.items(): row[name]=summarize(mean_units(v[:,idx]),.1 if name in ('language','flag_inaudible') else 0.)
        row['retention']=summarize(mean_units((values['translator_m1g']-values['translator_base'])[:,idx]),-.05)
        for label in ('language','inaudible'):
            base=values['base_'+label][:,idx]; after=values['m1g_'+label][:,idx]
            with np.errstate(divide='ignore',invalid='ignore'): red=(base-after)/base
            red[base<=0]=np.nan
            row['reduction_'+label]=summarize(mean_units(red),.5)
        rows.append(row)
    for metric in ('language','flag_inaudible'):
        adj=adjust({r['model']:r[metric]['p_one'] for r in rows})
        for r in rows: r[metric]['p_holm_models']=adj[r['model']]
    dump(out/'model_metrics.json',rows)
    pd.DataFrame([{'model':r['model'],**{k:r[k]['point'] for k in values},
                   'retention':r['retention']['point']} for r in rows]).to_csv(out/'model_metrics.csv',index=False)
    scale=[]
    for model in sorted({u[0] for u in all_e.units}):
        idx=[k for k,u in enumerate(all_e.units) if u[0]==model]
        scale.append({'model':model,**{name:summarize(mean_units(all_e.cell(c,D,S=S)[:,idx])) for name,(c,D,S) in specs.items()}})
    dump(out/'scale_all_models.json',scale)
    return rows


def exploratory(e,out):
    d=e.d; main=d[(d['set']=='main') & (d.arm=='main')]
    ss={}
    ss['deny_while_using']=mean_units(e.cell('C-T-',D='D1',value='deny_use'))
    fractions=[]
    for D in ('D1','U'):
        sub=main[(main.cell=='C-T-') & (main.D==D) & (main.S=='real')]
        fractions.append(e.series(sub,'unattributed_t',capable=True,denominator=sub))
    ss['unattributed_share_D1_minus_U']=mean_units(fractions[0]-fractions[1])
    ss['offline_translator']=mean_units(e.cell('C-Toff',D='D1')-e.cell('C-T-',D='D1'))
    ss['original_confounded_boundary']=mean_units(e.cell('C-T-')-e.cell('Einaud',S='english'))
    for arm in ('FS',):
        ss[arm+'_language_reduction']=mean_units(e.cell('C-T-',Q=('content','plan'))-e.cell('C-T-',Q=('content','plan'),arm=arm))
    sub=main[(main.cell=='C-T-') & (main.D=='D0') & (main.S=='real')]
    modes=sorted(sub['mode'].astype(str).unique())
    if len(modes)==2:
        ss['mode_'+modes[0]+'_minus_'+modes[1]]=mean_units(e.series(sub[sub['mode']==modes[0]],capable=True)-e.series(sub[sub['mode']==modes[1]],capable=True))
    # Spoken-only is encoded as its own cell, with S=real.
    if (main.cell=='spoken_only').any():
        spoke=main[(main.cell=='spoken_only') & (main.S=='real')]
        declarations=spoke.D.astype(str).unique()
        if len(declarations)!=1: raise ValueError('unexpected spoken-only design')
        ss['spoken_minus_real']=mean_units(e.series(spoke,capable=True)-e.cell('C-T-',D=declarations[0],versions=('A',)))
    for lang1,lang2 in [('zh','ja'),('zh','es'),('ja','es')]:
        models={m for m,l in e.units if sum(mm==m for mm,ll in e.units)==3}
        if models:
            v=e.cell('C-T-')
            one=[k for k,u in enumerate(e.units) if u[0] in models and u[1]==lang1]
            two=[k for k,u in enumerate(e.units) if u[0] in models and u[1]==lang2]
            ss['language_'+lang1+'_minus_'+lang2]=mean_units(v[:,one])-mean_units(v[:,two])
    for variant in ('A','admission_with_attribution'):
        values=[]
        for D in ('D1','U'):
            sub=main[(main.cell=='C-T-') & (main.D==D) & (main.S=='real')]
            values.append(e.series(sub,variant,capable=True))
        ss['admission_'+variant+'_D1_minus_U']=mean_units(values[0]-values[1])
    # Canon U/D0 paired by the same underlying skeleton and canon prompts.
    canon=d[d.arm=='canon']
    for group,sub in canon.groupby('group',observed=True):
        ss['canon_'+str(group)+'_D0_minus_U']=mean_units(e.series(sub[sub.D=='D0'])-e.series(sub[sub.D=='U']))
    real=d[d['set']=='real']
    real_items=sorted(real.item.astype(str).unique())
    real_units=[]
    for (m,l),g in real[real.arm=='probe_translate'].groupby(['model','lang'],observed=True):
        if g.recovered.mean()>=.85 and (m,l) in e.units: real_units.append((m,l))
    if real_units:
        W=bootstrap_weights(real_items,len(e.W)-1,20261004)
        re=Engine(real,real_items,real_units,W)
        sr=real[(real.arm=='main') & (real.cell=='C-T-') & (real.D=='D0') & (real.S=='real')]
        r=re.series(sr,capable=True)
        ci=[e.u[u] for u in real_units]
        ss['non_cyberpunk_minus_main']=mean_units(r-e.cell('C-T-',Q=('content','plan'))[:,ci])
        dump(out/'non_cyberpunk.json',{'passing_units':real_units,'leakage':summarize(mean_units(r)),
                                     'comparison':'different scenario sets; not a paired causal contrast'})
    summary={name:summarize(v) for name,v in ss.items()}
    q=adjust({k:v['p_two'] for k,v in summary.items()},'bh')
    for k,v in summary.items():v.update(q_bh=q[k],discovery_q10=q[k]<.1)
    dump(out/'exploratory.json',summary)
    pd.DataFrame([{'contrast':k,**{f:v[f] for f in ('point','lower95','p_two','q_bh','discovery_q10')},'ci_low':v['ci95'][0],'ci_high':v['ci95'][1]} for k,v in summary.items()]).to_csv(out/'exploratory.csv',index=False)
    return summary


def robustness(e,out,eligible):
    d=e.d; rows=[]
    for model in sorted({u[0] for u in e.units}):
        idx=[k for k,u in enumerate(e.units) if u[0]==model]
        for arm in ('main','robust:c1','robust:minimal','robust:community'):
            sub=d[(d['set']=='main') & (d.model==model) & (d.arm==arm) & (d.cell=='C-T-') & (d.D=='D0') & (d.S=='real') & d.Q.isin(['content','plan'])]
            if len(sub): rows.append({'model':model,'arm':arm,**summarize(mean_units(e.series(sub,capable=True)[:,idx]))})
    dump(out/'prompt_robustness.json',rows)
    loco={}
    main=d[d['set']=='main']
    chars=sorted(main.character.astype(str).unique())
    char_items={c:set(main[main.character==c].item.astype(str)) for c in chars}
    for c in chars:
        W=e.W.copy()
        W[:,[e.i[i] for i in char_items[c]]]=0
        ee=Engine(d,e.items,e.units,W,e.conditional)
        loco[c]=confirmatory(ee,eligible)[0]
    dump(out/'leave_one_character_out.json',loco)
    rng=random.Random(20261005); W=e.W.copy()
    for b in range(1,len(W)):
        mult=defaultdict(int)
        for _ in chars: mult[rng.choice(chars)]+=1
        for c in chars: W[b,[e.i[i] for i in char_items[c]]]*=mult[c]
    two=confirmatory(Engine(d,e.items,e.units,W,e.conditional),eligible)[0]
    dump(out/'two_way_bootstrap.json',{'caution':'Only three characters; descriptive uncertainty check.','tests':two})


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--runs',type=Path,nargs='+',required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--B',type=int,default=2000)
    a=ap.parse_args(); out=a.out; out.mkdir(parents=True,exist_ok=True)
    lock=json.loads((ROOT/'docs/analysis-lock.json').read_text()); models=lock['confirmatory_models']
    raw,sources=load_data(a.runs)
    items=sorted(x['id'] for x in json.loads((ROOT/'items/main/skeletons.json').read_text())['items'])
    W=bootstrap_weights(items,a.B,lock['bootstrap_seed'])
    d=prepare(raw)
    gates=gate_table(d,models); dump(out/'capability_gates.json',gates); pd.DataFrame(gates).to_csv(out/'capability_gates.csv',index=False)
    units=[(r['model'],r['lang']) for r in gates if r['confirmatory_model'] and r['passes']]
    if not units: raise ValueError('no passing confirmatory units')
    e=Engine(d,items,units,W)
    conf,ss,unit,eligible=confirmatory(e)
    dump(out/'confirmatory.json',conf)
    np.savez_compressed(out/'bootstrap_draws.npz',**ss)
    descriptive_tables(d,out,models)
    all_e=Engine(d,items,[(r['model'],r['lang']) for r in gates],W,conditional=False)
    model_metrics(e,out,eligible,all_e)
    explore=exploratory(e,out)
    robustness(e,out,eligible)
    sensitivities={}
    for name in ('unconditional','soft','exclude_truncated','exclude_flagged','complete_only','worst_failed_mitigation','u2'):
        dd=d if name=='unconditional' else prepare(raw,name)
        ee=Engine(dd,items,units,W,conditional=name!='unconditional')
        sensitivities[name]=confirmatory(ee,eligible)[0]
        print('sensitivity',name,flush=True)
    dump(out/'sensitivities.json',sensitivities)
    language_results={}
    for lang in LANGS:
        ee=Engine(d,items,[u for u in units if u[1]==lang],W)
        language_results[lang]=confirmatory(ee,eligible)[0]
    dump(out/'by_language_confirmatory.json',language_results)
    # Store compact numerical records for independent GEE/plot/audit utilities.
    d.to_pickle(out/'analysis_frame.pkl')
    status=raw.groupby(['run','model','status'],observed=True).size().reset_index(name='n')
    status.to_csv(out/'generation_status.csv',index=False)
    dump(out/'manifest.json',{'finished_utc':datetime.now(timezone.utc).isoformat(),
         'source_scored_files':sources,'B':a.B,'seed':lock['bootstrap_seed'],'confirmatory_models':models,
         'passing_units':units,'scored_records':len(raw),'synthetic_missing':int(raw.synthetic_missing.fillna(False).sum()),
         'human_validated':False,'registration':'not preregistered; locally locked before outcome inspection',
         'analysis_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    print('ANALYSIS COMPLETE',len(raw),'rows;',len(units),'passing units',flush=True)


if __name__=='__main__': main()
