"""Synthetic logic fixtures only: no native engine or strength measurements.
IDEA_SOURCE: user deterministic/opening-format requirements and Forge R8 contract.
"""
import dataclasses
import importlib.util
import json
from pathlib import Path
import random
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/data'))
import generate_openings as gen

E4 = 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1'
D4 = 'rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3 0 1'
E5 = 'rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2'

class FakeProbe:
    binary_sha256 = 'synthetic-unit-fixture-not-a-native-binary'
    def __init__(self, graph=None, scores=None, checks=(), terminal=()):
        self.graph = graph if graph is not None else {gen.STANDARD_FEN:[('e2e4',E4),('d2d4',D4)]}
        self.scores = scores or {}; self.checks=set(checks);self.terminal=set(terminal);self.calls=[]
    def query(self, fen, op='analyze', request_id=None):
        self.calls.append((fen,op))
        if op == 'analyze':
            return {'operation':op,'score':self.scores.get(fen,0),'depth':4,'nodes':5000,'bestmove':'a2a3'}
        terminal = fen in self.terminal
        moves = [] if terminal else self.graph.get(fen,[('a7a6',fen)])
        return {'operation':op,'in_check':fen in self.checks,'terminal':terminal,
                'moves':[{'uci':m,'fen':f,'capture':False,'promotion':False} for m,f in moves]}

class Tests(unittest.TestCase):
    def setUp(self):
        # Preserve every synthetic fixture; never remove previous runs.
        self.root=Path(tempfile.mkdtemp(prefix='astra_a1_openings_unit_'))
    def config(self, name='out', **kw):
        values=dict(out=self.root/name,count=1,seed=7,min_plies=1,max_plies=1,max_attempts=20)
        values.update(kw);return gen.Config(**values)
    def test_deterministic_books_and_metadata(self):
        for name in ('one','two'):
            report=gen.generate(self.config(name,count=2),FakeProbe(scores={E4:100,D4:-80}))
            self.assertEqual(report['accepted'],2)
        for filename in ('openings.moves','metadata.jsonl','settings.json','generation.json'):
            self.assertEqual((self.root/'one'/filename).read_bytes(),(self.root/'two'/filename).read_bytes())
        rows=(self.root/'one/openings.moves').read_text().splitlines()
        self.assertEqual(set(rows),{'e2e4','d2d4'})
        for record in map(json.loads,(self.root/'one/metadata.jsonl').read_text().splitlines()):
            self.assertEqual(record['score_white_cp'],-record['score_stm_cp'])
            self.assertLessEqual(abs(record['score_stm_cp']),150)
            self.assertTrue(all(abs(check['score_stm_cp']) <= 150 for check in record['checks']))
    def test_default_rejects_out_of_band_intermediate(self):
        graph={gen.STANDARD_FEN:[('e2e4',E4)],E4:[('e7e5',E5)]}
        probe=FakeProbe(graph,{E4:151,E5:0})
        config=self.config(min_plies=2,max_plies=2,max_attempts=1)
        report=gen.generate(config,probe)
        self.assertEqual(report['rejected_band'],1);self.assertEqual(report['accepted'],0)
        self.assertNotIn((E5,'analyze'),probe.calls)
        self.assertFalse((config.out/'SUCCESS.json').exists())
    def test_final_only_is_explicit_and_checks_only_final(self):
        graph={gen.STANDARD_FEN:[('e2e4',E4)],E4:[('e7e5',E5)]}
        probe=FakeProbe(graph,{E4:151,E5:0})
        config=self.config(min_plies=2,max_plies=2,max_attempts=1,final_only=True)
        report=gen.generate(config,probe)
        self.assertEqual(report['accepted'],1)
        self.assertEqual([f for f,op in probe.calls if op=='analyze'],[E5])
        self.assertEqual((config.out/'openings.moves').read_text(),'e2e4 e7e5\n')
    def test_terminal_child_is_rejected_before_analysis(self):
        probe=FakeProbe({gen.STANDARD_FEN:[('e2e4',E4)]},terminal=[E4])
        report=gen.generate(self.config(max_attempts=1),probe)
        self.assertEqual(report['rejected_terminal'],1)
        self.assertNotIn((E4,'analyze'),probe.calls)
    def test_in_check_final_is_rejected(self):
        probe=FakeProbe({gen.STANDARD_FEN:[('e2e4',E4)]},checks=[E4])
        self.assertEqual(gen.generate(self.config(max_attempts=1),probe)['rejected_check'],1)
    def test_duplicate_and_attempt_limit_do_not_seal(self):
        config=self.config(count=2,max_attempts=2)
        report=gen.generate(config,FakeProbe({gen.STANDARD_FEN:[('e2e4',E4)]}))
        self.assertEqual(report['status'],'INCOMPLETE_ATTEMPT_LIMIT')
        self.assertEqual(report['accepted'],1);self.assertEqual(report['rejected_duplicate'],1)
        with self.assertRaises(ValueError):gen.seal(config,report)
        self.assertFalse((config.out/'SUCCESS.json').exists())
    def test_existing_output_is_untouched(self):
        config=self.config();config.out.mkdir();(config.out/'keep.txt').write_bytes(b'original')
        with self.assertRaises(FileExistsError):gen.generate(config,FakeProbe())
        self.assertEqual(list(config.out.iterdir()),[config.out/'keep.txt'])
        self.assertEqual((config.out/'keep.txt').read_bytes(),b'original')
    def test_zero_ply_r8_and_960_r8_rejected(self):
        for config in [self.config(min_plies=0),self.config(chess960_style=True)]:
            with self.assertRaises(ValueError):gen.generate(config,FakeProbe())
            self.assertFalse(config.out.exists())
    def test_960_arrangement_and_no_castling(self):
        rows=set()
        for seed in range(1000):
            fen=gen.chess960_style_fen(random.Random(seed));fields=fen.split();row=fields[0].split('/')[-1]
            bishops=[i for i,x in enumerate(row) if x=='B'];rooks=[i for i,x in enumerate(row) if x=='R']
            self.assertEqual(sorted(row),sorted('RNBQKBNR'))
            self.assertNotEqual(bishops[0]%2,bishops[1]%2)
            self.assertLess(rooks[0],row.index('K'));self.assertLess(row.index('K'),rooks[1])
            self.assertEqual(fields[2],'-');rows.add(row)
        self.assertGreater(len(rows),500)
    def test_960_fen_export_is_not_r8(self):
        config=self.config(format='fen',chess960_style=True,min_plies=0,max_plies=0)
        report=gen.generate(config,FakeProbe())
        self.assertEqual(report['accepted'],1);self.assertFalse(report['r8_compatible'])
        self.assertEqual((config.out/'openings.fen').read_text().split()[2],'-')
        self.assertFalse((config.out/'openings.moves').exists())
    def test_minimum_score_is_explicit(self):
        report=gen.generate(self.config(min_abs_cp=20,max_attempts=1),FakeProbe())
        self.assertEqual(report['rejected_minimum'],1);self.assertEqual(report['accepted'],0)
    def test_incorrect_probe_operation_fails_closed(self):
        probe=FakeProbe();original=probe.query
        def broken(fen,op='analyze',request_id=None):
            value=original(fen,op,request_id);value['operation']='other';return value
        probe.query=broken
        config=self.config()
        with self.assertRaises(ValueError):gen.generate(config,probe)
        self.assertFalse((config.out/'SUCCESS.json').exists())
    def test_success_only_after_probe_clean_shutdown(self):
        probe=FakeProbe()
        class BadClose:
            def __init__(self,*a,**kw):pass
            def __enter__(self):return probe
            def __exit__(self,*a):raise RuntimeError('synthetic shutdown error')
        config=self.config()
        with mock.patch('forge_probe.ProbeClient',BadClose):
            result=gen.main(['--probe','unused','--out',str(config.out),'--count','1','--min-plies','1','--max-plies','1'])
        self.assertEqual(result,2);self.assertTrue((config.out/'FAILED.json').exists())
        self.assertFalse((config.out/'SUCCESS.json').exists())
    def test_seal_hashes_and_refuses_reseal(self):
        config=self.config();report=gen.generate(config,FakeProbe());gen.seal(config,report)
        manifest=json.loads((config.out/'MANIFEST.sha256.json').read_text())
        for name,value in manifest.items():self.assertEqual(gen.digest(config.out/name),value)
        before=(config.out/'SUCCESS.json').read_bytes()
        with self.assertRaises(FileExistsError):gen.seal(config,report)
        self.assertEqual((config.out/'SUCCESS.json').read_bytes(),before)

if __name__ == '__main__': unittest.main()
