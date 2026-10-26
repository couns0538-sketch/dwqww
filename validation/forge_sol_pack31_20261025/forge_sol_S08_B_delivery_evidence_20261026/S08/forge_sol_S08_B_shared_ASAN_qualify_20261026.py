"""Single bounded B shared-ASan/UBSan runtime gate; no speed/strength claim."""
import argparse, contextlib, importlib.util, json, os, re, signal, sys, time
from pathlib import Path
HERE=Path(__file__).resolve().parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
builder=load('s08_shared_builder',HERE/'forge_sol_S08_B_asan_shared_build_20261026.py')
bqual=load('s08_B_qualified',HERE/'forge_sol_S08_B_qualify_20261026.py')
shared=builder.shared
sha=shared.sha
BUILD=HERE/'forge_sol_S08_B_ASAN_SHARED_NODWARF_window1_20261026/build'
SOURCE=HERE/'B_v2'
BUILD_RECEIPT=BUILD.parent/'forge_sol_S08_B_shared_ASAN_build_result_20261026.json'
BUILD_RECEIPT_SHA='d97a6011f3a352ad15461f69bdffac413a9d749fc513c67e2898e05660ebb654'
FREEZE=HERE/'forge_sol_S08_B_v2_source_freeze_20261026.json'
FREEZE_SHA='fcd93778dc3bae5bed2f941c9ee0fff08f6ee07ce6ecf22bf82a007e8a8904d7'
FIRST=HERE/'forge_sol_S08_B_SHARED_FIRST_native_20261026/forge_sol_S08_B_shared_FIRST_result_20261026.json'
ENGINE_SHA='7bf208b9b860990685118219948227b9799a26e9d8905954eda9bf1c07f894c0'
CORE_SHA='26ad38fa04986a1e1e654be8d2138b702160d964aae62f158b06cc44640bd01b'
HELPER=HERE.parent/'S26/successor_ctest_v4/forge_sol_S26_netbatch_v4_20261026.py'
ALLOW=HERE.parent/'S26/forge_sol_S26_allowlist_20261026.json'
CTEST=shared.CMAKE.with_name('ctest')
def expected_environment():return {'ASAN_OPTIONS':'detect_leaks=1:halt_on_error=1','UBSAN_OPTIONS':'halt_on_error=1:print_stacktrace=1','LD_LIBRARY_PATH':str(BUILD)}
@contextlib.contextmanager
def runtime_environment():
    updates=dict(expected_environment(),PYTHONDONTWRITEBYTECODE='1');keys=[*updates,'LD_PRELOAD'];old={key:os.environ.get(key) for key in keys}
    try:
        os.environ.update(updates);os.environ.pop('LD_PRELOAD',None);yield expected_environment()
    finally:
        for key,value in old.items():
            if value is None:os.environ.pop(key,None)
            else:os.environ[key]=value
def verify_first(first,artifacts):
    for key,value in {'status':'PASS','returncode':0,'timeout':False,'bench_counts':[308972],'first_runtime_bare_bench':True,'no_UCI_before_bench':True,'source_and_14_artifacts_unchanged':True,'build_receipt_sha256':BUILD_RECEIPT_SHA,'source_freeze_sha256':FREEZE_SHA,'runtime_artifacts':artifacts,'environment':expected_environment(),'LD_PRELOAD_removed':True,'remaining_group':[]}.items():
        if first.get(key)!=value:raise ValueError('FIRST binding mismatch: '+key)
    if first.get('streams',{}).get('stderr')!={'bytes':0,'sha256':bqual.EMPTY_SHA}:raise ValueError('FIRST stderr mismatch')
    if set(artifacts)!=set(builder.RUNTIME_ARTIFACTS) or artifacts['forge']['sha256']!=ENGINE_SHA or artifacts[builder.CORE]['sha256']!=CORE_SHA:raise ValueError('FIRST exact14 artifact pins mismatch')
def verify_binding():
    if sha(BUILD_RECEIPT)!=BUILD_RECEIPT_SHA or sha(FREEZE)!=FREEZE_SHA:raise ValueError('build/freeze digest mismatch')
    info=json.loads(BUILD_RECEIPT.read_text());freeze=json.loads(FREEZE.read_text())
    for key,value in {'status':'PASS_BUILD_ONLY','profile':builder.PROFILE,'stage':'all','pending_targets':[],'source':str(SOURCE),'build_dir':str(BUILD),'source_unchanged':True,'source_freeze_sha256':FREEZE_SHA,'runtime_artifact_manifest_complete':True,'expected_full_CTest_count':16,'completed_targets':list(builder.TARGETS)}.items():
        if info.get(key)!=value:raise ValueError('build binding mismatch: '+key)
    if shared.snapshot(SOURCE)!=freeze['source_sha256'] or info['source_before']!=freeze['source_sha256'] or info['source_after']!=freeze['source_sha256']:raise ValueError('source hash mapping changed')
    if sha(shared.CXX)!=shared.CXX_SHA or info['compiler_sha256']!=shared.CXX_SHA:raise ValueError('compiler changed')
    recipe=builder.audit_recipe(SOURCE,BUILD,freeze)
    if recipe!=info['recipe_before'] or recipe!=info['recipe_after']:raise ValueError('compile/link recipe changed')
    artifacts=info['target_artifacts']
    if set(artifacts)!=set(builder.RUNTIME_ARTIFACTS) or set(info['dynamic_metadata'])!=set(artifacts):raise ValueError('all14 runtime inventory required')
    for name,row in artifacts.items():
        path=BUILD/name
        if path.is_symlink() or not path.is_file() or sha(path)!=row['sha256'] or path.stat().st_size!=row['bytes']:raise ValueError('runtime artifact changed: '+name)
        metadata=info['dynamic_metadata'][name]
        if metadata['sha256']!=row['sha256'] or metadata['path']!=str(path):raise ValueError('dynamic metadata artifact binding changed')
    for command in info['commands']:
        if command.get('error') or command.get('stop_reason') or command['returncode']!=0 or not command['leader_reaped'] or command['all_group_members_after_reap']:raise ValueError('build command not closed')
    verify_first(json.loads(FIRST.read_text()),artifacts)
    return {'source_sha256':freeze['source_sha256'],'runtime_artifacts':artifacts,'recipe':recipe,'first_receipt_sha256':sha(FIRST),'ctest_definition_sha256':sha(BUILD/'CTestTestfile.cmake')}
class Guard(bqual.Guard):
    def __init__(self,path,stop,deadline):super().__init__(path,stop,deadline-3);self.phase_deadline=None
    def reason(self,unused=None,deadline=None):
        reason=super().reason(unused,deadline)
        if reason:return reason
        if self.phase_deadline is not None and time.monotonic()>=self.phase_deadline:return 'EXTRA_DEADLINE'
        if sum(p.stat().st_size for p in self.path.rglob('*') if p.is_file())>2*1048576:return 'OUTPUT_CAP_2MIB'
class Process(bqual.Process):
    def __init__(self,*args):super().__init__(*args);self.timeout=min(self.timeout,120);self.max_bytes=1500000
    def close(self,successful):
        if self.closed:return
        try:super().close(successful)
        finally:
            if hasattr(self,'proc'):
                reaped,left=shared._reap_group(self.proc.pid,timeout=.1)
                if left:
                    more,left=shared._close_group(self.proc);reaped.extend(more)
                proof={'pid':self.proc.pid,'process_group':self.proc.pid,'returncode':self.proc.returncode,'leader_reaped':self.proc.returncode is not None,'reaped_descendants':reaped,'remaining_group':left}
                shared.save_new(self.out/(self.label+'.owned_group.json'),proof)
                if left or self.proc.returncode is None:raise RuntimeError('profile process group not reaped')
def expected_commands():
    result={name:[str(BUILD/name)] for name in builder.TARGETS if name not in ('forge','forge_bench')}
    result['forge_legal_witness_tests'] += [str(SOURCE/'tests/legal_witness_fixtures.tsv'),str(SOURCE/'tools/openings/forge-10000.epd')]
    # Exact configured spelling, not the controller's interchangeable symlink.
    python='/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3.12'
    result.update(match_tool_tests=[python,str(SOURCE/'tools/match/test_match_tools.py')],windows_validation_tests=[python,str(SOURCE/'tools/match/tests/test_windows_validate.py')],uci_regression=[python,str(SOURCE/'tools/uci_regression.py'),str(BUILD/'forge'),'--log',str(BUILD/'uci-regression.log')],ponder_regression=[python,str(SOURCE/'tools/ponder_regression.py'),str(BUILD/'forge')],ownbook_regression=[python,str(SOURCE/'tools/ownbook_regression.py'),str(BUILD/'forge'),str(BUILD/'ownbook-regression.json')])
    return result
def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute',action='store_true');parser.add_argument('--output',required=True,type=Path);parser.add_argument('--stop-file',required=True,type=Path);args=parser.parse_args(argv)
    if not args.execute or sorted(os.sched_getaffinity(0))!=[4] or os.getpriority(os.PRIO_PROCESS,0)!=19:parser.error('requires explicit execute CPU4 nice19')
    dependencies={HERE/'forge_sol_S08_B_asan_shared_build_20261026.py':'fb7ae112c4687372da8e686de3393c3bfce1ef831fed209437165f8c353943ee',HERE/'forge_sol_S08_collect_profiles_20261026.py':bqual.COLLECTOR_SHA,HERE/'forge_sol_S08_build_window_subreaper_20261026.py':'85acc70b0dd987d21e6ae93276f7183eb23806b35a92dc217c72da2018ab8fa0',HELPER:'4dbf73e63032d7512c6beff12fdca03b7d29e1489b6d0ae3cab26b09753ac36f',ALLOW:'14b5559f1158b98bc86fa571a8af9da87afd79ba1e395a9a06a7d5c5299814ef'}
    for path,digest in dependencies.items():
        if sha(path)!=digest:raise ValueError('dependency changed: '+str(path))
    dependencies.update({HERE/'forge_sol_S08_B_qualify_20261026.py':'69ea878aea1b6ad7f98ac3636606e69d60f8f4acab063f2eae9db083bde08d0f',bqual.FMA:'e7ba90e5c2bdb43c490d9c992a684f7f0d311d83c7639ad852f77a4dd079d07f',CTEST:'4757644d13a4460c2d46f591ff0693d7c66e73f01b92519850ef4b00cd21554e'})
    for path,digest in dependencies.items():
        if sha(path)!=digest:raise ValueError('dependency changed: '+str(path))
    helper=load('s08_ctest_inventory',HELPER);binding=verify_binding()
    if bqual.shutil.disk_usage(HERE).free<12*1048576:raise ValueError('requires12MiBfree before launch')
    out=bqual.collector.exclusive_directory(args.output);started=time.monotonic();guard=Guard(out,args.stop_file,started+600)
    result={'status':'RUNNING','profile':builder.PROFILE,'no_speed_or_strength_claim':True,'binding_before':binding,'controller_sha256':sha(__file__),'dependencies':{str(p):d for p,d in dependencies.items()},'max_total_seconds':600,'extra_phase_seconds':120,'start_floor_bytes':12*1048576,'active_floor_bytes':8*1048576,'cpu':[4],'nice':19,'commands':[],'steps':[]}
    receipt=out/'forge_sol_S08_B_shared_ASAN_qualification_result_20261026.json'
    def save():receipt.write_text(json.dumps(result,indent=2)+'\n')
    def run(command,label):
        row=shared.run_owned(command,out,label,out,guard.deadline);result['commands'].append(row);save()
        if row.get('error') or row.get('stop_reason') or row['returncode']!=0 or not row['leader_reaped'] or row['all_group_members_after_reap']:raise ValueError('owned command failed: '+label)
        if row['captures']['stderr']['bytes']:raise ValueError('unexpected command stderr: '+label)
        return row
    old=shared.boundary_reason;shared.boundary_reason=guard.reason;signals={s:signal.getsignal(s) for s in (signal.SIGTERM,signal.SIGINT)}
    for s in signals:signal.signal(s,shared._signal_stop)
    process=None;scope=shared.SubreaperScope();scope.__enter__();save()
    try:
        with runtime_environment() as env:
            result['environment']=env;save();guard.check()
            run([str(CTEST),'--test-dir',str(BUILD),'--show-only=json-v1'],'discovery')
            inventory=helper.load_ctest_inventory(out/'discovery.stdout',SOURCE,BUILD)
            if len(inventory['expected_names'])!=16 or inventory['commands']!=expected_commands():raise ValueError('exact16 test command argv inventory mismatch')
            result['inventory']=inventory;save()
            junit=out/'forge_sol_S08_B_shared_ASAN_full16_20261026.xml'
            command=run([str(CTEST),'--test-dir',str(BUILD),'--output-on-failure','-V','-j1','--no-tests=error','--output-junit',str(junit)],'full16_CTest')
            result['source_known_cases']=bqual.verify_ctest((out/'full16_CTest.stdout').read_text(),command['returncode'])
            allow=helper.bind_allowlist(json.loads(ALLOW.read_text()),sha(SOURCE/'tests/tests.cpp'),sha(SOURCE/'src/nnue_weights.inc'))
            result['ctest_proof']=helper.check_ctest(junit,command['returncode'],allow,inventory['expected_names'])
            if any(row['failed'] for row in result['ctest_proof']['test_cases']):raise ValueError('failed CTest case')
            save();guard.phase_deadline=min(guard.deadline,time.monotonic()+120)
            process=Process(BUILD/'forge',out,'profile_on_extra',guard)
            def until(predicate):return process.until(predicate)
            def fence():
                process.send('isready')
                if until(lambda line:line=='readyok')!=['readyok']:raise ValueError('late output at ready fence')
            process.send('uci');uci=until(lambda line:line=='uciok')
            if 'option name Profile type check default false' not in uci:raise ValueError('missing typed profile option')
            for name,value in [('Hash','16'),('Threads','1'),('OwnBook','false'),('Profile','true')]:process.send('setoption name '+name+' value '+value)
            fence();process.send('bench_prof 11');lines=until(lambda line:bool(bqual.collector.BENCH.fullmatch(line)))
            match=bqual.collector.BENCH.fullmatch(lines[-1])
            if [int(match[1]),int(match[2])]!=[11,308972]:raise ValueError('profiled bare11 reference mismatch')
            packet=bqual.collector.parse_packet(lines,terminal='bench');bqual.collector.verify_profile_work(packet,expected_nodes=308972);fence()
            if packet['overflow']:raise ValueError('profile overflow')
            result['steps'].append({'name':'bench_prof11','packet':packet});save()
            for threads in (1,2):
                for command in ['setoption name Threads value '+str(threads),'ucinewgame','setoption name Clear Hash','position startpos','go nodes 10000']:process.send(command)
                lines=until(lambda line:bool(bqual.collector.MOVE.fullmatch(line)));verified=bqual.verify_search(lines,True)
                if threads==1:bqual.collector.verify_profile_work(verified['profile'],node_limit=10000)
                result['steps'].append({'name':'profile_T'+str(threads),'parallel_node_ceiling_asserted':threads==1,**verified});fence();save()
            for name,position,expected in [('startpos','startpos',197281),('kiwipete','fen '+bqual.KIWI,4085603)]:
                process.send('position '+position);process.send('go perft 4');lines=until(lambda line:bool(re.fullmatch(r'nodes \d+',line)))
                divides=[re.fullmatch(r'[a-h][1-8][a-h][1-8][nbrq]?: (\d+)',line) for line in lines[:-1]]
                if lines[-1]!='nodes '+str(expected) or any(match is None for match in divides) or sum(int(match[1]) for match in divides)!=expected:raise ValueError('perft4 divide/total mismatch')
                result['steps'].append({'name':'perft4_'+name,'nodes':expected});fence();save()
            process.close(True);process=None
            for name,path in [('FMA_NNUE_object',BUILD/'CMakeFiles/forge_core.dir/src/nnue.cpp.o'),('FMA_NNUE_scope_coreSO',BUILD/builder.CORE)]:
                run([sys.executable,'-B',str(bqual.FMA),str(path)],name);result['steps'].append({'name':name,'proof':json.loads((out/(name+'.stdout')).read_text())});save()
            run([str(CTEST),'--test-dir',str(BUILD),'--show-only=json-v1'],'discovery_after')
            after=helper.load_ctest_inventory(out/'discovery_after.stdout',SOURCE,BUILD)
            if after['commands']!=inventory['commands'] or after['binding']!=inventory['binding']:raise ValueError('CTest definitions/commands changed during runtime')
            result['binding_after']=verify_binding()
            if result['binding_after']!=binding:raise ValueError('full source/runtime binding changed')
            if any(sha(path)!=digest for path,digest in dependencies.items()):raise ValueError('dependency changed during runtime')
            result['status']='PASS'
    except BaseException as exc:result.update(status='FAIL',failure=type(exc).__name__+': '+str(exc))
    finally:
        if process is not None:
            try:process.close(False)
            except BaseException as exc:result['cleanup_failure']=type(exc).__name__+': '+str(exc)
        scope.__exit__(None,None,None)
        shared.boundary_reason=old
        for s,handler in signals.items():signal.signal(s,handler)
        result.update(elapsed_seconds=time.monotonic()-started,minimum_observed_free_bytes=guard.minimum);save()
    print(json.dumps({'status':result['status'],'failure':result.get('failure'),'output':str(out)}),flush=True)
    return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
