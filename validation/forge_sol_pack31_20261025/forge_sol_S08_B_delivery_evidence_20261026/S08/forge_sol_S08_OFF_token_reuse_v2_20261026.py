#!/usr/bin/env python3
"""Both-base OFF preprocessor proof; native Clang lexer only for raw mismatches."""
import argparse, hashlib, importlib.util, json, os, pathlib, subprocess, time

HERE=pathlib.Path(__file__).resolve().parent
ORIGINAL=HERE/'forge_sol_S08_OFF_preprocess_reuse_20261026.py'
LEXER=HERE/'forge_sol_S08_libclang_token_hash_20261026.py'
OLD=HERE/'forge_sol_S08_OFF_PREPROCESS_NATIVE_20261026'
def sha(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api);return api

def capture_for_lexer(command,shared,expected,root):
    """Bounded RAM buffer only for the two raw-different UCI inputs."""
    with shared.SubreaperScope():
        process=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
        try:data,error=process.communicate(timeout=60)
        except BaseException:shared._close_group(process);raise
        reaped,members=shared._reap_group(process.pid,.1)
    if process.returncode or error or members:raise ValueError('lexer input preprocessor failed')
    if len(data)>4*1048576:raise ValueError('lexer input exceeds4MiB RAM limit')
    if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('lexer input differs from streamed preprocessor hash')
    return data

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute',action='store_true');parser.add_argument('--output',required=True,type=pathlib.Path)
    args=parser.parse_args(argv)
    if not args.execute:parser.error('explicit --execute')
    if sorted(os.sched_getaffinity(0))!=[1] or os.getpriority(os.PRIO_PROCESS,0)!=19:parser.error('requires CPU1 nice19')
    first=module(ORIGINAL,'raw_off_proof');lex=module(LEXER,'off_native_lexer');shared=first.load_shared()
    if sha(shared.CXX)!=shared.CXX_SHA or sha(first.PATCH)!=first.PATCH_SHA or sha(first.FREEZE)!=first.FREEZE_SHA:raise ValueError('frozen input changed')
    freeze=json.loads(first.FREEZE.read_text())
    if shared.snapshot(first.V2)!=freeze['source_sha256']:raise ValueError('v2 source mismatch')
    overlay=OLD/'B_preprocess_overlay'
    old=json.loads((OLD/'forge_sol_S08_OFF_preprocess_result_20261026.json').read_text())
    if old['status']!='FAIL' or old['patch_sha256']!=first.PATCH_SHA:raise ValueError('original raw failure history changed')
    originals={name:shared.snapshot(base) for name,base in [('Lprime',first.LP),('B',first.B)]}
    result={'status':'RUNNING','scope':'PREPROCESSED_TOKEN_IDENTITY_ONLY','new_OFF_binary_built':False,'B_ON_native_qualified':False,'original_raw_failure_preserved':True,'original_raw_result_sha256':sha(OLD/'forge_sol_S08_OFF_preprocess_result_20261026.json'),'original_helper_sha256':sha(ORIGINAL),'lexer_source_sha256':sha(LEXER),'compiler_sha256':shared.CXX_SHA,'source_freeze_sha256':first.FREEZE_SHA,'patch_sha256':first.PATCH_SHA,'source_before':originals,'pairs':[],'no_code_or_string_normalization':True,'maximum_total_seconds':600,'maximum_lexer_input_bytes_in_RAM':4*1048576}
    output=shared.new_directory(args.output);path=output/'forge_sol_S08_OFF_token_reuse_v2_result_20261026.json';start=time.monotonic()
    def save():path.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    save();flags=first.production_flags()
    try:
        for name,base,candidate in [('Lprime',first.LP,first.V2),('B',first.B,overlay)]:
            if first.cmake_off_residue(candidate/'CMakeLists.txt')!=(base/'CMakeLists.txt').read_text():raise ValueError('OFF CMake unguarded residue mismatch')
            result.setdefault('cmake',{})[name]={'FORGE_PROF_default_OFF':True,'only_ON_blocks_add_profile_cpp_or_prof_tests':True,'unconditional_residue_byte_identical':True}
            for relative in first.TUS:
                if time.monotonic()-start>=600:raise TimeoutError('total600seconddeadline')
                baseline=[str(shared.CXX),*flags[relative],'-I',str(base/'include'),'-E','-P',str(base/relative)]
                if name=='Lprime':selected=candidate/relative;includes=['-I',str(candidate/'include')]
                else:
                    selected=candidate/relative if (candidate/relative).exists() else base/relative
                    includes=['-I',str(candidate/'include'),'-I',str(base/'include'),'-iquote',str(base/'src')]
                proposed=[str(shared.CXX),*flags[relative],*includes,'-E','-P',str(selected)]
                left=first.stream_preprocess(baseline,shared,output);right=first.stream_preprocess(proposed,shared,output)
                same=(left['stdout_sha256'],left['stdout_bytes'])==(right['stdout_sha256'],right['stdout_bytes'])
                row={'base':name,'tu':relative,'baseline':left,'candidate':right,'raw_byte_identical':same}
                if same:row['preprocessing_token_identity']='PASS_BY_RAW_BYTE_IDENTITY'
                else:
                    a=capture_for_lexer(baseline,shared,left['stdout_sha256'],output)
                    b=capture_for_lexer(proposed,shared,right['stdout_sha256'],output)
                    l=lex.token_hash(a);r=lex.token_hash(b)
                    row['native_lexer']={'baseline':l,'candidate':r}
                    row['preprocessing_token_identity']='PASS' if (l['sha256'],l['tokens'])==(r['sha256'],r['tokens']) else 'FAIL'
                    if row['preprocessing_token_identity']!='PASS':
                        result['pairs'].append(row);save();raise ValueError('actual preprocessing token mismatch: '+name+':'+relative)
                result['pairs'].append(row);save()
        empty=first.stream_preprocess([str(shared.CXX),*flags['src/uci.cpp'],'-I',str(first.V2/'include'),'-E','-P',str(first.V2/'src/profile.cpp')],shared,output)
        if empty['stdout_bytes']!=0:raise ValueError('OFF profile.cpp is not empty')
        result['profile_cpp_OFF']=empty
        for name,base in [('Lprime',first.LP),('B',first.B)]:
            if shared.snapshot(base)!=originals[name]:raise ValueError('original tree changed: '+name)
        if shared.snapshot(first.V2)!=freeze['source_sha256']:raise ValueError('v2 source changed')
        result.update(status='PASS_PREPROCESSED_TOKEN_IDENTITY',original_trees_unchanged=True,v2_source_unchanged=True)
    except Exception as exc:result.update(status='FAIL',failure=type(exc).__name__+': '+str(exc))
    finally:result['elapsed_seconds']=time.monotonic()-start;save()
    print(json.dumps({'status':result['status'],'pairs':len(result['pairs']),'raw_mismatches':sum(not row['raw_byte_identical'] for row in result['pairs']),'output':str(output)}),flush=True)
    return 0 if result['status']=='PASS_PREPROCESSED_TOKEN_IDENTITY' else 1

if __name__=='__main__':raise SystemExit(main())
