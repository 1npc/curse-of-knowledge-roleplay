"""Mark a restored runtime ready only after version, dependency and CUDA checks."""
import importlib.metadata as m,json,os,subprocess,time,sys,hashlib
from pathlib import Path

def main():
 root=Path(sys.argv[1]);ops=root/'operations';lock=ops/'original-runtime-requirements.txt'
 expected=dict(x.split('==') for x in lock.read_text().splitlines() if x)
 installed={name:m.version(name) for name in expected}
 bad={name:[v,installed[name]] for name,v in expected.items() if v!=installed[name]}
 if bad:raise RuntimeError('Recorded runtime pins differ: '+repr(bad))
 subprocess.run([sys.executable,'-m','pip','check'],check=True)
 import torch,vllm,transformers
 if not torch.cuda.is_available():raise RuntimeError('CUDA unavailable')
 receipt={'ready':True,'checked_unix':time.time(),'python':sys.version,'torch':torch.__version__,'vllm':vllm.__version__,'transformers':transformers.__version__,'cuda':torch.version.cuda,'installed':installed,'requirements_sha256':hashlib.sha256(lock.read_bytes()).hexdigest(),'visible_gpu':os.environ.get('CUDA_VISIBLE_DEVICES')}
 (ops/'runtime-ready.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:receipt[k] for k in ['ready','torch','vllm','transformers','cuda']}),flush=True)
if __name__=='__main__':main()
