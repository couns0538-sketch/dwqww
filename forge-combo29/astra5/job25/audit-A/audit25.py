"""Independent readback of the Job 25 hard-node searches; the ca2 subcommand only tests dispersion."""
import argparse
import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import re
from statistics import median
import sys

import chess


LIMIT = 100064
BUILDS = ("r15d", "kF")
LINE = re.compile(r"^(\d+) ([<>]) (.*)$")


def rows(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


@dataclass
class Search:
    pos: int
    rep: int
    fen: str
    started: int
    stopped: int
    start_line: int
    move_line: int
    move: str
    info: list

    def last(self):
        for no,t,line in reversed(self.info):
            fields = line.split()
            if all(k in fields for k in ("depth", "score", "nodes","pv")):
                score_at=fields.index("score")+1
                score=fields[score_at:score_at+2]
                if fields[score_at+2:score_at+3] in (["lowerbound"],["upperbound"]):
                    score.append(fields[score_at+2])
                return (int(fields[fields.index("depth")+1])," ".join(score),
                        int(fields[fields.index("nodes")+1])," ".join(fields[fields.index("pv")+1:]),self.move), (no,t,line)
        raise ValueError(f"position {self.pos} repeat {self.rep}: missing structured info")

    def all_nodes(self):
        for ln,t,line in self.info:
            for m in re.finditer(r"(?:^|\s)nodes\s+(\d+)(?=\s|$)",line):
                yield int(m[1]),ln,t,line


def read_arm(root, fens, tcount, build, count=240):
    arm=root/f"A{tcount}"/build
    log=arm/"uci.log"
    found=[]
    new=asked=ready=False
    fen=None
    active=None
    options=[]
    markers=set()
    with log.open() as f:
        for no,raw in enumerate(f,1):
            raw=raw.rstrip("\r\n")
            m=LINE.fullmatch(raw)
            if not m: raise ValueError(f"{log}:{no}: malformed raw transcript")
            ts,side,text=int(m[1]),m[2],m[3]
            if side==">":
                if text.startswith("setoption "):
                    options.append(text)
                elif text=="ucinewgame":
                    new,asked,ready,fen=True,False,False,None
                elif text=="isready" and new:
                    asked=True
                elif text.startswith("position fen "):
                    if not ready: raise ValueError(f"{log}:{no}: FEN before readyok")
                    fen=text[len("position fen "):]
                elif text.startswith("go "):
                    if not (text=="go nodes 100000" and fen and active is None):
                        raise ValueError(f"{log}:{no}: unexpected go sequence")
                    n=len(found)
                    pos,rep=divmod(n,8)
                    if fen!=fens[pos]:
                        raise ValueError(f"{log}:{no}: input FEN differs at position {pos+1}")
                    active=Search(pos+1,rep+1,fen,ts,0,no,0,"",[])
                    new=asked=ready=False
            else:
                if asked and text=="readyok":
                    ready=True
                for tag in ("NNUE v3 loaded:","NNUE v3 active:"):
                    if tag in text and "checksum 30ab43b4ba5db5f3" in text:
                        markers.add(tag)
                if active is not None:
                    if text.startswith("info "):
                        active.info.append((no,ts,text))
                    elif text.startswith("bestmove "):
                        active.stopped,active.move_line,active.move=ts,no,text.split()[1]
                        found.append(active)
                        active=None
    if active is not None:
        found.append(active)
    if len(markers)!=2 or f"setoption name Threads value {tcount}" not in options:
        raise ValueError(f"{arm}: wrong net, missing v3 active/loaded marker or wrong thread option")
    if len(found)!=count:
        raise ValueError(f"{arm}: read {len(found)} searches, expected {count}")
    return found


def compare_tsv(root,t,build,samples):
    summary=rows(root/f"A{t}"/build/"searches.tsv")
    if len(summary)!=len(samples):
        raise ValueError(f"A{t}/{build}: wrong number of TSV rows")
    for s,r in zip(samples,summary):
        sig,_=s.last()
        recorded=(int(r["depth"]),r["score"],int(r["nodes"]),r["pv"],r["bestmove"])
        if (s.pos,s.rep)!=(int(r["position"]),int(r["repeat"])) or sig!=recorded:
            raise ValueError(f"A{t}/{build} {s.pos}/{s.rep}: raw {sig}, TSV {r}")


def read_both(root,fens,t):
    data={b:read_arm(root,fens,t,b) for b in BUILDS}
    for b in BUILDS:
        compare_tsv(root,t,b,data[b])
    return data


def ka1(data):
    print("position\trepeats_each\tdepth\tscore\tnodes\tbestmove\tpv\tka1")
    for pos in range(1,31):
        ref=data["r15d"][(pos-1)*8]
        sig,refline=ref.last()
        for build in BUILDS:
            for x in data[build][(pos-1)*8:pos*8]:
                actual,line=x.last()
                if actual!=sig:
                    raise ValueError(f"KA1 differs for {build} position {pos} repeat {x.rep}. "
                                     f"r15d repeat 1: {refline}, bestmove {ref.move}. {build}: {line}, bestmove {x.move}")
        print(pos,8,sig[0],sig[1],sig[2],sig[4],sig[3],"equal",sep="\t")
    print("KA1 PASS: all eight repeat signatures of each build and both builds agree for 30/30 positions.")


def ca2(data):
    # This gate compares the last counts across repeats only. It never visits intermediate node values.
    print("position\tr15d distinct last counts\tkF distinct last counts")
    counts={b:0 for b in BUILDS}
    for pos in range(1,31):
        distinct=[]
        for b in BUILDS:
            values={s.last()[0][2] for s in data[b][(pos-1)*8:pos*8]}
            distinct.append(len(values))
            counts[b]+=len(values)>1
        print(pos,*distinct,sep="\t")
    print(f"CA2 varied positions (out of 30): r15d={counts['r15d']}, kF={counts['kF']}.")
    if any(n<15 for n in counts.values()):
        raise ValueError("CA2 failed: fewer than 15 positions had varying last counts")
    print("CA2 PASS")


def stats(args,fens):
    args.output.mkdir(exist_ok=True,parents=True)
    legal=[set(m.uci() for m in chess.Board(f).legal_moves) for f in fens]
    with (args.output/"search-readback.tsv").open("w") as search_out, (args.output/"modes.tsv").open("w") as mode_out, (args.output/"spread.tsv").open("w") as spread_out, (args.output/"threshold-cases.tsv").open("w") as raw_out:
        print("part\tbuild\tposition\trepeat\tgo line\tanswer line\tms to bestmove\tlegal\twithin60\tlargest nodes\tlast nodes\tlast depth\tbestmove",file=search_out)
        print("part\tposition\tr15d bestmove counts\tkF bestmove counts\tkF co-modes\tco-modes present in r15d\tany present\tall present",file=mode_out)
        print("part\tbuild\tsearches\tlast depth median\tmin\tmax\tlast nodes median\tmin\tmax\tpositions with varying move",file=spread_out)
        print("part\tbuild\tposition\trepeat\tfirst breach raw line number\tmonotonic ns\tengine line",file=raw_out)
        print("part\tbuild\tsearches\tmax over all info\tsearches above bound\tmissing bestmove within 60s\tillegal bestmoves\tinfo lines")
        for t in args.threads:
            data=read_both(args.root,fens,t)
            for build,records in data.items():
                maximum=missing=bad=above=infos=0
                depths=[]; lastnodes=[]
                for s in records:
                    allnodes=list(s.all_nodes())
                    if not allnodes:
                        raise ValueError(f"A{t}/{build}, position {s.pos} repeat {s.rep}: no reported nodes")
                    peak=max(x[0] for x in allnodes)
                    info=next((x for x in allnodes if x[0]>LIMIT),None)
                    if info:
                        _,line,ns,raw=info
                        print(f"A{t}",build,s.pos,s.rep,line,ns,raw,sep="\t",file=raw_out)
                    sig,_=s.last()
                    delta=s.stopped-s.started if s.stopped else None
                    timely=delta is not None and 0<=delta<=60_000_000_000
                    valid=s.move in legal[s.pos-1]
                    print(f"A{t}",build,s.pos,s.rep,s.start_line,s.move_line,
                          f"{delta/1e6:.6f}" if delta is not None else "NA",int(valid),int(timely),peak,
                          sig[2],sig[0],s.move,sep="\t",file=search_out)
                    depths.append(sig[0]);lastnodes.append(sig[2])
                    infos+=len(s.info);maximum=max(maximum,peak);above+=info is not None
                    missing+=not timely;bad+=bool(s.move) and not valid
                varying=sum(len({s.move for s in records[8*p:8*p+8]})>1 for p in range(30))
                print(f"A{t}",build,len(records),maximum,above,missing,bad,infos,sep="\t")
                print(f"A{t}",build,len(records),median(depths),min(depths),max(depths),median(lastnodes),
                      min(lastnodes),max(lastnodes),varying,sep="\t",file=spread_out)
            for pos in range(1,31):
                move_counts={b:Counter(s.move for s in data[b][(pos-1)*8:pos*8]) for b in BUILDS}
                def encode(b): return ",".join(f"{m}={n}" for m,n in sorted(move_counts[b].items()))
                modes=sorted(m for m,n in move_counts["kF"].items() if n==max(move_counts["kF"].values()))
                seen=[m for m in modes if m in move_counts["r15d"]]
                print(f"A{t}",pos,encode("r15d"),encode("kF"),",".join(modes),",".join(seen) or "none",
                      int(bool(seen)),int(len(seen)==len(modes)),sep="\t",file=mode_out)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("ka1","ca2","stats"))
    p.add_argument("root",type=Path)
    p.add_argument("epd",type=Path)
    p.add_argument("--output",type=Path)
    p.add_argument("--threads",type=int,choices=(1,2,4),nargs="+",default=(1,2,4))
    args=p.parse_args()
    fens=[" ".join(x.split()[:4])+" 0 1" for x in args.epd.read_text().splitlines()]
    if len(fens)!=30: p.error("expected exactly 30 EPD records")
    if args.mode=="stats":
        if args.output is None: p.error("stats requires --output")
        stats(args,fens)
    elif args.mode=="ka1":
        ka1(read_both(args.root,fens,1))
    else:
        ca2(read_both(args.root,fens,2))


if __name__=="__main__":
    try:
        main()
    except (OSError,ValueError,KeyError,IndexError) as err:
        sys.exit(str(err))
