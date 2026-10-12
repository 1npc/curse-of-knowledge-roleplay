python3 -u - <<'PY'
from pathlib import Path
import json,time,subprocess,shutil,hashlib
r=Path('/data/qianru/over-comprehension-v2-20261001');ops=r/'operations'
q=json.loads((ops/'queue.json').read_text())
sums=[json.loads(p.read_text()) for p in (r/'responses').glob('*/*/summary-*.json')]
health={}
launch=json.loads((ops/'weight-recovery-launch.json').read_text()) if (ops/'weight-recovery-launch.json').exists() else json.loads((ops/'range-weight-supplier.json').read_text())
worker_launch_path=next((p for p in [ops/'available-gpu-worker-launch.json',ops/'gpu5-worker-launch.json'] if p.exists()),None)
worker_policy=json.loads(worker_launch_path.read_text()) if worker_launch_path else None
workers=[('worker_'+slot,info['pid']) for slot,info in worker_policy['workers'].items()] if worker_policy else [('worker_1',2645609),('worker_2',2645610)]
for name,pid in [('finalizer',2567062),*workers,('weight_supplier',launch['pid'])]:
 p=Path('/proc')/str(pid)/'cmdline'
 try:cmd=p.read_bytes().replace(b'\x00',b' ').decode()
 except FileNotFoundError:cmd=''
 health[name]={'pid':pid,'alive':bool(cmd),'command':cmd}
 if name.startswith('worker_') and worker_policy:
  health[name]['matches_launch_command']=cmd.strip()==' '.join(worker_policy['workers'][name.split('_',1)[1]]['command'])
weights={}
ref=json.loads((r/'code/harness/weights_reference.json').read_text())['models']
for p in ops.glob('range-weight-transport-*.json'):
 d=json.loads(p.read_text())
 if not d.get('ok'):weights[d['model']]={'verified_bytes':sum(f['bytes'] for f in d['files'].values()),'total_bytes':sum(f['bytes'] for f in ref[d['model']]['files'].values()),'error':d.get('error')}
verified=json.loads((ops/'weights-verified.json').read_text())['models']
weight_status={m:{'ok':v.get('ok'),'revision':v.get('revision'),'matches_pinned_revision':v.get('revision')==ref[m]['revision'],'path_exists':Path(v['path']).is_dir() if v.get('path') else False} for m,v in verified.items()}
recovery=json.loads((ops/'weight-recovery-state.json').read_text()) if (ops/'weight-recovery-state.json').exists() else None
for model,state in (recovery or {}).get('models',{}).items():
 if state.get('status')=='downloading' and state.get('attempts'):
  pid=state['attempts'][-1]['child_pid'];p=Path('/proc')/str(pid)/'cmdline'
  try:cmd=p.read_bytes().replace(b'\x00',b' ').decode()
  except FileNotFoundError:cmd=''
  health['download_'+model]={'pid':pid,'alive':bool(cmd),'command':cmd}
policy_path=r/'code'/worker_policy.get('amendment_path','docs/access-v2/gpu5-only-amendment.json') if worker_policy else r/'code/docs/access-v2/hardware-amendment.json'
policy_doc=json.loads(policy_path.read_text()) if policy_path.exists() else None
policy_integrity={'amendment_matches_launch':hashlib.sha256(policy_path.read_bytes()).hexdigest()==worker_policy['amendment_sha256'],'source_digests_match':{name:hashlib.sha256((r/'code'/name).read_bytes()).hexdigest()==digest for name,digest in policy_doc['operational_code_sha256'].items()},'allowed_gpu_uuid':policy_doc['allowed_gpu_uuid']} if worker_policy and policy_doc else None
phase_summaries=[{k:v for k,v in summary.items() if k in ('model','records','planned','status','interrupted_chunks','responses_sha256','run_sha256')} for summary in sums]
print(json.dumps({'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'models':q['models'],'actual_records_in_completed_phases':sum(s['records'] for s in sums),'processes':health,'gpu_policy':worker_policy['restriction'] if worker_policy else None,'worker_launch':worker_policy,'worker_launch_path':str(worker_launch_path) if worker_launch_path else None,'pending_weight_transport':weights,'weights_verified':weight_status,'phase_summaries':phase_summaries,'gpu_policy_integrity':policy_integrity,'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).splitlines(),'recovery':json.loads((ops/'weight-recovery-state.json').read_text()) if (ops/'weight-recovery-state.json').exists() else None,'free_gib':shutil.disk_usage(r).free/(1<<30),'gpu_compute_apps':subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader,nounits'],text=True).splitlines(),'supplier_tail':{p.name:p.read_text().splitlines()[-5:] for p in (r/'logs').glob('weight-recovery-*.log')}},indent=2))
PY
