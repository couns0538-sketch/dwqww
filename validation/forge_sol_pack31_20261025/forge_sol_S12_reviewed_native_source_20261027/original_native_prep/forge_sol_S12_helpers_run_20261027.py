"""Finite regression or real bench-counter runs; source-only until new grant.
Compiler AS cap is intentionally never inherited by an ASan runtime.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import os
import re
import resource
import signal
import time
import forge_sol_S12_native_common_20261027 as common
import forge_sol_S12_helpers_build_20261027 as helpers


def regression(text, stderr, returncode, baseline):
    common.require(not stderr, 'native regression stderr is not empty (including sanitizer errors)')
    lines = text.splitlines()
    common.require(bool(lines), 'missing native regression output')
    tail = re.fullmatch(r'CHECKS ([0-9]+) FAILURES ([0-9]+)',lines[-1])
    common.require(tail is not None and int(tail[1]) == len(lines)-1, 'truncated/extra regression records')
    common.require(all(x.startswith(('PASS ','FAIL ')) for x in lines[:-1]), 'unknown regression output')
    failures = [x[5:] for x in lines[:-1] if x.startswith('FAIL ')]
    common.require(int(tail[2]) == len(failures) and len(lines) > 100, 'regression count accounting incomplete')
    required = {
        'actual opt-in implementation present (must fail on base)',
        'actual null accumulator copy avoided (must fail on base)',
        'null uses root physical owner', 'alias chain is flattened to physical root',
        'real skip counter changed (must fail on base)',
    }
    for fixture in ('en passant','white castle','black castle','white underpromotion','black underpromotion','capture underpromotion'):
        required |= {fixture+' null cache remains unmaterialized',fixture+' null borrows physical real predecessor'}
    if baseline:
        common.require(type(returncode) is int and returncode == 1 and len(failures) == len(required)
            and set(failures) == required, 'baseline RED must fail only the exact real alias/copy assertions; parity is never waived')
    else:
        common.require(type(returncode) is int and returncode == 0 and not failures, 'candidate alias/parity regression failed')
    return {'status':'PASS_BASELINE_RED_CONTROL' if baseline else 'PASS_ACTUAL_WORKER_REGRESSION',
        'checks':int(tail[1]),'observed_failures':failures,'returncode':returncode,
        'waived_parity_failures':0,'native_not_mocked':True}


def counter_parser():
    path = common.HERE/'inputs/forge_sol_S12_benchcounter_records_20261026.py'
    common.require(common.sha(path) == '8ab292b042318c43ed204430a19fee01802e9efeea8347eb14104cf1c7b2fe2a',
                   'frozen bench-counter parser changed')
    spec=importlib.util.spec_from_file_location('s12_frozen_counter_parser',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true');parser.add_argument('--authorization-reference',required=True)
    parser.add_argument('--helper-receipt',type=Path,required=True)
    parser.add_argument('--operation',choices=('regression','counters'),required=True)
    parser.add_argument('--out',type=Path,required=True);parser.add_argument('--cpu',type=int,required=True)
    parser.add_argument('--max-seconds',type=float,default=300)
    args=parser.parse_args(argv)
    if not args.execute or not 10<=args.max_seconds<=900:parser.error('fresh bounded helper runtime grant required')
    if sorted(os.sched_getaffinity(0)) != [args.cpu] or os.getpriority(os.PRIO_PROCESS,0) != 19:
        parser.error('exact granted core/nice19 required')
    if not common.permitted(args.out) or args.out.exists():parser.error('new S12 helper runtime directory required')
    built,arm=helpers.verify(args.helper_receipt)
    if args.operation=='counters' and not (arm['role']=='candidate' and arm['feature']=='ON' and arm['profile']=='Release'):
        parser.error('five-depth counters require qualified feature-capable Release candidate')
    if arm['profile']=='ASAN':
        if resource.getrlimit(resource.RLIMIT_AS)[0] != resource.RLIM_INFINITY:parser.error('ASan shadow requires unlimited AS')
        os.environ['ASAN_OPTIONS']='detect_leaks=1:halt_on_error=1';os.environ['UBSAN_OPTIONS']='halt_on_error=1:print_stacktrace=1'
    else:
        for k in ('ASAN_OPTIONS','UBSAN_OPTIONS'):os.environ.pop(k,None)
    for k in ('LSAN_OPTIONS','LD_PRELOAD','LD_LIBRARY_PATH'):os.environ.pop(k,None)
    owned=common.old_builder().owned
    signal.signal(signal.SIGTERM,owned._signal_stop);signal.signal(signal.SIGINT,owned._signal_stop)
    args.out.mkdir();start=time.monotonic()
    guard=helpers.binding.qual.previous.RSSGuard(args.out,args.out/'ROOT_STOP',start+args.max_seconds)
    previous=owned.boundary_reason
    def boundary(job=None,end=None):
        if owned._STOP_REQUESTED:return 'EXTERNAL_STOP'
        return guard.reason(job,end)
    owned.boundary_reason=boundary
    row={'schema':'forge.S12.helpers_runtime.v1','status':'FAIL','operation':args.operation,
        'helper_receipt':str(args.helper_receipt),'helper_receipt_sha256':common.sha(args.helper_receipt),
        'arm':arm,'controller_sha256':common.sha(__file__),'authorization_reference':args.authorization_reference,
        'cpu':[args.cpu],'nice':19,'max_seconds':args.max_seconds,'commands':[],'checks':[],'nps_or_Elo_claim':False,
        'ASAN_address_space_limit':resource.getrlimit(resource.RLIMIT_AS)[0],
        'runtime_environment':{k:os.environ.get(k) for k in ('ASAN_OPTIONS','UBSAN_OPTIONS','LSAN_OPTIONS')}}
    def run(argv,label,allowed):
        result=owned.run_owned(argv,args.out,label,args.out,guard.deadline);row['commands'].append(result)
        common.require(type(result.get('returncode')) is int and result['returncode'] in allowed
            and result.get('leader_reaped') is True and result.get('all_group_members_after_reap') == []
            and not result.get('stop_reason') and not result.get('error'),'native helper failed/open: '+label)
        return result
    try:
        if args.operation=='regression':
            item=next(x for x in built['helpers'] if x['kind']=='regression')
            result=run([item['path']],'actual_Worker_regression',{1} if arm['role']=='baseline' else {0})
            row['checks'].append(regression((args.out/'actual_Worker_regression.stdout').read_text(),
                (args.out/'actual_Worker_regression.stderr').read_bytes(),result['returncode'],arm['role']=='baseline'))
        else:
            item=next(x for x in built['helpers'] if x['kind']=='counters')
            binding_path=common.HERE/'inputs/forge_sol_S12_benchcounter_source_binding_20261026.json'
            common.require(common.sha(binding_path)=='cf0889f4b62773430ee0184fb8a43bff4aacaf69c76b74c9e782c23834ebca28',
                           'frozen actual counter source binding changed')
            binding=json.loads(binding_path.read_text())
            api=counter_parser()
            for depth in api.REFERENCES:
                parsed={}
                for mode in ('OFF','ON'):
                    label='counter_d'+str(depth)+'_'+mode
                    run([item['path'],str(depth),mode],label,{0})
                    common.require(not (args.out/(label+'.stderr')).read_bytes(),'counter helper stderr is not empty')
                    parsed[mode]=api.validate((args.out/(label+'.stdout')).read_text(),binding,mode,depth)
                check=api.compare(parsed['OFF'],parsed['ON'])
                # The original engine records aggregate refreshes. This split
                # is a source-derived invariant, not separate measured counters.
                check['root_refreshes_source_derived']=8
                check['fallback_refreshes_source_derived']={mode:parsed[mode]['totals']['refreshes']-8 for mode in ('OFF','ON')}
                check['refresh_share_measured']={mode:{'numerator':parsed[mode]['totals']['refreshes'],
                    'denominator':parsed[mode]['totals']['evaluations']} for mode in ('OFF','ON')}
                row['checks'].append(check)
        common.require(helpers.verify(args.helper_receipt)[0] == built, 'source/core/helpers changed during native runtime')
        row['status']='PASS'
    except BaseException as error:row['error']=type(error).__name__+': '+str(error)
    finally:
        owned.boundary_reason=previous
        row['maximum_observed_owned_RSS_bytes']=guard.maximum_owned_RSS_bytes
        row['elapsed_seconds']=time.monotonic()-start
        row['raw_sha256']={p.name:common.sha(p) for p in sorted(args.out.iterdir()) if p.is_file()}
        owned.save_new(args.out/'forge_sol_S12_helpers_runtime_result_20261027.json',row)
    print(json.dumps({'status':row['status'],'error':row.get('error')}))
    return 0 if row['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
