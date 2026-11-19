"""Extract the earliest raw lines for each Part A failure kind and describe its build coverage."""
import argparse
import csv
from itertools import groupby
from pathlib import Path


def rows(path):
    with path.open() as f:
        return list(csv.DictReader(f,delimiter="\t"))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("evidence",type=Path,help="A directory, containing A1, A2, A4")
    p.add_argument("tables",type=Path,help="directory produced by audit25.py stats")
    args=p.parse_args()
    records=rows(args.tables/"search-readback.tsv")
    breach={(r["part"],r["build"],r["position"],r["repeat"]):r for r in rows(args.tables/"threshold-cases.tsv")}
    failures=[]
    for r in records:
        if r["part"] not in ("A2","A4"): continue
        key=tuple(r[k] for k in ("part","build","position","repeat"))
        for condition,kind in ((key in breach,"node bound"),(r["within60"]=="0","60-second answer"),
                               (r["legal"]=="0" and r["bestmove"]!="","illegal bestmove")):
            if condition:
                raw=breach[key] if kind=="node bound" else None
                failures.append((kind,r,raw))
    if not failures:
        parts=", ".join(sorted({r["part"] for r in records} & {"A2","A4"}))
        print(f"No case in {parts} violated the node bound, answer deadline or move legality.")
        return
    def event_ns(item):
        _,r,br=item
        if br: return int(br["monotonic ns"])
        lines=(args.evidence/r["part"]/r["build"]/"uci.log").read_text().splitlines()
        i=int(r["answer line"]) or int(r["go line"])
        return int(lines[i-1].split(maxsplit=1)[0])
    print("Chronology uses the host monotonic timestamps. The build label describes whether the same failure kind occurs in each build. Positions and repeat numbers below identify the actual observations.")
    for kind,group in groupby(sorted(failures,key=lambda x:x[0]),key=lambda x:x[0]):
        events=list(group)
        seen={item[1]["build"] for item in events}
        tag="in both builds" if len(seen)==2 else next(iter(seen))+" only"
        print(f"\n{kind}: {tag}")
        for build in ("r15d","kF"):
            subset=[e for e in events if e[1]["build"]==build]
            if not subset: continue
            _,r,raw=min(subset,key=event_ns)
            path=args.evidence/r["part"]/build/"uci.log"
            lines=path.read_text().splitlines()
            print(f'{r["part"]} {build}, position {r["position"]}, repeat {r["repeat"]}, '
                  f'{len(subset)} affected searches across counted parts')
            indexes=[int(r["go line"])-1,int(r["go line"])]
            if raw: indexes.append(int(raw["first breach raw line number"]))
            if int(r["answer line"]): indexes.append(int(r["answer line"]))
            for i in indexes: print(f"{r['part']}/{build}/uci.log:{i}  {lines[i-1]}")
    _,r,_=min(failures,key=event_ns)
    print(f'\nEarliest across these A searches: {r["part"]} {r["build"]} position {r["position"]} repeat {r["repeat"]}.')


if __name__=="__main__":
    main()
