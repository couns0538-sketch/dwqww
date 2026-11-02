"""Incomplete-data sealer regressions; all inputs are synthetic fixtures."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, 'D:/a10/wt/astra_r10/job1/pack-tests')
from test_seal_evidence import SealerTests


class IncompleteDataTests(SealerTests):
    # Inherits all15 strict engine/data regressions unchanged.
    def incomplete_reports(self):
        self.data_reports()
        self.audit.update(status='UNVERIFIED', evidence_scope='actual-inputs', unknown_game_id_rows=4)
        self.replace_report('audit_report', self.audit)

    def test_incomplete_data_keeps_unverified_status_and_blocks_training(self):
        self.incomplete_reports()
        self.manifest(blockers=['Authentic game IDs unavailable; clearance UNVERIFIED.'])
        report = self.run_seal('incomplete-data')
        self.assertEqual(report['status'], 'SEALED_INCOMPLETE')
        self.assertEqual(report['strength'], 'UNPROVEN')
        self.assertEqual(report['training_clearance'], 'BLOCKED')
        self.assertEqual(report['input_report_statuses']['audit_report']['status'], 'UNVERIFIED')
        self.assertEqual(report['input_report_statuses']['replay_report']['status'], 'PASS')
        copied = json.loads((self.out / 'artifacts/audit.json').read_text())
        self.assertEqual(copied['unknown_game_id_rows'], 4)
        self.assertEqual(copied['status'], 'UNVERIFIED')
        for algorithm, filename in [('sha256', 'SHA256SUMS'), ('md5', 'MD5SUMS')]:
            for line in (self.out / filename).read_text().splitlines():
                expected, rel = line.split('  ', 1)
                self.assertEqual(hashlib.new(algorithm, (self.out / rel).read_bytes()).hexdigest(), expected)

    def test_incomplete_data_without_blockers_refused(self):
        self.incomplete_reports()
        self.manifest(blockers=[])
        with self.assertRaisesRegex(ValueError, 'incomplete-data needs at least one blocker'):
            self.run_seal('incomplete-data')
        self.assertFalse(self.out.exists())

    def test_incomplete_data_missing_required_deliverable_refused(self):
        self.incomplete_reports()
        self.artifacts = [entry for entry in self.artifacts if entry['role'] != 'training_command']
        self.manifest(blockers=['Game IDs absent; guarded training command is not supplied.'])
        with self.assertRaisesRegex(ValueError, 'incomplete-data requires one training_command'):
            self.run_seal('incomplete-data')
        self.assertFalse(self.out.exists())

    def test_unverified_evidence_cannot_upgrade_to_strict_data_tool(self):
        self.incomplete_reports()
        self.manifest(blockers=[])
        with self.assertRaisesRegex(ValueError, 'must PASS with actual-adapter scope'):
            self.run_seal('data-tool')
        self.assertFalse(self.out.exists())

    def test_pass_report_cannot_upgrade_incomplete_purpose(self):
        self.data_reports()
        self.manifest(blockers=['Independent native review and required test remain outstanding.'])
        report = self.run_seal('incomplete-data')
        self.assertEqual(report['status'], 'SEALED_INCOMPLETE')
        self.assertEqual(report['training_clearance'], 'BLOCKED')
        self.assertEqual(report['input_report_statuses']['audit_report']['status'], 'PASS')
        self.assertNotIn('READY_FOR_QA_REVIEW', (self.out / 'REPORT.json').read_text())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--threads', type=int, choices=[1], required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--new-only', action='store_true')
    args = parser.parse_args()
    from test_seal_evidence import seal
    out = seal.checked_path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    tempfile.tempdir = str(out)
    names = unittest.defaultTestLoader.getTestCaseNames(IncompleteDataTests)
    if args.new_only:
        names = [name for name in names if name in IncompleteDataTests.__dict__]
    suite = unittest.TestSuite(IncompleteDataTests(name) for name in names)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {'scope': 'synthetic-fixture-only', 'classification': 'UNPROVEN', 'tests': result.testsRun,
              'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped),
              'status': 'PASS' if result.wasSuccessful() and not result.skipped else 'FAIL',
              'new_only': args.new_only}
    with (out / 'result.json').open('x') as stream:
        json.dump(report, stream, indent=2)
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
