"""Accelerate restoration of the recorded H200 runtime, without local installs.

Fetch only exact official wheels absent from the task wheelhouse. All archives
are checked against PyPI SHA-256, transferred through existing SSH, then removed
from the local temporary directory. This writes no remote environment itself.
"""
import argparse,concurrent.futures,hashlib,json,subprocess,tempfile,re
from pathlib import Path
from stage_h200_runtime import compatible

def main():
 p=argparse.ArgumentParser();p.add_argument('--socket',required=True);p.add_argument('--root',required=True);p.add_argument('--state',type=Path,required=True);a=p.parse_args();a.state.mkdir(parents=True,exist_ok=True)
 ssh=['ssh','-S',a.socket,'-o','BatchMode=yes','-o','ConnectTimeout=20','q84453243@192.168.1.105'];nested='ssh -T -o BatchMode=yes -o ConnectTimeout=15 -o StrictHostKeyChecking=yes qianru@10.201.226.77 '
 script="python3 - <<'PY'\nfrom pathlib import Path\nimport json\nr=Path("+repr(a.root)+")\nprint(json.dumps({'pins':(r/'operations/original-runtime-requirements.txt').read_text().splitlines(),'files':[x.name for x in (r/'wheelhouse').iterdir()]}))\nPY\n"
 data=json.loads(subprocess.check_output(ssh+[nested+'/bin/sh'],input=script.encode(),timeout=90));existing=set(data['files'])
 def metadata(pin):
  name,v=pin.split('==');url='https://pypi.org/pypi/'+name+'/'+v+'/json'
  d=json.loads(subprocess.check_output(['curl','--fail','--silent','--show-error','--retry','2','--max-time','90',url]))
  choices=[x for x in d['urls'] if compatible(x['filename'])]
  if not choices:raise RuntimeError('No compatible official wheel: '+pin)
  f=min(choices,key=lambda x:x['size']);return None if f['filename'] in existing else {'pin':pin,**f}
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:files=[x for x in pool.map(metadata,data['pins']) if x]
 files.sort(key=lambda x:-x['size']);print('EXACT_WHEELS_MISSING',len(files),'GiB',round(sum(x['size'] for x in files)/2**30,3),flush=True)
 manifest=[]
 def transfer(f):
  if not f['url'].startswith('https://files.pythonhosted.org/'):raise RuntimeError('unexpected source')
  print('DOWNLOAD_PIN',f['pin'],round(f['size']/2**20,1),'MiB',flush=True)
  with tempfile.TemporaryDirectory(prefix='oc-pinned-wheel-') as tmp:
   path=Path(tmp)/f['filename'];subprocess.run(['curl','--fail','--silent','--show-error','--retry','3','--connect-timeout','10','--max-time','900','--output',str(path),f['url']],check=True)
   h=hashlib.sha256()
   with path.open('rb') as fd:
    for b in iter(lambda:fd.read(8<<20),b''):h.update(b)
   if h.hexdigest()!=f['digests']['sha256'] or path.stat().st_size!=f['size']:raise RuntimeError('size/hash mismatch '+f['pin'])
   dest=a.root+'/wheelhouse/'+f['filename'];assert re.fullmatch(r'[A-Za-z0-9_./+-]+',dest)
   with path.open('rb') as fd:subprocess.run(ssh+[nested+'dd of='+dest+' status=none'],stdin=fd,stdout=subprocess.DEVNULL,check=True,timeout=900)
   checked=subprocess.check_output(ssh+[nested+'sha256sum '+dest],timeout=180).decode().split()[0]
   if checked!=h.hexdigest():raise RuntimeError('remote hash mismatch '+f['pin'])
  print('STAGED_PIN',f['pin'],flush=True);return {'pin':f['pin'],'filename':f['filename'],'url':f['url'],'bytes':f['size'],'sha256':h.hexdigest()}
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  futures=[pool.submit(transfer,f) for f in files]
  for future in concurrent.futures.as_completed(futures):
   manifest.append(future.result());(a.state/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('ALL_EXACT_WHEELS_STAGED',len(manifest),flush=True)
if __name__=='__main__':main()
