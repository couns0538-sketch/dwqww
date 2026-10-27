"""Pure RSS regression controls against preserved actual OWN status captures."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('S18_scope_v3',HERE/'forge_sol_S18_train_selected_v3_20261027.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
CAP=Path('/tmp/forge_sol_S18_RSS_EXIT_DIAGNOSTIC_20261027')
PID=275331;TID=275333
LEADER=(CAP/'forge_sol_S18_actual_leader_original_20261027.status').read_text()
WORKER=(CAP/('forge_sol_S18_actual_task_'+str(TID)+'_original_20261027.status')).read_text()
EXPECTED=12572*1024

class ScopeTests(unittest.TestCase):
    def patched_capture(self,pid=PID,worker=WORKER,ids=None):
        def read(path):
            path=str(path)
            if path==f'/proc/{PID}/status' or path==f'/proc/{PID}/task/{PID}/status':return LEADER
            if path==f'/proc/{PID}/task/{TID}/status':return worker
            raise FileNotFoundError(path)
        return patch.object(m,'read_proc_status',side_effect=read),patch.object(m,'owned_task_ids',return_value=[PID,TID] if ids is None else ids)
    def test_actual_captured_exit_leader_uses_owned_live_thread_RSS(self):
        self.assertTrue(callable(getattr(m,'read_proc_status',None)),'owned-task RSS fallback missing')
        a,b=self.patched_capture();observation={}
        with a,b:r=m.read_rss_bytes(PID,observation=observation)
        self.assertEqual(r,EXPECTED);self.assertEqual(observation['scope'],'OWNED_LIVE_THREAD_SHARED_MM')
        self.assertEqual(observation['selected_tid'],TID);self.assertEqual(observation['rss_bytes'],EXPECTED)
    def test_RSS_limit_still_rejects_fallback_sample(self):
        self.assertTrue(callable(getattr(m,'read_proc_status',None)))
        class Process:
            pid=PID;returncode=None
            def poll(self):return None
        a,b=self.patched_capture()
        with a,b,patch.object(m.os,'killpg') as kill:
            guard=m.RSSGuard(Process(),EXPECTED-1);guard.poll()
        self.assertEqual(guard.stop_reason,'RSS_LIMIT');self.assertEqual(guard.max_sampled_rss_bytes,EXPECTED)
        self.assertEqual(kill.call_args.args[0],PID)
    def test_no_false_stop_for_fallback_then_normal_close(self):
        self.assertTrue(callable(getattr(m,'read_proc_status',None)))
        class Process:
            pid=PID;returncode=None
            calls=0
            def poll(self):
                self.calls+=1
                if self.calls>=3:self.returncode=0
                return self.returncode
        a,b=self.patched_capture()
        with a,b,patch.object(m.os,'killpg') as kill:
            guard=m.RSSGuard(Process(),3*2**30);self.assertIsNone(guard.poll());self.assertEqual(guard.poll(),0)
        self.assertIsNone(guard.stop_reason);kill.assert_not_called();self.assertEqual(guard.fallback_samples,1)
    def test_foreign_Tgid_rejected(self):
        self.assertTrue(callable(getattr(m,'read_proc_status',None)))
        a,b=self.patched_capture(worker=WORKER.replace('Tgid:\t275331','Tgid:\t1'))
        with a,b,self.assertRaises(ValueError):m.read_rss_bytes(PID)
    def test_wrong_thread_Pid_rejected(self):
        self.assertTrue(callable(getattr(m,'read_proc_status',None)))
        a,b=self.patched_capture(worker=WORKER.replace('Pid:\t275333','Pid:\t1'))
        with a,b,self.assertRaises(ValueError):m.read_rss_bytes(PID)
    def test_unknown_live_leader_without_RSS_not_suppressed(self):
        self.assertTrue(callable(getattr(m,'read_proc_status',None)))
        with patch.object(m,'read_proc_status',return_value=LEADER.replace('Z (zombie)','R (running)')),patch.object(m,'owned_task_ids',side_effect=AssertionError('no unproven fallback')):
            with self.assertRaises(ValueError):m.read_rss_bytes(PID)
    def test_missing_all_worker_RSS_not_zero(self):
        self.assertTrue(callable(getattr(m,'read_proc_status',None)))
        a,b=self.patched_capture(ids=[PID])
        with a,b,self.assertRaises(ValueError):m.read_rss_bytes(PID)
    def test_permission_error_not_suppressed(self):
        self.assertTrue(callable(getattr(m,'read_proc_status',None)))
        def read(path):
            if str(path)==f'/proc/{PID}/status':return LEADER
            raise PermissionError('fixture denied')
        with patch.object(m,'read_proc_status',side_effect=read),patch.object(m,'owned_task_ids',return_value=[TID]):
            with self.assertRaises(PermissionError):m.read_rss_bytes(PID)
    def test_shared_mm_samples_are_max_not_sum(self):
        self.assertTrue(callable(getattr(m,'read_proc_status',None)))
        other=WORKER.replace('Pid:\t275333','Pid:\t275334').replace('12572 kB','14000 kB')
        def read(path):
            path=str(path)
            if path==f'/proc/{PID}/status':return LEADER
            if path.endswith('/275333/status'):return WORKER
            if path.endswith('/275334/status'):return other
            raise FileNotFoundError(path)
        with patch.object(m,'read_proc_status',side_effect=read),patch.object(m,'owned_task_ids',return_value=[TID,TID+1]):
            self.assertEqual(m.read_rss_bytes(PID),14000*1024)
    def test_task_scan_cap_is_enforced(self):
        self.assertTrue(callable(getattr(m,'owned_task_ids',None)))
        class Entry:
            def __init__(self,n):self.name=str(n)
        with patch.object(Path,'iterdir',return_value=iter(Entry(i) for i in range(1,66))):
            with self.assertRaises(ValueError):m.owned_task_ids(PID)
    def test_read_status_cap(self):
        self.assertTrue(callable(getattr(m,'read_proc_status',None)))
        from io import BytesIO
        class Context(BytesIO):
            def __enter__(self):return self
            def __exit__(self,*args):self.close()
        with patch.object(Path,'open',return_value=Context(b'x'*8193)):
            with self.assertRaises(ValueError):m.read_proc_status('/proc/FIXTURE/status')

if __name__=='__main__':unittest.main()
