"""Reuse self-owned NAS snapshots, otherwise fetch exactly frozen files on H200."""
import argparse,concurrent.futures,fcntl,hashlib,json,os,time
from pathlib import Path

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(16<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--model',required=True);a=p.parse_args()
 ref=json.loads((a.root/'code/harness/weights_reference.json').read_text())['models'][a.model]
 cache_name='models--'+ref['repo'].replace('/','--')
 candidates=[Path('/mnt/nas_ssd/qianru')/x/'hub'/cache_name/'snapshots'/ref['revision'] for x in ['npcbank-p0-weights','npcbank-c3-weights']]
 existing=next((x for x in candidates if all((x/n).exists() and (x/n).stat().st_size==s['bytes'] for n,s in ref['files'].items())),None)
 dest=existing or a.root/'weights'/a.model
 if existing is None:
  dest.mkdir(parents=True,exist_ok=True)
  # Reuse valid files from an incomplete old snapshot without changing it.
  for name,info in ref['files'].items():
   if (dest/name).exists():continue
   for old in candidates:
    src=old/name
    if src.exists() and src.stat().st_size==info['bytes']:
     if info.get('sha256') and sha(src)!=info['sha256']:continue
     (dest/name).parent.mkdir(parents=True,exist_ok=True);(dest/name).symlink_to(src);break
  missing=[n for n,s in ref['files'].items() if not (dest/n).exists() or (dest/n).stat().st_size!=s['bytes']]
  if missing:
   from huggingface_hub import snapshot_download
   snapshot_download(repo_id=ref['repo'],revision=ref['revision'],local_dir=str(dest),allow_patterns=missing,max_workers=8)
 def verify(pair):
  name,info=pair;f=dest/name
  if not f.exists() or f.stat().st_size!=info['bytes']:raise RuntimeError('Missing/wrong-size '+name)
  digest=sha(f)
  if info.get('sha256') and digest!=info['sha256']:raise RuntimeError('SHA-256 mismatch '+name)
  print(json.dumps({'model':a.model,'verified_file':name,'bytes':info['bytes']}),flush=True)
  return name,{'bytes':info['bytes'],'sha256':digest}
 start=time.time()
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:files=dict(pool.map(verify,ref['files'].items()))
 receipt={'path':str(dest),'repo':ref['repo'],'revision':ref['revision'],'ok':True,'files':files,'reused_complete_snapshot':existing is not None,'verified_unix':time.time(),'verify_seconds':time.time()-start}
 ops=a.root/'operations';ops.mkdir(exist_ok=True)
 with (ops/'weights-verification.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);p=ops/'weights-verified.json';d=json.loads(p.read_text()) if p.exists() else {'models':{}}
  d['models'][a.model]=receipt;tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(d,indent=2)+'\n');os.replace(tmp,p)
 print(json.dumps({'model':a.model,'verified':True,'path':str(dest),'seconds':receipt['verify_seconds']}),flush=True)
if __name__=='__main__':main()
