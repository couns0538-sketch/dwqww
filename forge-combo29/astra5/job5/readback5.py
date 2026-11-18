"""Independently replay P transcripts and recount the depth-12 O/G rows for Job 5."""
import argparse
import csv
from fractions import Fraction
from pathlib import Path
import sys


SIZES = {"O": 200, "G": 353}
OPTION = {"A": "NullMateGuard", "B": "QsNullChecks"}
REF_KEYS = ("index", "fen", "nodes", "bestmove")


def md(*values):
    print("| " + " | ".join(map(str, values)) + " |")


def header(*values):
    md(*values)
    md(*["---"] * len(values))


def columns(path):
    with path.open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source, delimiter="\t"))


def demand_equal(rows, expected, keys, name):
    if len(rows) != len(expected):
        raise ValueError(f"{name}: row counts {len(rows)} vs {len(expected)}")
    for i,(r,e) in enumerate(zip(rows,expected),1):
        obs = [r[k] for k in keys]
        ref = [e[k] for k in keys]
        if obs != ref:
            raise ValueError(f"{name}, first difference at row {i}: measured {obs}, reference {ref}")


def p_values(row):
    return f"{row[2]} / {row[3]} {row[4]} / {row[5]:,}"


def grade_file(prediction):
    forecasts = {}
    for line in prediction.read_text().splitlines():
        cells = line.split()
        if len(cells) == 5 and cells[0] in OPTION and cells[1] in ("mate", "G_ratio", "flagged", "unflagged"):
            forecasts[cells[0],cells[1]] = tuple(map(Fraction, cells[2:]))
    if len(forecasts) != 8:
        raise ValueError(f"expected eight named forecast rows in {prediction}, parsed {len(forecasts)}")
    return forecasts


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("part",choices=("A","B"))
    parser.add_argument("mode",choices=("zero","one"))
    parser.add_argument("root",type=Path,help="job5 directory containing A/ and B/")
    parser.add_argument("lab",type=Path,help="parent of job1, job3, job4 and job5 directories")
    args=parser.parse_args()
    sys.dont_write_bytecode=True
    sys.path.insert(0,str(args.lab/"job3"))
    sys.path.insert(0,str(args.lab/"job4"))
    from read_ladders import audit
    from readback4 import read_suite, digest, extend_options

    raw_floor,_,_,floor_options = audit(args.lab/"job4/A","Floor0",20)
    pc20 = audit(args.lab/"job3/step1","PC20",20)[-1]
    if floor_options != extend_options(pc20,"NullChildFloor 0"):
        raise ValueError("historical F0 control does not use PC20 plus NullChildFloor 0")
    historical = {s:columns(args.lab/f"job4/A/{s}_floor0.tsv") for s in SIZES}
    maskrows=columns(args.lab/"job4/C/rows/G_F0.tsv")
    demand_equal(maskrows,historical["G"],REF_KEYS,"job4 G_F0 pre-treatment mask")
    mask=[int(r["nc0"].split()[5])>0 for r in maskrows]
    if len(mask)!=353 or sum(mask)!=81 or sum(int(r["nc0"].split()[5]) for r in maskrows)!=513:
        raise ValueError("historical G mask differs from 513 events across 81/353 positions")

    datasets={}
    arm=args.part
    for level in (("zero",) if args.mode=="zero" else ("zero","one")):
        d=args.root/arm/level
        val=int(level=="one")
        opts=extend_options(pc20, f"{OPTION[arm]} {val}")
        ladder, first, _, sent=audit(d,"P",20)
        if sent!=opts:
            raise ValueError(f"{d}: raw UCI settings differ from expected PC20 override")
        sha=digest((d/"P.meta").read_text().splitlines())
        if level=="zero":
            demand_equal(ladder,raw_floor,range(6),f"{arm} zero P versus job4")
        else:
            if sha!=datasets["zero"]["sha"]:
                raise ValueError(f"{arm} on/off executable identities differ")
        suites={}
        for s,n in SIZES.items():
            suites[s] = read_suite(d/f"{s}.tsv",n,opts,sha)
            demand_equal(suites[s], historical[s],
                         REF_KEYS if level=="zero" else ("index","fen"), f"{arm} {level} {s} versus job4")
        datasets[level]={"sha":sha, "p":ladder, "first":first[0] if first else None, **suites}
    print(f"{arm}, {OPTION[arm]} 0: all 20 P ladder depths, 200 O rows and 353 G rows matched job 4 floor 0. "
          "Each P TSV row matched its UCI transcript.\n")
    if args.mode=="zero":
        return
    base,armdata=datasets["zero"],datasets["one"]
    mate=armdata["first"]
    print(f"{OPTION[arm]} 1 first reported g3g6 with a positive mate score at "
          + (f"D{mate[0]} ({mate[5]:,} nodes)." if mate else "no depth through D20.") + "\n")
    header("D","Value 0 move / score / nodes","Value 1 move / score / nodes")
    for r0,r1 in zip(base["p"],armdata["p"]):
        md(r0[0],p_values(r0),p_values(r1))
    print()
    header("Suite","Rows","Value 0 nodes","Value 1 nodes","Node ratio","Value 1 first three","Changed best moves")
    results={"mate":mate[0] if mate else None}
    for s in SIZES:
        old,new=base[s],armdata[s]
        n0=sum(int(r["nodes"]) for r in old)
        n1=sum(int(r["nodes"]) for r in new)
        ratio=Fraction(n1,n0)
        changed=[a["bestmove"]!=b["bestmove"] for a,b in zip(old,new)]
        md(s,len(new),f"{n0:,}",f"{n1:,}",f"{float(ratio):.8f}",
           ", ".join(r["nodes"] for r in new[:3]), sum(changed))
        if s=="G":
            flagged=sum(c and f for c,f in zip(changed,mask))
            other=sum(c and not f for c,f in zip(changed,mask))
            results.update(G_ratio=ratio,flagged=flagged,unflagged=other)
    print()
    header("Pre-treatment G group","Changed / positions","Changed move rate")
    for key,desc,n in (("flagged","Job 4 NC0[4] > 0",sum(mask)), ("unflagged","Job 4 NC0[4] = 0",len(mask)-sum(mask))):
        md(desc,f"{results[key]} / {n}",f"{results[key]/n:.4%}")
    print()
    forecasts=grade_file(args.lab/"job5/prediction.txt")
    header("Forecast","Point","Inclusive range","Actual","Exact","Within range")
    for key in ("mate","G_ratio","flagged","unflagged"):
        point,lo,hi=forecasts[arm,key]
        x=results[key]
        md(key,f"{float(point):g}",f"{float(lo):g} to {float(hi):g}",
           (f"{float(x):.8f}" if key=="G_ratio" else x) if x is not None else "not by 20",
           "yes" if point==x else "no","yes" if x is not None and lo<=x<=hi else "no")


if __name__=="__main__":
    try:
        main()
    except (OSError,ValueError,IndexError) as e:
        sys.exit(str(e))
