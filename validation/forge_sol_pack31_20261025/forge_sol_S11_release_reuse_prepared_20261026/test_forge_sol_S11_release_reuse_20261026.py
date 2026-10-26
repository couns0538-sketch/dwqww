"""Negative reuse-boundary tests; no native/compiler/engine execution."""
from pathlib import Path
import ast,copy,importlib.util,json,subprocess,sys,tempfile,unittest
HERE=Path(__file__).resolve().parent
P=HERE/'forge_sol_S11_release_reuse_20261026.py'
api=None
if P.exists():
    spec=importlib.util.spec_from_file_location('s11_reuse',P);api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
class ReuseBoundaries(unittest.TestCase):
    def need(self):self.assertIsNotNone(api,'Explicit frozen Release-baseline evidence producer is absent')
    def test_01_real_binding_is_explicit_old_evidence_not_fresh_build(self):
        self.need();b=api.make_binding('Lprime');self.assertEqual(b['evidence_class'],'REUSE_NOT_NEW_RUN');self.assertFalse(b['new_main_ELF']);self.assertFalse(b['new_full_Std']);self.assertEqual(b['raw_Std']['passed'],14)
    def test_02_candidate_role_refused(self):
        self.need()
        with self.assertRaisesRegex(ValueError,'baseline'):api.require_arm('B','candidate','Release')
    def test_03_ASAN_profile_refused(self):
        self.need()
        with self.assertRaisesRegex(ValueError,'Release'):api.require_arm('B','baseline','ASAN')
    def test_04_L_is_not_Lprime(self):
        self.need()
        with self.assertRaisesRegex(ValueError,'base'):api.require_arm('L','baseline','Release')
    def test_05_wrong_raw_FIRST_hash_refused(self):
        self.need();b=api.make_binding('Lprime');b['raw_FIRST']['stdout_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'binding'):api.verify_binding(b)
    def test_06_wrong_current_test_source_refused(self):
        self.need();b=api.make_binding('B');b['tests_source_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'binding'):api.verify_binding(b)
    def test_07_wrong_core_hash_refused(self):
        self.need();b=api.make_binding('B');b['core_archive']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'binding'):api.verify_binding(b)
    def test_08_wrong_original_Std_hash_refused(self):
        self.need();b=api.make_binding('B');b['raw_Std']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'binding'):api.verify_binding(b)
    def test_09_wrong_oracle_flags_refused(self):
        self.need();build=Path('/tmp/forge_sol_S11_native_20261026/test_oracle_plan/build');argv=api.oracle_plan('Lprime',build);argv.append('-ffast-math')
        with self.assertRaisesRegex(ValueError,'oracle'):api.verify_oracle_plan('Lprime',build,argv)
    def test_10_wrong_requested_source_refused(self):
        self.need();b=api.make_binding('Lprime');b['source']='/tmp/other_engine'
        with self.assertRaisesRegex(ValueError,'binding'):api.verify_binding(b)
    def test_11_corrupted_pinned_JSON_refused(self):
        self.need()
        with tempfile.TemporaryDirectory(dir='/tmp') as d:
            p=Path(d)/'copied.json';p.write_text('{}')
            with self.assertRaisesRegex(ValueError,'pin'):api.pinned_json(p,'0'*64)
    def test_12_original_sealed_verifier_still_rejects_reuse_schema(self):
        self.need()
        with tempfile.TemporaryDirectory(dir='/tmp') as d:
            p=Path(d)/'reuse.json';p.write_text(json.dumps({'schema':api.SCHEMA,'status':'REUSE_NOT_NEW_RUN'}))
            with self.assertRaisesRegex(ValueError,'S11 build'):api.sealed_qualifier().verify_build(p)
    def test_13_oracle_plan_is_original_baseline_source_and_normal_flags(self):
        self.need();b=api.make_binding('B');build=Path('/tmp/forge_sol_S11_native_20261026/test_oracle_plan/build');argv=api.oracle_plan('B',build);api.verify_oracle_plan('B',build,argv);self.assertIn('-I'+b['source'],argv);self.assertNotIn('-DS11_REQUIRE_TABLE=1',argv)
    def test_14_fake_complete_reuse_receipt_cannot_bypass_oracle_gate(self):
        self.need()
        with tempfile.TemporaryDirectory(dir='/tmp') as d:
            p=Path(d)/'reuse.json';p.write_text(json.dumps({'schema':api.SCHEMA,'status':'PASS_ORACLE_ONLY_WITH_REUSED_STD','base':'B','role':'baseline','profile':'Release','evidence':api.make_binding('B')}))
            with self.assertRaisesRegex(ValueError,'oracle|receipt|directory'):api.bind_reuse_arm(p,Path('/tmp/wrong_FIRST'),'baseline','a'*40)
    def test_15_unpinned_module_path_refused(self):
        self.need()
        with tempfile.TemporaryDirectory(dir='/tmp') as d:
            p=Path(d)/'substitute.py';p.write_text('SENTINEL=1\n')
            with self.assertRaisesRegex(ValueError,'sealed'):api.load('unexpected_substitute',p)
    def test_16_oracle_producer_help_does_not_execute_native(self):
        p=HERE/'forge_sol_S11_reuse_oracle_build_20261026.py';self.assertTrue(p.is_file(),'oracle-only producer absent')
        r=subprocess.run([sys.executable,'-B',str(p),'--help'],capture_output=True);self.assertEqual(r.returncode,0,r.stderr)
    def test_17_oracle_producer_requires_explicit_execute_before_writes(self):
        p=HERE/'forge_sol_S11_reuse_oracle_build_20261026.py';self.assertTrue(p.is_file(),'oracle-only producer absent')
        with tempfile.TemporaryDirectory(dir='/tmp') as d:
            out=Path(d)/'must_not_exist';r=subprocess.run([sys.executable,'-B',str(p),'--base','B','--out',str(out),'--cpu','0','--authorization-reference','SOURCE_ONLY_TEST','--s10-published-commit','a'*40],capture_output=True)
            self.assertNotEqual(r.returncode,0);self.assertIn(b'explicit',r.stderr);self.assertFalse(out.exists())
    def test_18_parity_successor_preserves_original_candidate_binding_tail(self):
        p=HERE/'forge_sol_S11_scalar_parity_reuse_run_20261026.py';self.assertTrue(p.is_file(),'explicit parity successor absent')
        old=ast.parse((api.SEALED/'forge_sol_S11_scalar_parity_run_20261026.py').read_text());new=ast.parse(p.read_text())
        a=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name=='bind_arm');b=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=='bind_arm')
        self.assertEqual([ast.dump(n) for n in b.body[-len(a.body):]],[ast.dump(n) for n in a.body])
    def test_19_light_check_helper_help_does_not_execute_native(self):
        p=HERE/'forge_sol_S11_reuse_light_checks_20261026.py';self.assertTrue(p.is_file(),'explicit light checker absent')
        r=subprocess.run([sys.executable,'-B',str(p),'--help'],capture_output=True);self.assertEqual(r.returncode,0,r.stderr)
    def test_20_light_checks_require_execute_before_writes(self):
        p=HERE/'forge_sol_S11_reuse_light_checks_20261026.py';self.assertTrue(p.is_file(),'explicit light checker absent')
        with tempfile.TemporaryDirectory(dir='/tmp') as d:
            out=Path(d)/'must_not_exist';r=subprocess.run([sys.executable,'-B',str(p),'--reuse-receipt',str(Path(d)/'no_receipt'),'--out',str(out),'--cpu','0','--authorization-reference','SOURCE_ONLY_TEST'],capture_output=True)
            self.assertNotEqual(r.returncode,0);self.assertIn(b'explicit',r.stderr);self.assertFalse(out.exists())
    def test_21_reuse_refuses_fresh_FIRST_and_JUnit_claims(self):
        self.need();self.assertTrue(hasattr(api,'verify_reuse_claims'),'explicit no-fresh-FIRST/JUnit guard absent')
        b={'evidence_class':'REUSE_NOT_NEW_RUN','new_main_ELFs':0,'new_FIRST_runs':0,'new_full_Std_runs':0,'new_JUnit':False};api.verify_reuse_claims(b)
        for key,value in [('new_FIRST_runs',1),('new_JUnit',True),('new_main_ELFs',False)]:
            changed=dict(b);changed[key]=value
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'fresh'):api.verify_reuse_claims(changed)
    def test_22_runtime_dependencies_are_fixed_and_wrong_hash_is_rejected(self):
        self.need();self.assertTrue(hasattr(api,'verify_runtime_dependencies'),'light dependency guard absent')
        good=api.verify_runtime_dependencies();self.assertGreater(len(good),3)
        bad=dict(api.RUNTIME_PINS);bad[next(iter(bad))]='0'*64
        with self.assertRaisesRegex(ValueError,'runtime'):api.verify_runtime_dependencies(bad)
if __name__=='__main__':unittest.main(verbosity=2)
