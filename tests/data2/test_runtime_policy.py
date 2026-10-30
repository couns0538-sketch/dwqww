"""Explicit runtime opt-ins; original small fixtures, no production data."""
import contextlib, io, json, pathlib, subprocess, sys, tempfile, unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]/'tools/data2'))
import convert_dataset as c
FEN='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 | 61 | 0.0\n'

class RuntimePolicy(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.root=pathlib.Path(self.temp.name);self.src=self.root/'in.txt';self.src.write_text(FEN*2)
  self.out=self.root/'out';self.tool=self.root/'adapter.py';self.tool.write_text('#!/usr/bin/env python3\nraise SystemExit("must not run")\n');self.tool.chmod(0o700)
 def args(self,*extra):
  return c.parser().parse_args(['convert','--input',str(self.src),'--out',str(self.out),'--no-filters','--min-free-mb','0',*extra])
 def convert(self,*extra):
  with contextlib.redirect_stdout(io.StringIO()): return c.run(self.args(*extra))
 def test_acknowledged_external_tool_is_accepted(self):
  self.assertEqual(c.external_binpack_tool(self.tool,True),str(self.tool.resolve()))
 def test_empty_git_placeholder_is_not_a_repository(self):
  (self.root/'.git').mkdir()
  self.assertEqual(c.external_binpack_tool(self.tool,True),str(self.tool.resolve()))
 def test_bare_repository_tool_is_rejected(self):
  (self.root/'HEAD').write_text('ref: refs/heads/main\n');(self.root/'objects').mkdir()
  args=self.args('--binpack-tool',str(self.tool),'--allow-transport-moves');args.accept_gpl3=True
  with self.assertRaisesRegex(ValueError,'outside'):c.run(args)
  self.assertFalse(self.out.exists())
 def test_symlink_dotdot_cannot_check_outside_then_execute_inside_repo(self):
  repo=self.root/'repo';repo.mkdir();(repo/'.git').mkdir();(repo/'.git'/'HEAD').write_text('ref: refs/heads/test\n');(repo/'.git'/'objects').mkdir()
  (repo/'subdir').mkdir();(repo/'adapter.py').write_text('must not run')
  (self.root/'link').symlink_to(repo/'subdir',target_is_directory=True)
  original=str(self.root/'link'/'..'/'adapter.py')
  self.assertEqual(pathlib.Path(original).resolve(),repo/'adapter.py')
  args=self.args('--binpack-tool',original,'--allow-transport-moves');args.accept_gpl3=True
  with self.assertRaisesRegex(ValueError,'outside'):c.run(args)
  self.assertFalse(self.out.exists())
 def test_completion_retains_index_until_explicit_verify_prune(self):
  self.convert(); indexes=list(self.out.glob('attempt_*/index.sqlite'));self.assertEqual(len(indexes),1)
  before={p:p.read_bytes() for p in indexes};c.verify(self.out)
  self.assertEqual(before,{p:p.read_bytes() for p in indexes})
  result=subprocess.run([sys.executable,str(pathlib.Path(c.__file__)),'verify','--out',str(self.out),'--prune-indexes'],capture_output=True,text=True)
  self.assertEqual(result.returncode,0,result.stderr);self.assertGreater(json.loads(result.stdout)['pruned_index_bytes'],0)
  self.assertFalse(list(self.out.glob('attempt_*/index.sqlite')));self.assertEqual(c.verify(self.out)['rows'],1)
 def test_resume_never_deletes_prior_indexes_implicitly(self):
  self.convert('--chunk-rows','1','--stop-after-chunks','1');old=next(self.out.glob('attempt_*/index.sqlite'));before=old.read_bytes()
  result=self.convert('--chunk-rows','1','--resume');self.assertEqual(result['counts']['duplicate'],1)
  self.assertEqual(old.read_bytes(),before);self.assertEqual(len(list(self.out.glob('attempt_*/index.sqlite'))),2)
  self.convert('--chunk-rows','1','--resume');self.assertEqual(old.read_bytes(),before)
 def test_convert_requires_gpl_ack_before_output_created(self):
  with self.assertRaisesRegex(ValueError,'accept-gpl3'):self.convert('--binpack-tool',str(self.tool),'--allow-transport-moves')
  self.assertFalse(self.out.exists())
 def test_verify_requires_gpl_ack_before_adapter_runs(self):
  self.convert()
  with self.assertRaisesRegex(ValueError,'accept-gpl3'):c.verify(self.out,self.tool)
 def test_accepted_adapter_must_be_outside_repository(self):
  (self.root/'.git').mkdir();(self.root/'.git'/'HEAD').write_text('ref: refs/heads/test\n');(self.root/'.git'/'objects').mkdir()
  args=self.args('--binpack-tool',str(self.tool),'--allow-transport-moves');args.accept_gpl3=True
  with self.assertRaisesRegex(ValueError,'outside'):c.run(args)
  self.assertFalse(self.out.exists())
 def test_symlink_into_repository_is_rejected(self):
  repo=self.root/'nested';repo.mkdir();(repo/'.git').write_text('gitdir: elsewhere');target=repo/'adapter';target.write_text('not executed')
  alias=self.root/'link';alias.symlink_to(target)
  args=self.args('--binpack-tool',str(alias),'--allow-transport-moves');args.accept_gpl3=True
  with self.assertRaisesRegex(ValueError,'outside'):c.run(args)
  self.assertFalse(self.out.exists())
 def test_repository_symlink_to_external_tool_is_rejected(self):
  repo=self.root/'nested';repo.mkdir();(repo/'.git').mkdir();(repo/'.git'/'HEAD').write_text('ref: refs/heads/test\n');(repo/'.git'/'objects').mkdir();alias=repo/'link';alias.symlink_to(self.tool)
  args=self.args('--binpack-tool',str(alias),'--allow-transport-moves');args.accept_gpl3=True
  with self.assertRaisesRegex(ValueError,'outside'):c.run(args)
  self.assertFalse(self.out.exists())
 def test_verify_repository_tool_is_rejected_even_with_gpl_ack(self):
  self.convert();(self.root/'.git').mkdir();(self.root/'.git'/'HEAD').write_text('ref: refs/heads/test\n');(self.root/'.git'/'objects').mkdir()
  try:
   with self.assertRaisesRegex(ValueError,'outside'):c.verify(self.out,self.tool,accept_gpl3=True)
  except TypeError as e:self.fail('verify needs explicit GPL runtime gate: '+str(e))
 def test_verify_cli_requires_ack_without_modifying_output(self):
  self.convert();before={p:p.read_bytes() for p in self.out.rglob('*') if p.is_file()}
  result=subprocess.run([sys.executable,str(pathlib.Path(c.__file__)),'verify','--out',str(self.out),'--binpack-tool',str(self.tool)],capture_output=True,text=True)
  self.assertNotEqual(result.returncode,0);self.assertIn('accept-gpl3',result.stderr)
  self.assertEqual(before,{p:p.read_bytes() for p in self.out.rglob('*') if p.is_file()})

if __name__=='__main__':unittest.main()
