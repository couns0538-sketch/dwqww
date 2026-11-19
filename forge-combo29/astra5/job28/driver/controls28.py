"""Play the Job 28 start-position controls and compare exact first-search rows to the PC."""
import argparse
import asyncio
import csv
import hashlib
import json
import os
from pathlib import Path
import traceback
from contextlib import redirect_stderr, redirect_stdout

from game28 import GAME_COLS, chess, play, utc

HERE=Path(__file__).resolve().parent
RESULTS=Path(os.environ.get("JOB28_RESULTS",HERE/"results"))
EXE=Path(os.environ.get("JOB28_NC_EXE","/workspace/work/run23/job26work/P/build/forge"))
NC_SHA="9f95f854dd0dd6dd5c201a8303cc52dfbbcc74e4796b0b6850e216ab756b68e3"
ODD=["1 21600 d2d4","2 39366 g8f6","3 23305 c2c4"]
EVEN=["1 28565 d2d4","2 39366 g8f6","3 34511 c2c4"]
SPECIAL=["1 28565 d2d4","2 95535 c7c5","3 18811 d4d5"]
TARGETS=[("f49482fe2b9738aa",470764,ODD),("749f902e91070fc2",507873,EVEN),
         ("f7dc1451fef2f337",583536,EVEN),("af5f929dd8c03cc2",551293,SPECIAL),
         ("fb0a79e5c1ffcd06",433827,ODD),("749f902e91070fc2",507873,EVEN)]
C28_HASH="492d271d43b7ce03"
C28_SUM=485583
CLOCK_TARGETS={3:(3290,4084),5:(4661,4211)}



async def run(stage,dest):
    with EXE.open("rb") as f: actual=hashlib.file_digest(f,"sha256").hexdigest()
    if actual!=NC_SHA or chess.__version__!="1.11.2": raise RuntimeError("executable or python-chess version differs")
    if stage=="C28" and not json.loads((RESULTS/"K28/gate.json").read_text())["passed"]:
        raise RuntimeError("K28 gate did not pass")
    games_to_play=range(1,7) if stage=="K28" else (3,)
    (dest/"inputs.json").write_text(json.dumps(dict(exe=str(EXE.resolve()),exe_sha256=actual,fen=chess.STARTING_FEN,
         python_chess=chess.__version__,clock_divisor=100,initial_clocks=[6000,6000],increment=60,
         execution="One game at a time, two fresh UCI engines per game; max one active search."),indent=2)+"\n")
    checks=[]; passed=True; began=utc()
    with (dest/"games.tsv").open("x",newline="",buffering=1) as games,(dest/"comparison.tsv").open("x",newline="",buffering=1) as compare:
        gw=csv.writer(games,delimiter="\t",lineterminator="\n");gw.writerow(GAME_COLS)
        cw=csv.writer(compare,delimiter="\t",lineterminator="\n")
        cw.writerow(["pair","color_game","game","kept_rows","sha","expected_sha","sum_N","expected_sum_N","first_three","reference_first_three","check"])
        for g in games_to_play:
            k=(g+1)//2
            outcome=await play(EXE,stage,dest,g,k,chess.STARTING_FEN)
            gw.writerow(outcome)
            with (dest/f"g{g:04d}"/"searches.tsv").open() as f:
                rows=list(csv.DictReader(f,delimiter="\t"))[:20]
            lines=[r['ply']+' '+r['N']+' '+r['bestmove'] for r in rows]
            data=''.join(x+'\n' for x in lines).encode('ascii')
            (dest/f"first20-g{g:04d}.txt").write_bytes(data)
            sig=hashlib.sha256(data).hexdigest()[:16]; nodes=sum(int(r['N']) for r in rows)
            want_sig,want_sum,first_three=TARGETS[g-1]
            if stage=="K28":
                ok=len(rows)==20 and sig==want_sig and nodes==want_sum and lines[:3]==first_three
                if g in CLOCK_TARGETS:
                    clocks=(int(rows[18]["clock_after"]),int(rows[19]["clock_after"])) if len(rows)==20 else (None,None)
                    ok=ok and clocks==CLOCK_TARGETS[g]
                    checks.append(dict(game=g,pair=k,color_game=1,white_after_ply19=clocks[0],
                                       black_after_ply20=clocks[1],expected=list(CLOCK_TARGETS[g])))
            else:
                with (RESULTS/"K28"/"first20-g0003.txt").open("rb") as f:
                    reference=hashlib.file_digest(f,"sha256").hexdigest()[:16]
                ok=len(rows)==20 and sig==C28_HASH and nodes==C28_SUM and sig!=reference and reference==want_sig
                checks.append(dict(game=g,changed_from_K28_pair2_game1=(sig!=reference),K28_reference=reference))
                want_sig,want_sum=C28_HASH,C28_SUM
            passed=passed and ok
            cw.writerow([k,1+(g-1)%2,g,len(rows),sig,want_sig,
                       nodes,want_sum,' / '.join(lines[:3]),
                       ' / '.join(first_three) if stage=="K28" else "","pass" if ok else "fail"])
            first_difference=next((dict(row=i+1,observed=b,expected=a) for i,(a,b) in enumerate(zip(first_three,lines[:3])) if a!=b),None) if stage=="K28" else None
            checks.append(dict(game=g,passed=ok,first_three_difference=first_difference))
            print(utc(),stage,g,sig,nodes,ok,flush=True)
    (dest/"gate.json").write_text(json.dumps(dict(stage=stage,passed=passed,started_utc=began,ended_utc=utc(),checks=checks),indent=2)+"\n")
    return passed


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage",choices=("K28","C28"))
    stage=parser.parse_args().stage
    dest=RESULTS/stage;dest.mkdir(parents=True,exist_ok=False)
    with (dest/"controller.log").open("x",buffering=1) as log,redirect_stdout(log),redirect_stderr(log):
        try: ok=asyncio.run(run(stage,dest))
        except BaseException: traceback.print_exc();raise SystemExit(2)
    return 0 if ok else 1


if __name__=="__main__":
    raise SystemExit(main())
