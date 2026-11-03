"""Bounded deterministic property review over fresh legal positions, no engine."""
import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import random
import struct
import time
import chess
import chess.pgn
from qc_core import Profile, decode_pos, fen_info, is_mate, signed_score
from game_hash import game_records
from run_policy import Inputs, free_guard, new_directory, safe_path, write_json

def rejected(function,*arguments):
    try:
        function(*arguments)
    except ValueError:
        return
    raise AssertionError('malformed input was accepted')

def run(seconds,seed,out):
    out=new_directory(out,16*1024*1024)
    source_inputs=Inputs()
    for name in ('property_review.py','qc_core.py','run_policy.py','game_hash.py'):
        source_inputs.get(Path(__file__).parent/name).digest()
    randomizer=random.Random(seed)
    profile=Profile()
    turns=Counter()
    total=white_total=mate_count=cases=games=pgn_pairs=0
    start=time.monotonic()
    progress=start
    fen=None
    try:
        while time.monotonic()-start<seconds:
            board=chess.Board()
            limit=randomizer.randrange(24,180)
            for ply in range(limit):
                moves=list(board.legal_moves)
                if not moves or board.is_game_over():
                    break
                board.push(randomizer.choice(moves))
                fen=board.fen(en_passant='fen')
                info=fen_info(fen)
                oracle=bytearray(32)
                for square,piece in board.piece_map().items():
                    code=piece.piece_type+(0 if piece.color==chess.WHITE else 6)
                    oracle[square//2]|=code<<(4*(square%2))
                if info['board']!=bytes(oracle) or info['pieces']!=len(board.piece_map()):
                    raise AssertionError('independent board/piece oracle mismatch')
                phase=min(24,sum({chess.KNIGHT:1,chess.BISHOP:1,chess.ROOK:2,chess.QUEEN:4}.get(p.piece_type,0) for p in board.piece_map().values()))
                if phase!=info['phase']:
                    raise AssertionError('material phase oracle mismatch')
                score=randomizer.choice([-32767,-30000,-29999,0,29999,30000,32767]) if cases%3==0 else randomizer.randint(-32767,32767)
                result=randomizer.choice([0,0.5,1])
                meta=int(not board.turn)|(int(result*2)<<1)
                packed=struct.pack('<4sIQ',b'FPOS',1,1)+oracle+struct.pack('<hB',score,meta)
                if list(decode_pos(packed))!=[(bytes(oracle),score,meta)]:
                    raise AssertionError('FPOS column roundtrip mismatch')
                profile.add(fen,score,result,'fixture',0)
                total+=score
                white_total+=score if board.turn else -score
                turns['w' if board.turn else 'b']+=1
                mate_count+=abs(score)>=30000
                if is_mate(score)!=(abs(score)>=30000):
                    raise AssertionError('mate boundary mismatch')
                rejected(signed_score,randomizer.choice([True,False,-32768,32768,1.5,'nan']))
                malformed=fen.replace(' ','\u00a0',1) if cases%2 else fen.replace(' ','\n',1)
                rejected(fen_info,malformed)
                if cases%16==0:
                    rejected(lambda b:list(decode_pos(b)),packed[:-1])
                    rejected(lambda b:list(decode_pos(b)),packed[:-1]+b'\x06')
                    rejected(safe_path,'D:/a13/'+randomizer.choice(['NUL.txt','bad?.txt','../escape','locks/file','network.nnue']))
                cases+=1
                if cases%256==0:
                    free_guard(1024*1024)
                    now=time.monotonic()
                    if now-progress>=30:
                        print(json.dumps(dict(cases=cases,games=games,pgn_pairs=pgn_pairs,seconds=now-start)),flush=True)
                        progress=now
                    if now-start>=seconds:
                        break
            game=chess.pgn.Game.from_board(board)
            text=game.accept(chess.pgn.StringExporter(headers=True,variations=False,comments=False))
            changed=text.replace('\n\n','\n\n{format-only comment}\n',1).replace('[Event "?"]','[Event "renamed"]',1)
            a=list(game_records(io.StringIO(text)))
            b=list(game_records(io.StringIO(changed)))
            if len(a)!=1 or len(b)!=1 or a[0]['game_hash']!=b[0]['game_hash'] or a[0]['plies']!=len(board.move_stack):
                raise AssertionError('PGN identity changed with formatting')
            pgn_pairs+=1
            games+=1
        result=profile.report()
        if (result['rows'],result['score_stm']['sum'],result['score_white']['sum'],result['mate_rows'],result['side_to_move'])!=(cases,total,white_total,mate_count,dict(turns)):
            raise AssertionError('aggregate score/STM oracle mismatch')
        report=dict(status='PASS',seed=seed,cases=cases,games=games,pgn_format_pairs=pgn_pairs,seconds=time.monotonic()-start,
                    method='Random legal python-chess walks; independent piece-code/material/score oracle; malformed mutations; canonical PGN formatting pairs',
                    source_identities=source_inputs.receipts(),strength='NO_CLAIM',training=False,gpu=False)
        write_json(out/'REPORT.json',report)
        print(json.dumps(report),flush=True)
    except BaseException as error:
        write_json(out/'FAILURE.json',dict(status='FAIL',seed=seed,cases=cases,games=games,fen=fen,error=repr(error)))
        raise

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds',type=int,required=True)
    parser.add_argument('--seed',type=int,default=20261103)
    parser.add_argument('--out',required=True)
    parser.add_argument('--threads',type=int,choices=[1],required=True)
    args=parser.parse_args()
    if not 1<=args.seconds<=1800:
        parser.error('seconds must be within 1..1800')
    run(args.seconds,args.seed,args.out)
