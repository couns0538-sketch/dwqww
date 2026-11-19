"""Build the job 19 edge manifest from the frozen job 18 table and both UCI advertisements."""
import argparse
import csv
import hashlib
from pathlib import Path
import re
import subprocess

WORK = Path('/workspace/work')
TABLE_SHA = '8b9f11a1ca4f209b57cbc59ae6fc4c2bd6a09a54ffd4ce5af265fa87fbbede81'
BUILDS = {
    'r15d': (WORK/'j7base/build/forge','9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671'),
    'kF': (WORK/'j16kf/build/forge','c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb')}
HEADER = 'edge index name bound start table_value r15d_min r15d_max kF_min kF_max value status first_game last_game'.split()
SPIN = re.compile(r'^option name ([A-Za-z0-9]+) type spin default (-?\d+) min (-?\d+) max (-?\d+)$',re.M)
REFUSAL = re.compile(r'unknown option|invalid value|\bERROR\b',re.I)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def exchange(exe, script):
    result = subprocess.run([str(exe)],input='\n'.join(script)+'\n',cwd=exe.parent,
                            text=True,capture_output=True,check=True,timeout=25)
    output=result.stdout+result.stderr
    for line in output.splitlines():
        if REFUSAL.search(line):
            raise RuntimeError(f'{exe}: {line}')
    return output

def spins(output):
    return {name:tuple(map(int,(start,lo,hi))) for name,start,lo,hi in SPIN.findall(output)}

def generate(table, ads):
    rows=[]
    for i,setting in enumerate(table,1):
        name=setting['name']
        start=int(setting['start'])
        lo0,hi0=map(int,(setting['min'],setting['max']))
        _,lo1,hi1=ads['r15d'][name]
        _,lo2,hi2=ads['kF'][name]
        lo,hi=max(lo0,lo1,lo2),min(hi0,hi1,hi2)
        if not lo <= start <= hi:
            raise ValueError(f'{name} start outside joint range')
        for side,bound in enumerate(('min','max')):
            edge=2*i-1+side
            value=(lo,hi)[side]
            first=500001+10*(edge-1)
            rows.append(dict(zip(HEADER,(edge,i,name,bound,start,(lo0,hi0)[side],lo1,hi1,lo2,hi2,value,'start' if start==value else 'play',first,first+4))))
    return rows

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--table',type=Path,default=WORK/'j18sets/sets.txt')
    parser.add_argument('--out',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--r15d',type=Path,default=BUILDS['r15d'][0])
    parser.add_argument('--kf',type=Path,default=BUILDS['kF'][0])
    args=parser.parse_args()
    assert sha(args.table)==TABLE_SHA
    with args.table.open() as f: table=list(csv.DictReader(f,delimiter='\t'))
    assert len({row['name'] for row in table})==len(table)==40
    binaries={'r15d':args.r15d,'kF':args.kf}
    ads={}
    args.out.mkdir(exist_ok=True,parents=True)
    with (args.out/'uci-bounds.txt').open('w') as out:
        for label,exe in binaries.items():
            assert sha(exe)==BUILDS[label][1]
            uci=exchange(exe,['uci','quit'])
            assert 'uciok' in uci.splitlines()
            ads[label]=spins(uci)
            print(label,exe,sha(exe),file=out)
            for row in table:
                name=row['name']
                matches=[line for line in uci.splitlines() if line.startswith(f'option name {name} type spin ')]
                assert len(matches)==1 and name in ads[label]
                print(matches[0],file=out)
    records=generate(table,ads)
    manifest=args.out/'edge-sets.tsv'
    with manifest.open('w',newline='') as f:
        writer=csv.DictWriter(f,HEADER,delimiter='\t',lineterminator='\n')
        writer.writeheader();writer.writerows(records)
    skipped=[r for r in records if r['status']=='start']
    narrower=[r for r in records if r['value']!=r['table_value']]
    print('Frozen job 18 table SHA-256',TABLE_SHA)
    print('Manifest SHA-256',sha(manifest))
    print('80 edges; play',len(records)-len(skipped),'start',len(skipped))
    print('Start edges:',', '.join(f"{r['edge']} {r['name']} {r['bound']}={r['value']}" for r in skipped))
    print('Effective bounds narrowed relative to table:',len(narrower))
    for r in narrower: print(r)

if __name__=='__main__': main()
