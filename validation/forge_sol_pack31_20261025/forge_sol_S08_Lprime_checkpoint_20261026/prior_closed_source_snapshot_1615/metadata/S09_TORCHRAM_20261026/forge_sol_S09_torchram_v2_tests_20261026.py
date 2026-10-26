"""Reuse toy loader tests; verify new child-only search path and BUILD guards."""
import importlib.util
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import sys

ROOT=Path(__file__).resolve().parent
def load(path,name):
    if not path.exists():return None
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
probe=load(ROOT/'forge_sol_S09_torchram_probe_v2_20261026.py','probe_v2')
controller=load(Path(os.environ.get('FORGE_S09_CONTROLLER_TEST_PATH',str(ROOT/'forge_sol_S09_torchram_controller_v2_20261026.py'))),'controller_v2')
base=load(ROOT/'forge_sol_S09_torchram_tests_20261026.py','toy_contract')
base.tool=probe


class ChildControllerTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(controller,'successor child controller not implemented')
        self.root=Path(tempfile.mkdtemp(prefix='forge_sol_S09_v2toy_',dir=ROOT));self.job=self.root/'job';self.job.mkdir()
        (self.job/'002_build.stdout').write_text('synthetic in-progress BUILD marker')
    def tearDown(self):
        if hasattr(self,'root'):shutil.rmtree(self.root)
    def test_exact_search_path_is_child_only_and_CPU_environment_is_bounded(self):
        before=dict(os.environ);command,env,meta=controller.build_plan(self.root/'out',self.job)
        self.assertEqual(env['LD_LIBRARY_PATH'],str(controller.LIBDIR))
        self.assertEqual(env['CUDA_VISIBLE_DEVICES'],'')
        for key in ['OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS']:self.assertEqual(env[key],'1')
        self.assertEqual(dict(os.environ),before)
        self.assertIn('f023-BUILD',command)
        self.assertEqual(meta['archive_contents_read'],False)
    def test_existing_output_and_completed_BUILD_are_refused(self):
        out=self.root/'out';out.mkdir();(out/'marker').write_text('unchanged')
        with self.assertRaises(ValueError):controller.build_plan(out,self.job)
        bench=self.job/'bench';bench.mkdir();(bench/'processes.json').write_text('[]')
        with self.assertRaises(ValueError):controller.build_plan(self.root/'new_out',self.job)
        self.assertEqual((out/'marker').read_text(),'unchanged')
    def test_probe_source_and_small_dependencies_are_hash_pinned(self):
        _,_,meta=controller.build_plan(self.root/'out',self.job)
        self.assertEqual(len(meta['probe_sha256']),64)
        self.assertEqual(set(meta['dependency_sha256']),{'libgomp-a34b3233.so.1','libc10.so'})
    def test_child_exit_between_poll_and_signal_still_yields_waited_status(self):
        class ExitedChild:
            pid=123456789
            def wait(self,timeout=None):return 0
        with patch.object(controller.os,'killpg',side_effect=ProcessLookupError):
            self.assertEqual(controller.stop_owned_child(ExitedChild()),0)
    def test_BUILD_is_rechecked_after_plan_before_any_child_launch(self):
        out=self.root/'out'
        def plan(*args):
            bench=self.job/'bench';bench.mkdir();(bench/'processes.json').write_text('[]')
            env=os.environ.copy();env.update(LD_LIBRARY_PATH=str(controller.LIBDIR),OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',OMP_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='')
            return [sys.executable,'-B','-c','pass'],env,{}
        with patch.object(controller,'ROOT',self.root),patch.object(controller,'build_plan',side_effect=plan):
            with self.assertRaises(ValueError):controller.run(out,self.job,1)
        self.assertFalse((self.root/'forge_sol_S09_torchram_v2_actual_20261026.stdout').exists())


if __name__=='__main__':
    suite=unittest.TestSuite()
    for name in unittest.defaultTestLoader.getTestCaseNames(base.ToyMemfdTests):
        if name!='test_existing_output_is_refused_before_real_candidate_work':suite.addTest(base.ToyMemfdTests(name))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(ChildControllerTests))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
