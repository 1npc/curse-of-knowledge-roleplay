"""Fetch only fixed official weight bytes via the existing proxy in parallel.

Transport-only addition: byte ranges must match Content-Range, and full files
must match the previously frozen SHA before the original verifier can mark a
model ready. Original snapshots and generation/scoring code stay unchanged.
"""
from pathlib import Path
import argparse,concurrent.futures,fcntl,hashlib,json,os,re,shutil,subprocess,time
from urllib.parse import urlsplit

ORDER=['qwen35_9b','glm47_flash','nemotron3_nano30b','qwen38_27b','gpt_oss_20b','phi4','gemma4_12b','falcon_h1_34b','mistral_small3','seed_oss_36b']
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(16<<20),b''):h.update(b)
 return h.hexdigest()
def atomic(p,d):
 t=p.with_name(p.name+'.tmp');t.write_text(json.dumps(d,indent=2)+'\n');os.replace(t,p)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--workers',type=int,default=32);ap.add_argument('--model',action='append');a=ap.parse_args();root=a.root;ops=root/'operations';refs=json.loads((root/'code/harness/weights_reference.json').read_text())['models']
 assert 1<=a.workers<=32
 lock=(ops/'range-weight-supplier.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 env=os.environ.copy();env.update(HTTP_PROXY='http://127.0.0.1:3128',HTTPS_PROXY='http://127.0.0.1:3128')
 common=['curl','--fail','--location','--silent','--show-error','--retry','3','--retry-delay','3','--connect-timeout','15']
 for model in a.model or ORDER:
  ref=refs[model];startmodel=time.time();queue=json.loads((ops/'queue.json').read_text())['models'];verified=json.loads((ops/'weights-verified.json').read_text())['models']
  if queue[model]['status'] in ['finished','failed'] or verified.get(model,{}).get('ok'):print('MODEL_ALREADY_ACCOUNTED',model,flush=True);continue
  dest=root/'weights'/model;dest.mkdir(parents=True,exist_ok=True);receipt={'model':model,'repo':ref['repo'],'revision':ref['revision'],'workers':a.workers,'chunk_bytes':64<<20,'source_sha256':sha(Path(__file__)),'transport':'official pinned HTTPS through existing HTTP proxy, parallel exact byte ranges','files':{},'started_unix':time.time()}
  while True:
   remaining=sum(i['bytes'] for n,i in ref['files'].items() if not (dest/n).exists() or (dest/n).stat().st_size!=i['bytes'])
   if shutil.disk_usage(root).free>=remaining+(20<<30):break
   print('WAIT_SSD_SPACE',model,'remaining',remaining,flush=True);time.sleep(30)
  print('MODEL_PREPARE',model,flush=True)
  try:
   for name,info in ref['files'].items():
    if '..' in Path(name).parts or not re.fullmatch(r'[A-Za-z0-9_./+-]+',name):raise RuntimeError('Unsafe frozen filename')
    out=dest/name;out.parent.mkdir(parents=True,exist_ok=True);expected=info.get('sha256')
    candidates=[out]+[Path('/mnt/nas_ssd/qianru')/x/'hub'/('models--'+ref['repo'].replace('/','--'))/'snapshots'/ref['revision']/name for x in ['npcbank-p0-weights','npcbank-c3-weights']]
    reusable=next((p for p in candidates if expected and p.exists() and p.stat().st_size==info['bytes'] and sha(p)==expected),None)
    if reusable:
     if reusable!=out:
      if out.exists() or out.is_symlink():out.unlink()
      out.symlink_to(reusable)
     receipt['files'][name]={'bytes':info['bytes'],'sha256':expected,'reused':str(reusable)};print('REUSED_PINNED_FILE',model,name,flush=True);continue
    url='https://huggingface.co/'+ref['repo']+'/resolve/'+ref['revision']+'/'+name
    started=time.time()
    if info['bytes']<=(64<<20):
     tmp=out.with_name(out.name+'.http-part')
     subprocess.run(common+['--max-time','600','--output',str(tmp),url],env=env,check=True)
     if tmp.stat().st_size!=info['bytes'] or expected and sha(tmp)!=expected:raise RuntimeError('Small file size/SHA mismatch '+name)
     digest=sha(tmp);os.replace(tmp,out);ranges=[]
    else:
     if not expected:raise RuntimeError('Parallel large file requires a frozen official SHA')
     # Resolve once rather than sending one Hub request per range. The signed
     # public CDN URL is kept in memory and never printed in logs or receipts.
     p=subprocess.run(common+['--max-time','90','--head','--output','/dev/null','--write-out','%{url_effective}',url],env=env,capture_output=True,text=True,check=True)
     cdn=p.stdout.strip();parsed=urlsplit(cdn)
     if parsed.scheme!='https' or parsed.username or parsed.password:raise RuntimeError('Unexpected official redirect')
     tmp=out.with_name(out.name+'.range-part');state=dest/'.range-meta'/expected;state.mkdir(parents=True,exist_ok=True)
     fd=os.open(tmp,os.O_RDWR|os.O_CREAT,0o600);os.ftruncate(fd,info['bytes']);chunk=64<<20
     def fetch(i):
      offset=i*chunk;size=min(chunk,info['bytes']-offset);done=state/(str(i)+'.json')
      if done.exists():
       d=json.loads(done.read_text());data=os.pread(fd,size,offset)
       if len(data)==size and hashlib.sha256(data).hexdigest()==d['sha256']:return d
      part=state/(str(i)+'.part');headers=state/(str(i)+'.headers')
      p=subprocess.run(common+['--max-time','600','--range',str(offset)+'-'+str(offset+size-1),'--dump-header',str(headers),'--output',str(part),'--write-out','%{http_code}',cdn],env=env,capture_output=True,text=True)
      if p.returncode:raise RuntimeError('Range download failed '+name+' #'+str(i)+' curl='+str(p.returncode))
      cr=re.findall(r'(?im)^content-range:\s*bytes\s+(\d+)-(\d+)/(\d+)\s*$',headers.read_text())
      if p.stdout!='206' or not cr or tuple(map(int,cr[-1]))!=(offset,offset+size-1,info['bytes']) or part.stat().st_size!=size:raise RuntimeError('Exact Content-Range mismatch '+name+' #'+str(i))
      h=hashlib.sha256();written=0
      with part.open('rb') as f:
       for data in iter(lambda:f.read(8<<20),b''):
        h.update(data);view=memoryview(data)
        while view:
         n=os.pwrite(fd,view,offset+written);written+=n;view=view[n:]
      os.fsync(fd);d={'i':i,'offset':offset,'bytes':size,'sha256':h.hexdigest()};atomic(done,d);part.unlink();headers.unlink();print('RANGE_DONE',model,name,i,size,flush=True);return d
     try:
      with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:ranges=list(pool.map(fetch,range((info['bytes']+chunk-1)//chunk)))
     finally:os.close(fd)
     digest=sha(tmp)
     if digest!=expected:raise RuntimeError('Frozen full-file SHA mismatch '+name)
     os.replace(tmp,out)
    receipt['files'][name]={'bytes':info['bytes'],'sha256':digest,'seconds':round(time.time()-started,2),'ranges':ranges};atomic(ops/('range-weight-transport-'+model+'.json'),receipt)
    print('FILE_VERIFIED',model,name,info['bytes'],round(time.time()-started,2),flush=True)
   with (root/'logs'/(model+'-range-final-verify.log')).open('ab') as log:
    e=env.copy();e.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_XET='1')
    subprocess.run([str(root/'.venv/bin/python'),'harness/h200_download_v2.py','--root',str(root),'--model',model],cwd=root/'code',env=e,stdout=log,stderr=subprocess.STDOUT,check=True)
   receipt.update(ok=True,finished_unix=time.time(),seconds=round(time.time()-startmodel,2));atomic(ops/('range-weight-transport-'+model+'.json'),receipt);print('MODEL_WEIGHTS_READY',model,receipt['seconds'],flush=True)
  except Exception as e:
   receipt.update(ok=False,error=repr(e),failed_unix=time.time());atomic(ops/('range-weight-transport-'+model+'.json'),receipt)
   print('MODEL_PREPARATION_FAILED',model,repr(e),flush=True)
   # Preparation did not attempt any model prompt. Preserve all partial
   # downloads; leave this model pending so a reported transport failure is
   # never silently treated as a completed inference experiment.
 print('WEIGHT_SUPPLIER_PASS_FINISHED',flush=True)
if __name__=='__main__':main()
