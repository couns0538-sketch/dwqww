"""Deterministic safety tests; no engines or measured performance trials run."""
import copy
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import shutil
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch


RUNNER = Path(__file__).with_name('run_hosted.py')


def load_runner():
    if not RUNNER.is_file():
        raise AssertionError('The bounded hosted runner has not been implemented')
    spec = importlib.util.spec_from_file_location('hosted_nnue_runner_test', RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def bench_output(nodes=419798, count=12):
    return ''.join('info string bench depth 11 nodes %d time 17 nps 24694\n' % nodes
                   for _ in range(count))


def kernel_output(**changes):
    row = dict(benchmark='public_nnue_update_microkernel', group='quiet',
               iterations=2000000, warmup_calls=16384, corpus_size=64,
               hidden_size=256, accumulator_bytes=2052, wall_ns=1000000000,
               cpu_ticks=1000000, clocks_per_sec=1000000, fp_control=8064,
               actual_counts=[0, 0, 2000000, 0, 0], corpus_seen=[12, 0, 240, 20, 4],
               input_hash_fnv1a64='0123456789abcdef', output_hash_fnv1a64='fedcba9876543210',
               checksum_scope='all_final_output_ring_lanes_and_validity_outside_timing',
               compiler='fixture compiler', flags_label='fixture strict flags',
               driver_avx2=True, driver_optimized=True,
               strict_math_preprocessor_check=True,
               core_and_driver_lto='must_be_disabled_and_verified_externally')
    row.update(changes)
    return json.dumps(row) + '\n'


def protocol():
    return dict(status='PREREGISTERED_REVIEWED_READY_FOR_SINGLE_PUSH',
                primary=dict(bench_depth=11, benches_per_process=12, expected_nodes=419798,
                             aa_pairs=6, ab_blocks=['ABBA', 'BAAB'] * 3),
                kernel=dict(iterations=2000000, group='quiet', aa_pairs=6,
                            ab_blocks=['ABBA', 'BAAB'] * 3),
                calibration=dict(each_ratio_min=.97, each_ratio_max=1.03,
                                 median_min=.99, median_max=1.01),
                analysis=dict(t_critical_df5=2.57058, claim_cpu_geomean_min=1.03,
                              claim_cpu_lower_ci_exclusive_min=1., claim_wall_geomean_exclusive_min=1.,
                              blocks=6, confidence=.95), attempts=1, fault_retries=0,
                bounds=dict(timing_minutes=10, per_process_timeout_seconds=45,
                            no_adaptive_iterations_or_retries=True, no_gameplay=True))


class ParseAndStatisticsTests(unittest.TestCase):
    def setUp(self):
        self.runner = load_runner()

    def test_all_twelve_bench_signatures_are_required(self):
        self.assertEqual(len(self.runner.parse_bench(bench_output())), 12)
        for text in [bench_output(count=11), bench_output(count=13),
                     bench_output(nodes=419797), bench_output() +
                     'info string bench depth 12 nodes 419798 time 1 nps 1\n']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.runner.parse_bench(text)

    def test_kernel_counts_and_finite_loop_times_are_required(self):
        self.runner.parse_kernel(kernel_output())
        for changes in [dict(iterations=1), dict(group='all'), dict(cpu_ticks=0),
                        dict(wall_ns=0), dict(wall_ns=float('nan')),
                        dict(actual_counts=[0, 0, 1999999, 0, 0]),
                        dict(strict_math_preprocessor_check=False)]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.runner.parse_kernel(kernel_output(**changes))

    def test_calibration_requires_each_ratio_and_both_medians(self):
        pairs = [dict(A=dict(cpu_seconds=1., wall_seconds=1.),
                      B=dict(cpu_seconds=1., wall_seconds=1.)) for _ in range(6)]
        self.assertTrue(self.runner.calibration(pairs)['passed'])
        pairs[0]['A']['cpu_seconds'] = 1.031
        self.assertFalse(self.runner.calibration(pairs)['passed'])
        pairs[0]['A']['cpu_seconds'] = 1.
        for pair in pairs:
            pair['A']['wall_seconds'] = 1.011
        self.assertFalse(self.runner.calibration(pairs)['passed'])
        with self.assertRaises(ValueError):
            self.runner.calibration(pairs[:5])

    def test_log_t_interval_uses_six_counterbalanced_block_ratios(self):
        ratios = [1.04, 1.05, 1.06, 1.07, 1.08, 1.09]
        blocks = [[dict(variant=v, cpu_seconds=r if v == 'A' else 1.,
                        wall_seconds=1.01 if v == 'A' else 1.) for v in order]
                  for order, r in zip(['ABBA', 'BAAB'] * 3, ratios)]
        result = self.runner.analyze_blocks(blocks)
        logs = [math.log(r) for r in ratios]
        mean = sum(logs) / 6
        se = math.sqrt(sum((x - mean) ** 2 for x in logs) / 5 / 6)
        self.assertAlmostEqual(result['cpu']['geomean'], math.exp(mean))
        self.assertAlmostEqual(result['cpu']['ci95_lower'], math.exp(mean - 2.57058 * se))
        self.assertTrue(result['qualifies_hosted_speed_claim'])
        for row in blocks[0]:
            row['wall_seconds'] = 1.
        self.assertTrue(self.runner.analyze_blocks(blocks)['wall']['geomean'] > 1.)
        for block in blocks:
            for row in block:
                row['wall_seconds'] = 1.
        self.assertFalse(self.runner.analyze_blocks(blocks)['qualifies_hosted_speed_claim'])
        with self.assertRaises(ValueError):
            self.runner.analyze_blocks(blocks[:5])


class ExperimentSafetyTests(unittest.TestCase):
    def setUp(self):
        self.runner = load_runner()
        self.temp = tempfile.TemporaryDirectory(prefix='mocked hosted nnue ')
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        package = root / 'package'
        frozen = root / 'frozen'
        package.mkdir()
        frozen.mkdir()
        (package / 'protocol.json').write_text(json.dumps(protocol()))
        shutil.copytree(package, frozen / 'package')
        (frozen / 'source.tar').write_bytes(b'frozen fixture source')
        self.binaries = []
        for name in ['baseline', 'candidate', 'baseline-kernel', 'candidate-kernel']:
            path = frozen / name
            path.write_bytes(name.encode())
            self.binaries.append(path)
        self.args = SimpleNamespace(package=package, frozen_root=frozen, out=root / 'out',
                                    baseline=self.binaries[0], candidate=self.binaries[1],
                                    baseline_kernel=self.binaries[2], candidate_kernel=self.binaries[3],
                                    cpu=min(os.sched_getaffinity(0)), timeout=600.)
        self.calls = []
        self.write_build_manifest()

    def write_build_manifest(self):
        self.build_manifest = self.args.frozen_root.parent / 'frozen-build-SHA256.json'
        self.build_manifest.write_text(json.dumps({
            path.relative_to(self.args.frozen_root).as_posix(): self.runner.sha(path)
            for path in self.args.frozen_root.rglob('*') if path.is_file()}))

    def fake_run(self, command, stdin, out, cpu, timeout):
        self.calls.append((command, stdin, Path(out).name))
        Path(out).mkdir(parents=True)
        is_kernel = '--iterations' in command
        text = kernel_output() if is_kernel else bench_output()
        Path(out, 'stdout.txt').write_text(text)
        Path(out, 'stderr.txt').write_text('')
        return dict(command=command, returncode=0, timed_out=False,
                    cpu_seconds=1., user_seconds=.9, system_seconds=.1,
                    wall_seconds=1., stdout=str(Path(out, 'stdout.txt')),
                    stderr=str(Path(out, 'stderr.txt')), cpu=cpu)

    def test_fixed_counts_and_fresh_process_input(self):
        report = self.runner.run_experiment(self.args, self.fake_run)
        self.assertEqual(report['status'], 'completed_no_hosted_speed_claim')
        self.assertEqual(len(self.calls), 72)
        engine = [call for call in self.calls if '--iterations' not in call[0]]
        self.assertEqual(len(engine), 36)
        self.assertTrue(all(stdin == b'bench 11\n' * 12 + b'quit\n'
                            for _, stdin, _ in engine))
        self.assertEqual(len(set(name for _, _, name in self.calls)), 72)
        self.assertEqual(report['final_input_rehash']['status'], 'passed')
        self.assertTrue((self.args.out / 'initial-inputs.json').is_file())

    def test_failed_primary_calibration_stops_before_all_ab_and_kernel(self):
        def noisy(*args):
            row = self.fake_run(*args)
            if len(self.calls) == 1:
                row['cpu_seconds'] = 1.1
            return row
        report = self.runner.run_experiment(self.args, noisy)
        self.assertEqual(len(self.calls), 12)
        self.assertEqual(report['status'], 'failed_primary_calibration_no_ab')
        self.assertFalse(report['primary']['calibration']['passed'])
        self.assertEqual(report['final_input_rehash']['status'], 'passed')

    def test_wrong_signature_stops_without_retry_and_rehashes(self):
        def wrong(*args):
            row = self.fake_run(*args)
            Path(row['stdout']).write_text(bench_output(nodes=7))
            return row
        report = self.runner.run_experiment(self.args, wrong)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(report['status'], 'failed_or_inconclusive_no_claim')
        self.assertEqual(report['final_input_rehash']['status'], 'passed')

    def test_failed_kernel_calibration_keeps_only_primary_ab_eligible(self):
        def noisy(*args):
            row = self.fake_run(*args)
            if len(self.calls) == 13:
                Path(row['stdout']).write_text(kernel_output(cpu_ticks=1100000))
            return row
        report = self.runner.run_experiment(self.args, noisy)
        self.assertEqual(len(self.calls), 48)
        self.assertEqual(report['status'], 'completed_no_hosted_speed_claim')
        self.assertFalse(report['kernel']['calibration']['passed'])
        self.assertNotIn('ab_blocks', report['kernel'])
        self.assertEqual(len(report['primary']['ab_blocks']), 6)

    def test_kernel_hash_change_stops_without_ab_or_retry(self):
        def changed(*args):
            row = self.fake_run(*args)
            if len(self.calls) == 14:
                Path(row['stdout']).write_text(kernel_output(output_hash_fnv1a64='0000000000000000'))
            return row
        report = self.runner.run_experiment(self.args, changed)
        self.assertEqual(len(self.calls), 14)
        self.assertEqual(report['status'], 'failed_or_inconclusive_no_claim')
        self.assertIn('signature identity mismatch', report['error'])

    def test_nonzero_exit_stops_without_retry(self):
        def failed(*args):
            row = self.fake_run(*args)
            row['returncode'] = 3
            return row
        report = self.runner.run_experiment(self.args, failed)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(report['status'], 'failed_or_inconclusive_no_claim')
        self.assertEqual(report['final_input_rehash']['status'], 'passed')

    def test_build_manifest_mismatch_prevents_timing(self):
        self.binaries[1].write_bytes(b'changed between build and timing')
        report = self.runner.run_experiment(self.args, self.fake_run)
        self.assertEqual(self.calls, [])
        self.assertEqual(report['status'], 'failed_or_inconclusive_no_claim')
        self.assertIn('build', report['error'])

    def test_added_frozen_input_is_not_silently_ignored(self):
        def add_input(*args):
            row = self.fake_run(*args)
            (self.args.frozen_root / 'unexpected').write_bytes(b'added during timing')
            return row
        report = self.runner.run_experiment(self.args, add_input)
        self.assertEqual(report['status'], 'failed_or_inconclusive_no_claim')
        self.assertEqual(report['final_input_rehash']['status'], 'failed')
        self.assertEqual(len(report['final_input_rehash']['added_inputs']), 1)

    def test_mutation_after_trial_revokes_any_claim(self):
        def mutate(*args):
            row = self.fake_run(*args)
            self.binaries[1].write_bytes(b'mutated')
            return row
        report = self.runner.run_experiment(self.args, mutate)
        self.assertEqual(report['status'], 'failed_or_inconclusive_no_claim')
        self.assertEqual(report['final_input_rehash']['status'], 'failed')
        self.assertFalse(report['qualifies_hosted_speed_claim'])

    def test_exception_still_has_final_hashes_and_raw_error(self):
        def broken(*args):
            self.binaries[0].unlink()
            raise RuntimeError('mocked launch failure')
        report = self.runner.run_experiment(self.args, broken)
        self.assertEqual(report['status'], 'failed_or_inconclusive_no_claim')
        self.assertIn('mocked launch failure', report['error'])
        self.assertEqual(report['final_input_rehash']['status'], 'failed')

    def test_pending_protocol_never_launches(self):
        data = protocol()
        data['status'] = 'PENDING_REVIEW'
        (self.args.package / 'protocol.json').write_text(json.dumps(data))
        report = self.runner.run_experiment(self.args, self.fake_run)
        self.assertEqual(self.calls, [])
        self.assertEqual(report['status'], 'failed_or_inconclusive_no_claim')


class Wait4SafetyTests(unittest.TestCase):
    def setUp(self):
        self.runner = load_runner()

    def test_timeout_kills_process_group_and_archives_wait4_cpu(self):
        with tempfile.TemporaryDirectory() as root:
            process = SimpleNamespace(pid=321, returncode=None)
            usage = SimpleNamespace(ru_utime=.2, ru_stime=.1)
            with patch.object(self.runner.subprocess, 'Popen', return_value=process) as launch, \
                    patch.object(self.runner.os, 'wait4', side_effect=[(0, 0, None), (321, 9, usage)]), \
                    patch.object(self.runner.os, 'killpg') as kill, \
                    patch.object(self.runner.time, 'monotonic', side_effect=[10., 12., 13.]), \
                    patch.object(self.runner.time, 'sleep'):
                result = self.runner.run_owned(['fixture-command'], b'fixture\n',
                                               Path(root) / 'one', 2, 1.)
            self.assertTrue(result['timed_out'])
            self.assertEqual(result['returncode'], -9)
            self.assertAlmostEqual(result['cpu_seconds'], .3)
            kill.assert_any_call(321, signal.SIGKILL)
            self.assertIs(launch.call_args.kwargs['start_new_session'], True)
            self.assertTrue((Path(root) / 'one' / 'status.json').is_file())


if __name__ == '__main__':
    unittest.main()
