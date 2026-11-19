from datetime import datetime
from pathlib import Path
import time
from audit import ARMS,HERE,WORK,MANIFEST,rows,table
RESULT=WORK/'j19match/results'
def overview():
    edges=rows(MANIFEST)
    statuses={f"E{int(r['edge']):02}":r['status'] for r in edges}
    ordered=list(ARMS);ordered.insert(-1,'E')
    summary=[];timings=[];intervals=[];last=None;measured=[]
    for stage in ordered:
        if statuses.get(stage)=='start':
            for arm in ARMS[stage][:2]:
                assert not (RESULT/arm/'records.txt').exists(),arm
                summary.append((stage,'start','',arm,'start','','','','','',''))
            continue
        dest=HERE/stage
        if not (dest/'verified.txt').exists():continue
        reading=(dest/'summary.txt').read_text().splitlines()[0].split(' ',1)[1]
        diffs=len(rows(dest/'differences.tsv'))
        arms=rows(dest/'arms.tsv')
        for r in arms:summary.append((stage,reading,diffs,*[r[c] for c in ('arm','status','games','records','na_records','nodes','bytes','sha256')]))
        if stage in ('D1','E','D2'):measured.append((stage,reading,arms))
        if stage=='E':continue
        times=[]
        for name in (r['arm'] for r in arms if not (stage=='C19' and r['arm']=='K19-1')):
            path=RESULT/name
            meta=(path/'run.log').read_text().splitlines()
            lo=datetime.fromisoformat(next(l.split()[1] for l in meta if l.startswith('start_utc ')))
            hi=datetime.fromisoformat(next(l.split()[1] for l in reversed(meta) if l.startswith('end_utc ')))
            times.append((lo,hi))
            for slot in path.glob('slot[0-9]'):
                pergame={int(r['book_line']):datetime.fromisoformat(r['end_utc']) for r in rows(slot/'games.tsv')}
                for line in (slot/'run.log').read_text().splitlines():
                    if line.startswith('game_start '):
                        words=line.split();gid=int(words[1]);start=datetime.fromisoformat(words[2])
                        end=pergame.get(gid,hi)
                        assert start<=end,(name,gid,start,end)
                        intervals.extend([(start,1),(end,-1)])
        lo=min(r[0] for r in times);hi=max(r[1] for r in times)
        if last is not None:assert lo>=last,(stage,lo,last)
        last=hi
        timings.append((stage,lo.isoformat(),hi.isoformat()))
    a=HERE/'stage-summary.inprogress'
    table(a,('stage','reading','differing_games','arm','status','games','records','na_records','nodes','bytes','sha256'),summary)
    a.replace(HERE/'stage-summary.tsv')
    a=HERE/'stage-order.inprogress';table(a,('stage','first_arm_start','last_arm_end'),timings);a.replace(HERE/'stage-order.tsv')
    n=peak=0
    for _,delta in sorted(intervals):
        n+=delta
        peak=max(n,peak)
    assert n==0 and peak<=2,(peak,n)
    if len(measured)==3:
        result='KEEPS' if all(r=='IDENTICAL' for s,r,a in measured) else 'DIFFERS'
        chosen=[a[0] for _,_,a in measured]
        games,records,na,nodes=[sum(int(row[key]) for row in chosen) for key in ('games','records','na_records','nodes')]
        screened=sum(1 for r in summary if r[3].endswith('-r15d') and r[0] in statuses and r[1]=='IDENTICAL')
        report=[f'{result}. D1, the per-edge and whole E comparisons, and D2 are listed in stage-summary.tsv.',f'{screened} edge settings produced byte-identical files, {sum(x=="start" for x in statuses.values())} are listed as start.',f'D1 + E + D2 per r15d build: {games} games, {records} records, {na} NA, {nodes} summed numeric node values. E is counted once.',f'All observed phase and individual edge stage arm time ranges are ordered. Peak simultaneous games from slot game-start/end timestamps across all complete stages: {peak} (maximum allowed 2).']
        (HERE/'reading.txt').write_text('\n'.join(report)+'\n')
    return len(timings),len(summary)

if __name__=='__main__':
    from aggregate import verify
    change=None
    while True:
        if (RESULT/'E-cmp.txt').exists() and not (HERE/'E'/'verified.txt').exists():
            played=[f"E{int(r['edge']):02}" for r in rows(MANIFEST) if r['status']=='play' and (RESULT/f"E{int(r['edge']):02}-r15d"/'run.log').is_file()]
            if all((HERE/e/'verified.txt').exists() for e in played):verify()
        available=(len(list(HERE.glob('*/verified.txt'))),bool(MANIFEST.exists()))
        if available!=change and available[1]:
            print(overview(),flush=True);change=available
        if (HERE/'reading.txt').is_file():break
        time.sleep(1)
