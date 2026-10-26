"""Exact original bit-snapshot driver comparison; no new NNUE/FEN parser."""
from pathlib import Path
import filecmp,importlib.util,json,os,time

HERE=Path('/workspace/forge-pack24-20261026/S09_NATIVE_PREP_20261026')
spec=importlib.util.spec_from_file_location('s09_runtime',HERE/'forge_sol_S09_qualify_native_20261026.py')
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
TMP=q.TMP

def main():
    if sorted(os.sched_getaffinity(0))!=[1] or os.getpriority(os.PRIO_PROCESS,0)!=19:raise ValueError('CPU1nice19 required')
    out=TMP/'original_bit_snapshot_pair_once_20261026';out.mkdir(exist_ok=False)
    start=time.monotonic();guard=q.q.Guard(out,out/'ROOT_STOP',start+360)
    result={'status':'FAIL','scope':'unchanged original deterministic six edge-FEN paths and100000 synthetic activations; all serialized float accumulator words/NNUE CP bytes compared',
        'controller_sha256':q.q.shared.sha(__file__),'cpu':[1],'nice':19,'commands':[],'arms':[],'no_speed_or_strength_claim':True}
    old=q.q.shared.boundary_reason;q.q.shared.boundary_reason=guard.reason
    try:
        artifacts=[]
        for label in ('reference','Lprime'):
            receipt=TMP/(label+'_release_once_20261026')/'forge_sol_S09_build_result_20261026.json'
            data,source,build=q.verify_build(receipt);sc=data['snapshot_compilation'];exe=build/'forge_nnue_bit_snapshot'
            if sc['source']!=str(q.build_api.SNAP) or sc['sha256']!=q.q.shared.sha(q.build_api.SNAP) or sc['argv']!=data['commands'][sc['command_index']]['argv'] or sc['argv'].count(sc['source'])!=1:
                raise ValueError('actual original snapshot compile source binding differs')
            artifacts.append(exe);result['arms'].append({'label':label,'build_receipt':str(receipt),'build_receipt_sha256':q.q.shared.sha(receipt),'executable_sha256':q.q.shared.sha(exe),'snapshot_compilation':sc})
        if os.path.samefile(*artifacts):raise ValueError('snapshot self-comparison')
        for arm,exe in zip(result['arms'],artifacts):
            r=q.q.shared.run_owned([str(exe)],out,arm['label'],out,guard.deadline);result['commands'].append(r)
            if r.get('error') or r['stop_reason'] or r['returncode']!=0 or r['all_group_members_after_reap'] or r['captures']['stderr']['bytes']:
                raise ValueError('snapshot child failed or incomplete')
            if r['captures']['stdout']['bytes']<=400000 or r['captures']['stdout']['bytes']%4:
                raise ValueError('snapshot binary output incomplete')
            arm['raw_snapshot_sha256']=r['captures']['stdout']['sha256'];arm['raw_snapshot_bytes']=r['captures']['stdout']['bytes']
        if not filecmp.cmp(out/'reference.stdout',out/'Lprime.stdout',shallow=False):raise ValueError('cross-build original float-bit snapshot bytes differ')
        for arm in result['arms']:q.verify_build(Path(arm['build_receipt']))
        result['status']='PASS_ORIGINAL_BIT_SNAPSHOT';result['all_serialized_bytes_equal']=True
    except BaseException as exc:result['error']=type(exc).__name__+': '+str(exc)
    finally:
        q.q.shared.boundary_reason=old;result['elapsed_seconds']=time.monotonic()-start
        q.q.shared.save_new(out/'forge_sol_S09_original_bit_snapshot_result_20261026.json',result)
    print(json.dumps({'status':result['status'],'error':result.get('error'),'elapsed_seconds':result['elapsed_seconds']}))
    return 0 if result['status']=='PASS_ORIGINAL_BIT_SNAPSHOT' else 1

if __name__=='__main__':raise SystemExit(main())
