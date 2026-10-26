import importlib.util
from pathlib import Path
import shlex
import unittest

spec=importlib.util.spec_from_file_location('build',Path(__file__).with_name('forge_sol_S09_build_native_20261026.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class BuildTests(unittest.TestCase):
    def test_generated_public_ffp_contract_duplicate_is_identical(self):
        tokens=[str(m.owned.CXX),*m.FLAGS.split(),'-O3','-DNDEBUG','-std=gnu++20','-ffp-contract=off','-c','fixture.cpp']
        m.strict_tokens(tokens)

    def test_bad_math_isa_profile_macro_and_standard_overrides_refused(self):
        base=[str(m.owned.CXX),*m.FLAGS.split(),'-O3','-DNDEBUG','-std=c++20']
        for bad in ('-ffp-contract=fast','-march=native','-mtune=generic','-ffast-math','-flto','-fprofile-use','-DFORGE_PROF=1','-UFORGE_NNUE_HIDDEN','-std=c++17','-Ofast','-O2'):
            with self.subTest(bad=bad),self.assertRaises(ValueError):m.strict_tokens(base+[bad])

    def test_manual_driver_is_observed_source_and_core_with_lock_flags(self):
        source=Path('/unit/source');core=Path('/unit/core.a');driver=Path('/unit/parity.cpp');dest=Path('/unit/parity')
        command=m.manual_command(source,core,driver,dest)
        m.strict_tokens(command)
        self.assertEqual(command.count(str(driver)),1)
        self.assertEqual(command.count(str(core)),1)
        self.assertEqual(command[-2:],['-o',str(dest)])
        self.assertIn('-I/unit/source/include',command)

    def test_only_new_exact_tmp_descendants_allowed(self):
        self.assertTrue(m.permitted(m.TMP/'one'))
        for bad in (m.TMP,Path('/tmp/other'),Path('relative'),m.TMP/'..'/'bad'):
            with self.subTest(bad=bad):self.assertFalse(m.permitted(bad))


if __name__=='__main__':unittest.main(verbosity=2)
