"""Synthetic adapter regressions only; never clears actual native data."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path('D:/a10')
sys.path.insert(0, str(ROOT / 'wt/skills/npt-data-holdout-check/scripts'))
import audit_selfplay as audit

A = 'r3k2r/ppp2ppp/2n5/3pP3/8/8/PPP2PPP/R3K2R w KQkq d6 0 8'
B = '4k3/8/8/8/8/8/4P3/4K3 w - - 0 1'
C = '4k3/8/8/8/8/8/3P4/4K3 b - - 1 1'
D = '4k3/8/8/8/8/8/2P5/4K3 w - - 0 1'
DEST = None


def write_new(path, value):
    raw = value if isinstance(value, bytes) else value.encode()
    with path.open('xb') as stream:
        stream.write(raw)
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest()}


def json_lines(rows):
    return ''.join(json.dumps(row, sort_keys=True) + '\n' for row in rows)


class Fixtures(unittest.TestCase):
    def fixture(self, *, ids=True, game_leak=False, position_leak=False,
                strip_castle=False, strip_ep=False, duplicate=False,
                missing_source=False, malformed=False, wrong_count=False,
                bad_sidecar=False, wrong_hash=False):
        self.base = DEST / self._testMethodName
        self.base.mkdir()
        source_literal = 'authentic-original/source001.txt'
        source_lines = [A, B]
        source = write_new(self.base / 'source.txt', ''.join(f'{fen} | 10 | 0.5\n' for fen in source_lines))
        source.update(role='source001', record_source_literal=source_literal, first_source_row=1, last_source_row=2)
        cohort_rows = [dict(source=source_literal, source_row=i, fen=fen) for i, fen in enumerate(source_lines, 1)]
        train_rows = [dict(row) for row in cohort_rows]
        if strip_castle:
            train_rows[0]['fen'] = A.replace(' KQkq ', ' - ')
        if strip_ep:
            cohort_rows[0]['fen'] = A.replace(' d6 ', ' - ')
        if duplicate:
            train_rows.append(dict(train_rows[0]))
        if missing_source:
            train_rows[0]['source_row'] = 99
        if malformed:
            train_rows[0]['fen'] = 'not a full FEN'
        cohort = write_new(self.base / 'cohort.jsonl', json_lines(cohort_rows))
        cohort['rows'] = 2
        train = write_new(self.base / 'train.jsonl', json_lines(train_rows))
        train['rows'] = len(train_rows)
        h13 = write_new(self.base / '013.txt', f'{A if position_leak else C} | 7 | 0.0\n')
        h14 = write_new(self.base / '014.txt', f'{D} | -4 | 1.0\n')
        h13.update(name='013', rows=2 if wrong_count else 1)
        h14.update(name='014', rows=1)
        if wrong_hash:
            h13['sha256'] = '0' * 64
        if ids:
            for spec, values, stem in [(source, ['G1', 'G2'], 'source'),
                                        (h13, ['G1' if game_leak else 'G3'], '013'),
                                        (h14, ['G4'], '014')]:
                rows = [dict(physical_row=i, game_id=value) for i, value in enumerate(values, 1)]
                if bad_sidecar and stem == '013':
                    rows[0]['physical_row'] = 2
                side = write_new(self.base / (stem + '.games.jsonl'), json_lines(rows))
                side.update(rows=len(values), provenance='SYNTHETIC deliberately assigned fixture identities; not native provenance')
                spec['game_ids'] = side
        config = {'schema': 1, 'purpose': 'synthetic-fixture', 'source_maps': [source],
                  'cohort': cohort, 'filtered': train, 'holdouts': [h13, h14]}
        self.manifest = self.base / 'manifest.json'
        write_new(self.manifest, json.dumps(config, indent=2))
        return config

    def run_audit(self):
        return audit.audit(self.manifest, self.base / 'output')

    def test_01_clean_synthetic_control(self):
        self.fixture()
        result = self.run_audit()
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['evidence_scope'], 'synthetic-fixture')
        self.assertEqual(result['source_rows'], 2)
        self.assertEqual(result['cohort_rows'], 2)
        self.assertEqual(result['training_rows'], 2)
        self.assertEqual(result['unknown_game_id_rows'], 0)
        self.assertTrue(result['complete'])
        self.assertFalse(result['holdouts']['013']['trusted_complete'])

    def test_02_same_game_different_position(self):
        self.fixture(game_leak=True)
        result = self.run_audit()
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(result['game_overlap_rows'], 1)
        self.assertEqual(result['position_overlap_rows'], 0)

    def test_03_stripped_castling_in_training(self):
        self.fixture(strip_castle=True)
        result = self.run_audit()
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(result['training_state_mismatch_rows'], 1)
        self.assertEqual(result['cohort_state_mismatch_rows'], 0)

    def test_04_stripped_ep_in_cohort(self):
        self.fixture(strip_ep=True)
        result = self.run_audit()
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(result['cohort_state_mismatch_rows'], 1)
        self.assertEqual(result['training_state_mismatch_rows'], 0)

    def test_05_missing_ids_never_pass(self):
        self.fixture(ids=False)
        result = self.run_audit()
        self.assertEqual(result['status'], 'UNVERIFIED')
        self.assertEqual(result['unknown_game_id_rows'], 4)
        self.assertEqual(result['missing_game_ids_by_role'], {'source001': 2, 'cohort': 2, 'filtered': 2, 'holdout013': 1, 'holdout014': 1})
        self.assertTrue(result['complete'])

    def test_06_changed_input_after_scan(self):
        config = self.fixture()
        original = audit.BoundInputs.final
        target = Path(config['filtered']['path'])
        def mutate_then_recheck(bindings):
            raw = target.read_bytes()
            write_new(self.base / 'train.before-mutation.jsonl', raw)
            target.write_bytes(raw + b' ')
            original(bindings)
        with patch.object(audit.BoundInputs, 'final', mutate_then_recheck):
            result = self.run_audit()
        self.assertEqual(result['status'], 'FAIL')
        self.assertIn('input changed during audit', result['error'])
        self.assertFalse(result['complete'])

    def test_07_duplicate_provenance_refused(self):
        self.fixture(duplicate=True)
        result = self.run_audit()
        self.assertEqual(result['status'], 'FAIL')
        self.assertIn('duplicate filtered provenance', result['error'])

    def test_08_unmapped_provenance_refused(self):
        self.fixture(missing_source=True)
        result = self.run_audit()
        self.assertEqual(result['status'], 'FAIL')
        self.assertIn('unmapped source provenance', result['error'])

    def test_09_malformed_fen_refused(self):
        self.fixture(malformed=True)
        self.assertEqual(self.run_audit()['status'], 'FAIL')

    def test_10_trusted_holdout_count_refused(self):
        self.fixture(wrong_count=True)
        result = self.run_audit()
        self.assertEqual(result['status'], 'FAIL')
        self.assertIn('trusted holdout row count mismatch', result['error'])

    def test_11_trusted_holdout_hash_refused(self):
        self.fixture(wrong_hash=True)
        with self.assertRaisesRegex(audit.AuditFailure, 'trusted input hash mismatch'):
            self.run_audit()

    def test_12_sidecar_alignment_refused(self):
        self.fixture(bad_sidecar=True)
        result = self.run_audit()
        self.assertEqual(result['status'], 'FAIL')
        self.assertIn('misaligned game sidecar', result['error'])

    def test_13_position_overlap_detected(self):
        self.fixture(position_leak=True)
        result = self.run_audit()
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(result['position_overlap_rows'], 1)
        self.assertEqual(result['game_overlap_rows'], 0)

    def test_14_existing_output_refused(self):
        self.fixture()
        self.run_audit()
        with self.assertRaisesRegex(audit.AuditFailure, 'new output directory required'):
            self.run_audit()

    def test_15_archive_exact_parsed_manifest_snapshot(self):
        self.fixture()
        original_bytes = self.manifest.read_bytes()
        original_read = Path.read_bytes
        calls = []
        def transient_manifest(path):
            if path == self.manifest:
                calls.append(1)
                # Independent fingerprint reads still observe the original.
                # A second unbound archive read sees transient changed bytes.
                if len(calls) > 1:
                    return b'{"purpose":"wrong archived manifest"}\n'
            return original_read(path)
        with patch.object(Path, 'read_bytes', transient_manifest):
            result = self.run_audit()
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual((self.base / 'output/manifest.json').read_bytes(), original_bytes)
        self.assertEqual(len(calls), 1)


def main():
    global DEST
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--threads', type=int, choices=[1], required=True)
    args = parser.parse_args()
    DEST = audit.safe_path(args.out)
    if DEST.exists():
        raise RuntimeError('new fixture root required; preserve previous results')
    DEST.mkdir(parents=True)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Fixtures))
    summary = {'scope': 'synthetic-fixture-only', 'classification': 'UNPROVEN', 'tests_run': result.testsRun,
               'failures': len(result.failures), 'errors': len(result.errors), 'success': result.wasSuccessful()}
    write_new(DEST / 'fixture_summary.json', json.dumps(summary, indent=2))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
