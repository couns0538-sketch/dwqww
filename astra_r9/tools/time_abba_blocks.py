"""Protocol v2: retain and replace entire interfered blocks, never individual runs."""
import argparse,datetime,hashlib,json,pathlib,re,sys,time
from validate_uci import Engine
from time_abba import DEADLINE,busy_fraction,summary
import psutil

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('lock'); ap.add_argument('candidate'); ap.add_argument('out')
    args=ap.parse_args(); out=pathlib.Path(args.out); out.mkdir(parents=True,exist_ok=False)
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS); psutil.Process().cpu_affinity([3])
    hashes={a:hashlib.sha256(pathlib.Path(e).read_bytes()).hexdigest() for a,e in [('A',args.lock),('B',args.candidate)]}
    result={'protocol':'v2 whole-block replacement','hashes':hashes,'classification':'ADVISORY','Elo':'UNPROVEN',
            'blocks':[],'rows':[],'speed_gate_pass':False,'status':'RUNNING'}
    try:
        for phase,required in [('AA',4),('ABBA',10)]:
            accepted=0
            for attempt in range(80):
                if accepted==required:break
                while True:
                    if time.time()>DEADLINE:raise RuntimeError('deadline awaiting quiet core')
                    load=psutil.cpu_percent(interval=3,percpu=True)
                    if load[2]<20 and load[3]<20:break
                    print('WAIT',phase,load[2:4],flush=True); time.sleep(15)
                group=[]
                for slot,arm in enumerate('ABBA'):
                    if time.time()>DEADLINE:raise RuntimeError('deadline')
                    exe=args.lock if phase=='AA' or arm=='A' else args.candidate
                    label=f'{phase}_{attempt:02}_{slot}_{arm}'; e=None
                    try:
                        e=Engine(exe,out/(label+'.log'),on=phase=='ABBA' and arm=='B')
                        e.send('bench 20'); warm=e.wait(r'bench depth 20 nodes ')[-1]
                        if 'nodes 12389307 ' not in warm:raise RuntimeError(warm)
                        process=psutil.Process(e.p.pid); cb=process.cpu_times(); sb=psutil.cpu_times(percpu=True)
                        start=time.perf_counter(); e.send('bench 20'); line=e.wait(r'bench depth 20 nodes ')[-1]
                        elapsed=time.perf_counter()-start; ca=process.cpu_times(); sa=psutil.cpu_times(percpu=True)
                        ratio=(ca.user+ca.system-cb.user-cb.system)/elapsed
                        sibling=busy_fraction(sb[3],sa[3]); match=re.search(r'nodes (\d+) time (\d+) nps (\d+)',line)
                        if not match or int(match[1])!=12389307:raise RuntimeError(line)
                        row={'phase':phase,'attempt':attempt,'slot':slot,'arm':arm,'exe':exe,
                             'sha256':hashes['A' if phase=='AA' else arm],'nodes':int(match[1]),'ms':int(match[2]),
                             'nps':int(match[3]),'wall_s':elapsed,'pre_core_load':load[2:4],
                             'engine_cpu_wall_ratio':ratio,'sibling_busy_percent':sibling,
                             'contaminated':ratio<.95 or sibling>=30,
                             'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
                        e.close();e=None
                    finally:
                        if e:e.abort()
                    group.append(row);result['rows'].append(row)
                    with (out/'runs.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
                    print(label,'nps',row['nps'],'quiet',not row['contaminated'],flush=True)
                # Eligibility depends only on predeclared telemetry, never NPS/gain.
                eligible=not any(r['contaminated'] for r in group)
                block={'phase':phase,'attempt':attempt,'eligible':eligible,
                       'pair_gain_percent':[100*(group[b]['nps']/group[a]['nps']-1) for a,b in [(0,1),(3,2)]]}
                result['blocks'].append(block)
                if eligible:accepted+=1
                with (out/'blocks.jsonl').open('a') as f:f.write(json.dumps(block)+'\n')
                print(phase,'eligible blocks',accepted,'/',required,'attempts',attempt+1,flush=True)
            if accepted!=required:raise RuntimeError('insufficient quiet blocks')
            selected={b['attempt'] for b in result['blocks'] if b['phase']==phase and b['eligible']}
            selected_rows=[r for r in result['rows'] if r['phase']==phase and r['attempt'] in selected]
            pairs=[g for b in result['blocks'] if b['phase']==phase and b['eligible'] for g in b['pair_gain_percent']]
            result[phase]={a:summary([r['nps'] for r in selected_rows if r['arm']==a]) for a in 'AB'}
            result[phase]['paired_gain_percent']=summary(pairs)
            all_pairs=[g for b in result['blocks'] if b['phase']==phase for g in b['pair_gain_percent']]
            result[phase]['all_attempts_gain_percent']=summary(all_pairs)
            if phase=='AA':
                control=result['AA']['paired_gain_percent']
                result['aa_stable']=abs(control['median'])<=.75 and control['iqr']<=3
                if not result['aa_stable']:
                    result['status']='CONTROL_FAIL';return
        result['speed_gate_pass']=result['ABBA']['paired_gain_percent']['median']>=1
        result['status']='PASS' if result['speed_gate_pass'] else 'BELOW_1_PERCENT'
    except BaseException as exc:
        result['status']='INCOMPLETE';result['error']=repr(exc);raise
    finally:
        (out/'summary.json').write_text(json.dumps(result,indent=2))
        print(json.dumps({k:v for k,v in result.items() if k not in ['rows','blocks']},indent=2),flush=True)
if __name__=='__main__':main()
