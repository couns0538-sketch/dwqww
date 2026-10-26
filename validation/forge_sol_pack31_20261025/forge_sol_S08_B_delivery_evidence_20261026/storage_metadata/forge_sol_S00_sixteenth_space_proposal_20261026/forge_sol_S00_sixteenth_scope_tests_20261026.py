import importlib.util
from pathlib import Path
import unittest

P = Path(__file__).with_name('forge_sol_S00_sixteenth_readonly_audit_20261026.py')
spec = importlib.util.spec_from_file_location('wave15', P)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ScopeTests(unittest.TestCase):
    def test_exact_two_roots_only(self):
        self.assertEqual(len(m.BUILDS), 2)
        for root in m.BUILDS:
            self.assertTrue(m.scope_path(root / 'libforge_core.a'))
            self.assertTrue(m.scope_path(root / 'CMakeFiles/forge_core.dir/src/search.cpp.o'))

    def test_v2_and_unknown_window_are_excluded(self):
        for name in ('forge_sol_S08_ASAN_v2_window3_20261026',
                     'forge_sol_S08_ASAN_window2_20261026',
                     'forge_sol_S08_B_Release_ON_window1_20261026'):
            self.assertFalse(m.scope_path(m.S08 / name / 'build/libforge_core.a'))

    def test_every_raw_executable_is_excluded(self):
        for name in ('forge', 'Forge', 'forge_prof_tests', 'forge_tests', 'forge_bench'):
            self.assertFalse(m.scope_path(m.BUILDS[0] / name))

    def test_source_log_net_and_other_archive_excluded(self):
        for name in ('search.cpp', 'build.stdout', 'nnue_weights.inc', 'libother.a', 'x.o'):
            self.assertFalse(m.scope_path(m.BUILDS[0] / name))

    def test_repo_and_source_roots_excluded(self):
        for path in ('/workspace/dwqww/build/libforge_core.a',
                     '/workspace/.cloud-setup/dwqww/build/libforge_core.a',
                     str(m.S08 / 'Lprime/build/libforge_core.a')):
            self.assertFalse(m.scope_path(Path(path)))

    def test_traversal_and_prefix_sibling_excluded(self):
        self.assertFalse(m.scope_path(m.BUILDS[0] / '../build/libforge_core.a'))
        self.assertFalse(m.scope_path(Path(str(m.BUILDS[0]) + '-other/libforge_core.a')))

    def test_unknown_target_is_excluded(self):
        self.assertFalse(m.scope_path(m.BUILDS[0] / 'CMakeFiles/not_forge.dir/x.o'))

    def test_only_et_rel_objects_and_ar_archives(self):
        header = bytearray(20)
        header[:4] = b'\x7fELF'
        header[5] = 1
        header[16] = 1
        self.assertEqual(m.format_kind(bytes(header), '.o'), 'ELF_ET_REL_compiler_object')
        header[16] = 2
        self.assertIsNone(m.format_kind(bytes(header), '.o'))
        header[16] = 3
        self.assertIsNone(m.format_kind(bytes(header), '.o'))
        self.assertEqual(m.format_kind(b'!<arch>\n', '.a'), 'AR_static_core_library')

    def test_every_alias_must_be_scoped_and_compiler_bound(self):
        safe = str(m.BUILDS[0] / 'CMakeFiles/forge_core.dir/src/search.cpp.o')
        row = {'path': safe, 'nlink': 2}
        self.assertIn('all_hardlink_aliases_not_accounted', m.group_reasons([row], {safe}, set(), set()))
        unsafe = dict(row, path='/workspace/dwqww/evidence/search.cpp.o')
        reasons = m.group_reasons([row, unsafe], {safe}, set(), set())
        self.assertIn('alias_outside_exact_two_build_cache_roots', reasons)
        self.assertIn('alias_has_no_exact_compile_or_static_library_binding', reasons)

    def test_active_reference_and_prior_map_reject_whole_group(self):
        safe = str(m.BUILDS[0] / 'libforge_core.a')
        row = {'path': safe, 'nlink': 1}
        self.assertEqual(m.group_reasons([row], {safe}, set(), set()), [])
        self.assertIn('active_process_reference', m.group_reasons([row], {safe}, set(), {safe}))
        self.assertIn('active_process_reference', m.group_reasons([row], {safe}, set(), {str(m.BUILDS[0])}))
        self.assertIn('prior_retirement_map_collision', m.group_reasons([row], {safe}, {safe}, set()))


if __name__ == '__main__':
    unittest.main(verbosity=2)
