#!/usr/bin/env python3
"""Prespecified one-attempt/net orchestration; no adopted engine/pin changes."""
import argparse,datetime,hashlib,json,os,pathlib,re,signal,subprocess,sys,time,types,xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
R=pathlib.Path('/workspace/forge-pack24-20261026/S26')
PLAN=R/'forge_sol_S26_f019_f023_command_preflight_20261026.json'
APPROVAL=R/'forge_sol_S26_f019_f023_CACHE_CLOSED_receipt_20261026.json'
MASTER=R/'forge_sol_S26_NATIVE_f019_f023_BATCH_OUTSIDE_20261026'
TOOL=R/'forge_sol_S26_netbatch_20261026.py'
HELPER=R/'forge_sol_S26_native_B_lock_driver_20261026.py'

def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text())
def write(p,j):pathlib.Path(p).write_text(json.dumps(j,indent=2,allow_nan=False)+'\n')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def module(path,name,expected=None):
 source=pathlib.Path(path).read_bytes()
 if expected and hashlib.sha256(source).hexdigest()!=expected:raise RuntimeError('source digest mismatch: '+str(path))
 m=types.ModuleType(name);m.__file__=str(path);exec(compile(source,str(path),'exec'),m.__dict__);return m
H=module(HELPER,'closed_B_control_helpers')

def seal(root):
 path=root/'SHA256SUMS.txt';files=sorted(p for p in root.rglob('*') if p.is_file() and p!=path)
 path.write_text(''.join(sha(p)+'  '+str(p.relative_to(root))+'\n' for p in files))
 return {'path':str(path),'sha256':sha(path),'entries':len(files)}
def verify_manifest(root):
 manifest=root/'SHA256SUMS.txt';count=total=0
 for line in manifest.read_text().splitlines():
  d,rel=line.split('  ',1);p=root/rel
  if not p.is_file() or sha(p)!=d:raise RuntimeError('manifest mismatch: '+str(p))
  count+=1;total+=p.stat().st_size
 return {'path':str(manifest),'sha256':sha(manifest),'entries':count,'payload_bytes':total,'status':'PASS'}
def diagnostics(xml):
 cases=list(ET.parse(xml).getroot().iter('testcase'));lines=[]
 for case in cases:
  for item in case:
   if item.tag in ('failure','error','system-out','system-err'):
    lines.extend(line for line in ''.join(item.itertext()).splitlines() if re.match(r'^(?:FAIL:|KNOWN_FAILURE:|PIN_MISMATCH:)',line))
 return cases,list(dict.fromkeys(lines))

def evaluate(plan,netplan,outside,process,source_before,input_before,lock_before,seen,limits,stop_reason,toolmodule,decl):
 native=pathlib.Path(netplan['native_out']);case=netplan['case'];base=pathlib.Path(plan['base']);checks={}
 table=H.proc_table();live=[H.details(table[pid]) for (pid,start) in seen if pid in table and table[pid]['starttime_ticks']==start]
 source_after=toolmodule.snapshot(base);inputs_after={p:sha(p) for p in input_before};lock=pathlib.Path(plan['shared_existing_lock'])
 record={'utc':now(),'id':case['id'],'case_protocol':case,'native_out':str(native),'outside_out':str(outside),'returncode':process.poll() if process else None,'stop_reason':stop_reason,
  'source_after':source_after,'input_sha256_after':inputs_after,'resource_minima':limits,'observed_owned_processes':list(seen.values()),'observed_owned_processes_still_live':live,'checks':checks,'unsafe_abort':True,
  'interpretation':'Single prespecified local box attempt; an evidence-complete qualification FAIL is preserved. No retry, pin adoption, Elo/NPS/speed or new-engine acceptance.'}
 checks.update(no_resource_stop=stop_reason is None,all_observed_children_closed=not live,source_unchanged=source_before==source_after,inputs_unchanged=input_before==inputs_after,lock_bytes_unchanged=lock_before=={'sha256':sha(lock),'bytes':lock.stat().st_size})
 try:
  result=read(native/'result.json');rows=result.get('nets',[])+result.get('failed_nets',[])
  if len(rows)!=1 or result.get('compare_lock') is not None:raise RuntimeError('exactly one candidate and no compare-lock required')
  row=rows[0];job=pathlib.Path(row['job']);record.update(tool_status=result['status'],net_status=row['status'],tool_failure=result.get('failure'),native_result_sha256=sha(native/'result.json'),engine_sha256=sha(row['engine']))
  checks['tool_exit_matches_verdict']=(process.returncode==0 and result['status']=='PASS') or (process.returncode==1 and result['status']=='FAIL')
  checks['intentional_net_identity']=row['net_sha256']==case['net_sha256'] and row['net_md5']==case['net_md5'] and sha(job/'source/src/nnue_weights.inc')==case['net_sha256']
  changes=[k for k in source_before.keys()|row['private_source_sha256_before'].keys() if source_before.get(k)!=row['private_source_sha256_before'].get(k)]
  checks['private_net_only_change']=changes==['src/nnue_weights.inc'];checks['private_source_unchanged_during_attempt']=toolmodule.snapshot(job/'source')==row['private_source_sha256_before']
  checks['binary_object_unchanged']=row['binary_sha256_before']==row['binary_sha256_after'] and all(sha(p)==d for p,d in row['binary_sha256_after'].items())
  record['bench']=row.get('bench');checks['five_external_bench_refs']=row.get('bench')==case['bench_reference']
  cap=read(job/'bench/processes.json');first=cap[0];stdin=pathlib.Path(first['stdin']['path']).read_text();first_stdout=pathlib.Path(first['stdout']['path']).read_text()
  checks['first_bare_bench11_matches_candidate']=len(cap)==6 and first['label']=='FIRST_BARE_BENCH11' and stdin=='bench 11\nquit\n' and re.search(r'info string bench depth 11 nodes '+str(case['bench_reference']['11'])+r'\b',first_stdout) is not None and all(x['status']=='PASS' and x['child_waited'] for x in cap)
  record['FMA']=row['fma'];checks['FMA0_executable_and_object']=row['fma']['status']=='PASS' and row['fma']['fma_count']==0 and len(row['fma']['artifacts'])==2 and all(x['fma_count']==0 for x in row['fma']['artifacts'])
  recipe=toolmodule.load_dependency(decl['recipe'],'candidate_outside_recipe_'+case['id']);cxx=pathlib.Path('/usr/bin/c++').resolve();proof=toolmodule.audit_build_recipe(recipe,job/'source',job/'build',cxx);write(outside/'actual_recipe_independent_recheck.json',proof)
  record['actual_translation_units']=len(proof['translation_units']);record['compiler']=proof['compiler'];checks['actual_pre_post_recipe_guarded']=proof['status']=='PASS' and row['recipe_before']['status']=='PASS' and row['recipe_after']['status']=='PASS'
  wac=read(job/'wac/result.json');waccap=read(job/'wac/processes.json');wacstdin=pathlib.Path(waccap[0]['stdin']['path']).read_text();ref=case['wac1000_reference'];expected_status='UNKNOWN' if ref is None else ('PASS' if abs(wac['solved']-ref)<=3 else 'FAIL')
  record['WAC']={'solved':wac['solved'],'evaluated':wac['evaluated'],'movetime_ms':wac['movetime_ms'],'reference':ref,'reference_status':row['wac']['reference_status'],'historical_reference_scope':case['wac_reference_status'],'interpretation':'One actual local box score. UNKNOWN remains UNKNOWN for unmeasured historical references; no external speed/strength claim.'}
  checks['one_complete_legal_WAC1000']=len(waccap)==1 and waccap[0]['status']=='PASS' and wac['status']=='PASS' and wac['evaluated']==300 and wac['movetime_ms']==1000 and all(x['legal'] for x in wac['results']) and wacstdin.splitlines().count('go movetime 1000')==300
  checks['WAC_verdict_preserved']=row['wac']['reference_status']==expected_status
  pins=row['pin_observations'];record['pins']=[{k:x[k] for k in ('case','depth','bestmove','score_kind','score','pv0','documented_pin_matches')} for x in pins['cases']]
  checks['pin_observations_retained']=len(pins['cases'])==3 and pins['pins_edited'] is False
  proposal=row['pin_proposal'];checks['pin_proposal_unreviewed_unapplied']=proposal['review_status']=='UNREVIEWED' and proposal['applied'] is False and proposal['original_expectations_changed'] is False
  cases,lines=diagnostics(job/'ctest.xml');unknown=[x for x in lines if not toolmodule.reviewable_pin_line(x)]
  abnormal=any(case.find('error') is not None or case.find('skipped') is not None for case in cases)
  status_text=' '.join(' '.join(str(v) for v in item.attrib.values())+' '+''.join(item.itertext()) for case in cases for item in [case,*case.findall('failure'),*case.findall('error')])
  if re.search(r'Segmentation fault|\bSIG(?:SEGV|ABRT|KILL|TERM|ILL|FPE|BUS)\b|Timeout|timed out|Subprocess aborted|AddressSanitizer|runtime error:',status_text,re.I):abnormal=True
  record['CTest']={'status':row['ctest']['status'],'returncode':row['ctest']['returncode'],'cases':len(cases),'diagnostics':lines,'unknown_failure_cases':unknown,'classification_failure':row['ctest'].get('failure')}
  checks['CTest_complete_no_runtime_failure']=len(cases)==15 and len({x.attrib.get('name') for x in cases})==15 and not abnormal and not unknown
  checks['WAC_FAIL_never_overridden']=expected_status!='FAIL' or row['status']=='FAIL'
  checks['resource_nice19_CPU4']=result['resource_lease']['nice']==19 and result['resource_lease']['affinity']==[4] and all(x.get('nice')==19 and x.get('affinity')==[4] for x in seen.values() if x.get('argv') and not x['argv'][0].endswith('taskset'))
  record['native_manifest']=verify_manifest(native)
  record['unsafe_abort']=not all(checks.values())
  if row['status']=='FAIL':
   failure=row.get('failure','')
   qualification=('WAC differs from documentary reference' in failure or 'PIN_MISMATCH:' in failure or 'reviewed diagnostic count mismatch' in failure or 'unallowlisted test diagnostic: FAIL: WAC 001' in failure or 'unallowlisted test diagnostic: FAIL: unrestricted search chooses the winning rook underpromotion' in failure)
   if not qualification:record['unsafe_abort']=True;record['unclassified_failure']=failure
  record['status']='UNSAFE_PATH_STOP_NO_RETRY' if record['unsafe_abort'] else ('COMPLETED_QUALIFICATION_FAIL_PRESERVED' if row['status']=='FAIL' else 'COMPLETED_TOOL_PASS_PENDING_ROOT_REVIEW')
 except Exception as exc:
  record.update(evaluation_error=type(exc).__name__+': '+str(exc),status='UNSAFE_PATH_STOP_NO_RETRY',unsafe_abort=True)
 record['stdout']={'path':str(outside/'tool.stdout'),'sha256':sha(outside/'tool.stdout')};record['stderr']={'path':str(outside/'tool.stderr'),'sha256':sha(outside/'tool.stderr')}
 return record

def run_one(plan,netplan,toolmodule,decl):
 case=netplan['case'];outside=pathlib.Path(netplan['outside_out']);native=pathlib.Path(netplan['native_out']);base=pathlib.Path(plan['base']);lock=pathlib.Path(plan['shared_existing_lock'])
 if outside.exists() or native.exists():raise RuntimeError('attempt output already exists; never rerun '+case['id'])
 outside.mkdir();source_before=toolmodule.snapshot(base);lock_before={'sha256':sha(lock),'bytes':lock.stat().st_size}
 inputs=[TOOL,pathlib.Path(plan['protocol_path']),PLAN,APPROVAL,pathlib.Path(case['net']),R/'forge_sol_S26_bench_refs_20261026.json',R/'forge_sol_S26_allowlist_20261026.json',R/'forge_sol_S26_dependencies_20261026.json',pathlib.Path('/usr/bin/c++').resolve()]
 input_before={str(p):sha(p) for p in inputs}
 env=dict(os.environ,PYTHONPATH='/workspace/.cloud-setup/venv/lib/python3.12/site-packages',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',CMAKE_BUILD_PARALLEL_LEVEL='1',TMPDIR=str(outside),TMP=str(outside),TEMP=str(outside))
 relevant={k:env[k] for k in ['PATH','PYTHONPATH','PYTHONDONTWRITEBYTECODE','OMP_NUM_THREADS','CMAKE_BUILD_PARALLEL_LEVEL','TMPDIR','TMP','TEMP','CXX','CC','CXXFLAGS','CPPFLAGS','LDFLAGS','MAKEFLAGS'] if k in env}
 write(outside/'invocation.json',{'utc':now(),'driver_sha256':sha(__file__),'helper_source_sha256':sha(HELPER),'argv':netplan['argv'],'cwd':'/','environment':relevant,'case':case,'input_sha256_before':input_before,'source_before':source_before,'lock_before':lock_before,'free_bytes_before':H.free(),'RAM_available_before':H.mem()})
 p=None;seen={};started=time.monotonic();stop_reason=None;limits={'min_free_bytes':H.free(),'min_RAM_available':H.mem()}
 try:
  with (outside/'tool.stdout').open('wb') as so,(outside/'tool.stderr').open('wb') as se,(outside/'resources.jsonl').open('w') as resources:
   p=subprocess.Popen(netplan['argv'],cwd='/',env=env,stdout=so,stderr=se,start_new_session=True)
   write(outside/'launch.json',{'utc':now(),'pid':p.pid,'argv':netplan['argv'],'cwd':'/'})
   while p.poll() is None:
    owned=H.children(H.proc_table(),p.pid);disk=H.free();ram=H.mem();limits['min_free_bytes']=min(limits['min_free_bytes'],disk);limits['min_RAM_available']=min(limits['min_RAM_available'],ram)
    for item in owned:seen[(item['pid'],item['starttime_ticks'])]=item
    sample={'utc':now(),'case':case['id'],'elapsed_seconds':time.monotonic()-started,'free_bytes':disk,'RAM_available':ram,'owned_processes':owned}
    resources.write(json.dumps(sample)+'\n');resources.flush();write(outside/'progress.json',sample);write(MASTER/'progress.json',sample)
    if disk<plan['active_disk_stop_floor_bytes']:stop_reason='DISK_FLOOR8MiB'
    if ram<plan['RAM_floor']:stop_reason='RAM_FLOOR3GiB'
    if stop_reason:p.send_signal(signal.SIGTERM);p.wait(timeout=15);break
    time.sleep(2)
   p.wait()
 except BaseException as exc:
  stop_reason=stop_reason or (type(exc).__name__+': '+str(exc))
  if p is not None and p.poll() is None:
   p.send_signal(signal.SIGTERM)
   try:p.wait(timeout=15)
   except subprocess.TimeoutExpired:stop_reason+='; CLI still alive afterSIGTERM, ownedpid='+str(p.pid)
 record=evaluate(plan,netplan,outside,p,source_before,input_before,lock_before,seen,limits,stop_reason,toolmodule,decl);record['elapsed_seconds']=time.monotonic()-started;write(outside/'result.json',record);record['outside_manifest']=seal(outside)
 return record

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--resume',action='store_true');args=ap.parse_args()
 pre=read(PLAN);approval=read(APPROVAL);protocol=read(pre['protocol'])
 if approval['state']!='ROOT_CACHE_CLOSED_READY' or approval['protocol_sha256']!=pre['protocol_sha256']:raise RuntimeError('explicit matching ROOT CACHE_CLOSED receipt required')
 if sha(pre['protocol'])!=pre['protocol_sha256'] or sha(TOOL)!=pre['source_tool_sha256']:raise RuntimeError('frozen protocol/tool changed')
 decl=read(R/'forge_sol_S26_dependencies_20261026.json')
 for d in decl.values():
  if sha(d['path'])!=d['sha256']:raise RuntimeError('dependency changed')
 toolmodule=module(TOOL,'frozen275b_candidate_tool',pre['source_tool_sha256'])
 plan=dict(protocol,protocol_path=pre['protocol'],active_disk_stop_floor_bytes=pre['active_disk_stop_floor_bytes'],minimum_free_before_each_net_bytes=pre['minimum_free_before_each_net_bytes'])
 if MASTER.exists():
  if not args.resume:raise RuntimeError('NEW batch master required or explicit --resume of disk-paused unstarted cases')
  state=read(MASTER/'result.json')
  if state['status']!='PAUSED_BEFORE_NEXT_NET' or state['driver_sha256']!=sha(__file__) or state['plan_sha256']!=sha(PLAN):raise RuntimeError('only identical disk-paused batch canresume unstarted cases')
 else:
  if args.resume:raise RuntimeError('cannot resume nonexistentbatch')
  MASTER.mkdir();state={'started_utc':now(),'status':'RUNNING','driver_sha256':sha(__file__),'helper_source_sha256':sha(HELPER),'plan_sha256':sha(PLAN),'protocol_sha256':pre['protocol_sha256'],'cache_closed_receipt_sha256':sha(APPROVAL),'source_tool_sha256':sha(TOOL),'cases':[],'scope':'Prespecifiedf019-f023oneattempt/net; no adoptedengine/pin/referencechanges. Rootonlyreview/accept/publish.'}
  write(MASTER/'plan_snapshot.json',pre)
 done={x['id'] for x in state['cases']}
 for netplan in pre['cases']:
  case=netplan['case']
  if case['id'] in done:continue
  if H.free()<plan['minimum_free_before_each_net_bytes'] or H.mem()<plan['RAM_floor']:
   state.update(status='PAUSED_BEFORE_NEXT_NET',next_unstarted=case['id'],pause_utc=now(),free_bytes=H.free(),RAM_available=H.mem());write(MASTER/'result.json',state);seal(MASTER);print(json.dumps({'status':state['status'],'next_unstarted':case['id'],'free_bytes':state['free_bytes']}),flush=True);return 3
  if sha(case['net'])!=case['net_sha256']:raise RuntimeError('net identity changed before launch')
  active=[x for x in H.proc_table().values() if re.fullmatch(r'(?:forge.*|stockfish.*|fastchess.*|clang.*|gcc.*|g\+\+.*|cc1.*|lto.*|cmake|ctest|ninja|g?make)',x['comm'],re.I)]
  if active:raise RuntimeError('native preflight conflict before '+case['id']+': '+json.dumps(active))
  state.update(status='RUNNING',active_case=case['id']);write(MASTER/'result.json',state);print(json.dumps({'status':'STARTING_SINGLE_ATTEMPT','id':case['id'],'native_out':netplan['native_out'],'outside_out':netplan['outside_out'],'free_bytes':H.free()}),flush=True)
  record=run_one(plan,netplan,toolmodule,decl);state['cases'].append(record);done.add(case['id']);write(MASTER/'result.json',state)
  print(json.dumps({'status':record['status'],'id':case['id'],'WAC':record.get('WAC'),'CTest':record.get('CTest'),'engine_sha256':record.get('engine_sha256'),'unsafe_abort':record['unsafe_abort'],'free_bytes':H.free()}),flush=True)
  if record['unsafe_abort']:
   state.update(status='STOPPED_UNSAFE_PATH_NO_RETRY',active_case=None,finished_utc=now());write(MASTER/'result.json',state);seal(MASTER);return 1
 state.update(status='ALL_PRESPECIFIED_ATTEMPTS_COMPLETED_PENDING_ROOT_REVIEW',active_case=None,finished_utc=now(),free_bytes=H.free());write(MASTER/'result.json',state);seal(MASTER);print(json.dumps({'status':state['status'],'completed_ids':[x['id'] for x in state['cases']],'free_bytes':state['free_bytes']}),flush=True);return 0

if __name__=='__main__':raise SystemExit(main())
