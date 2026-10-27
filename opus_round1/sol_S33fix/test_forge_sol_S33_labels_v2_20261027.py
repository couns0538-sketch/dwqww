"""Tests for S33-1 (v2): approx-model labels on every advice table, fastchess-only gate figures.

Run: python -I -B test_forge_sol_S33_labels_v2_20261027.py -v
Env: S33_LABELS_DIR (mutant copy of the labels module), S33_SOL_DIR (Sol's S33 folder for the original-doc checks),
     S33_SCRATCH (scratch dir outside git for rendered copies).
"""
import csv
import importlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, os.environ.get('S33_LABELS_DIR', str(HERE)))
lab = importlib.import_module('forge_sol_S33_labels_v2_20261027')
ex = importlib.import_module('forge_sol_S33_exact_sprt_v2_20261027')
GATES = HERE / 'tests_fixtures' / 'gates'
SOL = Path(os.environ.get('S33_SOL_DIR', HERE / 'tests_fixtures' / 'sol_original'))  # byte copies of Sol's 17aa0cae files
SCRATCH = Path(os.environ.get('S33_SCRATCH', tempfile.gettempdir()))
V2_DOCS = ['forge_sol_S33_advice_net_v2_20261027.md', 'forge_sol_S33_advice_search_v2_20261027.md',
           'forge_sol_S33_advice_speed_v2_20261027.md', 'forge_sol_S33_sprt_plan_table_v2_20261027.md']
FIGS = lab.fastchess_figures(GATES)


def check(text):
    return lab.check_text(text, FIGS, 'doc')


class Figures(unittest.TestCase):
    def test_fastchess_strings_read_from_result_md(self):
        self.assertEqual(FIGS['G119'], {'llr': '1.72', 'elo': '9.50', 'elo_err': '8.84', 'nelo': '18.90', 'nelo_err': '17.58'})
        self.assertEqual(FIGS['G100r']['llr'], '2.22')
        self.assertEqual(FIGS['G95']['llr'], '-0.56')
        self.assertEqual(FIGS['G120']['llr'], '2.99')

    def test_exact_llr_reproduces_printed(self):
        import numpy as np
        for gate, counts in (('G119', [9, 130, 435, 163, 13]), ('G100r', [5, 121, 458, 154, 12]),
                             ('G95', [13, 128, 463, 137, 9])):
            with self.subTest(gate=gate):
                llr = float(ex.exact_llr(np.asarray([counts], float), 0.0, 10.0)[0])
                self.assertEqual('%.2f' % llr, FIGS[gate]['llr'])


class LabelRule(unittest.TestCase):
    def test_v2_docs_pass(self):
        for name in V2_DOCS:
            with self.subTest(doc=name):
                self.assertEqual(check((HERE / name).read_text(encoding='utf-8')), [])

    @unittest.skipUnless((SOL / 'forge_sol_S33_advice_net_20261026.md').is_file(), 'Sol S33 folder not available')
    def test_sol_original_tables_are_flagged(self):
        p = check((SOL / 'forge_sol_S33_advice_net_20261026.md').read_text(encoding='utf-8'))
        self.assertEqual(len(p), 1)
        self.assertIn('table without "approx model" label', p[0])
        p = check((SOL / 'forge_sol_S33_sprt_plan_table_20261026.md').read_text(encoding='utf-8'))
        self.assertEqual(len(p), 1)

    def test_caption_or_header_label_required(self):
        table = '|a|b|\n|---|---|\n|1|2|\n'
        self.assertEqual(len(check('Some text.\n\n' + table)), 1)
        self.assertEqual(check('**approx model** — forecast\n\n' + table), [])
        self.assertEqual(check('|a approx model|b|\n|---|---|\n|1|2|\n'), [])
        self.assertEqual(check('Gate figures, fastchess-printed (RESULT.md):\n' + table), [])
        self.assertEqual(len(check('approx model\n\nunrelated paragraph\n\n' + table)), 1)

    def test_removing_a_v2_caption_fails(self):
        text = (HERE / 'forge_sol_S33_advice_net_v2_20261027.md').read_text(encoding='utf-8')
        cut = text.replace('**approx model** — Sol\'s S33 planner (Gaussian online-LLR approximation, 20,000 modeled trials per cell; not\n'
                           'fastchess\'s exact GSPRT, not played games):', 'Model forecasts:')
        self.assertNotEqual(cut, text)
        self.assertEqual(check(cut), [])  # header cells still carry the label (deliberately redundant)
        header = '|Bounds/cap games|P(H1) approx model|P(cap) approx model|Mean games approx model|'
        self.assertIn(header, cut)
        bare = cut.replace(header, '|Bounds/cap games|P(H1)|P(cap)|Mean games|')
        self.assertEqual(len(check(bare)), 1)


class FastchessFigureRule(unittest.TestCase):
    def test_non_fastchess_llr_or_elo_fails(self):
        self.assertEqual(check('G119 (fastchess LLR 1.72) capped.'), [])
        self.assertEqual(len(check('G119 Gaussian LLR 1.727094 at the cap.')), 1)
        self.assertEqual(len(check('G119 LLR 1.73.')), 1)
        self.assertEqual(check('fastchess-printed G119: Elo 9.50 +/- 8.84, LLR 1.72'), [])
        self.assertEqual(len(check('G119: Elo 9.5 +/- 8.84')), 1)
        self.assertEqual(len(check('G100r LLR 2.22 and G119 LLR 2.22')), 1)  # second quote belongs to G119

    def test_v2_net_doc_quotes_are_fastchess(self):
        text = (HERE / 'forge_sol_S33_advice_net_v2_20261027.md').read_text(encoding='utf-8')
        self.assertIn('Elo 9.50 +/- 8.84, LLR 1.72', text)
        bad = text.replace('LLR 1.72', 'LLR 1.727094', 1)
        self.assertEqual(len(check(bad)), 1)


class Render(unittest.TestCase):
    @unittest.skipUnless((SOL / 'forge_sol_S33_sprt_plan_table_20261026.csv').is_file(), 'Sol S33 folder not available')
    def test_render_keeps_numbers_and_adds_labels(self):
        out = Path(tempfile.mkdtemp(prefix='s33v2_render_', dir=SCRATCH))
        n = lab.render(SOL / 'forge_sol_S33_sprt_plan_table_20261026.csv', out / 't.md', out / 't.csv')
        self.assertEqual(n, 630)
        mine = (out / 't.md').read_text(encoding='utf-8').splitlines()
        sol = (SOL / 'forge_sol_S33_sprt_plan_table_20261026.md').read_text(encoding='utf-8').splitlines()
        self.assertEqual([l for l in mine if l.startswith('|G') or l.startswith('|draw')],
                         [l for l in sol if l.startswith('|G') or l.startswith('|draw')])
        self.assertEqual(check('\n'.join(mine)), [])
        self.assertEqual((out / 't.md').read_bytes(), (HERE / 'forge_sol_S33_sprt_plan_table_v2_20261027.md').read_bytes())
        rows = list(csv.DictReader(open(out / 't.csv', encoding='utf-8')))
        orig = list(csv.DictReader(open(SOL / 'forge_sol_S33_sprt_plan_table_20261026.csv', encoding='utf-8')))
        self.assertTrue(all(r['model_label'] == 'approx model' for r in rows))
        self.assertEqual([{k: v for k, v in r.items() if k != 'model_label'} for r in rows], orig)


class ApproxVsExact(unittest.TestCase):
    def test_logged_cells_within_three_points(self):
        rows = json.loads((HERE / 'logs' / 'approx_vs_exact_v2.json').read_text(encoding='utf-8'))
        self.assertEqual(len(rows), 6)
        for r in rows:
            if r['approx_model_sol_csv']:
                self.assertLess(abs(r['diff_P_H1']), 0.03)
                self.assertLess(abs(r['diff_P_cap']), 0.03)
        v1 = rows[-1]['exact']
        self.assertGreater(v1['P_cap'], max(v1['P_H1'], v1['P_H0']))  # cap most likely at true +9.5

    def test_oc_cell_deterministic(self):
        a = ex.oc_cell([9, 130, 435, 163, 13], 10.0, 0.0, 10.0, 200, 300, 5)
        b = ex.oc_cell([9, 130, 435, 163, 13], 10.0, 0.0, 10.0, 200, 300, 5)
        self.assertEqual(a, b)
        self.assertAlmostEqual(a['P_H1'] + a['P_H0'] + a['P_cap'], 1.0)


if __name__ == '__main__':
    unittest.main()
