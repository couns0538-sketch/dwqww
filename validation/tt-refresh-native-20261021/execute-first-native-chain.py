#!/usr/bin/env python3
"""First authorized serial native23 chain. Records original streams/exits; never retries."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,subprocess,sys,time
ROOT=Path('/workspace/dwqww');HERE=ROOT/'validation/tt-refresh-native-20261021'
PY='/workspace/.cloud-setup/venv/bin/python'
SOURCE='1d3ed25bea2c8b781f7ee5a178af0f66061b3984'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
clear=json.loads((HERE/'ROOT-CLEARANCE.json').read_text());provenance=json.loads((HERE/'DRIVER-PROVENANCE.json').read_text())
assert clear['authorized'] is True and clear['source_commit']==SOURCE
assert sha(HERE/'ROOT-CLEARANCE.json')=='a58ccac85937205f200e1297c44b0ecae5dec654edcae1d5d7ebb2ee9aac68bd'
assert sha(HERE/'ROOT-FROZEN-SOURCE-GATES.json')=='f029228717c97678b124722efdba0ed7c9b356d90e4e79236597674ba82b7294'
assert sha(HERE/'DRIVER-PROVENANCE.json')=='3e2fe83fcf6b1463c226104afa91fa9c780dc5d0fb0633a0a78544827bc34c20'
assert sha(HERE/'independent-audit.py')=='9a36989b400dbec00893cabcf81b197166abeb68928c19c9b77dfc6e345449c1'
assert all(sha(HERE/name)==value for name,value in provenance['scripts'].items())
sealed={**provenance['scripts'],**{name:sha(HERE/name) for name in ['ROOT-CLEARANCE.json','ROOT-FROZEN-SOURCE-GATES.json','DRIVER-PROVENANCE.json','RELEASE-SIGNATURE-PROTOCOL.json','ACTIVE-UCI-PROTOCOL.json','EXPECTED-CTEST-COMMANDS.json']}}
freeze={'source_commit':SOURCE,'frozen_utc':datetime.now(timezone.utc).isoformat(),'frozen_files_sha256':sealed,'execution_controller_sha256':sha(Path(__file__)),'first_attempt_only':True}
with (HERE/'SOURCE-AND-DRIVER-FREEZE.json').open('x') as f:json.dump(freeze,f,indent=2);f.write('\n')
commands=[('release',['run-frozen-validation.py','release']),('release-signature',['run-release-signature.py']),('asan',['run-frozen-validation.py','asan']),('tsan',['run-frozen-validation.py','tsan']),('active',['run-active-validation.py']),('snapshot',['snapshot-originals.py']),('audit',['independent-audit.py','--require-active'])]
record={'status':'RUNNING_FIRST_AUTHORIZED_NATIVE23_CHAIN','source_commit':SOURCE,'started_utc':datetime.now(timezone.utc).isoformat(),'steps':[],'engine_gate_retries_performed':False}
save(HERE/'DRIVER-EXECUTIONS.json',record)
for label,args in commands:
    assert all(sha(HERE/name)==value for name,value in sealed.items()),'Sealed source driver/protocol/clearance changed'
    command=[PY,'-B',str(HERE/args[0]),*args[1:]]
    facts={'label':label,'command':command,'cwd':str(ROOT),'started_utc':datetime.now(timezone.utc).isoformat(),'attempt':1}
    with (HERE/(label+'-driver-command.json')).open('x') as f:json.dump(facts,f,indent=2);f.write('\n')
    print('START_NATIVE23 '+label,flush=True);started=time.monotonic();error=None;rc=None
    with (HERE/(label+'-driver.stdout')).open('xb') as out,(HERE/(label+'-driver.stderr')).open('xb') as err:
        try:rc=subprocess.run(command,cwd=ROOT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},stdout=out,stderr=err,check=False).returncode
        except Exception as e:error=repr(e)
    facts.update(exit_code=rc,error=error,completed_utc=datetime.now(timezone.utc).isoformat(),elapsed_seconds_operational_only=time.monotonic()-started,stdout_sha256=sha(HERE/(label+'-driver.stdout')),stderr_sha256=sha(HERE/(label+'-driver.stderr')),sealed_inputs_unchanged=all(sha(HERE/name)==value for name,value in sealed.items()))
    save(HERE/(label+'-driver-command.json'),facts);record['steps'].append(facts);save(HERE/'DRIVER-EXECUTIONS.json',record)
    print('FINISH_NATIVE23 '+label+' '+json.dumps(facts,sort_keys=True),flush=True)
    if rc!=0 or error or not facts['sealed_inputs_unchanged']:
        record.update(status='FAILED_FIRST_AUTHORIZED_NATIVE23_CHAIN',failed_stage=label,completed_utc=datetime.now(timezone.utc).isoformat());save(HERE/'DRIVER-EXECUTIONS.json',record);raise SystemExit(1)
record.update(status='PASS_FIRST_AUTHORIZED_NATIVE23_CHAIN',completed_utc=datetime.now(timezone.utc).isoformat());save(HERE/'DRIVER-EXECUTIONS.json',record)
print(record['status'],flush=True)
