#!/usr/bin/env python3
"""Read-only Linux resource samples for this full-data experiment.
IDEA_SOURCE: bounded resource/evidence requirements; /proc process accounting.
"""
import argparse,json,time
from datetime import datetime,timezone
from pathlib import Path

def process(pid):
    base=Path('/proc')/str(pid)
    fields=(base/'stat').read_text().rsplit(')',1)[1].split()
    status=(base/'status').read_text().splitlines()
    rss=next((int(x.split()[1]) for x in status if x.startswith('VmRSS:')),0)
    return {'pid':pid,'ppid':int(fields[1]),'start_ticks':fields[19],'state':fields[0],
            'rss_kib':rss,'cpu_ticks':int(fields[11])+int(fields[12])}

p=argparse.ArgumentParser()
p.add_argument('--pid',required=True,type=int)
p.add_argument('--run',required=True,type=Path)
p.add_argument('--out',required=True,type=Path)
a=p.parse_args();identity=process(a.pid)['start_ticks']
with a.out.open('x') as out:
    while True:
        sample={'utc':datetime.now(timezone.utc).isoformat()}
        try:
            parent=process(a.pid)
            if parent['start_ticks']!=identity or parent['state']=='Z':break
            sample['processes']=[parent]
            for child in Path('/proc').iterdir():
                if not child.name.isdigit():continue
                try:
                    info=process(int(child.name))
                    if info['ppid']==a.pid:sample['processes'].append(info)
                except (OSError,ValueError,IndexError):pass
            sample['rss_sum_kib']=sum(x['rss_kib'] for x in sample['processes'])
            try:
                progress=json.loads((a.run/'progress.json').read_text())
                sample['progress']={k:progress.get(k) for k in ('status','input_rows','kept','wall_seconds_so_far')}
            except (OSError,ValueError):sample['progress']='temporarily unreadable'
        except OSError as error:
            out.write(json.dumps({'ended_utc':sample['utc'],'reason':repr(error)})+'\n');out.flush();break
        out.write(json.dumps(sample,sort_keys=True)+'\n');out.flush()
        time.sleep(30)
