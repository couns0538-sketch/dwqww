#!/usr/bin/env python3
"""One explicitly cleared21 archive process; preserve raw logs outside its frozen output."""
from pathlib import Path
import datetime,hashlib,json,os,signal,subprocess,sys
ROOT=Path('/workspace/dwqww');OUT=ROOT/'validation/nearest-pawn-distance-20261020/archive-complete';BASE=Path('/workspace/.cloud-setup')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
assert Path(__file__).resolve().parent==OUT, 'Preparation is not executable; root must promote reviewed files'
clear=json.loads((OUT/'ROOT-CLEARANCE.json').read_text())
assert clear.get('authorized') is True and clear['authorization']=='21 COMPLETE ARCHIVE TASK AUTHORIZED' and clear['provided_by']=='/root' and clear['included_writers_quiescent'] is True
assert clear['source_commit']=='2e151d019bc58dff2ab4e76e99ef99516af8d222'
logs=[BASE/'forge21-archive-run.stdout',BASE/'forge21-archive-run.stderr']
for path in logs:assert not path.exists() and not path.is_symlink(), 'Never overwrite run logs'
for name in ['ARCHIVE-LAUNCH-COMMAND.json','DRIVER-EXIT.json','driver.stdout','driver.stderr']:assert not (OUT/name).exists()
command=[sys.executable,'-B',str(OUT/'archive_complete.py'),'--root-clearance','21-ARCHIVE-AUTHORIZED']
env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';started=now()
record={'status':'ROOT_AUTHORIZED_BEFORE_EXECUTION','started_utc':started,'command':command,'cwd':str(ROOT),'timeout_seconds':1800,'root_clearance_sha256':sha(OUT/'ROOT-CLEARANCE.json'),'launcher_sha256':sha(Path(__file__)),'driver_sha256':sha(OUT/'archive_complete.py'),'raw_logs_outside_snapshot':[str(path) for path in logs],'no_engine_compiler_git_execution':True}
with (OUT/'ARCHIVE-LAUNCH-COMMAND.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
child=None;code=None;error=None;timed=False
with logs[0].open('xb') as stdout,logs[1].open('xb') as stderr:
    try:
        child=subprocess.Popen(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
        try:code=child.wait(timeout=1800)
        except subprocess.TimeoutExpired:timed=True;error='archive process timeout';os.killpg(child.pid,signal.SIGKILL);code=child.wait(timeout=10)
    except BaseException as exc:error=repr(exc)
receipt={'status':'PASS_COMMAND_EXIT' if code==0 and not timed and not error else 'FAILED_COMMAND_RETAINED_NO_RETRY','started_utc':started,'completed_utc':now(),'command':command,'cwd':str(ROOT),'exit_code':code,'timed_out':timed,'error':error,'raw_logs_outside_snapshot':[str(path) for path in logs],'stdout_sha256':sha(logs[0]),'stderr_sha256':sha(logs[1]),'source_engine_compiler_or_git_execution':False}
with (OUT/'DRIVER-EXIT.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
for source,name in zip(logs,['driver.stdout','driver.stderr']):
    with source.open('rb') as src,(OUT/name).open('xb') as dst:
        while True:
            data=src.read(1024*1024)
            if not data:break
            dst.write(data)
print(json.dumps(receipt,indent=2))
sys.exit(0 if receipt['status']=='PASS_COMMAND_EXIT' else 1)
