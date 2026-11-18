import json
from pathlib import Path
import tempfile
import unittest

import uci_stream


MOCK = '''#!/usr/bin/env python3
import sys

previous = False
wrong = False
for raw in sys.stdin:
    cmd = ' '.join(raw.split())
    if cmd == 'uci':
        print('id name test mock')
        for key in {options!r}:
            print('option name ' + key + ' type string')
        print('uciok', flush=True)
    elif cmd == 'setoption name NNUEArch value true':
        print('info string NNUE v3 active: mock hidden 768 checksum 30ab43b4ba5db5f3', flush=True)
    elif cmd == 'ucinewgame':
        previous = False
    elif cmd == 'isready':
        print('readyok', flush=True)
    elif cmd.startswith('position '):
        wrong = {control!r} and previous and 'c7c5' in cmd
        previous = True
        if 'b0b9' in cmd:
            print('info string illegal move b0b9', flush=True)
    elif cmd == 'go perft 1':
        print('a2a3: 1' if wrong else 'h2h3: 1')
        print('nodes 1', flush=True)
    elif cmd == 'eval':
        print('info string eval hce 0 nnue 7 total 7', flush=True)
    elif cmd in ('go depth 4', 'go nodes 2000'):
        print('info depth 4 score cp 12 nodes 30 nps {noise} time {noise} hashfull {noise} pv e2e4')
        print('bestmove e2e4', flush=True)
    elif cmd == 'quit':
        break
'''


class TestStream(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.fixture = self.work / 'fixture.jsonl'
        self.rows = [
            {'index': 1, 'kind': 'fork_base', 'position': 'position startpos moves e2e4 e7e5', 'before': []},
            {'index': 2, 'kind': 'fork', 'position': 'position\tstartpos moves e2e4 c7c5', 'before': []},
            {'index': 3, 'kind': 'illegal', 'position': 'position startpos moves e2e4 b0b9',
             'before': ['go depth 4', 'setoption name Hash value 16', 'isready']},
            {'index': 4, 'kind': 'reset', 'position': 'position startpos',
             'before': ['ucinewgame', 'go nodes 2000', 'setoption name Hash value 16']},
        ]
        self.fixture.write_text(''.join(json.dumps(row) + '\n' for row in self.rows))

    def run_fake(self, label, mode, *, control=False, noise=10):
        fake = self.work / (label + '.py')
        fake.write_text(MOCK.format(control=control, noise=noise,
                                    options=[*uci_stream.identity.PC20, 'NNUEArch', 'NNUEArchFile']))
        fake.chmod(0o700)
        out = self.work / label
        result = uci_stream.run_stream(fake, self.work / 'synthetic', uci_stream.fixture_rows(self.fixture), mode, out, 2)
        result.update({'build': label, 'fixture': str(self.fixture), 'fixture_sha256': uci_stream.digest(self.fixture)})
        (out / 'summary.json').write_text(json.dumps(result))
        self.assertIsNone(result['error'])
        self.assertEqual(result['positions_completed'], 4)
        return out, result

    def test_cross_mode_common_and_within_mode_search(self):
        cached, cached_data = self.run_fake('cached', 'cached')
        reset, reset_data = self.run_fake('reset', 'reset', noise=110)
        other_cached, _ = self.run_fake('other_cached', 'cached', noise=210)
        self.assertEqual(reset_data['raw_stdout_lines'] - cached_data['raw_stdout_lines'], 4)
        self.assertEqual(reset_data['raw_stdin_lines'] - cached_data['raw_stdin_lines'], 8)
        common = uci_stream.compare_channel('common', [cached, reset, other_cached])
        self.assertTrue(all(pair['equal'] for pair in common['comparisons']))
        self.assertIn('info string illegal move b0b9\n', (reset / 'common.txt').read_text())
        self.assertIn('position\tstartpos', (reset / 'commands.txt').read_text())
        self.assertTrue(uci_stream.compare_channel('search', [cached, other_cached])['comparisons'][0]['equal'])
        search = (cached / 'search.txt').read_text()
        self.assertEqual(search, 'info depth 4 score cp 12 nodes 30 pv e2e4\nbestmove e2e4\n' * 2)
        with self.assertRaisesRegex(RuntimeError, 'require one mode'):
            uci_stream.compare_channel('search', [cached, reset])

    def test_control_matches_reset_first_mismatch_provenance(self):
        control, _ = self.run_fake('control', 'cached', control=True)
        reset, _ = self.run_fake('control_reset', 'reset', control=True)
        result = uci_stream.compare_channel('common', [reset, control])['comparisons'][0]
        self.assertFalse(result['equal'])
        found = result['first_difference']
        self.assertEqual(found['baseline']['raw_stdout_line'], 'h2h3: 1')
        self.assertEqual(found['candidate']['raw_stdout_line'], 'a2a3: 1')
        self.assertEqual(found['candidate']['fixture_row']['index'], 2)
        self.assertNotEqual(found['baseline']['raw_stdout_line_no'], found['candidate']['raw_stdout_line_no'])


if __name__ == '__main__':
    unittest.main()
