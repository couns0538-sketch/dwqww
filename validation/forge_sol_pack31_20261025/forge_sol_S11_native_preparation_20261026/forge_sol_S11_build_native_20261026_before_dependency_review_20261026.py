"""S11 build-only adapter over the qualified S09 compiler/ownership protocol.

No engine, CTest or timing run occurs here. S10 publication and a fresh root
execution grant are prerequisites; source preparation alone is not a grant.
"""
from pathlib import Path
import argparse,importlib.util,json,os,re,resource,shutil,signal,time

HERE=Path(__file__).resolve().parent
PREP=Path('/workspace/forge-pack24-20261026/S11')
INVENTORY=PREP/'forge_sol_S11_source_inventory_20261026.json'
INVENTORY_SHA='7c6843ac3c419c96fc7014beb84805154e4ab7ebe083ae79aa8e5e86d472ecc9'
PATCH=PREP/'forge_sol_S11_material_history_key_20261026.patch'
PATCH_SHA='1ac47bd324bf971005fcf3f8f57ad5f9ed6e4758e3186274230f07be4ea8bcee'
ORACLE=PREP/'forge_sol_S11_materialkey_api_oracle_20261026.cpp'
ORACLE_SHA='7d3be5616fe9e52382b2deb5b36d76c507a07a66bda07a6311f2e6a5dd557bd1'
TMP=Path('/tmp/forge_sol_S11_native_20261026')
RELEASE=Path('/workspace/forge-pack24-20261026/S09_NATIVE_PREP_20261026/forge_sol_S09_build_native_20261026.py')
ASAN=Path('/workspace/forge-pack24-20261026/S09_ASAN_PREP_20261026/forge_sol_S09_build_ASAN_20261026.py')
PROFILE_SOURCES={'Release':RELEASE,'ASAN':ASAN}
PROFILE_SHAS={'Release':'de17f7ac6b83a6d7f1e90fc202ffff0343717a5afc0839ce310d473469c4a39d','ASAN':'523bc1954cee0b0451722e095695df42641c2922b24de988ec82011eb34e0109'}

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

release=load('s11_old_release_build',RELEASE)
owned=release.owned
sources=release.source_api
STDLIB_TARGETS=release.STDLIB_TARGETS

def permitted(path):
    p=Path(path)
    return p.is_absolute() and p.resolve()==p and p!=TMP and p.is_relative_to(TMP)

def frozen():
    if owned.sha(INVENTORY)!=INVENTORY_SHA or owned.sha(PATCH)!=PATCH_SHA or owned.sha(ORACLE)!=ORACLE_SHA:
        raise ValueError('frozen S11 inventory/patch/oracle changed')
    return json.loads(INVENTORY.read_text())

def selected_source(base,role):
    if base not in ('Lprime','B') or role not in ('baseline','candidate'):raise ValueError('unknown source arm')
    inv=frozen();root=sources.BASES[base] if role=='baseline' else Path(inv['source_views'][base])
    expected=inv['original_source_freezes'][base] if role=='baseline' else inv['source_freezes'][base]
    if sources.inventory(root)!=expected:raise ValueError('actual source differs from frozen S11 arm')
    originals={k:sources.inventory(sources.BASES[k])==v for k,v in inv['original_source_freezes'].items()}
    if not all(originals.values()):raise ValueError('an original L/Lprime/B source changed')
    baseline=inv['original_source_freezes'][base];candidate=inv['source_freezes'][base]
    if set(baseline)!=set(candidate) or {p for p in baseline if baseline[p]!=candidate[p]}!={'src/search.cpp','README.md','IDEA_SOURCE.md'}:
        raise ValueError('S11 candidate changes outside its three declared files')
    return root,expected

def artifact_names(source,profile):
    names=list(STDLIB_TARGETS)
    if (source/'tests/bad_capture_tests.cpp').exists():names.append('forge_bad_capture_tests')
    if profile=='Release':names.append('forge_sol_S11_materialkey_oracle')
    elif profile!='ASAN':raise ValueError('unknown build profile')
    return names+['core_archive']

def oracle_command(profile_api,source,build,role):
    command=profile_api.manual_command(source,build/'libforge_core.a',ORACLE,build/'forge_sol_S11_materialkey_oracle')
    command.insert(1,'-I'+str(source))
    if role=='candidate':command.insert(1,'-DS11_REQUIRE_TABLE=1')
    command.append('-Wl,-Map,'+str(build/'forge_sol_S11_materialkey_oracle.map'))
    return command

def main(argv=None):
    os.environ['PYTHONDONTWRITEBYTECODE']='1'
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute',action='store_true');p.add_argument('--authorization-reference',required=True)
    p.add_argument('--s10-published-commit',required=True);p.add_argument('--base',choices=('Lprime','B'),required=True)
    p.add_argument('--role',choices=('baseline','candidate'),required=True);p.add_argument('--profile',choices=PROFILE_SOURCES,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--cpu',type=int,required=True);p.add_argument('--max-seconds',type=float,default=900)
    a=p.parse_args(argv)
    if not a.execute or not re.fullmatch('[0-9a-f]{40}',a.s10_published_commit) or not 10<=a.max_seconds<=900:
        p.error('fresh bounded grant and verified S10 publication reference required')
    if sorted(os.sched_getaffinity(0))!=[a.cpu] or os.getpriority(os.PRIO_PROCESS,0)!=19:p.error('use exactly the granted CPU/nice19')
    if not permitted(a.out) or a.out.exists() or not re.fullmatch('[A-Za-z0-9_.-]+',a.out.name):p.error('new literal safe S11 output descendant required')
    if owned.sha(PROFILE_SOURCES[a.profile])!=PROFILE_SHAS[a.profile]:p.error('qualified build adapter changed')
    source,before=selected_source(a.base,a.role);api=load('s11_selected_build',PROFILE_SOURCES[a.profile])
    TMP.mkdir(exist_ok=True)
    if shutil.disk_usage(TMP).free<128*1048576:p.error('128MiB temporary build start floor')
    cap=4*1024**3;soft,hard=resource.getrlimit(resource.RLIMIT_AS)
    if hard!=resource.RLIM_INFINITY:cap=min(cap,hard)
    resource.setrlimit(resource.RLIMIT_AS,(cap,cap))  # Compiler only; not inherited by a later runtime tool.
    a.out.mkdir();build=a.out/'build';start=time.monotonic();deadline=start+a.max_seconds
    result={'schema':'forge.S11.build.v1','status':'FAIL_BUILD_ONLY','base':a.base,'role':a.role,'profile':a.profile,
        'source':str(source),'source_before':before,'source_inventory_sha256':INVENTORY_SHA,'patch_sha256':PATCH_SHA,
        'controller_sha256':owned.sha(__file__),'qualified_build_adapter_sha256':PROFILE_SHAS[a.profile],
        'compiler_sha256':owned.CXX_SHA,'S10_published_commit':a.s10_published_commit,'authorization_reference':a.authorization_reference,
        'environment':{'PYTHONDONTWRITEBYTECODE':'1'},'commands':[],'target_artifacts':{},'engine_executions':0,
        'cpu':[a.cpu],'nice':19,'max_seconds':a.max_seconds,'compiler_RLIMIT_AS_bytes':cap,'maximum_observed_owned_RSS_bytes':0,
        'first_main_runtime_required':'bare bench11/quit before UCI or API helpers'}
    def guard(_job,end):
        if time.monotonic()>=end:return 'OWNED_DEADLINE'
        if owned._STOP_REQUESTED:return 'EXTERNAL_STOP'
        if shutil.disk_usage(TMP).free<32*1048576:return 'DISK_FREE_FLOOR'
        pids={os.getpid()};events=a.out/'events.jsonl'
        if events.exists():
            rows=events.read_text().splitlines()
            if rows:pids.update(x['pid'] for x in owned._all_members(json.loads(rows[-1])['pid']))
        rss=0
        for pid in pids:
            try:
                for line in Path('/proc',str(pid),'status').read_text().splitlines():
                    if line.startswith('VmRSS:'):rss+=int(line.split()[1])*1024
            except (OSError,ValueError):pass
        result['maximum_observed_owned_RSS_bytes']=max(result['maximum_observed_owned_RSS_bytes'],rss)
        if rss>4*1024**3:return 'OWNED_RSS_LIMIT'
    previous=owned.boundary_reason;owned.boundary_reason=guard
    def run(command,label):
        row=owned.run_owned(command,a.out,label,a.out,deadline);result['commands'].append(row)
        if row.get('error') or row['stop_reason'] or row['returncode']!=0 or not row['leader_reaped'] or row['all_group_members_after_reap']:
            raise RuntimeError('owned build did not close: '+label)
    try:
        asan=a.profile=='ASAN';kind='RelWithDebInfo' if asan else 'Release';optimization='-O2 -g -DNDEBUG' if asan else '-O3 -DNDEBUG'
        configure=[str(owned.CMAKE),'-S',str(source),'-B',str(build),'-DCMAKE_BUILD_TYPE='+kind,
            '-DCMAKE_CXX_COMPILER='+str(owned.CXX),'-DCMAKE_CXX_FLAGS='+owned.FLAGS,
            '-DCMAKE_CXX_FLAGS_'+kind.upper()+'='+optimization,'-DBUILD_SHARED_LIBS=OFF',
            '-DFORGE_ENABLE_SANITIZERS='+('ON' if asan else 'OFF'),'-DFORGE_NATIVE=OFF','-DFORGE_EXPOSE_TUNABLES=OFF',
            '-DFORGE_BUILD_VALIDATION_TOOLS=OFF','-DFORGE_BUILD_TUNING_TOOLS=OFF',
            '-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON']
        run(configure,'00_configure');result['recipe_before']=api.audit_recipe(source,build)
        targets=[x for x in artifact_names(source,a.profile) if x not in {'core_archive','forge_sol_S11_materialkey_oracle'}]
        for n,target in enumerate(targets,1):run([str(owned.CMAKE),'--build',str(build),'--target',target,'--parallel','1','--verbose'],f'{n:02d}_{target}')
        if not asan:
            command=oracle_command(api,source,build,a.role);api.strict_tokens(command)
            index=len(result['commands']);run(command,'materialkey_oracle_compile')
            linkmap=build/'forge_sol_S11_materialkey_oracle.map'
            checker=load('s11_linkmap_checker',HERE/'forge_sol_S11_scalar_parity_20261026.py')
            result['material_oracle_compilation']={'source':str(ORACLE),'sha256':ORACLE_SHA,'argv':command,'command_index':index,
                'map_path':str(linkmap),'map_sha256':owned.sha(linkmap),'link_map_audit':checker.verify_link_map(linkmap.read_text(),build/'libforge_core.a'),
                'S11_REQUIRE_TABLE':a.role=='candidate'}
        for name in artifact_names(source,a.profile):
            path=build/('libforge_core.a' if name=='core_archive' else name)
            result['target_artifacts'][name]={'path':str(path),'sha256':owned.sha(path),'bytes':path.stat().st_size}
        result['recipe_after']=api.audit_recipe(source,build);result['status']='PASS_BUILD_ONLY'
    except BaseException as error:result['error']=type(error).__name__+': '+str(error)
    finally:
        owned.boundary_reason=previous;result['source_after']=sources.inventory(source)
        result['source_unchanged']=result['source_after']==before
        try:selected_source(a.base,a.role)
        except Exception as error:result.update(status='FAIL_BUILD_ONLY',error='post-build source audit: '+str(error))
        if not result['source_unchanged']:result['status']='FAIL_BUILD_ONLY'
        result['elapsed_seconds']=time.monotonic()-start;owned.save_new(a.out/'forge_sol_S11_build_result_20261026.json',result)
    print(json.dumps({'status':result['status'],'error':result.get('error'),'elapsed_seconds':result['elapsed_seconds']}))
    return 0 if result['status']=='PASS_BUILD_ONLY' else 1

if __name__=='__main__':
    signal.signal(signal.SIGTERM,owned._signal_stop);signal.signal(signal.SIGINT,owned._signal_stop)
    raise SystemExit(main())
