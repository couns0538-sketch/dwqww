#!/usr/bin/env python3
"""test_promote_sim.py (S46, opus 2026-10-27): tests for forge_sol_S46_promote_sim_20261027.py.
- every fixture: golden log (byte for byte) + hand-written ordered `must` / `must_not` decisions under the voted rules;
- same input -> byte-identical output; the fixture files regenerate byte-identically;
- rule profiles: pc_896663b0 differs from the voted rules only on the step-5 suffix fixture (the live G55/G56 bug);
  pre_fix_F41CF92F fails every 16:15 rework fixture (i)-(vi);
- wrong-rule check: each single deliberately wrong rule in the config makes at least one fixture fail.
The simulator is loaded from $S46_SIM (default: next to this file). Run: python -I -B test_promote_sim.py"""
import glob
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.environ.get('S46_SIM', os.path.join(HERE, 'forge_sol_S46_promote_sim_20261027.py'))
spec = importlib.util.spec_from_file_location('s46sim', SIM)
sim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sim)
CONF = os.path.join(HERE, 'config')
FIX = [json.load(open(f, encoding='utf-8')) for f in sorted(glob.glob(os.path.join(HERE, 'fixtures', '*.json')))]
VOTED = sim.load_rules(os.path.join(CONF, 'rules_voted_20261026.json'))
PC = sim.load_rules(os.path.join(CONF, 'rules_pc_896663b0.json'))
PRE = sim.load_rules(os.path.join(CONF, 'rules_pre_fix_F41CF92F.json'))
S5 = 's5_step5_suffix_src_dir_resolution'
REWORKS_I_VI = ['i_void_confirm_with_h1_line_never_h1', 'ii_lagging_csv_wait_then_promote', 'iii_stopped_rival_is_not_a_rival',
                'iv_crash_after_pointer_reconciled', 'v_cap_late_z_g104c_h1_releases_regate', 'v2_cap_late_z_g104c_h0_drops_regate',
                'vi_void_hold_one_rerun']
MUTATIONS = [('spacing_hours', 12), ('max_chained_without_cr', 3), ('race_hold.cap_hours', 6), ('race_hold.enabled', False),
             ('void_never_h1', False), ('void_chain_not_marked', False), ('wait_on_missing_data', False), ('race_hold.rival_off', []),
             ('inflight_record', False), ('cap_late_z.z2_hold_until_e48_h1', False), ('cap_late_z.exempt24_stems', []),
             ('cap_late_z.exempt24_all_regates', True), ('cap_late_z.z1_net_only', False), ('void_hold.enabled', False),
             ('rhq1.enabled', False), ('rhq1.hold_when_e48_not_promotable', False), ('rollback.window_games', 300),
             ('rollback.on_tl', False), ('combine_list_on_stale_lock', False), ('step5.src_resolution', 'exe_name'),
             ('step5.max_rebuild_per_tick', 3), ('edits_need_running_gate', False), ('race_hold.rival_off_status_regex', '')]


def body(log):
    return log.split('\n', 1)[1]


def check(fx, log):
    pos = 0
    for m in fx['must']:
        i = log.find(m, pos)
        if i < 0:
            return f'missing: {m}'
        pos = i + len(m)
    for m in fx['must_not']:
        if m in log:
            return f'forbidden: {m}'
    return ''


def norm(text):
    # Line endings follow the checkout's autocrlf setting: compare text, not bytes.
    return text.replace('\r\n', '\n')


def golden(name):
    with open(os.path.join(HERE, 'expected', name + '.log'), encoding='utf-8', newline='') as f:
        return norm(f.read())


class Voted(unittest.TestCase):
    def test_enough_fixtures_and_spec_cases(self):
        self.assertGreaterEqual(len(FIX), 10)
        refs = ' '.join(f['spec_ref'] for f in FIX)
        for k in ['(a)', '(b)', '(c)', '(d)', '(e)', '(f)', '(g)', '(h)', '(i)', '(ii)', '(iii)', '(iv)', '(v)', '(vi)', '(vii)', '(viii)', 'step-5 suffix']:
            self.assertIn(k, refs)

    def test_golden_logs(self):
        for fx in FIX:
            with self.subTest(fx=fx['name']):
                self.assertEqual(norm(sim.simulate(VOTED, fx)), golden(fx['name']))

    def test_must_decisions(self):
        for fx in FIX:
            with self.subTest(fx=fx['name']):
                self.assertEqual(check(fx, sim.simulate(VOTED, fx)), '')

    def test_byte_identical_rerun(self):
        for fx in FIX:
            self.assertEqual(sim.simulate(VOTED, fx), sim.simulate(VOTED, fx))

    def test_fixture_files_regenerate_identically(self):
        d = tempfile.mkdtemp(prefix='s46fx_', dir=os.environ.get('S46_SCRATCH'))   # left in place (no deletes)
        subprocess.run([sys.executable, '-I', '-B', os.path.join(HERE, 'make_s46_fixtures.py'), '--out', d], check=True, capture_output=True)
        for fx in FIX:
            with open(os.path.join(d, fx['name'] + '.json'), 'rb') as a, open(os.path.join(HERE, 'fixtures', fx['name'] + '.json'), 'rb') as b:
                self.assertEqual(a.read().replace(b'\r\n', b'\n'), b.read().replace(b'\r\n', b'\n'), fx['name'])

    def test_cli_out_equals_golden(self):
        fx = FIX[0]
        out = os.path.join(tempfile.mkdtemp(prefix='s46cli_', dir=os.environ.get('S46_SCRATCH')), 'o.log')
        sim.main(['--rules', os.path.join(CONF, 'rules_voted_20261026.json'), '--fixture', os.path.join(HERE, 'fixtures', fx['name'] + '.json'), '--out', out])
        with open(out, encoding='utf-8', newline='') as f:
            self.assertEqual(norm(f.read()), golden(fx['name']))


class Profiles(unittest.TestCase):
    def test_pc_896663b0_differs_only_on_step5_suffix(self):
        diff = sorted(fx['name'] for fx in FIX if body(sim.simulate(PC, fx)) != body(golden(fx['name'])))
        self.assertEqual(diff, [S5])
        log = sim.simulate(PC, next(f for f in FIX if f['name'] == S5))
        self.assertIn("LABEL | gate55_e20i_vs_h256e12 | keeps old opponent h256_e12", log)   # the live bug: silent, no alert
        self.assertNotIn('ALERT | rbskip_', log)

    def test_pre_fix_F41CF92F_fails_reworks_i_to_vi(self):
        for name in REWORKS_I_VI:
            fx = next(f for f in FIX if f['name'] == name)
            with self.subTest(fx=name):
                self.assertNotEqual(check(fx, sim.simulate(PRE, fx)), '')

    def test_each_wrong_rule_fails_some_fixture(self):
        for key, val in MUTATIONS:
            with self.subTest(rule=f'{key}={val}'):
                bad = sim.load_rules(os.path.join(CONF, 'rules_voted_20261026.json'), {key: val})
                failing = [fx['name'] for fx in FIX if check(fx, sim.simulate(bad, fx)) or body(sim.simulate(bad, fx)) != body(golden(fx['name']))]
                self.assertTrue(failing, f'wrong rule {key}={val} is not caught by any fixture')


if __name__ == '__main__':
    unittest.main(verbosity=2)
