"""Compare exact depth-2 score/nodes/bestmove from frozen production exes."""
import argparse,hashlib,json,pathlib,re,sys
from validate_uci import Engine
import chess,psutil
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('lock'); ap.add_argument('candidate'); ap.add_argument('out')
    args=ap.parse_args(); out=pathlib.Path(args.out); out.mkdir(parents=True,exist_ok=False)
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS); psutil.Process().cpu_affinity([3])
    corpus=pathlib.Path(__file__).parents[1]/'evidence/fens_12k.txt'
    fens=corpus.read_text().splitlines(); assert len(fens)>=10000
    assert len(set(fens))==len(fens) and all(chess.Board(f).is_valid() for f in fens)
    baseline=None; results=[]
    for name,exe,on in [('lock',args.lock,False),('off',args.candidate,False),('on',args.candidate,True)]:
        e=None; records=[]
        try:
            e=Engine(exe,out/(name+'.uci.log'),on=on)
            with (out/(name+'.jsonl')).open('x') as stream:
                for i,fen in enumerate(fens):
                    e.send('position fen '+fen); e.send('go depth 2'); lines=e.wait('^bestmove ')
                    infos=[s for s in lines if re.search(r'^info depth 2 .*score (cp|mate) ',s)]
                    if not infos: raise RuntimeError('no depth2 score '+str(i))
                    info=infos[-1]; score=re.search(r'score ((?:cp|mate) -?\d+)',info)[1]
                    nodes=int(re.search(r' nodes (\d+)',info)[1]); move=lines[-1].split()[1]
                    b=chess.Board(fen)
                    if b.legal_moves.count():
                        assert chess.Move.from_uci(move) in b.legal_moves,(i,move)
                    else: assert move in ['0000','(none)'],(i,move)
                    row=[i,score,nodes,move]; records.append(row); stream.write(json.dumps(row)+'\n')
                    if baseline is not None and row!=baseline[i]: raise RuntimeError(f'{name} mismatch at {i}: {row} != {baseline[i]}')
                    if (i+1)%2000==0: print(name,i+1,'PASS',flush=True)
            e.close(); e=None
        finally:
            if e:e.abort()
        if baseline is None:baseline=records
        results.append({'name':name,'exe':exe,'sha256':hashlib.sha256(pathlib.Path(exe).read_bytes()).hexdigest(),
                        'positions':len(records),'digest':hashlib.sha256(json.dumps(records).encode()).hexdigest()})
    (out/'result.json').write_text(json.dumps({'status':'PASS','corpus_sha256':hashlib.sha256(corpus.read_bytes()).hexdigest(),'runs':results},indent=2))
    print('PRODUCTION PARITY PASS',flush=True)
if __name__=='__main__':main()
