"""V2 scoring uses the frozen v1 canary rules; no third-party local dependency."""
from pathlib import Path
import sys,json,argparse,hashlib,collections
ROOT=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(ROOT))
from oc_v2.score import score_record

def main():
 p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True);p.add_argument('--items',type=Path,required=True);p.add_argument('--responses',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--model',required=True);a=p.parse_args()
 plans=[json.loads(x) for x in a.plan.read_text().splitlines() if x.strip()]
 items={x['id']:x for x in json.loads(a.items.read_text())['items']}
 responses=[json.loads(x) for x in a.responses.read_text().splitlines() if x.strip()]
 assert len({r['prompt_id'] for r in responses})==len(responses),'Duplicate response IDs'
 replies={r['prompt_id']:r for r in responses}
 assert all(r['model']==a.model for r in responses),'Foreign model responses'
 expected={r['prompt_id'] for r in plans}|{r['prompt_id']+'#2' for r in plans if 'next_step' in r}
 assert set(replies)<=expected,'Unplanned response IDs'
 rows=[score_record(r,items[r['item']],replies) for r in plans]
 for r in rows:r['model']=a.model
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in rows))
 receipt={'planned_endpoints':len(rows),'raw_records':len(replies),'status':dict(collections.Counter(r['status'] for r in rows)),'sha256':hashlib.sha256(a.out.read_bytes()).hexdigest(),'files':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [a.plan,a.items,a.responses,ROOT/'oc_v2/score.py',ROOT/'oc/score.py']}}
 a.out.with_suffix('.receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt['status']))
if __name__=='__main__':main()
