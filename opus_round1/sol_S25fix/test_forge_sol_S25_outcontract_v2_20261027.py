"""S25 v2 tests (S25-1 pins/PIN_MISMATCH/UCI always; S25-2 timeout, owned temp dir + cleanup, --allow-expose).

Run: python -I -B test_forge_sol_S25_outcontract_v2_20261027.py -v
Env: S25_CHECKER (mutant copy), S25_SCRATCH (scratch dir outside git; temp dirs are created there).
The synthetic engine is tests_fixtures/fake_engine.py run with this Python; CLI tests use a .bat/.sh wrapper.
"""
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRATCH = Path(os.environ.get('S25_SCRATCH', tempfile.gettempdir()))
spec = importlib.util.spec_from_file_location('s25v2', os.environ.get('S25_CHECKER', HERE / 'forge_sol_S25_outcontract_v2_20261027.py'))
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)
FAKE = HERE / 'tests_fixtures' / 'fake_engine.py'
APPROVED = json.loads((HERE / 'forge_sol_S25_options_v2_20261027.json').read_text(encoding='utf-8'))['options']
AL1 = {11: 312866, 13: 862329, 16: 3024920, 20: 12389307, 22: 34048354}


def fake(mode):
    return [sys.executable, '-I', '-B', str(FAKE), mode]


def new_dir(tag):
    return Path(tempfile.mkdtemp(prefix='s25v2_%s_' % tag, dir=SCRATCH))


def wrapper(mode):
    d = new_dir('wrap')
    if os.name == 'nt':
        p = d / 'engine.bat'
        p.write_text('@"%s" -I -B "%s" %s\r\n' % (sys.executable, FAKE, mode), encoding='ascii')
    else:
        p = d / 'engine.sh'
        p.write_text('#!/bin/sh\nexec "%s" -I -B "%s" %s\n' % (sys.executable, FAKE, mode))
        p.chmod(0o755)
    return p


def run(mode, pins=AL1, depths=(11,), timeout=60, allow_expose=False):
    return C.run_contract(fake(mode), new_dir('run'), APPROVED, pins, list(depths), timeout, allow_expose)


class Refs(unittest.TestCase):
    def test_default_and_named(self):
        self.assertEqual(C.resolve_ref('AL1'), AL1)
        self.assertEqual(C.resolve_ref('Lprime')[11], 308972)
        self.assertEqual(C.resolve_ref('B')[22], 31111774)
        p = new_dir('ref') / 'pins.json'
        p.write_text('{"11": 5, "13": 6}')
        self.assertEqual(C.resolve_ref(str(p)), {11: 5, 13: 6})
        for bad in ('nope', None):
            with self.assertRaises(ValueError):
                C.resolve_ref(bad)

    def test_cli_default_ref_is_AL1(self):
        import argparse
        self.assertIn("p.add_argument('--ref', default='AL1'", Path(spec.origin).read_text(encoding='utf-8'))


class S25_1_PinsAndUci(unittest.TestCase):
    def test_al1_engine_passes(self):
        r = run('al1')
        self.assertEqual((r['status'], r['bench_status'], r['uci_status']), ('PASS', 'PASS', 'PASS'))

    def test_pin_mismatch_and_uci_still_runs(self):
        r = run('lprime')
        self.assertEqual(r['bench_status'], 'PIN_MISMATCH')
        self.assertEqual(r['uci_status'], 'PASS')  # UCI checked although the pin failed
        self.assertEqual(r['status'], 'FAIL')
        self.assertEqual(r['bench'][0]['actual_nodes'], 308972)
        self.assertEqual([e['code'] for e in r['errors']], ['bench_pin_mismatch'])

    def test_same_engine_passes_with_its_own_tree_pins(self):
        self.assertEqual(run('lprime', pins=C.resolve_ref('Lprime'))['status'], 'PASS')

    def test_all_depths_one_process_each(self):
        r = run('al1', depths=sorted(AL1))
        self.assertEqual(r['depths_run'], [11, 13, 16, 20, 22])
        self.assertEqual(r['status'], 'PASS')

    def test_tail_is_fail_not_pin_and_uci_still_runs(self):
        r = run('tail')
        self.assertEqual(r['bench_status'], 'FAIL')
        self.assertIn('bench_post_summary_bytes', [e['code'] for e in r['errors']])
        self.assertEqual(r['uci_status'], 'PASS')

    def test_tail_and_pin_both_reported(self):
        b = C.inspect_bench(b'info string bench depth 11 nodes 1 time 1 nps 1\ninfo string stats 0\n', b'', 0, 11, 312866)
        self.assertEqual(b['status'], 'FAIL')
        self.assertEqual(sorted(e['code'] for e in b['errors']), ['bench_pin_mismatch', 'bench_post_summary_bytes'])

    def test_crlf_engine_passes(self):
        self.assertEqual(run('crlf')['status'], 'PASS')

    def test_uci_failures_without_pin_problem(self):
        for mode, code in (('extra_option', 'unexpected_option'), ('missing_option', 'missing_option')):
            with self.subTest(mode=mode):
                r = run(mode)
                self.assertEqual(r['bench_status'], 'PASS')
                self.assertEqual(r['uci_status'], 'FAIL')
                self.assertIn(code, [e['code'] for e in r['errors']])


class SolParserCasesPorted(unittest.TestCase):
    """Sol's 12 v1 parser cases (forge_sol_S25_parser_tests_20261025.py), ported with explicit AL1 pins."""
    S = b'info string bench depth 11 nodes 312866 time 123 nps 2511967\n'

    def bench(self, data):
        return C.inspect_bench(data, b'', 0, 11, 312866)

    def text(self, rows):
        out = []
        for r in rows:
            s = 'option name %s type %s' % (r['name'], r['type'])
            if r['type'] == 'spin':
                s += ' default %d min %d max %d' % (r['default'], r['min'], r['max'])
            elif r['type'] == 'check':
                s += ' default ' + str(r['default']).lower()
            elif r['type'] == 'string':
                s += ' default ' + r['default']
            out.append(s)
        return ('\n'.join(out) + '\nuciok\n').encode()

    def test_cases(self):
        S = self.S
        self.assertEqual(self.bench(S)['status'], 'PASS')
        self.assertEqual(C.inspect_uci(self.text(APPROVED), b'', 0, APPROVED)['status'], 'PASS')
        self.assertEqual(self.bench(S[:-1] + b'\r\n')['status'], 'PASS')
        self.assertEqual(self.bench(S[:-1] + b'\r\n\r\n')['status'], 'FAIL')
        self.assertIn('bench_post_summary_bytes', [e['code'] for e in self.bench(S + b'\n')['errors']])
        self.assertEqual(self.bench(S + b'info string stats 0\n')['status'], 'FAIL')
        self.assertEqual(self.bench(S + S)['status'], 'FAIL')
        self.assertEqual(self.bench(S.replace(b' nps ', b' rate '))['status'], 'FAIL')
        self.assertEqual(self.bench(S[:-1])['status'], 'FAIL')
        self.assertEqual(self.bench(S.replace(b'312866', b'312867'))['status'], 'PIN_MISMATCH')
        extra = APPROVED + [{'name': 'Extra', 'type': 'check', 'default': False}]
        self.assertIn('unexpected_option', [e['code'] for e in C.inspect_uci(self.text(extra), b'', 0, APPROVED)['errors']])
        rows = [dict(r) for r in APPROVED]
        rows[0]['default'], rows[0]['max'] = 64, 4096
        self.assertIn('option_metadata_mismatch', [e['code'] for e in C.inspect_uci(self.text(rows), b'', 0, APPROVED)['errors']])
        self.assertIn('duplicate_option', [e['code'] for e in C.inspect_uci(self.text(APPROVED + APPROVED[:1]), b'', 0, APPROVED)['errors']])
        bad = self.text(APPROVED).replace(b'type spin default 32', b'type spin value 32')
        self.assertEqual(C.inspect_uci(bad, b'', 0, APPROVED)['status'], 'FAIL')


class S25_2_TimeoutTempExpose(unittest.TestCase):
    def test_timeout_kills_own_child_and_is_recorded(self):
        r = run('sleep', timeout=2)
        self.assertEqual(r['bench_status'], 'FAIL')
        self.assertIn('bench_timeout', [e['code'] for e in r['errors']])
        self.assertEqual(r['uci_status'], 'PASS')

    def test_allow_expose(self):
        self.assertEqual(run('expose')['uci_status'], 'FAIL')
        r = run('expose', allow_expose=True)
        self.assertEqual(r['status'], 'PASS')
        self.assertEqual(r['uci']['exposed_tunables_allowed'], ['LmrBase', 'RfpMargin'])
        r = run('expose_check', allow_expose=True)
        self.assertEqual(r['uci_status'], 'FAIL')  # only spin tunables are accepted
        self.assertEqual(run('missing_option', allow_expose=True)['uci_status'], 'FAIL')

    def test_cli_temp_dir_is_outside_build_tree_and_removed(self):
        root = new_dir('workroot')
        rc = C.main([str(wrapper('al1')), '--work-root', str(root)])
        self.assertEqual(rc, 0)
        self.assertEqual(list(root.iterdir()), [])  # its own mkdtemp directory was removed, nothing else existed

    def test_cli_keep_and_out_are_kept(self):
        root = new_dir('keep')
        self.assertEqual(C.main([str(wrapper('al1')), '--work-root', str(root), '--keep']), 0)
        kept = list(root.iterdir())
        self.assertEqual(len(kept), 1)
        self.assertTrue((kept[0] / 'contract_result.json').is_file())
        out = new_dir('out') / 'NEW'
        self.assertEqual(C.main([str(wrapper('lprime')), '--out', str(out)]), 1)
        result = json.loads((out / 'contract_result.json').read_text())
        self.assertEqual((result['bench_status'], result['uci_status']), ('PIN_MISMATCH', 'PASS'))

    def test_cleanup_refuses_foreign_directories(self):
        d = new_dir('foreign')
        (d / 'keepme.txt').write_text('x')
        with self.assertRaises(RuntimeError):
            C.remove_owned(d, 'token')
        (d / C.MARKER).write_text('other-token')
        with self.assertRaises(RuntimeError):
            C.remove_owned(d, 'token')
        self.assertTrue((d / 'keepme.txt').is_file())

    def test_cli_rejects_bad_invocation(self):
        self.assertEqual(C.main([str(wrapper('al1')), '--ref', 'nope', '--work-root', str(new_dir('bad'))]), 2)
        self.assertEqual(C.main([str(wrapper('al1')), '--depths', '12', '--work-root', str(new_dir('bad'))]), 2)


if __name__ == '__main__':
    unittest.main()
