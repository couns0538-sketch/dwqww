"""Verify archived record rows against the literal final-info evidence and game receipts."""
import argparse
import csv
from hashlib import sha256
from itertools import zip_longest
from pathlib import Path


def stream(directory, name):
    with (directory / f"{name}-manifest.tsv").open() as f:
        entries = list(csv.DictReader(f, delimiter="\t"))
    whole = entries[-1]
    if whole["kind"] != "whole":
        raise ValueError(f"{directory}: missing whole {name} entry")
    total_hash = sha256()
    nbytes = nlines = 0
    for part in entries[:-1]:
        if part["kind"] != "part" or Path(part["file"]).name != part["file"]:
            raise ValueError(f"{directory}: invalid {name} manifest entry")
        ph = sha256()
        size = count = 0
        with (directory / part["file"]).open("rb") as f:
            for line in f:
                ph.update(line)
                total_hash.update(line)
                size += len(line)
                count += 1
                if not line.endswith(b"\n"):
                    raise ValueError("partial line in part")
                yield line[:-1]
        if (str(size),str(count),ph.hexdigest()) != (part["bytes"],part["rows"],part["sha256"]):
            raise ValueError(f"{directory}: {part['file']} differs from manifest")
        nbytes += size
        nlines += count
    if (str(nbytes),str(nlines),total_hash.hexdigest()) != (whole["bytes"],whole["rows"],whole["sha256"]):
        raise ValueError(f"{directory}: concatenated {name} differs from manifest")


def verify(directory):
    log=(directory/"run.log").read_text().splitlines()
    for marker in ("NNUE v3 loaded:", "NNUE v3 active:"):
        if not any(marker in line and "checksum 30ab43b4ba5db5f3" in line for line in log):
            raise ValueError(f"{directory}: no logged {marker} with pinned checksum")
    with (directory/"games.tsv").open() as f:
        games=list(csv.DictReader(f,delimiter="\t"))
    with (directory/"rss-all.tsv").open() as f:
        observations=list(csv.DictReader(f,delimiter="\t"))
    pids={r["p1_pid"] for r in games} | {r["p2_pid"] for r in games}
    ticks={(r["pid"],r["start_ticks"]) for r in observations}
    if len(pids)!=1 or len(ticks)!=1 or next(iter(ticks))[0]!=next(iter(pids)):
        raise ValueError(f"{directory}: process identity changes")
    starts=[line.split() for line in log if line.startswith("game_start ")]
    # An interrupted final game may be logged, but must not be included as a completed one.
    if (len(starts)<len(games) or [s[1] for s in starts[:len(games)]]!=[r["book_line"] for r in games]
        or any(s[3:]!=["readyok_all",next(iter(pids))] for s in starts)
        or [r["game"] for r in observations]!=[r["book_line"] for r in games]):
        raise ValueError(f"{directory}: per-game ready or process observation mismatch")
    nodes = na = count = 0
    for record,raw in zip_longest(stream(directory,"records"),stream(directory,"raw-last")):
        if record is None or raw is None:
            raise ValueError(f"{directory}: stream length mismatch")
        game,ply,move,*info = raw.split(b" ")
        if info == [b"NA"]:
            field=b"NA"
            na+=1
        else:
            if not info or info[0]!=b"info" or b"nodes" not in info:
                raise ValueError(f"{directory}: missing literal info nodes: {raw}")
            field=info[info.index(b"nodes")+1]
            nodes+=int(field)
        if record!=b" ".join([game,ply,move,field]):
            raise ValueError(f"{directory}: raw and record differ at {game} {ply}: {record} / {raw}")
        count+=1
    if (count,na,nodes)!=(sum(int(r["plies"]) for r in games),sum(int(r["na"]) for r in games),
                          sum(int(r["nodes"]) for r in games)):
        raise ValueError(f"{directory}: receipt counts differ")
    pid,start=next(iter(ticks))
    print(f"{directory.name}\t{len(games)}\t{count}\t{na}\t{nodes}\t{pid}\t{start}\t{len(starts)}\tVERIFIED")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archives",nargs="+",type=Path)
    args=parser.parse_args()
    print("arm\tgames\traw records\tNA\tnode sum\tengine PID\tstart ticks\treadyok games\tstatus")
    for archive in args.archives:
        verify(archive)
