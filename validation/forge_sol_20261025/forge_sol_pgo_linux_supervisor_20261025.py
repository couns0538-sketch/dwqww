from pathlib import Path
import os,resource,json,datetime,subprocess,time,hashlib
h=Path('/workspace/forge-sol-20261025');p=Path('/workspace/forge-sol-20261025-pgo');out=p/'forge_sol_pgo_linux_proof_20261025';assert not out.exists()
argv=['bash',str(p/'forge_sol_pgo_build_20261025.sh'),'--source',str(h/'forge_sol_return_20261025/forge_sol_lock_source_20261025'),'--recipe',str(h/'forge_sol_return_20261025/forge_sol_lock_pc_recipe_20261025.ps1'),'--out',str(out),'--cxx','/usr/bin/g++','--cmake','/workspace/.cloud-setup/venv/lib/python3.12/site-packages/cmake/data/bin/cmake']
env={**os.environ,'FORGE_PGO_REVIEWED_ENVELOPE':'ACTIVE','FORGE_PGO_ADMISSION_DEADLINE_UNIX':str(time.time()+2580),'PYTHONDONTWRITEBYTECODE':'1','CTEST_PARALLEL_LEVEL':'1'}
def limits():
 os.sched_setaffinity(0,{0,1,2,3});os.nice(19);resource.setrlimit(resource.RLIMIT_AS,(3*1024**3,3*1024**3))
r={'status':'STARTING','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'argv':argv,'scope':'Native Linux GCC14.2 pure-PGO build/correctness proof; no Windows/Zen5 speed claim','cpu_mask':[0,1,2,3],'nice':19,'per_process_address_space_limit_bytes':3*1024**3,'memory_limit_scope':'Inherited per-process RLIMIT_AS, not aggregate Windows Job limit','workers':'one compiler/build job at a time','original_CTest_transitive_kill_policy':'Linux QA only; original timeout cleanup may kill its own engine. PC orchestrator excludes CTest.','worker_sha256':hashlib.sha256((p/'forge_sol_pgo_worker_20261025.py').read_bytes()).hexdigest(),'actual_exit':None}
receipt=h/'forge_sol_pgo_linux_supervisor_20261025.json'
with (h/'forge_sol_pgo_linux_supervisor_20261025.stdout').open('xb') as stdout,(h/'forge_sol_pgo_linux_supervisor_20261025.stderr').open('xb') as stderr:
 child=subprocess.Popen(argv,cwd='/workspace/dwqww',env=env,stdout=stdout,stderr=stderr,preexec_fn=limits);r.update(status='RUNNING',pid=child.pid,affinity_readback=sorted(os.sched_getaffinity(child.pid)),nice_readback=os.getpriority(os.PRIO_PROCESS,child.pid));receipt.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True);code=child.wait()
r.update(status='PASS' if code==0 else 'FAIL',actual_exit=code,closed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());receipt.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
raise SystemExit(code)
