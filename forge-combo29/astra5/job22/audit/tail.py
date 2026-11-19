"""Cut the matching last ten records directly from each build's L1 output."""
import csv,hashlib,subprocess,time
from pathlib import Path
from itertools import zip_longest
from audit import Stream,waitfiles,RAW,HERE,rows,status,write,difference,decode

def audit_tail(build):
    stage=f'L0-{build}';base=RAW/stage
    waitfiles(stage)
    while not status(base/'run.log'):time.sleep(.2)
    l1=RAW/f'L1-{build}'
    receipts=rows(l1/'games.tsv');old=receipts[-10:]
    assert len(old)==10
    lo=int(old[0]['book_line']);hi=int(old[-1]['book_line']);assert hi-lo==9
    s=Stream(stage,lo)
    target=HERE/stage;target.mkdir(exist_ok=True)
    readback=target/'independent-from-L1.txt'
    saved=rows(HERE/'L1'/'arms.tsv')
    prev_arm=next(r for r in saved if r['arm']==f'L1-{build}')
    tailname=f'{build}-L1-tail'
    prev_game_rows=[r for r in rows(HERE/'L1'/'games.tsv') if r['arm']==f'L1-{build}' and int(r['game'])>=lo]
    assert len(prev_game_rows)==10 and prev_arm['last_game']==str(hi)
    start=(int(receipts[-11]['record_bytes']) if len(receipts)>10 else 0)
    bufhash=hashlib.sha256();gn=na=recn=nb=0
    gref=[];diffs=[];first_diff=[]
    with (l1/'records.txt').open('rb') as record,readback.open('wb') as cut:
        record.seek(start)
        for row,known in zip(old,prev_game_rows):
            gid=int(row['book_line']);end=int(row['record_bytes'])
            chunk=record.read(end-record.tell());assert len(chunk)==int(known['bytes'])
            assert hashlib.sha256(chunk).hexdigest()==known['sha256']
            cut.write(chunk);bufhash.update(chunk)
            correct=chunk.splitlines(keepends=True)
            fresh_id,fresh=s.take();assert gid==fresh_id
            if correct!=fresh:
                idx=next(i for i,(x,y) in enumerate(zip_longest(correct,fresh)) if x!=y)
                diffs.append((gid,decode((correct[idx:idx+1] or fresh[idx:idx+1])[0])[1],len(correct),len(fresh)))
                if not first_diff:first_diff=difference(stage,(tailname,stage),gid,correct,fresh,recn+1)
            recn+=len(correct);gn+=int(known['nodes']);na+=int(known['na_records']);nb+=len(chunk)
            gref.append((tailname,gid,len(correct),int(known['na_records']),int(known['nodes']),len(chunk),known['sha256'],known['result'],known['termination'],nb))
        assert record.read(1)==b''
    actual=s.finish()
    assert s.pid!=prev_arm['pid'] and s.ticks!=prev_arm['start_ticks'],(stage,s.pid,s.ticks,prev_arm)
    assert len(s.game_rows)==10 and s.game_rows[-1][1]==hi
    # The controller's tail cut is produced by its stage-level comparison, after the engine exits.
    external=base/'from-L1.txt'
    while not external.is_file():time.sleep(.2)
    assert subprocess.run(['cmp','-s',str(readback),str(external)]).returncode==0
    ret=subprocess.run(['cmp','-s',str(readback),str(base/'records.txt')]).returncode
    assert ret==int(bool(diffs))
    ref=(tailname,'L1_REFERENCE',10,lo,hi,recn,na,gn,nb,bufhash.hexdigest(),prev_arm['pid'],prev_arm['start_ticks'])
    hints=[f'Located exact tail within {l1.name}/records.txt (byte offset {start} to final EOF after {nb} bytes). Every tail game digest and complete receipt matches the preceding verified L1 run. Independent cut vs controller from-L1.txt cmp exit 0; independent cut vs fresh {stage}/records.txt cmp exit {ret}.',
           'Fresh L0 engine PID and process lifetime start_ticks differ from the L1 engine. Full raw last-info projection and seeded legal replay verified separately for all ten fresh games.']
    write(stage,'CARRIES' if ret else 'SAME',[],[ref,actual],gref+s.game_rows,s.rss,diffs,first_diff,hints)
if __name__=='__main__':
    import sys
    audit_tail(sys.argv[1])
