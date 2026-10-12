"""Descriptive secondary checks; definitions completed after main outcome inspection.

No additional result enters the locked eight-test family. DI is suppressed when any
component probability is below .05 or at one, following the proposal's sparse-rate rule.
"""
import argparse,json
from collections import defaultdict
from pathlib import Path
import numpy as np
import pandas as pd
from full_analysis import Engine,bootstrap_weights,mean_units,summarize,dump,ROOT


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--run',type=Path,required=True);a=ap.parse_args()
    d=pd.read_pickle(a.results/'analysis_frame.pkl');manifest=json.loads((a.results/'manifest.json').read_text())
    d['wrong']=d.wrong & (d.status=='complete') & ~d.R
    units=[tuple(x) for x in manifest['passing_units']];models=manifest['confirmatory_models']
    items={x['id']:x for x in json.loads((ROOT/'items/main/skeletons.json').read_text())['items']}
    W=bootstrap_weights(sorted(items),manifest['B'],manifest['seed']);e=Engine(d,sorted(items),units,W)
    main=d[(d['set']=='main')&(d.arm=='main')];out={}
    SU=e.cell('C+T-');OC=e.cell('C-T-');E=e.cell('E',S='english')
    with np.errstate(divide='ignore',invalid='ignore'):ratio=OC/SU
    ratio[SU<=0]=np.nan
    out['sensitivity_SU']=summarize(mean_units(SU));out['english_ceiling']=summarize(mean_units(E))
    out['DSI']=summarize(mean_units(SU-OC));out['leakage_ratio_OC_SU']=summarize(mean_units(ratio))
    out['channel_ignoring_N_deny']=summarize(mean_units(e.cell('C-T+',value='N_deny')))
    out['SU_minus_translator']=summarize(mean_units(SU-e.cell('C-T+')))
    sub=main[(main.cell=='C-T-')&(main.D=='D1')&(main.S=='real')&main.Q.isin(['content','plan'])&~main.R]
    out['deny_use_original_proposal_Q_content_plan_nonrefusal']=summarize(mean_units(e.series(sub,'deny_use',capable=True)),.05)
    # Original no-admission-only variant, compared to the narrower unattributed definition.
    main=main.copy();main['no_admission_use']=main.target*(~main.A).astype(float)
    shares=[]
    for D in ('D1','U'):
        sub=main[(main.cell=='C-T-')&(main.D==D)&(main.S=='real')]
        shares.append(e.series(sub,'no_admission_use',capable=True,denominator=sub))
    out['no_admission_share_D1_minus_U']=summarize(mean_units(shares[0]-shares[1]))
    sub=main[(main.cell=='C-T-')&(main.D=='D0')&(main.S=='real')&~main.F]
    out['H1_exclude_channel_claims']=summarize(mean_units(e.series(sub,capable=True)),.1)
    # DI orientation is explicitly labeled here, because the frozen draft did not define it.
    di=[]
    for model in models+['POOLED']:
        idx=[j for j,u in enumerate(units) if model=='POOLED' or u[0]==model]
        v={}
        for D in ('U','D1'):
            for metric in ('admission','target'):
                v[D+'_'+metric]=mean_units(e.cell('C-T-',D=D,Q=('content',),value=metric)[:,idx])
        point={k:float(x[0]) for k,x in v.items()};valid=all(.05<=x<1 for x in point.values())
        absolute=(v['D1_admission']-v['U_admission'])-(v['D1_target']-v['U_target'])
        result={'model':model,'components':point,'absolute_DID':summarize(absolute),'logit_DI':None}
        if valid:
            with np.errstate(divide='ignore',invalid='ignore'):
                lv={k:np.log(x/(1-x)) for k,x in v.items()}
            result['logit_DI']=summarize((lv['D1_admission']-lv['U_admission'])-(lv['D1_target']-lv['U_target']))
        else:result['reason']='At least one rate < .05 or at 1; logit index suppressed, not imputed.'
        di.append(result)
    dump(a.results/'secondary_checks.json',{'status':'secondary/descriptive; implementation completed after main inspection',
        'DI_definition':'[logit A(D1)-logit A(U)] - [logit target(D1)-logit target(U)], Q-content, capability-conditioned',
        'estimates':out,'DI':di})
    per=[]
    for model in models:
        idx=[j for j,u in enumerate(units) if u[0]==model]
        gates=[x['rate'] for x in json.loads((a.results/'capability_gates.json').read_text()) if x['model']==model]
        per.append({'model':model,'translation_recovery':np.mean(gates),'OC':mean_units(OC[:,idx])[0],'SU':mean_units(SU[:,idx])[0],
                    'OC_over_SU':mean_units(ratio[:,idx])[0],'english_ceiling':mean_units(E[:,idx])[0]})
    pd.DataFrame(per).to_csv(a.results/'capability_normalized_models.csv',index=False)
    # Noise calibration: same A-version rows, capability-conditioned real versus unconditional noise.
    real=main[(main.cell=='C-T-')&(main.D=='D0')&(main.S=='real')&(main.version=='A')]
    noise=main[(main.cell=='C-T-')&(main.D=='D0')&(main.S=='noise')&(main.version=='A')]
    rt=e.series(real,'target',capable=True);rw=e.series(real,'wrong',capable=True)
    nt=e.series(noise,'target');nw=e.series(noise,'wrong')
    with np.errstate(divide='ignore',invalid='ignore'):
        q=nt/(nt+nw);guess=rt-rw*q/(1-q)
    guess[(q>=1)|~np.isfinite(q)]=np.nan
    dump(a.results/'noise_calibration.json',{'real_A_target':summarize(mean_units(rt)),'noise_A_target':summarize(mean_units(nt)),
        'noise_q':summarize(mean_units(q)),'OC_noise':summarize(mean_units(rt-nt)),
        'OC_guess':summarize(mean_units(guess)), 'note':'Secondary diagnostic; undefined q or q=1 units are not imputed.',
        'q_valid_units':int(np.isfinite(q[0]).sum()),'OC_guess_valid_units':int(np.isfinite(guess[0]).sum())})
    # Find cells lacking a generated B counterpart. Use each of the other two languages' A canaries separately.
    absent=[]
    for (S,c,D),g in main.groupby(['S','cell','D'],observed=True):
        if S=='real' and set(g.version.astype(str))=={'A'}:absent.append((str(c),str(D)))
    cross=[];overlap=0
    for model in models:
        for line in (a.run/model/'scored.jsonl').open():
            r=json.loads(line)
            if r.get('set')!='main' or r['arm']!='main' or r['S']!='real' or (r['cell'],r['D']) not in absent:continue
            form=items[r['item']]['langs'];s=r['score'];valid=r['status']=='complete' and not s['R'];foils=[]
            for other in ('zh','ja','es'):
                if other==r['lang']:continue
                candidates={t:form[other]['A'][t] for t in ('PLACE','OBJECT') if form[other]['A'][t]!=form[r['lang']]['A'][t]}
                overlap+=2-len(candidates)
                if candidates:foils.append(float(valid and any(s['found'][t]==[v] for t,v in candidates.items())))
            cross.append({'model':model,'prompt_id':r['prompt_id'],'cross_foil':np.mean(foils) if foils else np.nan})
    cx=pd.DataFrame(cross).merge(d[['model','prompt_id','lang','cell','D','capable','target']],on=['model','prompt_id'],validate='one_to_one')
    cx=cx[cx.capable & cx.cross_foil.notna()];cx['net_cross']=cx.target-cx.cross_foil
    grouped=cx.groupby(['model','lang','cell','D'],observed=True)[['target','cross_foil','net_cross']].mean()
    grouped.to_csv(a.results/'cross_language_foil_units.csv')
    grouped.groupby(['cell','D'],observed=True).mean().to_csv(a.results/'cross_language_foils.csv')
    dump(a.results/'secondary_manifest.json',{'cross_foil_cells':absent,'cross_foil_rows':len(cx),'overlapping_canary_types_removed':overlap,
        'cross_foil_rule':'Average hits against each other-language A pair; drop any type identical to target. Descriptive equal unit averages.',
        'no_new_confirmatory_tests':True})
    print('Secondary checks complete',flush=True)

if __name__=='__main__':main()
