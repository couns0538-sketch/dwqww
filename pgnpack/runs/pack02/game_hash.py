"""Exact canonical mainline identity; this never invents original row bindings."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'astra_r8'/'datafilter'))
from records import read_pgn_game
from run_policy import Inputs, free_guard, new_directory, safe_path, write_json


def game_records(stream):
    ordinal=0
    while True:
        game=read_pgn_game(stream)
        if game is None:
            return
        ordinal+=1
        board=game.board()
        initial=board.fen(en_passant='fen')
        moves=[]
        for move in game.mainline_moves():
            if not board.is_legal(move):
                raise ValueError('illegal mainline move')
            moves.append(board.uci(move))
            board.push(move)
        canonical='astra-r13-mainline-v1\0'+initial+'\0'+' '.join(moves)
        yield dict(game_ordinal=ordinal,game_hash=hashlib.sha256(canonical.encode('ascii')).hexdigest(),
                   initial_fen=initial,plies=len(moves),result=game.headers.get('Result','*'))


def separation(train_hashes,holdout_hashes,*,bindings_verified=False):
    shared=set(train_hashes)&set(holdout_hashes)
    return dict(status=('FAIL' if shared else 'PASS') if bindings_verified else 'UNVERIFIED',
                exact_movetext_overlap=len(shared),authentic_game_overlap=len(shared) if bindings_verified else None,
                overlap_hashes=sorted(shared),
                limitation='Exact complete mainline identity only. Truncated/extended games and original population row bindings need independent evidence.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pgn',required=True)
    parser.add_argument('--out',required=True)
    parser.add_argument('--threads',type=int,choices=[1],required=True)
    args=parser.parse_args()
    source=safe_path(args.pgn)
    inputs=Inputs()
    snapshot=inputs.get(source)
    before=snapshot.digest()
    out=new_directory(args.out,32*1024*1024)
    count=0
    with source.open('r',encoding='utf-8',newline=None) as stream,(out/'games.jsonl').open('x',encoding='utf-8',newline='\n') as target:
        for record in game_records(stream):
            free_guard(16384)
            target.write(json.dumps(record,sort_keys=True)+'\n')
            count+=1
    snapshot.digest()
    write_json(out/'REPORT.json',dict(status='HASHED_ONLY',game_separation='UNVERIFIED',authentic_game_overlap=None,games=count,input=snapshot.receipt(),
                                      reason='No authenticated train/holdout row-binding manifest supplied; no split invented'))

if __name__=='__main__':
    main()
