"""Run one Job 26 node-clock pin or its positive control, with a fresh engine process."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

import chess


FIXED = [
    ("Threads",1), ("Hash",16), ("OwnBook","false"), ("MateAlphaGuard","true"),
    ("LmrQuietBase",93), ("LmrQuietDivisor",205), ("LmrNoisyBase",13), ("LmrNoisyDivisor",333),
    ("LmrHistoryDivisor",5643), ("NullMoveBase",5), ("LmpBase",8), ("HistoryPruneMultiplier",2220),
    ("HistoryBonusQuadratic",24), ("HistoryBonusLinear",54), ("HistoryBonusMax",2212), ("SingularDepth",6),
    ("IirDepth",2), ("NonPawnCorrection","true"), ("CuckooRep","true"), ("HistRework",2),
    ("TtPruneV2","true"), ("CorrHistV2","true"),
]
# suite, clock in node-ms, row signature, T, over count and reported over N
CASES={
    "O0":("O",6000,"3eac50dd8fd5297e",54326,0,None),
    "A0":("G",6000,"424d931234dd3ff9",98026,1,1585152),
    "A1":("G",6000,"5a85f018917c736f",82001,1,1585152),
    "B0":("G",2000,"244776b6649f2ce1",45372,2,675840),
    "C0":("G",300,"4e8210e936e59fd5",20715,7,174080),
    "CP1":("G",6000,None,None,None,None),
}
EPD_SHA={"O":"02d59eaf2515a4e11aecb78c5736db193812516f42ab8a6aa0b2411332186300",
         "G":"af3aefd80fcea207b215e95560f5921aa7a3bb9186d4cdfadf2e567207b5c54d"}
FOOTER = re.compile(r"info string softnodes nodes (\d+)$")
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def utc(): return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def split_if_large(path):
    if path.stat().st_size<=20_000_000:
        return
    manifest=path.with_name(path.name+".parts.tsv")
    full=digest(path)
    with path.open("rb") as src,manifest.open("x") as inf:
        print("part\tbytes\tsha256",file=inf)
        block=bytearray()
        count=0
        def store():
            nonlocal count
            count+=1
            p=path.with_name(f"{path.stem}.part{count:04d}{path.suffix}")
            p.write_bytes(block)
            print(p.name,len(block),digest(p),sep="\t",file=inf)
            block.clear()
        for line in src:
            if block and len(block)+len(line)>15_000_000: store()
            block.extend(line)
        if block: store()
        print("WHOLE",path.stat().st_size,full,sep="\t",file=inf)
    combined=hashlib.sha256()
    for index in range(1,count+1):
        combined.update(path.with_name(f"{path.stem}.part{index:04d}{path.suffix}").read_bytes())
    if combined.hexdigest()!=full: raise ValueError("split readback mismatch")
    path.unlink()


def run(args):
    suite,millis,expected,t0,n_over,n_value=CASES[args.case]
    epd=args.inputs/f"{suite}.epd"
    if digest(epd)!=EPD_SHA[suite]: raise ValueError(f"{epd}: EPD hash mismatch")
    fens=[" ".join(line.split()[:4])+" 0 1" for line in epd.read_text().splitlines()]
    if len(fens)!={"G":353,"O":200}[suite]: raise ValueError("EPD count mismatch")
    clock=2000 if args.case=="CP1" else 1000
    options=[*FIXED,("NodeClock",clock)]
    if args.case=="A1": options.append(("TmFinishIteration","true"))
    if args.cpu is not None: os.sched_setaffinity(0,{args.cpu})
    go=f"go wtime {millis} btime {millis} winc 60 binc 60"
    dest=args.out/args.case
    dest.mkdir(parents=True,exist_ok=False)
    exe=args.exe.resolve(strict=True)
    raw_path=dest/"uci.log"
    rowfile=dest/"rows.txt"
    overs=[]
    total=hold=actual_used=0
    signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(TimeoutError("engine response timed out")))
    with subprocess.Popen([str(exe)],cwd=exe.parent,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                          bufsize=1,text=True,encoding="utf-8") as proc, raw_path.open("x",buffering=1) as raw, \
         rowfile.open("x",buffering=1) as rows, (dest/"searches.tsv").open("x",buffering=1) as searches, \
         (dest/"run.meta").open("x",buffering=1) as meta:
        print(f"start UTC {utc()}\nexe {exe}\nsha256 {digest(exe)}\npid {proc.pid}\nCPU affinity {sorted(os.sched_getaffinity(0))}"
              f"\nEPD {epd}\nEPD SHA256 {digest(epd)}\npython-chess {chess.__version__}\nUTC clock and monotonic nanoseconds",file=meta)
        writer=csv.writer(searches,delimiter="\t",lineterminator="\n")
        writer.writerow(["index","fen","depth","last_nodes","bestmove","N","T1000","hold_lines"])
        def send(line):
            print(time.monotonic_ns(),">",line,file=raw)
            proc.stdin.write(line+"\n");proc.stdin.flush()
        def read():
            value=proc.stdout.readline()
            if not value: raise RuntimeError("unexpected EOF")
            line=value.rstrip("\r\n")
            print(time.monotonic_ns(),"<",line,file=raw)
            if any(x in line.lower() for x in ("unknown option","invalid value","error")):
                raise ValueError(f"engine rejected command: {line}")
            return line
        try:
            signal.alarm(120)
            send("uci")
            names=set()
            while (line:=read())!="uciok":
                m=re.match(r"option name (.+?) type ",line)
                if m: names.add(m[1])
            for name,value in options:
                if name not in names: raise ValueError(f"option missing: {name}")
                send(f"setoption name {name} value {value}")
            for i,fen in enumerate(fens,1):
                signal.alarm(120)
                send("ucinewgame")
                send("isready")
                while read()!="readyok": pass
                send("position fen "+fen)
                send(go)
                last=None
                footer=[]
                holds=0
                while True:
                    line=read()
                    if line.startswith("info depth ") and " nodes " in line:
                        fields=line.split()
                        last=int(fields[2]),int(fields[fields.index("nodes")+1])
                    if line.startswith("info string TmFinishIteration hold"): holds+=1
                    if m:=FOOTER.fullmatch(line): footer.append(int(m[1]))
                    if line.startswith("bestmove "):
                        move=line.split()[1]
                        break
                if last is None or len(footer)!=1:
                    raise ValueError(f"position {i}: missing depth info or nonunique footer {footer}")
                board=chess.Board(fen)
                if chess.Move.from_uci(move) not in board.legal_moves: raise ValueError(f"position {i}: illegal move {move}")
                depth,nodes=last
                N=footer[0]
                if N<nodes: raise ValueError(f"position {i}: N less than last completed nodes")
                if N>nodes: overs.append((i,depth,nodes,N,N-nodes))
                total+=N//1000; actual_used+=N//clock;hold+=holds>0
                print(i,depth,nodes,move,file=rows)
                writer.writerow((i,fen,depth,nodes,move,N,N//1000,holds))
            send("quit")
            proc.stdin.close()
            status=proc.wait(timeout=10)
            if status: raise ValueError(f"engine exited {status}")
            signal.alarm(0)
            print("end UTC",utc(),file=meta)
        finally:
            signal.alarm(0)
            if proc.poll() is None: proc.kill()
    sig=digest(rowfile)
    first=rowfile.read_text().splitlines()[0]
    firstpins={"O0":"1 16 172312 f1e2","A0":"1 16 170070 g7g6"}
    ns=sorted({x[3] for x in overs})
    ok=(sig[:16] != "424d931234dd3ff9" if args.case=="CP1" else
        sig[:16]==expected and total==t0 and len(overs)==n_over and
        ns==([n_value] if n_over else []) and (args.case!="A1" or hold==162) and first==firstpins.get(args.case,first))
    with (dest/"summary.txt").open("x") as f:
        print(f"Run {args.case} / {suite}, {len(fens)} positions, Threads 1, built-in evaluation, NodeClock {clock}\n{go}",file=f)
        print(f"Rows SHA256 {sig}\nRow signature {sig[:16]}\nFirst row {first}\nT (sum of floor N/1000) {total}"
              f"\nSum of floor N/NodeClock {actual_used}\nOver searches {len(overs)}\nDistinct N for over searches {ns}"
              f"\nSearches with TmFinishIteration hold {hold}\n{'PASS' if ok else 'FAIL'}",file=f)
    with (dest/"over.tsv").open("x") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n");w.writerow(["position","depth","last_nodes","N","difference"]);w.writerows(overs)
    split_if_large(raw_path)
    print((dest/"summary.txt").read_text(),end="",flush=True)
    if not ok: raise ValueError("known answer or control failed")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("case",choices=CASES)
    p.add_argument("exe",type=Path);p.add_argument("inputs",type=Path);p.add_argument("out",type=Path)
    p.add_argument("--cpu",type=int)
    run(p.parse_args())
