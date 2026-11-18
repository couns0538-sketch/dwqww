"""Recalculate the Job 12 four-match table and the three budget pools from PGN audits."""
import argparse
from pathlib import Path
import re
from paired_elo import TARGET, measures

CURRENT = {
    "K12": ("0 vs 0", "80,000", 7341),
    "C12": ("0 vs 0", "40,000 / 80,000", 7342),
    "M3": ("2 vs 0", "80,000", 7343),
    "M3b": ("2 vs 0", "80,000", 7344),
}
POOLS = {
    2000: ((8,"M1"),(9,"M1b")),
    20000: ((8,"M2"),(9,"M2b"),(11,"M2c"),(11,"M2d")),
    80000: ((12,"M3"),(12,"M3b")),
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
    same,total=map(int,item(text,r"identical move lists (\d+)/(\d+)"))
    assert total==sum(bins) and 0<=same<=total
    return status,int(games),wld,bins,ends,same


def elo(bins):
    if not sum(bins):
        return None
    *_,point,width=measures(bins)
    return point,point-width,point+width


def display(result):
    return "unavailable" if result is None else f"{result[0]:+.2f} [{result[1]:+.2f}, {result[2]:+.2f}]"


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    for job in (8,9,11,12):
        cli.add_argument(f"job{job}",type=Path)
    cli.add_argument("output",type=Path)
    args=cli.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    results={}
    for job,name in set((job,name) for pool in POOLS.values() for job,name in pool) | {(12,name) for name in CURRENT}:
        results[name]=parse(getattr(args,f"job{job}")/name/"pgn-audit.txt")

    def complete(name):
        row=results[name]
        return bool(row) and row[0]=="complete" and row[1]==2*TARGET[name]

    lines=["| Match | NullMateGuard A vs B | Nodes per move | Seed | Games | W-L-D | Pentanomial | Elo [95%] | Same moves (pairs) | Endings (mate / draw rule / 300-move limit) |",
           "|---|---|---:|---:|---:|---|---|---|---:|---|"]
    for name,(guard,nodes,seed) in CURRENT.items():
        v=results[name]
        if not v:
            lines.append(f"| {name} | {guard} | {nodes} | {seed} | not played | — | — | — | — | — |")
            continue
        _,games,wld,bins,ends,same=v
        endings="/".join(map(str,ends[:3]))
        if ends[3]:
            endings+=f", other {ends[3]}"
        status=f"{games:,}"+("" if complete(name) else " (incomplete)")
        lines.append(f"| {name} | {guard} | {nodes} | {seed} | {status} | {'–'.join(map(str,wld))} | {list(bins)} | {display(elo(bins))} | {same}/{sum(bins)} | {endings} |")
    (args.output/"match-table.md").write_text("\n".join(lines)+"\n")
    pool_lines=["| Nodes per move | Included matches | Games | Pooled pentanomial | Elo [95%] |",
                "|---:|---|---:|---|---|"]
    details=[]
    for nodes, pool in POOLS.items():
        used=[name for _,name in pool if complete(name)]
        excluded=[f"{name} ({'missing' if not results[name] else 'incomplete'})" for _,name in pool if not complete(name)]
        bins=[sum(results[name][3][i] for name in used) for i in range(5)]
        group=elo(bins)
        pool_lines.append(f"| {nodes:,} | {', '.join(used) or 'none'} | {2*sum(bins):,} | {bins} | {display(group)} |")
        details.append(f"{nodes:,} nodes: excluded {', '.join(excluded) or 'none'}.")
        if group:
            _,_,_,xlo,xhi,_,_=measures(bins)
            details.append(f"Unrounded paired Elo {group[0]:+.12f}; symmetric fastchess interval [{group[1]:+.12f}, {group[2]:+.12f}]; direct transforms [{xlo:+.12f}, {xhi:+.12f}].")
        if nodes==80000:
            m3=elo(results["M3"][3])[0] if complete("M3") else None
            if group and m3 is not None and group[1]>0 and m3>0:
                reading="BETTER"
            elif group and m3 is not None and group[2]<0 and m3<0:
                reading="WORSE"
            else:
                reading="LEVEL"
            note=f"{m3:+.12f}" if m3 is not None else "no complete result"
            details.append(f"POOL80 reading: {reading}. M3 alone: {note}.")
    (args.output/"pools.md").write_text("\n".join(pool_lines)+"\n\n"+"\n".join(details)+"\n")


if __name__=="__main__":
    main()
