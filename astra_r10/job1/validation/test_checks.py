import argparse, io, pathlib, sys, unittest
from unittest.mock import Mock
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from validate_uci import Engine,validate_start,smoke_move,chess

class SafetyChecks(unittest.TestCase):
    def test_invalid_and_terminal_starts_refused(self):
        for b in [chess.Board(None),chess.Board('7k/5Q2/6K1/8/8/8/8/8 b - - 0 1')]:
            with self.assertRaises(RuntimeError):validate_start(b)
        validate_start(chess.Board())
    def test_slow_smoke_move_refused(self):
        e=Mock();e.last_move_seconds=.501;e.move.return_value=chess.Move.from_uci('e2e4')
        with self.assertRaises(RuntimeError):smoke_move(e,chess.Board())
        e.last_move_seconds=.1
        self.assertEqual(smoke_move(e,chess.Board()),chess.Move.from_uci('e2e4'))
    def test_incomplete_drain_cannot_pass(self):
        e=object.__new__(Engine);e.p=Mock();e.p.poll.return_value=0
        e.reader=Mock();e.reader.is_alive.return_value=True;e.log=io.StringIO()
        with self.assertRaisesRegex(RuntimeError,'drain'):e.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--threads',choices=['1'],required=True);p.parse_args()
    unittest.main(argv=[sys.argv[0]])
