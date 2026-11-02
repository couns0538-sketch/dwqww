import json
from pathlib import Path
import subprocess
import sys
import numpy as np
import pytest
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
from filter_lichess_rec import REC

def positions():
    for placement, score in [('7k/8/8/8/4Q3/8/8/K7',900),('7k/8/8/3q4/8/8/8/K7',-900)]:
        for turn in ('w','b'):
            yield f'{placement} {turn} - - 17 81',score

def execute(tmp_path, args):
    p=subprocess.run([sys.executable,str(HERE/'convert_forge.py'),str(tmp_path/'out'),*args],capture_output=True,text=True)
    assert p.returncode==0,p.stdout+p.stderr
    data=[]
    for split in ('train','val'):
        binary=np.fromfile(tmp_path/'out'/f'{split}.bin',dtype=REC)
        meta=[json.loads(line) for line in (tmp_path/'out'/f'{split}.metadata.jsonl').read_text().splitlines()]
        assert len(binary)==len(meta)
        data.extend(zip(binary,meta))
    return data

def test_duplicate_outcome_first_occurrence(tmp_path):
    lines=[]
    for fen,white in positions():
        stm=white if ' w ' in fen else -white
        lines.extend([f'{fen} | {stm} | 1', f'{fen} | {stm+10} | 0'])
    source=tmp_path/'input.txt'; source.write_text('\n'.join(lines)+'\n')
    data=execute(tmp_path,['--selfplay',str(source),'--keep-result'])
    assert len(data)==4
    for binary,meta in data:
        assert meta['result_white']==1 and binary['rsv'][0]==1 and binary['rsv'][1]==2
        assert meta['ply'] in (160,161) and ' 17 81' in meta['fen']
        assert meta['source_row'] in (1,3,5,7)

def test_lichess_converter_route(tmp_path):
    source=tmp_path/'lichess.jsonl'
    source.write_text('\n'.join(json.dumps({'fen':fen,'evals':[{'pvs':[{'cp':score}]}]}) for fen,score in positions())+'\n')
    data=execute(tmp_path,['--lichess',str(source),'--keep-result'])
    assert len(data)==4
    assert all(not m['has_result'] and m['result_stm'] is None and b['rsv'][0]==0 for b,m in data)

def test_pgn_results_and_original_clocks(tmp_path):
    source=tmp_path/'input.pgn'
    import chess
    games=[]
    for fen,white in positions():
        board=chess.Board(fen)
        move=next(m for m in board.legal_moves if not board.is_capture(m) and not m.promotion)
        score=white if board.turn else -white
        move_number='81.' if board.turn else '81...'
        games.append(f'[SetUp "1"]\n[FEN "{fen}"]\n[Result "1-0"]\n\n{move_number} {board.san(move)} {{{score/100:+.2f}/12}} 1-0\n')
    source.write_text('\n'.join(games))
    data=execute(tmp_path,['--pgn',str(source),'--keep-result'])
    assert len(data)==4
    for b,m in data:
        assert m['result_white']==1 and m['best_move'] is not None
        assert ' 17 81' in m['fen']
