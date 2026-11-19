"""Sample the two existing L1 processes only while the coordinator writes a common checkpoint."""
from ctypes import CDLL, get_errno
import csv
from datetime import datetime,timezone
import os
from pathlib import Path
import re
import select
import struct
import time
w=Path('/workspace/work'); result=w/'j22match/results'
directory=w/'j22match/checkpoints/L1'
out=Path(__file__).resolve().parent/'stationary-proc.tsv'
if 0 in os.sched_getaffinity(0):os.sched_setaffinity(0,{0})
lib=CDLL(None,use_errno=True)
fd=lib.inotify_init1(os.O_CLOEXEC)
assert fd>=0
wd=lib.inotify_add_watch(fd,os.fsencode(directory),0x100)
assert wd>=0,(wd,get_errno())
clock=lambda:datetime.now(timezone.utc).isoformat(timespec='microseconds')
end=datetime.fromisoformat('2026-11-19T02:29:00+00:00').timestamp()
ident={}
for name in ('r15d','kF'):
    log=(result/f'L1-{name}'/'run.log').read_text()
    ident[name]=(int(re.search(r'^P1_Both pid (\d+)',log,re.M)[1]),re.search(r'^engine_start_ticks (\d+)',log,re.M)[1])
with out.open('x',buffering=1) as f:
    print('ordinal\tgame\tbuild\tengine_pid\tstart_ticks\tindependent_kB\tofficial_kB\tread_start_utc\tread_end_utc',file=f)
    while time.time()<end:
        got,_,_=select.select([fd],[],[],min(25,max(0,end-time.time())))
        if not got:continue
        data=os.read(fd,8192)
        while data:
            _,mask,_,size=struct.unpack_from('iIII',data)
            raw=data[16:16+size].rstrip(b'\0')
            data=data[16+size:]
            if not raw.isdigit():continue
            ordinal=int(raw)
            if ordinal%1000 and (ordinal!=600):continue
            complete=directory/raw.decode()/'ready.txt'
            if complete.exists():continue
            before=clock()
            observations={}
            for name,(pid,ticks) in ident.items():
                proc=Path('/proc')/str(pid)
                try:
                    assert (proc/'stat').read_text().rsplit(')',1)[1].split()[19]==ticks
                    status=(proc/'status').read_text()
                except FileNotFoundError:break
                observations[name]=int(re.search(r'^VmRSS:\s+(\d+) kB$',status,re.M)[1])
            after=clock()
            if complete.exists() or len(observations)!=2:continue
            # next PLAY cannot be sent until ready.txt exists. Both engine reads are
            # therefore strictly between the same games, including the final checkpoint.
            for name,(pid,ticks) in ident.items():
                with (result/f'L1-{name}'/'rss-all.tsv').open() as source:
                    row=next(r for r in csv.DictReader(source,delimiter='\t') if int(r['completed'])==ordinal)
                assert row['pid']==str(pid) and row['start_ticks']==ticks
                print(ordinal,row['game'],name,pid,ticks,observations[name],row['vmrss_kb'],before,after,sep='\t',file=f)
            if ordinal==5000:raise SystemExit(0)
