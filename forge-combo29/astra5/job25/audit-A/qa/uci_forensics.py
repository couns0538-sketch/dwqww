"""Independent job 25 Part A readback of raw UCI order, timestamps, moves and node maxima."""
import argparse
from collections import Counter
import csv
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
import re
import statistics

import chess


BOUND = 100064
ONE_SECOND = 10**9
TOKEN = re.compile(r"(?:^|\s)nodes\s+(\d+)(?=\s|$)")


def checked(value, reason):
    if not value:
        raise ValueError(reason)


def split_payload(directory):
    whole = directory / "uci.log"
    if whole.is_file():
        checked(whole.stat().st_size <= 20_000_000, "uci.log exceeds 20 MB unsplit")
        return whole.read_bytes(), 1
    parts = sorted(directory.glob("uci.part*.log"))
    checked(parts and all(x.stat().st_size <= 15_000_000 for x in parts), "missing or oversized log parts")
    checked(all(x.name == f"uci.part{i:04d}.log" for i,x in enumerate(parts,1)), "non-contiguous split log parts")
    return b"".join(x.read_bytes() for x in parts), len(parts)


def read(directory, fens, threads, reference):
    payload,np = split_payload(directory)
    rows = list(csv.DictReader((directory/"searches.tsv").read_text().splitlines(), delimiter="\t"))
    meta = (directory/"run.meta").read_text()
    checked("exit 0" in meta, f"{directory}: missing completed process receipt")
    checked(len(rows)==240, f"{directory}: {len(rows)} search receipts")
    raw = payload.decode('ascii').splitlines()
    events = []
    for n,line in enumerate(raw,1):
        stamp,direction,content = line.split(" ",2)
        checked(direction in ("<",">") and stamp.isdecimal(), f"bad raw line {n}")
        events.append((int(stamp), direction, content))
    settings=[content for _,direction,content in events if direction==">" and content.startswith("setoption ")]
    expected_settings=[s.replace("Threads value 1",f"Threads value {threads}") for s in reference]
    checked(settings[:-2]==expected_settings and settings[-2].startswith("setoption name NNUEArchFile value ")
            and settings[-1]=="setoption name NNUEArch value true","wrong or misordered UCI settings")
    for marker in ("NNUE v3 loaded","NNUE v3 active"):
        checked(any(marker in c and "30ab43b4ba5db5f3" in c for _,d,c in events if d=="<"), marker)
    checked(events[-1][1:]==(">","quit"), "missing clean quit")
    starts=[i for i,e in enumerate(events) if e[1:]==(">","ucinewgame")]
    checked(len(starts)==240,"wrong number of ucinewgame commands")
    scans = []
    problems = []
    most = []
    total_info=0
    for k,(start,end,row) in enumerate(zip(starts,starts[1:]+[len(events)-1],rows,strict=True)):
        number=k//8+1
        rep=k%8+1
        prefix = [(">","ucinewgame"),(">","isready"),("<","readyok"),(">","position fen "+fens[number-1]),(">","go nodes 100000")]
        msg = f"{directory.parent.name} {directory.name} position={number} repeat={rep}"
        checked([e[1:] for e in events[start:start+5]]==prefix, msg+" command sequence")
        go_ns=events[start+4][0]
        best=[]
        values=[]
        final=None
        infos=0
        first_over=None
        for idx in range(start+5,end):
            t,d,s=events[idx]
            if d=="<" and s.startswith("info "):
                infos+=1
                tok=TOKEN.findall(s)
                if tok:
                    values.extend(map(int,tok))
                    if first_over is None and any(int(x)>BOUND for x in tok):
                        first_over=(t,idx+1)
                    if " depth " in s:
                        final=s
            if d=="<" and s.startswith("bestmove "):
                best.append((t,idx+1,s.split()[1]))
        checked(len(best)==1 and final is not None and values, msg+" missing or duplicate bestmove/info")
        t,ln,move=best[0]
        elapsed=t-go_ns
        board=chess.Board(fens[number-1])
        try:
            legal=board.is_legal(chess.Move.from_uci(move))
        except ValueError:
            legal=False
        timely=0<=elapsed<=60*ONE_SECOND
        if first_over:
            ft,fl=first_over
            problems.append((ft,msg+" node budget",fl,raw[fl-1]))
        if not timely:
            problems.append((go_ns+60*ONE_SECOND,msg+" 60s deadline",ln,raw[ln-1]))
        if not legal:
            problems.append((t,msg+" illegal bestmove",ln,raw[ln-1]))
        fields=final.split()
        score_ix=fields.index("score")
        score_fields=fields[score_ix+1:score_ix+3]
        if fields[score_ix+3] in ("lowerbound","upperbound"):
            score_fields.append(fields[score_ix+3])
        score=" ".join(score_fields)
        lastdepth=int(fields[fields.index("depth")+1])
        lastnodes=int(fields[fields.index("nodes")+1])
        pv=" ".join(fields[fields.index("pv")+1:])
        want=(number,rep,lastdepth,score,lastnodes,pv,move,int(legal),int(timely),elapsed,start+1,ln,infos)
        got=(int(row["position"]),int(row["repeat"]),int(row["depth"]),row["score"],int(row["nodes"]),row["pv"],
             row["bestmove"],int(row["legal"]),int(row["within60"]),int(Decimal(row["elapsed_s"])*ONE_SECOND),
             int(row["first_raw_line"]),int(row["last_raw_line"]),int(row["info_count"]))
        checked(got==want,msg+f" receipt mismatch: {got!r} vs {want!r}")
        scans.append((number,rep,lastdepth,lastnodes,move,elapsed,legal,timely,first_over is not None))
        most.append(max(values)); total_info+=infos
    ds=[r[2] for r in scans]; ns=[r[3] for r in scans]
    modes=[]
    for n in range(30):
        counts=Counter(r[4] for r in scans[8*n:8*n+8])
        modes.append(sorted(m for m,c in counts.items() if c==max(counts.values())))
    print(f"{directory.parent.name} {directory.name} threads={threads} searches=240 infos={total_info} "
          f"max_any_info_nodes={max(most)} over_bound_searches={sum(r[-1] for r in scans)} "
          f"slow={sum(not r[7] for r in scans)} illegal={sum(not r[6] for r in scans)} "
          f"slowest_ns={max(r[5] for r in scans)} raw_bytes={len(payload)} parts={np} sha256={sha256(payload).hexdigest()}")
    print(f"last_depth median={statistics.median(ds)} range={min(ds)}..{max(ds)} "
          f"last_nodes median={statistics.median(ns)} range={min(ns)}..{max(ns)} "
          f"positions_with_varied_bestmove={sum(len({r[4] for r in scans[8*n:8*n+8]})>1 for n in range(30))} "
          f"positions_with_tied_modes={[i for i,m in enumerate(modes,1) if len(m)>1]}")
    if problems:
        first=min(problems)
        print(f"FIRST problem {first[1]}, timestamp {first[0]} log line {first[2]}: {first[3]}")
    return scans,modes,problems,[(r["depth"],r["score"],r["nodes"],r["pv"],r["bestmove"]) for r in rows]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage",type=Path)
    p.add_argument("positions",type=Path)
    p.add_argument("pc20",type=Path)
    a=p.parse_args()
    threads={"A1":1,"A2":2,"A4":4}[a.stage.name]
    checked(chess.__version__=="1.11.2","python-chess chess 1.11.2 required")
    lines=a.positions.read_text().splitlines()[:30]
    checked(len(lines)==30,"expected 30 opening rows")
    fens=[" ".join(s.split()[:4]+["0","1"]) for s in lines]
    print(f"Move validator: python-chess chess {chess.__version__}; elapsed = bestmove receipt ns minus go send ns.")
    results={}
    for build in ("r15d","kF"):
        results[build]=read(a.stage/build,fens,threads,a.pc20.read_text().splitlines())
    rs,_,_,rvalues=results["r15d"]
    _,kfm,_,kvalues=results["kF"]
    if threads==1:
        for pos in range(30):
            equivalent=set(rvalues[8*pos:8*pos+8] + kvalues[8*pos:8*pos+8])
            checked(len(equivalent)==1,f"KA1 mismatch position {pos+1}")
        print("KA1: all 30 positions have identical (depth, score, nodes, PV, bestmove) across eight repeats on both builds.")
    if threads!=1:
        none=[]; some=[]; ties=[]
        for i,k in enumerate(kfm):
            r={r[4] for r in rs[8*i:8*i+8]}
            if not set(k)&r: none.append(i+1)
            elif not set(k)<=r: some.append(i+1)
            if len(k)>1: ties.append((i+1,k,sorted(r)))
        print(f"kF modes absent in r15d replies: {none}; only a subset of tied kF modes in r15d replies: {some}")
        for pos,k,r in ties:
            print(f"tied kF modes position {pos}: {k}; r15d observed {r}")
    problems=[entry for _,_,probs,_ in results.values() for entry in probs]
    if problems:
        t,msg,ln,raw=min(problems)
        print(f"Earliest raw witness by monotonic receipt: {msg} at {t}, line {ln}: {raw}")


if __name__ == '__main__':
    main()
