"""Job 11 match and pool tables from the three jobs’ independent PGN audits."""
import argparse
from pathlib import Path
import re
from paired_elo import TARGET, measures


SPECS = {
    "K8": (8, "0 vs 0", "2,000", 7311),
    "C8": (8, "0 vs 0", "10,000 / 20,000", 7312),
    "M1": (8, "2 vs 0", "2,000", 7313),
    "M2": (8, "2 vs 0", "20,000", 7314),
    "K9": (9, "0 vs 0", "2,000", 7321),
    "C9": (9, "0 vs 0", "10,000 / 20,000", 7322),
    "M1b": (9, "2 vs 0", "2,000", 7323),
    "M2b": (9, "2 vs 0", "20,000", 7324),
    "K11": (11, "0 vs 0", "20,000", 7331),
    "C11": (11, "0 vs 0", "10,000 / 20,000", 7332),
    "M2c": (11, "2 vs 0", "20,000", 7333),
    "M2d": (11, "2 vs 0", "20,000", 7334),
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
    p.add_argument("job11_audits",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=True)
    rows=["| Match | Guard A vs B | Nodes per move | Seed | Games | W-L-D | Pentanomial | Elo [95%] | Endings (mate / draw rule / 300-move limit) |",
          "|---|---|---:|---:|---:|---|---|---|---|"]
    results={}
    roots={8:a.job8_audits,9:a.job9_audits,11:a.job11_audits}
    for k,(job,guard,nodes,seed) in SPECS.items():
        source=roots[job]
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
    def complete(name):
        result=results.get(name)
        return bool(result and result[0]=="complete" and result[1]==2*TARGET[name])

    def seed(name):
        if not results[name]:
            return "not played"
        result=elo(results[name][3])
        value="unavailable" if result is None else f"{result[0]:+.2f}"
        return value if complete(name) else value+" (incomplete)"

    pool=["| Nodes per move | Job 8 | Job 9 | Job 11, seed 7333 | Job 11, seed 7334 |",
          "|---:|---:|---:|---:|---:|",
          f"| 2,000 | 7313: {seed('M1')} | 7323: {seed('M1b')} | — | — |",
          f"| 20,000 | 7314: {seed('M2')} | 7324: {seed('M2b')} | {seed('M2c')} | {seed('M2d')} |",""]
    names=("M2","M2b","M2c","M2d")
    used=[name for name in names if complete(name)]
    excluded=[f"{name} ({'missing' if not results[name] else 'incomplete'})" for name in names if name not in used]
    bins=[sum(results[name][3][i] for name in used) for i in range(5)]
    aggregate=elo(bins)
    m2c=elo(results["M2c"][3])[0] if complete("M2c") else None
    if aggregate and m2c is not None and aggregate[1]>0 and m2c>0:
        reading="BETTER"
    elif aggregate and m2c is not None and aggregate[2]<0 and m2c<0:
        reading="WORSE"
    else:
        reading=f"LEVEL — level at 20,000 nodes in {len(used)} seeds"
    pool+=["| Pool | Included matches | Games | Pooled pentanomial | Elo [95%] | Reading |","|---|---|---:|---|---|---|",
           f"| POOL20 | {', '.join(used) or 'none'} | {2*sum(bins):,} | {bins} | {display(aggregate)} | {reading} |","",
           f"Excluded matches: {', '.join(excluded) or 'none'}.",
           f"M2c alone: {seed('M2c')} Elo."]
    if aggregate:
        pool.append(f"Unrounded POOL20 Elo {aggregate[0]:+.12f}; interval [{aggregate[1]:+.12f}, {aggregate[2]:+.12f}].")
    (a.output/"pools.md").write_text("\n".join(pool)+"\n")


if __name__=="__main__":
    main()
