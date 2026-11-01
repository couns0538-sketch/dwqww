"""Predeclared advisory native timing: 4 A/A + 10 ABBA blocks, d20."""
import argparse,datetime,hashlib,json,pathlib,statistics,sys,time
from validate_uci import Engine
import psutil

DEADLINE=datetime.datetime.fromisoformat('2026-11-01T19:57:00-08:00').timestamp()
def summary(values):
    q=statistics.quantiles(values,n=4,method='inclusive')
    return {'median':statistics.median(values),'min':min(values),'max':max(values),'iqr':q[2]-q[0]}
def busy_fraction(before,after):
    # Windows system time already includes interrupt/DPC time.
    fields=['user','system','idle']
    total=sum(getattr(after,k)-getattr(before,k) for k in fields)
    idle=after.idle-before.idle
    return 0.0 if total<=0 else 100*(1-idle/total)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('lock'); ap.add_argument('candidate'); ap.add_argument('out')
    args=ap.parse_args(); out=pathlib.Path(args.out); out.mkdir(parents=True,exist_ok=False)
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS); psutil.Process().cpu_affinity([3])
    hashes={a:hashlib.sha256(pathlib.Path(e).read_bytes()).hexdigest() for a,e in [('A',args.lock),('B',args.candidate)]}
    rows=[]; pairs=[]
    for phase,blocks in [('AA',4),('ABBA',10)]:
        for block in range(blocks):
            while True:
                load=psutil.cpu_percent(interval=3,percpu=True)
                if load[2]<30 and load[3]<30: break
                if time.time()>DEADLINE: raise RuntimeError('no quiet core before deadline')
                print('WAIT quiet core',load[2:4],flush=True); time.sleep(15)
            group=[]
            for slot,arm in enumerate('ABBA'):
                if time.time()>DEADLINE: raise RuntimeError('deadline')
                exe=args.lock if phase=='AA' or arm=='A' else args.candidate
                label=f'{phase}_{block:02}_{slot}_{arm}'
                e=None
                try:
                    e=Engine(exe,out/(label+'.log'),on=phase=='ABBA' and arm=='B')
                    e.send('bench 16'); warm=e.wait(r'bench depth 16 nodes ')[-1]
                    if 'nodes 3024920 ' not in warm: raise RuntimeError(warm)
                    process=psutil.Process(e.p.pid); cpu_before=process.cpu_times()
                    system_before=psutil.cpu_times(percpu=True)
                    start=time.perf_counter(); e.send('bench 20'); line=e.wait(r'bench depth 20 nodes ')[-1]
                    elapsed=time.perf_counter()-start
                    cpu_after=process.cpu_times(); system_after=psutil.cpu_times(percpu=True)
                    cpu_ratio=(cpu_after.user+cpu_after.system-cpu_before.user-cpu_before.system)/elapsed
                    sibling_busy=busy_fraction(system_before[3],system_after[3])
                    import re
                    m=re.search(r'nodes (\d+) time (\d+) nps (\d+)',line)
                    if not m or int(m[1])!=12389307: raise RuntimeError(line)
                    row={'phase':phase,'block':block,'slot':slot,'arm':arm,'exe':exe,
                         'sha256':hashes['A' if phase=='AA' else arm],'nodes':int(m[1]),'ms':int(m[2]),
                         'nps':int(m[3]),'wall_s':elapsed,'pre_core_load':load[2:4],
                         'engine_cpu_wall_ratio':cpu_ratio,'sibling_busy_percent':sibling_busy,
                         'contaminated':cpu_ratio<.95 or sibling_busy>=30,
                         'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
                    e.close(); e=None
                finally:
                    if e: e.abort()
                group.append(row); rows.append(row)
                with (out/'runs.jsonl').open('a') as f: f.write(json.dumps(row)+'\n')
                print(label,'nps',row['nps'],flush=True)
            for x,y in [(group[0],group[1]),(group[3],group[2])]:
                pairs.append({'phase':phase,'block':block,'A_nps':x['nps'],'B_nps':y['nps'],
                              'gain_percent':100*(y['nps']/x['nps']-1)})
    result={'hashes':hashes,'rows':rows,'pairs':pairs,'classification':'ADVISORY','Elo':'UNPROVEN'}
    for phase in ['AA','ABBA']:
        result[phase]={arm:summary([r['nps'] for r in rows if r['phase']==phase and r['arm']==arm]) for arm in 'AB'}
        result[phase]['paired_gain_percent']=summary([p['gain_percent'] for p in pairs if p['phase']==phase])
    control=result['AA']['paired_gain_percent']; gain=result['ABBA']['paired_gain_percent']['median']
    result['aa_stable']=abs(control['median'])<=.75 and control['iqr']<=3
    result['contaminated_runs']=sum(r['contaminated'] for r in rows)
    result['speed_gate_pass']=result['aa_stable'] and gain>=1 and result['contaminated_runs']==0
    (out/'summary.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in ['rows','pairs']},indent=2))
if __name__=='__main__': main()
