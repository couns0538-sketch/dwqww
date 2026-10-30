"""Original converter regression tests, including interruption and bad seals."""
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/data2'))
import convert_dataset as c
from bullet_records import encode, verify_record
from forge_pos import text_record

FENS = [
 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 | 61 | 0.0\n',
 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1 | -27 | 1.0\n',
 'rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2 | 20 | 0.5\n',
]


class ConverterTests(unittest.TestCase):
 def setUp(self):
  self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
  self.root = Path(self.temp.name); self.src = self.root/'input.txt'; self.src.write_text(''.join(FENS))
 def args(self, *extra, out='out'):
  return c.parser().parse_args(['convert','--input',str(self.src),'--out',str(self.root/out),'--no-filters','--min-free-mb','0',*extra])
 def test_black_normalization_score_result(self):
  r,_=text_record(FENS[1]); raw=encode(r)
  self.assertEqual(len(raw),32); self.assertEqual(struct.unpack_from('<h',raw,24)[0],-27)
  self.assertEqual(raw[26],0); self.assertEqual(raw[27],4); self.assertEqual(raw[28],4)
 def test_corrupt_weight_detected(self):
  r,_=text_record(FENS[0]); raw=bytearray(encode(r)); raw[24]^=1
  with self.assertRaises(ValueError): verify_record(raw,r)
 def test_exact_roundtrip(self):
  result=c.run(self.args('--no-dedupe')); self.assertEqual(result['counts']['kept'],3)
  self.assertEqual(c.verify(self.root/'out')['rows'],3)
  chunk=c.read_chunks(self.root/'out')[0]
  self.assertEqual((self.root/'out'/chunk['text']).read_text(),''.join(FENS))
 def test_resume(self):
  first=self.args('--chunk-rows','1','--stop-after-chunks','1')
  self.assertEqual(c.run(first)['status'],'CHECKPOINT')
  result=c.run(self.args('--chunk-rows','1','--resume'))
  self.assertEqual(result['counts']['kept'],3); self.assertEqual(c.verify(self.root/'out')['rows'],3)
 def test_resume_nodedupe_duplicates(self):
  self.src.write_text(FENS[0]*3)
  c.run(self.args('--no-dedupe','--chunk-rows','1','--stop-after-chunks','1'))
  self.assertEqual(c.run(self.args('--no-dedupe','--chunk-rows','1','--resume'))['counts']['kept'],3)
 def test_resume_source_mutation_rejected(self):
  c.run(self.args('--stop-after-chunks','1','--chunk-rows','1')); self.src.write_text(FENS[0])
  with self.assertRaisesRegex(ValueError,'identity mismatch'): c.run(self.args('--chunk-rows','1','--resume'))
 def test_existing_output_never_overwritten(self):
  c.run(self.args())
  with self.assertRaises(FileExistsError): c.run(self.args())
 def test_sealed_corruption_rejected(self):
  c.run(self.args()); chunk=c.read_chunks(self.root/'out')[0]
  with (self.root/'out'/chunk['bullet']).open('ab') as f:f.write(b'x')
  with self.assertRaisesRegex(ValueError,'hash mismatch'): c.verify(self.root/'out')
 def test_holdout_all_overlap_zero_remain(self):
  result=c.run(self.args('--holdout',str(self.src)))
  self.assertEqual(result['counts']['holdout_position'],3); self.assertEqual(c.verify(self.root/'out')['rows'],0)
 def test_game_exclusion_removes_distinct_position(self):
  hold=self.root/'hold.txt';hold.write_text(FENS[0]); hgid=self.root/'hgame.txt';hgid.write_text('gameA\n')
  gid=self.root/'games.txt';gid.write_text('gameA\ngameA\ngameB\n')
  result=c.run(self.args('--holdout',str(hold),'--holdout-game-ids',str(hgid),'--game-ids',str(gid),'--require-game-clearance'))
  self.assertEqual(result['counts']['holdout_game'],2);self.assertEqual(result['counts']['kept'],1)
 def test_absent_game_ids_cannot_claim_production(self):
  with self.assertRaisesRegex(ValueError,'game clearance'):c.run(self.args('--require-game-clearance'))
 def test_truncated_game_ids(self):
  gid=self.root/'games.txt';gid.write_text('A\n')
  with self.assertRaisesRegex(ValueError,'truncated'):c.run(self.args('--game-ids',str(gid)))
  self.assertFalse((self.root/'out'/'COMPLETE.json').exists())
 def test_extra_game_ids(self):
  gid=self.root/'games.txt';gid.write_text('A\nB\nC\nD\n')
  with self.assertRaisesRegex(ValueError,'extra'):c.run(self.args('--game-ids',str(gid)))
 def test_dedup_ignores_clocks_rights_by_policy(self):
  self.src.write_text(FENS[0]+FENS[0].replace('KQkq - 0 1','- - 2 3'))
  result=c.run(self.args());self.assertEqual(result['counts']['duplicate'],1)
 def test_filter_requires_native_proof(self):
  a=self.args();a.no_filters=False
  with self.assertRaisesRegex(ValueError,'requires --probe'):c.run(a)
 def test_manifest_commit_exclusive(self):
  p=self.root/'seal.json';c.dump_new(p,{'x':1})
  with self.assertRaises(FileExistsError):c.dump_new(p,{'x':2})
  self.assertEqual(json.loads(p.read_text()),{'x':1})

if __name__=='__main__':unittest.main()
