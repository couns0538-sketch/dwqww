"""S11 FIRST/Std adapter over actually qualified S09 native transport/checks.

Source-only preparation until S10 publication and a fresh execution grant.
No benchmark timings from these correctness runs are speed evidence.
"""
from pathlib import Path
import argparse,importlib.util,json,os,re,resource,shutil,signal,sys,time

HERE=Path(__file__).resolve().parent
RUNTIME=Path('/workspace/forge-pack24-20261026/S09_ASAN_PREP_20261026/forge_sol_S09_qualify_ASAN_20261026.py')
RUNTIME_SHA='162da3119d09a63e1152ca855dfe14940e91225feaa1f9bc420f59061d914b39'

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

build_api=load('s11_build_api',HERE/'forge_sol_S11_build_native_20261026.py')
previous=load('s11_owned_std_transport',RUNTIME)
q=previous.q
shared=q.shared
TMP=build_api.TMP

def verify_build(path):
    data=json.loads(path.read_text())
    if data.get('schema')!='forge.S11.build.v1' or data.get('status')!='PASS_BUILD_ONLY' or data.get('source_unchanged') is not True:
        raise ValueError('closed complete S11 build required')
    if data.get('profile') not in ('Release','ASAN'):raise ValueError('unknown build profile')
    source,expected=build_api.selected_source(data.get('base'),data.get('role'));build=path.parent/'build'
    if data.get('source')!=str(source) or data.get('source_before')!=expected or data.get('source_after')!=expected:
        raise ValueError('actual build source/role differs from frozen S11 arm')
    if not build_api.permitted(build):raise ValueError('build outside new S11 native root')
    if data.get('environment',{}).get('PYTHONDONTWRITEBYTECODE')!='1':raise ValueError('bytecode-off build required')
    if not re.fullmatch('[0-9a-f]{40}',data.get('S10_published_commit','')):raise ValueError('S10 publication reference absent')
    commands=data.get('commands',[])
    if not commands or any(type(c.get('returncode')) is not int or c['returncode']!=0 or c.get('leader_reaped') is not True or c.get('all_group_members_after_reap')!=[] or c.get('stop_reason') or c.get('error') for c in commands):
        raise ValueError('build contains failed/unclosed commands')
    artifacts=data.get('target_artifacts',{})
    if set(artifacts)!=set(build_api.artifact_names(source,data['profile'])):raise ValueError('incomplete/extra artifact inventory')
    for name,item in artifacts.items():
        actual=build/('libforge_core.a' if name=='core_archive' else name)
        if item.get('path')!=str(actual) or item.get('sha256')!=shared.sha(actual) or item.get('bytes')!=actual.stat().st_size:
            raise ValueError('runtime artifact changed: '+name)
    profile_api=build_api.load('s11_recipe_auditor',build_api.PROFILE_SOURCES[data['profile']])
    if profile_api.audit_recipe(source,build)!=data.get('recipe_after'):raise ValueError('generated compiler recipe changed')
    if data['profile']=='Release':
        checker=build_api.load('s11_oracle_binding',HERE/'forge_sol_S11_scalar_parity_20261026.py')
        checker.verify_oracle_compilation(data,data['role'])
        oracle=data['material_oracle_compilation'];map_path=Path(oracle['map_path'])
        if shared.sha(map_path)!=oracle['map_sha256']:raise ValueError('link map changed')
        checker.verify_link_map(map_path.read_text(),build/'libforge_core.a')
    return data,source,build

def verify_first(first,build_digest,engine_digest,profile):
    if (first.get('schema')!='forge.S11.first_runtime.v1' or first.get('status')!='PASS'
        or first.get('profile')!=profile or first.get('build_receipt_sha256')!=build_digest
        or first.get('engine_sha256')!=engine_digest or first.get('commands_sent')!=['bench 11','quit']
        or first.get('no_UCI_before_bench') is not True or first.get('bench_nodes')!=308972
        or type(first.get('returncode')) is not int or first['returncode']!=0
        or first.get('source_unchanged') is not True or first.get('all_artifacts_unchanged') is not True
        or first.get('all_engine_groups_closed') is not True):
        raise ValueError('original S11 FIRST bare11/order/source/artifact receipt differs')

def main(argv=None):
    os.environ['PYTHONDONTWRITEBYTECODE']='1';sys.dont_write_bytecode=True
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute',action='store_true');p.add_argument('--authorization-reference',required=True)
    p.add_argument('--mode',choices=('FIRST','FULL'),required=True);p.add_argument('--build-receipt',type=Path,required=True)
    p.add_argument('--first-runtime-receipt',type=Path);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--max-seconds',type=float,default=600);a=p.parse_args(argv)
    if not a.execute or not 10<=a.max_seconds<=600:p.error('fresh bounded native execution grant required')
    if len(os.sched_getaffinity(0))!=1 or os.getpriority(os.PRIO_PROCESS,0)!=19:p.error('single granted CPU/nice19 required')
    if not build_api.permitted(a.out) or a.out.exists():p.error('new literal S11 output descendant required')
    if shared.sha(RUNTIME)!=RUNTIME_SHA:p.error('qualified transport changed')
    data,source,build=verify_build(a.build_receipt);asan=data['profile']=='ASAN'
    if asan:
        if resource.getrlimit(resource.RLIMIT_AS)[0]!=resource.RLIM_INFINITY:p.error('ASAN shadow requires unlimited AS; use owned RSS guard')
        os.environ['ASAN_OPTIONS']='detect_leaks=1:halt_on_error=1';os.environ['UBSAN_OPTIONS']='halt_on_error=1:print_stacktrace=1'
    for key in ('LSAN_OPTIONS','LD_PRELOAD','LD_LIBRARY_PATH'):os.environ.pop(key,None)
    if shutil.disk_usage(TMP).free<64*1048576:p.error('64MiB temporary native start floor')
    engine=build/'forge';engine_digest=shared.sha(engine);build_digest=shared.sha(a.build_receipt)
    if a.mode=='FULL':
        if a.first_runtime_receipt is None:p.error('FULL requires the original FIRST receipt')
        first=json.loads(a.first_runtime_receipt.read_text());verify_first(first,build_digest,engine_digest,data['profile'])
        previous.verify_first_files(a.first_runtime_receipt,first)
    elif a.first_runtime_receipt is not None:p.error('FIRST cannot consume previous runtime evidence')
    a.out.mkdir();start=time.monotonic();guard=previous.RSSGuard(a.out,a.out/'ROOT_STOP',start+a.max_seconds)
    result={'schema':'forge.S11.first_runtime.v1' if a.mode=='FIRST' else 'forge.S11.full_runtime.v1','status':'FAIL',
        'mode':a.mode,'base':data['base'],'role':data['role'],'profile':data['profile'],'source':str(source),
        'source_before':build_api.sources.inventory(source),'build_receipt_sha256':build_digest,'engine_sha256':engine_digest,
        'artifact_inventory':data['target_artifacts'],'controller_sha256':shared.sha(__file__),'qualified_transport_sha256':RUNTIME_SHA,
        'authorization_reference':a.authorization_reference,'S10_published_commit':data['S10_published_commit'],
        'cpu':sorted(os.sched_getaffinity(0)),'nice':19,'max_seconds':a.max_seconds,'steps':[],'nps_used':False,
        'runtime_environment':{k:os.environ.get(k) for k in ('ASAN_OPTIONS','UBSAN_OPTIONS','LSAN_OPTIONS')},
        'ASAN_address_space_limit':resource.getrlimit(resource.RLIMIT_AS)[0] if asan else 'not an ASAN runtime'}
    old=shared.boundary_reason;shared.boundary_reason=guard.reason
    def step(name,value):
        result['steps'].append({'name':name,'result':value});shared.save_new(a.out/(f'{len(result["steps"]):02d}_'+name+'.json'),value)
        print(json.dumps({'stage':name,'status':'PASS'}),flush=True)
    def command(args,label):
        r=shared.run_owned(args,a.out,label,a.out,guard.deadline)
        if r.get('error') or r.get('stop_reason') or r.get('returncode')!=0 or r.get('all_group_members_after_reap'):raise RuntimeError('owned command failed/open: '+label)
        return r
    try:
        if a.mode=='FIRST':
            q.engine_once(engine,a.out,'FIRST_bare11',['bench 11'],lambda x:bool(q.collector.BENCH.fullmatch(x)),guard)
            check=q.s25.inspect_bench((a.out/'FIRST_bare11.stdout').read_bytes(),(a.out/'FIRST_bare11.stderr').read_bytes(),0)
            if check['status']!='PASS':raise ValueError('FIRST fixed-node/EOF contract failed')
            result.update(commands_sent=['bench 11','quit'],no_UCI_before_bench=True,bench_nodes=308972,returncode=0)
            result['first_captures']={n:shared.sha(a.out/n) for n in ('FIRST_bare11.stdin','FIRST_bare11.stdout','FIRST_bare11.stderr','FIRST_bare11.receipt.json')}
            step('FIRST_bare11',check)
        else:
            for depth,nodes in ([(11,308972)] if asan else list(q.REFS.items())):
                label='bench_'+str(depth);q.engine_once(engine,a.out,label,[f'bench {depth}'],lambda x:bool(q.collector.BENCH.fullmatch(x)),guard)
                check=q.s25.inspect_bench((a.out/(label+'.stdout')).read_bytes(),(a.out/(label+'.stderr')).read_bytes(),0,depth,nodes)
                if check['status']!='PASS':raise ValueError('reference bench/EOF mismatch: '+str(depth))
                step(label,check)
            depth=4 if asan else 5
            for name,position,nodes in [('startpos','startpos',197281 if asan else 4865609),('kiwipete','fen '+q.KIWI,4085603 if asan else 193690690)]:
                label=f'perft{depth}_'+name;lines=q.engine_once(engine,a.out,label,['position '+position,f'go perft {depth}'],lambda x:bool(re.fullmatch(r'nodes \d+',x)),guard)
                if lines[-1]!='nodes '+str(nodes):raise ValueError('fixed perft mismatch')
                step(label,{'depth':depth,'nodes':nodes})
            step('UCI_T1_T2',previous.lifecycle(engine,a.out,guard))
            ctest=shared.CMAKE.with_name('ctest');command([str(ctest),'--test-dir',str(build),'--show-only=json-v1'],'CTest_inventory_before')
            inventory=json.loads((a.out/'CTest_inventory_before.stdout').read_text());tests=inventory['tests'];names=[x['name'] for x in tests]
            expected=re.findall(r'add_test\(NAME\s+(\w+)',(source/'CMakeLists.txt').read_text())
            if sorted(names)!=sorted(expected) or len(names)!=len(set(names)):raise ValueError('configured CTest not full source inventory')
            for test in tests:
                if test['name'].startswith('forge_') and Path(test['command'][0])!=build/test['name']:raise ValueError('CTest primary outside frozen build')
            step('CTest_inventory',{'names':names,'count':len(names)})
            r=command([str(ctest),'--test-dir',str(build),'--output-on-failure','-V','-j1','--output-junit',str(a.out/'full_ctest.xml')],'full_CTest')
            step('full_CTest',previous.verify_ctest((a.out/'full_CTest.stdout').read_text(),r['returncode'],names,a.out/'full_ctest.xml'))
            command([str(ctest),'--test-dir',str(build),'--show-only=json-v1'],'CTest_inventory_after')
            if json.loads((a.out/'CTest_inventory_after.stdout').read_text())!=inventory:raise ValueError('CTest definitions changed')
            for label,path in [('FMA_NNUE_object',build/'CMakeFiles/forge_core.dir/src/nnue.cpp.o'),('FMA_NNUE_scope_ELF',engine)]:
                command([sys.executable,'-B',str(q.FMA),str(path)],label);value=json.loads((a.out/(label+'.stdout')).read_text());previous.verify_fma(value);step(label,value)
            command(['objdump','-d','--no-show-raw-insn',str(engine)],'whole_ELF_assembly')
            if any(re.match(r'^\s*[0-9a-fA-F]+:\s+vf(?:n)?m(?:add|sub)[a-z0-9]*\b',x) for x in (a.out/'whole_ELF_assembly.stdout').read_text().splitlines()):raise ValueError('whole ELF FMA nonzero')
            step('FMA_whole_ELF',{'fma_count':0,'assembly_sha256':shared.sha(a.out/'whole_ELF_assembly.stdout')})
        result['status']='PASS'
    except BaseException as error:result['error']=type(error).__name__+': '+str(error)
    finally:
        shared.boundary_reason=old;result['source_after']=build_api.sources.inventory(source)
        result['source_unchanged']=result['source_before']==result['source_after']
        try:
            after,_,_=verify_build(a.build_receipt)
            result['all_artifacts_unchanged']=after['target_artifacts']==data['target_artifacts'] and shared.sha(a.build_receipt)==build_digest
        except Exception as error:result['all_artifacts_unchanged']=False;result['postflight_error']=str(error)
        ownership=[json.loads(p.read_text()) for p in sorted(a.out.glob('*.ownership.json'))]
        result['engine_process_ownership']=ownership
        result['all_engine_groups_closed']=bool(ownership) and all(x['leader_reaped'] and not x['all_group_members_after_reap'] and not x.get('cleanup_error') for x in ownership)
        result['maximum_observed_owned_RSS_bytes']=guard.maximum_owned_RSS_bytes
        if not result['source_unchanged'] or not result['all_artifacts_unchanged'] or not result['all_engine_groups_closed']:result['status']='FAIL'
        result['elapsed_seconds']=time.monotonic()-start;shared.save_new(a.out/'forge_sol_S11_runtime_result_20261026.json',result)
    print(json.dumps({'status':result['status'],'error':result.get('error')}));return 0 if result['status']=='PASS' else 1

if __name__=='__main__':
    signal.signal(signal.SIGTERM,shared._signal_stop);signal.signal(signal.SIGINT,shared._signal_stop)
    raise SystemExit(main())
