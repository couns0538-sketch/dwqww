"""Disk-budget, disposable-index and binpack streaming regressions."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/data2'))
import convert_dataset as c

FENS = [
 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 | 61 | 0.0\n',
 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1 | -27 | 1.0\n',
]


class DiskTests(unittest.TestCase):
 def setUp(self):
  self.temp = tempfile.TemporaryDirectory(dir='/tmp'); self.addCleanup(self.temp.cleanup)
  self.root = Path(self.temp.name); self.src = self.root/'input.txt'; self.src.write_text(''.join(FENS))
 def args(self, *extra, out='out'):
  return c.parser().parse_args(['convert','--input',str(self.src),'--out',str(self.root/out),'--no-filters','--min-free-mb','0',*(['--accept-gpl3'] if '--binpack-tool' in extra else []),*extra])
 def test_default_reserve_rejects_ten_gib_free(self):
  args = self.args(); args.min_free_mb = c.parser().parse_args(['convert','--input',str(self.src),'--out',str(self.root/'unused')]).min_free_mb
  with mock.patch.object(c.shutil,'disk_usage',return_value=type('Usage',(),{'free':10*1024**3})()):
   with self.assertRaisesRegex(ValueError,'free-space guard'): c.run(args)
  self.assertFalse((self.root/'out'/'COMPLETE.json').exists())
 def test_preflight_budgets_index_before_creation(self):
  prior=self.root/'prior.txt';prior.write_text(FENS[0]*2000)
  with mock.patch.object(c.shutil,'disk_usage',return_value=type('Usage',(),{'free':1024})()):
   with self.assertRaisesRegex(ValueError,'preflight'): c.run(self.args('--dedup-against',str(prior)))
  self.assertFalse(list((self.root/'out').glob('attempt_*/index.sqlite')))
 def test_budget_covers_utf8_game_id_output_bytes(self):
  self.src.write_text(FENS[0]);ids=self.root/'games.txt';ids.write_text('\U0001f600'*256+'\n')
  a=self.args('--game-ids',str(ids));budget=c.disk_budget(a,[]);c.run(a)
  chunk=c.read_chunks(self.root/'out')[0]
  actual=sum((self.root/'out'/chunk[role]).stat().st_size for role in ('text','bullet','provenance'))
  self.assertGreaterEqual(budget['output_bytes_estimate'],actual)
 def test_preflight_reserves_native_probe_log_space(self):
  self.src.write_text(FENS[0]);a=self.args('--shard-id','003');a.no_filters=False;a.probe=str(self.src)
  class Probe:
   def __init__(self,*args,**kwargs):pass
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def query(self,fen,*args):return dict(fen=fen,nodes_limit=1024,threads=1,hash_mb=1,in_check=False,terminal=False,analyzed=True,depth=1,capture=False,promotion=False,bestmove='e2e4')
  with mock.patch.object(c,'ProbeClient',Probe), mock.patch.object(c.shutil,'disk_usage',return_value=type('Usage',(),{'free':1024*1024+1000})()):
   with self.assertRaisesRegex(ValueError,'preflight'):c.run(a)
 def assert_loading_guard(self, option, label):
  prior=self.root/'prior.txt';prior.write_text(FENS[0]*1024+'INVALID\n')
  seen=0; real_key=c.key
  def counted_key(record):
   nonlocal seen
   seen+=1
   return real_key(record)
  def disk_usage(path):
   return type('Usage',(),{'free':0 if seen>=1024 else 1024**3})()
  with mock.patch.object(c,'key',counted_key), mock.patch.object(c.shutil,'disk_usage',disk_usage):
   with self.assertRaisesRegex(ValueError,'loading '+label): c.run(self.args(option,str(prior),'--min-free-mb','1'))
  self.assertFalse((self.root/'out'/'COMPLETE.json').exists())
 def test_holdout_loading_checks_disk_before_next_batch(self):
  self.assert_loading_guard('--holdout','holdout')
 def test_prior_loading_checks_disk_before_next_batch(self):
  self.assert_loading_guard('--dedup-against','prior')
 def prune(self):
  with mock.patch.object(sys,'argv',['convert_dataset.py','verify','--out',str(self.root/'out'),'--prune-indexes']):c.main()
 def test_explicit_verified_cleanup_prunes_only_owned_index(self):
  result=c.run(self.args())
  self.assertEqual(result['counts']['kept'],2)
  self.assertTrue(list((self.root/'out').glob('attempt_*/index.sqlite')))
  self.prune()
  self.assertFalse(list((self.root/'out').glob('attempt_*/index.sqlite')))
  self.assertEqual(self.src.read_text(),''.join(FENS))
  self.assertEqual(c.verify(self.root/'out')['rows'],2)
 def test_checkpoint_resume_recovers_duplicates_then_prunes_indexes(self):
  self.src.write_text(FENS[0]+FENS[1]+FENS[0])
  c.run(self.args('--chunk-rows','1','--stop-after-chunks','1'))
  self.assertTrue(list((self.root/'out').glob('attempt_*/index.sqlite')))
  result=c.run(self.args('--chunk-rows','1','--resume'))
  self.assertEqual(result['counts']['kept'],2);self.assertEqual(result['counts']['duplicate'],1)
  self.assertTrue(list((self.root/'out').glob('attempt_*/index.sqlite')))
  self.prune()
  self.assertFalse(list((self.root/'out').glob('attempt_*/index.sqlite')))
  self.assertEqual(c.run(self.args('--chunk-rows','1','--resume'))['rows'],2)
 def test_corrupt_checkpoint_retains_index(self):
  c.run(self.args('--chunk-rows','1','--stop-after-chunks','1'))
  chunk=c.read_chunks(self.root/'out')[0]
  with (self.root/'out'/chunk['bullet']).open('ab') as f: f.write(b'x')
  with self.assertRaisesRegex(ValueError,'hash mismatch'):c.run(self.args('--chunk-rows','1','--resume'))
  self.assertTrue(list((self.root/'out').glob('attempt_*/index.sqlite')))
 def test_partial_index_is_rebuilt_from_verified_rows(self):
  self.src.write_text(FENS[0]+FENS[1]+FENS[0])
  c.run(self.args('--chunk-rows','1','--stop-after-chunks','1'))
  next((self.root/'out').glob('attempt_*/index.sqlite')).write_bytes(b'interrupted non-durable index')
  result=c.run(self.args('--chunk-rows','1','--resume'))
  self.assertEqual(result['counts']['duplicate'],1);self.assertEqual(result['counts']['kept'],2)
 def test_output_lock_blocks_concurrent_resume(self):
  c.run(self.args('--chunk-rows','1','--stop-after-chunks','1'))
  with c.output_lock(self.root/'out'):
   with self.assertRaisesRegex(ValueError,'locked'):c.run(self.args('--chunk-rows','1','--resume'))
  self.assertFalse((self.root/'out'/'COMPLETE.json').exists())
 def test_verify_prunes_completed_crash_leftovers(self):
  c.run(self.args('--chunk-rows','1','--stop-after-chunks','1'))
  old=next((self.root/'out').glob('attempt_*/index.sqlite'));data=old.read_bytes()
  c.run(self.args('--chunk-rows','1','--resume'));old.write_bytes(data)
  with mock.patch.object(sys,'argv',['convert_dataset.py','verify','--out',str(self.root/'out'),'--prune-indexes']):
   try:c.main()
   except SystemExit as error:self.fail('verify --prune-indexes rejected: '+str(error))
  self.assertFalse(old.exists());self.assertEqual(c.verify(self.root/'out')['rows'],2)
 def test_unowned_legacy_index_is_not_pruned(self):
  c.run(self.args('--chunk-rows','1','--stop-after-chunks','1'))
  old=self.root/'out'/('attempt_'+'a'*32);old.mkdir();(old/'index.sqlite').write_bytes(b'legacy evidence')
  c.run(self.args('--chunk-rows','1','--resume'));self.prune()
  self.assertEqual((old/'index.sqlite').read_bytes(),b'legacy evidence')
 def test_explicit_prune_refuses_symlink_index_without_deleting_target(self):
  c.run(self.args('--chunk-rows','1','--stop-after-chunks','1'))
  index=next((self.root/'out').glob('attempt_*/index.sqlite'));index.unlink();index.symlink_to(self.src)
  c.run(self.args('--chunk-rows','1','--resume'))
  with self.assertRaisesRegex(ValueError,'symlink|unsafe'):self.prune()
  self.assertEqual(self.src.read_text(),''.join(FENS))
 def adapter(self):
  path=self.root/'adapter.py'
  path.write_text('''#!/usr/bin/env python3
import pathlib,sys
assert sys.argv[1]=='encode'
if sys.argv[2]=='-':
 rows=sys.stdin.readlines()
 assert all(row.count('|')==3 and row.rstrip().endswith('e2e4') for row in rows)
else:
 rows=pathlib.Path(sys.argv[2]).read_text().splitlines(True)
pathlib.Path(sys.argv[3]).write_text(''.join(rows))
''')
  path.chmod(0o700);return path
 def test_binpack_format_uses_existing_rows_directly(self):
  result=c.run(self.args('--binpack-tool',str(self.adapter()),'--allow-transport-moves'))
  self.assertEqual(result['binpack'],'GENERATED')
  self.assertFalse(list((self.root/'out').glob('data_*/binpack_input.txt')))
  self.assertEqual(c.verify(self.root/'out')['rows'],2)
 def test_binpack_filtered_stream_preserves_native_bestmove(self):
  self.src.write_text(FENS[0]);a=self.args('--binpack-tool',str(self.adapter()),'--shard-id','003');a.no_filters=False;a.probe=str(self.src)
  class Probe:
   def __init__(self,*args,**kwargs):pass
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def query(self,fen,*args):return dict(fen=fen,nodes_limit=1024,threads=1,hash_mb=1,in_check=False,terminal=False,analyzed=True,depth=1,capture=False,promotion=False,bestmove='e2e4')
  with mock.patch.object(c,'ProbeClient',Probe):result=c.run(a)
  self.assertEqual(result['counts']['kept'],1)
  self.assertFalse(list((self.root/'out').glob('data_*/binpack_input.txt')))
  moves=list((self.root/'out').glob('data_*/bestmoves.txt'));self.assertEqual(len(moves),1)
  self.assertEqual(moves[0].read_text(),'e2e4\n')
  self.assertEqual(moves[0].with_name('rows.binpack').read_text(),FENS[0].rstrip()+' | e2e4\n')
 def decoded_payload(self, payload):
  c.run(self.args('--binpack-tool',str(self.adapter()),'--allow-transport-moves'))
  decoder=self.root/'decoder.py'
  decoder.write_text('#!/usr/bin/env python3\nimport sys\nassert sys.argv[1] == "decode"\nsys.stdout.buffer.write('+repr(payload)+')\n')
  decoder.chmod(0o700)
  return decoder
 def test_binpack_decode_accepts_only_transport_crlf(self):
  decoder=self.decoded_payload(''.join(FENS).encode().replace(b'\n',b'\r\n'))
  try: result=c.verify(self.root/'out',decoder,accept_gpl3=True)
  except ValueError as error:self.fail('valid CRLF decoder transport rejected: '+str(error))
  self.assertEqual(result['binpack_decoded_rows'],2)
 def test_binpack_decode_rejects_changed_value_with_crlf(self):
  decoder=self.decoded_payload(''.join(FENS).encode().replace(b'| 61 |',b'| 62 |').replace(b'\n',b'\r\n'))
  with self.assertRaisesRegex(ValueError,'differs'):c.verify(self.root/'out',decoder,accept_gpl3=True)
 def test_binpack_decode_rejects_embedded_cr_with_crlf(self):
  decoder=self.decoded_payload(''.join(FENS).encode().replace(b'| 61 |',b'| 6\r1 |').replace(b'\n',b'\r\n'))
  with self.assertRaisesRegex(ValueError,'differs'):c.verify(self.root/'out',decoder,accept_gpl3=True)
 def test_binpack_decode_rejects_extra_terminal_cr(self):
  decoder=self.decoded_payload(''.join(FENS).encode().replace(b'\n',b'\r\r\n'))
  with self.assertRaisesRegex(ValueError,'differs'):c.verify(self.root/'out',decoder,accept_gpl3=True)
 def test_binpack_decode_rejects_changed_whitespace(self):
  decoder=self.decoded_payload(''.join(FENS).encode().replace(b' | ',b'  | ',1).replace(b'\n',b'\r\n'))
  with self.assertRaisesRegex(ValueError,'differs'):c.verify(self.root/'out',decoder,accept_gpl3=True)
 def test_binpack_decode_rejects_extra_crlf_row(self):
  decoder=self.decoded_payload((''.join(FENS)+FENS[0]).encode().replace(b'\n',b'\r\n'))
  with self.assertRaisesRegex(ValueError,'extra binpack decoded rows'):c.verify(self.root/'out',decoder,accept_gpl3=True)
 def test_binpack_decode_rejects_unterminated_last_row(self):
  decoder=self.decoded_payload(''.join(FENS).encode().replace(b'\n',b'\r\n').removesuffix(b'\r\n'))
  with self.assertRaisesRegex(ValueError,'differs'):c.verify(self.root/'out',decoder,accept_gpl3=True)


if __name__=='__main__':unittest.main()
