"""Benign Python process observations only; never executes an engine or build."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import unittest

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[1]
TARGET=Path(os.environ.get('OWNED_PROCESS_TEST_MODULE',str(REPO/'.github/hosted-runtime-psqt-performance/owned_process.py')))
spec=importlib.util.spec_from_file_location('owned_process_under_test',TARGET)
owned=importlib.util.module_from_spec(spec);spec.loader.exec_module(owned)

class OwnedProcessObservations(unittest.TestCase):
    def setUp(self):
        phase=os.environ.get('PROCESS_TEST_PHASE','manual-'+str(time.time_ns()))
        self.case=ROOT/'process-fixture-runs'/phase/self._testMethodName;self.case.mkdir(parents=True,exist_ok=False)
        self.out=self.case/'sample';self.affinity=os.sched_getaffinity(0);self.cpu=min(self.affinity)
    def run_fixture(self,code,stdin=b'',timeout=2):
        return owned.run_owned([sys.executable,'-c',code],stdin,self.out,self.cpu,timeout)
    def check_hashes(self,row):
        for stream in ('stdout','stderr'):
            path=self.out/(stream+'.txt');digest=hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(row.get(stream+'_sha256'),digest)
            self.assertIsInstance(row.get(stream+'_sha256_before_verdict'),str)
        self.assertTrue((self.out/'status-before-verdict.json').is_file())
        self.assertEqual(json.loads((self.out/'status.json').read_text())['returncode'],row['returncode'])
    def test_success_preserves_raw_bytes_and_exact_wait4_cpu(self):
        row=self.run_fixture('import sys; x=sum(i*i for i in range(100000));sys.stdout.buffer.write(sys.stdin.buffer.read());print(x) ',b'raw input\n')
        self.assertEqual(row['returncode'],0);self.assertEqual(row.get('returncode_before_verdict'),0)
        self.assertTrue(row.get('owned_group_empty_before_verdict'));self.assertTrue(row.get('owned_group_empty_after_cleanup'))
        self.assertGreater(row['cpu_seconds'],0);self.assertEqual(row['cpu_seconds'],row['user_seconds']+row['system_seconds'])
        self.assertGreater(row['wall_seconds'],0);self.assertEqual(row.get('wall_stop_reason'),'wait4_leader_observed');self.assertEqual((self.out/'stdin.txt').read_bytes(),b'raw input\n');self.check_hashes(row)
    def test_nonzero_and_stderr_are_observed_before_verdict(self):
        row=self.run_fixture('import sys;print("original out");print("original err",file=sys.stderr);sys.exit(7)')
        self.assertEqual(row['returncode'],7);self.assertEqual(row.get('returncode_before_verdict'),7)
        self.assertEqual((self.out/'stderr.txt').read_bytes(),b'original err\n');self.check_hashes(row)
    def test_timeout_preserves_unknown_before_and_killed_after(self):
        row=self.run_fixture('import time;print("partial",flush=True);time.sleep(10)',timeout=.3)
        self.assertTrue(row['timed_out']);self.assertIsNone(row.get('returncode_before_verdict'))
        self.assertNotEqual(row['returncode'],0);self.assertTrue(row.get('cleanup_attempted'))
        self.assertTrue(row.get('owned_group_empty_after_cleanup'));self.assertEqual((self.out/'stdout.txt').read_bytes(),b'partial\n');self.check_hashes(row)
    def test_leader_exit_orphan_cannot_look_clean_before_cleanup(self):
        row=self.run_fixture('import subprocess,sys; p=subprocess.Popen([sys.executable,"-c","import time;time.sleep(10)"]); print(p.pid,flush=True)')
        self.assertEqual(row['returncode'],0);self.assertFalse(row.get('owned_group_empty_before_verdict',True))
        self.assertTrue(row.get('cleanup_attempted'));self.check_hashes(row)
        pid=int((self.out/'stdout.txt').read_text().splitlines()[0]);status=Path('/proc')/str(pid)/'stat'
        deadline=time.monotonic()+.5
        while status.exists() and status.read_text().split(') ',1)[1].split()[0]!='Z' and time.monotonic()<deadline:time.sleep(.005)
        if status.exists():self.assertEqual(status.read_text().split(') ',1)[1].split()[0],'Z')
    def test_affinity_is_singleton_in_child_and_parent_is_restored(self):
        row=self.run_fixture('import os,json;print(json.dumps(sorted(os.sched_getaffinity(0))))')
        self.assertEqual(json.loads((self.out/'stdout.txt').read_text()),[self.cpu]);self.assertEqual(os.sched_getaffinity(0),self.affinity)
        self.assertEqual(row.get('measurement_affinity'),[self.cpu])
    def test_nonfinite_timeout_rejects_before_launch(self):
        for value in (float('nan'),float('inf'),0,-1,True):
            with self.subTest(value=value),self.assertRaises(ValueError):owned.run_owned([sys.executable,'-c','pass'],b'',self.out,self.cpu,value)
        self.assertFalse(self.out.exists())
    def test_spawn_error_still_preserves_command_streams_and_unknown_facts(self):
        with self.assertRaises(OSError):owned.run_owned(['/nonexistent/benign-fixture'],b'input',self.out,self.cpu,1)
        facts=json.loads((self.out/'status.json').read_text());self.assertIsNone(facts['returncode'])
        self.assertTrue((self.out/'status-before-verdict.json').is_file());self.assertEqual((self.out/'stdin.txt').read_bytes(),b'input')
        self.assertIn('error',facts)

if __name__=='__main__':unittest.main(verbosity=2)
