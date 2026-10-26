#!/usr/bin/env python3
"""One root-authorized B+locked-net control; outside-tool argv/resource evidence."""
import datetime,hashlib,json,os,pathlib,re,runpy,signal,subprocess,sys,time
sys.dont_write_bytecode=True
R=pathlib.Path('/workspace/forge-pack24-20261026/S26')
PROTOCOL=R/'forge_sol_S26_native_B_lock_protocol_20261026.json'
TOOL=R/'forge_sol_S26_netbatch_20261026.py'
NATIVE=R/'forge_sol_S26_NATIVE_B_lock_control_20261026'
OUT=R/'forge_sol_S26_NATIVE_B_lock_OUTSIDE_20261026'

def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def write(p,j):
 b=json.dumps(j,indent=2,allow_nan=False)+'\n';pathlib.Path(p).write_text(b)
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def mem():
 for line in pathlib.Path('/proc/meminfo').read_text().splitlines():
  if line.startswith('MemAvailable:'):return int(line.split()[1])*1024
 raise RuntimeError('MemAvailable unavailable')
def free():
 s=os.statvfs('/workspace');return s.f_bavail*s.f_frsize

def proc_table():
 rows={}
 for p in pathlib.Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   raw=(p/'stat').read_text();end=raw.rfind(')');fields=raw[end+2:].split();comm=raw[raw.find('(')+1:end]
   row={'pid':int(p.name),'ppid':int(fields[1]),'comm':comm,'starttime_ticks':int(fields[19])}
   rows[row['pid']]=row
  except (OSError,ValueError,IndexError):pass
 return rows

def details(row):
 p=pathlib.Path('/proc')/str(row['pid']);row=dict(row)
 for name,fn in [('nice',lambda:os.getpriority(os.PRIO_PROCESS,row['pid'])),('affinity',lambda:sorted(os.sched_getaffinity(row['pid']))),('argv',lambda:[x.decode(errors='replace') for x in (p/'cmdline').read_bytes().split(b'\0') if x])]:
  try:row[name]=fn()
  except OSError:row[name]=None
 return row

def children(table,pid):
 keep={pid};changed=True
 while changed:
  changed=False
  for n,row in table.items():
   if row['ppid'] in keep and n not in keep:keep.add(n);changed=True
 return [details(table[n]) for n in sorted(keep) if n in table]

def main():
 if OUT.exists() or NATIVE.exists():raise RuntimeError('NEW output paths required; no native retry or overwrite')
 protocol=json.loads(PROTOCOL.read_text());assert protocol['state']=='AUTHORIZED_BEFORE_NATIVE_LAUNCH'
 assert sha(TOOL)==protocol['source_tool_sha256']
 base=pathlib.Path(protocol['base']);net=pathlib.Path(protocol['net']);tests=base/'tests/tests.cpp'
 assert sha(net)==protocol['net_sha256'];assert sha(tests)==protocol['test_source_sha256']
 m=runpy.run_path(str(TOOL));before=m['snapshot'](base);decl=json.loads((R/'forge_sol_S26_dependencies_20261026.json').read_text())
 for item in decl.values():assert sha(item['path'])==item['sha256']
 cxx=pathlib.Path('/usr/bin/c++').resolve(strict=True)
 assert sha(cxx)=='6b3696e4dcb85e1c949c732a02befa50e3983ecf94ce7e8e58d9d503b954b79d'
 table=proc_table();active=[details(row) for row in table.values() if re.fullmatch(r'(?:forge.*|stockfish.*|fastchess.*|clang.*|gcc.*|g\+\+.*|cc1.*|lto.*|cmake|ctest|ninja|make)',row['comm'],re.I)]
 if active:raise RuntimeError('native preflight process conflict: '+json.dumps(active))
 if free()<32*1024**2:raise RuntimeError('Insufficient disk before native:32MiB minimum')
 if mem()<protocol['RAM_floor']:raise RuntimeError('Insufficient RAM before native')
 OUT.mkdir();lock=R/'forge_sol_S26_resource.lock';assert lock.is_file();lock_before={'sha256':sha(lock),'bytes':lock.stat().st_size}
 env=dict(os.environ,PYTHONPATH='/workspace/.cloud-setup/venv/lib/python3.12/site-packages',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',CMAKE_BUILD_PARALLEL_LEVEL='1',TMPDIR=str(OUT),TMP=str(OUT),TEMP=str(OUT))
 relevant={k:env[k] for k in ['PATH','PYTHONPATH','PYTHONDONTWRITEBYTECODE','OMP_NUM_THREADS','CMAKE_BUILD_PARALLEL_LEVEL','TMPDIR','TMP','TEMP','CXX','CC','CXXFLAGS','CPPFLAGS','LDFLAGS','MAKEFLAGS'] if k in env}
 argv=['/usr/bin/taskset','-c','4','/usr/bin/nice','-n','19',sys.executable,'-B',str(TOOL),
  '--base',str(base),'--net',str(net),'--out',str(NATIVE),
  '--bench-ref',str(R/'forge_sol_S26_bench_refs_20261026.json'),'--allowlist',str(R/'forge_sol_S26_allowlist_20261026.json'),
  '--dependencies',str(R/'forge_sol_S26_dependencies_20261026.json'),'--suite','/workspace/forge-sol-next-20261024/int16-review/wac300.epd',
  '--lock-file',str(lock),'--cmake','/workspace/.cloud-setup/venv/lib/python3.12/site-packages/cmake/data/bin/cmake',
  '--ctest','/workspace/.cloud-setup/venv/lib/python3.12/site-packages/cmake/data/bin/ctest',
  '--objdump',str(pathlib.Path('/usr/bin/objdump').resolve()),'--cxx',str(cxx),'--cpu','4','--record-pins','--timeout','1800']
 identities={str(p):sha(p) for p in [PROTOCOL,TOOL,tests,net,R/'forge_sol_S26_bench_refs_20261026.json',R/'forge_sol_S26_allowlist_20261026.json',R/'forge_sol_S26_dependencies_20261026.json',cxx]}
 invocation={'utc':now(),'driver_sha256':sha(__file__),'argv':argv,'cwd':'/','environment':relevant,'protocol':protocol,'protocol_sha256':sha(PROTOCOL),'input_sha256_before':identities,'source_before':before,'lock_before':lock_before,'free_bytes_before':free(),'RAM_available_before':mem(),'active_native_preflight':active,'scope':'One native B+locked-net control; --compare-lock omitted; no f019 or retry. Raw output preserved. Root alone reviews/accepts/publishes.'}
 write(OUT/'invocation.json',invocation);started=time.monotonic();seen={};limits={'min_free_bytes':free(),'min_RAM_available':mem()};p=None;stop_reason=None
 try:
  with (OUT/'tool.stdout').open('wb') as so,(OUT/'tool.stderr').open('wb') as se,(OUT/'resources.jsonl').open('w') as resources:
   p=subprocess.Popen(argv,cwd='/',env=env,stdout=so,stderr=se,start_new_session=True)
   write(OUT/'launch.json',{'utc':now(),'pid':p.pid,'argv':argv,'cwd':'/'})
   while p.poll() is None:
    table=proc_table();owned=children(table,p.pid);disk=free();ram=mem();limits['min_free_bytes']=min(limits['min_free_bytes'],disk);limits['min_RAM_available']=min(limits['min_RAM_available'],ram)
    for row in owned:seen[(row['pid'],row['starttime_ticks'])]=row
    sample={'utc':now(),'elapsed_seconds':time.monotonic()-started,'free_bytes':disk,'RAM_available':ram,'owned_processes':owned};resources.write(json.dumps(sample)+'\n');resources.flush()
    write(OUT/'progress.json',sample)
    if disk<8*1024**2:stop_reason='DISK_FLOOR8MiB'
    if ram<protocol['RAM_floor']:stop_reason='RAM_FLOOR3GiB'
    if stop_reason:
     p.send_signal(signal.SIGTERM);p.wait(timeout=15);break
    time.sleep(2)
   p.wait()
 except BaseException as exc:
  stop_reason=stop_reason or (type(exc).__name__+': '+str(exc))
  if p is not None and p.poll() is None:
   p.send_signal(signal.SIGTERM)
   try:p.wait(timeout=15)
   except subprocess.TimeoutExpired:stop_reason+='; CLI still alive after SIGTERM; owned pid='+str(p.pid)
 finally:
  after=m['snapshot'](base);table=proc_table();live=[]
  for (pid,start),row in seen.items():
   if pid in table and table[pid]['starttime_ticks']==start:live.append(details(table[pid]))
  record={'utc':now(),'driver_sha256':sha(__file__),'elapsed_seconds':time.monotonic()-started,'cli_pid':p.pid if p else None,'cli_returncode':p.poll() if p else None,'stop_reason':stop_reason,'resource_minima':limits,'observed_owned_processes':list(seen.values()),'observed_owned_processes_still_live':live,'source_after':after,'source_unchanged':before==after,'input_sha256_after':{q:sha(q) for q in identities},'lock_after':{'sha256':sha(lock),'bytes':lock.stat().st_size},'native_out':str(NATIVE),'checks':{},'acceptance':'PENDING_ROOT_REVIEW_NO_ADOPTION_OR_EXTERNAL_STRENGTH_CLAIM'}
  checks=record['checks'];checks['cli_exit0']=p is not None and p.poll()==0;checks['no_stop']=stop_reason is None;checks['source_unchanged']=before==after;checks['inputs_unchanged']=record['input_sha256_after']==identities;checks['lock_bytes_unchanged']=record['lock_after']==lock_before;checks['all_observed_children_closed']=not live
  try:
   result=json.loads((NATIVE/'result.json').read_text());record['tool_result_sha256']=sha(NATIVE/'result.json');record['tool_status']=result.get('status');checks['tool_PASS_one_net_no_compare']=result.get('status')=='PASS' and len(result.get('nets',[]))==1 and not result.get('failed_nets') and result.get('compare_lock') is None
   rows=result.get('nets',[])+result.get('failed_nets',[]);row=rows[0] if rows else None
   if row:
    record['engine_sha256']=sha(row['engine']);checks['engine_expected55fa']=record['engine_sha256']==protocol['expected_engine_sha256']
    record['bench']=row.get('bench');checks['five_fixed_bench']=row.get('bench')==dict(zip(['11','13','16','20','22'],protocol['bench_fixed']))
    checks['FMA0_executable_and_object']=row.get('fma',{}).get('status')=='PASS' and row['fma']['fma_count']==0 and len(row['fma']['artifacts'])==2 and all(x['fma_count']==0 for x in row['fma']['artifacts'])
    cases=row.get('ctest',{}).get('test_cases',[]);known=[line for case in cases for line in case.get('known_diagnostics',[])]
    record['CTest']={'status':row.get('ctest',{}).get('status'),'returncode':row.get('ctest',{}).get('returncode'),'cases':len(cases),'known_diagnostics':known};checks['CTest15_fourKNOWN_zeroFAIL']=len(cases)==15 and row['ctest']['returncode']==0 and all(not case['failed'] and case['status']=='PASS' for case in cases) and len(known)==4 and all(line.startswith('KNOWN_FAILURE:') for line in known)
    wac=json.loads((pathlib.Path(row['job'])/'wac/result.json').read_text());record['WAC']={'status':wac['status'],'solved':wac['solved'],'evaluated':wac['evaluated'],'movetime_ms':wac['movetime_ms'],'reference_status':row['wac']['reference_status'],'scope':'Single local box screen only; no external reference/reproduction/strength/speed claim'}
    checks['single_WAC300_1000ms_no_external_ref']=wac['status']=='PASS' and wac['evaluated']==300 and wac['movetime_ms']==1000 and row['wac']['reference_status']=='UNKNOWN' and len(json.loads((pathlib.Path(row['job'])/'wac/processes.json').read_text()))==1 and all(x['legal'] for x in wac['results'])
    checks['pin_proposal_unreviewed_unapplied']=row['pin_proposal']['review_status']=='UNREVIEWED' and row['pin_proposal']['applied'] is False and row['pin_proposal']['original_expectations_changed'] is False
    cap=json.loads((pathlib.Path(row['job'])/'bench/processes.json').read_text());first=cap[0];stdin=pathlib.Path(first['stdin']['path']).read_text();checks['first_runtime_bare11']=first['label']=='FIRST_BARE_BENCH11' and stdin.startswith('bench 11\n') and 'uci' not in stdin and first['status']=='PASS'
    recipe=m['load_dependency'](decl['recipe'],'outside_s27_recipe');proof=m['audit_build_recipe'](recipe,pathlib.Path(row['private_source']),pathlib.Path(row['job'])/'build',cxx);write(OUT/'actual_recipe_independent_recheck.json',proof);record['actual_TUs']=len(proof['translation_units']);record['actual_compiler']=proof['compiler'];checks['actual_recipe_guarded']=proof['status']=='PASS' and row['recipe_before']['status']=='PASS' and row['recipe_after']['status']=='PASS'
    checks['nice19_CPU4']=result['resource_lease']['nice']==19 and result['resource_lease']['affinity']==[4] and all(x.get('nice')==19 and x.get('affinity')==[4] for x in seen.values() if x.get('argv') and not x['argv'][0].endswith('taskset'))
  except Exception as exc:record['evaluation_error']=type(exc).__name__+': '+str(exc);checks['evaluation_complete']=False
  record['status']='CONTROL_CHECKS_PASS_PENDING_ROOT_REVIEW' if checks and all(checks.values()) else 'CONTROL_FAILED_PRESERVED_NO_RETRY'
  record['stdout']={'path':str(OUT/'tool.stdout'),'sha256':sha(OUT/'tool.stdout')};record['stderr']={'path':str(OUT/'tool.stderr'),'sha256':sha(OUT/'tool.stderr')}
  write(OUT/'result.json',record)
  files=sorted(x for x in OUT.rglob('*') if x.is_file() and x.name!='SHA256SUMS.txt');(OUT/'SHA256SUMS.txt').write_text(''.join(sha(x)+'  '+str(x.relative_to(OUT))+'\n' for x in files))
  print(json.dumps({'status':record['status'],'returncode':record['cli_returncode'],'stop_reason':stop_reason,'checks':checks,'out':str(OUT)},indent=2),flush=True)
 return 0 if record['status']=='CONTROL_CHECKS_PASS_PENDING_ROOT_REVIEW' else 1

if __name__=='__main__':raise SystemExit(main())
