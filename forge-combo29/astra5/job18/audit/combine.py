"""Read the independent stage evidence and summarize only completed comparisons."""
from datetime import datetime
from pathlib import Path
from audit import ARMS,HERE,WORK,rows,table

ends=None
lines=[];stats=[];whole=0
for stage,(left,right,lower,upper) in ARMS.items():
    path=HERE/stage
    if not (path/'arms.tsv').is_file():break
    records=rows(path/'arms.tsv')
    assert [r['arm'] for r in records]==[left,right]
    summary=(path/'summary.txt').read_text()
    reading=summary.splitlines()[0].split(' ',1)[1]
    changed=len(rows(path/'differences.tsv'))
    unique=(right,) if stage=='C18' else (left,right)
    times={}
    for arm in unique:
        run=(WORK/'j18match/results'/arm/'run.log').read_text().splitlines()
        start=next(s.split()[1] for s in run if s.startswith('start_utc '))
        end=next(s.split()[1] for s in reversed(run) if s.startswith('end_utc '))
        times[arm]=(datetime.fromisoformat(start),datetime.fromisoformat(end))
    start=min(s[0] for s in times.values());stop=max(s[1] for s in times.values())
    if ends:assert start>=ends,(stage,start,ends)
    ends=stop
    lines.append((stage,reading,changed,start.isoformat(),stop.isoformat(),' '.join(unique)))
    for r in records:
        stats.append((stage,reading,changed,*[r[c] for c in ['arm','status','games','records','na_records','nodes','bytes','sha256']]))
headers=['stage','reading','differing_games','arm','status','games','records','na_records','nodes','bytes','sha256']
table(HERE/'stage-summary.tsv',headers,stats)
table(HERE/'stage-order.tsv',('stage','reading','differing_games','first_arm_started','last_arm_ended','new_arm_processes'),lines)
tested=[s for s in lines if s[0][0] in ('R','F')]
if len(tested)==10 and all(s[1]=='IDENTICAL' for s in tested):
    a=[r for r in stats if r[0][0] in ('R','F') and r[3].endswith('-r15d')]
    games=sum(int(r[5]) for r in a);nr=sum(int(r[6]) for r in a);na=sum(int(r[7]) for r in a);nodes=sum(int(r[8]) for r in a)
    output=f'KEEPS. All ten measured R/F stages completed and matched byte for byte. Per build these comprise {games} whole games, {nr} recorded searches, {na} NA records, and {nodes} nodes from final numeric info values. Stage order verified against each new arm’s start/end receipt.\n'
    output+='R uses the engine’s final soft-node count. F uses the node count in its last hard-limit UCI iteration report. The total above adds the recorded columns.\n'
    for kind in ['R','F']:
        arms=[r for r in a if r[0].startswith(kind)]
        output+=f'{kind} per build: {sum(int(r[5]) for r in arms)} games, {sum(int(r[6]) for r in arms)} records, {sum(int(r[7]) for r in arms)} NA, {sum(int(r[8]) for r in arms)} recorded nodes.\n'
    (HERE/'reading.txt').write_text(output)
print(len(lines),len(tested))
