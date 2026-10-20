#!/usr/bin/env python3
"""Exactly one authorized parent startup + candidate OwnBook diagnostic pair."""
from pathlib import Path
import hashlib,importlib.util,json,os,re,signal,subprocess,sys,time
ROOT=Path('/workspace/dwqww');HERE=Path(__file__).resolve().parent;OUT=HERE/'diagnostic-attempt1';OUT.mkdir(exist_ok=False)
def interrupted(signum,frame):
 signal.signal(signal.SIGTERM,signal.SIG_IGN);signal.signal(signal.SIGINT,signal.SIG_IGN)
 raise KeyboardInterrupt('Termination signal '+str(signum))
signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGINT,interrupted)
START=time.monotonic();RUN_DEADLINE=START+50 # Up to10s reserved for trusted cleanup, aggregate60s.
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def snapshot():
 data={}
 for label in ['see','mask']:
  source=Path('/workspace/.cloud-setup/forge-pin-'+label+'-source');build=Path('/workspace/.cloud-setup/forge-pin-'+label+'-tsan')
  data[label]={'binaries':{name:sha(build/name) for name in ['forge','libforge_core.a']},'source':{p.relative_to(source).as_posix():sha(p) for p in sorted(source.rglob('*'),key=lambda p:p.relative_to(source).as_posix()) if p.is_file()}}
 return data

def context():
 data={'affinity':sorted(os.sched_getaffinity(0))}
 for name in ['/proc/self/cgroup','/sys/fs/cgroup/cpu.max','/sys/fs/cgroup/cpu.stat','/sys/fs/cgroup/cpu.pressure','/sys/fs/cgroup/memory.pressure','/sys/fs/cgroup/memory.events','/proc/pressure/cpu','/proc/pressure/memory']:
  try:data[name]=Path(name).read_text()
  except OSError as error:data[name]={'read_error':repr(error)}
 return data

# Exact existing causal trusted cleanup, including descendants after leader exit.
spec=importlib.util.spec_from_file_location('trusted_cleanup',ROOT/'.github/hosted-pin-see-strength/run_hosted.py');trusted=importlib.util.module_from_spec(spec);spec.loader.exec_module(trusted)
def cleanup_group(child):
 previous={sig:signal.getsignal(sig) for sig in [signal.SIGTERM,signal.SIGINT]}
 for sig in previous:signal.signal(sig,signal.SIG_IGN)
 try:trusted.stop_group(child)
 finally:
  for sig,handler in previous.items():signal.signal(sig,handler)

original_paths=[ROOT/'validation/pin-mask-see-20261020/native/frozen-tsan-attempt1'/name for name in ['ctest.stdout','ctest.stderr','summary.json']]+[ROOT/'validation/pin-mask-see-20261020/native/tsan-driver.stderr',Path('/workspace/.cloud-setup/forge-pin-mask-tsan/Testing/Temporary/LastTest.log'),Path('/workspace/.cloud-setup/forge-pin-mask-tsan/ownbook-regression.json')]
original_before={str(p):sha(p) for p in original_paths}
record={'original_failure_sha256_before':original_before,'status':'RUNNING','scope':'One parent15 startup and one candidate16 unchanged five-transition OwnBook; diagnostic only; original failed batch remains FAILED','aggregate_guard_seconds':60,'execution_guard_seconds':50,'cleanup_reserve_seconds':10,'trusted_cleanup_file':str(ROOT/'.github/hosted-pin-see-strength/run_hosted.py'),'trusted_cleanup_sha256':sha(ROOT/'.github/hosted-pin-see-strength/run_hosted.py'),'observer_sha256':sha(HERE/'diagnostic_observer.py'),'supervisor_sha256':sha(Path(__file__)),'before':snapshot(),'host_before':context(),'commands':[],'results':[],'strace_enabled':Path('/usr/bin/strace').is_file()}
(OUT/'state.json').write_text(json.dumps(record,indent=2)+'\n');env=os.environ.copy();env['TSAN_OPTIONS']='halt_on_error=1:exitcode=66';env['PYTHONDONTWRITEBYTECODE']='1'
try:
 for case in ['parent15-handshake','candidate16-ownbook']:
  childout=OUT/case;trace=OUT/(case+'.strace.log');command=[sys.executable,'-B',str(HERE/'diagnostic_observer.py'),'--case',case,'--out',str(childout)]
  if record['strace_enabled']:command=['/usr/bin/strace','-f','-ttt','-T','-s','65535','-xx','-e','trace=process,read,write,futex','-o',str(trace)]+command
  record['commands'].append(command);(OUT/'state.json').write_text(json.dumps(record,indent=2)+'\n')
  if time.monotonic()>=RUN_DEADLINE:raise RuntimeError('aggregate_execution_guard_before_case')
  with (OUT/(case+'.wrapper.stdout')).open('xb') as stdout,(OUT/(case+'.wrapper.stderr')).open('xb') as stderr:
   child=subprocess.Popen(command,stdout=stdout,stderr=stderr,env=env,start_new_session=True);row={'case':case,'leader_pid':child.pid,'started_monotonic':time.monotonic()}
   try:code=child.wait(timeout=max(.001,RUN_DEADLINE-time.monotonic()))
   except subprocess.TimeoutExpired:
    row['error']='aggregate_execution_deadline';cleanup_group(child);raise RuntimeError('aggregate_execution_deadline')
   finally:
    row['returncode']=child.poll();row['finished_monotonic']=time.monotonic()
    try:os.killpg(child.pid,0)
    except ProcessLookupError:row['owned_process_group_empty_after_leader']=True
    else:
     row['owned_process_group_empty_after_leader']=False;cleanup_group(child);row['owned_orphan_cleanup_required']=True
    record['results'].append(row)
   if row.get('owned_orphan_cleanup_required'):raise RuntimeError('owned_descendant_after_leader_exit')
   resultpath=childout/'result.json'
   if not resultpath.exists():raise RuntimeError('instrumentation_produced_no_case_result')
   row['case_result']=json.loads(resultpath.read_text());row['case_result_sha256']=sha(resultpath)
   if record['strace_enabled']:
    lines=trace.read_text(errors='replace').splitlines()
    def trace_pid(line):
     match=re.match(r'^(?:\[pid\s+)?(\d+)(?:\])?\s+',line);return int(match[1]) if match else None
    edges=[]
    for line in lines:
     match=re.search(r'(?:clone3?|fork|vfork)(?:\(| resumed>).*?=\s*(\d+)\b',line)
     if match and trace_pid(line) is not None:edges.append((trace_pid(line),int(match[1])))
    engine_pids={row['case_result']['engine_pid']}
    while True:
     found={child for parent,child in edges if parent in engine_pids}
     if found<=engine_pids:break
     engine_pids|=found
    row['engine_trace_pids']=sorted(engine_pids)
    for fd in [1,2]:
     selected=[line for line in lines if trace_pid(line) in engine_pids and re.search(r'\bwrite\('+str(fd)+r',',line)];(OUT/(case+'.fd'+str(fd)+'-write-records.txt')).write_text('\n'.join(selected)+('\n' if selected else ''))
     payload=bytearray();parsed=0
     for line in selected:
      match=re.search(r'write\('+str(fd)+r', "((?:\\x[0-9a-fA-F]{2})*)", (\d+)\)\s*=\s*(\d+)',line)
      if match:
       data=bytes.fromhex(match[1].replace('\\x',''));payload.extend(data[:int(match[3])]);parsed+=1
     (OUT/(case+'.fd'+str(fd)+'-write-bytes.bin')).write_bytes(payload);row['fd'+str(fd)+'_write_records']=len(selected);row['fd'+str(fd)+'_complete_records_parsed']=parsed;row['fd'+str(fd)+'_parsed_byte_capture_complete']=parsed==len(selected)
   if code==3 or row['case_result']['status']=='INSTRUMENTATION_FAILED':raise RuntimeError('instrumentation_failure_no_second_case_or_retry')
  (OUT/'state.json').write_text(json.dumps(record,indent=2)+'\n')
 record['status']='PAIR_FINISHED_DIAGNOSTIC_ONLY'
except BaseException as error:record['status']='STOPPED_FAILED_OR_INCOMPLETE';record['error']=repr(error)
finally:
 record['original_failure_sha256_after']={str(p):sha(p) for p in original_paths};record['original_failure_unchanged']=record['original_failure_sha256_before']==record['original_failure_sha256_after'];record['after']=snapshot();record['frozen_inputs_unchanged']=record['before']==record['after'];record['host_after']=context();record['elapsed_seconds']=time.monotonic()-START
 if not record['frozen_inputs_unchanged'] or not record['original_failure_unchanged'] or record['elapsed_seconds']>60:record['status']='STOPPED_FAILED_OR_INCOMPLETE';record.setdefault('error','input_change_or_aggregate_guard')
 (OUT/'state.json').write_text(json.dumps(record,indent=2)+'\n')
 paths=sorted([p for p in OUT.rglob('*') if p.is_file()],key=lambda p:p.relative_to(OUT).as_posix());(OUT/'SHA256SUMS').write_text(''.join(sha(p)+'  '+p.relative_to(OUT).as_posix()+'\n' for p in paths));print(json.dumps({'status':record['status'],'elapsed_seconds':record['elapsed_seconds'],'frozen_inputs_unchanged':record['frozen_inputs_unchanged'],'results':[{'case':r['case'],'returncode':r.get('returncode'),'status':r.get('case_result',{}).get('status')} for r in record['results']]}))
sys.exit(0 if record['status']=='PAIR_FINISHED_DIAGNOSTIC_ONLY' and all(r.get('case_result',{}).get('status')=='PASS_DIAGNOSTIC_ONLY' for r in record['results']) else 1)
