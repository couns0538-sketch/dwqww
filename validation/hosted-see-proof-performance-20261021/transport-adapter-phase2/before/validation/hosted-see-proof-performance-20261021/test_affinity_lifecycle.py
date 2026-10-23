"""Actual performance main AST; all expensive operations and affinity are inert.
Faults prove unconditional restoration. No engine/process/import of packet code.
"""
import argparse,ast,copy,json,os,signal,sys,tempfile,time,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
SOURCE=Path(os.environ.get('LIFECYCLE_RUNNER',str(HERE/'template-originals/run_hosted.py')))
class Injected(RuntimeError):pass
class Lifecycle(unittest.TestCase):
 def exercise(self,fault=None,restore_fault=False):
  tree=ast.parse(SOURCE.read_text());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
  restore_error=Injected('injected restoration failure');reports=[]
  error=Injected('injected '+str(fault));mask={2,5};restores=[];pinned=[False];hosts=[0]
  def pin(cpu):mask.clear();mask.add(cpu);pinned[0]=True
  def restore(pid,new):
   restores.append(set(new))
   if restore_fault:raise restore_error
   mask.clear();mask.update(new)
  def context():
   hosts[0]+=1
   if hosts[0]==2 and fault=='final_context':raise error
   return {}
  def rehash(frozen):
   if fault=='final_rehash':raise error
   return {'status':'passed','mismatches':[],'observed':frozen}
  def save(path,value):
   reports.append(copy.deepcopy(value))
   if fault=='final_save' and pinned[0] and hosts[0]==2:raise error
  def experiment(cfg,base,cand,out,cpu,deadline,report):report['status']='completed_gain_pending_final_integrity'
  common=types.SimpleNamespace(save=save,require_ready=lambda c:None,inventory=lambda *a:[],proof_paths=lambda *a:[],transport_paths=lambda *a:[],snapshot=lambda p:{'inert':{'sha256':'a'*64,'mode':420}},sha=lambda p:'a'*64,WORKFLOW='workflow',host_context=context,rehash=rehash)
  ns=dict(argparse=argparse,json=json,os=os,signal=signal,time=time,Path=Path,common=common,owned=types.SimpleNamespace(pin_cpu=pin),analysis=object(),evidence=types.SimpleNamespace(verify_build_evidence=lambda *a:[]),run_experiment=experiment)
  with tempfile.TemporaryDirectory(dir=HERE) as tmp:
   repo=Path(tmp);(repo/'protocol.json').write_text(json.dumps({'workflow_sha256':'a'*64}));(repo/'baseline').write_text('INERT');(repo/'candidate').write_text('INERT');ns['HERE']=repo
   argv=['test','--repo',str(repo),'--baseline',str(repo/'baseline'),'--candidate',str(repo/'candidate'),'--out',str(repo/'out')]
   exec(compile(ast.fix_missing_locations(ast.Module(body=[main],type_ignores=[])),str(SOURCE),'exec'),ns)
   caught=None
   with patch.object(sys,'argv',argv),patch.dict(os.environ,{'GITHUB_RUN_ATTEMPT':'1'}),patch.object(os,'sched_getaffinity',lambda p:set(mask)),patch.object(os,'sched_setaffinity',restore),patch.object(signal,'signal',lambda *a:None):
    try:ns['main']()
    except BaseException as e:caught=e
  self.assertEqual(restores,[{2,5}],'Every post-pin exit must attempt original-affinity restoration')
  if not restore_fault:self.assertEqual(mask,{2,5})
  if restore_fault:
   self.assertFalse(reports[-1]['verified_hosted_gain']);self.assertIn('affinity_restore_error',reports[-1])
  if fault:self.assertIs(caught,error,'Preserve original operation exception')
  elif restore_fault:self.assertIs(caught,restore_error)
  else:self.assertIsNone(caught)
  if fault and restore_fault:self.assertIs(caught.__cause__,restore_error)
 def test_restore_failure_invalidates_gain(self):self.exercise(restore_fault=True)
 def test_original_hash_error_preserved_with_restore_failure(self):self.exercise('final_rehash',True)
 def test_normal(self):self.exercise()
 def test_final_rehash_failure(self):self.exercise('final_rehash')
 def test_final_context_failure(self):self.exercise('final_context')
 def test_final_save_failure(self):self.exercise('final_save')
if __name__=='__main__':unittest.main(verbosity=2)
