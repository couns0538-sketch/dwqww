#!/usr/bin/env python3
"""test_autolock_audit.py (S47, opus 2026-10-27): tests for Part A (net-only tree check) and Part B (AUTO-LOCK audit).
Part B defects are planted in scratch COPIES of fixtures/partB ($S47_SCRATCH, default: system temp; never deleted).
The tools are loaded from $S47_PARTA / $S47_PARTB (default: next to this file) so mutation_check_s47.py can swap in mutants.
Run: python -I -B test_autolock_audit.py"""
import hashlib
import importlib.util
import io
import json
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
FX = os.path.join(HERE, 'fixtures')
SCR = os.environ.get('S47_SCRATCH', tempfile.gettempdir())


def load(env, name):
    path = os.environ.get(env, os.path.join(HERE, name))
    spec = importlib.util.spec_from_file_location(env.lower(), path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


A = load('S47_PARTA', 'forge_sol_S47_verify_netonly_tree_20261027.py')
B = load('S47_PARTB', 'forge_sol_S47_autolock_audit_20261027.py')
PA = os.path.join(FX, 'partA')
NET_MD5 = None   # set below, after rd()


def rd(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def run(mod, args):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = mod.main(args)
    return code, buf.getvalue()


NET_MD5 = rd(os.path.join(PA, 'expected_net_md5.txt')).strip()


class PartA(unittest.TestCase):
    def a(self, cand, md5=NET_MD5, lock='lock', extra=()):
        code, out = run(A, ['--lock', os.path.join(PA, lock), '--cand', os.path.join(PA, cand), '--net-md5', md5] + list(extra))
        return code, json.loads(out)

    def test_net_only_passes(self):
        code, v = self.a('cand_net')
        self.assertEqual((code, v['verdict'], v['differ']), (0, 'PASS', ['src/nnue_weights.inc']))
        self.assertEqual(v['net']['match'], 'raw')

    def test_crlf_only_edits_ignored(self):
        code, v = self.a('cand_crlf')
        self.assertEqual(code, 0)
        self.assertEqual(v['crlf_only_ignored'], ['include/forge/a.hpp', 'src/main.cpp'])

    def test_src_change_fails(self):
        code, v = self.a('cand_src')
        self.assertEqual(code, 1)
        self.assertIn('src/main.cpp', ' '.join(v['reasons']))

    def test_extra_file_fails(self):
        self.assertEqual(self.a('cand_extra')[0], 1)

    def test_identical_tree_fails(self):
        with open(os.path.join(PA, 'lock', 'src', 'nnue_weights.inc'), 'rb') as f:
            same = hashlib.md5(f.read()).hexdigest()
        code, v = self.a('cand_same', md5=same)
        self.assertEqual(code, 1)
        self.assertIn('identical to the lock', ' '.join(v['reasons']))

    def test_wrong_md5_fails(self):
        self.assertEqual(self.a('cand_net', md5='0' * 32)[0], 1)

    def test_any_autolock_dir_as_lock(self):
        code, v = self.a('cand_net', lock='AUTOLOCK_1_fx')
        self.assertEqual(code, 0)
        self.assertTrue(v['lock']['autolock_dir'])
        self.assertEqual(v['lock']['lock_json']['tag'], 'AUTOLOCK_1_fx')

    def test_z1_regate_not_net_only_fails_with_message(self):
        code, v = self.a('cand_src', extra=['--gate-json', os.path.join(PA, 'gate_regate.json')])
        self.assertEqual(code, 1)
        self.assertTrue(any(r.startswith('Z-1 (CAP-LATE Z): gate104_e48f006_rebase_vs_AL1 is a re-gate of gate104_e48f006_vs_h256e12') for r in v['reasons']))
        self.assertEqual(self.a('cand_net', extra=['--gate-json', os.path.join(PA, 'gate_regate.json')])[0], 0)


class PartB(unittest.TestCase):
    def copy(self):
        d = tempfile.mkdtemp(prefix='s47b_', dir=SCR)
        shutil.copytree(os.path.join(FX, 'partB'), os.path.join(d, 'partB'))
        return os.path.join(d, 'partB')

    def args(self, b, **over):
        x = {'--old-lock': os.path.join(b, 'locks', 'AUTOLOCK_1_gate120_fx'), '--new-lock': os.path.join(b, 'locks', 'AUTOLOCK_2_gate130_fx'),
             '--old-hashes': os.path.join(b, 'locks', 'AUTOLOCK_1_gate120_fx', 'SOURCES.sha256'),
             '--gate-result': os.path.join(b, 'gate', 'RESULT.md'), '--gate-run-info': os.path.join(b, 'gate', 'RUN_INFO.json'),
             '--confirm-result': os.path.join(b, 'confirm', 'RESULT.md'), '--confirm-run-info': os.path.join(b, 'confirm', 'RUN_INFO.json'),
             '--gate-record': os.path.join(b, 'gate', 'record.json'), '--confirm-record': os.path.join(b, 'confirm', 'record.json'),
             '--net-md5': rd(os.path.join(b, 'net_md5.txt')).strip(), '--pin-allow': os.path.join(b, 'pin_allow.json'),
             '--cr-dir': os.path.join(b, 'cr'), '--out-json': os.path.join(b, 'audit.json'), '--out-md': os.path.join(b, 'audit.md')}
        x.update(over)
        out = []
        for k, v in x.items():
            if v is not None:
                out += [k, v]
        return out

    def audit(self, b, **over):
        code, md = run(B, self.args(b, **over))
        with open(os.path.join(b, 'audit.json'), encoding='utf-8') as f:
            j = json.load(f)
        return code, {r['id']: r for r in j['checks']}, j, md

    def edit(self, path, old, new):
        with open(path, 'rb') as f:
            t = f.read()
        self.assertIn(old.encode(), t)
        with open(path, 'wb') as f:
            f.write(t.replace(old.encode(), new.encode(), 1))

    def test_good_lock_all_checks_pass_but_no_cr_grant(self):
        b = self.copy()
        code, c, j, md = self.audit(b)
        self.assertEqual((code, j['overall']), (0, 'ALL_CHECKS_PASS'), md)
        self.assertFalse(j['grants_cr_approval'])
        self.assertIn('NOT a CR approval', md)
        self.assertFalse(os.path.exists(os.path.join(b, 'cr', 'CR_PASS_AUTOLOCK_2.txt')))
        self.assertEqual(c['A11']['status'], 'INFO')

    def test_edited_pin_fails(self):
        b = self.copy()
        self.edit(os.path.join(b, 'locks', 'AUTOLOCK_2_gate130_fx', 'pins', 'e48f006_pin_rerecord_PROPOSED.diff'), '445320', '445321')
        code, c, j, _ = self.audit(b)
        self.assertEqual((code, c['A10']['status']), (1, 'FAIL'))

    def test_one_node_bench_drift_fails(self):
        b = self.copy()
        p = os.path.join(b, 'locks', 'AUTOLOCK_2_gate130_fx', 'BENCH_REF.txt')
        t = rd(p)
        with open(p, 'w', newline='\n') as f:
            f.write(t.replace('4197338', '4197339'))
        code, c, j, _ = self.audit(b)
        self.assertEqual((code, c['A5']['status']), (1, 'FAIL'))
        self.assertIn('drift [0, 0, 1, 0, 0]', c['A5']['evidence'])

    def test_confirm_reusing_gate_srand_fails(self):
        b = self.copy()
        self.edit(os.path.join(b, 'confirm', 'RUN_INFO.json'), '1983003762', '344808634')
        code, c, j, _ = self.audit(b)
        self.assertEqual((code, c['A8']['status']), (1, 'FAIL'))
        self.assertIn('confirm reuses the gate srand', c['A8']['evidence'])

    def test_confirm_reusing_gate_openings_start_fails(self):
        b = self.copy()
        self.edit(os.path.join(b, 'confirm', 'RUN_INFO.json'), '348001', '321001')
        self.assertEqual(self.audit(b)[1]['A8']['status'], 'FAIL')

    def test_old_lock_file_changed_fails(self):
        b = self.copy()
        self.edit(os.path.join(b, 'locks', 'AUTOLOCK_1_gate120_fx', 'source', 'src', 'main.cpp'), '42', '41')
        self.assertEqual(self.audit(b)[1]['A2']['status'], 'FAIL')

    def test_net_and_exe_mismatch_fail(self):
        b = self.copy()
        self.assertEqual(self.audit(b, **{'--net-md5': '1' * 32})[1]['A3']['status'], 'FAIL')
        self.edit(os.path.join(b, 'confirm', 'RUN_INFO.json'), '"sha256": "', '"sha256": "00')
        self.assertEqual(self.audit(b)[1]['A4']['status'], 'FAIL')

    def test_perft_fma_and_uci_fail(self):
        b = self.copy()
        self.edit(os.path.join(b, 'locks', 'AUTOLOCK_2_gate130_fx', 'PERFT.txt'), 'objdump -Cd): 0', 'objdump -Cd): 3')
        self.edit(os.path.join(b, 'locks', 'AUTOLOCK_2_gate130_fx', 'UCI_OPTIONS.txt'), 'default 32', 'default 64')
        c = self.audit(b)[1]
        self.assertEqual((c['A6']['status'], c['A7']['status']), ('FAIL', 'FAIL'))

    def test_void_confirm_fails(self):
        b = self.copy()
        self.edit(os.path.join(b, 'confirm', 'RESULT.md'), '# gate130_fx_confirm RESULT', '# gate130_fx_confirm RESULT: **VOID**')
        self.assertEqual(self.audit(b)[1]['A9']['status'], 'FAIL')

    def test_missing_inputs_flagged_not_guessed(self):
        b = self.copy()
        code, c, j, md = self.audit(b, **{'--old-uci': os.path.join(b, 'nope.txt'), '--gate-record': None, '--net-md5': None})
        self.assertEqual((code, j['overall']), (3, 'INCOMPLETE'))
        self.assertEqual((c['A7']['status'], c['A5']['status'], c['A3']['status']), ('MISSING', 'MISSING', 'MISSING'))
        self.assertIn('## Missing (flagged, not guessed)', md)

    def test_not_a_new_dir_and_orphan_fail(self):
        b = self.copy()
        self.assertEqual(self.audit(b, **{'--new-lock': os.path.join(b, 'locks', 'AUTOLOCK_1_gate120_fx')})[1]['A1']['status'], 'FAIL')
        os.makedirs(os.path.join(b, 'locks', 'AUTOLOCK_1_stale_orphan'))
        c = self.audit(b)[1]
        self.assertEqual(c['A1']['status'], 'FAIL')
        self.assertIn('orphan lower-n AUTOLOCK dir(s): AUTOLOCK_1_stale_orphan', c['A1']['evidence'])

    def test_bench_equal_to_old_lock_fails(self):
        b = self.copy()
        old = rd(os.path.join(b, 'locks', 'AUTOLOCK_1_gate120_fx', 'BENCH_REF.txt'))
        with open(os.path.join(b, 'locks', 'AUTOLOCK_2_gate130_fx', 'BENCH_REF.txt'), 'w', newline='\n') as f:
            f.write(old)
        c = self.audit(b, **{'--expected-bench': '312866/862329/3024920/12389307/34048354'})[1]
        self.assertEqual(c['A5']['status'], 'FAIL')
        self.assertIn('equals the old lock bench', c['A5']['evidence'])

    def test_applied_pin_in_tests_tree_fails(self):
        b = self.copy()
        self.edit(os.path.join(b, 'locks', 'AUTOLOCK_2_gate130_fx', 'source', 'tests', 'pins.txt'), '312866', '445320')
        self.assertEqual(self.audit(b)[1]['A10']['status'], 'FAIL')


if __name__ == '__main__':
    unittest.main(verbosity=2)
