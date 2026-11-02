"""Read approved remote revisions into isolated R10 copies; UNPROVEN."""
import argparse, hashlib, json, os, pathlib, subprocess, sys, time
sys.path.insert(0, 'D:/a10/pydeps')
import psutil

ROOT = pathlib.Path('D:/a10')
WT = ROOT/'wt'
REVS = {'p4':'df79fb6e33e0ec45e4bdf40cbbdfadb3b6fc27a6',
        'p7':'cd9cb992fd6a6b05766d1117c1de441a430586a9',
        'status':'43af044a14a375b653f3d0bc633d9f476325ca81'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--threads',type=int,choices=[1],required=True)
    p.add_argument('--out',type=pathlib.Path,required=True);args=p.parse_args()
    out=args.out
    if not out.is_absolute() or not out.is_relative_to(WT/'astra_r10/job2') or out.exists():
        raise ValueError('new Job2 output required')
    out.mkdir(parents=True)
    me=psutil.Process()
    if me.nice()!=psutil.IDLE_PRIORITY_CLASS or not set(me.cpu_affinity())<={2,3}:
        raise RuntimeError('safe launcher required')
    os.environ['TEMP']=os.environ['TMP']=str(ROOT/'tmp')
    for attempt in range(40):
        load=psutil.cpu_percent(interval=3,percpu=True)
        with (out/'load.jsonl').open('a') as f:f.write(json.dumps({'attempt':attempt,'cpu2_3':load[2:4],'mean':sum(load)/len(load)})+'\n')
        if max(load[2:4])<50 and sum(load)/len(load)<98:break
        time.sleep(10)
    else:raise RuntimeError('saturated host; no Git fetch started')
    records=[];total=0
    for label,rev in REVS.items():
        command=['git','-C',str(WT),'fetch','--no-tags','--depth=1','origin',rev]
        result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=300)
        (out/(label+'-fetch.stdout')).write_bytes(result.stdout)
        (out/(label+'-fetch.stderr')).write_bytes(result.stderr)
        if result.returncode:raise RuntimeError(label+' fetch failed; retain outputs')
        listing=subprocess.check_output(['git','-C',str(WT),'ls-tree','-r','--name-only',rev]).decode().splitlines()
        (out/(label+'-tree.txt')).write_text('\n'.join(listing)+'\n')
        selected=[name for name in listing if name.startswith('opus_r13/'+label+'/') or
                  (label=='status' and 'status' in name.lower() and name.lower().endswith('.md')) or
                  name in ('LICENSE','LICENSE.md','COPYING')]
        target=out/label;target.mkdir()
        for name in selected:
            rel=pathlib.PurePosixPath(name)
            if rel.is_absolute() or '..' in rel.parts:raise ValueError('unsafe git path')
            size=int(subprocess.check_output(['git','-C',str(WT),'cat-file','-s',rev+':'+name]))
            if size>100_000_000 or total+size>500_000_000:raise ValueError('snapshot reservation exceeded')
            blob=subprocess.check_output(['git','-C',str(WT),'show',rev+':'+name])
            path=target.joinpath(*rel.parts);path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('xb') as f:f.write(blob)
            total+=len(blob);records.append({'revision':rev,'path':name,'copy':str(path),'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest()})
        if not selected:raise ValueError(label+' snapshot empty')
    (out/'INPUTS.json').write_text(json.dumps({'classification':'UNPROVEN','revisions':REVS,'files':records,'bytes':total},indent=2))
    print(json.dumps({'status':'RECOVERED','classification':'UNPROVEN','files':len(records),'bytes':total}))

if __name__=='__main__':main()
