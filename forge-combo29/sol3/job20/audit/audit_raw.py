#!/usr/bin/env python3
"""Reconstruct Job 20 depth-search counts from raw transcripts, without the run driver."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re


ROOT = Path('/workspace/work/forge-sol3/forge-combo29/sol3')
FIXTURES = {
    9: (ROOT/'job19/positions.txt', '3c1b17332eca46a912f572eae8197324f466a8e2f909653104c427457ffb0521', 1000),
    12: (ROOT/'job14/references/O.epd.txt', '02d59eaf2515a4e11aecb78c5736db193812516f42ab8a6aa0b2411332186300', 200),
}
CASES = {
    'K1-r15d': ('K1/r15d-shadow', 9, 1000, True, 'avx512', 'r15d'),
    'K1-kF': ('K1/kF-shadow', 9, 1000, True, 'avx512', 'kF'),
    'K2': ('K2/kF-promotion-control', 9, 200, True, 'avx512', None),
    'S1-r15d': ('S1/r15d-shadow', 9, 1000, True, 'avx512', 'r15d'),
    'S1-kF': ('S1/kF-shadow', 9, 1000, True, 'avx512', 'kF'),
    'S3-kF': ('S3_W1/kF', 9, 1000, False, 'avx512', 'kF'),
    'S3-kFscalar': ('S3_W1/kFscalar', 9, 1000, False, 'scalar', 'kF'),
    'S3-O': ('S3_O/kFscalar', 12, 200, False, 'scalar', None),
}
REFUSAL = re.compile(r'unknown option|invalid value|invalid fen|\bERROR\b', re.I)
DIFF = 'info string shadow differ fast '
COUNT = re.compile(r'info string shadow evals (\d+) differ (\d+)$')
BEST = re.compile(r'bestmove ([a-h][1-8][a-h][1-8][qrbn]?|0000)(?: ponder [a-h][1-8][a-h][1-8][qrbn]?)?$')


def hash_file(file):
    with file.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def prescribed_input(fens, depth):
    archived=(ROOT/'job19/W1/r15d/engine.commands.txt').read_text().splitlines()
    startup=archived[:archived.index('ucinewgame')]
    assert startup[-3:] == ['setoption name NNUEArchFile value /workspace/work/sol3-job4-net/net768.fnn3',
                            'setoption name NNUEArch value true','isready']
    assert 'setoption name Threads value 1' in startup and 'setoption name Hash value 16' in startup
    expected=startup.copy()
    for fen in fens:
        expected.extend(('ucinewgame','isready',f'position fen {fen}',f'go depth {depth}'))
    return [*expected,'quit']


def options_and_rounds(path, fens, depth, wanted_kernel):
    actual=(path/'engine.commands.txt').read_text().splitlines()
    expected=prescribed_input(fens,depth)
    assert actual==expected, f'unexpected option sequence or fixture row/depth in {path}'
    raw=(path/'engine.stdout.txt').read_text(encoding='ascii').splitlines()
    err=(path/'engine.stderr.txt').read_text(encoding='ascii').splitlines()
    assert not any(REFUSAL.search(line) for line in (*raw,*err))
    assert raw.count('uciok')==1 and raw.count('readyok')==actual.count('isready')
    net=[(n,line) for n,line in enumerate(raw) if line.startswith('info string NNUE v3 active:')]
    assert len(net)==1
    net_slot, marker=net[0]
    assert raw.index('uciok')<net_slot<raw.index('readyok')
    assert ' hidden 768 ' in marker and ' checksum 30ab43b4ba5db5f3 ' in marker
    assert marker.endswith(f' kernel {wanted_kernel}')
    start=raw.index('readyok')+1
    round_starts=[n for n in range(start,len(raw)) if raw[n]=='readyok']
    assert len(round_starts)==len(fens) and round_starts[0]==start
    return [(left+1,raw[left+1:right]) for left,right in zip(round_starts,[*round_starts[1:],len(raw)],strict=True)], marker


def recount(path, fens, depth, shadow, kernel):
    blocks,marker=options_and_rounds(path,fens,depth,kernel)
    rows=[]
    diag=[]
    for index, (fen,(start,block)) in enumerate(zip(fens,blocks,strict=True),1):
        finished=BEST.fullmatch(block[-1])
        assert finished and sum(line.startswith('bestmove ') for line in block)==1
        info=next(line for line in reversed(block[:-1]) if line.startswith('info depth '))
        pk=info.split()
        assert 0<=int(pk[2])<=depth
        row={'row':index,'fen':fen,'nodes':int(pk[pk.index('nodes')+1]),'bestmove':finished[1],
             'last_info':info,'bestmove_line':block[-1],
             'stdout_first':start+1,'stdout_last':start+len(block)}
        shadows=[(offset,line) for offset,line in enumerate(block) if line.startswith('info string shadow ')]
        if shadow:
            last=COUNT.fullmatch(block[-2])
            assert last and shadows[-1]==(len(block)-2,block[-2])
            evals,diffs=map(int,last.groups())
            assert 0<=diffs<=evals
            row.update({'shadow_evals':evals,'shadow_differ':diffs,'shadow_count_line':block[-2]})
            assert len(shadows)-1==min(5-len(diag),diffs)
            for offset,line in shadows[:-1]:
                assert line.startswith(DIFF)
                cols=line.removeprefix(DIFF).split(' ',4)
                assert cols[1]=='ref' and cols[3]=='fen' and len(cols[4].split())==6
                fast,reference=int(cols[0]),int(cols[2])
                assert fast != reference
                diag.append({'search_row':index,'root_fen':fen,'raw_stdout_line':start+offset+1,
                             'fast':fast,'reference':reference,'evaluated_fen':cols[4],'raw_line':line})
        else:
            assert not shadows
        rows.append(row)
    with (path/'rows.tsv').open(encoding='ascii',newline='') as fh:
        recorded=list(csv.DictReader(fh,delimiter='\t'))
    assert [{key:str(val) for key,val in row.items()} for row in rows]==recorded
    return rows,diag,marker


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('case',choices=CASES)
    name=cli.parse_args().case
    sub,depth,n,shadow,kernel,reference=CASES[name]
    directory=ROOT/'job20'/sub
    summary=json.loads((directory/'summary.json').read_text())
    assert summary['rows_expected']==n and summary['error'] is None
    inputs,required_hash,m=FIXTURES[depth]
    assert hash_file(inputs)==summary['fixture_sha256']==required_hash
    fens=inputs.read_text().splitlines()
    assert len(fens)==m
    rows,first_five,marker=recount(directory,fens[:n],depth,shadow,kernel)
    nodes=sum(x['nodes'] for x in rows)
    first_three=[x['nodes'] for x in rows[:3]]
    assert nodes==summary['terminal_nodes'] and first_three==summary['first_three_nodes']
    if shadow:
        evals=sum(x['shadow_evals'] for x in rows)
        diff=sum(x['shadow_differ'] for x in rows)
        affected=sum(x['shadow_differ']>0 for x in rows)
        assert evals==summary['shadow_evals'] and diff==summary['shadow_differ']
        assert first_five==summary['first_differences']
    else:
        evals=diff=affected=None
    comparison=None
    if reference:
        original,_,_=recount(ROOT/'job19/W1'/reference,fens,depth,False,'avx512')
        differences=[(a,b) for a,b in zip(original,rows,strict=True) if (a['nodes'],a['bestmove'])!=(b['nodes'],b['bestmove'])]
        comparison={'reference':reference,'equal':n-len(differences),'differ':len(differences),
                    'first_difference':differences[0] if differences else None}
    if name=='S3-O':
        assert (nodes,first_three)==(32504791,[37409,213822,139142])
    print(json.dumps({'case':name,'path':str(directory),'active':marker,'fixture_sha256':required_hash,
          'rows':len(rows),'terminal_nodes':nodes,'first_three_nodes':first_three,'evals':evals,'differ':diff,
          'affected_searches':affected,'evals_per_last_info_node':evals/nodes if evals is not None else None,
          'first_five':first_five,'comparison':comparison,
          'sha256':{f:hash_file(directory/f) for f in ('engine.stdout.txt','engine.commands.txt','engine.stderr.txt','rows.tsv')}},indent=2))


if __name__=='__main__':
    main()
