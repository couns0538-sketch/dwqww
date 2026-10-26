"""Compile ONLY the new baseline oracle after an explicit native grant.

Main/helper ELFs and full Std remain original canonical evidence, not new runs.
"""
from pathlib import Path
import argparse,gzip,hashlib,json,os,re,resource,shutil,signal,sys,time
if not __debug__:raise RuntimeError('Run without -O/PYTHONOPTIMIZE')
sys.dont_write_bytecode=True
import forge_sol_S11_release_reuse_20261026 as reuse

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true')
    p.add_argument('--base',choices=('Lprime','B'),required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--cpu',type=int,required=True);p.add_argument('--authorization-reference',required=True)
    p.add_argument('--s10-published-commit',required=True);p.add_argument('--max-seconds',type=float,default=180)
    a=p.parse_args(argv)
    if not a.execute or not re.fullmatch('[0-9a-f]{40}',a.s10_published_commit) or not 10<=a.max_seconds<=300:p.error('explicit bounded native grant and published S10 reference required')
    if sorted(os.sched_getaffinity(0))!=[a.cpu] or os.getpriority(os.PRIO_PROCESS,0)!=19:p.error('use exact granted single CPU/nice19')
    builder=reuse.sealed_builder();owned=builder.owned
    if not builder.permitted(a.out) or a.out.exists():p.error('new literal S11 output descendant required')
    binding=reuse.make_binding(a.base);source=Path(binding['source']);builder.verify_dependencies('Release')
    reuse.TMP.mkdir(exist_ok=True)
    if shutil.disk_usage(reuse.TMP).free<128*1048576:p.error('128MiB temporary start floor')
    soft,hard=resource.getrlimit(resource.RLIMIT_AS);cap=4*1024**3 if hard==resource.RLIM_INFINITY else min(4*1024**3,hard);resource.setrlimit(resource.RLIMIT_AS,(cap,cap))
    a.out.mkdir();build=a.out/'build';build.mkdir();start=time.monotonic();deadline=start+a.max_seconds
    result={'schema':reuse.SCHEMA,'status':'FAIL_ORACLE_ONLY_REUSE','base':a.base,'role':'baseline','profile':'Release','evidence_class':'REUSE_NOT_NEW_RUN','source':str(source),'source_before':binding['source_before'],'evidence':binding,'build':str(build),'source_inventory_sha256':builder.INVENTORY_SHA,'patch_sha256':builder.PATCH_SHA,'compiler_sha256':owned.CXX_SHA,'S10_published_commit':a.s10_published_commit,'authorization_reference':a.authorization_reference,'commands':[],'target_artifacts':{},'new_main_ELFs':0,'new_FIRST_runs':0,'new_full_Std_runs':0,'new_JUnit':False,'new_light_checks':'REQUIRED_SEPARATE_GATE','controller_sha256':reuse.sha(__file__),'reuse_verifier_sha256':reuse.sha(reuse.__file__),'cpu':[a.cpu],'nice':19,'max_seconds':a.max_seconds,'compiler_RLIMIT_AS_bytes':cap}
    def guard(_job,end):
        if time.monotonic()>=min(deadline-2,end):return 'OWNED_DEADLINE'
        if owned._STOP_REQUESTED:return 'EXTERNAL_STOP'
        if shutil.disk_usage(reuse.TMP).free<32*1048576:return 'DISK_FREE_FLOOR'
    previous=owned.boundary_reason;owned.boundary_reason=guard
    signal.signal(signal.SIGTERM,owned._signal_stop);signal.signal(signal.SIGINT,owned._signal_stop)
    try:
        core=build/'libforge_core.a'
        with core.open('xb') as f:f.write(gzip.decompress(Path(binding['core_archive']['compressed_path']).read_bytes()));f.flush();os.fsync(f.fileno())
        core.chmod(binding['core_archive']['restore_mode'])
        reuse.require(reuse.sha(core)==binding['core_archive']['sha256'] and core.stat().st_size==binding['core_archive']['bytes'],'restored canonical core differs')
        command=reuse.oracle_plan(a.base,build);reuse.verify_oracle_plan(a.base,build,command)
        row=owned.run_owned(command,a.out,'oracle_only_compile',a.out,deadline-2);result['commands'].append(row)
        reuse.require(row.get('returncode')==0 and row.get('leader_reaped') is True and row.get('all_group_members_after_reap')==[] and not row.get('stop_reason') and not row.get('error'),'oracle compiler failed/open')
        proof=reuse.load('s11_reuse_build_linkcheck',reuse.SEALED/'forge_sol_S11_scalar_parity_20261026.py');mp=build/'forge_sol_S11_materialkey_oracle.map'
        result['material_oracle_compilation']={'source':str(builder.ORACLE),'sha256':builder.ORACLE_SHA,'argv':command,'command_index':0,'map_path':str(mp),'map_sha256':reuse.sha(mp),'link_map_audit':proof.verify_link_map(mp.read_text(),core),'S11_REQUIRE_TABLE':False,'link_checker_sha256':reuse.sha(reuse.SEALED/'forge_sol_S11_scalar_parity_20261026.py')}
        result['target_artifacts']=reuse.artifact_inventory(binding,build);result['status']='PASS_ORACLE_ONLY_WITH_REUSED_STD'
    except BaseException as error:result['error']=type(error).__name__+': '+str(error)
    finally:
        owned.boundary_reason=previous
        try:
            builder.selected_source(a.base,'baseline');builder.verify_dependencies('Release')
            reuse.verify_binding(binding);result['source_after']=builder.sources.inventory(source)
            reuse.require(result['source_after']==result['source_before'],'source changed during oracle compile')
            reuse.require(reuse.sha(__file__)==result['controller_sha256'] and reuse.sha(reuse.__file__)==result['reuse_verifier_sha256'],'reuse controllers changed')
        except Exception as error:result.update(status='FAIL_ORACLE_ONLY_REUSE',postflight_error=str(error))
        result['elapsed_seconds']=time.monotonic()-start;owned.save_new(a.out/'forge_sol_S11_baseline_reuse_result_20261026.json',result)
    print(json.dumps({'status':result['status'],'evidence_class':'REUSE_NOT_NEW_RUN','new_main_ELFs':0,'new_full_Std_runs':0,'error':result.get('error')}))
    return 0 if result['status']=='PASS_ORACLE_ONLY_WITH_REUSED_STD' else 1
if __name__=='__main__':raise SystemExit(main())
