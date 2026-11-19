"""Recount first score crossings and match results from completed, common Job 29 blocks."""
import argparse
import csv
import hashlib
import io
import json
import math
import re
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from statistics import NormalDist

THRESHOLDS = (300, 500, 800, 1200, 2000)
LIMITS = {"D1": (4000,2000), "D2": (2000,1000), "E": (4000,2000),
          "D3": (8000,4000), "D4": (1000,500), "F1": (2800,2000), "F2": (2000,1400)}
PHASES = {"primary": ("D1","D2","E"), "additional": ("D3","D4"), "standing": ("F1","F2")}
SCORE_RE = re.compile(r"(?:^| )score (cp|mate) (-?\d+)(?: |$)")
DEPTH_RE = re.compile(r"(?:^| )depth (\d+)(?: |$)")
RESULT = {"1-0": 2, "1/2-1/2": 1, "0-1": 0}
HIT_COLUMNS = ["block","match","game","opening","side","color","threshold_cp","outcome","end_ply",
               "first_ply","depth","score_type","score","bestmove","plies_remaining"]


def check(condition, message):
    if not condition:
        raise ValueError(message)


def csvrows(data):
    return csv.DictReader(io.StringIO(data.decode()),delimiter="\t")


def write_tsv(path, header, rows):
    tmp=path.with_name("."+path.name+".tmp")
    with tmp.open("w",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
    tmp.replace(path)


def write_json(path, value):
    tmp=path.with_name("."+path.name+".tmp")
    tmp.write_text(json.dumps(value,indent=2)+"\n")
    tmp.replace(path)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_source(stage, filename, manifest):
    def read(name):
        data=(stage/name).read_bytes()
        check(len(data)==manifest[name]["bytes"] and digest(data)==manifest[name]["sha256"],
              f"Stage hash {stage}/{name}")
        return data
    if filename in manifest:
        return read(filename)
    parts=list(csvrows(read(filename+".parts.tsv")))
    data=b"".join(read(item["filename"]) for item in parts if item["kind"]=="part")
    whole=[row for row in parts if row["kind"]=="whole"]
    check(len(whole)==1 and len(data)==int(whole[0]["bytes"]) and digest(data)==whole[0]["sha256"],
          f"Split {stage}/{filename}")
    return data


@dataclass
class Stage:
    arm: str
    game_count: int
    game_results: Counter
    penta: list
    search_totals: dict
    endings: Counter
    hits: list
    inputs: list


def parse_score(row):
    raw = row["info_line"]
    score = SCORE_RE.search(raw)
    if not score:
        check(row["score"] == row["depth"] == raw == "NA", "Missing score inconsistent")
        return None
    kind, value=score.groups()
    check(row["score"]==f"{kind} {value}", "Parsed and printed score differ")
    depth=DEPTH_RE.search(raw)
    check(depth and int(depth[1])==int(row["depth"]), "Score depth differs")
    return kind,int(value),int(depth[1])


def read_stage(block_no, block, arm, opening_range):
    stage=block/arm
    receipt=(stage/"receipt.json").read_bytes()
    info=json.loads(receipt)
    check(info["complete"] and info["stage"]==arm and info["block"]==block_no, f"Unsealed {stage}")
    lower,upper=info["opening_first"],info["opening_last"]
    check((lower,upper)==opening_range,f"Stage opening range {stage}")
    allowed=range(2*lower-1,2*upper+1)
    games_bytes=read_source(stage,"games.tsv",info["files"])
    searches_bytes=read_source(stage,"searches.tsv",info["files"])
    inputs=[[block_no,arm,name,len(data),digest(data)] for name,data in [
        ("receipt.json",receipt),("games.tsv",games_bytes),("searches.tsv",searches_bytes)]]
    games={}
    wld=Counter();endings=Counter()
    for g in csvrows(games_bytes):
        gid=int(g["game"])
        check(g["match"]==arm and gid in allowed and gid not in games and int(g["opening"])==(gid+1)//2,
              f"{arm}/game {gid} bad ID")
        colors = ("A","B") if gid%2 else ("B","A")
        check((g["white"],g["black"])==colors, f"{arm}/game {gid} bad color")
        white=RESULT[g["result"]]
        g["a_half"]=white if colors[0]=="A" else 2-white
        g["nplies"]=int(g["plies"])
        games[gid]=g
        wld[g["a_half"]]+=1
        endings[g["ending"]]+=1
    check(set(games)==set(allowed),f"{arm} incomplete game pair")
    sides={"A":Counter(),"B":Counter()}
    lastply=Counter()
    first={}
    for row in csvrows(searches_bytes):
        gid=int(row["game"]);ply=int(row["ply"]);side=row["side"]
        g=games[gid]
        check(row["match"]==arm and ply==lastply[gid]+1 and side in sides,
              f"{arm}/game {gid} search sequence")
        white_to_move = row["color"]=="W"
        check(row["color"] in ("W","B") and side==g["white" if white_to_move else "black"],
              f"{arm}/game {gid} role mismatch")
        lastply[gid]=ply
        c=sides[side]; c["nsearch"]+=1
        budget=LIMITS[arm][0 if side=="A" else 1]
        plain=arm=="E" and side=="A"
        expected=f"go {'nodes' if plain else 'softnodes'} {budget}"
        check(row["go"]==expected and row["move_line"].split()[1]==row["bestmove"], "Go/bestmove mismatch")
        if plain:
            check(row["n"]==row["info_nodes"],"Plain finished-depth n")
            if row["soft_line"]=="NA":
                check(row["soft_n"]=="NA","Plain search missing footer but numeric footer present")
            else:
                check(row["soft_n"].isdigit() and row["soft_line"]=="info string softnodes nodes "+row["soft_n"],
                      "Plain search footer with inconsistent raw count")
                c["plain_footer"]+=1
            c["sum_spent"]+=budget
        else:
            check(row["n"]==row["soft_n"] and row["soft_line"]=="info string softnodes nodes "+row["n"],
                  "Soft footer count")
            n=int(row["n"])
            c["sum_spent"]+=n
            c["cap"]+=int(n>=4*budget)
        if row["n"]!="NA":
            c["nreported"]+=1
            c["sum_n"]+=int(row["n"])
        s=parse_score(row)
        if s is None:
            c["no_score"]+=1
            continue
        kind,value,depth=s
        c["nscore"]+=1; c["sum_depth"]+=depth
        for threshold in THRESHOLDS:
            if (kind=="mate" and value>0) or (kind=="cp" and value>=threshold):
                first.setdefault((gid,side,threshold),(ply,depth,kind,value,row["bestmove"]))
    check(all(lastply[g]==v["nplies"] for g,v in games.items()),f"{arm} plies/searches")
    check(sum(lastply.values())==info["searches"],f"{arm} receipt count")
    penta=[0]*5
    for k in range(lower,upper+1):
        penta[games[2*k-1]["a_half"]+games[2*k]["a_half"]]+=1
    hits=[]
    for gid,g in sorted(games.items()):
        for side in ("A","B"):
            color="W" if g["white"]==side else "B"
            out=g["a_half"] if side=="A" else 2-g["a_half"]
            for threshold in THRESHOLDS:
                key=(gid,side,threshold)
                prefix=[block_no,arm,gid,int(g["opening"]),side,color,threshold,("L","D","W")[out],g["nplies"]]
                if key in first:
                    ply,depth,kind,value,best=first[key]
                    hits.append(prefix+[ply,depth,kind,value,best,g["nplies"]-ply])
                else:
                    hits.append(prefix+[""]*6)
    return Stage(arm,len(games),wld,penta,sides,endings,hits,inputs)


def mean(total, n):
    return f"{total/n:.12f}" if n else ""


def elo(p):
    if p <= 0: return -math.inf
    if p >= 1: return math.inf
    return 400*math.log10(p/(1-p))


def publish(out, root, blocks, stages, final):
    allhits=[];inputs=[];thresh=[];matches=[];side_rows=[];ending_rows=[]
    match_names=list(dict.fromkeys(s.arm for s in stages))
    for name in match_names:
        subset=[s for s in stages if s.arm==name]
        p=[sum(s.penta[i] for s in subset) for i in range(5)]
        ng=sum(s.game_count for s in subset);op=sum(p);wdl=sum((s.game_results for s in subset),Counter())
        ends=sum((s.endings for s in subset),Counter())
        ss={side:sum((s.search_totals[side] for s in subset),Counter()) for side in ("A","B")}
        check(2*op==ng==sum(wdl.values()),"Pentanomial/total games")
        sums={(side,t):Counter() for side in ss for t in THRESHOLDS}
        for s in subset:
            allhits.extend(s.hits); inputs.extend(s.inputs)
            for row in s.hits:
                if row[9]!="":
                    counter=sums[(row[4],row[6])]
                    counter[row[7]]+=1
                    counter["remaining"]+=row[-1]
        for side,c in ss.items():
            plain=name=="E" and side=="A"
            side_rows.append([name,side,c["nsearch"],c["nreported"],c["sum_n"],mean(c["sum_n"],c["nreported"]),
                              c["sum_spent"],mean(c["sum_spent"],c["nsearch"]),c["nscore"],c["no_score"],
                              c["sum_depth"],mean(c["sum_depth"],c["nscore"]),"" if plain else c["cap"],
                              "" if plain else mean(c["cap"],c["nsearch"]),c["plain_footer"] if plain else ""])
            for t in THRESHOLDS:
                s=sums[(side,t)]; reach=s["W"]+s["D"]+s["L"]
                thresh.append([name,side,t,reach,s["W"],s["D"],s["L"],mean(s["remaining"],reach)])
        for ending,count in sorted(ends.items()): ending_rows.append([name,ending,count])
        pa=sum(i*count for i,count in enumerate(p))/(4*op)
        var=sum(count*(i/4-pa)**2 for i,count in enumerate(p))/op
        margin=NormalDist().inv_cdf(.975)*math.sqrt(var/op)
        ep=elo(pa);eh=(elo(pa+margin)-elo(pa-margin))/2
        lo,hi=ep-eh,ep+eh
        ma=ss["A"]["sum_spent"]/ss["A"]["nsearch"];mb=ss["B"]["sum_spent"]/ss["B"]["nsearch"]
        matches.append([name,op,ng,wdl[2],wdl[0],wdl[1],*p,mean(ss["A"]["sum_n"],ss["A"]["nreported"]),
                        f"{ma:.12f}",f"{mb:.12f}",f"{ma/mb:.12f}",f"{ep:.12f}",f"{lo:.12f}",f"{hi:.12f}",
                        "A BETTER" if lo>0 else "B BETTER" if hi<0 else "LEVEL",mean(sum(c["nsearch"] for c in ss.values()),ng)])
    out.mkdir(parents=True,exist_ok=True)
    write_tsv(out/"per_game.tsv",HIT_COLUMNS,allhits)
    write_tsv(out/"summary.tsv",["match","side","threshold_cp","games_reached","won","drew","lost","mean_plies_remaining"],thresh)
    write_tsv(out/"match-check.tsv",["match","pairs","games","A_wins","A_losses","A_draws","p0","p05","p1","p15","p2",
              "A_mean_n_column","A_mean_spent","B_mean_spent","A_to_B_spend","elo","ci_low","ci_high","reading","mean_plies"],matches)
    write_tsv(out/"search-check.tsv",["match","side","searches","n_reported","sum_n","mean_n","sum_spent","mean_spent",
              "scored_searches","no_score","sum_depth","mean_scored_depth","soft_cap_hits","soft_cap_share","plain_footer_count"],side_rows)
    write_tsv(out/"endings-check.tsv",["match","ending","games"],ending_rows)
    write_tsv(out/"inputs.tsv",["block","match","source_file","bytes","sha256"],inputs)
    write_json(out/"status.json",{"final":final,"common_complete_blocks":blocks,"counted_matches":match_names,
                                      "match_games":sum(s.game_count for s in stages),"threshold_game_side_rows":len(allhits)})


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--blocks",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--watch",action="store_true")
    args=ap.parse_args()
    seen=[];stages=[]
    while True:
        receipts=[(int(p.parent.name[5:]),p) for p in sorted(args.blocks.glob("block*/receipt.json"))]
        for block,p in receipts:
            if block in seen: continue
            rc=json.loads(p.read_text())
            if not rc["complete"]: continue
            check(block==int(rc["block"]), "Block identity")
            phase=rc["phase"]
            arms=PHASES[phase]
            check(tuple(rc["stages"])==arms,"Block phase/arm assignment")
            for arm in arms:
                stages.append(read_stage(block,p.parent,arm,(rc["opening_first"],rc["opening_last"])))
            seen.append(block)
            if args.watch:
                publish(args.out,args.blocks,seen,stages,False)
                print("Common block",block,"published",flush=True)
        end=args.blocks/"schedule-end.json"
        if end.is_file():
            final=json.loads(end.read_text())
            check(seen==final["common_complete_blocks"],"Final schedule and complete block receipts differ")
            publish(args.out,args.blocks,seen,stages,True)
            print("Final common blocks",seen,flush=True)
            break
        if not args.watch:
            publish(args.out,args.blocks,seen,stages,False)
            break
        time.sleep(3)


if __name__=="__main__":
    main()
