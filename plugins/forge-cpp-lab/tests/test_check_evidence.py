"""Original real-file regressions for the offline evidence checker."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/cpp-chess-engineering/scripts/check_evidence.py'


class EvidenceCheckerTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), 'evidence checker is missing')
        spec = importlib.util.spec_from_file_location('check_evidence', SCRIPT)
        self.checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.checker)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.record_path = self.root / 'record.json'
        self.record = {
            'schema': 1, 'kind': 'exact-speed',
            'baseline': {'commit': 'a' * 40, 'artifacts': [self.file('base.exe', b'base')]},
            'candidate': {'commit': 'b' * 40, 'artifacts': [self.file('candidate.exe', b'candidate')]},
            'bench': {'expected': {'11': 100, '13': 500},
                      'baseline': {'11': 100, '13': 500},
                      'candidate': {'11': 100, '13': 500}},
            'checks': [{'name': 'perft', 'status': 'PASS', 'evidence': self.file('perft.log', b'original test log\n')}]}

    def file(self, name, data):
        (self.root / name).write_bytes(data)
        return {'path': name, 'sha256': hashlib.sha256(data).hexdigest()}

    def run_record(self):
        self.record_path.write_text(json.dumps(self.record), encoding='utf-8')
        return self.checker.check_record(self.record_path)

    def test_valid_record_passes_without_changing_input_files(self):
        self.record_path.write_text(json.dumps(self.record), encoding='utf-8')
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        result = self.checker.check_record(self.record_path)
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['strength_claim'], 'UNVERIFIED')
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir()})

    def test_artifact_corruption_and_missing_artifact_fail(self):
        (self.root / 'candidate.exe').write_bytes(b'corruption')
        self.assertEqual(self.run_record()['status'], 'FAIL')
        self.record['candidate']['artifacts'][0]['path'] = 'absent.exe'
        self.assertEqual(self.run_record()['status'], 'FAIL')

    def test_declared_test_failure_is_not_accepted(self):
        self.record['checks'][0]['status'] = 'FAIL'
        result = self.run_record()
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(result['checks'][0]['status'], 'FAIL')

    def test_unverified_check_stays_unverified_and_blocks_pass(self):
        self.record['checks'][0] = {'name': 'Windows', 'status': 'UNVERIFIED'}
        result = self.run_record()
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(result['checks'][0]['status'], 'UNVERIFIED')

    def test_missing_and_empty_required_evidence_are_invalid(self):
        for field in ('baseline', 'candidate', 'checks'):
            with self.subTest(field=field):
                old = self.record[field]
                self.record[field] = [] if field == 'checks' else {'commit': 'a'*40, 'artifacts': []}
                self.assertEqual(self.run_record()['status'], 'INVALID')
                self.record[field] = old
        del self.record['checks'][0]['evidence']
        self.assertEqual(self.run_record()['status'], 'INVALID')

    def test_bench_exact_mismatch_is_failure_not_rounding_tolerance(self):
        self.record['bench']['candidate']['13'] += 1
        self.assertEqual(self.run_record()['status'], 'FAIL')

    def test_bench_must_match_pins_even_if_both_runs_agree(self):
        self.record['bench']['candidate']['11'] = 101
        self.record['bench']['baseline']['11'] = 101
        self.assertEqual(self.run_record()['status'], 'FAIL')

    def test_exact_speed_requires_all_depths_and_nonempty_pins(self):
        for bad in ({}, {'expected': {}, 'baseline': {}, 'candidate': {}},
                    {'expected': {'11':100}, 'baseline': {'11':100}, 'candidate': {'13':100}}):
            self.record['bench'] = bad
            self.assertEqual(self.run_record()['status'], 'INVALID')
        del self.record['bench']
        self.assertEqual(self.run_record()['status'], 'INVALID')

    def test_bool_and_noninteger_node_counts_and_schema_are_invalid(self):
        for value in (True, -1, 1.5, '100', None):
            self.record['bench']['candidate']['11'] = value
            self.assertEqual(self.run_record()['status'], 'INVALID')
        self.record['bench']['candidate']['11'] = 100
        self.record['schema'] = True
        self.assertEqual(self.run_record()['status'], 'INVALID')

    def test_duplicate_json_keys_and_nonfinite_values_are_invalid(self):
        for data in ('{"schema":1,"schema":1}', '{"value":NaN}', '{"value":Infinity}', '{"value":-Infinity}', '{"value":1e999}'):
            self.record_path.write_text(data)
            self.assertEqual(self.checker.check_record(self.record_path)['status'], 'INVALID')

    def test_overflowed_numeric_literal_cannot_hide_in_extra_field(self):
        self.record_path.write_text(json.dumps(self.record)[:-1] + ', "extra": 1e999}')
        self.assertEqual(self.checker.check_record(self.record_path)['status'], 'INVALID')

    def test_bad_commit_digest_and_absolute_paths_are_invalid(self):
        for value in ('abcd', 'z' * 40, 42):
            self.record['baseline']['commit'] = value
            self.assertEqual(self.run_record()['status'], 'INVALID')
        self.record['baseline']['commit'] = 'a' * 40
        for value in ('bad', 'g' * 64, None):
            self.record['baseline']['artifacts'][0]['sha256'] = value
            self.assertEqual(self.run_record()['status'], 'INVALID')
        self.record['baseline']['artifacts'][0] = self.file('base.exe', b'base')
        for path in ('/tmp/base.exe', r'C:\\base.exe', r'C:base.exe', r'\\server\share\base.exe'):
            self.record['baseline']['artifacts'][0]['path'] = path
            self.assertEqual(self.run_record()['status'], 'INVALID')

    def test_record_relative_paths_do_not_depend_on_working_directory(self):
        self.record_path.write_text(json.dumps(self.record))
        completed = subprocess.run([sys.executable, str(SCRIPT), str(self.record_path)],
                                   cwd=self.root.parent, capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)['status'], 'PASS')

    def test_correctness_and_strength_records_never_claim_elo(self):
        del self.record['bench']
        for kind in ('correctness', 'strength'):
            self.record['kind'] = kind
            result = self.run_record()
            self.assertEqual(result['status'], 'PASS')
            self.assertEqual(result['strength_claim'], 'UNVERIFIED')
            self.assertIn('not', result['scope'].lower())

    def test_cli_reports_failure_invalid_and_missing_record_as_json(self):
        for change, code, status in [('failure',1,'FAIL'), ('invalid',2,'INVALID'), ('missing',2,'INVALID')]:
            with self.subTest(change=change):
                self.record['checks'][0]['status'] = 'FAIL' if change == 'failure' else 'PASS'
                self.record['schema'] = 9 if change == 'invalid' else 1
                self.record_path.write_text(json.dumps(self.record))
                path = self.root/'absent.json' if change == 'missing' else self.record_path
                result = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)
                self.assertEqual(result.returncode, code, result.stderr)
                self.assertEqual(json.loads(result.stdout)['status'], status)


if __name__ == '__main__':
    unittest.main()
