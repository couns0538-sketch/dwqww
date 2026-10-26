"""Finite S11 three-arm native parity CLI. No native execution without --execute.

Consumes completed same-base Release and FIRST receipts after S10 publication.
Only a test scalar NNUE object and normally compiled oracle tool are built here.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import os
import re
import resource
import shlex
import signal
import time

HERE=Path(__file__).resolve().parent

def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

proof=load('s11_scalar_proof',HERE/'forge_sol_S11_scalar_parity_20261026.py')
qual=load('s11_std_bindings',HERE/'forge_sol_S11_qualify_native_20261026.py')
builder=qual.build_api
owned=builder.owned


def bind_arm(build_receipt,first_receipt,role,published_commit):
    data,source,build=qual.verify_build(build_receipt)
    if data['profile']!='Release' or data['role']!=role or data.get('S10_published_commit')!=published_commit:raise ValueError('wrong arm role/profile/publication')
    builder.verify_dependencies('Release')
    if data.get('compiler_sha256')!=owned.CXX_SHA or data.get('source_inventory_sha256')!=builder.INVENTORY_SHA or data.get('patch_sha256')!=builder.PATCH_SHA:raise ValueError('arm frozen compiler/source/patch identity differs')
    first=json.loads(first_receipt.read_text());qual.verify_first(first,proof.sha(build_receipt),proof.sha(build/'forge'),'Release');qual.previous.verify_first_files(first_receipt,first)
    oracle=data['material_oracle_compilation'];proof.verify_oracle_compilation(oracle,role)
    index=oracle.get('command_index')
    if type(index) is not int or not 0<=index<len(data['commands']) or data['commands'][index].get('argv')!=oracle['argv']:raise ValueError('oracle compile invocation not tied to actual closed command')
    if oracle['source']!=str(builder.ORACLE) or proof.sha(builder.ORACLE)!=proof.ORACLE_SHA or [x for x in oracle['argv'] if x.startswith('-I')]!=['-I'+str(source),'-I'+str(source/'include')]:raise ValueError('actual searched implementation include binding differs')
    builder.release.strict_tokens(oracle['argv']);core=build/'libforge_core.a';proof.verify_oracle_link_argv(oracle['argv'],core)
    map_path=build/'forge_sol_S11_materialkey_oracle.map'
    if oracle.get('map_path')!=str(map_path) or proof.sha(map_path)!=oracle.get('map_sha256'):raise ValueError('material oracle map path/hash differs')
    audit=proof.verify_link_map(map_path.read_text(),core)
    return {'data':data,'source':source,'build':build,'build_receipt_sha256':proof.sha(build_receipt),'FIRST_receipt_sha256':proof.sha(first_receipt),'link_map_audit':audit}


def scalar_link_argv(normal_argv,core,scalar_object,output,map_path):
    argv=list(normal_argv)
    maps=[x for x in argv if x.startswith(('-Wl,-Map,','-Wl,-Map='))]
    if len(maps)!=1 or argv.count('-o')!=1 or argv.count(str(core))!=1:raise ValueError('normal oracle link output/map/core shape differs')
    argv.remove(maps[0]);argv[argv.index('-o')+1]=str(output);argv.insert(argv.index(str(core)),str(scalar_object));argv.append('-Wl,-Map,'+str(map_path))
    proof.verify_oracle_link_argv(argv,core,scalar_object);return argv


def verify_scalar_artifacts(binding):
    for key in ('object','driver','map'):
        if proof.sha(Path(binding[key]))!=binding[key+'_sha256']:raise ValueError('qualified scalar '+key+' changed')


def normal_nnue_command(source,build):
    rows=json.loads((build/'compile_commands.json').read_text());matches=[r for r in rows if r['file']==str(source/'src/nnue.cpp')]
    if len(matches)!=1:raise ValueError('one actual normally built NNUE TU required')
    argv=matches[0].get('arguments') or shlex.split(matches[0]['command']);builder.release.strict_tokens(argv)
    if any(x in proof.SCALAR_FLAGS for x in argv):raise ValueError('ordinary NNUE recipe is already scalar-modified')
    return argv


def bind_corpus(manifest):
    value=json.loads(manifest.read_text())
    required={'count':1000000,'unique_position_fields':1000000,'gzip_size':8950562,'gzip_sha256':'e06bf2de476f1819ab098b854d718ff1b528c49c60ee9edbfd82206b99798a42','raw_size':52261200,'raw_sha256':'0d6594d3fb7dba38064eddc2a0f673d23c6551c052186cc5989047b86e762eb6'}
    if any(value.get(k)!=v for k,v in required.items()):raise ValueError('corpus is not the completed original S09 unique1M input')
    path=Path('/workspace/forge-pack24-20261026/S09_TORCHRAM_20261026/forge_sol_S09_torchram_probe_v2_20261026.py')
    if proof.sha(path)!='e43b6ec82a611e9fd03a1b44b70487189b7df1ed32cfe5734de9e139b055d7bb':raise ValueError('original sealed-corpus loader changed')
    sealer=load('s11_original_corpus_sealer',path)
    fd=sealer.sealed_memfd_from_gzip(value['gzip'],compressed_size=value['gzip_size'],compressed_sha256=value['gzip_sha256'],raw_size=value['raw_size'],raw_sha256=value['raw_sha256'])
    return value,fd


def main(argv=None):
    os.environ['PYTHONDONTWRITEBYTECODE']='1'
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute',action='store_true');p.add_argument('--authorization-reference',required=True);p.add_argument('--s10-published-commit',required=True)
    for name in ('baseline-build','candidate-build','baseline-first','candidate-first','corpus-manifest','out'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--cpu',type=int,required=True);p.add_argument('--max-seconds',type=float,default=1800);p.add_argument('--arm-seconds',type=float,default=500);p.add_argument('--scalar-build-seconds',type=float,default=180)
    a=p.parse_args(argv)
    if not a.execute or not re.fullmatch('[0-9a-f]{40}',a.s10_published_commit) or not 30<=a.max_seconds<=3600 or not 1<=a.arm_seconds<=1800 or not 10<=a.scalar_build_seconds<=300:p.error('explicit bounded grant and verified S10 publication reference required')
    if sorted(os.sched_getaffinity(0))!=[a.cpu] or os.getpriority(os.PRIO_PROCESS,0)!=19:p.error('use the granted single CPU/nice19')
    if not builder.permitted(a.out) or a.out.exists():p.error('new exact S11 native output descendant required')
    baseline=bind_arm(a.baseline_build,a.baseline_first,'baseline',a.s10_published_commit);candidate=bind_arm(a.candidate_build,a.candidate_first,'candidate',a.s10_published_commit)
    if baseline['data']['base']!=candidate['data']['base'] or os.path.samefile(a.baseline_build,a.candidate_build):p.error('distinct same-base baseline/candidate receipts required')
    if os.path.samefile(baseline['build']/'forge_sol_S11_materialkey_oracle',candidate['build']/'forge_sol_S11_materialkey_oracle'):p.error('same executable/inode cannot prove parity')
    if __import__('shutil').disk_usage(a.out.parent).free<3*(36+1000000*2068)+128*1048576:p.error('capacity for three full raw-equivalent streams plus margin required')
    soft,hard=resource.getrlimit(resource.RLIMIT_AS);cap=4*1024**3 if hard==resource.RLIM_INFINITY else min(4*1024**3,hard);resource.setrlimit(resource.RLIMIT_AS,(cap,cap))
    a.out.mkdir();start=time.monotonic();deadline=start+a.max_seconds;fd=None
    result={'schema':'forge.S11.three_arm_parity.v1','status':'FAIL','authorization_reference':a.authorization_reference,'S10_published_commit':a.s10_published_commit,'cpu':[a.cpu],'nice':19,'maximum_seconds':a.max_seconds,'per_arm_seconds':a.arm_seconds,'RLIMIT_AS_bytes':cap,'maximum_observed_owned_RSS_bytes':0,'positions':1000000,'child_limit':4096,'retention':{'records_per_chunk':10000,'gzip_level':1,'one_original_stream_per_arm':True},'source_only_before_explicit_grant':False,'commands':[],'arms':{},'nps_used':False,'new_main_engine_ELFs':0,'corpus_regenerations':0,'support_sources':{name:proof.sha(HERE/name) for name in ('forge_sol_S11_scalar_parity_20261026.py','forge_sol_S11_build_native_20261026.py','forge_sol_S11_qualify_native_20261026.py','forge_sol_S11_scalar_parity_run_20261026.py')}}
    previous=owned.boundary_reason
    def guard(_job=None,end=None):
        if time.monotonic()>=min(deadline-2,end or deadline-2):return 'OWNED_DEADLINE'
        if owned._STOP_REQUESTED:return 'EXTERNAL_STOP'
        if __import__('shutil').disk_usage(a.out).free<64*1048576:return 'DISK_FREE_FLOOR'
        pids={os.getpid()};events=a.out/'events.jsonl'
        if events.exists():
            lines=events.read_text().splitlines()
            if lines:pids.update(x['pid'] for x in owned._all_members(json.loads(lines[-1])['pid']))
        rss=0
        for pid in pids:
            try:
                for line in Path('/proc',str(pid),'status').read_text().splitlines():
                    if line.startswith('VmRSS:'):rss+=int(line.split()[1])*1024
            except (OSError,ValueError):pass
        result['maximum_observed_owned_RSS_bytes']=max(result['maximum_observed_owned_RSS_bytes'],rss)
        if rss>4*1024**3:return 'OWNED_RSS_LIMIT'
    owned.boundary_reason=guard
    def run(command,label,end):
        row=owned.run_owned(command,a.out,label,a.out,end);result['commands'].append(row)
        if row.get('error') or row.get('stop_reason') or row.get('returncode')!=0 or not row.get('leader_reaped') or row.get('all_group_members_after_reap'):raise RuntimeError('owned scalar-preparation command failed/open: '+label)
    try:
        source=candidate['source'];build=candidate['build'];core=build/'libforge_core.a';normal_object=build/'CMakeFiles/forge_core.dir/src/nnue.cpp.o';normal_hash=proof.sha(normal_object)
        original=normal_nnue_command(source,build);scalar=a.out/'forge_sol_S11_scalar_nnue_20261026.o';scalar_exe=a.out/'forge_sol_S11_scalar_materialkey_oracle_20261026';scalar_map=a.out/'forge_sol_S11_scalar_materialkey_oracle_20261026.map';build_end=min(deadline-2,time.monotonic()+a.scalar_build_seconds)
        run(['/usr/bin/x86_64-linux-gnu-ar','p',str(core),'nnue.cpp.o'],'00_actual_archive_nnue_member',build_end)
        if proof.sha(a.out/'00_actual_archive_nnue_member.stdout')!=normal_hash:raise ValueError('normal NNUE object differs from actual linked core member')
        scalar_command=proof.scalar_compile_argv(original,scalar);builder.release.strict_tokens(scalar_command);run(scalar_command,'01_compile_scalar_nnue_only',build_end)
        for mode,command,obj in [('avx2',original,normal_object),('scalar',scalar_command,scalar)]:
            run(proof.macro_probe_argv(command),'02_'+mode+'_actual_macros',build_end)
            result[mode+'_macro_proof']=proof.verify_macros((a.out/('02_'+mode+'_actual_macros.stdout')).read_text(),mode)
            run(['objdump','-d','-C','--no-show-raw-insn',str(obj)],'03_'+mode+'_actual_disassembly',build_end)
            result[mode+'_ISA_proof']=proof.verify_disassembly((a.out/('03_'+mode+'_actual_disassembly.stdout')).read_text(),mode)
        scalar_link=scalar_link_argv(candidate['data']['material_oracle_compilation']['argv'],core,scalar,scalar_exe,scalar_map);builder.release.strict_tokens(scalar_link)
        run(scalar_link,'04_link_normally_compiled_scalar_oracle',build_end)
        result['scalar_link_map']=proof.verify_link_map(scalar_map.read_text(),core,scalar)
        result['scalar_build']={'object':str(scalar),'object_sha256':proof.sha(scalar),'object_argv':scalar_command,'normal_object_sha256':normal_hash,'normal_archive_member_equal':True,'driver':str(scalar_exe),'driver_sha256':proof.sha(scalar_exe),'driver_argv':scalar_link,'map':str(scalar_map),'map_sha256':proof.sha(scalar_map),'production_source_unchanged':True,'scope':'test utility only; no new main engine'}
        corpus,fd=bind_corpus(a.corpus_manifest);result['corpus_manifest_sha256']=proof.sha(a.corpus_manifest);result['sealed_input']=proof.verify_sealed_input(fd,corpus['raw_size'],corpus['raw_sha256'])
        for label,exe,table in [('baseline_AVX2',baseline['build']/'forge_sol_S11_materialkey_oracle',0),('candidate_AVX2',build/'forge_sol_S11_materialkey_oracle',650),('candidate_SCALAR',scalar_exe,650)]:
            bind_arm(a.baseline_build,a.baseline_first,'baseline',a.s10_published_commit);bind_arm(a.candidate_build,a.candidate_first,'candidate',a.s10_published_commit)
            verify_scalar_artifacts(result['scalar_build'])
            allowed=min(a.arm_seconds,deadline-time.monotonic()-3)
            if allowed<1:raise TimeoutError('finite total budget exhausted before next arm')
            result['arms'][label]=proof.capture_arm(exe,fd,input_bytes=corpus['raw_size'],input_sha256=corpus['raw_sha256'],positions=1000000,child_limit=4096,table_checks=table,out=a.out,label=label,seconds=allowed,stop=guard)
        result['baseline_candidate']=proof.compare_chunked(a.out/'baseline_AVX2.stdout.chunks.json',a.out/'candidate_AVX2.stdout.chunks.json',1000000,4096,stop=guard)
        result['AVX2_scalar']=proof.compare_chunked(a.out/'candidate_AVX2.stdout.chunks.json',a.out/'candidate_SCALAR.stdout.chunks.json',1000000,4096,stop=guard)
        coverage=[{k:v for k,v in row['summary'].items() if k!='actual_table_basis_checks'} for row in result['arms'].values()]
        if not coverage[0]==coverage[1]==coverage[2]:raise ValueError('actual API/state coverage counts differ across arms')
        verify_scalar_artifacts(result['scalar_build'])
        if proof.sha(normal_object)!=normal_hash:raise ValueError('ordinary NNUE object changed')
        result['status']='PASS_NATIVE_EXACT_PARITY'
    except BaseException as e:result['error']=type(e).__name__+': '+str(e)
    finally:
        owned.boundary_reason=previous
        if fd is not None:os.close(fd)
        try:
            bind_arm(a.baseline_build,a.baseline_first,'baseline',a.s10_published_commit);bind_arm(a.candidate_build,a.candidate_first,'candidate',a.s10_published_commit)
            result['original_sources_and_all_artifacts_unchanged']=True
            if any(proof.sha(HERE/name)!=digest for name,digest in result['support_sources'].items()):raise ValueError('native support source changed during run')
        except Exception as e:result['original_sources_and_all_artifacts_unchanged']=False;result['postflight_error']=type(e).__name__+': '+str(e);result['status']='FAIL'
        result['elapsed_seconds']=time.monotonic()-start;owned.save_new(a.out/'forge_sol_S11_scalar_parity_result_20261026.json',result)
    print(json.dumps({'status':result['status'],'error':result.get('error'),'elapsed_seconds':result['elapsed_seconds']}));return 0 if result['status']=='PASS_NATIVE_EXACT_PARITY' else 1

if __name__=='__main__':
    signal.signal(signal.SIGTERM,owned._signal_stop);signal.signal(signal.SIGINT,owned._signal_stop)
    raise SystemExit(main())
