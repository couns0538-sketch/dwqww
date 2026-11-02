"""Adapter fixtures only; preserve attempts under the launcher's TEMP."""
import argparse
import pathlib
import json
import shutil
import struct
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import parity_adapter as adapter


class WeightImageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=pathlib.Path('D:/a10/c1/src/nnue_weights.inc').read_bytes()
        cls.image,cls.spans=adapter.weights(cls.data)

    def test_complete_image_layout(self):
        self.assertEqual(len(self.image),2*(196608+256+512+1))
        self.assertEqual(self.spans['NnueW2']['offset'],2*(196608+256))
        self.assertEqual(struct.unpack_from('<h',self.image,self.spans['NnueW2']['offset'])[0],self.spans['NnueW2']['values'][0])

    def test_one_w2_mutation_changes_only_its_two_bytes(self):
        tensor=self.spans['NnueW2'];old=tensor['values'][0];new=old+4096 if old+4096<=32767 else old-4096
        lo,hi=tensor['tokens'][0]
        changed=self.data[:lo]+str(new).encode()+self.data[hi:]
        image,_=adapter.weights(changed)
        diffs=[i for i,(x,y) in enumerate(zip(self.image,image)) if x!=y]
        self.assertTrue(diffs)
        self.assertTrue(all(tensor['offset']<=i<tensor['offset']+2 for i in diffs))
        self.assertEqual(struct.unpack_from('<h',image,tensor['offset'])[0],new)

    def test_wrong_array_count_refused(self):
        changed=self.data.replace(b'NnueW2[512]',b'NnueW2[511]',1)
        with self.assertRaisesRegex(ValueError,'NnueW2'): adapter.weights(changed)

    def test_out_of_range_int16_refused(self):
        lo,hi=self.spans['NnueW2']['tokens'][0]
        changed=self.data[:lo]+b'32768'+self.data[hi:]
        with self.assertRaisesRegex(ValueError,'range'): adapter.weights(changed)

    def test_path_traversal_refused(self):
        with self.assertRaises(ValueError): adapter.own('D:/a10/../outside')

    def test_new_json_refuses_overwrite(self):
        path=pathlib.Path(tempfile.mkdtemp(prefix='adapter-fixture-'))/'receipt.json'
        adapter.new_json(path,{'first':1})
        with self.assertRaises(FileExistsError): adapter.new_json(path,{'later':2})

    def test_compiler_path_fix_is_child_local(self):
        original={'PATH':'D:\\fixture-tools','TEMP':'D:\\a10\\tmp','OTHER':'kept'}
        environment=adapter.compiler_environment(original)
        self.assertEqual(original['PATH'],'D:\\fixture-tools')
        self.assertEqual(environment['PATH'],'C:\\msys64\\ucrt64\\bin;D:\\fixture-tools')
        self.assertEqual(environment['TEMP'],original['TEMP'])
        self.assertEqual(environment['OTHER'],'kept')

    def test_source_drift_refused_before_preparation(self):
        root=pathlib.Path(tempfile.mkdtemp(prefix='source-drift-fixture-'))
        source=root/'source';shutil.copytree('D:/a10/c1',source)
        with (source/'src/nnue.cpp').open('ab') as f: f.write(b'\n// Deliberate source drift fixture\n')
        args=SimpleNamespace(source=source,source_manifest='D:/a10/wt/astra_r9/evidence/c1-source.json',
                             fens='D:/a10/inputs/fens_12k.txt',out=root/'prepared',negative_source=root/'negative',seed=3771096103)
        with self.assertRaisesRegex(ValueError,'authoritative source'):
            adapter.prepare(args)
        self.assertFalse(args.out.exists())

    def test_prepared_fens_path_validated_before_hash_read(self):
        root=pathlib.Path(tempfile.mkdtemp(prefix='path-fixture-'));path=root/'prepared.json'
        path.write_text(json.dumps({'fens':'C:/fixture-must-not-be-read','harness':'D:/a10/fixture','fens_sha256':adapter.FENS_SHA}))
        with patch.object(adapter,'sha',side_effect=AssertionError('unvalidated path read')):
            with self.assertRaises(ValueError): adapter.load_prepared(path)

    def test_prepared_harness_path_validated_before_hash_read(self):
        root=pathlib.Path(tempfile.mkdtemp(prefix='path-fixture-'));path=root/'prepared.json'
        path.write_text(json.dumps({'fens':'D:/a10/inputs/fens_12k.txt','harness':'C:/fixture-must-not-be-read','fens_sha256':adapter.FENS_SHA}))
        def checked_sha(p):
            if pathlib.Path(p)==pathlib.Path('D:/a10/inputs/fens_12k.txt'): return adapter.FENS_SHA
            raise AssertionError('unvalidated harness read')
        with patch.object(adapter,'sha',side_effect=checked_sha):
            with self.assertRaises(ValueError): adapter.load_prepared(path)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--threads',required=True,type=int,choices=[1]);ap.parse_args()
    unittest.main(argv=['test_adapter'],verbosity=2)
