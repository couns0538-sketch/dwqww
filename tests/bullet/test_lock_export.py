"""Exact lock-schema tests; no inference claim without native parity evidence."""
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'/'bullet'))
import lock_export as le

FEN='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

class LockExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.d=Path(self.tmp.name)
        self.t={'ftw':np.zeros((768,256),dtype=np.float32),'ftb':np.zeros(256,dtype=np.float32),'outw':np.zeros((2,256),dtype=np.float32),'outb':np.array([.25],dtype=np.float32)}
    def tearDown(self):self.tmp.cleanup()
    def checkpoint(self):
        out=self.d/'checkpoint';le.write_checkpoint(out,self.t,'synthetic unit fixture, not trained')
        return le.load_quantized(out/'weights.bin',out/'manifest.json')
    def test_include_roundtrip_exact_tensors(self):
        self.t['ftw'][5,9]=-.125;self.t['outw'][1,13]=.5;q=self.checkpoint()
        p=self.d/'out.inc';p.write_bytes(le.render_include(q));restored=le.parse_include(p)
        for name in q:self.assertTrue(np.array_equal(q[name],restored[name]))
    def test_zero_network_bias_scale(self):
        q=self.checkpoint();cp,bits=le.evaluate(q,FEN)
        self.assertEqual(cp,44);self.assertEqual(bits,struct.unpack('<I',struct.pack('<f',.25))[0])
    def test_activation_clip_and_perspective(self):
        self.t['outb'][:]=0;self.t['ftb'][0]=2;self.t['outw'][0,0]=.125
        q=self.checkpoint();self.assertEqual(le.evaluate(q,FEN)[0],22)
        self.t['ftb'][0]=-2;q2={k:v.copy() for k,v in q.items()};q2['ftb'][0]=-8192
        self.assertEqual(le.evaluate(q2,FEN)[0],0)
    def test_nonfinite_or_shape_reject_before_output(self):
        self.t['outw'][0,1]=float('nan')
        with self.assertRaises(ValueError):le.write_checkpoint(self.d/'bad',self.t,'unit')
        self.assertFalse((self.d/'bad').exists())
    def test_refuse_output_overwrite(self):
        out=self.d/'checkpoint';le.write_checkpoint(out,self.t,'unit')
        with self.assertRaises(FileExistsError):le.write_checkpoint(out,self.t,'unit')
    def test_manifest_for_actual_bullet_layout(self):
        out=self.d/'checkpoint';le.write_checkpoint(out,self.t,'unit')
        p=self.d/'manifest-new.json';m=le.make_manifest(out/'weights.bin',p,'unit attribution')
        self.assertEqual(m['checkpoint_sha256'],le.common.sha256(out/'weights.bin'))
        q=le.load_quantized(out/'weights.bin',p);self.assertEqual(le.evaluate(q,FEN)[0],44)
        with self.assertRaises(FileExistsError):le.make_manifest(out/'weights.bin',p,'unit')
    def test_reject_wrong_architecture(self):
        out=self.d/'checkpoint';m=le.write_checkpoint(out,self.t,'unit');m['architecture']='R10';p=self.d/'wrong.json';p.write_text(json.dumps(m))
        with self.assertRaises(ValueError):le.load_quantized(out/'weights.bin',p)
    def test_corruption_changes_nonzero_weight(self):
        self.t['ftb'][1]=.5;self.t['outw'][0,1]=.25;q=self.checkpoint();changed={k:v.copy() for k,v in q.items()};changed['outw'][1]+=4096
        self.assertNotEqual(le.evaluate(q,FEN)[0],le.evaluate(changed,FEN)[0])

if __name__=='__main__':unittest.main()
