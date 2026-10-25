"""One preregistered Linux-only ABAB screen; not native Zen5 qualification."""
from pathlib import Path
import os,resource,subprocess,time,datetime,json,hashlib,re,statistics
h=Path('/workspace/forge-sol-20261025');run=Path('/workspace/forge-sol-20261025-pgo/forge_sol_pgo_linux_proof_20261025');out=h/'forge_sol_pgo_linux_abab_20261025';out.mkdir(exist_ok=False)
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def limited():
 os.sched_setaffinity(0,{0,1,2,3});os.nice(19);resource.setrlimit(resource.RLIMIT_AS,(3*1024**3,3*1024**3))
a=run/'bin/forge_sol_pgo_baseline_20261025.exe';b=run/'bin/forge_sol_pgo_final_20261025.exe';hashes={str(p):sha(p) for p in [a,b]}
for label,p in [('check-baseline',a),('check-use',b)]:assert json.loads((run/'receipts'/f'{label}.PASS.json').read_text())['binary_sha256']==sha(p)
assert json.loads((h/'forge_sol_pgo_linux_extra_checks_20261025/forge_sol_pgo_linux_extra_results_20261025.json').read_text())['status']=='PASS'
assert (run/'receipts/validate.PASS.json').exists()
os.sched_setaffinity(0,{0,1,2,3});os.nice(19)
start=time.monotonic();deadline=start+1200
cpuinfo=Path('/proc/cpuinfo').read_text();model=next(x.split(':',1)[1].strip() for x in cpuinfo.splitlines() if x.startswith('model name'))
protocol={'started_utc':utc(),'scope':'Native Linux GCC14.2 on shared Intel host, NOT Windows/GCC15.2/Zen5 or Elo evidence','cpu':model,'affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'per_process_address_space_limit_bytes':3*1024**3,'binaries':hashes,'depth':20,'nodes':11901452,'Threads':1,'Hash':16,'OwnBook':False,'order':'8 complete ABAB blocks=32 processes=16 adjacent B/A ratios','primary':'median of all16 adjacent B/A NPS ratios; >=1.03 passes descriptive Linux3percent screen; below drops Linux candidacy','supplementary':'8 geometric block ratios; no outlier removal, no adaptive stopping, no repeats','admission_seconds':1200,'per_child_watchdog_seconds':90,'no_kill':True,'raw_correctness_gate':'all5locksignatures+perfts+NNUEFMA0+originalCTest13/14 exactknown4','controller_sha256':sha(Path(__file__)),'load_start':os.getloadavg()}
(out/'forge_sol_pgo_linux_protocol_20261025.json').write_text(json.dumps(protocol,indent=2)+'\n');print(json.dumps({'status':'STARTED','protocol':protocol}),flush=True)
raw=out/'forge_sol_pgo_linux_raw_20261025';raw.mkdir();samples=[];ratios=[];blocks=[]
payload='uci\nsetoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nisready\nbench 20\nquit\n'
try:
 for block in range(1,9):
  values=[]
  for index,(label,exe) in enumerate([('A',a),('B',b),('A',a),('B',b)]):
   if time.monotonic()>=deadline:raise TimeoutError('whole admission deadline')
   assert sha(exe)==hashes[str(exe)]
   tag=f'forge_sol_pgo_block{block:02d}_{index}_{label}_20261025';(raw/(tag+'.stdin')).write_text(payload)
   meta={'tag':tag,'utc':utc(),'argv':[str(exe)],'exe_sha256':sha(exe),'load_before':os.getloadavg(),'label':label}
   p=subprocess.Popen([str(exe)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,preexec_fn=limited)
   meta.update(pid=p.pid,affinity=sorted(os.sched_getaffinity(p.pid)),nice=os.getpriority(os.PRIO_PROCESS,p.pid));timed_out=False
   try:stdout,stderr=p.communicate(payload.encode(),timeout=min(90,deadline-time.monotonic()))
   except subprocess.TimeoutExpired:
    timed_out=True
    # quit is already queued after synchronous bench. No termination API used.
    try:stdout,stderr=p.communicate(timeout=min(120,max(1,deadline-time.monotonic())))
    except subprocess.TimeoutExpired:
     (out/'forge_sol_pgo_linux_unclosed_child_20261025.json').write_text(json.dumps({'pid':p.pid,'scope':'owned child only; no kill; qualification invalid'},indent=2)+'\n');raise
   (raw/(tag+'.stdout')).write_bytes(stdout);(raw/(tag+'.stderr')).write_bytes(stderr)
   meta.update(actual_exit=p.returncode,watchdog_expired=timed_out,closed_utc=utc(),load_after=os.getloadavg(),stdout_sha256=hashlib.sha256(stdout).hexdigest(),stderr_sha256=hashlib.sha256(stderr).hexdigest());(raw/(tag+'.json')).write_text(json.dumps(meta,indent=2)+'\n')
   assert not timed_out and p.returncode==0 and not stderr and meta['affinity']==[0,1,2,3] and meta['nice']==19
   matches=re.findall(rb'^info string bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)\r?$',stdout,re.M);assert len(matches)==1
   d,n,ms,nps=map(int,matches[0]);assert d==20 and n==11901452 and ms>0 and nps>0 and sha(exe)==hashes[str(exe)]
   samples.append({**meta,'nodes':n,'time_ms':ms,'nps':nps});values.append(nps)
  r1=values[1]/values[0];r2=values[3]/values[2];ratios.extend([r1,r2]);row={'block':block,'A1':values[0],'B1':values[1],'A2':values[2],'B2':values[3],'adjacent_ratios':[r1,r2],'geometric':(r1*r2)**0.5};blocks.append(row)
  (out/'forge_sol_pgo_linux_partial_20261025.json').write_text(json.dumps({'status':'PARTIAL_NOT_A_VERDICT','samples':samples,'blocks':blocks},indent=2)+'\n');print(json.dumps(row),flush=True)
 assert len(samples)==32 and len(ratios)==16
 median=statistics.median(ratios);verdict='PASS_3PCT_LINUX_SCREEN_ONLY' if median>=1.03 else 'DROP_BELOW_3PCT_LINUX_SCREEN'
 result={'status':'COMPLETE','closed_utc':utc(),'scope':protocol['scope'],'samples':32,'ABAB_blocks':8,'adjacent_pairs':16,'median_adjacent_ratio':median,'median_gain_pct':100*(median-1),'adjacent_ratios':ratios,'supplementary_median_block_geometric_ratio':statistics.median(x['geometric'] for x in blocks),'verdict':verdict,'native_Zen5_Windows_speed':'UNVERIFIED','Elo':None,'no_AA_confidence_claim':True,'load_end':os.getloadavg()}
 (out/'forge_sol_pgo_linux_samples_20261025.json').write_text(json.dumps(samples,indent=2)+'\n');(out/'forge_sol_pgo_linux_results_20261025.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
except Exception as e:
 (out/'forge_sol_pgo_linux_failure_20261025.json').write_text(json.dumps({'status':'FAILED_OR_INCOMPLETE_NO_VERDICT','utc':utc(),'error':repr(e),'complete_samples':len(samples),'complete_blocks':len(blocks)},indent=2)+'\n');raise
