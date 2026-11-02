"""Recover pinned Job3 Git inputs into immutable D:/a10 copies; no data jobs."""
import argparse, hashlib, json, os, pathlib, subprocess, sys, time
ROOT=pathlib.Path('D:/a10'); WT=ROOT/'wt'
REV='d8982bc04d3a828ba440bad250d02fb72526f1a2'
sys.path.insert(0,str(ROOT/'pydeps'))
import psutil
sys.path.insert(0, 'D:/a10/wt/astra_r10/job1')  # CR crfix 0e91e02e: shared lane guard (crfix_abcbb9c9 lane_guard.py 596ecbe6)
import lane_guard
sys.path.insert(0,str(WT/'skills/gate-handover-pack/scripts'))
import seal_evidence as safety


def main():
    p=argparse.ArgumentParser();p.add_argument('--threads',type=int,choices=[1],required=True);p.parse_args()
    lane_guard.check_lane()  # before any output/fetch
    out=WT/'astra_r10/job3/recovery01';source=ROOT/'job3/source'
    if out.exists() or source.exists():raise ValueError('preserve existing recovery/source')
    me=psutil.Process()
    if me.nice()!=psutil.IDLE_PRIORITY_CLASS or not set(me.cpu_affinity())<={2,3}:raise RuntimeError('safe launcher required')
    safety.disk_budget(1_000_000_000)
    if safety.workspace_bytes()+1_000_000_000>safety.CAP:raise RuntimeError('workspace budget insufficient')
    out.mkdir(parents=True)
    for attempt in range(30):
        load=psutil.cpu_percent(interval=3,percpu=True)
        with (out/'load.jsonl').open('a') as stream:stream.write(json.dumps({'attempt':attempt,'cpu2_3':load[2:4],'total_mean':sum(load)/len(load)})+'\n')
        if max(load[2:4])<50 and sum(load)/len(load)<98:
            lane_guard.check_lane();break
        time.sleep(10)
    else:raise RuntimeError('saturated host; fetch not started')
    git=['git','-c','pack.threads=1','-c','gc.auto=0','-c','maintenance.auto=false','-C',str(WT)]
    cmd=git+['fetch','--no-tags','--no-recurse-submodules','--depth=1','origin',REV]
    result=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=300)
    (out/'fetch.stdout').write_bytes(result.stdout);(out/'fetch.stderr').write_bytes(result.stderr)
    (out/'fetch-receipt.json').write_text(json.dumps({'argv':cmd,'exit_code':result.returncode,'scope':'own clone only'},indent=2))
    if result.returncode:raise RuntimeError('fetch failed; evidence retained')
    actual=subprocess.check_output(git+['rev-parse',REV+'^{commit}'],timeout=120).decode().strip()
    if actual!=REV:raise RuntimeError('revision mismatch')
    listing=subprocess.check_output(git+['ls-tree','-rl','--full-tree',REV],timeout=300).decode()
    (out/'tree.txt').write_text(listing)
    records=[];total=0;selected=[]
    for line in listing.splitlines():
        info,name=line.split('\t',1);mode,kind,oid,size=info.split()
        if name.startswith('astra_r8/datafilter/') or name.startswith('tools/') or name in ('LICENSE','LICENSE.md','COPYING','AGENTS.md'):
            rel=pathlib.PurePosixPath(name)
            if rel.is_absolute() or '..' in rel.parts or mode not in ('100644','100755') or kind!='blob':raise ValueError('unsafe Git tree entry')
            size=int(size)
            if size>100_000_000 or total+size>500_000_000:raise ValueError('snapshot exceeds reservation')
            total+=size;selected.append((name,oid,size))
    if not any(name.startswith('astra_r8/datafilter/') for name,_,_ in selected):raise ValueError('datafilter tree absent')
    source.mkdir(parents=True)
    for name,oid,size in selected:
        blob=subprocess.check_output(git+['cat-file','blob',oid],timeout=300)
        if len(blob)!=size:raise ValueError('blob size changed')
        target=source/pathlib.PurePosixPath(name);target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as stream:stream.write(blob)
        records.append({'revision':REV,'path':name,'git_blob':oid,'bytes':size,'sha256':hashlib.sha256(blob).hexdigest(),'copy':str(target)})
    report={'status':'RECOVERED','classification':'UNPROVEN','revision':REV,'source':str(source),'bytes':total,'files':records}
    with (out/'INPUTS.json').open('x') as stream:json.dump(report,stream,indent=2)
    with (source/'SOURCE_MANIFEST.json').open('x') as stream:json.dump(report,stream,indent=2)
    print(json.dumps({'status':'RECOVERED','source':str(source),'files':len(records),'bytes':total,'revision':REV}))


if __name__=='__main__':main()
