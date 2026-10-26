import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('activity', Path(__file__).with_name('forge_sol_S00_sixteenth_activity_preflight_20261026.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ActivityTests(unittest.TestCase):
    def test_root_cwd_and_descendant_affect_whole_build(self):
        root = str(m.BUILDS[0])
        self.assertEqual(m.affected_build(root), root)
        self.assertEqual(m.affected_build(root + '/CMakeFiles/forge.dir'), root)
        self.assertEqual(m.affected_build(root + '/forge (deleted)'), root)

    def test_other_windows_and_prefix_siblings_do_not_affect_v1(self):
        self.assertIsNone(m.affected_build(str(m.BUILDS[0]) + '-other/x'))
        self.assertIsNone(m.affected_build('/workspace/forge-pack24-20261026/S08/forge_sol_S08_B_Release_ON_window1_20261026/build/forge'))
        self.assertIsNone(m.affected_build('pipe:[1234]'))

    def test_generic_ninja_cwd_blocks_without_root_in_cmdline(self):
        with tempfile.TemporaryDirectory() as temp:
            proc = Path(temp)
            pid = proc / '12345'
            (pid / 'fd').mkdir(parents=True)
            (pid / 'status').write_text('Name:\tninja\nState:\tS (sleeping)\n')
            (pid / 'cmdline').write_bytes(b'ninja\0forge\0')
            (pid / 'cwd').symlink_to(m.BUILDS[1] / 'CMakeFiles', target_is_directory=True)
            (pid / 'maps').write_text('')
            d = m.snapshot_proc(proc)
            self.assertEqual(d['blocked_build_roots'], [str(m.BUILDS[1])])
            self.assertEqual(d['references'][0]['kind'], 'cwd')

    def test_fd_and_map_references_block_even_unknown_process(self):
        with tempfile.TemporaryDirectory() as temp:
            proc = Path(temp)
            pid = proc / '12345'
            (pid / 'fd').mkdir(parents=True)
            (pid / 'status').write_text('Name:\tunknown\nState:\tR (running)\n')
            (pid / 'cmdline').write_bytes(b'custom\0')
            (pid / 'fd/7').symlink_to(m.BUILDS[0] / 'libforge_core.a')
            (pid / 'maps').write_text('1000-2000 r--p 0 00:00 1 ' + str(m.BUILDS[1] / 'forge') + '\n')
            d = m.snapshot_proc(proc)
            self.assertEqual(set(d['blocked_build_roots']), {str(m.BUILDS[0]), str(m.BUILDS[1])})


if __name__ == '__main__':
    unittest.main(verbosity=2)
