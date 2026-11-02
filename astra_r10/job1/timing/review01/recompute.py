"""Independent read-only R10 timing audit. Does not import timing helpers/run engines."""
import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

ap=argparse.ArgumentParser();ap.add_argument('--threads',type=int,choices=[1],required=True);a=ap.parse_args()
HERE=Path(__file__).parent
ROOT=HERE.parent
RUN=ROOT/'run01'
REPO=Path('D:/a10/wt')
PREREG='bd9f81a77416a68c1b59a7ba87acd4e383c10c03'
LOCK='fd3a51903e73dc1fa20263f1dcc7a4eec506592e9f25e50b8f8739ca36873072'
EXPECTED_PROTOCOL='c83ccb17d428069be129eaf4f1b253dbf299bb6d77ad0353a5667fa82ccb3245'
NODES=12389307
checks=[]
def check(ok,name):
    checks.append({'name':name,'status':'PASS' if ok else 'FAIL'})
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def load(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def rows(path):return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines()]
def git(*args):
    p=subprocess.run(['git','-c','pack.threads=1',*args],cwd=REPO,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
    if p.returncode:raise RuntimeError(p.stderr.decode('utf-8','replace'))
    return p.stdout
def percentile(values,p):
    v=sorted(values);i=(len(v)-1)*p;j=int(math.floor(i));k=int(math.ceil(i))
    return v[j]+(v[k]-v[j])*(i-j)
def stats(values):
    if not values:return None
    q1=percentile(values,.25);q3=percentile(values,.75)
    return {'count':len(values),'median':percentile(values,.5),'q1':q1,'q3':q3,'iqr':q3-q1,'min':min(values),'max':max(values)}
def near(a,b):return math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-11)

protocol=load(ROOT/'protocol.json');summary=load(RUN/'summary.json')
arms=rows(RUN/'runs.jsonl');blocks=rows(RUN/'blocks.jsonl');waits=rows(RUN/'waits.jsonl')
protocol_hash=sha(ROOT/'protocol.json')
check(protocol_hash==EXPECTED_PROTOCOL==sha(RUN/'PROTOCOL.json')==summary['protocol_sha256'],'registered protocol SHA current/copied/summary')
blob=git('show',PREREG+':astra_r10/job1/timing/protocol.json')
check(hashlib.sha256(blob).hexdigest()==protocol_hash,'prereg commit protocol blob bytes equal consumed protocol')
commit_time=git('show','-s','--format=%cI',PREREG).decode().strip()
check(dt.datetime.fromisoformat(commit_time)<dt.datetime.fromisoformat(summary['start_utc']),'prereg commit time precedes experiment start')
check(git('merge-base','--is-ancestor',PREREG,'HEAD')==b'','prereg commit ancestor of local branch')
remote=git('ls-remote','origin','refs/heads/astra-r10-3jobs').decode().strip()
remote_sha=remote.split()[0]
check(git('merge-base','--is-ancestor',PREREG,remote_sha)==b'','published remote branch contains prereg commit')
for ref in protocol['inputs']:
    check(sha(ref['path'])==ref['sha256'].lower(),'input '+ref['role']+' SHA')
for name,ref in protocol['prerequisites'].items():
    check(sha(ref['path'])==ref['sha256'].lower() and ref['status']=='PASS' and ref['evidence_scope']=='native','prerequisite '+name+' hash/status')

by_key={};transcripts=set();reasons=Counter();last_end=None
for arm in arms:
    key=(arm['phase'],arm['attempt'],arm['slot'])
    check(key not in by_key,'unique arm '+str(key));by_key[key]=arm
    stem=f"{arm['phase']}-{arm['attempt']:02d}-{arm['slot']}-{arm['arm']}.log"
    transcripts.add(stem);text=(RUN/stem).read_text(encoding='utf-8')
    check(sha(RUN/stem)==arm['transcript_sha256'],stem+' transcript hash')
    observed=re.findall(r'^info string bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)$',text,re.M)
    expected=[(20,arm['warmup']['nodes'],arm['warmup']['engine_ms'],arm['warmup']['engine_nps']),
              (20,arm['nodes'],arm['engine_ms'],arm['engine_nps'])]
    check([tuple(map(int,x)) for x in observed]==expected and all(x[1]==NODES for x in expected),stem+' warmup/measured transcript pins')
    commands=[x[2:] for x in text.splitlines() if x.startswith('> ')]
    check(commands==['uci','setoption name Threads value 1','setoption name Hash value 16','setoption name OwnBook value false','isready','bench 20','bench 20','quit'],stem+' identical AA command lifecycle')
    check('option name Threads type spin default 1 ' in text and '\nuciok\n' in text and '\nreadyok\n' in text,stem+' handshake/thread default')
    check(arm['sha256']==arm['sha256_after_exit']==LOCK and arm['phase']=='AA',stem+' same lock binary binding')
    check(arm['protocol_sha256']==protocol_hash and arm['network_sha256']==protocol['network_sha256'],stem+' protocol/network binding')
    check(arm['status']=='PASS' and arm['exit_code']==0,stem+' completion/exit')
    check(arm['actual_affinity']==arm['after_affinity']==[2] and arm['actual_priority']==arm['after_priority']==64 and arm['requested_search_threads']==1,stem+' scheduling')
    check(arm['options']=={'Threads':1,'Hash':16,'OwnBook':False,'NNUEWideOutput':False},stem+' same AA options')
    wall=(arm['monotonic_end_ns']-arm['monotonic_start_ns'])/1e9
    check(wall>0 and near(wall,arm['wall_seconds']) and near(NODES/wall,arm['wall_nps']),stem+' independent elapsed/rate')
    expected_reasons=[]
    if arm['engine_cpu_wall_ratio']<protocol['cpu_wall_min_inclusive']:expected_reasons.append('engine_cpu_wall_below_0.95')
    if arm['sibling_busy_percent']>=protocol['sibling_busy_max_exclusive']:expected_reasons.append('sibling_busy_at_least_30_percent')
    check(expected_reasons==arm['contamination_reasons'],stem+' eligibility from retained telemetry')
    reasons.update(expected_reasons)
    if last_end is not None:check(last_end<=dt.datetime.fromisoformat(arm['utc_start']),stem+' sequential arm lifecycle')
    last_end=dt.datetime.fromisoformat(arm['utc_end'])
check(transcripts=={p.name for p in RUN.glob('*.log')},'no orphan/unaccounted transcripts')

all_gains=[];eligible_gains=[];eligible_attempts=[];recomputed=[]
for index,block in enumerate(blocks):
    key=(block['phase'],block['attempt'])
    matched=[by_key[(key[0],key[1],slot)] for slot in range(4)]
    check(block['rows']==matched and [r['arm'] for r in matched]==list('ABBA'),str(key)+' block/arm equality and order')
    check(block['status']=='COMPLETE' and block['attempt']==index and block['phase']=='AA',str(key)+' complete contiguous AA block')
    durations=[(r['monotonic_end_ns']-r['monotonic_start_ns'])/1e9 for r in matched]
    # Matched nodes cancel; derive from durations, not stored NPS or production arithmetic helper.
    ratio=math.sqrt((durations[0]*durations[3])/(durations[1]*durations[2]))
    gain=100*(ratio-1)
    eligible=all(r['engine_cpu_wall_ratio']>=.95 and r['sibling_busy_percent']<30 for r in matched)
    check(near(ratio,block['ratio']) and near(gain,block['gain_percent']) and eligible==block['eligible'],str(key)+' independently recomputed ratio/gain/eligibility')
    preceding=[w for w in waits if (w['phase'],w['attempt'])==key and dt.datetime.fromisoformat(w['utc'])<=dt.datetime.fromisoformat(matched[0]['utc_start'])]
    check(bool(preceding) and preceding[-1]['load']==block['pre_core_busy_percent'] and all(x<20 for x in preceding[-1]['load']),str(key)+' pre-block quietness')
    check(all(r['pre_core_busy_percent']==block['pre_core_busy_percent'] for r in matched),str(key)+' arm pre-block binding')
    all_gains.append(gain)
    if eligible:eligible_gains.append(gain);eligible_attempts.append(index)
    recomputed.append({'attempt':index,'eligible':eligible,'gain_percent':gain,'ratio':ratio})
check(summary['blocks']==blocks,'summary duplicates exact original block records')
computed={'eligible':stats(eligible_gains),'all_complete':stats(all_gains)}
for category,key in [('eligible','eligible_gain_percent'),('all_complete','all_complete_gain_percent')]:
    claimed=summary['phase_summaries']['AA'][key]
    check(all(near(value,claimed[name]) for name,value in computed[category].items()),category+' summary recomputation')
cal=computed['eligible']
gates={'ten_blocks':len(eligible_gains)==10,'median':abs(cal['median'])<=.5,'iqr':cal['iqr']<=1,'min':cal['min']>=-2,'max':cal['max']<=2}
check(not all(gates.values()) and summary['status']=='CALIBRATION_FAIL' and summary['calibration']['passed'] is False and summary['advisory_threshold_met'] is False,'calibration fail correctly stops comparison')
check(len(arms)==156 and len(blocks)==39 and len(eligible_gains)==10 and not any(x['phase']=='ABBA' for x in arms),'39 AA attempts/10 eligible/zero candidate arms')
check(summary['phase_summaries']['ABBA']=={'attempted_blocks':0,'complete_blocks':0,'eligible_blocks':0,'eligible_gain_percent':None,'all_complete_gain_percent':None},'zero comparison explicitly retained')
check(summary['controller_priority']==64 and summary['controller_affinity']==[3],'controller scheduling')
elapsed=(dt.datetime.fromisoformat(summary['finish_utc'])-dt.datetime.fromisoformat(summary['start_utc'])).total_seconds()
check(0<elapsed<3600,'experiment completed within preregistered deadline')
launch=ROOT/'run-launch02';receipt=load(launch/'result.json');manifest=load(launch/'manifest.json')
check(sha(launch/'manifest.json')==receipt['manifest_sha256'].lower(),'launcher receipt copied-manifest hash')
check(manifest==load(ROOT/'run-launch02-manifest.json'),'launcher consumed declared manifest')
check(receipt['native_exit_code']==1 and not receipt['capture_errors'] and not receipt['disk_floor_breached'],'launcher exit1 is expected calibration failure without capture/storage failure')
check(receipt['priority']=='Idle' and receipt['affinity']==12 and receipt['worker_threads']==1,'launcher scheduling contract')
check((launch/'stderr.log').stat().st_size==0,'launcher stderr empty')
check(dt.datetime.fromisoformat(summary['finish_utc'])<=dt.datetime.fromisoformat(receipt['finished_utc']),'launcher receipt follows final summary')

result={'review_scope':'Independent timing recomputation and retained evidence review; no engine execution. UNPROVEN.',
        'status':'PASS' if all(x['status']=='PASS' for x in checks) else 'FINDINGS',
        'protocol_sha256':protocol_hash,'prereg_commit':PREREG,'prereg_commit_time':commit_time,
        'remote_observed':remote,'start_utc':summary['start_utc'],'finish_utc':summary['finish_utc'],
        'statistics_percent':computed,'calibration_gates':gates,'eligible_attempts':eligible_attempts,
        'contamination_reason_counts':dict(reasons),'counts':{'arms':len(arms),'blocks':len(blocks),'eligible_blocks':len(eligible_gains),'rejected_blocks':len(blocks)-len(eligible_gains),'candidate_arms':0},
        'checks':checks,'block_recomputations':recomputed,
        'limitations':['Raw process CPU-time and per-CPU before/after counters are not retained; eligibility is independently recomputed from recorded derived telemetry, not raw counter deltas.',
                       'Current remote ancestry confirms publication of the prereg commit, and commit time precedes execution. No separate immutable push-time receipt was found; publication-before-start relies additionally on the main agent publication log/history.',
                       'Loaded-host rejection and A/A calibration failure preclude any candidate speed inference; zero candidate ABBA blocks were run.']}
with (HERE/'REVIEW.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
md='# Independent R10 timing review — UNPROVEN\n\n'+result['status']+': original records and statistics '+('agree.' if result['status']=='PASS' else 'have discrepancies.')+'\n\n'
md+='| Population | Blocks | Median % | Q1 % | Q3 % | IQR pp | Min % | Max % |\n|---|---:|---:|---:|---:|---:|---:|---:|\n'
for name,s in computed.items():md+=f"| {name} | {s['count']} | {s['median']:.9f} | {s['q1']:.9f} | {s['q3']:.9f} | {s['iqr']:.9f} | {s['min']:.9f} | {s['max']:.9f} |\n"
md+='\nThe preregistered IQR gate fails; the other calibration gates pass. No candidate ABBA was run. '+str(sum(c['status']=='PASS' for c in checks))+' checks PASS of '+str(len(checks))+'. All 156 transcript hashes, 312 warmup/timed node pins, block/arm identities and telemetry-based eligibility were checked.\n\n'
md+='Protocol SHA256 `'+protocol_hash+'`; preregistration commit `'+PREREG+'`.\n\nLimitations:\n\n'+''.join('- '+x+'\n' for x in result['limitations'])
failed=[x['name'] for x in checks if x['status']=='FAIL']
if failed:md+='\nDefects:\n\n'+''.join('- '+x+'\n' for x in failed)
with (HERE/'REVIEW.md').open('x',encoding='utf-8') as f:f.write(md)
print(json.dumps({k:v for k,v in result.items() if k not in ('checks','block_recomputations')},indent=2))
if failed:raise SystemExit(1)
