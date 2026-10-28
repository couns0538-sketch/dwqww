#!/usr/bin/env python3
"""test_gate_time_audit.py (S38, opus 2026-10-27): unit + fixture tests for forge_sol_S38_gate_time_audit_20261027.py.
The tool is loaded from $S38_TOOL (default: next to this file) so mutation_check_s38.py can test mutants.
Scratch files go to $S38_SCRATCH (default: the system temp dir). Run: python -I -B test_gate_time_audit.py"""
import hashlib
import importlib.util
import io
import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.environ.get('S38_TOOL', os.path.join(HERE, 'forge_sol_S38_gate_time_audit_20261027.py'))
GEN = os.path.join(HERE, 'make_s38_fixture.py')
HAND = os.path.join(HERE, 's38_hand_count.sh')
SCRATCH = os.environ.get('S38_SCRATCH', tempfile.gettempdir())
spec = importlib.util.spec_from_file_location('s38tool', TOOL)
T = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)


def run_tool(args):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = T.main(args)
    return code, buf.getvalue()


def sha(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


class Units(unittest.TestCase):
    def test_time_model_known_values(self):
        tm = T.TimeModel()
        self.assertEqual(tm.limits(10100, 100), (533, 2665))   # avail 10090: 10090//22+75=533; min(6054, 2665)
        self.assertEqual(tm.limits(200, 100), (83, 114))       # avail 190: 8+75=83; min(114, 415)
        self.assertEqual(tm.limits(5, 100), (1, 1))            # clamped to available

    def test_percentile_nearest_rank(self):
        s = list(range(1, 101))
        self.assertEqual((T.pct(s, 50), T.pct(s, 95), T.pct(s, 99)), (50, 95, 99))
        self.assertEqual(T.pct(list(range(1, 11)), 50), 5)
        self.assertEqual(T.pct([7], 99), 7)
        self.assertEqual(T.dist([3, 1, 2])['max'], 3)

    def test_parse_comment(self):
        c = T.parse_comment('+0.22/18 0.857s, tl=9.343s')
        self.assertEqual((c['kind'], c['depth'], c['used_ms'], c['tl_ms']), ('engine', 18, 857, 9343))
        c = T.parse_comment('0.00/64 0.001s, tl=7.007s, Draw by 3-fold repetition')
        self.assertEqual((c['used_ms'], c['reason']), (1, 'Draw by 3-fold repetition'))
        self.assertEqual(T.parse_comment('book')['kind'], 'book')
        self.assertEqual(T.parse_comment('-M5/30 0.100s, tl=1.000s')['depth'], 30)
        self.assertEqual(T.parse_comment('+0.10/12 1.234s, tl=-0.012s, White loses on time')['tl_ms'], -12)

    def test_parse_game_fen_and_colors(self):
        mv = T.parse_game({'FEN': '8/8/8/8/8/8/8/K6k b - - 0 10'}, '10... Kg2 {+0.1/5 0.100s, tl=1.000s} 11. Kb2 {book} 1/2-1/2')
        self.assertEqual([(m['ply'], m['color'], m['kind']) for m in mv], [(19, 'b', 'engine'), (20, 'w', 'book')])

    def test_classify_and_loser(self):
        self.assertEqual(T.classify('time forfeit', []), 'tl')
        self.assertEqual(T.classify('normal', ['Black loses on time (12ms overrun)']), 'tl')
        self.assertEqual(T.classify('illegal move', []), 'illegal')
        self.assertEqual(T.classify('abandoned', []), 'crash')
        self.assertEqual(T.classify('normal', ["White's connection stalls"]), 'crash')
        self.assertIsNone(T.classify('normal', ['Draw by 3-fold repetition']))
        self.assertEqual(T.loser_side([], '0-1'), 'w')
        self.assertEqual(T.loser_side(['Black loses on time'], '1-0'), 'b')

    def test_ply_of_position(self):
        self.assertEqual(T.ply_of_position('position startpos'), 0)
        self.assertEqual(T.ply_of_position('position startpos moves e2e4 e7e5 g1f3'), 3)
        self.assertEqual(T.ply_of_position('position fen 8/8/8/8/8/8/8/K6k b - - 0 10 moves h1g1 a1b1'), 21)

    def test_phase_bands(self):
        self.assertEqual([T.phase_of(p, [40, 80]) for p in (39, 40, 79, 80, None)],
                         ['P0_ply<40', 'P1_ply40-79', 'P1_ply40-79', 'P2_ply>=80', 'unknown'])

    def test_engine_log_last_info_min_ms_and_per_engine_games(self):
        lines = ['[Engine] [00:00:00.0] <  3>  A <--- ucinewgame', '[Engine] [00:00:00.0] <  3>  B <--- ucinewgame',
                 '[Engine] [00:00:00.1] <  3>  A <--- position startpos moves e2e4', '[Engine] [00:00:00.1] <  3>  A <--- go wtime 1 btime 1',
                 '[Engine] [00:00:00.2] <  3>  A ---> info depth 5 nodes 100 nps 1000 time 100 pv a',
                 '[Engine] [00:00:00.3] <  3>  A ---> info depth 6 nodes 400 nps 2000 time 200 pv a',
                 '[Engine] [00:00:00.3] <  3>  A ---> bestmove a2a3',
                 '[Engine] [00:00:00.4] <  3>  B <--- position startpos moves e2e4 a2a3', '[Engine] [00:00:00.4] <  3>  B <--- go wtime 1 btime 1',
                 '[Engine] [00:00:00.5] <  3>  B ---> info depth 4 nodes 50 nps 9000 time 50 pv b',
                 '[Engine] [00:00:00.5] <  3>  B ---> bestmove h7h6', 'garbage half line ---> info']
        p = os.path.join(SCRATCH, 's38_unit_engine.log')
        with open(p, 'w', encoding='utf-8', newline='\r\n') as f:
            f.write('\n'.join(lines) + '\n')
        eng = {}
        st, pg = T.audit_engine_logs([p], [40, 80], 100, eng, 5)
        self.assertEqual(eng['A']['nps'], [2000])                  # the LAST info line of the search
        self.assertEqual((eng['B']['nps'], eng['B']['short']), ([], 1))   # 50 ms search below --nps-min-ms
        self.assertEqual(st['unmatched_lines'], 1)
        self.assertEqual([r['searches'] for r in pg['A']], [1])
        self.assertEqual([r['searches'] for r in pg['B']], [0])   # B's game holds no qualifying search
        self.assertEqual(eng['A']['nps_phase'], {'P0_ply<40': [2000]})


class Fixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = tempfile.mkdtemp(prefix='s38fx_', dir=SCRATCH)
        subprocess.run([sys.executable, '-I', '-B', GEN, '--out', cls.d], check=True, capture_output=True)
        with open(os.path.join(HERE, 'fixtures', 'fixture.sha256'), encoding='utf-8') as f:
            cls.want = {n.lstrip('*'): h for h, n in (line.split() for line in f if line.strip())}
        with open(os.path.join(cls.d, 's38fx_truth.json'), encoding='utf-8') as f:
            cls.truth = json.load(f)
        j = lambda n: os.path.join(cls.d, n)
        cls.ref_json, cls.a_json = j('s38fx_REF_report.json'), j('s38fx_A_report.json')
        cls.ref_code, _ = run_tool(['--pgn', j('s38fx_REF.pgn'), '--log', j('s38fx_REF.log'), '--engine-log', j('s38fx_REF_engine_io.log'),
                                    '--label', 's38fx_REF', '--out-json', cls.ref_json, '--out-md', j('s38fx_REF_report.md')])
        cls.a_code, cls.a_md = run_tool(['--pgn', j('s38fx_A.pgn'), '--log', j('s38fx_A.log'), '--engine-log', j('s38fx_A_engine_io.log'),
                                         '--ref', cls.ref_json, '--per-game-nps', '5', '--label', 's38fx_A',
                                         '--out-json', cls.a_json, '--out-md', j('s38fx_A_report.md')])
        with open(cls.a_json, encoding='utf-8') as f:
            cls.A = json.load(f)
        with open(cls.ref_json, encoding='utf-8') as f:
            cls.R = json.load(f)

    def test_fixture_bytes_are_the_committed_ones(self):
        got = {n: sha(os.path.join(self.d, n)) for n in self.want}
        self.assertEqual(got, self.want)

    def test_tl_count_equals_fastchess_own_lines(self):
        c = self.A['cross_checks']['tl_pgn_vs_fastchess_log']
        self.assertTrue(c['match'])
        self.assertEqual(c['pgn'], self.truth['s38fx_A']['tl'])
        self.assertEqual(c['log'], {'base_s38': 1, 'cand_s38': 2})
        self.assertTrue(self.A['cross_checks']['illegal_crash_pgn_vs_fastchess_log']['match'])
        self.assertEqual({n: e['events'] for n, e in self.A['engines'].items()},
                         {'base_s38': {'tl': 1, 'illegal': 1, 'crash': 0}, 'cand_s38': {'tl': 2, 'illegal': 0, 'crash': 1}})
        self.assertEqual(self.A['fastchess_log']['warning_lines'], 1)

    def test_nps_median_equals_generator_truth(self):
        for n in ('base_s38', 'cand_s38'):
            self.assertEqual(self.A['engines'][n]['nps']['median'], round(float(statistics.median(self.truth['s38fx_A']['nps'][n])), 1))
            self.assertEqual(self.A['engines'][n]['engine_moves'], self.truth['s38fx_A']['engine_moves'][n])

    def test_flags(self):
        self.assertEqual(self.ref_code, 0)
        self.assertEqual(self.R['flags'], [])
        self.assertEqual(self.a_code, 1)
        self.assertTrue(any(f.startswith('NPS_ASYMMETRY') for f in self.A['flags']))
        self.assertTrue(any(f.startswith('P99_OVERSHOOT cand_s38') for f in self.A['flags']))
        self.assertFalse(any(f.startswith('P99_OVERSHOOT base_s38') for f in self.A['flags']))
        self.assertFalse(any(f.startswith(('CLOCK_ACCOUNTING', 'CROSS_CHECK')) for f in self.A['flags']))

    def test_golden_reports(self):
        for name, path in (('s38fx_REF_report.json', self.ref_json), ('s38fx_A_report.json', self.a_json),
                           ('s38fx_REF_report.md', self.ref_json[:-4] + 'md'), ('s38fx_A_report.md', self.a_json[:-4] + 'md')):
            # Compare text, not line endings: the golden files follow the checkout's autocrlf setting.
            with open(os.path.join(HERE, 'sample_reports', name), 'rb') as f:
                want = f.read().replace(b'\r\n', b'\n')
            with open(path, 'rb') as f:
                self.assertEqual(f.read().replace(b'\r\n', b'\n'), want, name)

    def test_hand_count_awk_matches(self):
        bash = shutil.which('bash')
        if not bash:
            self.skipTest('bash not available')
        hand = ''
        for e in ('base_s38', 'cand_s38'):
            hand += subprocess.run([bash, HAND, os.path.join(self.d, 's38fx_A_engine_io.log'), e, '5'], check=True,
                                   capture_output=True, text=True).stdout
        tool = ''.join(l + '\n' for l in self.a_md.splitlines() if l.startswith('- ') and ' game ' in l)
        self.assertEqual(tool, hand)

    def test_same_input_byte_identical(self):
        j = lambda n: os.path.join(self.d, n)
        out2 = j('out_A2.json')
        run_tool(['--pgn', j('s38fx_A.pgn'), '--log', j('s38fx_A.log'), '--engine-log', j('s38fx_A_engine_io.log'), '--ref', self.ref_json,
                  '--per-game-nps', '5', '--label', 's38fx_A', '--out-json', out2])
        self.assertEqual(sha(out2), sha(self.a_json))

    def test_clock_tamper_is_flagged(self):
        src = os.path.join(self.d, 's38fx_REF.pgn')
        bad = os.path.join(self.d, 'tampered.pgn')
        with open(src, encoding='utf-8') as f:
            t = f.read()
        i = t.index(', tl=', t.index('{-') if '{-' in t else t.index('{+'))
        j = t.index('s}', i)
        with open(bad, 'w', encoding='utf-8', newline='') as f:
            f.write(t[:i] + ', tl=1.234' + t[j:])
        code, _ = run_tool(['--pgn', bad, '--out-json', os.path.join(self.d, 'tamper.json')])
        with open(os.path.join(self.d, 'tamper.json'), encoding='utf-8') as f:
            self.assertTrue(any(f.startswith('CLOCK_ACCOUNTING') for f in json.load(f)['flags']))
        self.assertEqual(code, 1)

    def test_refuses_protected_or_input_outputs(self):
        pgn = os.path.join(self.d, 's38fx_REF.pgn')
        bad = r'D:\grok-pc-data\forge_push\__s38_no_such_dir__\x.json'
        code, _ = run_tool(['--pgn', pgn, '--out-json', bad])
        self.assertEqual(code, 2)
        self.assertFalse(os.path.exists(bad))
        code, _ = run_tool(['--pgn', pgn, '--out-md', pgn])
        self.assertEqual(code, 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
