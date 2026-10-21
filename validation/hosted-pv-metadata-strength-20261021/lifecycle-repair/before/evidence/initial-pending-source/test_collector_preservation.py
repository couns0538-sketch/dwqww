"""Future collector: benign subprocesses only; never compiler/engine/network/Git."""
import importlib.util
import json
import os
import stat
from pathlib import Path
import sys
import tempfile
import time
import unittest

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('future_collector_under_test',ROOT.parents[1]/'.github/hosted-pv-metadata-strength/prepare_hosted.py')
collector=importlib.util.module_from_spec(spec);spec.loader.exec_module(collector)

class CollectorFailureFacts(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=ROOT,prefix='collector-benign-unit-');self.addCleanup(self.temp.cleanup);self.out=Path(self.temp.name)

    def test_copied_forge_preserves_executable_mode_without_execution(self):
        source=self.out/"source";source.mkdir();build=self.out/"build";build.mkdir()
        (build/"forge").write_bytes(b"INERT UNIT ARTIFACT; NEVER EXECUTED\n");(build/"forge").chmod(0o751)
        (build/"libforge_core.a").write_bytes(b"INERT UNIT CORE\n")
        collector.collect_label(self.out,"candidate","unit-only",source,build)
        target=self.out/"artifacts/candidate/forge"
        self.assertEqual(stat.S_IMODE(target.stat().st_mode),0o751)
        self.assertTrue(os.access(target,os.X_OK))

    def test_nonzero_stage_preserves_original_streams_returncode_and_manifest(self):
        command=[sys.executable,'-c','import sys;print("benign stage stdout");print("benign stage stderr",file=sys.stderr);sys.exit(7)']
        with self.assertRaises(RuntimeError):collector.stage(self.out,'unit-stage',command,self.out,2,time.monotonic()+3)
        facts=json.loads((self.out/'unit-stage-command.json').read_text())
        self.assertEqual(facts['returncode_before_verdict'],7);self.assertEqual(facts['exit_code'],7)
        self.assertTrue(facts['owned_group_empty_after_cleanup'])
        self.assertEqual((self.out/'unit-stage.stdout').read_bytes(),b'benign stage stdout\n')
        self.assertEqual((self.out/'unit-stage.stderr').read_bytes(),b'benign stage stderr\n')
        collector.publish_existing(self.out)
        inventory=json.loads((self.out/'build-evidence-SHA256.json').read_text())
        self.assertIn('unit-stage-command.json',inventory);self.assertIn('unit-stage.stderr',inventory)

    def test_timeout_preserves_partial_bytes_and_separate_before_after_facts(self):
        command=[sys.executable,'-c','import time;print("partial benign output",flush=True);time.sleep(5)']
        with self.assertRaises(collector.subprocess.TimeoutExpired) as caught:
            collector.stage(self.out,'unit-timeout',command,self.out,.2,time.monotonic()+2)
        self.assertIsInstance(caught.exception,collector.subprocess.TimeoutExpired)
        facts=json.loads((self.out/'unit-timeout-command.json').read_text())
        self.assertIsNone(facts['returncode_before_verdict']);self.assertIsNotNone(facts['exit_code'])
        self.assertTrue(facts['cleanup_attempted']);self.assertTrue(facts['owned_group_empty_after_cleanup'])
        self.assertEqual((self.out/'unit-timeout.stdout').read_bytes(),b'partial benign output\n')
        self.assertIn('stderr_sha256_before_verdict',facts);self.assertIn('stderr_sha256',facts)

if __name__=='__main__':unittest.main(verbosity=2)
