"""Small independent fixtures; never read production data."""
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from qc_core import Profile, fen_info, is_mate, read_pos, signed_score
from run_policy import safe_path, free_guard, Snapshot, Inputs

FEN = '4k3/8/8/8/8/8/8/4K3 w - - 0 1'


class CoreTests(unittest.TestCase):
    def test_mate_inclusive_both_signs(self):
        self.assertFalse(is_mate(29999))
        self.assertFalse(is_mate(-29999))
        self.assertTrue(is_mate(30000))
        self.assertTrue(is_mate(-30000))
        self.assertTrue(is_mate(32767))

    def test_score_not_bool_float_or_outside_format(self):
        for value in (True, 1.5, 'nan', '-32768', 32768):
            with self.subTest(value=value), self.assertRaises(ValueError):
                signed_score(value)

    def test_full_state_key_and_pieces(self):
        value = fen_info(FEN)
        self.assertEqual(value['pieces'], 2)
        self.assertEqual(value['phase'], 0)
        self.assertNotEqual(value['fen'], fen_info(FEN.replace('0 1', '1 1'))['fen'])
        for fen in (FEN.rsplit(' ', 2)[0], FEN.replace('4k3', '4k4'), FEN.replace(' - - ', ' KK - ')):
            with self.assertRaises(ValueError):
                fen_info(fen)

    def test_fen_does_not_normalize_invalid_original_text(self):
        for fen in (FEN.replace(' w ','\u00a0w '),FEN.replace('0 1','0\n1'),FEN.replace('0 1','0 \u0661'),None):
            with self.subTest(fen=fen),self.assertRaises(ValueError):
                fen_info(fen)

    def test_stm_white_scores_unknown_outcomes(self):
        profile = Profile()
        profile.add(FEN, 100, 1, 'train', 50)
        profile.add(FEN.replace(' w ', ' b '), 100, 1, 'val', 50)
        profile.add(FEN, 0, None, 'train', 0)
        report = profile.report()
        self.assertEqual(report['rows'], 3)
        self.assertEqual(report['score_white']['sum'], 0)
        self.assertEqual(report['wdl_stm'], {'win': 1, 'loss': 1, 'unknown': 1})
        self.assertEqual(report['wdl_white'], {'win': 2, 'unknown': 1})
        self.assertEqual(report['paired_old_score']['rows'], 3)

    def test_invalid_outcome_not_draw(self):
        for result in ('unknown', True, -1, 0.25):
            with self.assertRaises(ValueError):
                Profile().add(FEN, 0, result, 'train', 0)

    def test_pos_size_and_column_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'fixture.pos'
            board = bytes(32)
            path.write_bytes(struct.pack('<4sIQ', b'FPOS', 1, 1) + board + struct.pack('<hB', 123, 5))
            rows = list(read_pos(path))
            self.assertEqual(rows, [(board, 123, 5)])
            path.write_bytes(path.read_bytes()[:-1])
            with self.assertRaises(ValueError):
                list(read_pos(path))


class PolicyTests(unittest.TestCase):
    def test_os_null_sink_handle_is_not_a_filesystem_output(self):
        descriptor=os.open(os.devnull,os.O_RDWR)
        try:
            self.assertEqual(os.write(descriptor,b'null-sink fixture'),17)
        finally:
            os.close(descriptor)
        with self.assertRaises(ValueError):
            safe_path('D:/a13/NUL.txt',write=True)

    def test_windows_device_and_wildcard_paths_rejected(self):
        for leaf in ('NUL','CON.txt','COM1.log','LPT9','file?.json','bad|name','bad<name'):
            with self.subTest(leaf=leaf),self.assertRaises(ValueError):
                safe_path('D:/a13/'+leaf,write=True)

    def test_line_limit_includes_terminated_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'long.txt'
            path.write_bytes(b'a'*(1024*1024+1)+b'\n')
            with self.assertRaisesRegex(ValueError,'line too long'):
                list(Snapshot(path).lines())

    def test_owned_link_removal_preserves_target_and_cannot_write_through(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'target.txt'
            target.write_text('preserved')
            alias=Path(tmp)/'alias.txt'
            alias.symlink_to(target)
            with self.assertRaises(ValueError):
                safe_path(alias,write=True)
            alias.unlink()
            self.assertEqual(target.read_text(),'preserved')

    def test_outside_root_and_protected_paths(self):
        for path in ('C:/escape/output', 'D:/a13/../escape', 'D:/a13/x.nnue',
                     'D:/a13/handoff_v7/file', 'F:/forge_push/file', 'D:/a13/a:stream',
                     'D:/a13/alias./file', 'D:/a13/locks/file'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                safe_path(path, write=True)

    def test_disk_floor_plus_allocation(self):
        floor = 50 * 1024 ** 3
        with self.assertRaises(OSError):
            free_guard(1024, free=floor + 1023)
        self.assertEqual(free_guard(1024, free=floor + 1024), floor + 1024)
        with self.assertRaises(ValueError):
            free_guard(-1, free=floor)

    def test_snapshot_rejects_changed_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'input.txt'
            path.write_text('a', encoding='utf-8')
            snapshot = Snapshot(path)
            snapshot.digest()
            path.write_text('changed', encoding='utf-8')
            with self.assertRaises(ValueError):
                snapshot.check()

    def test_receipts_rehash_same_size_input_with_restored_mtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'input.txt'
            path.write_bytes(b'original')
            audit=Inputs()
            audit.get(path).digest()
            initial=path.stat()
            path.write_bytes(b'changed!')
            os.utime(path,ns=(initial.st_atime_ns,initial.st_mtime_ns))
            with self.assertRaisesRegex(ValueError,'content changed'):
                audit.receipts()


if __name__ == '__main__':
    unittest.main()
