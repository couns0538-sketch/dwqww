#!/usr/bin/env python3
"""Verify Job 8 defaults, bridge, controls and exact opening-row identities."""
import argparse
from fractions import Fraction
from hashlib import sha256
from itertools import islice
import json
from pathlib import Path
import re

KEEPS = (1024,896,768,512,256,0)
FIELDS = ("game","ply","fen","depth","nodes","bestmove","final_nodes","final_nodes_info","cnt")
VOLATILE = re.compile(r" (?:time|nps) [0-9]+(?= |$)")
BRIDGE = {"O": (200,8315168,[21812,26844,35173],"fd609b7b1a8dd179","14583c86b5f56cb6"),
          "G": (353,17611204,[31779,46086,84457],"60b6916f01395e99","0846f027e7e9b77e")}


def read_rows(path):
    with path.open() as rows:
        yield from map(json.loads,rows)


def identity(row):
    return (*[row[key] for key in FIELDS], VOLATILE.sub("",row["info"]))


def compare(path,reference,count,prefix=False,openings=False):
    left,right=read_rows(path),read_rows(reference)
    if prefix:
        right=islice(right,count)
    if openings:
        left=(row for row in left if row["ply"]==0)
        right=(row for row in right if row["ply"]==0)
    size=0
    for size,(a,b) in enumerate(zip(left,right,strict=True),1):
        if identity(a)!=identity(b):
            print(f"{path.name} differs from {reference.name} at search {size}.")
            print(json.dumps({"current":a,"reference":b},separators=(",",":")))
            raise SystemExit(1)
    assert size==count,(path,reference,size,count)
    print(f"{path.name} vs {reference.name}: {size}/{count} exact.")


def tally(path):
    total = takes = size = 0
    for row in read_rows(path):
        size += 1
        counts=json.loads(row["cnt"].removeprefix("info string CNT "))
        total+=sum(counts["main_nodes"])+sum(counts["q_nodes"])
        takes+=sum(counts["history_pruning_taken"])
    assert size==1800
    return total,takes


def verify_baseline(age,legacy):
    for mode,expected in (("warm-soft",(6753665,17791)),("warm-hard",(36000000,454974)),("cold-soft",(5523343,349))):
        path=age/f"keep-1024-{mode}.jsonl"
        compare(path,legacy/f"base-{mode}.jsonl",1800)
        actual=tally(path)
        assert actual==expected,(mode,actual,expected)
        print(f"{mode}: {actual[0]} actual nodes, {actual[1]} history-pruning takes.")


def digest(values):
    return sha256("".join(f"{v}\n" for v in values).encode()).hexdigest()[:16]


def bridge(raw,legacy):
    for key,expected in BRIDGE.items():
        arm=list(read_rows(raw/f"bridge-{key}.jsonl"))
        nodes,moves=([row[field] for row in arm] for field in ("nodes","bestmove"))
        actual=(len(rows:=arm),sum(nodes),nodes[:3],digest(nodes),digest(moves))
        print(f"{key}: {actual}. Expected {expected}. Match={actual == expected}.")
        if actual != expected:
            old=list(read_rows(legacy/f"identity-plain-{key}.jsonl"))
            differing=[(a,b) for a,b in zip(rows,old) if (a["fen"],a["nodes"],a["bestmove"]) !=
                       (b["fen"],b["nodes"],b["bestmove"])]
            for a,b in differing[:5]:
                print(json.dumps({"current":a,"reference":b},separators=(",",":")))
            print(f"{key}: {len(differing)} paired differences, current {len(rows)}, reference {len(old)}.")


def warm_openings(folder,full=False):
    for mode in ("warm-soft","warm-hard"):
        anchor=folder/f"keep-1024-{mode}.jsonl"
        for keep in KEEPS[1:]:
            path=folder/f"keep-{keep}-{mode}.jsonl"
            if full:
                sidecar=path.with_suffix(".jsonl.meta")
                if not sidecar.exists() or not sidecar.stat().st_size or json.loads(sidecar.read_text())["status"] != "complete":
                    print(f"{path.name} full opening readback unfinished.")
                    continue
            compare(path,anchor,30,openings=full)


def age_controls(age,legacy):
    for value in (512,0):
        compare(age/f"keep-{value}-cold-soft.jsonl",legacy/"base-cold-soft.jsonl",1800)
    nodes,takes=tally(age/"keep-0-warm-soft.jsonl")
    base_nodes,base_takes=tally(age/"keep-1024-warm-soft.jsonl")
    ratio=Fraction(takes*base_nodes,base_takes*nodes)
    print(f"Keep 0 warm-soft: {nodes} nodes, {takes} takes, {takes*1000/nodes:.6f} per 1k, "
          f"{float(ratio):.6f}× default ({base_nodes} nodes, {base_takes} takes).")
    assert ratio < Fraction(1,5),ratio


def hard_gate(folder,legacy,controls):
    base=folder/"base-cold-hard.jsonl"
    if controls:
        for direction in ("minus","plus"):
            compare(folder/f"QsSeeMargin-{direction}-cold-hard.jsonl",base,1800)
    else:
        compare(base,legacy/"D-hard-cold.jsonl",1800,prefix=True)
        count=tally(base)
        print(f"Cold-hard base: {count[0]} nodes, {count[1]} history-pruning takes.")
        assert count == (36000000,27804)


parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("stage",choices=("baselines","bridge","openings","full-openings","age-controls","D-base","D-controls"))
parser.add_argument("--job2",type=Path,default=Path("../job2/raw"))
parser.add_argument("--job3",type=Path,default=Path("../job3/raw"))
parser.add_argument("--job6",type=Path,default=Path("../job6/raw"))
args=parser.parse_args()
age=Path("age-raw")
{
  "baselines": lambda: verify_baseline(age,args.job6),
  "bridge": lambda: bridge(Path("bridge-raw"),args.job2),
  "openings": lambda: warm_openings(Path("opening-raw")),
  "full-openings": lambda: warm_openings(age,full=True),
  "age-controls": lambda: age_controls(age,args.job6),
  "D-base": lambda: hard_gate(Path("raw"),args.job3,False),
  "D-controls": lambda: hard_gate(Path("raw"),args.job3,True),
}[args.stage]()
