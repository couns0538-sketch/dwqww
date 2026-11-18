"""Compare every A13 color-reversed pair by full opening FEN, mainline SAN, and scores."""
from collections import defaultdict
from itertools import zip_longest
from pathlib import Path
import csv,sys
from audit import read_pgn, FINISHED
HERE=Path(__file__).resolve().parent
WORK=HERE.parent
sys.path.insert(0,str(WORK/'j10fens/vendor'))
import chess

def main():
    raw=WORK/'j13match/results'
    out=HERE/'A13'
    games=read_pgn(raw/'A13.pgn')
    finished={int(i):(w,b,r) for i,w,b,r,why in FINISHED.findall((raw/'A13.out').read_text())}
    pairing=defaultdict(list)
    for g in games:pairing[int(g['tags']['Round'])].append(g)
    same=[];diff=[];score_exceptions=[];both=[];evidence=[];first=None
    for rnd in sorted(pairing):
        p=pairing[rnd]
        assert len(p)==2 and p[0]['fen']==p[1]['fen']
        byid={}
        for g in p:
            t=g['tags'];gid=next(i for i in (2*rnd-1,2*rnd) if finished[i]==(t['White'],t['Black'],t['Result']))
            assert gid not in byid;byid[gid]=g
        x,y=[(i,byid[i]) for i in sorted(byid)]
        header=f"Pair {rnd}; opening FEN {p[0]['fen']}"
        def pergame(rec):
            i,g=rec;t=g['tags']
            score=0.5 if t['Result']=='1/2-1/2' else float((t['White']=='A13-A') == (t['Result']=='1-0'))
            return score,f'game {i}: White {t["White"]}, Black {t["Black"]}, result {t["Result"]}, value 1 score {score:g}'
        xs,xlabel=pergame(x);ys,ylabel=pergame(y)
        if xs+ys!=1:score_exceptions.append(rnd)
        # Replay legal SAN in physical move order, checking the canonical UCI move at the first discrepancy.
        b=chess.Board(x[1]['fen']);divergence=None
        for ply,(left,right) in enumerate(zip_longest(x[1]['moves'],y[1]['moves']),1):
            lm=b.parse_san(left) if left is not None else None; rm=b.parse_san(right) if right is not None else None
            if lm!=rm or left!=right:
                pos=b.fen(en_passant='fen')
                divergence=(ply,pos,left or '<game ended>',right or '<game ended>',lm.uci() if lm else '-',rm.uci() if rm else '-')
                break
            b.push(lm)
        if divergence is None:
            same.append(rnd);both.append((rnd,x[0],y[0],p[0]['fen'],x[1]['tags']['Result'],y[1]['tags']['Result'],xs,ys,' '.join(x[1]['moves'])))
        else:
            diff.append(rnd);ply,fen,left,right,lu,ru=divergence
            evidence.extend([header,xlabel,ylabel,f'First differing ply {ply} after the opening: {fen}',f'Game {x[0]} SAN {left}, UCI {lu}; game {y[0]} SAN {right}, UCI {ru}.',''])
            if first is None:first=(rnd,ply,fen)
    txt=[f'All {len(games)} game results checked by scheduled game ID against the PGN tags. Compared {len(pairing)} color-swapped openings, starting from each full FEN and replaying legal moves.',
         f'Pairs with identical opening and full SAN move list: {len(same)}/{len(pairing)}.',
         'Identical pair IDs: '+', '.join(map(str,same))+'.',
         f'Pairs with differing moves: {len(diff)}. Pair IDs: '+(', '.join(map(str,diff)) if diff else 'none')+'.',
         f'Pairs with value-1 score different from 1 out of 2: {len(score_exceptions)}; '+(', '.join(map(str,score_exceptions)) if score_exceptions else 'none')+'.',
         'An identical pair’s common SAN line, opening, scheduled game IDs, results, and value 1 scores are recorded in same-lines.tsv.','']
    if diff:
        txt += ['Every differing pair, ordered by round.','',*evidence]
    else:txt+=['Values 1 and 2 played identical lines in all 100 color-reversed opening pairs (200 games). No differing position was observed.']
    (out/'part-a.txt').write_text('\n'.join(txt)+'\n')
    with (out/'same-lines.tsv').open('w') as f:
        w=csv.writer(f,delimiter='\t',lineterminator='\n')
        w.writerow(('pair','game1_id','game2_id','opening_fen','game1_result','game2_result','value1_score_game1','value1_score_game2','common_san_mainline'));w.writerows(both)
    print('A13 replay',len(same),'identical,',len(diff),'differing,',len(score_exceptions),'nonunit pair scores',flush=True)
if __name__=='__main__':main()
