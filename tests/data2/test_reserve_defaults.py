"""QA Final2 7B: default D-volume headroom is 32 GiB, not 20 GiB."""
import pathlib
import sys
import unittest
from unittest import mock
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / 'tools/data2'))
import convert_dataset as converter
import audit_holdout_clearance as audit

class ReserveDefaults(unittest.TestCase):
    def test_converter_default_blocks_25_gib_before_any_index_work(self):
        for command in ('convert', 'holdout-dedup'):
            with self.subTest(command=command):
                args = converter.parser().parse_args([command, '--input', 'unused', '--out', 'unused'])
                with mock.patch.object(converter.shutil, 'disk_usage', return_value=type('Usage', (), {'free':25*1024**3})()):
                    with self.assertRaisesRegex(ValueError, 'free-space guard'):
                        converter.disk_guard(pathlib.Path('/tmp'), args.min_free_mb, 'test preflight')
    def test_audit_default_reserves_32_gib(self):
        self.assertEqual(audit.parser().get_default('min_free_mb') * 1024**2, 32*1024**3)
    def test_explicit_test_override_remains_available(self):
        args = converter.parser().parse_args(['convert','--input','unused','--out','unused','--min-free-mb','0'])
        self.assertEqual(args.min_free_mb, 0)

if __name__ == '__main__': unittest.main()
