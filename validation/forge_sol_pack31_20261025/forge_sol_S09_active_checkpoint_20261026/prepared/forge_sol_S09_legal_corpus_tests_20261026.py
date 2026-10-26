import importlib.util
from pathlib import Path
import unittest
import chess

spec=importlib.util.spec_from_file_location('corpus',Path(__file__).with_name('forge_sol_S09_legal_corpus_20261026.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class CorpusTests(unittest.TestCase):
    def test_real_chess_API_legal_unique_and_reproducible(self):
        first=list(m.legal_fens(128,20261026));again=list(m.legal_fens(128,20261026))
        self.assertEqual(first,again);self.assertEqual(len(first),128)
        self.assertEqual(len({' '.join(f.split()[:4]) for f in first}),128)
        self.assertTrue(all(chess.Board(f).is_valid() for f in first))
        self.assertEqual(first[0],chess.STARTING_FEN)

    def test_seed_changes_walk(self):
        self.assertNotEqual(list(m.legal_fens(8,1)),list(m.legal_fens(8,2)))

    def test_finite_bounds_and_bool_traps(self):
        for count,seed in [(0,1),(1000001,1),(True,1),(1,0),(1,False)]:
            with self.assertRaises(ValueError):list(m.legal_fens(count,seed))

    def test_output_bounds(self):
        self.assertTrue(m.permitted(Path('/tmp/forge_sol_S09_native_20261026/corpus')))
        self.assertTrue(m.permitted(Path('/workspace/forge-pack24-20261026/S09_NATIVE_20261026/corpus')))
        for p in (Path('/tmp/forge_sol_S09_native_20261026'),Path('/tmp/outside'),Path('relative'),Path('/tmp/forge_sol_S09_native_20261026/../outside')):
            self.assertFalse(m.permitted(p))

if __name__=='__main__':unittest.main(verbosity=2)
