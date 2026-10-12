"""Stage official Linux wheels through an existing SSH session; local stdlib only.

Resolution and installation happen on H200. This program never installs a local
package. It transfers one SHA-256 verified archive at a time, keeping disk use low.
"""
from pathlib import Path
import argparse, hashlib, json, re, shlex, subprocess, tempfile, time

def version(v):
    if not re.fullmatch(r'\d+(?:\.\d+)*(?:\.post\d+)?',v): return None
    a,b=(v.split('.post')+[None])[:2]
    digits=tuple(map(int,a.split('.')))
    return digits+(0,)*(6-len(digits))+(int(b or 0),)

def satisfies(v,spec):
    vv=version(v)
    if vv is None:return False
    for op,s in re.findall(r'(===|==|!=|>=|<=|~=|>|<)\s*([\w.*+!-]+)',spec):
        if s.endswith('.*'):
            ok=v==s[:-2] or v.startswith(s[:-1])
            if (op=='==' and not ok) or (op=='!=' and ok):return False
            continue
        sv=version(s)
        if sv is None:raise ValueError('unsupported version constraint '+s)
        ok={'==':vv==sv,'===':vv==sv,'!=':vv!=sv,'>=':vv>=sv,'<=':vv<=sv,'>':vv>sv,'<':vv<sv}.get(op)
        if op=='~=':
            bits=s.split('.');upper=bits[:-1] if len(bits)>2 else bits[:1]
            upper[-1]=str(int(upper[-1])+1);ok=vv>=sv and vv<version('.'.join(upper))
        if not ok:return False
    return True

def compatible(filename):
    if not filename.endswith('.whl'):return False
    tags=filename[:-4].rsplit('-',3)
    if len(tags)!=4:return False
    py,abi,plat=tags[1:]
    generic=any(x=='py3' or (re.fullmatch(r'py3\d+',x) and int(x[3:])<=12) for x in py.split('.'))
    if plat=='any':return generic
    if 'x86_64' not in plat or 'manylinux' not in plat:return False
    glibc=re.findall(r'manylinux_(\d+)_(\d+)',plat)
    if glibc and not any(tuple(map(int,x))<=(2,39) for x in glibc):return False
    if generic and abi=='none':return True
    if 'cp312' in py.split('.') and abi in ('cp312','abi3','none'):return True
    return abi=='abi3' and any(re.fullmatch(r'cp3\d+',x) and int(x[3:])<=12 for x in py.split('.'))

def main():
    p=argparse.ArgumentParser();p.add_argument('--socket',required=True);p.add_argument('--root',required=True)
    p.add_argument('--state',type=Path,required=True);a=p.parse_args();a.state.mkdir(parents=True,exist_ok=True)
    ssh=['ssh','-S',a.socket,'-o','BatchMode=yes','-o','ConnectTimeout=20','q84453243@192.168.1.105']
    nested='ssh -T -o BatchMode=yes -o ConnectTimeout=15 -o StrictHostKeyChecking=yes qianru@10.201.226.77 '
    def remote(script):
        return subprocess.run(ssh+[nested+'/bin/sh'],input=script.encode(),capture_output=True,timeout=180)
    def get(url):
        return json.loads(subprocess.check_output(['curl','--fail','--silent','--show-error','--retry','2','--connect-timeout','10','--max-time','90',url]))
    manifest=[];roots='vllm==0.29.0 transformers==5.17.0'
    for attempt in range(240):
        cmd=shlex.join([a.root+'/.venv/bin/python','-m','pip','install','--dry-run','--ignore-installed','--no-index','--find-links',a.root+'/wheelhouse','--report',a.root+'/operations/runtime-resolution.json'])+' '+roots+'\n'
        r=remote(cmd);out=(r.stdout+r.stderr).decode(errors='replace')
        (a.state/'last-resolution.log').write_text(out)
        if r.returncode==0:
            print('RESOLVED',len(manifest),'new archives',flush=True)
            install=shlex.join([a.root+'/.venv/bin/python','-m','pip','install','--no-index','--find-links',a.root+'/wheelhouse'])+' '+roots
            script='nohup /bin/sh -c '+shlex.quote(install)+' > '+shlex.quote(a.root+'/logs/offline-install.log')+' 2>&1 < /dev/null &\nprintf "%s\\n" "$!" > '+shlex.quote(a.root+'/operations/offline-install.pid')+'\ncat '+shlex.quote(a.root+'/operations/offline-install.pid')+'\n'
            rr=remote(script);print('INSTALL_PID',rr.stdout.decode().strip(),'exit',rr.returncode,flush=True)
            if rr.returncode:raise RuntimeError(rr.stderr.decode())
            return
        m=re.search(r'Could not find a version that satisfies the requirement (.+?) \(from ',out)
        if not m:m=re.search(r'No matching distribution found for (.+)',out)
        if not m:raise RuntimeError(out[-3500:])
        req=m[1].strip();pkg=re.match(r'([A-Za-z0-9_.-]+)(?:\[[^]]+\])?(.*)',req)
        if not pkg:raise RuntimeError('cannot parse '+req)
        name,spec=pkg.groups();data=get('https://pypi.org/pypi/'+name+'/json')
        candidates=[]
        for v,files in data['releases'].items():
            if satisfies(v,spec):
                ws=[f for f in files if compatible(f['filename']) and not f.get('yanked')]
                if ws:candidates.append((version(v),v,ws))
        if not candidates:raise RuntimeError('no official compatible Linux wheel for '+req)
        _,v,ws=max(candidates);f=min(ws,key=lambda x:x['size'])
        if any(x['filename']==f['filename'] for x in manifest):raise RuntimeError('resolver repeated '+req+' after '+f['filename'])
        if not f['url'].startswith('https://files.pythonhosted.org/'):raise RuntimeError('unexpected archive host')
        print('DOWNLOAD',req,'->',f['filename'],round(f['size']/2**20,1),'MiB',flush=True)
        with tempfile.TemporaryDirectory(prefix='oc-runtime-wheel-') as tmp:
            file=Path(tmp)/f['filename']
            subprocess.run(['curl','--fail','--silent','--show-error','--retry','3','--connect-timeout','15','--max-time','900','--output',str(file),f['url']],check=True)
            h=hashlib.sha256()
            with file.open('rb') as fd:
                for b in iter(lambda:fd.read(8<<20),b''):h.update(b)
            if h.hexdigest()!=f['digests']['sha256'] or file.stat().st_size!=f['size']:raise RuntimeError('archive digest/size mismatch')
            dest=a.root+'/wheelhouse/'+f['filename']
            # Wheel filenames and this task root contain no spaces or shell metacharacters.
            if not re.fullmatch(r'[A-Za-z0-9_./+-]+',dest):raise RuntimeError('unsafe destination')
            with file.open('rb') as fd:
                up=subprocess.run(ssh+[nested+'dd of='+dest+' status=none'],stdin=fd,capture_output=True,timeout=900)
            if up.returncode:raise RuntimeError(up.stderr.decode())
            check=remote('sha256sum '+shlex.quote(dest)+'\n')
            if check.returncode or check.stdout.decode().split()[0]!=h.hexdigest():raise RuntimeError('remote archive digest mismatch')
        manifest.append({'requirement':req,'version':v,'filename':f['filename'],'bytes':f['size'],'url':f['url'],'sha256':h.hexdigest(),'staged_unix':time.time()})
        (a.state/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        print('STAGED',f['filename'],flush=True)
    raise RuntimeError('resolution limit reached')

if __name__=='__main__':main()
