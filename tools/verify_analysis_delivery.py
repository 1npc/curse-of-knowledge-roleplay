"""Standard-library, independent verification of delivered main-analysis artifacts."""
import csv,hashlib,json,math
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'analysis/results/main-20260929'

def main():
    manifest=json.loads((OUT/'manifest.json').read_text());checks={}
    for rel,expected in json.loads((ROOT/'docs/analysis-lock.json').read_text())['source_sha256'].items():
        assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==expected,rel
    checks['locked_sources_unchanged']=True
    for s in manifest['source_scored_files']:
        p=ROOT/'runs'/s['run']/s['model']/'scored.jsonl'
        h=hashlib.sha256()
        with p.open('rb') as f:
            for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
        actual=h.hexdigest()
        assert actual==s['sha256'],str(p)
    checks['scored_sha256_matches']=len(manifest['source_scored_files'])
    labels=['use_set1_place','use_set1_object','use_set2_place','use_set2_object','N_deny','A_explicit','refusal','echo_only','notes']
    counts={}
    for f,n in [('annotator-A.csv',360),('annotator-B.csv',360),('adjudicated.csv',360),('miss-audit.csv',220),('language-echo-review.csv',3211)]:
        rows=list(csv.DictReader((OUT/'audit'/f).open(encoding='utf-8-sig')))
        assert len(rows)==n and len({r['audit_id'] for r in rows})==n
        assert all(all(r[k]=='' for k in labels) for r in rows)
        assert not {'model','prompt_id','cell','D','version','target_set'}.intersection(rows[0])
        counts[f]=n
    checks['blank_blinded_packets']=counts
    ck=list(csv.DictReader((OUT/'audit-private/certification-key.csv').open(encoding='utf-8-sig')))
    mk=list(csv.DictReader((OUT/'audit-private/miss-key.csv').open(encoding='utf-8-sig')))
    assert not ({(r['model'],r['prompt_id']) for r in ck}&{(r['model'],r['prompt_id']) for r in mk})
    ct=[r for r in ck if r['stratum'].startswith('ct_')]
    assert len(ct)==200 and sum(r['machine_hit_t']=='True' for r in ct)>=120
    assert sum(r['D']=='D1' and r['machine_N_deny']=='True' for r in ct)>=60
    checks['sampling_quotas_and_no_overlap']=True
    totals=defaultdict(lambda:[0.,0]);denominators={};probe_status={}
    for model in manifest['confirmatory_models']:
        cap={};state={};selected=[]
        for line in (ROOT/'runs/main-v1'/model/'scored.jsonl').open():
            r=json.loads(line)
            if r.get('set')!='main':continue
            valid=r['status']=='complete' and not r['score']['R']
            key=(r['item'],r['lang'],r['version'])
            if r['arm']=='probe_translate' and r['S']=='real':cap[key]=valid and r['score']['U2']
            if r['arm']=='probe_state' and r['cell']=='C-T-' and r['D']=='D0':state[key[:2]]=valid and r.get('probe_answer')==r.get('probe_expected')
            if r['arm'] in ('main','M1g') and r['cell'] in ('C-T-','C-T-_flag','C-T+','Einaud','Einaud_S'):selected.append(r)
        for r in selected:
            if r['S'] not in ('real','english'):continue
            if r['S']=='real' and not cap.get((r['item'],r['lang'],r['version']),False):continue
            s=r['score'];valid=r['status']=='complete' and not s['R'];target=float(s['hit_t']) if valid else 0.;net=target-(float(s['hit_f']) if valid else 0.)
            kinds=[]
            if r['arm']=='main':
                if r['D']=='D0':
                    kind={'C-T-':'L','C-T-_flag':'F','Einaud':'IP','Einaud_S':'I'}.get(r['cell'])
                    if kind:kinds.append((kind,net))
                    if r['cell']=='C-T-' and state.get((r['item'],r['lang']),False):kinds.append(('PC',net))
                if r['D']=='D1' and r['cell']=='C-T-':kinds.append(('LP',net))
            if r['Q'] in ('content','plan') and r['D']=='D0' and (r['arm']=='main' or r['step']==2):
                prefix='B' if r['arm']=='main' else 'M'
                if r['cell'] in ('C-T-','Einaud_S'):kinds.append((prefix+('L' if r['cell']=='C-T-' else 'I'),net))
                if r['cell']=='C-T+' and r['version']=='A':kinds.append((prefix+'T',target))
            for kind,val in kinds:
                t=totals[model,r['lang'],kind];t[0]+=val;t[1]+=1
        probe_status[model]=sum(state.values())
        print('independent rows verified',model,flush=True)
    units=[tuple(u) for u in manifest['passing_units']]
    def val(u,k):return totals[u+(k,)][0]/totals[u+(k,)][1]
    def mean(xs):return sum(xs)/len(xs)
    point={'H1':mean([val(u,'L') for u in units]),'H1i':mean([val(u,'I') for u in units]),
        'H2a':mean([val(u,'L')-val(u,'LP') for u in units]),'H2b':mean([val(u,'I')-val(u,'IP') for u in units]),
        'H3':mean([val(u,'L')-val(u,'F') for u in units]),'H4':mean([val(u,'I')-val(u,'F') for u in units]),
        'H5a':mean([val(u,'PC') for u in units if totals[u+('PC',)][1]])}
    conf=json.loads((OUT/'confirmatory.json').read_text())
    for k,v in point.items():assert math.isclose(v,conf[k]['point'],abs_tol=1e-12),(k,v,conf[k]['point'])
    red=mean([((val(u,'BL')-val(u,'ML'))/val(u,'BL')+(val(u,'BI')-val(u,'MI'))/val(u,'BI'))/2 for u in units])
    keep=mean([val(u,'MT')-val(u,'BT') for u in units])
    assert math.isclose(red,conf['H5b']['reduction']['point'],abs_tol=1e-12)
    assert math.isclose(keep,conf['H5b']['retention']['point'],abs_tol=1e-12)
    checks['independent_point_estimates_match']=dict(point,H5b_reduction=red,H5b_retention=keep)
    checks['H5a_units']=sum(totals[u+('PC',)][1]>0 for u in units)
    checks['state_correct_counts']=probe_status
    checks['response_denominators']={k:sum(totals[u+(k,)][1] for u in units) for k in ('L','I','F','LP','IP','PC','BL','ML','BI','MI','BT','MT')}
    (OUT/'delivery-verification.json').write_text(json.dumps(checks,indent=2)+'\n')
    print('DELIVERY VERIFIED')

if __name__=='__main__':main()
