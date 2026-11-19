"""Collect literal UCI hold lines and verify each completed search against its archived count."""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import os
import tempfile
import time

from pack_arm28 import sha, save_json, split


def read_plies(game):
    with (game/"searches.tsv").open() as source:
        return {int(row["ply"]): (row["side"],row["engine"],int(row["holds"]))
                for row in csv.DictReader(source, delimiter="\t")}


def extract(game, game_id, finished, table):
    seen=Counter()
    plies=read_plies(game) if (game/"searches.tsv").exists() else {}
    wire=game/"wire.txt"
    current=0
    active=None
    recorded=0
    if wire.exists():
        with wire.open() as source:
            for line_no,original in enumerate(source,1):
                line=original.rstrip("\n")
                side, marker, content=line.split(" ",2)
                if marker==">" and content.startswith("go wtime "):
                    if active is not None:
                        raise ValueError(f"{game}: overlapping go")
                    current+=1
                    active=side
                elif marker=="<" and content.startswith("info string TmFinishIteration hold"):
                    if side!=active:
                        raise ValueError(f"{game}: stray hold line {line_no}")
                    seen[current]+=1
                    role=("A" if (game_id%2==1)==(side=="W") else "B")
                    if current in plies and plies[current][:2]!=(side,role):
                        raise ValueError(f"{game}: ply {current} side mismatch")
                    disposition="finished_game" if finished else "unfinished_game"
                    if current not in plies:disposition="open_search"
                    table.writerow((game_id,current,side,role,disposition,line_no,content))
                    recorded+=1
                elif marker=="<" and content.startswith("bestmove "):
                    if active!=side: raise ValueError(f"{game}: unexpected bestmove {line_no}")
                    active=None
    for ply,(_,_,declared) in plies.items():
        if seen[ply]!=declared:raise ValueError(f"{game}: ply {ply} reports {declared} holds; wire has {seen[ply]}")
    if finished and (active or current!=len(plies)):
        raise ValueError(f"{game}: incomplete wire and finished result")
    return recorded,len(plies),sum(seen[i]>0 for i in plies)


def capture(root,archive):
    arm=json.loads(archive.read_text());block=archive.parent.parent.name;stage=arm["stage"]
    out=root/"hold-evidence"/block/stage
    if (out/"receipt.json").exists():return
    out.parent.mkdir(parents=True,exist_ok=True)
    temp=Path(tempfile.mkdtemp(prefix="."+stage+".",dir=out.parent))
    live=root/"live"/block/stage
    finished=set(arm["finished_game_ids"])
    started=sorted(finished | set(arm["unfinished_game_ids"]))
    total=searches=positive=0
    recorded={}
    with (temp/"holds.tsv").open("x",newline="") as dest:
        table=csv.writer(dest,delimiter="\t",lineterminator="\n")
        table.writerow(("game","ply","side","engine","disposition","wire_line","uci_line"))
        for idx in started:
            count,n,hits=extract(live/f"g{idx:04d}",idx,idx in finished,table)
            total+=count;searches+=n;positive+=hits
            if idx in finished:
                recorded["finished_searches"]=recorded.get("finished_searches",0)+n
                recorded["finished_searches_with_holds"]=recorded.get("finished_searches_with_holds",0)+hits
    split(temp/"holds.tsv")
    if searches!=arm["searches"]+arm["unfinished_searches"]:raise ValueError(f"{archive}: search count mismatch")
    rec={"block":arm["block"],"stage":stage,"arm_receipt_sha256":sha(archive),
         "verified_completed_searches_in_all_started_games":searches,
         "searches_with_holds_in_all_verified_searches":positive,"literal_hold_lines_including_open_searches":total,
         **recorded,"files":{p.name:{"bytes":p.stat().st_size,"sha256":sha(p)} for p in sorted(temp.iterdir())},
         "utc":datetime.now(timezone.utc).isoformat(timespec="milliseconds")}
    save_json(temp/"receipt.json",rec)
    os.rename(temp,out)
    print(json.dumps({"event":"holds_ready","path":str(out),**{k:v for k,v in rec.items() if k!="files"}}),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root",type=Path)
    parser.add_argument("--watch",action="store_true")
    args=parser.parse_args()
    while True:
        for receipt in sorted((args.root/"blocks").glob("block*/M*/receipt.json")):
            capture(args.root,receipt)
        if not args.watch or (args.root/"blocks"/"schedule-end.json").exists():
            for receipt in sorted((args.root/"blocks").glob("block*/M*/receipt.json")):
                capture(args.root,receipt)
            return
        time.sleep(1)


if __name__=="__main__":main()
