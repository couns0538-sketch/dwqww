"""Read only the recorded job 19 commands and compare them to the frozen edge manifest."""
import argparse
import csv
from datetime import datetime
import hashlib
from pathlib import Path
import re
import time

W=Path('/workspace/work')
DEST=Path(__file__).resolve().parent
RESULTS=W/'j19match/results'
EDGE_SHA='8a2c10231f4ea230831c6d2e73da26c369f121ddf93432c8135b17f42150d6d9'
TABLE_SHA='8b9f11a1ca4f209b57cbc59ae6fc4c2bd6a09a54ffd4ce5af265fa87fbbede81'
def manifest(p,h):
    assert hashlib.sha256(p.read_bytes()).hexdigest()==h
    with p.open() as f: return list(csv.DictReader(f,delimiter='\t'))
edges=manifest(DEST/'edge-sets.tsv',EDGE_SHA)
starts={row['name']:row['start'] for row in manifest(W/'j18sets/sets.txt',TABLE_SHA)}
pc=dict(re.fullmatch(r'setoption name (\S+) value (\S+)',s).groups() for s in (W/'j7base/pc20.txt').read_text().splitlines())
digests={'r15d':'9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671','kF':'c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb'}
def compare(arm):
    is_edge=arm.startswith('E')
    control=arm in ('K19-1','K19-2','C19')
    build='r15d' if control else arm.split('-')[1]
    options=pc.copy()
    if is_edge:
        eid=int(arm[1:3])
        edge=edges[eid-1]
        assert edge['status']=='play'
        options.update(starts)
        options[edge['name']]=edge['value']
        low,high=(int(edge[k]) for k in ('first_game','last_game'))
    elif arm=='C19': options['LmrQuietBase']='60'
    options.update({'NNUEArchFile':str(W/'j7net/net768.nnue'),'NNUEArch':'true'})
    if not is_edge:
        if control: low,high=3791,3792
        elif arm.startswith('D1'): low,high=3793,3808
        else: low,high=3809,3812
    prefix='engine' if is_edge else 'both'
    go='go softnodes 2000' if is_edge else ('go nodes 1000000' if arm.startswith('D2') else 'go nodes 250000')
    txt=(RESULTS/arm/'slot1/run.log').read_text()
    assert txt.endswith('status COMPLETE\n')
    assert f'S 1 logical_cpu ' in txt and f'book_range {low} {high} slot_first {low} stride 1' in txt
    assert f'Search command: {go}' in txt
    assert re.search(r'^executable \S+ sha256 '+digests[build]+r'$',txt,re.M)
    commands=[f'setoption name {key} value {val}' for key,val in options.items()]
    assert re.findall(r'^'+prefix+r' (setoption .*)$',txt,re.M)==commands
    if is_edge:
        assert f'edge_manifest_sha256 {EDGE_SHA} edge {eid} {edge["name"]} {edge["bound"]} requested {edge["table_value"]} applied {edge["value"]}' in txt
    roles=['P1_Both'] if is_edge else ['P1_White','P2_Black']
    for role in roles:
        assert re.search(rf'^{role} info string NNUE v3 active: .*checksum 30ab43b4ba5db5f3\b',txt,re.M)
    return f'{arm}\t{build}\t{len(options)}\t{len(roles)}\t{go}\t{low}\t{high}\tPASS'
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--watch',action='store_true')
    args=parser.parse_args()
    end=datetime.fromisoformat('2026-11-19T01:33:15+00:00').timestamp()
    print('arm\tbuild\toptions_checked\tactive_net_processes\tgo\tfirst\tlast\tverification',flush=True)
    names=['K19-1','K19-2','C19']+[f'{stage}-{build}' for stage in ['D1']+[f'E{int(row["edge"]):02}' for row in edges if row['status']=='play']+['D2'] for build in digests]
    for arm in names:
        p=RESULTS/arm/'run.log'
        while args.watch and not p.exists() and time.time()<end and not (RESULTS/'JOB-STOP.txt').exists(): time.sleep(1)
        if not p.exists():
            print(f'# Stopped before {arm}');return
        print(compare(arm),flush=True)
    for row in edges:
        if row['status']=='start':
            assert not list(RESULTS.glob(f'E{int(row["edge"]):02}-*/slot*/run.log'))
    print('# All 159 prepared arms passed; all four start edges have zero slot logs.',flush=True)

if __name__=='__main__': main()
