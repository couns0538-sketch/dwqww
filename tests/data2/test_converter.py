"""Original converter regression tests, including interruption and bad seals."""
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/data2'))
import convert_dataset as c
from bullet_records import encode, verify_record
from forge_pos import text_record, PosWriter

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
 def test_summary_counts_corruption_rejected(self):
  c.run(self.args());p=self.root/'out'/'COMPLETE.json';data=json.loads(p.read_text());data['counts']['in_check']=400;p.write_text(json.dumps(data))
  with self.assertRaisesRegex(ValueError,'aggregate counts'):c.verify(self.root/'out')
 def test_summary_chunk_count_corruption_rejected(self):
  c.run(self.args());p=self.root/'out'/'COMPLETE.json';data=json.loads(p.read_text());data['chunks']=999;p.write_text(json.dumps(data))
  with self.assertRaisesRegex(ValueError,'chunk-count'):c.verify(self.root/'out')
 def test_unknown_count_corruption_rejected(self):
  c.run(self.args());p=self.root/'out'/'COMPLETE.json';data=json.loads(p.read_text());data['counts']['unreported_drop']=1;p.write_text(json.dumps(data))
  with self.assertRaisesRegex(ValueError,'counts keys'):c.verify(self.root/'out')
 def test_bool_count_rejected(self):
  with self.assertRaises(ValueError):c.checked_counts({'kept':True})
 def test_data_role_must_be_hashed(self):
  c.run(self.args());p=self.root/'out'/'chunk_000000.json';data=json.loads(p.read_text());data['text']='../input.txt';p.write_text(json.dumps(data))
  with self.assertRaisesRegex(ValueError,'data role'):c.verify(self.root/'out')
 def test_requested_binpack_cannot_disappear(self):
  c.run(self.args());p=self.root/'out'/'config.json';data=json.loads(p.read_text());data['binpack_tool']='declared_adapter';p.write_text(json.dumps(data))
  p=self.root/'out'/'COMPLETE.json';data=json.loads(p.read_text());data['binpack']='GENERATED';p.write_text(json.dumps(data))
  with self.assertRaisesRegex(ValueError,'required binpack'):c.verify(self.root/'out')
 def test_retargeted_symlink_cannot_seal_wrong_source(self):
  link=self.root/'alias.txt';link.symlink_to(self.src);other=self.root/'other.txt';other.write_text(FENS[1]);a=self.args();a.input=str(link)
  original=c.sources
  def retarget_then_read(args):
   link.rename(self.root/'old_alias.txt');link.symlink_to(other)
   yield from original(args)
  with mock.patch.object(c,'sources',retarget_then_read):
   with self.assertRaisesRegex(ValueError,'binding changed'):c.run(a)
  self.assertFalse((self.root/'out'/'COMPLETE.json').exists())
  chunk=c.read_chunks(self.root/'out')[0]
  self.assertEqual((self.root/'out'/chunk['text']).read_text(),''.join(FENS))
 def test_holdout_all_overlap_zero_remain(self):
  result=c.run(self.args('--holdout',str(self.src)))
  self.assertEqual(result['counts']['holdout_position'],3); self.assertEqual(c.verify(self.root/'out')['rows'],0)
 def test_game_exclusion_removes_distinct_position(self):
  hold=self.root/'hold.txt';hold.write_text(FENS[0]); hgid=self.root/'hgame.txt';hgid.write_text('gameA\n')
  gid=self.root/'games.txt';gid.write_text('gameA\ngameA\ngameB\n')
  result=c.run(self.args('--holdout',str(hold),'--holdout-game-ids',str(hgid),'--game-ids',str(gid),'--require-game-clearance','--shard-id','003'))
  self.assertEqual(result['counts']['holdout_game'],2);self.assertEqual(result['counts']['kept'],1)
 def test_absent_shard_id_cannot_claim_split(self):
  with self.assertRaisesRegex(ValueError,'game clearance'):c.run(self.args('--require-game-clearance'))
 def test_holdout_shard_rejected(self):
  with self.assertRaisesRegex(ValueError,'holdout shard'):c.run(self.args('--shard-id','013'))
 def test_accepted_shard_split_no_invented_game_ids(self):
  result=c.run(self.args('--shard-id','003','--require-game-clearance'))
  self.assertEqual(result['game_clearance'],'ACCEPTED_WHOLE_SHARD_SPLIT_013_014')
  self.assertFalse(result['game_id_exclusion'])
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
 def test_prior_training_result_does_not_change_identity(self):
  prior=self.root/'prior.txt';prior.write_text(FENS[0].replace('61 | 0.0','-44 | 1.0'))
  result=c.run(self.args('--dedup-against',str(prior)))
  self.assertEqual(result['counts']['duplicate'],1);self.assertEqual(result['counts']['holdout_position'],0)
  self.assertEqual(result['prior_training_index']['rows_indexed'],1);self.assertEqual(result['prior_training_index']['unique_keys'],1)
 def test_prior_training_fpos(self):
  writer=PosWriter(self.root/'prior','previous',False)
  writer.append(text_record(FENS[0])[0]);writer.seal();writer.close()
  result=c.run(self.args('--dedup-against',str(self.root/'prior'/'previous.pos')))
  self.assertEqual(result['counts']['duplicate'],1);self.assertEqual(result['counts']['kept'],2)
 def test_prior_training_stm_distinct(self):
  prior=self.root/'prior.txt';prior.write_text(FENS[0]);self.src.write_text(FENS[0].replace(' w ',' b '))
  self.assertEqual(c.run(self.args('--dedup-against',str(prior)))['counts']['kept'],1)
 def test_prior_training_holdout_counts_separate(self):
  prior=self.root/'prior.txt';prior.write_text(FENS[0]);hold=self.root/'hold.txt';hold.write_text(FENS[1])
  result=c.run(self.args('--dedup-against',str(prior),'--holdout',str(hold)))
  self.assertEqual(result['counts']['duplicate'],1);self.assertEqual(result['counts']['holdout_position'],1);self.assertEqual(result['counts']['kept'],1)
 def test_prior_training_resume_and_input_change(self):
  prior=self.root/'prior.txt';prior.write_text(FENS[0])
  c.run(self.args('--dedup-against',str(prior),'--chunk-rows','1','--stop-after-chunks','1'))
  result=c.run(self.args('--dedup-against',str(prior),'--chunk-rows','1','--resume'))
  self.assertEqual(result['counts']['duplicate'],1);self.assertEqual(result['counts']['kept'],2)
  prior.write_text(FENS[1])
  with self.assertRaisesRegex(ValueError,'identity mismatch'):c.run(self.args('--dedup-against',str(prior),'--chunk-rows','1','--resume'))
 def test_prior_training_no_dedupe_conflict(self):
  with self.assertRaisesRegex(ValueError,'cannot be combined'):c.run(self.args('--dedup-against',str(self.src),'--no-dedupe'))
 def test_prior_training_impossible_summary_rejected(self):
  c.run(self.args('--dedup-against',str(self.src)));p=self.root/'out'/'COMPLETE.json';data=json.loads(p.read_text());data['prior_training_index']['unique_keys']=1000;p.write_text(json.dumps(data))
  with self.assertRaisesRegex(ValueError,'key count invalid'):c.verify(self.root/'out')
 def test_filter_requires_native_proof(self):
  a=self.args();a.no_filters=False
  with self.assertRaisesRegex(ValueError,'requires --probe'):c.run(a)
 def test_manifest_commit_exclusive(self):
  p=self.root/'seal.json';c.dump_new(p,{'x':1})
  with self.assertRaises(FileExistsError):c.dump_new(p,{'x':2})
  self.assertEqual(json.loads(p.read_text()),{'x':1})

if __name__=='__main__':unittest.main()
