"""Audit completed job 19 runs from per-slot game starts and receipt timestamps."""
import argparse
import csv
import hashlib
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class Interval:
    name: str
    start: datetime
    end: datetime

def t(s):
    return datetime.fromisoformat(s.replace('Z','+00:00'))

def peak_intervals(windows):
    events=[]
    for interval in windows:
        assert interval.start<=interval.end, interval
        if interval.start<interval.end:
            events.extend([(interval.start,1,interval.name),(interval.end,-1,interval.name)])
    active=set()
    peaks=[]
    highest=0
    for moment,kind,label in sorted(events):
        if kind<0:
            assert label in active,label
            active.remove(label)
        else:
            assert label not in active,label
            active.add(label)
            if len(active)>highest:
                highest=len(active)
                peaks.append((moment,tuple(sorted(active))))
    assert not active
    return highest,peaks[-1]

def read_csv(p):
    with p.open() as f:
        return list(csv.DictReader(f,delimiter='\t'))

def tabfile(path,columns,rows):
    with path.open('w') as f:
        out=csv.writer(f,delimiter='\t',lineterminator='\n')
        out.writerow(columns)
        out.writerows(rows)

def hashfile(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()

def spec(name,edges):
    if name in ('K19-1','K19-2','C19'):
        return 'r15d','F',250000,3791,3792,None
    stage,arm=name.rsplit('-',1)
    assert arm in ('r15d','kF')
    if stage=='D1':
        return arm,'F',250000,3793,3808,None
    if stage=='D2':
        return arm,'F',1000000,3809,3812,None
    m=re.fullmatch('E(\\d+)',stage)
    assert m,name
    edge=edges[int(m[1])]
    assert edge['status']=='play'
    n=int(m[1])
    first=500001+10*(n-1)
    assert [int(edge['first_game']),int(edge['last_game'])]==[first,first+4]
    return arm,'R',2000,first,first+4,edge

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root',type=Path,help='results directory with one subdirectory per arm')
    parser.add_argument('edges',type=Path)
    parser.add_argument('pc20',type=Path)
    parser.add_argument('out',type=Path)
    parser.add_argument('--require-final',action='store_true')
    parser.add_argument('--deadline',help='expected UTC cutoff (optional)')
    args=parser.parse_args()
    edges={int(row['edge']):row for row in read_csv(args.edges)}
    assert len(edges)==80
    root=args.root
    args.out.mkdir(parents=True,exist_ok=True)
    slots=[]
    games=[]
    ongoing=[]
    cells=[]
    starts={row['name']:row['start'] for row in edges.values()}
    base={x[15:].rsplit(' value ',1)[0]:x.rsplit(' value ',1)[1] for x in args.pc20.read_text().splitlines()}
    assert len(base)==22 and base['Threads']=='1' and base['Hash']=='16' and base['OwnBook']=='false'
    exes={
        'r15d':'9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671',
        'kF':'c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb'
    }
    net='c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7'
    book='7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a'
    order={}
    def add_order(name):
        order[name]=len(order)
    for stage in ('K19-1','K19-2','C19','D1'): add_order(stage)
    for i in sorted(edges):
        if edges[i]['status']=='play': add_order(f'E{i}')
    add_order('D2')
    for path in sorted(root.glob('*/slot*/run.log')):
        arm=path.parent.parent.name
        slot=path.parent.name
        log=path.read_text()
        if not re.search('^status ',log,re.M):
            ongoing.append(arm)
            continue
        build,driver,cap,first,last,edge=spec(arm,edges)
        stage0=arm if arm in ('K19-1','K19-2','C19') else arm.rsplit('-',1)[0]
        stage='E'+str(int(stage0[1:])) if re.fullmatch('E\\d+',stage0) else stage0
        ncpu=int(re.search(r'^arm .*? nproc (\d+) ',log,re.M)[1])
        slots_n=int(re.search(r'^arm .*? S (\d+) ',log,re.M)[1])
        assert ncpu==5 and slots_n==1 and slot=='slot1'
        assert re.search(rf'^arm {arm} build {build} slot 1 .*? book_range {first} {last} slot_first {first} stride 1$',log,re.M)
        assert re.search(rf'^executable .*? sha256 {exes[build]}$',log,re.M)
        assert re.search(rf'^net .*? sha256 {net}$',log,re.M)
        assert re.search(rf'^book .*? sha256 {book}$',log,re.M)
        assert re.search(rf'go go (?:softnodes {cap} driver R|nodes {cap} driver F)',log) and ('go softnodes ' if driver=='R' else 'go nodes ')+str(cap) in log
        inputs=re.findall(r'^(?:engine|both) setoption name (\w+) value (.*)$',log,re.M)
        settings=dict(inputs)
        assert len(settings)==len(inputs)
        expected=base.copy()
        if arm=='C19': expected['LmrQuietBase']='60'
        if edge:
            expected.update(starts)
            expected[edge['name']]=edge['value']
        expected['NNUEArch']='true'
        assert Path(settings['NNUEArchFile']).name=='net768.nnue'
        expected['NNUEArchFile']=settings['NNUEArchFile']
        assert expected==settings, (arm,expected.items()^settings.items())
        pidmap={role:int(pid) for role,pid in re.findall(r'^(P1_White|P2_Black|P1_Both) pid (\d+) child_cpu_affinity',log,re.M)}
        roles=['P1_Both'] if driver=='R' else ['P1_White','P2_Black']
        assert list(pidmap)==roles and len(set(pidmap.values()))==len(roles)
        for role in roles:
            assert re.search(rf'^{role} info string NNUE v3 active: .*checksum 30ab43b4ba5db5f3 ',log,re.M)
        beg=t(re.search(r'^start_utc (\S+)$',log,re.M)[1])
        end=t(re.search(r'^end_utc (\S+)$',log,re.M)[1])
        slot_life=Interval(arm,beg,end)
        slots.append(slot_life)
        rows=read_csv(path.parent/'games.tsv')
        by_id={int(row['book_line']):row for row in rows}
        assert len(by_id)==len(rows)
        assert list(by_id)==list(range(first,first+len(rows)))
        opens={int(i):(t(ts),tuple(int(n) for n in pids.split())) for i,ts,pids in re.findall(r'^game_start (\d+) (\S+) (?:readyok_all|terminal_random_opening) ([\d ]+)$',log,re.M)}
        assert list(opens)==list(range(first,first+len(opens)))
        assert set(by_id)<=set(opens)
        st=re.search(r'^status (\S+)$',log,re.M)[1]
        if st=='COMPLETE': assert set(opens)==set(by_id)==set(range(first,last+1)), arm
        lastend=beg
        for gid,(tm,pids) in opens.items():
            assert pids==tuple(pidmap.values())
            row=by_id.get(gid)
            if row:
                pp=[int(row['p1_pid']),int(row['p2_pid'])]
                assert pp==([pids[0],pids[0]] if driver=='R' else list(pids))
                done=t(row['end_utc'])
            else:
                # A cut game may be open in the log. Bound its duration by slot end.
                assert st!='COMPLETE'
                done=end
            assert lastend<=tm<=done<=end
            games.append(Interval(f'{arm}/{gid}',tm,done))
            lastend=done
            if args.deadline and row:
                assert done<t(args.deadline)
        cells.append([order[stage],stage,arm,st,beg.isoformat(),end.isoformat(),len(opens),len(by_id),int((end-beg).total_seconds()*1000)])
    assert slots and games
    if args.require_final: assert not ongoing,ongoing
    peak_g,peak_example=peak_intervals(games)
    peak_s,peak_slot=peak_intervals(slots)
    assert peak_g<=2 and peak_s<=2
    group=defaultdict(list)
    for rank,stage,arm,st,beg,end,*_ in cells:
        group[(rank,stage)].append((t(beg),t(end)))
    previous=None
    for (rank,stage),ts in sorted(group.items()):
        first_start=min(x[0] for x in ts)
        if previous: assert previous<=first_start,stage
        previous=max(x[1] for x in ts)
    by_build=defaultdict(list)
    for interval in slots:
        b=spec(interval.name,edges)[0]
        by_build[b].append(interval)
    assert all(peak_intervals(items)[0]==1 for items in by_build.values())
    if args.require_final:
        assert not (root/'JOB-STOP.txt').exists(),'engine refusal indicated, retain raw refusal separately'
    tabfile(args.out/'arm-intervals.tsv',['stage_order','stage','arm','status','slot_start_utc','slot_end_utc','games_started','games_completed','slot_elapsed_ms'],sorted(cells))
    bits=[
        f'nproc 5; floor((nproc - 1) / 2) = 2 simultaneous games across both builds.',
        f'{len(slots)} finished slot-worker lifetimes; {len(games)} game-start intervals, including cut games if present. {sum(x[7] for x in cells)} game-end receipts.',
        f'Peak overlapping game intervals {peak_g}, first observed at {peak_example[0].isoformat()} for {", ".join(peak_example[1])}.',
        f'Peak overlapping slot-worker lifetimes {peak_s}, first observed at {peak_slot[0].isoformat()} for {", ".join(peak_slot[1])}.',
        f'Per-build peak slot-worker lifetimes: '+', '.join(f'{name} {peak_intervals(items)[0]}' for name,items in sorted(by_build.items()))+'.',
        'Each slot worker processed one game at a time. Ties at the same millisecond were treated as one game ending before the next began. The broader worker-lifetime upper bound includes setup and teardown.',
        'The measured stages and controls represented in these logs occurred in the declared order, with no worker-lifetime overlap between adjacent stages.',
        'Every audited slot matched the required executable, net, book and search budget. All logged options matched PC20, with the stated control override or exactly one edge change among the 40 start values. Every engine process reported NNUE v3 active with checksum 30ab43b4ba5db5f3.',
        f'First worker began {min(x.start for x in slots).isoformat()}; final worker ended {max(x.end for x in slots).isoformat()}.',
    ]
    if args.deadline:
        boundary=t(args.deadline)
        bits.append(f'Operational stop-playing cutoff {boundary.isoformat()}; {sum(x[7] for x in cells)} completed game receipts strictly before it.')
    grouped={}
    for _,stage,arm,_,beg,end,gs,gc,_ in cells:
        key='E (played edge sets)' if re.fullmatch('E[0-9]+',stage) else stage
        grouped.setdefault(key,[]).append((t(beg),t(end),gc))
    for phase in ('K19-1','K19-2','C19','D1','E (played edge sets)','D2'):
        if phase in grouped:
            items=grouped[phase]
            span=(max(x[1] for x in items)-min(x[0] for x in items)).total_seconds()
            bits.append(f'{phase}: {sum(x[2] for x in items)} completed games across workers, {span:.3f} seconds from first worker start to last worker end, including time between arms or edge sets.')
    if ongoing: bits.append('Excluded still-running slots from this interim receipt: '+', '.join(ongoing)+'.')
    (args.out/'concurrency.txt').write_text('\n'.join(bits)+'\n')
    print('\n'.join(bits[:4]))

if __name__=='__main__': main()
