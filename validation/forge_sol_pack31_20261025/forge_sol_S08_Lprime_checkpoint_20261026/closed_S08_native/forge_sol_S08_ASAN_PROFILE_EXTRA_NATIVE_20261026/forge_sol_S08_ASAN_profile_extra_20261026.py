#!/usr/bin/env python3
"""Bounded actual profile-ON sanitizer supplement; fixed work, no NPS claim."""
import argparse, datetime, hashlib, importlib.util, json, os, pathlib, re, shutil, time
import chess

HERE=pathlib.Path(__file__).resolve().parent
BINARY=HERE/'forge_sol_S08_ASAN_v2_window1_20261026/build/forge'
BINARY_SHA='4f6b1b5e919b43e691a45f8effbe7c5a419581e9a27d1ecaa39788f0df7475c5'
COLLECTOR=HERE/'forge_sol_S08_collect_profiles_20261026.py'
COLLECTOR_SHA='bf5d18d25bc1fb342c06092a36bfbac2b4717dc8a3f3c8f5cac34add3c3b1143'
FREEZE=HERE/'forge_sol_S08_TLS_v2_source_freeze_20261026.json'
FREEZE_SHA='2923e86c186e357aac177e453f5745993d0839af02422d2622ff9f80dffae5ad'
WAC=pathlib.Path('/workspace/forge-sol-next-20261024/int16-review/wac300.epd')
WAC_SHA='9bfb7b42cf5bbc7f3d60ff767ca3be460e0ae4d9110ef9a71ddf0bd7071d4d46'
FULL=HERE/'forge_sol_S08_ASAN_FULL_NATIVE_20261026/forge_sol_S08_ASAN_full_qualification_v2_result_20261026.json'
KIWI='r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1'

def sha(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def snapshot(source):
    rows={}
    for p in sorted(source.rglob('*')):
        if p.is_symlink():raise ValueError('source symlink')
        if p.is_file():rows[str(p.relative_to(source))]=sha(p)
    return rows

def legal_bestmove(fen,lines):
    terminals=[line for line in lines if line.startswith('bestmove ')]
    if len(terminals)!=1:raise ValueError('one bestmove required')
    board=chess.Board(fen);token=terminals[0].split()[1]
    if token=='0000':
        if any(board.legal_moves):raise ValueError('null bestmove in nonterminal board')
    else:
        move=chess.Move.from_uci(token)
        if move not in board.legal_moves:raise ValueError('illegal bestmove '+token)
    return token

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true');parser.add_argument('--output',required=True,type=pathlib.Path)
    args=parser.parse_args(argv)
    if not args.execute:parser.error('explicit --execute required')
    if sorted(os.sched_getaffinity(0))!=[4] or os.getpriority(os.PRIO_PROCESS,0)!=19:parser.error('use CPU4 nice19')
    if os.environ.get('ASAN_OPTIONS')!='detect_leaks=1:halt_on_error=1' or os.environ.get('UBSAN_OPTIONS')!='halt_on_error=1:print_stacktrace=1':parser.error('requires enabled ASAN/UBSAN+LSan')
    for p,expected in ((BINARY,BINARY_SHA),(COLLECTOR,COLLECTOR_SHA),(FREEZE,FREEZE_SHA),(WAC,WAC_SHA)):
        if sha(p)!=expected:raise ValueError('input hash mismatch '+str(p))
    full=json.loads(FULL.read_text())
    if full['status']!='PASS' or len(full['ctest_proof']['test_cases'])!=15 or any(r['failed'] for r in full['ctest_proof']['test_cases']):raise ValueError('requires complete full sanitizer PASS')
    freeze=json.loads(FREEZE.read_text());source=pathlib.Path(freeze['source'])
    if snapshot(source)!=freeze['source_sha256']:raise ValueError('frozen source changed')
    spec=importlib.util.spec_from_file_location('s08_profile_transport',COLLECTOR)
    api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
    out=api.exclusive_directory(args.output)
    started=time.monotonic();deadline=started+600;minimum_free=shutil.disk_usage(out).free
    record={'status':'RUNNING','no_speed_or_strength_claim':True,'binary_sha256_before':BINARY_SHA,'source_freeze_sha256':FREEZE_SHA,'collector_sha256':COLLECTOR_SHA,'full_ctest_receipt_sha256':sha(FULL),'wac_sha256':WAC_SHA,'max_total_seconds':600,'max_operation_seconds':120,'affinity':[4],'nice':19,'sanitizer_env':{key:os.environ[key] for key in ('ASAN_OPTIONS','UBSAN_OPTIONS')},'searches':[],'perfts':[]}
    result=out/'forge_sol_S08_ASAN_profile_extra_result_20261026.json'
    def save():result.write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
    def guard():
        nonlocal minimum_free
        free=shutil.disk_usage(out).free;minimum_free=min(minimum_free,free)
        if free<8*1048576:raise RuntimeError('free disk below8MiB')
        if time.monotonic()>=deadline:raise TimeoutError('total600seconddeadline')
    class GuardedProcess(api._Process):
        def _pump(self,wait=.05):guard();return super()._pump(wait)
    process=None
    def until(predicate):
        guard();process.timeout=min(120,max(.1,deadline-time.monotonic()));return process.until(predicate)
    def fence():
        process.send('isready');tail=until(lambda line:line=='readyok')
        if tail!=['readyok']:raise ValueError('unexpected output before ready fence')
        return tail
    save()
    try:
        guard();process=GuardedProcess([str(BINARY)],out,'profile_on',120,1500000)
        process.send('uci');uci=until(lambda line:line=='uciok')
        if 'option name Profile type check default false' not in uci:raise ValueError('profile option missing')
        for name,value in [('Threads','1'),('Hash','16'),('OwnBook','false'),('Profile','true')]:process.send('setoption name '+name+' value '+value)
        fence()
        process.send('bench_prof 11');lines=until(lambda line:bool(api.BENCH.fullmatch(line)))
        match=api.BENCH.fullmatch(lines[-1])
        if (int(match[1]),int(match[2]))!=(11,308972):raise ValueError('bench11pin')
        packet=api.parse_packet(lines+fence(),terminal='bench');api.verify_profile_work(packet,expected_nodes=308972)
        if packet['overflow'] or len(packet['counters'])!=55:raise ValueError('bench profile packet invalid')
        record['bench_prof11']={'nodes':308972,'packet':packet};save()
        canonical=api.corpus_metadata([WAC],required=300)['positions']
        cases=[(1,row) for row in canonical[:25]]+[(2,canonical[i]) for i in (0,8,17)]
        previous_threads=1
        for threads,row in cases:
            guard()
            if threads!=previous_threads:
                process.send('setoption name Threads value '+str(threads));fence();previous_threads=threads
            process.send('ucinewgame');process.send('setoption name Clear Hash');fence()
            process.send('position fen '+row['fen']);process.send('go nodes 20000')
            lines=until(lambda line:line.startswith('bestmove '));tail=fence()
            packet=api.parse_packet(lines+tail)
            if packet['overflow']:raise ValueError('profile counter overflow')
            if threads==1:api.verify_profile_work(packet,node_limit=20000)
            best=legal_bestmove(row['fen'],lines)
            record['searches'].append({'id':row['id'],'fen':row['fen'],'threads':threads,'requested_nodes':20000,'parallel_budget_ceiling_asserted':threads==1,'bestmove':best,'legal_bestmove':True,'packet':packet});save()
        for name,fen,expected in [('startpos',chess.STARTING_FEN,197281),('kiwipete',KIWI,4085603)]:
            process.send('position fen '+fen);process.send('go perft 4')
            lines=until(lambda line:bool(re.fullmatch(r'nodes \d+',line)));fence()
            observed=int(lines[-1].split()[1]);divides=[]
            for line in lines[:-1]:
                m=re.fullmatch(r'([a-h][1-8][a-h][1-8][nbrq]?): (\d+)',line)
                if m is None:raise ValueError('unexpected perft output')
                divides.append(int(m[2]))
            if observed!=expected or sum(divides)!=expected:raise ValueError('perft4 mismatch '+name)
            record['perfts'].append({'name':name,'depth':4,'nodes':observed,'expected':expected,'divide_sum':sum(divides)});save()
        process.timeout=min(120,max(.1,deadline-time.monotonic()));process.close(True);process=None
        if sha(BINARY)!=BINARY_SHA or snapshot(source)!=freeze['source_sha256']:raise ValueError('source/binary changed')
        record['binary_sha256_after']=sha(BINARY);record['source_unchanged']=True;record['status']='PASS'
    except Exception as exc:record.update(status='FAIL',failure=type(exc).__name__+': '+str(exc))
    finally:
        if process is not None:
            try:process.close(False)
            except Exception as exc:record['cleanup_failure']=type(exc).__name__+': '+str(exc)
        record.update(elapsed_seconds=time.monotonic()-started,minimum_free_bytes=minimum_free,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),controller_sha256=sha(__file__))
        save()
    print(json.dumps({'status':record['status'],'searches':len(record['searches']),'perfts':record['perfts'],'output':str(out)}),flush=True)
    return 0 if record['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
