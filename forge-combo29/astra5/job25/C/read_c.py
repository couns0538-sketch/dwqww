"""Reconcile finished games, official score lines and pairs for job 25."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import re
import sys
try:
    import chess.pgn
except ImportError:
    sys.path.insert(0,"/workspace/work/tactic3/deps")
    import chess.pgn


START = re.compile(r"^Started game (\d+) of (\d+) \((kF|r15d) vs (kF|r15d)\)")
FINISH = re.compile(r"^Finished game (\d+) \((kF|r15d) vs (kF|r15d)\): (1-0|0-1|1/2-1/2|\*) \{(.*)\}")
SCORE = re.compile(r"^Games: (\d+), Wins: (\d+), Losses: (\d+), Draws: (\d+)")
ISSUE = re.compile(r"illegal move|lost connection|connection lost|connection (?:closed|was lost)|disconnect|stall|(?:loss|lost|loses|forfeit|expires?) on time|time forfe[it]+",re.I)
RULE = re.compile(r"\bmates?\b|stalemate|repetition|50[- ]move|fifty[- ]move|insufficient (?:mating )?material",re.I)


def analyze(dest):
    stage=dest.name
    target={"C1":40,"C2":120,"C4":80}[stage]
    raw=(dest/"fastchess.log").read_text(errors="replace").splitlines()
    finished={}; started=[]; score=None; issues=[]; endings=Counter()
    for i,line in enumerate(raw,1):
        if m:=START.match(line): started.append(int(m[1]))
        if m:=FINISH.match(line):
            gid=int(m[1])
            if gid in finished: raise ValueError(f"duplicate Finished game {gid}")
            finished[gid]=tuple(m.groups()[1:]);endings[m[5]]+=1
        if m:=SCORE.match(line): score=list(map(int,m.groups()))
        if ISSUE.search(line): issues.append(f"{i}\t{line}")
    (dest/"issues.txt").write_text("".join(s+"\n" for s in issues))
    recs={}; outcome=Counter()
    with (dest/"games.pgn").open() as pgn:
        while game:=chess.pgn.read_game(pgn):
            h=game.headers
            rnd=int(h["Round"]); colors=(h["White"],h["Black"])
            keys=[g for g in (2*rnd-1,2*rnd) if g in finished and finished[g][:3]==(*colors,h["Result"])]
            if not keys and h['Result']=='*': continue
            if len(keys)!=1 or keys[0] in recs or game.errors:
                raise ValueError(f"unexpected PGN: {h} errors={game.errors}")
            gid=keys[0]; moves=tuple(m.uci() for m in game.mainline_moves())
            if len(moves)!=int(h["PlyCount"]): raise ValueError("incorrect PGN PlyCount")
            kfpoints=1 if h["Result"]=="1/2-1/2" else 2*int((h["White"]=="kF")==(h["Result"]=="1-0"))
            outcome[kfpoints]+=1
            recs[gid]=(h["FEN"],moves,kfpoints)
    if len(started)!=len(set(started)) or not set(finished)<=set(started): raise ValueError("game ID mismatch")
    if set(recs)!=set(finished): raise ValueError("finished games missing PGNs")
    wld=[outcome[v] for v in (2,0,1)]
    if len(recs)==target and score!=[target,*wld]: raise ValueError(f"PGN/official score mismatch: {wld} vs {score}")
    bins=[0]*5; paired=0; diffs=0; first=None; score_balanced=True
    with (dest/"pairs.tsv").open("w") as f:
        print("round\tgame_a\tgame_b\tmatching_moves\tkF_halfpoints\tplies_a\tplies_b",file=f)
        for rnd in range(1,1+target//2):
            a,b=2*rnd-1,2*rnd
            if a not in recs or b not in recs: continue
            af,am,ap=recs[a];bf,bm,bp=recs[b]
            if af!=bf or finished[a][:2]!=tuple(reversed(finished[b][:2])):
                raise ValueError(f"unpaired openings/colors in round {rnd}")
            paired+=1;bins[ap+bp]+=1
            if ap+bp!=2: score_balanced=False
            if am!=bm:
                diffs+=1
                if first is None:
                    n=next((i for i,(x,y) in enumerate(zip(am,bm)) if x!=y),min(len(am),len(bm)))
                    first=dict(round=rnd,game_a=a,game_b=b,ply_from_book=n+1,a_prefix=am[:n+1],b_prefix=bm[:n+1])
            print(rnd,a,b,int(am==bm),ap+bp,len(am),len(bm),sep="\t",file=f)
    with (dest/"games.tsv").open("w") as f:
        print("game\tround\twhite\tblack\tresult\tending\tplies\tkF_halfpoints",file=f)
        for gid,(fen,moves,points) in sorted(recs.items()):
            print(gid,(gid+1)//2,*finished[gid],len(moves),points,sep="\t",file=f)
    out=dict(stage=stage,target_games=target,games_started=len(started),games_finished=len(finished),complete_pairs=paired,
             endings=dict(endings),non_rule_endings=sum(n for reason,n in endings.items() if not RULE.search(reason)),
             issue_lines=len(issues),kF_WLD=wld,kF_points=(2*wld[0]+wld[2])/2,
             kF_points_share=(2*wld[0]+wld[2])/(2*len(finished)) if finished else None,official_score=score,
             pentanomial=bins,different_move_pairs=diffs,first_divergence=first,every_pair_scored_one_each=score_balanced)
    if stage=="C1": out["KC1"]=len(recs)==target and paired==20 and diffs==0 and score_balanced and wld[0]==wld[1]
    if stage=="C2": out["CC2"]=diffs>0
    (dest/"summary.json").write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps({k:v for k,v in out.items() if k!="first_divergence"}))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage_directory",type=Path)
    analyze(parser.parse_args().stage_directory)
