import contextlib, io, json, os, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest import mock
sys.dont_write_bytecode=True
sys.path.insert(0, '/tmp/forge-astra-fen-convert/tools/data2')
import convert_dataset as c
FEN='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 | 61 | 0.0\n'
FEN2='rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1 | -27 | 1.0\n'
class Independent(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(dir='/tmp/astra-qa-independent-20261030');self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.src=self.root/'input.txt';self.src.write_text(FEN+FEN2)
 def args(self,*extra): return c.parser().parse_args(['convert','--input',str(self.src),'--out',str(self.root/'out'),'--no-filters','--min-free-mb','0',*extra])
 def checkpoint(self):
  c.run(self.args('--chunk-rows','1','--stop-after-chunks','1'))
  return next((self.root/'out').glob('attempt_*/index.sqlite'))
 def test_marker_mismatch_refuses_pruning(self):
  idx=self.checkpoint();marker=idx.with_name('INDEX_OWNER.json');data=json.loads(marker.read_text());data['config_sha256']='0'*64;marker.unlink();marker.write_text(json.dumps(data))
  with self.assertRaisesRegex(ValueError,'ownership/config mismatch'):c.run(self.args('--chunk-rows','1','--resume'))
  self.assertTrue(idx.is_file())
 def test_hardlinked_source_retained(self):
  idx=self.checkpoint();idx.unlink();os.link(self.src,idx)
  with self.assertRaisesRegex(ValueError,'unsafe disposable index'):c.run(self.args('--chunk-rows','1','--resume'))
  self.assertEqual(self.src.read_text(),FEN+FEN2);self.assertTrue(idx.exists())
 def test_source_path_never_pruned(self):
  idx=self.checkpoint();cfg=json.loads((self.root/'out'/'config.json').read_text());cfg['inputs'].append({'path':str(idx.resolve())})
  with self.assertRaisesRegex(ValueError,'unsafe disposable index'):c.prune_owned_indexes(self.root/'out',cfg)
  self.assertTrue(idx.exists())
 def test_other_evidence_retained_after_resume(self):
  idx=self.checkpoint();proof=idx.with_name('keep.log');proof.write_text('original native proof');orphan=self.root/'out'/'data_aborted';orphan.mkdir();(orphan/'rows.txt').write_text('unsealed original')
  c.run(self.args('--chunk-rows','1','--resume'))
  self.assertFalse(idx.exists());self.assertEqual(proof.read_text(),'original native proof');self.assertEqual((orphan/'rows.txt').read_text(),'unsealed original')
 def test_concurrent_process_cannot_acquire_lock(self):
  out=self.root/'out';out.mkdir()
  code='import sys;sys.path.insert(0,"/tmp/forge-astra-fen-convert/tools/data2");import convert_dataset as c;from pathlib import Path\nwith c.output_lock(Path(sys.argv[1])): print("LOCK_ACQUIRED")'
  with c.output_lock(out):
   child=subprocess.run([sys.executable,'-B','-c',code,str(out)],capture_output=True,text=True)
  self.assertNotEqual(child.returncode,0);self.assertIn('locked by another converter/pruner',child.stderr);self.assertNotIn('LOCK_ACQUIRED',child.stdout)
 def test_in_loop_output_disk_guard(self):
  self.src.write_text(FEN*1025);seen=0;real_key=c.key
  def key(record):
   nonlocal seen
   seen+=1;return real_key(record)
  def usage(path):return type('Usage',(),{'free':0 if seen>=1024 else 2**30})()
  with mock.patch.object(c,'key',key),mock.patch.object(c.shutil,'disk_usage',usage):
   with self.assertRaisesRegex(ValueError,'writing output chunk/index'):c.run(self.args('--no-dedupe','--min-free-mb','1'))
  self.assertFalse((self.root/'out'/'COMPLETE.json').exists());self.assertEqual(seen,1024)
 def test_recovered_index_disk_guard(self):
  import itertools
  records=[]
  for first,second in itertools.islice(itertools.combinations([i for i in range(64) if i not in (4,60)],2),1025):
   board=['']*64;board[4]='K';board[60]='k';board[first]='N';board[second]='N';ranks=[]
   for rank in range(7,-1,-1):
    line='';empty=0
    for square in board[rank*8:rank*8+8]:
     if not square:empty+=1
     else:
      if empty:line+=str(empty);empty=0
      line+=square
    if empty:line+=str(empty)
    ranks.append(line)
   records.append('/'.join(ranks)+' w - - 0 1 | 0 | 0.5\n')
  self.src.write_text(''.join(records));c.run(self.args('--chunk-rows','1024','--stop-after-chunks','1','--min-free-mb','1'))
  seen=0;real_key=c.key
  def key(record):
   nonlocal seen
   seen+=1;return real_key(record)
  def usage(path):return type('Usage',(),{'free':0 if seen>=1024 else 2**30})()
  with mock.patch.object(c,'key',key),mock.patch.object(c.shutil,'disk_usage',usage):
   with self.assertRaisesRegex(ValueError,'loading recovered training index'):c.run(self.args('--chunk-rows','1024','--resume','--min-free-mb','1'))
  self.assertFalse((self.root/'out'/'COMPLETE.json').exists());self.assertEqual(seen,1024)
 def test_unicode_budget_covers_retained_output(self):
  self.src.write_text(FEN);ids=self.root/'game_ids.txt';ids.write_text('\U0001f600'*256+'\n')
  args=self.args('--game-ids',str(ids));budget=c.disk_budget(args,[]);c.run(args);chunk=c.read_chunks(self.root/'out')[0]
  actual=sum((self.root/'out'/chunk[role]).stat().st_size for role in ['text','bullet','provenance'])
  self.assertGreaterEqual(budget['output_bytes_estimate'],actual)
 def test_encoder_failure_keeps_unsealed_evidence(self):
  adapter=self.root/'adapter.py';adapter.write_text('#!/usr/bin/env python3\nimport sys\nprint("intentional failure",file=sys.stderr)\nsys.exit(9)\n');adapter.chmod(0o700)
  with self.assertRaises(subprocess.CalledProcessError):c.run(self.args('--binpack-tool',str(adapter),'--allow-transport-moves'))
  self.assertFalse((self.root/'out'/'COMPLETE.json').exists());self.assertTrue(list((self.root/'out').glob('attempt_*/index.sqlite')));self.assertTrue(list((self.root/'out').glob('data_*/binpack.stderr')))
if __name__=='__main__':unittest.main(verbosity=2)
