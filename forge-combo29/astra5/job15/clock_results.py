"""Reconcile job 15 Fastchess scores to the separate PGN pair audit."""
import argparse
from collections import Counter
import csv
from pathlib import Path
import re
from paired_elo import TARGET, measures, render

GAME = re.compile(r"^Finished game (\d+) \(([^()]+) vs ([^()]+)\): (1-0|0-1|1/2-1/2) \{(.*)\}$")
DRAW = {"Draw by 3-fold repetition","Draw by fifty moves rule","Draw by insufficient mating material","Draw by stalemate"}
SPECS = {"C15":("0 vs 0","5+0.05 / 10+0.1",7371),"T1b":("2 vs 0","10+0.1 / 10+0.1",7372)}
HIST = {2000:((8,"M1"),(9,"M1b")),20000:((8,"M2"),(9,"M2b"),(11,"M2c"),(11,"M2d")),80000:((12,"M3"),(12,"M3b"),(13,"M3c"),(13,"M3d"))}
HEAD=("mate","draw_rule","limit_300","time_A_loss","time_B_loss","other")


def field(text, heading):
    m=re.search("^"+re.escape(heading)+" (.*)$",text,re.M)
    if not m:
        raise ValueError("Missing PGN-audit field "+heading)
    return m[1]


def elo(bins):
    if not sum(bins):
        return None
    *_,e,err=measures(bins)
    return e,e-err,e+err


def show(v):
    return "unavailable" if v is None else f"{v[0]:+.2f} [{v[1]:+.2f}, {v[2]:+.2f}]"


def scan(name, runner, audit, out):
    a=(audit/name/"pgn-audit.txt").read_text()
    bins=tuple(map(int,field(a,"pentanomial").split()))
    wld=tuple(map(int,field(a,"A W-L-D").split()))
    endings=dict(x.split("=") for x in field(a,"endings").split())
    status=field(a,"status")
    expected=TARGET[name]
    with (audit/name/"pairs.tsv").open() as f:
        pairs=list(csv.DictReader(f,delimiter="\t"))
    ids={int(pair[k]) for pair in pairs for k in ("first_game","second_game")}
    assert len(ids)==2*sum(bins)==len(pairs)*2
    raw={}
    for line in runner.read_text().splitlines():
        m=GAME.fullmatch(line)
        if not m:
            continue
        game=int(m[1])
        assert game not in raw
        white,black,res,reason=m.groups()[1:]
        assert {white,black}=={name+"-A",name+"-B"}
        if res=="1/2-1/2":
            mark="D"
        else:
            winner=white if res=="1-0" else black
            mark="W" if winner==name+"-A" else "L"
        if reason.endswith(" mates"):
            ending="mate"
        elif reason in DRAW:
            ending="draw_rule"
        elif reason=="Draw by adjudication":
            ending="limit_300"
        elif "loses on time" in reason:
            color=reason.split()[0]
            assert (color,res) in (("White","0-1"),("Black","1-0"))
            loser=white if color=="White" else black
            ending="time_A_loss" if loser==name+"-A" else "time_B_loss"
        else:
            ending="other"
        raw[game]=(white,black,res,reason,mark,ending)
    assert ids <= raw.keys()
    (out/name).mkdir(exist_ok=True)
    with (out/name/"game-readback.tsv").open('w',newline="") as f:
        t=csv.writer(f,delimiter="\t",lineterminator="\n")
        t.writerow(("scheduled_game","round","scored_complete_pair","white","black","result","runner_reason","A_result","ending"))
        for game,r in sorted(raw.items()):
            t.writerow((game,(game+1)//2,int(game in ids),*r))
    rescore=[0]*5
    for pair in pairs:
        pair_ids=[int(pair[k]) for k in ("first_game","second_game")]
        assert sorted(pair_ids)==[2*int(pair["round"])-1,2*int(pair["round"])]
        marks=[raw[i][4] for i in pair_ids]
        assert marks==[pair["A_result_first"],pair["A_result_second"]]
        rescore[sum({"D":1,"L":0,"W":2}[x] for x in marks)]+=1
    assert tuple(rescore)==bins
    groups=Counter(raw[i][5] for i in ids)
    totals=Counter(raw[i][5] for i in raw)
    scored=Counter(raw[i][4] for i in ids)
    assert wld==tuple(scored[c] for c in "WLD")
    assert all(groups[c]==int(endings[c]) for c in HEAD), (groups,endings)
    assert sum(wld)==2*sum(bins)==sum(groups.values())
    complete=(status=="complete" and len(pairs)==expected)
    lines=render(name,list(bins),runner)
    lines += [f"Raw finished games {len(raw)}; games in audited complete pairs {len(ids)}.",
              f"Time losses in scored pairs: A {groups['time_A_loss']}, B {groups['time_B_loss']}.",
              f"Time losses in all finished runner records: A {totals['time_A_loss']}, B {totals['time_B_loss']}.",
              f"Unpaired or out-of-scope raw finished game IDs {sorted(raw.keys()-ids)}."]
    return dict(bins=bins,wld=wld,ends=groups,total=totals,complete=complete,elo=elo(bins),lines=lines)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("raw",type=Path)
    p.add_argument("audit",type=Path)
    p.add_argument("output",type=Path)
    for job in (8,9,11,12,13,14):
        p.add_argument(f"job{job}", type=Path)
    args=p.parse_args()
    out=args.output
    out.mkdir(exist_ok=True,parents=True)
    result={}
    if (args.job14/"T1"/"pgn-audit.txt").exists():
        result["T1"]=scan("T1",args.job14/"T1.out",args.job14,out)
        historical=result["T1"]
        (out/"T1-elo.txt").write_text("\n".join(historical["lines"])+"\n")
    warnings=[]
    for k in SPECS:
        if (args.audit/k/"pgn-audit.txt").exists():
            r=result[k]=scan(k,args.raw/(k+".out"),args.audit,out)
            ma,mb=(r["total"][kind] for kind in ("time_A_loss","time_B_loss"))
            if ma+mb>5:
                warnings.append(f"{k} had {ma+mb} losses on time (A {ma}, B {mb})")
    warning=" " + "; ".join(warnings) + ". The clock then measures the machine, not the engines." if warnings else ""
    rows=["| Match | Guard A vs B | Clock A / B | Seed | Games | A W-L-D | Pentanomial | Elo [95%] | Endings (mate / draw rule / 300-move limit / A time losses / B time losses) |",
          "|---|---|---|---:|---:|---|---|---|---|"]
    for k,(guard,limit,seed) in SPECS.items():
        r=result.get(k)
        if not r:
            rows.append(f"| {k} | {guard} | {limit} | {seed} | not played | — | — | — | — |")
            continue
        bins=r["bins"]
        label=f"{2*sum(bins)}/{2*TARGET[k]}"+("" if r["complete"] else " (incomplete)")
        ending="/".join(str(r["ends"][c]) for c in HEAD if c!="other")
        if r["ends"]["other"]:
            ending+=f" and {r['ends']['other']} other"
        rows.append(f"| {k} | {guard} | {limit} | {seed} | {label} | {'–'.join(map(str,r['wld']))} | {list(bins)} | {show(r['elo'])} | {ending} |")
        if k=="C15":
            reading="PASS" if r["complete"] and r["elo"] and r["elo"][2]<0 else "FAIL"
            r["lines"].append("C15 control gate: "+reading+"."+warning)
        else:
            q="complete" if r["complete"] else "incomplete"
            r["lines"].append(f"T1b {q}; individual estimate is based on scored pairs. POOLT has its own complete-match eligibility rule."+warning)
        (out/f"{k}-elo.txt").write_text("\n".join(r["lines"])+"\n")
    (out/"match-table.md").write_text("\n".join(rows)+"\n")
    comparison=["| Search limit | Measured seeds | Scored games | Pentanomial | Elo [95%] |",
                "|---|---|---:|---|---|"]
    for nodes,cohort in HIST.items():
        bs=[]
        for j,k in cohort:
            text=(getattr(args,"job"+str(j))/k/"pgn-audit.txt").read_text()
            if field(text,"status")=="complete":
                bs.append((k,list(map(int,field(text,"pentanomial").split()))))
        added=[sum(b[i] for _,b in bs) for i in range(5)]
        comparison.append(f"| {nodes:,} nodes | {', '.join(k for k,_ in bs)} | {sum(added)*2:,} | {added} | {show(elo(added))} |")
    clock_names=("T1","T1b")
    used=[k for k in clock_names if k in result and result[k]["complete"]]
    excluded=[]
    elig=["match\tstatus\tindividual_pairs\tindividual_elo_ci\teligible_pool_pairs"]
    for k in clock_names:
        r=result.get(k)
        status="missing" if r is None else ("complete" if r["complete"] else "incomplete")
        if k not in used:
            excluded.append(f"{k} ({status})")
        n=sum(r["bins"]) if r else 0
        elig.append(f"{k}\t{status}\t{n}\t{show(r['elo']) if r else 'unavailable'}\t{n if k in used else 0}")
    (out/"eligibility.tsv").write_text("\n".join(elig)+"\n")
    bins=[sum(result[k]["bins"][i] for k in used) for i in range(5)]
    pairs=sum(bins)
    pooled=elo(bins)
    desc=', '.join(used) if used else 'none'
    cell=str(bins) if pairs else '— (empty pool)'
    comparison.append(f"| 10+0.1 (POOLT) | {desc} | {pairs*2:,} | {cell} | {show(pooled)} |")
    comparison.extend(["",f"POOLT included {len(used)} complete matches and {pairs} opening pairs. Excluded {', '.join(excluded) or 'none'}."])
    t1b=result.get("T1b")
    if not pooled:
        reading="POOLT is unevaluable; zero eligible pairs provide no Elo estimate or confidence interval. The rule's fallback is LEVEL otherwise; the empty pool provides no strength reading."
    elif t1b and t1b["elo"] and pooled[1]>0 and t1b["elo"][0]>0:
        reading="POOLT: BETTER."
    elif t1b and t1b["elo"] and pooled[2]<0 and t1b["elo"][0]<0:
        reading="POOLT: WORSE."
    else:
        reading="POOLT: LEVEL."
    comparison.extend([reading+warning,"","Rule: BETTER when its interval lies wholly above 0 AND T1b alone has a positive Elo; WORSE when wholly below 0 AND T1b alone negative; LEVEL otherwise."+warning])
    (out/"pools.md").write_text("\n".join(comparison)+"\n")


if __name__=="__main__":
    main()
