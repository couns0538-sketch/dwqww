#!/usr/bin/env python3
"""Execute a newly exec'd eight-thread cold-constructor probe on every iteration."""
import argparse,base64,hashlib,json,os,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('probe',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--runs',type=int,default=1000);a=p.parse_args()
if a.runs<1:raise SystemExit('positive run count required')
exe=a.probe.resolve(strict=True);a.out.mkdir(parents=False,exist_ok=False);digest=hashlib.sha256(exe.read_bytes()).hexdigest();env=dict(os.environ);env['TSAN_OPTIONS']='halt_on_error=1:exitcode=66';rows=[];start=time.monotonic();expected=b'COLD_FIRST_BOARD_PASS workers=8 startpos_d3=8902 kiwipete_d2=2039\n';status='UNVERIFIED'
with (a.out/'forge_sol_S04_cold_runs_20261025.jsonl').open('x') as log:
 for index in range(a.runs):
  child=subprocess.Popen([str(exe)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env);stdout,stderr=child.communicate();row={'iteration':index+1,'pid':child.pid,'exec_argv':[str(exe)],'exit':child.returncode,'stdout_sha256':hashlib.sha256(stdout).hexdigest(),'stderr_sha256':hashlib.sha256(stderr).hexdigest(),'stdout_base64':base64.b64encode(stdout).decode(),'stderr_base64':base64.b64encode(stderr).decode()};rows.append(row);log.write(json.dumps(row,sort_keys=True)+'\n');log.flush()
  if child.returncode!=0 or stdout!=expected or stderr:
   status='FAIL';print('COLD_FRESH_PROCESS_FAIL',index+1,'exit',child.returncode,flush=True);break
  if (index+1)%100==0:os.fsync(log.fileno());print('COLD_FRESH_PROCESS_PASS',index+1,flush=True)
 else:status='PASS'
result={'status':status,'probe_sha256':digest,'TSAN_OPTIONS':env['TSAN_OPTIONS'],'requested_fresh_processes':a.runs,'completed_processes':len(rows),'workers_per_process':8,'successful_processes':sum(r['exit']==0 and r['stdout_sha256']==hashlib.sha256(expected).hexdigest() and r['stderr_sha256']==hashlib.sha256(b'').hexdigest() for r in rows),'elapsed_seconds':time.monotonic()-start,'policy':'Every iteration is a separate Popen exec; no serial Board bootstrap, warm loop, race retry or sanitizer suppression. No signal/kill/affinity/host-limit API.','owned_live_child':None};(a.out/'forge_sol_S04_cold_result_20261025.json').write_text(json.dumps(result,indent=2)+'\n');print(status,len(rows),'fresh eight-thread processes');raise SystemExit(0 if status=='PASS' else 1)
