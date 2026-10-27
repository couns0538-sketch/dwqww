"""Tests for the S06 fix-ups S06-1, S06-2, S06-3 (v2 modules). Synthetic PGN/log/RESULT fixtures are
clearly synthetic; the gate table fixture is a read-only extract of real PC RESULT.md files.
Opt-in real-gate test: set FORGE_S06_REAL_GATE (a folder holding one gate's .pgn, .log and RESULT.md copies)
plus FORGE_S06_REAL_CANDIDATE / FORGE_S06_REAL_BASELINE."""
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import forge_sol_S06_statistics_v2 as st  # noqa: E402
import forge_sol_S06_pgn_v2 as pgn  # noqa: E402
import forge_sol_S06_logs_v2 as logs  # noqa: E402

CLI = HERE / 'forge_sol_S06_gatelog_miner_v2.py'
RESULT = 'forge_sol_S06_result_v2.json'
TABLE = HERE / 'fixtures' / 'gate_results_normalized.tsv'
BOOK = '1. d4 {book} Nf6 {book} 2. c4 {book} e6 {book}'
BOOK2 = '1. e4 {book} e5 {book} 2. Nf3 {book} Nc6 {book}'


def fc_game(round_, white, black, result, *, book=BOOK, termination='normal', event='SYNTHETIC fastchess-style'):
    """Synthetic game in the fastchess gate dialect: no FEN tag, book moves marked {book}."""
    tags = {'Event': event, 'Site': '?', 'Round': round_, 'White': white, 'Black': black, 'Result': result,
            'TimeControl': '10+0.1'}
    if termination is not None:
        tags['Termination'] = termination
    head = '\n'.join(f'[{k} "{v}"]' for k, v in tags.items())
    return head + '\n\n' + book + ' 3. Nc3 {+0.10/12 0.100s, tl=9.9s} Bb4 {-0.10/12 0.100s} ' + result + '\n\n'


def fc_pair(round_, first, second, **kw):
    """Round with the candidate white in game 1 and black in game 2; results from the PGN's point of view."""
    return fc_game(round_, 'Cand', 'Base', first, **kw) + fc_game(round_, 'Base', 'Cand', second, **kw)


class ExactLLR(unittest.TestCase):
    """S06-1: exact fastchess normalized-pentanomial GSPRT is the primary LLR; Gaussian is secondary."""

    def test_g120_known_answer(self):
        r = st.summarize_pentanomial([5, 74, 252, 119, 14], e0=0, e1=10)
        self.assertEqual(r['llr_primary'], 'exact_llr')
        self.assertTrue(r['exact_llr']['primary'])
        self.assertTrue(r['exact_llr']['exact_fastchess'])
        self.assertFalse(r['gaussian_llr']['primary'])
        self.assertAlmostEqual(r['exact_llr']['value'], 2.992, delta=0.0005)
        self.assertEqual(round(r['exact_llr']['value'], 2), 2.99)
        d = r['fastchess_display']
        self.assertEqual((round(d['elo'], 2), round(d['elo_error95'], 2)), (23.62, 11.90))
        self.assertEqual((round(d['nelo'], 2), round(d['nelo_error95'], 2)), (44.52, 22.35))
        self.assertEqual(r['wald_diagnostic']['llr_used'], 'exact_llr')
        self.assertEqual(r['wald_diagnostic']['decision'], 'accept_h1_diagnostic')
        self.assertFalse(r['inference']['acceptance_authorized'])

    def test_reproduces_printed_statistics_of_every_normalized_pc_gate(self):
        rows = [line.rstrip('\n').split('\t') for line in TABLE.read_text(encoding='utf-8').splitlines()
                if line and not line.startswith('#')]
        header, rows = rows[0], rows[1:]
        self.assertGreaterEqual(len(rows), 40)
        for row in rows:
            g = dict(zip(header, row))
            counts = [int(x) for x in g['ptnml'].split(',')]
            e0, e1 = float(g['e0']), float(g['e1'])
            with self.subTest(gate=g['gate_dir']):
                exact = st.fastchess_llr(counts, e0, e1)
                self.assertLessEqual(abs(exact - float(g['printed_llr'])), 0.0051)
                self.assertLessEqual(abs(st.converged_llr(counts, e0, e1) - float(g['s44_numpy_converged_llr'])), 1e-9)
                self.assertLessEqual(abs(exact - st.converged_llr(counts, e0, e1)), 1e-6)
                d = st.summarize_pentanomial(counts, e0=e0, e1=e1)['fastchess_display']
                for key, printed in (('elo', 'printed_elo'), ('elo_error95', 'printed_elo_err'),
                                     ('nelo', 'printed_nelo'), ('nelo_error95', 'printed_nelo_err'),
                                     ('los_percent', 'printed_los')):
                    self.assertLessEqual(abs(d[key] - float(g[printed])), 0.0051, key)

    def test_decision_follows_exact_not_gaussian(self):
        # Gaussian 2.980 would cross +2.944; the exact LLR 2.935 does not.
        r = st.summarize_pentanomial([5, 73, 247, 117, 14])
        self.assertGreater(r['gaussian_llr']['value'], r['wald_diagnostic']['upper'])
        self.assertLess(r['exact_llr']['value'], r['wald_diagnostic']['upper'])
        self.assertEqual(r['wald_diagnostic']['decision'], 'continue')
        self.assertAlmostEqual(r['llr_difference_exact_minus_gaussian'],
                               r['exact_llr']['value'] - r['gaussian_llr']['value'], places=12)

    def test_zero_cells_are_regularized_like_fastchess(self):
        self.assertIsNone(st.converged_llr([0, 0, 0, 1000, 1000], 0, 10))
        value = st.fastchess_llr([0, 0, 0, 1000, 1000], 0, 10)
        self.assertTrue(math.isfinite(value) and value > 2.944)
        self.assertLess(st.fastchess_llr([1000, 1000, 0, 0, 0], 0, 10), -2.944)

    def test_logistic_units_use_the_logistic_port(self):
        r = st.summarize_pentanomial([5, 74, 252, 119, 14], units='logistic', e0=0, e1=5)
        self.assertIn('logistic', r['exact_llr']['model'])
        self.assertTrue(math.isfinite(r['exact_llr']['value']))
        self.assertGreater(r['exact_llr']['value'], 0)

    def test_symmetry(self):
        a = st.fastchess_llr([5, 74, 252, 119, 14], -10, 10)
        b = st.fastchess_llr([14, 119, 252, 74, 5], -10, 10)
        self.assertAlmostEqual(a, -b, places=6)


class RealGateDialect(unittest.TestCase):
    """S06-2 building blocks: fastchess PGNs (no FEN, {book} moves), orphan games, finished-game pairing."""

    def test_book_moves_identify_openings(self):
        report = pgn.mine_pgn(fc_pair('1', '1-0', '0-1') + fc_pair('2', '1/2-1/2', '1-0', book=BOOK2), 'Cand', 'Base')
        self.assertEqual(report['games'][0]['opening_key'], 'book:d4 Nf6 c4 e6')
        self.assertEqual(report['games'][0]['book_moves'], 4)
        self.assertEqual(report['paired']['valid_pairs'], 2)
        # Round 1: candidate wins both games (WW, cell 4); round 2: draw + loss (LD, cell 1).
        self.assertEqual(report['paired']['pentabins'], [0, 1, 0, 0, 1])
        self.assertTrue(report['paired']['aggregate_eligible'])

    def test_book_mismatch_within_a_round_is_not_a_pair(self):
        text = fc_game('1', 'Cand', 'Base', '1-0') + fc_game('1', 'Base', 'Cand', '0-1', book=BOOK2)
        report = pgn.mine_pgn(text, 'Cand', 'Base')
        self.assertEqual(report['paired']['valid_pairs'], 0)
        self.assertIn('opening_mismatch', report['pairs'][0]['issues'])

    def test_no_book_and_no_fen_stays_unknown(self):
        text = fc_pair('1', '1-0', '0-1', book='1. d4 Nf6')
        report = pgn.mine_pgn(text, 'Cand', 'Base')
        self.assertIn('opening_unknown', report['pairs'][0]['issues'])

    def test_orphan_game_is_excluded_and_not_blocking(self):
        text = fc_pair('1', '1-0', '0-1') + fc_pair('2', '1/2-1/2', '1/2-1/2', book=BOOK2) + \
            fc_game('3', 'Cand', 'Base', '1-0', book='1. c4 {book} c5 {book}')
        report = pgn.mine_pgn(text, 'Cand', 'Base')
        self.assertEqual(report['raw']['games'], 5)
        self.assertEqual(report['paired']['orphan_games'], 1)
        self.assertEqual(report['paired']['valid_pairs'], 2)
        self.assertEqual(report['paired']['pentabins'], [0, 0, 1, 0, 1])
        self.assertTrue(report['paired']['aggregate_eligible'])
        self.assertEqual(report['orphans'][0]['pair_key'], '3')
        self.assertFalse(any(i['code'] == 'orphan_game' for i in report['issues']))
        only = pgn.mine_pgn(fc_game('1', 'Cand', 'Base', '1-0'), 'Cand', 'Base')
        self.assertFalse(only['paired']['aggregate_eligible'])

    def test_log_orphan_matches_summary_of_complete_pairs(self):
        # fastchess summaries count complete pairs only (G120: 929 finished lines, Games 928).
        text = ('Finished game 1 (Cand vs Base): 1-0 {White mates}\n'
                'Finished game 2 (Base vs Cand): 0-1 {Black mates}\n'
                'Finished game 3 (Cand vs Base): 1/2-1/2 {Draw}\n'
                'Results of Cand vs Base (10+0.1, 1t, 16MB, book.pgn):\n'
                'Games: 2, Wins: 2, Losses: 0, Draws: 0, Points: 2.0 (100.00 %)\n'
                'Ptnml(0-2): [0, 0, 0, 0, 1], WL/DD Ratio: 0.00\n'
                'LLR: 0.10 (3.4%) (-2.94, 2.94) [0.00, 10.00]\n')
        r = logs.mine_log(text, 'Cand', 'Base')
        self.assertEqual(r['status'], 'PARSED', r['issues'])
        self.assertEqual(r['finished']['summary_view'], 'complete_pairs_only')
        self.assertEqual(r['finished']['orphan_game_ids'], [3])
        self.assertEqual(r['finished']['summary_ptnml_vs_finished_pairs'], 'PASS')
        bad = logs.mine_log(text.replace('[0, 0, 0, 0, 1]', '[0, 0, 0, 1, 0]'), 'Cand', 'Base')
        self.assertEqual(bad['status'], 'BLOCKED')


class TerminationsAndInputs(unittest.TestCase):
    """S06-3: non-normal Termination pairs, more than one PGN."""

    def test_non_normal_termination_pairs_are_counted(self):
        text = (fc_pair('1', '1-0', '0-1') +
                fc_game('2', 'Cand', 'Base', '0-1', book=BOOK2, termination='time forfeit') +
                fc_game('2', 'Base', 'Cand', '1-0', book=BOOK2) +
                fc_game('3', 'Cand', 'Base', '1-0', book='1. c4 {book}', termination=None) +
                fc_game('3', 'Base', 'Cand', '0-1', book='1. c4 {book}', termination='abandoned'))
        report = pgn.mine_pgn(text, 'Cand', 'Base')
        paired = report['paired']
        self.assertEqual(paired['non_normal_termination_pairs'], 2)
        self.assertEqual(paired['non_normal_termination_pairs_by_value'],
                         {'abandoned': 1, 'missing': 1, 'time forfeit': 1})
        self.assertEqual(report['raw']['non_normal_termination_games'], 3)
        self.assertFalse(paired['aggregate_eligible'])

    def test_several_pgns_are_mined_together(self):
        report = pgn.mine_pgns([fc_pair('1', '1-0', '0-1'), fc_pair('2', '0-1', '1-0', book=BOOK2)], 'Cand', 'Base')
        self.assertEqual(report['sources'], 2)
        self.assertEqual([g['source'] for g in report['games']], [0, 0, 1, 1])
        self.assertEqual(report['paired']['pentabins'], [1, 0, 0, 0, 1])
        self.assertTrue(report['paired']['aggregate_eligible'])

    def test_same_pgn_twice_is_not_double_counted(self):
        text = fc_pair('1', '1-0', '0-1')
        report = pgn.mine_pgns([text, text], 'Cand', 'Base')
        self.assertEqual(report['paired']['valid_pairs'], 0)
        self.assertIn('pair_game_count', report['pairs'][0]['issues'])

    def test_truncated_game_does_not_merge_into_the_next_file(self):
        first = fc_pair('1', '1-0', '0-1') + '[Event "SYNTHETIC fastchess-style"]\n[Round "9"]\n\n1. e4 {book}'
        report = pgn.mine_pgns([first, fc_pair('2', '0-1', '1-0', book=BOOK2)], 'Cand', 'Base')
        self.assertEqual(report['raw']['games'], 5)
        self.assertEqual(report['games'][2]['source'], 0)
        self.assertEqual(report['paired']['valid_pairs'], 2)


RESULT_MD = '''\ufeff# gateX_synthetic RESULT: Cand vs Base (SYNTHETIC)
- Settings: fastchess 1.8.2, 10+0.1 timemargin=1000, SPRT normalized [0,10] a=b=0.05 (synthetic).
- Games: 8  W/L/D (candidate view): 3 / 2 / 3  Points 4.5 (56.25 %)
- Pentanomial Ptnml(0-2): [0, 1, 2, 0, 1]  complete pairs = 4
- Elo: {elo} +/- {err}   nElo: {nelo} +/- {nerr}   LOS {los} %
- LLR: {llr}  bounds (-2.94, 2.94)  [elo0=0, elo1=10, normalized]
- Time losses: 0   Crashes/disconnects/stalls/illegal: 0   fastchess 'Warning;' lines: 0   (clean requires 0 and 0): CLEAN
- **Verdict: synthetic**
'''
LOG = '''Finished game 1 (Cand vs Base): 1-0 {White mates}
Finished game 2 (Base vs Cand): 0-1 {Black mates}
Finished game 3 (Cand vs Base): 1/2-1/2 {Draw by 3-fold repetition}
Finished game 4 (Base vs Cand): 1-0 {White mates}
Finished game 6 (Base vs Cand): 1/2-1/2 {Draw by 3-fold repetition}
Finished game 5 (Cand vs Base): 1/2-1/2 {Draw by 3-fold repetition}
Finished game 7 (Cand vs Base): 1-0 {White mates}
Finished game 8 (Base vs Cand): 1-0 {White mates}
--------------------------------------------------
Results of Cand vs Base (10+0.1, 1t, 16MB, book.pgn):
Games: 8, Wins: 3, Losses: 2, Draws: 3, Points: 4.5 (56.25 %)
Ptnml(0-2): [0, 1, 2, 0, 1], WL/DD Ratio: 1.00
LLR: {llr} (1.0%) (-2.94, 2.94) [0.00, 10.00]
--------------------------------------------------
Finished match
'''


class CommandLine(unittest.TestCase):
    """S06-2 reconciliation through the CLI and the S06-3 --out guard / repeated --pgn."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        d = st.summarize_pentanomial([0, 1, 2, 0, 1])
        disp, llr = d['fastchess_display'], d['exact_llr']['value']
        self.result_text = RESULT_MD.format(elo=f"{disp['elo']:.2f}", err=f"{disp['elo_error95']:.2f}",
                                            nelo=f"{disp['nelo']:.2f}", nerr=f"{disp['nelo_error95']:.2f}",
                                            los=f"{disp['los_percent']:.2f}", llr=f'{llr:.2f}')
        self.log_text = LOG.replace('{llr}', f'{llr:.2f}')
        self.pgn_a = self.root / 'a.pgn'
        # Rounds 1-2 in a.pgn, 3-4 in b.pgn: WW, LD, DD, WL -> Ptnml [0, 1, 2, 0, 1], W/D/L 3/3/2.
        self.pgn_a.write_text(fc_pair('1', '1-0', '0-1') + fc_pair('2', '1/2-1/2', '1-0', book=BOOK2), encoding='utf-8')
        self.pgn_b = self.root / 'b.pgn'
        self.pgn_b.write_text(fc_pair('3', '1/2-1/2', '1/2-1/2', book='1. c4 {book} c5 {book}') +
                              fc_pair('4', '1-0', '1-0', book='1. Nf3 {book} d5 {book}'), encoding='utf-8')
        self.log = self.root / 'x.log'
        self.log.write_text(self.log_text, encoding='utf-8')
        self.res = self.root / 'inputs_RESULT.md'
        self.res.write_text(self.result_text, encoding='utf-8')

    def tearDown(self):
        self.tmp.cleanup()

    def cli(self, *args, out=None, env=None):
        out = out or self.root / 'new_out'
        run = subprocess.run([sys.executable, '-B', str(CLI), *map(str, args), '--out', str(out)],
                             capture_output=True, text=True, timeout=60, env={**os.environ, **(env or {})})
        return run, out

    def mine_args(self, *extra):
        return ('mine', '--gate-id', 'synthetic', '--candidate', 'Cand', '--baseline', 'Base',
                '--pgn', self.pgn_a, '--pgn', self.pgn_b, '--log', self.log, '--result', self.res, *extra)

    def test_two_pgns_log_and_result_reconcile(self):
        run, out = self.cli(*self.mine_args())
        self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
        data = json.loads((out / RESULT).read_text())
        self.assertEqual(data['status'], 'RECONCILED')
        fields = {c['field']: c['status'] for c in data['reconciliation']['comparisons']}
        for key in ('pentabins (Ptnml 0-2)', 'time_losses', 'wdl (candidate W/D/L, complete pairs)',
                    'LLR (exact GSPRT from Ptnml vs printed)', 'elo (recomputed vs RESULT.md)'):
            self.assertEqual(fields[key], 'PASS', key)
        self.assertEqual(len([i for i in data['inputs'] if i['role'] == 'pgn']), 2)

    def test_result_mismatch_blocks(self):
        self.res.write_text(self.result_text.replace('[0, 1, 2, 0, 1]', '[0, 2, 1, 0, 1]'), encoding='utf-8')
        run, out = self.cli(*self.mine_args())
        self.assertEqual(run.returncode, 1)
        data = json.loads((out / RESULT).read_text())
        self.assertEqual(data['status'], 'BLOCKED')
        self.assertIn('FAIL', [c['status'] for c in data['reconciliation']['comparisons']
                               if c['field'] == 'pentabins (Ptnml 0-2)'])

    def test_time_loss_in_result_but_not_in_games_blocks(self):
        self.res.write_text(self.result_text.replace('Time losses: 0', 'Time losses: 1'), encoding='utf-8')
        run, out = self.cli(*self.mine_args())
        self.assertEqual(run.returncode, 1)
        data = json.loads((out / RESULT).read_text())
        self.assertIn('time_losses mismatch; no favorable subset selected', data['reconciliation']['issues'])

    def test_hash_only_inputs_and_summary_detail(self):
        run, out = self.cli(*self.mine_args('--hash-only-inputs', '--detail', 'summary'))
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(sorted(p.name for p in out.iterdir()),
                         ['forge_sol_S06_SHA256SUMS_v2.txt', RESULT])
        data = json.loads((out / RESULT).read_text())
        self.assertNotIn('games', data['pgn'])
        self.assertTrue(all(i['saved_as'] is None and len(i['sha256']) == 64 for i in data['inputs']))

    def test_out_refuses_gate_lock_queue_and_protected_dirs(self):
        refused = [self.root / 'gate38_packa_w55_vs_h256e12' / 'out', self.root / 'gate_auto_e48f029' / 'out',
                   self.root / 'forge_LOCK_AL1_s198_FULL' / 'out', self.root / '3_lock_record' / 'out',
                   self.root / 'run_queue' / 'out']
        for out in refused:
            out.parent.mkdir()
            with self.subTest(out=out):
                run, _ = self.cli('counts', '--penta', 1, 2, 3, 2, 1, out=out)
                self.assertEqual(run.returncode, 1)
                self.assertIn('gate/lock/queue', run.stderr)
                self.assertFalse(out.exists())
        marked = self.root / 'copied_gate'
        marked.mkdir()
        (marked / 'RUN_INFO.json').write_text('{}')
        run, _ = self.cli('counts', '--penta', 1, 2, 3, 2, 1, out=marked / 'sub' / 'out')
        self.assertEqual(run.returncode, 1)
        self.assertIn('gate markers', run.stderr)
        mine = self.root / 'protected_by_flag'
        mine.mkdir()
        run, _ = self.cli('counts', '--penta', 1, 2, 3, 2, 1, '--protect', mine, out=mine / 'out')
        self.assertEqual(run.returncode, 1)
        run, _ = self.cli('counts', '--penta', 1, 2, 3, 2, 1, out=mine / 'out2',
                          env={'FORGE_S06_PROTECTED': str(mine)})
        self.assertEqual(run.returncode, 1)
        self.assertIn('protected PC data', run.stderr)
        run, out = self.cli('counts', '--penta', 1, 2, 3, 2, 1, out=self.root / 'scratch_out')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue((out / RESULT).is_file())

    def test_default_protected_roots(self):
        # The parent below each root does not exist, so even a broken guard could not create anything there.
        for root in ('D:/grok-pc-data/forge_push', 'F:/forge_nnue_train', 'C:/Users/Administrator/grok-pc',
                     'D:/grok-pc-data/selfplay_out'):
            with self.subTest(root=root):
                out = Path(root) / 'S06_no_such_parent_0f3c' / 'out'
                self.assertFalse(out.parent.exists())
                run, _ = self.cli('counts', '--penta', 1, 2, 3, 2, 1, out=out)
                self.assertEqual(run.returncode, 1)
                self.assertIn('protected PC data', run.stderr)
                self.assertFalse(out.parent.exists())


@unittest.skipUnless(os.environ.get('FORGE_S06_REAL_GATE'), 'set FORGE_S06_REAL_GATE to a copied gate folder')
class RealGate(unittest.TestCase):
    def test_real_gate_reconciles_with_its_result(self):
        folder = Path(os.environ['FORGE_S06_REAL_GATE'])
        pgns = sorted(folder.glob('*.pgn'))
        log = sorted(folder.glob('*.log'))[0]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'real_out'
            args = ['mine', '--gate-id', folder.name, '--candidate', os.environ['FORGE_S06_REAL_CANDIDATE'],
                    '--baseline', os.environ['FORGE_S06_REAL_BASELINE'], '--log', str(log),
                    '--result', str(folder / 'RESULT.md'), '--detail', 'summary', '--hash-only-inputs']
            for p in pgns:
                args += ['--pgn', str(p)]
            run = subprocess.run([sys.executable, '-B', str(CLI), *args, '--out', str(out)],
                                 capture_output=True, text=True, timeout=600)
            self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
            data = json.loads((out / RESULT).read_text())
            self.assertEqual(data['status'], 'RECONCILED')
            self.assertTrue(all(c['status'] == 'PASS' for c in data['reconciliation']['comparisons']))


if __name__ == '__main__':
    unittest.main()
