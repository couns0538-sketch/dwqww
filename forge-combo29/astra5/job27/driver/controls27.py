"""Play the Job 27 start-position controls and compare exact first-search rows to the PC."""
import argparse
import asyncio
import csv
import hashlib
import json
import os
from pathlib import Path
import traceback
from contextlib import redirect_stderr, redirect_stdout

from game27 import GAME_COLS, chess, play, utc

HERE=Path(__file__).resolve().parent
RESULTS=Path(os.environ.get("JOB27_RESULTS",HERE/"results"))
EXE=Path(os.environ.get("JOB27_NC_EXE","/workspace/work/run23/job26work/P/build/forge"))
NC_SHA="9f95f854dd0dd6dd5c201a8303cc52dfbbcc74e4796b0b6850e216ab756b68e3"
ODD=["1 21600 d2d4","2 39366 g8f6","3 23305 c2c4"]
EVEN=["1 28565 d2d4","2 39366 g8f6","3 34511 c2c4"]
TARGETS=[("f49482fe2b9738aa",470764),("f0130049ccd2829f",592206),
         ("965681ae07f6c314",539887),("749f902e91070fc2",507873),
         ("93caf8323c20a6ea",529836),("6d5378c21381a5a2",604702)]


async def run(stage,dest):
    with EXE.open("rb") as f: actual=hashlib.file_digest(f,"sha256").hexdigest()
    if actual!=NC_SHA or chess.__version__!="1.11.2": raise RuntimeError("executable or python-chess version differs")
    if stage=="C27" and not json.loads((RESULTS/"K27/gate.json").read_text())["passed"]:
        raise RuntimeError("K27 gate did not pass")
    n=6 if stage=="K27" else 1
    (dest/"inputs.json").write_text(json.dumps(dict(exe=str(EXE.resolve()),exe_sha256=actual,fen=chess.STARTING_FEN,
         python_chess=chess.__version__,clock_divisor=100,initial_clocks=[6000,6000],increment=60,
         execution="One game at a time, two fresh UCI engines per game; max one active search."),indent=2)+"\n")
    checks=[]; passed=True; began=utc()
    with (dest/"games.tsv").open("x",newline="",buffering=1) as games,(dest/"comparison.tsv").open("x",newline="",buffering=1) as compare:
        gw=csv.writer(games,delimiter="\t",lineterminator="\n");gw.writerow(GAME_COLS)
        cw=csv.writer(compare,delimiter="\t",lineterminator="\n")
        cw.writerow(["pair","color_game","game","kept_rows","sha","expected_sha","sum_N","expected_sum_N","first_three","reference_first_three","check"])
        for g in range(1,n+1):
            k=(g+1)//2
            outcome=await play(EXE,stage,dest,g,k,chess.STARTING_FEN)
            gw.writerow(outcome)
            with (dest/f"g{g:04d}"/"searches.tsv").open() as f:
                rows=list(csv.DictReader(f,delimiter="\t"))[:20]
            lines=[r['ply']+' '+r['N']+' '+r['bestmove'] for r in rows]
            data=''.join(x+'\n' for x in lines).encode('ascii')
            (dest/f"first20-g{g:04d}.txt").write_bytes(data)
            sig=hashlib.sha256(data).hexdigest()[:16]; nodes=sum(int(r['N']) for r in rows)
            want_sig,want_sum=TARGETS[g-1]; first_three=ODD if g%2 else EVEN
            if stage=="K27":
                ok=len(rows)==20 and sig==want_sig and nodes==want_sum and lines[:3]==first_three
                if g==1:
                    clocks=(int(rows[18]["clock_after"]),int(rows[19]["clock_after"])) if len(rows)==20 else (None,None)
                    ok=ok and clocks==(4434,4070)
                    checks.append(dict(pair1_game1_white_after_ply19=clocks[0],black_after_ply20=clocks[1],expected=[4434,4070]))
            else:
                ok=bool(rows) and sig!=want_sig
            passed=passed and ok
            cw.writerow([k,1+(g-1)%2,g,len(rows),sig,want_sig if stage=="K27" else "differ from "+want_sig,
                       nodes,want_sum if stage=="K27" else "",' / '.join(lines[:3]),
                       ' / '.join(first_three) if stage=="K27" else "","pass" if ok else "fail"])
            first_difference=next((dict(row=i+1,observed=b,expected=a) for i,(a,b) in enumerate(zip(first_three,lines[:3])) if a!=b),None)
            checks.append(dict(game=g,passed=ok,first_three_difference=first_difference))
            print(utc(),stage,g,sig,nodes,ok,flush=True)
    (dest/"gate.json").write_text(json.dumps(dict(stage=stage,passed=passed,started_utc=began,ended_utc=utc(),checks=checks),indent=2)+"\n")
    return passed


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage",choices=("K27","C27"))
    stage=parser.parse_args().stage
    dest=RESULTS/stage;dest.mkdir(parents=True,exist_ok=False)
    with (dest/"controller.log").open("x",buffering=1) as log,redirect_stdout(log),redirect_stderr(log):
        try: ok=asyncio.run(run(stage,dest))
        except BaseException: traceback.print_exc();raise SystemExit(2)
    return 0 if ok else 1


if __name__=="__main__":
    raise SystemExit(main())
