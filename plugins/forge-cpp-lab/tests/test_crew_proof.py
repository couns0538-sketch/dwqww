"""Real subprocess fixtures validate the runner; they are not engine qualification."""
import hashlib, importlib.util, json, pathlib, subprocess, sys, tempfile, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'skills/forge-lock-proof-set/scripts/run_proof_set.py'
SHA='a'*40

def digest(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()

ADAPTER=r'''import hashlib,json,pathlib,sys
stage,result,mode=sys.argv[1:]; p=pathlib.Path(result);root=p.parent;name=root.name
h=lambda f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()
log=root/'native.log';log.write_text('fixture native execution transcript; not an engine\n')
net=hashlib.sha256(b'fixture net').hexdigest();source='a'*40; nodes={'11':101,'13':202}
a=root.parent/'build_a'/'forge.exe';b=root.parent/'build_b'/'forge.exe'
m={}
if name.startswith('build_'):
 exe=root/'forge.exe';exe.write_bytes(b'fixture engine' if not(mode=='different' and name=='build_b') else b'different')
 profile=root/'profile.gcda';profile.write_bytes(b'fixture profile')
 m={'binary':'forge.exe','profile_files':[{'path':'profile.gcda','sha256':h(profile)}], 'compile_commands':[['g++','-flto','-fprofile-generate','-ffp-contract=off','-fno-fast-math'],['g++','-flto','-fprofile-use','-Werror=missing-profile','-Werror=coverage-mismatch','-ffp-contract=off','-fno-fast-math','-o',str(exe)]]}
elif name=='off_pins':m={'binary_a_sha256':h(a),'binary_b_sha256':h(b),'nodes_a':nodes,'nodes_b':dict(nodes),'options':{'Feature':0}}
elif name=='on_active':m={'binary_sha256':h(a),'nodes':{'11':102,'13':202},'active_count':1,'options':{'Feature':1}}
elif name=='perft':m={'binary_sha256':h(a),'startpos5':4865609,'kiwipete5':193690690}
elif name.startswith('smoke_'):m={'binary_sha256':h(a),'threads':1 if name=='smoke_t1' else 4,'searches':2,'illegal_moves':0,'crashes':0,'time_forfeits':0,'completed':True}
else:
 exe=root/'sanitized.exe';exe.write_bytes(b'fixture instrumented engine')
 m={'instrumented_binary':'sanitized.exe','compile_commands':[['g++','-fsanitize=address,undefined']], 'sanitizers':['address','undefined'],'executed_tests':2,'failures':0,'runtime_started':True}
if mode=='pin' and name=='off_pins':m['nodes_a']['11']=100
if mode=='inactive' and name=='on_active':m['active_count']=0
if mode=='sameon' and name=='on_active':m['nodes']={'11':101,'13':202}
if mode=='asan' and name=='asan_ubsan':m['runtime_started']=False
if mode=='sanlog' and name=='asan_ubsan':log.write_text('ERROR: AddressSanitizer: heap-use-after-free')
if mode=='bool' and name=='smoke_t1':m['searches']=True
if mode=='badreceipt' and name=='perft':
 p.write_text('[]');raise SystemExit(0)
if mode=='profile' and name=='build_a':m['profile_files']=[]
if mode=='uselto' and name=='build_a':m['compile_commands'][1].remove('-flto')
if mode=='conflict' and name=='build_a':m['compile_commands'][1].append('-fno-lto')
if mode=='fma' and name=='build_a':m['compile_commands'][1].append('-ffp-contract=fast')
if mode=='wronglink' and name=='build_a':m['compile_commands'][1][-1]=str(root/'another.exe')
if mode=='profilewarnings' and name=='build_a':m['compile_commands'][1].remove('-Werror=missing-profile')
if mode=='downgrade' and name=='build_a':m['compile_commands'][1].append('-Wno-error=missing-profile')
if mode=='profilediag' and name=='build_a':log.write_text('warning: profile count data file not found [-Wmissing-profile]\n')
if mode=='mutation' and name=='asan_ubsan':a.write_bytes(b'changed by later stage')
if mode=='timeout' and name=='build_a':
 import time;time.sleep(5)
p.write_text(json.dumps({'schema':1,'status':'PASS','source_commit':source,'network_sha256':net,'metrics':m,'logs':[{'path':'native.log','sha256':h(log)}]}))
if mode=='nonzero' and name=='perft':raise SystemExit(7)
'''

class ProofTests(unittest.TestCase):
 def setUp(self):
  self.assertTrue(SCRIPT.exists(),'proof runner missing')
  spec=importlib.util.spec_from_file_location('crewproof',SCRIPT);self.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.m)
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.r=pathlib.Path(self.tmp.name)
  self.adapter=self.r/'adapter.py';self.adapter.write_text(ADAPTER)
  self.source=self.r/'source.tar';self.source.write_bytes(b'fixture source');self.net=self.r/'net';self.net.write_bytes(b'fixture net');self.base=self.r/'baseline.exe';self.base.write_bytes(b'fixture baseline')
 def contract(self,mode='ok'):
  inputs=[{'role':role,'path':str(p),'sha256':digest(p)} for role,p in [('compiler',pathlib.Path(sys.executable)),('recipe',self.adapter),('source',self.source),('network',self.net),('baseline_binary',self.base)]]
  c={'schema':1,'evidence_scope':'fixture','baseline_commit':'c'*40,'candidate_commit':SHA,'network_sha256':digest(self.net),'max_worker_threads':4,'expected_off_nodes':{'11':101,'13':202},'off_options':{'Feature':0},'on_options':{'Feature':1},'inputs':inputs,'stages':{}}
  for stage in self.m.STAGES:c['stages'][stage]={'argv':[sys.executable,str(self.adapter),stage,'{result}',mode],'timeout_seconds':10}
  p=self.r/'contract.json';p.write_text(json.dumps(c));return p
 def runproof(self,mode='ok'):
  p=self.contract(mode);out=self.r/'result';return self.m.run(p,out),out
 def test_complete_fixture_records_all_nine_check_rows(self):
  report,out=self.runproof();self.assertEqual(report['status'],'PASS');self.assertEqual(len(report['checks']),9);self.assertEqual(report['evidence_scope'],'fixture');self.assertTrue((out/'TABLE.md').is_file());self.assertEqual(report['baseline_binary_sha256'],digest(self.base));self.assertEqual(report['candidate_binary_sha256'],digest(out/'build_a/forge.exe'));self.assertEqual(report['net_sha256'],digest(self.net));self.assertEqual(report['tested_options'],{'off':{'Feature':0},'on':{'Feature':1}})
  for row in report['checks']:
   self.assertEqual(row['status'],'PASS');self.assertTrue(row['evidence'])
   for ref in row['evidence']:self.assertEqual(digest(out/ref['path']),ref['sha256'])
 def test_actual_fixture_report_is_rejected_by_gate_pack(self):
  report,out=self.runproof();self.assertEqual(report['status'],'PASS')
  spec=importlib.util.spec_from_file_location('gate_fixture_for_proof',ROOT/'tests/test_crew_gate_pack.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  gate=module.GatePackTests();gate.setUp();self.addCleanup(gate.doCleanups)
  item=next(a for a in gate.data['artifacts'] if a['role']=='proof');target=gate.root/item['path'];target.write_bytes((out/'REPORT.json').read_bytes());item['sha256']=digest(target)
  with self.assertRaisesRegex(ValueError,'native evidence scope'):gate.make()
  self.assertFalse(gate.out.exists())
 def test_different_builds_fail(self):self.assertEqual(self.runproof('different')[0]['status'],'FAIL')
 def test_off_pin_mismatch_fails(self):self.assertEqual(self.runproof('pin')[0]['status'],'FAIL')
 def test_inactive_on_fails(self):self.assertEqual(self.runproof('inactive')[0]['status'],'FAIL')
 def test_on_nodes_must_differ(self):self.assertEqual(self.runproof('sameon')[0]['status'],'FAIL')
 def test_sanitizer_must_execute(self):self.assertEqual(self.runproof('asan')[0]['status'],'FAIL')
 def test_sanitizer_error_log_overrides_claimed_pass(self):self.assertEqual(self.runproof('sanlog')[0]['status'],'FAIL')
 def test_nonzero_child_cannot_pass(self):self.assertEqual(self.runproof('nonzero')[0]['status'],'FAIL')
 def test_bool_count_rejected(self):self.assertEqual(self.runproof('bool')[0]['status'],'FAIL')
 def test_malformed_adapter_receipt_cannot_crash_without_table(self):self.assertEqual(self.runproof('badreceipt')[0]['status'],'FAIL')
 def test_use_phase_must_keep_lto(self):self.assertEqual(self.runproof('uselto')[0]['status'],'FAIL')
 def test_contradictory_lto_flags_reject(self):self.assertEqual(self.runproof('conflict')[0]['status'],'FAIL')
 def test_contradictory_fma_flag_rejects(self):self.assertEqual(self.runproof('fma')[0]['status'],'FAIL')
 def test_profile_use_requires_failure_on_missing_profiles(self):self.assertEqual(self.runproof('profilewarnings')[0]['status'],'FAIL')
 def test_profile_error_downgrade_rejects(self):self.assertEqual(self.runproof('downgrade')[0]['status'],'FAIL')
 def test_profile_diagnostics_override_claimed_pass(self):self.assertEqual(self.runproof('profilediag')[0]['status'],'FAIL')
 def test_final_link_binds_output(self):self.assertEqual(self.runproof('wronglink')[0]['status'],'FAIL')
 def test_missing_profile_cannot_pass(self):self.assertEqual(self.runproof('profile')[0]['status'],'FAIL')
 def test_later_stage_binary_mutation_cannot_pass(self):self.assertEqual(self.runproof('mutation')[0]['status'],'FAIL')
 def test_timeout_stops_later_stages_and_preserves_table(self):
  p=self.contract('timeout');c=json.loads(p.read_text());c['stages']['build_a']['timeout_seconds']=1;p.write_text(json.dumps(c));report=self.m.run(p,self.r/'out')
  self.assertEqual(report['status'],'FAIL');self.assertFalse((self.r/'out'/'build_b').exists());self.assertEqual(len(report['checks']),9)
 def test_two_thread_contract_refuses_before_launch(self):
  p=self.contract();c=json.loads(p.read_text());c['max_worker_threads']=2;p.write_text(json.dumps(c))
  with self.assertRaisesRegex(ValueError,'four-thread'):self.m.run(p,self.r/'out')
  self.assertFalse((self.r/'out').exists())
 def test_changed_recipe_refuses_before_output(self):
  p=self.contract();self.adapter.write_text(ADAPTER+'\n# changed\n')
  with self.assertRaisesRegex(ValueError,'hash'):self.m.run(p,self.r/'out')
  self.assertFalse((self.r/'out').exists())
 def test_never_overwrites_existing_output(self):
  p=self.contract();out=self.r/'out';out.mkdir();(out/'old').write_text('keep')
  with self.assertRaises(FileExistsError):self.m.run(p,out)
  self.assertEqual((out/'old').read_text(),'keep')
 def test_cli_reports_failure_and_exit(self):
  p=self.contract('pin');r=subprocess.run([sys.executable,str(SCRIPT),str(p),'--out',str(self.r/'out')],capture_output=True,text=True)
  self.assertEqual(r.returncode,1,r.stderr);self.assertIn('FAIL',r.stdout)

if __name__=='__main__':unittest.main()
