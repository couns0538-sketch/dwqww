"""Mocked runner safety checks only; no chess games or strength evidence.

The subprocess fixtures are short Python programs. Frozen likelihood values
exercise the independent 0/+10 audit without launching an engine or Fastchess.
"""
import ast
import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
RUNNER = REPO / '.github/hosted-tt-refresh-strength/run_hosted.py'
VALIDATOR = REPO / 'tools/match/windows_validate.py'
MATCH_RUNNER = RUNNER.parent / 'match/run_match.py'
PROTOCOL = RUNNER.parent / 'protocol.json'


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner = load_module('promotion_see_strength_runner_under_test', RUNNER)
validator = load_module('promotion_see_strength_reference_validator', VALIDATOR)
FROZEN_CANDIDATE_SHA = runner.CANDIDATE_SHA


class InputRehashTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='mocked pin SEE strength inputs ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.paths = [self.root / 'first input', self.root / 'second input']
        for number, path in enumerate(self.paths):
            path.write_bytes(('mocked frozen input %d\n' % number).encode())
        self.frozen = {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in self.paths}

    def test_unchanged_inputs_have_matching_final_hashes(self):
        result = runner.rehash_inputs(self.frozen)
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(result['mismatches'], [])
        self.assertEqual(set(result['inputs']), set(self.frozen))
        for name, digest in self.frozen.items():
            self.assertEqual(result['inputs'][name]['expected_sha256'], digest)
            self.assertEqual(result['inputs'][name]['actual_sha256'], digest)
            self.assertIs(result['inputs'][name]['matches'], True)

    def test_changed_input_is_reported_with_actual_digest(self):
        changed = self.paths[0]
        changed.write_bytes(b'mocked changed input\n')
        result = runner.rehash_inputs(self.frozen)
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['mismatches'], [str(changed)])
        row = result['inputs'][str(changed)]
        self.assertEqual(row['expected_sha256'], self.frozen[str(changed)])
        self.assertEqual(row['actual_sha256'], hashlib.sha256(changed.read_bytes()).hexdigest())
        self.assertIs(row['matches'], False)
        self.assertIs(result['inputs'][str(self.paths[1])]['matches'], True)

    def test_missing_input_is_reported_and_other_inputs_are_still_checked(self):
        missing = self.paths[0]
        missing.unlink()
        result = runner.rehash_inputs(self.frozen)
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['mismatches'], [str(missing)])
        self.assertIs(result['inputs'][str(missing)]['matches'], False)
        self.assertTrue(result['inputs'][str(missing)]['error'])
        self.assertIs(result['inputs'][str(self.paths[1])]['matches'], True)

    def test_final_rehash_cannot_leave_success_after_mutation(self):
        report = {'status': 'completed', 'sprt': {'decision': 'H1_accepted'}}
        self.paths[0].write_bytes(b'mocked mutation after successful result\n')
        runner.ensure_final_inputs(report, self.frozen)
        self.assertEqual(report['status'], 'failed_or_inconclusive_no_acceptance')
        self.assertEqual(report['final_input_rehash']['status'], 'failed')
        self.assertTrue(report['error'])

    def test_final_rehash_cannot_leave_success_after_deletion(self):
        report = {'status': 'completed', 'sprt': {'decision': 'H1_accepted'}}
        self.paths[1].unlink()
        runner.ensure_final_inputs(report, self.frozen)
        self.assertEqual(report['status'], 'failed_or_inconclusive_no_acceptance')
        self.assertEqual(report['final_input_rehash']['mismatches'], [str(self.paths[1])])

    def test_final_rehash_keeps_a_passing_report_and_records_evidence(self):
        report = {'status': 'completed'}
        runner.ensure_final_inputs(report, self.frozen)
        self.assertEqual(report['status'], 'completed')
        self.assertEqual(report['final_input_rehash']['status'], 'passed')

class LikelihoodAuditTest(unittest.TestCase):
    @staticmethod
    def console(llr, decision=None):
        text = 'Mocked fixture only; no chess evidence\nLLR: %s\n' % llr
        if decision:
            text += 'SPRT test completed - %s was accepted\n' % decision
        return text

    def audit(self, penta, llr, decision=None, pairs=None, cap=128):
        return runner.audit_likelihood(self.console(llr, decision), penta,
                                       sum(penta) if pairs is None else pairs, cap, validator)

    def test_h1_uses_zero_plus_ten_and_independent_boundary_crossing(self):
        penta = [0, 0, 0, 0, 104]
        with patch.object(validator, 'logistic_llr', wraps=validator.logistic_llr) as compute:
            decision, audit = self.audit(penta, '2.95', 'H1')
        compute.assert_called_once_with(penta, 0, 10)
        self.assertEqual(decision, 'H1_accepted')
        self.assertAlmostEqual(audit['independent_llr'], 2.950344550755079, places=11)
        self.assertGreater(audit['independent_llr'], math.log(19))
        self.assertEqual(audit['native_printed_llr'], 2.95)

    def test_h0_requires_independent_lower_boundary(self):
        decision, audit = self.audit([101, 0, 0, 0, 0], '-2.95', 'H0')
        self.assertEqual(decision, 'H0_accepted')
        self.assertAlmostEqual(audit['independent_llr'], -2.9489024135909996, places=11)

    def test_pair_cap_is_inconclusive_when_no_boundary_is_crossed(self):
        decision, audit = self.audit([32, 0, 64, 0, 32], '-.11')
        self.assertEqual(decision, 'inconclusive_at_pair_cap')
        self.assertAlmostEqual(audit['independent_llr'], -0.1059820071203011, places=11)
        self.assertEqual((audit['elo0'], audit['elo1']), (0, 10))

    def test_native_likelihood_mismatch_cannot_accept(self):
        with self.assertRaises(ValueError):
            self.audit([0, 0, 20, 0, 0], '2.95', 'H1')

    def test_native_acceptance_cannot_replace_true_boundary_crossing(self):
        with self.assertRaises(ValueError):
            self.audit([0, 0, 0, 0, 103], '2.92', 'H1')

    def test_missing_native_decision_before_cap_cannot_accept(self):
        with self.assertRaises(ValueError):
            self.audit([0, 0, 20, 0, 0], '-.58')

    def test_missing_native_decision_at_crossed_boundary_cannot_accept(self):
        with self.assertRaises(ValueError):
            self.audit([0, 0, 0, 0, 104], '2.95', cap=104)

    def test_exactly_one_native_decision_and_finite_final_token_are_required(self):
        good = self.console('2.95', 'H1')
        malformed = [good + 'LLR: nan\n', good + 'LLR: inf\n',
                     good + 'LLR: -inf\n', good + good,
                     good + self.console('-2.95', 'H0'), good + 'LLR: garbage\n']
        for console in malformed:
            with self.subTest(console=console), self.assertRaises(ValueError):
                runner.audit_likelihood(console, [0, 0, 0, 0, 104], 104, 128, validator)

    def test_zero_or_exceeded_pair_cap_is_rejected(self):
        for pairs, cap in [(104, 0), (104, 103), (True, 128), (104, True), (104.0, 128)]:
            with self.subTest(pairs=pairs, cap=cap), self.assertRaises(ValueError):
                self.audit([0, 0, 0, 0, 104], '2.95', 'H1', pairs=pairs, cap=cap)

    def test_retained_pair_count_must_match_pentanomial_total(self):
        with self.assertRaises(ValueError):
            self.audit([0, 0, 0, 0, 104], '2.95', 'H1', pairs=105)

    def test_final_llr_is_used_after_an_earlier_finite_value(self):
        console = 'LLR: 123.45\n' + self.console('-.11')
        decision, audit = runner.audit_likelihood(
            console, [32, 0, 64, 0, 32], 128, 128, validator)
        self.assertEqual(decision, 'inconclusive_at_pair_cap')
        self.assertEqual(audit['native_printed_llr'], -.11)

    def test_nonfinite_or_missing_llr_at_cap_cannot_be_inconclusive_success(self):
        for token in ('nan', 'inf', '-inf', 'garbage', ''):
            console = 'LLR: -.11\nLLR: ' + token + '\n' if token else 'No likelihood\n'
            with self.subTest(token=token), self.assertRaises(ValueError):
                runner.audit_likelihood(console, [32, 0, 64, 0, 32],
                                        128, 128, validator)

    def test_lower_boundary_also_requires_native_acceptance(self):
        with self.assertRaises(ValueError):
            self.audit([101, 0, 0, 0, 0], '-2.95', cap=101)

class IncrementalFaultScannerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='mocked incremental scanner ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.scanner = runner.FaultScanner(self.root)

    def test_initially_missing_files_are_allowed_and_later_creation_is_scanned(self):
        self.assertIsNone(self.scanner())
        path = self.root / 'console.txt'
        path.write_bytes(b'Warning: mocked new file fault\n')
        self.assertTrue(self.scanner())

    def test_complete_warning_error_fatal_and_bracket_levels_are_faults(self):
        for name, text in [('console.txt', b'Warning: mocked fault\n'),
                           ('console.txt', b' ERROR: mocked fault\n'),
                           ('console.txt', b'Fatal: mocked fault\n'),
                           ('fastchess.log', b'123 [WARN ] mocked fault\n'),
                           ('fastchess.log', b'123 [ERROR ] mocked fault\n'),
                           ('fastchess.log', b'123 [FATAL ] mocked fault\n')]:
            with self.subTest(name=name, text=text):
                path = self.root / name
                path.write_bytes(text)
                scanner = runner.FaultScanner(self.root)
                self.assertTrue(scanner())

    def test_warning_prefix_split_across_writes_is_detected(self):
        path = self.root / 'console.txt'
        path.write_bytes(b'War')
        self.assertIsNone(self.scanner())
        with path.open('ab') as stream:
            stream.write(b'ning: mocked split prefix\n')
        self.assertTrue(self.scanner())

    def test_termination_tag_split_across_writes_is_detected(self):
        path = self.root / 'games.pgn'
        path.write_bytes(b'[Termination "time')
        self.assertIsNone(self.scanner())
        with path.open('ab') as stream:
            stream.write(b' forfeit"]\n')
        self.assertTrue(self.scanner())

    def test_normal_termination_and_engine_communications_are_benign(self):
        (self.root / 'console.txt').write_bytes(
            b'Engine sent info string warning is text in a mocked fixture\n'
            b'Finished game 1 (mocked): 1/2-1/2\n')
        (self.root / 'fastchess.log').write_bytes(
            b'123 [engine] >> info depth 1 score cp 0\n'
            b'123 [engine] << bestmove e2e4\n')
        (self.root / 'games.pgn').write_bytes(b'[Termination "normal"]\n')
        self.assertIsNone(self.scanner())

    def test_later_truncation_is_a_fault(self):
        path = self.root / 'console.txt'
        path.write_bytes(b'mocked original long line\n')
        self.assertIsNone(self.scanner())
        path.write_bytes(b'short\n')
        self.assertTrue(self.scanner())

    def test_later_replacement_is_a_fault_even_at_same_size(self):
        path = self.root / 'fastchess.log'
        path.write_bytes(b'mocked original line\n')
        self.assertIsNone(self.scanner())
        replacement = self.root / 'replacement.log'
        replacement.write_bytes(b'mocked replaced line\n')
        replacement.replace(path)
        self.assertTrue(self.scanner())

    def test_later_deletion_is_a_fault(self):
        path = self.root / 'games.pgn'
        path.write_bytes(b'[Termination "normal"]\n')
        self.assertIsNone(self.scanner())
        path.unlink()
        self.assertTrue(self.scanner())

    def test_append_only_scan_reads_each_byte_once(self):
        path = self.root / 'fastchess.log'
        initial = b'mocked benign trace line\n' * 1000
        path.write_bytes(initial)
        self.assertIsNone(self.scanner())
        self.assertEqual(self.scanner.bytes_read, len(initial))
        for _ in range(10):
            self.assertIsNone(self.scanner())
        self.assertEqual(self.scanner.bytes_read, len(initial))
        appended = b'mocked appended partial'
        with path.open('ab') as stream:
            stream.write(appended)
        self.assertIsNone(self.scanner())
        self.assertEqual(self.scanner.bytes_read, len(initial) + len(appended))
        with path.open('ab') as stream:
            stream.write(b' line\n')
        self.assertIsNone(self.scanner())
        self.assertEqual(self.scanner.bytes_read, len(initial) + len(appended) + len(b' line\n'))

class OwnedSubprocessTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='mocked owned subprocess ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.stdout = self.root / 'mocked-process.stdout'
        self.pid_file = self.root / 'mocked-process-pids.json'
        self.pids = []
        self.addCleanup(self.cleanup_fixtures)

    @staticmethod
    def running(pid):
        try:
            # A killed orphan may wait briefly for the container's init to reap.
            # Zombie state cannot execute or consume engine resources.
            return Path('/proc/%d/stat' % pid).read_text().split(') ', 1)[1].split()[0] != 'Z'
        except FileNotFoundError:
            return False

    def cleanup_fixtures(self):
        if self.pid_file.exists():
            self.pids = json.loads(self.pid_file.read_text())
        for pid in self.pids:
            if self.running(pid):
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def owned_command(self):
        child = ('import signal,time; signal.signal(signal.SIGINT, signal.SIG_IGN); '
                 'print("mocked child only",flush=True); time.sleep(60)')
        code = ('import json,os,pathlib,subprocess,sys,time; '
                'child=subprocess.Popen([sys.executable,"-u","-c",' + repr(child) + ']); '
                'pathlib.Path(' + repr(str(self.pid_file)) + ').write_text(json.dumps([os.getpid(),child.pid])); '
                'print("mocked parent only; no chess evidence",flush=True); time.sleep(60)')
        return [sys.executable, '-u', '-c', code]

    def unrelated_process(self):
        unrelated = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'],
                                     start_new_session=True)
        def stop_unrelated():
            if unrelated.poll() is None:
                unrelated.kill()
            unrelated.wait(timeout=2)
        self.addCleanup(stop_unrelated)
        return unrelated

    def assert_owned_processes_stopped(self):
        self.assertTrue(self.pid_file.exists(), 'mocked parent did not write its process IDs')
        self.pids = json.loads(self.pid_file.read_text())
        until = time.monotonic() + 2
        while any(self.running(pid) for pid in self.pids) and time.monotonic() < until:
            time.sleep(0.01)
        self.assertFalse([pid for pid in self.pids if self.running(pid)],
                         'owned parent or child survived runner cleanup')

    def test_success_returns_exit_status_and_preserves_stdout(self):
        command = [sys.executable, '-c', 'print("mocked success only; no chess evidence")']
        result = runner.run_owned(command, self.stdout, lambda: None, None)
        self.assertEqual(result, 0)
        self.assertIn('mocked success only; no chess evidence', self.stdout.read_text())

    def test_fault_detected_after_quick_exit_is_not_lost(self):
        command = [sys.executable, '-c', 'print("mocked fault output",flush=True)']
        def fault():
            return ('mocked terminal fault' if self.stdout.exists()
                    and 'mocked fault output' in self.stdout.read_text() else None)
        with self.assertRaisesRegex(RuntimeError, 'mocked terminal fault'):
            runner.run_owned(command, self.stdout, fault, None)
        self.assertIn('mocked fault output', self.stdout.read_text())

    def test_successful_parent_exit_with_live_child_cannot_accept(self):
        unrelated = self.unrelated_process()
        child = ('import signal,time; signal.signal(signal.SIGINT, signal.SIG_IGN); '
                 'time.sleep(60)')
        code = ('import json,os,pathlib,subprocess,sys; '
                'child=subprocess.Popen([sys.executable,"-u","-c",' + repr(child) + ']); '
                'pathlib.Path(' + repr(str(self.pid_file)) + ').write_text(json.dumps([os.getpid(),child.pid])); '
                'print("mocked successful parent with surviving child",flush=True)')
        with self.assertRaisesRegex(RuntimeError, 'descendant survived'):
            runner.run_owned([sys.executable, '-u', '-c', code],
                             self.stdout, lambda: None, None)
        self.assert_owned_processes_stopped()
        self.assertIsNone(unrelated.poll(), 'orphan cleanup killed an unrelated process group')
        self.assertIn('mocked successful parent', self.stdout.read_text())

    def test_live_fault_stops_owned_parent_and_child(self):
        unrelated = self.unrelated_process()
        def fault():
            return 'mocked live fault' if self.pid_file.exists() else None
        with self.assertRaisesRegex(RuntimeError, 'mocked live fault'):
            runner.run_owned(self.owned_command(), self.stdout, fault, None)
        self.assert_owned_processes_stopped()
        self.assertIsNone(unrelated.poll(), 'fault cleanup killed an unrelated process group')
        self.assertIn('mocked parent only; no chess evidence', self.stdout.read_text())

    def test_emergency_deadline_stops_owned_parent_and_child(self):
        unrelated = self.unrelated_process()
        real_monotonic = time.monotonic
        started = real_monotonic()
        def emergency_clock():
            # Trigger the deadline after the real parent/child startup handshake;
            # shared-host Python startup can itself exceed a short wall timeout.
            ready = (self.pid_file.exists() and self.stdout.exists()
                     and 'mocked parent only' in self.stdout.read_text())
            return started + 1 if ready or real_monotonic() - started > 5 else started
        with patch.object(runner.time, 'monotonic', side_effect=emergency_clock), \
                self.assertRaisesRegex(RuntimeError, 'deadline'):
            runner.run_owned(self.owned_command(), self.stdout, lambda: None, 0.25)
        self.assert_owned_processes_stopped()
        self.assertIsNone(unrelated.poll(), 'cleanup killed an unrelated process group')
        self.assertIn('mocked parent only; no chess evidence', self.stdout.read_text())

    def test_fault_scanner_exception_still_stops_owned_group(self):
        def fault():
            if self.pid_file.exists():
                raise ValueError('mocked scanner failure')
            return None
        with self.assertRaisesRegex(ValueError, 'mocked scanner failure'):
            runner.run_owned(self.owned_command(), self.stdout, fault, None)
        self.assert_owned_processes_stopped()

    def test_keyboard_interrupt_stops_owned_group_and_preserves_unrelated_process(self):
        unrelated = self.unrelated_process()
        def interrupted():
            if self.pid_file.exists():
                raise KeyboardInterrupt('mocked cancellation only')
            return None
        with self.assertRaisesRegex(KeyboardInterrupt, 'mocked cancellation only'):
            runner.run_owned(self.owned_command(), self.stdout, interrupted, None)
        self.assert_owned_processes_stopped()
        self.assertIsNone(unrelated.poll(), 'cancellation killed an unrelated process group')
        self.assertIn('mocked parent only; no chess evidence', self.stdout.read_text())

if __name__ == '__main__':
    unittest.main(verbosity=2)
