"""Direct policy fixtures: never open or stat any forbidden filesystem path."""
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import path_guard
import run_regression


class RuntimeGuardTests(unittest.TestCase):
    def test_forbidden_paths_and_windows_aliases(self):
        paths = ('F:/never-open', 'D:/a10/never-open', 'D:/a11/not-created.nnue',
                 'D:/a11/forge_queue_state.json', 'D:/a11/STOP', 'D:/a11/PAUSE',
                 'D:/a10./never-open', 'D:/a11/not-created.nnue.',
                 'D:/a11/not-created.nnue ', 'D:/a11/forge_queue_state.json.',
                 'D:/a11/STOP.txt', 'D:/a11/subdir /file', '\\\\?\\D:\\a11\\x')
        with patch.object(path_guard.os, 'lstat', side_effect=AssertionError('forbidden path inspected')):
            for path in paths:
                for guard in (path_guard.audit_open, run_regression.write_guard):
                    with self.subTest(path=path, guard=guard.__name__), self.assertRaises(ValueError):
                        guard('open', (path, 'rb', 0))

    def test_write_outside_owned_root_refused_before_stat(self):
        with patch.object(path_guard.os, 'lstat', side_effect=AssertionError('outside path inspected')):
            with self.assertRaises(ValueError):
                path_guard.audit_open('open', ('C:/not-created', 'wb', os.O_WRONLY))
            with self.assertRaises(ValueError):
                run_regression.own('D:/a10/not-created')

    def test_root_to_leaf_stops_at_reparse(self):
        visited = []
        def fake_lstat(path):
            visited.append(path)
            return SimpleNamespace(st_mode=0, st_file_attributes=(0x400 if path == 'd:\\a11\\junction' else 0))
        with patch.object(path_guard.os, 'lstat', fake_lstat):
            with self.assertRaises(ValueError):
                path_guard.no_reparse('D:/a11/junction/forbidden-descendant')
        self.assertEqual(visited, ['d:\\', 'd:\\a11', 'd:\\a11\\junction'])

    def test_exact_owned_runtime_configuration(self):
        self.assertEqual(run_regression.ROOT, Path('D:/a11'))
        self.assertEqual(run_regression.RUNTIME, Path('D:/a11/runtime'))
        self.assertEqual(run_regression.LANE_GUARD, Path(__file__).parent/'lane_guard.py')


if __name__ == '__main__':
    unittest.main()
