"""Pure shared-ASAN parameter, PIC, loader metadata and resume guards."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
MODULE=Path(__file__).with_name('forge_sol_S08_B_asan_shared_build_20261026.py')
class SharedSanitizerTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(MODULE.is_file(),'shared sanitizer adapter missing')
        spec=importlib.util.spec_from_file_location('sharedasan',MODULE);self.api=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.api)
    def tokens(self,pic=False):
        return [str(self.api.shared.CXX),*self.api.shared.FLAGS.split(),'-O2','-g0','-DNDEBUG','-DFORGE_PROF=1','-std=c++20','-fsanitize=address,undefined','-fno-omit-frame-pointer']+(['-fPIC'] if pic else [])
    def test_config_is_separate_shared_profile_and_14_runtime_artifacts(self):
        args=self.api.configure_args(Path('/source'),Path('/newbuild'))
        for flag in ('-DCMAKE_BUILD_TYPE=RelWithDebInfo','-DBUILD_SHARED_LIBS=ON','-DCMAKE_CXX_FLAGS_RELWITHDEBINFO=-O2 -g0 -DNDEBUG','-DFORGE_ENABLE_SANITIZERS=ON','-DFORGE_PROF=ON','-DFORGE_NATIVE=OFF','-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF'):self.assertIn(flag,args)
        self.assertEqual(self.api.REQUIRED_CPU,0)
        self.assertEqual(len(self.api.TARGETS),13);self.assertEqual(len(self.api.CORE_TUS),8);self.assertEqual(len(self.api.EXPECTED_TUS),21)
        self.assertEqual(self.api.RUNTIME_ARTIFACTS,(self.api.CORE,)+self.api.TARGETS)
    def test_compile_flags_require_sanitizers_noDWARF_and_corePIC(self):
        self.api.check_tokens(self.tokens(True),'src/search.cpp',True)
        self.api.check_tokens(self.tokens(False),'src/uci.cpp',True)
        with self.assertRaises(ValueError):self.api.check_tokens(self.tokens(False),'src/search.cpp',True)
        for extra in ('-O3','-g','-ggdb','-flto','-ffast-math','-fomit-frame-pointer','-fno-sanitize=undefined','-march=x86-64','-DFORGE_NNUE_HIDDEN=128'):
            with self.subTest(flag=extra),self.assertRaises(ValueError):self.api.check_tokens(self.tokens(True)+[extra],'src/search.cpp',True)
        with self.assertRaises(ValueError):self.api.check_tokens([x for x in self.tokens(True) if not x.startswith('-fsanitize=')],'src/search.cpp',True)
    def dynamic(self,core=False,nearest=False):
        lines=['0x1 (NEEDED) Shared library: [libasan.so.8]','0x1 (NEEDED) Shared library: [libubsan.so.1]']
        if core:lines.append('0xe (SONAME) Library soname: [libforge_core.so]')
        else:
            if not nearest:lines.append('0x1 (NEEDED) Shared library: [libforge_core.so]')
            lines.append('0x1d (RUNPATH) Library runpath: [/newbuild]')
        return '\n'.join(lines)
    def test_dynamic_metadata_binds_soname_needed_and_private_search_path(self):
        self.api.parse_dynamic(self.dynamic(core=True),self.api.CORE,Path('/newbuild'))
        self.api.parse_dynamic(self.dynamic(),'forge',Path('/newbuild'))
        self.api.parse_dynamic(self.dynamic(nearest=True),'forge_nearest_pawn_tests',Path('/newbuild'))
        for text,name in [(self.dynamic().replace('/newbuild','/other'),'forge'),(self.dynamic().replace('/newbuild','/newbuild:'),'forge'),(self.dynamic(nearest=True),'forge'),(self.dynamic(core=True).replace('libforge_core.so','different.so'),self.api.CORE),(self.dynamic(core=True).replace('libubsan.so.1','missing.so'),self.api.CORE)]:
            with self.subTest(name=name),self.assertRaises(ValueError):self.api.parse_dynamic(text,name,Path('/newbuild'))
    def test_resume_cannot_mix_profiles_or_change_SO(self):
        with tempfile.TemporaryDirectory() as folder:
            build=Path(folder)
            for name in (self.api.CORE,'forge'):(build/name).write_bytes(name.encode())
            artifacts={name:{'sha256':self.api.shared.sha(build/name)} for name in (self.api.CORE,'forge')}
            old={'status':'PAUSED_BUILD_ONLY','profile':self.api.PROFILE,'build_dir':str(build),'source_freeze_sha256':'freeze','source_unchanged':True,'configured':True,'completed_targets':['forge'],'target_artifacts':artifacts,'dynamic_metadata':{},'commands':[{'pid':101,'leader_reaped':True,'all_group_members_after_reap':[]}]}
            self.assertEqual(self.api.resume_state(old,build,'freeze')['completed_targets'],['forge'])
            paused=dict(old,commands=[{'pid':None,'leader_reaped':False,'all_group_members_after_reap':[],'stop_reason':'DISK_FREE_BELOW_8MIB'}])
            self.assertEqual(self.api.resume_state(paused,build,'freeze')['completed_targets'],['forge'])
            with self.assertRaises(ValueError):self.api.resume_state(dict(old,commands=[{'pid':123,'leader_reaped':False,'all_group_members_after_reap':[]}]),build,'freeze')
            for change in ({'profile':'B_RELEASE_ON'},{'source_freeze_sha256':'wrong'},{'commands':[{'leader_reaped':True,'all_group_members_after_reap':[{'state':'Z'}]}]}):
                with self.assertRaises(ValueError):self.api.resume_state(dict(old,**change),build,'freeze')
            (build/self.api.CORE).write_bytes(b'changed')
            with self.assertRaises(ValueError):self.api.resume_state(old,build,'freeze')

class SharedRecipeAndLedgerTests(unittest.TestCase):
    setUp=SharedSanitizerTests.setUp
    tokens=SharedSanitizerTests.tokens
    dynamic=SharedSanitizerTests.dynamic
    def test_full21_TU_14_link_recipe_and_ownership_ledger(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'source';source.mkdir();build=root/'build';build.mkdir();out=root/'out';out.mkdir()
            cache={'CMAKE_BUILD_TYPE':'RelWithDebInfo','CMAKE_CXX_COMPILER':str(self.api.shared.CXX),'CMAKE_CXX_FLAGS':self.api.shared.FLAGS,'CMAKE_CXX_FLAGS_RELWITHDEBINFO':'-O2 -g0 -DNDEBUG','CMAKE_HOME_DIRECTORY':str(source),'BUILD_SHARED_LIBS':'ON','FORGE_ENABLE_SANITIZERS':'ON','FORGE_PROF':'ON','FORGE_NATIVE':'OFF','CMAKE_INTERPROCEDURAL_OPTIMIZATION':'OFF','CMAKE_EXPORT_COMPILE_COMMANDS':'ON','FORGE_EXPOSE_TUNABLES':'OFF','FORGE_BUILD_VALIDATION_TOOLS':'OFF','FORGE_BUILD_TUNING_TOOLS':'OFF'}
            (build/'CMakeCache.txt').write_text(''.join(k+':STRING='+v+'\n' for k,v in cache.items()))
            rows=[{'file':str(source/name),'arguments':self.tokens(name in self.api.CORE_TUS)} for name in sorted(self.api.EXPECTED_TUS)]
            (build/'compile_commands.json').write_text(json.dumps(rows));freeze={'source_sha256':{name:'unused' for name in self.api.EXPECTED_TUS}}
            common=[str(self.api.shared.CXX),*self.api.shared.FLAGS.split(),'-O2','-g0','-DNDEBUG','-fsanitize=address,undefined']
            for name in ('forge_core',)+self.api.TARGETS:
                path=build/f'CMakeFiles/{name}.dir/link.txt';path.parent.mkdir(parents=True)
                tokens=common+(['-fPIC','-shared','-Wl,-soname,libforge_core.so'] if name=='forge_core' else ['-Wl,-rpath,'+str(build),self.api.CORE])
                path.write_text(' '.join(tokens))
            recipe=self.api.audit_recipe(source,build,freeze);self.assertEqual(len(recipe['translation_units']),21);self.assertEqual(len(recipe['links']),14)
            core_row=next(row for row in rows if row['file'].endswith('/src/search.cpp'))
            core_row['arguments']=[x for x in core_row['arguments'] if x!='-fPIC'];(build/'compile_commands.json').write_text(json.dumps(rows))
            with self.assertRaises(ValueError):self.api.audit_recipe(source,build,freeze)
            (build/'forge').write_bytes(b'fixture');receipt={'pid':101,'returncode':0,'stop_reason':None,'leader_reaped':True,'all_group_members_after_reap':[],'captures':{'stderr':{'bytes':0}}}
            def owned(argv,dest,label,unused,deadline):
                (dest/(label+'.stdout')).write_text(self.dynamic().replace('/newbuild',str(build)))
                (dest/(label+'.receipt.json')).write_text(json.dumps(receipt));return receipt
            ledger=[]
            with patch.object(self.api.shared,'run_owned',owned):self.api.audit_runtime('forge',build,out,999999,0,ledger)
            self.assertEqual(ledger,[receipt])
if __name__=='__main__':unittest.main(verbosity=2)
