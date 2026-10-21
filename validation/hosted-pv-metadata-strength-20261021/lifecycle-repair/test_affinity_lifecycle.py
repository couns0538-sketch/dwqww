"""Actual main lifecycle with only nested bench/match bodies replaced by inert mocks.
No engine, child process, affinity mutation or real match; injected resource faults
exercise actual setup/finalization/exception paths and original exception identity.
"""
import ast,copy,importlib.util,json,os,sys,tempfile,types,unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
SOURCE=Path(os.environ.get('LIFECYCLE_RUNNER',str(HERE/'before/package/run_hosted.py')))
class InjectedError(RuntimeError):pass
class Lifecycle(unittest.TestCase):
 def exercise(self,fault=None,restore_fault=False):
  tree=ast.parse(SOURCE.read_text())
  main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
  # Keep actual main, setup, exception handling and every finalization statement.
  # Only nested expensive operation bodies become explicit no-op fixtures.
  for node in ast.walk(main):
   if isinstance(node,ast.FunctionDef) and node.name in ('bench','match'):
    node.body=ast.parse("return {'wall_seconds':1.0,'cpu_seconds':1.0}" if node.name=='bench' else "return {'decision':'SYNTHETIC_NOT_A_RESULT'}").body
  ast.fix_missing_locations(tree);m=types.ModuleType('lifecycle_actual_main');m.__file__=str(SOURCE);exec(compile(tree,str(SOURCE),'exec'),m.__dict__)
  error=KeyboardInterrupt('injected interrupt') if fault=='interrupt' else InjectedError('injected '+str(fault))
  restoration=InjectedError('injected restore failure');mask={2,5};calls=[];reports=[];pin=[False];final=[False]
  def affinity(pid,new):
   calls.append(set(new))
   if len(calls)==1:mask.clear();mask.update(new);pin[0]=True
   else:
    if restore_fault:raise restoration
    mask.clear();mask.update(new)
  def load(name,path):
   if pin[0] and fault=='import':raise error
   return types.SimpleNamespace(verify_build_evidence=lambda *args:[])
  def sha(path):
   if pin[0] and not final[0] and fault=='hash':raise error
   return 'a'*64
  def save(path,value):
   if pin[0] and fault=='initial_save' and path.name=='host-context-before.json':raise error
   if fault=='final_save' and final[0] and path.name=='summary.json':raise error
   if path.name=='summary.json':reports.append(copy.deepcopy(value))
  def rehash(report,frozen):
   final[0]=True
   if fault=='final_rehash':raise error
   report['final_input_rehash']={'status':'passed','mismatches':[]}
  def candidate(*args):
   if fault=='interrupt':raise error
   return {'SYNTHETIC_NOT_A_SIGNATURE':True}
  with tempfile.TemporaryDirectory(dir=HERE) as tmp,ExitStack() as stack:
   repo=Path(tmp);package=repo/'pkg';package.mkdir();(repo/'.github/workflows').mkdir(parents=True)
   (repo/'.github/workflows/forge-hosted-pv-metadata-strength.yml').write_text('INERT')
   cfg={'workflow_sha256':'a'*64,'correctness_evidence_sha256':{},'baseline_sha':'1'*40,'candidate_sha':'2'*40,'baseline_benchmark_nodes':321912,'candidate_benchmark_nodes':292545,'seed':20261031}
   (package/'protocol.json').write_text(json.dumps(cfg))
   for name in ['baseline','candidate','fastchess']:(repo/name).write_text('INERT_NOT_EXECUTABLE')
   argv=['test','--repo',str(repo),'--package',str(package),'--baseline',str(repo/'baseline'),'--candidate',str(repo/'candidate'),'--fastchess',str(repo/'fastchess'),'--out',str(repo/'out')]
   for target,name,value in [(sys,'argv',argv),(m,'require_launch_protocol',lambda c:None),(m,'verify_package_inventory',lambda *a:None),(m,'load',load),(m,'sha',sha),(m,'save',save),(m,'ensure_final_inputs',rehash),(m,'host_context',lambda:{}),(m,'candidate_bench_readiness',candidate),(m,'_owned_readiness_probe',lambda *a,**k:{}),(m.signal,'signal',lambda *a:None),(m.os,'sched_getaffinity',lambda pid:set(mask)),(m.os,'sched_setaffinity',affinity)]:stack.enter_context(patch.object(target,name,value))
   stack.enter_context(patch.object(m.subprocess,'Popen',side_effect=AssertionError('No subprocess')))
   stack.enter_context(patch.object(m.subprocess,'run',side_effect=AssertionError('No subprocess')))
   caught=None
   try:m.main()
   except BaseException as actual:caught=actual
  self.assertEqual(calls,[{2},{2,5}], 'Original affinity must be restored after all post-pin exits')
  if not restore_fault:self.assertEqual(mask,{2,5})
  if fault:self.assertIs(caught,error,'Original operation exception must remain primary')
  elif restore_fault:self.assertIs(caught,restoration)
  else:self.assertIsNone(caught)
  if restore_fault and reports:
   self.assertEqual(reports[-1]['status'],'failed_or_inconclusive_no_acceptance')
   self.assertIn('affinity_restore_error',reports[-1])
  if fault and restore_fault:self.assertIs(caught.__cause__,restoration)
 def test_normal(self):self.exercise()
 def test_import(self):self.exercise('import')
 def test_hash(self):self.exercise('hash')
 def test_initial_save(self):self.exercise('initial_save')
 def test_final_rehash(self):self.exercise('final_rehash')
 def test_final_save(self):self.exercise('final_save')
 def test_interrupt(self):self.exercise('interrupt')
 def test_restore_failure_blocks_acceptance(self):self.exercise(restore_fault=True)
 def test_original_exception_preserved_with_restore_failure(self):self.exercise('import',True)
if __name__=='__main__':unittest.main(verbosity=2)
