#!/usr/bin/env python3
"""Complete frozen-v2 ASan/UBSan CTest gate with owned descendant containment."""
import argparse, contextlib, datetime, hashlib, importlib.util, json, os, pathlib, shutil, signal, time

HERE=pathlib.Path(__file__).resolve().parent
BUILD=HERE/'forge_sol_S08_ASAN_v2_window1_20261026/build'
SOURCE=HERE/'Lprime_v2'
CTEST=pathlib.Path('/workspace/.cloud-setup/venv/lib/python3.12/site-packages/cmake/data/bin/ctest')
FREEZE=HERE/'forge_sol_S08_TLS_v2_source_freeze_20261026.json'
FREEZE_SHA='2923e86c186e357aac177e453f5745993d0839af02422d2622ff9f80dffae5ad'
SHARED=HERE/'forge_sol_S08_build_window_subreaper_20261026.py'
SHARED_SHA='85acc70b0dd987d21e6ae93276f7183eb23806b35a92dc217c72da2018ab8fa0'
ADAPTER=HERE/'forge_sol_S08_sanitizer_build_20261026.py'
ADAPTER_SHA='e07f60715d0fb3eff4fbbcde6c2b674ecff049167dfb9bf901b622607b036fc5'
HELPER=HERE.parent/'S26/successor_ctest_v4/forge_sol_S26_netbatch_v4_20261026.py'
HELPER_SHA='4dbf73e63032d7512c6beff12fdca03b7d29e1489b6d0ae3cab26b09753ac36f'
ALLOW=HERE.parent/'S26/forge_sol_S26_allowlist_20261026.json'
ALLOW_SHA='14b5559f1158b98bc86fa571a8af9da87afd79ba1e395a9a06a7d5c5299814ef'
FLOOR=20*1048576

def sha(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def load(path,name,expected):
    if sha(path)!=expected:raise ValueError('dependency SHA256 mismatch: '+str(path))
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def verify_binding(receipt,first,freeze,source,build,shared,adapter,freeze_sha):
    """Reject changes to ANY frozen source/ELF or sanitizer compile/link recipe."""
    source,build=pathlib.Path(source),pathlib.Path(build)
    targets=list(shared.TARGETS)
    required={'status':'PASS_BUILD_ONLY','profile':'RelWithDebInfo_ASAN_UBSAN_PROF_H256',
              'source':str(source),'build_dir':str(build),'source_freeze_sha256':freeze_sha,
              'source_unchanged':True,'expected_full_CTest_count':15,'stage':'all',
              'shared_controller_sha256':SHARED_SHA,'adapter_sha256':ADAPTER_SHA}
    for key,value in required.items():
        if receipt.get(key)!=value:raise ValueError('closed build binding mismatch: '+key)
    if receipt.get('pending_targets')!=[] or receipt.get('completed_targets')!=targets or receipt.get('all_targets_order')!=targets:
        raise ValueError('complete exact target inventory required')
    if freeze.get('source')!=str(source) or receipt.get('source_before')!=freeze.get('source_sha256'):
        raise ValueError('source freeze/receipt mapping mismatch')
    if shared.snapshot(source)!=freeze['source_sha256']:raise ValueError('frozen source changed')
    if receipt.get('compiler_sha256')!=shared.CXX_SHA or sha(shared.CXX)!=shared.CXX_SHA:
        raise ValueError('frozen compiler changed')
    artifacts=receipt.get('target_artifacts',{})
    if set(artifacts)!=set(targets):raise ValueError('artifact inventory differs from all targets')
    for name in targets:
        p=build/name;record=artifacts[name]
        if p.is_symlink() or not p.is_file():raise ValueError('artifact absent/symlink: '+name)
        if record.get('sha256')!=sha(p) or record.get('bytes')!=p.stat().st_size:
            raise ValueError('frozen target artifact changed: '+name)
        with p.open('rb') as stream:
            if stream.read(4)!=b'\x7fELF':raise ValueError('artifact is not ELF: '+name)
    rows=[row for row in first.get('results',[]) if row.get('label')=='ASAN']
    if len(rows)!=1:raise ValueError('exactly one original ASAN first-runtime row required')
    row=rows[0]
    if not (row.get('pass') is True and row.get('bench_counts')==[308972] and row.get('returncode')==0
            and not row.get('timeout') and row.get('first_runtime_bare_bench') is True
            and row.get('no_uci_before_bench') is True
            and row.get('binary_sha256_before')==row.get('binary_sha256_after')==artifacts['forge']['sha256']):
        raise ValueError('ASAN first-runtime binding failed')
    expected={name for name in freeze['source_sha256'] if name.endswith('.cpp') and
              (name.startswith(('src/','tests/')) or name=='bench/benchmark.cpp')}
    recipe=adapter.audit_recipe(source,build,expected)
    if receipt.get('recipe_before')!=recipe or receipt.get('recipe_after')!=recipe:
        raise ValueError('compile/link recipe changed since completed build')
    for command in receipt.get('commands',[]):
        if command.get('error') or command.get('stop_reason') or command.get('returncode')!=0:
            raise ValueError('completed build includes failed command')
        if command.get('leader_reaped') is not True or command.get('all_group_members_after_reap')!=[]:
            raise ValueError('completed build process group not closed')
    return {'status':'PASS_FROZEN_SOURCE_ALL_TARGETS_RECIPE','targets':targets,
            'source_file_count':len(freeze['source_sha256']),'recipe':recipe,
            'target_sha256':{name:artifacts[name]['sha256'] for name in targets}}

class Guard:
    def __init__(self,path,shared,stop):self.path,self.shared,self.stop=path,shared,stop
    def check(self,unused,deadline):
        if self.shared._STOP_REQUESTED:return 'EXTERNAL_STOP'
        if self.stop.exists():return 'ROOT_STOP_FILE'
        if time.monotonic()>=deadline:return 'OWNED_DEADLINE'
        if shutil.disk_usage(self.path).free<FLOOR:return 'DISK_FREE_BELOW_20MIB'
        return None

@contextlib.contextmanager
def sanitizer_environment():
    updates={'ASAN_OPTIONS':'detect_leaks=1:halt_on_error=1','UBSAN_OPTIONS':'halt_on_error=1:print_stacktrace=1','PYTHONDONTWRITEBYTECODE':'1'}
    previous={k:os.environ.get(k) for k in updates}
    try:os.environ.update(updates);yield dict(updates)
    finally:
        for key,value in previous.items():
            if value is None:os.environ.pop(key,None)
            else:os.environ[key]=value

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--execute',action='store_true');ap.add_argument('--closed-build-receipt',required=True,type=pathlib.Path)
    ap.add_argument('--output',required=True,type=pathlib.Path);ap.add_argument('--stop-file',required=True,type=pathlib.Path)
    args=ap.parse_args(argv)
    if not args.execute:ap.error('execution must be explicit')
    if sorted(os.sched_getaffinity(0))!=[4] or os.getpriority(os.PRIO_PROCESS,0)!=19:ap.error('use taskset -c4 nice -n19')
    if sha(FREEZE)!=FREEZE_SHA:raise ValueError('source freeze SHA256 mismatch')
    shared=load(SHARED,'s08_asan_owned',SHARED_SHA)
    adapter=load(ADAPTER,'s08_asan_recipe',ADAPTER_SHA)
    helper=load(HELPER,'s08_complete_ctest',HELPER_SHA)
    if sha(ALLOW)!=ALLOW_SHA:raise ValueError('known-failure allowlist SHA256 mismatch')
    ctest_sha=sha(CTEST)
    build_receipt=json.loads(args.closed_build_receipt.read_text());freeze=json.loads(FREEZE.read_text())
    first_path=HERE/'forge_sol_S08_TLS_v2_FIRST_native_20261026/forge_sol_S08_TLS_v2_first_runtime_result_20261026.json'
    first=json.loads(first_path.read_text())
    binding=verify_binding(build_receipt,first,freeze,SOURCE,BUILD,shared,adapter,FREEZE_SHA)
    if shutil.disk_usage(HERE).free<FLOOR:raise ValueError('requires20MiBfree')
    output=shared.new_directory(args.output)
    path=output/'forge_sol_S08_ASAN_full_qualification_v2_result_20261026.json'
    receipt={'status':'RUNNING','source':str(SOURCE),'build':str(BUILD),'no_speed_claim':True,
      'first_runtime_receipt_sha256':sha(first_path),'closed_build_receipt_sha256':sha(args.closed_build_receipt),
      'source_freeze_sha256':FREEZE_SHA,'helper_sha256':HELPER_SHA,'shared_sha256':SHARED_SHA,
      'adapter_sha256':ADAPTER_SHA,'binding_before':binding,'commands':[],
      'allowlist_sha256':ALLOW_SHA,'ctest_sha256_before':ctest_sha,
      'legacy_shared_engine_executions_field':'shared build-controller receipts contain engine_executions=0; this legacy field is NOT applicable to native CTest. Actual engine invocation count is not measured here.'}
    def save():path.write_text(json.dumps(receipt,indent=2)+'\n')
    previous_guard=shared.boundary_reason
    guard=Guard(output,shared,args.stop_file);shared.boundary_reason=guard.check
    old_signals={s:signal.getsignal(s) for s in (signal.SIGTERM,signal.SIGINT)}
    for s in old_signals:signal.signal(s,shared._signal_stop)
    def run(command,label,timeout):
        row=shared.run_owned(command,output,label,output,time.monotonic()+timeout)
        receipt['commands'].append(row);save()
        if row.get('error') or row.get('stop_reason') or row['returncode']!=0:
            raise ValueError('command failed: '+label)
        if not row['leader_reaped'] or row['all_group_members_after_reap']:
            raise ValueError('owned descendants not closed: '+label)
        return row
    save()
    try:
        with sanitizer_environment() as env:
            receipt['sanitizer_environment']=env;save()
            run([str(CTEST),'--test-dir',str(BUILD),'--show-only=json-v1'],'discovery',60)
            if (output/'discovery.stderr').read_bytes():raise ValueError('CTest discovery stderr')
            inventory=helper.load_ctest_inventory(output/'discovery.stdout',SOURCE,BUILD)
            if len(inventory['expected_names'])!=15:raise ValueError('expected15configuredtests')
            receipt['inventory']=inventory;save()
            junit=output/'forge_sol_S08_ASAN_full_ctest_v2_20261026.xml'
            c=run([str(CTEST),'--test-dir',str(BUILD),'--output-on-failure','--no-tests=error','--parallel','1','--output-junit',str(junit)],'ctest',1800)
            allow=helper.bind_allowlist(json.loads(ALLOW.read_text()),sha(SOURCE/'tests/tests.cpp'),sha(SOURCE/'src/nnue_weights.inc'))
            receipt['ctest_proof']=helper.check_ctest(junit,c['returncode'],allow,inventory['expected_names'])
            if (output/'ctest.stderr').read_bytes():raise ValueError('CTeststderr')
            if any(r['failed'] for r in receipt['ctest_proof']['test_cases']):raise ValueError('failedCTestcase')
            receipt['binding_after']=verify_binding(build_receipt,first,freeze,SOURCE,BUILD,shared,adapter,FREEZE_SHA)
            if sha(ALLOW)!=ALLOW_SHA or sha(CTEST)!=ctest_sha:raise ValueError('allowlist/CTest changed during qualification')
            receipt['ctest_sha256_after']=sha(CTEST)
            receipt['status']='PASS'
    except Exception as exc:receipt.update(status='FAIL',failure=type(exc).__name__+': '+str(exc))
    finally:
        shared.boundary_reason=previous_guard
        for s,h in old_signals.items():signal.signal(s,h)
        receipt['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save()
    print(json.dumps({'status':receipt['status'],'output':str(output)}),flush=True)
    return 0 if receipt['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
