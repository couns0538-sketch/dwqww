"""Read identity from independently opened procfs records for Forge engines launched by this match."""
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import sys
import time
ROOT=Path('/workspace/work')
MATCH=ROOT/'j22match/results'
LOG=Path(__file__).resolve().parent/'live-pid-identity.tsv'
PINS={str(ROOT/'j7base/build/forge'):'9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671',str(ROOT/'j16kf/build/forge'):'c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb'}
end=datetime.fromisoformat('2026-11-19T02:40:00+00:00').timestamp()
if 0 in os.sched_getaffinity(0):os.sched_setaffinity(0,{0})
known=set()
with LOG.open('w',buffering=1) as out:
    print('sample_utc\tarm\tpid\tppid\tproc_starttime_ticks\tcpu_affinity\texe\texe_sha256\tpurpose',file=out)
    while time.time()<end:
        for path in MATCH.glob('*/run.log'):
            if path.parent.name in known:continue
            with path.open('rb') as run:txt=run.read(10000).decode(errors='replace')
            pidmatch=re.search(r'^(?:P1_Both|engine|engine_process|engine_pid)\s+(?:pid\s+)?(\d+)\b',txt,re.M)
            if not pidmatch:continue
            pid=int(pidmatch[1]); proc=Path('/proc')/str(pid)
            try:
                exe=(proc/'cmdline').read_bytes().split(b'\0')[0].decode()
                if exe not in PINS:continue
                try:
                    assert os.readlink(proc/'exe')==exe
                    sha=hashlib.sha256((proc/'exe').read_bytes()).hexdigest()
                    method='direct proc exe + cmdline + pid start ticks'
                except PermissionError:
                    sha=hashlib.sha256(Path(exe).read_bytes()).hexdigest()
                    method='live cmdline + pid start ticks + named executable digest; proc exe verified by its parent worker'
                assert PINS[exe]==sha
                stat=(proc/'stat').read_text().rsplit(')',1)[1].split() # first token is field 3 (state)
                ppid,start_time=stat[1],stat[19]
                aff=','.join(map(str,sorted(os.sched_getaffinity(pid))))
                assert (proc/'cmdline').read_bytes().split(b'\0')[0].decode()==exe
            except (ProcessLookupError,FileNotFoundError):continue
            stamp=datetime.now(timezone.utc).isoformat(timespec='milliseconds')
            print(stamp,path.parent.name,pid,ppid,start_time,aff,exe,sha,method,sep='\t',file=out)
            known.add(path.parent.name)
        if sum(arm.startswith('L0') for arm in known)==2:break
        time.sleep(.15 if len(known)<3 else 1)
