"""Original fixed-seed legal walks using the existing python-chess public API.

This emits full FENs, unique in their first four position fields. It is a
candidate-independent evaluation corpus, not games or strength evidence.
No FEN, move, network, or binary-record parser is reimplemented here.
"""
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import platform
import random
import shutil
import chess


def legal_fens(count,seed):
    if type(count) is not int or not 1<=count<=1000000 or type(seed) is not int or seed<=0:
        raise ValueError('count must be1..1000000 and seed a positive integer')
    rng=random.Random(seed);board=chess.Board();seen=set();plies=0;attempts=0
    while len(seen)<count:
        fen=board.fen(en_passant='fen');key=' '.join(fen.split()[:4])
        if key not in seen:
            seen.add(key);yield fen
        if board.is_game_over(claim_draw=False) or plies==256:
            board.reset();plies=0
        else:
            moves=sorted(board.legal_moves,key=lambda m:m.uci())
            board.push(moves[rng.randrange(len(moves))]);plies+=1
        attempts+=1
        if attempts>count*64+4096:raise RuntimeError('finite legal-walk uniqueness budget exhausted')


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--count',type=int,default=1000000);ap.add_argument('--seed',type=int,default=20261026);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    allowed=Path('/workspace/forge-pack24-20261026/S09_NATIVE_20261026')
    if not args.out.is_absolute() or args.out.resolve()!=args.out or args.out==allowed or not args.out.is_relative_to(allowed):ap.error('output must be a new descendant of S09_NATIVE_20261026')
    if not 1<=args.count<=1000000 or args.seed<=0:ap.error('invalid finite count/seed')
    if shutil.disk_usage(args.out.parent).free<32*1048576:raise RuntimeError('32MiB free-disk precheck failed')
    args.out.mkdir(exist_ok=False);target=args.out/'legal_fens.fen.gz';raw=hashlib.sha256();rows=0;raw_size=0
    with target.open('xb') as f:
        with gzip.GzipFile(fileobj=f,filename='',mode='wb',mtime=0,compresslevel=6) as z:
            for fen in legal_fens(args.count,args.seed):
                b=(fen+'\n').encode('ascii');raw.update(b);z.write(b);rows+=1;raw_size+=len(b)
    assert rows==args.count
    result={'count':rows,'unique_position_fields':rows,'seed':args.seed,'max_walk_plies':256,'move_order':'sorted UCI; random.Random(seed).randrange','source_sha256':digest(__file__),'python':platform.python_version(),'python_chess_version':chess.__version__,'chess_module':str(Path(chess.__file__).resolve()),'chess_module_sha256':digest(chess.__file__),'gzip':str(target),'gzip_size':target.stat().st_size,'gzip_sha256':digest(target),'raw_size':raw_size,'raw_sha256':raw.hexdigest(),'scope':'legal evaluation corpus only; no training/matches/GPU/engine execution'}
    (args.out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
