import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import forge_sol_datafilter_v2_20261026 as codec
PATH=ROOT/'forge_sol_S17_gamesplit_20261026.py'
tool=None
if PATH.exists():
    spec=importlib.util.spec_from_file_location('s17',PATH)
    tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)

A=['7k/8/8/8/8/8/P7/K7 w - - 0 1 | 10 | 1',
   '7k/8/8/8/8/8/P7/1K6 b - - 1 1 | 11 | 1',
   '6k1/8/8/8/8/8/P7/1K6 w - - 2 2 | 12 | 1']
B=['7k/8/8/8/8/8/1P6/K7 w - - 0 1 | 20 | 0',
   '7k/8/8/8/8/8/1P6/1K6 b - - 1 1 | 21 | 0']
C=['7k/8/8/8/8/8/2P5/K7 w - - 0 1 | 30 | 0.5',
   '7k/8/8/8/8/8/2P5/1K6 b - - 1 1 | 31 | 0.5']

class GameSplit(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(tool,'S17 game-split implementation missing')
        self.root=Path(tempfile.mkdtemp(prefix='forge_sol_S17_fixture_',dir=ROOT))
        self.data=self.root/'inputs';self.data.mkdir()
        self.work=self.root/'scratch';self.work.mkdir()
    def tearDown(self):
        if hasattr(self,'root'):
            for p in self.root.rglob('*'):
                if p.is_file():p.chmod(0o600)
            shutil.rmtree(self.root)
    def source(self,name,lines,ids=None,crlf=False):
        pos=self.data/(name+'.pos');text=self.data/(name+'.txt')
        records=[]
        for i,line in enumerate(lines):
            row,_=codec.text_record(line);records.append(codec.Record(row.board,row.score,row.meta,10+i))
        codec.write_records(pos,pos.with_suffix('.hce'),records)
        text.write_bytes(('\r\n' if crlf else '\n').join(lines).encode()+ (b'\r\n' if crlf else b'\n'))
        source={'name':name,'pos':pos,'text':text}
        if ids is not None:
            q=self.data/(name+'.ids');q.write_text(''.join(x+'\n' for x in ids));source['game_ids']=q
        for p in self.data.iterdir():p.chmod(0o444)
        return source
    def split(self,sources,name='out',production=False,**kw):
        return tool.split_sources(sources,self.root/name,self.work,seed=20261026,
                                  validation_basis_points=2500,production=production,**kw)
    def hashes(self,name):
        return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (self.root/name).iterdir() if p.is_file()}
    def ledger(self,name='out'):
        return [json.loads(x) for x in (self.root/name/'forge_sol_S17_row_selection_20261026.jsonl').read_text().splitlines()]
    def test_multifile_group_continuation_never_resets_at_shard(self):
        first=self.source('first',A[:2]);second=self.source('second',A[2:]+B+C)
        summary=self.split([first,second]);rows=self.ledger()
        self.assertEqual(summary['groups'],3)
        self.assertEqual(len({r['group'] for r in rows[:3]}),1)
        self.assertEqual(len({r['assigned_split'] for r in rows[:3]}),1)
        self.assertEqual(summary['cross_split_defined_groups'],0)
        self.assertFalse(summary['game_overlap_verified'])
        self.assertIn('UNVERIFIED',summary['authentic_game_overlap'])
    def test_authoritative_ids_positive_multifile_and_binary_roundtrip(self):
        first=self.source('first',A[:2],['gameA']*2);second=self.source('second',A[2:]+B+C,['gameA']+['gameB']*2+['gameC']*2)
        summary=self.split([first,second],production=True,game_id_provenance='Owned synthetic fixture game identities')
        self.assertTrue(summary['game_overlap_verified']);self.assertEqual(summary['authentic_game_overlap'],0)
        self.assertEqual(summary['binary_output_status'],'WRITTEN_WITH_PROVIDED_HCE')
        observed=[]
        for p in (self.root/'out').glob('*.pos'):observed.extend(codec.read_records(p,p.with_suffix('.hce')))
        expected=[]
        for s in (first,second):expected.extend(codec.read_records(s['pos'],s['pos'].with_suffix('.hce')))
        self.assertCountEqual(observed,expected)
    def test_production_missing_ids_rejected_before_output(self):
        source=self.source('first',A+B+C)
        with self.assertRaisesRegex(ValueError,'authoritative'):
            self.split([source],production=True)
        self.assertFalse((self.root/'out').exists());self.assertFalse(list(self.work.iterdir()))
    def test_synchronized_interleaving_reopened_ids_is_rejected(self):
        lines=[A[0],B[0].replace('| 0','| 1'),A[1],B[1].replace('| 0','| 1')]
        source=self.source('interleaved',lines,['a','b','a','b'])
        with self.assertRaisesRegex(ValueError,'interleaved|reopened'):
            self.split([source],production=True,game_id_provenance='Planted interleaved fixture IDs')
    def test_duplicate_positions_never_cross_split_and_ledger_accounts_every_row(self):
        source=self.source('first',A+B+[A[0].replace('| 10 | 1','| 90 | 0.5')]+C)
        summary=self.split([source]);rows=self.ledger()
        self.assertEqual(len(rows),8);self.assertEqual(summary['input_rows'],8)
        self.assertGreater(summary['dropped_rows'],0);self.assertEqual(summary['cross_split_position_overlap'],0)
        self.assertEqual(summary['retained_rows']+summary['dropped_rows'],8)
    def test_repeat_every_file_byte_identical_and_outputs_sealed(self):
        source=self.source('first',A+B+C)
        self.split([source],name='one');self.split([source],name='two')
        self.assertEqual(self.hashes('one'),self.hashes('two'))
        self.assertTrue(all(p.stat().st_mode&0o222==0 for p in (self.root/'one').iterdir()))
    def test_existing_out_and_source_bytes_never_modified(self):
        source=self.source('first',A+B+C);out=self.root/'out';out.mkdir();(out/'keep').write_text('unchanged')
        before={p.name:p.read_bytes() for p in self.data.iterdir()}
        with self.assertRaises(FileExistsError):self.split([source])
        self.assertEqual((out/'keep').read_text(),'unchanged')
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.data.iterdir()})
    def test_manifest_scans_every_sealed_shard_and_reports_whole_duplicate(self):
        source=self.source('first',A+B+C);sealed=self.root/'sealed';sealed.mkdir()
        for ext in ('.pos','.hce'):shutil.copy2(source['pos'].with_suffix(ext),sealed/('copy'+ext))
        summary=self.split([source],sealed_dirs=[sealed])
        manifest=[json.loads(x) for x in (self.root/'out'/'forge_sol_S17_shard_dedupe_20261026.jsonl').read_text().splitlines()]
        self.assertEqual(len(manifest),2)
        self.assertEqual(sum(r['records'] for r in manifest),14)
        self.assertEqual(summary['sealed_manifest']['whole_shard_duplicates'],1)
        self.assertEqual(summary['sealed_manifest']['duplicate_positions'],7)
    def test_empty_declared_sealed_directory_rejected(self):
        source=self.source('first',A+B+C);empty=self.root/'empty';empty.mkdir()
        with self.assertRaisesRegex(ValueError,'empty'):self.split([source],sealed_dirs=[empty])
    def test_text_binary_mismatch_fails_with_unsealed_marker(self):
        source=self.source('first',A+B+C);source['text'].chmod(0o600);source['text'].write_text('\n'.join([A[0].replace('| 10 |','| 99 |')]+A[1:]+B+C)+'\n');source['text'].chmod(0o444)
        with self.assertRaisesRegex(ValueError,'mismatch'):self.split([source])
        self.assertTrue((self.root/'out'/'forge_sol_S17_FAILED_UNSEALED_20261026.json').exists())
    def test_missing_HCE_is_never_filled_with_placeholder(self):
        source=self.source('first',A+B+C);source['pos'].with_suffix('.hce').unlink()
        summary=self.split([source]);self.assertEqual(summary['binary_output_status'],'UNVERIFIED_MISSING_HCE')
        self.assertFalse(list((self.root/'out').glob('*.pos')))
        self.assertFalse(list((self.root/'out').glob('*.hce')))
    def test_crlf_text_content_is_preserved(self):
        source=self.source('first',A+B+C,crlf=True);self.split([source])
        rows=[]
        for part in ('train','validation'):
            text=(self.root/'out'/('forge_sol_S17_'+part+'_20261026.txt')).read_bytes()
            self.assertNotIn(b'\n',text.replace(b'\r\n',b''));rows.extend(text.splitlines())
        self.assertCountEqual(rows,[s.encode() for s in A+B+C])
    def test_scratch_allocation_failure_is_explicitly_unsealed(self):
        source=self.source('first',A+B+C)
        with patch.object(tool.tempfile,'mkdtemp',side_effect=OSError('planted unavailable scratch')):
            with self.assertRaisesRegex(OSError,'scratch'):self.split([source])
        marker=self.root/'out'/'forge_sol_S17_FAILED_UNSEALED_20261026.json'
        self.assertTrue(marker.exists(),'failed scratch setup must not leave an ambiguous new output directory')
    def test_unterminated_input_row_does_not_merge_records_across_files(self):
        first=self.source('first',A);second=self.source('second',B+C)
        first['text'].chmod(0o600);first['text'].write_bytes(first['text'].read_bytes().rstrip(b'\n'));first['text'].chmod(0o444)
        try:summary=self.split([first,second])
        except ValueError as error:self.fail('valid final source row must remain a separate output record: '+str(error))
        self.assertEqual(summary['retained_rows'],7)
        observed=[]
        for part in ('train','validation'):
            data=(self.root/'out'/('forge_sol_S17_'+part+'_20261026.txt')).read_bytes()
            if data:self.assertTrue(data.endswith(b'\n'))
            observed.extend(data.splitlines())
        self.assertCountEqual(observed,[s.encode() for s in A+B+C])

if __name__=='__main__':unittest.main()
