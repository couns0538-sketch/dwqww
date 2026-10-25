#!/usr/bin/env python3
"""Pure synthetic source/metadata fixtures; no native or live AUTO-LOCK claim."""
import copy,hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent; CODE=HERE/'forge_sol_S28_v2_audit_checks_20261025.py'
mod=None
if CODE.exists():
 spec=importlib.util.spec_from_file_location('audit',CODE);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

class AuditTests(unittest.TestCase):
 def test_implementation_present(self):self.assertIsNotNone(mod,'S47 audit APIs have not been implemented')
 def setUp(self):
  if mod is None:
   if self._testMethodName=='test_implementation_present':return
   self.skipTest('Implementation absence recorded by presence test')
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.old=self.root/'old';self.new=self.root/'new'
  for base,net in [(self.old,b'old net\n'),(self.new,b'new net\n')]:
   (base/'src').mkdir(parents=True);(base/'src/search.cpp').write_bytes(b'unchanged search\n');(base/'src/nnue_weights.inc').write_bytes(net);(base/'README.md').write_bytes(b'read me\n')
  self.md5=hashlib.md5(b'new net\n').hexdigest();h='a'*64
  snap={q.relative_to(self.old).as_posix():hashlib.sha256(q.read_bytes()).hexdigest() for q in self.old.rglob('*') if q.is_file()}
  self.packet={'old_before':dict(snap),'old_after':dict(snap),'old_lock_dir':str(self.old),'new_lock_dir':str(self.new),'new_dir_existed_before':False,'candidate_net_md5':self.md5,'gated_net_md5':self.md5,'candidate_exe_sha256':h,'gated_exe_sha256':h,'candidate_build_flavour':'Release exposeOFF','gated_build_flavour':'Release exposeOFF','bench_reference_sha256':'b'*64,'bench_expected':{'11':1,'13':2,'16':3,'20':4,'22':5},'bench_first':{'11':1,'13':2,'16':3,'20':4,'22':5},'bench_repeat':{'11':1,'13':2,'16':3,'20':4,'22':5},'perft5':4865609,'kiwipete5':193690690,'whole_executable_fma':0,'uci_before':{'build_flavour':'Release exposeOFF','options':['option name Hash type spin default 16 min 1 max 1024']},'uci_after':{'build_flavour':'Release exposeOFF','options':['option name Hash type spin default 16 min 1 max 1024']},'gate':{'srand':10,'start':1},'confirm':{'srand':11,'start':2},'pins_before':{'WAC_score':661},'pins_after':{'WAC_score':661}}
 def verdict(self,p=None):return mod.audit_packet(self.packet if p is None else p)
 def test_netonly_green(self):self.assertEqual(mod.netonly_tree(self.old,self.new,self.md5)['status'],'PASS')
 def test_crlf_green(self):
  (self.new/'src/search.cpp').write_bytes(b'unchanged search\r\n');self.assertEqual(mod.netonly_tree(self.old,self.new,self.md5)['status'],'PASS')
 def test_b_against_l_red(self):
  (self.new/'src/search.cpp').write_bytes(b'buffer fix\n');self.assertEqual(mod.netonly_tree(self.old,self.new,self.md5)['status'],'FAIL')
 def test_added_path_red(self):
  (self.new/'surprise').write_bytes(b'x');self.assertEqual(mod.netonly_tree(self.old,self.new,self.md5)['status'],'FAIL')
 def test_empty_directory_red(self):
  (self.new/'surprise_dir').mkdir();self.assertEqual(mod.netonly_tree(self.old,self.new,self.md5)['status'],'FAIL')
 def test_symlink_red(self):
  (self.new/'link').symlink_to(self.old/'README.md');self.assertEqual(mod.netonly_tree(self.old,self.new,self.md5)['status'],'FAIL')
 def test_complete_packet_green(self):
  result=self.verdict();self.assertEqual(result['status'],'PASS');self.assertEqual(len(result['checks']),11);self.assertFalse(result['live_autolock_verified']);self.assertTrue(result['missing_spec_inputs'])
 def test_edited_pin_red(self):self.packet['pins_after']['WAC_score']=629;self.assertEqual(self.verdict()['status'],'FAIL')
 def reviewed_packet(self):
  self.packet['pins_after']['WAC_score']=629;self.packet['reviewed_pin_diff']={'review_sha256':'c'*64,'patch_sha256':'d'*64,'changes':[{'key':'WAC_score','before':661,'after':629}],'expected_file_changes':[{'path':'tests/tests.cpp','before_sha256':'e'*64,'after_sha256':'f'*64}]};self.packet['file_changes']=copy.deepcopy(self.packet['reviewed_pin_diff']['expected_file_changes']);self.packet['applied_pin_patch_sha256']='d'*64
 def test_reviewed_pin_green(self):self.reviewed_packet();self.assertEqual(self.verdict()['status'],'PASS')
 def test_reviewed_file_extra_red(self):
  self.reviewed_packet();self.packet['file_changes'].append({'path':'src/search.cpp','before_sha256':'a'*64,'after_sha256':'b'*64});self.assertEqual(self.verdict()['status'],'FAIL')
 def test_reviewed_patch_wrong_red(self):
  self.reviewed_packet();self.packet['applied_pin_patch_sha256']='a'*64;self.assertEqual(self.verdict()['status'],'FAIL')
 def test_raw_reviewed_delta_not_netonly(self):
  self.reviewed_packet();(self.new/'README.md').write_bytes(b'reviewed pin notes\n');before=hashlib.sha256((self.old/'README.md').read_bytes()).hexdigest();after=hashlib.sha256((self.new/'README.md').read_bytes()).hexdigest();rows=[{'path':'README.md','before_sha256':before,'after_sha256':after}];self.packet['file_changes']=rows;self.packet['reviewed_pin_diff']['expected_file_changes']=copy.deepcopy(rows);result=self.verdict();self.assertEqual(result['part_b_status'],'PASS');self.assertEqual(result['strict_netonly_status'],'FAIL');self.assertEqual(result['status'],'FAIL');self.assertEqual(result['classification'],'REVIEWED_DELTA')
 def test_unreviewed_file_beats_missing_pins(self):
  del self.packet['pins_before'];self.packet['file_changes']=[{'path':'tests/tests.cpp','before_sha256':'e'*64,'after_sha256':'f'*64}];self.assertEqual(self.verdict()['status'],'FAIL')
 def test_wrong_reviewed_pin_red(self):
  self.packet['pins_after']['WAC_score']=629;self.packet['reviewed_pin_diff']={'review_sha256':'c'*64,'changes':[{'key':'WAC_score','before':661,'after':628}]};self.assertEqual(self.verdict()['status'],'FAIL')
 def test_reviewed_pin_missing_files_red(self):
  self.packet['pins_after']['WAC_score']=629;self.packet['reviewed_pin_diff']={'review_sha256':'c'*64,'changes':[{'key':'WAC_score','before':661,'after':629}]};self.assertEqual(self.verdict()['status'],'FAIL')
 def test_old_partial_manifest_red(self):
  self.packet['old_before']={'src/search.cpp':self.packet['old_before']['src/search.cpp']};self.packet['old_after']=dict(self.packet['old_before']);self.assertEqual(self.verdict()['status'],'FAIL')
 def test_old_stale_manifest_red(self):
  (self.old/'README.md').write_bytes(b'changed after manifest\n');self.assertEqual(self.verdict()['status'],'FAIL')
 def test_one_node_red(self):self.packet['bench_repeat']['16']+=1;self.assertEqual(self.verdict()['status'],'FAIL')
 def test_reused_srand_red(self):self.packet['confirm']['srand']=10;self.assertEqual(self.verdict()['status'],'FAIL')
 def test_reused_start_red(self):self.packet['confirm']['start']=1;self.assertEqual(self.verdict()['status'],'FAIL')
 def test_missing_unverified(self):del self.packet['gate'];self.assertEqual(self.verdict()['status'],'UNVERIFIED')
 def test_fail_beats_missing(self):del self.packet['gate'];self.packet['pins_after']['WAC_score']=1;self.assertEqual(self.verdict()['status'],'FAIL')
 def test_bool_not_integer(self):self.packet['whole_executable_fma']=False;self.assertEqual(self.verdict()['status'],'FAIL')
 def test_flavour_red(self):self.packet['uci_after']['build_flavour']='Release exposeON';self.assertEqual(self.verdict()['status'],'FAIL')
 def test_snapshot_red(self):self.packet['old_after']['src/search.cpp']='d'*64;self.assertEqual(self.verdict()['status'],'FAIL')
 def test_missing_tree_unverified(self):self.packet['new_lock_dir']=str(self.root/'missing');self.assertEqual(self.verdict()['status'],'UNVERIFIED')
 def test_bool_bench_red(self):self.packet['bench_first']['11']=True;self.assertEqual(self.verdict()['status'],'FAIL')
 def test_bool_seed_red(self):self.packet['confirm']['srand']=False;self.assertEqual(self.verdict()['status'],'FAIL')
 def test_pin_bool_drift_red(self):self.packet['pins_after']['WAC_score']=True;self.assertEqual(self.verdict()['status'],'FAIL')
 def test_executable_red(self):self.packet['gated_exe_sha256']='d'*64;self.assertEqual(self.verdict()['status'],'FAIL')
 def test_whole_fma_red(self):self.packet['whole_executable_fma']=1;self.assertEqual(self.verdict()['status'],'FAIL')
 def test_output_deterministic(self):self.assertEqual(json.dumps(self.verdict(),sort_keys=True),json.dumps(self.verdict(),sort_keys=True))

if __name__=='__main__':unittest.main(verbosity=2)
