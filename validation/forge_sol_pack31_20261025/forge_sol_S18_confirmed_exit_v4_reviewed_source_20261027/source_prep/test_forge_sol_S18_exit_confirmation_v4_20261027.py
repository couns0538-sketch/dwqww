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
    def test_malformed_State_never_attempts_confirmation(self):
        for state in ['garbage','RR','?','0','']:
            with self.subTest(state=state):
                p=Process();raw=f'Name:\tPURE\nState:\t{state}\nTgid:\t987653\nPid:\t987653\n'
                with patch.object(m,'read_proc_status',return_value=raw),patch.object(m.os,'killpg'):
                    g=m.RSSGuard(p,3*2**30);g.poll()
                self.assertEqual(p.wait_calls,[]);self.assertEqual(g.stop_reason,'RSS_UNAVAILABLE')
                self.assertIsNone(g.exit_confirmation);self.assertIsNone(g.max_sampled_rss_bytes)
                self.assertEqual(g.last_rss_observation['leader_status_original'],raw)
    def test_actual_t200_unavailable_capture_is_retained_without_running_leader_fallback(self):
        raw=(HERE/'forge_sol_S18_t200_v3_unavailable_leader_original_20261027.status').read_text()
        p=Process();p.pid=280643
        with patch.object(m,'read_proc_status',return_value=raw),patch.object(m,'owned_task_ids',side_effect=AssertionError('no R fallback')),patch.object(m.os,'killpg') as kill:
            g=m.RSSGuard(p,3*2**30);self.assertEqual(g.poll(),0);self.assertEqual(g.poll(),0)
        self.assertEqual(p.wait_calls,[.05]);kill.assert_not_called();self.assertIsNone(g.max_sampled_rss_bytes)
        self.assertEqual(g.last_rss_observation['scope'],'UNAVAILABLE');self.assertNotIn('rss_bytes',g.last_rss_observation)
        self.assertEqual(g.last_rss_observation['leader_status_original'],raw)
        self.assertEqual(g.exit_confirmation['outcome'],'CONFIRMED_EXIT');self.assertFalse(g.exit_confirmation['rss_synthesized'])
    def test_real_parser_wrong_ids_and_malformed_RSS_never_attempt_confirmation(self):
        good='Name:\tPURE\nState:\tR (running)\nTgid:\t987653\nPid:\t987653\n'
        for raw in [good.replace('Tgid:\t987653','Tgid:\t1'),good.replace('Pid:\t987653','Pid:\t1'),good+'VmRSS:\tbad kB\n',good+'VmRSS:\t-1 kB\n',good+'VmRSS:\t1 MB\n',good+'State:\tR (running)\n']:
            with self.subTest(raw=raw):
                p=Process()
                with patch.object(m,'read_proc_status',return_value=raw),patch.object(m.os,'killpg'):
                    g=m.RSSGuard(p,3*2**30);g.poll()
                self.assertEqual(p.wait_calls,[]);self.assertEqual(g.stop_reason,'RSS_UNAVAILABLE');self.assertIsNone(g.exit_confirmation)
    def test_wait_exception_failsclosed_and_does_not_retry(self):
        p=Process();error=self.missing()
        def fail(**kwargs):p.wait_calls.append(kwargs['timeout']);raise ChildProcessError('PURE wait unavailable')
        p.wait=fail
        with patch.object(m,'read_rss_bytes',side_effect=error),patch.object(m.os,'killpg'):
            g=m.RSSGuard(p,3*2**30);g.poll();g.poll()
        self.assertEqual(p.wait_calls,[.05]);self.assertEqual(g.stop_reason,'RSS_UNAVAILABLE');self.assertEqual(g.exit_confirmation['outcome'],'WAIT_ERROR')
    def test_controller_rejects_actual_nonzero_confirmed_exit(self):
        from test_forge_sol_S18_postscore_contract_v4_20261027 import exercise_controller
        code,r=exercise_controller(m,lambda r:r,child_returncode=7,confirm_missing_rss=True)
        self.assertNotEqual(code,0);self.assertEqual(r['status'],'FAIL_S18_TRAINING')
        self.assertEqual(r['arms']['none']['RSS_guard']['exit_confirmation']['outcome'],'CONFIRMED_EXIT')
        self.assertEqual(r['arms']['none']['RSS_guard']['exit_confirmation']['returncode'],7)
    def test_AST_only_observer_and_receipt_scope_changes_from_v3(self):
        import ast
        old=ast.parse(Path('/tmp/forge_sol_S18_RSS_SCOPE_V3_PREP_20261027/forge_sol_S18_train_selected_v3_20261027.py').read_text())
        new=ast.parse((HERE/'forge_sol_S18_train_selected_v4_20261027.py').read_text())
        self.assertEqual(len(new.body),len(old.body)+1)
        self.assertEqual([n.name for n in new.body if isinstance(n,ast.ClassDef)],['RSSExitTransition','RSSGuard'])
        old_rest=[n for n in old.body if not isinstance(n,(ast.FunctionDef,ast.ClassDef))]
        new_rest=[n for n in new.body if not isinstance(n,(ast.FunctionDef,ast.ClassDef))]
        self.assertEqual([ast.dump(n) for n in old_rest],[ast.dump(n) for n in new_rest])
        for a in old.body:
            if not isinstance(a,(ast.FunctionDef,ast.ClassDef)) or a.name in ('read_rss_bytes','RSSGuard','run_controller'):continue
            b=next(n for n in new.body if isinstance(n,type(a)) and n.name==a.name)
            self.assertEqual(ast.dump(a),ast.dump(b),a.name)
        a=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name=='run_controller')
        b=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=='run_controller')
        removals=0
        for node in ast.walk(b):
            if isinstance(node,ast.Dict):
                for i in range(len(node.keys)-1,-1,-1):
                    if isinstance(node.keys[i],ast.Constant) and node.keys[i].value=='exit_confirmation':
                        self.assertEqual(ast.dump(node.values[i]),ast.dump(ast.Attribute(value=ast.Name(id='process',ctx=ast.Load()),attr='exit_confirmation',ctx=ast.Load())))
                        node.keys.pop(i);node.values.pop(i);removals+=1
        self.assertEqual(removals,2);self.assertEqual(ast.dump(a),ast.dump(b))

if __name__=='__main__':unittest.main()
