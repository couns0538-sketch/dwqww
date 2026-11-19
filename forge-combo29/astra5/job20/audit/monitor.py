import csv
from pathlib import Path
import subprocess,sys,time
from audit import HERE,WORK,ARMS,decoded,first_description,rows,table
from itertools import zip_longest
def ready(p):
    if not p.exists():return False
    with p.open('rb') as f:
        f.seek(0,2);f.seek(max(0,f.tell()-256))
        return f.read().rstrip().splitlines()[-1:] in ([b'status COMPLETE'],[b'status INCOMPLETE'])
def receipts(path):
    if not path.exists():return []
    with path.open() as f:return list(csv.DictReader((l for l in f if l.endswith('\n')),delimiter='\t'))
def check_diff(stage,left,right,offsets,count):
    gamefiles=[receipts(p/'games.tsv') for p in (left,right)]
    common=min(map(len,gamefiles))
    if count>=common:return count,False
    with (left/'records.txt').open('rb') as af,(right/'records.txt').open('rb') as bf:
        for j,f in enumerate((af,bf)):f.seek(offsets[j])
        for i in range(count,common):
            ends=[int(g[i]['record_bytes']) for g in gamefiles]
            res=[f.read(ends[j]-offsets[j]) for j,f in enumerate((af,bf))]
            offsets[:]=ends
            if res[0]==res[1]:continue
            gid=int(gamefiles[0][i]['book_line']);assert gid==int(gamefiles[1][i]['book_line'])
            ll,rr=(r.splitlines(keepends=True) for r in res)
            idx=next(k for k,(x,y) in enumerate(zip_longest(ll,rr)) if x!=y)
            data=first_description(stage,left.name,right.name,gid,idx,ll,rr)
            dest=HERE/stage;dest.mkdir(exist_ok=True)
            (dest/'live-first-difference.txt').write_text('\n'.join(data)+'\n')
            return i+1,True
    return common,False
def index():
    rec=[];games=columns=na=mate=score=0;measured=0;diffs=0
    times=[];prev=None
    for s,(a,b,lo,hi) in ARMS.items():
        p=HERE/s
        if not (p/'verified.txt').is_file():break
        armrows=rows(p/'arms.tsv');d=len(rows(p/'differences.tsv'))
        word=(p/'summary.txt').read_text().splitlines()[0].split(' ',1)[1]
        for r in armrows:rec.append((s,word,d,*r.values()))
        src=[b] if s=='C20' else [a,b]
        ts=[]
        for n in src:
            l=(WORK/'j20match/results'/n/'run.log').read_text().splitlines()
            ts.append(tuple(next(x.split()[1] for x in l if x.startswith(v)) for v in ('start_utc','end_utc')))
        start=min(t[0] for t in ts);end=max(t[1] for t in ts)
        assert prev is None or prev<=start,(s,prev,start)
        prev=end;times.append((s,start,end))
        if s.startswith('P'):
            measured+=1;diffs+=d
            r=armrows[0];games+=int(r['games']);columns+=int(r['records']);na+=int(r['na_records']);mate+=int(r['mate_records']);score+=int(r['score_records'])
    if rec:
        p=HERE/'stage-summary.temp';table(p,('stage','reading','differing_games',*armrows[0].keys()),rec);p.replace(HERE/'stage-summary.tsv')
        p=HERE/'stage-order.temp';table(p,('stage','first_start','last_end'),times);p.replace(HERE/'stage-order.tsv')
    if measured==3:
        result='KEEPS' if diffs==0 and all(r[1]=='IDENTICAL' for r in rec if r[0].startswith('P')) else 'DIFFERS'
        (HERE/'reading.txt').write_text(f'{result}. {games} measured games per r15d build, {columns} recorded searches, {na} NA, {score} scored, {mate} score-mate records. {diffs} differing measured games.\n')
def main():
    data=WORK/'j20match/results'
    for stage,(a,b,lo,hi) in ARMS.items():
        if (HERE/stage/'verified.txt').is_file():index();continue
        left=data/a;right=data/b
        count=0;offsets=[0,0];found=False
        while True:
            if not found:count,found=check_diff(stage,left,right,offsets,count)
            if ready(left/'run.log') and ready(right/'run.log'):break
            time.sleep(2)
        with (HERE/'audit-monitor.log').open('a') as log:
            subprocess.run([sys.executable,'-B',str(HERE/'audit.py'),stage],stdout=log,stderr=log,check=True)
        index()
if __name__=='__main__':main()
