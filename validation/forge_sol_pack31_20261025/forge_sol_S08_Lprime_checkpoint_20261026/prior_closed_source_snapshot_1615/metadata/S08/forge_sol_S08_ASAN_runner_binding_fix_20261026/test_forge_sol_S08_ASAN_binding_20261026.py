import contextlib, copy, hashlib, importlib.util, json, os, pathlib, sys, tempfile, types, unittest
from unittest import mock

ROOT=pathlib.Path(__file__).resolve().parent
ORIGINAL='--original' in sys.argv
if ORIGINAL:sys.argv.remove('--original')
def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
new=load(ROOT.parent/'forge_sol_S08_ASAN_full_qualification_v2_20261026.py','new_qualification')
old=load(ROOT/'forge_sol_S08_ASAN_full_qualification_original_e019_20261026.py','old_qualification')

class BindingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=pathlib.Path(self.temp.name);self.source=self.root/'source';self.build=self.root/'build'
        self.source.mkdir();self.build.mkdir()
        for name in ('src/nnue_weights.inc','src/example.cpp','tests/tests.cpp'):
            p=self.source/name;p.parent.mkdir(exist_ok=True);p.write_bytes(name.encode())
        self.targets=['forge','forge_prof_tests']+['test'+str(i) for i in range(10)]
        for name in self.targets:(self.build/name).write_bytes(b'\x7fELF'+name.encode())
        compiler=self.root/'compiler';compiler.write_bytes(b'fixture compiler')
        def snapshot(source):return {str(p.relative_to(source)):new.sha(p) for p in sorted(pathlib.Path(source).rglob('*')) if p.is_file()}
        self.shared=types.SimpleNamespace(TARGETS=tuple(self.targets),snapshot=snapshot,CXX=compiler,CXX_SHA=new.sha(compiler))
        self.recipe={'status':'PASS_ASAN_UBSAN_RECIPE','fixture':'unchanged'}
        self.adapter=types.SimpleNamespace(audit_recipe=lambda *unused:copy.deepcopy(self.recipe))
        self.freeze={'source':str(self.source),'source_sha256':snapshot(self.source)}
        self.receipt={'status':'PASS_BUILD_ONLY','profile':'RelWithDebInfo_ASAN_UBSAN_PROF_H256','source':str(self.source),'build_dir':str(self.build),'source_freeze_sha256':'fixture_sha','source_unchanged':True,'expected_full_CTest_count':15,'stage':'all','shared_controller_sha256':new.SHARED_SHA,'adapter_sha256':new.ADAPTER_SHA,'pending_targets':[],'completed_targets':self.targets,'all_targets_order':self.targets,'source_before':copy.deepcopy(self.freeze['source_sha256']),'compiler_sha256':self.shared.CXX_SHA,'target_artifacts':{name:{'sha256':new.sha(self.build/name),'bytes':(self.build/name).stat().st_size} for name in self.targets},'recipe_before':copy.deepcopy(self.recipe),'recipe_after':copy.deepcopy(self.recipe),'commands':[{'returncode':0,'stop_reason':None,'leader_reaped':True,'all_group_members_after_reap':[]}]}
        engine_sha=self.receipt['target_artifacts']['forge']['sha256']
        self.first={'results':[{'label':'ASAN','pass':True,'bench_counts':[308972],'returncode':0,'timeout':False,'first_runtime_bare_bench':True,'no_uci_before_bench':True,'binary_sha256_before':engine_sha,'binary_sha256_after':engine_sha}]}
    def validate(self):
        if not ORIGINAL:
            return new.verify_binding(self.receipt,self.first,self.freeze,self.source,self.build,self.shared,self.adapter,'fixture_sha')
        # Actual original main with downstream CTest mocked PASS, no child/engine.
        # This isolates preflight invariants, rather than testing CTest itself.
        helper=self.root/'fixture_helper.py'
        helper.write_text('def load_ctest_inventory(*a):return {"expected_names":list(map(str,range(15)))}\ndef bind_allowlist(*a):return {}\ndef check_ctest(*a):return {"test_cases":[{"failed":False} for i in range(15)]}\n')
        first_path=self.root/'forge_sol_S08_TLS_v2_FIRST_native_20261026';first_path.mkdir()
        (first_path/'forge_sol_S08_TLS_v2_first_runtime_result_20261026.json').write_text(json.dumps(self.first))
        receipt=self.root/'receipt.json';receipt.write_text(json.dumps(self.receipt))
        allow=self.root/'allow.json';allow.write_text('{}')
        class FakePopen:
            pid=99999999;returncode=0
            def __init__(self,*a,**kw):kw['stdout'].write(b'{}')
            def wait(self,*a,**kw):return 0
        patches={'HERE':self.root,'BUILD':self.build,'SOURCE':self.source,'HELPER':helper,'HELPER_SHA':new.sha(helper),'ALLOW':allow}
        with contextlib.ExitStack() as stack:
            for key,value in patches.items():stack.enter_context(mock.patch.object(old,key,value))
            stack.enter_context(mock.patch.object(old.subprocess,'Popen',FakePopen))
            stack.enter_context(mock.patch.object(sys,'argv',['fixture','--execute','--closed-build-receipt',str(receipt),'--output',str(self.root/'out')]))
            stack.enter_context(mock.patch.object(old.shutil,'disk_usage',return_value=types.SimpleNamespace(free=100000000)))
            code=old.main()
        if code:raise ValueError('original rejected fixture')
        return {'status':'PASS'}
    def test_unchanged_fixture_accepted(self):self.assertIn('PASS',self.validate()['status'])
    def test_changed_test_executable_rejected(self):
        (self.build/'test0').write_bytes(b'\x7fELFmodified test')
        with self.assertRaises(ValueError):self.validate()
    def test_changed_helper_executable_rejected(self):
        (self.build/'forge_prof_tests').write_bytes(b'\x7fELFmodified helper')
        with self.assertRaises(ValueError):self.validate()
    def test_changed_source_rejected(self):
        (self.source/'src/example.cpp').write_bytes(b'modified source')
        with self.assertRaises(ValueError):self.validate()
    def test_changed_recipe_rejected(self):
        self.recipe['fixture']='modified'
        with self.assertRaises(ValueError):self.validate()
    @unittest.skipIf(ORIGINAL,'successor-specific exact inventory control')
    def test_missing_artifact_rejected(self):
        del self.receipt['target_artifacts']['test0']
        with self.assertRaises(ValueError):self.validate()
    @unittest.skipIf(ORIGINAL,'successor-specific exact inventory control')
    def test_duplicate_target_rejected(self):
        self.receipt['completed_targets']=self.targets[:-1]+['test0']
        with self.assertRaises(ValueError):self.validate()
    @unittest.skipIf(ORIGINAL,'successor-specific compiler control')
    def test_changed_compiler_rejected(self):
        self.shared.CXX.write_bytes(b'modified compiler')
        with self.assertRaises(ValueError):self.validate()
    @unittest.skipIf(ORIGINAL,'successor-specific cleanup receipt control')
    def test_unreaped_build_descendant_rejected(self):
        self.receipt['commands'][0]['all_group_members_after_reap']=[{'pid':123,'state':'Z'}]
        with self.assertRaises(ValueError):self.validate()
    @unittest.skipIf(ORIGINAL,'successor-specific first runtime control')
    def test_changed_first_runtime_after_hash_rejected(self):
        self.first['results'][0]['binary_sha256_after']='0'*64
        with self.assertRaises(ValueError):self.validate()
    @unittest.skipIf(ORIGINAL,'successor environment control')
    def test_sanitizer_environment_enabled_and_restored(self):
        previous={k:os.environ.get(k) for k in ('ASAN_OPTIONS','UBSAN_OPTIONS','PYTHONDONTWRITEBYTECODE')}
        with new.sanitizer_environment():
            self.assertEqual(os.environ['ASAN_OPTIONS'],'detect_leaks=1:halt_on_error=1')
            self.assertEqual(os.environ['UBSAN_OPTIONS'],'halt_on_error=1:print_stacktrace=1')
        self.assertEqual(previous,{k:os.environ.get(k) for k in previous})

if __name__=='__main__':unittest.main(verbosity=2)
