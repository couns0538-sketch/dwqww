"""One stored-eight-head run of the unchanged original bit-snapshot driver.

Reuse the already captured reference output, verifying its original hash/receipt;
do not rerun the reference or reconstruct a stream from result summaries.
"""
from pathlib import Path
import filecmp,importlib.util,json,os,time

HERE=Path('/workspace/forge-pack24-20261026/S09_NATIVE_PREP_20261026')
spec=importlib.util.spec_from_file_location('s09_pair',HERE/'forge_sol_S09_native_pair_20261026.py')
pair=importlib.util.module_from_spec(spec);spec.loader.exec_module(pair)
spec=importlib.util.spec_from_file_location('s09_runtime',HERE/'forge_sol_S09_qualify_native_20261026.py')
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
ROOT=q.TMP

def main():
    assert sorted(os.sched_getaffinity(0))==[1] and os.getpriority(os.PRIO_PROCESS,0)==19
    baseline=ROOT/'original_bit_snapshot_pair_once_20261026';receipt=baseline/'forge_sol_S09_original_bit_snapshot_result_20261026.json'
    assert pair.sha(receipt)=='89d7b172b5622f5fb3a3bace3211da53f5900fddb3caf3488aa4c1a4a20bb25b'
    old=json.loads(receipt.read_text());assert old['status']=='PASS_ORIGINAL_BIT_SNAPSHOT'
    reference=baseline/'reference.stdout';assert pair.sha(reference)==old['arms'][0]['raw_snapshot_sha256']
    arm_path=ROOT/'converted8_helper_build_once_20261026/forge_sol_S09_converted8_parity_arm_binding_20261026.json'
    arm=json.loads(arm_path.read_text());before=pair.verify_arm(arm['executable'],arm_path,'candidate',pair.load_preparer())
    br=Path(arm['build_receipt']);b=json.loads(br.read_text());sc=b['snapshot_compilation'];exe=Path(b['target_artifacts']['forge_nnue_bit_snapshot']['path'])
    assert pair.sha(exe)==b['target_artifacts']['forge_nnue_bit_snapshot']['sha256']
    assert sc['source']==str(q.build_api.SNAP) and sc['sha256']==pair.sha(q.build_api.SNAP)
    assert sc['argv']==b['commands'][sc['command_index']]['argv'] and sc['argv'].count(sc['source'])==1
    out=ROOT/'converted8_original_bit_snapshot_once_20261026';out.mkdir(exist_ok=False)
    start=time.monotonic();guard=q.q.Guard(out,out/'ROOT_STOP',start+180);prior=q.q.shared.boundary_reason;q.q.shared.boundary_reason=guard.reason
    result={'status':'FAIL','scope':'unchanged original six edge-FEN walk/100000 synthetic activation driver against stored8; exact full raw output compared to original prior reference bytes',
        'controller_sha256':pair.sha(__file__),'reference_result_sha256':pair.sha(receipt),'reference_raw_sha256':pair.sha(reference),'arm_before':before,'snapshot_compilation':sc,'snapshot_executable_sha256':pair.sha(exe),'cpu':[1],'nice':19}
    try:
        r=q.q.shared.run_owned([str(exe)],out,'stored8_snapshot',out,guard.deadline);result['command']=r
        if r.get('error') or r['stop_reason'] or r['returncode']!=0 or r['all_group_members_after_reap'] or r['captures']['stderr']['bytes']:raise ValueError('stored8 snapshot did not close successfully')
        if not filecmp.cmp(reference,out/'stored8_snapshot.stdout',shallow=False):raise ValueError('stored8 full original float-word/CP bytes differ')
        if pair.verify_arm(arm['executable'],arm_path,'candidate',pair.load_preparer())!=before or pair.sha(exe)!=result['snapshot_executable_sha256']:raise ValueError('stored8 build/source/inputs changed')
        result.update(status='PASS_STORED8_ORIGINAL_BIT_SNAPSHOT',all_serialized_bytes_equal=True,raw_snapshot_bytes=r['captures']['stdout']['bytes'],raw_snapshot_sha256=r['captures']['stdout']['sha256'])
    except BaseException as exc:result['error']=type(exc).__name__+': '+str(exc)
    finally:
        q.q.shared.boundary_reason=prior;result['elapsed_seconds']=time.monotonic()-start
        q.q.shared.save_new(out/'forge_sol_S09_converted8_snapshot_result_20261026.json',result)
    print(json.dumps({'status':result['status'],'error':result.get('error'),'elapsed_seconds':result['elapsed_seconds']}))
    return 0 if result['status']=='PASS_STORED8_ORIGINAL_BIT_SNAPSHOT' else 1

if __name__=='__main__':raise SystemExit(main())
