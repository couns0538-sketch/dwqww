r"""Arithmetic/negative-calibration/binding regressions. No engines are launched.

Run: python -B test_timing.py --out D:\a10\...\new-test-directory
Fixtures are retained, never automatically deleted.
"""
import argparse
import copy
import json
import pathlib
import sys
import unittest
from unittest.mock import patch
from math_checks import NODES, block_ratio, calibration, protocol_snapshot, sha, summary, validate_binding

OUT = None


class TimingRegression(unittest.TestCase):
    def test_geometric_block_uses_external_wall_times(self):
        rows = [dict(arm=arm,status='PASS',nodes=NODES,wall_seconds=wall,engine_nps=1)
                for arm,wall in zip('ABBA', [10,8,5,10])]
        self.assertAlmostEqual(block_ratio(rows), (2.5)**.5)

    def test_incomplete_or_wrong_work_block_is_refused(self):
        rows = [dict(arm=arm,status='PASS',nodes=NODES,wall_seconds=10) for arm in 'ABBA']
        with self.assertRaises(ValueError):
            block_ratio(rows[:3])
        rows[1]['nodes'] -= 1
        with self.assertRaisesRegex(ValueError, 'search work'):
            block_ratio(rows)

    def test_quartiles_are_inclusive(self):
        self.assertEqual(summary(list(range(10)))['iqr'], 4.5)

    def test_calibration_requires_ten_and_rejects_old_r9_bias(self):
        self.assertFalse(calibration([0]*9)['passed'])
        self.assertFalse(calibration([.626352]*10)['passed'])
        self.assertTrue(calibration([-.1,0,.1,0,-.1,.1,0,.1,0,-.1])['passed'])

    def test_calibration_range_and_iqr_are_independent_gates(self):
        self.assertFalse(calibration([-2.01]+[0]*9)['passed'])
        self.assertFalse(calibration([-1]*5+[1]*5)['passed'])

    def protocol(self):
        root = OUT/self._testMethodName
        root.mkdir()
        test_input = root/'fixture.bin'
        test_input.write_bytes(b'R10 synthetic binding fixture')
        topology = root/'host.json'
        topology.write_text(json.dumps({'physical_cores':[{'group':0,'logical_cpus':[2,3]}]}))
        p = json.loads(pathlib.Path(__file__).with_name('protocol.template.json').read_text())
        for item in p['inputs']:
            item['path'] = str(test_input)
            if item['role'] == 'baseline_binary':
                item['path'] = 'D:/a10/inputs/lock.exe'
            elif item['role'] == 'corpus':
                item['path'] = 'D:/a10/inputs/fens_12k.txt'
            elif item['role'] == 'compiler':
                item['path'] = 'D:/a10/inputs/gcc-15.2-gpp.exe'
            elif item['role'] == 'host_topology':
                item['path'] = str(topology)
            item['sha256'] = sha(item['path'])
        p['network_sha256'] = sha(test_input)
        for item in p['prerequisites'].values():
            item.update(path=str(test_input),sha256=sha(test_input),candidate_sha256=sha(test_input),
                        status='PASS',evidence_scope='native')
        return p

    def test_valid_hash_binding_fixture(self):
        # This tests checker mechanics only: fixture receipt text is not native proof.
        self.assertEqual(validate_binding(self.protocol())['baseline_binary']['role'], 'baseline_binary')

    def test_changed_candidate_bytes_are_refused(self):
        p = self.protocol()
        row = next(x for x in p['inputs'] if x['role'] == 'candidate_binary')
        changed = OUT/self._testMethodName/'changed.bin'
        changed.write_bytes(b'changed fixture bytes')
        row['path'] = str(changed)
        with self.assertRaisesRegex(ValueError, 'candidate_binary'):
            validate_binding(p)

    def test_unverified_prerequisite_is_refused(self):
        p = self.protocol(); p['prerequisites']['raw_bit_parity']['status'] = 'UNVERIFIED'
        with self.assertRaisesRegex(ValueError, 'raw_bit_parity'):
            validate_binding(p)

    def test_receipt_from_different_candidate_is_refused(self):
        p = self.protocol(); p['prerequisites']['off_on_pins']['candidate_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'off_on_pins'):
            validate_binding(p)

    def test_loosened_protocol_is_refused(self):
        p = self.protocol(); p['calibration_abs_median_max'] = .75
        with self.assertRaisesRegex(ValueError, 'calibration_abs_median_max'):
            validate_binding(p)

    def test_different_physical_core_topology_is_refused(self):
        p = self.protocol()
        ref = next(x for x in p['inputs'] if x['role'] == 'host_topology')
        pathlib.Path(ref['path']).write_text(json.dumps({'physical_cores':[{'group':0,'logical_cpus':[2,4]}]}))
        ref['sha256'] = sha(ref['path'])
        with self.assertRaisesRegex(ValueError, 'CPU2/3'):
            validate_binding(p)

    def test_protocol_hash_binds_consumed_bytes(self):
        root = OUT/self._testMethodName; root.mkdir()
        path = root/'protocol.json'; path.write_bytes(b'{"version":"old"}')
        original_read = pathlib.Path.read_bytes
        def changed_after_read(obj):
            raw = original_read(obj)
            if obj == path:
                obj.write_bytes(b'{"version":"new"}')
            return raw
        with patch.object(pathlib.Path,'read_bytes',changed_after_read):
            with self.assertRaisesRegex(ValueError, 'changed while taking snapshot'):
                protocol_snapshot(path)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True, type=pathlib.Path)
    ap.add_argument('--threads', type=int, choices=[1], default=1)
    a = ap.parse_args(); OUT = a.out; OUT.mkdir(parents=True,exist_ok=False)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TimingRegression))
    sys.exit(0 if result.wasSuccessful() else 1)
