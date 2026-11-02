"""Read-only FD3A5190 UCI/perft/lock-bench compatibility check. UNPROVEN strength."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import time
import chess
from filter_positions import low_priority, sha256
from resource_policy import storage_guard

ENGINE=Path('C:/Users/Administrator/grok-pc/forge_push/bin/forge_ltopgo_x_al1s198_v23.exe')
LOCK='fd3a51903e73dc1fa20263f1dcc7a4eec506592e9f25e50b8f8739ca36873072'
PINS={11:312866,13:862329,16:3024920,20:12389307,22:34048354}


def perft2(board):
    count=0
    for move in list(board.legal_moves):
        board.push(move);count+=board.legal_moves.count();board.pop()
    return count


def run(output, sample):
    output=Path(output);storage_guard(output);output.mkdir()
    if sha256(ENGINE)!=LOCK:raise ValueError('wrong lock executable')
    fens=[]
    with Path(sample).open(encoding='utf-8') as fh:
        for _,line in zip(range(24),fh):fens.append(json.loads(line)['fen'])
    fens += [chess.STARTING_FEN,'r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1',
             '4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 81','4k3/P7/8/8/8/8/8/4K3 w - - 0 81',
             '4k3/8/8/8/8/8/4r3/4K3 w - - 0 1','7k/6Q1/6K1/8/8/8/8/8 b - - 0 1',
             '7k/5Q2/6K1/8/8/8/8/8 b - - 0 1']
    fens += [chess.Board(fen).mirror().fen(en_passant='fen') for fen in list(fens)]
    expected=[perft2(chess.Board(fen)) for fen in fens]
    commands=['uci','setoption name Threads value 1','setoption name Hash value 16',
              'setoption name OwnBook value false','setoption name UseNNUE value true','isready']
    for fen in fens:commands += ['position fen '+fen,'go perft 2']
    commands += ['bench '+str(depth) for depth in PINS]+['quit']
    request='\n'.join(commands)+'\n'
    (output/'stdin.txt').write_text(request,encoding='utf-8')
    started=time.perf_counter()
    # communicate's timeout owns/terminates only this child via subprocess.run.
    try:
        completed=subprocess.run([str(ENGINE)],input=request,text=True,capture_output=True,
                                 cwd=output,timeout=120,creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)
    except subprocess.TimeoutExpired as exc:
        # TimeoutExpired may carry bytes even when text=True was requested.
        for name, captured in [('stdout.log', exc.stdout), ('stderr.log', exc.stderr)]:
            text = captured.decode('utf-8', errors='replace') if isinstance(captured, bytes) else captured or ''
            (output/name).write_text(text, encoding='utf-8')
        receipt = dict(status='FAIL', reason='engine timeout', timeout_seconds=exc.timeout,
                       engine=str(ENGINE), sha256=sha256(ENGINE), expected_sha256=LOCK,
                       elapsed_seconds=time.perf_counter()-started, strength='UNPROVEN')
        (output/'report.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
        raise
    (output/'stdout.log').write_text(completed.stdout,encoding='utf-8')
    (output/'stderr.log').write_text(completed.stderr,encoding='utf-8')
    actual=[int(n) for n in re.findall(r'^nodes (\d+)\s*$',completed.stdout,re.M)]
    bench={int(d):int(n) for d,n in re.findall(r'bench depth (\d+) nodes (\d+)',completed.stdout)}
    report={'status':'PASS' if completed.returncode==0 and actual==expected and bench==PINS else 'FAIL',
            'engine':str(ENGINE),'sha256':sha256(ENGINE),'expected_sha256':LOCK,
            'exit_code':completed.returncode,'elapsed_seconds':time.perf_counter()-started,
            'threads':1,'hash_mb':16,'UseNNUE':True,'priority':'BelowNormal',
            'option_basis':'Recorded lock OFF transcript uses default UseNNUE=true; OFF refers to candidate options, not disabling NNUE',
            'positions':len(fens),'fens':fens,'expected_perft2':expected,'actual_perft2':actual,
            'bench_expected':PINS,'bench_actual':bench,'sample_sha256':sha256(sample),
            'reference':'python-chess legal-move tree; perft checks state/move compatibility, not eval',
            'strength':'UNPROVEN'}
    if report['sha256']!=LOCK:report['status']='FAIL'
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    if report['status']!='PASS':raise ValueError('native Forge smoke failed; see preserved report')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('sample',type=Path)
    a=p.parse_args();low_priority();print(json.dumps(run(a.output,a.sample),indent=2))
