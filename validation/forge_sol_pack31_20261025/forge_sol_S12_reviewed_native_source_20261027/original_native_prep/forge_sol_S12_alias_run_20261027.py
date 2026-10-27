"""Bounded baseline/OFF/ON actual-Worker parity; reuses original S09 input.
No scalar/material-key producer and no invented million-position S12 gate.
"""
from pathlib import Path
import argparse
import json
import os
import re
import shutil
import signal
import time
import forge_sol_S12_alias_transport_20261027 as wire
import forge_sol_S12_helpers_build_20261027 as helpers
import forge_sol_S12_native_common_20261027 as common

SEALER=Path('/workspace/forge-pack24-20261026/S09_TORCHRAM_20261026/forge_sol_S09_torchram_probe_v2_20261026.py')


def corpus(path, allow_rewrapped):
    value=json.loads(Path(path).read_text())
    wanted={'count':1000000,'unique_position_fields':1000000,'raw_size':52261200,
            'raw_sha256':'0d6594d3fb7dba38064eddc2a0f673d23c6551c052186cc5989047b86e762eb6'}
    common.require(all(value.get(k)==v for k,v in wanted.items()), 'not the sealed original S09 corpus')
    original=value.get('gzip_size')==8950562 and value.get('gzip_sha256')=='e06bf2de476f1819ab098b854d718ff1b528c49c60ee9edbfd82206b99798a42'
    common.require(original or allow_rewrapped, 'same-raw rewrap requires explicit recovery flag')
    common.require(type(value.get('gzip_size')) is int and value['gzip_size']>0
        and re.fullmatch('[0-9a-f]{64}',value.get('gzip_sha256','')), 'actual compressed metadata missing')
    sealer=common.load_pinned('s12_original_S09_corpus_sealer',SEALER)
    fd=sealer.sealed_memfd_from_gzip(value['gzip'],compressed_size=value['gzip_size'],
        compressed_sha256=value['gzip_sha256'],raw_size=value['raw_size'],raw_sha256=value['raw_sha256'])
    return value,fd


def require_pair(left,right):
    common.require(left['base']==right['base'] and left['profile']==right['profile']=='Release'
        and left['role']=='baseline' and right['role']=='candidate' and right['feature']=='ON',
        'distinct same-base pristine/feature-capable Release arms required')
    common.require(left['core_sha256']!=right['core_sha256'] and left['source']!=right['source'],
                   'baseline-vs-itself cannot prove candidate parity')


def summary_pair(off,on):
    for key in ('positions','selected_nulls','legal_children','nulls','verified_evaluations',
                'fresh_mismatches','state_mismatches','refreshes','zero_dirty_edges','evaluations'):
        common.require(off[key]==on[key], 'actual traversal/evaluation/refresh count differs: '+key)
    common.require(off['updates']==on['updates']+on['copies_avoided'], 'nonempty update accounting differs')
    return {'status':'PASS_MEASURED_ALIAS_ACCOUNTING','OFF':off,'ON':on,'speed_or_Elo_claim':False}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute',action='store_true');p.add_argument('--authorization-reference',required=True)
    for name in ('baseline-helpers','candidate-helpers','corpus-manifest','out'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--allow-rewrapped-corpus',action='store_true');p.add_argument('--cpu',type=int,required=True)
    p.add_argument('--max-seconds',type=float,default=600);p.add_argument('--arm-seconds',type=float,default=180)
    a=p.parse_args(argv)
    if not a.execute or not 30<=a.max_seconds<=900 or not 1<=a.arm_seconds<=300:p.error('new bounded serial parity grant required')
    if sorted(os.sched_getaffinity(0)) != [a.cpu] or os.getpriority(os.PRIO_PROCESS,0) != 19:p.error('exact granted core/nice19 required')
    if not common.permitted(a.out) or a.out.exists():p.error('new S12 parity output directory required')
    baseline,left=helpers.verify(a.baseline_helpers);candidate,right=helpers.verify(a.candidate_helpers)
    require_pair(left,right)
    common.require(common.sha(common.HERE/'forge_sol_S12_alias_oracle_20261027.cpp')==wire.ORACLE_SHA,
                   'bounded actual-Worker producer changed')
    def helper(row,mode):return Path(next(x['path'] for x in row['helpers'] if x['kind']=='alias' and x['mode']==mode))
    selected=[('baseline',helper(baseline,0),0),('candidate_OFF',helper(candidate,1),1),('candidate_ON',helper(candidate,2),2)]
    common.require(len({os.stat(path).st_ino for _,path,_ in selected})==3, 'distinct helper executables/inodes required')
    common.require(shutil.disk_usage(common.TMP).free>=3*(36+8192*2068)+128*1048576,
                   'three raw-equivalent streams plus128MiB capacity required')
    # Runtime is separate from the AS-capped compiler process. No test is timed
    # for speed; the budget limits only this finite correctness experiment.
    for key in ('ASAN_OPTIONS','UBSAN_OPTIONS','LSAN_OPTIONS','LD_PRELOAD','LD_LIBRARY_PATH'):os.environ.pop(key,None)
    owned=common.old_builder().owned
    signal.signal(signal.SIGTERM,owned._signal_stop);signal.signal(signal.SIGINT,owned._signal_stop)
    a.out.mkdir();start=time.monotonic();guard=helpers.binding.qual.previous.RSSGuard(a.out,a.out/'ROOT_STOP',start+a.max_seconds)
    def stop(job=None,end=None):
        if owned._STOP_REQUESTED:return 'EXTERNAL_STOP'
        return guard.reason(job,end)
    row={'schema':'forge.S12.actual_alias_parity.v1','status':'FAIL','baseline_arm':left,'candidate_arm':right,
        'controller_sha256':common.sha(__file__),'producer_sha256':wire.ORACLE_SHA,'transport_sha256':common.sha(wire.__file__),
        'authorization_reference':a.authorization_reference,'cpu':[a.cpu],'nice':19,'max_seconds':a.max_seconds,
        'arm_seconds':a.arm_seconds,'positions_per_arm':8192,'transition_roots_per_arm':1024,
        'worker_constructions_per_arm':1,'history_clears_after_construction':0,'arms':{},'nps_or_Elo_claim':False,
        'S11_material_key_producer_reused':False,'corpus_regenerations':0}
    fd=None
    try:
        value,fd=corpus(a.corpus_manifest,a.allow_rewrapped_corpus)
        row['corpus_manifest_sha256']=common.sha(a.corpus_manifest);row['original_corpus']=value
        row['intentional_scope']='first8192 lines of original1M corpus; extra transitions at first1024 roots; not1M coverage'
        for label,exe,mode in selected:
            common.require(helpers.verify(a.baseline_helpers)[0]==baseline and helpers.verify(a.candidate_helpers)[0]==candidate,
                           'helper/source/core bindings changed before next arm')
            available=min(a.arm_seconds,guard.deadline-time.monotonic()-3)
            if available<1:raise TimeoutError('finite total budget exhausted')
            row['arms'][label]=wire.capture_arm(exe,fd,input_bytes=value['raw_size'],input_sha256=value['raw_sha256'],
                positions=8192,child_limit=1024,expected_mode=mode,out=a.out,label=label,seconds=available,stop=stop,chunk_records=2048)
        for first,second in (('baseline','candidate_OFF'),('candidate_OFF','candidate_ON')):
            row[first+'_vs_'+second]=wire.compare_chunked(a.out/(first+'.stdout.chunks.json'),a.out/(second+'.stdout.chunks.json'),
                8192,1024,stop=stop,left_capture=row['arms'][first],right_capture=row['arms'][second])
        row['actual_counters']=summary_pair(row['arms']['candidate_OFF']['summary'],row['arms']['candidate_ON']['summary'])
        common.require(helpers.verify(a.baseline_helpers)[0]==baseline and helpers.verify(a.candidate_helpers)[0]==candidate,
                       'qualified source/core changed during parity')
        row['status']='PASS_BOUNDED_ACTUAL_WORKER_PARITY'
    except BaseException as error:row['error']=type(error).__name__+': '+str(error)
    finally:
        if fd is not None:os.close(fd)
        row['maximum_observed_owned_RSS_bytes']=guard.maximum_owned_RSS_bytes;row['elapsed_seconds']=time.monotonic()-start
        row['raw_sha256']={path.name:common.sha(path) for path in sorted(a.out.iterdir()) if path.is_file()}
        owned.save_new(a.out/'forge_sol_S12_alias_parity_result_20261027.json',row)
    print(json.dumps({'status':row['status'],'error':row.get('error')}));return 0 if row['status']=='PASS_BOUNDED_ACTUAL_WORKER_PARITY' else 1


if __name__=='__main__':raise SystemExit(main())
