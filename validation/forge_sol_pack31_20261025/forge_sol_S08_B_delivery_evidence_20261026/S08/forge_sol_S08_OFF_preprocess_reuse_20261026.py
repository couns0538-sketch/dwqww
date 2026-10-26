#!/usr/bin/env python3
"""Stream-hash raw OFF preprocessor output; no compile, link or engine run."""
import argparse, hashlib, importlib.util, json, os, pathlib, re, selectors, shlex, shutil, subprocess, tempfile, time

HERE=pathlib.Path(__file__).resolve().parent
F=pathlib.Path('/workspace/forge-pack24-20261025/new_handoff_1435/selected/forge_handoff_full_20261025_1435/files')
LP=F/'01c_lockderived_jobC_S01/forge_h256_e12_lockderived_jobC_S01_src'
B=F/'01b_base_h256_e12_buffix/forge_h256_e12_buffix_jobC_S01_src'
V2=HERE/'Lprime_v2'
PATCH=HERE/'forge_sol_S08_profcounters_TLS_v2_20261026.patch'
PATCH_SHA='91c28d9f3b70af08885d50239141890813722cf00114bda8a2d12b71eb5e476c'
FREEZE=HERE/'forge_sol_S08_TLS_v2_source_freeze_20261026.json'
FREEZE_SHA='2923e86c186e357aac177e453f5745993d0839af02422d2622ff9f80dffae5ad'
SHARED=HERE/'forge_sol_S08_build_window_subreaper_20261026.py'
SHARED_SHA='85acc70b0dd987d21e6ae93276f7183eb23806b35a92dc217c72da2018ab8fa0'
OFF_COMMANDS=HERE/'forge_sol_S08_OFF_build_window1_20261026/build/compile_commands.json'
TUS=['src/'+name+'.cpp' for name in ('bitboard','board','book','eval','eval_params','nnue','search','uci')]
FLOOR=8*1048576

def sha(path):
    h=hashlib.sha256()
    with pathlib.Path(path).open('rb') as stream:
        for part in iter(lambda:stream.read(65536),b''):h.update(part)
    return h.hexdigest()

def load_shared():
    if sha(SHARED)!=SHARED_SHA:raise ValueError('shared controller hash changed')
    spec=importlib.util.spec_from_file_location('off_preprocess_owned',SHARED)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def production_flags():
    result={}
    for row in json.loads(OFF_COMMANDS.read_text()):
        relative=pathlib.Path(row['file']).relative_to(HERE/'Lprime').as_posix()
        if relative not in TUS:continue
        tokens=shlex.split(row['command']);flags=[];skip=False
        for token in tokens[1:]:
            if skip:skip=False;continue
            if token=='-o':skip=True;continue
            if token=='-c' or token==row['file'] or token.startswith('-I'):continue
            flags.append(token)
        if '-DNDEBUG' not in flags or any('FORGE_PROF' in x for x in flags):raise ValueError('not a production OFF recipe')
        result[relative]=flags
    if set(result)!=set(TUS):raise ValueError('eight original production TUs required')
    return result

def stream_preprocess(command,shared,work_root):
    start=time.monotonic();digest=hashlib.sha256();size=0;stderr=bytearray();process=None
    receipt={'argv':list(map(str,command)),'stdout_saved':False,'normalization':'NONE; hash exact GCC -E -P stdout bytes'}
    with shared.SubreaperScope():
        try:
            if shutil.disk_usage(work_root).free<FLOOR:raise RuntimeError('disk below8MiB')
            process=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
            receipt['pid']=process.pid
            selector=selectors.DefaultSelector();selector.register(process.stdout,selectors.EVENT_READ,'stdout');selector.register(process.stderr,selectors.EVENT_READ,'stderr')
            while selector.get_map():
                if time.monotonic()-start>60:raise TimeoutError('preprocess60seconddeadline')
                if shutil.disk_usage(work_root).free<FLOOR:raise RuntimeError('disk below8MiB')
                for key,_ in selector.select(.1):
                    data=os.read(key.fileobj.fileno(),65536)
                    if not data:selector.unregister(key.fileobj);continue
                    if key.data=='stdout':digest.update(data);size+=len(data)
                    else:
                        stderr.extend(data)
                        if len(stderr)>65536:raise ValueError('stderr exceeds64KiB')
            process.wait(timeout=2)
            reaped,members=shared._reap_group(process.pid,.1)
            receipt.update(returncode=process.returncode,stdout_sha256=digest.hexdigest(),stdout_bytes=size,stderr=stderr.decode('utf-8','replace'),stderr_sha256=hashlib.sha256(stderr).hexdigest(),leader_reaped=True,reaped_descendants=reaped,all_group_members_after_reap=members)
            if process.returncode!=0 or stderr or members:raise ValueError('preprocessor failed or descendants remain')
        except BaseException:
            if process is not None:shared._close_group(process)
            raise
        finally:
            if process is not None:
                process.stdout.close();process.stderr.close()
    receipt['elapsed_seconds']=time.monotonic()-start
    return receipt

def cmake_off_residue(candidate):
    blocks=[
      'option(FORGE_PROF "Build opt-in search-only profiling counters" OFF)\n',
      'if(FORGE_PROF)\n    target_sources(forge_core PRIVATE src/profile.cpp)\n    target_compile_definitions(forge_core PUBLIC FORGE_PROF=1)\nendif()\n',
      'if(FORGE_PROF)\n    add_executable(forge_prof_tests tests/prof_tests.cpp)\n    target_link_libraries(forge_prof_tests PRIVATE forge_core Threads::Threads)\n    add_test(NAME forge_prof_tests COMMAND forge_prof_tests)\nendif()\n',
    ]
    text=candidate.read_text()
    for block in blocks:
        if text.count(block)!=1:raise ValueError('unexpected FORGE_PROF CMake block')
        text=text.replace(block,'',1)
    if 'FORGE_PROF' in text:raise ValueError('unaccounted profiling CMake directive')
    return text

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute',action='store_true');parser.add_argument('--output',required=True,type=pathlib.Path)
    args=parser.parse_args(argv)
    if not args.execute:parser.error('requires --execute')
    if sorted(os.sched_getaffinity(0))!=[1] or os.getpriority(os.PRIO_PROCESS,0)!=19:parser.error('use CPU1nice19')
    shared=load_shared()
    if sha(shared.CXX)!=shared.CXX_SHA or sha(PATCH)!=PATCH_SHA or sha(FREEZE)!=FREEZE_SHA:raise ValueError('input hash mismatch')
    freeze=json.loads(FREEZE.read_text())
    if shared.snapshot(V2)!=freeze['source_sha256']:raise ValueError('v2 source changed')
    before={name:shared.snapshot(root) for name,root in [('Lprime',LP),('B',B)]}
    out=shared.new_directory(args.output);overlay=out/'B_preprocess_overlay';overlay.mkdir()
    files=re.findall(r'^diff --git a/(.+) b/.+$',PATCH.read_text(),re.M)
    copied=0
    for relative in files:
        source=B/relative
        if source.exists():
            target=overlay/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes());copied+=source.stat().st_size
    if copied>200000:raise ValueError('overlay copied more than200KB')
    command=['patch','-p1','-F0','--no-backup-if-mismatch','-d',str(overlay)]
    with PATCH.open('rb') as stream:applied=subprocess.run(command,stdin=stream,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
    (out/'forge_sol_S08_B_overlay_apply_20261026.stdout').write_bytes(applied.stdout)
    (out/'forge_sol_S08_B_overlay_apply_20261026.stderr').write_bytes(applied.stderr)
    if applied.returncode or applied.stderr:raise ValueError('B overlay patch failed')
    flags=production_flags()
    result={'status':'RUNNING','no_engine_compile_link_or_execution':True,'compiler_sha256':shared.CXX_SHA,'patch_sha256':PATCH_SHA,'source_freeze_sha256':FREEZE_SHA,'recipe_compile_commands_sha256':sha(OFF_COMMANDS),'overlay_copied_existing_bytes':copied,'patch_command':command,'normalization':'No custom normalization. GCC -E -P suppresses line markers; complete stdout bytes are hashed while streaming.','pairs':[]}
    path=out/'forge_sol_S08_OFF_preprocess_result_20261026.json'
    def save():path.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    save()
    try:
        for name,base,candidate in [('Lprime',LP,V2),('B',B,overlay)]:
            residue=cmake_off_residue(candidate/'CMakeLists.txt')
            if residue!=(base/'CMakeLists.txt').read_text():raise ValueError('OFF CMake residue differs: '+name)
            result.setdefault('cmake',{})[name]={'default_PROF_OFF':True,'only_guarded_source_and_test_targets_added':True,'unconditional_residue_byte_identical':True,'candidate_sha256':sha(candidate/'CMakeLists.txt'),'baseline_sha256':sha(base/'CMakeLists.txt')}
            for relative in TUS:
                baseline=[str(shared.CXX),*flags[relative],'-I',str(base/'include'),'-E','-P',str(base/relative)]
                if name=='Lprime':selected=candidate/relative;includes=['-I',str(candidate/'include')]
                else:
                    selected=candidate/relative if (candidate/relative).exists() else base/relative
                    includes=['-I',str(candidate/'include'),'-I',str(base/'include'),'-iquote',str(base/'src')]
                proposed=[str(shared.CXX),*flags[relative],*includes,'-E','-P',str(selected)]
                left=stream_preprocess(baseline,shared,out);right=stream_preprocess(proposed,shared,out)
                same=(left['stdout_sha256'],left['stdout_bytes'])==(right['stdout_sha256'],right['stdout_bytes'])
                result['pairs'].append({'base':name,'tu':relative,'baseline':left,'candidate':right,'raw_byte_identical':same});save()
                if not same:raise ValueError('actual preprocessed byte mismatch: '+name+':'+relative)
        empty=stream_preprocess([str(shared.CXX),*flags['src/uci.cpp'],'-I',str(V2/'include'),'-E','-P',str(V2/'src/profile.cpp')],shared,out)
        if empty['stdout_bytes']!=0:raise ValueError('OFF profile.cpp is not empty')
        result['new_profile_cpp_OFF']=empty
        for name,base in [('Lprime',LP),('B',B)]:
            if shared.snapshot(base)!=before[name]:raise ValueError('original source tree changed: '+name)
        if shared.snapshot(V2)!=freeze['source_sha256']:raise ValueError('v2 source changed during proof')
        result.update(status='PASS_PREPROCESS_ONLY',originals_unchanged=True,v2_source_unchanged=True,new_OFF_binary_built=False,B_ON_native_qualified=False)
    except Exception as exc:result.update(status='FAIL',failure=type(exc).__name__+': '+str(exc))
    finally:save()
    print(json.dumps({'status':result['status'],'pairs':len(result['pairs']),'output':str(out)}),flush=True)
    return 0 if result['status']=='PASS_PREPROCESS_ONLY' else 1

if __name__=='__main__':raise SystemExit(main())
