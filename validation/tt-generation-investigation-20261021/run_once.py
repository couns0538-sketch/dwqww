from pathlib import Path
import hashlib,json,subprocess,os,sys,time
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));from process_facts import cleanup
S=Path('/workspace/.cloud-setup/tt-generation-observer-source');B=Path('/workspace/.cloud-setup/tt-generation-investigation-attempt1');B.mkdir(exist_ok=False);O=D/'attempt1';O.mkdir(exist_ok=False);BASE=Path('/workspace/.cloud-setup/pv-metadata-native-release');sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();F=['-std=c++20','-O3','-DNDEBUG','-march=x86-64-v3','-mtune=znver5','-fno-fast-math','-ffp-contract=off','-fno-lto'];src=json.loads((D/'SOURCE-BASE.json').read_text());assert sha(BASE/'libforge_core.a')==src['parent_core_sha256'];report={'status':'RUNNING','steps':[],'parent_core_sha256':src['parent_core_sha256'],'policy_changed':False}
def save():(O/'result.json').write_text(json.dumps(report,indent=2)+'\n')
def run(label,cmd,timeout=90):
 row={'label':label,'command':cmd,'exit_code':None};report['steps'].append(row);save();p=None
 try:
  with (O/(label+'.stdout')).open('xb') as out,(O/(label+'.stderr')).open('xb') as err:
   p=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=out,stderr=err,cwd=B,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},start_new_session=True);row['pid']=p.pid
   try:p.wait(timeout=timeout);row['exit_code']=p.returncode
   finally:row['cleanup']=cleanup(p.pid);p.wait(timeout=2);row['after_cleanup_exit']=p.returncode
  row['stdout_sha256']=sha(O/(label+'.stdout'));row['stderr_sha256']=sha(O/(label+'.stderr'));save();assert row['exit_code']==0 and row['cleanup']['no_live_owned_processes']
 finally:save()
try:
 run('compile-actual-table-fixture',['/usr/bin/g++-14',*F,'-I'+str(S/'include'),str(D/'table_fixture.cpp'),str(BASE/'libforge_core.a'),'-pthread','-o',str(B/'table_fixture')])
 run('actual-table-fixture',[str(B/'table_fixture')]);report['status']='ACTUAL_TABLE_FIXTURE_PASS_OBSERVER_NOT_YET_RUN';save()
except BaseException as e:report['status']='FAILED_STOP_NO_RETRY';report['error']=repr(e);save();raise
