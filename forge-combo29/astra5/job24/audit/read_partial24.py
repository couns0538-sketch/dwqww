"""Report finished games in an interrupted set, excluding games without a final PGN and runner result."""
import argparse
from collections import Counter
from pathlib import Path
import re,sys,json
try:
    import chess.pgn
except ImportError:
    sys.path.insert(0,'/workspace/work/tactic3/deps')
    import chess.pgn
from reconcile_games import FINISH,load

def read(root,stage,j):
    prefix=root/stage/f'j{j:03d}'
    text=prefix.with_suffix('.log').read_text(errors='replace')
    closed={int(i):(w,b,r,reason) for i,w,b,r,reason in FINISH.findall(text)}
    score=Counter(); covered=[];differences=[]
    compare=load(root/'R1',j)[0] if stage!='R1' else {}
    pgn=prefix.with_suffix('.pgn')
    if pgn.exists():
        with pgn.open() as f:
            while game:=chess.pgn.read_game(f):
                h=game.headers
                if h['Result']=='*' or not str(h.get('Round','')).isdigit():continue
                rnd=int(h['Round'])
                key=(h['White'],h['Black'],h['Result'])
                games=[i for i in [2*rnd-1,2*rnd] if i in closed and closed[i][:3]==key]
                if not games: continue
                assert len(games)==1
                i=games[0]
                if re.search(r'interrupt|abandon|disconnect|on time|stall',closed[i][3],re.I): continue
                assert not game.errors and i not in [row[0] for row in covered]
                moves=tuple(m.uci() for m in game.mainline_moves())
                assert 'PlyCount' in h and int(h['PlyCount'])==len(moves)
                covered.append((i,len(moves)))
                score['D' if h['Result']=='1/2-1/2' else ('W' if (h['White']=='plus')==(h['Result']=='1-0') else 'L')]+=1
                if compare:
                    old=compare[i]
                    assert (h['FEN'],h['White'],h['Black'])==(old.fen,old.white,old.black)
                    if moves!=old.moves: differences.append(i)
    return dict(stage=stage,j=j,complete_games=len(covered),completed_fastchess_ids=sorted(i for i,_ in covered),complete_plies=sum(n for _,n in covered),wins=score['W'],losses=score['L'],draws=score['D'],different_games=len(differences),different_ids=differences,fastchess_finish_records=len(closed))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('base',type=Path);parser.add_argument('stage');parser.add_argument('j',type=int);args=parser.parse_args()
    print(json.dumps(read(args.base,args.stage,args.j),indent=2))
