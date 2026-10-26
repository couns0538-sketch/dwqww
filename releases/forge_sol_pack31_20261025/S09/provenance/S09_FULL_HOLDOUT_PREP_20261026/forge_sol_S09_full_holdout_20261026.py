"""Prepared, separately authorized CPU evaluation of the full synthetic holdout.

Loads existing f006 include weights; never trains, exports or queues a network.
Reader/targets and model forward are imported from pinned original/candidate
v3b sources. Existing sealed-Torch loader is reused without package changes.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
FILES=Path('/workspace/forge-pack24-20261025/new_handoff_1435/selected/forge_handoff_full_20261025_1435/files')
DIAGNOSTIC=HERE.parent/'S09_TORCHRAM_20261026/f023_forensics_20261026/forge_sol_S09_shutdown_diagnostic_20261026.py'
DIAGNOSTIC_SHA='84b3f7f5a773340dfaddb3c2942d117a03ee68f82faaec7bfef756a6e4648729'
OWNED=HERE.parent/'S08/forge_sol_S08_build_window_subreaper_20261026.py'
OWNED_SHA='85acc70b0dd987d21e6ae93276f7183eb23806b35a92dc217c72da2018ab8fa0'
STAGED=HERE.parent/'S09'
OLD=FILES/'07_nnue_context/train_resid_v3b.py'
NEW=STAGED/'forge_sol_S09_train_resid_v3b_20261026.py'
NET=FILES/'03_nets/resid_h256_e48_f006_b06_ep48.inc'
SAMPLE=FILES/'06_jobD/data32_sample/data32_sample_50k'
PINS={OLD:'5cebba4d44133630e247d9ab4c0085fa6301dde8db1dfe1389452ac19d92313f',
      NEW:'8ea6111cffce3f2ea24096e7af27b8e34e1a7a73f805560fbdd7bbd68fb74f6c',
      NET:'0fdf9bdb6bdf4c9f1622bcef29921912acb139fdf388e541b017a948118d4661',
      STAGED/'forge_sol_S09_buckets_20261026.py':'08270b7ec29d467928585fd7433b2588896d41b93fe24cda838006498630bb7e',
      STAGED/'make_heads_inc.py':'39ec705a93fed1cb80773fc37ea4a2dfe20008c628fcd38b462620c1c112b6b0',
      SAMPLE/'h000.pos':'92c40ae25c3b650db9f5db235786133afed3e9a8f6691e7860dff6bdc5aa11b3',
      SAMPLE/'h000.hce':'212e51e6c108f3ff6b879b0f247277925f9483102e34230b5024e5fb7ef2cc44'}
PRIVATE=Path('/workspace/.cloud-setup/nnue-pipeline-20261023-venv')
LIBDIR=PRIVATE/'lib/python3.12/site-packages/torch/lib'
OUTROOT=Path('/tmp/forge_sol_S09_native_20261026')
ROWS=50000
BATCH=512
TOLERANCE=1e-5
WORK_SECONDS=180
HARD_SECONDS=240


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def module(path,name,expected=None):
    if expected is not None and sha(path)!=expected:raise ValueError('pinned source changed: '+str(path))
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec)
    sys.modules[name]=value;spec.loader.exec_module(value);return value


def verify_inputs():
    actual={str(path):sha(path) for path in PINS}
    if any(actual[str(path)]!=value for path,value in PINS.items()):raise ValueError('frozen source/net/sample input changed')
    return actual


def model_arrays(net,heads):
    """Invert the original exporter layout, not the include parser/record format."""
    import numpy as np
    if type(heads) is not int or heads not in (1,8) or net['hidden']!=256 or net['heads']!=1:
        raise ValueError('requires H256 original one-head include and target1or8')
    if [len(net[k]) for k in ('w1','b1','w2','b2')]!=[768*256,256,512,1]:
        raise ValueError('wrong original network shapes')
    scale=np.float32(4096)
    return {'ft.weight':(np.asarray(net['w1'],dtype=np.float32).reshape(768,256).T/scale).copy(),
            'ft.bias':np.asarray(net['b1'],dtype=np.float32)/scale,
            'out.weight':np.repeat(np.asarray(net['w2'],dtype=np.float32)[None,:]/scale,heads,axis=0),
            'out.bias':np.repeat(np.asarray(net['b2'],dtype=np.float32)/scale,heads)}


def evaluate_full(report,journal,diagnostic):
    import torch
    import numpy as np
    before=verify_inputs();old=module(OLD,'forge_s09_holdout_original',PINS[OLD])
    candidate=module(NEW,'forge_s09_holdout_candidate',PINS[NEW])
    converter=module(STAGED/'forge_sol_S09_buckets_20261026.py','forge_s09_holdout_converter',PINS[STAGED/'forge_sol_S09_buckets_20261026.py'])
    net=converter.inspect_inc(NET)
    if net['heads']!=1:raise ValueError('actual f006 source must be one head')
    models=[]
    for heads in (1,8):
        model=candidate.NNUE(256,qat=True,residual=True,buckets=heads).cpu()
        arrays=model_arrays(net,heads)
        model.load_state_dict({key:torch.from_numpy(value) for key,value in arrays.items()},strict=True)
        model.eval();models.append(model)
    data=old.load_set_mmap([str(SAMPLE/'h000.pos')],str(SAMPLE))
    if data['n']!=ROWS:raise ValueError('full50000 supplied holdout required')
    sums=[0.,0.,0.];count=0;head_counts=np.zeros(8,dtype=np.int64);maximum=0.;control_changed=0
    batches=[]
    with torch.no_grad():
        for begin in range(0,ROWS,BATCH):
            end=min(begin+BATCH,ROWS);idx=np.arange(begin,end,dtype=np.int64)
            codes,stm,wres,score,hce=old.make_batch(data,idx)
            c=torch.from_numpy(codes.astype(np.int64));s=torch.from_numpy(stm.astype(np.int64))
            wr=torch.from_numpy(wres.astype(np.float32));sc=torch.from_numpy(score.astype(np.float32))
            hc=torch.from_numpy(hce.astype(np.float32))*(2.25/400.)
            target=old.targets(sc,s,wr,2.25,0.6)[2]
            left=models[0](c,s,hc);right=models[1](c,s,hc)
            if not (torch.isfinite(left).all() and torch.isfinite(right).all()):raise ValueError('nonfinite actual forward')
            delta=float(torch.max(torch.abs(left-right)));maximum=max(maximum,delta)
            if delta>TOLERANCE:raise ValueError('replicated8 Torch forward exceeds preregistered tolerance')
            for k,pred in enumerate((left,right,hc)):
                sums[k]+=float((torch.sigmoid(pred)-target).double().square().sum())
            head_counts+=np.bincount(np.clip((np.count_nonzero(codes,axis=1)-1)//4,0,7),minlength=8)
            count+=end-begin;batches.append(end-begin)
            if begin==0:
                models[1].out.bias.add_(0.125)
                changed=models[1](c,s,hc)
                control_changed=int(torch.count_nonzero(torch.abs(changed-right)>TOLERANCE))
                models[1].out.bias.sub_(0.125)
                if control_changed!=end-begin:raise ValueError('head-bias positive control did not affect every first-batch logit')
            diagnostic.emit(journal,'HOLDOUT_BATCH',begin=begin,end=end,max_abs_logit_difference=delta)
    if count!=ROWS or int(head_counts.sum())!=ROWS:raise ValueError('holdout count does not close')
    after=verify_inputs()
    if before!=after:raise ValueError('holdout input changed during evaluation')
    report.update(work_complete=True,scope='full supplied synthetic h000 sample only; no real013/014 or gain claim',
        model_source='actual f006 quantized include; existing v3b NNUE forward, QAT and targets',
        torch_version=torch.__version__,numpy_version=np.__version__,private_sys_prefix=sys.prefix,
        rows=count,batch_size=BATCH,batch_count=len(batches),last_batch=batches[-1],dropped_tail_rows=0,
        blend=0.6,k=2.25,head_counts=head_counts.tolist(),max_abs_logit_difference=maximum,
        logit_tolerance=TOLERANCE,first_batch_changed_bias_control_rows=control_changed,
        one_head_MSE=sums[0]/count,eight_replicated_heads_MSE=sums[1]/count,HCE_only_MSE=sums[2]/count,
        input_sha256_before=before,input_sha256_after=after,inputs_unchanged=True,
        peak_self_RSS_linux_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        training_steps=0,GPU_operations=0,exports=0,normal_exit_required=True)


def child(args,diagnostic):
    original=diagnostic._work
    def work(_case,journal,report):
        original('load_only',journal,report)
        report['work_complete']=False
        diagnostic.emit(journal,'FULL_HOLDOUT_BEGIN')
        evaluate_full(report,journal,diagnostic)
        diagnostic.emit(journal,'FULL_HOLDOUT_DONE',rows=report['rows'])
    diagnostic._work=work
    args.toy_protocol_only=False;args.case='full50k_holdout';args.work_seconds=WORK_SECONDS
    return diagnostic.child(args)


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute',action='store_true')
    ap.add_argument('--child',action='store_true');ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--root-authorized-window',required=True);args=ap.parse_args(argv)
    if not args.execute:ap.error('explicit root runtime grant required; source preparation is not execution permission')
    if not args.out.is_absolute() or args.out.resolve()!=args.out or args.out==OUTROOT or not args.out.is_relative_to(OUTROOT):
        ap.error('new exact /tmp S09 native descendant required')
    resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3))
    diagnostic=module(DIAGNOSTIC,'forge_s09_holdout_frozen_diagnostic',DIAGNOSTIC_SHA)
    if args.child:return child(args,diagnostic)
    if sorted(os.sched_getaffinity(0))!=[1] or os.getpriority(os.PRIO_PROCESS,0)!=19:ap.error('CPU1 nice19 required')
    inputs=verify_inputs();args.out.mkdir(exist_ok=False)
    owned=module(OWNED,'forge_s09_holdout_owned',OWNED_SHA)
    command=[str(PRIVATE/'bin/python'),'-B',str(Path(__file__).resolve()),'--execute','--child','--out',str(args.out),
             '--root-authorized-window',args.root_authorized_window]
    env=os.environ.copy();env.pop('LD_PRELOAD',None)
    env.pop('PYTHONPATH',None)
    env.update(LD_LIBRARY_PATH=str(LIBDIR),OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',OMP_NUM_THREADS='1',
               CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1')
    result={'status':'FAIL_FULL_HOLDOUT_PROCESS','controller_sha256':sha(__file__),
        'diagnostic_sha256':DIAGNOSTIC_SHA,'owned_helper_sha256':OWNED_SHA,
        'scope':'actual f006 full50k synthetic-h000 holdout MSE; no optimizer/export/training',
        'root_authorized_window':args.root_authorized_window,'command':command,
        'work_seconds':WORK_SECONDS,'hard_seconds':HARD_SECONDS,'reserved_cleanup_seconds':HARD_SECONDS-WORK_SECONDS,
        'source_inputs_before':inputs,'cpu':[1],'nice':19,'per_process_RLIMIT_AS_bytes':4*1024**3}
    start=time.monotonic();process=None
    try:
        with (args.out/'stdout').open('xb') as so,(args.out/'stderr').open('xb') as se,owned.SubreaperScope():
            process=subprocess.Popen(command,env=env,cwd=HERE,stdout=so,stderr=se,start_new_session=True)
            record=diagnostic.monitor_process(process,args.out,WORK_SECONDS,HARD_SECONDS,start=start)
            reaped,remaining=owned._reap_group(process.pid)
            if remaining:
                more,remaining=owned._close_group(process);reaped+=more
            result.update(observer=record,owned_descendants_reaped=reaped,all_owned_group_members_after_reap=remaining)
        report=json.loads((args.out/'child_result.json').read_text());result['child_result']=report
        result['source_inputs_after']=verify_inputs()
        result['conservative_sum_parent_child_peak_RSS_bytes']=1024*(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss+resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)
        if (record['returncode']==0 and record['stop_reason'] is None and record['observer_error'] is None
                and report.get('work_complete') is True and report.get('rows')==ROWS and not remaining
                and result['source_inputs_after']==inputs
                and result['conservative_sum_parent_child_peak_RSS_bytes']<=4*1024**3):result['status']='PASS_FULL_HOLDOUT_PROCESS'
    except BaseException as exc:
        result['error']=type(exc).__name__+': '+str(exc)
        if process is not None and process.poll() is None:
            owned._close_group(process)
    finally:
        result['elapsed_seconds']=time.monotonic()-start
        (args.out/'forge_sol_S09_full_holdout_result_20261026.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'elapsed_seconds':result['elapsed_seconds'],'error':result.get('error')}))
    return 0 if result['status']=='PASS_FULL_HOLDOUT_PROCESS' else 1


if __name__=='__main__':raise SystemExit(main())
