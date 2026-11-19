"""Archive Job 20 label streams, keeping a common prefix of completed games."""
import argparse
import csv
import ctypes
import fcntl
import hashlib
import io
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile

MAX_SINGLE = 20_000_000
MAX_PART = 15_000_000
MANIFEST_COLUMNS = ('kind', 'file', 'bytes', 'rows', 'sha256')
ARMS = {'K20-1': (600001,600020), 'K20-2': (600001,600020), 'C20': (600001,600020)}
for stage,lo,hi in [('P1',600101,603100),('P2',610001,610500),('P3',620001,620100)]:
    for build in ('r15d','kF'):
        ARMS[f'{stage}-{build}']=(lo,hi)
MOVE = re.compile(rb'[a-h][1-8][a-h][1-8][nbrq]?\Z')
RAW_METRICS = re.compile(rb'(?<!\S)(?:time|nps)[ \t]+[0-9]+(?=\s|$)')
SCORE_FIELD = re.compile(rb'(?<!\S)score[ \t]+(?:cp|mate)[ \t]+-?[0-9]+(?=\s|$)')
MATE_FIELD = re.compile(rb'(?<!\S)score[ \t]+mate[ \t]+-?[0-9]+(?=\s|$)')


def fail(message):
    raise ValueError(message)


def game_receipts(source, target, final):
    """Read only rows with a line terminator, then index by cumulative stream bytes."""
    complete=[]
    with (source/'games.tsv').open('rb') as stream:
        header=stream.readline()
        if not header.endswith(b'\n'):
            fail('games.tsv header has not been flushed')
        names=header.decode('utf-8').rstrip('\r\n').split('\t')
        for field in ('book_line','plies','record_bytes','end_utc','na','score','mate'):
            if field not in names: fail(f'{source}: missing {field} field')
        raw=bytearray(header)
        while target is None or len(complete)<target:
            line=stream.readline()
            if not line: break
            if not line.endswith(b'\n'):
                if final: fail(f'{source}: incomplete final games.tsv line')
                break
            row=dict(zip(names,line.decode('utf-8').rstrip('\r\n').split('\t'),strict=True))
            if not row['end_utc']: fail(f'{source}: missing completed-game timestamp')
            raw.extend(line)
            complete.append(row)
    if target is not None and len(complete)!=target:
        fail(f'{source.name}: {len(complete)} completed, requested {target}')
    first,last=ARMS[source.name]
    if len(complete)>last-first+1: fail(f'{source.name}: more games than scheduled')
    offset=0
    for gid,row in enumerate(complete,first):
        if int(row['book_line'])!=gid or int(row['record_bytes'])<offset:
            fail(f'{source.name}: out-of-order game or nonmonotone offset at {gid}')
        offset=int(row['record_bytes'])
    return bytes(raw),complete,offset


def count_labels(source, receipts, expected_size):
    """Read each signed-off game at its byte boundaries, verifying row order and fields."""
    total=na=mate=score=0
    with source.open('rb') as stream:
        for row in receipts:
            gid=int(row['book_line'])
            n=int(row['plies'])
            counts=[0,0,0]
            if not 0<=n<=292: fail(f'{source}: invalid engine ply count {n} for {gid}')
            for ply in range(8,8+n):
                line=stream.readline()
                try:
                    game,idx,move,label=line[:-1].split(b' ',3)
                except ValueError:
                    fail(f'{source}: malformed record for {gid} ply {ply}')
                if not line.endswith(b'\n') or game!=str(gid).encode() or idx!=str(ply).encode() or not MOVE.fullmatch(move):
                    fail(f'{source}: record IDs, move, or newline for game {gid} ply {ply}')
                if b'\r' in label or b'\0' in label: fail(f'{source}: noncanonical line ending or NUL')
                if label==b'NA':
                    counts[0]+=1
                else:
                    if not label.startswith(b'info depth ') or RAW_METRICS.search(label): fail(f'{source}: unexpected normalized info fields')
                    if SCORE_FIELD.search(label): counts[1]+=1
                    if MATE_FIELD.search(label): counts[2]+=1
            if stream.tell()!=int(row['record_bytes']): fail(f'{source}: game {gid} disagrees with receipt offset')
            expected=[int(row[k]) for k in ('na','score','mate')]
            if counts!=expected: fail(f'{source}: observed NA/score/mate {counts} for {gid}, expected {expected}')
            total+=n; na+=counts[0]; score+=counts[1]; mate+=counts[2]
        if stream.tell()!=expected_size: fail(f'{source}: prefix accounting mismatch')
    return total,na,score,mate


def next_line_parts(source, size, split):
    """Yield whole-line chunks. The greedy boundary is invariant under appending."""
    limit = MAX_PART if split else MAX_SINGLE
    with source.open('rb') as stream:
        pending=bytearray(); consumed=0; rows=0
        while consumed<size:
            line=stream.readline(min(size-consumed,limit)+1)
            if not line or len(line)>limit or len(line)>size-consumed or not line.endswith(b'\n') or b'\0' in line:
                fail(f'{source}: invalid or overlong UTF-8 record at byte {consumed}')
            if pending and len(pending)+len(line)>limit:
                yield pending,rows
                pending=bytearray(); rows=0
            pending.extend(line)
            rows+=1; consumed+=len(line)
        if pending or size==0: yield pending,rows


def archive_stream(source,size,base,tmp,old,split):
    entries=[]
    full=hashlib.sha256()
    total_rows=0
    for part,(payload,rows) in enumerate(next_line_parts(source,size,split),1):
        # Validate UTF-8 from beginning to end, independently of the data hashes.
        payload.decode('utf-8')
        full.update(payload)
        digest=hashlib.sha256(payload).hexdigest()
        name=f'{base}.part{part:04d}.txt' if split else f'{base}.txt'
        same=old/name if old else None
        target=tmp/name
        if same and same.is_file() and same.stat().st_size==len(payload):
            with same.open('rb') as fp:
                if hashlib.file_digest(fp,'sha256').hexdigest()==digest:
                    os.link(same,target)
        if not target.exists(): target.write_bytes(payload)
        total_rows+=rows
        entries.append(('part',name,len(payload),rows,digest))
    if not split and len(entries)!=1: fail('single file unexpectedly required splitting')
    whole=('whole',f'{base}.txt',size,total_rows,full.hexdigest())
    with (tmp/f'{base}-manifest.tsv').open('w',newline='',encoding='utf-8') as fp:
        wr=csv.writer(fp,delimiter='\t',lineterminator='\n')
        wr.writerow(MANIFEST_COLUMNS); wr.writerows(entries); wr.writerow(whole)
    # Check the materialized archive against source bytes directly, in manifest order.
    with source.open('rb') as original, (tmp/f'{base}-manifest.tsv').open() as fp:
        manifest=list(csv.DictReader(fp,delimiter='\t'))
        complete=hashlib.sha256(); checked_size=checked_rows=0
        for meta in manifest[:-1]:
            part_digest=hashlib.sha256(); n=r=0
            if meta['kind']!='part': fail(f'{base}: manifest part out of order')
            with (tmp/meta['file']).open('rb') as part:
                while data:=part.read(262144):
                    if original.read(len(data))!=data: fail(f'{source}: direct byte comparison failed')
                    n+=len(data); r+=data.count(b'\n'); part_digest.update(data); complete.update(data)
            if (n,r,part_digest.hexdigest())!=(int(meta['bytes']),int(meta['rows']),meta['sha256']):
                fail(f'{base}: archived part failed SHA/size/row check')
            checked_size+=n; checked_rows+=r
        finalrow=manifest[-1]
        observed=('whole',f'{base}.txt',checked_size,checked_rows,complete.hexdigest())
        if observed!=whole or (finalrow['kind'],finalrow['file'],int(finalrow['bytes']),int(finalrow['rows']),finalrow['sha256'])!=whole:
            fail(f'{base}: whole-stream manifest disagrees with source')
    return entries,whole


def publish(tmp,target):
    if not target.exists():
        os.replace(tmp,target)
        return
    # Exchange whole directories so parallel readers cannot see an unfinished set.
    libc=ctypes.CDLL(None,use_errno=True)
    if libc.renameat2(-100,os.fsencode(tmp),-100,os.fsencode(target),2)!=0:
        errno=ctypes.get_errno(); raise OSError(errno,os.strerror(errno),str(target))
    shutil.rmtree(tmp)


def check_previous(arm,target,final,requested):
    path=target/'archive.txt'
    if not path.exists(): return
    data=path.read_text()
    prior=int(re.search(r'^games (\d+)$',data,re.M)[1])
    was_final='\nmode final\n' in data
    if not final and (requested<prior or was_final):
        fail(f'{arm}: refusing to replace {prior} archived games with an earlier checkpoint; select a distinct --out path')


def reconcile_checkpoint(args,arm,tmp,count,size,digest):
    if not arm.startswith(('P1-','P2-','P3-')): return
    stage,build=arm.rsplit('-',1)
    ready=args.results.parent/'checkpoints'/stage/f'{count:04d}'/'ready.txt'
    if not ready.is_file(): return
    data=ready.read_text()
    if f'common_completed_games {count}\n' not in data:
        fail(f'{ready}: game count differs')
    row=next((s.split() for s in data.splitlines() if s.startswith(build+' ')),None)
    if not row: fail(f'{ready}: no entry for {build}')
    fields=dict(zip(row[1::2],row[2::2],strict=True))
    if fields['prefix_sha256']!=digest or int(fields['end_byte_offset'])!=size:
        fail(f'{ready}: runner and independent prefix disagree')
    (tmp/'runner-checkpoint.txt').write_bytes(ready.read_bytes())


def raw_paths(rawdir,arm):
    return rawdir/f'{arm}.txt'


def prepare(arm,args,tmp,target):
    src=args.results/arm
    final=args.final
    receipt,records,end=game_receipts(src,args.games,final)
    if final:
        log=(src/'run.log').read_text()
        m=re.search(r'^status (COMPLETE|INCOMPLETE)\s*\Z',log,re.M)
        if not m: fail(f'{arm}: final status marker has not been flushed')
        status=m[1]
        first,last=ARMS[arm]
        if status=='COMPLETE' and len(records)!=last-first+1: fail(f'{arm}: final incomplete game count for COMPLETE arm')
        if (src/'records.txt').stat().st_size!=end: fail(f'{arm}: final stream extends beyond games.tsv receipt')
    else:
        status='PREFIX'
    if target.exists(): check_previous(arm,target,final,args.games)
    total,na,score,mate=count_labels(src/'records.txt',records,end)
    parts,logical=archive_stream(src/'records.txt',end,'records',tmp,target,end>MAX_SINGLE or (not final and arm.startswith('P1-')))
    if logical[3]!=total: fail(f'{arm}: total row mismatch')
    reconcile_checkpoint(args,arm,tmp,len(records),end,logical[4])
    (tmp/'games.tsv').write_bytes(receipt)
    lines=[f'arm {arm}',f'mode {"final" if final else "checkpoint"}',f'status {status}',f'games {len(records)}',
           f'first_game {records[0]["book_line"] if records else "none"}',f'last_game {records[-1]["book_line"] if records else "none"}',
           f'records {total}',f'na {na}',f'score {score}',f'score_mate {mate}',f'record_bytes {end}',f'record_sha256 {logical[4]}',
           f'canonical_chunks {len(parts)}','verification canonical concatenation byte-compared with source through last completed games.tsv offset; per-game row order, record count, NA/score/mate counters checked.']
    if final:
        for key,value in [('games',len(records)),('records',total),('na_records',na),('score_records',score),('mate_records',mate)]:
            field=re.search(r'^'+key+r' (\d+)$',log,re.M)
            if not field or int(field[1])!=value: fail(f'{arm}: {key} differs from run.log')
        found=re.search(r'^records_sha256 (\w+)$',log,re.M)
        if not found or found[1]!=logical[4]: fail(f'{arm}: final source SHA does not match run.log')
        raw=raw_paths(args.raw_labels,arm)
        rawsize=raw.stat().st_size
        rawparts,rawlogical=archive_stream(raw,rawsize,'raw-labels',tmp,target,rawsize>MAX_SINGLE)
        rawhash=re.search(r'^raw_labels_sha256 (\w+)$',log,re.M)
        if not rawhash or rawhash[1]!=rawlogical[4]: fail(f'{arm}: verbatim SHA disagrees with run.log')
        if rawlogical[3]!=total: fail(f'{arm}: raw information-line count differs from canonical')
        verify_raw(raw,src/'records.txt',total)
        lines.extend([f'raw_rows {rawlogical[3]}',f'raw_bytes {rawsize}',f'raw_sha256 {rawlogical[4]}',f'raw_chunks {len(rawparts)}',
                      'verification raw-label concatenation byte-compared with original; each raw label independently matched to its normalized search record.'])
    (tmp/'archive.txt').write_text('\n'.join(lines)+'\n')
    return (arm,len(records),records[-1]['book_line'] if records else None,total,end,logical[4])


def verify_raw(raw_path,canonical_path,rows):
    # Use token spans from the original byte string and drop only each matched
    # (key, integer) pair and its one preceding separator. Other spacing is literal.
    removed = re.compile(rb'(?<!\S)(?:nps|time)[ \t]+[0-9]+(?=[ \t]|$)')
    with raw_path.open('rb') as raw, canonical_path.open('rb') as canonical:
        for i in range(rows):
            original=raw.readline()
            normal=canonical.readline()
            ids1=original[:-1].split(b' ',3)
            ids2=normal[:-1].split(b' ',3)
            if len(ids1)!=4 or len(ids2)!=4 or ids1[:3]!=ids2[:3] or not original.endswith(b'\n'):
                fail(f'{raw_path}: verbatim row {i+1} lacks its canonical identity')
            label=ids1[3]
            if label!=b'NA' and not label.startswith(b'info depth '):
                fail(f'{raw_path}: unknown label at row {i+1}')
            pieces=[]; last=0
            for field in removed.finditer(label):
                if field.start()==0 or label[field.start()-1:field.start()] not in (b' ',b'\t'):
                    fail(f'{raw_path}: invalid timing token at row {i+1}')
                pieces.append(label[last:field.start()-1])
                last=field.end()
            reconstructed=b''.join(pieces)+label[last:]
            if reconstructed!=ids2[3]: fail(f'{raw_path}: removing timing fields differs at row {i+1}')
        if raw.read(1) or canonical.read(1): fail(f'{raw_path}: unread tail in a final label stream')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--games',type=int,help='export this many completed games of each supplied arm')
    mode.add_argument('--final',action='store_true',help='export each finished arm including its full verbatim raw-label stream')
    p.add_argument('--results',type=Path,default=Path('/workspace/work/j20match/results'))
    p.add_argument('--raw-labels',type=Path,help='directory of <arm>.txt verbatim label streams (default adjacent to results)')
    p.add_argument('--out',type=Path,default=Path('/workspace/work/j20archive/export'))
    p.add_argument('arms',nargs='+',choices=sorted(ARMS))
    args=p.parse_args()
    if args.games is not None and args.games<0: p.error('--games must be nonnegative')
    if len(set(args.arms))!=len(args.arms): p.error('duplicate arm')
    if args.games is not None and len({ARMS[arm] for arm in args.arms})!=1: p.error('checkpoint arms need matching scheduled ranges')
    args.raw_labels=args.raw_labels or args.results.parent/'raw-labels'
    args.out.mkdir(parents=True,exist_ok=True)
    staged=[]
    with (args.out.parent/f'.{args.out.name}.lock').open('a') as lk:
        fcntl.flock(lk,fcntl.LOCK_EX)
        with tempfile.TemporaryDirectory(prefix='.archiving-',dir=args.out.parent) as work:
            for arm in args.arms:
                tmp=Path(work)/arm; tmp.mkdir()
                info=prepare(arm,args,tmp,args.out/arm)
                staged.append((arm,tmp,info))
            for arm,tmp,info in staged:
                publish(tmp,args.out/arm)
                print(f'{info[0]} games={info[1]} last={info[2]} rows={info[3]} bytes={info[4]} sha256={info[5]}')

if __name__=='__main__':
    try: main()
    except (OSError,ValueError,KeyError) as e: sys.exit(str(e))
