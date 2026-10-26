"""Bounded helper-only eight-head archive build; original source remains untouched."""
import importlib.util
import json
import os
from pathlib import Path
import resource
import shlex
import shutil
import signal
import sys
import time

HERE=Path(__file__).resolve().parent
PREP=HERE.parent/'S09_NATIVE_PREP_20261026'
PROTOCOL=HERE/'forge_sol_S09_convert8_native_protocol_20261026.json'
OUT=Path('/tmp/forge_sol_S09_native_20261026/converted8_helper_build_once_20261026')
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
build_api=load('s09_base_build',PREP/'forge_sol_S09_build_native_20261026.py');owned=build_api.owned
qual=load('s09_base_qualify',PREP/'forge_sol_S09_qualify_native_20261026.py');api=build_api.source_api
pair=load('s09_pair',PREP/'forge_sol_S09_native_pair_20261026.py')


def main():
    if sys.argv[1:]!=['--execute-derived8-only']:raise ValueError('explicit bounded derived8 grant required')
    if sorted(os.sched_getaffinity(0))!=[0] or os.getpriority(os.PRIO_PROCESS,0)!=19:raise ValueError('CPU0nice19 required')
    os.environ['PYTHONDONTWRITEBYTECODE']='1';sys.dont_write_bytecode=True
    resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3))
    plan=json.loads(PROTOCOL.read_text());parent_path=Path(plan['parent_build_receipt'])
    parent,source,parent_build=qual.verify_build(parent_path)
    if owned.sha(parent_path)!=plan['parent_build_receipt_sha256'] or api.inventory(source)!=plan['parent_source_inventory']:raise ValueError('parent closed build/source changed')
    converter=Path(plan['converter']['path'])
    if owned.sha(converter)!=plan['converter']['sha256']:raise ValueError('converter changed')
    for item in plan['object_closure']:
        if owned.sha(Path(item['path']))!=item['sha256'] or owned.sha(Path(item['source']))!=item['source_sha256']:raise ValueError('object/source closure changed')
        build_api.strict_tokens(item['compiler_argv'])
    if shutil.disk_usage(OUT.parent).free<64*1048576:raise ValueError('64MiB derived build start floor')
    OUT.mkdir(exist_ok=False);build=OUT/'build';build.mkdir();start=time.monotonic();deadline=start+180
    source_before=api.inventory(source);weights=build/'forge_sol_S09_replicated8_h256e12_20261026.inc';core=build/'libforge_core.a';commands=[]
    result={'schema':'forge.S09.build.v1','status':'FAIL_BUILD_ONLY','source':str(source),'source_before':source_before,'role':'candidate','source_receipt':str(source/'S09_source_view.json'),'source_receipt_sha256':owned.sha(source/'S09_source_view.json'),'weights_file':str(weights),'commands':commands,'target_artifacts':{},'environment':{'PYTHONDONTWRITEBYTECODE':'1'},'expected_stored_heads':8,'scope':'DERIVED8_HELPER_ONLY_NO_NEW_ENGINE_NO_FULL_STD_NO_PARITY_RUN','parent_build_receipt_sha256':owned.sha(parent_path),'parent_artifacts':parent['target_artifacts'],'object_closure':plan['object_closure'],'protocol_sha256':owned.sha(PROTOCOL),'controller_sha256':owned.sha(__file__),'compiler_sha256':owned.sha(owned.CXX),'core_archive':str(core),'cpu':[0],'nice':19,'engine_UCI_executions':0,'contract_test_executions':0,'nps_claim':False}
    old=owned.boundary_reason
    def guard(_unused,limit):
        if time.monotonic()>=limit:return 'OWNED_DEADLINE'
        if owned._STOP_REQUESTED:return 'EXTERNAL_STOP'
        if shutil.disk_usage(OUT).free<32*1048576:return 'TEMP_DISK_FLOOR'
    owned.boundary_reason=guard
    def run(argv,label):
        record=owned.run_owned(argv,OUT,label,OUT,deadline);commands.append(record)
        if record.get('error') or record.get('stop_reason') or record.get('returncode')!=0 or not record.get('leader_reaped') or record.get('all_group_members_after_reap'):raise RuntimeError('owned derived build failed/open: '+label)
    try:
        run([sys.executable,'-B',str(converter),'replicate',str(source/'src/nnue_weights.inc'),str(weights)],'00_convert_1_to_8')
        result['weights_sha256']=owned.sha(weights);result['conversion']=json.loads((OUT/'00_convert_1_to_8.stdout').read_text())
        if result['conversion'].get('all_heads_identical') is not True or result['conversion'].get('heads')!=8:raise ValueError('conversion contract failed')
        run([sys.executable,'-B',str(HERE/'forge_sol_S09_verify_archive_members_20261026.py'),str(PROTOCOL)],'01_verify_reused_archive_members')
        nnue=next(x for x in plan['object_closure'] if not x['reused']);argv=list(nnue['compiler_argv']);index=argv.index('-o');argv[index+1]=str(build/'nnue.cpp.o')
        macro='-DFORGE_NNUE_WEIGHTS_FILE="'+str(weights)+'"';argv.insert(1,macro);build_api.strict_tokens(argv)
        run(argv,'02_compile_nnue_only');result['nnue_compilation']={'source':nnue['source'],'source_sha256':nnue['source_sha256'],'argv':argv,'command_index':2,'weights_include_macro':macro}
        objects=[str(build/'nnue.cpp.o') if not x['reused'] else x['path'] for x in plan['object_closure']]
        run(['/usr/bin/x86_64-linux-gnu-ar','rcsD',str(core),*objects],'03_assemble_derived_archive')
        drivers=[('forge_nnue_heads_parity',build_api.HARN),('forge_nnue_bit_snapshot',build_api.SNAP),('forge_nnue_heads_contract',source/'tests/nnue_heads_contract.cpp')]
        for number,(name,driver) in enumerate(drivers,4):
            argv=build_api.manual_command(source,core,driver,build/name);build_api.strict_tokens(argv);index=len(commands);run(argv,f'{number:02}_compile_'+name)
            field='harness_compilation' if name=='forge_nnue_heads_parity' else 'snapshot_compilation' if name=='forge_nnue_bit_snapshot' else 'contract_compilation'
            result[field]={'source':str(driver),'sha256':owned.sha(driver),'argv':argv,'command_index':index}
            result['target_artifacts'][name]={'path':str(build/name),'sha256':owned.sha(build/name),'bytes':(build/name).stat().st_size}
        result['target_artifacts']['core_archive']={'path':str(core),'sha256':owned.sha(core),'bytes':core.stat().st_size}
        run([str(build/'forge_nnue_heads_contract'),'8'],'07_contract_stored8');result['contract_test_executions']=1
        if (OUT/'07_contract_stored8.stdout').read_text()!='available=1 residual=1 hidden=256 stored_heads=8\n' or (OUT/'07_contract_stored8.stderr').read_bytes():raise ValueError('actual stored8 contract failed')
        run([sys.executable,'-B',str(qual.q.FMA),str(build/'nnue.cpp.o')],'08_FMA_NNUE_object')
        result['FMA']=json.loads((OUT/'08_FMA_NNUE_object.stdout').read_text());qual.verify_fma(result['FMA']);result['status']='PASS_BUILD_ONLY'
    except BaseException as e:result['error']=type(e).__name__+': '+str(e)
    finally:
        owned.boundary_reason=old;result['source_after']=api.inventory(source);result['source_unchanged']=source_before==result['source_after']
        result['all_original_objects_unchanged']=all(owned.sha(Path(x['path']))==x['sha256'] for x in plan['object_closure'])
        try:
            qual.verify_build(parent_path);result['parent_build_still_unchanged']=owned.sha(parent_path)==plan['parent_build_receipt_sha256']
        except Exception as e:result['parent_build_still_unchanged']=False;result['parent_postflight_error']=type(e).__name__+': '+str(e)
        result['peak_child_rss_kib']=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss;result['elapsed_seconds']=time.monotonic()-start
        if not result['source_unchanged'] or not result['all_original_objects_unchanged'] or not result['parent_build_still_unchanged'] or result['peak_child_rss_kib']>4*1024**2:result['status']='FAIL_BUILD_ONLY'
        owned.save_new(OUT/'forge_sol_S09_build_result_20261026.json',result)
    print(json.dumps({'status':result['status'],'error':result.get('error'),'elapsed_seconds':result['elapsed_seconds']}));return 0 if result['status']=='PASS_BUILD_ONLY' else 1

if __name__=='__main__':
    signal.signal(signal.SIGTERM,owned._signal_stop);signal.signal(signal.SIGINT,owned._signal_stop)
    raise SystemExit(main())
