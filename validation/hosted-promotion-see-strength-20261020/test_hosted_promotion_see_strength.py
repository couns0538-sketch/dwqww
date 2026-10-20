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
RUNNER = REPO / '.github/hosted-promotion-see-strength/run_hosted.py'
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


class PackageInventoryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='mocked package inventory ')
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.package = self.repo / '.github/hosted-promotion-see-strength'
        self.inventory = self.package / 'PACKAGE-SHA256SUMS'
        self.files = {
            '.github/hosted-promotion-see-strength/z.py': b'last root file\n',
            '.github/hosted-promotion-see-strength/nested/a.py': b'nested file\n',
            '.github/workflows/forge-hosted-promotion-see-strength.yml': b'mocked workflow\n',
        }
        for relative, data in self.files.items():
            path = self.repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        self.expected = {relative: hashlib.sha256(data).hexdigest()
                         for relative, data in self.files.items()}
        self.lines = [self.expected[relative] + '  ' + relative
                      for relative in sorted(self.files)]
        self.write_inventory(self.lines)

    def write_inventory(self, lines):
        self.inventory.write_text('\n'.join(lines) + '\n')

    def test_valid_inventory_uses_relative_posix_order_and_hashes(self):
        self.assertEqual(runner.verify_package_inventory(self.repo, self.package), self.expected)
        self.assertEqual(list(runner.verify_package_inventory(self.repo, self.package)),
                         sorted(self.files))

    def test_workflow_relative_package_path_is_resolved(self):
        original = Path.cwd()
        try:
            os.chdir(self.repo)
            self.assertEqual(runner.verify_package_inventory(Path.cwd(), Path('.github/hosted-promotion-see-strength')), self.expected)
        finally:
            os.chdir(original)

    def test_changed_file_cannot_pass_current_self_hash(self):
        (self.package / 'z.py').write_bytes(b'changed after freeze\n')
        with self.assertRaisesRegex(ValueError, 'self hash mismatch'):
            runner.verify_package_inventory(self.repo, self.package)

    def test_missing_file_cannot_pass_inventory(self):
        (self.package / 'nested/a.py').unlink()
        with self.assertRaisesRegex(ValueError, 'file set/order mismatch'):
            runner.verify_package_inventory(self.repo, self.package)

    def test_unregistered_extra_file_cannot_pass_inventory(self):
        (self.package / 'unexpected.txt').write_bytes(b'extra\n')
        with self.assertRaisesRegex(ValueError, 'file set/order mismatch'):
            runner.verify_package_inventory(self.repo, self.package)

    def test_reordered_inventory_cannot_pass(self):
        self.write_inventory(self.lines[::-1])
        with self.assertRaisesRegex(ValueError, 'file set/order mismatch'):
            runner.verify_package_inventory(self.repo, self.package)

    def test_duplicate_and_unsafe_inventory_paths_are_rejected(self):
        for line in (self.lines[0], 'a' * 64 + '  ../outside',
                     'a' * 64 + '  /absolute/path'):
            self.write_inventory(self.lines + [line])
            with self.subTest(line=line), self.assertRaisesRegex(ValueError, 'Malformed'):
                runner.verify_package_inventory(self.repo, self.package)

    def test_registered_python_bytecode_is_rejected(self):
        relative = '.github/hosted-promotion-see-strength/__pycache__/module.pyc'
        path = self.repo / relative
        path.parent.mkdir()
        path.write_bytes(b'mocked bytecode')
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        self.write_inventory(sorted(self.lines + [digest + '  ' + relative],
                                    key=lambda line: line.split('  ', 1)[1]))
        with self.assertRaisesRegex(ValueError, 'file set/order mismatch'):
            runner.verify_package_inventory(self.repo, self.package)


class CandidateBenchReadinessTest(unittest.TestCase):
    GOOD = 'bench depth 11 nodes 385781 time 123 nps 3136430\n'

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='mocked candidate bench ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.engine = self.root / 'pretend engine; never executable'

    def test_exact_candidate17_bench_signature_is_readiness_only(self):
        result = runner.verify_candidate_bench_signature(self.GOOD, '', 0, 385781)
        self.assertEqual(result['engine_nodes'], 385781)
        self.assertEqual(result['engine_ms'], 123)
        self.assertEqual(result['engine_nps'], 3136430)
        self.assertEqual(result['scope'], 'Signature readiness only; no speed comparison')

    def test_parent_signature_or_unfrozen_expected_count_is_rejected(self):
        for stdout, expected in ((self.GOOD.replace('385781', '385792'), 385781),
                                 (self.GOOD, 385792), (self.GOOD, 419798),
                                 (self.GOOD, True), (self.GOOD, None)):
            with self.subTest(stdout=stdout, expected=expected), self.assertRaises(ValueError):
                runner.verify_candidate_bench_signature(stdout, '', 0, expected)

    def test_missing_malformed_or_duplicate_signature_is_rejected(self):
        for stdout in ('', 'bench depth 11 nodes missing time 123 nps 456\n',
                       self.GOOD.replace('time 123', 'time nan'),
                       self.GOOD.replace('nps 3136430', 'nps -1'),
                       self.GOOD.replace('nps 3136430', 'nps 3136430garbage'),
                       self.GOOD + self.GOOD):
            with self.subTest(stdout=stdout), self.assertRaises(ValueError):
                runner.verify_candidate_bench_signature(stdout, '', 0, 385781)

    def test_nonzero_exit_or_any_stderr_is_rejected(self):
        for stderr, code in (('', 1), ('', -9), ('mocked stderr\n', 0), (' ', 0)):
            with self.subTest(stderr=stderr, code=code), self.assertRaises(ValueError):
                runner.verify_candidate_bench_signature(self.GOOD, stderr, code, 385781)

    def test_warning_error_or_fatal_prevents_acceptance(self):
        for fault in ('Warning: mocked fault\n', ' ERROR mocked fault\n',
                      '[WARN ] mocked fault\n', '[ERROR ] mocked fault\n',
                      '[FATAL ] mocked fault\n'):
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                runner.verify_candidate_bench_signature(self.GOOD + fault, '', 0, 385781)

    def mock_process(self, failure=None):
        from unittest.mock import Mock
        process = Mock(pid=5757, returncode=0)
        def communicate(**kwargs):
            (self.root / 'candidate-bench11.stdout').write_text(self.GOOD)
            (self.root / 'candidate-bench11.stderr').write_text('')
            if failure is not None:
                raise failure
            return None, None
        process.communicate.side_effect = communicate
        return process

    def test_one_probe_uses_frozen_stdin_ten_second_guard_and_new_group(self):
        process = self.mock_process()
        with patch.object(runner.subprocess, 'Popen', return_value=process) as popen, \
                patch.object(runner.os, 'killpg', side_effect=ProcessLookupError) as group, \
                patch.object(runner.time, 'monotonic', side_effect=[100, 100.1, 100.2]):
            result = runner.candidate_bench_readiness(self.engine, self.root, 385781)
        self.assertEqual(popen.call_count, 1)
        self.assertEqual(popen.call_args.args, ([str(self.engine)],))
        self.assertTrue(popen.call_args.kwargs['start_new_session'])
        self.assertIs(popen.call_args.kwargs['stdin'], subprocess.PIPE)
        self.assertTrue(popen.call_args.kwargs['text'])
        self.assertEqual(process.communicate.call_count, 1)
        self.assertEqual(process.communicate.call_args.kwargs['input'], 'bench 11\nquit\n')
        self.assertAlmostEqual(process.communicate.call_args.kwargs['timeout'], 9.9)
        group.assert_called_once_with(process.pid, 0)
        self.assertEqual(result['engine_nodes'], 385781)
        self.assertTrue(result['owned_process_group_empty'])
        self.assertEqual(result['guard_seconds'], 10)
        self.assertEqual(json.loads((self.root / 'candidate-bench11.json').read_text()), result)

    def test_probe_timeout_preserves_raw_output_and_cleans_only_owned_group(self):
        process = self.mock_process(subprocess.TimeoutExpired('mocked bench', 10))
        with patch.object(runner.subprocess, 'Popen', return_value=process) as popen, \
                patch.object(runner, 'stop_group') as stop, \
                patch.object(runner.os, 'killpg') as group, \
                patch.object(runner.time, 'monotonic', side_effect=[100, 100.1]):
            with self.assertRaises(subprocess.TimeoutExpired):
                runner.candidate_bench_readiness(self.engine, self.root, 385781)
        self.assertEqual(popen.call_count, 1)
        stop.assert_called_once_with(process)
        group.assert_not_called()
        self.assertEqual((self.root / 'candidate-bench11.stdout').read_text(), self.GOOD)
        self.assertFalse((self.root / 'candidate-bench11.json').exists())

    def test_probe_orphan_invalidates_and_calls_owned_cleanup(self):
        process = self.mock_process()
        with patch.object(runner.subprocess, 'Popen', return_value=process), \
                patch.object(runner, 'stop_group') as stop, \
                patch.object(runner.os, 'killpg') as group, \
                patch.object(runner.time, 'monotonic', side_effect=[100, 100.1]):
            with self.assertRaisesRegex(ValueError, 'descendant survived'):
                runner.candidate_bench_readiness(self.engine, self.root, 385781)
        group.assert_called_once_with(process.pid, 0)
        stop.assert_called_once_with(process)
        self.assertEqual((self.root / 'candidate-bench11.stdout').read_text(), self.GOOD)
        self.assertFalse((self.root / 'candidate-bench11.json').exists())


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


class FrozenCliAndReviewGateTest(unittest.TestCase):
    def setUp(self):
        # Only fixture-level gate checks use this pretend source. No process runs.
        self.mock_candidate = 'f' * 40
        source_pin = patch.object(runner, 'CANDIDATE_SHA', self.mock_candidate)
        source_pin.start()
        self.addCleanup(source_pin.stop)

    def test_actual_freeze_uses_candidate17_source_version_and_seed(self):
        protocol = json.loads(PROTOCOL.read_text())
        exact_candidate = '47f0560221d986e41a309853e1295c557fcf5bf6'
        self.assertEqual(FROZEN_CANDIDATE_SHA, exact_candidate)
        self.assertEqual(protocol['candidate_sha'], exact_candidate)
        self.assertEqual(protocol['candidate_version'], '6.4.17')
        self.assertEqual(protocol['baseline_sha'], '21538ec5416c909fc98a08688242a0b3b9710b25')
        self.assertEqual(protocol['baseline_version'], '6.4.14')
        self.assertEqual(protocol['seed'], 20261025)

    def test_copied_candidate16_source_version_or_seed_cannot_launch(self):
        original = self.ready_protocol()
        for key, value in (
                ('candidate_sha', '553caef144ae2e1b696ba35d7a0eb1a50a03fde9'),
                ('candidate_version', '6.4.16'),
                ('seed', 20261024)):
            protocol = copy.deepcopy(original)
            protocol[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                runner.require_launch_protocol(protocol)

    def test_match_cli_is_serial_zero_plus_ten_without_adjudication(self):
        source = MATCH_RUNNER.read_text()
        tree = ast.parse(source)
        strings = [node.value for node in ast.walk(tree)
                   if isinstance(node, ast.Constant) and isinstance(node.value, str)]
        for forbidden in ('-maxmoves', '-draw', '-resign'):
            self.assertNotIn(forbidden, source)
        self.assertIn('elo0=0', strings)
        self.assertIn('elo1=10', strings)
        lists = [[item.value if isinstance(item, ast.Constant) else None for item in node.elts]
                 for node in ast.walk(tree) if isinstance(node, ast.List)]
        self.assertTrue(any(values[index:index + 2] == ['-concurrency', '1']
                            for values in lists for index in range(len(values) - 1)),
                        'Fastchess command must freeze concurrency=1')

    def test_wrapper_freezes_128_pair_command_and_independent_audit(self):
        tree = ast.parse(RUNNER.read_text())
        literals = [node.value for node in ast.walk(tree) if isinstance(node, ast.Constant)]
        self.assertIn('128', literals, 'wrapper CLI must request all 128 preregistered pairs')
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Name) and node.func.id == 'audit_likelihood']
        self.assertEqual(len(calls), 1)
        self.assertIsInstance(calls[0].args[3], ast.Constant)
        self.assertEqual(calls[0].args[3].value, 128)

    def test_pending_review_protocol_rejects_before_processes_or_affinity(self):
        with tempfile.TemporaryDirectory(prefix='mocked pending strength protocol ') as directory:
            root = Path(directory)
            package = root / 'package'
            package.mkdir()
            # Deliberately omit source/build provenance: the review gate must fail first.
            (package / 'protocol.json').write_text(json.dumps({'status': 'PENDING_REVIEW'}))
            paths = []
            for name in ('baseline', 'candidate', 'fastchess'):
                path = root / name
                path.write_bytes(b'mocked input, never executable\n')
                paths.extend(['--' + name, str(path)])
            argv = [str(RUNNER), '--repo', str(root), '--package', str(package),
                    '--out', str(root / 'out')] + paths
            with patch.object(sys, 'argv', argv), \
                    patch.object(runner.subprocess, 'Popen') as popen, \
                    patch.object(runner.subprocess, 'run') as run, \
                    patch.object(runner.os, 'sched_setaffinity') as affinity:
                with self.assertRaisesRegex(ValueError, 'review'):
                    runner.main()
            popen.assert_not_called()
            run.assert_not_called()
            affinity.assert_not_called()

    @staticmethod
    def ready_protocol():
        protocol = copy.deepcopy(json.loads(PROTOCOL.read_text()))
        protocol.update(status='PREREGISTERED_REVIEWED_READY_FOR_SINGLE_PUSH',
                        candidate_sha=runner.CANDIDATE_SHA,
                        source_gates_status='PASSED',
                        correctness_evidence_sha256={'mocked-proof.txt': 'a' * 64},
                        operational_qualification_status='authorized_for_one_fresh_host_readiness_attempt_with_prior_anomalies_unresolved')
        return protocol

    def test_reviewed_protocol_preserves_seed_and_rejects_changed_settings(self):
        ready = self.ready_protocol()
        self.assertEqual(ready['seed'], 20261025)
        runner.require_launch_protocol(ready)
        ready['seed'] = 20261020
        with self.assertRaises(ValueError):
            runner.require_launch_protocol(ready)
        for field, replacement in (('elo0', -1), ('elo1', 5), ('alpha', .1),
                                   ('beta', .1), ('pair_cap', 500), ('game_cap', 1024),
                                   ('tc', '2+0.02'), ('concurrency', 2),
                                   ('emergency_seconds', 18000)):
            changed = self.ready_protocol()
            changed['sprt_settings'][field] = replacement
            with self.subTest(field=field), self.assertRaises(ValueError):
                runner.require_launch_protocol(changed)

    def test_status_alone_cannot_bypass_pending_source_and_correctness_gates(self):
        protocol = json.loads(PROTOCOL.read_text())
        # Model an incomplete source proof independently of the actual root gate state.
        protocol['source_gates_status'] = 'PENDING'
        protocol['correctness_evidence_sha256'] = {}
        protocol['operational_qualification_status'] = 'PENDING'
        protocol['status'] = 'PREREGISTERED_REVIEWED_READY_FOR_SINGLE_PUSH'
        protocol['candidate_sha'] = runner.CANDIDATE_SHA
        with self.assertRaisesRegex(ValueError, 'Source freeze'):
            runner.require_launch_protocol(protocol)
        protocol['source_gates_status'] = 'PASSED'
        with self.assertRaisesRegex(ValueError, 'Source freeze'):
            runner.require_launch_protocol(protocol)
        protocol['correctness_evidence_sha256'] = {'mocked-proof.txt': 'a' * 64}
        protocol['operational_qualification_status'] = 'authorized_for_one_fresh_host_readiness_attempt_with_prior_anomalies_unresolved'
        runner.require_launch_protocol(protocol)

    def test_pending_operational_qualification_cannot_launch(self):
        protocol = self.ready_protocol()
        for state in ('PENDING', 'PASSED'):
            protocol['operational_qualification_status'] = state
            with self.subTest(state=state), self.assertRaisesRegex(ValueError, 'Source freeze'):
                runner.require_launch_protocol(protocol)

    def test_source_identity_and_tool_pin_changes_are_rejected(self):
        original = self.ready_protocol()
        self.assertEqual(original['baseline_sha'], '21538ec5416c909fc98a08688242a0b3b9710b25')
        self.assertEqual(original['candidate_sha'], self.mock_candidate)
        self.assertEqual(json.loads(PROTOCOL.read_text())['candidate_sha'], FROZEN_CANDIDATE_SHA)
        for key, value in [('baseline_sha', '2' * 40),
                           ('candidate_sha', original['baseline_sha']),
                           ('candidate_sha', '1' * 40),
                           ('candidate_sha', '_'.join(('PENDING', 'ROOT', 'SOURCE', 'FREEZE'))),
                           ('fastchess_sha', '3' * 40),
                           ('baseline_version', '6.4.11'),
                           ('candidate_version', '6.4.14')]:
            changed = copy.deepcopy(original)
            changed[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                runner.require_launch_protocol(changed)

    def test_placeholder_candidate_cannot_launch_even_with_ready_flags(self):
        protocol = self.ready_protocol()
        placeholder = '_'.join(('PENDING', 'ROOT', 'SOURCE', 'FREEZE'))
        protocol['candidate_sha'] = placeholder
        with patch.object(runner, 'CANDIDATE_SHA', placeholder):
            with self.assertRaisesRegex(ValueError, 'Source freeze'):
                runner.require_launch_protocol(protocol)

    def test_placeholder_rejects_before_processes_or_affinity(self):
        with tempfile.TemporaryDirectory(prefix='mocked pending source protocol ') as directory:
            root = Path(directory)
            package = root / 'package'
            package.mkdir()
            protocol = self.ready_protocol()
            placeholder = '_'.join(('PENDING', 'ROOT', 'SOURCE', 'FREEZE'))
            protocol['candidate_sha'] = placeholder
            (package / 'protocol.json').write_text(json.dumps(protocol))
            paths = []
            for name in ('baseline', 'candidate', 'fastchess'):
                path = root / name
                path.write_bytes(b'mocked input, never executable\n')
                paths.extend(['--' + name, str(path)])
            argv = [str(RUNNER), '--repo', str(root), '--package', str(package),
                    '--out', str(root / 'out')] + paths
            with patch.object(sys, 'argv', argv), \
                    patch.object(runner, 'CANDIDATE_SHA', placeholder), \
                    patch.object(runner.subprocess, 'Popen') as popen, \
                    patch.object(runner.subprocess, 'run') as run, \
                    patch.object(runner.os, 'sched_setaffinity') as affinity:
                with self.assertRaisesRegex(ValueError, 'Source freeze'):
                    runner.main()
            popen.assert_not_called()
            run.assert_not_called()
            affinity.assert_not_called()

    def test_workflow_runs_review_gate_before_compiler_setup_or_build(self):
        workflow = (REPO / '.github/workflows/forge-hosted-promotion-see-strength.yml').read_text()
        gate = workflow.index('gate.require_launch_protocol(p)')
        self.assertLess(workflow.index('set -euo pipefail'), gate)
        for command in ('if ! command -v g++-14', 'cmake -S', 'cmake --build',
                        'ctest --test-dir', 'make -C'):
            with self.subTest(command=command):
                self.assertLess(gate, workflow.index(command))


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
