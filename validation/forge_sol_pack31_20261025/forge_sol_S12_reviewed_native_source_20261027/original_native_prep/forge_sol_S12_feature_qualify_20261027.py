"""ON functional qualification after the same main's FIRST and full OFF Std.
No timing/strength claims; options are sent only while workers are joined.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import os
import re
import resource
import signal
import sys
import time
import forge_sol_S12_bind_arm_20261027 as binding
import forge_sol_S12_helpers_run_20261027 as helper_run
import forge_sol_S12_native_common_20261027 as common

CHESS = Path('/workspace/.cloud-setup/venv/lib/python3.12/site-packages/chess/__init__.py')
CHESS_SHA = '1fde6a8e932508d14b31f6a584497b49c2969fc3c7cdc675347f819f0d667a5b'


def chess_api():
    common.require(common.sha(CHESS) == CHESS_SHA, 'independent legal-move checker changed')
    spec = importlib.util.spec_from_file_location('s12_independent_python_chess',CHESS)
    module = importlib.util.module_from_spec(spec);sys.modules[spec.name] = module;spec.loader.exec_module(module)
    return module


def legal_terminal(lines):
    terminals = [x for x in lines if binding.qual.q.collector.MOVE.fullmatch(x)]
    common.require(len(terminals) == 1, 'exactly one complete bestmove required')
    api = chess_api(); board = api.Board(); words = terminals[0].split()
    move = api.Move.from_uci(words[1]);common.require(move in board.legal_moves, 'illegal bestmove')
    board.push(move)
    if len(words) > 2:
        common.require(len(words) == 4 and words[2] == 'ponder', 'unknown bestmove suffix')
        common.require(api.Move.from_uci(words[3]) in board.legal_moves, 'illegal ponder after actual bestmove')
    return {'bestmove':words[1],'ponder':None if len(words)==2 else words[3],'independent_legality':True}


def diagnostics(lines, active, stats):
    api = helper_run.counter_parser()
    seen = [x for x in lines if x.startswith('info string NnueLazyAcc ')]
    actual = seen.count('info string NnueLazyAcc active')
    values = []
    for line in seen:
        if line == 'info string NnueLazyAcc active':continue
        words = line.removeprefix('info string NnueLazyAcc stats ').split()
        common.require(len(words)==12 and tuple(words[::2])==api.FIELDS
            and all(re.fullmatch('[0-9]+',x) for x in words[1::2]), 'unknown feature diagnostic')
        values.append(api.counters({k:int(v) for k,v in zip(words[::2],words[1::2])}))
    common.require(actual == active and len(values) == stats, 'active-once/stat count differs')
    if values:
        common.require(all(x['evaluations'] > 0 and x['copies_avoided'] == x['zero_dirty_edges'] for x in values)
            and sum(x['copies_avoided'] for x in values) > 0, 'ON path/counter evidence missing')
    return {'active':actual,'stats':values}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute',action='store_true');p.add_argument('--authorization-reference',required=True)
    p.add_argument('--arm',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--cpu',type=int,required=True);p.add_argument('--max-seconds',type=float,default=600)
    a=p.parse_args(argv)
    if not a.execute or not 10<=a.max_seconds<=900:p.error('new finite feature runtime grant required')
    if sorted(os.sched_getaffinity(0)) != [a.cpu] or os.getpriority(os.PRIO_PROCESS,0) != 19:p.error('exact granted core/nice19 required')
    if not common.permitted(a.out) or a.out.exists():p.error('new S12 feature output directory required')
    arm=binding.resolve(a.arm)
    if not (arm['role']=='candidate' and arm['feature']=='ON'):p.error('feature-capable same-main Std qualification required')
    if arm['profile']=='ASAN':
        if resource.getrlimit(resource.RLIMIT_AS)[0] != resource.RLIM_INFINITY:p.error('ASan shadow requires unlimited AS')
        os.environ['ASAN_OPTIONS']='detect_leaks=1:halt_on_error=1';os.environ['UBSAN_OPTIONS']='halt_on_error=1:print_stacktrace=1'
    else:
        for k in ('ASAN_OPTIONS','UBSAN_OPTIONS'):os.environ.pop(k,None)
    for k in ('LSAN_OPTIONS','LD_PRELOAD','LD_LIBRARY_PATH'):os.environ.pop(k,None)
    q=binding.qual.q;shared=q.shared
    signal.signal(signal.SIGTERM,shared._signal_stop);signal.signal(signal.SIGINT,shared._signal_stop)
    a.out.mkdir();start=time.monotonic();guard=binding.qual.previous.RSSGuard(a.out,a.out/'ROOT_STOP',start+a.max_seconds)
    old=shared.boundary_reason;shared.boundary_reason=guard.reason
    row={'schema':'forge.S12.feature_runtime.v1','status':'FAIL','arm':arm,'arm_receipt_sha256':common.sha(a.arm),
        'controller_sha256':common.sha(__file__),'independent_legality_checker_sha256':CHESS_SHA,
        'authorization_reference':a.authorization_reference,'cpu':[a.cpu],'nice':19,'max_seconds':a.max_seconds,
        'checks':[],'nps_or_Elo_claim':False}
    engine=Path(arm['engine'])
    def once(label,commands,predicate):return q.engine_once(engine,a.out,label,commands,predicate,guard)
    try:
        for depth,nodes in ([(11,308972)] if arm['profile']=='ASAN' else list(q.REFS.items())):
            label='ON_bench_'+str(depth)
            lines=once(label,['setoption name NnueLazyAcc value true',f'bench {depth}'],lambda x:bool(q.collector.BENCH.fullmatch(x)))
            result=q.s25.inspect_bench((a.out/(label+'.stdout')).read_bytes(),(a.out/(label+'.stderr')).read_bytes(),0,depth,nodes)
            common.require(result['status']=='PASS','ON fixed reference/EOF differs')
            row['checks'].append({'name':label,'bench':result,'diagnostics':diagnostics(lines,1,8)})
        depth=4 if arm['profile']=='ASAN' else 5
        for name,position,nodes in [('startpos','startpos',197281 if depth==4 else 4865609),('kiwipete','fen '+q.KIWI,4085603 if depth==4 else 193690690)]:
            label='ON_perft_'+name
            lines=once(label,['setoption name NnueLazyAcc value true','position '+position,f'go perft {depth}'],lambda x:bool(re.fullmatch('nodes [0-9]+',x)))
            common.require(lines[-1]=='nodes '+str(nodes),'ON fixed perft differs')
            row['checks'].append({'name':label,'depth':depth,'nodes':nodes,'diagnostics':diagnostics(lines,0,0)})
        process=q.Process(engine,a.out,'ON_repeated_bench_active_once',guard)
        try:
            process.send('setoption name NnueLazyAcc value true')
            for index in range(2):
                process.send('bench 11');lines=process.until(lambda x:bool(q.collector.BENCH.fullmatch(x)))
                common.require(q.collector.BENCH.fullmatch(lines[-1]).group(2)=='308972','repeated bench nodes differ')
                row['checks'].append({'name':'repeated_bench_'+str(index),'diagnostics':diagnostics(lines,1 if index==0 else 0,8)})
            process.close(True)
        except BaseException:process.close(False);raise
        process=q.Process(engine,a.out,'ON_T1_T2_toggle_join_resize',guard)
        try:
            emitted=False
            for threads,enabled in ((1,True),(2,True),(1,False),(2,True)):
                for command in [f'setoption name Threads value {threads}','setoption name Hash value 16',
                    'setoption name OwnBook value false','setoption name UseNNUE value true',
                    'setoption name NnueLazyAcc value '+str(enabled).lower(),'ucinewgame','isready']:process.send(command)
                common.require(process.until(lambda x:x=='readyok')==['readyok'],'unexpected pre-go output')
                process.send('position startpos');process.send('go nodes 10000')
                lines=process.until(lambda x:bool(q.collector.MOVE.fullmatch(x)))
                check=legal_terminal(lines)
                check.update(threads=threads,enabled=enabled,diagnostics=diagnostics(lines,int(enabled and not emitted),int(enabled)))
                emitted |= enabled
                process.send('isready');common.require(process.until(lambda x:x=='readyok')==['readyok'],'late output after worker join')
                row['checks'].append(check)
            process.send('setoption name UseNNUE value false');process.send('setoption name NnueLazyAcc value true')
            process.send('ucinewgame');process.send('position startpos');process.send('go nodes 1000')
            lines=process.until(lambda x:bool(q.collector.MOVE.fullmatch(x)))
            row['checks'].append({'name':'UseNNUE_false','terminal':legal_terminal(lines),'diagnostics':diagnostics(lines,0,0)})
            process.send('setoption name UseNNUE value true');process.send('position startpos');process.send('go infinite');process.send('stop')
            lines=process.until(lambda x:bool(q.collector.MOVE.fullmatch(x)))
            row['checks'].append({'name':'stop_join','terminal':legal_terminal(lines)})
            process.send('isready');common.require(process.until(lambda x:x=='readyok')==['readyok'],'late stop/join output')
            process.close(True)
        except BaseException:process.close(False);raise
        common.require(binding.resolve(a.arm)==arm,'qualified source/core/main changed during ON checks')
        row['status']='PASS'
    except BaseException as error:row['error']=type(error).__name__+': '+str(error)
    finally:
        shared.boundary_reason=old
        ownership=[json.loads(path.read_text()) for path in a.out.glob('*.ownership.json')]
        row['all_engine_groups_closed']=bool(ownership) and all(x['leader_reaped'] and not x['all_group_members_after_reap'] and not x.get('cleanup_error') for x in ownership)
        if not row['all_engine_groups_closed']:row['status']='FAIL'
        row['maximum_observed_owned_RSS_bytes']=guard.maximum_owned_RSS_bytes;row['elapsed_seconds']=time.monotonic()-start
        row['raw_sha256']={path.name:common.sha(path) for path in sorted(a.out.iterdir()) if path.is_file()}
        shared.save_new(a.out/'forge_sol_S12_feature_runtime_result_20261027.json',row)
    print(json.dumps({'status':row['status'],'error':row.get('error')}));return 0 if row['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
