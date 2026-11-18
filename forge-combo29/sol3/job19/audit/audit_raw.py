#!/usr/bin/env python3
"""Independently stream-check Job 19 W1 and W3 raw transcripts."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re


ROOT = Path('/workspace/work/forge-sol3/forge-combo29/sol3')
EXPECTED = '3c1b17332eca46a912f572eae8197324f466a8e2f909653104c427457ffb0521'
BAD = re.compile(r'unknown option|invalid value|invalid FEN|\bERROR\b', re.I)
MOVE = r'[a-h][1-8][a-h][1-8][qrbn]?'
BEST = re.compile(rf'bestmove ({MOVE}|0000)(?: ponder {MOVE})?')
EVAL = re.compile(r'info string eval hce 0 nnue (-?\d+) total (-?\d+)(?: incheck 1)?')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_commands(path, positions, action):
    archive = (ROOT/'job13/A1/engine.commands.txt').read_text().splitlines()
    pc20 = archive[:archive.index('isready')]
    actual = path.read_text().splitlines()
    net_at = len(pc20)
    expected_net = 'setoption name NNUEArchFile value /workspace/work/sol3-job4-net/net768.fnn3'
    assert actual[:net_at] == pc20
    assert actual[net_at:net_at+3] == [expected_net,'setoption name NNUEArch value true','isready']
    expected_cases = []
    for fen in positions:
        expected_cases.extend(('ucinewgame','isready',f'position fen {fen}',action))
        if action == 'eval': expected_cases.append('isready')
    assert actual[net_at+3:] == [*expected_cases, 'quit']
    return len(actual), actual.count('isready')


def depth_rows(raw):
    start = None
    last = None
    for line_no, output in raw:
        if output == 'readyok':
            assert start is None
            start = line_no + 1
        elif output.startswith('info depth '):
            assert start is not None
            last = output
        else:
            finish = BEST.fullmatch(output)
            if finish is None:
                assert start is not None and output.startswith('info '), (line_no, output)
                continue
            assert last is not None and start is not None
            fields = last.split()
            assert 0 <= int(fields[2]) <= 9
            nodes = int(fields[fields.index('nodes')+1])
            assert nodes >= 0
            yield {'stdout_first': start,'stdout_last': line_no,'bestmove': finish[1], 'nodes': nodes,
                   'last_info': last, 'bestmove_line': output}
            start = last = None
    assert start is None and last is None


def eval_rows(raw):
    remaining = iter(raw)
    for _, ready in remaining:
        assert ready == 'readyok'
        line_no, output = next(remaining)
        row = EVAL.fullmatch(output)
        assert row and int(row[1]) == int(row[2])
        assert next(remaining)[1] == 'readyok'
        yield {'stdout_first': line_no,'stdout_last': line_no,'eval_line': output}


def read_arm(root, positions, action, wanted_kernel):
    summary = json.loads((root/'summary.json').read_text())
    assert summary['error'] is None and summary['rows_expected'] == len(positions)
    commands = root/'engine.commands.txt'
    raw = root/'engine.stdout.txt'
    stderr = root/'engine.stderr.txt'
    stdin_lines, ready_count = check_commands(commands,positions,action)
    native = raw.read_text(encoding='ascii').splitlines()
    assert not any(BAD.search(s) for s in native)
    assert not BAD.search(stderr.read_text())
    assert native.count('readyok') == ready_count and native.count('uciok') == 1
    start = native.index('readyok')
    active = [(i,s) for i,s in enumerate(native) if s.startswith('info string NNUE v3 active:')]
    assert len(active) == 1 and native.index('uciok') < active[0][0] < start
    marker = active[0][1]
    assert ' hidden 768 ' in marker and ' checksum 30ab43b4ba5db5f3 ' in marker
    assert marker.endswith(f' kernel {wanted_kernel}')
    after_setup = enumerate(native[start+1:],start+2)
    decoded = list(eval_rows(after_setup) if action=='eval' else depth_rows(after_setup))
    assert len(decoded)==len(positions)
    rows = [{'row': n,'fen': fen,**row} for n,(fen,row) in enumerate(zip(positions,decoded,strict=True),1)]
    with (root/'rows.tsv').open() as recorded:
        saved = list(csv.DictReader(recorded,delimiter='\t'))
    assert [{k:str(v) for k,v in row.items()} for row in rows]==saved
    if action == 'eval':
        assert (root/'eval.txt').read_text()==''.join(row['eval_line']+'\n' for row in rows)
    metadata = {'run': str(root), 'build_sha256': summary['exe_sha256'], 'kernel': wanted_kernel,
                'active': marker, 'raw_stdout_lines': len(native), 'raw_stdin_lines': stdin_lines,
                'readyok': ready_count, 'rows': len(rows), 'nodes_sum': sum(r['nodes'] for r in rows) if action!='eval' else None,
                'sha256': {p.name:digest(p) for p in (commands,raw,stderr,root/'rows.tsv')}}
    return rows, metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case',choices=('W1','W3_depth','W3_eval','scalar'))
    args=parser.parse_args()
    job=ROOT/'job19'
    cases = {'W1':('W1/r15d','W1/kF',1000,'go depth 9','avx512'),
             'W3_depth':('W3_depth/kF','W3_depth/kF0',300,'go depth 9','avx512'),
             'W3_eval':('W3_eval/kF','W3_eval/kF0',1000,'eval','avx512'),
             'scalar':('W3_depth/kF','scalar/kFscalar',300,'go depth 9','scalar')}
    left,right,count,action,kernel=cases[args.case]
    fixture = job/'positions.txt'
    positions = fixture.read_text().splitlines()
    assert len(positions)==1000
    a,meta_a=read_arm(job/left,positions[:count],action,'avx512')
    b,meta_b=read_arm(job/right,positions[:count],action,kernel)
    fields=('eval_line',) if action=='eval' else ('nodes','bestmove')
    diffs=[(x,y) for x,y in zip(a,b,strict=True) if any(x[k]!=y[k] for k in fields)]
    print(json.dumps({'case':args.case,'fixture_sha256':digest(fixture),'fixture_known_hash_matches':digest(fixture)==EXPECTED,
                      'compared':count,'equal':count-len(diffs),'differs':len(diffs),'fields':fields,
                      'runs':[meta_a,meta_b], 'first_diff':diffs[0] if diffs else None},indent=2))
    return int(bool(diffs))


if __name__=='__main__':
    raise SystemExit(main())
