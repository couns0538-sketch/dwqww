from pathlib import Path
import subprocess,json,os,time,signal,hashlib,re
P=Path(__file__).parent;R=Path('/workspace/dwqww');core=Path('/workspace/.cloud-setup/nnue-final-linux-a52efa5f7864-attempt1/build-release/libforge_core.a')
def run(label,cmd,expected):
 (P/(label+'.command.json')).write_text(json.dumps({'argv':[str(x) for x in cmd],'cwd':str(P)},indent=2)+'\n');start=time.monotonic();error=None
 with (P/(label+'.stdout')).open('wb') as out,(P/(label+'.stderr')).open('wb') as err:
  p=subprocess.Popen([str(x) for x in cmd],cwd=P,stdout=out,stderr=err,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},start_new_session=True)
  try:p.wait(timeout=180)
  except BaseException as e:
   error=repr(e)
   if p.poll() is None:os.killpg(p.pid,signal.SIGKILL)
   p.wait()
 result={'returncode':p.returncode,'expected_returncode':expected,'elapsed_seconds':time.monotonic()-start,'error':error,'owned_process_reaped':True};(P/(label+'.result.json')).write_text(json.dumps(result,indent=2)+'\n')
 if error or p.returncode!=expected:raise RuntimeError(label+' unexpected result; originalevidencepreserved')
flags=['/usr/bin/g++-14','-std=c++20','-O3','-DNDEBUG','-march=x86-64-v3','-mtune=znver5','-fno-fast-math','-ffp-contract=off','-fno-lto','-pthread','-DFORGE_NNUE_HIDDEN=128','-I'+str(R/'include')]
obj=P/'search-nmp-disabled.o';binary=P/'tests-repaired-nmp-disabled';linkmap=P/'nmp-disabled.map'
run('compile-private-search-negative',flags+['-c',P/'search.nmp-disabled.cpp','-o',obj],0)
run('link-negative',flags+[P/'tests.repaired.cpp',obj,core,'-Wl,-Map='+str(linkmap),'-o',binary],0)
maptext=linkmap.read_text();assert str(obj) in maptext and not re.search(r'libforge_core\.a\(search\.cpp\.o\)',maptext)
run('run-negative',[binary],1)
stdout=(P/'run-negative.stdout').read_text();stderr=(P/'run-negative.stderr').read_text()
assert 'Controlled null cutoff: prepared 1 tries 0 cutoffs 0' in stdout
assert 'FAIL: eligible non-pawn null pruning attempts and cuts off through its child' in stderr
result={'status':'PASS_NEGATIVE_CONTROL_REAL_NMP_REMOVAL_CAUGHT','expected_binary_exit':1,'controlled_tries':0,'controlled_cutoffs':0,'private_search_override_sha256':hashlib.sha256(obj.read_bytes()).hexdigest(),'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'link_map_sha256':hashlib.sha256(linkmap.read_bytes()).hexdigest(),'original_archive_search_object_linked':False,'actual_private_object_linked':str(obj),'failure_stderr':stderr,'stdout_sha256':hashlib.sha256((P/'run-negative.stdout').read_bytes()).hexdigest(),'production_core_untouched':True}
(P/'NEGATIVE.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
