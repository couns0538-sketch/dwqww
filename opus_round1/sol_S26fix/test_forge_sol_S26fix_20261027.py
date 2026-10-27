"""S26fix tests: v5 check_ctest on REAL CI JUnit, ASan verdict checker, B rebuild inputs, closed-net summaries.

Run: python -I -B test_forge_sol_S26fix_20261027.py   (stdlib only; v4/v5 import with a stub fcntl on Windows)
Fixtures: tests_fixtures/ci_run_40505681846 = unedited CI outputs of run 40505681846 (Linux, g++ 14.2.0).
"""
import html
import importlib.util
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIX = HERE / 'tests_fixtures' / 'ci_run_40505681846'
SOL_V4 = Path(os.environ.get('S26_V4', r'F:/opus_scratch/sol_S26fix/sol_orig/S26/S26/successor_ctest_v4/'
                                       r'forge_sol_S26_netbatch_v4_20261026.py'))
V5 = Path(os.environ.get('S26_V5', HERE / 'forge_sol_S26_netbatch_v5_20261027.py'))
sys.path.insert(0, str(HERE / 'ci'))
sys.path.insert(0, str(HERE))


def load(path, name):
    if 'fcntl' not in sys.modules:  # main() only; check_ctest is platform independent
        sys.modules['fcntl'] = types.ModuleType('fcntl')
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ALLOW = json.loads((FIX / 'forge_sol_S26_allowlist_20261026.json').read_text())
EXPECTED = json.loads((HERE / 'ci' / 'inputs' / 'expected_v3_diagnostics.json').read_text())['nets']
TESTS_SHA = '55334ba94fd508d5f8e8e0e715c86a6996eddc69b20b1c110110a96e46deaa2c'


def junit(net):
    d = FIX / ('v4_' + net)
    names = json.loads((d / 'ctest_inventory.json').read_text())['expected_names']
    return d / 'ctest.xml', names


class V5CheckCtest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v5 = load(V5, 's26_v5')
        cls.v4 = load(SOL_V4, 's26_v4') if SOL_V4.is_file() else None

    def bound(self, mod, net):
        return mod.bind_allowlist(ALLOW, TESTS_SHA, EXPECTED[net]['net_sha256'])

    def test_real_f023_junit_v5_reports_the_real_reason(self):
        path, names = junit('f023')
        with self.assertRaises(ValueError) as cm:
            self.v5.check_ctest(path, 8, self.bound(self.v5, 'f023'), expected_names=names)
        self.assertIn('unallowlisted test diagnostic: PIN_MISMATCH: WAC 001 documented f6h5/661/d12', str(cm.exception))

    def test_real_f023_junit_v4_misreports_not_run(self):
        if self.v4 is None:
            self.skipTest('Sol v4 source not available at S26_V4')
        path, names = junit('f023')
        with self.assertRaises(ValueError) as cm:
            self.v4.check_ctest(path, 8, self.bound(self.v4, 'f023'), expected_names=names)
        self.assertIn('CTest case was not run: forge_tests', str(cm.exception))

    def test_real_B_lock_junit_passes_in_both(self):
        path, names = junit('B_lock')
        for mod in [m for m in (self.v5, self.v4) if m is not None]:
            with self.subTest(mod=mod.__name__):
                self.assertEqual(mod.check_ctest(path, 0, self.bound(mod, 'B_lock'), expected_names=names)['status'], 'PASS')

    def test_v5_still_rejects_nonrun_and_inconsistent_fail(self):
        import xml.etree.ElementTree as ET
        path, names = junit('B_lock')
        tmp = Path(tempfile.mkdtemp(prefix='s26v5_', dir=os.environ.get('S26_SCRATCH')))
        for status in ('notrun', 'disabled', 'skipped', 'unknown', 'fail'):
            with self.subTest(status=status):
                tree = ET.parse(path)
                case = [c for c in tree.getroot().iter('testcase') if c.attrib['name'] == 'forge_tests'][0]
                case.set('status', status)
                for f in case.findall('failure'):
                    case.remove(f)
                p = tmp / ('junit_%s.xml' % status)
                tree.write(p)
                with self.assertRaises(ValueError):
                    self.v5.check_ctest(p, 0, self.bound(self.v5, 'B_lock'), expected_names=names)

    def test_v5_differs_from_v4_only_in_check_ctest(self):
        if self.v4 is None:
            self.skipTest('Sol v4 source not available at S26_V4')
        import ast
        a = {n.name: ast.dump(n) for n in ast.parse(SOL_V4.read_text()).body if isinstance(n, ast.FunctionDef)}
        b = {n.name: ast.dump(n) for n in ast.parse(V5.read_text()).body if isinstance(n, ast.FunctionDef)}
        self.assertEqual(set(a), set(b))
        self.assertEqual(sorted(k for k in a if a[k] != b[k]), ['check_ctest'])


class AsanChecker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import check_pernet_asan
        cls.mod = check_pernet_asan

    def test_real_artifacts_pass(self):
        for net in ('B_lock', 'f023'):
            with self.subTest(net=net):
                r = self.mod.check(str(FIX / ('asan_' + net)), EXPECTED[net])
                self.assertEqual(r['status'], 'PASS', r['problems'])

    def test_planted_sanitizer_report_fails(self):
        tmp = Path(tempfile.mkdtemp(prefix='s26asan_', dir=os.environ.get('S26_SCRATCH')))
        src = FIX / 'asan_B_lock'
        for f in src.iterdir():
            if f.is_file():
                (tmp / f.name).write_bytes(f.read_bytes())
        (tmp / 'sanitizer_logs').mkdir()
        (tmp / 'sanitizer_logs' / 'asan.123').write_text('ERROR: AddressSanitizer: heap-buffer-overflow\n')
        r = self.mod.check(str(tmp), EXPECTED['B_lock'])
        self.assertEqual(r['status'], 'FAIL')
        self.assertTrue(any('sanitizer report files' in p for p in r['problems']))

    def test_wrong_net_expectation_fails(self):
        r = self.mod.check(str(FIX / 'asan_f023'), EXPECTED['B_lock'])
        self.assertEqual(r['status'], 'FAIL')


class Inputs(unittest.TestCase):
    def test_expected_diagnostics_unescaped_and_complete(self):
        self.assertEqual(sorted(EXPECTED), ['B_lock', 'f019', 'f020', 'f021', 'f022', 'f023'])
        for net, row in EXPECTED.items():
            for line in row['forge_tests_diagnostics']:
                self.assertEqual(line, html.unescape(line))
        self.assertIn('PIN_MISMATCH: WAC 001 documented f6h5/661/d12/PV=f6h5, observed f6h5/620/d12/PV=f6h5; '
                      're-record Job C pins in a reviewed change if the lock changed',
                      EXPECTED['f023']['forge_tests_diagnostics'])

    def test_net_hashes(self):
        import gzip
        import hashlib
        names = {'B_lock': 'resid_h256_e12_e_ep12', 'f019': 'resid_h256_e20_f019_b06_ep20',
                 'f020': 'resid_h256_e16_f020_b06_sol_ep16', 'f021': 'resid_h256_e20_f021_b06_ep20',
                 'f022': 'resid_h256_e20_f022_b06_ep20', 'f023': 'resid_h256_e16_f023_b06_ep16'}
        for net, name in names.items():
            with self.subTest(net=net):
                data = gzip.decompress((HERE / 'ci' / 'inputs' / 'nets' / (name + '.inc.gz')).read_bytes())
                self.assertEqual(hashlib.sha256(data).hexdigest(), EXPECTED[net]['net_sha256'])


class ClosedNetSummaries(unittest.TestCase):
    def test_every_summary_number_matches_its_json(self):
        import forge_sol_S26_closed_net_summaries_20261027 as m
        problems = m.verify(HERE / 'closed_nets')
        self.assertEqual(problems, [])


if __name__ == '__main__':
    unittest.main()
