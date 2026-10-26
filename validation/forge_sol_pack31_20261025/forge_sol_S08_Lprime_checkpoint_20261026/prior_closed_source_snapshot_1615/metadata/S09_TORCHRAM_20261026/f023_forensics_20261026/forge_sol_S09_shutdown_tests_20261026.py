"""Small protocol tests; no archive, Torch, ctypes or native engine execution."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import signal
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parent
PATH=ROOT/'forge_sol_S09_shutdown_diagnostic_20261026.py'
if PATH.exists():
    spec=importlib.util.spec_from_file_location('shutdown_diag',PATH);tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)
else:tool=None


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(tool,'shutdown diagnostic protocol is not implemented')
        self.root=Path(tempfile.mkdtemp(prefix='forge_sol_S09_diag_toy_',dir=ROOT))
    def tearDown(self):
        if hasattr(self,'root'):shutil.rmtree(self.root)
    def test_functional_PASS_does_not_override_forced_process_failure(self):
        child={'status':'PASS_CPU_MEMFD_S09_PROCESS_ONLY','verified_raw_memfd':True}
        controller={'returncode':-15,'stop_reason':'owned watchdog','archive_contents_read':False}
        original=copy.deepcopy((child,controller))
        result=tool.classify(child,controller)
        self.assertEqual(result['overall'],'FAIL_PROCESS_EXIT')
        self.assertTrue(result['work_complete']);self.assertTrue(result['child_archive_read_verified'])
        self.assertFalse(result['normal_process_exit_observed'])
        self.assertEqual((child,controller),original)
    def test_successful_normal_exit_and_budget_failure_are_distinct(self):
        self.assertEqual(tool.classify({'work_complete':True},{'returncode':0,'stop_reason':None})['overall'],'PASS_DIAGNOSTIC')
        result=tool.classify({'work_complete':False},{'returncode':2,'stop_reason':None})
        self.assertTrue(result['normal_process_exit_observed']);self.assertEqual(result['overall'],'FAIL_WORK')
    def test_work90_hard150_reserve_cleanup_and_cannot_increase_limits(self):
        self.assertEqual(tool.validate_budgets(90,150),60)
        for work,hard in [(91,150),(90,151),(90,119),(0,150)]:
            with self.assertRaises(ValueError):tool.validate_budgets(work,hard)
    def test_cleanup_reserve_ends_at_first_TERM_not_later_KILL(self):
        with self.assertRaises(ValueError):tool.validate_budgets(90,120)
    def test_journal_is_flushed_monotonic_and_ignores_only_partial_tail(self):
        path=self.root/'events.jsonl';fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        try:tool.emit(fd,'first');tool.emit(fd,'second',answer=42)
        finally:os.close(fd)
        events=tool.read_events(path);self.assertEqual([e['event'] for e in events],['first','second'])
        self.assertGreater(events[1]['monotonic_ns'],events[0]['monotonic_ns']);self.assertEqual(events[1]['answer'],42)
        with path.open('ab') as stream:stream.write(b'{"event":')
        self.assertEqual(len(tool.read_events(path)),2)
    def test_proc_snapshot_is_owned_metadata_and_handles_missing_process(self):
        result=tool.proc_snapshot(os.getpid());self.assertTrue(result['alive']);self.assertEqual(result['pid'],os.getpid())
        self.assertIn('Threads',result['status'])
        self.assertFalse(tool.proc_snapshot(999999999)['alive'])
    def test_process_disappearance_during_thread_listing_is_recorded_not_raised(self):
        with patch.object(Path,'iterdir',side_effect=FileNotFoundError('process exited')):
            result=tool.proc_snapshot(os.getpid())
        self.assertFalse(result['alive'])
    def test_short_post_report_window_cannot_qualify_shutdown_observation(self):
        result=tool.classify({'work_complete':True},{'returncode':-15,'stop_reason':'watchdog',
                             'exit_observation_headroom_seconds':1.93454})
        self.assertFalse(result['cleanup_observation_eligible'])
    def test_toy_child_exits_normally_with_phase_and_atexit_markers(self):
        self.assertTrue(hasattr(tool,'monitor_process'),'bounded owned observer missing')
        out=self.root/'toy';out.mkdir();stdout=out/'stdout';stderr=out/'stderr'
        command=[sys.executable,'-B',str(PATH),'--child','--toy-protocol-only','--out',str(out),
                 '--root-authorized-window','TOY_ONLY','--case','autograd','--work-seconds','90']
        with stdout.open('xb') as so,stderr.open('xb') as se:
            process=subprocess.Popen(command,stdout=so,stderr=se,cwd=ROOT,start_new_session=True)
            observed=tool.monitor_process(process,out,10,15)
        self.assertEqual(observed['returncode'],0,stderr.read_text())
        self.assertIsNotNone(observed['main_return_seconds'])
        result=json.loads(stdout.read_text());self.assertTrue(result['toy_protocol_only'])
        events=tool.read_events(out/'events.jsonl');names=[e['event'] for e in events]
        self.assertLess(names.index('MAIN_RETURN'),names.index('PY_ATEXIT_BEFORE_TORCH'))
        self.assertLess(names.index('PY_ATEXIT_BEFORE_TORCH'),names.index('PY_ATEXIT_AFTER_TORCH'))
        self.assertFalse(result['archive_read'])
    def test_external_work_cutoff_does_not_depend_on_native_Python_signal_delivery(self):
        self.assertTrue(tool.work_cutoff_due(90,[],90))
        self.assertFalse(tool.work_cutoff_due(89,[],90))
        self.assertFalse(tool.work_cutoff_due(90,[{'event':'MAIN_RETURN'}],90))
        self.assertFalse(tool.work_cutoff_due(90,[{'event':'WORK_FAILED'}],90))
    def test_observer_IO_error_terminates_and_reaps_only_its_child(self):
        self.assertTrue(hasattr(tool,'monitor_process'),'bounded owned observer missing')
        out=self.root/'error';out.mkdir()
        process=subprocess.Popen([sys.executable,'-B','-c','import time; time.sleep(30)'],start_new_session=True)
        try:
            with patch.object(tool,'read_events',side_effect=OSError('synthetic journal read failure')):
                result=tool.monitor_process(process,out,10,15)
            self.assertIsNotNone(process.poll());self.assertEqual(result['stop_reason'],'observer_error')
        finally:
            if process.poll() is None:os.killpg(process.pid,signal.SIGKILL);process.wait()
    def test_observer_budget_includes_time_before_child_spawn_returns(self):
        class Finished:
            returncode=0
            def poll(self):return 0
            def wait(self,timeout=None):return 0
        observed=tool.monitor_process(Finished(),self.root,90,150,start=time.monotonic()-5)
        self.assertGreaterEqual(observed['elapsed_seconds'],5)
    def test_toy_only_flag_cannot_silently_invoke_real_observer(self):
        with patch.object(tool,'observe',return_value=123):
            with self.assertRaisesRegex(ValueError,'toy'):
                tool.main(['--out',str(self.root/'never'),'--root-authorized-window','TOY_ONLY','--toy-protocol-only'])
    def test_child_mode_cannot_ignore_explicit_plan_only_prohibition(self):
        with patch.object(tool,'child',return_value=123):
            with self.assertRaisesRegex(ValueError,'plan'):
                tool.main(['--out',str(self.root/'never'),'--root-authorized-window','PLAN_ONLY','--child','--plan-only'])


if __name__=='__main__':unittest.main(verbosity=2)
