"""Independently audit the published value table and both actual UCI configurations."""
import csv
import hashlib
from pathlib import Path
import random
import re
import subprocess
import sys

work = Path('/workspace/work')
folder = Path(__file__).resolve().parent
tablefile = folder/'sets.txt'
job = (work/'job18.md').read_text().split('\nTHE 40 SETTINGS')[1].split('\n\nTHE FIVE VALUE SETS')[0]
parameters = re.findall(r'\b([A-Z][A-Za-z]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)',job)
with tablefile.open() as f:
    reader = csv.DictReader(f, delimiter='\t')
    assert reader.fieldnames == ['name','start','min','max','step','v1','v2','v3','v4','v5']
    table = list(reader)
assert len(set(row['name'] for row in table)) == len(table) == len(parameters) == 40
assert [tuple(row[key] for key in reader.fieldnames[:5]) for row in table] == parameters
byname = {row['name']:row for row in table}
net = work/'j7net/net768.nnue'
pc20 = dict(re.fullmatch(r'setoption name (\S+) value (\S+)',line).groups() for line in (work/'j7base/pc20.txt').read_text().splitlines())
retained = {k:v for k,v in pc20.items() if k not in byname}
assert retained == {'Threads':'1','Hash':'16','NonPawnCorrection':'true','CuckooRep':'true','HistRework':'2','TtPruneV2':'true','CorrHistV2':'true','MateAlphaGuard':'true','OwnBook':'false'}
for name in pc20.keys() & byname.keys():
    assert byname[name]['start'] == pc20[name]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

builds = {'r15d':(work/'j7base/build/forge','9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671'), 'kF':(work/'j16kf/build/forge','c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb')}
assert all(digest(path)==sha for path,sha in builds.values())
assert digest(net)=='c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7'
print(f'Input table {digest(tablefile)}. {len(table)} distinct names in handoff order. All 40 (start,min,max,step) tuples match the handoff verbatim.')
print('13 PC20 numeric tunables overlap the table and all handoff starting values match. The 9 retained controls are:',retained)
ngames=0
for v in range(1,6):
    rng=random.Random(9000+v)
    tweaks={}
    clamped=[]
    for row in table:
        name=row['name']
        raw=int(row['start'])+(rng.randrange(7)-3)*int(row['step'])
        expected=sorted((int(row['min']),raw,int(row['max'])))[1]
        assert int(row[f'v{v}'])==expected
        if raw!=expected: clamped.append(f'{name}={raw}->{expected}')
        tweaks[name]=str(expected)
    commands = pc20 | tweaks | {'NNUEArchFile':str(net),'NNUEArch':'true'}
    assert len(commands)==51
    print(f'Set {v}, seed {9000+v}: 40/40 independently regenerated; clamped {len(clamped)}: '+', '.join(clamped))
    lines=[f'setoption name {name} value {value}' for name,value in commands.items()]
    for label,(path,_) in builds.items():
        sequence=['uci',*lines,'isready','uci','quit']
        result=subprocess.run([str(path)],input='\n'.join(sequence)+'\n',capture_output=True,text=True,timeout=20,check=True)
        replies=result.stdout+result.stderr
        if re.search(r'unknown option|invalid value|\bERROR\b',replies,re.I):
            print(replies,flush=True);raise SystemExit(f'REFUSAL {label} set {v}')
        before,after=replies.split('readyok\n')
        assert 'NNUE v3 loaded' in before and re.search(r'NNUE v3 active: .*checksum 30ab43b4ba5db5f3\b',before)
        def spins(response):
            return dict((n,tuple(map(int,x))) for n,*x in re.findall(r'^option name (\w+) type spin default (\d+) min (\d+) max (\d+)$',response,re.M))
        start=spins(before); updated=spins(after)
        for name,row in byname.items():
            assert start[name][1:] == (int(row['min']),int(row['max'])),(name,start[name])
            assert pc20.get(name,str(start[name][0])) == row['start'],name
            if name!='DrawJitter': assert str(updated[name][0])==tweaks[name],(label,name,updated[name][0],tweaks[name])
        assert all(f'option name {name} type ' in before for name in commands)
        print(f'  {label} SHA-256 {digest(path)}. All 51 commands declared, 40 bounds verified, 39 dynamic tunable values read back, readyok, no refusal; '+next(l for l in before.splitlines() if l.startswith('info string NNUE v3 active')))
print('DrawJitter is the one static UCI declaration. Source directly assigns its separately clamped integer in src/uci.cpp (r15d line 730, kF line 815). The other 39 declarations dereference the live parameter table, verified after setoption by a second uci. For switches the audit verifies command values, advertisement and absence of refusals. No search commands or games were used.')
