from pathlib import Path
import datetime,hashlib,json,os,shutil,subprocess,sys
R=Path('/workspace/dwqww'); O=R/'validation/pawn-span-fill-20261020/archive-complete'; C=Path('/workspace/.cloud-setup')
stdout_path=C/'forge20-archive-run.stdout'; stderr_path=C/'forge20-archive-run.stderr'
assert not stdout_path.exists() and not stderr_path.exists(), 'Never overwrite a run log'
command=[sys.executable,'-B',str(O/'archive_complete.py'),'--root-clearance','20-ARCHIVE-AUTHORIZED']
env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
with stdout_path.open('xb') as out,stderr_path.open('xb') as err:
    done=subprocess.run(command,cwd=R,env=env,stdout=out,stderr=err,timeout=1800)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt={'status':'PASS_COMMAND_EXIT' if done.returncode==0 else 'FAILED_COMMAND_RETAINED','started_utc':started,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':command,'cwd':str(R),'exit_code':done.returncode,'live_stdout_stderr_routed_outside_output':True,'stdout_original':str(stdout_path),'stderr_original':str(stderr_path),'stdout_sha256':sha(stdout_path),'stderr_sha256':sha(stderr_path),'source_engine_compiler_or_git_execution':False}
with (O/'DRIVER-EXIT.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
for source,name in [(stdout_path,'driver.stdout'),(stderr_path,'driver.stderr'),(Path(__file__),'launch_archive_once.py')]:
    target=O/name
    assert not target.exists();shutil.copy2(source,target)
print(json.dumps(receipt,indent=2),flush=True)
raise SystemExit(done.returncode)
