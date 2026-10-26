"""Build-only S09 ASan+UBSan qualification on sealed original/source-view inputs.

No engine, CTest, snapshot or parity helper is executed here. The exact original
parity and bit-snapshot drivers are compiled against each observed core archive.
The established owned-process/subreaper helper captures every compiler command.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import resource
import shlex
import shutil
import signal
import time

HERE=Path(__file__).resolve().parent
SHARED=HERE.parent/'S08/forge_sol_S08_build_window_subreaper_20261026.py'
SHARED_SHA='85acc70b0dd987d21e6ae93276f7183eb23806b35a92dc217c72da2018ab8fa0'
spec=importlib.util.spec_from_file_location('s09_owned_build',SHARED)
owned=importlib.util.module_from_spec(spec);spec.loader.exec_module(owned)
spec=importlib.util.spec_from_file_location('s09_source',HERE.parent/'S09_NATIVE_PREP_20261026/forge_sol_S09_prepare_source_view_20261026.py')
source_api=importlib.util.module_from_spec(spec);spec.loader.exec_module(source_api)
TMP=Path('/tmp/forge_sol_S09_native_20261026')
FLAGS=owned.FLAGS
FLOOR=16*1048576
HARN=HERE.parent/'S09_NATIVE_PREP_20261026/overlay/tools/nnue/heads_parity.cpp'
HARN_SHA='4572a45df6ef7d33757fcac267bb9397591d64f996fdf64cb456af51ce6aef91'
SNAP=source_api.BASES['L']/'tools/nnue_snapshot.cpp'
STDLIB_TARGETS=('forge','forge_tests','forge_tt_tests','forge_rule50_tests',
    'forge_legal_witness_tests','forge_correction_history_tests',
    'forge_runtime_psqt_tests','forge_pawn_span_tests','forge_nearest_pawn_tests',
    'forge_pv_metadata_tests','forge_bench')


def permitted(path):
    p=Path(path)
    return p.is_absolute() and p.resolve()==p and p!=TMP and p.is_relative_to(TMP)


def strict_tokens(tokens):
    required=set(FLAGS.split())|{'-O2','-g','-DNDEBUG','-fsanitize=address,undefined','-fno-omit-frame-pointer'}
    if Path(tokens[0]).resolve()!=owned.CXX.resolve() or not required.issubset(tokens):
        raise ValueError('wrong compiler or incomplete ASan/UBSan recipe')
    if [x for x in tokens if x.startswith('-std=')] not in (['-std=c++20'],['-std=gnu++20']):
        raise ValueError('C++20 missing or overridden')
    for prefix,want in {'-march=':['-march=x86-64-v3'],'-mtune=':['-mtune=znver5'],
            '-DFORGE_NNUE_HIDDEN':['-DFORGE_NNUE_HIDDEN=256']}.items():
        if [x for x in tokens if x.startswith(prefix)]!=want:raise ValueError('recipe override '+prefix)
    contracts=[x for x in tokens if x.startswith('-ffp-contract=')]
    if not contracts or any(x!='-ffp-contract=off' for x in contracts):raise ValueError('floating contraction recipe differs')
    for token in tokens:
        if ((token.startswith('-fsanitize=') and token!='-fsanitize=address,undefined') or token=='-fomit-frame-pointer' or (token.startswith('-g') and token!='-g')):raise ValueError('sanitizer/frame/debug override '+token)
        if (token.startswith(('-flto','-fprofile','-fauto-profile','-UFORGE_','-DFORGE_PROF','-fno-sanitize'))
                or (token.startswith('-O') and token!='-O2')
                or token in {'-ffast-math','-funsafe-math-optimizations','-fassociative-math',
                             '-freciprocal-math','-fno-signed-zeros','-ffinite-math-only'}):
            raise ValueError('forbidden native recipe flag '+token)


def audit_recipe(source,build):
    cache={}
    for line in (build/'CMakeCache.txt').read_text().splitlines():
        if line and not line.startswith(('#','//')) and ':' in line and '=' in line:
            k,v=line.split('=',1);cache[k.split(':',1)[0]]=v
    expected={'CMAKE_HOME_DIRECTORY':str(source),'CMAKE_BUILD_TYPE':'RelWithDebInfo',
        'CMAKE_CXX_FLAGS':FLAGS,'CMAKE_CXX_FLAGS_RELWITHDEBINFO':'-O2 -g -DNDEBUG',
        'FORGE_NATIVE':'OFF','FORGE_ENABLE_SANITIZERS':'ON','FORGE_EXPOSE_TUNABLES':'OFF',
        'FORGE_BUILD_VALIDATION_TOOLS':'OFF','FORGE_BUILD_TUNING_TOOLS':'OFF',
        'CMAKE_INTERPROCEDURAL_OPTIMIZATION':'OFF','CMAKE_EXPORT_COMPILE_COMMANDS':'ON',
        'BUILD_SHARED_LIBS':'OFF'}
    if any(cache.get(k)!=v for k,v in expected.items()):raise ValueError('generated native CMake cache differs')
    if Path(cache.get('CMAKE_CXX_COMPILER','')).resolve()!=owned.CXX.resolve():raise ValueError('CMake compiler differs')
    rows=json.loads((build/'compile_commands.json').read_text());seen=[]
    for row in rows:
        rel=Path(row['file']).relative_to(source).as_posix()
        strict_tokens(row.get('arguments') or shlex.split(row['command']));seen.append(rel)
    if len(seen)!=len(set(seen)) or not {'src/nnue.cpp','src/search.cpp','src/uci.cpp'}.issubset(seen):
        raise ValueError('duplicate or incomplete generated translation units')
    return {'translation_units':sorted(seen),'compile_commands_sha256':owned.sha(build/'compile_commands.json'),
        'cache_sha256':owned.sha(build/'CMakeCache.txt')}


def manual_command(source,core,driver,dest):
    return [str(owned.CXX),'-std=c++20','-O2','-g','-DNDEBUG',*FLAGS.split(),'-fsanitize=address,undefined','-fno-omit-frame-pointer',
            '-I'+str(source/'include'),str(driver),str(core),'-pthread','-o',str(dest)]


def main(argv=None):
    os.environ['PYTHONDONTWRITEBYTECODE']='1'
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--execute',action='store_true');ap.add_argument('--authorization-reference',required=True)
    ap.add_argument('--role',choices=('reference','candidate'),required=True)
    ap.add_argument('--source',type=Path,required=True);ap.add_argument('--source-receipt',type=Path,required=True)
    ap.add_argument('--stored-heads',choices=(1,8),type=int,default=1)
    ap.add_argument('--out',type=Path,required=True);ap.add_argument('--max-seconds',type=float,default=900)
    ap.add_argument('--cpu',type=int,default=3)
    a=ap.parse_args(argv)
    if not a.execute or not 10<=a.max_seconds<=900:ap.error('explicit bounded build authorization required')
    if sorted(os.sched_getaffinity(0))!=[a.cpu] or os.getpriority(os.PRIO_PROCESS,0)!=19:
        ap.error('pin exactly the granted CPU at nice19')
    if not permitted(a.out) or a.out.exists():ap.error('output must be a new exact /tmp native descendant')
    if owned.sha(SHARED)!=SHARED_SHA or owned.sha(HARN)!=HARN_SHA or owned.sha(owned.CXX)!=owned.CXX_SHA:
        ap.error('frozen compiler/helper/driver changed')
    audits=source_api.verify_all_baselines()
    if not all(x['unchanged'] for x in audits.values()):ap.error('frozen baseline changed')
    source=a.source
    if not source.is_absolute() or source.resolve()!=source:ap.error('exact absolute source path required')
    if a.role=='reference':
        if source!=source_api.BASES['L'] or a.stored_heads!=1 or owned.sha(a.source_receipt)!=source_api.BASELINE_SHA:
            ap.error('reference must be exact original one-head L')
    else:
        sr=json.loads(a.source_receipt.read_text())
        allowed=HERE.parent/'S09_NATIVE_20261026'
        if not source.is_relative_to(allowed) or sr.get('private_source')!=str(source) or sr.get('new_delta_sha256')!=source_api.PATCH_SHA:
            ap.error('candidate must be a prepared exact private source view')
    if a.stored_heads!=1:ap.error('eight-head build protocol awaits its own sealed converted-net source receipt')
    if TMP.exists() and (TMP.resolve()!=TMP or not TMP.is_dir()):ap.error('native output root is not an exact directory')
    TMP.mkdir(exist_ok=True)
    if shutil.disk_usage(TMP).free<64*1048576:ap.error('64MiB build-start floor')
    memory_limit=4*1024**3
    soft,hard=resource.getrlimit(resource.RLIMIT_AS)
    cap=min(memory_limit,hard) if hard!=resource.RLIM_INFINITY else memory_limit
    resource.setrlimit(resource.RLIMIT_AS,(cap,cap))
    a.out.mkdir();build=a.out/'build';start=time.monotonic();deadline=start+a.max_seconds
    before=source_api.inventory(source);core=build/'libforge_core.a'
    weights=source/'src/nnue_weights.inc';commands=[]
    result={'profile':'ASAN_UBSAN_STATIC_O2_DEBUG','schema':'forge.S09.build.v1','status':'FAIL_BUILD_ONLY','source':str(source),
        'source_before':before,'source_receipt':str(a.source_receipt),'source_receipt_sha256':owned.sha(a.source_receipt),
        'role':a.role,'compiler_sha256':owned.CXX_SHA,'controller_sha256':owned.sha(__file__),
        'owned_helper_sha256':SHARED_SHA,'environment':{'PYTHONDONTWRITEBYTECODE':'1'},
        'weights_file':str(weights),'weights_sha256':owned.sha(weights),'commands':commands,
        'target_artifacts':{},'authorization_reference':a.authorization_reference,
        'engine_executions':0,'cpu':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),
        'expected_stored_heads':a.stored_heads,'runtime_requires_first_bare_bench11':True}
    result['memory_protocol']={'per_process_RLIMIT_AS_bytes':cap,'sampled_owned_group_RSS_limit_bytes':memory_limit,
        'sampling':'at each owned guard poll; includes controller and current child group',
        'maximum_observed_owned_RSS_bytes':0,'parallel_build_jobs':1}
    def guard(_job,end):
        if time.monotonic()>=end:return 'OWNED_DEADLINE'
        if owned._STOP_REQUESTED:return 'EXTERNAL_STOP'
        if shutil.disk_usage(TMP).free<FLOOR:return 'FREE_DISK_FLOOR'
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
        result['memory_protocol']['maximum_observed_owned_RSS_bytes']=max(result['memory_protocol']['maximum_observed_owned_RSS_bytes'],rss)
        if rss>memory_limit:return 'OWNED_RSS_LIMIT'
        return None
    old=owned.boundary_reason;owned.boundary_reason=guard
    def run(command,label):
        r=owned.run_owned(command,a.out,label,a.out,deadline);r['running_group_members_after_close']=r.get('running_group_members_after_close',[])
        commands.append(r)
        if r.get('error') or r['stop_reason'] or r['returncode']!=0 or not r['leader_reaped'] or r['all_group_members_after_reap']:
            raise RuntimeError('owned build command did not close successfully: '+label)
    try:
        configure=[str(owned.CMAKE),'-S',str(source),'-B',str(build),'-DCMAKE_BUILD_TYPE=RelWithDebInfo',
            '-DCMAKE_CXX_COMPILER='+str(owned.CXX),'-DCMAKE_CXX_FLAGS='+FLAGS,
            '-DCMAKE_CXX_FLAGS_RELWITHDEBINFO=-O2 -g -DNDEBUG','-DBUILD_SHARED_LIBS=OFF',
            '-DFORGE_ENABLE_SANITIZERS=ON','-DFORGE_NATIVE=OFF','-DFORGE_EXPOSE_TUNABLES=OFF',
            '-DFORGE_BUILD_VALIDATION_TOOLS=OFF','-DFORGE_BUILD_TUNING_TOOLS=OFF',
            '-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON']
        run(configure,'00_configure');result['recipe_before']=audit_recipe(source,build)
        targets=list(STDLIB_TARGETS)
        if (source/'tests/bad_capture_tests.cpp').exists():targets.append('forge_bad_capture_tests')
        if a.role=='candidate':targets+=['forge_nnue_heads_tests','forge_nnue_heads_contract']
        for i,target in enumerate(targets,1):
            run([str(owned.CMAKE),'--build',str(build),'--target',target,'--parallel','1','--verbose'],f'{i:02}_{target}')
        for name,driver in [('forge_nnue_heads_parity',HARN),('forge_nnue_bit_snapshot',SNAP)]:
            command=manual_command(source,core,driver,build/name);strict_tokens(command)
            index=len(commands);run(command,name)
            if name=='forge_nnue_heads_parity':result['harness_compilation']={'source':str(HARN),'sha256':HARN_SHA,'argv':command,'command_index':index}
            else:result['snapshot_compilation']={'source':str(SNAP),'sha256':owned.sha(SNAP),'argv':command,'command_index':index}
        for name in targets+['forge_nnue_heads_parity','forge_nnue_bit_snapshot']:
            result['target_artifacts'][name]={'path':str(build/name),'sha256':owned.sha(build/name),'bytes':(build/name).stat().st_size}
        result['target_artifacts']['core_archive']={'path':str(core),'sha256':owned.sha(core),'bytes':core.stat().st_size}
        result['recipe_after']=audit_recipe(source,build);result['status']='PASS_BUILD_ONLY'
    except BaseException as exc:result['error']=type(exc).__name__+': '+str(exc)
    finally:
        owned.boundary_reason=old;result['source_after']=source_api.inventory(source)
        result['source_unchanged']=before==result['source_after'];result['baseline_inventory_after']=source_api.verify_all_baselines()
        if not result['source_unchanged'] or not all(x['unchanged'] for x in result['baseline_inventory_after'].values()):result['status']='FAIL_BUILD_ONLY';result['error']='source/baseline changed during build'
        result['elapsed_seconds']=time.monotonic()-start
        owned.save_new(a.out/'forge_sol_S09_build_result_20261026.json',result)
    print(json.dumps({'status':result['status'],'error':result.get('error'),'elapsed_seconds':result['elapsed_seconds']}))
    return 0 if result['status']=='PASS_BUILD_ONLY' else 1


if __name__=='__main__':
    signal.signal(signal.SIGTERM,owned._signal_stop);signal.signal(signal.SIGINT,owned._signal_stop)
    raise SystemExit(main())
