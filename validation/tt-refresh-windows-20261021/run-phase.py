from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys,time
from pipeline_gate import load_freeze
FREEZE=load_freeze()
here=Path(__file__).resolve().parent
assert json.loads((here/'WINDOWS-BUILD-CLEAR.json').read_text())['authorization']=='23 WINDOWS BUILD CLEAR'
phase=sys.argv[1]
assert phase in ('build','validation'), 'Use run-package.py for closed-writer package capture'
cmd=[sys.executable,str(here/(phase+'-driver.py'))]
env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
start=time.monotonic()
with (here/(phase+'-phase.stdout')).open('xb') as stdout,(here/(phase+'-phase.stderr')).open('xb') as stderr:
 result=subprocess.run(cmd,cwd='/workspace/dwqww',env=env,stdout=stdout,stderr=stderr,timeout=1200)
record={'phase':phase,'command':cmd,'exit_code':result.returncode,'elapsed_seconds_diagnostic_only':time.monotonic()-start,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'driver_sha256':hashlib.sha256((here/(phase+'-driver.py')).read_bytes()).hexdigest()}
(here/(phase+'-phase-command.json')).write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record),flush=True)
raise SystemExit(result.returncode)
