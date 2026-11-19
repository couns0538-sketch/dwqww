"""Check all 76 playable edge configurations on each real binary, without issuing search commands."""
import csv
import hashlib
import re
import subprocess
from pathlib import Path

ROOT=Path('/workspace/work')
DEST=Path(__file__).resolve().parent
EDGES=DEST/'edge-sets.tsv'
TABLE=ROOT/'j18sets/sets.txt'
NET=ROOT/'j7net/net768.nnue'
PIN={'r15d':(ROOT/'j7base/build/forge','9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671'),'kF':(ROOT/'j16kf/build/forge','c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb')}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
    with p.open() as f: return list(csv.DictReader(f,delimiter='\t'))
meta=read(TABLE)
edges=read(EDGES)
assert sha(EDGES)=='8a2c10231f4ea230831c6d2e73da26c369f121ddf93432c8135b17f42150d6d9'
assert sha(TABLE)=='8b9f11a1ca4f209b57cbc59ae6fc4c2bd6a09a54ffd4ce5af265fa87fbbede81'
assert sha(NET)=='c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7'
assert all(sha(binary)==digest for binary,digest in PIN.values())
starts={r['name']:r['start'] for r in meta}
pc=dict(re.fullmatch(r'setoption name ([A-Za-z0-9]+) value (\S+)',s).groups() for s in (ROOT/'j7base/pc20.txt').read_text().splitlines())
assert pc | starts == starts | pc
retained={n:x for n,x in pc.items() if n not in starts}
assert retained=={'Threads':'1','Hash':'16','NonPawnCorrection':'true','CuckooRep':'true','HistRework':'2','TtPruneV2':'true','CorrHistV2':'true','MateAlphaGuard':'true','OwnBook':'false'}
print(f'Edge manifest {sha(EDGES)}; table {sha(TABLE)}. SHA match both executables and net.',flush=True)
print('Each probed process is fresh. Sent uci, all 51 options, isready, uci for live readback, quit. No searches or game commands.',flush=True)
print('39 tunables expose live integer storage in the second uci. DrawJitter advertises a fixed default and uses a separately clamped UCI handler (r15d src/uci.cpp:730; kF src/uci.cpp:815).',flush=True)
counts={label:0 for label in PIN}
for e,row in enumerate(edges,1):
    assert e==int(row['edge'])
    setting=meta[(e-1)//2]
    name=setting['name']
    bound='min' if e%2 else 'max'
    assert row['bound']==bound and row['name']==name and int(row['index'])==(e+1)//2
    assert [int(row[k]) for k in ('first_game','last_game')]==[500001+10*(e-1),500005+10*(e-1)]
    assert all(int(row[arm+'_'+side])==int(setting[side]) for arm in PIN for side in ('min','max'))
    assert row['value']==row['table_value']==setting[bound]
    assert row['start']==setting['start'] and (row['status']=='start')==(row['value']==row['start'])
    if row['status']=='start':
        print(f'{e:02d} {name} {bound} {row["value"]} start. Probes skipped.',flush=True)
        continue
    applied=starts | {name:row['value']}
    assert [key for key in applied if applied[key]!=starts[key]]==[name]
    config=pc | applied | {'NNUEArchFile':str(NET),'NNUEArch':'true'}
    assert len(config)==51 and all(config[k]==v for k,v in retained.items())
    commands=[f'setoption name {key} value {value}' for key,value in config.items()]
    for label,(binary,_) in PIN.items():
        script=['uci',*commands,'isready','uci','quit']
        raw=subprocess.run([str(binary)],input='\n'.join(script)+'\n',text=True,capture_output=True,timeout=15,cwd=binary.parent,check=True)
        answer=raw.stdout+raw.stderr
        for line in answer.splitlines():
            if re.search(r'(?:unknown option|invalid value|\bERROR\b)',line,re.I):
                print(f'{e} {label} REFUSAL {line}',flush=True)
                raise RuntimeError(line)
        initial,final=answer.split('readyok\n')
        assert all(f'option name {key} type ' in initial for key in config)
        assert re.search(r'NNUE v3 loaded: .*checksum 30ab43b4ba5db5f3\b',initial)
        active=next(s for s in initial.splitlines() if 'NNUE v3 active:' in s)
        assert re.search(r'checksum 30ab43b4ba5db5f3\b',active)
        spins={n:(v,lo,hi) for n,v,lo,hi in re.findall(r'^option name (\S+) type spin default (-?\d+) min (-?\d+) max (-?\d+)$',final,re.M)}
        for key,value in applied.items():
            stored,lo,hi=spins[key]
            assert int(lo)<=int(value)<=int(hi)
            if key!='DrawJitter': assert stored==value,(e,label,key,stored,value)
        counts[label]+=1
        print(f'{e:02d} {name} {bound} {row["value"]} {label} accepted 51/51 commands; 39/39 live values; {active}',flush=True)
print(f'Completed {counts["r15d"]} r15d and {counts["kF"]} kF fresh-process configurations, 4 start edges skipped, no refusal.',flush=True)
