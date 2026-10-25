from pathlib import Path
import json,re,hashlib,statistics,datetime
h=Path('/workspace/forge-sol-20261025');p=h/'forge_sol_pgo_linux_abab_20261025';raw=p/'forge_sol_pgo_linux_raw_20261025';result=json.loads((p/'forge_sol_pgo_linux_results_20261025.json').read_text());protocol=json.loads((p/'forge_sol_pgo_linux_protocol_20261025.json').read_text());samples=json.loads((p/'forge_sol_pgo_linux_samples_20261025.json').read_text());supervisor=json.loads((h/'forge_sol_pgo_linux_abab_supervisor_20261025.json').read_text())
assert supervisor['actual_exit']==0 and result['status']=='COMPLETE' and len(samples)==32
assert hashlib.sha256((h/'forge_sol_pgo_linux_abab_20261025.py').read_bytes()).hexdigest()==protocol['controller_sha256']
ratios=[]
for i,s in enumerate(samples):
 tag=s['tag'];meta=json.loads((raw/(tag+'.json')).read_text());stdout=(raw/(tag+'.stdout')).read_bytes();stderr=(raw/(tag+'.stderr')).read_bytes()
 assert hashlib.sha256(stdout).hexdigest()==meta['stdout_sha256']==s['stdout_sha256'] and hashlib.sha256(stderr).hexdigest()==meta['stderr_sha256'] and not stderr
 assert meta['actual_exit']==0 and not meta['watchdog_expired'] and meta['affinity']==[0,1,2,3] and meta['nice']==19 and s['label']==('A' if i%2==0 else 'B')
 rows=re.findall(rb'^info string bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)\r?$',stdout,re.M);assert len(rows)==1;d,n,ms,nps=map(int,rows[0]);assert(d,n)==(20,11901452) and ms==s['time_ms'] and nps==s['nps']
 if i%2:ratios.append(s['nps']/samples[i-1]['nps'])
assert len(list(raw.glob('*.json')))==32 and len(ratios)==16 and ratios==result['adjacent_ratios'] and statistics.median(ratios)==result['median_adjacent_ratio'] and result['verdict']=='DROP_BELOW_3PCT_LINUX_SCREEN'
run=Path('/workspace/forge-sol-20261025-pgo/forge_sol_pgo_linux_proof_20261025');train=json.loads((run/'receipts/train.PASS.json').read_text());current={x.relative_to(run/'work/profile-frozen').as_posix():hashlib.sha256(x.read_bytes()).hexdigest() for x in(run/'work/profile-frozen').rglob('*.gcda')};assert current==train['profile_sha256']
out={'status':'PASS','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actual_complete_samples':32,'all_raw_hashes_exits_nodes_affinity_priority_and_order_checked':True,'ratios_recomputed':16,'median':statistics.median(ratios),'gain_pct':result['median_gain_pct'],'decision':'DROP_BELOW_3PCT_LINUX_SCREEN','used_frozen_profiles_unchanged':8,'native_Windows_Zen5':'UNVERIFIED','scope':'Read-only raw evidence audit; no new speed run'};(p/'forge_sol_pgo_linux_audit_20261025.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
