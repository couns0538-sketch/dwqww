import importlib.util,pathlib,unittest

P=pathlib.Path(__file__).with_name('forge_sol_S08_ASAN_profile_extra_20261026.py')
spec=importlib.util.spec_from_file_location('asan_profile_extra',P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class BestmoveTests(unittest.TestCase):
    def test_legal_move(self):self.assertEqual(m.legal_bestmove(m.chess.STARTING_FEN,['bestmove e2e4']),'e2e4')
    def test_illegal_move_rejected(self):
        with self.assertRaises(ValueError):m.legal_bestmove(m.chess.STARTING_FEN,['bestmove e2e5'])
    def test_false_null_rejected(self):
        with self.assertRaises(ValueError):m.legal_bestmove(m.chess.STARTING_FEN,['bestmove 0000'])
    def test_duplicate_terminal_rejected(self):
        with self.assertRaises(ValueError):m.legal_bestmove(m.chess.STARTING_FEN,['bestmove e2e4','bestmove d2d4'])

if __name__=='__main__':unittest.main(verbosity=2)
