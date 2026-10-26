import hashlib, importlib.util, json, pathlib, tempfile, unittest

ROOT=pathlib.Path(__file__).resolve().parent
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/(name+'.py'))
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

class SelectionTests(unittest.TestCase):
    def test_preserves_order_and_dedupes_four_board_fields(self):
        m=load('forge_sol_S08_authorized_corpus_20261026')
        rows=[{'fen':'8/8/8/8/8/8/K7/7k w - - 0 1','source':'WAC'},
              {'fen':'8/8/8/8/8/8/K7/7k w - - 9 12','source':'BENCH'},
              {'fen':'8/8/8/8/8/8/K7/7k b - - 0 1','source':'OPENING'}]
        got,duplicates=m.select_unique(rows,2)
        self.assertEqual([x['source'] for x in got],['WAC','OPENING'])
        self.assertEqual(duplicates,1)
    def test_refuses_short_corpus_without_padding(self):
        m=load('forge_sol_S08_authorized_corpus_20261026')
        with self.assertRaisesRegex(ValueError,'distinct'):
            m.select_unique([],2000)
    def test_replay_verifies_recorded_final_board(self):
        m=load('forge_sol_S08_authorized_corpus_20261026')
        good='1\trnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1\te2e4'
        self.assertEqual(m.replay_opening(good)['id'],'Forge-1')
        with self.assertRaisesRegex(ValueError,'final board'):
            m.replay_opening(good.replace(' b KQkq',' w KQkq'))
    def test_replay_rejects_illegal_move(self):
        m=load('forge_sol_S08_authorized_corpus_20261026')
        with self.assertRaisesRegex(ValueError,'illegal'):
            m.replay_opening('1\tunused\te2e5')
    def test_no_overwrite(self):
        m=load('forge_sol_S08_authorized_corpus_20261026')
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(FileExistsError):m.new_directory(pathlib.Path(temp))

class CollectorExtensionTests(unittest.TestCase):
    def test_explicit_authority_accepts_profile_only_openings_without_bm(self):
        m=load('forge_sol_S08_collect_profiles_substitute_20261026')
        with tempfile.TemporaryDirectory() as temp:
            p=pathlib.Path(temp)/'openings.epd';p.write_text('8/8/8/8/8/8/K7/7k w - - id "Forge-1";\n')
            manifest={'authorization':{'kind':'handoff_S08_opening_substitution','sha256':'11e1be8ac83c6ce78d7e609059c4a96ec4b002ae923d44683077a0df038862b2'},'corpora':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'kind':'OPENING','source':'supplied original synthetic opening; profile only'}]}
            got=m.corpus_metadata([p],required=1,manifest=manifest)
            self.assertEqual(got['coverage_status'],'COMPLETE_AUTHORIZED_SUBSTITUTE')
            self.assertEqual(got['wac_sts_only_coverage_gap'],1)
            self.assertTrue(got['opening_or_training_boards_counted'])
            self.assertFalse(got['training_boards_counted'])
    def test_no_authority_still_rejects_openings(self):
        m=load('forge_sol_S08_collect_profiles_substitute_20261026')
        with tempfile.TemporaryDirectory() as temp:
            p=pathlib.Path(temp)/'openings.epd';p.write_text('8/8/8/8/8/8/K7/7k w - - id "Forge-1";\n')
            manifest={'corpora':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'kind':'OPENING','source':'supplied opening'}]}
            with self.assertRaises(ValueError):m.corpus_metadata([p],required=1,manifest=manifest)
    def test_training_still_rejected_even_with_authority(self):
        m=load('forge_sol_S08_collect_profiles_substitute_20261026')
        with tempfile.TemporaryDirectory() as temp:
            p=pathlib.Path(temp)/'training.epd';p.write_text('8/8/8/8/8/8/K7/7k w - - id "Train-1";\n')
            manifest={'authorization':{'kind':'handoff_S08_opening_substitution','sha256':'11e1be8ac83c6ce78d7e609059c4a96ec4b002ae923d44683077a0df038862b2'},'corpora':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'kind':'TRAINING','source':'training'}]}
            with self.assertRaises(ValueError):m.corpus_metadata([p],required=1,manifest=manifest)
    def test_wrong_authority_hash_rejects_substitution(self):
        m=load('forge_sol_S08_collect_profiles_substitute_20261026')
        with tempfile.TemporaryDirectory() as temp:
            p=pathlib.Path(temp)/'openings.epd';p.write_text('8/8/8/8/8/8/K7/7k w - - id "Forge-1";\n')
            manifest={'authorization':{'kind':'handoff_S08_opening_substitution','sha256':'0'*64},'corpora':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'kind':'OPENING','source':'supplied opening'}]}
            with self.assertRaises(ValueError):m.corpus_metadata([p],required=1,manifest=manifest)
    def test_substitute_input_hash_is_still_required(self):
        m=load('forge_sol_S08_collect_profiles_substitute_20261026')
        with tempfile.TemporaryDirectory() as temp:
            p=pathlib.Path(temp)/'openings.epd';p.write_text('8/8/8/8/8/8/K7/7k w - - id "Forge-1";\n')
            manifest={'authorization':{'kind':'handoff_S08_opening_substitution','sha256':'11e1be8ac83c6ce78d7e609059c4a96ec4b002ae923d44683077a0df038862b2'},'corpora':[{'path':str(p),'sha256':'0'*64,'kind':'OPENING','source':'supplied opening'}]}
            with self.assertRaises(ValueError):m.corpus_metadata([p],required=1,manifest=manifest)
    def test_undeclared_substitute_is_still_rejected(self):
        m=load('forge_sol_S08_collect_profiles_substitute_20261026')
        with tempfile.TemporaryDirectory() as temp:
            p=pathlib.Path(temp)/'openings.epd';p.write_text('8/8/8/8/8/8/K7/7k w - - id "Forge-1";\n')
            manifest={'authorization':{'kind':'handoff_S08_opening_substitution','sha256':'11e1be8ac83c6ce78d7e609059c4a96ec4b002ae923d44683077a0df038862b2'},'corpora':[]}
            with self.assertRaises(ValueError):m.corpus_metadata([p],required=1,manifest=manifest)

if __name__=='__main__':unittest.main()
