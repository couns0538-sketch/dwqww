"""Real owned-worker interruption fixture; no production job is touched."""
import importlib.util,pathlib,tempfile,unittest,json
from unittest import mock
ROOT=pathlib.Path(__file__).resolve().parents[1];MODULE=ROOT/'skills/resumable-shard-job/scripts/resume_fixture.py'
class ResumeTests(unittest.TestCase):
 def setUp(self):
  self.assertTrue(MODULE.is_file(),'resume proof helper missing')
  s=importlib.util.spec_from_file_location('resume_fixture',MODULE);self.m=importlib.util.module_from_spec(s);s.loader.exec_module(self.m)
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=pathlib.Path(self.tmp.name)
  self.inputs=[]
  for index in range(3):
   path=self.root/f'shard-{index}.txt';path.write_bytes(b'a\nb\nc\n'+str(index).encode()+b'\n');self.inputs.append(path)
 def test_real_terminated_worker_resume_matches_uninterrupted(self):
  r=self.m.selftest(self.root/'proof');self.assertEqual(r['status'],'PASS');self.assertEqual(r['full_md5'],r['resumed_md5']);self.assertTrue(r['owned_worker_terminated']);self.assertGreater(r['retained_partial_files'],0)
 def test_natural_completion_race_is_not_interruption_proof(self):
  def completed(command,**kwargs):
   root=pathlib.Path(command[command.index('--fixture-root')+1]);run=root/'interrupted'
   self.m.run([root/f'input_{n:03}.txt' for n in range(3)],run)
   class Child:
    code=None
    def poll(self):return self.code
    def terminate(self):pass
    def wait(self,timeout=None):self.code=0;return 0
    def kill(self):self.code=-9
   return Child()
  with mock.patch.object(self.m.subprocess,'Popen',side_effect=completed):
   with self.assertRaisesRegex(RuntimeError,'normally|interruption'):self.m.selftest(self.root/'race')
 def test_completed_next_shard_is_not_counted_as_partial(self):
  out=self.root/'completed';out.mkdir();(out/'checkpoint_000001.json').write_text('{}');(out/'stage_shard_000001_fixture').write_bytes(b'x'*65)
  self.assertTrue(hasattr(self.m,'verify_interruption'),'interruption boundary validator missing')
  with self.assertRaisesRegex(RuntimeError,'incomplete|checkpoint'):self.m.verify_interruption(out,-15,65)
 def test_existing_output_requires_explicit_resume(self):
  self.m.run(self.inputs,self.root/'run')
  before={p.name:p.read_bytes() for p in (self.root/'run').iterdir() if p.is_file()}
  with self.assertRaises(FileExistsError):self.m.run(self.inputs,self.root/'run')
  self.assertEqual(before,{p.name:p.read_bytes() for p in (self.root/'run').iterdir() if p.is_file()})
 def test_completed_resume_keeps_same_bytes(self):
  a=self.m.run(self.inputs,self.root/'run');before={p.name:p.read_bytes() for p in (self.root/'run').iterdir() if p.is_file()}
  b=self.m.run(self.inputs,self.root/'run',True);self.assertEqual(a,b)
  self.assertEqual(before,{p.name:p.read_bytes() for p in (self.root/'run').iterdir() if p.is_file()})
 def test_changed_source_refuses_resume(self):
  self.m.run(self.inputs,self.root/'run');self.inputs[0].write_bytes(b'changed\n')
  with self.assertRaisesRegex(ValueError,'configuration'):self.m.run(self.inputs,self.root/'run',True)
 def test_corrupted_sealed_shard_refuses_resume(self):
  self.m.run(self.inputs,self.root/'run');(self.root/'run'/'shard_000000.bin').write_bytes(b'corrupt')
  with self.assertRaisesRegex(ValueError,'hash'):self.m.run(self.inputs,self.root/'run',True)
if __name__=='__main__':unittest.main()
