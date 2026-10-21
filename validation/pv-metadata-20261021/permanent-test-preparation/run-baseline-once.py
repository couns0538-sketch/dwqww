#!/usr/bin/env python3
from pathlib import Path
import sys,json,hashlib,subprocess,time,os,re,datetime
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2]
sys.path.insert(0,str(HERE.parent));from process_facts import cleanup
REV='2e151d019bc58dff2ab4e76e99ef99516af8d222'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
expected=load(HERE/'EXPECTED-BASELINE.json');source=Path('/workspace/.cloud-setup/nearest-pawn-native-source');core=Path(expected['core']);receipt=REPO/'validation/nearest-pawn-native-20261020/FINAL-RECEIPT.json';native=load(receipt)
assert native['source_commit']==REV
assert sha(core)==native['native_profiles']['release']['core_sha256']
base=load(HERE.parent/'EXPECTED-VARIANTS.json')['base76_source_sha256']
assert {str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()}==base
inputs=[Path(__file__),HERE/'pv_metadata_tests.cpp',HERE/'EXPECTED-BASELINE.json',HERE.parent/'process_facts.py',receipt,core,*sorted((source/'include').rglob('*.hpp'))]
frozen={str(p):sha(p) for p in inputs};out=HERE/'baseline-attempt1';out.mkdir(exist_ok=False);build=Path('/workspace/.cloud-setup/pv-metadata-permanent-red-build-attempt1');build.mkdir(exist_ok=False)
report={'status':'RUNNING','source_commit':REV,'inputs_before':frozen,'steps':[],'production_edits':False,'purpose':'Permanent diagnostic-free actual-core regression; new question, not a repeated diagnostic experiment'}
def save():(out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
def run(name,cmd,exitcode):
 row={'label':name,'command':cmd,'cwd':str(build),'stdin':'empty','exit_code':None};report['steps'].append(row);save();p=None
 try:
  with (out/(name+'.stdout')).open('xb') as stdout,(out/(name+'.stderr')).open('xb') as stderr:
   p=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,cwd=build,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},start_new_session=True);row['pid']=row['pgid']=p.pid
   try:p.wait(timeout=90);row['exit_code']=p.returncode
   finally:
    row['cleanup']=cleanup(p.pid)
    try:p.wait(timeout=2)
    except subprocess.TimeoutExpired:row['wait_error']='unreaped'
    row['post_cleanup_exit_code']=p.returncode
  row['stdout_sha256']=sha(out/(name+'.stdout'));row['stderr_sha256']=sha(out/(name+'.stderr'));save()
  assert row['exit_code']==exitcode and row['cleanup']['no_live_owned_processes']
 finally:save()
save()
try:
 exe=build/'forge_pv_metadata_tests';cmd=['/usr/bin/g++-14','-std=c++20','-O3','-DNDEBUG','-march=x86-64-v3','-mtune=znver5','-fno-fast-math','-ffp-contract=off','-fno-lto','-Wall','-Wextra','-Wpedantic','-I'+str(source/'include'),str(HERE/'pv_metadata_tests.cpp'),str(core),'-pthread','-o',str(exe)]
 run('compile-link',cmd,0);report['binary_sha256']=sha(exe);save();run('actual-core-unit',[str(exe)],1)
 stdout=(out/'actual-core-unit.stdout').read_text();stderr=(out/'actual-core-unit.stderr').read_text();bad=re.findall(r'^FAIL (.*)$',stderr,re.M);assert sorted(bad)==sorted(expected['expected_failed_assertions']),bad
 assert all(line.startswith('FAIL ') for line in stderr.splitlines() if line.strip())
 summary=re.findall(r'^PV metadata: assertions (\d+) failures (\d+)$',stdout,re.M);assert len(summary)==1 and int(summary[0][1])==len(bad)
 cases=re.findall(r'^PV_METADATA_CASE (\S+) nodes=(\d+) aborted=(\d+) flag=(\d+) pv_moves=(\d+)$',stdout,re.M);assert len(cases)==5
 report['assertions']=int(summary[0][0]);report['expected_failures']=bad;report['case_rows']=cases;report['core_unchanged']=sha(core)==frozen[str(core)];assert report['core_unchanged']
 assert all(sha(p)==v for p,v in frozen.items());report['status']='EXPECTED_BASELINE_RED_PERMANENT_REGRESSION';report['all_other_assertions_passed']=True
except BaseException as error:report['status']='FAILED_OR_INCONCLUSIVE_STOP_NO_RETRY';report['error']=repr(error);raise
finally:
 report['inputs_after']={str(p):sha(p) for p in inputs if p.is_file()};report['completed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save()
