"""Full-state converter/relabel regression fixtures; no engine or training runs."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE/'data'), str(HERE/'datafilter'), 'D:/a10/pydeps']
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
from forge_pos import PosWriter, fen_record, PosReader
import relabel_positions

FENS = [
    'r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 17 81',
    '4k3/8/8/8/4P3/8/8/4K3 b - e3 0 1',  # legal, non-capturable EP
    '4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 42',
]
ROOT = None
CONVERTER = False
DEPS = Path('D:/a10/pydeps')

class FixtureProbePool:
    """Protocol fixture only: never invokes an engine or claims native analysis."""
    calls = []
    total_child_cpu_seconds = 0
    def __init__(self, probe, nodes, workers, log, hash_mb):
        self.nodes, self.hash_mb = nodes, hash_mb
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def map(self, rows, op):
        import chess
        self.calls.extend(rows)
        return [dict(id=index,fen=fen,ok=True,terminal=False,depth=2,score=60,hce=55,
                     nodes=self.nodes,cpu_ns=0,analyzed=True,nodes_limit=self.nodes,
                     hash_mb=self.hash_mb,threads=1,bestmove=next(iter(chess.Board(fen).legal_moves)).uci())
                for index,fen in rows]

class StateTests(unittest.TestCase):
    def setUp(self):
        self.out = ROOT/self._testMethodName
        self.out.mkdir()

    def source(self):
        rows = [dict(fen=fen, source='frozen-original', source_row=i+1,
                     game_id='authentic-alpha' if i == 0 else None)
                for i, fen in enumerate(FENS)]
        with PosWriter(self.out/'input', 'source', False) as writer:
            for fen in FENS:
                writer.append(fen_record(fen, 50, '0.5'), fen)
        return writer.pos_path, writer.fen_path, rows

    def test_opt_in_hash_bound_relabel_contract(self):
        # RED on frozen d8982bc0: Config rejects state_manifest.
        config = relabel_positions.Config(Path('x'), Path('y'), Path('z'), Path('p'),
                    state_manifest=Path('state.json'), state_sha256='a'*64)
        self.assertEqual(config.state_sha256, 'a'*64)

    def test_full_state_manifest_contract(self):
        # RED on frozen source: no hash/row-bound state manifest API exists.
        import full_state
        pos, fen, rows = self.source()
        manifest = self.out/'state.json'
        full_state.write_state(pos, rows, manifest, binary_format='fpos1', sources=[fen])
        loaded = full_state.verify_state(manifest, full_state.sha256(manifest), pos)
        self.assertEqual([r['fen'] for r in loaded], FENS)
        self.assertEqual([r.get('game_id') for r in loaded], ['authentic-alpha', None, None])

    def binding(self):
        import full_state
        pos, fen, rows = self.source()
        manifest = self.out/'state.json'
        full_state.write_state(pos, rows, manifest, binary_format='fpos1', sources=[fen])
        return pos, fen, rows, manifest

    def test_missing_ids_are_unverified(self):
        pos, fen, rows, manifest = self.binding()
        data = json.loads(manifest.read_text())
        self.assertEqual(data['missing_game_ids'], 2)
        self.assertEqual(data['game_id_status'], 'UNVERIFIED')

    def test_manifest_requires_external_hash(self):
        import full_state
        pos, fen, rows, manifest = self.binding()
        with self.assertRaisesRegex(ValueError, 'pinned'):
            full_state.verify_state(manifest, None, pos)
        with self.assertRaisesRegex(ValueError, 'manifest SHA256'):
            full_state.verify_state(manifest, '0'*64, pos)

    def test_corrupted_binary_detected(self):
        import full_state
        pos, fen, rows, manifest = self.binding()
        corrupted = self.out/'corrupt.pos'
        data = bytearray(pos.read_bytes()); data[17] ^= 1
        corrupted.write_bytes(data)
        with self.assertRaisesRegex(ValueError, 'binary SHA256'):
            full_state.verify_state(manifest, full_state.sha256(manifest), corrupted)

    def test_metadata_reorder_detected(self):
        import full_state
        pos, fen, rows, manifest = self.binding()
        original = json.loads(manifest.read_text())
        lines = (manifest.parent/original['metadata']['path']).read_bytes().splitlines(keepends=True)
        changed = self.out/'reordered.rows.jsonl'
        changed.write_bytes(b''.join(reversed(lines)))
        original['metadata'] = dict(path=changed.name, bytes=changed.stat().st_size, sha256=full_state.sha256(changed))
        changed_manifest = self.out/'reordered.json'
        changed_manifest.write_text(json.dumps(original))
        with self.assertRaisesRegex(ValueError, 'index/record'):
            full_state.verify_state(changed_manifest, full_state.sha256(changed_manifest), pos)

    def test_metadata_truncation_detected(self):
        import full_state
        pos, fen, rows = self.source()
        with self.assertRaisesRegex(ValueError, 'row count'):
            full_state.write_state(pos, rows[:-1], self.out/'truncated.json', binary_format='fpos1')
        self.assertFalse((self.out/'truncated.json').exists())

    def test_overwrite_refused(self):
        import full_state
        pos, fen, rows, manifest = self.binding()
        old_hash = full_state.sha256(manifest)
        with self.assertRaises(FileExistsError):
            full_state.write_state(pos, rows, manifest, binary_format='fpos1')
        self.assertEqual(full_state.sha256(manifest), old_hash)

    def test_reconstructed_origin_refused(self):
        import full_state
        pos, fen, rows = self.source()
        with self.assertRaisesRegex(ValueError, 'original full FEN'):
            full_state.write_state(pos, rows, self.out/'bad.json', binary_format='fpos1', state_origin='reconstructed')

    def test_consumed_metadata_is_hashed(self):
        import full_state
        pos, fen, rows, manifest = self.binding()
        receipt = json.loads(manifest.read_text())
        metadata = manifest.parent/receipt['metadata']['path']
        tampered = metadata.read_text().replace(' KQkq ', ' - ')
        original_open = Path.open
        def read_changed_snapshot(path, *args, **kwargs):
            # Hash/identity reads see the original, while the parser sees a
            # changed FPOS sidecar (rights are not represented in FPOS bytes).
            if path == metadata and sys._getframe(1).f_code.co_name == 'verify_state':
                mode = args[0] if args else kwargs.get('mode', 'r')
                return io.BytesIO(tampered.encode()) if 'b' in mode else io.StringIO(tampered)
            return original_open(path, *args, **kwargs)
        with patch.object(Path, 'open', read_changed_snapshot):
            with self.assertRaisesRegex(ValueError, 'consumed metadata'):
                full_state.verify_state(manifest, full_state.sha256(manifest), pos)

    def test_manifest_parses_the_hashed_snapshot(self):
        import full_state
        pos, fen, rows, manifest = self.binding()
        receipt = json.loads(manifest.read_text())
        metadata = manifest.parent/receipt['metadata']['path']
        alternate = self.out/'alternate.rows.jsonl'
        alternate.write_text(metadata.read_text().replace(' KQkq ', ' - '))
        altered_receipt = dict(receipt, metadata=dict(path=alternate.name,bytes=alternate.stat().st_size,sha256=full_state.sha256(alternate)))
        original_read = Path.read_text
        def changed_manifest(path, *args, **kwargs):
            if path == manifest:
                return json.dumps(altered_receipt)
            return original_read(path, *args, **kwargs)
        with patch.object(Path, 'read_text', changed_manifest):
            loaded = full_state.verify_state(manifest,full_state.sha256(manifest),pos)
        self.assertEqual(loaded[0]['fen'],FENS[0])

    def test_windows_ads_metadata_name_refused(self):
        import full_state
        pos, fen, rows, manifest = self.binding()
        receipt = json.loads(manifest.read_text())
        receipt['metadata']['path'] = 'rows.jsonl:alternate_stream'
        changed = self.out/'ads.json'
        changed.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(ValueError, 'local filename'):
            full_state.verify_state(changed,full_state.sha256(changed),pos)

    def test_explicit_lichess_game_id_retained(self):
        from records import lichess_record, validate_record
        value = dict(fen=FENS[1],evals=[dict(pvs=[dict(cp=100)])],game_id='stored-authentic-game-id')
        result = lichess_record(value,'source.jsonl',1)
        self.assertEqual(result['game_id'],value['game_id'])
        self.assertEqual(validate_record(result)['game_id'],value['game_id'])
        del value['game_id']
        self.assertNotIn('game_id',lichess_record(value,'source.jsonl',1))
        value['game_id'] = None
        self.assertIsNone(lichess_record(value,'source.jsonl',1)['game_id'])
        value['game_id'] = 42
        with self.assertRaisesRegex(ValueError, 'game_id'):
            lichess_record(value,'source.jsonl',1)

    def test_binary_mutation_during_verify_refused(self):
        import full_state
        pos, fen, rows = self.source()
        changed = self.out/'negative-mutable-copy.pos'
        changed.write_bytes(pos.read_bytes())
        manifest = self.out/'mutable.state.json'
        full_state.write_state(changed,rows,manifest,binary_format='fpos1',sources=[fen])
        original_rows = full_state._binary_rows
        def change_after_consumption(path, binary_format):
            yield from original_rows(path,binary_format)
            with changed.open('r+b') as stream:
                stream.write(b'X');stream.flush();os.fsync(stream.fileno())
        with patch.object(full_state,'_binary_rows',change_after_consumption):
            with self.assertRaisesRegex(ValueError, 'identity changed'):
                full_state.verify_state(manifest,full_state.sha256(manifest),changed)

    def config(self, pos, fen, manifest, **extra):
        import full_state
        return relabel_positions.Config(pos, fen, self.out/'relabel', Path(__file__), nodes=16,
                count=3, state_manifest=manifest, state_sha256=full_state.sha256(manifest), **extra)

    def test_actual_relabel_roundtrip_and_ids(self):
        import full_state
        pos, fen, rows, manifest = self.binding()
        FixtureProbePool.calls = []
        report = relabel_positions.run(self.config(pos, fen, manifest), pool_factory=FixtureProbePool)
        output = self.out/'relabel'
        self.assertEqual((output/'relabeled.fen').read_text().splitlines(), FENS)
        self.assertEqual([fen for _,fen in FixtureProbePool.calls], FENS)
        state = Path(report['full_state']['manifest'])
        output_rows = full_state.verify_state(state, report['full_state']['sha256'], output/'relabeled.pos')
        self.assertEqual([row['fen'] for row in output_rows], FENS)
        self.assertEqual([row.get('game_id') for row in output_rows], ['authentic-alpha',None,None])
        self.assertEqual([row['score_stm'] for row in output_rows], [60]*3)
        self.assertEqual(report['full_state']['missing_game_ids'], 2)
        self.assertTrue((output/'summary.json').exists())
        (self.out/'SCOPE.json').write_text(json.dumps(dict(real_adapter='relabel_positions.run',
            probe='FixtureProbePool protocol fixture; NO native engine', claim='UNPROVEN'))+'\n')

    def test_stripped_castling_unselected_row_refused(self):
        pos, fen, rows, manifest = self.binding()
        stripped = self.out/'stripped.fen'
        stripped.write_text('\n'.join([FENS[0].replace(' KQkq ', ' - '),*FENS[1:]])+'\n')
        config = self.config(pos, stripped, manifest)
        config.start, config.count = 1, 1
        FixtureProbePool.calls = []
        with self.assertRaisesRegex(ValueError, 'six-field FEN mismatch at0'):
            relabel_positions.run(config, pool_factory=FixtureProbePool)
        self.assertEqual(FixtureProbePool.calls, [])

    def test_stripped_noncapturable_ep_refused(self):
        pos, fen, rows, manifest = self.binding()
        stripped = self.out/'stripped.fen'
        stripped.write_text('\n'.join([FENS[0],FENS[1].replace(' e3 ', ' - '),FENS[2]])+'\n')
        with self.assertRaisesRegex(ValueError, 'six-field FEN mismatch at1'):
            relabel_positions.run(self.config(pos, stripped, manifest), pool_factory=FixtureProbePool)

    def test_default_relabel_binary_bytes_unchanged(self):
        import importlib.util
        baseline = Path('D:/a10/job3/source/tools/data/relabel_positions.py')
        spec = importlib.util.spec_from_file_location('baseline_relabel', baseline)
        old = importlib.util.module_from_spec(spec); sys.modules[spec.name] = old; spec.loader.exec_module(old)
        pos, fen, rows = self.source()
        arguments = dict(pos=pos, sidecar=fen, probe=Path(__file__), nodes=16, count=3, sidecar_origin='original_full_fen')
        old.run(old.Config(out=self.out/'old', **arguments), pool_factory=FixtureProbePool)
        relabel_positions.run(relabel_positions.Config(out=self.out/'new', **arguments), pool_factory=FixtureProbePool)
        for suffix in ('.pos','.hce','.fen'):
            self.assertEqual((self.out/'old'/('relabeled'+suffix)).read_bytes(),(self.out/'new'/('relabeled'+suffix)).read_bytes())

    def test_converter_default_and_keep_fen_bytes_and_ids(self):
        if not CONVERTER:
            self.skipTest('converter dependencies/slot not selected')
        import chess
        import full_state
        from records import record, dumps
        fens = FENS + ['7k/8/8/8/4Q3/8/8/K7 w - - 17 81', '7k/8/8/3q4/8/8/8/K7 w - - 17 81']
        values = [0,100,0,900,-900]
        source = self.out/'original.jsonl'
        rows = [record(fen, white if chess.Board(fen).turn else -white, 'cp', 0, 'authentic-source',i+1,'selfplay') for i,(fen,white) in enumerate(zip(fens,values))]
        rows[0]['game_id'] = 'stored-real-game-id'
        source.write_text(''.join(dumps(row)+'\n' for row in rows))
        env = dict(os.environ, PYTHONPATH=str(DEPS), OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
        variants = [('baseline', Path('D:/a10/job3/source/astra_r8/datafilter/convert_forge.py'), []),
                    ('default', HERE/'datafilter/convert_forge.py', []),
                    ('keep', HERE/'datafilter/convert_forge.py', ['--keep-fen'])]
        for name, script, extra in variants:
            command = [sys.executable,'-B',str(script),str(self.out/name),'--normalized',str(source),'--seed','4803011981',*extra]
            completed = subprocess.run(command,env=env,capture_output=True,text=True)
            (self.out/(name+'.stdout.txt')).write_text(completed.stdout)
            (self.out/(name+'.stderr.txt')).write_text(completed.stderr)
            self.assertEqual(completed.returncode,0,completed.stderr)
        combined = []
        for split in ('train','val'):
            original = (self.out/'baseline'/(split+'.bin')).read_bytes()
            self.assertEqual(original,(self.out/'default'/(split+'.bin')).read_bytes())
            self.assertEqual(original,(self.out/'keep'/(split+'.bin')).read_bytes())
            state = self.out/'keep'/(split+'.state.json')
            combined.extend(full_state.verify_state(state,full_state.sha256(state),self.out/'keep'/(split+'.bin')))
        self.assertEqual({row['fen'] for row in combined},set(fens))
        self.assertEqual([row.get('game_id') for row in combined].count('stored-real-game-id'),1)

def main():
    global ROOT, CONVERTER, DEPS
    parser = argparse.ArgumentParser()
    parser.add_argument('--threads', type=int, choices=[1], required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--converter', action='store_true')
    parser.add_argument('--deps', type=Path, default=DEPS)
    parser.add_argument('--only', nargs='+')
    args = parser.parse_args()
    ROOT = args.out
    ROOT.mkdir(parents=True, exist_ok=False)
    CONVERTER = args.converter
    DEPS = args.deps
    sys.path.insert(0,str(DEPS))
    os.environ.update(PYTHONPATH=str(DEPS),PYTHONNOUSERSITE='1',CUDA_VISIBLE_DEVICES='',HIP_VISIBLE_DEVICES='',
                      ROCR_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    suite = unittest.TestSuite(StateTests(name) for name in args.only) if args.only else unittest.defaultTestLoader.loadTestsFromTestCase(StateTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    (ROOT/'result.json').write_text(json.dumps(dict(tests=result.testsRun, failures=len(result.failures),
        errors=len(result.errors), skipped=len(result.skipped),
        status=('PASS_WITH_SKIPS' if result.skipped else 'PASS') if result.wasSuccessful() else 'FAIL'), indent=2)+'\n')
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    raise SystemExit(main())
