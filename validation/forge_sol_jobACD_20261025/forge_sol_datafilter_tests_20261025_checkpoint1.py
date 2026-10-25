#!/usr/bin/env python3
"""Independent behavioral checks for the original sealed data32 filter."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
TOOL = ROOT / 'forge_sol_datafilter_20261025.py'
spec = importlib.util.spec_from_file_location('forge_sol_datafilter_20261025', TOOL)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
Record = module.Record


def board_of(tag=0):
    a = bytearray(32)
    # White Ka1 / Black Kh8 plus a single changing white pawn square.
    a[0] = 6
    a[31] = 12 << 4
    square = 8 + tag % 48
    a[square // 2] |= 1 << (4 * (square % 2))
    return bytes(a)


def hashes(folder):
    return {str(p.relative_to(folder)): hashlib.md5(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob('*')) if p.is_file()}


class FilterTests(unittest.TestCase):
    def setUp(self):
        self.work = Path(tempfile.mkdtemp(prefix='forge_sol_filter_test_20261025_', dir=ROOT))
        self.data = self.work / 'inputs'; self.data.mkdir()

    def tearDown(self):
        # Only this test's new disposable directory; never existing source data.
        for p in self.work.rglob('*'):
            if p.is_file(): p.chmod(0o600)
        shutil.rmtree(self.work)

    def shard(self, stem, rows):
        p = self.data / (stem + '.pos')
        module.write_records(p, p.with_suffix('.hce'), rows)
        return p

    def run_filter(self, train, holdout, name='out', **kw):
        return module.filter_data(train, holdout, self.data, self.work / name, **kw)

    def output_rows(self, name='out'):
        rows = []
        for p in sorted((self.work / name).glob('*.pos')):
            rows.extend(module.read_records(p, p.with_suffix('.hce')))
        return rows

    def test_record_roundtrip_exact_fields_and_empty(self):
        original = [Record(board_of(0), -32767, 0, -32000),
                    Record(board_of(1), 32767, 5, 30000),
                    Record(board_of(2), -17, 3, 42)]
        p = self.shard('t000', original)
        self.assertEqual(list(module.read_records(p, p.with_suffix('.hce'))), original)
        self.assertEqual(p.stat().st_size, 16 + 35 * len(original))
        self.assertEqual(p.with_suffix('.hce').stat().st_size, 16 + 2 * len(original))
        self.assertEqual(p.read_bytes()[:16], struct.pack('<4sIQ', b'FPOS', 1, 3))
        q = self.shard('t001', [])
        self.assertEqual(list(module.read_records(q, q.with_suffix('.hce'))), [])

    def test_dedupe_board_stm_only_and_holdout_exclusion(self):
        held = Record(board_of(0), 10, 4, 20)
        # Two differing score/result rows have same board+STM; one opposite STM survives.
        a = self.shard('t000', [held, Record(board_of(1), 11, 0, 21),
                                Record(board_of(1), -80, 4, 27), Record(board_of(1), 12, 1, 22)])
        h = self.shard('h013', [Record(board_of(0), -1, 0, 0)])
        before = hashes(self.data)
        self.run_filter([a], [h])
        out = self.output_rows()
        self.assertEqual(len(out), 2)
        self.assertEqual({(r.board, r.meta & 1) for r in out}, {(board_of(1), 0), (board_of(1), 1)})
        self.assertEqual(before, hashes(self.data))

    def test_result_filter_is_off_by_default_and_stm_symmetric(self):
        # decisive white/black loss vs positive STM score; white/black win vs negative.
        rows = [Record(board_of(0), 500, 0, 10), Record(board_of(1), -500, 4, 10),
                Record(board_of(2), 500, 5, 10), Record(board_of(3), -500, 1, 10),
                Record(board_of(4), 500, 2, 10), Record(board_of(5), 299, 0, 10),
                Record(board_of(6), 500, 4, 10)]
        a = self.shard('t000', rows); h = self.shard('h013', [])
        self.run_filter([a], [h], name='off')
        self.assertEqual(self.output_rows('off'), rows)
        self.run_filter([a], [h], name='on', threshold=300)
        out = self.output_rows('on')
        self.assertEqual(out, rows[-2:])

    def test_same_seed_all_output_bytes_identical_and_inputs_readonly(self):
        a = self.shard('t000', [Record(board_of(i), i - 5, i % 6, i + 10) for i in range(8)])
        b = self.shard('t001', [Record(board_of(i), 900, 4, 100) for i in range(8)])
        h = self.shard('h013', [Record(board_of(3), 0, 3, 0)])
        before = hashes(self.data)
        self.run_filter([a, b], [h], name='one', seed=17)
        self.run_filter([b, a], [h], name='two', seed=17)
        self.assertEqual(hashes(self.work / 'one'), hashes(self.work / 'two'))
        self.assertEqual(hashes(self.data), before)
        for p in (self.work / 'one').rglob('*'):
            if p.is_file(): self.assertEqual(p.stat().st_mode & 0o222, 0)
        manifest = list((self.work / 'one').glob('*md5*'))
        self.assertTrue(manifest, 'new sealed output needs MD5 manifest')

    def test_existing_output_refused_without_changes(self):
        a = self.shard('t000', [Record(board_of(), 1, 0, 2)]); h = self.shard('h013', [])
        self.run_filter([a], [h]); original = hashes(self.work / 'out')
        with self.assertRaises((FileExistsError, ValueError)):
            self.run_filter([a], [h])
        self.assertEqual(original, hashes(self.work / 'out'))

    def test_holdout_alias_cannot_be_a_training_source(self):
        a = self.shard('h013', [Record(board_of(), 1, 0, 2)])
        alias = self.data / 't_alias.pos'; alias.symlink_to(a.name)
        self.run_filter([alias], [a])
        self.assertEqual(self.output_rows(), [])

    def test_reader_rejects_truncated_or_mismatched_structures(self):
        a = self.shard('t000', [Record(board_of(), 1, 0, 2)])
        b = self.data / 'bad.pos'; b.write_bytes(a.read_bytes()[:-1])
        with self.assertRaises((ValueError, OSError)):
            list(module.read_records(b, a.with_suffix('.hce')))
        b.write_bytes(a.read_bytes() + b'x')
        with self.assertRaises((ValueError, OSError)):
            list(module.read_records(b, a.with_suffix('.hce')))
        b.write_bytes(a.read_bytes()); c = self.data / 'bad.hce'
        c.write_bytes(struct.pack('<4sIQ', b'FHCE', 1, 2) + b'\0' * 4)
        with self.assertRaises((ValueError, OSError)):
            list(module.read_records(b, c))

    def test_writer_refuses_existing_pair(self):
        a = self.shard('t000', [Record(board_of(), 1, 0, 2)])
        before = hashes(self.data)
        with self.assertRaises((FileExistsError, ValueError)):
            module.write_records(a, a.with_suffix('.hce'), [])
        self.assertEqual(hashes(self.data), before)

    def test_nonpositive_threshold_rejected(self):
        a = self.shard('t000', []); h = self.shard('h013', [])
        for threshold in [0, -1]:
            with self.assertRaises(ValueError):
                self.run_filter([a], [h], name='bad_' + str(threshold), threshold=threshold)

    def test_missing_text_map_never_claims_game_zero(self):
        a = self.shard('t000', [Record(board_of(), 1, 0, 2)]); h = self.shard('h013', [])
        summary = self.run_filter([a], [h])
        text = json.dumps(summary, sort_keys=True)
        self.assertIn('UNVERIFIED', text)
        self.assertTrue(any('game' in str(k).lower() for k in summary), 'game proof status explicit')


    @staticmethod
    def board_fen(fen):
        piece = {c: i + 1 for i, c in enumerate('PNBRQKpnbrqk')}
        b = bytearray(32)
        for rank, row in enumerate(fen.split()[0].split('/')):
            file = 0
            for c in row:
                if c.isdigit(): file += int(c)
                else:
                    square = (7 - rank) * 8 + file
                    b[square // 2] |= piece[c] << (4 * (square % 2)); file += 1
        return bytes(b)

    def text_fixture(self, uncertain_merge=False):
        fens = [
            '7k/8/8/8/8/8/P7/K7 w - - 0 10',
            '7k/8/8/8/8/P7/8/K7 b - - 0 10',
            '6k1/8/8/8/8/P7/8/K7 w - - 1 11',
            '7k/8/8/8/8/8/1P6/K7 w - - 0 ' + ('12' if uncertain_merge else '1')]
        stems = ['t001', 'h013', 't002', 't003']; paths = {}; texts = {}
        for stem, fen in zip(stems, fens):
            meta = 4 | int(fen.split()[1] == 'b')
            row = Record(self.board_fen(fen), 100, meta, 42)
            paths[stem] = self.shard(stem, [row])
            text = self.data / (stem + '.txt'); text.write_text(fen + ' | 100 | 1\n')
            texts[stem] = text
        return paths, texts, stems

    def test_ordered_text_excludes_entire_holdout_touched_group_across_files(self):
        paths, texts, order = self.text_fixture()
        summary = self.run_filter([paths[s] for s in order if s != 'h013'], [paths['h013']],
                                  text_map=texts, ordered_stems=order)
        self.assertEqual(self.output_rows(), list(module.read_records(paths['t003'], paths['t003'].with_suffix('.hce'))))
        self.assertEqual(summary['game_overlap'], 0)
        self.assertEqual(summary['supplied_holdout_overlap'], 0)

    def test_uncertain_game_boundary_merges_conservatively(self):
        paths, texts, order = self.text_fixture(uncertain_merge=True)
        summary = self.run_filter([paths[s] for s in order if s != 'h013'], [paths['h013']],
                                  text_map=texts, ordered_stems=order)
        self.assertEqual(self.output_rows(), [])
        self.assertEqual(summary['game_overlap'], 0)

    def test_text_must_match_pos_fields_and_cover_complete_order(self):
        paths, texts, order = self.text_fixture()
        train = [paths[s] for s in order if s != 'h013']; holdout = [paths['h013']]
        with self.assertRaises(ValueError):
            self.run_filter(train, holdout, name='partial', text_map={'t001': texts['t001']}, ordered_stems=order)
        texts['h013'].write_text(texts['h013'].read_text().replace(' | 100 | ', ' | 101 | '))
        with self.assertRaises(ValueError):
            self.run_filter(train, holdout, name='mismatch', text_map=texts, ordered_stems=order)

    def test_invalid_record_fields_are_counted_and_not_emitted(self):
        rows = [Record(board_of(i), 50, 4, 100) for i in range(4)]
        a = self.shard('t000', rows); h = self.shard('h013', [])
        # Plant corrupt record FIELDS in own fixtures, not structural corruption.
        data = bytearray(a.read_bytes()); n = len(rows)
        data[16 + 1 * 32 + 1] = 13  # record1 unknown piece nibble
        data[16 + n * 34 + 2] = 255 # record2 bad-line meta sentinel
        a.write_bytes(data)
        hce = bytearray(a.with_suffix('.hce').read_bytes())
        struct.pack_into('<h', hce, 16 + 3 * 2, -32768); a.with_suffix('.hce').write_bytes(hce)
        summary = self.run_filter([a], [h])
        self.assertEqual(self.output_rows(), [rows[0]])
        self.assertEqual(summary['totals']['kept'], 1)
        self.assertEqual(summary['totals']['input'], 4)


    def test_malformed_holdout_field_fails_closed(self):
        a = self.shard('t000', [Record(board_of(), 50, 4, 42)])
        h = self.shard('h013', [Record(board_of(1), 50, 4, 42)])
        data = bytearray(h.read_bytes()); data[-1] = 255; h.write_bytes(data)
        with self.assertRaises(ValueError): self.run_filter([a], [h])

    def test_standin_position_zero_is_never_production_holdout_proof(self):
        a = self.shard('t000', [Record(board_of(), 50, 4, 42)])
        h = self.shard('h013', [Record(board_of(1), 50, 4, 42)])
        summary = self.run_filter([a], [h])
        self.assertEqual(summary['supplied_holdout_overlap'], 0)
        self.assertIn('UNVERIFIED', str(summary['real_holdout_overlap']))


    def test_empty_text_cannot_match_one_record_pos(self):
        paths, texts, order = self.text_fixture()
        texts['t001'].write_text('')
        with self.assertRaises(ValueError):
            self.run_filter([paths[s] for s in order if s != 'h013'], [paths['h013']],
                            text_map=texts, ordered_stems=order)

    def test_writer_rejects_same_output_pair_path_before_writing(self):
        p = self.data / 'same.pos'
        with self.assertRaises(ValueError): module.write_records(p, p, [])
        self.assertFalse(p.exists())

    def test_md5_manifest_independently_matches_every_sealed_payload(self):
        a = self.shard('t000', [Record(board_of(), 50, 4, 42)])
        h = self.shard('h013', [])
        self.run_filter([a], [h])
        out = self.work / 'out'; manifest, = out.glob('*.md5')
        expected = {p.name: hashlib.md5(p.read_bytes()).hexdigest()
                    for p in out.iterdir() if p.is_file() and p != manifest}
        listed = {}
        for line in manifest.read_text().splitlines():
            digest, name = line.split(None, 1); listed[name.strip()] = digest
        self.assertEqual(listed, expected)


if __name__ == '__main__': unittest.main(verbosity=2)
