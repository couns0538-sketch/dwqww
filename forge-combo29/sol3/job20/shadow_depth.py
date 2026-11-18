#!/usr/bin/env python3
"""Capture and independently decode the Job 20 fixed-depth evidence."""

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

import identity


HELPERS = {
    '4a51fe258b610b32055cc7e42614640d9dd0abb8988fdb304d1ad31f7fbcef61',
    '1f7703dae17160651c6a9d163a4af0d14cb34848c7523fa70a50e260c86d93ca',
}
INFO_NODES = re.compile(r'\bnodes (\d+)\b')
MOVE = re.compile(r'bestmove ([a-h][1-8][a-h][1-8][qrbn]?|0000)(?: ponder [a-h][1-8][a-h][1-8][qrbn]?)?')
COUNT = re.compile(r'info string shadow evals (\d+) differ (\d+)')
FAULT = re.compile(r'info string shadow differ fast (-?\d+) ref (-?\d+) fen (.+)')
NET = re.compile(r'\bhidden 768\b.*\bchecksum 30ab43b4ba5db5f3\b.*\bkernel (avx512|avx2|scalar)$')
REFUSAL = re.compile(r'unknown option|invalid value|invalid FEN|\bERROR\b', re.I)
COMMON_FIELDS = ('row', 'fen', 'nodes', 'bestmove', 'last_info', 'bestmove_line', 'stdout_first', 'stdout_last')


def sha(path):
    with path.open('rb') as file:
        return hashlib.file_digest(file, 'sha256').hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def positions(path, depth):
    data = path.read_bytes()
    raw = data.decode('ascii').splitlines()
    expected = 1000 if depth == 9 else 200
    if not data.endswith(b'\n') or b'\r' in data or len(raw) != expected:
        raise ValueError(f'{path} must have {expected} LF-terminated FEN lines')
    if any(len(fen.split()) != 6 for fen in raw):
        raise ValueError(f'{path} must provide six-field FENs as used in the replay')
    return raw


def capture(executable, net, fens, depth, out, timeout):
    with ((out/'engine.stdout.txt').open('xb') as stdout, (out/'engine.stderr.txt').open('x+b') as stderr,
          (out/'engine.commands.txt').open('xb') as commands):
        with identity.EngineRun(executable, stdout, stderr, commands, timeout) as engine:
            engine.set_up(net)
            for index, fen in enumerate(fens, 1):
                engine.send('ucinewgame')
                if engine.ready() != [b'readyok']:
                    raise RuntimeError(f'row {index}: unexpected reset text')
                engine.send(f'position fen {fen}')
                engine.send(f'go depth {depth}')
                engine.receive(lambda line: line.startswith(b'bestmove '), f'bestmove on row {index}')


def expected_commands(net, fens, depth):
    startup = ['uci', *(f'setoption name {name} value {value}' for name,value in identity.PC20.items()),
               f'setoption name NNUEArchFile value {net}', 'setoption name NNUEArch value true', 'isready']
    actions = [cmd for fen in fens for cmd in ('ucinewgame', 'isready', f'position fen {fen}', f'go depth {depth}')]
    return [*startup, *actions, 'quit']


def split_searches(stdout):
    ready_at = [i for i, line in enumerate(stdout) if line == 'readyok']
    if not ready_at:
        raise ValueError('missing setup readyok')
    active = [(i, line) for i, line in enumerate(stdout) if line.startswith('info string NNUE v3 active:')]
    id_lines = [line for line in stdout if line.startswith('id name ')]
    if len(active) != 1 or len(id_lines) != 1 or stdout.count('uciok') != 1:
        raise ValueError('expected one UCI id and one active v3 net line')
    net_index, net_line = active[0]
    marker = NET.search(net_line)
    if marker is None or not stdout.index('uciok') < net_index < ready_at[0]:
        raise ValueError(f'bad net768 activation: {net_line!r}')
    if any(line.startswith('info string shadow ') for line in stdout[: ready_at[0]]):
        raise ValueError('shadow output appeared before the setup barrier')
    starts, ends = ready_at[1:], [*ready_at[2:], len(stdout)]
    return [(a + 1, stdout[a + 1:b]) for a,b in zip(starts, ends, strict=True)], {
        'engine_id': id_lines[0], 'net_activation': net_line, 'kernel': marker[1],
        'readyok': len(ready_at), 'stdout_lines': len(stdout),
    }


def parse_one(start, lines, index, fen, depth, mode, logged):
    best = MOVE.fullmatch(lines[-1]) if lines else None
    if best is None or sum(line.startswith('bestmove ') for line in lines) != 1:
        raise ValueError(f'row {index}: expected one terminal bestmove')
    last = next((line for line in reversed(lines[:-1]) if line.startswith('info depth ')), None)
    nodes = INFO_NODES.search(last or '')
    if nodes is None or not 0 <= int(last.split()[2]) <= depth:
        raise ValueError(f'row {index}: missing or invalid final info depth/nodes')
    result = {'row': index, 'fen': fen, 'nodes': int(nodes[1]), 'bestmove': best[1], 'last_info': last,
              'bestmove_line': lines[-1], 'stdout_first': start+1, 'stdout_last': start+len(lines)}
    shadow = [(i,line) for i,line in enumerate(lines) if line.startswith('info string shadow ')]
    if mode == 'plain':
        if shadow:
            raise ValueError(f'row {index}: a plain run emitted shadow output')
        return result, []
    count = COUNT.fullmatch(lines[-2]) if len(lines) >= 2 else None
    if count is None:
        raise ValueError(f'row {index}: shadow count missing directly before bestmove')
    evals, diff = map(int,count.groups())
    if diff > evals:
        raise ValueError(f'row {index}: more mismatches than shadow evaluations')
    result.update({'shadow_evals':evals,'shadow_differ':diff,'shadow_count_line':lines[-2]})
    faults = []
    for offset, line in shadow:
        if offset == len(lines)-2:
            continue
        parsed = FAULT.fullmatch(line)
        if parsed is None or parsed[1] == parsed[2] or len(parsed[3].split()) != 6:
            raise ValueError(f'row {index}: invalid mismatch diagnostic: {line!r}')
        faults.append({'search_row':index,'root_fen':fen,'raw_stdout_line':start+offset+1,
                       'fast':int(parsed[1]),'reference':int(parsed[2]),'evaluated_fen':parsed[3],
                       'raw_line':line})
    if len(faults) != min(diff, 5 - logged):
        raise ValueError(f'row {index}: wrong number of first-five mismatch records')
    return result, faults


def read_raw(out, net, fens, depth, mode):
    commands = (out/'engine.commands.txt').read_text(encoding='ascii').splitlines()
    expected = expected_commands(net,fens,depth)
    if commands != expected:
        raise ValueError(f'{out}: command sequence differs from pinned PC20 net setup or FEN/depth order')
    stdout = (out/'engine.stdout.txt').read_text(encoding='ascii').splitlines()
    stderr = (out/'engine.stderr.txt').read_text(encoding='ascii').splitlines()
    refused = next((line for line in (*stdout, *stderr) if REFUSAL.search(line)), None)
    if refused:
        raise ValueError(f'{out}: engine refused a command: {refused}')
    cases, metadata = split_searches(stdout)
    if len(cases) != len(fens) or metadata['readyok'] != expected.count('isready'):
        raise ValueError(f'{out}: expected {len(fens)} reset-delimited search blocks, found {len(cases)}')
    rows, notices = [], []
    for index, ((start,seq),fen) in enumerate(zip(cases,fens,strict=True),1):
        row, records = parse_one(start,seq,index,fen,depth,mode,len(notices))
        rows.append(row)
        notices.extend(records)
    metadata.update({'stdin_lines':len(commands), 'searches':len(rows), 'terminal_nodes':sum(r['nodes'] for r in rows),
                     'first_three_nodes':[r['nodes'] for r in rows[:3]],'first_differences':notices})
    if mode=='shadow':
        evals=sum(r['shadow_evals'] for r in rows)
        diff=sum(r['shadow_differ'] for r in rows)
        metadata.update({'shadow_evals':evals,'shadow_differ':diff,
                         'shadow_eval_share':evals / metadata['terminal_nodes'] if metadata['terminal_nodes'] else None})
    return rows, metadata


def labels_compare(a,b):
    if len(a)!=len(b) or [r['fen'] for r in a]!=[r['fen'] for r in b]:
        raise ValueError('cannot compare different position sequences')
    different=[(left,right) for left,right in zip(a,b,strict=True)
               if (left['nodes'],left['bestmove']) != (right['nodes'],right['bestmove'])]
    first = {'row':different[0][0]['row'],'fen':different[0][0]['fen'],
             'baseline':different[0][0],'candidate':different[0][1]} if different else None
    return {'fields':['nodes','bestmove'],'compared':len(a),'equal':len(a)-len(different),
            'differ':len(different),'first_difference':first}


def read_previous(directory, fens, depth):
    report=json.loads((directory/'summary.json').read_text())
    if report['error'] is not None:
        raise ValueError(f'incomplete previous arm: {directory}')
    previous_depth=report.get('depth',9)
    previous_count=report['rows_expected']
    if previous_depth!=depth or previous_count>len(fens):
        raise ValueError(f'previous arm has incompatible position count/depth: {directory}')
    mode=report.get('mode','plain')
    rows, meta=read_raw(directory,report['net_path'],fens[:previous_count],depth,mode)
    with (directory/'rows.tsv').open(encoding='ascii',newline='') as file:
        saved=list(csv.DictReader(file,delimiter='\t'))
    all_fields=COMMON_FIELDS if mode=='plain' else (*COMMON_FIELDS,'shadow_evals','shadow_differ','shadow_count_line')
    if len(saved)!=len(rows) or any(any(new[field] != str(old[field]) for field in all_fields) for old,new in zip(rows,saved,strict=True)):
        raise ValueError(f'previous saved rows differ from independent raw labels: {directory}')
    return rows, meta, report


def write_rows(out, rows):
    with (out/'rows.tsv').open('x',encoding='ascii',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=list(rows[0]),delimiter='\t',lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def run(args):
    exe,net,fixture=(p.resolve(strict=True) for p in (args.engine,args.net,args.fixture))
    helper_hash = sha(Path(identity.__file__))
    if sha(exe)!=args.exe_sha256 or sha(net)!=identity.NET_SHA or helper_hash not in HELPERS:
        raise ValueError('binary, net768 or identity helper hash mismatch')
    fens=positions(fixture,args.depth)
    limit=args.limit if args.limit is not None else len(fens)
    if not 0 < limit <= len(fens) or not 0 < args.timeout <= 300 or '\n' in str(net) or '\r' in str(net):
        raise ValueError('invalid fixture limit, timeout, or multiline net path')
    out=args.output
    out.mkdir(parents=True,exist_ok=False)
    begin=utc()
    info={}; error=None
    try:
        capture(exe,net,fens[:limit],args.depth,out,args.timeout)
        rows,info=read_raw(out,str(net),fens[:limit],args.depth,args.mode)
        write_rows(out,rows)
        if args.baseline is not None:
            past,old,report=read_previous(args.baseline,fens,args.depth)
            info['reference']={'run':str(args.baseline),'exe_sha256':report['exe_sha256'],'kernel':old['kernel'],
                               **labels_compare(past[:limit],rows)}
    except (OSError,RuntimeError,ValueError,KeyError) as exc:
        error=str(exc)
    report={'build':args.build,'exe':str(exe),'exe_sha256':args.exe_sha256,'mode':args.mode,'depth':args.depth,
            'fixture':str(fixture),'fixture_sha256':sha(fixture),'net_path':str(net),'net_sha256':identity.NET_SHA,
            'pc20':identity.PC20,'rows_expected':limit,'started_utc':begin,'finished_utc':utc(),'error':error,
            'runner_sha256':sha(Path(__file__)),'identity_sha256':helper_hash,
            'artifacts_sha256':{p.name:sha(p) for p in sorted(out.iterdir())},**info}
    summary=json.dumps(report,indent=2)+'\n'
    (out/'summary.json').write_text(summary,encoding='utf-8')
    print(summary,end='')
    return int(error is not None)


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    actions=cli.add_subparsers(dest='task',required=True)
    execute=actions.add_parser('run')
    execute.add_argument('--build',required=True)
    execute.add_argument('--exe-sha256',required=True)
    for flag in ('engine','net','fixture','output'):
        execute.add_argument('--'+flag,type=Path,required=True)
    execute.add_argument('--mode',choices=('shadow','plain'),required=True)
    execute.add_argument('--depth',type=int,choices=(9,12),required=True)
    execute.add_argument('--limit',type=int)
    execute.add_argument('--timeout',type=float,default=120)
    execute.add_argument('--baseline',type=Path)
    compare=actions.add_parser('compare')
    compare.add_argument('baseline',type=Path)
    compare.add_argument('candidate',type=Path)
    compare.add_argument('--fixture',type=Path,required=True)
    compare.add_argument('--depth',type=int,choices=(9,12),required=True)
    args=cli.parse_args()
    if args.task=='run':
        return run(args)
    fens=positions(args.fixture,args.depth)
    left,meta_l,summary_l=read_previous(args.baseline,fens,args.depth)
    right,meta_r,summary_r=read_previous(args.candidate,fens,args.depth)
    details=labels_compare(left[:len(right)],right)
    print(json.dumps({**details,'baseline':{'build':summary_l['build'],'kernel':meta_l['kernel'],
                                           'total_nodes':meta_l['terminal_nodes']},
                      'candidate':{'build':summary_r['build'],'kernel':meta_r['kernel'],
                                   'total_nodes':meta_r['terminal_nodes']}},indent=2))
    return 0


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except (OSError,RuntimeError,ValueError,KeyError) as exc:
        print(f'Fixed-depth workload failed: {exc}',file=sys.stderr)
        raise SystemExit(1) from exc
