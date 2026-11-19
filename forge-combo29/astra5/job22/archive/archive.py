"""Archive Job 22 node-record streams, keeping a common prefix of completed games."""
import argparse
import csv
import ctypes
import fcntl
import hashlib
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile

MAX_SINGLE = 20_000_000
MAX_PART = 15_000_000
MANIFEST_COLUMNS = ('kind', 'file', 'bytes', 'rows', 'sha256')

ARMS = ('K22-1','K22-2','C22','L1-r15d','L1-kF','L0-r15d','L0-kF')
MOVE = re.compile(rb'[a-h][1-8][a-h][1-8][nbrq]?\Z')

def fail(message):
    raise ValueError(message)

def read_game_receipts(source, target):
    complete=[]
    with source.open('rb') as stream:
        header=stream.readline()
        if not header.endswith(b'\n'): fail(f'{source}: incomplete header')
        names=header.decode('utf-8').rstrip('\r\n').split('\t')
        required=('book_line','plies','record_bytes','end_utc','na','nodes','p1_pid','p2_pid')
        if not set(required)<=set(names): fail(f'{source}: missing game receipt columns')
        raw=bytearray(header)
        while target is None or len(complete)<target:
            line=stream.readline()
            if not line:break
            if not line.endswith(b'\n'):
                if target is None: fail(f'{source}: final receipt is partial')
                break
            row=dict(zip(names,line.decode('utf-8').rstrip('\r\n').split('\t'),strict=True))
            if not row['end_utc']: fail(f'{source}: incomplete game receipt')
            raw.extend(line)
            complete.append(row)
    if target is not None and len(complete)!=target:
        fail(f'{source}: {len(complete)} completed games; {target} requested')
    return bytes(raw),complete

def game_bounds(arm,results):
    if arm in ('K22-1','K22-2','C22'): return 700001,700010
    if arm.startswith('L1-'): return 700001,705000
    long_name=arm.replace('L0-','L1-')
    _,history=read_game_receipts(results/long_name/'games.tsv',None)
    if len(history)<10: fail(f'{arm}: fewer than 10 prior games in {long_name}')
    return int(history[-10]['book_line']),int(history[-1]['book_line'])

def count_nodes(source,receipts,first,last):
    total=na=nodes=end=0
    pid=None
    if len(receipts)>last-first+1: fail(f'{source}: too many game receipts')
    with source.open('rb') as fp:
        for gid,row in enumerate(receipts,first):
            if int(row['book_line'])!=gid: fail(f'{source}: unexpected game ID, wanted {gid}')
            if pid is None: pid=row['p1_pid']
            if row['p1_pid']!=pid or row['p2_pid']!=pid: fail(f'{source}: engine PID changed')
            n=int(row['plies'])
            if not 0<=n<=292: fail(f'{source}: unexpected searched ply count in {gid}')
            missing=node_sum=0
            for ply in range(8,8+n):
                record=fp.readline()
                fields=record[:-1].split(b' ')
                if len(fields)!=4 or not record.endswith(b'\n') or fields[0]!=str(gid).encode() or fields[1]!=str(ply).encode() or not MOVE.fullmatch(fields[2]):
                    fail(f'{source}: malformed or unordered record in game {gid} ply {ply}')
                if fields[3]==b'NA': missing+=1
                elif fields[3].isdigit(): node_sum+=int(fields[3])
                else: fail(f'{source}: invalid node count in game {gid} ply {ply}')
            end=fp.tell()
            if (int(row['na']),int(row['nodes']),int(row['record_bytes']))!=(missing,node_sum,end):
                fail(f'{source}: game {gid} NA, node sum or end offset differs')
            total+=n;na+=missing;nodes+=node_sum
    return total,na,nodes,end,pid

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



def archive_rss(src, dest, games, pid, final):
    header = b'completed\tgame\tpid\tstart_ticks\tvmrss_kb\tobserved_utc\n'
    with (src/'rss-all.tsv').open('rb') as all_in, (src/'rss-source.txt').open('rb') as raw_in, (dest/'rss-all.tsv').open('wb') as all_out, (dest/'rss-source.txt').open('wb') as raw_out:
        if all_in.readline()!=header: fail(f'{src}: unexpected RSS columns')
        all_out.write(header)
        selected = {}
        ticks = None
        for ordinal,game in enumerate(games,1):
            line = all_in.readline()
            raw = raw_in.readline()
            fields = line.decode('ascii').rstrip('\n').split('\t')
            if len(fields)!=6 or not line.endswith(b'\n'): fail(f'{src}: missing RSS receipt {ordinal}')
            count, gid, who, lifetime, kb, observed = fields
            m=re.fullmatch(rb'([0-9]+) ([0-9]+) ([0-9]+) (\S+) VmRSS:\s+([0-9]+) kB\n',raw)
            if not m or tuple(v.decode('ascii') for v in m.groups()) != (count,gid,who,observed,kb): fail(f'{src}: literal VmRSS differs for {ordinal}')
            if ticks is None: ticks = lifetime
            if (int(count),gid,who,lifetime)!=(ordinal,game['book_line'],pid,ticks) or int(kb)<=0 or observed>game['end_utc']: fail(f'{src}: invalid RSS identity or timestamp {ordinal}')
            all_out.write(line)
            raw_out.write(raw)
            if ordinal in (1,1000,2000,3000,4000) or ordinal==len(games) and final: selected[ordinal]=line
        if final and (all_in.read(1) or raw_in.read(1)): fail(f'{src}: extra final RSS receipts')
    with (src/'rss.tsv').open('rb') as milestones, (dest/'rss.tsv').open('wb') as clipped:
        if milestones.readline()!=header: fail(f'{src}: invalid RSS milestone header')
        clipped.write(header)
        for ordinal,expected in selected.items():
            if milestones.readline()!=expected: fail(f'{src}: milestone {ordinal} differs')
            clipped.write(expected)
        if final and milestones.read(1): fail(f'{src}: unexpected extra final RSS milestone')
    return ticks

def archive_raw(src, canonical, tmp, target, run_log, expected_rows):
    rows=0
    with src.open('rb') as raw, canonical.open('rb') as nodes:
        for line in raw:
            fields=line[:-1].split(b' ',3)
            if len(fields)!=4 or not line.endswith(b'\n'): fail(f'{src}: malformed line {rows+1}')
            label=fields[3]
            if label==b'NA': value=b'NA'
            else:
                m=re.search(rb'(?:^| )nodes ([0-9]+)\b',label)
                if not label.startswith(b'info ') or not m: fail(f'{src}: missing info nodes at {rows+1}')
                value=m[1]
            if b' '.join([*fields[:3],value])+b'\n'!=nodes.readline(): fail(f'{src}: raw-to-canonical projection differs on row {rows+1}')
            rows+=1
        if rows!=expected_rows or nodes.read(1): fail(f'{src}: raw and canonical row counts differ')
    size=src.stat().st_size
    parts,whole=archive_stream(src,size,'raw-last',tmp,target,size>MAX_SINGLE)
    mark=re.search(r'^raw_last_sha256 (\w{64})$',run_log,re.M)
    if not mark or (mark[1],rows)!=(whole[4],whole[3]): fail(f'{src}: final raw SHA or rows disagree')
    return parts,whole

def compare_barrier(arm, args, dst, count, whole, records):
    if not arm.startswith('L1-') or count==0: return
    folder=args.results.parent/'checkpoints'/'L1'/f'{count:04}'
    ready=folder/'ready.txt'
    if not ready.is_file(): return
    data=ready.read_text()
    if f'common_completed_games {count}\n' not in data: fail(f'{arm}: checkpoint count differs')
    build=arm.split('-',1)[1]
    line=re.search(rf'^{build} chunk_bytes (\d+) start_offset (\d+) end_offset (\d+) chunk_sha256 ([0-9a-f]{{64}}) prefix_sha256 ([0-9a-f]{{64}})$',data,re.M)
    if not line or (int(line[3]),line[5])!=(whole[2],whole[4]): fail(f'{arm}: barrier prefix disagrees')
    start,stop=int(line[2]),int(line[3])
    with records.open('rb') as src:
        src.seek(start)
        chunk=src.read(stop-start)
    if not (len(chunk)==stop-start==int(line[1]) and hashlib.sha256(chunk).hexdigest()==line[4] and chunk==(folder/f'{build}-records.txt').read_bytes()):
        fail(f'{arm}: runner barrier fragment differs')
    (dst/'runner-checkpoint.txt').write_text(data)

def prepare(arm,args,tmp,target):
    src=args.results/arm
    first,last=game_bounds(arm,args.results)
    receipt,games=read_game_receipts(src/'games.tsv',args.games)
    total,na,nodes,end,pid=count_nodes(src/'records.txt',games,first,last)
    status='PREFIX'
    if args.final:
        log=(src/'run.log').read_text()
        marker=re.search(r'^status (.+)$',log,re.M)
        if not marker: fail(f'{arm}: final status not written')
        status=marker[1]
        if status=='COMPLETE' and len(games)!=last-first+1: fail(f'{arm}: incomplete games for final COMPLETE status')
        if (src/'records.txt').stat().st_size!=end: fail(f'{arm}: bytes after final game end offset')
    check_previous(arm,target,args.final,args.games)
    parts,whole=archive_stream(src/'records.txt',end,'records',tmp,target,end>MAX_SINGLE)
    compare_barrier(arm,args,tmp,len(games),whole,src/'records.txt')
    if whole[3]!=total: fail(f'{arm}: archive row count disagrees')
    if args.final:
        logged=dict(re.findall(r'^(games|records|na_records|sum_nodes|records_sha256) (\S+)$',log,re.M))
        want={'games':str(len(games)),'records':str(total),'na_records':str(na),'sum_nodes':str(nodes),'records_sha256':whole[4]}
        if logged!=want: fail(f'{arm}: final run summary differs: {logged} versus {want}')
    ticks=archive_rss(src,tmp,games,pid,args.final)
    if args.final:
        if games and (f'engine_start_ticks {ticks}\n' not in log or f'P1_Both pid {pid} ' not in log): fail(f'{arm}: original log does not confirm RSS PID and start ticks')
        raw_parts,raw_whole=archive_raw(args.results.parent/'raw-last'/f'{arm}.txt',src/'records.txt',tmp,target,log,total)
    (tmp/'games.tsv').write_bytes(receipt)
    lines=[f'arm {arm}',f'mode {"final" if args.final else "checkpoint"}',f'status {status}',f'games {len(games)}',
           f'first_game {games[0]["book_line"] if games else "none"}',f'last_game {games[-1]["book_line"] if games else "none"}',
           f'records {total}',f'na {na}',f'sum_nodes {nodes}',f'record_bytes {end}',f'record_sha256 {whole[4]}',f'canonical_chunks {len(parts)}',
           f'engine_pid {pid or "none"}','verification Every recorded game matched its signed-off byte offset, searched ply count, absolute ply ordering, NA count and node sum. The complete manifest concatenation was byte-compared with the original stream.']
    lines.append(f'engine_start_ticks {ticks or "none"}')
    if args.final:
        lines.extend([f'raw_last_bytes {raw_whole[2]}',f'raw_last_sha256 {raw_whole[4]}',f'raw_last_parts {len(raw_parts)}','raw_projection all rows independently reconstructed canonical nodes from the literal last-info payload; NA preserved'])
    (tmp/'archive.txt').write_text('\n'.join(lines)+'\n')
    return arm,len(games),int(games[-1]['book_line']) if games else None,total,end,whole[4]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--games',type=int,help='export this many completed games of each supplied arm')
    mode.add_argument('--final',action='store_true',help='export each finished arm and reconcile its durable game receipts')
    p.add_argument('--results',type=Path,default=Path('/workspace/work/j22match/results'))
    p.add_argument('--out',type=Path,default=Path('/workspace/work/j22archive/export'))
    p.add_argument('arms',nargs='+',choices=sorted(ARMS))
    args=p.parse_args()
    if args.games is not None and args.games<0: p.error('--games must be nonnegative')
    if len(set(args.arms))!=len(args.arms): p.error('duplicate arm')
    if args.games is not None and len({a.split('-')[0] for a in args.arms})!=1: p.error('a common checkpoint needs arms from the same run')
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
