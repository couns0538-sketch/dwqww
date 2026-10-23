from pathlib import Path
import subprocess,json,os,time,signal,hashlib
P=Path(__file__).parent;ROOT=Path('/workspace/dwqww')
def dump(name,data):(P/name).write_text(json.dumps(data,indent=2)+'\n')
def run(label,cmd,expected=0):
 dump(label+'.command.json',{'argv':[str(x) for x in cmd],'cwd':str(P),'environment_overrides':{'PYTHONDONTWRITEBYTECODE':'1'}});start=time.monotonic();error=None
 with (P/(label+'.stdout')).open('wb') as out,(P/(label+'.stderr')).open('wb') as err:
  proc=subprocess.Popen([str(x) for x in cmd],cwd=P,stdout=out,stderr=err,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},start_new_session=True)
  try:proc.wait(timeout=180)
  except BaseException as e:
   error=repr(e)
   if proc.poll() is None:os.killpg(proc.pid,signal.SIGKILL)
   proc.wait()
 fact={'returncode':proc.returncode,'elapsed_seconds':time.monotonic()-start,'error':error,'owned_process_reaped':True};dump(label+'.result.json',fact)
 if error or proc.returncode!=expected:raise RuntimeError(label+' failed; originalevidencepreserved')
 return fact
flags=['/usr/bin/g++-14','-std=c++20','-O3','-DNDEBUG','-march=x86-64-v3','-mtune=znver5','-fno-fast-math','-ffp-contract=off','-fno-lto','-pthread','-DFORGE_NNUE_HIDDEN=128','-I'+str(ROOT/'include')]
cores={'old':Path('/workspace/.cloud-setup/nnue-pipeline-20261023-working-build/libforge_core.a'),'new':Path('/workspace/.cloud-setup/nnue-final-linux-a52efa5f7864-attempt1/build-release/libforge_core.a')}
results={}
for label,core in cores.items():
 binary=P/('tests-repaired-'+label)
 run('compile-'+label,flags+[P/'tests.repaired.cpp',core,'-Wl,-Map='+str(P/(label+'.map')),'-o',binary])
 fact=run('run-'+label,[binary]);output=(P/('run-'+label+'.stdout')).read_text()
 assert 'Controlled null cutoff: prepared 1 tries 1 cutoffs 1 nodes 2 score 0 restored 1' in output and 'All tests passed' in output
 assert not (P/('run-'+label+'.stderr')).stat().st_size
 results[label]={'actual_exit':fact['returncode'],'stdout_sha256':hashlib.sha256((P/('run-'+label+'.stdout')).read_bytes()).hexdigest(),'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'core_sha256':hashlib.sha256(core.read_bytes()).hexdigest(),'controlled_tries':1,'controlled_cutoffs':1,'controlled_nodes':2,'controlled_score':0,'board_restored':True,'complete_original_test_translation_unit_with_bounded_test_repair':True}
dump('POSITIVE.json',{'status':'PASS_BOTH_OLD_AND_SELECTED_NETWORK_CORE_FULL_TEST_TRANSLATION_UNITS','results':results,'test_sha256':hashlib.sha256((P/'tests.repaired.cpp').read_bytes()).hexdigest(),'negative_control':'pending'})
print(json.dumps(results))
