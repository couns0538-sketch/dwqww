"""Pure controls of reviewed gaps; old adapter must fail the new requirements."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import resource
import unittest

ROOT=Path(__file__).parent
TARGET=Path(os.environ.get('S10_T2_ADAPTER',str(ROOT/'forge_sol_S10_ON_T2_asan_v2_20261026.py')))
spec=importlib.util.spec_from_file_location('adapter',TARGET);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
RELEASE=json.loads(Path('/tmp/forge_sol_S10_native_20261026/quiet_check_survival_Lprime_once/release/progress.json').read_text())
MINIMAL={'status':'REJECTED_SEARCH_SCREEN','release':{'status':'PASS','bench':{'first_bare11':308972},'ctest':{'inventory_status':'PASS'},'runtime_artifacts_unchanged':True}}
MINIMAL['asan_ubsan']=copy.deepcopy(MINIMAL['release'])
OPTION='QuietCheckLmpSurvival'
VALID_STREAM='option name '+OPTION+' type check default false\nuciok\ninfo string '+OPTION+' active\nbestmove a2a3\nbestmove a2a3\nbestmove a2a3\n'
def document():
 d={'status':'REJECTED_SEARCH_SCREEN','controller_sha256':m.CONTROLLER_SHA,'source_unchanged':True,'feature':{'option':OPTION},'base':'Lprime','release':copy.deepcopy(RELEASE),'asan_ubsan':copy.deepcopy(RELEASE)}
 a=d['asan_ubsan'];a['asan']=True
 a['bench']['off']={'11':308972};a['bench']['on']={'11':RELEASE['bench']['on']['11']}
 for key in ('perft5','compile_OFF_proof','node_screen'):a.pop(key,None)
 return d

class ProofControls(unittest.TestCase):
 def test_real_release_schema_and_asan_schema_shape(self):m.verified_status(document())
 def test_minimal_sentinels_do_not_prove_Std(self):
  with self.assertRaises(ValueError):m.verified_status(MINIMAL)
 def test_wrong_producer_rejected(self):
  d=document();d['controller_sha256']='0'*64
  with self.assertRaises(ValueError):m.verified_status(d)
 def test_perft_omission_rejected(self):
  d=document();d['release'].pop('perft5')
  with self.assertRaises(ValueError):m.verified_status(d)
 def test_configured_test_omission_rejected(self):
  d=document();d['asan_ubsan']['ctest']['test_cases'].pop()
  with self.assertRaises(ValueError):m.verified_status(d)
 def test_missing_active_rejected(self):
  with self.assertRaises(ValueError):
   if hasattr(m,'verify_active'):m.verify_active(VALID_STREAM.replace('info string '+OPTION+' active\n',''),OPTION)
 def test_late_active_rejected(self):
  text=VALID_STREAM.replace('info string '+OPTION+' active\n','')+'info string '+OPTION+' active\n'
  with self.assertRaises(ValueError):
   if hasattr(m,'verify_active'):m.verify_active(text,OPTION)
 def test_clipped_AS_rejected(self):
  with self.assertRaises(ValueError):
   if hasattr(m,'verify_limits'):m.verify_limits((1<<30,resource.RLIM_INFINITY))
 def test_valid_stream_and_unlimited_AS(self):
  if hasattr(m,'verify_active'):m.verify_active(VALID_STREAM,OPTION)
  if hasattr(m,'verify_limits'):m.verify_limits((resource.RLIM_INFINITY,resource.RLIM_INFINITY))
if __name__=='__main__':unittest.main()
