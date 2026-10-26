import importlib.util
from pathlib import Path
import tempfile
import unittest
import numpy as np

spec=importlib.util.spec_from_file_location('holdout',Path(__file__).with_name('forge_sol_S09_full_holdout_CPU3_20261026.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class FullHoldoutPreparationTests(unittest.TestCase):
    def fixture(self):
        return {'hidden':256,'heads':1,'w1':list(range(768*256)),
            'b1':list(range(256)),'w2':list(range(512)),'b2':[165]}

    def test_inverse_export_layout_and_identical_head_replication(self):
        net=self.fixture();one=m.model_arrays(net,1);eight=m.model_arrays(net,8)
        self.assertEqual(one['ft.weight'].shape,(256,768))
        self.assertEqual(one['ft.weight'][3,7],np.float32(7*256+3)/np.float32(4096))
        self.assertTrue(np.array_equal(one['ft.weight'],eight['ft.weight']))
        self.assertTrue(np.array_equal(one['ft.bias'],eight['ft.bias']))
        for k in range(8):
            self.assertTrue(np.array_equal(one['out.weight'][0],eight['out.weight'][k]))
            self.assertEqual(one['out.bias'][0],eight['out.bias'][k])

    def test_shape_and_head_contract_refuses_wrong_inputs(self):
        for heads in (0,True,2,9):
            with self.assertRaises(ValueError):m.model_arrays(self.fixture(),heads)
        for key,value in [('hidden',128),('heads',8),('w2',[1])]:
            n=self.fixture();n[key]=value
            with self.assertRaises(ValueError):m.model_arrays(n,1)

    def test_source_pin_rejects_changed_input_before_import(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'fixture.py';p.write_text('raise RuntimeError("must never execute")')
            with self.assertRaisesRegex(ValueError,'pinned source changed'):
                m.module(p,'never_import','0'*64)

    def test_full_tail_and_cleanup_reserve_are_explicit(self):
        self.assertEqual(m.ROWS,50000)
        batches=[min(m.BATCH,m.ROWS-i) for i in range(0,m.ROWS,m.BATCH)]
        self.assertEqual(sum(batches),50000)
        self.assertEqual(batches[-1],336)
        self.assertGreaterEqual(m.HARD_SECONDS-m.WORK_SECONDS-2,30)
        self.assertLessEqual(m.BATCH,512)


if __name__=='__main__':unittest.main(verbosity=2)
