#!/usr/bin/env python3
"""Original pure contract fixtures; these are not native engine observations."""
import argparse,copy,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
sys.dont_write_bytecode=True
LOCK='74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b'
CAND='0fdf9bdb6bdf4c9f1622bcef29921912acb139fdf388e541b017a948118d4661'
REASON=' (h256_e12 net-evaluation horizon; original 6.4.24 expectation retained)'
PROM='unrestricted search chooses the winning rook underpromotion over stalemating queen promotion'
def pins(wac=661,promo=642,status='PASS'):
 rows=[]
 for case,move,depth,score in [('WAC001','f6h5',12,wac),('promotion_white','c6d7',1,promo),('promotion_black','c3d2',1,promo)]:rows.append({'case':case,'depth':depth,'requested_depth':depth,'score_kind':'cp','score':score,'bestmove':move,'pv':[move],'status':'OBSERVED','exit':0,'unclosed_pid':None,'stream_capture_complete':True})
 return {'status':status,'cases':rows}
def known(wac=661,promo=642):
 return ('KNOWN_FAILURE: WAC 001 expected g3g6 got f6h5'+REASON+'\nKNOWN_FAILURE: WAC 001 score expected >= 31997 got '+str(wac)+REASON+'\n'+''.join('KNOWN_FAILURE: '+PROM+' expected '+rook+' score > 100 at d1 got '+move+' score '+str(promo)+' at d1'+REASON+'\n' for rook,move in [('c7c8r','c6d7'),('c2c1r','c3d2')])).encode()
def pending():
 return ('PIN_MISMATCH: WAC 001 documented f6h5/661/d12/PV=f6h5, observed f6h5/629/d12/PV=f6h5; re-record Job C pins in a reviewed change if the lock changed\nFAIL: WAC 001 expected g3g6 got f6h5\nFAIL: WAC 001 score 629 below 31997\n').encode()+b'\n'.join(known(629,686).splitlines()[2:])+b'\n'
class Contracts(unittest.TestCase):
 def test_current_known4(self):self.assertEqual(M.known_failures(known(),LOCK,pins())['status'],'KNOWN4_PASS')
 def test_candidate_rerecorded_known4(self):self.assertEqual(M.known_failures(known(629,686),CAND,pins(629,686),documented_wac_score=629)['status'],'KNOWN4_PASS')
 def test_candidate_pending_is_proposed(self):self.assertEqual(M.known_failures(pending(),CAND,pins(629,686,status='RECORDED'),actual_exit=1)['status'],'PROPOSED_PIN_RERECORD_REQUIRED')
 def test_missing_known_fails(self):
  with self.assertRaises(ValueError):M.known_failures(b'\n'.join(known().splitlines()[:-1]),LOCK,pins())
 def test_extra_known_fails(self):
  with self.assertRaises(ValueError):M.known_failures(known()+known().splitlines()[0]+b'\n',LOCK,pins())
 def test_unrelated_fail_fails(self):
  with self.assertRaises(ValueError):M.known_failures(known()+b'FAIL: unrelated mate\n',LOCK,pins())
 def test_wac_score_drift_fails(self):
  with self.assertRaises(ValueError):M.known_failures(known(662),LOCK,pins())
 def test_promotion_score_drift_fails(self):
  with self.assertRaises(ValueError):M.known_failures(known(promo=643),LOCK,pins())
 def test_false_known_for_unrecorded_wac_fails(self):
  with self.assertRaises(ValueError):M.known_failures(known(629,686),CAND,pins(629,686))
 def test_fake_pin_observation_fails(self):
  bad=pins();bad['cases'][0]['pv']=['g3g6']
  with self.assertRaises(ValueError):M.known_failures(known(),LOCK,bad)
 def test_pending_pin_drift_fails(self):
  with self.assertRaises(ValueError):M.known_failures(pending().replace(b'observed f6h5/629',b'observed f6h5/630'),CAND,pins(629,686,status='RECORDED'),actual_exit=1)
 def test_wrong_exit_fails(self):
  with self.assertRaises(ValueError):M.known_failures(known(),LOCK,pins(),actual_exit=1)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--module',type=Path,required=True);ap.add_argument('--only-current',action='store_true');args=ap.parse_args();spec=importlib.util.spec_from_file_location('s28_contract_module',args.module);M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M);suite=unittest.TestSuite([Contracts('test_current_known4')]) if args.only_current else unittest.defaultTestLoader.loadTestsFromTestCase(Contracts);r=unittest.TextTestRunner(verbosity=2).run(suite);raise SystemExit(not r.wasSuccessful())
