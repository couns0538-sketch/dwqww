"""Pure B-only qualification bindings and frozen-helper equivalence."""
import ast
import importlib.util
from pathlib import Path
import re
import unittest
MODULE=Path(__file__).with_name('forge_sol_S08_B_qualify_20261026.py')
BASE=Path(__file__).with_name('forge_sol_S08_v2_qualify_20261026.py')
class BQualificationTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(MODULE.is_file(),'B qualifier missing')
        spec=importlib.util.spec_from_file_location('bqualify',MODULE);self.api=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.api)
    def test_full16_accepts_and_full15_rejects_without_changing_known_policy(self):
        text='\n'.join('1: '+line for line in self.api.KNOWN)+'\n100% tests passed, 0 tests failed out of 16\n'
        self.assertEqual(self.api.verify_ctest(text,0)['registered_tests'],16)
        with self.assertRaises(ValueError):self.api.verify_ctest(text.replace('out of 16','out of 15'),0)
        for valid in (101,607,642,12345):self.api.verify_ctest(text.replace('score 642 at d1',f'score {valid} at d1'),0)
        with self.assertRaises(ValueError):self.api.verify_ctest(text.replace('score 642 at d1','score 100 at d1'),0)
    def test_fixed_B_source_binding_and_pending_or_explicit_ELF_pin(self):
        self.assertEqual(self.api.FREEZE_SHA,'fcd93778dc3bae5bed2f941c9ee0fff08f6ee07ce6ecf22bf82a007e8a8904d7')
        self.assertEqual(self.api.KNOWN_SOURCE,MODULE.parent/'B_v2/tests/tests.cpp')
        self.assertTrue(self.api.ELF_SHA=='UNBUILT_B_ON_ELF_PIN' or re.fullmatch('[0-9a-f]{64}',self.api.ELF_SHA))
    def test_all_native_process_bench_perft_UCI_EOF_FMA_helpers_are_identical(self):
        get=lambda p:{x.name:ast.dump(x,include_attributes=False) for x in ast.parse(p.read_text()).body if isinstance(x,(ast.FunctionDef,ast.ClassDef))}
        before,after=get(BASE),get(MODULE)
        self.assertEqual(set(before),set(after))
        for name in before.keys()-{'verify_ctest','main'}:
            with self.subTest(helper=name):self.assertEqual(before[name],after[name])
if __name__=='__main__':unittest.main(verbosity=2)
