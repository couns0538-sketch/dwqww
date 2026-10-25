#!/usr/bin/env python3
"""Synthetic-only authoritative-checklist fixtures; no engine or PC operation."""
import copy,hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent;CODE=HERE/'forge_sol_S28_v2_autolock_checklist_20261025.py';mod=None
if CODE.exists():
 spec=importlib.util.spec_from_file_location('autolock',CODE);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

class ChecklistTests(unittest.TestCase):
 def test_implementation_present(self):self.assertIsNotNone(mod,'New authoritative checker is not implemented')
 def artifact(self,name,data):
  p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);return {'path':str(p),'sha256':hashlib.sha256(data).hexdigest()}
 def setUp(self):
  if mod is None:
   if self._testMethodName=='test_implementation_present':return
   self.skipTest('Missing implementation asserted independently')
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
  script=self.artifact('fixture_script.txt',b'SYNTHETIC successor script snapshot, never executed\n');sh=script['sha256'];review=self.artifact('fixture_script_review.txt',('PASS successor '+sh+'\nSYNTHETIC FIXTURE ONLY, not a real CR review\n').encode());review.update(external=True,decision='PASS',script_sha256=sh)
  tag='AUTOLOCK_1_fixture';exe=hashlib.sha256(b'synthetic candidate executable identity only').hexdigest();oldexe='e3df99cddb609d9f00168d8df3187fdf6943c10812dd5c4f82206895e594367b'
  source=self.root/'old_sources';source.mkdir();(source/'source.cpp').write_bytes(b'synthetic immutable source\n');sourcehash={'source.cpp':hashlib.sha256((source/'source.cpp').read_bytes()).hexdigest()}
  backup=self.artifact('CURRENT_LOCK.json.bak_pre_fixture_0001',b'{"fixture":true}\n');gbackup=self.artifact('forge_gates.json.bak_rebuild_1_fixture',json.dumps({'gates':[{'tag':'started1','srand':5}]}).encode());cr=self.artifact('fixture_external_review.txt',('PASS '+tag+'\nSYNTHETIC FIXTURE ONLY, not a real CR_PASS\n').encode());cr.update(external=True,decision='PASS',lock_tag=tag,record_name='CR_PASS_AUTOLOCK_1.txt')
  ref={'11':1,'13':2,'16':3,'20':4,'22':5}
  self.packet={'synthetic_fixture':True,'event':'first','script':{'live_sha256':sh,'snapshot':script,'review':review,'no_autopromote_absent':True},'winner':{'parent':{'void_file_exists':False,'result_md':'H1','options_check':'PASS\n','candidate_sha256':exe},'confirm':{'void_file_exists':False,'result_md':'H1','options_check':'PASS\n','candidate_sha256':exe}},'race':{'g104c':'H1','cap_expired':False,'winner_id':'G104','winner_tag':'gate104_e48f006','g120_status':'PARKED-E32','rework_list':['G120'],'g120_rebase_gates':[],'g104_rebase_gates':[],'mode':'RH-Q1'},'lock':{'n':1,'tag':tag,'path':'locks\\'+tag,'directory_new':True,'orphan_lower_n_dirs':[],'exe_sha256':exe,'parent_tag':'h256_e12','kind':'net','tree_diff':['src\\nnue_weights.inc'],'net_md5':'0fae54a4c0c437432ddb5da85512b5f4','net_manifest_md5':'0fae54a4c0c437432ddb5da85512b5f4','pins_refs':{'3AECB403':'attached','5A4ED675':'attached'},'pins_applied':False,'gate_id':'G104','gate_tag':'gate104_e48f006','chain_id':'chain104'},'checks':{'perft5':4865609,'kiwipete5':193690690,'fma':0,'bench_reference_source':'gate.prebench.cand_off','bench_reference':dict(ref),'bench_first':dict(ref),'bench_repeat':dict(ref),'nps_ratio':0.7},'old_lock':{'exe_before_sha256':oldexe,'exe_after_sha256':oldexe,'sources_before':sourcehash,'sources_after':dict(sourcehash),'source_snapshot':str(source),'read_only_attributes_only':True,'pointer_backup':backup,'steps':[{'action':'CREATE','tag':tag,'hashes':{'exe_sha256':exe}},{'action':'POINTER','tag':tag,'hashes':{'exe_sha256':exe}}]},'state':{'promotes_last_tag':tag,'pointer_tag':tag,'seen':{'gate104_e48f006':'PROMOTED'},'datagen_pending':True,'combine_list':[]},'gates':{'manifest_backup':gbackup,'rebuilt_net':[{'id':'net-next','notes':'REBUILT on synthetic date','before_srand':1,'srand':2,'base_override':tag,'ag_prev':{'fixture':'old'}}],'search_option':[{'id':'search-next','kind':'search','label':'search-next vs h256_e12'}],'started_before':{'started1':{'tag':'started1','srand':5}},'started_after':{'started1':{'tag':'started1','srand':5}}},'high2':{'all_chains_inspected':True,'chains':[{'id':'chain104','double_h1':True,'seen_status':'PROMOTED','seen_reason':''}]},'datagen':{'switch_completed':True,'file_boundary':True,'nps_ratio':1.0,'trainer_before_sha256':'a'*64,'trainer_after_sha256':'a'*64},'cr':{'chained_without_cr':1,'external_pass':cr},'post_promote':{'inflight':None,'alerts_lines':[]}}
 def result(self):return mod.audit_autolock(self.packet)
 def test_all_synthetic_green(self):
  r=self.result();self.assertEqual(r['status'],'PASS');self.assertEqual(len(r['checks']),11);self.assertFalse(r['live_pc_verified']);self.assertFalse(r['writes_cr_pass'])
 def test_01_wrong_script_snapshot_red(self):self.packet['script']['live_sha256']='a'*64;self.assertEqual(self.result()['status'],'FAIL')
 def test_01_known_prefix_only_unverified(self):
  self.packet['script']['live_sha256']='896663B0';del self.packet['script']['snapshot'];self.assertEqual(self.result()['checks'][0]['status'],'UNVERIFIED')
 def test_02_void_red(self):self.packet['winner']['confirm']['void_file_exists']=True;self.assertEqual(self.result()['status'],'FAIL')
 def test_02_final_options_red(self):self.packet['winner']['confirm']['options_check']='PASS\nFAIL\n';self.assertEqual(self.result()['status'],'FAIL')
 def test_03_wrong_winner_red(self):self.packet['race']['winner_id']='G120';self.assertEqual(self.result()['status'],'FAIL')
 def test_04_applied_pins_red(self):self.packet['lock']['pins_applied']=True;self.assertEqual(self.result()['status'],'FAIL')
 def test_04_not_netonly_red(self):self.packet['lock']['tree_diff'].append('tests/tests.cpp');self.assertEqual(self.result()['status'],'FAIL')
 def test_04_missing_pin_refs_unverified(self):self.packet['lock']['pins_refs']={};self.assertEqual(self.result()['status'],'UNVERIFIED')
 def test_04_wrong_directory_component_red(self):self.packet['lock']['path']='badlocks\\'+self.packet['lock']['tag'];self.assertEqual(self.result()['status'],'FAIL')
 def test_06_missing_source_snapshot_unverified(self):self.packet['old_lock']['source_snapshot']=str(self.root/'missing_source');self.assertEqual(self.result()['status'],'UNVERIFIED')
 def test_06_invalid_matching_step_hashes_red(self):
  for row in self.packet['old_lock']['steps']:row['hashes']={'exe_sha256':True}
  self.assertEqual(self.result()['status'],'FAIL')
 def test_05_missing_advisory_NPS_warn_only(self):del self.packet['checks']['nps_ratio'];self.assertEqual(self.result()['status'],'PASS')
 def test_05_node_drift_red(self):self.packet['checks']['bench_repeat']['16']+=1;self.assertEqual(self.result()['status'],'FAIL')
 def test_05_missing_reference_but_repeat_drift_red(self):del self.packet['checks']['bench_reference'];self.packet['checks']['bench_repeat']['16']+=1;self.assertEqual(self.result()['status'],'FAIL')
 def test_05_nps_only_warns(self):self.packet['checks']['nps_ratio']=0.5;self.assertEqual(self.result()['status'],'PASS')
 def test_06_old_sources_red(self):self.packet['old_lock']['sources_after']['source.cpp']='b'*64;self.assertEqual(self.result()['status'],'FAIL')
 def test_07_state_red(self):self.packet['state']['pointer_tag']='wrong';self.assertEqual(self.result()['status'],'FAIL')
 def test_08_started_edited_red(self):self.packet['gates']['started_after']['started1']['srand']=99;self.assertEqual(self.result()['status'],'FAIL')
 def test_09_high2_red(self):self.packet['high2']['chains'][0].update(seen_status='INELIGIBLE',seen_reason='RUN_INFO.json missing');self.assertEqual(self.result()['status'],'FAIL')
 def test_10_trainer_red(self):self.packet['datagen']['trainer_after_sha256']='b'*64;self.assertEqual(self.result()['status'],'FAIL')
 def test_10_nps_red(self):self.packet['datagen']['nps_ratio']=0.89;self.assertEqual(self.result()['status'],'FAIL')
 def test_11_missing_external_cr_unverified(self):del self.packet['cr']['external_pass'];self.assertEqual(self.result()['status'],'UNVERIFIED')
 def test_11_three_without_cr_red(self):self.packet['cr']['chained_without_cr']=3;del self.packet['cr']['external_pass'];self.assertEqual(self.result()['status'],'FAIL')
 def test_post_inflight_red(self):self.packet['post_promote']['inflight']={};self.assertEqual(self.result()['status'],'FAIL')
 def test_post_alert_red(self):self.packet['post_promote']['alerts_lines']=['inflight_timeout'];self.assertEqual(self.result()['status'],'FAIL')
 def test_bool_integer_red(self):self.packet['checks']['perft5']=True;self.assertEqual(self.result()['status'],'FAIL')
 def test_missing_plus_contradiction_red(self):del self.packet['script'];self.packet['lock']['pins_applied']=True;self.assertEqual(self.result()['status'],'FAIL')
 def test_missing_packet_unverified(self):self.assertEqual(mod.audit_autolock(None)['status'],'UNVERIFIED')
 def cap(self,status='PENDING',expired=True):
  p=self.packet;p['race'].update(g104c=status,cap_expired=expired,winner_id='G120',winner_tag='gate120_e32',rework_list=['G104'],g104_rebase_gates=['gate104_e48f006_rebase_vs_AL1'] if expired else[]);p['lock'].update(gate_id='G120',gate_tag='gate120_e32',chain_id='chain120',net_md5=hashlib.md5(b'synthetic e32').hexdigest(),net_manifest_md5=hashlib.md5(b'synthetic e32').hexdigest());p['state']['seen']={'gate120_e32':'PROMOTED'}
  if expired:p['cap_late']={'z2_enabled':True,'queued_gate':'gate104_e48f006_rebase_vs_AL1','ag_rebase_exempt24':True,'srand':7,'original_srand':6,'conc':5,'g104c_current':'PENDING','queue_status':'HELD','crew_alert':{'level':'INFO','visible':True}}
 def test_G104_H0_green(self):self.cap('H0',False);self.assertEqual(self.result()['status'],'PASS')
 def test_G104_capped_green(self):self.cap('CAPPED',False);self.assertEqual(self.result()['status'],'PASS')
 def test_cap_green(self):self.cap();self.assertEqual(self.result()['status'],'PASS')
 def test_cap_conc_red(self):self.cap();self.packet['cap_late']['conc']=7;self.assertEqual(self.result()['status'],'FAIL')
 def test_cap_not_HELD_red(self):self.cap();self.packet['cap_late']['queue_status']='QUEUED';self.assertEqual(self.result()['status'],'FAIL')
 def test_fallback_note_green(self):self.cap();self.packet['race']['mode']='RH-Q1 FALLBACK';self.packet['fallback']={'crew_visible_note':'synthetic visible note'};self.assertEqual(self.result()['status'],'PASS')
 def test_fallback_missing_note_unverified(self):self.cap();self.packet['race']['mode']='RH-Q1 FALLBACK';self.assertEqual(self.result()['status'],'UNVERIFIED')
 def later(self):
  self.cap();p=self.packet;p['event']='later_cap_late';p['lock'].update(n=2,tag='AUTOLOCK_2_fixture',path='locks\\AUTOLOCK_2_fixture',parent_tag='AUTOLOCK_1_fixture',kind='net',net_md5='0fae54a4c0c437432ddb5da85512b5f4',net_manifest_md5='0fae54a4c0c437432ddb5da85512b5f4',gate_id='G104_REBASE',gate_tag='gate104_e48f006_rebase_vs_AL1',chain_id='chain104-rebase');p['cap_late'].update(g104c_current='H1',queue_status='PROMOTED',later_promote_logged=True,log_kind='net',log_parent_tag='AUTOLOCK_1_fixture');p['state'].update(promotes_last_tag=p['lock']['tag'],pointer_tag=p['lock']['tag'],seen={'gate104_e48f006_rebase_vs_AL1':'PROMOTED'});p['gates']['rebuilt_net'][0]['base_override']=p['lock']['tag']
  for row in p['old_lock']['steps']:row['tag']=p['lock']['tag']
  cr=self.artifact('fixture_later_external_review.txt',('PASS '+p['lock']['tag']+'\nSYNTHETIC FIXTURE ONLY, not a real CR_PASS').encode());cr.update(external=True,decision='PASS',lock_tag=p['lock']['tag'],record_name='CR_PASS_AUTOLOCK_2.txt');p['cr']['external_pass']=cr

 def test_later_CAP_LATE_green(self):self.later();self.assertEqual(self.result()['status'],'PASS')
 def test_peer_f006_wrong_net_red(self):
  self.packet['lock']['net_md5']='b'*32;self.packet['lock']['net_manifest_md5']='b'*32;del self.packet['lock']['pins_refs'];del self.packet['lock']['pins_applied'];self.assertEqual(self.result()['status'],'FAIL')
 def test_peer_f006_kind_bypass_red(self):self.packet['lock']['kind']='search';self.packet['lock']['tree_diff'].append('tests/tests.cpp');self.assertEqual(self.result()['status'],'FAIL')
 def test_peer_later_wrong_gate_red(self):self.later();self.packet['lock']['gate_tag']='gate120_e32';self.assertEqual(self.result()['status'],'FAIL')
 def test_peer_first_wrong_gate_id_red(self):self.packet['lock']['gate_id']='G120';self.packet['state']['seen']={'G120':'PROMOTED'};self.assertEqual(self.result()['status'],'FAIL')
 def test_peer_external_CR_raw_FAIL_red(self):
  data=self.artifact('fixture_CR_raw_FAIL.txt',('FAIL '+self.packet['lock']['tag']+' synthetic').encode());self.packet['cr']['external_pass'].update(data);self.assertEqual(self.result()['status'],'FAIL')
 def test_peer_successor_review_raw_FAIL_red(self):
  data=self.artifact('fixture_script_review_FAIL.txt',('FAIL successor '+self.packet['script']['live_sha256']).encode());self.packet['script']['review'].update(data);self.assertEqual(self.result()['status'],'FAIL')
 def test_peer_CR_ambiguous_unverified(self):
  data=self.artifact('fixture_CR_ambiguous.txt',('Unclassified historical text '+self.packet['lock']['tag']).encode());self.packet['cr']['external_pass'].update(data);self.assertEqual(self.result()['status'],'UNVERIFIED')
 def test_peer_actual_backup_contradiction_red(self):
  self.packet['gates']['manifest_backup']=self.artifact('forge_gates.json.bak_rebuild_1_changed',json.dumps({'gates':[{'tag':'started1','srand':99}]}).encode());self.assertEqual(self.result()['status'],'FAIL')
 def test_peer_matching_wrong_steps_red(self):
  for row in self.packet['old_lock']['steps']:row['hashes']={'exe_sha256':'b'*64}
  self.assertEqual(self.result()['status'],'FAIL')
 def test_peer_cap_and_terminal_decision_red(self):
  original=copy.deepcopy(self.packet);self.cap();late=self.packet['cap_late'];self.packet=original;self.packet['race']['cap_expired']=True;self.packet['cap_late']=late;self.assertEqual(self.result()['status'],'FAIL')
 def test_peer_missing_lock_exe_but_candidates_differ_red(self):
  del self.packet['lock']['exe_sha256'];self.packet['winner']['confirm']['candidate_sha256']='b'*64;self.assertEqual(self.result()['status'],'FAIL')
 def test_peer_missing_locktag_but_state_differs_red(self):
  del self.packet['lock']['tag'];self.packet['state']['pointer_tag']='wrong';self.assertEqual(self.result()['status'],'FAIL')
 def test_peer_missing_locktag_only_unverified(self):del self.packet['lock']['tag'];self.assertEqual(self.result()['status'],'UNVERIFIED')
 def test_peer_missing_old_before_wrong_after_red(self):
  del self.packet['old_lock']['exe_before_sha256'];self.packet['old_lock']['exe_after_sha256']='b'*64;self.assertEqual(self.result()['status'],'FAIL')
 def test_peer_uppercase_hashes_green(self):
  self.packet['old_lock']['steps'][0]['hashes']['exe_sha256']=self.packet['lock']['exe_sha256'].upper();self.packet['lock']['net_md5']=self.packet['lock']['net_md5'].upper();self.packet['lock']['net_manifest_md5']=self.packet['lock']['net_manifest_md5'].upper();self.assertEqual(self.result()['status'],'PASS')
 def test_peer_lowercase_refs_green(self):self.packet['lock']['pins_refs']={k.lower():v for k,v in self.packet['lock']['pins_refs'].items()};self.assertEqual(self.result()['status'],'PASS')
 def test_peer_original_attachment_hash_binding_red(self):
  self.packet['lock']['pin_attachment_sha256']={'3aecb403afebae7a5046e9e4bd3f8f97':'7feadcd7212c1106f44559bac641f80eaa39c8289bce9d86e5c1aa65c9d29136','5a4ed6758d7778e26d2d4c504f3a47bb':'5685e836373afaecafba0e284f35d62402df478beedda7b0f3f40564ef2ccbca'};self.assertEqual(self.result()['status'],'FAIL')

 def test_peer_known_wrong_f006_manifest_with_missing_net_red(self):
  del self.packet['lock']['net_md5'];self.packet['lock']['net_manifest_md5']='b'*32;self.assertEqual(self.result()['status'],'FAIL')
 def test_peer_PASS_other_lock_with_historical_current_unverified(self):
  raw=('PASS AUTOLOCK_2_other\nHistorical FAIL '+self.packet['lock']['tag']).encode();self.packet['cr']['external_pass'].update(self.artifact('fixture_wrong_CR_coverage.txt',raw));self.assertEqual(self.result()['status'],'UNVERIFIED')
 def test_peer_PASS_other_script_with_historical_current_unverified(self):
  raw=('PASS successor '+'b'*64+'\nHistorical FAIL '+self.packet['script']['live_sha256']).encode();self.packet['script']['review'].update(self.artifact('fixture_wrong_script_coverage.txt',raw));self.assertEqual(self.result()['status'],'UNVERIFIED')

 def test_peer_header_longer_lock_token_unverified(self):
  raw=('PASS '+self.packet['lock']['tag']+'_other\nSYNTHETIC').encode();self.packet['cr']['external_pass'].update(self.artifact('fixture_longer_CR_tag.txt',raw));self.assertEqual(self.result()['status'],'UNVERIFIED')
 def test_peer_header_longer_script_token_unverified(self):
  raw=('PASS successor '+self.packet['script']['live_sha256']+'abcd\nSYNTHETIC').encode();self.packet['script']['review'].update(self.artifact('fixture_longer_script_hash.txt',raw));self.assertEqual(self.result()['status'],'UNVERIFIED')

if __name__=='__main__':unittest.main(verbosity=2)
