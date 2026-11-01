"""Independent normalized-export audit; fixture results are not real holdout clearance."""
import importlib.util,json,hashlib,pathlib,tempfile,unittest,os
from unittest import mock
ROOT=pathlib.Path(__file__).resolve().parents[1]
MODULE=ROOT/'skills/npt-data-holdout-check/scripts/audit_exports.py'
FEN='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
OTHER='rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1'
THIRD='rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3 0 1'
class HoldoutTests(unittest.TestCase):
 def setUp(self):
  self.assertTrue(MODULE.is_file(),'independent auditor missing')
  spec=importlib.util.spec_from_file_location('audit_exports',MODULE);self.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.m)
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=pathlib.Path(self.temp.name)
  self.rows=[dict(row_id='003:0',fen=FEN,game_id='003:g1')]
  self.source=self.write('source',self.rows);self.train=self.write('train',self.rows)
  self.h13=self.write('013',[dict(row_id='013:0',fen=OTHER,game_id='013:g2')]);self.h14=self.write('014',[dict(row_id='014:0',fen=THIRD,game_id='014:g3')])
 def write(self,name,rows):
  p=self.root/(name+'.jsonl');p.write_text(''.join(json.dumps(r)+'\n' for r in rows));return p
 def run_audit(self):
  expected={p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rows':1} for p in (self.h13,self.h14)}
  return self.m.audit(self.source,self.train,[self.h13,self.h14],expected,self.root/'out',0)
 def test_clean_provenance_and_disjoint_ids_pass(self):
  r=self.run_audit();self.assertEqual(r['status'],'PASS');self.assertEqual(r['position_overlap_rows'],0);self.assertEqual(r['game_overlap_rows'],0);self.assertEqual(r['state_mismatch_rows'],0)
 def test_position_overlap_detects_different_clocks_and_rights(self):
  self.h13=self.write('013',[dict(row_id='013:0',fen=FEN.replace('KQkq - 0 1','- - 80 45'),game_id='013:other')]);r=self.run_audit();self.assertEqual(r['status'],'FAIL');self.assertEqual(r['position_overlap_rows'],1)
 def test_game_overlap_across_different_positions_fails(self):
  self.h13=self.write('013',[dict(row_id='013:0',fen=OTHER,game_id='003:g1')]);r=self.run_audit();self.assertEqual(r['status'],'FAIL');self.assertEqual(r['game_overlap_rows'],1)
 def test_missing_game_ids_is_unverified_not_pass(self):
  self.train=self.write('train',[dict(row_id='003:0',fen=FEN,game_id=None)]);self.source=self.write('source',[dict(row_id='003:0',fen=FEN,game_id=None)]);self.assertEqual(self.run_audit()['status'],'UNVERIFIED')
 def test_castling_or_ep_loss_is_rejected(self):
  for original,changed in [(FEN,FEN.replace('KQkq','-')),(OTHER,OTHER.replace(' e3 ',' - '))]:
   with self.subTest(original=original):
    with tempfile.TemporaryDirectory() as out:
     self.source=self.write('source',[dict(row_id='003:0',fen=original,game_id='g1')]);self.train=self.write('train',[dict(row_id='003:0',fen=changed,game_id='g1')]);expected={p.name:dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),rows=1) for p in (self.h13,self.h14)}
     r=self.m.audit(self.source,self.train,[self.h13,self.h14],expected,pathlib.Path(out)/'new',0);self.assertEqual(r['status'],'FAIL');self.assertEqual(r['state_mismatch_rows'],1)
 def test_wrong_trusted_count_or_hash_rejected(self):
  expected={p.name:dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),rows=1) for p in (self.h13,self.h14)};expected[self.h13.name]['rows']=2
  with self.assertRaisesRegex(ValueError,'count'):self.m.audit(self.source,self.train,[self.h13,self.h14],expected,self.root/'out',0)
 def test_existing_output_never_overwritten(self):
  (self.root/'out').mkdir();sentinel=self.root/'out'/'old';sentinel.write_text('preserve')
  with self.assertRaises(FileExistsError):self.run_audit()
  self.assertEqual(sentinel.read_text(),'preserve')
 def test_duplicate_row_id_rejected(self):
  self.source=self.write('source',self.rows*2)
  with self.assertRaisesRegex(ValueError,'duplicate'):self.run_audit()
 def test_replace_train_during_scan_then_restore_original_is_blocked(self):
  # Original train leaks FEN into 013. The transient replacement matches the
  # source and is disjoint, so an unbound scan can falsely clear the old bytes.
  self.source=self.write('source',[dict(row_id='003:0',fen=OTHER,game_id='g1')])
  self.train=self.write('train',[dict(row_id='003:0',fen=FEN,game_id='g1')])
  self.h13=self.write('013',[dict(row_id='013:0',fen=FEN,game_id='holdout:g')])
  original=self.train.read_bytes();real=self.m.records;changed=False
  def replaced(path,guard,*args):
   nonlocal changed
   if path==self.train and not changed:
    changed=True
    saved=self.root/'original-train.saved';self.train.rename(saved)
    self.train.write_text(json.dumps(dict(row_id='003:0',fen=OTHER,game_id='g1'))+'\n')
    try:yield from real(path,guard,*args)
    finally:
     swap=self.root/'temporary-train.saved';self.train.rename(swap);saved.rename(self.train)
   else:yield from real(path,guard,*args)
  with mock.patch.object(self.m,'records',replaced):
   with self.assertRaisesRegex(ValueError,'identity|changed'):self.run_audit()
  self.assertEqual(self.train.read_bytes(),original)
 def test_windows_identity_ignores_only_ctime(self):
  stat=type('Stat',(),dict(st_dev=1,st_ino=2,st_size=3,st_mtime_ns=4,st_ctime_ns=5))()
  with mock.patch.object(self.m,'os',type('OS',(),dict(name='nt'))()):
   a=self.m.identity(stat);stat.st_ctime_ns=99;self.assertEqual(self.m.identity(stat),a)
   stat.st_mtime_ns=10;self.assertNotEqual(self.m.identity(stat),a)
 def test_empty_training_does_not_pass(self):
  self.train=self.write('train',[])
  with self.assertRaisesRegex(ValueError,'empty'):self.run_audit()
if __name__=='__main__':unittest.main()
