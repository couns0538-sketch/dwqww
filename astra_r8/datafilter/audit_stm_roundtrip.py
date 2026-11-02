"""Actual converter round-trip against a literal outcome oracle. UNPROVEN."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

import chess
import numpy as np
from filter_lichess_rec import REC
from filter_positions import low_priority, sha256
from resource_policy import storage_guard
from result_codec import decode_result

HERE = Path(__file__).resolve().parent
# Columns are signed STM outcome and encoded payload, independently reviewable.
ORACLE = {('w','0'):(-1,0), ('w','0.5'):(0,1), ('w','1'):(1,2), ('w','?'):(None,0),
          ('b','0'):(1,2), ('b','0.5'):(0,1), ('b','1'):(-1,0), ('b','?'):(None,0)}
OPPOSITE = {'0':'1', '1':'0', '0.5':'0.5', '?':'?'}


def fixtures():
    """1000 distinct eligible boards, 125 per turn/outcome, material-exact scores."""
    rows = []
    for turn in (chess.WHITE, chess.BLACK):
        count = 0
        for wk in range(8):
            for queen in range(64):
                for color in (chess.WHITE, chess.BLACK):
                    if queen in (wk, chess.H8): continue
                    board = chess.Board(None)
                    board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
                    board.set_piece_at(chess.H8, chess.Piece(chess.KING, chess.BLACK))
                    board.set_piece_at(queen, chess.Piece(chess.QUEEN, color))
                    board.turn = turn
                    if not board.is_valid() or board.is_check() or board.is_game_over(): continue
                    token = ('0','0.5','1','?')[count % 4]
                    white_cp = 900 if color else -900
                    rows.append((board, white_cp if turn else -white_cp, token))
                    count += 1
                    if count == 500: break
                if count == 500: break
            if count == 500: break
        if count != 500: raise ValueError('insufficient distinct fixtures')
    return rows


def run(root):
    root = Path(root)
    storage_guard(root, allowance=20*10**6)
    root.mkdir()
    cases = fixtures()
    reports = {}
    for name, mirror in [('original',False), ('mirror',True)]:
        source = root / (name + '.txt')
        expected = []
        with source.open('x', encoding='utf-8', newline='\n') as fh:
            for board, score, token in cases:
                if mirror: board, token = board.mirror(), OPPOSITE[token]
                fh.write(f'{board.fen(en_passant="fen")} | {score} | {token}\n')
                expected.append(ORACLE[('w' if board.turn else 'b',token)])
        command = [sys.executable,str(HERE/'convert_forge.py'),str(root/name),
                   '--selfplay',str(source),'--keep-result']
        with (root/(name+'.log')).open('xb') as log:
            proc = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        if proc.returncode: raise RuntimeError(f'converter failed: {name}, exit {proc.returncode}')
        seen = set()
        for split in ('train','val'):
            records = np.fromfile(root/name/(split+'.bin'), dtype=REC)
            with (root/name/(split+'.metadata.jsonl')).open(encoding='utf-8') as fh:
                metadata = [json.loads(line) for line in fh]
            assert len(records) == len(metadata)
            for binary, meta in zip(records,metadata):
                row = meta['source_row']
                assert row not in seen
                seen.add(row)
                result, code = expected[row-1]
                assert tuple(binary['rsv']) == (int(result is not None),code,1)
                assert decode_result(binary['rsv'],binary['stm']) == result == meta['result_stm']
                board, score, token = cases[row-1]
                if mirror: board, token = board.mirror(), OPPOSITE[token]
                assert meta['fen'] == board.fen(en_passant='fen')
                assert meta['score_stm'] == score
                assert int(binary['score']) * (1 if binary['stm']==0 else -1) == score
        assert seen == set(range(1,1001))
        reports[name] = dict(rows=len(seen), command=command,
                            hashes={p.name:sha256(p) for p in sorted((root/name).iterdir())})
    assert all(ORACLE[('w' if b.turn else 'b',t)] ==
               ORACLE[('b' if b.turn else 'w',OPPOSITE[t])] for b,s,t in cases)
    report = dict(status='PASS', cases=1000, mirrors=1000, format_version=1,
                  oracle='literal eight-cell outcome table; actual converter bytes', runs=reports)
    with (root/'report.json').open('x') as fh: json.dump(report,fh,indent=2)
    return report


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);a=p.parse_args()
    low_priority(); print(json.dumps(run(a.output),indent=2))
