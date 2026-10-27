"""Pure fixtures for the new S12 ABI/cache extension; no compiler executes."""
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch
import forge_sol_S12_native_common_20261027 as common


class SyntheticRecipeFixtures(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='forge_s12_recipe_fixture_')
        self.addCleanup(self.tmp.cleanup)
        self.source = Path(self.tmp.name) / 'source'
        self.build = Path(self.tmp.name) / 'build'
        self.source.mkdir(); self.build.mkdir()
        self.base = type('QualifiedBaseRecipeFixture', (), {'audit_recipe': lambda self, s, b: {'status': 'BASE_FIXTURE'}})()

    def recipe(self, setting, definition=True, has_option=True, extra=None):
        (self.source / 'CMakeLists.txt').write_text('option(FORGE_NNUE_LAZY_ACC "fixture" OFF)\n' if has_option else '# pristine base\n')
        (self.build / 'CMakeCache.txt').write_text('FORGE_NNUE_LAZY_ACC:BOOL=' + setting + '\n' if has_option else '')
        argv = ['fixture-cxx', '-DFORGE_NNUE_HIDDEN=256']
        if setting == 'ON' and definition: argv += ['-DFORGE_NNUE_LAZY_ACC=1']
        if extra: argv += [extra]
        (self.build / 'compile_commands.json').write_text(json.dumps([{'arguments': argv, 'file': str(self.source / 'src/search.cpp')}]))
        with patch.object(common, 'profile_api', return_value=self.base):
            return common.audit_recipe(self.source, self.build, 'Release', setting)

    def test_pristine_off_cache_does_not_invent_feature_option(self):
        try: result = self.recipe('OFF', has_option=False)
        except ValueError as error: result = {'status': 'REJECTED', 'reason': str(error)}
        self.assertEqual(result.get('S12_feature'), 'OFF')

    def test_candidate_build_off_has_no_feature_define(self):
        self.assertEqual(self.recipe('OFF')['S12_feature'], 'OFF')

    def test_candidate_build_on_has_exact_one_feature_define(self):
        self.assertEqual(self.recipe('ON')['S12_feature'], 'ON')

    def test_on_missing_abi_define_rejected(self):
        with self.assertRaisesRegex(ValueError, 'ABI'):
            self.recipe('ON', definition=False)

    def test_on_duplicate_abi_define_rejected(self):
        with self.assertRaisesRegex(ValueError, 'ABI'):
            self.recipe('ON', extra='-DFORGE_NNUE_LAZY_ACC=1')

    def test_off_forced_abi_define_rejected(self):
        with self.assertRaisesRegex(ValueError, 'ABI'):
            self.recipe('OFF', extra='-DFORGE_NNUE_LAZY_ACC=1')

    def test_unrelated_feature_define_rejected(self):
        with self.assertRaisesRegex(ValueError, 'ABI'):
            self.recipe('OFF', extra='-DFORGE_NNUE_INT16=1')


if __name__ == '__main__':
    unittest.main(verbosity=2)
