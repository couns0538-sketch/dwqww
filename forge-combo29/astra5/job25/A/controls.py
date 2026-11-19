"""Evaluate the KA1 and CA2 controls without comparing node counts to the Part A budget."""
import argparse
import csv
from pathlib import Path


def rows(file):
    with file.open(newline='') as f:
        result=list(csv.DictReader(f,delimiter='\t'))
    assert [(int(r['position']),int(r['repeat'])) for r in result]==[(i,j) for i in range(1,31) for j in range(1,9)]
    return result


def value(row):
    return tuple(row[k] for k in ('depth','score','nodes','pv','bestmove'))


def run(p):
    arm=p.name; a,b=[rows(p/n/'searches.tsv') for n in ['r15d','kF']]
    if arm=='A1':
        for i in range(30):
            aa,bb=a[8*i:8*(i+1)],b[8*i:8*(i+1)]
            for name,group in [('r15d',aa),('kF',bb)]:
                for row in group:
                    if value(row)!=value(aa[0]):
                        print(f'KA1 FAIL position {i+1}: r15d repeat 1 {value(aa[0])} vs {name} repeat {row["repeat"]} {value(row)}');return 1
        print('KA1 PASS: 30/30 positions; all 8 repeats in each build and across both builds had identical last depth, score, nodes, PV and bestmove (240 searches per build).')
        return 0
    passed=True
    for name,group in [('r15d',a),('kF',b)]:
        variable=[i+1 for i in range(30) if len({r['nodes'] for r in group[8*i:8*(i+1)]})>1]
        passed=passed and len(variable)>=15
        print(f'{name}: {len(variable)}/30 positions had >1 distinct final node count in eight repeats; positions '+','.join(map(str,variable)))
    print('CA2 '+('PASS' if passed else 'FAIL'))
    return int(not passed)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('arm',type=Path);args=p.parse_args();assert args.arm.name in ('A1','A2');raise SystemExit(run(args.arm))
