#!/usr/bin/env python3
"""One preregistered advisory Linux screen; no adoption/speed/Elo conclusion."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,statistics,subprocess,time
ap=argparse.ArgumentParser();ap.add_argument('--protocol-only',action='store_true');a=ap.parse_args()
h=Path('/workspace/forge-jobACD-20261025');base=Path('/workspace/forge-sol-20261025-pgo/forge_sol_pgo_linux_proof_20261025/bin/forge_sol_pgo_baseline_20261025.exe');cand=h/'forge_sol_a_release_20261025/forge';out=h/'forge_sol_a_advisory_abba_20261025'
p={'purpose':'ADVISORY_ONLY_NO_SPEED_CLAIM_OR_ADOPTION','A':'untouched lock float, original GCC14.2 static recipe','B':'exact-int32 feature ON, GCC14.2 static strict-FP','A_sha256':hashlib.sha256(base.read_bytes()).hexdigest(),'B_sha256':hashlib.sha256(cand.read_bytes()).hexdigest(),'depths':{'13':745494,'16':2460422},'blocks_per_depth':10,'order':'ABBA','paired_ratios':'2 per ABBA block: B1/A1 and B2/A2; primary median ALL20 adjacent ratios at each depth','no_outlier_removal':True,'no_retry':True,'affinity':[0],'nice':19,'resource':'T1 builtin bench Hash16; original bench resets positions; source overhead included inB','stop_rule':'complete80 normal processes or stop FAIL on any signature/exit/output error','elapsed_refresh_time_share':'UNVERIFIED; construction-call share reported separately','protocol_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
protocol=h/'forge_sol_a_advisory_protocol_20261025.json'
if a.protocol_only:
 assert not protocol.exists();protocol.write_text(json.dumps(p,indent=2)+'\n');print('Protocol frozen');raise SystemExit
assert json.loads(protocol.read_text())==p,'Protocol or engines changed after registration'
os.sched_setaffinity(0,{0});os.nice(19);assert os.sched_getaffinity(0)=={0} and os.getpriority(os.PRIO_PROCESS,0)==19
out.mkdir(exist_ok=False);result={'protocol':p,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'INCOMPLETE','rows':[],'depths':{}}
try:
 for depth,expected in [(13,745494),(16,2460422)]:
  ratios=[]
  for block in range(10):
   times=[]
   for slot,label in enumerate('ABBA'):
    exe=base if label=='A' else cand;commands=('setoption name NnueExactInt32 value true\n' if label=='B' else '')+f'bench {depth}\nquit\n';start=time.monotonic_ns();run=subprocess.run([str(exe)],input=commands,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE);elapsed=time.monotonic_ns()-start;name=f'forge_sol_d{depth}_block{block:02d}_{slot}_{label}_20261025';(out/(name+'.stdout')).write_text(run.stdout);(out/(name+'.stderr')).write_text(run.stderr)
    import re
    m=re.search(r'bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)',run.stdout);assert run.returncode==0 and not run.stderr and m and int(m[2])==expected
    if label=='B':assert 'NnueExactInt32 active' in run.stdout and re.search(r'int32_updates [1-9]',run.stdout)
    row={'depth':depth,'block':block,'slot':slot,'engine':label,'nodes':int(m[2]),'internal_ms':int(m[3]),'nps':int(m[4]),'process_wall_ns':elapsed,'stdout_sha256':hashlib.sha256(run.stdout.encode()).hexdigest(),'stderr_sha256':hashlib.sha256(run.stderr.encode()).hexdigest(),'actual_exit':run.returncode};result['rows'].append(row);times.append(row['nps']);(out/'forge_sol_advisory_partial_20261025.json').write_text(json.dumps(result,indent=2)+'\n')
   ratios.extend([times[1]/times[0],times[2]/times[3]])
  median=statistics.median(ratios);result['depths'][str(depth)]={'ratios':ratios,'median_ratio':median,'median_percent':100*(median-1),'screen':'DROP_BELOW_1PCT' if median<1.01 else 'ADVISORY_ABOVE1PCT_ADOPTION_UNVERIFIED'}
 result['status']='COMPLETE_ADVISORY_ONLY';result['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
finally:(out/'forge_sol_advisory_result_20261025.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
