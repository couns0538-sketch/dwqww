import io,queue,unittest
from unittest.mock import Mock,patch
from collections import namedtuple
from validate_uci import Engine
from time_abba import busy_fraction

class ValidationRegression(unittest.TestCase):
    def test_absolute_deadline_rejects_queued_late_readyok(self):
        e=object.__new__(Engine); e.q=queue.Queue(); e.q.put('readyok')
        with patch('validate_uci.time.monotonic',side_effect=[0,2]):
            with self.assertRaises(TimeoutError): e.wait('readyok',timeout=1)
    def test_affinity_failure_kills_owned_child(self):
        log=io.StringIO(); p=Mock(); p.pid=123; p.poll.return_value=None
        owner=Mock(); owner.cpu_affinity.side_effect=RuntimeError('test setup failure')
        with patch('builtins.open',return_value=log),patch('validate_uci.subprocess.Popen',return_value=p),patch('validate_uci.psutil.Process',return_value=owner):
            with self.assertRaisesRegex(RuntimeError,'test setup failure'): Engine('fake','fake')
        p.kill.assert_called_once(); p.wait.assert_called_once(); self.assertTrue(log.closed)
    def test_windows_busy_does_not_double_count_interrupts(self):
        T=namedtuple('T','user system idle interrupt dpc')
        self.assertAlmostEqual(busy_fraction(T(0,0,0,0,0),T(1,1,8,1,1)),20)

if __name__=='__main__': unittest.main()
