"""Offline storage planning: retained indexes are never credited as free space."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


MODULE = Path(__file__).resolve().parents[2] / 'tools/data2/plan_shard_batches.py'


class ShardPlanTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(MODULE.is_file(), 'offline shard planner is missing')
        spec = importlib.util.spec_from_file_location('plan_shard_batches', MODULE)
        self.p = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.p)

    def inventory(self):
        return {'schema': 1, 'holdout_rows': 20, 'shards': [
            {'id': f'{i:03}', 'rows': i * 10, 'text_bytes': i * 700}
            for i in range(1, 40) if i not in (13, 14)]}

    def plan(self, free, **kwargs):
        return self.p.plan(self.inventory(), [{'name': 'data', 'free_bytes': free}],
                           reserve_bytes=100, **kwargs)

    def test_exact_boundary_fits_and_one_byte_less_blocks(self):
        full = self.plan(10**12)
        needed = sum(step['additional_bytes'] for step in full['steps']) + 100
        self.assertEqual(self.plan(needed)['status'], 'PLANNED')
        blocked = self.plan(needed - 1)
        self.assertEqual(blocked['status'], 'BLOCKED')
        self.assertEqual(blocked['blocked_shard'], '039')
        self.assertEqual(len(blocked['steps']), 36)

    def test_each_retained_index_and_prior_keys_accumulate(self):
        result = self.plan(10**12)
        first, second = result['steps'][:2]
        self.assertEqual(first['index_keys_upper_bound'], 20 + 10)
        self.assertEqual(second['index_keys_upper_bound'], 20 + 10 + 20)
        self.assertEqual(second['free_before_bytes'], 10**12 - first['additional_bytes'])
        self.assertEqual(second['index_bytes_estimate'], (20 + 10 + 20) * 64 + 1024**2)
        self.assertEqual(first['output_bytes_estimate'], 700 + 10 * (32 + 32 + 128))
        self.assertEqual(result['volumes'][0]['new_retained_bytes'],
                         sum(step['additional_bytes'] for step in result['steps']))

    def test_single_volume_stops_before_next_shard_without_reclaiming(self):
        steps = self.plan(10**12)['steps']
        free = 100 + steps[0]['additional_bytes'] + steps[1]['additional_bytes'] - 1
        result = self.plan(free)
        self.assertEqual(result['blocked_shard'], '002')
        self.assertEqual([s['shard_id'] for s in result['steps']], ['001'])
        self.assertEqual(result['batches'][0]['shard_ids'], ['001'])

    def test_independent_volumes_preserve_each_earlier_allocation(self):
        steps = self.plan(10**12)['steps']
        first = steps[0]['additional_bytes']
        rest = sum(step['additional_bytes'] for step in steps[1:])
        result = self.p.plan(self.inventory(), [
            {'name': 'data', 'free_bytes': first + 100},
            {'name': 'archive', 'free_bytes': rest + 100}], reserve_bytes=100,
            independent_volumes=True)
        self.assertEqual(result['status'], 'PLANNED')
        self.assertEqual(result['batches'][0]['shard_ids'], ['001'])
        self.assertEqual(result['volumes'][0]['free_after_bytes'], 100)
        self.assertEqual(result['volumes'][0]['new_retained_bytes'], first)
        self.assertEqual(result['volumes'][1]['free_after_bytes'], 100)
        self.assertEqual(result['steps'][1]['prior_retained_rows_upper_bound'], 10)

    def test_multiple_capacities_require_declared_independent_storage(self):
        with self.assertRaisesRegex(ValueError, 'independent'):
            self.p.plan(self.inventory(), [
                {'name': 'data', 'free_bytes': 10**12},
                {'name': 'alias', 'free_bytes': 10**12}], reserve_bytes=100)

    def test_restart_uses_actual_prior_rows_and_current_observed_free(self):
        result = self.plan(10**12, start_at='015', prior_retained_rows=123)
        first = result['steps'][0]
        self.assertEqual(first['shard_id'], '015')
        self.assertEqual(first['index_keys_upper_bound'], 20 + 123 + 150)
        self.assertEqual(first['free_before_bytes'], 10**12)
        self.assertEqual(result['steps'][1]['prior_retained_rows_upper_bound'], 123 + 150)
        with self.assertRaisesRegex(ValueError, 'prior-retained-rows'):
            self.plan(10**12, start_at='015')

    def test_inventory_requires_every_training_shard_and_nonnegative_counts(self):
        data = self.inventory()
        data['shards'].pop()
        with self.assertRaisesRegex(ValueError, '37'):
            self.p.plan(data, [{'name': 'data', 'free_bytes': 10**12}])
        data = self.inventory()
        data['shards'][0]['rows'] = -1
        with self.assertRaisesRegex(ValueError, 'nonnegative integer'):
            self.p.plan(data, [{'name': 'data', 'free_bytes': 10**12}])
        data = self.inventory()
        data['shards'][0]['rows'] = True
        with self.assertRaisesRegex(ValueError, 'nonnegative integer'):
            self.p.plan(data, [{'name': 'data', 'free_bytes': 10**12}])

    def test_measured_directories_on_one_device_cannot_double_capacity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'alias').mkdir()
            with self.assertRaisesRegex(ValueError, 'same volume'):
                self.p.read_volumes([], [f'data={root}', f'alias={root / "alias"}'])

    def test_gib_input_is_explicit_and_default_reserve_is_32_gib(self):
        volumes = self.p.read_volumes(['data=1.5'], [])
        self.assertEqual(volumes[0]['free_bytes'], 1610612736)
        self.assertEqual(volumes[0]['measurement'], 'user_observed')
        args = self.p.parser().parse_args(['--inventory', 'actual.json', '--observed-free-gib', 'data=99'])
        self.assertEqual(args.min_free_mb, 32768)
        with self.assertRaisesRegex(ValueError, 'finite'):
            self.p.read_volumes(['data=NaN'], [])

    def test_binpack_output_allowance_is_added_without_replacing_index(self):
        plain = self.plan(10**12)['steps'][0]
        packed = self.plan(10**12, binpack=True)['steps'][0]
        self.assertEqual(packed['index_bytes_estimate'], plain['index_bytes_estimate'])
        self.assertEqual(packed['additional_bytes'] - plain['additional_bytes'], 700 + 10 * 128)

    def test_cli_blocked_and_missing_capacity_report_json_exit_codes(self):
        with tempfile.TemporaryDirectory() as directory:
            inventory = Path(directory) / 'inventory.json'
            inventory.write_text(json.dumps(self.inventory()))
            command = [sys.executable, str(MODULE), '--inventory', str(inventory)]
            blocked = subprocess.run(command + ['--observed-free-gib', 'data=1'],
                                     capture_output=True, text=True)
            self.assertEqual(blocked.returncode, 1)
            self.assertEqual(json.loads(blocked.stdout)['blocked_shard'], '001')
            invalid = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(invalid.returncode, 2)
            self.assertEqual(json.loads(invalid.stdout)['status'], 'INVALID')

    def test_invalid_id_types_and_false_prior_count_fail_cleanly(self):
        data = self.inventory()
        data['shards'][0]['id'] = 1
        with self.assertRaisesRegex(ValueError, '37 unique IDs'):
            self.p.plan(data, [{'name': 'data', 'free_bytes': 10**12}])
        with self.assertRaisesRegex(ValueError, 'nonnegative integer'):
            self.plan(10**12, prior_retained_rows=False)


if __name__ == '__main__':
    unittest.main()
