"""Only new typed T1/T2 lifecycle and FMA checks on a reused Release baseline.

No new FIRST, deep benchmark, perft, full CTest, JUnit or main build is claimed.
"""
from pathlib import Path
import argparse,json,os,re,resource,shutil,signal,sys,time
if not __debug__:raise RuntimeError('Run without -O/PYTHONOPTIMIZE')
sys.dont_write_bytecode=True
import forge_sol_S11_release_reuse_20261026 as reuse

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true')
    p.add_argument('--reuse-receipt',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--cpu',type=int,required=True);p.add_argument('--authorization-reference',required=True)
    p.add_argument('--max-seconds',type=float,default=120);a=p.parse_args(argv)
    if not a.execute or not 10<=a.max_seconds<=180:p.error('explicit bounded native grant required')
    if sorted(os.sched_getaffinity(0))!=[a.cpu] or os.getpriority(os.PRIO_PROCESS,0)!=19:p.error('use exact granted single CPU/nice19')
    data=json.loads(a.reuse_receipt.read_text());first=Path(data['evidence']['original_receipt']);arm=reuse.bind_reuse_arm(a.reuse_receipt,first,'baseline',data['S10_published_commit'])
    builder=reuse.sealed_builder()
    if not builder.permitted(a.out) or a.out.exists():p.error('new literal S11 output descendant required')
    if shutil.disk_usage(reuse.TMP).free<64*1048576:p.error('64MiB temporary start floor')
    runtime_dependencies=reuse.verify_runtime_dependencies()
    qual=reuse.sealed_qualifier();transport=qual.previous;q=transport.q;shared=q.shared
    for key in ('ASAN_OPTIONS','UBSAN_OPTIONS','LSAN_OPTIONS','LD_PRELOAD','LD_LIBRARY_PATH'):os.environ.pop(key,None)
    soft,hard=resource.getrlimit(resource.RLIMIT_AS);cap=4*1024**3 if hard==resource.RLIM_INFINITY else min(4*1024**3,hard);resource.setrlimit(resource.RLIMIT_AS,(cap,cap))
    a.out.mkdir();start=time.monotonic();guard=transport.RSSGuard(a.out,a.out/'ROOT_STOP',start+a.max_seconds)
    engine=Path(data['evidence']['canonical_build'])/'forge';core=arm['build']/'libforge_core.a'
    result={'schema':'forge.S11.reused_baseline_light_checks.v1','status':'FAIL','evidence_class':'REUSE_NOT_NEW_RUN','reuse_receipt':str(a.reuse_receipt),'reuse_receipt_sha256':reuse.sha(a.reuse_receipt),'base':data['base'],'profile':'Release','role':'baseline','S10_published_commit':data['S10_published_commit'],'main_ELF_sha256':reuse.sha(engine),'controller_sha256':reuse.sha(__file__),'reuse_verifier_sha256':reuse.sha(reuse.__file__),'authorization_reference':a.authorization_reference,'cpu':[a.cpu],'nice':19,'max_seconds':a.max_seconds,'commands':[],'new_FIRST_runs':0,'new_full_Std_runs':0,'new_JUnit':False,'new_main_ELFs':0,'original_evidence_sha256':data['evidence']['original_receipt_sha256']}
    result['runtime_dependency_sha256']=runtime_dependencies
    old=shared.boundary_reason;shared.boundary_reason=guard.reason
    signal.signal(signal.SIGTERM,shared._signal_stop);signal.signal(signal.SIGINT,shared._signal_stop)
    def command(args,label):
        row=shared.run_owned(args,a.out,label,a.out,guard.deadline);result['commands'].append(row)
        reuse.require(row.get('returncode')==0 and row.get('leader_reaped') is True and row.get('all_group_members_after_reap')==[] and not row.get('stop_reason') and not row.get('error'),'light check command failed/open: '+label)
        return row
    try:
        result['UCI_T1_T2']=transport.lifecycle(engine,a.out,guard)
        command(['/usr/bin/x86_64-linux-gnu-ar','p',str(core),'nnue.cpp.o'],'canonical_archive_nnue_member')
        obj=a.out/'canonical_archive_nnue_member.stdout'
        for label,path in [('FMA_NNUE_object',obj),('FMA_NNUE_scope_ELF',engine)]:
            command([sys.executable,'-B',str(q.FMA),str(path)],label);val=json.loads((a.out/(label+'.stdout')).read_text());transport.verify_fma(val);result[label]=val
        command(['objdump','-d','--no-show-raw-insn',str(engine)],'canonical_whole_ELF_assembly')
        assembly=a.out/'canonical_whole_ELF_assembly.stdout'
        reuse.require(not any(re.match(r'^\s*[0-9a-fA-F]+:\s+vf(?:n)?m(?:add|sub)[a-z0-9]*\b',s) for s in assembly.read_text().splitlines()),'whole-ELF FMA nonzero')
        result['FMA_whole_ELF']={'fma_count':0,'assembly_sha256':reuse.sha(assembly)};result['status']='PASS_NEW_LIGHT_CHECKS_WITH_REUSED_STD'
    except BaseException as e:result['error']=type(e).__name__+': '+str(e)
    finally:
        shared.boundary_reason=old
        try:
            reuse.require(reuse.verify_runtime_dependencies()==runtime_dependencies,'runtime dependencies changed during light checks')
            after=reuse.bind_reuse_arm(a.reuse_receipt,first,'baseline',data['S10_published_commit'])
            reuse.require(after['data']==data and reuse.sha(a.reuse_receipt)==result['reuse_receipt_sha256'],'reuse arm changed during light checks')
            reuse.require(reuse.sha(__file__)==result['controller_sha256'] and reuse.sha(reuse.__file__)==result['reuse_verifier_sha256'],'light-check source changed')
            result['original_sources_and_all_artifacts_unchanged']=True
        except Exception as e:result.update(status='FAIL',postflight_error=str(e),original_sources_and_all_artifacts_unchanged=False)
        ownership=[json.loads(p.read_text()) for p in sorted(a.out.glob('*.ownership.json'))];result['engine_process_ownership']=ownership
        result['all_new_engine_groups_closed']=bool(ownership) and all(r['leader_reaped'] and not r['all_group_members_after_reap'] and not r.get('cleanup_error') for r in ownership)
        if not result['all_new_engine_groups_closed']:result['status']='FAIL'
        result['maximum_observed_owned_RSS_bytes']=guard.maximum_owned_RSS_bytes;result['elapsed_seconds']=time.monotonic()-start
        shared.save_new(a.out/'forge_sol_S11_reused_baseline_light_result_20261026.json',result)
    print(json.dumps({'status':result['status'],'evidence_class':'REUSE_NOT_NEW_RUN','error':result.get('error')}));return 0 if result['status']=='PASS_NEW_LIGHT_CHECKS_WITH_REUSED_STD' else 1
if __name__=='__main__':raise SystemExit(main())
