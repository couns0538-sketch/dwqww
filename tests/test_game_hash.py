import io
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from game_hash import game_records, separation

PGN='[Event "one"]\n[Result "1-0"]\n\n1. e4 e5 2. Nf3 Nc6 1-0\n'

class GameHashTests(unittest.TestCase):
    def test_comments_headers_variations_do_not_hide_duplicate(self):
        other='[Event "renamed"]\n[Result "1-0"]\n\n1. e4 {comment} e5 (1... c5) 2. Nf3 Nc6 1-0\n'
        a=list(game_records(io.StringIO(PGN)))
        b=list(game_records(io.StringIO(other)))
        self.assertEqual(a[0]['game_hash'],b[0]['game_hash'])

    def test_missing_binding_is_unknown_not_zero(self):
        result=separation({'a'},{'b'},bindings_verified=False)
        self.assertEqual(result['status'],'UNVERIFIED')
        self.assertIsNone(result['authentic_game_overlap'])
        self.assertEqual(result['exact_movetext_overlap'],0)

    def test_same_game_different_selected_positions_leaks(self):
        key=list(game_records(io.StringIO(PGN)))[0]['game_hash']
        result=separation({key},{key},bindings_verified=True)
        self.assertEqual(result['status'],'FAIL')
        self.assertEqual(result['authentic_game_overlap'],1)

    def test_setup_requires_original_full_fen(self):
        for pgn in ('[SetUp "1"]\n[Result "*"]\n\n*\n',
                    '[SetUp "1"]\n[FEN "8/8/8/8/8/8/8/K6k w - -"]\n[Result "*"]\n\n*\n'):
            with self.assertRaises(ValueError):
                list(game_records(io.StringIO(pgn)))

    def test_illegal_movetext_rejected(self):
        with self.assertRaises(ValueError):
            list(game_records(io.StringIO('[Result "*"]\n\n1. e5 *\n')))

if __name__=='__main__':
    unittest.main()
