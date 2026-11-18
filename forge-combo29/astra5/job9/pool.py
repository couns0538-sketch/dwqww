"""Job 9 two-seed tables. Read independent PGN audit summaries from both jobs."""
import argparse
from pathlib import Path
import re
from paired_elo import TARGET, measures


SPECS = {
    "K9": ("0 vs 0", "2,000", 7321),
    "C9": ("0 vs 0", "10,000 / 20,000", 7322),
    "M1": ("2 vs 0", "2,000", 7313),
    "M1b": ("2 vs 0", "2,000", 7323),
    "M2": ("2 vs 0", "20,000", 7314),
    "M2b": ("2 vs 0", "20,000", 7324),
}


def item(text,pattern):
    hit=re.search("^"+pattern+"$",text,re.M)
    if not hit:
        raise ValueError("audit missing: "+pattern)
    return hit.groups()


def parse(path):
    if not path.exists():
        return None
    text=path.read_text()
    [status]=item(text,r"status (.+)")
    [games]=item(text,r"scored games (\d+)")
    wld=tuple(map(int,item(text,r"A W-L-D (\d+) (\d+) (\d+)")))
    bins=tuple(map(int,item(text,r"pentanomial (\d+) (\d+) (\d+) (\d+) (\d+)")))
    ends=tuple(map(int,item(text,r"endings mate=(\d+) draw_rule=(\d+) limit_300=(\d+) other=(\d+)")))
    assert int(games)==sum(wld)==2*sum(bins)==sum(ends)
    return status,int(games),wld,bins,ends


def elo(bins):
    if not sum(bins):
        return None
    *_,point,width=measures(bins)
    return point,point-width,point+width


def display(result):
    return "unavailable" if result is None else f"{result[0]:+.2f} [{result[1]:+.2f}, {result[2]:+.2f}]"


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("job8_audits",type=Path)
    p.add_argument("job9_audits",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=True)
    rows=["| Match | Guard A vs B | Nodes per move | Seed | Games | W-L-D | Pentanomial | Elo [95%] | Endings (mate / draw rule / 300-move limit) |",
          "|---|---|---:|---:|---:|---|---|---|---|"]
    results={}
    for k,(guard,nodes,seed) in SPECS.items():
        source=a.job8_audits if k in ("M1","M2") else a.job9_audits
        v=results[k]=parse(source/k/"pgn-audit.txt")
        if not v:
            rows.append(f"| {k} | {guard} | {nodes} | {seed} | not played | — | — | — | — |")
            continue
        status,games,wld,bins,ends=v
        complete=(status=="complete" and games==2*TARGET[k])
        gtotal=f"{games:,}" + ("" if complete else " (incomplete)")
        endings="/".join(map(str,ends[:3]))
        if ends[3]:
            endings += f", other {ends[3]}"
        rows.append(f"| {k} | {guard} | {nodes} | {seed} | {gtotal} | {'–'.join(map(str,wld))} | [{', '.join(map(str,bins))}] | {display(elo(bins))} | {endings} |")
    (a.output/"match-table.md").write_text("\n".join(rows)+"\n")
    pool=["| Nodes per move | Job 8 Elo | Job 9 Elo | Pooled games | Pooled pentanomial | Pooled Elo [95%] | Reading |",
        "|---:|---:|---:|---:|---|---|---|"]
    detail=[]
    for old,new in (("M1","M1b"),("M2","M2b")):
        nodes=SPECS[old][1]
        used=[]
        excluded=[]
        for k in (old,new):
            v=results[k]
            if not v:
                excluded.append(k+" (missing)")
            elif v[0]!="complete" or v[1]!=2*TARGET[k]:
                excluded.append(k+" (incomplete)")
            else:
                used.append(k)
        bins=[sum(results[k][3][i] for k in used) for i in range(5)]
        pair_elo=elo(bins)
        def individual(k):
            return elo(results[k][3])[0] if k in used else None
        e8,e9=individual(old),individual(new)
        if pair_elo and e9 is not None and pair_elo[1]>0 and e9>0:
            reading="BETTER"
        elif pair_elo and e9 is not None and pair_elo[2]<0 and e9<0:
            reading="WORSE"
        else:
            reading="LEVEL — level at this node count in two seeds"
            if excluded:
                reading="LEVEL (two-seed reading unavailable)"
        vals=["—" if e is None else f"{e:+.2f}" for e in (e8,e9)]
        pool.append(f"| {nodes} | {vals[0]} | {vals[1]} | {sum(bins)*2:,} | {bins} | {display(pair_elo)} | {reading} |")
        detail.append(f"Nodes {nodes}; included {', '.join(used) or 'none'}; excluded {', '.join(excluded) or 'none'}.")
        if pair_elo:
            detail.append(f"  Unrounded pooled Elo {pair_elo[0]:+.12f}; interval [{pair_elo[1]:+.12f}, {pair_elo[2]:+.12f}].")
    (a.output/"pools.md").write_text("\n".join(pool)+"\n\n"+"\n".join(detail)+"\n")


if __name__=="__main__":
    main()
