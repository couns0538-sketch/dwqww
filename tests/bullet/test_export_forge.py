"""Original tests of the documented Bullet checkpoint and Forge R10 contracts."""
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys
import tempfile
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools' / 'bullet'))
import export_forge as ef
import make_checkpoint_fixture as mf

START = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

class CheckpointTests(unittest.TestCase):
    def test_rounding_contract(self):
        a = np.array([-1.5, -.5, .5, 1.5], dtype=np.float32)
        self.assertEqual(ef.quantize(a, 1, 'nearest_ties_away', 'i1').tolist(), [-2,-1,1,2])
        self.assertEqual(ef.quantize(a, 1, 'truncate', 'i1').tolist(), [-1,0,0,1])
    def test_nonfinite_and_overflow(self):
        for x in [float('nan'), float('inf'), 128, -129]:
            with self.subTest(x=x), self.assertRaises(ValueError):
                ef.quantize(np.array([x], dtype=np.float32), 1, 'truncate', 'i1')
    def test_float64_scaling_before_round(self):
        a = np.array([.1], dtype=np.float32)
        self.assertEqual(ef.quantize(a, 10, 'truncate', 'i4').item(), 1)
    def test_checkpoint_ids_counts_and_size(self):
        valid = b'abc\n' + struct.pack('<Qf', 1, .25)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'weights.bin'; p.write_bytes(valid)
            self.assertEqual(ef.read_checkpoint(p)['abc'].tolist(), [.25])
            for content in [valid[:-1], valid+valid, b'abc', b'abc\n'+struct.pack('<Q',2**63), b'\xff\n'+struct.pack('<Q',0), b'\n'+struct.pack('<Q',0)]:
                p.write_bytes(content)
                with self.subTest(content=content[:20]), self.assertRaises(ValueError): ef.read_checkpoint(p)
    def test_truncation_matches_cpp(self):
        for a,b,want in [(-17,16,-1),(17,16,1),(-1,16,0),(-32769,32768,-1)]:
            self.assertEqual(ef.trunc_div(a,b),want)
    def test_fen_orientation_and_buckets(self):
        board, stm = ef.parse_fen(START)
        self.assertEqual(stm,0)
        self.assertEqual(ef.feature_indices(board,0),ef.feature_indices(board,1))
        self.assertEqual(ef.stack_index(board,stm),31)
        for fen in ['',START.replace(' w ',' x '),START.replace('rnbqkbnr','rnbqkbn9'),START.replace('KBNR','QBNR'),START.replace(' 0 1',' -1 1')]:
            with self.subTest(fen=fen), self.assertRaises(ValueError): ef.parse_fen(fen)

class ExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.d=Path(cls.tmp.name)
        ef.create_fixture(cls.d/'fixture', 19)
        cls.checkpoint=cls.d/'fixture'/'weights.bin';cls.manifest=cls.d/'fixture'/'manifest.json'
        cls.net=ef.load_quantized(cls.checkpoint,cls.manifest)
    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()
    def test_export_header_hash_and_size(self):
        payload=ef.serialize(self.net)
        version,nethash,descsize=struct.unpack_from('<III',payload)
        self.assertEqual(version,0x6A448AFA)
        self.assertEqual(nethash,ef.fc_hash(64,32,32)^0xAB005CEF^128)
        self.assertEqual(struct.unpack_from('<I',payload,12+descsize)[0],0xAB005CEF^128)
        self.assertEqual(len(payload),12+descsize+4+2*64+67584*64+32*(4+4*32+32*64+4*32+32*64+4+128))
    def test_column_major_dense_transpose(self):
        ck=ef.read_checkpoint(self.checkpoint)
        expected=ck['l1w'].reshape((1024,64),order='F')[:32]
        self.assertTrue(np.array_equal(self.net.tensors['l1w'][0],expected))
    def test_native_net_checkpoint_roundtrip(self):
        payload=ef.serialize(self.net);p=self.d/'bridge.nnue';p.write_bytes(payload)
        destination=self.d/'bridge-checkpoint'
        result=mf.import_fixture(p,destination,64,32,32)
        self.assertEqual(result['status'],'SYNTHETIC_CHECKPOINT_NOT_BULLET_TRAINED')
        restored=ef.load_quantized(destination/'weights.bin',destination/'manifest.json')
        self.assertEqual(ef.serialize(restored),payload)
        with self.assertRaises(FileExistsError):mf.import_fixture(p,destination,64,32,32)
    def test_native_net_bad_header_reject(self):
        p=self.d/'bad.nnue';p.write_bytes(b'x'*100)
        with self.assertRaises(ValueError):mf.import_fixture(p,self.d/'bad-out',64,32,32)
    def test_reference_deterministic_and_not_constant(self):
        fs=[START, START.replace(' w ',' b '), '7k/8/8/8/8/8/P7/K7 w - - 0 1']
        out=[ef.evaluate(self.net,f) for f in fs]
        self.assertGreater(len(set(out)),1)
        self.assertEqual(out,[ef.evaluate(self.net,f) for f in fs])
    def test_manifest_checksum_and_arch_reject(self):
        original=json.loads(self.manifest.read_text())
        for field,value in [('checkpoint_sha256','0'*64),('architecture','stock_bullet_768'),('usize_bytes',4),('bullet_commit','main')]:
            m=dict(original);m[field]=value;p=self.d/(field+'.json');p.write_text(json.dumps(m))
            with self.subTest(field=field), self.assertRaises(ValueError):ef.load_quantized(self.checkpoint,p)
    def test_no_overwrite(self):
        out=self.d/'existing.nnue';out.write_bytes(b'keep')
        with self.assertRaises(FileExistsError):ef.write_new(out, b'new')
        self.assertEqual(out.read_bytes(),b'keep')
    def test_one_active_output_weight_changes_eval(self):
        payload=ef.serialize(self.net)
        changed,record=ef.corrupt_active_weight(self.net,payload,START)
        self.assertEqual(sum(a!=b for a,b in zip(payload,changed)),1)
        self.assertNotEqual(record['raw_before'],record['raw_after'])
        self.assertEqual(record['kind'],'single_output_weight_byte')
    def test_exact_comparison_rejects_corruption_and_line_count(self):
        for a,b in [(['1 0'],['2 0']),(['1 0'],[]),([],[])]:
            with self.subTest(a=a,b=b),self.assertRaises(ValueError):ef.compare_eval_lines(a,b)
        self.assertEqual(ef.compare_eval_lines(['-17 -1','16 1'],['-17 -1','16 1']),2)
    def test_bounds_reject_ft_and_dense(self):
        ft=self.net.tensors['ftb'];old=ft[0].copy();ft[0]=32767
        with self.assertRaises(ValueError):ef.validate_bounds(self.net)
        ft[0]=old
        b=self.net.tensors['l1b'];old=b[0,0].copy();b[0,0]=2**31-1
        with self.assertRaises(ValueError):ef.validate_bounds(self.net)
        b[0,0]=old

if __name__=='__main__':unittest.main()
