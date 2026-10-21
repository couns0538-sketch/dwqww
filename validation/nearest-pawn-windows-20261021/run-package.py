from pathlib import Path
import datetime,hashlib,json,os,shutil,subprocess,sys,time
from pipeline_gate import load_freeze
FREEZE=load_freeze()
here=Path(__file__).resolve().parent
assert json.loads((here/'WINDOWS-BUILD-CLEAR.json').read_text())['authorization']=='21 WINDOWS BUILD CLEAR'
capture=Path('/workspace/.cloud-setup/windows6421-package-capture')
capture.mkdir(exist_ok=False)
cmd=[sys.executable,str(here/'package-driver.py')]
env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat();start=time.monotonic();before=hashlib.sha256((here/'package-driver.py').read_bytes()).hexdigest()
with (capture/'stdout').open('xb') as stdout,(capture/'stderr').open('xb') as stderr:
 result=subprocess.run(cmd,cwd='/workspace/dwqww',env=env,stdout=stdout,stderr=stderr,timeout=1200)
record={'phase':'package','command':cmd,'exit_code':result.returncode,'elapsed_seconds_diagnostic_only':time.monotonic()-start,'started_utc':started_utc,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'driver_sha256_before':before,'driver_sha256_after':hashlib.sha256((here/'package-driver.py').read_bytes()).hexdigest(),'capture_note':'Package process stdout/stderr captured outside the raw snapshot and copied after completion, avoiding actively changing archived originals.'}
(here/'package-phase-command.json').write_text(json.dumps(record,indent=2)+'\n')
shutil.copyfile(capture/'stdout',here/'package-phase.stdout');shutil.copyfile(capture/'stderr',here/'package-phase.stderr')
assert record['driver_sha256_before']==record['driver_sha256_after']
print(json.dumps(record),flush=True)
raise SystemExit(result.returncode)
