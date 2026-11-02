"""Fixture-only contract regressions. No engine/native qualification is claimed."""
import json
import pathlib
import sys
import tempfile
import unittest

import run_proof_set as proof


PINS = {'11': 312866, '13': 862329, '16': 3024920, '20': 12389307, '22': 34048354}


class ContractModes(unittest.TestCase):
    def setUp(self):
        # Preserve fixture attempts as evidence; never clean them up on failure.
        self.root = pathlib.Path(tempfile.mkdtemp(prefix='proof-modes-'))
        self.binary = self.root / 'candidate.exe'
        self.binary.write_bytes(b'fixture only')
        self.contract = {
            'candidate_commit': 'a' * 40,
            'network_sha256': 'b' * 64,
            'expected_off_nodes': PINS,
            'on_options': {'Threads': 1, 'Hash': 16, 'NNUEWideOutput': True},
            'identity_mode': 'exact',
        }
        self.receipt = {
            'schema': 1, 'status': 'PASS',
            'source_commit': self.contract['candidate_commit'],
            'network_sha256': self.contract['network_sha256'],
            'metrics': {'binary_sha256': proof.sha(self.binary), 'nodes': dict(PINS),
                        'active_count': 12000, 'options': dict(self.contract['on_options'])},
        }

    def validate_on(self):
        proof.validate('on_active', self.receipt, self.contract, self.root,
                       {'build_a': self.binary})

    def test_exact_same_pins_pass(self):
        self.validate_on()

    def test_exact_one_wrong_pin_fails(self):
        self.receipt['metrics']['nodes']['20'] += 1
        with self.assertRaisesRegex(ValueError, 'exact'):
            self.validate_on()

    def test_exact_missing_depth_fails(self):
        del self.receipt['metrics']['nodes']['22']
        with self.assertRaisesRegex(ValueError, 'depths'):
            self.validate_on()

    def test_exact_inactive_fails(self):
        self.receipt['metrics']['active_count'] = 0
        with self.assertRaisesRegex(ValueError, 'inactive'):
            self.validate_on()

    def test_exact_options_mismatch_fails(self):
        self.receipt['metrics']['options']['NNUEWideOutput'] = False
        with self.assertRaisesRegex(ValueError, 'options'):
            self.validate_on()

    def test_default_behavior_changing_still_requires_difference(self):
        del self.contract['identity_mode']
        with self.assertRaises(ValueError):
            self.validate_on()
        self.receipt['metrics']['nodes']['20'] += 1
        self.validate_on()

    def test_explicit_behavior_changing_accepts_difference(self):
        self.contract['identity_mode'] = 'behavior-changing'
        self.receipt['metrics']['nodes']['20'] += 1
        self.validate_on()

    def integration_contract(self, skip=True):
        pinned = self.root / 'input.bin'
        pinned.write_bytes(b'pinned fixture input')
        adapter = pathlib.Path(__file__).with_name('fixture_modes_adapter.py').resolve()
        interpreter = pathlib.Path(sys.executable).resolve()
        c = {
            'schema': 1, 'evidence_scope': 'fixture', 'identity_mode': 'exact',
            'max_worker_threads': 2, 'baseline_commit': 'c' * 40,
            'candidate_commit': 'a' * 40, 'network_sha256': proof.sha(pinned),
            'expected_off_nodes': dict(PINS),
            'off_options': {'Threads': 1, 'Hash': 16},
            'on_options': {'Threads': 1, 'Hash': 16, 'NNUEWideOutput': True},
            'inputs': [{'role': role, 'path': str(pinned), 'sha256': proof.sha(pinned)}
                       for role in ('compiler', 'source', 'network', 'baseline_binary')],
            'stages': {},
        }
        c['inputs'] += [
            {'role': 'interpreter', 'path': str(interpreter), 'sha256': proof.sha(interpreter)},
            {'role': 'recipe', 'path': str(adapter), 'sha256': proof.sha(adapter)},
        ]
        for name in proof.STAGES:
            c['stages'][name] = {'argv': [str(interpreter), '-I', '-B', str(adapter),
                                        name, '{result}', c['network_sha256']],
                                 'timeout_seconds': 30}
        if skip:
            c['stages']['smoke_t4'] = {'skip_reason': 'fixture: T4 not authorized on two-worker host'}
        return c

    def run_contract(self, c):
        path = self.root / 'contract.json'
        path.write_text(json.dumps(c), encoding='utf-8')
        return proof.run(path, self.root / 'run')

    def test_skipped_t4_is_unverified_and_sanitizer_runs(self):
        report = self.run_contract(self.integration_contract())
        rows = {r['name']: r for r in report['checks']}
        self.assertEqual(report['status'], 'UNVERIFIED')
        self.assertEqual(rows['smoke_t4']['status'], 'UNVERIFIED')
        self.assertIn('T4 not authorized', rows['smoke_t4']['reason'])
        self.assertFalse((self.root / 'run/smoke_t4/executed.txt').exists())
        self.assertEqual(rows['asan_ubsan']['status'], 'PASS')
        self.assertTrue((self.root / 'run/asan_ubsan/executed.txt').is_file())
        self.assertEqual(len(report['checks']), 9)
        self.assertEqual(report['evidence_scope'], 'fixture')

    def test_t4_without_skip_still_requires_four_thread_authorization(self):
        with self.assertRaisesRegex(ValueError, 'four-thread'):
            self.run_contract(self.integration_contract(skip=False))

    def test_skipping_sanitizer_refused(self):
        c = self.integration_contract()
        c['stages']['asan_ubsan'] = {'skip_reason': 'not allowed'}
        with self.assertRaisesRegex(ValueError, 'only smoke_t4'):
            self.run_contract(c)

    def test_empty_skip_reason_refused(self):
        c = self.integration_contract()
        c['stages']['smoke_t4']['skip_reason'] = '   '
        with self.assertRaisesRegex(ValueError, 'skip_reason'):
            self.run_contract(c)

    def test_skip_and_argv_ambiguity_refused(self):
        c = self.integration_contract()
        c['stages']['smoke_t4']['argv'] = ['do not execute']
        with self.assertRaisesRegex(ValueError, 'skip_reason'):
            self.run_contract(c)

    def test_unknown_identity_mode_refused_before_launch(self):
        c = self.integration_contract()
        c['identity_mode'] = 'anything'
        with self.assertRaisesRegex(ValueError, 'identity_mode'):
            self.run_contract(c)

    def test_failure_before_t4_still_stops_later_stages(self):
        c = self.integration_contract()
        c['expected_off_nodes']['20'] += 1
        report = self.run_contract(c)
        rows = {r['name']: r for r in report['checks']}
        self.assertEqual(report['status'], 'FAIL')
        self.assertEqual(rows['off_pins']['status'], 'FAIL')
        self.assertEqual(rows['asan_ubsan']['status'], 'UNVERIFIED')
        self.assertFalse((self.root / 'run/asan_ubsan/executed.txt').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
