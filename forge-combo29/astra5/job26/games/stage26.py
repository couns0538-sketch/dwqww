"""Run one node-time stage, at most four active games, with independent per-game engines."""
import argparse
import asyncio
import csv
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from game26 import GAME_COLS, chess, play, utc

ROOT=Path(__file__).resolve().parent
RESULTS=Path(os.environ.get("JOB26_RESULTS", ROOT/"results"))
CLOSE_PAIRS=datetime.fromisoformat(os.getenv("JOB26_CLOSE_PAIRS","2026-11-19T19:11:02+00:00")).timestamp()
HARD=datetime.fromisoformat(os.getenv("JOB26_HARD_STOP","2026-11-19T19:16:02+00:00")).timestamp()
BOOK_SHA="889e8db12ee327cae68b29ada3458a2fb957cf8f5563d29a7fd13d850ff3f638"
NC_SHA="9f95f854dd0dd6dd5c201a8303cc52dfbbcc74e4796b0b6850e216ab756b68e3"


def sha(path):
    with path.open("rb") as f: return hashlib.file_digest(f,"sha256").hexdigest()


def signature(stage,g):
    path=stage/f"g{g:04d}"
    with (path/"result.tsv").open() as f: result=next(csv.DictReader(f,delimiter="\t"))
    with (path/"searches.tsv").open() as f: searches=list(csv.DictReader(f,delimiter="\t"))
    return ([result[k] for k in GAME_COLS[:9]],[(r["N"],r["bestmove"]) for r in searches])


def compare(stage,dest):
    base=RESULTS/"K26-1"; differences=[]
    for game in range(1,21):
        ar,a=signature(base,game);br,b=signature(dest,game)
        if a!=b or ar!=br:
            n=next((i for i,(x,y) in enumerate(zip(a,b)) if x!=y),min(len(a),len(b)))
            differences.append(dict(game=game,ply=n+1,reference=a[n] if n<len(a) else None,
                observed=b[n] if n<len(b) else None,reference_result=ar,observed_result=br))
    ok=(not differences) if stage=="K26-2" else bool(differences)
    report=dict(games=20,games_different=len(differences),first=differences[0] if differences else None,
                differing_game_ids=[r["game"] for r in differences],passes=ok)
    (dest/"compare.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report),flush=True)
    if not ok: raise ValueError(f"known answer/control failed: {report}")


async def run(stage,exe,book):
    exe=exe.resolve(strict=True);book=book.resolve(strict=True)
    if sha(exe)!=NC_SHA or sha(book)!=BOOK_SHA or chess.__version__!="1.11.2":
        raise ValueError("unexpected executable, book or python-chess version")
    fens=[" ".join(line.split()[:4])+" 0 1" for line in book.read_text().splitlines()]
    if len(fens)!=234: raise ValueError("unexpected opening count")
    if stage=="M": order=range(11,len(fens)+1)
    elif stage=="K26-2": order=range(10,0,-1)
    else: order=range(1,11)
    games=[(2*k-1+b,k) for k in order for b in (0,1)]
    width=min(4,len(os.sched_getaffinity(0))-1)
    if width<1: raise RuntimeError("no available game workers")
    dest=RESULTS/stage;dest.mkdir(parents=True,exist_ok=False)
    (dest/"inputs.json").write_text(json.dumps(dict(exe=str(exe),sha256=NC_SHA,book=str(book),book_sha256=BOOK_SHA,
        python_chess=chess.__version__,concurrent_games=width,clock_charge="N // 1000 on both controls and M",
        time_loss_clock="unchanged; losing attempted search included, unplayed move excluded from plies",
        wire="all commands and startup replies, all holds, final node and bestmove lines. Every reply of an interrupted search is saved."),
        indent=2)+"\n")
    active={}; paired={};done_pairs=[]; indexed=set(); next_i=0; stop_reason="all openings finished"
    with (dest/"games.tsv").open("x",newline="",buffering=1) as gf, (dest/"launch.tsv").open("x",buffering=1) as lf, (dest/"pairs.tsv").open("x",buffering=1) as pf:
        gw=csv.writer(gf,delimiter="\t",lineterminator="\n");gw.writerow(GAME_COLS)
        print("ordinal\tgame\topening\tutc",file=lf)
        print("opening\tgame_A_white\tgame_B_white\tcompleted_utc",file=pf)
        def register(answer):
            g,k=map(int,answer[:2])
            if g in indexed: return
            indexed.add(g);gw.writerow(answer)
            paired.setdefault(k,[]).append(g)
            if len(paired[k])==2:
                done_pairs.append(k)
                print(k,2*k-1,2*k,utc(),sep="\t",file=pf)
                print(stage,k,"pair completed",len(done_pairs),utc(),flush=True)
        try:
            while True:
                while len(active)<width and next_i<len(games):
                    g,k=games[next_i]
                    if time.time()>=HARD: raise TimeoutError("minute50 stop")
                    if stage=="M" and g%2 and time.time()>=CLOSE_PAIRS:
                        stop_reason="minute45 no new pair";break
                    next_i+=1
                    print(next_i,g,k,utc(),sep="\t",file=lf)
                    task=asyncio.create_task(play(exe,stage,dest,g,k,fens[k-1]))
                    active[task]=(g,k)
                if not active: break
                finished,_=await asyncio.wait(active,return_when=asyncio.FIRST_COMPLETED,timeout=max(0,HARD-time.time()))
                if not finished: raise TimeoutError("minute50 stop")
                for task in finished:
                    active.pop(task)
                    register(task.result())
        except BaseException as error:
            if isinstance(error,TimeoutError) and time.time()>=HARD-.2: stop_reason="minute50 stop"
            else: stop_reason="match halted: "+repr(error)
            for task in active: task.cancel()
            await asyncio.gather(*active,return_exceptions=True)
            # A game can finish before the deadline while its two UCI processes
            # are still quitting. Reconcile these already-written results.
            for g,k in games[:next_i]:
                receipt=dest/f"g{g:04d}"/"result.tsv"
                if g not in indexed and receipt.exists():
                    with receipt.open() as f:
                        row=next(csv.DictReader(f,delimiter="\t"))
                    if datetime.fromisoformat(row["ended_utc"]).timestamp()<=HARD:
                        register([row[col] for col in GAME_COLS])
            (dest/"stop.txt").write_text(f"{utc()} {stop_reason}\n")
            if not stop_reason.startswith("minute50"): raise
        finally:
            (dest/"end.json").write_text(json.dumps(dict(stage=stage,utc=utc(),reason=stop_reason,
                  games_started=next_i,complete_pairs=len(done_pairs),complete_openings=sorted(done_pairs)),indent=2)+"\n")
    if stage in ("K26-2","C26") and len(done_pairs)==10: compare(stage,dest)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage",choices=("K26-1","K26-2","C26","M"))
    parser.add_argument("exe",type=Path)
    parser.add_argument("book",type=Path)
    args=parser.parse_args()
    asyncio.run(run(args.stage,args.exe,args.book))
