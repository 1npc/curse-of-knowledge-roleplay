"""Canary-level GEE robustness, exchangeable within each reply; primary inference remains skeleton bootstrap."""
import argparse,json,warnings
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
from full_analysis import dump


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True)
    ap.add_argument('--target-only',action='store_true',help='Post hoc convergence diagnostic; preserves original target/foil fits')
    a=ap.parse_args();out=a.results
    d=pd.read_pickle(out/'analysis_frame.pkl');manifest=json.loads((out/'manifest.json').read_text())
    units={tuple(u) for u in manifest['passing_units']};models=manifest['confirmatory_models']
    selected=d[(d['set']=='main') & (d.arm=='main')].copy()
    selected['condition']=None
    for name,c,D,S in [('language','C-T-','D0','real'),('flag_understand','C-T-_flag','D0','real'),
                       ('flag_inaudible','Einaud_S','D0','english'),('narrated_inaudible','Einaud','D0','english'),
                       ('language_prose','C-T-','D1','real')]:
        selected.loc[(selected.cell==c)&(selected.D==D)&(selected.S==S),'condition']=name
    selected=selected[selected.condition.notna()]
    selected=selected[[(m,l) in units for m,l in zip(selected.model,selected.lang)]]
    selected=selected[(selected.S=='english')|selected.capable]
    coefficients=[];fits=[]
    for model in models:
        subset=selected[selected.model==model];frames=[]
        if not len(subset):continue
        for typ in ('place','object'):
            for target in ((1,) if a.target_only else (0,1)):
                frames.append(pd.DataFrame({'use':subset[typ+('_target' if target else '_foil')].astype(int),
                    'target':target,'condition':subset.condition.astype(str),'canary':typ,'lang':subset.lang.astype(str),
                    'question':subset.Q.astype(str),'character':subset.character.astype(str),
                    'reply':subset.prompt_id.astype(str)}))
        data=pd.concat(frames,ignore_index=True)
        with warnings.catch_warnings(record=True) as ww:
            warnings.simplefilter('always')
            try:
                formula='use ~ C(condition, Treatment(reference="language"))'+('' if a.target_only else ' * target')+' + C(canary) + C(lang) + C(question) + C(character)'
                fit=sm.GEE.from_formula(formula,
                    groups='reply',data=data,family=sm.families.Binomial(),cov_struct=sm.cov_struct.Exchangeable()).fit(maxiter=100)
                ci=fit.conf_int()
                for name,beta in fit.params.items():
                    coefficients.append({'model':model,'term':name,'beta_log_odds':float(beta),'se':float(fit.bse[name]),
                        'ci_low':float(ci.loc[name].iloc[0]),'ci_high':float(ci.loc[name].iloc[1]),'p':float(fit.pvalues[name])})
                fits.append({'model':model,'converged':bool(fit.converged),'n_canary_observations':len(data),
                             'reply_clusters':data.reply.nunique(),'working_correlation':float(fit.cov_struct.dep_params),
                             'finite':bool(np.isfinite(fit.params).all() and np.isfinite(fit.bse).all()),'warnings':sorted({str(w.message) for w in ww}),
                             'formula':formula,'post_hoc_target_only':a.target_only})
            except Exception as ex:
                fits.append({'model':model,'converged':False,'error':str(ex),'n_canary_observations':len(data)})
        print('GEE',model,fits[-1]['converged'],flush=True)
    prefix='gee_target_only' if a.target_only else 'gee'
    pd.DataFrame(coefficients).to_csv(out/(prefix+'_coefficients.csv'),index=False)
    dump(out/(prefix+'_fits.json'),fits)

if __name__=='__main__':main()
