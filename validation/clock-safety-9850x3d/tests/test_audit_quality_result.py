#!/usr/bin/env python3
"""Lightweight synthetic tests; no engine, match, or build is executed.

Run with PYTHONDONTWRITEBYTECODE=1 python3 test_audit_quality_result.py.
"""
import importlib.util
import hashlib
import json
import math
import re
import sys
from pathlib import Path
import subprocess
import tempfile
import unittest

sys.dont_write_bytecode = True
SCRIPT = Path(__file__).resolve().with_name('audit-quality-result.py')


def module():
    if not SCRIPT.exists():
        raise AssertionError('standalone quality auditor has not been implemented')
    spec = importlib.util.spec_from_file_location('independent_quality_audit', SCRIPT)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


class AuditTests(unittest.TestCase):
    def fixture(self, root):
        audit = module()
        run = root / 'run'
        run.mkdir()
        def write(name, value):
            (run / name).write_text(json.dumps(value))
        selected = ['rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -',
                    'rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR w KQkq -']
        (run / 'selected.epd').write_text('\n'.join(selected) + '\n')
        inputs = {}
        for key in ['baseline', 'candidate', 'fastchess', 'corpus', 'original_zip', 'pgn_checker', 'protocol_runner', 'selected']:
            path = run / 'selected.epd' if key == 'selected' else root / key
            if key != 'selected':
                path.write_text(key)
            inputs[key] = {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        command = [inputs['fastchess']['path'], '-strict']
        sprt = {'alpha': .05, 'beta': .05, 'elo0': 0, 'elo1': 20, 'model': 'logistic', 'bounds': [-math.log(19), math.log(19)]}
        protocol = dict(kind='fixed-node search-quality SPRT', nodes_per_move=10000, tc='inf', threads=1,
                        hash_mib=32, ownbook=False, restart=True, concurrency=1, max_pairs=2,
                        inputs=inputs, command=command, selected_fens=selected, sprt=sprt)
        write('protocol.json', protocol)
        write('input-hashes.json', inputs)
        write('command.json', command)
        games = []
        console = []
        for i in range(4):
            white, black = ('Candidate', 'Baseline') if i % 2 == 0 else ('Baseline', 'Candidate')
            games.append(f'[Event "Fixture"]\n[Round "{i//2+1}"]\n[White "{white}"]\n[Black "{black}"]\n'
                         f'[Result "1-0"]\n[SetUp "1"]\n[FEN "{selected[i//2]} 0 1"]\n[PlyCount "2"]\n'
                         '[Termination "normal"]\n[TimeControl "-"]\n\n1. e2e4 {0.00/1 n=5} e7e5 1-0\n')
            console += [f'Started game {i+1} of 4 ({white} vs {black})',
                        f'Finished game {i+1} ({white} vs {black}): 1-0 {{White mates}}']
        penta = [0, 0, 2, 0, 0]
        console += ['Games: 4, Wins: 2, Losses: 2, Draws: 0, Points: 2.0 (50.00 %)',
                    'Ptnml(0-2): [0, 0, 2, 0, 0], WL/DD Ratio: inf',
                    f'LLR: {audit.logistic_llr(penta, 0, 20):.2f} (0.0%) (-2.94, 2.94) [0.00, 20.00]', 'Finished match']
        (run / 'games.pgn').write_text('\n'.join(games))
        (run / 'console.txt').write_text('\n'.join(console) + '\n')
        (run / 'fastchess.log').write_text('')
        stats = dict(pairs=2, games=4, candidate_wins_draws_losses=[2, 0, 2], pentanomial_0_half_1_1half_2=penta,
                     unique_openings=2, terminations={'normal': 4}, score_fraction=.5)
        write('stats.json', stats)
        native = {'wins': 2, 'draws': 0, 'losses': 2, 'penta_LL': 0, 'penta_LD': 0, 'penta_WL': 2,
                  'penta_DD': 0, 'penta_WD': 0, 'penta_WW': 0}
        engines = [dict(name=n, cmd=inputs[n.lower()]['path'], restart=True,
                        options=[['OwnBook', 'false'], ['Threads', '1'], ['Hash', '32']],
                        limit={'nodes': 10000, 'plies': 0, 'tc': {'time': 0, 'fixed_time': 0, 'increment': 0, 'moves': 0, 'timemargin': 0}})
                   for n in ['Candidate', 'Baseline']]
        state = dict(rounds=2, games=2, concurrency=1, report_penta=True, noswap=False, reverse=False, recover=False,
                     sprt={**sprt, 'enabled': True}, engines=engines,
                     opening={'order': 1, 'start': 1, 'file': str(run / 'selected.epd')}, stats={'Candidate vs Baseline': native})
        state.update({key: {'enabled': False} for key in ['resign', 'draw', 'maxmoves', 'tb_adjudication']})
        write('state.json', state)
        result = dict(status='completed', exit_code=0, statistics=stats, progress={'finished_game_messages': 4},
                      quality_gain_established=False, equal_clock_gain_established=False, sprt_decision='inconclusive_at_pair_cap',
                      final_input_hashes={key: value['sha256'] for key, value in inputs.items()},
                      outputs_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in run.iterdir()})
        write('result.json', result)
        return run

    def test_full_completed_cap_fixture_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            report = module().audit_run(self.fixture(Path(directory)))
            self.assertEqual(report['errors'], [])
            self.assertEqual(report['supported_decision'], 'inconclusive_at_pair_cap')
            self.assertFalse(report['quality_gain_established'])

    def test_input_and_output_tampering_cannot_establish_result(self):
        for target in ['candidate', 'run/console.txt']:
            with self.subTest(target=target), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                run = self.fixture(root)
                path = root / target
                path.write_text(path.read_text() + '\nchanged')
                report = module().audit_run(run)
                self.assertEqual(report['audit_status'], 'failed')
                self.assertFalse(report['quality_gain_established'])
                self.assertTrue(any('hash changed' in error for error in report['errors']), report['errors'])

    def test_cli_requires_new_external_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = self.fixture(root)
            output = root / 'audit.json'
            result = subprocess.run(['python3', str(SCRIPT), '--run', str(run), '--output', str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertEqual(json.loads(output.read_text())['audit_status'], 'passed')
            for forbidden in [output, run / 'audit.json']:
                result = subprocess.run(['python3', str(SCRIPT), '--run', str(run), '--output', str(forbidden)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 2, result.stderr + result.stdout)
            self.assertFalse((run / 'audit.json').exists())

    def test_rehashed_semantic_failures_remain_unsupported(self):
        changes = {
            'non_normal': ('games.pgn', lambda s: s.replace('[Termination "normal"]', '[Termination "time forfeit"]', 1)),
            'wrong_round': ('games.pgn', lambda s: s.replace('[Round "1"]', '[Round "2"]', 1)),
            'wrong_likelihood': ('console.txt', lambda s: re.sub(r'LLR: [^ ]+', 'LLR: 1.23', s)),
            'false_acceptance': ('console.txt', lambda s: s + 'SPRT ([0.00, 20.00]) completed - H1 was accepted\n'),
        }
        for name, (file, transform) in changes.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                run = self.fixture(Path(directory))
                path = run / file
                path.write_text(transform(path.read_text()))
                result_path = run / 'result.json'
                result = json.loads(result_path.read_text())
                result['outputs_sha256'][file] = hashlib.sha256(path.read_bytes()).hexdigest()
                result_path.write_text(json.dumps(result))
                report = module().audit_run(run)
                self.assertEqual(report['audit_status'], 'failed')
                self.assertFalse(report['quality_gain_established'])
                self.assertTrue(report['errors'])

    def test_independent_likelihood_matches_known_pentanomial_example(self):
        audit = module()
        self.assertAlmostEqual(audit.logistic_llr([1, 1, 9, 1, 0], 0, 20), -0.6946618090937976, places=9)

    def test_likelihood_reverses_sign_when_hypotheses_swap(self):
        audit = module()
        counts = [4, 8, 20, 9, 5]
        self.assertAlmostEqual(audit.logistic_llr(counts, 0, 20), -audit.logistic_llr(counts, 20, 0), places=12)

    def test_pgn_parser_checks_actual_move_count_and_terminal_result(self):
        audit = module()
        text = '[Event "Test"]\n[Result "1-0"]\n[PlyCount "2"]\n\n1. e2e4 {ignored 0-1} e7e5 1-0\n'
        games = audit.parse_pgn(text)
        self.assertEqual(games[0]['moves'], ['e2e4', 'e7e5'])
        with self.assertRaises(ValueError):
            audit.parse_pgn(text.replace('e7e5 1-0', 'e7e5 0-1'))
        with self.assertRaises(ValueError):
            audit.parse_pgn(text.replace('[PlyCount "2"]', '[PlyCount "3"]'))

    def test_boundary_check_rejects_rounded_acceptance_without_independent_crossing(self):
        audit = module()
        bound = math.log(19)
        self.assertEqual(audit.classify_decision('H1', bound + .001, bound, -bound, 2, 500), 'H1_accepted')
        with self.assertRaises(ValueError):
            audit.classify_decision('H1', bound - .001, bound, -bound, 2, 500)
        self.assertEqual(audit.classify_decision(None, 0.0, bound, -bound, 500, 500), 'inconclusive_at_pair_cap')
        with self.assertRaises(ValueError):
            audit.classify_decision(None, 0.0, bound, -bound, 499, 500)


if __name__ == '__main__':
    unittest.main(verbosity=2)

