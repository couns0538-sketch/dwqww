"""Pure one-wait exit contracts; no Torch or real process/signal here."""
import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('S18_exit_v4',HERE/'forge_sol_S18_train_selected_v4_20261027.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class Process:
    pid=987653
    def __init__(self,rc=0,timeout=False):self.returncode=None;self.target=rc;self.timeout=timeout;self.wait_calls=[]
    def poll(self):return self.returncode
    def wait(self,*,timeout):
        self.wait_calls.append(timeout)
        if self.timeout:raise subprocess.TimeoutExpired('PURE_FIXTURE',timeout)
        self.returncode=self.target;return self.returncode

class ConfirmationTests(unittest.TestCase):
    def missing(self):
        self.assertTrue(hasattr(m,'RSSExitTransition'),'typed exit condition missing')
        return m.RSSExitTransition('PURE genuinely missing own RSS fixture')
    def test_normal_confirmed_exit_returns0_without_signal_or_RSS0(self):
        p=Process();error=self.missing()
        with patch.object(m,'read_rss_bytes',side_effect=error),patch.object(m.os,'killpg') as kill:
            g=m.RSSGuard(p,3*2**30);self.assertEqual(g.poll(),0)
        self.assertEqual(p.wait_calls,[.05]);self.assertIsNone(g.stop_reason);self.assertIsNone(g.max_sampled_rss_bytes)
        self.assertEqual(g.exit_confirmation['outcome'],'CONFIRMED_EXIT');self.assertEqual(g.exit_confirmation['returncode'],0);kill.assert_not_called()
    def test_nonzero_confirmed_exit_returns_actual_nonzero(self):
        p=Process(rc=7);error=self.missing()
        with patch.object(m,'read_rss_bytes',side_effect=error),patch.object(m.os,'killpg') as kill:
            g=m.RSSGuard(p,3*2**30);self.assertEqual(g.poll(),7)
        self.assertEqual(p.wait_calls,[.05]);self.assertEqual(g.exit_confirmation['returncode'],7);kill.assert_not_called()
    def test_nonzero_stays_controller_failure(self):
        from test_forge_sol_S18_postscore_contract_v4_20261027 import exercise_controller
        code,r=exercise_controller(m,lambda r:r,child_returncode=7)
        self.assertNotEqual(code,0);self.assertEqual(r['status'],'FAIL_S18_TRAINING')
    def test_timeout_persistent_unknown_fails_and_waits_only_once(self):
        p=Process(timeout=True);error=self.missing()
        with patch.object(m,'read_rss_bytes',side_effect=error),patch.object(m.os,'killpg') as kill:
            g=m.RSSGuard(p,3*2**30);g.poll();g.poll()
        self.assertEqual(p.wait_calls,[.05]);self.assertEqual(g.stop_reason,'RSS_UNAVAILABLE');self.assertEqual(g.exit_confirmation['outcome'],'TIMEOUT')
        self.assertIsNone(g.max_sampled_rss_bytes);self.assertTrue(kill.called)
    def test_denied_malformed_or_identity_error_never_waits(self):
        for error in [PermissionError('denied'),ValueError('malformed owned VmRSS'),ValueError('owned task Pid/Tgid mismatch'),FileNotFoundError('UNCLASSIFIED arbitrary file')]:
            with self.subTest(error=repr(error)):
                p=Process()
                with patch.object(m,'read_rss_bytes',side_effect=error),patch.object(m.os,'killpg'):
                    g=m.RSSGuard(p,3*2**30);g.poll()
                self.assertEqual(p.wait_calls,[]);self.assertEqual(g.stop_reason,'RSS_UNAVAILABLE')
    def test_genuine_owned_proc_disappearance_is_typed(self):
        self.assertTrue(hasattr(m,'RSSExitTransition'))
        with patch.object(m,'read_proc_status',side_effect=FileNotFoundError('/proc/987653/status')):
            with self.assertRaises(m.RSSExitTransition):m.read_rss_bytes(987653)
    def test_R_missing_RSS_is_typed_without_R_task_fallback(self):
        self.assertTrue(hasattr(m,'RSSExitTransition'))
        raw='Name:\tPURE\nState:\tR (running)\nTgid:\t987653\nPid:\t987653\n'
        with patch.object(m,'read_proc_status',return_value=raw),patch.object(m,'owned_task_ids',side_effect=AssertionError('no R fallback')):
            with self.assertRaises(m.RSSExitTransition):m.read_rss_bytes(987653)
    def test_positive_3GiB_limit_and_low_limit_still_enforced_without_wait(self):
        for limit,expected in [(3*2**30,None),(100,'RSS_LIMIT')]:
            with self.subTest(limit=limit):
                p=Process()
                with patch.object(m,'read_rss_bytes',return_value=200),patch.object(m.os,'killpg'):
                    g=m.RSSGuard(p,limit);g.poll()
                self.assertEqual(g.stop_reason,expected);self.assertEqual(p.wait_calls,[]);self.assertEqual(g.max_sampled_rss_bytes,200)
    def test_invalid_wait_result_stays_unknown(self):
        p=Process();p.wait=lambda **kwargs:None;error=self.missing()
        with patch.object(m,'read_rss_bytes',side_effect=error),patch.object(m.os,'killpg'):
            g=m.RSSGuard(p,3*2**30);g.poll()
        self.assertEqual(g.stop_reason,'RSS_UNAVAILABLE');self.assertEqual(g.exit_confirmation['outcome'],'INVALID_WAIT_RESULT')

if __name__=='__main__':unittest.main()
