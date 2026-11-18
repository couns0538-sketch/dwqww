"""Audit the Job 4 P ladders from raw UCI traffic and recount the O/G suite rows."""
import argparse
import csv
from pathlib import Path
import sys


SUITES = {"O": (200, 8315168, [21812, 26844, 35173]), "G": (353, 17611204, [31779, 46086, 84457])}
B = [("S14", "S14", ""), ("PC20", "PC20", ""), ("B1", "PC20", "HistRework 0"),
     ("B2", "PC20", "CorrHistV2 false"), ("B3", "S14", "CuckooRep true"),
     ("B4", "S14", "HistRework 2"), ("B5", "S14", "TtPruneV2 true"),
     ("B6", "S14", "CorrHistV2 true"), ("B7", "S14", "MateAlphaGuard true")]


def settings(meta):
    return [s for s in meta if s.startswith("setoption ")]


def digest(meta):
    return next(l for l in meta if l.startswith("sha256 "))


def extend_options(options, change):
    if not change:
        return options
    name, value = change.split()
    return [*options, f"setoption name {name} value {value}"]


def read_suite(path, n, commands, exe_sha):
    meta = Path(str(path) + ".meta").read_text().splitlines()
    if f"completed_rows {n}" not in meta or settings(meta) != commands or digest(meta) != exe_sha or "depth 12" not in meta:
        raise ValueError(f"{path.name}: incomplete or mismatched depth, executable or settings")
    with path.open(newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    if len(rows) != n or [r["index"] for r in rows] != list(map(str, range(1,n+1))):
        raise ValueError(f"{path.name}: row count or indices differ")
    return rows


def md(*cells):
    print("| " + " | ".join(str(c) for c in cells) + " |")


def header(*cells):
    md(*cells)
    md(*["---"]*len(cells))


def first_diff(left,right,keys):
    if len(left) != len(right):
        return f"row counts differ: {len(left)} versus {len(right)}"
    for i,(l,r) in enumerate(zip(left,right),1):
        a=tuple(l[k] for k in keys)
        b=tuple(r[k] for k in keys)
        if a != b:
            return f"position/depth {i}, observed {a}, reference {b}"
    return None


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("part",choices=["A","B","D"])
    parser.add_argument("root",type=Path,help="Job4 results directory")
    parser.add_argument("lab",type=Path,help="parent containing job1, job3 and job4 evidence")
    arg=parser.parse_args()
    sys.dont_write_bytecode=True
    sys.path.insert(0,str(arg.lab/"job3"))
    from read_ladders import audit
    def old_dir(): return arg.lab/"job3/step1"
    originals={s:audit(old_dir(), s,20) for s in ("S14","PC20")}
    old_sha=digest((old_dir()/"PC20.meta").read_text().splitlines())
    def ladder(part,label,profile,change,patch):
        rows,hits,repeat,opts=audit(arg.root/part,label,20)
        metadata=(arg.root/part/f"{label}.meta").read_text().splitlines()
        if opts!=extend_options(originals[profile][-1],change) or f"profile {profile}" not in metadata:
            raise ValueError(f"{part}/{label}: wrong profile/ordered settings")
        if not patch and digest(metadata)!=old_sha:
            raise ValueError(f"{part}/{label}: executable differs from job 3 PC")
        return rows, hits[0] if hits else None, repeat
    if arg.part=="B":
        print("PC build on P, depth 1 through 20. Each result was reconstructed from raw UCI traffic.\n")
        header("Arm","Settings","First mate depth","Score","Nodes there","D20 move / score / nodes")
        for label,profile,change in B:
            rows,hit,_=ladder("B",label,profile,change,False)
            if not change:
                diff=first_diff(rows,originals[profile][0],range(6))
                if diff: raise ValueError(f"B/{label} vs job 3: {diff}")
            last=rows[-1]
            md(label,profile+(" + "+change if change else ""),hit[0] if hit else "not by 20",
               f"{hit[3]} {hit[4]}" if hit else "—",hit[5] if hit else "—",
               f"{last[2]} / {last[3]} {last[4]} / {last[5]:,}")
        print("\nBoth unchanged ladders matched job 3 on all 20 depths.")
        return
    floor_sha=digest((arg.root/"A/Floor0.meta").read_text().splitlines())
    documented=originals["PC20"][-1]
    if arg.part=="D":
        print("PC with the floor patch, PC20, depth 12. Ratios use the same suite at floor 0.\n")
        header("Suite","Rows per floor","Floor 0 nodes","Floor 1 nodes","Ratio","Floor 1 first three","Changed best moves")
        for suite,(count,_,_) in SUITES.items():
            floor=[]
            for part,level in (("A",0),("D",1)):
                path=arg.root/part/f"{suite}_floor{level}.tsv"
                floor.append(read_suite(path,count,extend_options(documented,f"NullChildFloor {level}"),floor_sha))
            a,b=floor
            diff=first_diff(a,b,["index","fen"])
            if diff: raise ValueError(f"D/{suite}: {diff}")
            n0=sum(int(r["nodes"]) for r in a)
            n1=sum(int(r["nodes"]) for r in b)
            md(suite,count,f"{n0:,}",f"{n1:,}",f"{n1/n0:.8f}",", ".join(r["nodes"] for r in b[:3]),
               sum(l["bestmove"]!=r["bestmove"] for l,r in zip(a,b)))
        return
    forecast={}
    path=arg.lab/"job4/prediction.txt"
    for line in path.read_text().splitlines():
        fields=line.split()
        if fields and fields[0] in ("A1","A2","A3"):
            forecast[fields[0]]=tuple(map(int,fields[-3:]))
    if set(forecast)!={"A1","A2","A3"}:
        raise ValueError(f"{path}: expected three forecast rows")
    print("PC20 on P, requested depths 1 through 20. Each result was reconstructed from raw UCI traffic.\n")
    header("Arm","Change","First mate depth","Score","Nodes there","Forecast point [range]","Exact","In range")
    for label,arm,change,patch in (("Base3","A1","NullMoveBase 3",False),("Base4","A2","NullMoveBase 4",False),
                                   ("Floor1","A3","NullChildFloor 1",True)):
        rows,hit,_=ladder("A",label,"PC20",change,patch)
        if patch and digest((arg.root/"A"/(label+".meta")).read_text().splitlines())!=floor_sha:
            raise ValueError(f"A/{label}: executable differs from Floor0")
        point,low,high=forecast[arm]
        actual=hit[0] if hit else None
        md(arm,change,actual or "not by 20",f"{hit[3]} {hit[4]}" if hit else "—",
           hit[5] if hit else "—",f"{point} [{low}, {high}]","yes" if actual==point else "no",
           "yes" if actual is not None and low<=actual<=high else "no")
    ref=originals["PC20"][0]
    floor,_,_=ladder("A","Floor0","PC20","NullChildFloor 0",True)
    diff=first_diff(floor,ref,range(6))
    if diff: raise ValueError("A/Floor0 versus job 3 PC20: "+diff)
    last=floor[-1]
    print(f"\nFloor 0 on P matched job 3 on 20/20 depths, including D20 {last[2]} {last[3]} {last[4]}, {last[5]:,} nodes.\n")
    header("Suite","Rows at floor 0","Node sum","First three","Historical PCA comparison")
    for suite,(count,target,first3) in SUITES.items():
        rows=read_suite(arg.root/"A"/f"{suite}_floor0.tsv",count,extend_options(documented,"NullChildFloor 0"),floor_sha)
        path=arg.lab/"job1/rows"/f"{suite}_base_d12.tsv"
        with path.open() as stream:
            ref=list(csv.DictReader(stream,delimiter="\t"))
        diff=first_diff(rows,ref,["index","fen","nodes","bestmove"])
        values=[int(r["nodes"]) for r in rows]
        same=not diff and sum(values)==target and values[:3]==first3
        md(suite,count,f"{sum(values):,}",", ".join(map(str,values[:3])),f"{count}/{count} equal" if same else diff or "different totals")


if __name__=="__main__":
    try:
        main()
    except (OSError,ValueError,IndexError) as exc:
        sys.exit(str(exc))
