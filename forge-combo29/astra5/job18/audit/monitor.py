"""Read durable slot results, emit the earliest sorted disagreement, then do a final full replay."""
from pathlib import Path
import csv
import subprocess
import sys
import time
from audit import ARMS,HERE,WORK,RECORD,load_book,OPENING_PREFIX
results=WORK/'j18match/results'
bookpath=WORK/'j8gate/UHO_Lichess_4852_v1.epd'

def available(arm):
    index={}
    for slot in (1,2):
        root=arm/f'slot{slot}'
        receipt=root/'games.tsv'
        if not receipt.exists():
            continue
        with receipt.open() as f:
            complete=[line for line in f if line.endswith('\n')]
        start=0
        for row in csv.DictReader(complete,delimiter='\t'):
            end=int(row['record_bytes'])
            index[int(row['book_line'])]=(root/'records.txt',start,end)
            start=end
    return index
def read_game(entry):
    path,start,end=entry
    with path.open('rb') as f:
        f.seek(start)
        data=f.read(end-start)
    assert len(data)==end-start,(entry,len(data))
    return data
def inspect_first(a,b,first,last,known,book,stage):
    ai,bi=available(a),available(b)
    for gid in range(first,last+1):
        if gid in known:continue
        if gid not in ai or gid not in bi:break
        aa,bb=read_game(ai[gid]),read_game(bi[gid])
        known.add(gid)
        if aa==bb:continue
        al,bl=aa.splitlines(keepends=True),bb.splitlines(keepends=True)
        ply=next(j for j in range(max(len(al),len(bl))) if al[j:j+1]!=bl[j:j+1])
        text=[f'{stage}: first differing completed game, book line {gid}, ply {ply+(len(OPENING_PREFIX[gid]) if gid in OPENING_PREFIX else 1)}.','Opening FEN '+book[gid]]
        if gid in OPENING_PREFIX:text.append('Eight initial UCI moves '+' '.join(OPENING_PREFIX[gid]))
        for d,v in ((a,al),(b,bl)):
            text.append(d.name+' record '+(v[ply].decode('ascii').strip() if ply<len(v) else '(missing)'))
            text.append(d.name+' preceding UCI moves '+(' '.join(RECORD.fullmatch(r)[3].decode('ascii') for r in v[:ply]) or '(none)'))
        path=HERE/stage/'live-first-difference.txt'
        path.parent.mkdir(exist_ok=True)
        path.write_text('\n'.join(text)+'\n')
        return True
    return False
def ended(path):
    if not path.exists():return False
    return path.read_text().rstrip().split('\n')[-1] in ('status COMPLETE','status INCOMPLETE')
def main():
    for stage,(left,right,lo,hi) in ARMS.items():
        a,b=results/left,results/right
        known=set();found=False
        book=load_book(bookpath,lo,hi)
        while True:
            if not found:found=inspect_first(a,b,lo,hi,known,book,stage)
            if ended(a/'run.log') and ended(b/'run.log') and (a/'records.txt').is_file() and (b/'records.txt').is_file():
                break
            time.sleep(2)
        with (HERE/'audit-monitor.log').open('a') as log:
            subprocess.run([sys.executable,'-B',str(HERE/'audit.py'),stage],stdout=log,stderr=log,check=True)
if __name__=='__main__':main()
