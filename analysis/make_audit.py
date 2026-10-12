"""Deterministic human audit packages; no AI labels populate annotation columns."""
import argparse
import csv
import hashlib
import json
import random
import re
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
QUOTAS={'ct_boundary':50,'ct_d1_deny_hit':60,'ct_other_hit':60,'ct_remaining':30,
        'understand':30,'translator':30,'inaudible':20,'offline':20,'noise':30,'mitigation':30}
MISS={'U':60,'D0':60,'D1':60,'C+T-':40}
LABELS=['use_set1_place','use_set1_object','use_set2_place','use_set2_object','N_deny','A_explicit','refusal','echo_only','notes']

def reservoir(pool,counts,key,row,quota,rng):
    counts[key]+=1
    if len(pool[key])<quota:pool[key].append(row)
    else:
        j=rng.randrange(counts[key])
        if j<quota:pool[key][j]=row


def stratum(r):
    s=r['score']
    if r['arm']=='M1g' and r['step']==2:return 'mitigation'
    if r['arm']!='main':return None
    if r['S']=='noise':return 'noise'
    if r['cell']=='C-T-' and r['S']=='real':
        boundary=(s.get('mode')=='tentative' or 'multi' in s['canary'].values() or
                  (not s['hit_t'] and bool(re.search(r'\b(somewhere|something|place|object|item)\b',r['text'],re.I))))
        if boundary:return 'ct_boundary'
        if r['D']=='D1' and s['N_deny'] and s['hit_t']:return 'ct_d1_deny_hit'
        if s['hit_t']:return 'ct_other_hit'
        return 'ct_remaining'
    if r['cell']=='C+T-' and r['S']=='real':return 'understand'
    if r['cell']=='C-T+' and r['S']=='real':return 'translator'
    if r['cell'] in ('Einaud','Einaud_S'):return 'inaudible'
    if r['cell']=='C-Toff' and r['S']=='real':return 'offline'
    return None


def write_csv(path,rows,fields):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();out=a.out;public=out/'audit';private=out/'audit-private';public.mkdir(parents=True,exist_ok=True);private.mkdir(exist_ok=True)
    models=json.loads((ROOT/'docs/analysis-lock.json').read_text())['confirmatory_models']
    items={it['id']:it for it in json.loads((ROOT/'items/main/skeletons.json').read_text())['items']}
    rng=random.Random(2026092901); cr=defaultdict(list);cn=Counter();mr=defaultdict(list);mn=Counter();flagged=[]
    populations=Counter()
    for model in models:
        for line in (a.run/model/'scored.jsonl').open():
            r=json.loads(line)
            if r.get('set')!='main' or r['status'] not in ('complete','truncated'):continue
            if r['arm'] not in ('main','M1g'):continue
            if r['arm']=='M1g' and r['step']!=2:continue
            s=r['score'];st=stratum(r)
            populations[(r['cell'],r['D'],'positive' if s['hit_t'] else 'negative')]+=1
            if st:reservoir(cr,cn,st,r,QUOTAS[st],rng)
            if r['arm']=='main' and r['S']=='real' and not s['hit_t']:
                key=r['D'] if r['cell']=='C-T-' and r['D'] in ('U','D0','D1') else ('C+T-' if r['cell']=='C+T-' else None)
                if key:reservoir(mr,mn,key,r,MISS[key],rng)
            if s['L'] or s['echo_only']:flagged.append(r)
    if any(len(cr[k])!=v for k,v in QUOTAS.items()) or any(len(mr[k])!=v for k,v in MISS.items()):
        raise ValueError('Insufficient strata; do not silently substitute samples: '+str({k:(len(cr[k]),v) for k,v in QUOTAS.items()}))
    def packet(selected,prefix,counts,quotas):
        tagged=[(k,r) for k,rs in selected.items() for r in rs];rng.shuffle(tagged);public_rows=[];keys=[]
        for n,(st,r) in enumerate(tagged,1):
            forms=items[r['item']]['langs'][r['lang']];order=['A','B'];rng.shuffle(order)
            row={'audit_id':f'{prefix}{n:04d}','reply':r['text']}
            for j,v in enumerate(order,1):
                row[f'set{j}_gold']=' / '.join(forms[v]['gold'])
                row[f'set{j}_place']=forms[v]['PLACE'];row[f'set{j}_object']=forms[v]['OBJECT']
            row.update({k:'' for k in LABELS});public_rows.append(row)
            keys.append({'audit_id':row['audit_id'],'model':r['model'],'prompt_id':r['prompt_id'],'cell':r['cell'],'D':r['D'],
                         'stratum':st,'population':counts[st],'sample_n':quotas[st],'inclusion_probability':quotas[st]/counts[st],
                         'target_set':order.index(r['version'])+1,'status':r['status'],
                         **{'machine_'+k:r['score'][k] for k in ('hit_t','hit_f','U2','N_deny','A','R','echo_only')}})
        return public_rows,keys
    cert,ck=packet(cr,'C',cn,QUOTAS);miss,mk=packet(mr,'M',mn,MISS)
    fields=list(cert[0]);write_csv(public/'annotator-A.csv',cert,fields);write_csv(public/'annotator-B.csv',cert,fields)
    write_csv(public/'miss-audit.csv',miss,fields)
    write_csv(private/'certification-key.csv',ck,list(ck[0]));write_csv(private/'miss-key.csv',mk,list(mk[0]))
    adjudicated=[dict(r,adjudication_notes='') for r in cert]
    write_csv(public/'adjudicated.csv',adjudicated,fields+['adjudication_notes'])
    # Flagged queue is separate from certification and does not carry machine labels.
    flagged_sample={'flagged':flagged};fc=Counter(flagged=len(flagged));fq={'flagged':len(flagged)}
    flagged_rows,fk=packet(flagged_sample,'L',fc,fq) if flagged else ([],[])
    write_csv(public/'language-echo-review.csv',flagged_rows,fields)
    if fk:write_csv(private/'language-echo-key.csv',fk,list(fk[0]))
    manifest={'seed':2026092901,'certification':len(cert),'miss_audit':len(miss),'flagged_queue':len(flagged),
              'strata_population':dict(cn),'strata_sample':QUOTAS,'miss_population':dict(mn),'miss_sample':MISS,
              'positive_in_certification':sum(r['machine_hit_t'] for r in ck),
              'd1_deny_positive':sum(r['D']=='D1' and r['machine_N_deny'] for r in ck),
              'human_labels_completed':0,'labels_are_blank':True,
              'same_source_overlap_cert_miss':len({(r['model'],r['prompt_id']) for r in ck}&{(r['model'],r['prompt_id']) for r in mk})}
    (private/'sampling-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    guide='''# 主实验人工盲标说明

所有标签都是空白。只共享 `audit/` 内文件，不向标注者共享 `audit-private/` 的模型、条件及机器标签。

1. 两人分别填写 annotator-A.csv 与 annotator-B.csv，独立完成 360 条。列内填 1（是）或 0（否）；不确定写 notes。
2. set1/set2 是随机换序的两版金标译文与地点/物品词；不是模型条件，也不代表正确/错误。判断回复是否实际使用对应语义，包括明确同义词；纯外语回显、泛称和列出多个互斥候选不算唯一命中。
3. use_setN_place/object：是否使用该组的地点/物品；N_deny：第一人称否认会该语言或听懂；A_explicit：第一人称理解声明、明确翻译框架或括号释义。
4. refusal 是拒绝扮演/作答或无有效回复；echo_only 是主要复述刺激而未使用译义。不得根据“角色应该知道什么”猜测标签。
5. 两人提交后再裁定分歧，将最终值写入 adjudicated.csv；不要边讨论边填独立标注文件。
6. miss-audit.csv 是另 220 条漏检检查，可由一名标注者填写。language-echo-review.csv 是额外的语言/回显复核队列。

模型、条件、声明强度和原 A/B 版本均未提供；回复文字本身仍可能提示条件，这是文本盲标的局限。
金标是生成阶段的草稿译文，尚未经母语者确认；若发现译文问题，在 notes 标记，不能无记录地修改输入。
机器评分尚未获得人工认证。未填写表格不能计算或声称通过 precision、recall、κ、AC1 或误分类校正。
'''
    (public/'README.md').write_text(guide)
    print(json.dumps(manifest))


if __name__=='__main__':main()
