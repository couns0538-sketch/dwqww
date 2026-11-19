"""Reconcile fastchess PGNs by pair set, round, and game, and verify plus W-L-D."""
import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import sys

try:
    import chess.pgn
except ModuleNotFoundError:
    sys.path.insert(0, '/workspace/work/tactic3/deps')
    import chess.pgn

FINISH = re.compile(r'^Finished game (\d+) \((plus|minus) vs (plus|minus)\): (1-0|0-1|1/2-1/2) \{(.*)\}', re.M)
SCORE = re.compile(r'^Games: (\d+), Wins: (\d+), Losses: (\d+), Draws: (\d+)',re.M)

@dataclass(frozen=True)
class Game:
    round: int
    number: int
    white: str
    black: str
    result: str
    fen: str
    moves: tuple
    def plus_score(self):
        if self.result=='1/2-1/2': return 'D'
        return 'W' if (self.white=='plus')==(self.result=='1-0') else 'L'

def load(folder, j):
    stem=f'j{j:03d}'
    raw=(folder/(stem+'.log')).read_text()
    finished={int(i):(w,b,r,why) for i,w,b,r,why in FINISH.findall(raw)}
    assert sorted(finished)==list(range(1,17)),(folder,stem,finished)
    totals=tuple(map(int,SCORE.findall(raw)[-1]))
    assert totals[0]==16
    records={}
    with (folder/(stem+'.pgn')).open() as source:
        while game:=chess.pgn.read_game(source):
            assert not game.errors,game.errors
            h=game.headers
            rnd=int(h['Round'])
            key=tuple(h[s] for s in ('White','Black','Result'))
            hits=[i for i in (2*rnd-1,2*rnd) if finished[i][:3]==key]
            assert len(hits)==1,(folder,stem,rnd,key)
            i=hits[0]
            assert i not in records
            moves=tuple(m.uci() for m in game.mainline_moves())
            assert int(h['PlyCount'])==len(moves),(folder,stem,i)
            assert not re.search(r'illegal move|disconnect|on time|stall',finished[i][3],re.I),(folder,stem,i,finished[i])
            records[i]=Game(rnd,1+(i-1)%2,*key,h['FEN'],moves)
    assert len(records)==16
    for i in range(1,17,2):
        assert records[i].fen==records[i+1].fen and records[i].white==records[i+1].black
    scores=Counter(r.plus_score() for r in records.values())
    assert tuple(scores[s] for s in 'WLD')==totals[1:]
    return records, totals[1:]

def scan(args):
    report=args.output;report.mkdir(parents=True,exist_ok=True)
    positions=[];stage_stats=[];changed_game_count=changed_wld=changed_outcome=0
    first_change=None
    with (report/'sets.tsv').open('w') as out:
        print('j\tgames\tplies\tplus_W\tplus_L\tdraws\tmoves_differ_from_R1\tWLD_differs_from_R1\tresults_differ_from_R1',file=out)
        for j in range(1,args.sets+1):
            cur,score=load(args.base/args.stage,j)
            baseline,prevscore=load(args.base/'R1',j) if args.stage!='R1' else (cur,score)
            count=changed=0
            for i in range(1,17):
                x=baseline[i]; y=cur[i]
                assert (x.round,x.number,x.white,x.black,x.fen)==(y.round,y.number,y.white,y.black,y.fen),(j,i)
                changed+=x.result!=y.result
                if x.moves==y.moves: continue
                count+=1
                if first_change is None:
                    k=0
                    while k<min(len(x.moves),len(y.moves)) and x.moves[k]==y.moves[k]: k+=1
                    first_change=dict(pair_set=j,round=x.round,game=x.number,white=x.white,black=x.black,fen=x.fen,
                                      first_differing_move_from_FEN=k+1,R1_prefix=list(x.moves[:k+1]),test_prefix=list(y.moves[:k+1]))
            plies=sum(len(g.moves) for g in cur.values())
            print(j,len(cur),plies,*score,count,int(score!=prevscore),changed,sep='\t',file=out)
            stage_stats.append([len(cur),plies,*score])
            changed_game_count+=count;changed_wld+=score!=prevscore;changed_outcome+=changed
    result=dict(stage=args.stage,sets=args.sets,**dict(zip(('games','plies','wins','losses','draws'),map(sum,zip(*stage_stats)))),
                games_with_different_moves=changed_game_count,sets_with_different_wld=changed_wld,games_with_different_result=changed_outcome,first_game_difference=first_change)
    (report/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('base',type=Path);p.add_argument('stage');p.add_argument('sets',type=int);p.add_argument('output',type=Path);scan(p.parse_args())
