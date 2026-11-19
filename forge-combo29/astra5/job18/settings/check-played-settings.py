"""Compare each completed slot's actual configuration log with the frozen set table."""
import csv
import hashlib
from pathlib import Path
import re
import sys

root=Path('/workspace/work')
results=root/'j18match/results'
frozen=Path(__file__).resolve().parent/'sets.txt'
digest=hashlib.sha256(frozen.read_bytes()).hexdigest()
assert digest=='8b9f11a1ca4f209b57cbc59ae6fc4c2bd6a09a54ffd4ce5af265fa87fbbede81'
with frozen.open() as f: table=list(csv.DictReader(f,delimiter='\t'))
pc20=dict(re.fullmatch(r'setoption name (\S+) value (\S+)',line).groups() for line in (root/'j7base/pc20.txt').read_text().splitlines())
build_digests={'r15d':'9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671','kF':'c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb'}
arms=['K18-1','K18-2','C18']+[f'{driver}{v}-{build}' for v in range(1,6) for driver in 'RF' for build in build_digests]
for arm in sys.argv[1:] or arms:
    assert arm in arms
    folder=results/arm
    assert (folder/'run.log').read_text().endswith('status COMPLETE\n')
    control=arm.startswith(('K','C'))
    v=(2 if arm.startswith('C') else 1) if control else int(arm[1])
    driver='R' if control else arm[0]
    build='r15d' if control else arm.split('-')[1]
    config=pc20 | {row['name']:row[f'v{v}'] for row in table} | {'NNUEArchFile':str(root/'j7net/net768.nnue'),'NNUEArch':'true'}
    commands=[f'setoption name {n} value {val}' for n,val in config.items()]
    go='go softnodes 2000' if driver=='R' else 'go nodes 20000'
    slots=1 if driver=='R' else 2
    prefix='engine ' if driver=='R' else 'both '
    processes=[]
    for s in range(1,slots+1):
        text=(folder/f'slot{s}/run.log').read_text()
        assert text.endswith('status COMPLETE\n')
        assert re.findall('^'+prefix+'(setoption .*)$',text,re.M)==commands
        assert f'go {go} driver {driver} set {v} sets_sha256 {digest} ' in text
        assert re.search(r'^executable \S+ sha256 '+build_digests[build]+'$',text,re.M)
        roles=['P1_Both'] if driver=='R' else ['P1_White','P2_Black']
        for role in roles:
            pid=re.search(rf'^{role} pid (\d+) child_cpu_affinity',text,re.M)[1]
            assert re.search(rf'^{role} info string NNUE v3 active: .*checksum 30ab43b4ba5db5f3 ',text,re.M)
            processes.append(pid)
    assert len(set(processes))==len(processes)
    print(f'{arm} set {v}, {driver}, {go}: all 51 ordered commands agree with frozen table and PC20; {slots} slot(s); {len(processes)} distinct process(es), every active net checksum 30ab43b4ba5db5f3.',flush=True)
