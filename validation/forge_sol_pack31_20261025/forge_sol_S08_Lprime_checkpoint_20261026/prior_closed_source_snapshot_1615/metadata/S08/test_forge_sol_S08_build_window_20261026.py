"""Build-window supervision fixtures; Python children only, no compiler/Forge."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

MODULE=Path(__file__).with_name('forge_sol_S08_build_window_20261026.py')


class WindowTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(MODULE.is_file(),'owned build-window supervisor is missing')
        spec=importlib.util.spec_from_file_location('s08window',MODULE)
        self.api=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.api)

    def job(self,root):
        job=Path(root)/'SYNTHETIC_S26_BUILD';job.mkdir()
        (job/'build').mkdir();(job/'progress.json').write_text('{}\n')
        return job

    def test_real_bench_directory_is_a_fail_closed_boundary(self):
        # Catches trusting stale declared phase rather than actual bench startup.
        with tempfile.TemporaryDirectory() as root:
            job=self.job(root);deadline=time.monotonic()+20
            self.assertIsNone(self.api.boundary_reason(job,deadline))
            (job/'bench').mkdir()
            self.assertEqual(self.api.boundary_reason(job,deadline),'S26_BENCH_BOUNDARY')

    def test_missing_build_or_expired_owned_deadline_blocks_launch(self):
        with tempfile.TemporaryDirectory() as root:
            job=self.job(root)
            self.assertEqual(self.api.boundary_reason(job,time.monotonic()-1),'OWNED_DEADLINE')
            (job/'build').rmdir()
            self.assertEqual(self.api.boundary_reason(job,time.monotonic()+20),'S26_NOT_FRESH_BUILD')

    def test_boundary_kills_owned_python_group_and_retains_raw_prefix(self):
        # A running synthetic child must close promptly when bench appears.
        with tempfile.TemporaryDirectory() as root:
            job=self.job(root);out=Path(root)/'receipt';out.mkdir()
            trigger=threading.Timer(.2,lambda:(job/'bench').mkdir());trigger.start()
            try:
                receipt=self.api.run_owned([sys.executable,'-u','-c','import time; print("SYNTHETIC prefix",flush=True); time.sleep(5)'],out,'boundary',job,time.monotonic()+10)
            finally:trigger.join()
            self.assertEqual(receipt['stop_reason'],'S26_BENCH_BOUNDARY')
            self.assertNotEqual(receipt['returncode'],0)
            self.assertEqual(receipt['running_group_members_after_close'],[])
            self.assertIn(b'SYNTHETIC prefix',(out/'boundary.stdout').read_bytes())
            self.assertTrue((out/'boundary.receipt.json').is_file())

    def test_global_deadline_retains_completed_command_and_stops_next(self):
        # Catches granting a fresh full timeout to each target.
        with tempfile.TemporaryDirectory() as root:
            job=self.job(root);out=Path(root)/'receipt';out.mkdir()
            deadline=time.monotonic()+1.4
            first=self.api.run_owned([sys.executable,'-c','print("SYNTHETIC done")'],out,'first',job,deadline)
            self.assertEqual(first['returncode'],0)
            second=self.api.run_owned([sys.executable,'-c','import time; time.sleep(5)'],out,'second',job,deadline)
            self.assertEqual(second['stop_reason'],'OWNED_DEADLINE')
            self.assertEqual(second['running_group_members_after_close'],[])

    def test_target_resume_is_ordered_and_bound_to_frozen_inputs(self):
        # Catches silently skipping an unfinished target or changing build roots.
        targets=list(self.api.TARGETS)
        old={'build_dir':'/tmp/example-build','source_freeze_sha256':'abc','completed_targets':targets[:2]}
        self.assertEqual(self.api.pending_targets(old,'/tmp/example-build','abc'),targets[2:])
        for bad in ({**old,'completed_targets':[targets[1]]},{**old,'source_freeze_sha256':'other'},{**old,'build_dir':'/tmp/other'}):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                self.api.pending_targets(bad,'/tmp/example-build','abc')

    def test_all_target_list_contains_engine_and_real_profile_fixture(self):
        # Fixed targets compile only; no ctest/run/profile commands are targets.
        self.assertEqual(len(self.api.TARGETS),12)
        self.assertEqual(self.api.TARGETS[:2],('forge','forge_prof_tests'))
        self.assertNotIn('test',self.api.TARGETS)

    def test_source_mutation_during_paused_window_returns_failure(self):
        # A pause cannot hide a failed final source-integrity check behind rc0.
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);job=self.job(root);source=root/'source';source.mkdir()
            source_file=source/'fixture.txt';source_file.write_text('SYNTHETIC original\n')
            compiler=root/'not_a_compiler';compiler.write_text('SYNTHETIC identity only\n')
            freeze=root/'freeze.json';freeze.write_text(json.dumps({'source':str(source),
                'source_sha256':self.api.snapshot(source),'compiler_sha256':self.api.sha(compiler)}))
            window=root/'window';build=window/'build'
            def pause_without_launch(*args,**kwargs):
                source_file.write_text('SYNTHETIC changed\n')
                return {'stop_reason':'S26_BENCH_BOUNDARY','returncode':None}
            with mock.patch.object(self.api,'CXX',compiler),mock.patch.object(self.api,'CXX_SHA',self.api.sha(compiler)), \
                 mock.patch.object(self.api,'run_owned',side_effect=pause_without_launch), \
                 mock.patch.object(self.api.os,'sched_getaffinity',return_value={0}), \
                 mock.patch.object(self.api.os,'getpriority',return_value=19):
                rc=self.api.main(['--execute','--s26-job',str(job),'--window-dir',str(window),
                    '--build-dir',str(build),'--source-freeze',str(freeze),
                    '--authorization-reference','SYNTHETIC fixture only'])
            stored=json.loads((window/'forge_sol_S08_ON_build_result_20261026.json').read_text())
            self.assertEqual(stored['status'],'FAIL_BUILD_ONLY')
            self.assertFalse(stored['source_unchanged'])
            self.assertEqual(rc,1)


if __name__=='__main__':unittest.main(verbosity=2)
