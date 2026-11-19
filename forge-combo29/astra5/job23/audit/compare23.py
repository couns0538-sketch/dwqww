"""Verify per-game byte slices and compare job 23 record streams to each other and to job 22."""
import argparse
import csv
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path


FIRST = 700001
LAST = 702000
R_COMMIT = "040834de294a31f81a3d6aa54a605af692a4fcb4"
R_HASH = "fb1420546364b50aa244b1fb1c2465db8edce55b3907a927f56e06979ab75dcc"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_records(directory):
    """Verify each part and the concatenation when a split-file manifest accompanies the data."""
    manifest = directory / "records-manifest.tsv"
    if not manifest.exists():
        return (directory / "records.txt").read_bytes()
    with manifest.open(newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    parts = []
    whole = [r for r in rows if r["kind"] == "whole"]
    if len(whole) != 1:
        raise ValueError(f"{manifest}: expected one whole-file entry")
    for part in (r for r in rows if r["kind"] == "part"):
        name = part["file"]
        if name != Path(name).name:
            raise ValueError(f"{manifest}: invalid part name")
        raw = (directory / name).read_bytes()
        if (len(raw),raw.count(b"\n"),sha(raw)) != (int(part["bytes"]),int(part["rows"]),part["sha256"]):
            raise ValueError(f"{manifest}: part differs: {name}")
        parts.append(raw)
    raw = b"".join(parts)
    w = whole[0]
    if (len(raw),raw.count(b"\n"),sha(raw)) != (int(w["bytes"]),int(w["rows"]),w["sha256"]):
        raise ValueError(f"{manifest}: concatenation differs")
    return raw


@dataclass
class Game:
    number: int
    data: bytes
    rows: int
    na: int
    nodes: int


def verified_games(raw, receipts):
    games, start = [], 0
    with receipts.open(encoding="ascii", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        for i,r in enumerate(reader,FIRST):
            game,end = int(r["book_line"]),int(r["record_bytes"])
            if game != i or not start <= end <= len(raw) or not r["end_utc"]:
                raise ValueError(f"{receipts}: bad ID, offset or completion receipt at {i}")
            data=raw[start:end]
            lines=data.splitlines(keepends=True)
            nodes=na=0
            for ply,line in enumerate(lines,8):
                if not line.endswith(b"\n") or b"\r" in line:
                    raise ValueError(f"{receipts}: non-LF record {game}/{ply}")
                fields=line[:-1].split(b" ")
                if len(fields)!=4 or fields[:2]!=[str(game).encode(),str(ply).encode()] or not fields[2]:
                    raise ValueError(f"{receipts}: malformed record {line!r}")
                if fields[3]==b"NA":
                    na += 1
                else:
                    if not fields[3].isdigit():
                        raise ValueError(f"{receipts}: malformed node value {line!r}")
                    nodes += int(fields[3])
            if (len(lines),na,nodes)!=(int(r["plies"]),int(r["na"]),int(r["nodes"])):
                raise ValueError(f"{receipts}: totals disagree at game {game}")
            games.append(Game(game,data,len(lines),na,nodes))
            start=end
    if not games or start!=len(raw):
        raise ValueError(f"{receipts}: empty run or trailing bytes beyond final game")
    return games


def summarize(label,games):
    payload = b"".join(g.data for g in games)
    values=(len(games),sum(g.rows for g in games),sum(g.na for g in games),sum(g.nodes for g in games),sha(payload))
    print(f"{label}\t{games[0].number}-{games[-1].number}\t" + "\t".join(map(str,values)))
    return values


def compare(label,left,right,same,diff):
    if [g.number for g in left] != [g.number for g in right]:
        raise ValueError(f"{label}: game coverage differs")
    changed=[(a,b) for a,b in zip(left,right) if a.data!=b.data]
    print(f"{label}\t{diff if changed else same}\tdifferent_games={len(changed)} of {len(left)}")
    if changed:
        a,b=changed[0]
        al,bl=a.data.splitlines(keepends=True),b.data.splitlines(keepends=True)
        def item(lines,i):
            return lines[i] if i < len(lines) else b"<end of game>"
        index=next(i for i in range(max(len(al),len(bl))) if item(al,i)!=item(bl,i))
        print(f"first differing game={a.number} within-game record={index+1}")
        for tag,lines in (("left",al),("right",bl)):
            print(tag+"  "+item(lines,index).decode("ascii").rstrip("\n"))
    return len(changed)


def prepare(args):
    data=args.records.read_bytes()
    if sha(data)!=R_HASH:
        raise ValueError("historical L1 r15d SHA-256 differs from job 22 report")
    games=verified_games(data,args.games)
    totals=summarize("Job22 L1 r15d, full pinned source",games)
    if totals[:4]!=(5000,579956,0,2409009543):
        raise ValueError(f"historical full counts differ: {totals}")
    chosen=[g for g in games if g.number<=LAST]
    if chosen[-1].number!=LAST:
        raise ValueError("missing reference games")
    args.dest.mkdir(exist_ok=True,parents=True)
    (args.dest/"records.txt").write_bytes(b"".join(g.data for g in chosen))
    with args.games.open("rb") as f, (args.dest/"games.tsv").open("wb") as out:
        for _ in range(len(chosen)+1):
            out.write(next(f))
    verified=verified_games(read_records(args.dest),args.dest/"games.tsv")
    print(f"Job22 commit {R_COMMIT}, path forge-combo29/astra5/job22/L1-r15d")
    print("run\tgame range\tgames\trecords\tNA\tnode sum\tsha256")
    summarize("Job22 L1 r15d, reference prefix",verified)
    print("zero-row games: "+" ".join(str(g.number) for g in verified if not g.rows))


def results(args):
    reference=verified_games(read_records(args.reference),args.reference/"games.tsv")
    print("run/build\tgame range\tgames\trecords\tNA\tnode sum\tsha256")
    decisions={}
    for driver in ("S1","B1"):
        variants=[]
        for build in ("r15d","kF"):
            folder=args.runs/f"{driver}-{build}"
            games=verified_games(read_records(folder),folder/"games.tsv")
            if games[-1].number>LAST:
                raise ValueError(f"{folder}: game outside requested range")
            summarize(driver+" "+build,games)
            variants.append(games)
        r,k=variants
        decisions[driver]=compare(driver+" r15d/kF",r,k,"IDENTICAL","DIFFERS")
        decisions[driver+"R"]=compare(driver+" r15d/R",r,reference[:len(r)],"MATCHES R","DIFFERS FROM R")
    print("Declared job reading: "+("KEEPS" if not any(decisions[k] for k in ("S1","S1R","B1")) else "KEEPS criteria failed"))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("prepare",help="verify the full job 22 L1 file then cut 700001-702000")
    p.add_argument("records",type=Path)
    p.add_argument("games",type=Path)
    p.add_argument("dest",type=Path)
    p=sub.add_parser("results",help="verify and compare four job 23 archives or raw directories")
    p.add_argument("runs",type=Path)
    p.add_argument("reference",type=Path)
    args=parser.parse_args()
    if args.cmd=="prepare":
        prepare(args)
    else:
        results(args)


if __name__=="__main__":
    try:
        main()
    except (ValueError,OSError) as error:
        sys.exit(str(error))
