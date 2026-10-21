#!/usr/bin/env python3
"""One exclusive read-only archive-audit launch; no producer or recovery import."""
import datetime,hashlib,json,os,subprocess,sys,time
from pathlib import Path
BASE=Path('/workspace/dwqww/validation/nearest-pawn-distance-20261020/archive-complete')
REPO=Path('/workspace/dwqww')
AUDIT=BASE/'independent_archive_audit.py'
EXPECTED='01b2544448dd26ad7fa7c88efb05a662c2ddcbe13d295f1f50af79bc525e8b67'
COMMAND=['/workspace/.cloud-setup/venv/bin/python','-B',str(AUDIT)]
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    assert sha(AUDIT)==EXPECTED,'Auditor bytes changed before authorized launch'
    for name in ['INDEPENDENT-ARCHIVE-AUDIT.json','independent-audit.stdout','independent-audit.stderr','INDEPENDENT-AUDIT-COMMAND.json','INDEPENDENT-AUDIT-EXIT.json']:
        assert not (BASE/name).exists(),'Refusing duplicate audit launch: '+name
    command={'command':COMMAND,'cwd':str(REPO),'audit_script_sha256':EXPECTED,'launcher_sha256':sha(Path(__file__)),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'attempt':1,'authorization':'Root authorized one fresh read-only independent actual21 complete archive audit','engines_compilers_git_recovery_extraction_chmod':False,'stdout':'independent-audit.stdout','stderr':'independent-audit.stderr'}
    with (BASE/'INDEPENDENT-AUDIT-COMMAND.json').open('x') as f:json.dump(command,f,indent=2);f.write('\n')
    result={'command':COMMAND,'attempt':1,'error':None,'timed_out':False}
    start=time.monotonic()
    try:
        with (BASE/'independent-audit.stdout').open('xb') as out,(BASE/'independent-audit.stderr').open('xb') as err:
            completed=subprocess.run(COMMAND,cwd=REPO,stdout=out,stderr=err,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},timeout=300,check=False)
        result['exit_code']=completed.returncode
    except Exception as e:
        result['error']={'type':type(e).__name__,'message':str(e)}
        result['timed_out']=isinstance(e,subprocess.TimeoutExpired)
        result['exit_code']=None
    result.update({'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'wall_seconds':time.monotonic()-start,'stdout_sha256':sha(BASE/'independent-audit.stdout'),'stderr_sha256':sha(BASE/'independent-audit.stderr'),'audit_script_sha256_after':sha(AUDIT),'auditor_script_unchanged':sha(AUDIT)==EXPECTED,'audit_receipt_exists':(BASE/'INDEPENDENT-ARCHIVE-AUDIT.json').exists(),'no_recovery_or_engine_execution':True})
    result['status']='PASS_AUDIT_COMMAND_EXIT' if result['exit_code']==0 and result['error'] is None else 'FAIL_AUDIT_COMMAND_EXIT'
    with (BASE/'INDEPENDENT-AUDIT-EXIT.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,sort_keys=True),flush=True)
    return 0 if result['status']=='PASS_AUDIT_COMMAND_EXIT' else 1
if __name__=='__main__':sys.exit(main())
