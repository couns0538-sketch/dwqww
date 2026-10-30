"""Synthetic-only clearance regressions; no private real013/014 is available."""
import contextlib
import hashlib
import importlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

TOOLS = Path(__file__).resolve().parents[2] / 'tools/data2'
sys.path.insert(0, str(TOOLS))
import convert_dataset as c
from forge_pos import PosReader, PosWriter, text_record

FENS = [
    'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 | 61 | 0.0\n',
    'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1 | -27 | 1.0\n',
    'rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2 | 20 | 0.5\n',
]


class HoldoutClearanceTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((TOOLS / 'audit_holdout_clearance.py').is_file(), 'clearance CLI is missing')
        self.audit = importlib.import_module('audit_holdout_clearance')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.work = self.root / 'scratch'
        self.work.mkdir()
        self.src = self.root / 'input.txt'
        self.out = self.root / 'converted'
        self.h13 = self.holdout('holdout013', [FENS[0]])
        self.h14 = self.holdout('holdout014', [FENS[1]])

    def holdout(self, name, rows):
        with contextlib.closing(PosWriter(self.root / name, name, False)) as writer:
            for row in rows:
                writer.append(text_record(row)[0])
            writer.seal()
        return self.root / name / (name + '.pos')

    def convert(self, rows, *extra):
        self.src.write_text(''.join(rows))
        args = c.parser().parse_args(['convert', '--input', str(self.src), '--out', str(self.out),
                                     '--no-filters', '--min-free-mb', '0', *extra])
        with contextlib.redirect_stdout(io.StringIO()):
            c.run(args)

    def argv(self):
        return ['--out', str(self.out), '--holdout-013', str(self.h13), '--holdout-014', str(self.h14),
                '--holdout-013-sha256', hashlib.sha256(self.h13.read_bytes()).hexdigest(),
                '--holdout-014-sha256', hashlib.sha256(self.h14.read_bytes()).hexdigest(),
                '--holdout-013-rows', '1', '--holdout-014-rows', '1',
                '--report', str(self.root / 'clearance.json'), '--work-dir', str(self.work), '--min-free-mb', '0']

    def run_audit(self, argv=None):
        with contextlib.redirect_stderr(io.StringIO()):
            report = self.audit.run(self.audit.parser().parse_args(argv or self.argv()))
        self.assertEqual(json.loads((self.root / 'clearance.json').read_text()), report)
        self.assertEqual(list(self.work.iterdir()), [], 'owned ephemeral indexes must not accumulate')
        self.assertEqual(hashlib.sha256(Path(report['log']['path']).read_bytes()).hexdigest(), report['log']['sha256'])
        return report

    def test_zero_overlap_records_actual_rows_and_source_hashes(self):
        self.convert([FENS[2]])
        result = self.run_audit()
        self.assertEqual(result['status'], 'PASS')
        self.assertTrue(result['position_overlap_clear'])
        self.assertEqual(result['output']['rows'], 1)
        self.assertEqual(result['overlap_output_rows'], 0)
        self.assertEqual(result['overlap_unique_keys'], 0)
        self.assertEqual([h['shard_id'] for h in result['holdouts']], ['013', '014'])
        self.assertEqual([h['rows_scanned'] for h in result['holdouts']], [1, 1])
        self.assertEqual(result['holdouts'][0]['identity']['sha256'], hashlib.sha256(self.h13.read_bytes()).hexdigest())
        self.assertIn('COMPLETE.json', result['output']['files'])
        self.assertIn('config.json', result['output']['files'])
        self.assertFalse(result['game_id_clearance'])

    def test_all_overlap_fails_and_counts_duplicates_as_output_rows(self):
        self.convert([FENS[0], FENS[0], FENS[1]], '--no-dedupe')
        result = self.run_audit()
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(result['overlap_output_rows'], 3)
        self.assertEqual(result['overlap_unique_keys'], 2)
        self.assertEqual([h['overlap_output_rows'] for h in result['holdouts']], [2, 1])

    def test_key_ignores_scores_results_rights_clocks_and_retains_stm(self):
        changed = FENS[0].replace('KQkq - 0 1', '- - 7 9').replace('61 | 0.0', '-99 | 1.0')
        self.convert([changed, FENS[0].replace(' w ', ' b ')])
        result = self.run_audit()
        self.assertEqual(result['overlap_output_rows'], 1)
        self.assertEqual(result['output']['rows'], 2)

    def test_zero_rows_does_not_pass_training_gate(self):
        self.convert([FENS[0]], '--holdout', str(self.h13))
        result = self.run_audit()
        self.assertEqual(result['status'], 'BLOCKED_EMPTY_OUTPUT')
        self.assertTrue(result['position_overlap_clear'])
        self.assertEqual(result['output']['rows'], 0)

    def test_wrong_holdout_hash_is_blocked(self):
        self.convert([FENS[2]])
        argv = self.argv()
        argv[argv.index('--holdout-013-sha256') + 1] = '0' * 64
        result = self.run_audit(argv)
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertIn('013', result['error'])
        self.assertFalse(result['position_overlap_clear'])

    def test_wrong_expected_count_is_blocked(self):
        self.convert([FENS[2]])
        argv = self.argv()
        argv[argv.index('--holdout-014-rows') + 1] = '2'
        result = self.run_audit(argv)
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertIn('row count', result['error'])

    def test_swapped_holdout_identity_is_blocked(self):
        self.convert([FENS[2]])
        argv = self.argv()
        argv[argv.index('--holdout-013') + 1] = str(self.h14)
        argv[argv.index('--holdout-014') + 1] = str(self.h13)
        self.assertEqual(self.run_audit(argv)['status'], 'BLOCKED')

    def test_same_holdout_file_cannot_be_bound_to_both_shards(self):
        self.convert([FENS[2]])
        self.h14.unlink()
        self.h14.hardlink_to(self.h13)
        self.assertEqual(self.run_audit()['status'], 'BLOCKED')

    def test_corrupt_sealed_output_is_blocked(self):
        self.convert([FENS[2]])
        chunk = c.read_chunks(self.out)[0]
        with (self.out / chunk['bullet']).open('ab') as stream:
            stream.write(b'corrupt')
        result = self.run_audit()
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertIn('hash mismatch', result['error'])

    def test_incomplete_output_is_blocked(self):
        self.convert([FENS[2]])
        (self.out / 'COMPLETE.json').unlink()
        self.assertEqual(self.run_audit()['status'], 'BLOCKED')

    def test_changed_holdout_after_scan_is_blocked(self):
        self.convert([FENS[2]])
        target = self.h13
        class ChangingReader(PosReader):
            def __iter__(self):
                yield from super().__iter__()
                if self.pos == target:
                    raw = bytearray(target.read_bytes())
                    raw[-1] ^= 2
                    target.write_bytes(raw)
        with mock.patch.object(self.audit, 'PosReader', ChangingReader):
            result = self.run_audit()
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertIn('changed', result['error'])

    def test_temporary_holdout_mutation_and_restore_cannot_false_pass(self):
        self.convert([FENS[0]])
        target = self.h13
        original_bytes = target.read_bytes()
        alternate = self.holdout('alternate', [FENS[2]]).read_bytes()
        class RestoringReader(PosReader):
            def __iter__(self):
                if self.pos != target:
                    yield from super().__iter__()
                    return
                target.write_bytes(alternate)
                try:
                    yield from super().__iter__()
                finally:
                    target.write_bytes(original_bytes)
        with mock.patch.object(self.audit, 'PosReader', RestoringReader):
            result = self.run_audit()
        self.assertEqual(target.read_bytes(), original_bytes)
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertFalse(result['position_overlap_clear'])

    def test_retargeted_holdout_symlink_is_blocked(self):
        self.convert([FENS[2]])
        original = self.h13
        alias = self.root / 'alias013.pos'
        alias.symlink_to(original)
        self.h13 = alias
        alternate = self.h14
        class RetargetingReader(PosReader):
            def __iter__(self):
                yield from super().__iter__()
                if self.pos == original:
                    alias.unlink()
                    alias.symlink_to(alternate)
        with mock.patch.object(self.audit, 'PosReader', RetargetingReader):
            self.assertEqual(self.run_audit()['status'], 'BLOCKED')

    def test_changed_output_after_verification_is_blocked(self):
        self.convert([FENS[2]])
        chunk = c.read_chunks(self.out)[0]
        output_text = self.out / chunk['text']
        class ChangingReader(PosReader):
            def __iter__(self):
                yield from super().__iter__()
                output_text.write_text(FENS[0])
        with mock.patch.object(self.audit, 'PosReader', ChangingReader):
            result = self.run_audit()
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertIn('changed', result['error'])

    def test_disk_reserve_is_checked_during_holdout_scan(self):
        self.convert([FENS[2]])
        free = [10**12]
        class LowSpaceReader(PosReader):
            def __iter__(self):
                for row in super().__iter__():
                    free[0] = 0
                    yield row
        argv = self.argv()
        argv[argv.index('--min-free-mb') + 1] = '20480'
        usage = lambda _: shutil._ntuple_diskusage(10**12, 10**12-free[0], free[0])
        with mock.patch.object(self.audit, 'BATCH_ROWS', 1), \
             mock.patch.object(self.audit, 'PosReader', LowSpaceReader), \
             mock.patch.object(self.audit.shutil, 'disk_usage', side_effect=usage):
            result = self.run_audit(argv)
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertEqual(result['holdouts'][0]['rows_scanned'], 1)
        self.assertIn('free-space', result['error'])

    def test_invalid_report_inside_sealed_output_creates_no_artifacts(self):
        self.convert([FENS[2]])
        argv = self.argv()
        argv[argv.index('--report') + 1] = str(self.out / 'clearance.json')
        before = sorted(path.name for path in self.out.iterdir())
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(ValueError):
            self.audit.run(self.audit.parser().parse_args(argv))
        self.assertEqual(sorted(path.name for path in self.out.iterdir()), before)

    def test_preflight_estimate_preserves_reserve_before_index_creation(self):
        self.convert([FENS[2]])
        argv = self.argv()
        argv[argv.index('--min-free-mb') + 1] = '20480'
        free = (20480 + 8) * 1024 * 1024
        usage = shutil._ntuple_diskusage(10**12, 10**12-free, free)
        with mock.patch.object(self.audit.shutil, 'disk_usage', return_value=usage):
            result = self.run_audit(argv)
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertIn('estimated index', result['error'])
        self.assertNotIn('owned_index_created', Path(result['log']['path']).read_text())

    def test_changed_audit_tool_source_is_blocked(self):
        self.convert([FENS[2]])
        fake_tool = self.root / 'implementation.py'
        fake_tool.write_text('initial source')
        class ChangingReader(PosReader):
            def __iter__(self):
                yield from super().__iter__()
                fake_tool.write_text('changed source')
        with mock.patch.object(self.audit, 'TOOL_FILES', (fake_tool,), create=True), \
             mock.patch.object(self.audit, 'PosReader', ChangingReader):
            result = self.run_audit()
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertIn('tool source changed', result['error'])

    def test_existing_report_is_never_overwritten(self):
        self.convert([FENS[2]])
        report = self.root / 'clearance.json'
        report.write_text('keep me')
        with self.assertRaises(FileExistsError):
            self.run_audit()
        self.assertEqual(report.read_text(), 'keep me')

    def test_disk_reserve_blocks_without_leaving_index(self):
        self.convert([FENS[2]])
        argv = self.argv()
        argv[argv.index('--min-free-mb') + 1] = '20480'
        with mock.patch.object(self.audit.shutil, 'disk_usage', return_value=shutil._ntuple_diskusage(100, 99, 1)):
            result = self.run_audit(argv)
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertIn('free-space', result['error'])

    def test_cli_failure_exit_and_required_identity_arguments(self):
        self.convert([FENS[0]])
        command = [sys.executable, str(TOOLS / 'audit_holdout_clearance.py')]
        failure = subprocess.run(command + self.argv(), capture_output=True, text=True)
        self.assertEqual(failure.returncode, 1, failure.stderr)
        self.assertEqual(json.loads(failure.stdout)['status'], 'FAIL')
        missing = subprocess.run(command + ['--out', str(self.out)], capture_output=True, text=True)
        self.assertEqual(missing.returncode, 2)


if __name__ == '__main__':
    unittest.main()
