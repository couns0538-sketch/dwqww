"""Pure adapter config/frozen-source/recipe tests; never compile or run Forge."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE=Path(__file__).with_name('forge_sol_S08_release_after_timing_20261026.py')

class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(MODULE.is_file(),'post-timing Release adapter missing')
        spec=importlib.util.spec_from_file_location('releaseadapter',MODULE)
        self.api=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.api)
    def test_ON_canonical_Release_and_OFF_omits_option(self):
        args=self.api.configure_args(Path('/src'),Path('/new'),True)
        for expected in ('-DCMAKE_BUILD_TYPE=Release','-DFORGE_NATIVE=OFF','-DFORGE_PROF=ON','-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF'):
            self.assertIn(expected,args)
        self.assertFalse(any('SANITIZERS=ON' in x for x in args))
        self.assertFalse(any('FORGE_PROF=' in x for x in self.api.configure_args(Path('/src'),Path('/off'),False)))
    def test_frozen_source_change_blocks_configuration(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'a').write_text('old')
            frozen={'source':str(root),'source_sha256':self.api.shared.snapshot(root),'compiler_sha256':self.api.shared.CXX_SHA}
            self.api.verify_source(frozen)
            (root/'a').write_text('new')
            with self.assertRaisesRegex(ValueError,'frozen source changed'):self.api.verify_source(frozen)
    def test_recipe_rejects_optimization_override_and_sanitizer(self):
        safe=[str(self.api.shared.CXX),*self.api.shared.FLAGS.split(),'-O3','-DNDEBUG','-std=c++20','-DFORGE_PROF=1']
        self.api.check_tokens(safe,True)
        for bad in ('-O2','-fsanitize=address,undefined','-ffast-math','-funsafe-math-optimizations','-flto'):
            with self.subTest(flag=bad),self.assertRaises(ValueError):self.api.check_tokens(safe+[bad],True)
        with self.assertRaises(ValueError):self.api.check_tokens(safe,False)

if __name__=='__main__':unittest.main(verbosity=2)
