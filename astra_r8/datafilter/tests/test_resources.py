"""Resource guard regressions; mocks never allocate data or relax production policy."""
from pathlib import Path
import sys
import stat
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class ResourcePolicyTests(unittest.TestCase):
    def setUp(self):
        import resource_policy
        self.policy = resource_policy

    def test_only_current_authorized_root(self):
        p = self.policy
        self.assertEqual(p.check_output_path(p.ARTIFACT_ROOT / 'new' / 'rows.jsonl'),
                         (p.ARTIFACT_ROOT / 'new' / 'rows.jsonl').resolve())
        for target in ('D:/grok-pc-data/dwqww/astra8_data/new',
                       'F:/astra8_data/new', 'C:/astra8_data_other/new',
                       'C:/astra8_data/../outside'):
            with self.subTest(target=target), self.assertRaises(ValueError):
                p.check_output_path(target)

    def test_redirected_root_or_child_refused(self):
        p = self.policy
        original = Path.resolve
        for redirected in (p.ARTIFACT_ROOT, p.ARTIFACT_ROOT / 'link' / 'new'):
            def resolve(path, *args, **kwargs):
                if path == redirected:
                    return Path('D:/outside').absolute()
                return original(path, *args, **kwargs)
            with self.subTest(redirected=redirected), patch.object(Path, 'resolve', resolve):
                with self.assertRaises(ValueError):
                    p.check_output_path(p.ARTIFACT_ROOT / 'link' / 'new')

    def test_d_reserve_includes_next_allocation(self):
        p = self.policy
        def usage(drive):
            return SimpleNamespace(free=p.MINIMUM_FREE_BYTES+100 if str(drive).startswith('D:') else 60_000_000_000)
        with patch.object(p.shutil, 'disk_usage', side_effect=usage), patch.object(p, 'tree_bytes', return_value=0):
            p.storage_guard(allowance=99)
            with self.assertRaisesRegex(OSError, 'D:.*reserve'):
                p.storage_guard(allowance=101)

    def test_f_read_only_low_space_does_not_block(self):
        p = self.policy
        def usage(drive):
            if str(drive).startswith('F:'):
                raise AssertionError('read-only F reserve is not an allocation gate')
            return SimpleNamespace(free=60_000_000_000)
        with patch.object(p.shutil, 'disk_usage', side_effect=usage), patch.object(p, 'tree_bytes', return_value=0):
            p.storage_guard(allowance=100)

    def test_d_write_reserve_is_preserved(self):
        p = self.policy
        def usage(drive):
            return SimpleNamespace(free=49_999_999_999 if str(drive).startswith('D:') else 60_000_000_000)
        with patch.object(p.shutil, 'disk_usage', side_effect=usage), patch.object(p, 'tree_bytes', return_value=0):
            with self.assertRaisesRegex(OSError, 'D:.*reserve'):
                p.storage_guard(allowance=100)

    def test_budget_counts_owned_roots_and_allowance(self):
        p = self.policy
        with patch.object(p.shutil, 'disk_usage', return_value=SimpleNamespace(free=60_000_000_000)), \
                patch.object(p, 'tree_bytes', return_value=p.MAX_ARTIFACT_BYTES//len(p.BUDGET_ROOTS)) as tree:
            p.storage_guard(allowance=0)
            self.assertEqual(set(call.args[0] for call in tree.call_args_list), set(p.BUDGET_ROOTS))
            with self.assertRaisesRegex(OSError, 'artifact cap'):
                p.storage_guard(allowance=1)

    def test_invalid_allowance_and_destination_fail_before_disk(self):
        p = self.policy
        with patch.object(p.shutil, 'disk_usage') as disk:
            for allowance in (-1, 1.5, True):
                with self.subTest(allowance=allowance), self.assertRaises(ValueError):
                    p.storage_guard(allowance=allowance)
            with self.assertRaises(ValueError):
                p.storage_guard('D:/outside')
            disk.assert_not_called()

    def test_d_reserve_cannot_fall_one_byte_short(self):
        p = self.policy
        with patch.object(p.shutil, 'disk_usage', return_value=SimpleNamespace(free=p.MINIMUM_FREE_BYTES+63)), \
                patch.object(p, 'tree_bytes', return_value=0):
            with self.assertRaises(OSError):
                p.storage_guard(allowance=64)

    def test_budget_scanner_counts_nested_regular_files(self):
        p = self.policy
        root = p.ARTIFACT_ROOT
        directory = SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0)
        def entry(name, mode, size=0, attributes=0):
            item = SimpleNamespace(path=str(root / name))
            item.stat = lambda follow_symlinks=False: SimpleNamespace(
                st_mode=mode, st_size=size, st_file_attributes=attributes)
            return item
        first = MagicMock()
        first.__enter__.return_value = [entry('one', stat.S_IFREG, 3), entry('nested', stat.S_IFDIR)]
        second = MagicMock()
        second.__enter__.return_value = [entry('nested/two', stat.S_IFREG, 4)]
        with patch.object(p.os.path, 'lexists', return_value=True), \
                patch.object(Path, 'lstat', return_value=directory), \
                patch.object(p.os, 'scandir', side_effect=[first, second]):
            self.assertEqual(p.tree_bytes(root), 7)

    def test_budget_scanner_rejects_symlinks_and_junctions(self):
        p = self.policy
        directory = SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0)
        for mode, flags in ((stat.S_IFLNK, 0), (stat.S_IFDIR, stat.FILE_ATTRIBUTE_REPARSE_POINT)):
            item = SimpleNamespace(path=str(p.ARTIFACT_ROOT / 'redirect'))
            item.stat = lambda follow_symlinks=False: SimpleNamespace(st_mode=mode, st_file_attributes=flags)
            entries = MagicMock()
            entries.__enter__.return_value = [item]
            original = Path.resolve
            def resolve(path, *args, **kwargs):
                if path == Path(item.path):
                    return Path('D:/outside')
                return original(path, *args, **kwargs)
            with self.subTest(mode=mode, flags=flags), \
                    patch.object(p.os.path, 'lexists', return_value=True), \
                    patch.object(Path, 'lstat', return_value=directory), \
                    patch.object(Path, 'resolve', resolve), \
                    patch.object(p.os, 'scandir', return_value=entries):
                with self.assertRaisesRegex(ValueError, 'redirected entry'):
                    p.tree_bytes(p.ARTIFACT_ROOT)

    def test_budget_scanner_skips_internal_alias_without_double_counting(self):
        p = self.policy
        root = p.ARTIFACT_ROOT
        directory = SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0)
        alias = SimpleNamespace(path=str(root / 'alias'))
        alias.stat = lambda follow_symlinks=False: SimpleNamespace(
            st_mode=stat.S_IFLNK, st_file_attributes=0, st_size=0)
        real = SimpleNamespace(path=str(root / 'real'))
        real.stat = lambda follow_symlinks=False: SimpleNamespace(
            st_mode=stat.S_IFREG, st_file_attributes=0, st_size=7)
        entries = MagicMock()
        entries.__enter__.return_value = [alias, real]
        original = Path.resolve
        def resolve(path, *args, **kwargs):
            if path == Path(alias.path):
                return root / 'real'
            return original(path, *args, **kwargs)
        with patch.object(p.os.path, 'lexists', return_value=True), \
                patch.object(Path, 'lstat', return_value=directory), \
                patch.object(Path, 'resolve', resolve), \
                patch.object(p.os, 'scandir', return_value=entries):
            self.assertEqual(p.tree_bytes(root), 7)

    def test_filter_preflight_checks_both_destinations_before_mkdir(self):
        import filter_positions as f
        seen = []
        def guard(root=None, allowance=64*1024*1024):
            seen.append(Path(root))
            if len(seen) == 2:
                raise OSError('reserve fixture')
        out = self.policy.ARTIFACT_ROOT / 'uncreated-resource-test'
        with patch.object(f, 'storage_guard', side_effect=guard), patch.object(Path, 'mkdir') as mkdir:
            with self.assertRaisesRegex(OSError, 'reserve fixture'):
                f.run_filter('unused', out)
            self.assertEqual(seen, [out, out.with_name(out.name + '.partial')])
            mkdir.assert_not_called()


if __name__ == '__main__':
    unittest.main()
