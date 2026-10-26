import copy
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('supplement',Path(__file__).parent/'forge_sol_S10_ON_T2_asan_20261026.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
BASE={'status':'REJECTED_SEARCH_SCREEN','release':{'status':'PASS','bench':{'first_bare11':308972},'ctest':{'inventory_status':'PASS'},'runtime_artifacts_unchanged':True}}
BASE['asan_ubsan']=copy.deepcopy(BASE['release'])
class ClosedGate(unittest.TestCase):
 def test_closed_correctness_even_when_WAC_fails(self):m.verified_status(BASE)
 def test_running_not_accepted(self):
  d=copy.deepcopy(BASE);d['status']='RUNNING'
  with self.assertRaises(ValueError):m.verified_status(d)
 def test_partial_asan_not_accepted(self):
  d=copy.deepcopy(BASE);d['asan_ubsan']['status']='FAIL'
  with self.assertRaises(ValueError):m.verified_status(d)
 def test_first_signature_missing_not_accepted(self):
  d=copy.deepcopy(BASE);d['release']['bench']['first_bare11']=1
  with self.assertRaises(ValueError):m.verified_status(d)
 def test_partial_ctest_inventory_not_accepted(self):
  d=copy.deepcopy(BASE);d['asan_ubsan']['ctest']={}
  with self.assertRaises(ValueError):m.verified_status(d)
if __name__=='__main__':unittest.main()
