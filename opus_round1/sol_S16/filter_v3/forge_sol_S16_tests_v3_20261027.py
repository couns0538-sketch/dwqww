"""S16 behavioral tests use the unchanged legacy parser/writer dependency."""
import hashlib
import contextlib
import io
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
PATH = ROOT / 'forge_sol_datafilter_v3_20261027.py'  # v3: only the filenames differ from Sol's test file
if PATH.exists():
    spec = importlib.util.spec_from_file_location('s16_filter', PATH)
    tool = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = tool
    spec.loader.exec_module(tool)
else:
    tool = None


class NewFilterTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(tool, 'S16 v2 filter is not implemented')
        self.root = Path(tempfile.mkdtemp(prefix='forge_sol_S16_test_', dir=ROOT))
        self.data = self.root / 'data'; self.data.mkdir()
        self.scratch = self.root / 'scratch'; self.scratch.mkdir()

    def tearDown(self):
        if hasattr(self, 'root'):
            for p in self.root.rglob('*'):
                if p.is_file(): p.chmod(0o600)
            shutil.rmtree(self.root)

    def row(self, tag=0, score=10, meta=4, hce=42):
        board = bytearray(32); board[0] = 6; board[31] = 12 << 4
        square = 8 + tag % 48; board[square // 2] |= 1 << (4 * (square % 2))
        return tool.Record(bytes(board), score, meta, hce)

    def shard(self, stem, rows):
        p = self.data / (stem + '.pos')
        tool.write_records(p, p.with_suffix('.hce'), rows)
        return p

    def run_filter(self, train, holdout, name='out', **kw):
        return tool.filter_data(train, holdout, self.data, self.root / name,
                                work_dir=self.scratch, **kw)

    def text_shard(self, stem, lines, ids=None):
        records = []
        for line in lines:
            row, _ = tool.text_record(line)
            records.append(tool.Record(row.board, row.score, row.meta, 0))
        p = self.shard(stem, records)
        text = self.data / (stem + '.txt'); text.write_text(''.join(line + '\n' for line in lines))
        idpath = self.data / (stem + '.ids')
        if ids is not None: idpath.write_text(''.join(i + '\n' for i in ids))
        return p, text, idpath

    def test_conflicting_labels_count_score_result_and_hce_duplicates(self):
        a = self.shard('t001', [self.row(), self.row(score=11), self.row(meta=0), self.row(hce=43), self.row()])
        h = self.shard('h013', [])
        summary = self.run_filter([a], [h])
        self.assertEqual(summary['conflicting_label_duplicates'], 3)
        self.assertEqual(summary['totals'], {'input': 5, 'kept': 1, 'dropped': 4})
        ledger = [json.loads(s) for s in (self.root / 'out' / 'forge_sol_S16_removals_20261026.jsonl').read_text().splitlines()]
        self.assertEqual([r['row'] for r in ledger], [1, 2, 3, 4])
        self.assertEqual({r['reason'] for r in ledger}, {'duplicate_position'})
        self.assertEqual(sum(r['conflicting_label'] for r in ledger), 3)

    def test_identical_whole_pos_copy_is_excluded_and_reported(self):
        h = self.shard('h013', [self.row()])
        a = self.data / 'copied.pos'; shutil.copyfile(h, a)
        shutil.copyfile(h.with_suffix('.hce'), a.with_suffix('.hce'))
        summary = self.run_filter([a], [h])
        self.assertEqual(summary['duplicate_holdout_shards'], ['copied.pos'])
        self.assertEqual(summary['shards'][0]['dropped'], {'duplicate_holdout_shard': 1})
        self.assertEqual(summary['input_position_overlap'], 1)

    def test_caller_work_dir_holds_sqlite_and_is_cleaned_after_success(self):
        a = self.shard('t001', [self.row()]); h = self.shard('h013', [])
        paths = []
        real_connect = tool.sqlite3.connect
        def observe(path, *args, **kwargs):
            paths.append(Path(path)); return real_connect(path, *args, **kwargs)
        with patch.object(tool.sqlite3, 'connect', side_effect=observe):
            self.run_filter([a], [h])
        self.assertTrue(paths)
        self.assertTrue(all(self.scratch in p.parents for p in paths))
        self.assertEqual(list(self.scratch.iterdir()), [])

    def test_low_free_disk_refuses_before_creating_output_or_scratch(self):
        a = self.shard('t001', [self.row()]); h = self.shard('h013', [])
        with patch.object(tool.shutil, 'disk_usage', return_value=shutil._ntuple_diskusage(100, 100, 0)):
            with self.assertRaisesRegex(ValueError, 'disk'):
                self.run_filter([a], [h])
        self.assertFalse((self.root / 'out').exists())
        self.assertEqual(list(self.scratch.iterdir()), [])

    def test_outputs_are_deterministic_sealed_and_roundtrip_exact_fields(self):
        a = self.shard('t001', [self.row(1, -32767, 0, -32000), self.row(2, 32767, 5, 30000)])
        h = self.shard('h013', [])
        self.run_filter([a], [h], name='one'); self.run_filter([a], [h], name='two')
        def hashes(name):
            return {p.name: hashlib.md5(p.read_bytes()).hexdigest() for p in (self.root / name).iterdir() if p.is_file()}
        self.assertEqual(hashes('one'), hashes('two'))
        output, = (self.root / 'one').glob('*.pos')
        self.assertEqual(list(tool.read_records(output, output.with_suffix('.hce'))), list(tool.read_records(a, a.with_suffix('.hce'))))
        self.assertEqual(output.read_bytes(), a.read_bytes())
        for p in (self.root / 'one').iterdir(): self.assertEqual(p.stat().st_mode & 0o222, 0)

    def test_diagnostic_never_authorizes_training_or_authentic_game_zero(self):
        a = self.shard('t001', [self.row()]); h = self.shard('h013', [])
        summary = self.run_filter([a], [h])
        self.assertFalse(summary['production_eligible'])
        self.assertFalse(summary['game_overlap_verified'])
        self.assertFalse(summary['sealed_for_training'])
        self.assertIn('UNVERIFIED', summary['authentic_game_overlap'])

    def test_production_refuses_synchronized_interleaving_without_game_ids(self):
        # A1 B1 A2 B2 has identical counters/result; the old boundary predicate sees none.
        lines = [
            '7k/8/8/8/8/8/P7/K7 w - - 0 1 | 10 | 1',
            '5k2/8/8/8/8/8/1P6/2K5 w - - 0 1 | 10 | 1',
            '7k/8/8/8/8/8/P7/1K6 b - - 1 1 | 10 | 1',
            '5k2/8/8/8/8/8/1P6/3K4 b - - 1 1 | 10 | 1']
        a, ta, _ = self.text_shard('t001', lines)
        h, th, _ = self.text_shard('h013', [])
        kwargs = {'text_map': {'t001': ta, 'h013': th}, 'ordered_stems': ['t001', 'h013']}
        with self.assertRaisesRegex(ValueError, 'game.ID'):
            self.run_filter([a], [h], production=True, **kwargs)
        self.assertFalse((self.root / 'out').exists())
        summary = self.run_filter([a], [h], name='diagnostic', **kwargs)
        self.assertEqual(summary['game_overlap'], 0)
        self.assertFalse(summary['game_overlap_verified'])
        self.assertFalse(summary['production_eligible'])

    def test_authoritative_maps_remove_whole_holdout_game_across_shards(self):
        first = '7k/8/8/8/8/8/P7/K7 w - - 0 10 | 10 | 1'
        held = '7k/8/8/8/8/P7/8/K7 b - - 0 10 | 10 | 1'
        last = '6k1/8/8/8/8/P7/8/K7 w - - 1 11 | 10 | 1'
        fresh = '7k/8/8/8/8/8/1P6/K7 w - - 0 1 | 10 | 1'
        paths = {}; texts = {}; ids = {}
        for stem, line, gid in [('t001', first, 'game-A'), ('h013', held, 'game-A'), ('t002', last, 'game-A'), ('t003', fresh, 'game-B')]:
            paths[stem], texts[stem], ids[stem] = self.text_shard(stem, [line], [gid])
        summary = self.run_filter([paths[s] for s in paths if s != 'h013'], [paths['h013']],
                                  text_map=texts, ordered_stems=list(paths), game_id_map=ids,
                                  game_id_provenance='Fixture row-aligned authentic game identifiers', production=True)
        self.assertEqual(summary['totals'], {'input': 3, 'kept': 1, 'dropped': 2})
        self.assertEqual(summary['input_game_overlap'], 2)
        self.assertEqual(summary['authentic_game_overlap'], 0)
        self.assertTrue(summary['game_overlap_verified'])
        self.assertTrue(summary['production_eligible'])

    def test_reopened_game_id_fails_closed_even_with_identical_counters(self):
        line = '7k/8/8/8/8/8/P7/K7 w - - 0 1 | 10 | 1'
        a, ta, ia = self.text_shard('t001', [line] * 4, ['A', 'B', 'A', 'B'])
        h, th, ih = self.text_shard('h013', [], [])
        with self.assertRaisesRegex(ValueError, 'interleaved|reopened'):
            self.run_filter([a], [h], text_map={'t001': ta, 'h013': th},
                            ordered_stems=['t001', 'h013'], game_id_map={'t001': ia, 'h013': ih},
                            game_id_provenance='Fixture IDs', production=True)
        self.assertFalse(list((self.root / 'out').glob('*.pos')))

    def test_game_id_map_must_cover_every_row_and_have_provenance(self):
        line = '7k/8/8/8/8/8/P7/K7 w - - 0 1 | 10 | 1'
        a, ta, ia = self.text_shard('t001', [line], [])
        h, th, ih = self.text_shard('h013', [], [])
        kw = dict(text_map={'t001': ta, 'h013': th}, ordered_stems=['t001', 'h013'],
                  game_id_map={'t001': ia, 'h013': ih}, production=True)
        with self.assertRaisesRegex(ValueError, 'provenance'): self.run_filter([a], [h], **kw)
        with self.assertRaisesRegex(ValueError, 'row|count'):
            self.run_filter([a], [h], name='bad_rows', game_id_provenance='Fixture IDs', **kw)

    def test_production_cli_refuses_missing_authentic_maps(self):
        a = self.shard('t001', [self.row()]); h = self.shard('h013', [])
        command = [sys.executable, '-B', str(PATH), '--train', str(a), '--holdout-pos', str(h),
                   '--hce-dir', str(self.data), '--out', str(self.root / 'cli_out'), '--work-dir', str(self.scratch)]
        result = subprocess.run(command, text=True, capture_output=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('game-ID', result.stderr)
        self.assertFalse((self.root / 'cli_out').exists())

    def test_protected_output_symlink_is_rejected_before_any_write(self):
        a = self.shard('t001', [self.row()]); h = self.shard('h013', [])
        protected = self.root / 'LOCK'; protected.mkdir()
        alias = self.root / 'alias'; alias.symlink_to(protected, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'protected'):
            tool.filter_data([a], [h], self.data, alias / 'new', work_dir=self.scratch)
        self.assertEqual(list(protected.iterdir()), [])

    def test_high_boundary_rate_interleaving_fails_closed_in_diagnostic_mode(self):
        lines = []
        for i in range(50):
            lines.append('7k/8/8/8/8/8/P7/K7 w - - 0 {} | 10 | 1'.format(1 + i // 2))
            lines.append('5k2/8/8/8/8/8/1P6/2K5 w - - 0 {} | 10 | 1'.format(101 + i // 2))
        a, ta, _ = self.text_shard('t001', lines[:50])
        b, tb, _ = self.text_shard('t002', lines[50:])
        h, th, _ = self.text_shard('h013', [])
        with self.assertRaisesRegex(ValueError, 'interleaved'):
            self.run_filter([a, b], [h], text_map={'t001': ta, 't002': tb, 'h013': th},
                            ordered_stems=['t001', 't002', 'h013'])
        self.assertFalse(list((self.root / 'out').glob('*.pos')))

    def test_linux_one_command_config_includes_D_and_every_sealed_shard(self):
        paths = {}; texts = {}; ids = {}
        for i, stem in enumerate(['D_output', 'sealed_a', 'sealed_b', 'forge_selfplay_013', 'forge_selfplay_014']):
            line = '7k/8/8/8/8/8/{}P{}/K7 w - - 0 1 | 10 | 1'.format(str(i) if i else '', str(7-i) if i<7 else '')
            paths[stem], texts[stem], ids[stem] = self.text_shard(stem, [line], ['game-' + str(i)])
        sealed = self.root / 'sealed'; sealed.mkdir()
        for stem in ('sealed_a', 'sealed_b'):
            p = sealed / (stem + '.pos'); shutil.move(paths[stem], p); p.chmod(0o444); paths[stem] = p
        tm = self.data / 'text_map.json'; tm.write_text(json.dumps({k: v.name for k, v in texts.items()}))
        gm = self.data / 'id_map.json'; gm.write_text(json.dumps({k: v.name for k, v in ids.items()}))
        config = self.root / 'config.json'
        config.write_text(json.dumps({'d_output_pos': [str(paths['D_output'])], 'sealed_pos_dirs': [str(sealed)],
                                     'holdout_pos': [str(paths['forge_selfplay_013']), str(paths['forge_selfplay_014'])],
                                     'hce_dir': str(self.data), 'out': str(self.root / 'runner_out'),
                                     'work_dir': str(self.scratch), 'text_map': str(tm), 'game_id_map': str(gm),
                                     'ordered_stems': list(paths), 'game_id_provenance': 'Synthetic authoritative fixture IDs'}))
        command = ['sh', str(ROOT / 'forge_sol_S16_overlap_runner_v3_20261027.sh'), str(config)]
        result = subprocess.run(command, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary['totals'], {'input': 3, 'kept': 3, 'dropped': 0})
        self.assertEqual({r['stem'] for r in summary['shards']}, {'D_output', 'sealed_a', 'sealed_b'})
        self.assertTrue(summary['production_eligible'])

    def test_alias_rows_are_included_in_authentic_input_game_overlap(self):
        line = '7k/8/8/8/8/8/P7/K7 w - - 0 1 | 10 | 1'
        held, text, ids = self.text_shard('h013', [line], ['A'])
        alias = self.data / 'alias.pos'; alias.symlink_to(held.name)
        summary = self.run_filter([alias], [held], text_map={'h013': text}, ordered_stems=['h013'],
                                  game_id_map={'h013': ids}, game_id_provenance='Fixture IDs', production=True)
        self.assertEqual(summary['input_game_overlap'], 1)
        self.assertEqual(summary['totals'], {'input': 1, 'kept': 0, 'dropped': 1})

    def test_config_cannot_silently_override_explicit_diagnostic_prohibition(self):
        command = [sys.executable, '-B', str(PATH), '--config', 'missing_config.json', '--diagnostic-mode']
        result = subprocess.run(command, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('cannot combine', result.stderr)

    def test_scratch_budget_reserves_authoritative_id_segment_and_index_costs(self):
        ids = self.data / 'many.ids'
        ids.write_text(''.join(('g' * 124 + str(i).zfill(4)) + '\n' for i in range(2000)))
        result = tool._preflight_space(self.root / 'out', self.scratch, {'t001': 2000},
                                       [self.data / 't001.pos'], game_id_map={'t001': ids})
        # A separate SQLite schema probe measured >911 B/row before WAL here.
        self.assertGreater(result['scratch_required_bytes'], 1000 * 2000 + 8 * 1024 * 1024)
        self.assertEqual(result['sqlite_estimate_bytes_per_row'], 300)

    def test_low_free_RAM_blocks_production_before_reading_config(self):
        error = io.StringIO()
        with patch.object(tool, '_free_ram_bytes', return_value=1, create=True), contextlib.redirect_stderr(error):
            result = tool.main(['--config', 'missing_config.json'])
        self.assertEqual(result, 2)
        self.assertIn('free RAM', error.getvalue())

    def test_long_contiguous_game_ids_are_budgeted_per_retained_row(self):
        ids = self.data / 'long_game.ids'; ids.write_text(('g' * 128 + '\n') * 2000)
        result = tool._preflight_space(self.root / 'out', self.scratch, {'t001': 2000},
                                       [self.data / 't001.pos'], game_id_map={'t001': ids})
        # Independent SQLite probe measured 444.416 B/row before WAL for this case.
        self.assertGreater(result['scratch_required_bytes'] - result['wal_reserve_bytes'], 444.416 * 2000)

    def test_unicode_stem_ledger_budget_covers_actual_serialized_rows(self):
        paths = {}; texts = {}; ids = {}
        for stem, pawn, gid in [('棋' * 8, 'P7', 'A' * 128), ('abcdefghi', '1P6', 'B' * 128)]:
            line = '7k/8/8/8/8/8/' + pawn + '/K7 w - - 0 1 | 10 | 1'
            paths[stem], texts[stem], ids[stem] = self.text_shard(stem, [line, line], [gid, gid])
        held, texts['h013'], ids['h013'] = self.text_shard('h013', [], [])
        summary = self.run_filter(list(paths.values()), [held], text_map=texts, ordered_stems=list(texts),
                                  game_id_map=ids, game_id_provenance='Fixture IDs', production=True)
        ledger = self.root / 'out' / 'forge_sol_S16_removals_20261026.jsonl'
        self.assertGreater(len(ledger.read_text().splitlines()), 0)
        self.assertLessEqual(max(len(line.encode()) + 1 for line in ledger.read_text().splitlines()),
                             summary['disk_preflight']['removal_ledger_budget_bytes_per_row'])


if __name__ == '__main__': unittest.main(verbosity=2)
