from pathlib import Path
import datetime,hashlib,importlib.util,json,os,subprocess,signal,time
REPO=Path('/workspace/dwqww');HERE=Path(__file__).resolve().parent
SOURCE=Path('/workspace/.cloud-setup/nearest-pawn-prototype-source')
BUILD=Path('/workspace/.cloud-setup/nearest-pawn-helper-attempt1');BUILD.mkdir(exist_ok=False)
OUT=HERE/'helper-attempt1';OUT.mkdir(exist_ok=False)
CXX='/usr/bin/g++-14'
FLAGS=['-std=c++20','-O3','-DNDEBUG','-march=x86-64-v3','-mtune=generic','-fno-fast-math','-ffp-contract=off','-fno-lto','-Wall','-Wextra','-Wpedantic','-Wconversion','-Wshadow']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected=json.loads((HERE/'EXPECTED-SOURCE-76.json').read_text())
def sources():return {p.relative_to(SOURCE).as_posix():sha(p) for p in sorted(SOURCE.rglob('*')) if p.is_file()}
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
spec=importlib.util.spec_from_file_location('trusted_native20_process_facts',REPO/'validation/pawn-span-fill-native-20261020/process_facts.py');owner=importlib.util.module_from_spec(spec);spec.loader.exec_module(owner)
summary={'status':'RUNNING','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(SOURCE),'source_files':76,'prototype_version':'6.4.20','next_candidate':'nearest-pawn-distance','baseline_source':'fc2391870b3bf2cd4d8fc20c7406ea6439c69c5e','steps':[],'speed_or_elo_claim':None}
assert sources()==expected
save(OUT/'summary.json',summary)
def run(label,command,limit):
 start=time.monotonic();child=None;code=None;error=None;timeout=False
 before=sources();assert before==expected
 with (OUT/(label+'.stdout')).open('xb') as stdout,(OUT/(label+'.stderr')).open('xb') as stderr:
  try:
   child=subprocess.Popen(command,cwd=REPO,stdout=stdout,stderr=stderr,start_new_session=True)
   try:code=child.wait(timeout=limit)
   except subprocess.TimeoutExpired:
    timeout=True;error='command timeout';os.killpg(child.pid,signal.SIGKILL);code=child.wait(timeout=10)
  except BaseException as exc:error=repr(exc)
  finally:cleanup=owner.cleanup(child.pid) if child else {'no_live_owned_processes':True,'not_started':True}
 record={'label':label,'command':command,'cwd':str(REPO),'timeout_seconds':limit,'returncode_before_verdict':code,'timed_out':timeout,'error':error,'pid':child.pid if child else None,'cleanup':cleanup,'stdout_sha256':sha(OUT/(label+'.stdout')),'stderr_sha256':sha(OUT/(label+'.stderr')),'source_before':before,'source_after':sources(),'elapsed_seconds_diagnostic_only':time.monotonic()-start}
 summary['steps'].append(record);save(OUT/(label+'-command.json'),record);save(OUT/'summary.json',summary)
 assert code==0 and not error and not timeout and cleanup['no_live_owned_processes'],label
 assert record['source_after']==before,label
try:
 run('compile',[CXX,*FLAGS,'-I',str(SOURCE/'include'),'-c',str(SOURCE/'tests/nearest_pawn_tests.cpp'),'-o',str(BUILD/'nearest_pawn_tests.o')],180)
 run('link',[CXX,'-fno-lto',str(BUILD/'nearest_pawn_tests.o'),'-o',str(BUILD/'nearest_pawn_tests')],60)
 before={p.name:sha(p) for p in BUILD.iterdir() if p.is_file()}
 run('unit',[str(BUILD/'nearest_pawn_tests')],60)
 assert before=={p.name:sha(p) for p in BUILD.iterdir() if p.is_file()}
 text=(OUT/'unit.stdout').read_text();assert text=='Nearest pawn distance: sets 395840 checks 791680 failures 0\n'
 assert not (OUT/'unit.stderr').read_bytes()
 summary.update(status='PASS',target_sets=395840,oracle_checks=791680,failures=0,compiled_constexpr_assertions=6,artifacts=before,completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
except BaseException as exc:summary.update(status='FAILED',error=repr(exc));raise
finally:save(OUT/'summary.json',summary)
print(json.dumps({k:v for k,v in summary.items() if k!='steps'}))
