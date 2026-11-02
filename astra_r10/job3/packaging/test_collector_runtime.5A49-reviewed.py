"""Synthetic collector integration checks; no actual pack, runtime or native execution."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import prepare_job3_pack as c

sys.path.insert(0, 'D:/a10/pydeps')
import psutil


def create(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = value if isinstance(value, bytes) else (json.dumps(value) + '\n').encode()
    path.write_bytes(raw)
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest()}


class RuntimeCollectorFixtures(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='collector-runtime-', dir='D:/a10/tmp')
        self.root = Path(self.tmp.name)
        self.job = self.root / 'wt/astra_r10/job3'
        self.root_patch = patch.object(c, 'ROOT', self.root); self.root_patch.start()
        self.job_patch = patch.object(c, 'JOB', self.job); self.job_patch.start()
        self.addCleanup(self.tmp.cleanup); self.addCleanup(self.root_patch.stop); self.addCleanup(self.job_patch.stop)

    def attempt(self, report=None, wrong_target=False):
        directory = self.root / 'job3/regression-runs/fixture01'
        result = {'status': 'FAIL'} if report is None else report
        report_path = directory / ('RESULT.json' if result['status'] == 'PASS' else 'FAILURE.json')
        create(report_path, result)
        generated = directory / 'cache/generated.cpp'
        create(generated, b'// synthetic fixture generated text\n')
        launch = self.job / 'regression/fixture01-launch'
        manifest = create(launch / 'manifest.json', {'arguments': ['--out', str(directory / 'wrong' if wrong_target else directory)]})
        receipt = create(launch / 'result.json', {'native_exit_code': 0 if result['status'] == 'PASS' else 1,
            'finished_utc': '2026-11-02T08:00:00Z', 'capture_errors': [], 'disk_floor_breached': False,
            'manifest_sha256': manifest['sha256']})
        ready = {'regression': {'launcher': receipt, 'attempts': [{'directory': str(directory), 'launcher': receipt}]}}
        return ready, directory, report_path, result, generated

    def test_changed_assembled_manifest_refused(self):
        create(self.root / 'job3/runtime312/RUNTIME_FILES.json', b'changed manifest\n')
        with self.assertRaisesRegex(ValueError, 'isolated runtime evidence changed'):
            c.runtime312_inputs(lambda path: None)

    def test_failed_native_records_preserved_generated_code_hash_only(self):
        ready, directory, report_path, report, generated = self.attempt()
        log = directory / 'pytest.log'
        create(log, b'synthetic pytest log\n')
        shipped = set()
        summary, bindings, retained, inventories = c.regression_inputs(ready, report_path, report, shipped.add)
        self.assertIn(report_path, shipped)
        self.assertIn(log, shipped)
        self.assertNotIn(generated, shipped)
        self.assertEqual(retained[generated], hashlib.sha256(generated.read_bytes()).hexdigest())
        self.assertEqual(summary[0]['status'], 'FAIL')
        self.assertEqual(inventories[directory], [generated])

    def test_unknown_output_requires_explicit_review(self):
        ready, directory, report_path, report, _ = self.attempt()
        create(directory / 'unreviewed.py', b'# fixture only\n')
        with self.assertRaisesRegex(ValueError, 'unrecognized regression output'):
            c.regression_inputs(ready, report_path, report, lambda path: None)

    def test_wrong_completed_launcher_target_refused(self):
        ready, _, report_path, report, _ = self.attempt(wrong_target=True)
        with self.assertRaisesRegex(ValueError, 'wrong completed launcher target'):
            c.regression_inputs(ready, report_path, report, lambda path: None)

    def test_preflight_cannot_upgrade_to_suite_pass(self):
        ready, _, report_path, report, _ = self.attempt({'status': 'PASS', 'preflight_only': True})
        with self.assertRaisesRegex(ValueError, 'complete unskipped suite'):
            c.regression_inputs(ready, report_path, report, lambda path: None)

    def test_pass_requires_exact_runtime_binding(self):
        result = {'status': 'PASS', 'preflight_only': False, 'collected': 73, 'passed': 73,
                  'failures': 0, 'skipped': 0, 'optimizer_updates': 0, 'training_loops': 0,
                  'external_runtime_unchanged': True, 'toolchain_unchanged': True,
                  'private_runtime_unchanged': True, 'private_runtime_binding': {'sha256': 'wrong'}}
        ready, _, report_path, report, _ = self.attempt(result)
        with self.assertRaisesRegex(ValueError, 'unchanged isolated runtime'):
            c.regression_inputs(ready, report_path, report, lambda path: None)

    def test_primary_report_cannot_use_other_attempt_launcher(self):
        ready, _, report_path, report, _ = self.attempt()
        other = create(self.job / 'regression/other-launch/result.json', {'native_exit_code': 0})
        ready['regression']['launcher'] = other
        with self.assertRaisesRegex(ValueError, 'own exact attempt launcher'):
            c.regression_inputs(ready, report_path, report, lambda path: None)

    def test_primary_pass_cannot_use_its_failed_native_exit(self):
        ready, _, report_path, report, _ = self.attempt({'status': 'PASS'})
        path = Path(ready['regression']['launcher']['path'])
        receipt = json.loads(path.read_bytes()); receipt['native_exit_code'] = 1
        ref = create(path, receipt)
        ready['regression']['launcher'] = ref
        ready['regression']['attempts'][0]['launcher'] = ref
        with self.assertRaisesRegex(ValueError, 'contradicts its own native exit'):
            c.regression_inputs(ready, report_path, report, lambda path: None)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--threads', type=int, choices=[1], required=True)
    parser.parse_args()
    p = psutil.Process()
    if p.nice() != psutil.IDLE_PRIORITY_CLASS or p.cpu_affinity() != [3]:
        raise RuntimeError('Idle CPU3 required')
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(RuntimeCollectorFixtures))
    raise SystemExit(0 if result.wasSuccessful() else 1)
