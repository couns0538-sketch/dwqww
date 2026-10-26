"""Read-only safety checks; no compiler, CTest or engine subprocess runs."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('native',ROOT/'forge_sol_S10_native_controller_20261026.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
PROOF=json.loads((ROOT/'forge_sol_S10_patchcheck_v3_result_20261026.json').read_text())
DEPS=json.loads((ROOT/'forge_sol_S10_native_dependencies_20261026.json').read_text())
NET=m.load_checked(DEPS['ctest'],'ctest')
NATIVE=Path('/workspace/forge-pack24-20261026/S08/forge_sol_S08_B_SHARED_ASAN_FULL_NATIVE_20261026')
SOURCE=Path('/workspace/forge-pack24-20261026/S08/B_v2')
BUILD=Path('/workspace/forge-pack24-20261026/S08/forge_sol_S08_B_ASAN_SHARED_NODWARF_window1_20261026/build')

class NativeBindings(unittest.TestCase):
 def test_eight_exact_applied_source_views(self):
  for feature in ('singular_siblings','quiet_check_survival','improving_razor','capture_history_lmp'):
   for base in ('Lprime','B'):
    source,expected=m.select_source(PROOF,feature,base)
    self.assertEqual(m.verify_source(source,expected),expected)

 def test_missing_apply_step_rejected(self):
  proof=copy.deepcopy(PROOF)
  proof['rows']=[r for r in proof['rows'] if not (r.get('kind')=='GNUdry' and r.get('feature')=='singular_siblings' and r.get('base')=='B')]
  with self.assertRaises(ValueError):m.select_source(proof,'singular_siblings','B')

 def test_changed_file_rejected(self):
  source,expected=m.select_source(PROOF,'singular_siblings','B')
  expected=dict(expected);expected['src/search.cpp']='0'*64
  with self.assertRaises(ValueError):m.verify_source(source,expected)

 def test_dependency_mutation_rejected_before_exec(self):
  with tempfile.TemporaryDirectory() as temp:
   p=Path(temp)/'helper.py';p.write_text("raise AssertionError('must not execute')\n")
   with self.assertRaises(ValueError):m.load_checked({'path':str(p),'sha256':'0'*64},'bad')

 def inventory(self):return NET.load_ctest_inventory(NATIVE/'discovery.stdout',SOURCE,BUILD)

 def test_original_sixteen_ctest_command_bindings(self):
  inventory=self.inventory()
  actual=m.configured_commands(inventory,SOURCE,BUILD,inventory['commands']['uci_regression'][0])
  self.assertEqual(len(actual),16)
  self.assertIn('forge_bad_capture_tests',actual)

 def test_native_target_swap_rejected(self):
  inventory=self.inventory();inventory['commands']['forge_tests'][0]=str(BUILD/'forge_tt_tests')
  with self.assertRaises(ValueError):m.configured_commands(inventory,SOURCE,BUILD,inventory['commands']['uci_regression'][0])

 def test_python_suite_other_engine_rejected(self):
  inventory=self.inventory()
  inventory['commands']['uci_regression']=[s.replace(str(BUILD/'forge'),str(BUILD/'forge_tests')) for s in inventory['commands']['uci_regression']]
  with self.assertRaises(ValueError):m.configured_commands(inventory,SOURCE,BUILD,inventory['commands']['uci_regression'][0])

 def test_extra_configured_case_cannot_be_omitted(self):
  inventory=self.inventory();raw=json.loads((NATIVE/'discovery.stdout').read_text())
  raw['tests']=[case for case in raw['tests'] if case['name']!='forge_bad_capture_tests']
  with tempfile.TemporaryDirectory() as temp:
   p=Path(temp)/'partial.json';p.write_text(json.dumps(raw))
   with self.assertRaises(ValueError):NET.load_ctest_inventory(p,SOURCE,BUILD)

 def test_original_junit_full_inventory(self):
  inventory=self.inventory();allow=NET.bind_allowlist(json.loads(Path(DEPS['allowlist']['path']).read_text()),m.TESTS_SHA,m.NET_SHA)
  allow['required_groups']={'WAC001_move':1,'WAC001_score':1,'promotion_white':1,'promotion_black':1,'promotion_legacy':0}
  result=NET.check_ctest(NATIVE/'forge_sol_S08_B_shared_ASAN_full16_20261026.xml',0,allow,expected_names=inventory['expected_names'])
  self.assertEqual(len(result['test_cases']),16)

if __name__=='__main__':unittest.main()
