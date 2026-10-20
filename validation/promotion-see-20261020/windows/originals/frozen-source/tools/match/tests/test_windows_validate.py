"""Acceptance-safety tests; fake only the unavailable Windows process boundary."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch


RUNNER = Path(__file__).resolve().parents[1] / 'windows_validate.py'
SPEC = importlib.util.spec_from_file_location('windows_validate', RUNNER)
validator = importlib.util.module_from_spec(SPEC)
if RUNNER.exists():
    SPEC.loader.exec_module(validator)


class BundleTest(unittest.TestCase):
    def setUp(self):
        self.assertTrue(RUNNER.exists(), 'native Windows validation runner is missing')
        self.temp = tempfile.TemporaryDirectory(prefix='forge validation ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'bundle with spaces'
        self.root.mkdir()
        required = ['engine/candidate.exe', 'engine/original-6.4.exe',
                    'fastchess/fastchess.exe', 'runtime/python.exe']
        for name in required:
            path = self.root / name
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(b'MZportable fixture')
        shutil.copy(RUNNER.parent / 'pgn_stats.py', self.root / 'pgn_stats.py')
        (self.root / 'windows_validate.py').write_text('# frozen runner fixture\n')
        corpus = RUNNER.parents[1] / 'openings/forge-10000.epd'
        positions = [' '.join(line.split()[:4]) for line in corpus.read_text().splitlines()
                     if line.strip() and line.split()[3] == '-']
        (self.root / 'openings').mkdir()
        start = 0
        for phase, count in [('aa', 4), ('pilot', 8), ('sprt', 5000)]:
            (self.root / 'openings' / (phase + '.epd')).write_text(
                '\n'.join(positions[start:start + count]) + '\n')
            start += count
        self.manifest = {'schema_version': 1,
                         'provenance': {'fastchess_source': validator.PIN,
                                        'candidate': {'source': 'candidate source and build'},
                                        'original': {'source': 'original source and build'}},
                         'files': {p.relative_to(self.root).as_posix(): validator.sha(p)
                                   for p in self.root.rglob('*') if p.is_file()}}
        self.save_manifest()

    def save_manifest(self):
        (self.root / 'manifest.json').write_text(json.dumps(self.manifest))

    def phase_files(self, out, phase, *, fault=None, decision='H1', llr=None, count=None, penta=None):
        out.mkdir(parents=True, exist_ok=True)
        selected = (self.root / 'openings' / (phase + '.epd')).read_text().splitlines()
        if penta is None:
            if phase != 'sprt':
                penta = [0, 0, {'aa': 4, 'pilot': 8}[phase], 0, 0]
            elif decision == 'H0':
                penta = [count or 204, 0, 0, 0, 0]
            elif count == 5000 and decision is None:
                penta = [1000, 0, 3000, 0, 1000]
            else:
                penta = [0, 0, 0, 0, count or 207]
        count = sum(penta)
        if llr is None:
            # Independently frozen reference values, not computed by the runner.
            llr = '-2.96' if decision == 'H0' else '-1.29' if count == 5000 else '2.96'
        outcomes = [('0-1', '1-0'), ('0-1', '1/2-1/2'), ('1/2-1/2', '1/2-1/2'),
                    ('1/2-1/2', '0-1'), ('1-0', '0-1')]
        # Mix the balanced-cap fixture so it does not begin with a native lower
        # boundary crossing before its final inconclusive counts are reached.
        remaining, pair_outcomes = list(penta), []
        while any(remaining):
            for index, pair in enumerate(outcomes):
                if remaining[index]:
                    pair_outcomes.append(pair)
                    remaining[index] -= 1
        blocks = []
        for number, fen in enumerate(selected[:count], 1):
            for reverse in (False, True):
                white, black = ('Baseline', 'Candidate') if reverse else ('Candidate', 'Baseline')
                termination = 'time forfeit' if fault == 'timeout' and number == 1 else 'normal'
                moves = 'd2d4' if fault == 'aa_moves' and reverse else 'e2e4'
                if fault == 'orphan' and number == count and reverse:
                    continue
                if fault == 'wrong_prefix':
                    fen = selected[number + 1]
                result = pair_outcomes[number - 1][int(reverse)]
                blocks.append(f'[Event "Validation"]\n[Round "{number}"]\n'
                              f'[White "{white}"]\n[Black "{black}"]\n'
                              f'[FEN "{fen} 0 1"]\n[Termination "{termination}"]\n'
                              f'[Result "{result}"]\n\n'
                              f'1. {moves} {result}\n\n')
        (out / 'games.pgn').write_text(''.join(blocks))
        console = f'Ptnml(0-2): {penta}\n'
        if phase == 'sprt':
            console += f'LLR: {llr}\n'
            if decision:
                console += f'SPRT test completed - {decision} was accepted\n'
        if fault == 'warning':
            console += 'Warning: engine failed\n'
        (out / 'console.txt').write_text(console)
        (out / 'fastchess.log').write_text('trace engine conversation\n')

    def test_bundle_supports_spaces_and_freezes_manifest(self):
        _, frozen = validator.load_bundle(self.root)
        self.assertIn('manifest.json', frozen)
        command = validator.phase_command(self.root, self.root / 'results', 'pilot')
        self.assertIn('cmd=engine/candidate.exe', command)
        self.assertIn('tc=10+0.1', command)
        self.assertIn('timeleft=true', command)
        self.assertIn('option.Ponder=false', command)
        self.assertIn('option.Move Overhead=100', command)
        self.assertIn('-strict', command)
        self.assertNotIn('-resign', command)

    def test_rejects_non_ascii_and_traversal(self):
        with self.assertRaisesRegex(ValueError, 'ASCII'):
            validator.load_bundle(self.root / 'é')
        self.manifest['files']['../escape.exe'] = '0' * 64
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, 'relative'):
            validator.load_bundle(self.root)

    def test_rejects_changed_binary_before_play(self):
        (self.root / 'engine/candidate.exe').write_bytes(b'MZchanged')
        with self.assertRaisesRegex(ValueError, 'checksum'):
            validator.load_bundle(self.root)

    def test_unfrozen_runtime_dependency_is_rejected(self):
        (self.root / 'runtime/unrecorded.dll').write_bytes(b'MZunfrozen dependency')
        with self.assertRaisesRegex(ValueError, 'Unlisted'):
            validator.load_bundle(self.root)

    def test_normal_deterministic_aa_is_readiness_only(self):
        out = self.root / 'aa-output'
        self.phase_files(out, 'aa')
        result = validator.audit_phase(self.root, out, 'aa')
        self.assertEqual(result['status'], 'aa_passed')
        self.assertFalse(result['equal_clock_gain_established'])

    def test_fault_or_orphan_never_accepts_native_h1(self):
        for fault in ('timeout', 'orphan', 'wrong_prefix', 'warning'):
            with self.subTest(fault=fault):
                out = self.root / fault
                self.phase_files(out, 'sprt', fault=fault)
                with self.assertRaises(ValueError):
                    validator.audit_phase(self.root, out, 'sprt')

    def test_aa_requires_identical_moves(self):
        out = self.root / 'aa-fault'
        self.phase_files(out, 'aa', fault='aa_moves')
        with self.assertRaisesRegex(ValueError, 'deterministic'):
            validator.audit_phase(self.root, out, 'aa')

    def test_acceptance_uses_final_llr_and_exactly_one_decision(self):
        good = 'LLR: 3.0\nSPRT completed - H1 was accepted\n'
        self.assertEqual(validator.native_acceptance(good), 'H1_accepted')
        for text in (good + 'LLR: nan\n', good + 'LLR: inf\n', good + good):
            with self.subTest(text=text), self.assertRaises(ValueError):
                validator.native_acceptance(text)

    def test_h0_is_a_completed_test_without_a_gain_claim(self):
        out = self.root / 'h0'
        self.phase_files(out, 'sprt', decision='H0')
        result = validator.audit_phase(self.root, out, 'sprt')
        self.assertEqual(result['sprt_decision'], 'H0_accepted')
        self.assertFalse(result['equal_clock_gain_established'])
        self.assertAlmostEqual(result['likelihood_audit']['independent_llr'], -2.9569492106241353)

    def test_full_cap_without_native_boundary_is_inconclusive(self):
        out = self.root / 'cap'
        self.phase_files(out, 'sprt', count=5000, decision=None)
        result = validator.audit_phase(self.root, out, 'sprt')
        self.assertEqual(result['sprt_decision'], 'inconclusive_at_pair_cap')
        self.assertFalse(result['equal_clock_gain_established'])

    def test_native_penta_must_agree_with_retained_games(self):
        out = self.root / 'penta'
        self.phase_files(out, 'sprt')
        path = out / 'console.txt'
        path.write_text(path.read_text().replace('[0, 0, 0, 0, 207]', '[0, 0, 0, 1, 206]'))
        with self.assertRaisesRegex(ValueError, 'pentanomial'):
            validator.audit_phase(self.root, out, 'sprt')

    def test_finite_native_h1_needs_mathematically_consistent_pair_likelihood(self):
        out = self.root / 'false-acceptance'
        self.phase_files(out, 'sprt', penta=[0, 0, 2, 0, 0], llr='2.96')
        with self.assertRaisesRegex(ValueError, 'likelihood'):
            validator.audit_phase(self.root, out, 'sprt')

    def test_acceptance_needs_independent_boundary_crossing(self):
        out = self.root / 'inside-bounds'
        # Rounded native2.94 can equal rounded upperbound while trueLLR isinside.
        self.phase_files(out, 'sprt', count=206, llr='2.94')
        with self.assertRaisesRegex(ValueError, 'crossing'):
            validator.audit_phase(self.root, out, 'sprt')

    def test_cap_with_boundary_crossing_is_invalid_without_native_acceptance(self):
        out = self.root / 'crossed-cap'
        self.phase_files(out, 'sprt', decision=None, penta=[0, 0, 5000, 0, 0], llr='-72.46')
        with self.assertRaisesRegex(ValueError, 'crossing'):
            validator.audit_phase(self.root, out, 'sprt')

    def test_positive_early_stop_without_boundary_is_invalid(self):
        out = self.root / 'no-boundary'
        self.phase_files(out, 'sprt', decision=None)
        with self.assertRaisesRegex(ValueError, 'boundary'):
            validator.audit_phase(self.root, out, 'sprt')

    def test_gate_stops_after_aa_fault_and_preserves_logs(self):
        phases = []
        owner = self
        class FakeProcess:
            pid = 123
            returncode = None
            def __init__(self, command, **kwargs):
                phase = 'aa'
                phases.append(phase)
                path = Path(command[command.index('-pgnout') + 1][5:]).parent
                owner.phase_files(path, phase, fault='aa_moves')
                self.returncode = 0
            def wait(self, timeout=None): return self.returncode
            def poll(self): return self.returncode
        out = self.root / 'attempt'
        with patch.object(validator.subprocess, 'Popen', FakeProcess), \
             patch.object(validator, 'host_info', return_value={'test_host': True}), \
             patch.object(validator, 'runner_version', return_value='Fastchess ' + validator.PIN[:7]):
            result = validator.run_validation(self.root, out)
        self.assertEqual(phases, ['aa'])
        self.assertEqual(result['status'], 'failed_or_interrupted')
        self.assertFalse(result['equal_clock_gain_established'])
        self.assertTrue((out / 'aa/fastchess.log').exists())

    def test_interrupt_stops_child_and_keeps_attempt_invalid(self):
        stopped = []
        class FakeProcess:
            pid = 124
            returncode = None
            def __init__(self, command, **kwargs): pass
            def wait(self, timeout=None):
                if self.returncode is None:
                    raise KeyboardInterrupt()
                return self.returncode
            def poll(self): return self.returncode
            def send_signal(self, signum):
                stopped.append(signum)
                self.returncode = 1
            def terminate(self):
                stopped.append('terminate')
                self.returncode = 1
            def kill(self): self.returncode = 1
        out = self.root / 'interrupted'
        with patch.object(validator.subprocess, 'Popen', FakeProcess), \
             patch.object(validator, 'host_info', return_value={'test_host': True}), \
             patch.object(validator, 'runner_version', return_value='Fastchess ' + validator.PIN[:7]):
            result = validator.run_validation(self.root, out)
        self.assertTrue(stopped)
        self.assertEqual(result['status'], 'failed_or_interrupted')
        self.assertTrue((out / 'protocol.json').exists())

    def test_hash_change_after_games_blocks_next_gate(self):
        phases = []
        owner = self
        class FakeProcess:
            pid = 125
            returncode = 0
            def __init__(self, command, **kwargs):
                phases.append('aa')
                path = Path(command[command.index('-pgnout') + 1][5:]).parent
                owner.phase_files(path, 'aa')
                (owner.root / 'engine/candidate.exe').write_bytes(b'MZchanged during play')
            def wait(self, timeout=None): return 0
            def poll(self): return 0
        with patch.object(validator.subprocess, 'Popen', FakeProcess), \
             patch.object(validator, 'host_info', return_value={'test_host': True}), \
             patch.object(validator, 'runner_version', return_value='Fastchess ' + validator.PIN[:7]):
            result = validator.run_validation(self.root, self.root / 'hash-changed')
        self.assertEqual(phases, ['aa'])
        self.assertEqual(result['status'], 'failed_or_interrupted')
        self.assertIn('checksum', result['phases']['aa']['error'])

    def test_complete_gates_accept_only_final_native_decision(self):
        phases = []
        owner = self
        class FakeProcess:
            pid = 126
            returncode = 0
            def __init__(self, command, **kwargs):
                path = Path(command[command.index('-pgnout') + 1][5:]).parent
                phases.append(path.name)
                owner.phase_files(path, path.name)
            def wait(self, timeout=None): return 0
            def poll(self): return 0
        with patch.object(validator.subprocess, 'Popen', FakeProcess), \
             patch.object(validator, 'host_info', return_value={'test_host': True}), \
             patch.object(validator, 'runner_version', return_value='Fastchess ' + validator.PIN[:7]):
            result = validator.run_validation(self.root, self.root / 'accepted')
        self.assertEqual(phases, ['aa', 'pilot', 'sprt'])
        self.assertEqual(result['status'], 'completed')
        self.assertTrue(result['equal_clock_gain_established'])
        self.assertIn('does not prove >=5', result['claim_scope'])


if __name__ == '__main__':
    unittest.main()
