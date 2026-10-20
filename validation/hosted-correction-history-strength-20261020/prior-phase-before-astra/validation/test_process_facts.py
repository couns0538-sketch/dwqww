"""Real benign subprocesses verify process facts survive failed parser verdicts."""
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
SOURCE = Path(os.environ.get('BENCH_PARSER_DATA', str(ROOT.parents[1] / '.github/hosted-correction-history-strength/run_hosted.py')))
PHASE = os.environ.get('BENCH_TEST_PHASE', 'draft18-green')
namespace = {name: globals()[name] for name in ('hashlib','json','os','Path','re','signal','subprocess','time')}
names = {'sha','save','stop_group','verify_candidate_bench_signature','candidate_bench_readiness','_owned_group_empty','_owned_readiness_probe'}
tree = ast.parse(SOURCE.read_text())
functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
exec(compile(ast.Module(body=functions, type_ignores=[]), str(SOURCE), 'exec'), namespace)


class RealBenignProcessFacts(unittest.TestCase):
    def probe(self, mode, expected_code, expect_success):
        out = ROOT / 'fixture-runs' / PHASE / mode
        out.mkdir(parents=True, exist_ok=False)
        error = None
        with patch.dict(os.environ, {'BENCH_FIXTURE_MODE': mode}):
            try:
                result = namespace['candidate_bench_readiness'](ROOT/'benign_fixture.py', out, 385781)
            except BaseException as caught:
                error = caught
        facts_path = out / 'candidate-bench11-process.json'
        self.assertTrue(facts_path.exists(), f'Completed-process facts missing after {mode}: {error}')
        facts = json.loads(facts_path.read_text())
        self.assertEqual(facts['returncode_after_cleanup'], expected_code)
        self.assertEqual(facts['stdout_sha256'], hashlib.sha256((out/'candidate-bench11.stdout').read_bytes()).hexdigest())
        self.assertEqual(facts['stderr_sha256'], hashlib.sha256((out/'candidate-bench11.stderr').read_bytes()).hexdigest())
        self.assertTrue(facts['owned_group_empty_after_cleanup'])
        for field in ('stdout_sha256_before_verdict', 'stderr_sha256_before_verdict',
                      'stdout_sha256_after_cleanup', 'stderr_sha256_after_cleanup'):
            self.assertIn(field, facts, f'Missing distinct observation: {field}')
        self.assertEqual(facts['stdout_sha256_before_verdict'], facts['stdout_sha256_after_cleanup'])
        expected_before_stderr = b'benign fixture diagnostic\n' if mode == 'stderr' else b''
        self.assertEqual(facts['stderr_sha256_before_verdict'], hashlib.sha256(expected_before_stderr).hexdigest())
        self.assertEqual(facts['stderr_sha256_after_cleanup'], facts['stderr_sha256'])
        if mode == 'timeout':
            self.assertNotEqual(facts['stderr_sha256_before_verdict'], facts['stderr_sha256_after_cleanup'])
        self.assertEqual(facts['guard_seconds'], 10)
        self.assertEqual(facts['stdin'], 'bench 11\nquit\n')
        self.assertEqual(error is None, expect_success)
        if mode != 'timeout':
            self.assertEqual(facts['returncode_before_verdict'], expected_code)
            self.assertTrue(facts['owned_group_empty_before_verdict'])
        else:
            self.assertIsNone(facts['returncode_before_verdict'])
            self.assertTrue(facts['cleanup_attempted'])
            self.assertIsInstance(error, subprocess.TimeoutExpired)
        if expect_success:
            self.assertEqual(result['engine_nodes'], 385781)
            self.assertEqual(facts['verdict'], 'passed')
        else:
            self.assertEqual(facts['verdict'], 'failed')

    def test_success_facts(self): self.probe('canonical', 0, True)
    def test_parser_rejection_retains_exit_zero_and_hashes(self): self.probe('malformed', 0, False)
    def test_nonzero_exit_is_preserved(self): self.probe('nonzero', 7, False)
    def test_stderr_rejection_retains_exit_zero(self): self.probe('stderr', 0, False)
    def test_original_ten_second_guard_and_cleanup_are_preserved(self): self.probe('timeout', -signal.SIGINT, False)


if __name__ == '__main__':
    unittest.main(verbosity=2)
