"""Source/export tests; no framework import, training or native engine runs."""
import ast
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
import uuid
import warnings
import numpy as np

ROOT = Path(__file__).resolve().parent
TOOL = ROOT / 'forge_sol_S09_buckets_20261026.py'
TRAINER = ROOT / 'forge_sol_S09_train_resid_v3b_20261026.py'
BASE = Path(json.loads((ROOT / 'forge_sol_S09_source_before_20261026.json').read_text())['legacy_trainer']['path'])
if TOOL.exists():
    spec = importlib.util.spec_from_file_location('s09_buckets', TOOL)
    tool = importlib.util.module_from_spec(spec); spec.loader.exec_module(tool)
else: tool = None


def export_function(path):
    nodes = [n for n in ast.parse(path.read_text()).body if isinstance(n, ast.FunctionDef) and n.name in {'atomic_write', 'export_forge'}]
    namespace = {'np': np, 'os': os, 'uuid': uuid, 'SCALE': 4096.0}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace['export_forge']


class Parameter:
    """Real NumPy data implementing the export boundary's array access API."""
    def __init__(self, value): self.value = np.asarray(value, dtype=np.float32)
    def detach(self): return self
    def cpu(self): return self
    def t(self): return Parameter(self.value.T)
    def contiguous(self): return Parameter(np.ascontiguousarray(self.value))
    def numpy(self): return self.value


class Model:
    def __init__(self, buckets=1):
        self.hidden = 2; self.buckets = buckets
        self.ft = type('Layer', (), {})(); self.out = type('Layer', (), {})()
        self.ft.weight = Parameter((np.arange(1536).reshape(2, 768) % 17 - 8) / 4096)
        self.ft.bias = Parameter([3/4096, -5/4096])
        self.out.weight = Parameter((np.arange(4 * buckets).reshape(buckets, 4) - 2) / 4096)
        self.out.bias = Parameter(np.arange(buckets) / 4096)


class BucketTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(tool, 'S09 bucket helper is not implemented')
        self.assertTrue(TRAINER.exists(), 'S09 trainer support is not implemented')
        self.root = Path(tempfile.mkdtemp(prefix='forge_sol_S09_test_', dir=ROOT))
    def tearDown(self):
        if hasattr(self, 'root'): shutil.rmtree(self.root)
    def source(self):
        stem = self.root / 'source'; export_function(BASE)(Model(), stem, 2.25, True)
        return stem.with_suffix('.inc')

    def test_single_bucket_export_is_byte_identical_to_v3b_inc_and_bin(self):
        old = self.root / 'old'; new = self.root / 'new'; model = Model()
        export_function(BASE)(model, old, 2.25, True)
        export_function(TRAINER)(model, new, 2.25, True)
        for suffix in ('.inc', '.bin'): self.assertEqual(old.with_suffix(suffix).read_bytes(), new.with_suffix(suffix).read_bytes())

    def test_eight_bucket_export_is_head_major_and_keeps_every_bias(self):
        stem = self.root / 'b8'; model = Model(8)
        export_function(TRAINER)(model, stem, 2.25, True)
        parsed = tool.inspect_inc(stem.with_suffix('.inc'), hidden=2)
        self.assertEqual(parsed['heads'], 8)
        self.assertEqual(parsed['w2'], list(range(-2, 30)))
        self.assertEqual(parsed['b2'], list(range(8)))
        self.assertEqual(len(stem.with_suffix('.bin').read_bytes()), 4 * (1536 + 2 + 32 + 8))

    def test_replication_and_numeric_roundtrip_leave_input_and_feature_text_unchanged(self):
        source = self.source(); before = source.read_bytes(); out = self.root / 'b8.inc'
        tool.replicate_1_to_8(source, out, hidden=2)
        a = tool.inspect_inc(source, hidden=2); b = tool.inspect_inc(out, hidden=2)
        self.assertEqual(source.read_bytes(), before)
        self.assertEqual(b['w1'], a['w1']); self.assertEqual(b['b1'], a['b1'])
        self.assertEqual(b['w2'], a['w2'] * 8); self.assertEqual(b['b2'], a['b2'] * 8)
        _, arrays_a, _, _ = tool.step1.parse(source)
        _, arrays_b, _, _ = tool.step1.parse(out)
        for name in ('NnueW1', 'NnueB1'):
            x, y, _ = arrays_a[name]; u, v, _ = arrays_b[name]
            self.assertEqual(source.read_text()[x:y], out.read_text()[u:v])

    def test_replication_is_deterministic_and_never_overwrites(self):
        source = self.source(); a = self.root / 'a.inc'; b = self.root / 'b.inc'
        tool.replicate_1_to_8(source, a, hidden=2); tool.replicate_1_to_8(source, b, hidden=2)
        self.assertEqual(a.read_bytes(), b.read_bytes())
        before = a.read_bytes()
        with self.assertRaises((ValueError, FileExistsError)): tool.replicate_1_to_8(source, a, hidden=2)
        with self.assertRaises((ValueError, FileExistsError)): tool.replicate_1_to_8(source, source, hidden=2)
        self.assertEqual(a.read_bytes(), before)

    def test_any_single_head_spelling_and_singleton_bias_array_are_supported(self):
        for name in ('HEADS', 'BUCKETS'):
            source = self.source(); text = source.read_text()
            text = '#define FORGE_NNUE_OUTPUT_' + name + ' 1\n' + text
            text = text.replace('static const std::int16_t NnueB2 = 0;', 'static const std::int16_t NnueB2[1] = { 0, };')
            source.write_text(text)
            out = self.root / (name + '.inc'); tool.replicate_1_to_8(source, out, hidden=2)
            self.assertEqual(tool.inspect_inc(out, hidden=2)['heads'], 8)
            source.unlink(); source.with_suffix('.bin').unlink()

    def test_wrong_shape_range_and_already_bucketed_input_fail_before_output(self):
        source = self.source(); text = source.read_text()
        for index, broken in enumerate((text.replace('NnueW2[4]', 'NnueW2[5]'), text.replace('= 0;', '= 40000;'))):
            path = self.root / ('bad' + str(index) + '.inc'); path.write_text(broken)
            out = self.root / ('bad' + str(index) + '_out.inc')
            with self.assertRaises(ValueError): tool.replicate_1_to_8(path, out, hidden=2)
            self.assertFalse(out.exists())
        out = self.root / 'b8.inc'; tool.replicate_1_to_8(source, out, hidden=2)
        with self.assertRaises(ValueError): tool.replicate_1_to_8(out, self.root / 'again.inc', hidden=2)

    def test_piece_bands_include_kings_and_clamp_boundaries(self):
        for count, expected in [(-5,0),(0,0),(1,0),(2,0),(4,0),(5,1),(8,1),(9,2),(12,2),(13,3),(16,3),(17,4),(20,4),(21,5),(24,5),(25,6),(28,6),(29,7),(32,7),(64,7)]:
            self.assertEqual(tool.output_head(count), expected)

    def test_export_nonfinite_bad_bucket_and_shape_rejections(self):
        function = export_function(TRAINER)
        for model in (Model(3), Model(8), Model(1)):
            if model.buckets == 8: model.out.bias = Parameter([0] * 7)
            if model.buckets == 1: model.ft.bias = Parameter([float('nan'), 0])
            with self.assertRaises((ValueError, RuntimeError)): function(model, self.root / 'bad', 2.25, True)
            self.assertFalse((self.root / 'bad.inc').exists())

    def test_pinned_f006_recipe_uses_actual_run_values_and_single_bucket_default(self):
        recipe = tool.F006_RECIPE
        self.assertEqual({k: recipe[k] for k in ('shape','buckets','batch_size','lr','warmup_steps','blend_end','seed','epochs','residual')},
                         {'shape':256,'buckets':1,'batch_size':8192,'lr':0.000707,'warmup_steps':300,'blend_end':0.6,'seed':25,'epochs':48,'residual':True})

    def test_actual_trainer_cli_defaults_include_observed_f006_full_validation(self):
        main = next(n for n in ast.parse(TRAINER.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='main')
        body=[]
        for node in main.body:
            if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='a' for t in node.targets): break
            body.append(node)
        body.append(ast.Return(value=ast.Name(id='ap',ctx=ast.Load())))
        function=ast.FunctionDef(name='get_parser',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=body,decorator_list=[])
        namespace={'argparse':argparse,'K_DEFAULT':2.25,'__doc__':'actual source parser'}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[])),str(TRAINER),'exec'),namespace)
        args=namespace['get_parser']().parse_args(['--holdout','fixture.pos','--hce-dir','fixture'])
        self.assertTrue(args.final_full_val)
        for key,value in tool.F006_RECIPE.items(): self.assertEqual(getattr(args,key),value)

    def test_reused_parser_closes_file_descriptors_without_resource_warnings(self):
        source = self.source()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always', ResourceWarning)
            tool.inspect_inc(source, hidden=2)
        self.assertEqual([str(w.message) for w in caught if issubclass(w.category, ResourceWarning)], [])

    def test_numeric_head_control_hits_every_band_with_known_centipawns(self):
        codes = np.zeros((8, 64), dtype=np.uint8)
        for row, pieces in enumerate((2, 5, 9, 13, 17, 21, 25, 29)): codes[row, :pieces] = 1
        net = {'hidden':2,'heads':8,'w1':[0]*1536,'b1':[0,0],'w2':[0]*32,'b2':[64*i for i in range(1,9)]}
        result = tool.evaluate_numeric(codes, np.zeros(8, dtype=np.uint8), net)
        self.assertEqual(result['heads'].tolist(), list(range(8)))
        self.assertEqual(result['cp'].tolist(), [2,5,8,11,13,16,19,22])
        self.assertEqual(result['logits'].dtype, np.dtype('float32'))

    def test_numeric_feature_perspective_and_float_accumulation_match_known_answer(self):
        codes = np.zeros((2,64),dtype=np.uint8); codes[:,0]=6; codes[:,63]=12
        weights = [0]*768; weights[320]=4096; weights[327]=2048
        net = {'hidden':1,'heads':1,'w1':weights,'b1':[0],'w2':[4096,0],'b2':[0]}
        result = tool.evaluate_numeric(codes,np.array([0,1],dtype=np.uint8),net)
        self.assertEqual(result['cp'].tolist(),[177,44])

    def test_numeric_replicated_weights_match_at_float_bits_and_cp(self):
        source = self.source(); out = self.root/'b8.inc';tool.replicate_1_to_8(source,out,hidden=2)
        one,eight=tool.inspect_inc(source,2),tool.inspect_inc(out,2)
        rng=np.random.default_rng(9); codes=rng.integers(0,13,(80,64),dtype=np.uint8); stm=rng.integers(0,2,80,dtype=np.uint8)
        a=tool.evaluate_numeric(codes,stm,one);b=tool.evaluate_numeric(codes,stm,eight)
        self.assertEqual(a['logits'].tobytes(),b['logits'].tobytes())
        self.assertEqual(a['cp'].tobytes(),b['cp'].tobytes())

    def test_commented_head_directives_cannot_bypass_shape_validation(self):
        source=self.source();text=source.read_text()
        for prefix in ('#define FORGE_NNUE_OUTPUT_HEADS 8 // comment\n',
                       '#define FORGE_NNUE_OUTPUT_BUCKETS 8 /* comment */\n',
                       '#define FORGE_NNUE_OUTPUT_HEADS (1)\n'):
            source.write_text(prefix+text)
            with self.assertRaises(ValueError): tool.inspect_inc(source,hidden=2)
        source.write_text('#define FORGE_NNUE_OUTPUT_HEADS 1 // comment\n'+text)
        out=self.root/'commented.inc';tool.replicate_1_to_8(source,out,hidden=2)
        self.assertEqual(tool.inspect_inc(out,hidden=2)['heads'],8)


if __name__ == '__main__': unittest.main(verbosity=2)
