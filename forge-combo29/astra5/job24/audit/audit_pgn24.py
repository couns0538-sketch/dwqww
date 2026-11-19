"""Read fastchess PGNs, independently recover W-L-D, and compare UCI move lists by round and game."""
import argparse
import csv
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re

import chess
import chess.pgn


START = re.compile(r"^Started game (\d+) of 16 \((plus|minus) vs (plus|minus)\)")
FINISH = re.compile(r"^Finished game (\d+) \((plus|minus) vs (plus|minus)\): (1-0|0-1|1/2-1/2) ")
WLD = re.compile(r"Games:\s*(\d+),\s*Wins:\s*(\d+),\s*Losses:\s*(\d+),\s*Draws:\s*(\d+)")

class PgnBuilder(chess.pgn.GameBuilder):
    def visit_result(self, result):
        self.game.movetext_result = result
        super().visit_result(result)


@dataclass
class Game:
    round: int
    id_in_pair: int
    white: str
    black: str
    fen: str
    result: str
    moves: tuple

    @property
    def key(self):
        return self.round, self.id_in_pair


def read_set(folder, j, partial=False):
    prefix=folder/f"j{j:03d}"
    meta={}
    with prefix.with_suffix(".receipt.txt").open() as f:
        for row in csv.DictReader(f,delimiter="\t"):
            meta[row["field"]]=row["value"]
    if meta["status"]!="complete" and not partial:
        raise ValueError(f"{prefix}: status {meta['status']}")
    pgn,log=prefix.with_suffix(".pgn"),prefix.with_suffix(".log")
    if sha256(pgn.read_bytes()).hexdigest()!=meta["pgn_sha256"] or sha256(log.read_bytes()).hexdigest()!=meta["log_sha256"]:
        raise ValueError(f"{prefix}: PGN or log changed since receipt")
    cmd=json.loads(prefix.with_suffix(".command.json").read_text())
    if cmd.count("-srand")!=1 or cmd[cmd.index("-srand")+1]!=str(2400000+j):
        raise ValueError(f"{prefix}: invalid opening seed")
    started,finished,printed={},{},[]
    for line in log.read_text().splitlines():
        match=START.match(line)
        if match:
            i,w,b=match.groups()
            if int(i) in started: raise ValueError(f"{prefix}: duplicate start {i}")
            started[int(i)]=(w,b)
        match=FINISH.match(line)
        if match:
            i,w,b,r=match.groups()
            if int(i) in finished: raise ValueError(f"{prefix}: duplicate finish {i}")
            finished[int(i)]=(w,b,r)
        match=WLD.search(line)
        if match:
            printed.append(tuple(map(int,match.groups())))
    if not partial and (set(started)!=set(range(1,17)) or started!={i:t[:2] for i,t in finished.items()} or not printed):
        raise ValueError(f"{prefix}: controller's finished games or result line incomplete")
    if any(started.get(i)!=value[:2] for i,value in finished.items()):
        raise ValueError(f"{prefix}: controller's finished colors differ from its starts")
    games={}
    with pgn.open(encoding="utf-8-sig") as f:
        while (game:=chess.pgn.read_game(f,Visitor=PgnBuilder)) is not None:
            h=game.headers
            if partial and h["Result"]=="*":
                continue
            if game.errors or getattr(game,"movetext_result",None)!=h["Result"] or {h["White"],h["Black"]}!={"plus","minus"}:
                raise ValueError(f"{prefix}: invalid game or result {h}: {game.errors}")
            rnd=int(h["Round"])
            if not 1<=rnd<=8 or h.get("SetUp")!="1" or "FEN" not in h:
                raise ValueError(f"{prefix}: invalid round or opening setup")
            two_ids=(2*rnd-1,2*rnd)
            match=[i for i in two_ids if finished.get(i)==(h["White"],h["Black"],h["Result"])]
            if len(match)!=1:
                raise ValueError(f"{prefix}: finish ID does not identify round {rnd}, {h['White']} as White")
            id_in_pair=match[0]-(2*rnd-2)
            moves=tuple(m.uci() for m in game.mainline_moves())
            if len(moves)!=int(h["PlyCount"]):
                raise ValueError(f"{prefix}: expected {h['PlyCount']} plies in {h}, read {len(moves)}")
            g=Game(rnd,id_in_pair,h["White"],h["Black"],h["FEN"],h["Result"],moves)
            if g.key in games:
                raise ValueError(f"{prefix}: duplicate PGN game at {g.key}")
            games[g.key]=g
    if len(games)!=len(finished) or (not partial and len(games)!=16):
        raise ValueError(f"{prefix}: finished PGN and controller games differ")
    for rnd in range(1,9):
        if partial and not all((rnd,i) in games for i in (1,2)):
            continue
        one,two=games[rnd,1],games[rnd,2]
        if one.white!=two.black or one.black!=two.white or one.fen!=two.fen:
            raise ValueError(f"{prefix}: round {rnd} lacks matching FEN and swapped colors")
    wins=losses=draws=0
    for g in games.values():
        if g.result=="1/2-1/2":
            draws+=1
        elif (g.white=="plus")==(g.result=="1-0"):
            wins+=1
        else:
            losses+=1
    score=(len(games),wins,losses,draws)
    if (printed and (not partial or printed[-1][0]==score[0]) and score!=printed[-1]) or (not partial and score!=tuple(int(meta[k]) for k in ("games","wins","losses","draws"))):
        raise ValueError(f"{prefix}: PGN {score}, final WLD {printed[-1]}, receipt {meta}")
    return games,score


def describe(games,score):
    return [len(games),sum(len(g.moves) for g in games.values()),*score[1:]]


def summarize(args):
    target=1 if args.stage=="C24" else 80
    if args.through is not None: target=args.through
    if not 1<=target<=80: raise ValueError(f"invalid set count {target}")
    folder=args.results/args.stage
    baseline=args.results/"R1"
    totals=[0]*5
    ndiff=wdiff=rdiff=0
    first=None
    first_wld=None
    print("set\tgames\tplies\tplus wins\tplus losses\tdraws\tdifferent move lists vs R1\tWLD differs vs R1")
    first_set=args.single or 1
    if args.single:
        target=args.single
    for j in range(first_set,target+1):
        games,score=read_set(folder,j,partial=args.partial_last and j==target)
        base,bscore=(games,score) if args.stage=="R1" else read_set(baseline,j)
        mismatch=[]
        for key in sorted(games):
            g,b=games[key],base[key]
            if (g.white,g.black,g.fen)!=(b.white,b.black,b.fen):
                raise ValueError(f"{args.stage} j{j} round {key} has different colors or opening from R1")
            if g.moves!=b.moves:
                mismatch.append(key)
                if first is None:
                    pos=next((i for i,(x,y) in enumerate(zip(g.moves,b.moves)) if x!=y),min(len(g.moves),len(b.moves)))
                    first=(j,key,pos,g,b)
            rdiff+=g.result!=b.result
        partial_set=len(games)<16
        wd=not partial_set and score!=bscore
        if wd and first_wld is None:
            first_wld=(j,bscore[1:],score[1:])
        values=describe(games,score)
        totals=[a+b for a,b in zip(totals,values)]
        ndiff+=len(mismatch)
        wdiff+=wd
        print(j,*values,len(mismatch),"unfinished" if partial_set else int(wd),sep="\t")
    print(f"{args.stage} summary: {target-first_set+1} sets, {totals[0]} games, {totals[1]} plies, plus W-L-D "
          f"{totals[2]}-{totals[3]}-{totals[4]}, {ndiff} different move lists, {wdiff} different W-L-D lines, "
          f"{rdiff} different game outcomes vs R1.")
    if first is not None:
        j,(rnd,game_id),ply,g,b=first
        print(f"First differing move list: set {j}, round {rnd}, game {game_id}, White {g.white}, "
              f"Black {g.black}, first differing played ply {ply+1}.\nOpening FEN {g.fen}")
        for tag,seq in (("R1",b.moves),(args.stage,g.moves)):
            prefix=list(seq[:ply+1])
            if ply==len(seq): prefix.append("<end of game>")
            print(tag," ".join(prefix))
    if first_wld:
        print("First differing W-L-D: set",first_wld[0],"R1",first_wld[1],args.stage,first_wld[2])
    if target!=(1 if args.stage=="C24" else 80) or args.partial_last:
        print("Partial stage through last requested complete pair set.")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results",type=Path)
    parser.add_argument("stage",choices=("R1","R2","C24","K1"))
    parser.add_argument("--single",type=int,help="audit only this pair set")
    parser.add_argument("--partial-last",action="store_true",help="include only finished PGN games from an interrupted final set")
    parser.add_argument("--through",type=int,help="restrict to this many complete pair sets")
    summarize(parser.parse_args())
