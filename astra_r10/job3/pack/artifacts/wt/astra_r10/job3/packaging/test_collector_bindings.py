"""Targeted synthetic collector identity regressions; never executes collector."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parent))
import prepare_job3_pack as collector

OUT = None
ORIGINAL_HELPER = Path('D:/a10/wt/astra_r10/job3/regression/launcher_before_readonly/Invoke-GrokPcSafeRun.ps1')


def write_new(path, data):
    raw = data if isinstance(data, bytes) else (json.dumps(data, indent=2) + '\n').encode()
    with path.open('xb') as stream:
        stream.write(raw)
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest()}


class BindingTests(unittest.TestCase):
    def setUp(self):
        self.root = OUT / self._testMethodName
        self.root.mkdir()
        self.archived = self.root / 'archived_launcher.ps1'
        self.wrapper = self.root / 'owned_wrapper.ps1'
        original = ORIGINAL_HELPER.read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(), collector.ARCHIVED_LAUNCHER_SHA256)
        write_new(self.archived, original)
        wrapper = write_new(self.wrapper, b'# synthetic owned wrapper, never executed\n')
        admission = {'schema': 1, 'status': 'PASS', 'selected_cpu': 3,
                     'qualifying_pair': [{'utc': '2026-11-02T08:00:00+00:00', 'cpu3': 1, 'host_total': 50},
                                         {'utc': '2026-11-02T08:00:03+00:00', 'cpu3': 2, 'host_total': 51}]}
        binding = {'command_start_utc': '2026-11-02T08:00:04+00:00',
                   'manifest_sha256': 'a' * 64, 'archived_launcher': str(self.archived),
                   'sha256': collector.ARCHIVED_LAUNCHER_SHA256,
                   'wrapper': str(self.wrapper), 'wrapper_sha256': wrapper['sha256']}
        self.binding = binding
        self.admission_ref = write_new(self.root / 'admission.json', admission)
        self.binding_ref = write_new(self.root / 'binding.json', binding)
        self.ready = {'replay': {'admission': self.admission_ref, 'launcher_binding': self.binding_ref}}
        self.receipt = {'manifest_sha256': 'a' * 64}

    def admit(self):
        return collector.admitted_replay(self.ready, self.receipt)

    def test_exact_helper_and_wrapper_accepted(self):
        refs = self.admit()
        self.assertEqual(refs[self.archived], collector.ARCHIVED_LAUNCHER_SHA256)
        self.assertEqual(refs[self.wrapper], self.binding['wrapper_sha256'])
        collector.check_admission_artifacts(refs, {str(path): collector.digest(path)[0] for path in refs})

    def test_archived_launcher_drift_refused(self):
        self.archived.write_bytes(b'# deliberately changed disposable helper\n')
        with self.assertRaisesRegex(ValueError, 'archived admission launcher changed'):
            self.admit()

    def test_wrapper_drift_refused(self):
        self.wrapper.write_bytes(b'# deliberately changed disposable wrapper\n')
        with self.assertRaisesRegex(ValueError, 'admission wrapper changed'):
            self.admit()

    def test_wrong_archived_identity_in_binding_refused(self):
        self.binding['sha256'] = '0' * 64
        self.ready['replay']['launcher_binding'] = write_new(self.root / 'wrong-binding.json', self.binding)
        with self.assertRaisesRegex(ValueError, 'accepted immutable archived launcher identity'):
            self.admit()

    def test_wrapper_drift_after_validation_refused(self):
        refs = self.admit()
        self.wrapper.write_bytes(b'# disposable wrapper changed after admission validation\n')
        current = {str(path): collector.digest(path)[0] for path in refs}
        with self.assertRaisesRegex(ValueError, 'artifact changed after validation'):
            collector.check_admission_artifacts(refs, current)

    def test_archived_drift_after_validation_refused(self):
        refs = self.admit()
        self.archived.write_bytes(b'# disposable helper changed after admission validation\n')
        current = {str(path): collector.digest(path)[0] for path in refs}
        with self.assertRaisesRegex(ValueError, 'artifact changed after validation'):
            collector.check_admission_artifacts(refs, current)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--threads', type=int, choices=[1], required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    OUT = collector.sealing.checked_path(args.out)
    OUT.mkdir(parents=True, exist_ok=False)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(BindingTests))
    write_new(OUT / 'result.json', {'scope': 'synthetic-fixture-only', 'classification': 'UNPROVEN',
              'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
              'skipped': len(result.skipped), 'status': 'PASS' if result.wasSuccessful() and not result.skipped else 'FAIL'})
    raise SystemExit(0 if result.wasSuccessful() and not result.skipped else 1)
